# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def has_permission_for_series(series_name, user=None):
	"""
	Verifica se o utilizador tem permissão para usar a série Portugal especificada

	Args:
		series_name (str): Nome da Portugal Series Configuration
		user (str): ID do utilizador para verificar permissão. Por defeito é o utilizador atual.

	Returns:
		bool: True se o utilizador tem permissão, False caso contrário
	"""
	if not user:
		user = frappe.session.user

	try:
		# Verificar se a série existe
		if not frappe.db.exists('Portugal Series Configuration', series_name):
			return False

		# Obter documento da série
		series = frappe.get_doc('Portugal Series Configuration', series_name)

		# Verificar se utilizador tem permissão de leitura na série
		if not frappe.has_permission('Portugal Series Configuration', 'read', series_name,
									 user=user):
			return False

		# Verificar acesso à empresa
		if series.company:
			if not frappe.has_permission('Company', 'read', series.company, user=user):
				return False

		# Verificar se a série está ativa
		if not series.is_active:
			return False

		# Verificar se utilizador tem permissão para o tipo de documento
		if series.document_type:
			if not frappe.has_permission(series.document_type, 'create', user=user):
				return False

		return True

	except Exception as e:
		frappe.log_error(f"Error checking permission for series {series_name}: {str(e)}")
		return False


def get_permitted_series_for_user(user=None, document_type=None, company=None):
	"""
	Obtém lista de séries que o utilizador tem permissão para usar

	Args:
		user (str): ID do utilizador. Por defeito é o utilizador atual.
		document_type (str): Filtrar por tipo de documento específico
		company (str): Filtrar por empresa específica

	Returns:
		list: Lista de nomes de séries permitidas
	"""
	if not user:
		user = frappe.session.user

	try:
		# Construir filtros
		filters = {'is_active': 1}

		if document_type:
			filters['document_type'] = document_type

		if company:
			filters['company'] = company

		# Obter todas as séries ativas
		series_list = frappe.db.get_all('Portugal Series Configuration',
										filters=filters,
										fields=['name', 'series_name', 'company', 'document_type']
										)

		permitted_series = []

		for series in series_list:
			# Verificar permissões para cada série
			if has_permission_for_series(series.name, user):
				permitted_series.append(series.name)

		return permitted_series

	except Exception as e:
		frappe.log_error(f"Error getting permitted series for user {user}: {str(e)}")
		return []


def get_series_options_for_doctype(doctype, user=None, company=None):
	"""
	Obtém opções de séries para um tipo de documento específico

	Args:
		doctype (str): Tipo de documento (Sales Invoice, Purchase Invoice, etc.)
		user (str): ID do utilizador. Por defeito é o utilizador atual.
		company (str): Empresa específica. Por defeito é a empresa padrão do utilizador.

	Returns:
		list: Lista de opções de séries no formato [{'value': 'series_name', 'label': 'series_name'}]
	"""
	if not user:
		user = frappe.session.user

	if not company:
		company = frappe.defaults.get_user_default("Company", user)

	try:
		# Obter séries permitidas para o tipo de documento
		permitted_series = get_permitted_series_for_user(user, doctype, company)

		# Formatar como opções
		options = []
		for series_name in permitted_series:
			series_doc = frappe.get_doc('Portugal Series Configuration', series_name)
			options.append({
				'value': series_name,
				'label': f"{series_doc.series_name} ({series_doc.prefix})",
				'description': f"Company: {series_doc.company}"
			})

		return options

	except Exception as e:
		frappe.log_error(f"Error getting series options for doctype {doctype}: {str(e)}")
		return []


def validate_series_permission(series_name, user=None, raise_exception=True):
	"""
	Valida se o utilizador tem permissão para usar a série

	Args:
		series_name (str): Nome da série
		user (str): ID do utilizador. Por defeito é o utilizador atual.
		raise_exception (bool): Se deve lançar exceção em caso de erro

	Returns:
		bool: True se tem permissão

	Raises:
		frappe.PermissionError: Se não tem permissão e raise_exception=True
	"""
	if not user:
		user = frappe.session.user

	has_permission = has_permission_for_series(series_name, user)

	if not has_permission and raise_exception:
		frappe.throw(
			_("You don't have permission to use series '{0}'").format(series_name),
			frappe.PermissionError
		)

	return has_permission


def check_series_company_access(series_name, user=None):
	"""
	Verifica se o utilizador tem acesso à empresa da série

	Args:
		series_name (str): Nome da série
		user (str): ID do utilizador. Por defeito é o utilizador atual.

	Returns:
		bool: True se tem acesso à empresa
	"""
	if not user:
		user = frappe.session.user

	try:
		series = frappe.get_doc('Portugal Series Configuration', series_name)

		if not series.company:
			return True

		# Verificar se utilizador tem acesso à empresa
		return frappe.has_permission('Company', 'read', series.company, user=user)

	except Exception as e:
		frappe.log_error(f"Error checking company access for series {series_name}: {str(e)}")
		return False


def get_user_default_series(user=None, document_type=None):
	"""
	Obtém série padrão do utilizador para um tipo de documento

	Args:
		user (str): ID do utilizador. Por defeito é o utilizador atual.
		document_type (str): Tipo de documento

	Returns:
		str: Nome da série padrão ou None
	"""
	if not user:
		user = frappe.session.user

	if not document_type:
		return None

	try:
		# Tentar obter série padrão das configurações do utilizador
		default_series = frappe.db.get_value('User Permission', {
			'user': user,
			'allow': 'Portugal Series Configuration',
			'for_value': document_type
		}, 'for_value')

		if default_series and has_permission_for_series(default_series, user):
			return default_series

		# Se não há padrão, obter primeira série disponível
		permitted_series = get_permitted_series_for_user(user, document_type)

		if permitted_series:
			return permitted_series[0]

		return None

	except Exception as e:
		frappe.log_error(f"Error getting default series for user {user}: {str(e)}")
		return None


