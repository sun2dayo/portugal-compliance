# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def has_permission_for_atcud(user=None, atcud_code=None, document_type=None, company=None):
	"""
	Verifica se o utilizador tem permissão para acessar/gerar códigos ATCUD

	Args:
		user (str): ID do utilizador. Por defeito é o utilizador atual.
		atcud_code (str): Código ATCUD específico para verificar
		document_type (str): Tipo de documento (Sales Invoice, Purchase Invoice, etc.)
		company (str): Empresa específica

	Returns:
		bool: True se o utilizador tem permissão, False caso contrário
	"""
	if not user:
		user = frappe.session.user

	# Administrador tem acesso total
	if user == "Administrator":
		return True

	try:
		# Verificar se utilizador tem permissão básica para ATCUD
		if not check_basic_atcud_permission(user):
			return False

		# Verificar permissão para empresa específica
		if company and not check_company_atcud_permission(user, company):
			return False

		# Verificar permissão para tipo de documento específico
		if document_type and not check_document_type_atcud_permission(user, document_type):
			return False

		# Verificar permissão para código ATCUD específico
		if atcud_code and not check_specific_atcud_permission(user, atcud_code):
			return False

		return True

	except Exception as e:
		frappe.log_error(f"Error checking ATCUD permission: {str(e)}")
		return False


def check_basic_atcud_permission(user):
	"""
	Verifica permissões básicas para trabalhar com ATCUD

	Args:
		user (str): ID do utilizador

	Returns:
		bool: True se tem permissão básica
	"""
	try:
		user_roles = frappe.get_roles(user)

		# Roles que podem trabalhar com ATCUD
		atcud_roles = [
			"System Manager",
			"Accounts Manager",
			"Accounts User",
			"Portugal Compliance Manager",
			"Portugal Compliance User"
		]

		# Verificar se utilizador tem pelo menos uma role adequada
		if any(role in atcud_roles for role in user_roles):
			return True

		# Verificar permissões específicas para ATCUD Log
		if frappe.has_permission("ATCUD Log", "read", user=user):
			return True

		return False

	except Exception as e:
		frappe.log_error(f"Error checking basic ATCUD permission: {str(e)}")
		return False


def check_company_atcud_permission(user, company):
	"""
	Verifica se utilizador tem permissão para ATCUD da empresa específica

	Args:
		user (str): ID do utilizador
		company (str): Nome da empresa

	Returns:
		bool: True se tem permissão para a empresa
	"""
	try:
		# Verificar se utilizador tem acesso à empresa
		if not frappe.has_permission("Company", "read", company, user=user):
			return False

		# Verificar se empresa tem Portugal Compliance ativo
		company_compliance = frappe.db.get_value("Company", company, "portugal_compliance_enabled")
		if not company_compliance:
			return False

		# Verificar se utilizador tem permissão específica para séries da empresa
		series_permission = frappe.db.exists("Portugal Series Configuration", {
			"company": company
		})

		if series_permission:
			# Se há séries configuradas, verificar se utilizador pode acessá-las
			from portugal_compliance.queries.has_permission_for_series import \
				has_permission_for_series

			series_list = frappe.db.get_all("Portugal Series Configuration", {
				"company": company,
				"is_active": 1
			}, ["name"])

			# Verificar se tem acesso a pelo menos uma série
			for series in series_list:
				if has_permission_for_series(series.name, user):
					return True

			return False

		return True

	except Exception as e:
		frappe.log_error(f"Error checking company ATCUD permission: {str(e)}")
		return False


def check_document_type_atcud_permission(user, document_type):
	"""
	Verifica permissão para gerar ATCUD para tipo de documento específico

	Args:
		user (str): ID do utilizador
		document_type (str): Tipo de documento

	Returns:
		bool: True se tem permissão para o tipo de documento
	"""
	try:
		# Verificar se utilizador tem permissão para criar/modificar o tipo de documento
		if not frappe.has_permission(document_type, "write", user=user):
			return False

		# Verificar permissões específicas por tipo de documento
		user_roles = frappe.get_roles(user)

		# Mapeamento de tipos de documento para roles necessárias
		document_role_mapping = {
			"Sales Invoice": ["Accounts Manager", "Accounts User", "Sales Manager", "Sales User"],
			"Purchase Invoice": ["Accounts Manager", "Accounts User", "Purchase Manager",
								 "Purchase User"],
			"Payment Entry": ["Accounts Manager", "Accounts User"],
			"Delivery Note": ["Stock Manager", "Stock User", "Sales Manager", "Sales User"],
			"Purchase Receipt": ["Stock Manager", "Stock User", "Purchase Manager",
								 "Purchase User"],
			"Journal Entry": ["Accounts Manager"],
			"Stock Entry": ["Stock Manager", "Stock User"]
		}

		required_roles = document_role_mapping.get(document_type, [])
		required_roles.extend(["System Manager", "Portugal Compliance Manager"])

		return any(role in required_roles for role in user_roles)

	except Exception as e:
		frappe.log_error(f"Error checking document type ATCUD permission: {str(e)}")
		return False


