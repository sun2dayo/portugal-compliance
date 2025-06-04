# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, getdate


def validate_portugal_settings(doc, method=None):
	"""
	Valida configurações portuguesas da empresa
	"""
	try:
		# Verificar se Portugal Compliance está ativo
		if not getattr(doc, 'portugal_compliance_enabled', False):
			return

		# Validar país
		if doc.country != 'Portugal':
			frappe.throw(_("Portugal Compliance can only be enabled for companies in Portugal"))

		# Validar NIF
		if not doc.tax_id:
			frappe.throw(_("Tax ID (NIF) is required for Portuguese companies"))

		# Validar formato do NIF
		if not validate_portuguese_nif(doc.tax_id):
			frappe.throw(_("Invalid Portuguese NIF format: {0}").format(doc.tax_id))

		# Validar moeda
		if doc.default_currency != 'EUR':
			frappe.msgprint(
				_("Default currency should be EUR for Portuguese companies"),
				indicator="orange",
				title=_("Currency Warning")
			)

		# Criar configurações padrão se necessário
		create_default_configurations(doc)

	except Exception as e:
		frappe.log_error(f"Error validating Portugal settings: {str(e)}")


def validate_portuguese_nif(nif):
	"""
	Valida formato do NIF português
	"""
	try:
		if not nif:
			return False

		# Remover espaços e caracteres não numéricos
		import re
		nif = re.sub(r'[^\d]', '', str(nif))

		# Verificar se tem 9 dígitos
		if len(nif) != 9:
			return False

		# Verificar se começa com dígito válido
		if nif[0] not in '123456789':
			return False

		# Calcular dígito de controlo
		check_sum = 0
		for i in range(8):
			check_sum += int(nif[i]) * (9 - i)

		remainder = check_sum % 11
		check_digit = 0 if remainder < 2 else 11 - remainder

		return int(nif[8]) == check_digit

	except Exception:
		return False


def create_default_configurations(company_doc):
	"""
	Cria configurações padrão para empresa portuguesa
	"""
	try:
		# Criar séries padrão se não existirem
		create_default_series(company_doc)

		# Criar configurações de autenticação se necessário
		create_default_auth_settings(company_doc)

	except Exception as e:
		frappe.log_error(f"Error creating default configurations: {str(e)}")


def create_default_series(company_doc):
	"""
	Cria séries padrão para a empresa
	"""
	try:
		current_year = getdate().year
		company_abbr = company_doc.abbr.upper()

		default_series = [
			{
				'series_name': f'FT-{current_year}-{company_abbr}',
				'document_type': 'Sales Invoice',
				'prefix': f'FT-{current_year}-{company_abbr}'
			},
			{
				'series_name': f'FC-{current_year}-{company_abbr}',
				'document_type': 'Purchase Invoice',
				'prefix': f'FC-{current_year}-{company_abbr}'
			},
			{
				'series_name': f'RC-{current_year}-{company_abbr}',
				'document_type': 'Payment Entry',
				'prefix': f'RC-{current_year}-{company_abbr}'
			},
			{
				'series_name': f'GT-{current_year}-{company_abbr}',
				'document_type': 'Delivery Note',
				'prefix': f'GT-{current_year}-{company_abbr}'
			}
		]

		for series_data in default_series:
			try:
				# Verificar se série já existe
				existing = frappe.db.exists('Portugal Series Configuration', {
					'series_name': series_data['series_name'],
					'company': company_doc.name
				})

				if not existing:
					series_doc = frappe.get_doc({
						'doctype': 'Portugal Series Configuration',
						'series_name': series_data['series_name'],
						'document_type': series_data['document_type'],
						'prefix': series_data['prefix'],
						'company': company_doc.name,
						'current_sequence': 1,
						'is_active': 1,
						'is_communicated': 0
					})

					# Usar ignore_links para evitar validação de utilizadores
					series_doc.insert(ignore_permissions=True, ignore_links=True)

			except Exception as series_error:
				frappe.log_error(
					f"Error creating series {series_data['series_name']}: {str(series_error)}")
				continue

		frappe.msgprint(
			_("Default Portugal series created for company {0}").format(company_doc.company_name),
			indicator="green",
			title=_("Series Created")
		)

	except Exception as e:
		frappe.log_error(f"Error creating default series: {str(e)}")


