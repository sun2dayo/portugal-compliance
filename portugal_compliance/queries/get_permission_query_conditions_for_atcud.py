# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_permission_query_conditions_for_atcud(user):
	"""
	Retorna as condições de query para filtrar ATCUD Log
	com base nas permissões do utilizador

	Args:
		user (str): ID do utilizador

	Returns:
		str: Condições SQL para filtrar registos ATCUD
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso a tudo
	if user == "Administrator":
		return ""

	try:
		# Obter empresas que o utilizador tem permissão para acessar
		allowed_companies = get_user_atcud_companies(user)

		if not allowed_companies:
			# Nenhuma empresa permitida, negar acesso a tudo
			return "`tabATCUD Log`.name IS NULL"

		# Construir condição para filtrar ATCUD por empresa
		company_conditions = ",".join([f"'{company}'" for company in allowed_companies])
		conditions = f"`tabATCUD Log`.company IN ({company_conditions})"

		# Adicionar condições baseadas em roles do utilizador
		user_roles = frappe.get_roles(user)

		# Se não é System Manager ou Accounts Manager, filtrar apenas ATCUD próprios
		if not any(
			role in ["System Manager", "Accounts Manager", "Portugal Compliance Manager"] for role
			in user_roles):
			conditions += f" AND (`tabATCUD Log`.owner = '{user}' OR `tabATCUD Log`.created_by_user = '{user}')"

		# Filtrar apenas ATCUD válidos para utilizadores normais
		if "System Manager" not in user_roles:
			conditions += " AND `tabATCUD Log`.validation_status = 'Valid'"

		return conditions

	except Exception as e:
		frappe.log_error(f"Error getting ATCUD permission query conditions: {str(e)}")
		# Em caso de erro, negar acesso
		return "`tabATCUD Log`.name IS NULL"


def get_user_atcud_companies(user):
	"""
	Obtém lista de empresas que o utilizador pode acessar para ATCUD

	Args:
		user (str): ID do utilizador

	Returns:
		list: Lista de nomes de empresas permitidas
	"""
	try:
		# Obter todas as empresas com Portugal Compliance ativo
		companies = frappe.db.get_all("Company",
									  filters={"portugal_compliance_enabled": 1},
									  fields=["name"]
									  )

		# Filtrar empresas que o utilizador tem permissão para ler
		allowed_companies = []
		for company in companies:
			if frappe.has_permission("Company", "read", company["name"], user=user):
				# Verificar se utilizador tem acesso a séries da empresa
				if has_series_access_for_company(user, company["name"]):
					allowed_companies.append(company["name"])

		return allowed_companies

	except Exception as e:
		frappe.log_error(f"Error getting user ATCUD companies: {str(e)}")
		return []


def has_series_access_for_company(user, company):
	"""
	Verifica se utilizador tem acesso a séries da empresa

	Args:
		user (str): ID do utilizador
		company (str): Nome da empresa

	Returns:
		bool: True se tem acesso a pelo menos uma série
	"""
	try:
		# Verificar se há séries ativas na empresa
		series_count = frappe.db.count("Portugal Series Configuration", {
			"company": company,
			"is_active": 1
		})

		if series_count == 0:
			return False

		# Verificar se utilizador tem permissão para pelo menos uma série
		from portugal_compliance.queries.has_permission_for_series import has_permission_for_series

		series_list = frappe.db.get_all("Portugal Series Configuration", {
			"company": company,
			"is_active": 1
		}, ["name"], limit=5)  # Verificar apenas primeiras 5 para performance

		for series in series_list:
			if has_permission_for_series(series.name, user):
				return True

		return False

	except Exception as e:
		frappe.log_error(f"Error checking series access for company: {str(e)}")
		return False


def get_permission_query_conditions_for_document_type(user, document_type):
	"""
	Retorna condições de query filtradas por tipo de documento

	Args:
		user (str): ID do utilizador
		document_type (str): Tipo de documento

	Returns:
		str: Condições SQL específicas para o tipo de documento
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso a tudo
	if user == "Administrator":
		return ""

	try:
		# Obter condições base
		base_conditions = get_permission_query_conditions_for_atcud(user)

		if base_conditions == "`tabATCUD Log`.name IS NULL":
			return base_conditions

		# Adicionar filtro por tipo de documento
		if document_type:
			# Verificar se utilizador tem permissão para o tipo de documento
			if not frappe.has_permission(document_type, "read", user=user):
				return "`tabATCUD Log`.name IS NULL"

			document_condition = f"`tabATCUD Log`.document_type = '{document_type}'"

			if base_conditions:
				return f"({base_conditions}) AND ({document_condition})"
			else:
				return document_condition

		return base_conditions

	except Exception as e:
		frappe.log_error(f"Error getting ATCUD permission conditions for document type: {str(e)}")
		return "`tabATCUD Log`.name IS NULL"


