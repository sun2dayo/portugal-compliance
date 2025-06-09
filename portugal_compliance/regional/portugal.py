# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Regional Portugal - Portugal Compliance VERSÃO ATUALIZADA E ALINHADA
Configurações regionais específicas para Portugal
✅ ALINHADO: 100% compatível com document_hooks.py (sem duplicação)
✅ ESPECÍFICO: Funcionalidades regionais exclusivas
✅ FORMATO: SEM HÍFENS (FT2025NDX) - dinâmico baseado no abbr
✅ OTIMIZADO: Performance melhorada e validações não bloqueantes
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint, getdate
import re
from datetime import datetime, date

# ========== CONFIGURAÇÃO DE TIPOS DE DOCUMENTO ATUALIZADA ==========

PORTUGAL_DOCUMENT_TYPES = {
	# ✅ DOCUMENTOS DE VENDA (CORRIGIDOS)
	'Sales Invoice': {
		'code': 'FT',
		'name': 'Fatura',
		'description': 'Fatura de venda para clientes',
		'communication_required': True,
		'atcud_required': True,
		'qr_code_required': True,
		'saft_type': 'FT'
	},
	'POS Invoice': {
		'code': 'FS',
		'name': 'Fatura Simplificada',
		'description': 'Fatura simplificada para POS/Retail',
		'communication_required': True,
		'atcud_required': True,
		'qr_code_required': True,
		'nif_limit': 1000,
		'saft_type': 'FS'
	},
	'Sales Order': {
		'code': 'EC',  # ✅ CORRIGIDO: EN → EC
		'name': 'Encomenda Cliente',
		'description': 'Encomenda de cliente',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'EC'
	},
	'Quotation': {
		'code': 'OR',
		'name': 'Orçamento',
		'description': 'Orçamento para clientes',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'OR'
	},
	'Delivery Note': {
		'code': 'GT',  # ✅ CORRIGIDO: GR → GT
		'name': 'Guia de Transporte',
		'description': 'Guia de transporte para entregas',
		'communication_required': True,
		'atcud_required': True,
		'saft_type': 'GT'
	},

	# ✅ DOCUMENTOS DE COMPRA (CORRIGIDOS)
	'Purchase Invoice': {
		'code': 'FC',
		'name': 'Fatura de Compra',
		'description': 'Fatura de compra de fornecedores',
		'communication_required': True,
		'atcud_required': True,
		'saft_type': 'FC'
	},
	'Purchase Order': {
		'code': 'EF',  # ✅ CORRIGIDO: OC → EF
		'name': 'Encomenda Fornecedor',
		'description': 'Encomenda a fornecedor',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'EF'
	},
	'Purchase Receipt': {
		'code': 'GR',
		'name': 'Guia de Receção',
		'description': 'Guia de receção de mercadorias',
		'communication_required': True,
		'atcud_required': True,
		'saft_type': 'GR'
	},

	# ✅ OUTROS DOCUMENTOS
	'Stock Entry': {
		'code': 'GM',
		'name': 'Guia de Movimentação',
		'description': 'Guia de movimentação de stock',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'GM'
	},
	'Payment Entry': {
		'code': 'RC',
		'name': 'Recibo',
		'description': 'Recibo de pagamento/recebimento',
		'communication_required': True,
		'atcud_required': True,
		'saft_type': 'RC'
	},
	'Journal Entry': {
		'code': 'JE',
		'name': 'Lançamento Contábil',
		'description': 'Lançamento contábil manual',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'JE'
	},
	'Material Request': {
		'code': 'MR',
		'name': 'Requisição de Material',
		'description': 'Requisição de material interno',
		'communication_required': False,
		'atcud_required': False,
		'saft_type': 'MR'
	}
}

# ========== CONFIGURAÇÕES REGIONAIS ATUALIZADAS ==========

PORTUGAL_REGIONAL_CONFIG = {
	'country': 'Portugal',
	'currency': 'EUR',
	'date_format': 'dd-mm-yyyy',
	'time_format': '24 Hour',
	'number_format': '#.###,##',
	'float_precision': 2,
	'language': 'pt',
	'timezone': 'Europe/Lisbon',

	# ✅ CONFIGURAÇÕES FISCAIS ATUALIZADAS
	'tax_rates': [0, 6, 13, 23],  # Taxas IVA Portugal 2025
	'default_tax_rate': 23,
	'tax_name': 'IVA',
	'nif_required_limit': 1000,

	# ✅ CONFIGURAÇÕES DE COMPLIANCE
	'atcud_required': True,
	'qr_code_required': True,
	'series_communication_required': True,
	'at_environment_default': 'test'
}


