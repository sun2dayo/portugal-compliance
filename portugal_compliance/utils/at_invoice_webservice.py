# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Cliente do webservice de Comunicacao de Faturas da AT (RegisterInvoice),
para o modo "Tempo Real" (ver Portugal Auth Settings ->
invoice_communication_method). Alternativa legal ao SAF-T mensal -
Portaria n.º 195/2020 / Decreto-Lei 28/2019.

Especificacao de referencia: WSDL oficial (factemi.at.min_financas.pt/
documents, servico "fatcorews", incluido em wsdl/faturas.wsdl) e o
cliente do modulo Dolibarr "complianceportugal" (NovaDX), ja validado
contra a AT em producao.

Pontos-chave confirmados no WSDL/cliente de referencia:
  - Autenticacao: mTLS (mesmo certificado cliente do webservice de
    series) + o MESMO cabecalho WS-Security proprietario (AES-128 +
    RSA) ja implementado em at_webservice.py - nao ha nada novo a
    construir aqui, so reutilizar.
  - HashCharacters no payload NAO e a hash completa - sao so os 4
    caracteres de controlo (posicoes 1/11/21/31), o mesmo valor que ja
    guardamos como signature_hash_control em ATCUD Log (usado no QR
    code). E um campo DIFERENTE do <Hash> do SAF-T (que leva a hash
    completa) - confundir os dois foi um erro real que so se percebeu
    ao ler a estrutura exata do WSDL.
  - Os dados fiscais por linha (taxa, codigo de isencao, totais) usam
    exatamente a mesma logica que ja construimos e testamos para o
    SAF-T (utils/saft_generator.SAFTGenerator) - reutilizada aqui em
    vez de duplicada.