def check_specific_atcud_permission(user, atcud_code):
	"""
	Verifica permissão para código ATCUD específico

	Args:
		user (str): ID do utilizador
		atcud_code (str): Código ATCUD

	Returns:
		bool: True se tem permissão para o código específico
	"""
	try:
		# Verificar se ATCUD existe
		atcud_log = frappe.db.get_value("ATCUD Log", {
			"atcud_code": atcud_code
		}, ["company", "document_type", "document_name", "owner"], as_dict=True)

		if not atcud_log:
			return False

		# Verificar permissão para a empresa do ATCUD
		if atcud_log.company and not check_company_atcud_permission(user, atcud_log.company):
			return False

		# Verificar permissão para o tipo de documento
		if atcud_log.document_type and not check_document_type_atcud_permission(user,
																				atcud_log.document_type):
			return False

		# Verificar se é o proprietário do documento
		if atcud_log.owner == user:
			return True

		# Verificar permissão para o documento específico
		if atcud_log.document_name and atcud_log.document_type:
			if frappe.has_permission(atcud_log.document_type, "read", atcud_log.document_name,
									 user=user):
				return True

		return False

	except Exception as e:
		frappe.log_error(f"Error checking specific ATCUD permission: {str(e)}")
		return False


def get_permitted_atcud_companies(user=None):
	"""
	Obtém lista de empresas para as quais o utilizador pode gerar ATCUD

	Args:
		user (str): ID do utilizador

	Returns:
		list: Lista de empresas permitidas
	"""
	if not user:
		user = frappe.session.user

	try:
		# Obter todas as empresas com Portugal Compliance ativo
		companies = frappe.db.get_all("Company", {
			"portugal_compliance_enabled": 1
		}, ["name", "company_name"])

		permitted_companies = []

		for company in companies:
			if check_company_atcud_permission(user, company.name):
				permitted_companies.append(company)

		return permitted_companies

	except Exception as e:
		frappe.log_error(f"Error getting permitted ATCUD companies: {str(e)}")
		return []


def validate_atcud_generation_permission(user, company, document_type, raise_exception=True):
	"""
	Valida se utilizador pode gerar ATCUD para combinação específica

	Args:
		user (str): ID do utilizador
		company (str): Empresa
		document_type (str): Tipo de documento
		raise_exception (bool): Se deve lançar exceção em caso de erro

	Returns:
		bool: True se pode gerar ATCUD

	Raises:
		frappe.PermissionError: Se não tem permissão e raise_exception=True
	"""
	try:
		# Verificar permissões básicas
		if not check_basic_atcud_permission(user):
			if raise_exception:
				frappe.throw(_("You don't have permission to work with ATCUD codes"),
							 frappe.PermissionError)
			return False

		# Verificar permissão para empresa
		if not check_company_atcud_permission(user, company):
			if raise_exception:
				frappe.throw(
					_("You don't have permission to generate ATCUD for company '{0}'").format(
						company), frappe.PermissionError)
			return False

		# Verificar permissão para tipo de documento
		if not check_document_type_atcud_permission(user, document_type):
			if raise_exception:
				frappe.throw(
					_("You don't have permission to generate ATCUD for document type '{0}'").format(
						document_type), frappe.PermissionError)
			return False

		# Verificar se empresa tem séries comunicadas
		communicated_series = frappe.db.exists("Portugal Series Configuration", {
			"company": company,
			"document_type": document_type,
			"is_communicated": 1,
			"is_active": 1
		})

		if not communicated_series:
			if raise_exception:
				frappe.throw(
					_("No communicated series found for company '{0}' and document type '{1}'").format(
						company, document_type))
			return False

		return True

	except frappe.PermissionError:
		raise
	except Exception as e:
		frappe.log_error(f"Error validating ATCUD generation permission: {str(e)}")
		if raise_exception:
			frappe.throw(_("Error validating ATCUD permission: {0}").format(str(e)))
		return False