# ========== FUNÇÕES REGIONAIS ESPECÍFICAS ==========

def get_series_for_company_regional(company):
	"""
	✅ ATUALIZADO: Retornar séries com informações regionais específicas
	Complementa document_hooks.py sem duplicar
	"""
	if not company:
		return []

	# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
	if not is_portuguese_company_cached(company):
		return []

	try:
		# ✅ BUSCAR SÉRIES EXISTENTES COM INFORMAÇÕES REGIONAIS
		existing_series = frappe.get_all(
			'Portugal Series Configuration',
			filters={
				'company': company,
				'is_active': 1
			},
			fields=['name', 'prefix', 'naming_series', 'document_type', 'is_communicated',
					'validation_code', 'total_documents_issued', 'last_document_date']
		)

		series_list = []
		for series in existing_series:
			# ✅ ENRIQUECER COM INFORMAÇÕES REGIONAIS
			doc_info = PORTUGAL_DOCUMENT_TYPES.get(series.document_type, {})

			series_info = {
				'name': series.name,
				'prefix': series.prefix,
				'naming_series': series.naming_series,
				'document_type': series.document_type,
				'is_communicated': series.is_communicated,
				'validation_code': series.validation_code,
				'total_documents': series.total_documents_issued or 0,
				'last_document_date': series.last_document_date,

				# ✅ INFORMAÇÕES REGIONAIS ESPECÍFICAS
				'doc_info': doc_info,
				'saft_type': doc_info.get('saft_type'),
				'requires_communication': doc_info.get('communication_required', False),
				'requires_atcud': doc_info.get('atcud_required', False),
				'requires_qr': doc_info.get('qr_code_required', False),
				'regional_compliance': _evaluate_regional_compliance(series, doc_info)
			}

			series_list.append(series_info)

		return series_list

	except Exception as e:
		frappe.log_error(f"Erro ao buscar séries regionais para empresa {company}: {str(e)}")
		return []


def _evaluate_regional_compliance(series, doc_info):
	"""
	✅ NOVO: Avaliar compliance regional específico
	"""
	try:
		compliance_score = 0
		total_checks = 0
		issues = []

		# ✅ VERIFICAR COMUNICAÇÃO SE NECESSÁRIA
		if doc_info.get('communication_required'):
			total_checks += 1
			if series.is_communicated:
				compliance_score += 1
			else:
				issues.append("Série não comunicada à AT")

		# ✅ VERIFICAR VALIDATION CODE SE COMUNICADA
		if series.is_communicated:
			total_checks += 1
			if series.validation_code:
				compliance_score += 1
			else:
				issues.append("Validation code em falta")

		# ✅ VERIFICAR USO DA SÉRIE
		total_checks += 1
		if series.total_documents_issued and series.total_documents_issued > 0:
			compliance_score += 1
		else:
			issues.append("Série ainda não utilizada")

		compliance_rate = (compliance_score / total_checks * 100) if total_checks > 0 else 0

		return {
			'compliance_rate': compliance_rate,
			'status': 'OK' if compliance_rate >= 80 else 'WARNING' if compliance_rate >= 50 else 'CRITICAL',
			'issues': issues,
			'total_checks': total_checks,
			'passed_checks': compliance_score
		}

	except Exception:
		return {
			'compliance_rate': 0,
			'status': 'ERROR',
			'issues': ['Erro na avaliação de compliance'],
			'total_checks': 0,
			'passed_checks': 0
		}


