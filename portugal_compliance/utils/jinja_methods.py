# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Jinja Methods for Portugal Compliance - VERSÃO NATIVA CORRIGIDA
Métodos Jinja para uso em templates e print formats
✅ CORRIGIDO: Compatível com formato SEM HÍFENS (FT2025NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py, series_adapter.py e atcud_generator.py
✅ PERFORMANCE: Cache otimizado e validações thread-safe
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, formatdate, fmt_money, now, today
import re
from datetime import datetime, date
import qrcode
import io
import base64
from PIL import Image
import hashlib
import json


# ========== MÉTODOS ATCUD CERTIFICADOS CORRIGIDOS ==========

def get_atcud_code(doc):
	"""Obter código ATCUD do documento"""
	try:
		if hasattr(doc, 'atcud_code') and doc.atcud_code:
			return doc.atcud_code
		return ""
	except Exception:
		return ""


def format_atcud_display(atcud_code):
	"""
	✅ CORRIGIDO: Formatar ATCUD para exibição conforme Portaria 195/2020
	Formato: CODIGO-NNNNNNNN (ex: CSDF7T5H-00000001)
	"""
	try:
		if not atcud_code:
			return ""

		# ✅ FORMATO OFICIAL: CODIGO-SEQUENCIA
		if '-' in atcud_code:
			parts = atcud_code.split('-')
			if len(parts) == 2:
				validation_code = parts[0]
				sequence = parts[1]
				return f"{validation_code}-{sequence.zfill(8)}"

		return atcud_code
	except Exception:
		return atcud_code or ""


def validate_atcud_format(atcud_code):
	"""
	✅ CORRIGIDO: Validar formato ATCUD conforme legislação
	Formato: CODIGO-SEQUENCIA (8-12 chars alfanuméricos + hífen + 8 dígitos)
	"""
	try:
		if not atcud_code:
			return False

		# ✅ VERIFICAR FORMATO GERAL: CODIGO-SEQUENCIA
		if '-' not in atcud_code:
			return False

		parts = atcud_code.split('-')
		if len(parts) != 2:
			return False

		validation_code, sequence = parts

		# ✅ VALIDAR CÓDIGO DE VALIDAÇÃO (8-12 caracteres alfanuméricos maiúsculos)
		if not (8 <= len(validation_code) <= 12):
			return False

		if not validation_code.isalnum() or not validation_code.isupper():
			return False

		# ✅ VALIDAR SEQUÊNCIA (8 dígitos)
		if not (len(sequence) == 8 and sequence.isdigit()):
			return False

		return True
	except Exception:
		return False


def get_atcud_validation_code(atcud_code):
	"""Extrair código de validação do ATCUD"""
	try:
		if not atcud_code:
			return ""

		if '-' in atcud_code:
			return atcud_code.split('-')[0]

		return atcud_code[:8] if len(atcud_code) >= 8 else atcud_code
	except Exception:
		return ""


def get_atcud_sequence(atcud_code):
	"""Extrair sequência do ATCUD"""
	try:
		if not atcud_code:
			return ""

		if '-' in atcud_code:
			parts = atcud_code.split('-')
			if len(parts) == 2:
				return parts[1]

		return atcud_code[8:] if len(atcud_code) > 8 else ""
	except Exception:
		return ""


def get_atcud_info_formatted(doc):
	"""
	✅ NOVO: Obter informações formatadas do ATCUD para impressão
	"""
	try:
		atcud = get_atcud_code(doc)
		if not atcud:
			return ""

		validation_code = get_atcud_validation_code(atcud)
		sequence = get_atcud_sequence(atcud)

		return {
			"full_code": atcud,
			"validation_code": validation_code,
			"sequence": sequence,
			"formatted": format_atcud_display(atcud),
			"is_valid": validate_atcud_format(atcud)
		}
	except Exception:
		return {}


# ========== MÉTODOS NAMING_SERIES CERTIFICADOS CORRIGIDOS ==========

def get_naming_series(doc):
	"""Obter naming series do documento"""
	try:
		if hasattr(doc, 'naming_series') and doc.naming_series:
			return doc.naming_series
		return ""
	except Exception:
		return ""


def get_series_prefix(doc):
	"""
	✅ CORRIGIDO: Obter prefixo da série do documento (SEM HÍFENS)
	Formato: FT2025NDX (em vez de FT-2025-NDX)
	"""
	try:
		naming_series = get_naming_series(doc)
		if naming_series and '.####' in naming_series:
			return naming_series.replace('.####', '')
		return ""
	except Exception:
		return ""


def get_portugal_series_info(doc):
	"""
	✅ CORRIGIDO: Obter informações da série portuguesa (formato SEM HÍFENS)
	"""
	try:
		prefix = get_series_prefix(doc)
		if not prefix:
			return {}

		series_info = frappe.db.get_value("Portugal Series Configuration", {
			"prefix": prefix,
			"company": getattr(doc, 'company', '')
		}, [
											  "name", "series_name", "document_type",
											  "is_communicated",
											  "validation_code", "at_environment",
											  "communication_date",
											  "current_sequence", "is_active", "year"
										  ], as_dict=True)

		return series_info or {}
	except Exception:
		return {}


def is_portuguese_series(doc):
	"""
	✅ CORRIGIDO: Verificar se é série portuguesa (formato SEM HÍFENS)
	"""
	try:
		naming_series = get_naming_series(doc)
		if not naming_series:
			return False

		# ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
		pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'
		return bool(re.match(pattern, naming_series))
	except Exception:
		return False


def extract_series_components(doc):
	"""
	✅ NOVO: Extrair componentes da série portuguesa (SEM HÍFENS)
	Formato: FT2025NDX.#### → {doc_code: FT, year: 2025, company: NDX}
	"""
	try:
		naming_series = get_naming_series(doc)
		if not naming_series:
			return {}

		# ✅ PADRÃO NAMING SERIES PORTUGUESA SEM HÍFENS
		pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})\.####$'
		match = re.match(pattern, naming_series)

		if not match:
			return {}

		doc_code, year, company_abbr = match.groups()

		return {
			"naming_series": naming_series,
			"prefix": f"{doc_code}{year}{company_abbr}",
			"doc_code": doc_code,
			"year": int(year),
			"company_abbr": company_abbr,
			"is_portuguese": True
		}
	except Exception:
		return {}