def has_permission_for_atcud_log(doc, ptype, user):
	"""
	Verifica se o utilizador tem permissão para o log ATCUD específico

	Args:
		doc: Documento ATCUD Log
		ptype (str): Tipo de permissão (read, write, delete)
		user (str): ID do utilizador

	Returns:
		bool: True se tem permissão, False caso contrário
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso total
	if user == "Administrator":
		return True

	try:
		# Verificar se o documento é do tipo correto
		if doc.doctype != "ATCUD Log":
			return False

		# Verificar se utilizador tem permissão para a empresa
		if doc.company and not frappe.has_permission("Company", "read", doc.company, user=user):
			return False

		# Verificar se utilizador tem permissão para o tipo de documento
		if doc.document_type and not frappe.has_permission(doc.document_type, "read", user=user):
			return False

		# Verificar permissões específicas por tipo
		if ptype == "read":
			return check_atcud_read_permission(doc, user)
		elif ptype == "write":
			return check_atcud_write_permission(doc, user)
		elif ptype == "delete":
			return check_atcud_delete_permission(doc, user)
		else:
			return check_atcud_read_permission(doc, user)

	except Exception as e:
		frappe.log_error(f"Error checking ATCUD log permission: {str(e)}")
		return False


def check_atcud_read_permission(doc, user):
	"""
	Verifica permissão de leitura para ATCUD Log
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Roles que podem ler ATCUD
		read_roles = ["System Manager", "Accounts Manager", "Accounts User",
					  "Portugal Compliance Manager", "Portugal Compliance User"]

		if any(role in read_roles for role in user_roles):
			return True

		# Verificar se é o criador do ATCUD
		if hasattr(doc, 'owner') and doc.owner == user:
			return True

		if hasattr(doc, 'created_by_user') and doc.created_by_user == user:
			return True

		# Verificar se tem permissão para o documento original
		if doc.document_name and doc.document_type:
			if frappe.has_permission(doc.document_type, "read", doc.document_name, user=user):
				return True

		return False

	except Exception:
		return False


def check_atcud_write_permission(doc, user):
	"""
	Verifica permissão de escrita para ATCUD Log
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Apenas roles específicas podem modificar ATCUD
		write_roles = ["System Manager", "Portugal Compliance Manager"]

		if any(role in write_roles for role in user_roles):
			# Não permitir modificar ATCUD válidos
			if getattr(doc, 'validation_status', '') == 'Valid':
				return False
			return True

		return False

	except Exception:
		return False


def check_atcud_delete_permission(doc, user):
	"""
	Verifica permissão de eliminação para ATCUD Log
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Apenas System Manager pode eliminar
		if "System Manager" in user_roles:
			# Não permitir eliminar ATCUD válidos ou em uso
			if getattr(doc, 'validation_status', '') == 'Valid':
				return False
			return True

		return False

	except Exception:
		return False