def validate_portugal_company_settings_safe(doc, method=None):
	"""
	✅ ATUALIZADO: Validação NUNCA bloqueante - apenas avisos
	Baseado na sua experiência com programação.conformidade_portugal[6]
	"""
	try:
		if not hasattr(doc, 'country') or doc.country != 'Portugal':
			return

		# ✅ PRESERVAR COMPLIANCE SEMPRE (CRÍTICO)
		if hasattr(doc, '_doc_before_save') and hasattr(doc._doc_before_save,
														'portugal_compliance_enabled'):
			original_compliance = getattr(doc._doc_before_save, 'portugal_compliance_enabled', 0)
			if cint(original_compliance) and not cint(doc.portugal_compliance_enabled):
				# ✅ RESTAURAR COMPLIANCE AUTOMATICAMENTE
				doc.portugal_compliance_enabled = 1
				frappe.logger().info(
					f"✅ Compliance preservado automaticamente para empresa {doc.name}")

		# ✅ CONFIGURAR DEFAULTS REGIONAIS
		setup_portugal_regional_defaults(doc)

		# ✅ VALIDAÇÕES NÃO BLOQUEANTES
		warnings = validate_portugal_settings_non_blocking(doc)

		# ✅ MOSTRAR AVISOS SE HOUVER
		if warnings:
			frappe.msgprint(
				"Avisos de configuração regional:\n" + "\n".join(warnings),
				title="Avisos Portugal Regional",
				indicator="orange"
			)

	except Exception as e:
		frappe.log_error(f"Erro na validação regional (não crítico): {str(e)}")
	# ✅ NUNCA FALHAR - apenas log


def setup_portugal_regional_defaults(doc):
	"""
	✅ ATUALIZADO: Configurar defaults regionais específicos
	"""
	try:
		# ✅ CONFIGURAÇÕES REGIONAIS BÁSICAS
		if not getattr(doc, 'default_currency', None):
			doc.default_currency = PORTUGAL_REGIONAL_CONFIG['currency']

		if not getattr(doc, 'country', None):
			doc.country = PORTUGAL_REGIONAL_CONFIG['country']

		# ✅ CONFIGURAÇÕES DE COMPLIANCE
		if cint(doc.get('portugal_compliance_enabled', 0)):
			# Configurar ambiente AT padrão
			if not getattr(doc, 'at_environment', None):
				doc.at_environment = PORTUGAL_REGIONAL_CONFIG['at_environment_default']

			# Configurar formato de data
			if not getattr(doc, 'date_format', None):
				doc.date_format = PORTUGAL_REGIONAL_CONFIG['date_format']

		frappe.logger().info(
			f"Defaults regionais configurados para empresa {getattr(doc, 'name', 'Nova')}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar defaults regionais: {str(e)}")


def validate_portugal_settings_non_blocking(doc):
	"""
	✅ NOVO: Validações não bloqueantes - apenas avisos
	"""
	warnings = []

	try:
		# ✅ VERIFICAR NIF SE COMPLIANCE ATIVO
		if cint(doc.get('portugal_compliance_enabled', 0)):
			if not getattr(doc, 'tax_id', None):
				warnings.append("• Recomenda-se definir NIF para compliance completo")
			elif not validate_portuguese_nif_safe(doc.tax_id)['valid']:
				warnings.append("• NIF parece inválido - verifique o formato")

			# ✅ VERIFICAR CREDENCIAIS AT
			if not getattr(doc, 'at_username', None):
				warnings.append("• Configure credenciais AT para comunicação automática de séries")

			# ✅ VERIFICAR ABREVIATURA
			if not getattr(doc, 'abbr', None):
				warnings.append("• Abreviatura da empresa é necessária para séries portuguesas")
			elif len(doc.abbr) < 2 or len(doc.abbr) > 4:
				warnings.append("• Abreviatura deve ter entre 2 e 4 caracteres")

		# ✅ VERIFICAR CONFIGURAÇÕES REGIONAIS
		if doc.default_currency and doc.default_currency != 'EUR':
			warnings.append("• Moeda padrão deveria ser EUR para empresas portuguesas")

		return warnings

	except Exception as e:
		frappe.log_error(f"Erro nas validações não bloqueantes: {str(e)}")
		return ["• Erro na validação - verificar configurações"]


# ========== VALIDAÇÕES REGIONAIS ESPECÍFICAS ==========