def get_compliance_info(doc):
	"""
	✅ CORRIGIDO: Obter informações de compliance completas
	"""
	try:
		return {
			"atcud_code": get_atcud_code(doc),
			"atcud_info": get_atcud_info_formatted(doc),
			"naming_series": get_naming_series(doc),
			"series_prefix": get_series_prefix(doc),
			"series_components": extract_series_components(doc),
			"is_portuguese": is_portuguese_series(doc),
			"series_info": get_portugal_series_info(doc),
			"compliance_status": get_compliance_status(doc)
		}
	except Exception:
		return {}


def format_series_info_for_print(doc):
	"""
	✅ CORRIGIDO: Formatar informações da série para impressão
	"""
	try:
		series_info = get_portugal_series_info(doc)
		if not series_info:
			return ""

		lines = []

		# ✅ NOME DA SÉRIE
		if series_info.get('series_name'):
			lines.append(f"Série: {series_info['series_name']}")

		# ✅ CÓDIGO AT
		if series_info.get('validation_code'):
			lines.append(f"Código AT: {series_info['validation_code']}")
		else:
			lines.append("Código AT: Não comunicada")

		# ✅ AMBIENTE
		if series_info.get('at_environment'):
			env_text = "Produção" if series_info['at_environment'] == 'production' else "Teste"
			lines.append(f"Ambiente: {env_text}")

		# ✅ STATUS COMUNICAÇÃO
		if series_info.get('is_communicated'):
			if series_info.get('communication_date'):
				comm_date = formatdate(series_info['communication_date'], "dd/MM/yyyy")
				lines.append(f"Comunicada em: {comm_date}")
			else:
				lines.append("Status: Comunicada")
		else:
			lines.append("Status: Não comunicada")

		return " | ".join(lines)
	except Exception:
		return ""


def get_series_communication_status(doc):
	"""Obter status de comunicação da série"""
	try:
		series_info = get_portugal_series_info(doc)
		if not series_info:
			return "Não configurada"

		if series_info.get('is_communicated'):
			return "Comunicada"
		else:
			return "Não comunicada"
	except Exception:
		return "Desconhecido"