"""

import json

import frappe
from frappe import _
from frappe.utils import getdate, get_datetime, flt

import zeep
from zeep.transports import Transport

from portugal_compliance.utils.at_webservice import (
	ATWebserviceError,
	_build_mtls_session,
	_build_wsse_security_header,
)
from portugal_compliance.utils.saft_generator import SAFTGenerator

import os


# 2001 nao se aplica aqui (e especifico do webservice de series) - os
# codigos de sucesso deste webservice, confirmados numa chamada real
# contra a sandbox da AT (2026-08-21), sao 0 / 0000.
#
# "Documento duplicado" e tratado como sucesso idempotente (a fatura
# ja esta comunicada, repetir o envio nao e um erro operacional) - mas
# o CODIGO REAL devolvido pela sandbox foi -10 ("O documento ja foi
# registado pelo emitente"), nao o -3 documentado no cliente de
# referencia (modulo Dolibarr). Mantidos os dois: -3 porque e o que a
# documentacao/cliente de referencia afirma, -10 porque foi o que a AT
# realmente devolveu num teste ao vivo - a AT pode usar qualquer um
# consoante o tipo de duplicacao detetada.
SUCCESS_CODES = {"0", "0000"}
DUPLICATE_CODES = {"-3", "-10"}

AT_ERROR_MESSAGES = {
	"0": "Sucesso",
	"1": "Utilizador não preenchido",
	"2": "Tamanho do utilizador incorreto",
	"3": "NIF do Utilizador AT inválido",
	"4": "Utilizador com formato inválido",
	"5": "Subutilizador com formato inválido",
	"6": "Senha não preenchida",
	"7": "Codificação Base64 inválida",
	"8": "Cifra da chave pública inválida",
	"9": "Formato do Timestamp inválido",
	"10": "Validade da credencial expirada",
	"11": "Chave simétrica inválida",
	"12": "Chave simétrica repetida",
	"13": "Estrutura da senha inválida",
	"99": "Erro na validação da senha (senha errada ou acesso suspenso)",
	"-1": "Parâmetros de entrada inválidos",
	"-2": "Data de emissão inválida",
	"-3": "Documento duplicado (já existe na AT)",
	"-4": "Entidade emissora sem permissões para este NIF",
	"-16": "Utilizador não tem permissões para registar documentos com autofaturação para este NIF (confirmado em teste real - SelfBillingIndicator=1 exige autorizacao especifica na AT)",
	"-10": "Documento já registado pelo emitente (confirmado em teste real contra a AT)",
	"-98": "Erro de integridade/tipo de dados nos parâmetros",
	"-99": "Erro interno na AT",
}


def get_at_error_message(code, default_msg=""):
	return AT_ERROR_MESSAGES.get(str(code), default_msg or f"Erro desconhecido ({code})")


class InvoiceWebserviceError(Exception):
	pass


def get_invoice_webservice_client():
	"""
	Cliente zeep para o webservice de faturas (RegisterInvoice/
	ChangeInvoiceStatus/DeleteInvoice), com mTLS + WS-Security -
	reutiliza as MESMAS credenciais e o MESMO par de funcoes de baixo
	nivel ja usados no webservice de series (ver at_webservice.py).
	"""
	settings = frappe.get_single("Portugal Auth Settings")

	cert_path = settings.get("mtls_certificate_path")
	key_path = settings.get("mtls_private_key_path")
	if not cert_path or not key_path:
		raise InvoiceWebserviceError(
			_("Certificado mTLS não configurado em Portugal Auth Settings.")
		)

	at_public_cert_path = settings.get("at_public_certificate_path")
	if not at_public_cert_path:
		raise InvoiceWebserviceError(
			_("Certificado público da AT não configurado em Portugal Auth Settings.")
		)

	at_username = settings.get("at_username")
	at_password = settings.get_password("at_password", raise_exception=False)
	if not at_username or not at_password:
		raise InvoiceWebserviceError(
			_("Credenciais do webservice da AT não configuradas em Portugal Auth Settings.")
		)

	# Confirmado no manual tecnico de referencia: 723 (testes), 443/
	# sem porta explicita (producao) - mesmo par empresa/porta usado
	# pelo servico "fatcorews", distinto do "SeriesWSService".
	sandbox_mode = settings.get("sandbox_mode")
	if sandbox_mode is None:
		sandbox_mode = 1
	endpoint = (
		"https://servicos.portaldasfinancas.gov.pt:723/fatcorews/ws/"
		if int(sandbox_mode)
		else "https://servicos.portaldasfinancas.gov.pt/fatcorews/ws/"
	)

	wsdl_path = os.path.join(
		os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wsdl", "faturas.wsdl"
	)
	session = _build_mtls_session(cert_path, key_path)
	transport = Transport(session=session, timeout=60)
	client = zeep.Client(wsdl=wsdl_path, transport=transport)

	binding_name = list(client.wsdl.bindings.keys())[0]
	service = client.create_service(binding_name, endpoint)

	header = _build_wsse_security_header(at_username, at_password, at_public_cert_path)
	return service, header


def _get_signature_for_invoice(document_type, document_name):
	"""
	HashCharacters (4 caracteres de controlo, ver cabecalho do modulo)
	vem de ATCUD Log - a mesma assinatura RSA-SHA1 ja gerada no submit
	do documento (utils/signature.py), nunca recalculada aqui.
	"""
	return frappe.db.get_value(
		"ATCUD Log",
		{"document_type": document_type, "document_name": document_name, "generation_status": "Success"},
		["signature_hash", "signature_hash_control"],
		as_dict=True,
	)


def build_invoice_payload(document_type, document_name):
	"""
	Constroi o dict RegisterInvoiceRequest para uma unica fatura,
	reutilizando SAFTGenerator.get_sales_invoices_data() (ja testado e
	validado contra o XSD do SAF-T) para os dados fiscais por linha, em
	vez de recalcular a mesma logica de taxa/isencao aqui outra vez.
	"""
	if document_type != "Sales Invoice":
		raise InvoiceWebserviceError(
			_("Comunicação de faturas em tempo real só está implementada para Sales Invoice, não {0}").format(
				document_type
			)
		)

	doc = frappe.get_doc(document_type, document_name)
	if doc.docstatus != 1:
		raise InvoiceWebserviceError(_("Documento {0} não está submetido").format(document_name))

	company_doc = frappe.get_doc("Company", doc.company)
	generator = SAFTGenerator()

	# Reutiliza a query do SAF-T (filtrando por 1 dia so devolve as
	# faturas dessa data - filtramos a nossa pelo nome a seguir).
	invoices = generator.get_sales_invoices_data(doc.company, doc.posting_date, doc.posting_date)
	invoice = next((i for i in invoices if i.name == document_name), None)
	if invoice is None:
		raise InvoiceWebserviceError(
			_("Não foi possível reconstruir os dados fiscais de {0} a partir do gerador SAF-T").format(
				document_name
			)
		)

	signature = _get_signature_for_invoice(document_type, document_name)
	hash_characters = (signature.signature_hash_control if signature else None) or "0"

	settings = frappe.get_single("Portugal Auth Settings")
	certificate_number = settings.get("software_certificate_number") or "0"

	customer_tax_id = doc.tax_id or "999999990"
	customer_address_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": doc.customer, "parenttype": "Address"},
		"parent",
	)
	customer_country_name = (
		frappe.db.get_value("Address", customer_address_name, "country") if customer_address_name else None
	)
	customer_country = generator._country_code(customer_country_name)

	line_summary = []
	for item in invoice.lines:
		# item.amount ja vem em valor absoluto e item.debit_credit ja
		# vem calculado a partir do sinal real (ver
		# SAFTGenerator.get_sales_invoices_data) - reutilizado aqui tal
		# como esta, para nao repetir a logica de sinal/isencao numa
		# segunda vez. Uma Nota de Credito (linhas negativas no
		# ERPNext) tem de ir como "D" (Debito), nunca "C" fixo - o
		# proprio WSDL da AT usa a mesma convencao SalesInvoices do SAF-T.
		line_summary.append({
			"TaxPointDate": doc.posting_date,
			"DebitCreditIndicator": item.debit_credit,
			"Amount": flt(item.amount),
			"Tax": {
				"TaxType": "IVA",
				"TaxCountryRegion": "PT",
				"TaxCode": item.tax_code,
				"TaxPercentage": flt(item.tax_percentage),
			},
		})

	invoice_data = {
		"InvoiceNo": invoice.invoice_no,
		"ATCUD": doc.atcud_code or "",
		"InvoiceDate": doc.posting_date,
		# InvoiceType real (FT/NC), ver invoice.invoice_type -
		# calculado em SAFTGenerator a partir da serie realmente usada
		# pelo documento (Portugal Series Configuration.document_code),
		# nao um literal fixo - uma Nota de Credito emitida na serie NC
		# tinha de ser sempre reportada como "FT" a AT ate esta correcao.
		"InvoiceType": invoice.invoice_type,
		# Mesmo campo real do Customer (at_is_self_billing) usado no
		# SAF-T (ver SAFTGenerator.get_sales_invoices_data) - nao um
		# literal fixo.
		"SelfBillingIndicator": int(bool(invoice.self_billing_indicator)),
		"CustomerTaxID": customer_tax_id,
		"CustomerTaxIDCountry": customer_country,
		"DocumentStatus": {
			"InvoiceStatus": "N",
			"InvoiceStatusDate": get_datetime(doc.posting_date),
		},
		"HashCharacters": hash_characters,
		"CashVATSchemeIndicator": 0,
		"PaperLessIndicator": 0,
		"SystemEntryDate": get_datetime(doc.creation),
		"LineSummary": line_summary,
		"DocumentTotals": {
			"TaxPayable": invoice.tax_payable,
			"NetTotal": invoice.net_total_abs,
			"GrossTotal": invoice.gross_total_abs,
		},
	}
	if invoice.withholding_tax:
		invoice_data["WithholdingTax"] = [
			{"WithholdingTaxDescription": wh.description, "WithholdingTaxAmount": wh.amount}
			for wh in invoice.withholding_tax
		]

	request = {
		"eFaturaMDVersion": "0.0.1",
		"AuditFileVersion": "1.04_01",
		"TaxRegistrationNumber": int(company_doc.tax_id),
		"TaxEntity": "Global",
		"SoftwareCertificateNumber": int(certificate_number),
		"InvoiceData": invoice_data,
	}
	return request


def _write_log(log_name, document_type, document_name, company, status, code=None, message=None,
				payload=None, raw_response=None, bump_retry=False):
	if log_name:
		log = frappe.get_doc("Portugal Invoice Communication Log", log_name)
	else:
		log = frappe.new_doc("Portugal Invoice Communication Log")
		log.document_type = document_type
		log.document_name = document_name
		log.company = company

	log.status = status
	log.at_response_code = code
	log.at_response_message = message
	log.last_attempt_date = frappe.utils.now()
	if payload is not None:
		log.request_payload = json.dumps(payload, default=str, indent=2, ensure_ascii=False)
	if raw_response is not None:
		log.raw_response = raw_response
	if bump_retry:
		log.retry_count = (log.retry_count or 0) + 1
		if log.retry_count < 8:
			delay_minutes = min(2 ** log.retry_count, 240)
			log.next_retry_date = frappe.utils.add_to_date(frappe.utils.now(), minutes=delay_minutes)
		else:
			log.next_retry_date = None

	if log.is_new():
		log.insert(ignore_permissions=True)
	else:
		log.save(ignore_permissions=True)
	frappe.db.commit()
	return log


def register_invoice(document_type, document_name, log_name=None):
	"""
	Envia uma fatura ja submetida ao webservice RegisterInvoice da AT.
	Idempotente: se a AT responder "documento duplicado" (-3), trata-se
	como sucesso (a fatura ja esta comunicada), nao como falha.
	"""
	doc = frappe.get_doc(document_type, document_name)
	company = doc.company

	try:
		payload = build_invoice_payload(document_type, document_name)
	except InvoiceWebserviceError as e:
		return _write_log(log_name, document_type, document_name, company, "Failed",
						   message=str(e))

	try:
		service, wsse_header = get_invoice_webservice_client()
	except InvoiceWebserviceError as e:
		return _write_log(log_name, document_type, document_name, company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	try:
		response = service.RegisterInvoice(_soapheaders=[wsse_header], **payload)
	except zeep.exceptions.Fault as e:
		frappe.log_error(f"AT rejeitou RegisterInvoice (SOAP Fault): {str(e)}", "ATInvoiceWebservice")
		return _write_log(log_name, document_type, document_name, company, "Failed",
						   message=str(e), payload=payload, bump_retry=True)
	except Exception as e:
		frappe.log_error(f"Erro ao comunicar com o webservice de faturas: {str(e)}", "ATInvoiceWebservice")
		return _write_log(log_name, document_type, document_name, company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	raw_response = zeep.helpers.serialize_object(response)
	# O WSDL define RegisterInvoiceResponse com um unico filho "Response"
	# (ResponseType) - mas confirmado numa chamada real que o zeep
	# desembrulha automaticamente esse invólucro de um so campo, e o
	# objeto devolvido ja tem CodigoResposta/Mensagem diretamente (sem
	# nivel .Response). Mantido o fallback aninhado por seguranca, caso
	# uma versao futura do zeep ou do WSDL deixe de desembrulhar.
	info = getattr(response, "Response", None) or response
	code = str(getattr(info, "CodigoResposta", "")) if info else ""
	message = getattr(info, "Mensagem", "") if info else ""

	if code in SUCCESS_CODES or code in DUPLICATE_CODES:
		friendly = get_at_error_message(code, message) if code in DUPLICATE_CODES else message
		return _write_log(log_name, document_type, document_name, company, "Success",
						   code=code, message=friendly, payload=payload, raw_response=str(raw_response))

	friendly_msg = get_at_error_message(code, message)
	frappe.log_error(f"AT recusou a fatura {document_name} [{code}]: {friendly_msg}", "ATInvoiceWebservice")
	return _write_log(log_name, document_type, document_name, company, "Failed",
					   code=code, message=friendly_msg, payload=payload,
					   raw_response=str(raw_response), bump_retry=True)


def enqueue_invoice_communication(doc, method=None):
	"""
	Hook de on_submit. So enfileira se o metodo de comunicacao estiver
	definido como "Tempo Real" em Portugal Auth Settings - por omissao
	o modulo continua em modo Offline (SAF-T mensal), sem chamadas de
	rede novas para instalacoes existentes.
	"""
	method_setting = frappe.db.get_single_value(
		"Portugal Auth Settings", "invoice_communication_method"
	)
	if method_setting != "Tempo Real (Webservice)":
		return

	frappe.enqueue(
		"portugal_compliance.utils.at_invoice_webservice.register_invoice",
		queue="short",
		timeout=120,
		document_type=doc.doctype,
		document_name=doc.name,
	)


def change_invoice_status(document_type, document_name, new_status, log_name=None):
	"""
	Comunica uma mudanca de estado (ex: anulacao) de uma fatura ja
	registada na AT, via ChangeInvoiceStatus - reutiliza o mesmo
	InvoiceHeaderType (InvoiceNo/ATCUD/InvoiceType/SelfBillingIndicator/
	CustomerTaxID) ja calculado para RegisterInvoice, ver
	build_invoice_payload. So faz sentido para faturas que tenham sido
	mesmo comunicadas com sucesso via este canal (modo Tempo Real) - uma
	fatura reportada so pelo SAF-T mensal nunca foi registada
	individualmente na AT por aqui, nao ha nada para "mudar de estado".
	"""
	if document_type != "Sales Invoice":
		raise InvoiceWebserviceError(
			_("ChangeInvoiceStatus só está implementado para Sales Invoice, não {0}").format(document_type)
		)

	doc = frappe.get_doc(document_type, document_name)
	company_doc = frappe.get_doc("Company", doc.company)
	generator = SAFTGenerator()

	invoices = generator.get_sales_invoices_data(doc.company, doc.posting_date, doc.posting_date)
	invoice = next((i for i in invoices if i.name == document_name), None)
	if invoice is None:
		raise InvoiceWebserviceError(
			_("Não foi possível reconstruir os dados fiscais de {0} a partir do gerador SAF-T").format(document_name)
		)

	customer_tax_id = doc.tax_id or "999999990"
	customer_address_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": doc.customer, "parenttype": "Address"},
		"parent",
	)
	customer_country_name = (
		frappe.db.get_value("Address", customer_address_name, "country") if customer_address_name else None
	)
	customer_country = generator._country_code(customer_country_name)

	payload = {
		"eFaturaMDVersion": "0.0.1",
		"TaxRegistrationNumber": int(company_doc.tax_id),
		"InvoiceHeader": {
			"InvoiceNo": invoice.invoice_no,
			"ATCUD": doc.atcud_code or "",
			"InvoiceDate": doc.posting_date,
			"InvoiceType": invoice.invoice_type,
			"SelfBillingIndicator": int(bool(invoice.self_billing_indicator)),
			"CustomerTaxID": customer_tax_id,
			"CustomerTaxIDCountry": customer_country,
		},
		"InvoiceStatus": {
			"InvoiceStatus": new_status,
			"InvoiceStatusDate": get_datetime(frappe.utils.now()),
		},
	}

	try:
		service, wsse_header = get_invoice_webservice_client()
	except InvoiceWebserviceError as e:
		return _write_log(log_name, document_type, document_name, doc.company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	try:
		response = service.ChangeInvoiceStatus(_soapheaders=[wsse_header], **payload)
	except zeep.exceptions.Fault as e:
		frappe.log_error(f"AT rejeitou ChangeInvoiceStatus (SOAP Fault): {str(e)}", "ATInvoiceWebservice")
		return _write_log(log_name, document_type, document_name, doc.company, "Failed",
						   message=str(e), payload=payload, bump_retry=True)
	except Exception as e:
		frappe.log_error(f"Erro ao comunicar ChangeInvoiceStatus: {str(e)}", "ATInvoiceWebservice")
		return _write_log(log_name, document_type, document_name, doc.company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	raw_response = zeep.helpers.serialize_object(response)
	info = getattr(response, "Response", None) or response
	code = str(getattr(info, "CodigoResposta", "")) if info else ""
	message = getattr(info, "Mensagem", "") if info else ""

	if code in SUCCESS_CODES:
		return _write_log(log_name, document_type, document_name, doc.company, "Success",
						   code=code, message=message, payload=payload, raw_response=str(raw_response))

	friendly_msg = get_at_error_message(code, message)
	frappe.log_error(f"AT recusou ChangeInvoiceStatus para {document_name} [{code}]: {friendly_msg}",
					  "ATInvoiceWebservice")
	return _write_log(log_name, document_type, document_name, doc.company, "Failed",
					   code=code, message=friendly_msg, payload=payload,
					   raw_response=str(raw_response), bump_retry=True)


def enqueue_invoice_cancellation(doc, method=None):
	"""
	Hook de on_cancel da Sales Invoice. So enfileira ChangeInvoiceStatus
	se a fatura tiver mesmo um registo de sucesso prévio em Portugal
	Invoice Communication Log (foi comunicada via RegisterInvoice) - uma
	fatura em modo Offline (SAF-T mensal) nunca foi individualmente
	registada na AT por webservice, pelo que não há nada a anular por
	este canal (a anulação chega à AT no próximo SAF-T mensal, já com
	InvoiceStatus=A e valores a 0.00 - ver saft_generator.py).
	"""
	was_registered = frappe.db.exists(
		"Portugal Invoice Communication Log",
		{"document_type": doc.doctype, "document_name": doc.name, "status": "Success"},
	)
	if not was_registered:
		return

	frappe.enqueue(
		"portugal_compliance.utils.at_invoice_webservice.change_invoice_status",
		queue="short",
		timeout=120,
		document_type=doc.doctype,
		document_name=doc.name,
		new_status="A",
	)


@frappe.whitelist()
def test_connection():
	"""Testar configuracao do webservice de faturas (mesmo padrao do teste de series)."""
	try:
		get_invoice_webservice_client()
		return {"connected": True, "message": "Configuração válida (mTLS + credenciais AT presentes)."}
	except InvoiceWebserviceError as e:
		return {"connected": False, "error": str(e)}