def validate_portuguese_nif_enhanced(nif):
	"""
	✅ MELHORADO: Validação robusta de NIF português
	Baseado na sua experiência com programação.autenticação[3]
	"""
	try:
		if not nif:
			return {'valid': False, 'message': 'NIF não fornecido', 'type': None}

		# Limpar NIF
		nif_clean = re.sub(r'[^0-9]', '', str(nif))

		if len(nif_clean) != 9:
			return {'valid': False, 'message': 'NIF deve ter 9 dígitos', 'type': None}

		# Verificar primeiro dígito válido
		first_digit = nif_clean[0]
		if first_digit not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			return {'valid': False, 'message': 'Primeiro dígito do NIF inválido', 'type': None}

		# Algoritmo de validação mod 11
		checksum = 0
		for i in range(8):
			checksum += int(nif_clean[i]) * (9 - i)

		remainder = checksum % 11
		control_digit = 0 if remainder < 2 else 11 - remainder

		if int(nif_clean[8]) == control_digit:
			# ✅ DETERMINAR TIPO DE ENTIDADE
			entity_type = get_nif_entity_type(first_digit)

			return {
				'valid': True,
				'message': 'NIF válido',
				'type': entity_type,
				'formatted': format_nif_display(nif_clean)
			}
		else:
			return {'valid': False, 'message': 'Dígito de controlo inválido', 'type': None}

	except Exception as e:
		return {'valid': False, 'message': f'Erro na validação: {str(e)}', 'type': None}


def validate_portuguese_nif_safe(nif):
	"""
	✅ ALIAS: Versão segura da validação (compatibilidade)
	"""
	return validate_portuguese_nif_enhanced(nif)


def get_nif_entity_type(first_digit):
	"""
	✅ ATUALIZADO: Obter tipo de entidade baseado no primeiro dígito
	"""
	types = {
		'1': 'Pessoa Singular',
		'2': 'Pessoa Singular',
		'3': 'Pessoa Singular',
		'5': 'Pessoa Coletiva',
		'6': 'Administração Pública',
		'7': 'Outras Entidades',
		'8': 'Empresário em Nome Individual',
		'9': 'Pessoa Coletiva'
	}
	return types.get(first_digit, 'Desconhecido')


def format_nif_display(nif):
	"""
	✅ NOVO: Formatar NIF para exibição
	"""
	if len(nif) == 9:
		return f"{nif[:3]} {nif[3:6]} {nif[6:]}"
	return nif


def validate_portuguese_postal_code(postal_code):
	"""
	✅ ATUALIZADO: Validar código postal português
	"""
	try:
		if not postal_code:
			return {'valid': False, 'message': 'Código postal não fornecido'}

		# Padrão português: XXXX-XXX
		pattern = r'^\d{4}-\d{3}$'

		if re.match(pattern, postal_code.strip()):
			return {'valid': True, 'message': 'Código postal válido'}
		else:
			return {
				'valid': False,
				'message': 'Código postal deve ter formato XXXX-XXX (ex: 1000-001)'
			}

	except Exception as e:
		return {'valid': False, 'message': f'Erro na validação: {str(e)}'}


def validate_portuguese_address_enhanced(address_doc):
	"""
	✅ MELHORADO: Validar endereço português com avisos não bloqueantes
	"""
	if address_doc.country != 'Portugal':
		return

	warnings = []

	try:
		# ✅ VALIDAR CÓDIGO POSTAL
		if address_doc.pincode:
			postal_validation = validate_portuguese_postal_code(address_doc.pincode)
			if not postal_validation['valid']:
				warnings.append(f"Código postal: {postal_validation['message']}")

		# ✅ VERIFICAR CAMPOS RECOMENDADOS
		if not address_doc.address_line1:
			warnings.append("Morada é recomendada")

		if not address_doc.city:
			warnings.append("Cidade é recomendada")

		# ✅ MOSTRAR AVISOS SE HOUVER
		if warnings:
			frappe.msgprint(
				"Avisos no endereço português:\n" + "\n".join(warnings),
				title="Avisos de Endereço",
				indicator="orange"
			)

	except Exception as e:
		frappe.log_error(f"Erro na validação de endereço: {str(e)}")


# ========== CONFIGURAÇÕES DE IMPOSTOS REGIONAIS ==========

def get_portugal_tax_rates_detailed():
	"""
	✅ ATUALIZADO: Obter taxas de IVA portuguesas detalhadas
	"""
	return {
		'rates': PORTUGAL_REGIONAL_CONFIG['tax_rates'],
		'default': PORTUGAL_REGIONAL_CONFIG['default_tax_rate'],
		'details': {
			0: {'name': 'Isento', 'description': 'Operações isentas de IVA'},
			6: {'name': 'Taxa Reduzida',
				'description': 'Bens essenciais (alimentação, medicamentos)'},
			13: {'name': 'Taxa Intermédia', 'description': 'Restauração, hotelaria'},
			23: {'name': 'Taxa Normal', 'description': 'Taxa geral aplicável'}
		}
	}