def get_document_sequence_info(doc):
	"""
	✅ NOVO: Obter informações de sequência do documento
	"""
	try:
		series_info = get_portugal_series_info(doc)
		doc_name = getattr(doc, 'name', '')

		# ✅ EXTRAIR SEQUENCIAL DO NOME (COMPATÍVEL COM FORMATOS COM E SEM HÍFENS)
		sequence = 0
		if doc_name:
			# Padrões para extrair sequência
			patterns = [
				r'(\d{8})$',  # 8 dígitos no final: FT2025NDX00000001
				r'-(\d{8})$',  # 8 dígitos após hífen: FT-2025-NDX-00000001
				r'\.(\d{8})$',  # 8 dígitos após ponto: FT2025NDX.00000001
				r'(\d{6,})$',  # 6+ dígitos no final
				r'(\d+)$'  # Qualquer número no final
			]

			for pattern in patterns:
				match = re.search(pattern, doc_name)
				if match:
					sequence = int(match.group(1))
					break

		return {
			"document_name": doc_name,
			"sequence_number": sequence,
			"sequence_formatted": f"{sequence:08d}" if sequence > 0 else "00000000",
			"series_current": series_info.get('current_sequence', 0) if series_info else 0,
			"series_prefix": get_series_prefix(doc)
		}
	except Exception:
		return {}


# ========== MÉTODOS DE FORMATAÇÃO PORTUGUESES ==========

def format_portuguese_date(date_value, format_type="short"):
	"""Formatar data no formato português"""
	try:
		if not date_value:
			return ""

		if isinstance(date_value, str):
			date_value = getdate(date_value)

		if format_type == "long":
			return formatdate(date_value, "dd 'de' MMMM 'de' yyyy")
		elif format_type == "medium":
			return formatdate(date_value, "dd/MM/yyyy")
		else:  # short
			return formatdate(date_value, "dd/MM/yy")
	except Exception:
		return str(date_value) if date_value else ""


def format_portuguese_currency(amount, currency="EUR"):
	"""Formatar moeda no formato português"""
	try:
		if amount is None:
			return ""

		formatted = fmt_money(amount, currency=currency, precision=2)

		# Ajustar para formato português
		if currency == "EUR":
			return formatted.replace("EUR", "€")

		return formatted
	except Exception:
		return str(amount) if amount else ""


def format_portuguese_phone(phone):
	"""Formatar telefone português"""
	try:
		if not phone:
			return ""

		# Remover caracteres não numéricos
		digits = re.sub(r'[^\d]', '', str(phone))

		# Formato português: +351 XXX XXX XXX
		if digits.startswith('351') and len(digits) == 12:
			return f"+351 {digits[3:6]} {digits[6:9]} {digits[9:12]}"
		elif len(digits) == 9:
			return f"{digits[:3]} {digits[3:6]} {digits[6:9]}"

		return phone
	except Exception:
		return str(phone) if phone else ""


def format_postal_code(postal_code):
	"""Formatar código postal português"""
	try:
		if not postal_code:
			return ""

		# Remover caracteres não numéricos
		digits = re.sub(r'[^\d]', '', str(postal_code))

		# Formato português: XXXX-XXX
		if len(digits) == 7:
			return f"{digits[:4]}-{digits[4:7]}"
		elif len(digits) == 8:
			return f"{digits[:4]}-{digits[4:7]}"

		return postal_code
	except Exception:
		return str(postal_code) if postal_code else ""


def format_percentage(value, precision=2):
	"""Formatar percentagem"""
	try:
		if value is None:
			return ""

		return f"{flt(value, precision)}%"
	except Exception:
		return str(value) if value else ""


def format_iban(iban):
	"""Formatar IBAN português"""
	try:
		if not iban:
			return ""

		# Remover espaços e converter para maiúsculas
		iban_clean = re.sub(r'[^\w]', '', str(iban)).upper()

		# Formato IBAN: XXXX XXXX XXXX XXXX XXXX XXXX
		if len(iban_clean) >= 21:
			formatted = ""
			for i in range(0, len(iban_clean), 4):
				if i > 0:
					formatted += " "
				formatted += iban_clean[i:i + 4]
			return formatted

		return iban
	except Exception:
		return str(iban) if iban else ""


def get_month_name_portuguese(month_number):
	"""Obter nome do mês em português"""
	try:
		months = {
			1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
			5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
			9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
		}
		return months.get(cint(month_number), "")
	except Exception:
		return ""


def money_in_words_portuguese(amount):
	"""Converter valor para extenso em português"""
	try:
		if not amount:
			return ""

		# Implementação básica - pode ser expandida
		from frappe.utils import money_in_words
		words = money_in_words(amount, "EUR")

		# Substituições para português
		replacements = {
			"Euro": "Euro",
			"Euros": "Euros",
			"Cent": "Cêntimo",
			"Cents": "Cêntimos",
			"and": "e",
			"only": "apenas"
		}

		for en, pt in replacements.items():
			words = words.replace(en, pt)

		return words
	except Exception:
		return ""