# ✅ FUNÇÃO QUE ESTAVA EM FALTA - CAUSAVA O ERRO!
def get_filtered_series_list(doctype, txt, searchfield, start, page_len, filters):
	"""
	Obtém lista filtrada de séries para Link Field (função que estava em falta!)

	Args:
		doctype: Tipo de documento
		txt: Texto de busca
		searchfield: Campo de busca
		start: Início da paginação
		page_len: Tamanho da página
		filters: Filtros adicionais

	Returns:
		list: Lista de séries filtradas
	"""
	try:
		conditions = []
		values = []

		# Filtro por texto
		if txt:
			conditions.append("(series_name LIKE %s OR prefix LIKE %s)")
			values.extend([f"%{txt}%", f"%{txt}%"])

		# Filtro por empresa
		if filters and filters.get("company"):
			conditions.append("company = %s")
			values.append(filters["company"])

		# Filtro por tipo de documento
		if filters and filters.get("document_type"):
			conditions.append("document_type = %s")
			values.append(filters["document_type"])

		# Apenas séries ativas
		conditions.append("is_active = 1")

		# Construir query
		where_clause = " AND ".join(conditions) if conditions else "1=1"

		query = f"""
			SELECT name, series_name, prefix, document_type, company
			FROM `tabPortugal Series Configuration`
			WHERE {where_clause}
			ORDER BY series_name
			LIMIT %s OFFSET %s
		"""

		values.extend([page_len, start])

		return frappe.db.sql(query, values)

	except Exception as e:
		frappe.log_error(f"Error in get_filtered_series_list: {str(e)}")
		return []


# ✅ FUNÇÕES AUXILIARES PARA COMPATIBILIDADE COM HOOKS.PY
def has_permission(doc, user):
	"""
	Função de compatibilidade para hooks.py

	Args:
		doc: Documento ou nome do documento
		user: Usuário (opcional)

	Returns:
		bool: True se tem permissão
	"""
	try:
		if isinstance(doc, str):
			series_name = doc
		else:
			series_name = getattr(doc, 'name', None)

		if not series_name:
			return False

		return has_permission_for_series(series_name, user)

	except Exception as e:
		frappe.log_error(f"Error in has_permission: {str(e)}")
		return False


def get_permission_query_conditions(user):
	"""
	Obter condições de query para permissões (para hooks.py)

	Args:
		user: Usuário

	Returns:
		str: Condições SQL
	"""
	try:
		# Se é System Manager, ver tudo
		if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
			return ""

		# Se é Accounts Manager, ver tudo
		if "Accounts Manager" in frappe.get_roles():
			return ""

		# Obter empresas permitidas para o usuário
		user_companies = frappe.get_all("User Permission",
										filters={
											"user": user or frappe.session.user,
											"allow": "Company"
										},
										fields=["for_value"])

		if user_companies:
			companies = [f"'{company.for_value}'" for company in user_companies]
			return f"`tabPortugal Series Configuration`.company in ({','.join(companies)})"

		# Se não tem permissões específicas, não ver nada
		return "1=0"

	except Exception as e:
		frappe.log_error(f"Error in get_permission_query_conditions: {str(e)}")
		return "1=0"


@frappe.whitelist()
def get_series_for_document(doctype, company=None):
	"""
	Endpoint para obter séries disponíveis para um documento

	Args:
		doctype (str): Tipo de documento
		company (str): Empresa (opcional)

	Returns:
		dict: Informações das séries disponíveis
	"""
	try:
		user = frappe.session.user

		if not company:
			company = frappe.defaults.get_user_default("Company", user)

		# Obter opções de séries
		series_options = get_series_options_for_doctype(doctype, user, company)

		# Obter série padrão
		default_series = get_user_default_series(user, doctype)

		return {
			'status': 'success',
			'series_options': series_options,
			'default_series': default_series,
			'total_series': len(series_options)
		}

	except Exception as e:
		frappe.log_error(f"Error in get_series_for_document: {str(e)}")
		return {
			'status': 'error',
			'message': str(e),
			'series_options': [],
			'default_series': None
		}


@frappe.whitelist()
def validate_user_series_access(series_name):
	"""
	Endpoint para validar acesso do utilizador a uma série

	Args:
		series_name (str): Nome da série

	Returns:
		dict: Resultado da validação
	"""
	try:
		user = frappe.session.user
		has_access = has_permission_for_series(series_name, user)

		if has_access:
			series_doc = frappe.get_doc('Portugal Series Configuration', series_name)
			return {
				'status': 'success',
				'has_permission': True,
				'series_info': {
					'name': series_doc.name,
					'series_name': series_doc.series_name,
					'document_type': series_doc.document_type,
					'company': series_doc.company,
					'is_active': series_doc.is_active,
					'is_communicated': series_doc.is_communicated
				}
			}
		else:
			return {
				'status': 'error',
				'has_permission': False,
				'message': _("You don't have permission to access this series")
			}

	except Exception as e:
		frappe.log_error(f"Error validating series access: {str(e)}")
		return {
			'status': 'error',
			'has_permission': False,
			'message': str(e)
		}