def validate_portugal_tax_rate_enhanced(rate):
	"""
	✅ MELHORADO: Validar taxa de IVA com informações detalhadas
	"""
	tax_info = get_portugal_tax_rates_detailed()
	valid_rates = tax_info['rates']

	if rate in valid_rates:
		return {
			'valid': True,
			'rate': rate,
			'info': tax_info['details'].get(rate, {}),
			'message': f"Taxa IVA válida: {rate}%"
		}
	else:
		return {
			'valid': False,
			'rate': rate,
			'message': f"Taxa IVA inválida. Taxas válidas: {', '.join(map(str, valid_rates))}%",
			'valid_rates': valid_rates
		}


def setup_tax_accounts_for_company_enhanced(company):
	"""
	✅ MELHORADO: Configurar contas de impostos com tratamento robusto
	Baseado na sua experiência com programação.sistemas_erp[7]
	"""
	try:
		if not frappe.db.exists("Company", company):
			return None

		company_doc = frappe.get_doc("Company", company)

		# ✅ BUSCAR OU CRIAR CONTA DE IMPOSTOS
		tax_account = get_or_create_tax_account_enhanced(company, company_doc.abbr)

		if tax_account:
			frappe.logger().info(f"✅ Conta de impostos configurada: {tax_account}")
			return tax_account
		else:
			frappe.logger().warning(
				f"⚠️ Não foi possível configurar conta de impostos para {company}")
			return None

	except Exception as e:
		frappe.log_error(f"Erro ao configurar contas de impostos: {str(e)}")
		return None


def get_or_create_tax_account_enhanced(company, company_abbr):
	"""
	✅ MELHORADO: Obter ou criar conta de impostos com fallbacks
	"""
	try:
		# ✅ TENTAR DIFERENTES NOMES DE CONTA
		possible_account_names = [
			f"Duties and Taxes - {company_abbr}",
			f"IVA a Pagar - {company_abbr}",
			f"Tax Payable - {company_abbr}",
			f"Impostos - {company_abbr}"
		]

		# ✅ VERIFICAR SE ALGUMA CONTA JÁ EXISTE
		for account_name in possible_account_names:
			if frappe.db.exists("Account", account_name):
				# ✅ VERIFICAR SE É ADEQUADA
				account_doc = frappe.get_doc("Account", account_name)
				if account_doc.is_group == 0 and account_doc.account_type == "Tax":
					return account_name
				elif account_doc.is_group == 1:
					# ✅ CORRIGIR CONTA GROUP
					account_doc.is_group = 0
					account_doc.account_type = "Tax"
					account_doc.save(ignore_permissions=True)
					return account_name

		# ✅ CRIAR NOVA CONTA
		return create_new_tax_account_enhanced(company, company_abbr)

	except Exception as e:
		frappe.log_error(f"Erro ao obter/criar conta de impostos: {str(e)}")
		return None


def create_new_tax_account_enhanced(company, company_abbr):
	"""
	✅ NOVO: Criar nova conta de impostos com fallbacks robustos
	"""
	try:
		# ✅ BUSCAR CONTA PAI ADEQUADA
		parent_account = find_suitable_parent_account(company)

		if not parent_account:
			frappe.logger().warning(
				f"Não foi possível encontrar conta pai para impostos em {company}")
			return None

		# ✅ CRIAR CONTA
		account_name = f"Duties and Taxes - {company_abbr}"

		account_doc = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Duties and Taxes",
			"company": company,
			"parent_account": parent_account,
			"account_type": "Tax",
			"is_group": 0,
			"account_currency": "EUR"
		})

		account_doc.insert(ignore_permissions=True)
		frappe.logger().info(f"✅ Nova conta de impostos criada: {account_name}")

		return account_name

	except Exception as e:
		frappe.log_error(f"Erro ao criar nova conta de impostos: {str(e)}")
		return None


def find_suitable_parent_account(company):
	"""
	✅ NOVO: Encontrar conta pai adequada para impostos
	"""
	try:
		# ✅ TENTAR DIFERENTES OPÇÕES DE CONTA PAI
		parent_options = [
			{"root_type": "Liability", "account_type": "Tax", "is_group": 1},
			{"root_type": "Liability", "is_group": 1, "account_name": ["like", "%Tax%"]},
			{"root_type": "Liability", "is_group": 1, "account_name": ["like", "%Duties%"]},
			{"root_type": "Liability", "is_group": 1}
		]

		for option in parent_options:
			option["company"] = company
			parent_account = frappe.db.get_value("Account", option, "name")

			if parent_account:
				return parent_account

		return None

	except Exception as e:
		frappe.log_error(f"Erro ao encontrar conta pai: {str(e)}")
		return None