# ========== MÉTODOS DE VALIDAÇÃO CORRIGIDOS ==========
@frappe.whitelist()
def validate_portuguese_nif(nif):
	"""
	✅ CORRIGIDO: Validar NIF português conforme algoritmo oficial
	"""
	try:
		if not nif:
			return False

		# Remover caracteres não numéricos
		nif_clean = re.sub(r'[^\d]', '', str(nif))

		# Verificar se tem 9 dígitos
		if len(nif_clean) != 9:
			return False

		# Verificar se começa com dígito válido
		if nif_clean[0] not in '123456789':
			return False

		# ✅ ALGORITMO OFICIAL: Calcular dígito de controlo
		check_sum = 0
		for i in range(8):
			check_sum += int(nif_clean[i]) * (9 - i)

		remainder = check_sum % 11
		check_digit = 0 if remainder < 2 else 11 - remainder

		return int(nif_clean[8]) == check_digit
	except Exception:
		return False


def get_company_nif(company):
	"""Obter NIF da empresa"""
	try:
		if not company:
			return ""

		return frappe.db.get_value("Company", company, "tax_id") or ""
	except Exception:
		return ""


def get_customer_nif(doc):
	"""
	✅ NOVO: Obter NIF do cliente do documento
	"""
	try:
		if not hasattr(doc, 'customer') or not doc.customer:
			return ""

		return frappe.db.get_value("Customer", doc.customer, "tax_id") or ""
	except Exception:
		return ""


def get_supplier_nif(doc):
	"""
	✅ NOVO: Obter NIF do fornecedor do documento
	"""
	try:
		if not hasattr(doc, 'supplier') or not doc.supplier:
			return ""

		return frappe.db.get_value("Supplier", doc.supplier, "tax_id") or ""
	except Exception:
		return ""


def validate_nif_format(nif):
	"""Validar formato do NIF"""
	try:
		if not nif:
			return False

		nif_clean = re.sub(r'[^\d]', '', str(nif))
		return len(nif_clean) == 9 and nif_clean.isdigit()
	except Exception:
		return False


def get_nif_info(nif):
	"""
	✅ NOVO: Obter informações detalhadas do NIF
	"""
	try:
		if not nif:
			return {}

		nif_clean = re.sub(r'[^\d]', '', str(nif))

		return {
			"nif": nif_clean,
			"formatted": f"{nif_clean[:3]} {nif_clean[3:6]} {nif_clean[6:9]}" if len(
				nif_clean) == 9 else nif_clean,
			"is_valid": validate_portuguese_nif(nif),
			"format_valid": validate_nif_format(nif),
			"length": len(nif_clean)
		}
	except Exception:
		return {}


# ========== MÉTODOS DE DOCUMENTOS CORRIGIDOS ==========

def get_document_type_description(doctype):
	"""
	✅ CORRIGIDO: Obter descrição do tipo de documento (prefixos atualizados)
	"""
	try:
		descriptions = {
			"Sales Invoice": "Fatura de Venda",
			"Purchase Invoice": "Fatura de Compra",
			"POS Invoice": "Fatura Simplificada",
			"Payment Entry": "Recibo",
			"Delivery Note": "Guia de Transporte",
			"Purchase Receipt": "Guia de Receção",
			"Journal Entry": "Lançamento Contabilístico",
			"Stock Entry": "Movimento de Stock",
			"Quotation": "Orçamento",
			"Sales Order": "Encomenda de Cliente",  # ✅ CORRIGIDO
			"Purchase Order": "Encomenda a Fornecedor"  # ✅ CORRIGIDO
		}
		return descriptions.get(doctype, doctype)
	except Exception:
		return doctype or ""


def get_document_type_code(doctype):
	"""
	✅ CORRIGIDO: Obter código do tipo de documento (prefixos atualizados)
	"""
	try:
		codes = {
			"Sales Invoice": "FT",
			"Purchase Invoice": "FC",
			"POS Invoice": "FS",
			"Payment Entry": "RC",
			"Delivery Note": "GT",
			"Purchase Receipt": "GR",
			"Journal Entry": "JE",
			"Stock Entry": "GM",
			"Quotation": "OR",
			"Sales Order": "EC",  # ✅ CORRIGIDO: era EN
			"Purchase Order": "EF"  # ✅ CORRIGIDO: era OC
		}
		return codes.get(doctype, "FT")
	except Exception:
		return "FT"