def create_default_configurations(company_doc):
	"""
	Cria configurações padrão para empresa portuguesa
	"""
	try:
		# Criar séries padrão se não existirem
		create_default_series(company_doc)

		# Verificar se DocType de autenticação existe antes de criar
		if frappe.db.table_exists('tabPortugal Auth Settings'):
			create_default_auth_settings(company_doc)
		else:
			frappe.logger().info("Portugal Auth Settings DocType not available")

	except Exception as e:
		frappe.log_error(f"Error creating default configurations: {str(e)}")


def create_default_auth_settings(company_doc):
	"""
	Cria configurações de autenticação padrão (apenas se DocType existir)
	"""
	try:
		# Verificar se já existe configuração de autenticação
		existing_auth = frappe.db.exists('Portugal Auth Settings', {
			'company': company_doc.name
		})

		if not existing_auth:
			# Tentar criar apenas se DocType existir
			auth_doc = frappe.get_doc({
				'doctype': 'Portugal Auth Settings',
				'company': company_doc.name,
				'environment': 'Test',
				'is_active': 0
			})
			auth_doc.insert(ignore_permissions=True)

			frappe.msgprint(
				_("Default authentication settings created. Please configure AT credentials."),
				indicator="green",
				title=_("Auth Settings Created")
			)

	except Exception as e:
		# Log do erro mas não bloquear o processo
		frappe.logger().error(f"Could not create auth settings: {str(e)}")


def on_company_update(doc, method=None):
	"""
	Hook executado quando empresa é atualizada
	"""
	try:
		# Validar configurações portuguesas
		validate_portugal_settings(doc, method)

		# Atualizar cache de empresas com compliance
		update_compliance_cache(doc)

	except Exception as e:
		frappe.log_error(f"Error in company update hook: {str(e)}")


def update_compliance_cache(company_doc):
	"""
	Atualiza cache de empresas com compliance ativo
	"""
	try:
		if getattr(company_doc, 'portugal_compliance_enabled', False):
			# Adicionar ao cache de empresas com compliance
			compliance_companies = frappe.cache.get('portugal_compliance_companies') or []

			if company_doc.name not in compliance_companies:
				compliance_companies.append(company_doc.name)
				frappe.cache.set('portugal_compliance_companies', compliance_companies,
								 expires_in_sec=3600)
		else:
			# Remover do cache se compliance foi desativado
			compliance_companies = frappe.cache.get('portugal_compliance_companies') or []

			if company_doc.name in compliance_companies:
				compliance_companies.remove(company_doc.name)
				frappe.cache.set('portugal_compliance_companies', compliance_companies,
								 expires_in_sec=3600)

	except Exception as e:
		frappe.log_error(f"Error updating compliance cache: {str(e)}")


@frappe.whitelist()
def validate_company_nif(nif):
	"""
	Endpoint para validar NIF da empresa
	"""
	try:
		is_valid = validate_portuguese_nif(nif)
		return {
			'valid': is_valid,
			'message': _('Valid Portuguese NIF') if is_valid else _('Invalid Portuguese NIF')
		}
	except Exception as e:
		return {
			'valid': False,
			'message': str(e)
		}


@frappe.whitelist()
def get_company_compliance_status(company):
	"""
	Obtém status de compliance da empresa
	"""
	try:
		company_doc = frappe.get_doc('Company', company)

		status = {
			'compliance_enabled': getattr(company_doc, 'portugal_compliance_enabled', False),
			'has_nif': bool(company_doc.tax_id),
			'nif_valid': validate_portuguese_nif(
				company_doc.tax_id) if company_doc.tax_id else False,
			'country_portugal': company_doc.country == 'Portugal',
			'currency_eur': company_doc.default_currency == 'EUR'
		}

		# Verificar séries configuradas
		series_count = frappe.db.count('Portugal Series Configuration', {
			'company': company,
			'is_active': 1
		})

		status['has_series'] = series_count > 0
		status['series_count'] = series_count

		# Verificar autenticação configurada
		auth_configured = frappe.db.exists('Portugal Auth Settings', {
			'company': company,
			'is_active': 1
		})

		status['auth_configured'] = bool(auth_configured)

		return status

	except Exception as e:
		frappe.log_error(f"Error getting company compliance status: {str(e)}")
		return {'error': str(e)}