# ========== CONFIGURAÇÕES DE NAMING SERIES REGIONAIS ==========

def get_naming_series_options_regional(doctype):
	"""
	✅ ATUALIZADO: Obter opções de naming series com informações regionais
	"""
	if doctype not in PORTUGAL_DOCUMENT_TYPES:
		return []

	try:
		# ✅ BUSCAR SÉRIES PORTUGUESAS COM INFORMAÇÕES REGIONAIS
		series = frappe.get_all(
			'Portugal Series Configuration',
			filters={
				'document_type': doctype,
				'is_active': 1
			},
			fields=['naming_series', 'prefix', 'is_communicated', 'validation_code', 'company'],
			order_by='is_communicated desc, company, prefix'
		)

		options = []
		for s in series:
			# ✅ CRIAR OPÇÃO COM INFORMAÇÕES REGIONAIS
			status_icon = "✅" if s.is_communicated else "⚠️"
			validation_status = "🔑" if s.validation_code else "🔒"

			option_text = f"{s.naming_series} {status_icon}{validation_status} ({s.company})"
			options.append(option_text)

		return options

	except Exception as e:
		frappe.log_error(f"Erro ao buscar naming series regionais para {doctype}: {str(e)}")
		return []


def validate_naming_series_format_regional(naming_series):
	"""
	✅ ATUALIZADO: Validar formato com verificações regionais específicas
	"""
	if not naming_series:
		return {'valid': False, 'message': 'Naming series não fornecida'}

	try:
		# ✅ PADRÃO REGIONAL: XXYYYY + EMPRESA.#### (ex: FT2025NDX.####)
		pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})\.####$'
		match = re.match(pattern, naming_series)

		if not match:
			return {
				'valid': False,
				'message': 'Formato inválido. Use: XXYYYY + EMPRESA.#### (ex: FT2025NDX.####)'
			}

		doc_code, year, company_code = match.groups()

		# ✅ VALIDAÇÕES REGIONAIS ESPECÍFICAS
		current_year = datetime.now().year
		series_year = int(year)

		warnings = []

		# Verificar ano
		if series_year < current_year - 1:
			warnings.append(f"Ano da série ({series_year}) é muito antigo")
		elif series_year > current_year + 1:
			warnings.append(f"Ano da série ({series_year}) é muito futuro")

		# Verificar código do documento
		valid_doc_codes = [info['code'] for info in PORTUGAL_DOCUMENT_TYPES.values()]
		if doc_code not in valid_doc_codes:
			warnings.append(f"Código de documento '{doc_code}' não é padrão português")

		return {
			'valid': True,
			'message': 'Formato válido',
			'doc_code': doc_code,
			'year': series_year,
			'company_code': company_code,
			'warnings': warnings
		}

	except Exception as e:
		return {'valid': False, 'message': f'Erro na validação: {str(e)}'}


# ========== VALIDAÇÕES DE CLIENTES E FORNECEDORES ==========

def validate_portuguese_customer_enhanced(customer_doc):
	"""
	✅ MELHORADO: Validar cliente português com avisos não bloqueantes
	"""
	if customer_doc.country != 'Portugal':
		return

	warnings = []

	try:
		# ✅ VALIDAR NIF SE FORNECIDO
		if customer_doc.tax_id:
			nif_validation = validate_portuguese_nif_enhanced(customer_doc.tax_id)
			if not nif_validation['valid']:
				warnings.append(f"NIF inválido: {nif_validation['message']}")
			else:
				# ✅ CONFIGURAR TIPO DE ENTIDADE
				customer_doc.customer_type = "Individual" if nif_validation[
																 'type'] == "Pessoa Singular" else "Company"

		# ✅ CONFIGURAR CATEGORIA FISCAL
		if not customer_doc.tax_category:
			customer_doc.tax_category = 'Portugal - Cliente'

		# ✅ MOSTRAR AVISOS SE HOUVER
		if warnings:
			frappe.msgprint(
				"Avisos no cliente português:\n" + "\n".join(warnings),
				title="Avisos de Cliente",
				indicator="orange"
			)

	except Exception as e:
		frappe.log_error(f"Erro na validação de cliente português: {str(e)}")