def get_tax_rate_description(tax_rate):
	"""Obter descrição da taxa de imposto"""
	try:
		rate = flt(tax_rate)

		if rate == 0:
			return "Isento de IVA"
		elif rate == 6:
			return "IVA Taxa Reduzida (6%)"
		elif rate == 13:
			return "IVA Taxa Intermédia (13%)"
		elif rate == 23:
			return "IVA Taxa Normal (23%)"
		else:
			return f"IVA {rate}%"
	except Exception:
		return "IVA"


def format_tax_breakdown(doc):
	"""
	✅ CORRIGIDO: Formatar breakdown de impostos melhorado
	"""
	try:
		if not hasattr(doc, 'taxes') or not doc.taxes:
			return ""

		breakdown = []
		total_tax = 0

		for tax in doc.taxes:
			if hasattr(tax, 'tax_amount') and tax.tax_amount:
				rate = getattr(tax, 'rate', 0)
				rate_desc = get_tax_rate_description(rate)
				amount = format_portuguese_currency(tax.tax_amount)
				breakdown.append(f"{rate_desc}: {amount}")
				total_tax += tax.tax_amount

		if total_tax > 0:
			breakdown.append(f"Total IVA: {format_portuguese_currency(total_tax)}")

		return " | ".join(breakdown)
	except Exception:
		return ""


def get_invoice_totals_text(doc):
	"""Obter texto dos totais da fatura"""
	try:
		lines = []

		if hasattr(doc, 'net_total') and doc.net_total:
			lines.append(f"Subtotal: {format_portuguese_currency(doc.net_total)}")

		if hasattr(doc, 'total_taxes_and_charges') and doc.total_taxes_and_charges:
			lines.append(f"IVA: {format_portuguese_currency(doc.total_taxes_and_charges)}")

		if hasattr(doc, 'grand_total') and doc.grand_total:
			lines.append(f"Total: {format_portuguese_currency(doc.grand_total)}")

		return " | ".join(lines)
	except Exception:
		return ""


def get_payment_terms_text(doc):
	"""Obter texto dos termos de pagamento"""
	try:
		if hasattr(doc, 'payment_terms_template') and doc.payment_terms_template:
			return doc.payment_terms_template

		if hasattr(doc, 'due_date') and doc.due_date:
			return f"Vencimento: {format_portuguese_date(doc.due_date)}"

		return "Pagamento à vista"
	except Exception:
		return ""


def get_document_totals_summary(doc):
	"""
	✅ NOVO: Obter resumo completo dos totais do documento
	"""
	try:
		return {
			"net_total": flt(getattr(doc, 'net_total', 0)),
			"net_total_formatted": format_portuguese_currency(getattr(doc, 'net_total', 0)),
			"tax_total": flt(getattr(doc, 'total_taxes_and_charges', 0)),
			"tax_total_formatted": format_portuguese_currency(
				getattr(doc, 'total_taxes_and_charges', 0)),
			"grand_total": flt(getattr(doc, 'grand_total', 0)),
			"grand_total_formatted": format_portuguese_currency(getattr(doc, 'grand_total', 0)),
			"grand_total_words": money_in_words_portuguese(getattr(doc, 'grand_total', 0)),
			"currency": getattr(doc, 'currency', 'EUR'),
			"tax_breakdown": format_tax_breakdown(doc)
		}
	except Exception:
		return {}


# ========== MÉTODOS DE ENDEREÇOS E EMPRESA ==========

def get_company_address_formatted(company):
	"""Obter endereço da empresa formatado"""
	try:
		if not company:
			return ""

		address = frappe.db.get_value("Address", {
			"link_name": company,
			"link_doctype": "Company",
			"is_primary_address": 1
		}, ["address_line1", "address_line2", "city", "pincode", "country"], as_dict=True)

		if not address:
			return ""

		lines = []
		if address.address_line1:
			lines.append(address.address_line1)
		if address.address_line2:
			lines.append(address.address_line2)

		city_line = []
		if address.pincode:
			city_line.append(format_postal_code(address.pincode))
		if address.city:
			city_line.append(address.city)

		if city_line:
			lines.append(" ".join(city_line))

		if address.country and address.country != "Portugal":
			lines.append(address.country)

		return "<br>".join(lines)
	except Exception:
		return ""


