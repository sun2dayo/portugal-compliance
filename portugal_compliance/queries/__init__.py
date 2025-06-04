# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


# Função principal que o Frappe procura
def get_permission_query_conditions_for_series(user):
	"""
	Função principal para filtrar Portugal Series Configuration baseado em permissões
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso a tudo
	if user == "Administrator":
		return ""

	try:
		# Obter empresas permitidas
		allowed_companies = []

		# Verificar User Permissions para Company
		user_permissions = frappe.db.get_all("User Permission", {
			"user": user,
			"allow": "Company"
		}, ["for_value"])

		if user_permissions:
			allowed_companies = [p.for_value for p in user_permissions]
		else:
			# Se não há permissões específicas, verificar roles
			user_roles = frappe.get_roles(user)

			if any(role in ["System Manager", "Accounts Manager"] for role in user_roles):
				all_companies = frappe.db.get_all("Company", {
					"portugal_compliance_enabled": 1
				}, ["name"])
				allowed_companies = [c.name for c in all_companies]

		# Se não há empresas permitidas, bloquear acesso
		if not allowed_companies:
			return "1=0"

		# Construir condição SQL
		company_list = "','".join(allowed_companies)
		conditions = f"`tabPortugal Series Configuration`.company IN ('{company_list}')"

		# Adicionar condição para séries ativas apenas (exceto para System Manager)
		user_roles = frappe.get_roles(user)
		if "System Manager" not in user_roles:
			conditions += " AND `tabPortugal Series Configuration`.is_active = 1"

		return conditions

	except Exception as e:
		frappe.log_error(f"Error in get_permission_query_conditions_for_series: {str(e)}")
		return "1=0"


# Importar funções dos outros módulos (com tratamento de erro)
try:
	from .has_permission_for_series import (
		has_permission_for_series,
		get_filtered_series_list
	)
except ImportError as e:
	frappe.log_error(f"Error importing series functions: {str(e)}")


	def has_permission_for_series(series_name, user=None):
		return True


	def get_filtered_series_list(document_type=None, company=None):
		return {"status": "error", "series": [], "total": 0}

try:
	from .has_permission_for_atcud import (
		has_permission_for_atcud,
		get_filtered_atcud_list
	)
except ImportError as e:
	frappe.log_error(f"Error importing ATCUD functions: {str(e)}")


	def has_permission_for_atcud(user=None, atcud_code=None, document_type=None, company=None):
		return True


	def get_filtered_atcud_list(document_type=None, company=None, validation_status=None):
		return {"status": "error", "atcud_logs": [], "total": 0}

# Exportar apenas as funções que existem
__all__ = [
	'get_permission_query_conditions_for_series',
	'has_permission_for_series',
	'has_permission_for_atcud',
	'get_filtered_series_list',
	'get_filtered_atcud_list'
]