def validate_portuguese_supplier_enhanced(supplier_doc):
	"""
	✅ MELHORADO: Validar fornecedor português com avisos não bloqueantes
	"""
	if supplier_doc.country != 'Portugal':
		return

	warnings = []

	try:
		# ✅ NIF RECOMENDADO PARA FORNECEDORES PORTUGUESES
		if not supplier_doc.tax_id:
			warnings.append("NIF é recomendado para fornecedores portugueses")
		else:
			nif_validation = validate_portuguese_nif_enhanced(supplier_doc.tax_id)
			if not nif_validation['valid']:
				warnings.append(f"NIF inválido: {nif_validation['message']}")
			else:
				# ✅ CONFIGURAR TIPO DE FORNECEDOR
				supplier_doc.supplier_type = "Individual" if nif_validation[
																 'type'] == "Pessoa Singular" else "Company"

		# ✅ CONFIGURAR CATEGORIA FISCAL
		if not supplier_doc.tax_category:
			supplier_doc.tax_category = 'Portugal - Fornecedor'

		# ✅ MOSTRAR AVISOS SE HOUVER
		if warnings:
			frappe.msgprint(
				"Avisos no fornecedor português:\n" + "\n".join(warnings),
				title="Avisos de Fornecedor",
				indicator="orange"
			)

	except Exception as e:
		frappe.log_error(f"Erro na validação de fornecedor português: {str(e)}")


# ========== UTILITÁRIOS REGIONAIS ==========

def is_portuguese_company_cached(company):
	"""
	✅ OTIMIZADO: Verificar se empresa é portuguesa com cache
	"""
	if not company:
		return False

	try:
		cache_key = f"portuguese_company_{company}"
		cached_result = frappe.cache().get_value(cache_key)

		if cached_result is None:
			company_data = frappe.db.get_value("Company", company,
											   ["country", "portugal_compliance_enabled"],
											   as_dict=True)

			if company_data:
				cached_result = (company_data.country == "Portugal" and
								 cint(company_data.portugal_compliance_enabled))
			else:
				cached_result = False

			# Cache por 10 minutos
			frappe.cache().set_value(cache_key, cached_result, expires_in_sec=600)

		return cached_result

	except Exception:
		return False


def get_portugal_compliance_info_regional():
	"""
	✅ ATUALIZADO: Obter informações regionais de compliance português
	"""
	return {
		'document_types': PORTUGAL_DOCUMENT_TYPES,
		'regional_config': PORTUGAL_REGIONAL_CONFIG,
		'supported_doctypes': list(PORTUGAL_DOCUMENT_TYPES.keys()),
		'tax_rates': get_portugal_tax_rates_detailed(),
		'version': '2.1.0',
		'regional_features': {
			'nif_validation': True,
			'postal_code_validation': True,
			'address_validation': True,
			'tax_rate_validation': True,
			'series_format_validation': True
		}
	}


def get_company_series_summary_regional(company):
	"""
	✅ ATUALIZADO: Obter resumo regional das séries da empresa
	"""
	if not is_portuguese_company_cached(company):
		return {}

	try:
		series = frappe.get_all(
			'Portugal Series Configuration',
			filters={'company': company},
			fields=[
				'document_type', 'prefix', 'naming_series', 'is_active',
				'is_communicated', 'total_documents_issued', 'current_sequence',
				'validation_code', 'last_document_date'
			]
		)

		summary = {
			'company': company,
			'total_series': len(series),
			'active_series': len([s for s in series if s.is_active]),
			'communicated_series': len([s for s in series if s.is_communicated]),
			'series_with_validation': len([s for s in series if s.validation_code]),
			'total_documents': sum(s.total_documents_issued or 0 for s in series),
			'by_document_type': {},
			'regional_compliance': {}
		}

		# ✅ ANÁLISE POR TIPO DE DOCUMENTO
		for s in series:
			doc_type = s.document_type
			if doc_type not in summary['by_document_type']:
				summary['by_document_type'][doc_type] = {
					'count': 0,
					'communicated': 0,
					'documents_issued': 0,
					'has_validation_code': 0
				}

			summary['by_document_type'][doc_type]['count'] += 1
			if s.is_communicated:
				summary['by_document_type'][doc_type]['communicated'] += 1
			if s.validation_code:
				summary['by_document_type'][doc_type]['has_validation_code'] += 1
			summary['by_document_type'][doc_type][
				'documents_issued'] += s.total_documents_issued or 0

		# ✅ ANÁLISE DE COMPLIANCE REGIONAL
		doc_types_required = [dt for dt, info in PORTUGAL_DOCUMENT_TYPES.items()
							  if info.get('communication_required')]

		summary['regional_compliance'] = {
			'required_document_types': len(doc_types_required),
			'configured_required_types': len([dt for dt in doc_types_required
											  if dt in summary['by_document_type']]),
			'compliance_rate': 0
		}

		if summary['regional_compliance']['required_document_types'] > 0:
			summary['regional_compliance']['compliance_rate'] = round(
				(summary['regional_compliance']['configured_required_types'] /
				 summary['regional_compliance']['required_document_types']) * 100, 2
			)

		return summary

	except Exception as e:
		frappe.log_error(f"Erro ao obter resumo regional: {str(e)}")
		return {}