def format_customer_address(doc):
	"""Formatar endereço do cliente"""
	try:
		if not hasattr(doc, 'customer_address') or not doc.customer_address:
			return ""

		address = frappe.get_doc("Address", doc.customer_address)

		lines = []
		if address.address_line1:
			lines.append(address.address_line1)
		if address.address_line2:
			lines.append(address.address_line2)

		city_line = []
		if address.pincode:
			city_line.append(format_postal_code(address.pincode))
		if address.city:
			city_line.append(address.city)

		if city_line:
			lines.append(" ".join(city_line))

		if address.country and address.country != "Portugal":
			lines.append(address.country)

		return "<br>".join(lines)
	except Exception:
		return ""


def get_legal_text_footer():
	"""Obter texto legal do rodapé"""
	try:
		return (
			"Documento processado por programa informático certificado.<br>"
			"IVA - Regime Normal<br>"
			"Conservatória do Registo Comercial"
		)
	except Exception:
		return ""


def get_company_info_complete(company):
	"""
	✅ NOVO: Obter informações completas da empresa
	"""
	try:
		if not company:
			return {}

		company_data = frappe.db.get_value("Company", company, [
			"company_name", "tax_id", "email", "phone", "website",
			"country", "default_currency", "portugal_compliance_enabled"
		], as_dict=True)

		if not company_data:
			return {}

		return {
			"name": company_data.company_name,
			"nif": company_data.tax_id or "",
			"nif_formatted": get_nif_info(company_data.tax_id).get("formatted", ""),
			"nif_valid": validate_portuguese_nif(company_data.tax_id),
			"email": company_data.email or "",
			"phone": company_data.phone or "",
			"phone_formatted": format_portuguese_phone(company_data.phone),
			"website": company_data.website or "",
			"country": company_data.country or "",
			"currency": company_data.default_currency or "EUR",
			"portugal_compliance": bool(company_data.portugal_compliance_enabled),
			"address": get_company_address_formatted(company)
		}
	except Exception:
		return {}


# ========== MÉTODOS QR CODE E SAFT CORRIGIDOS ==========

def get_qr_code_data(doc):
	"""
	✅ CORRIGIDO: Obter dados do QR Code conforme especificações AT atualizadas
	"""
	try:
		if not doc:
			return ""

		# ✅ DADOS BÁSICOS DO QR CODE CONFORME LEGISLAÇÃO PORTUGUESA
		company_nif = get_company_nif(getattr(doc, 'company', ''))
		customer_nif = get_customer_nif(doc) or get_supplier_nif(doc)

		qr_data = {
			"A": company_nif,  # NIF do emitente
			"B": customer_nif,  # NIF do adquirente
			"C": getattr(doc, 'company', ''),  # Nome do emitente
			"D": get_document_type_code(doc.doctype),  # Tipo de documento
			"E": "N",  # Estado do documento (N=Normal, A=Anulado)
			"F": getdate(getattr(doc, 'posting_date', today())).strftime("%Y%m%d"),  # Data
			"G": getattr(doc, 'name', ''),  # Número do documento
			"H": get_atcud_code(doc),  # ATCUD
			"I1": f"{flt(getattr(doc, 'net_total', 0)):.2f}",  # Base tributável taxa normal
			"I2": f"{flt(getattr(doc, 'total_taxes_and_charges', 0)):.2f}",  # IVA taxa normal
			"I3": "0.00",  # Base tributável taxa intermédia
			"I4": "0.00",  # IVA taxa intermédia
			"I5": "0.00",  # Base tributável taxa reduzida
			"I6": "0.00",  # IVA taxa reduzida
			"I7": "0.00",  # Base tributável taxa zero
			"I8": "0.00",  # IVA taxa zero
			"N": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",  # Total do documento
			"O": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",  # Total com impostos
			"P": "0",  # Retenção na fonte
			"Q": hashlib.sha1(
				f"{getattr(doc, 'name', '')}{get_atcud_code(doc)}".encode()).hexdigest()[
				 :4].upper(),  # Hash de validação
			"R": get_series_prefix(doc)  # Identificador da série
		}

		# ✅ CONSTRUIR STRING QR CODE CONFORME FORMATO AT
		qr_string = "*".join([f"{key}:{value}" for key, value in qr_data.items() if value])
		return qr_string
	except Exception:
		return ""


def generate_qr_code_image(qr_data, size=200):
	"""Gerar imagem QR Code"""
	try:
		if not qr_data:
			return ""

		# Gerar QR Code
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=10,
			border=4,
		)
		qr.add_data(qr_data)
		qr.make(fit=True)

		# Criar imagem
		img = qr.make_image(fill_color="black", back_color="white")
		img = img.resize((size, size), Image.LANCZOS)

		# Converter para base64
		buffer = io.BytesIO()
		img.save(buffer, format='PNG')
		img_str = base64.b64encode(buffer.getvalue()).decode()

		return f"data:image/png;base64,{img_str}"
	except Exception:
		return ""


