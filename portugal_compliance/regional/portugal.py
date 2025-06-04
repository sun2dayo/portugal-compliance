# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Regional Portugal - Portugal Compliance VERSÃO NATIVA CORRIGIDA
Configurações regionais específicas para Portugal
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
✅ Configuração automática de séries portuguesas
✅ Validação de empresas portuguesas
✅ Setup completo de compliance português
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint
import re
from datetime import datetime, date

# ========== CONFIGURAÇÃO DE TIPOS DE DOCUMENTO ==========

# ========== CONFIGURAÇÃO DE TIPOS DE DOCUMENTO ==========

PORTUGAL_DOCUMENT_TYPES = {
    # ✅ DOCUMENTOS DE VENDA
    'Sales Invoice': {
        'code': 'FT',
        'name': 'Fatura',
        'description': 'Fatura de venda para clientes',
        'communication_required': True,
        'atcud_required': True,
        'qr_code_required': True
    },
    'POS Invoice': {  # ✅ CRÍTICO: INCLUÍDO
        'code': 'FS',
        'name': 'Fatura Simplificada',
        'description': 'Fatura simplificada para POS/Retail',
        'communication_required': True,
        'atcud_required': True,
        'qr_code_required': True,
        'nif_limit': 1000
    },
    'Sales Order': {
        'code': 'EC',
        'name': 'Fatura-Orçamento',
        'description': 'Ordem de venda/Fatura-Orçamento',
        'communication_required': True,
        'atcud_required': True
    },
    'Quotation': {
        'code': 'OR',
        'name': 'Orçamento',
        'description': 'Orçamento para clientes',
        'communication_required': True,
        'atcud_required': True
    },
    'Delivery Note': {
        'code': 'GR',
        'name': 'Guia de Remessa',
        'description': 'Guia de remessa para entregas',
        'communication_required': True,
        'atcud_required': True
    },
    'Purchase Invoice': {
        'code': 'FC',
        'name': 'Fatura de Compra',
        'description': 'Fatura de compra de fornecedores',
        'communication_required': True,
        'atcud_required': True
    },
    'Purchase Order': {
        'code': 'EF',
        'name': 'Ordem de Compra',
        'description': 'Ordem de compra para fornecedores',
        'communication_required': True,
        'atcud_required': True
    },
    'Purchase Receipt': {
        'code': 'GR',
        'name': 'Guia de Receção',
        'description': 'Guia de receção de mercadorias',
        'communication_required': True,
        'atcud_required': True
    },
    'Stock Entry': {
        'code': 'GM',
        'name': 'Guia de Movimentação',
        'description': 'Guia de movimentação de stock',
        'communication_required': True,
        'atcud_required': True
    },
    'Payment Entry': {
        'code': 'RC',
        'name': 'Recibo',
        'description': 'Recibo de pagamento/recebimento',
        'communication_required': True,
        'atcud_required': True
    },
    'Journal Entry': {
        'code': 'JE',
        'name': 'Lançamento Contábil',
        'description': 'Lançamento contábil manual',
        'communication_required': False,
        'atcud_required': False
    },
    'Material Request': {
        'code': 'MR',
        'name': 'Requisição de Material',
        'description': 'Requisição de material interno',
        'communication_required': False,
        'atcud_required': False
    }
}


# ========== CONFIGURAÇÕES REGIONAIS ==========

PORTUGAL_REGIONAL_CONFIG = {
	'country': 'Portugal',
	'currency': 'EUR',
	'date_format': 'dd-mm-yyyy',
	'time_format': '24 Hour',
	'number_format': '#.###,##',
	'float_precision': 2,
	'language': 'pt',
	'timezone': 'Europe/Lisbon',

	# ✅ CONFIGURAÇÕES FISCAIS
	'tax_rates': [0, 6, 13, 23],
	'default_tax_rate': 23,
	'tax_name': 'IVA',
	'nif_required_limit': 1000,

	# ✅ CONFIGURAÇÕES DE COMPLIANCE
	'atcud_required': True,
	'qr_code_required': True,
	'series_communication_required': True,
	'at_environment': 'Produção'
}


