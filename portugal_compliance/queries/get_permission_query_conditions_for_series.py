# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_permission_query_conditions_for_series(user):
	"""
	Retorna as condições de query para filtrar Portugal Series Configuration
	com base nas permissões do utilizador

	Args:
		user (str): ID do utilizador

	Returns:
		str: Condições SQL para filtrar registos
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso a tudo
	if user == "Administrator":
		return ""

	try:
		# Obter empresas que o utilizador tem permissão para ler
		allowed_companies = []

		# Verificar User Permissions para Company
		user_permissions = frappe.db.get_all("User Permission", {
			"user": user,
			"allow": "Company"
		}, ["for_value"])

		if user_permissions:
			# Se há permissões específicas, usar apenas essas
			allowed_companies = [p.for_value for p in user_permissions]
		else:
			# Se não há permissões específicas, verificar roles
			user_roles = frappe.get_roles(user)

			# Se tem role que permite acesso geral a empresas
			if any(role in ["System Manager", "Accounts Manager"] for role in user_roles):
				# Obter todas as empresas com Portugal Compliance ativo
				all_companies = frappe.db.get_all("Company", {
					"portugal_compliance_enabled": 1
				}, ["name"])
				allowed_companies = [c.name for c in all_companies]
			else:
				# Verificar empresas específicas por role
				for role in user_roles:
					role_companies = frappe.db.get_all("Company", {
						"name": ["like", f"%{role}%"]
					}, ["name"])
					allowed_companies.extend([c.name for c in role_companies])

		# Filtrar apenas empresas com Portugal Compliance ativo
		if allowed_companies:
			compliance_companies = frappe.db.get_all("Company", {
				"name": ["in", allowed_companies],
				"portugal_compliance_enabled": 1
			}, ["name"])

			final_companies = [c.name for c in compliance_companies]
		else:
			final_companies = []

		# Se não há empresas permitidas, bloquear acesso
		if not final_companies:
			return "1=0"

		# Construir condição SQL
		company_list = "','".join(final_companies)
		conditions = f"`tabPortugal Series Configuration`.company IN ('{company_list}')"

		# Adicionar condição para séries ativas apenas (exceto para System Manager)
		user_roles = frappe.get_roles(user)
		if "System Manager" not in user_roles:
			conditions += " AND `tabPortugal Series Configuration`.is_active = 1"

		return conditions

	except Exception as e:
		frappe.log_error(f"Error in get_permission_query_conditions_for_series: {str(e)}")
		return "1=0"  # Em caso de erro, bloquear acesso


def get_permission_query_conditions(user):
	"""
	Função alternativa para compatibilidade com diferentes versões do Frappe
	"""
	return get_permission_query_conditions_for_series(user)


@frappe.whitelist()
def has_permission_for_series(doc, ptype, user):
	"""
	Verifica se o utilizador tem permissão para a série específica

	Args:
		doc: Documento Portugal Series Configuration
		ptype (str): Tipo de permissão (read, write, delete, etc.)
		user (str): ID do utilizador

	Returns:
		bool: True se tem permissão, False caso contrário
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem todas as permissões
	if user == "Administrator":
		return True

	try:
		# Verificar se utilizador tem permissão para a empresa
		if doc.company:
			company_permission = frappe.has_permission("Company", "read", doc.company, user=user)
			if not company_permission:
				return False

		# Verificar permissões específicas por tipo
		if ptype == "read":
			return check_read_permission(doc, user)
		elif ptype == "write":
			return check_write_permission(doc, user)
		elif ptype == "delete":
			return check_delete_permission(doc, user)
		elif ptype == "create":
			return check_create_permission(doc, user)
		else:
			return check_read_permission(doc, user)

	except Exception as e:
		frappe.log_error(f"Error checking permission for series: {str(e)}")
		return False