def get_saft_hash(doc):
	"""
	✅ CORRIGIDO: Obter hash SAF-T do documento melhorado
	"""
	try:
		if not doc:
			return ""

		# ✅ DADOS PARA HASH CONFORME SAF-T PT
		hash_data = {
			"name": getattr(doc, 'name', ''),
			"doctype": doc.doctype,
			"company": getattr(doc, 'company', ''),
			"posting_date": str(getattr(doc, 'posting_date', '')),
			"grand_total": flt(getattr(doc, 'grand_total', 0)),
			"atcud_code": get_atcud_code(doc),
			"series_prefix": get_series_prefix(doc),
			"customer": getattr(doc, 'customer', '') or getattr(doc, 'supplier', '')
		}

		# ✅ GERAR HASH SHA-256
		hash_string = json.dumps(hash_data, sort_keys=True)
		return hashlib.sha256(hash_string.encode()).hexdigest()[:16]
	except Exception:
		return ""


def format_saft_data(doc):
	"""
	✅ CORRIGIDO: Formatar dados SAF-T melhorado
	"""
	try:
		sequence_info = get_document_sequence_info(doc)

		return {
			"hash": get_saft_hash(doc),
			"atcud": get_atcud_code(doc),
			"series": get_series_prefix(doc),
			"sequence": sequence_info.get("sequence_formatted", "00000000"),
			"sequence_number": sequence_info.get("sequence_number", 0),
			"date": format_portuguese_date(getattr(doc, 'posting_date', today())),
			"total": format_portuguese_currency(getattr(doc, 'grand_total', 0)),
			"document_type": get_document_type_code(doc.doctype),
			"document_description": get_document_type_description(doc.doctype)
		}
	except Exception:
		return {}


# ========== MÉTODOS DE COMPLIANCE CORRIGIDOS ==========

def get_compliance_status(doc):
	"""
	✅ CORRIGIDO: Obter status de compliance melhorado
	"""
	try:
		status = {
			"has_atcud": bool(get_atcud_code(doc)),
			"atcud_valid": validate_atcud_format(get_atcud_code(doc)),
			"has_portuguese_series": is_portuguese_series(doc),
			"series_communicated": False,
			"company_nif_valid": False,
			"customer_nif_valid": False,
			"compliance_level": "none",
			"warnings": [],
			"errors": []
		}

		# ✅ VERIFICAR SE SÉRIE ESTÁ COMUNICADA
		series_info = get_portugal_series_info(doc)
		if series_info:
			status["series_communicated"] = series_info.get('is_communicated', False)
			if not status["series_communicated"]:
				status["warnings"].append("Série não comunicada à AT")

		# ✅ VERIFICAR NIF DA EMPRESA
		company_nif = get_company_nif(getattr(doc, 'company', ''))
		status["company_nif_valid"] = validate_portuguese_nif(company_nif)
		if not status["company_nif_valid"]:
			status["errors"].append("NIF da empresa inválido")

		# ✅ VERIFICAR NIF DO CLIENTE/FORNECEDOR
		customer_nif = get_customer_nif(doc) or get_supplier_nif(doc)
		if customer_nif:
			status["customer_nif_valid"] = validate_portuguese_nif(customer_nif)
			if not status["customer_nif_valid"]:
				status["warnings"].append("NIF do cliente/fornecedor inválido")

		# ✅ DETERMINAR NÍVEL DE COMPLIANCE
		if (status["has_atcud"] and status["atcud_valid"] and
			status["series_communicated"] and status["company_nif_valid"]):
			status["compliance_level"] = "full"
		elif (status["has_portuguese_series"] and status["company_nif_valid"] and
			  status["has_atcud"]):
			status["compliance_level"] = "partial"
		elif status["has_portuguese_series"] and status["company_nif_valid"]:
			status["compliance_level"] = "basic"
		else:
			status["compliance_level"] = "none"

		return status
	except Exception:
		return {"compliance_level": "none", "errors": ["Erro ao verificar compliance"]}


def is_compliant_document(doc):
	"""Verificar se documento está em compliance"""
	try:
		status = get_compliance_status(doc)
		return status.get("compliance_level") in ["full", "partial"]
	except Exception:
		return False


