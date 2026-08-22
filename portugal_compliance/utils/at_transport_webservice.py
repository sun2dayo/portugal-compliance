# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Cliente do webservice de Comunicacao de Documentos de Transporte da AT
(envioDocumentoTransporte), para Delivery Note. Especificacao de
referencia: "Manual de Integracao de Software - Comunicacao dos
Documentos de Transporte a AT" (AT, atualizado 08-04-2026) e o WSDL
oficial (wsdl/documentosTransporte.wsdl), cruzados com o cliente do
modulo Dolibarr "complianceportugal" (NovaDX) - que ja tem um teste
real bem-sucedido contra este webservice, com o NIF da propria novadx
(ver logs/last_response_transport.xml no repo de referencia:
ReturnCode=0, ATDocCodeID=1107532032).

Pontos-chave confirmados no WSDL/manual oficial (nao assumidos):
  - Autenticacao: mesmo mTLS + cabecalho WS-Security proprietario
    (AES-128 + RSA) ja usado em at_webservice.py e
    at_invoice_webservice.py - reutilizado tal e qual.
  - Porto de PRODUCAO e 401, nao 701 (701 e so o ambiente de testes) -
    confirmado na seccao 6.6 do manual oficial.
  - Dentro de AddressStructurePT o campo e "Addressdetail" (d
    minusculo) - grafia diferente da usada na prosa do manual e nos
    outros webservices da AT. Confirmado no XSD real E no XML de
    pedido real do modulo de referencia.
  - CustomerTaxID/SupplierTaxID e um xsd:choice - nunca enviar os
    dois.
  - AddressFrom e MovementStartTime sao obrigatorios; MovementEndTime
    e opcional e fica de fora (nao existe um campo fiavel de "hora de
    fim de transporte" nativo no Delivery Note - inventar um valor
    seria pior do que omitir, mesmo criterio ja usado para
    WithholdingTaxType na Fase 2 do SAF-T).
  - O documento e aceite mesmo sem ATCUD (fica so um alerta, codigo 0
    com mensagem de aviso) - mas como a serie GR do Delivery Note ja
    esta comunicada e a gerar ATCUD real (ver document_hooks.py /
    supported_doctypes["Delivery Note"]), enviamo-lo sempre que
    existir.
  - MovementType tem de corresponder ao document_code REAL da serie
    usada (GR, neste sistema - ver Portugal Series Configuration),
    nunca um literal "GT" fixo: o ATCUD fica registado na AT sob essa
    classe de documento, e enviar um MovementType diferente arrisca
    erro de inconsistencia serie/tipo (o mesmo problema que a correcao
    do InvoiceType real ja evitou para Sales Invoice/Nota de Credito).
  - ResponseStatus tem maxOccurs="unbounded" no XSD - o zeep devolve
    sempre uma lista, mesmo havendo uma unica ocorrencia.