# ========== HOOKS REGIONAIS ==========

def on_company_update_regional(doc, method):
	"""
	✅ ATUALIZADO: Hook regional para atualização de empresa
	"""
	if doc.country == 'Portugal':
		validate_portugal_company_settings_safe(doc, method)


def on_customer_update_regional(doc, method):
	"""
	✅ ATUALIZADO: Hook regional para atualização de cliente
	"""
	if doc.country == 'Portugal':
		validate_portuguese_customer_enhanced(doc)


def on_supplier_update_regional(doc, method):
	"""
	✅ ATUALIZADO: Hook regional para atualização de fornecedor
	"""
	if doc.country == 'Portugal':
		validate_portuguese_supplier_enhanced(doc)


def on_address_update_regional(doc, method):
	"""
	✅ ATUALIZADO: Hook regional para atualização de endereço
	"""
	if doc.country == 'Portugal':
		validate_portuguese_address_enhanced(doc)


# ========== FUNÇÕES DE SETUP REGIONAIS ==========

def setup_portugal_compliance_for_company_regional(company):
	"""
	✅ ATUALIZADO: Setup regional de compliance (complementa document_hooks)
	"""
	if not is_portuguese_company_cached(company):
		frappe.throw(_("Empresa deve ser portuguesa com compliance ativo"))

	results = {}

	try:
		# ✅ CONFIGURAR CONTAS DE IMPOSTOS REGIONAIS
		tax_account = setup_tax_accounts_for_company_enhanced(company)
		results['tax_account'] = tax_account

		# ✅ CONFIGURAR DEFAULTS REGIONAIS
		company_doc = frappe.get_doc('Company', company)
		setup_portugal_regional_defaults(company_doc)
		company_doc.save(ignore_permissions=True)
		results['regional_defaults'] = True

		# ✅ VALIDAR CONFIGURAÇÃO FINAL
		validation_warnings = validate_portugal_settings_non_blocking(company_doc)
		results['validation_warnings'] = validation_warnings

		return {
			'success': True,
			'message': 'Configuração regional portuguesa aplicada com sucesso',
			'results': results
		}

	except Exception as e:
		frappe.log_error(f"Erro no setup regional: {str(e)}")
		return {
			'success': False,
			'error': str(e)
		}


# ========== APIS WHITELISTED REGIONAIS ==========

@frappe.whitelist()
def validate_nif_api(nif):
	"""✅ API regional para validar NIF"""
	try:
		return validate_portuguese_nif_enhanced(nif)
	except Exception as e:
		return {"valid": False, "error": str(e)}


@frappe.whitelist()
def validate_postal_code_api(postal_code):
	"""✅ API regional para validar código postal"""
	try:
		return validate_portuguese_postal_code(postal_code)
	except Exception as e:
		return {"valid": False, "error": str(e)}


@frappe.whitelist()
def get_tax_rates_api():
	"""✅ API regional para obter taxas de IVA"""
	try:
		return get_portugal_tax_rates_detailed()
	except Exception as e:
		return {"error": str(e)}


@frappe.whitelist()
def get_company_regional_summary_api(company):
	"""✅ API regional para resumo da empresa"""
	try:
		return get_company_series_summary_regional(company)
	except Exception as e:
		return {"error": str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Regional Configuration ATUALIZADO loaded - Version 2.1.0 - Regional Specific & Non-Blocking")