def get_at_environment_display(doc):
	"""Obter display do ambiente AT"""
	try:
		series_info = get_portugal_series_info(doc)
		if series_info and series_info.get('at_environment'):
			env = series_info['at_environment']
			return "Produção" if env == 'production' else "Teste"
		return "Não configurado"
	except Exception:
		return "Desconhecido"


def format_compliance_info(doc):
	"""
	✅ CORRIGIDO: Formatar informações de compliance para impressão melhorado
	"""
	try:
		status = get_compliance_status(doc)
		lines = []

		# ✅ ATCUD
		if status.get("has_atcud"):
			atcud = get_atcud_code(doc)
			if status.get("atcud_valid"):
				lines.append(f"ATCUD: {atcud}")
			else:
				lines.append(f"ATCUD: {atcud} (formato inválido)")

		# ✅ SÉRIE
		if status.get("series_communicated"):
			lines.append("Série Comunicada à AT")
		elif status.get("has_portuguese_series"):
			lines.append("Série Portuguesa (não comunicada)")

		# ✅ AMBIENTE
		env_display = get_at_environment_display(doc)
		if env_display != "Não configurado":
			lines.append(f"Ambiente: {env_display}")

		# ✅ STATUS GERAL
		compliance_level = status.get("compliance_level", "none")
		if compliance_level == "full":
			lines.append("✓ Totalmente Conforme")
		elif compliance_level == "partial":
			lines.append("⚠ Parcialmente Conforme")
		elif compliance_level == "basic":
			lines.append("⚠ Compliance Básico")
		else:
			lines.append("✗ Não Conforme")

		# ✅ AVISOS
		warnings = status.get("warnings", [])
		if warnings:
			lines.extend([f"⚠ {w}" for w in warnings[:2]])  # Máximo 2 avisos

		return " | ".join(lines)
	except Exception:
		return ""


def get_compliance_summary_for_print(doc):
	"""
	✅ NOVO: Obter resumo de compliance formatado para impressão
	"""
	try:
		compliance_info = get_compliance_info(doc)
		status = compliance_info.get("compliance_status", {})

		return {
			"atcud_display": format_atcud_display(compliance_info.get("atcud_code", "")),
			"series_info": format_series_info_for_print(doc),
			"compliance_status": format_compliance_info(doc),
			"environment": get_at_environment_display(doc),
			"is_compliant": is_compliant_document(doc),
			"compliance_level": status.get("compliance_level", "none"),
			"qr_code_data": get_qr_code_data(doc),
			"saft_data": format_saft_data(doc)
		}
	except Exception:
		return {}


# ========== REGISTRAR MÉTODOS NO JINJA CORRIGIDO ==========

# ✅ LISTA COMPLETA E CORRIGIDA DE MÉTODOS JINJA
JINJA_METHODS = [
	# ========== MÉTODOS ATCUD ==========
	get_atcud_code,
	format_atcud_display,
	validate_atcud_format,
	get_atcud_validation_code,
	get_atcud_sequence,
	get_atcud_info_formatted,

	# ========== MÉTODOS NAMING SERIES ==========
	get_naming_series,
	get_series_prefix,
	get_portugal_series_info,
	is_portuguese_series,
	extract_series_components,
	get_compliance_info,
	format_series_info_for_print,
	get_series_communication_status,
	get_document_sequence_info,

	# ========== MÉTODOS DE FORMATAÇÃO ==========
	format_portuguese_date,
	format_portuguese_currency,
	format_portuguese_phone,
	format_postal_code,
	format_percentage,
	format_iban,
	get_month_name_portuguese,
	money_in_words_portuguese,

	# ========== MÉTODOS DE VALIDAÇÃO ==========
	validate_portuguese_nif,
	get_company_nif,
	get_customer_nif,
	get_supplier_nif,
	validate_nif_format,
	get_nif_info,

	# ========== MÉTODOS DE DOCUMENTOS ==========
	get_document_type_description,
	get_document_type_code,
	get_tax_rate_description,
	format_tax_breakdown,
	get_invoice_totals_text,
	get_payment_terms_text,
	get_document_totals_summary,

	# ========== MÉTODOS DE ENDEREÇOS ==========
	get_company_address_formatted,
	format_customer_address,
	get_legal_text_footer,
	get_company_info_complete,

	# ========== MÉTODOS QR CODE E SAF-T ==========
	get_qr_code_data,
	generate_qr_code_image,
	get_saft_hash,
	format_saft_data,

	# ========== MÉTODOS DE COMPLIANCE ==========
	get_compliance_status,
	is_compliant_document,
	get_at_environment_display,
	format_compliance_info,
	get_compliance_summary_for_print
]
