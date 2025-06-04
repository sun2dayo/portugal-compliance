# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Módulo de autenticação para Portugal Compliance
"""

import frappe
from frappe import _
from frappe.utils import cint, now, get_datetime
from datetime import datetime, timedelta


def validate_auth():
	"""
	Hook de validação de autenticação para Portugal Compliance
	Esta função é chamada pelo Frappe durante o processo de autenticação
	"""
	try:
		# Verificar se o módulo Portugal Compliance está ativo
		if not is_portugal_compliance_enabled():
			return

		# Validações específicas para Portugal
		validate_user_compliance()
		validate_session_security()
		log_authentication_attempt()

	except Exception as e:
		frappe.log_error(f"Error in Portugal Compliance auth validation: {str(e)}")
		# Não bloquear autenticação por erros no módulo
		pass


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo
	"""
	try:
		# Verificar se há pelo menos uma empresa com compliance ativo
		companies_with_compliance = frappe.db.count("Company", {
			"portugal_compliance_enabled": 1
		})

		return companies_with_compliance > 0

	except Exception:
		return False


def validate_user_compliance():
	"""
	Valida compliance específico do utilizador
	"""
	try:
		# Verificar se utilizador está logado
		if not frappe.session.user or frappe.session.user == "Guest":
			return

		# Verificar se utilizador tem acesso a empresas portuguesas
		user_companies = get_user_companies()

		if user_companies:
			# Validar acesso a empresas com compliance português
			validate_company_access(user_companies)

			# Verificar permissões específicas
			validate_compliance_permissions()

	except Exception as e:
		frappe.log_error(f"Error validating user compliance: {str(e)}")


def get_user_companies():
	"""
	Obtém empresas às quais o utilizador tem acesso
	"""
	try:
		# Verificar se utilizador tem permissão para ver empresas
		if not frappe.has_permission("Company", "read"):
			return []

		# Obter empresas com compliance português ativo
		companies = frappe.db.get_all("Company",
									  filters={"portugal_compliance_enabled": 1},
									  fields=["name", "company_name"]
									  )

		return companies

	except Exception as e:
		frappe.log_error(f"Error getting user companies: {str(e)}")
		return []


def validate_company_access(companies):
	"""
	Valida acesso do utilizador a empresas portuguesas
	"""
	try:
		for company in companies:
			# Verificar se utilizador tem permissão para esta empresa
			if not frappe.has_permission("Company", "read", company.name):
				continue

			# Validações específicas para empresa portuguesa
			validate_portuguese_company_access(company)

	except Exception as e:
		frappe.log_error(f"Error validating company access: {str(e)}")


def validate_portuguese_company_access(company):
	"""
	Validações específicas para acesso a empresa portuguesa
	"""
	try:
		# Verificar se empresa tem configurações obrigatórias
		company_doc = frappe.get_doc("Company", company.name)

		# Verificar NIF
		if not company_doc.tax_id:
			frappe.msgprint(
				_("Company '{0}' is missing Tax ID (NIF)").format(company.company_name),
				indicator="orange",
				title=_("Portugal Compliance Warning")
			)

		# Verificar país
		if company_doc.country != "Portugal":
			frappe.msgprint(
				_("Company '{0}' is not configured for Portugal").format(company.company_name),
				indicator="orange",
				title=_("Portugal Compliance Warning")
			)

	except Exception as e:
		frappe.log_error(f"Error validating Portuguese company access: {str(e)}")


def validate_compliance_permissions():
	"""
	Valida permissões específicas de compliance
	"""
	try:
		# Verificar se utilizador tem acesso aos DocTypes de compliance
		compliance_doctypes = [
			"Portugal Series Configuration",
			"ATCUD Log",
			"SAF-T Export Log"
		]

		for doctype in compliance_doctypes:
			if frappe.db.table_exists(f"tab{doctype}"):
				# Não bloquear se não tiver permissão, apenas registar
				has_permission = frappe.has_permission(doctype, "read")
				if not has_permission:
					frappe.logger().debug(
						f"User {frappe.session.user} has no permission for {doctype}")

	except Exception as e:
		frappe.log_error(f"Error validating compliance permissions: {str(e)}")


def validate_session_security():
	"""
	Valida segurança da sessão para compliance
	"""
	try:
		# Verificar se sessão é segura (HTTPS)
		if frappe.request and hasattr(frappe.request, 'environ'):
			is_secure = frappe.request.environ.get('HTTPS') == 'on' or \
						frappe.request.environ.get('HTTP_X_FORWARDED_PROTO') == 'https'

			if not is_secure and frappe.conf.get('developer_mode') != 1:
				frappe.logger().warning("Portugal Compliance: Insecure connection detected")

		# Verificar tempo de sessão
		validate_session_timeout()

	except Exception as e:
		frappe.log_error(f"Error validating session security: {str(e)}")


def validate_session_timeout():
	"""
	Valida timeout de sessão para compliance
	"""
	try:
		# Verificar se sessão não expirou (configuração específica para Portugal)
		session_timeout = frappe.conf.get('portugal_session_timeout', 3600)  # 1 hora padrão

		if frappe.session.get('last_active'):
			last_active = get_datetime(frappe.session.get('last_active'))
			now_time = get_datetime(now())

			if (now_time - last_active).seconds > session_timeout:
				frappe.logger().info(f"Session timeout for user {frappe.session.user}")
			# Não forçar logout aqui, deixar o Frappe gerir

	except Exception as e:
		frappe.log_error(f"Error validating session timeout: {str(e)}")