def get_atcud_filters_for_user(user=None, filters=None):
	"""
	Obtém filtros adicionais para ATCUD baseados no utilizador

	Args:
		user (str): ID do utilizador
		filters (dict): Filtros adicionais

	Returns:
		dict: Filtros combinados
	"""
	if not user:
		user = frappe.session.user

	if not filters:
		filters = {}

	try:
		# Se não é administrador, adicionar filtros de permissão
		if user != "Administrator":
			# Filtrar por empresas permitidas
			allowed_companies = get_user_atcud_companies(user)

			if allowed_companies:
				filters["company"] = ["in", allowed_companies]
			else:
				# Nenhuma empresa permitida
				filters["name"] = ["in", []]

			# Filtrar apenas ATCUD válidos para utilizadores normais
			user_roles = frappe.get_roles(user)
			if not any(
				role in ["System Manager", "Portugal Compliance Manager"] for role in user_roles):
				filters["validation_status"] = "Valid"

		return filters

	except Exception as e:
		frappe.log_error(f"Error getting user ATCUD filters: {str(e)}")
		return {"name": ["in", []]}  # Negar acesso em caso de erro


@frappe.whitelist()
def get_filtered_atcud_list(document_type=None, company=None, validation_status=None):
	"""
	Endpoint para obter lista filtrada de ATCUD baseada nas permissões do utilizador

	Args:
		document_type (str): Tipo de documento (opcional)
		company (str): Empresa específica (opcional)
		validation_status (str): Status de validação (opcional)

	Returns:
		list: Lista de ATCUD que o utilizador pode acessar
	"""
	try:
		user = frappe.session.user

		# Construir filtros base
		filters = {}

		if document_type:
			filters["document_type"] = document_type

		if company:
			filters["company"] = company

		if validation_status:
			filters["validation_status"] = validation_status

		# Aplicar filtros de permissão do utilizador
		filters = get_atcud_filters_for_user(user, filters)

		# Obter lista de ATCUD
		atcud_list = frappe.db.get_all("ATCUD Log",
									   filters=filters,
									   fields=["name", "atcud_code", "document_type",
											   "document_name", "company",
											   "validation_status", "creation", "owner"],
									   order_by="creation desc",
									   limit=100
									   )

		return {
			"status": "success",
			"atcud_logs": atcud_list,
			"total": len(atcud_list)
		}

	except Exception as e:
		frappe.log_error(f"Error getting filtered ATCUD list: {str(e)}")
		return {
			"status": "error",
			"message": str(e),
			"atcud_logs": [],
			"total": 0
		}


@frappe.whitelist()
def check_atcud_log_permission(atcud_log_name, permission_type="read"):
	"""
	Endpoint para verificar permissão específica para um log ATCUD

	Args:
		atcud_log_name (str): Nome do log ATCUD
		permission_type (str): Tipo de permissão (read, write, delete)

	Returns:
		dict: Resultado da verificação de permissão
	"""
	try:
		user = frappe.session.user

		# Verificar se o log ATCUD existe
		if not frappe.db.exists("ATCUD Log", atcud_log_name):
			return {
				"status": "error",
				"has_permission": False,
				"message": _("ATCUD Log not found")
			}

		# Obter documento do log ATCUD
		atcud_doc = frappe.get_doc("ATCUD Log", atcud_log_name)

		# Verificar permissão
		has_access = has_permission_for_atcud_log(atcud_doc, permission_type, user)

		return {
			"status": "success",
			"has_permission": has_access,
			"atcud_info": {
				"atcud_code": atcud_doc.atcud_code,
				"document_type": atcud_doc.document_type,
				"document_name": atcud_doc.document_name,
				"company": atcud_doc.company,
				"validation_status": atcud_doc.validation_status
			} if has_access else None
		}

	except Exception as e:
		frappe.log_error(f"Error checking ATCUD log permission: {str(e)}")
		return {
			"status": "error",
			"has_permission": False,
			"message": str(e)
		}


# Função de compatibilidade para hooks antigos
def get_permission_query_conditions(user):
	"""
	Função de compatibilidade para manter compatibilidade com hooks antigos
	"""
	return get_permission_query_conditions_for_atcud(user)
