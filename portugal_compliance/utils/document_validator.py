# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Document Validator Utilities - UTILITÁRIO PURO REFATORADO
✅ ALINHADO: Sem duplicação com document_hooks.py
✅ FOCO: Apenas utilitários de validação (sem hooks)
✅ COMPLEMENTAR: Suporte ao document_hooks.py
✅ PORTÁVEL: Funções reutilizáveis em toda a aplicação
"""

import frappe
from frappe import _
import re
from frappe.utils import cint, flt, getdate
from datetime import datetime


class DocumentValidationUtilities:
	"""
	✅ CLASSE REFATORADA: Apenas utilitários de validação
	NÃO duplica funcionalidades do document_hooks.py
	Baseado na sua experiência com programação.técnicas_de_debugging[3]
	"""

	def __init__(self):
		self.module = "Portugal Compliance"
		self.supported_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'POS Invoice', 'Payment Entry',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry',
			'Quotation', 'Sales Order', 'Purchase Order', 'Material Request'
		]

	# ========== UTILITÁRIOS DE VALIDAÇÃO NIF ==========

	def validate_nif(self, nif):
		"""
		✅ UTILITÁRIO: Validar NIF português (algoritmo oficial)
		Usado por document_hooks.py e outras partes do sistema
		"""
		if not nif:
			return False

		try:
			# Remover espaços e caracteres não numéricos
			nif = re.sub(r'\D', '', str(nif))

			# Verificar comprimento
			if len(nif) != 9:
				return False

			# Verificar primeiro dígito
			first_digit = int(nif[0])
			valid_first_digits = [1, 2, 3, 5, 6, 7, 8, 9]

			if first_digit not in valid_first_digits:
				return False

			# Calcular dígito de controle
			total = 0
			for i in range(8):
				total += int(nif[i]) * (9 - i)

			remainder = total % 11
			check_digit = 0 if remainder < 2 else 11 - remainder

			return check_digit == int(nif[8])

		except (ValueError, IndexError):
			return False

	def get_nif_type(self, nif):
		"""
		✅ UTILITÁRIO: Identificar tipo de NIF
		"""
		if not self.validate_nif(nif):
			return None

		first_digit = int(str(nif)[0])

		nif_types = {
			1: "Pessoa Singular",
			2: "Pessoa Singular",
			3: "Pessoa Singular",
			5: "Pessoa Coletiva",
			6: "Administração Pública",
			7: "Outros",
			8: "Empresário em Nome Individual",
			9: "Pessoa Coletiva"
		}

		return nif_types.get(first_digit, "Desconhecido")

	def format_nif(self, nif):
		"""
		✅ UTILITÁRIO: Formatar NIF para exibição
		"""
		if not self.validate_nif(nif):
			return nif

		clean_nif = re.sub(r'\D', '', str(nif))
		return f"{clean_nif[:3]} {clean_nif[3:6]} {clean_nif[6:]}"

	# ========== UTILITÁRIOS DE VALIDAÇÃO ATCUD ==========

	def validate_atcud_format(self, atcud_code):
		"""
		✅ UTILITÁRIO: Validar formato ATCUD (múltiplos formatos)
		"""
		if not atcud_code:
			return False

		try:
			# ✅ FORMATOS ACEITOS
			patterns = [
				r'^[A-Z0-9]{8,12}-\d{8}$',  # Formato AT: VALIDATION_CODE-SEQUENCE
				r'^0\.\d+$',  # Formato alternativo: 0.SEQUENCE
				r'^[A-Z0-9]{8,12}$',  # Apenas validation_code
				r'^AT\d{14}$'  # Formato fallback
			]

			atcud_clean = atcud_code.strip().upper()

			for pattern in patterns:
				if re.match(pattern, atcud_clean):
					return True

			return False

		except Exception:
			return False

	def extract_atcud_parts(self, atcud_code):
		"""
		✅ UTILITÁRIO: Extrair partes do ATCUD
		"""
		if not atcud_code:
			return None

		try:
			atcud_clean = atcud_code.strip()

			if '-' in atcud_clean:
				parts = atcud_clean.split('-')
				return {
					'validation_code': parts[0],
					'sequence': parts[1] if len(parts) > 1 else None,
					'format': 'standard',
					'is_valid': self.validate_atcud_format(atcud_code)
				}
			elif atcud_clean.startswith('0.'):
				return {
					'validation_code': '0',
					'sequence': atcud_clean[2:],
					'format': 'alternative',
					'is_valid': self.validate_atcud_format(atcud_code)
				}
			else:
				return {
					'validation_code': atcud_clean,
					'sequence': None,
					'format': 'code_only',
					'is_valid': self.validate_atcud_format(atcud_code)
				}

		except Exception:
			return None

	def generate_atcud_preview(self, validation_code, sequence):
		"""
		✅ UTILITÁRIO: Gerar preview de ATCUD
		"""
		if not validation_code or not sequence:
			return None

		try:
			sequence_formatted = str(sequence).zfill(8)
			return f"{validation_code}-{sequence_formatted}"
		except Exception:
			return None

	# ========== UTILITÁRIOS DE VALIDAÇÃO MONETÁRIA ==========

	def validate_currency_precision(self, amount, max_decimals=2):
		"""
		✅ UTILITÁRIO: Validar precisão monetária
		"""
		if not amount:
			return True

		try:
			amount_str = str(flt(amount))
			if '.' in amount_str:
				decimal_places = len(amount_str.split('.')[1])
				return decimal_places <= max_decimals
			return True
		except Exception:
			return False

	def validate_eur_amount(self, amount):
		"""
		✅ UTILITÁRIO: Validar valor em EUR (máximo 2 decimais)
		"""
		return self.validate_currency_precision(amount, 2)

	def format_currency_eur(self, amount):
		"""
		✅ UTILITÁRIO: Formatar valor em EUR
		"""
		try:
			return f"€{flt(amount, 2):,.2f}".replace(',', ' ')
		except Exception:
			return str(amount)

	def validate_tax_rate(self, rate):
		"""
		✅ UTILITÁRIO: Validar taxa de imposto portuguesa
		"""
		if not rate:
			return True

		try:
			rate_float = flt(rate)
			# Taxas de IVA válidas em Portugal
			valid_rates = [0, 6, 13, 23]
			return rate_float in valid_rates
		except Exception:
			return False

	# ========== UTILITÁRIOS DE VALIDAÇÃO DE DATAS ==========

	def validate_fiscal_year_date(self, date_value, company):
		"""
		✅ UTILITÁRIO: Validar se data está no ano fiscal correto
		"""
		try:
			from erpnext.accounts.utils import get_fiscal_year
			fiscal_year = get_fiscal_year(date_value, company=company)
			return True
		except Exception:
			return False

	def validate_document_date(self, document_date):
		"""
		✅ UTILITÁRIO: Validar data do documento
		"""
		try:
			doc_date = getdate(document_date)
			today = getdate()

			# Não pode ser data futura (mais de 1 dia)
			if doc_date > today:
				return False

			# Não pode ser muito antiga (mais de 2 anos)
			years_diff = today.year - doc_date.year
			if years_diff > 2:
				return False

			return True
		except Exception:
			return False

	def get_fiscal_year_info(self, date_value, company):
		"""
		✅ UTILITÁRIO: Obter informações do ano fiscal
		"""
		try:
			from erpnext.accounts.utils import get_fiscal_year
			fiscal_year = get_fiscal_year(date_value, company=company)

			return {
				'fiscal_year': fiscal_year[0],
				'year_start_date': fiscal_year[1],
				'year_end_date': fiscal_year[2],
				'is_valid': True
			}
		except Exception as e:
			return {
				'fiscal_year': None,
				'is_valid': False,
				'error': str(e)
			}

	# ========== UTILITÁRIOS DE VALIDAÇÃO DE DOCUMENTOS ==========

	def extract_document_number(self, document_name):
		"""
		✅ UTILITÁRIO: Extrair número do documento
		"""
		if not document_name:
			return 0

		try:
			patterns = [
				r'\.(\d+)$',  # ERPNext: FT2025NDX.0001
				r'-(\d{8})$',  # ATCUD: AAJFJMVNTN-00000001
				r'-(\d+)$',  # Alternativo: PREFIX-NNNN
				r'(\d+)$'  # Apenas números no final
			]

			for pattern in patterns:
				match = re.search(pattern, document_name)
				if match:
					return cint(match.group(1))

			return 0
		except Exception:
			return 0

	def validate_document_sequence(self, document_name, expected_sequence, tolerance=100):
		"""
		✅ UTILITÁRIO: Validar se documento está na sequência esperada
		"""
		try:
			doc_number = self.extract_document_number(document_name)
			return abs(doc_number - expected_sequence) <= tolerance
		except Exception:
			return False

	def validate_naming_series_format(self, naming_series):
		"""
		✅ UTILITÁRIO: Validar formato de naming series portuguesa
		"""
		if not naming_series:
			return False

		try:
			# ✅ PADRÕES ACEITOS (FLEXÍVEIS)
			patterns = [
				r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$',  # Português SEM HÍFENS: FT2025NDX.####
				r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}\.####$',
				# Português COM HÍFENS: FT-2025-NDX.#### (compatibilidade)
				r'^[A-Z]{2,10}\.####$',  # Formato simples: FT.####
				r'^.+\.####$'  # ✅ PADRÃO GENÉRICO (SEGURO)
			]

			for pattern in patterns:
				if re.match(pattern, naming_series):
					return True

			return False
		except Exception:
			return False

	def extract_series_prefix(self, naming_series):
		"""
		✅ UTILITÁRIO: Extrair prefixo da naming series
		"""
		if not naming_series:
			return None

		try:
			return naming_series.replace('.####', '')
		except Exception:
			return None

	# ========== UTILITÁRIOS DE VALIDAÇÃO DE EMPRESA ==========

	def validate_company_portugal_compliance(self, company):
		"""
		✅ UTILITÁRIO: Verificar se empresa tem compliance português ativo
		"""
		try:
			if not company:
				return False

			company_data = frappe.db.get_value("Company", company,
											   ["country", "portugal_compliance_enabled"])

			if not company_data:
				return False

			country, compliance_enabled = company_data
			return country == "Portugal" and cint(compliance_enabled)

		except Exception:
			return False

	def get_company_compliance_info(self, company):
		"""
		✅ UTILITÁRIO: Obter informações de compliance da empresa
		"""
		try:
			company_data = frappe.db.get_value("Company", company, [
				"country", "portugal_compliance_enabled", "abbr",
				"at_username", "at_environment"
			], as_dict=True)

			if not company_data:
				return None

			return {
				'company': company,
				'country': company_data.country,
				'compliance_enabled': cint(company_data.portugal_compliance_enabled),
				'abbr': company_data.abbr,
				'has_at_credentials': bool(company_data.at_username),
				'at_environment': company_data.at_environment or 'test',
				'is_portuguese': company_data.country == "Portugal"
			}

		except Exception as e:
			return {'error': str(e)}

	# ========== RELATÓRIOS E ESTATÍSTICAS ==========

	def get_validation_statistics(self, company=None, doctype=None, date_range=None):
		"""
		✅ UTILITÁRIO: Obter estatísticas de validação
		"""
		try:
			stats = {
				'company': company,
				'doctype': doctype,
				'date_range': date_range,
				'total_documents': 0,
				'with_atcud': 0,
				'with_valid_atcud': 0,
				'with_naming_series': 0,
				'compliance_rate': 0,
				'by_doctype': {}
			}

			# Filtros base
			filters = {}
			if company:
				filters['company'] = company

			if date_range:
				filters['creation'] = ['between', date_range]

			# Tipos de documento para analisar
			doctypes_to_check = [doctype] if doctype else self.supported_doctypes

			for dt in doctypes_to_check:
				try:
					if not frappe.db.table_exists(f"tab{dt}"):
						continue

					# Verificar se campo atcud_code existe
					columns = frappe.db.get_table_columns(dt)
					if 'atcud_code' not in columns:
						continue

					# Contar total
					count = frappe.db.count(dt, filters)
					stats['total_documents'] += count

					# Contar com ATCUD
					atcud_filters = dict(filters)
					atcud_filters['atcud_code'] = ['!=', '']
					atcud_count = frappe.db.count(dt, atcud_filters)
					stats['with_atcud'] += atcud_count

					# Contar com naming series
					ns_filters = dict(filters)
					ns_filters['naming_series'] = ['!=', '']
					ns_count = frappe.db.count(dt, ns_filters)
					stats['with_naming_series'] += ns_count

					# Estatísticas por doctype
					stats['by_doctype'][dt] = {
						'total': count,
						'with_atcud': atcud_count,
						'with_naming_series': ns_count,
						'atcud_rate': round((atcud_count / count * 100), 2) if count > 0 else 0
					}

				except Exception as e:
					stats['by_doctype'][dt] = {'error': str(e)}

			# Calcular taxa de compliance geral
			if stats['total_documents'] > 0:
				stats['compliance_rate'] = round(
					(stats['with_atcud'] / stats['total_documents']) * 100, 2
				)

			return stats

		except Exception as e:
			frappe.log_error(f"Erro ao obter estatísticas: {str(e)}")
			return {'error': str(e)}

	def validate_document_compliance(self, doc_data):
		"""
		✅ UTILITÁRIO: Validar compliance de um documento (sem hooks)
		"""
		try:
			validation_result = {
				'is_compliant': True,
				'issues': [],
				'warnings': [],
				'recommendations': []
			}

			# ✅ VALIDAR EMPRESA
			if not self.validate_company_portugal_compliance(doc_data.get('company')):
				validation_result['issues'].append('Empresa não tem compliance português ativo')
				validation_result['is_compliant'] = False

			# ✅ VALIDAR NAMING SERIES
			naming_series = doc_data.get('naming_series')
			if naming_series:
				if not self.validate_naming_series_format(naming_series):
					validation_result['warnings'].append('Formato de naming series não padrão')
			else:
				validation_result['issues'].append('Naming series não definida')
				validation_result['is_compliant'] = False

			# ✅ VALIDAR ATCUD
			atcud_code = doc_data.get('atcud_code')
			if atcud_code:
				if not self.validate_atcud_format(atcud_code):
					validation_result['issues'].append('Formato de ATCUD inválido')
					validation_result['is_compliant'] = False
			else:
				validation_result['warnings'].append('ATCUD não gerado')

			# ✅ VALIDAR NIF DO CLIENTE (se aplicável)
			customer_nif = doc_data.get('tax_id')
			if customer_nif:
				if not self.validate_nif(customer_nif):
					validation_result['warnings'].append('NIF do cliente inválido')

			# ✅ VALIDAR VALORES MONETÁRIOS
			grand_total = doc_data.get('grand_total')
			if grand_total:
				if not self.validate_eur_amount(grand_total):
					validation_result['warnings'].append('Precisão monetária incorreta')

			# ✅ GERAR RECOMENDAÇÕES
			if not atcud_code and naming_series:
				validation_result['recommendations'].append('Gerar ATCUD para este documento')

			if not customer_nif and doc_data.get('doctype') in ['Sales Invoice', 'POS Invoice']:
				validation_result['recommendations'].append('Adicionar NIF do cliente')

			return validation_result

		except Exception as e:
			return {
				'is_compliant': False,
				'error': str(e)
			}


# ========== INSTÂNCIA GLOBAL ==========
document_validation_utilities = DocumentValidationUtilities()


# ========== FUNÇÕES AUXILIARES PARA USO EXTERNO ==========

def validate_nif(nif):
	"""✅ FUNÇÃO AUXILIAR: Validar NIF"""
	return document_validation_utilities.validate_nif(nif)


def validate_atcud_format(atcud_code):
	"""✅ FUNÇÃO AUXILIAR: Validar formato ATCUD"""
	return document_validation_utilities.validate_atcud_format(atcud_code)


def extract_document_number(document_name):
	"""✅ FUNÇÃO AUXILIAR: Extrair número do documento"""
	return document_validation_utilities.extract_document_number(document_name)


def validate_naming_series_format(naming_series):
	"""✅ FUNÇÃO AUXILIAR: Validar formato naming series"""
	return document_validation_utilities.validate_naming_series_format(naming_series)


def validate_company_portugal_compliance(company):
	"""✅ FUNÇÃO AUXILIAR: Validar compliance da empresa"""
	return document_validation_utilities.validate_company_portugal_compliance(company)


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def validate_nif_api(nif):
	"""✅ API: Validar NIF"""
	try:
		is_valid = validate_nif(nif)
		return {
			'valid': is_valid,
			'type': document_validation_utilities.get_nif_type(nif) if is_valid else None,
			'formatted': document_validation_utilities.format_nif(nif) if is_valid else nif
		}
	except Exception as e:
		return {'error': str(e)}


@frappe.whitelist()
def validate_atcud_api(atcud_code):
	"""✅ API: Validar ATCUD"""
	try:
		is_valid = validate_atcud_format(atcud_code)
		parts = document_validation_utilities.extract_atcud_parts(atcud_code) if is_valid else None

		return {
			'valid': is_valid,
			'parts': parts
		}
	except Exception as e:
		return {'error': str(e)}


@frappe.whitelist()
def get_validation_statistics_api(company=None, doctype=None):
	"""✅ API: Obter estatísticas de validação"""
	try:
		return document_validation_utilities.get_validation_statistics(company, doctype)
	except Exception as e:
		return {'error': str(e)}


@frappe.whitelist()
def validate_document_compliance_api(doc_data):
	"""✅ API: Validar compliance de documento"""
	try:
		if isinstance(doc_data, str):
			import json
			doc_data = json.loads(doc_data)

		return document_validation_utilities.validate_document_compliance(doc_data)
	except Exception as e:
		return {'error': str(e)}


@frappe.whitelist()
def get_company_compliance_info_api(company):
	"""✅ API: Obter informações de compliance da empresa"""
	try:
		return document_validation_utilities.get_company_compliance_info(company)
	except Exception as e:
		return {'error': str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Document Validation Utilities REFATORADO loaded - Version 2.1.0 - Pure Utilities")