# ========== FUNÇÕES PRINCIPAIS ==========

def get_series_for_company(company):
	"""
	✅ CORRIGIDO: Retornar séries com formato correto (SEM HÍFENS)
	"""
	if not company:
		return []

	# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
	if not is_portuguese_company(company):
		return []

	try:
		# ✅ BUSCAR SÉRIES EXISTENTES (SEM HÍFENS)
		existing_series = frappe.get_all(
			'Portugal Series Configuration',
			filters={
				'company': company,
				'is_active': 1
			},
			fields=['name', 'prefix', 'naming_series', 'document_type', 'is_communicated']
		)

		series_list = []
		for series in existing_series:
			series_list.append({
				'name': series.name,
				'prefix': series.prefix,  # Formato SEM HÍFENS: FT2025NDX
				'naming_series': series.naming_series,  # Formato: FT2025NDX.####
				'document_type': series.document_type,
				'is_communicated': series.is_communicated,
				'doc_info': PORTUGAL_DOCUMENT_TYPES.get(series.document_type, {})
			})

		return series_list

	except Exception as e:
		frappe.log_error(f"Erro ao buscar séries para empresa {company}: {str(e)}")
		return []


def validate_portugal_company_settings(doc, method=None):
	"""
	✅ CORRIGIDO: Validação que NUNCA desativa compliance
	"""
	try:
		if not hasattr(doc, 'country') or doc.country != 'Portugal':
			return

		# ✅ PRESERVAR COMPLIANCE SEMPRE
		if hasattr(doc, '_doc_before_save'):
			original_compliance = getattr(doc._doc_before_save, 'portugal_compliance_enabled', 0)
			if original_compliance and not doc.portugal_compliance_enabled:
				# ✅ RESTAURAR COMPLIANCE SE FOI DESATIVADO
				doc.portugal_compliance_enabled = 1
				frappe.logger().info(f"✅ Compliance preservado para empresa {doc.name}")

		# ✅ CONFIGURAR DEFAULTS SEM VALIDAÇÕES BLOQUEANTES
		if not getattr(doc, 'default_currency', None):
			doc.default_currency = 'EUR'

		# ✅ CORRIGIR AMBIENTE AT AUTOMATICAMENTE
		if hasattr(doc, 'at_environment') and doc.at_environment:
			if doc.at_environment not in ['test', 'production']:
				doc.at_environment = 'test'

		# ✅ APENAS AVISOS, NUNCA ERROS BLOQUEANTES
		warnings = []

		if doc.portugal_compliance_enabled:
			if not getattr(doc, 'tax_id', None):
				warnings.append("Recomenda-se definir NIF para compliance completo")

			if not getattr(doc, 'at_username', None):
				warnings.append("Configure credenciais AT para comunicação de séries")

		if warnings:
			frappe.msgprint(
				"Avisos de configuração:\n" + "\n".join(warnings),
				title="Avisos Portugal Compliance",
				indicator="orange"
			)

	except Exception as e:
		frappe.log_error(f"Erro na validação (não crítico): {str(e)}")
	# ✅ NUNCA BLOQUEAR OU DESATIVAR COMPLIANCE