@frappe.whitelist()
def check_user_atcud_permissions(company=None, document_type=None):
	"""
	Endpoint para verificar permissões ATCUD do utilizador

	Args:
		company (str): Empresa específica (opcional)
		document_type (str): Tipo de documento específico (opcional)

	Returns:
		dict: Informações sobre permissões ATCUD
	"""
	try:
		user = frappe.session.user

		result = {
			"status": "success",
			"has_basic_permission": check_basic_atcud_permission(user),
			"permitted_companies": [],
			"can_generate_atcud": False
		}

		# Obter empresas permitidas
		result["permitted_companies"] = get_permitted_atcud_companies(user)

		# Verificar permissão específica se empresa e tipo fornecidos
		if company and document_type:
			result["can_generate_atcud"] = validate_atcud_generation_permission(
				user, company, document_type, raise_exception=False
			)
			result["specific_check"] = {
				"company": company,
				"document_type": document_type,
				"has_permission": result["can_generate_atcud"]
			}

		return result

	except Exception as e:
		frappe.log_error(f"Error checking user ATCUD permissions: {str(e)}")
		return {
			"status": "error",
			"message": str(e),
			"has_basic_permission": False,
			"permitted_companies": [],
			"can_generate_atcud": False
		}


@frappe.whitelist()
def validate_atcud_access(atcud_code):
	"""
	Endpoint para validar acesso a código ATCUD específico

	Args:
		atcud_code (str): Código ATCUD

	Returns:
		dict: Resultado da validação
	"""
	try:
		user = frappe.session.user
		has_access = check_specific_atcud_permission(user, atcud_code)

		if has_access:
			atcud_info = frappe.db.get_value("ATCUD Log", {
				"atcud_code": atcud_code
			}, ["document_type", "document_name", "company", "creation"], as_dict=True)

			return {
				"status": "success",
				"has_permission": True,
				"atcud_info": atcud_info
			}
		else:
			return {
				"status": "error",
				"has_permission": False,
				"message": _("You don't have permission to access this ATCUD code")
			}

	except Exception as e:
		frappe.log_error(f"Error validating ATCUD access: {str(e)}")
		return {
			"status": "error",
			"has_permission": False,
			"message": str(e)
		}


# ✅ FUNÇÃO QUE ESTAVA EM FALTA - CAUSAVA O ERRO!
def get_filtered_atcud_list(doctype, txt, searchfield, start, page_len, filters):
	"""
	Obtém lista filtrada de logs ATCUD para Link Field (função que estava em falta!)

	Args:
		doctype: Tipo de documento
		txt: Texto de busca
		searchfield: Campo de busca
		start: Início da paginação
		page_len: Tamanho da página
		filters: Filtros adicionais

	Returns:
		list: Lista de logs ATCUD filtrados
	"""
	try:
		conditions = []
		values = []

		# Filtro por texto
		if txt:
			conditions.append(
				"(atcud_code LIKE %s OR document_name LIKE %s OR series_used LIKE %s)")
			values.extend([f"%{txt}%", f"%{txt}%", f"%{txt}%"])

		# Filtro por empresa
		if filters and filters.get("company"):
			conditions.append("company = %s")
			values.append(filters["company"])

		# Filtro por tipo de documento
		if filters and filters.get("document_type"):
			conditions.append("document_type = %s")
			values.append(filters["document_type"])

		# Filtro por status
		if filters and filters.get("generation_status"):
			conditions.append("generation_status = %s")
			values.append(filters["generation_status"])

		# Apenas logs com sucesso por padrão
		if not filters or not filters.get("include_failed"):
			conditions.append("generation_status = 'Success'")

		# Construir query
		where_clause = " AND ".join(conditions) if conditions else "1=1"

		query = f"""
			SELECT name, atcud_code, document_type, document_name, series_used, company, generation_date
			FROM `tabATCUD Log`
			WHERE {where_clause}
			ORDER BY creation DESC
			LIMIT %s OFFSET %s
		"""

		values.extend([page_len, start])

		return frappe.db.sql(query, values)

	except Exception as e:
		frappe.log_error(f"Error in get_filtered_atcud_list: {str(e)}")
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
		# Se é System Manager, tem acesso total
		if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
			return True

		# Se é Accounts Manager, tem acesso
		if "Accounts Manager" in frappe.get_roles():
			return True

		# Se é Portugal Compliance User, tem acesso de leitura
		if "Portugal Compliance User" in frappe.get_roles():
			return True

		return False

	except Exception as e:
		frappe.log_error(f"Error in has_permission_for_atcud: {str(e)}")
		return False