"""

import json
import os
import re

import frappe
from frappe import _
from frappe.utils import get_datetime, flt, cint

import zeep

from portugal_compliance.utils.at_webservice import (
	ATWebserviceError,
	_build_mtls_session,
	_build_wsse_security_header,
)
from portugal_compliance.utils.saft_generator import SAFTGenerator

from zeep.transports import Transport


# Confirmado no manual oficial (seccao 4.2, "Documentos de transporte -
# Resposta ao pedido SOAP") e no teste real do modulo de referencia.
SUCCESS_CODES = {"0"}
# -100 nao e erro, e um alerta ("data inicio de transporte e inferior
# a data atual, pelo que esta informacao sera considerada uma mera
# comunicacao de dados a AT") - tratado como sucesso, nunca como falha.
ALERT_CODES = {"-100"}

AT_ERROR_MESSAGES = {
	"0": "Sucesso",
	"-1": "Parâmetro de entrada inválido",
	"-3": "Já foi inserido um Documento de Transporte com o número fornecido",
	"-4": "Já foi anulado o Documento de Transporte com o número fornecido",
	"-6": "A Data de início de transporte não pode ser anterior à data atual",
	"-7": "O NIF do Remetente não corresponde ao NIF do Header do pedido",
	"-10": "O Remetente não tem atividade registada",
	"-17": "A comunicação de documentos só é permitida até 3 meses após o início do transporte",
	"-18": "O tipo de documento não pode ser alterado",
	"-21": "O documento deve ser comunicado com um máximo de 3 meses de antecedência",
	"-22": "Código ATCUD inválido: não preenchido ou formato inválido",
	"-23": "Código ATCUD inválido: não corresponde a série válida",
	"-24": "Código ATCUD inválido: já se encontra associado a um documento de transporte",
	"-26": "Código ATCUD inválido: código indicado não pertence ao documento",
	"-27": "Código ATCUD inválido: código pertence a uma série interna e reservada da AT",
	"-99": "Erro interno na AT",
	"33": "Pedido SOAP inválido",
	"54": "Sem permissões (WDT) para aceder a esta operação",
}


def get_at_error_message(code, default_msg=""):
	return AT_ERROR_MESSAGES.get(str(code), default_msg or f"Erro desconhecido ({code})")


class TransportWebserviceError(Exception):
	pass


def get_transport_webservice_client():
	"""
	Cliente zeep para o webservice de Documentos de Transporte
	(envioDocumentoTransporte), com mTLS + WS-Security - reutiliza as
	MESMAS credenciais e as MESMAS funcoes de baixo nivel ja usadas nos
	webservices de series e de faturas.
	"""
	settings = frappe.get_single("Portugal Auth Settings")

	cert_path = settings.get("mtls_certificate_path")
	key_path = settings.get("mtls_private_key_path")
	if not cert_path or not key_path:
		raise TransportWebserviceError(
			_("Certificado mTLS não configurado em Portugal Auth Settings.")
		)

	at_public_cert_path = settings.get("at_public_certificate_path")
	if not at_public_cert_path:
		raise TransportWebserviceError(
			_("Certificado público da AT não configurado em Portugal Auth Settings.")
		)

	at_username = settings.get("at_username")
	at_password = settings.get_password("at_password", raise_exception=False)
	if not at_username or not at_password:
		raise TransportWebserviceError(
			_("Credenciais do webservice da AT não configuradas em Portugal Auth Settings.")
		)

	# Confirmado no manual oficial (seccao 6.6): 701 so em testes,
	# producao e 401 - sem porta comum aos dois ambientes.
	sandbox_mode = settings.get("sandbox_mode")
	if sandbox_mode is None:
		sandbox_mode = 1
	port = "701" if int(sandbox_mode) else "401"
	endpoint = f"https://servicos.portaldasfinancas.gov.pt:{port}/sgdtws/documentosTransporte"

	wsdl_path = os.path.join(
		os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
		"wsdl", "documentosTransporte.wsdl",
	)
	session = _build_mtls_session(cert_path, key_path)
	transport = Transport(session=session, timeout=60)
	client = zeep.Client(wsdl=wsdl_path, transport=transport)

	binding_name = list(client.wsdl.bindings.keys())[0]
	service = client.create_service(binding_name, endpoint)

	header = _build_wsse_security_header(at_username, at_password, at_public_cert_path)
	return service, header


def _document_code_for(naming_series):
	"""
	Codigo real do tipo de documento (GR/GT/...) a partir da serie
	realmente usada (Portugal Series Configuration.document_code) -
	mesmo padrao ja usado em SAFTGenerator._document_code_for para
	Sales Invoice (FT/NC). Fallback "GR" (Guia de Remessa), o unico
	tipo com serie provisionada e comunicada neste sistema ate agora.
	"""
	code = frappe.db.get_value(
		"Portugal Series Configuration", {"naming_series": naming_series}, "document_code"
	)
	return code or "GR"


def _format_document_no(document_name, sequence_number, doc_code):
	"""Formato "CODIGO SERIE/NUMERO" (ex: "GR GR2026N/2") - mesma logica de
	SAFTGenerator._format_invoice_no, reutilizada aqui via instancia
	descartavel (metodo puro, sem estado de fatura)."""
	return SAFTGenerator()._format_invoice_no(document_name, sequence_number, doc_code=doc_code)


def _address_from_name(address_name):
	"""
	Morada no formato AddressStructurePT do XSD de Transportes -
	atencao a "Addressdetail" com "d" minusculo (diferente da grafia
	"AddressDetail" usada nos outros webservices da AT e na prosa do
	proprio manual). Fallback "Desconhecido" quando o ERPNext nao tem o
	dado preenchido, para nunca violar o minLength=1 do XSD.
	"""
	if not address_name:
		return None
	addr = frappe.db.get_value(
		"Address", address_name,
		["address_line1", "address_line2", "city", "pincode"], as_dict=True,
	)
	if not addr:
		return None
	detail = ((addr.address_line1 or "") + " " + (addr.address_line2 or "")).strip()
	return {
		"Addressdetail": (detail or "Desconhecido")[:210],
		"City": (addr.city or "Desconhecido")[:50],
		"PostalCode": _format_pt_postal_code(addr.pincode),
		"Country": "PT",
	}


def _format_pt_postal_code(pincode):
	"""
	O tipo PostalCodePT do XSD exige rigorosamente NNNN-NNN - e o
	proprio Country do endereco e "fixed=PT" no XSD (o webservice de
	Transportes so aceita moradas nacionais, ao contrario do SAF-T).
	Um pincode estrangeiro (ex: morada de um cliente em Sao Tome, "9044")
	ou mal formatado rejeitaria o pedido inteiro do lado do zeep antes
	de sequer chegar a AT - normaliza para o formato exigido, com
	"0000-000" como ultimo recurso, tal como o modulo de referencia
	(Dolibarr) ja fazia para o mesmo webservice.
	"""
	digits = re.sub(r"\D", "", pincode or "")
	if re.match(r"^\d{4}-\d{3}$", pincode or ""):
		return pincode
	if len(digits) == 7:
		return f"{digits[:4]}-{digits[4:]}"
	if len(digits) == 4:
		return f"{digits}-000"
	return "0000-000"


def build_transport_payload(document_type, document_name):
	"""
	Constroi o dict envioDocumentoTransporteRequestElem (StockMovement)
	para uma unica Delivery Note.
	"""
	if document_type != "Delivery Note":
		raise TransportWebserviceError(
			_("Comunicação de documentos de transporte só está implementada para Delivery Note, não {0}").format(
				document_type
			)
		)

	doc = frappe.get_doc(document_type, document_name)
	if doc.docstatus != 1:
		raise TransportWebserviceError(_("Documento {0} não está submetido").format(document_name))

	company_doc = frappe.get_doc("Company", doc.company)
	company_address_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Company", "link_name": doc.company, "parenttype": "Address"},
		"parent",
	)
	company_address = _address_from_name(company_address_name) or {
		"Addressdetail": "Desconhecido", "City": "Desconhecido",
		"PostalCode": "0000-000", "Country": "PT",
	}

	document_code = _document_code_for(doc.naming_series)

	atcud_log = frappe.db.get_value(
		"ATCUD Log",
		{"document_type": document_type, "document_name": document_name, "generation_status": "Success"},
		"sequence_number",
	)
	document_number = _format_document_no(doc.name, atcud_log, document_code)

	customer_tax_id = doc.tax_id or "999999990"
	customer_name = (doc.customer_name or doc.customer or "")[:100]

	# AddressFrom (Local de Carga): endereco de despacho, se definido,
	# senao a morada da propria empresa - mesmo criterio do modulo de
	# referencia (armazem -> fallback morada da empresa).
	address_from = (
		_address_from_name(getattr(doc, "dispatch_address_name", None))
		or _address_from_name(doc.company_address)
		or company_address
	)
	address_to = _address_from_name(doc.shipping_address_name) or _address_from_name(doc.customer_address)
	customer_address = _address_from_name(doc.customer_address)

	# MovementStartTime e obrigatorio no XSD - se o campo dedicado
	# (at_data_hora_inicio_transporte) nao foi preenchido, usar
	# data/hora de emissao do documento como fallback, nunca deixar em
	# branco.
	start_time = getattr(doc, "at_data_hora_inicio_transporte", None)
	if not start_time:
		start_time = get_datetime(f"{doc.posting_date} {doc.posting_time or '00:00:00'}")
	else:
		start_time = get_datetime(start_time)

	lines = []
	for item in doc.items:
		lines.append({
			"ProductDescription": (item.item_name or item.item_code)[:200],
			"Quantity": flt(item.qty),
			"UnitOfMeasure": (item.uom or "Un")[:20],
			# Documento sem valor fiscal - preco unitario 0.00 quando
			# nao valorizado, conforme secao 4.2 do manual oficial.
			"UnitPrice": flt(item.rate or 0),
		})

	payload = {
		"TaxRegistrationNumber": int(re.sub(r"\D", "", company_doc.tax_id or "0") or 0),
		"CompanyName": (company_doc.company_name or company_doc.name)[:100],
		"CompanyAddress": company_address,
		"DocumentNumber": document_number,
		"MovementStatus": "N",
		"MovementDate": doc.posting_date,
		"MovementType": document_code,
		"CustomerTaxID": customer_tax_id,
		"AddressFrom": address_from,
		"MovementStartTime": start_time,
		"Line": lines,
	}
	if doc.atcud_code:
		payload["ATCUD"] = doc.atcud_code
	if customer_address:
		payload["CustomerAddress"] = customer_address
	if customer_name:
		payload["CustomerName"] = customer_name
	if address_to:
		payload["AddressTo"] = address_to
	if getattr(doc, "vehicle_no", None):
		payload["VehicleID"] = doc.vehicle_no[:32]

	return payload


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


def register_transport_document(document_type, document_name, log_name=None):
	"""
	Envia uma Delivery Note ja submetida ao webservice
	envioDocumentoTransporte da AT. Idempotente: se a AT responder
	"documento ja registado" (-3), trata-se como sucesso.
	"""
	doc = frappe.get_doc(document_type, document_name)
	company = doc.company

	try:
		payload = build_transport_payload(document_type, document_name)
	except TransportWebserviceError as e:
		return _write_log(log_name, document_type, document_name, company, "Failed",
						   message=str(e))

	try:
		service, wsse_header = get_transport_webservice_client()
	except TransportWebserviceError as e:
		return _write_log(log_name, document_type, document_name, company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	try:
		response = service.envioDocumentoTransporte(_soapheaders=[wsse_header], **payload)
	except zeep.exceptions.Fault as e:
		frappe.log_error(f"AT rejeitou envioDocumentoTransporte (SOAP Fault): {str(e)}", "ATTransportWebservice")
		return _write_log(log_name, document_type, document_name, company, "Failed",
						   message=str(e), payload=payload, bump_retry=True)
	except Exception as e:
		frappe.log_error(f"Erro ao comunicar com o webservice de transportes: {str(e)}", "ATTransportWebservice")
		return _write_log(log_name, document_type, document_name, company, "Retrying",
						   message=str(e), payload=payload, bump_retry=True)

	raw_response = zeep.helpers.serialize_object(response)

	# ResponseStatus tem maxOccurs="unbounded" no XSD - o zeep devolve
	# sempre uma lista (confirmado na estrutura do WSDL, secao
	# StockMovementResponse), mesmo havendo uma unica ocorrencia real.
	status_list = getattr(response, "ResponseStatus", None) or []
	first_status = status_list[0] if status_list else None
	code = str(getattr(first_status, "ReturnCode", "")) if first_status else ""
	message = getattr(first_status, "ReturnMessage", "") or ""
	at_doc_code_id = getattr(response, "ATDocCodeID", None)

	if code in SUCCESS_CODES or code in ALERT_CODES:
		if at_doc_code_id:
			doc.db_set("at_codigo_transporte", at_doc_code_id, update_modified=False)
		friendly = message or get_at_error_message(code)
		return _write_log(log_name, document_type, document_name, company, "Success",
						   code=code, message=friendly, payload=payload, raw_response=str(raw_response))

	friendly_msg = get_at_error_message(code, message)
	frappe.log_error(f"AT recusou a guia {document_name} [{code}]: {friendly_msg}", "ATTransportWebservice")
	return _write_log(log_name, document_type, document_name, company, "Failed",
					   code=code, message=friendly_msg, payload=payload,
					   raw_response=str(raw_response), bump_retry=True)


def enqueue_transport_communication(doc, method=None):
	"""
	Hook de on_submit da Delivery Note. So enfileira se
	transport_communication_method estiver definido como "Tempo Real"
	em Portugal Auth Settings (por omissao ativo - ao contrario do
	toggle de faturas, aqui nao existe ainda um canal SAF-T de
	documentos de transporte implementado neste modulo, pelo que o
	webservice e a unica via de comunicacao automatica disponivel).
	"""
	method_setting = frappe.db.get_single_value(
		"Portugal Auth Settings", "transport_communication_method"
	)
	if method_setting == "Desativado":
		return

	frappe.enqueue(
		"portugal_compliance.utils.at_transport_webservice.register_transport_document",
		queue="short",
		timeout=120,
		document_type=doc.doctype,
		document_name=doc.name,
	)


@frappe.whitelist()
def test_connection():
	"""Testar configuracao do webservice de transportes (mesmo padrao do teste de faturas/series)."""
	try:
		get_transport_webservice_client()
		return {"connected": True, "message": "Configuração válida (mTLS + credenciais AT presentes)."}
	except TransportWebserviceError as e:
		return {"connected": False, "error": str(e)}