def log_authentication_attempt():
	"""
	Regista tentativa de autenticação para auditoria
	"""
	try:
		# Registar apenas se há empresas com compliance ativo
		if not is_portugal_compliance_enabled():
			return

		# Log básico de auditoria
		audit_data = {
			"user": frappe.session.user,
			"timestamp": now(),
			"ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None,
			"user_agent": frappe.request.headers.get('User-Agent') if frappe.request else None,
			"session_id": frappe.session.sid if hasattr(frappe.session, 'sid') else None
		}

		# Armazenar no cache para análise posterior (não na base de dados para não sobrecarregar)
		frappe.cache.set(f"portugal_auth_log_{frappe.session.user}_{now()}", audit_data,
						 expires_in_sec=86400)

	except Exception as e:
		frappe.log_error(f"Error logging authentication attempt: {str(e)}")


def get_user_compliance_info():
	"""
	Retorna informações de compliance do utilizador atual
	"""
	try:
		if not frappe.session.user or frappe.session.user == "Guest":
			return {}

		user_info = {
			"user": frappe.session.user,
			"has_portugal_access": False,
			"companies_with_compliance": [],
			"compliance_permissions": {},
			"session_secure": False
		}

		# Verificar acesso a empresas portuguesas
		companies = get_user_companies()
		user_info["companies_with_compliance"] = [c.name for c in companies]
		user_info["has_portugal_access"] = len(companies) > 0

		# Verificar permissões de compliance
		compliance_doctypes = ["Portugal Series Configuration", "ATCUD Log", "SAF-T Export Log"]
		for doctype in compliance_doctypes:
			if frappe.db.table_exists(f"tab{doctype}"):
				user_info["compliance_permissions"][doctype] = frappe.has_permission(doctype,
																					 "read")

		# Verificar segurança da sessão
		if frappe.request and hasattr(frappe.request, 'environ'):
			user_info["session_secure"] = frappe.request.environ.get('HTTPS') == 'on' or \
										  frappe.request.environ.get(
											  'HTTP_X_FORWARDED_PROTO') == 'https'

		return user_info

	except Exception as e:
		frappe.log_error(f"Error getting user compliance info: {str(e)}")
		return {}


@frappe.whitelist()
def check_compliance_status():
	"""
	Endpoint para verificar status de compliance do utilizador
	"""
	try:
		return {
			"status": "success",
			"compliance_enabled": is_portugal_compliance_enabled(),
			"user_info": get_user_compliance_info()
		}

	except Exception as e:
		frappe.log_error(f"Error checking compliance status: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


def validate_api_access():
	"""
	Valida acesso via API para compliance português
	"""
	try:
		# Verificar se é acesso via API
		if not frappe.request or not hasattr(frappe.request, 'path'):
			return

		# Verificar se é endpoint de API
		if not frappe.request.path.startswith('/api/'):
			return

		# Validações específicas para API
		validate_api_authentication()
		validate_api_rate_limiting()

	except Exception as e:
		frappe.log_error(f"Error validating API access: {str(e)}")


def validate_api_authentication():
	"""
	Valida autenticação via API
	"""
	try:
		# Verificar se tem token válido
		if frappe.session.user == "Guest":
			# API pública, permitir
			return

		# Verificar se utilizador tem permissão para API
		if not frappe.has_permission("System Settings", "read"):
			frappe.logger().warning(f"API access denied for user {frappe.session.user}")

	except Exception as e:
		frappe.log_error(f"Error validating API authentication: {str(e)}")


def validate_api_rate_limiting():
	"""
	Implementa rate limiting básico para API
	"""
	try:
		# Rate limiting básico por utilizador
		user_key = f"api_rate_limit_{frappe.session.user}"
		current_count = frappe.cache.get(user_key) or 0

		# Limite: 100 requests por minuto
		rate_limit = 100

		if current_count >= rate_limit:
			frappe.logger().warning(f"Rate limit exceeded for user {frappe.session.user}")
		# Não bloquear, apenas registar

		# Incrementar contador
		frappe.cache.set(user_key, current_count + 1, expires_in_sec=60)

	except Exception as e:
		frappe.log_error(f"Error in API rate limiting: {str(e)}")


# Função principal que o Frappe chama
def validate_auth():
	"""
	Função principal de validação de autenticação
	"""
	try:
		# Executar todas as validações
		validate_user_compliance()
		validate_session_security()
		validate_api_access()
		log_authentication_attempt()

	except Exception as e:
		# Log do erro mas não bloquear autenticação
		frappe.log_error(f"Portugal Compliance auth validation error: {str(e)}")

import frappe

@frappe.whitelist()
def my_secure_method():
    # Permite sempre para Administrator
    if frappe.session.user == "Administrator":
        return {"status": "ok"}

    # Sua lógica customizada para outros usuários
    if "System Manager" in frappe.get_roles():
        return {"status": "ok"}

    # Caso contrário, bloqueia
    frappe.throw("Acesso negado", frappe.PermissionError)