def check_read_permission(doc, user):
	"""
	Verifica permissão de leitura
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Roles que podem ler séries
		read_roles = ["System Manager", "Accounts Manager", "Accounts User"]

		if any(role in read_roles for role in user_roles):
			return True

		# Verificar se é o criador da série
		if hasattr(doc, 'owner') and doc.owner == user:
			return True

		return False

	except Exception:
		return False


def check_write_permission(doc, user):
	"""
	Verifica permissão de escrita
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Roles que podem modificar séries
		write_roles = ["System Manager", "Accounts Manager"]

		if any(role in write_roles for role in user_roles):
			return True

		# Verificar se é o criador e a série não está comunicada
		if hasattr(doc, 'owner') and doc.owner == user:
			if not getattr(doc, 'is_communicated', False):
				return True

		return False

	except Exception:
		return False


def check_delete_permission(doc, user):
	"""
	Verifica permissão de eliminação
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Apenas System Manager pode eliminar
		if "System Manager" in user_roles:
			# Não permitir eliminar séries comunicadas ou em uso
			if getattr(doc, 'is_communicated', False):
				return False

			if getattr(doc, 'total_documents_issued', 0) > 0:
				return False

			return True

		return False

	except Exception:
		return False


def check_create_permission(doc, user):
	"""
	Verifica permissão de criação
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Roles que podem criar séries
		create_roles = ["System Manager", "Accounts Manager"]

		if any(role in create_roles for role in user_roles):
			# Verificar se tem permissão para a empresa
			if doc.company:
				return frappe.has_permission("Company", "read", doc.company, user=user)
			return True

		return False

	except Exception:
		return False


def get_series_filters_for_user(user=None, document_type=None):
	"""
	Obtém filtros de séries para um utilizador específico

	Args:
		user (str): ID do utilizador
		document_type (str): Tipo de documento para filtrar

	Returns:
		dict: Filtros para aplicar na query
	"""
	if not user:
		user = frappe.session.user

	try:
		filters = {"is_active": 1}

		# Adicionar filtro de tipo de documento
		if document_type:
			filters["document_type"] = document_type

		# Obter empresas permitidas
		if user != "Administrator":
			# Obter empresas com permissão
			user_permissions = frappe.db.get_all("User Permission", {
				"user": user,
				"allow": "Company"
			}, ["for_value"])

			if user_permissions:
				allowed_companies = [p.for_value for p in user_permissions]
				filters["company"] = ["in", allowed_companies]

		return filters

	except Exception as e:
		frappe.log_error(f"Error getting series filters for user: {str(e)}")
		return {"name": ["=", ""]}  # Retornar filtro vazio em caso de erro


@frappe.whitelist()
def get_filtered_series_list(document_type=None, company=None):
	"""
	Endpoint para obter lista filtrada de séries

	Args:
		document_type (str): Tipo de documento
		company (str): Empresa específica

	Returns:
		list: Lista de séries filtradas
	"""
	try:
		user = frappe.session.user

		# Obter filtros base
		filters = get_series_filters_for_user(user, document_type)

		# Adicionar filtro de empresa se especificado
		if company:
			filters["company"] = company

		# Obter séries
		series_list = frappe.db.get_all("Portugal Series Configuration",
										filters=filters,
										fields=["name", "series_name", "prefix", "document_type",
												"company", "is_communicated"],
										order_by="company, document_type, series_name"
										)

		return {
			"status": "success",
			"series": series_list,
			"total": len(series_list)
		}

	except Exception as e:
		frappe.log_error(f"Error getting filtered series list: {str(e)}")
		return {
			"status": "error",
			"message": str(e),
			"series": [],
			"total": 0
		}


def apply_user_permissions_to_series_query(query, user):
	"""
	Aplica permissões de utilizador a uma query de séries

	Args:
		query (str): Query SQL base
		user (str): ID do utilizador

	Returns:
		str: Query modificada com permissões
	"""
	try:
		if user == "Administrator":
			return query

		# Obter condições de permissão
		permission_conditions = get_permission_query_conditions_for_series(user)

		if permission_conditions and permission_conditions != "1=0":
			# Adicionar condições à query
			if "WHERE" in query.upper():
				query += f" AND ({permission_conditions})"
			else:
				query += f" WHERE {permission_conditions}"

		return query

	except Exception as e:
		frappe.log_error(f"Error applying user permissions to query: {str(e)}")
		return query