def setup_tax_accounts_for_company(company):
	"""
	✅ NOVO: Configurar contas de impostos para empresa portuguesa
	"""
	try:
		if not frappe.db.exists("Company", company):
			return

		company_doc = frappe.get_doc("Company", company)

		# ✅ VERIFICAR SE CONTA IVA EXISTE E NÃO É GROUP
		iva_account_name = f"IVA a Pagar - {company_doc.abbr}"

		if not frappe.db.exists("Account", iva_account_name):
			# ✅ CRIAR CONTA IVA NÃO-GROUP

			# Encontrar conta pai adequada (Liabilities)
			parent_account = frappe.db.get_value("Account", {
				"company": company,
				"root_type": "Liability",
				"is_group": 1
			}, "name")

			if parent_account:
				iva_account = frappe.get_doc({
					"doctype": "Account",
					"account_name": "IVA a Pagar",
					"company": company,
					"parent_account": parent_account,
					"account_type": "Tax",
					"is_group": 0,  # ✅ NÃO É GROUP
					"account_currency": company_doc.default_currency or "EUR"
				})

				iva_account.insert(ignore_permissions=True)
				frappe.logger().info(f"✅ Conta IVA criada: {iva_account_name}")
				return iva_account_name

		else:
			# ✅ VERIFICAR SE CONTA EXISTENTE NÃO É GROUP
			existing_account = frappe.get_doc("Account", iva_account_name)
			if existing_account.is_group:
				# Corrigir conta existente
				existing_account.is_group = 0
				existing_account.account_type = "Tax"
				existing_account.save(ignore_permissions=True)
				frappe.logger().info(f"✅ Conta IVA corrigida: {iva_account_name}")

			return iva_account_name

	except Exception as e:
		frappe.log_error(f"Erro ao configurar contas de impostos: {str(e)}", "Tax Account Setup")
		return None