def get_permission_query_conditions(user):
	"""
	Obter condições de query para permissões ATCUD Log (para hooks.py)

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

		# Para outros usuários, apenas logs da sua empresa
		user_companies = frappe.get_all("User Permission",
										filters={
											"user": user or frappe.session.user,
											"allow": "Company"
										},
										fields=["for_value"])

		if user_companies:
			companies = [f"'{company.for_value}'" for company in user_companies]
			return f"`tabATCUD Log`.company in ({','.join(companies)})"

		return "1=0"

	except Exception as e:
		frappe.log_error(f"Error in get_permission_query_conditions_for_atcud: {str(e)}")
		return "1=0"


@frappe.whitelist()
def get_atcud_logs_for_document(document_type, document_name=None, company=None):
	"""
	Endpoint para obter logs ATCUD para um documento

	Args:
		document_type (str): Tipo de documento
		document_name (str): Nome do documento (opcional)
		company (str): Empresa (opcional)

	Returns:
		dict: Logs ATCUD encontrados
	"""
	try:
		filters = {"document_type": document_type}

		if document_name:
			filters["document_name"] = document_name

		if company:
			filters["company"] = company

		logs = frappe.get_all("ATCUD Log",
							  filters=filters,
							  fields=["name", "atcud_code", "document_name", "series_used",
									  "generation_status", "generation_date", "sequence_number"],
							  order_by="creation desc",
							  limit=50)

		return {
			"status": "success",
			"logs": logs,
			"total": len(logs)
		}

	except Exception as e:
		frappe.log_error(f"Error getting ATCUD logs: {str(e)}")
		return {
			"status": "error",
			"message": str(e),
			"logs": []
		}


@frappe.whitelist()
def validate_atcud_code(atcud_code):
	"""
	Endpoint para validar código ATCUD

	Args:
		atcud_code (str): Código ATCUD para validar

	Returns:
		dict: Resultado da validação
	"""
	try:
		if not atcud_code:
			return {
				"status": "error",
				"valid": False,
				"message": "Código ATCUD é obrigatório"
			}

		# Verificar se já existe
		existing = frappe.db.exists("ATCUD Log", {"atcud_code": atcud_code})

		if existing:
			log_doc = frappe.get_doc("ATCUD Log", existing)
			return {
				"status": "warning",
				"valid": True,
				"exists": True,
				"message": f"ATCUD já existe para documento {log_doc.document_name}",
				"existing_document": {
					"name": log_doc.document_name,
					"type": log_doc.document_type,
					"date": log_doc.generation_date
				}
			}

		# Validar formato básico (CODIGO-SEQUENCIA)
		if "-" not in atcud_code:
			return {
				"status": "error",
				"valid": False,
				"message": "Formato ATCUD inválido. Deve ser CODIGO-SEQUENCIA"
			}

		parts = atcud_code.split("-")
		if len(parts) != 2:
			return {
				"status": "error",
				"valid": False,
				"message": "Formato ATCUD inválido. Deve ter exatamente um hífen"
			}

		validation_code, sequence = parts

		# Validar código de validação (deve ter 8-10 caracteres)
		if len(validation_code) < 8 or len(validation_code) > 10:
			return {
				"status": "error",
				"valid": False,
				"message": "Código de validação deve ter entre 8 e 10 caracteres"
			}

		# Validar sequência (deve ser numérica)
		try:
			seq_num = int(sequence)
			if seq_num < 1:
				return {
					"status": "error",
					"valid": False,
					"message": "Sequência deve ser maior que zero"
				}
		except ValueError:
			return {
				"status": "error",
				"valid": False,
				"message": "Sequência deve ser numérica"
			}

		return {
			"status": "success",
			"valid": True,
			"exists": False,
			"message": "Código ATCUD válido",
			"validation_code": validation_code,
			"sequence": seq_num
		}

	except Exception as e:
		frappe.log_error(f"Error validating ATCUD code: {str(e)}")
		return {
			"status": "error",
			"valid": False,
			"message": str(e)
		}