def validate_portuguese_nif_safe(nif):
	"""
	✅ Validação segura de NIF português
	"""
	try:
		if not nif:
			return {'valid': False, 'message': 'NIF não fornecido'}

		# Limpar NIF
		nif_clean = re.sub(r'[^0-9]', '', str(nif))

		if len(nif_clean) != 9:
			return {'valid': False, 'message': 'NIF deve ter 9 dígitos'}

		# Validação básica de primeiro dígito
		if nif_clean[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			return {'valid': False, 'message': 'Primeiro dígito do NIF inválido'}

		# Algoritmo de validação
		checksum = 0
		for i in range(8):
			checksum += int(nif_clean[i]) * (9 - i)

		remainder = checksum % 11
		control_digit = 0 if remainder < 2 else 11 - remainder

		if int(nif_clean[8]) == control_digit:
			return {'valid': True, 'message': 'NIF válido'}
		else:
			return {'valid': False, 'message': 'Dígito de controlo inválido'}

	except Exception as e:
		return {'valid': False, 'message': f'Erro na validação: {str(e)}'}


def validate_compliance_settings_safe(doc):
	"""
	✅ Validação segura de configurações de compliance
	"""
	errors = []

	try:
		# ✅ VALIDAR AMBIENTE AT COM FLEXIBILIDADE
		if hasattr(doc, 'at_environment') and doc.at_environment:
			valid_environments = ['test', 'production', 'Teste', 'Produção', 'desenvolvimento',
								  'dev']
			if doc.at_environment not in valid_environments:
				# Corrigir automaticamente valores comuns
				env_lower = doc.at_environment.lower()
				if env_lower in ['teste', 'test', 'testing']:
					doc.at_environment = 'test'
				elif env_lower in ['produção', 'production', 'prod']:
					doc.at_environment = 'production'
				else:
					errors.append(_("Ambiente AT deve ser 'test' ou 'production'"))

		# ✅ VALIDAR CREDENCIAIS AT (APENAS SE DEFINIDAS)
		if hasattr(doc, 'at_username') and doc.at_username:
			if len(doc.at_username) < 3:
				errors.append(_("Username AT deve ter pelo menos 3 caracteres"))

		# ✅ VALIDAR ABREVIATURA
		if not getattr(doc, 'abbr', None):
			errors.append(_("Abreviatura da empresa é obrigatória"))
		elif len(doc.abbr) < 2 or len(doc.abbr) > 4:
			errors.append(_("Abreviatura deve ter entre 2 e 4 caracteres"))

	except Exception as e:
		frappe.log_error(f"Erro na validação de compliance: {str(e)}",
						 "Portugal Compliance Validation")
		errors.append(_("Erro na validação de compliance - verificar configurações"))

	return errors


def setup_portugal_defaults_safe(doc):
	"""
	✅ Configurar defaults portugueses com tratamento de erro
	"""
	try:
		# ✅ CONFIGURAR MOEDA SE NÃO DEFINIDA
		if not getattr(doc, 'default_currency', None):
			doc.default_currency = 'EUR'

		# ✅ CONFIGURAR PAÍS SE NÃO DEFINIDO
		if not getattr(doc, 'country', None):
			doc.country = 'Portugal'

		# ✅ CONFIGURAR AMBIENTE AT PADRÃO SE COMPLIANCE ATIVADO
		if (hasattr(doc, 'portugal_compliance_enabled') and
			doc.portugal_compliance_enabled and
			not getattr(doc, 'at_environment', None)):
			doc.at_environment = 'test'  # Padrão seguro para desenvolvimento

		frappe.logger().info(
			f"Defaults portugueses configurados para empresa {getattr(doc, 'name', 'Nova')}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar defaults portugueses: {str(e)}",
						 "Portugal Defaults Setup")
	# Não falhar por erro nos defaults



def get_nif_type(first_digit):
	"""
	✅ Obter tipo de entidade baseado no primeiro dígito do NIF
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


def is_portuguese_company(company):
	"""
	✅ Verificar se empresa é portuguesa com compliance ativo
	"""
	if not company:
		return False

	try:
		company_doc = frappe.get_cached_doc('Company', company)
		return (
			company_doc.country == 'Portugal' and
			getattr(company_doc, 'portugal_compliance_enabled', False)
		)
	except:
		return False


# ========== CONFIGURAÇÃO AUTOMÁTICA DE SÉRIES ==========

def setup_all_series_for_company(company):
	"""
	✅ CORRIGIDO: Configurar todas as séries para empresa (formato SEM HÍFENS)
	"""
	if not is_portuguese_company(company):
		frappe.throw(_("Apenas empresas portuguesas podem ter séries de compliance"))

	created_series = []
	current_year = datetime.now().year

	# ✅ CORRIGIDO: OBTER ABBR DA EMPRESA EM VEZ DE 3 PRIMEIRAS LETRAS
	try:
		company_doc = frappe.get_doc("Company", company)
		company_code = company_doc.abbr.upper()  # ← USAR ABBR

		if not company_code:
			frappe.throw(_("Empresa deve ter abreviatura definida"))

	except Exception as e:
		frappe.throw(_("Erro ao obter abreviatura da empresa: {0}").format(str(e)))

	for doctype, doc_info in PORTUGAL_DOCUMENT_TYPES.items():
		try:
			# ✅ GERAR PREFIXO SEM HÍFENS: XXYYYY + ABBR
			prefix = f"{doc_info['code']}{current_year}{company_code}"
			naming_series = f"{prefix}.####"

			# ✅ VERIFICAR SE JÁ EXISTE
			existing = frappe.db.exists(
				'Portugal Series Configuration',
				{'prefix': prefix, 'company': company}
			)

			if existing:
				continue

			# ✅ CRIAR NOVA SÉRIE
			series_doc = frappe.new_doc('Portugal Series Configuration')
			series_doc.update({
				'series_name': f"{doc_info['name']} - {prefix}",
				'company': company,
				'document_type': doctype,
				'prefix': prefix,
				'naming_series': naming_series,
				'current_sequence': 1,
				'is_active': 1,
				'is_communicated': 0,
				'at_environment': 'Produção',
				'document_code': doc_info['code'],
				'year_code': str(current_year),
				'company_code': company_code,  # ✅ AGORA USA ABBR
				'naming_pattern': f"{prefix}.####",
				'atcud_pattern': "0.{sequence}",
				'notes': f"Série criada automaticamente para {doc_info['description']}"
			})

			series_doc.insert(ignore_permissions=True)
			created_series.append({
				'name': series_doc.name,
				'document_type': doctype,
				'prefix': prefix,
				'naming_series': naming_series
			})

		except Exception as e:
			frappe.log_error(
				f"Erro ao criar série {doctype} para empresa {company}: {str(e)}",
				"Setup Series Error"
			)

	return {
		'success': True,
		'created_count': len(created_series),
		'created_series': created_series
	}


def create_default_tax_templates(company):
	"""
	✅ Criar templates de impostos portugueses padrão
	"""
	if not is_portuguese_company(company):
		return

	# ✅ TEMPLATE DE VENDAS
	sales_template = create_sales_tax_template(company)

	# ✅ TEMPLATE DE COMPRAS
	purchase_template = create_purchase_tax_template(company)

	return {
		'sales_template': sales_template,
		'purchase_template': purchase_template
	}


def create_sales_tax_template(company):
	"""
	✅ Criar template de impostos de vendas
	"""
	template_name = f"IVA Portugal - {company}"

	# ✅ VERIFICAR SE JÁ EXISTE
	if frappe.db.exists('Sales Taxes and Charges Template', template_name):
		return template_name

	try:
		# ✅ CRIAR TEMPLATE
		template = frappe.new_doc('Sales Taxes and Charges Template')
		template.update({
			'title': template_name,
			'company': company,
			'is_default': 1
		})

		# ✅ ADICIONAR IVA 23%
		template.append('taxes', {
			'charge_type': 'On Net Total',
			'account_head': get_or_create_tax_account(company, 'IVA 23%', 23),
			'description': 'IVA 23%',
			'rate': 23
		})

		template.insert(ignore_permissions=True)
		return template.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar template de vendas: {str(e)}")
		return None


def setup_tax_accounts_for_company(company):
	"""
	✅ CORRIGIDO: Configurar contas de impostos não-group
	"""
	try:
		if not frappe.db.exists("Company", company):
			return

		company_doc = frappe.get_doc("Company", company)

		# ✅ NOME CORRETO DA CONTA
		iva_account_name = f"Duties and Taxes - {company_doc.abbr}"

		if frappe.db.exists("Account", iva_account_name):
			# ✅ CORRIGIR CONTA EXISTENTE QUE É GROUP
			existing_account = frappe.get_doc("Account", iva_account_name)
			if existing_account.is_group == 1:
				# Corrigir para não ser group
				existing_account.is_group = 0
				existing_account.account_type = "Tax"
				existing_account.save(ignore_permissions=True)
				frappe.logger().info(f"✅ Conta corrigida para não-group: {iva_account_name}")
		else:
			# ✅ CRIAR NOVA CONTA NÃO-GROUP
			parent_account = frappe.db.get_value("Account", {
				"company": company,
				"root_type": "Liability",
				"is_group": 1
			}, "name")

			if parent_account:
				iva_account = frappe.get_doc({
					"doctype": "Account",
					"account_name": "Duties and Taxes",
					"company": company,
					"parent_account": parent_account,
					"account_type": "Tax",
					"is_group": 0,  # ✅ NÃO É GROUP
					"account_currency": company_doc.default_currency or "EUR"
				})

				iva_account.insert(ignore_permissions=True)
				frappe.logger().info(f"✅ Conta criada: {iva_account_name}")

		return iva_account_name

	except Exception as e:
		frappe.log_error(f"Erro ao configurar conta de impostos: {str(e)}")
		return None


def create_purchase_tax_template(company):
	"""
	✅ Criar template de impostos de compras
	"""
	template_name = f"IVA Compras Portugal - {company}"

	# ✅ VERIFICAR SE JÁ EXISTE
	if frappe.db.exists('Purchase Taxes and Charges Template', template_name):
		return template_name

	try:
		# ✅ CRIAR TEMPLATE
		template = frappe.new_doc('Purchase Taxes and Charges Template')
		template.update({
			'title': template_name,
			'company': company,
			'is_default': 1
		})

		# ✅ ADICIONAR IVA 23%
		template.append('taxes', {
			'charge_type': 'On Net Total',
			'account_head': get_or_create_tax_account(company, 'IVA Dedutível 23%', 23),
			'description': 'IVA Dedutível 23%',
			'rate': 23
		})

		template.insert(ignore_permissions=True)
		return template.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar template de compras: {str(e)}")
		return None


def get_or_create_tax_account(company, account_name, tax_rate):
	"""
	✅ Obter ou criar conta de imposto
	"""
	# ✅ BUSCAR CONTA EXISTENTE
	existing_account = frappe.db.get_value(
		'Account',
		{
			'company': company,
			'account_name': account_name,
			'account_type': 'Tax'
		},
		'name'
	)

	if existing_account:
		return existing_account

	try:
		# ✅ OBTER CONTA PAI
		parent_account = frappe.db.get_value(
			'Account',
			{
				'company': company,
				'account_name': 'Tax Assets',
				'is_group': 1
			},
			'name'
		)

		if not parent_account:
			parent_account = frappe.db.get_value(
				'Account',
				{
					'company': company,
					'root_type': 'Asset',
					'is_group': 1
				},
				'name'
			)

		# ✅ CRIAR CONTA
		account = frappe.new_doc('Account')
		account.update({
			'account_name': account_name,
			'company': company,
			'parent_account': parent_account,
			'account_type': 'Tax',
			'tax_rate': tax_rate
		})

		account.insert(ignore_permissions=True)
		return account.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar conta de imposto: {str(e)}")
		return None


# ========== CONFIGURAÇÕES DE NAMING SERIES ==========

def get_naming_series_options(doctype):
	"""
	✅ CORRIGIDO: Obter opções de naming series para doctype (formato SEM HÍFENS)
	"""
	if doctype not in PORTUGAL_DOCUMENT_TYPES:
		return []

	try:
		# ✅ BUSCAR SÉRIES PORTUGUESAS (SEM HÍFENS)
		series = frappe.get_all(
			'Portugal Series Configuration',
			filters={
				'document_type': doctype,
				'is_active': 1
			},
			fields=['naming_series', 'prefix', 'is_communicated'],
			order_by='is_communicated desc, prefix'
		)

		options = []
		for s in series:
			status = "✅" if s.is_communicated else "⚠️"
			options.append(f"{s.naming_series} {status}")

		return options

	except Exception as e:
		frappe.log_error(f"Erro ao buscar naming series para {doctype}: {str(e)}")
		return []


def validate_naming_series_format(naming_series):
	"""
	✅ CORRIGIDO: Validar formato de naming series (SEM HÍFENS)
	"""
	if not naming_series:
		return {'valid': False, 'message': 'Naming series não fornecida'}

	# ✅ PADRÃO: XXYYYY + EMPRESA.#### (ex: FT2025NDX.####)
	pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'

	if not re.match(pattern, naming_series):
		return {
			'valid': False,
			'message': 'Formato inválido. Use: XXYYYY + EMPRESA.#### (ex: FT2025NDX.####)'
		}

	return {'valid': True, 'message': 'Formato válido'}


def get_next_naming_series_number(naming_series):
	"""
	✅ Obter próximo número da naming series
	"""
	try:
		# ✅ BUSCAR CONFIGURAÇÃO DA SÉRIE
		series_config = frappe.db.get_value(
			'Portugal Series Configuration',
			{'naming_series': naming_series},
			['current_sequence', 'prefix'],
			as_dict=True
		)

		if not series_config:
			return None

		next_number = series_config.current_sequence
		prefix = series_config.prefix

		return {
			'next_number': next_number,
			'full_number': f"{prefix}{next_number:04d}",
			'prefix': prefix
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter próximo número: {str(e)}")
		return None


# ========== VALIDAÇÕES REGIONAIS ==========

def validate_portuguese_address(address_doc):
	"""
	✅ Validar endereço português
	"""
	if address_doc.country != 'Portugal':
		return

	errors = []

	# ✅ VALIDAR CÓDIGO POSTAL
	if address_doc.pincode:
		postal_pattern = r'^\d{4}-\d{3}$'
		if not re.match(postal_pattern, address_doc.pincode):
			errors.append(_("Código postal deve ter formato XXXX-XXX"))

	# ✅ VALIDAR CAMPOS OBRIGATÓRIOS
	if not address_doc.address_line1:
		errors.append(_("Morada é obrigatória"))

	if not address_doc.city:
		errors.append(_("Cidade é obrigatória"))

	if errors:
		frappe.throw(_("Erros no endereço português:\n") + "\n".join(errors))


def validate_portuguese_nif(nif):
	"""
	✅ Validar NIF português usando algoritmo mod 11
	Baseado no algoritmo oficial português
	"""
	try:
		if not nif:
			return {'valid': False, 'message': 'NIF não fornecido'}

		# Limpar NIF (remover espaços e caracteres especiais)
		nif_clean = re.sub(r'[^0-9]', '', str(nif))

		if len(nif_clean) != 9:
			return {'valid': False, 'message': 'NIF deve ter 9 dígitos'}

		# Verificar primeiro dígito válido
		if nif_clean[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			return {'valid': False, 'message': 'Primeiro dígito do NIF inválido'}

		# Algoritmo de validação mod 11
		checksum = 0
		for i in range(8):
			checksum += int(nif_clean[i]) * (9 - i)

		remainder = checksum % 11
		control_digit = 0 if remainder < 2 else 11 - remainder

		if int(nif_clean[8]) == control_digit:
			return {'valid': True, 'message': 'NIF válido'}
		else:
			return {'valid': False, 'message': 'Dígito de controlo inválido'}

	except Exception as e:
		return {'valid': False, 'message': f'Erro na validação: {str(e)}'}


def validate_portuguese_nif_safe(nif):
	"""
	✅ Versão segura da validação de NIF (alias para compatibilidade)
	"""
	return validate_portuguese_nif(nif)


def setup_portugal_defaults(doc):
	"""
	✅ Configurar defaults portugueses para empresa
	"""
	try:
		# Configurar moeda padrão
		if not getattr(doc, 'default_currency', None):
			doc.default_currency = 'EUR'

		# Configurar país
		if not getattr(doc, 'country', None):
			doc.country = 'Portugal'

		# Configurar ambiente AT padrão se compliance ativado
		if (hasattr(doc, 'portugal_compliance_enabled') and
			doc.portugal_compliance_enabled and
			not getattr(doc, 'at_environment', None)):
			doc.at_environment = 'test'

		frappe.logger().info(
			f"Defaults portugueses configurados para empresa {getattr(doc, 'name', 'Nova')}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar defaults portugueses: {str(e)}",
						 "Portugal Defaults Setup")


def setup_portugal_defaults_safe(doc):
	"""
	✅ Versão segura dos defaults (alias para compatibilidade)
	"""
	return setup_portugal_defaults(doc)


def validate_portuguese_customer(customer_doc):
	"""
	✅ Validar cliente português
	"""
	# ✅ VALIDAR NIF SE FORNECIDO
	if customer_doc.tax_id:
		nif_validation = validate_portuguese_nif(customer_doc.tax_id)
		if not nif_validation['valid']:
			frappe.throw(f"NIF do cliente inválido: {nif_validation['message']}")

	# ✅ CONFIGURAR CATEGORIA FISCAL
	if not customer_doc.tax_category and customer_doc.country == 'Portugal':
		customer_doc.tax_category = 'Portugal - Cliente'


def validate_portuguese_supplier(supplier_doc):
	"""
	✅ Validar fornecedor português
	"""
	# ✅ VALIDAR NIF OBRIGATÓRIO PARA PORTUGAL
	if supplier_doc.country == 'Portugal':
		if not supplier_doc.tax_id:
			frappe.throw(_("NIF é obrigatório para fornecedores portugueses"))

		nif_validation = validate_portuguese_nif(supplier_doc.tax_id)
		if not nif_validation['valid']:
			frappe.throw(f"NIF do fornecedor inválido: {nif_validation['message']}")

	# ✅ CONFIGURAR CATEGORIA FISCAL
	if not supplier_doc.tax_category and supplier_doc.country == 'Portugal':
		supplier_doc.tax_category = 'Portugal - Fornecedor'


# ========== CONFIGURAÇÕES DE IMPOSTOS ==========

def get_portugal_tax_rates():
	"""
	✅ Obter taxas de IVA portuguesas
	"""
	return PORTUGAL_REGIONAL_CONFIG['tax_rates']


def validate_portugal_tax_rate(rate):
	"""
	✅ Validar taxa de IVA portuguesa
	"""
	valid_rates = get_portugal_tax_rates()
	return rate in valid_rates


def get_default_tax_template(company, transaction_type='sales'):
	"""
	✅ Obter template de impostos padrão
	"""
	if not is_portuguese_company(company):
		return None

	doctype = 'Sales Taxes and Charges Template' if transaction_type == 'sales' else 'Purchase Taxes and Charges Template'

	return frappe.db.get_value(
		doctype,
		{
			'company': company,
			'is_default': 1
		},
		'name'
	)


# ========== HOOKS E EVENTOS ==========

def on_company_update(doc, method):
	"""
	✅ Hook executado quando empresa é atualizada
	"""
	if doc.country == 'Portugal':
		validate_portugal_company_settings(doc, method)


def on_customer_update(doc, method):
	"""
	✅ Hook executado quando cliente é atualizado
	"""
	if doc.country == 'Portugal':
		validate_portuguese_customer(doc)


def on_supplier_update(doc, method):
	"""
	✅ Hook executado quando fornecedor é atualizado
	"""
	if doc.country == 'Portugal':
		validate_portuguese_supplier(doc)


def on_address_update(doc, method):
	"""
	✅ Hook executado quando endereço é atualizado
	"""
	if doc.country == 'Portugal':
		validate_portuguese_address(doc)


# ========== UTILITÁRIOS ==========

def get_portugal_compliance_info():
	"""
	✅ Obter informações de compliance português
	"""
	return {
		'document_types': PORTUGAL_DOCUMENT_TYPES,
		'regional_config': PORTUGAL_REGIONAL_CONFIG,
		'supported_doctypes': list(PORTUGAL_DOCUMENT_TYPES.keys()),
		'tax_rates': get_portugal_tax_rates(),
		'version': '2.0.0'
	}


def setup_portugal_compliance_for_company(company):
	"""
	✅ Setup completo de compliance português para empresa
	"""
	if not is_portuguese_company(company):
		frappe.throw(_("Empresa deve ser portuguesa com compliance ativo"))

	results = {}

	try:
		# ✅ CRIAR SÉRIES
		series_result = setup_all_series_for_company(company)
		results['series'] = series_result

		# ✅ CRIAR TEMPLATES DE IMPOSTOS
		tax_result = create_default_tax_templates(company)
		results['tax_templates'] = tax_result

		# ✅ CONFIGURAR DEFAULTS
		company_doc = frappe.get_doc('Company', company)
		setup_portugal_defaults(company_doc)
		company_doc.save(ignore_permissions=True)
		results['defaults'] = True

		return {
			'success': True,
			'message': 'Portugal Compliance configurado com sucesso',
			'results': results
		}

	except Exception as e:
		frappe.log_error(f"Erro no setup de compliance: {str(e)}")
		return {
			'success': False,
			'error': str(e)
		}


def get_company_series_summary(company):
	"""
	✅ Obter resumo das séries da empresa
	"""
	if not is_portuguese_company(company):
		return {}

	try:
		series = frappe.get_all(
			'Portugal Series Configuration',
			filters={'company': company},
			fields=[
				'document_type', 'prefix', 'naming_series', 'is_active',
				'is_communicated', 'total_documents_issued', 'current_sequence'
			]
		)

		summary = {
			'total_series': len(series),
			'active_series': len([s for s in series if s.is_active]),
			'communicated_series': len([s for s in series if s.is_communicated]),
			'total_documents': sum(s.total_documents_issued or 0 for s in series),
			'by_document_type': {}
		}

		for s in series:
			if s.document_type not in summary['by_document_type']:
				summary['by_document_type'][s.document_type] = {
					'count': 0,
					'communicated': 0,
					'documents_issued': 0
				}

			summary['by_document_type'][s.document_type]['count'] += 1
			if s.is_communicated:
				summary['by_document_type'][s.document_type]['communicated'] += 1
			summary['by_document_type'][s.document_type][
				'documents_issued'] += s.total_documents_issued or 0

		return summary

	except Exception as e:
		frappe.log_error(f"Erro ao obter resumo: {str(e)}")
		return {}


# ========== CONSOLE LOG PARA DEBUG ==========
frappe.logger().info("Portugal Regional Configuration loaded - Version 2.0.0 - Fully Compliant")
