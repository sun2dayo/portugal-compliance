# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Queries for Portugal Compliance
Secure and optimized queries for Portuguese naming_series
Handles filtering, validation, and data retrieval for naming series
"""

import frappe
from frappe import _
from frappe.utils import cint, now, today
import re

@frappe.whitelist()
def get_naming_series_for_doctype(doctype, txt="", searchfield="naming_series", start=0,
								  page_len=20, filters=None):
	"""Query para naming series portuguesas - CORRIGIDA"""
	try:
		if not doctype:
			return []

		# Extrair filtros
		company = filters.get("company") if filters else None

		# Query simplificada
		conditions = ["document_type = %(doctype)s", "is_active = 1"]
		values = {"doctype": doctype}

		if company:
			conditions.append("company = %(company)s")
			values["company"] = company

		if txt:
			conditions.append("prefix LIKE %(txt)s")
			values["txt"] = f"%{txt}%"

		query = f"""
            SELECT
                CONCAT(prefix, '.####') as naming_series,
                prefix,
                series_name,
                is_communicated
            FROM `tabPortugal Series Configuration`
            WHERE {' AND '.join(conditions)}
            ORDER BY is_communicated DESC, prefix ASC
            LIMIT %(start)s, %(page_len)s
        """

		values.update({
			"start": int(start),
			"page_len": int(page_len)
		})

		results = frappe.db.sql(query, values, as_dict=True)

		# Formatar para Frappe
		formatted = []
		for row in results:
			status = "✅" if row.is_communicated else "⚠️"
			formatted.append([
				row.naming_series,
				f"{status} {row.prefix} - {row.series_name}"
			])

		return formatted

	except Exception as e:
		frappe.log_error(f"Error in get_naming_series_for_doctype: {str(e)}")
		return []


def get_naming_series_for_doctype(doctype, txt="", searchfield="naming_series", start=0,
								  page_len=20, filters=None):
	"""
	Query para obter naming_series portuguesas disponíveis para um DocType específico
	Usada em campos Link e Select com query personalizada
	"""
	try:
		# Validar parâmetros de entrada
		if not doctype:
			return []

		# Extrair filtros
		company = filters.get("company") if filters else None
		only_communicated = filters.get("only_communicated", False) if filters else False
		only_active = filters.get("only_active", True) if filters else True

		# Construir condições WHERE
		conditions = ["psc.document_type = %(doctype)s"]
		values = {"doctype": doctype}

		if company:
			conditions.append("psc.company = %(company)s")
			values["company"] = company

		if only_active:
			conditions.append("psc.is_active = 1")

		if only_communicated:
			conditions.append("psc.is_communicated = 1")
			conditions.append("psc.validation_code IS NOT NULL")
			conditions.append("psc.validation_code != ''")

		# Filtro de texto
		if txt:
			conditions.append("(psc.prefix LIKE %(txt)s OR psc.series_name LIKE %(txt)s)")
			values["txt"] = f"%{txt}%"

		# Query principal
		query = f"""
            SELECT
                CONCAT(psc.prefix, '.####') as naming_series,
                psc.prefix,
                psc.series_name,
                psc.is_communicated,
                psc.validation_code,
                psc.company,
                psc.at_environment
            FROM `tabPortugal Series Configuration` psc
            WHERE {' AND '.join(conditions)}
            ORDER BY
                psc.is_communicated DESC,
                psc.communication_date DESC,
                psc.prefix ASC
            LIMIT %(start)s, %(page_len)s
        """

		values.update({
			"start": cint(start),
			"page_len": cint(page_len)
		})

		# Executar query
		results = frappe.db.sql(query, values, as_dict=True)

		# Formatar resultados para o formato esperado pelo Frappe
		formatted_results = []
		for row in results:
			# Adicionar indicadores visuais
			status_indicator = "✅" if row.is_communicated else "⚠️"
			env_indicator = "🔴" if row.at_environment == "production" else "🟡"

			description = f"{status_indicator} {row.prefix}"
			if row.is_communicated and row.validation_code:
				description += f" (ATCUD: {row.validation_code[:8]}...)"

			if row.at_environment:
				description += f" {env_indicator}"

			formatted_results.append([
				row.naming_series,  # Valor retornado
				description,  # Descrição mostrada
				row.company  # Informação adicional
			])

		return formatted_results

	except Exception as e:
		frappe.log_error(f"Error in get_naming_series_for_doctype: {str(e)}")
		return []


def get_portuguese_series_list(doctype, company=None, include_inactive=False):
	"""
	Obter lista completa de séries portuguesas para um DocType
	"""
	try:
		conditions = ["document_type = %(doctype)s"]
		values = {"doctype": doctype}

		if company:
			conditions.append("company = %(company)s")
			values["company"] = company

		if not include_inactive:
			conditions.append("is_active = 1")

		query = f"""
            SELECT
                name,
                prefix,
                series_name,
                company,
                is_active,
                is_communicated,
                validation_code,
                current_sequence,
                total_documents_issued,
                communication_date,
                at_environment,
                creation,
                modified
            FROM `tabPortugal Series Configuration`
            WHERE {' AND '.join(conditions)}
            ORDER BY
                is_communicated DESC,
                is_active DESC,
                communication_date DESC,
                prefix ASC
        """

		return frappe.db.sql(query, values, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_portuguese_series_list: {str(e)}")
		return []


def get_series_by_prefix(prefix, company=None):
	"""
	Obter série portuguesa por prefixo
	"""
	try:
		conditions = ["prefix = %(prefix)s"]
		values = {"prefix": prefix}

		if company:
			conditions.append("company = %(company)s")
			values["company"] = company

		query = f"""
            SELECT
                name,
                prefix,
                series_name,
                document_type,
                company,
                is_active,
                is_communicated,
                validation_code,
                current_sequence,
                at_environment
            FROM `tabPortugal Series Configuration`
            WHERE {' AND '.join(conditions)}
            LIMIT 1
        """

		result = frappe.db.sql(query, values, as_dict=True)
		return result[0] if result else None

	except Exception as e:
		frappe.log_error(f"Error in get_series_by_prefix: {str(e)}")
		return None


def get_communicated_series_for_company(company):
	"""
	Obter todas as séries comunicadas para uma empresa
	"""
	try:
		query = """
				SELECT name, \
					   prefix, \
					   series_name, \
					   document_type, \
					   validation_code, \
					   communication_date, \
					   current_sequence, \
					   total_documents_issued, \
					   at_environment
				FROM `tabPortugal Series Configuration`
				WHERE company = %(company)s
				  AND is_active = 1
				  AND is_communicated = 1
				  AND validation_code IS NOT NULL
				  AND validation_code != ''
				ORDER BY document_type ASC, communication_date DESC \
				"""

		return frappe.db.sql(query, {"company": company}, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_communicated_series_for_company: {str(e)}")
		return []


def get_series_statistics_by_company(company):
	"""
	Obter estatísticas de séries por empresa
	"""
	try:
		query = """
				SELECT document_type, \
					   COUNT(*)                                             as total_series, \
					   SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END)       as active_series, \
					   SUM(CASE WHEN is_communicated = 1 THEN 1 ELSE 0 END) as communicated_series, \
					   SUM(CASE \
							   WHEN validation_code IS NOT NULL AND validation_code != '' THEN 1 \
							   ELSE 0 END)                                  as series_with_atcud, \
					   SUM(total_documents_issued)                          as total_documents, \
					   MAX(communication_date)                              as last_communication
				FROM `tabPortugal Series Configuration`
				WHERE company = %(company)s
				GROUP BY document_type
				ORDER BY document_type ASC \
				"""

		return frappe.db.sql(query, {"company": company}, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_series_statistics_by_company: {str(e)}")
		return []


def validate_naming_series_format(naming_series):
	"""
	Validar formato de naming series portuguesa
	"""
	try:
		if not naming_series:
			return False

		# Formato esperado: XX-YYYY-COMPANY.####
		pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{1,4}\.####$'
		return bool(re.match(pattern, naming_series))

	except Exception:
		return False


def get_next_sequence_for_series(series_name):
	"""
	Obter próxima sequência para uma série
	"""
	try:
		query = """
				SELECT current_sequence
				FROM `tabPortugal Series Configuration`
				WHERE name = %(series_name)s
				  AND is_active = 1 \
				"""

		result = frappe.db.sql(query, {"series_name": series_name}, as_dict=True)

		if result:
			return result[0].current_sequence
		else:
			return 1

	except Exception as e:
		frappe.log_error(f"Error in get_next_sequence_for_series: {str(e)}")
		return 1


def get_series_usage_report(date_from=None, date_to=None, company=None):
	"""
	Relatório de uso das séries
	"""
	try:
		conditions = ["psc.is_active = 1"]
		values = {}

		if company:
			conditions.append("psc.company = %(company)s")
			values["company"] = company

		if date_from:
			conditions.append("psc.creation >= %(date_from)s")
			values["date_from"] = date_from

		if date_to:
			conditions.append("psc.creation <= %(date_to)s")
			values["date_to"] = date_to

		query = f"""
            SELECT
                psc.name,
                psc.prefix,
                psc.series_name,
                psc.document_type,
                psc.company,
                psc.is_communicated,
                psc.validation_code,
                psc.current_sequence,
                psc.total_documents_issued,
                psc.communication_date,
                psc.at_environment,
                CASE
                    WHEN psc.total_documents_issued = 0 THEN 'Não Usada'
                    WHEN psc.total_documents_issued < 10 THEN 'Baixo Uso'
                    WHEN psc.total_documents_issued < 100 THEN 'Uso Médio'
                    ELSE 'Alto Uso'
                END as usage_category,
                DATEDIFF(CURDATE(), psc.last_used_date) as days_since_last_use
            FROM `tabPortugal Series Configuration` psc
            WHERE {' AND '.join(conditions)}
            ORDER BY
                psc.company ASC,
                psc.document_type ASC,
                psc.total_documents_issued DESC
        """

		return frappe.db.sql(query, values, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_series_usage_report: {str(e)}")
		return []


def get_series_by_document_name(doctype, document_name):
	"""
	Obter série portuguesa usada por um documento específico
	"""
	try:
		# Primeiro, obter naming_series do documento
		naming_series = frappe.db.get_value(doctype, document_name, "naming_series")

		if not naming_series:
			return None

		# Extrair prefixo da naming_series
		prefix = naming_series.replace('.####', '')

		# Buscar série portuguesa
		query = """
				SELECT name, \
					   prefix, \
					   series_name, \
					   document_type, \
					   company, \
					   is_communicated, \
					   validation_code, \
					   at_environment
				FROM `tabPortugal Series Configuration`
				WHERE prefix = %(prefix)s
				  AND document_type = %(doctype)s LIMIT 1 \
				"""

		result = frappe.db.sql(query, {
			"prefix": prefix,
			"doctype": doctype
		}, as_dict=True)

		return result[0] if result else None

	except Exception as e:
		frappe.log_error(f"Error in get_series_by_document_name: {str(e)}")
		return None


def get_duplicate_prefixes():
	"""
	Encontrar prefixos duplicados entre empresas
	"""
	try:
		query = """
				SELECT prefix, \
					   COUNT(*) as count,
                GROUP_CONCAT(DISTINCT company) as companies,
                GROUP_CONCAT(DISTINCT document_type) as document_types
				FROM `tabPortugal Series Configuration`
				WHERE is_active = 1
				GROUP BY prefix
				HAVING count > 1
				ORDER BY count DESC, prefix ASC \
				"""

		return frappe.db.sql(query, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_duplicate_prefixes: {str(e)}")
		return []


def get_series_communication_status():
	"""
	Status de comunicação de todas as séries
	"""
	try:
		query = """
				SELECT company, \
					   document_type, \
					   COUNT(*)                                             as total_series, \
					   SUM(CASE WHEN is_communicated = 1 THEN 1 ELSE 0 END) as communicated, \
					   SUM(CASE WHEN is_communicated = 0 THEN 1 ELSE 0 END) as not_communicated, \
					   ROUND( \
						   (SUM(CASE WHEN is_communicated = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100, \
						   2 \
					   )                                                    as communication_percentage
				FROM `tabPortugal Series Configuration`
				WHERE is_active = 1
				GROUP BY company, document_type
				ORDER BY company ASC, document_type ASC \
				"""

		return frappe.db.sql(query, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_series_communication_status: {str(e)}")
		return []


def search_series_by_atcud(atcud_code):
	"""
	Buscar série por código ATCUD
	"""
	try:
		if not atcud_code:
			return None

		# Extrair código de validação do ATCUD (parte antes do hífen)
		validation_code = atcud_code.split('-')[0] if '-' in atcud_code else atcud_code

		query = """
				SELECT name, \
					   prefix, \
					   series_name, \
					   document_type, \
					   company, \
					   validation_code, \
					   current_sequence, \
					   at_environment
				FROM `tabPortugal Series Configuration`
				WHERE validation_code = %(validation_code)s
				  AND is_active = 1
				  AND is_communicated = 1 LIMIT 1 \
				"""

		result = frappe.db.sql(query, {"validation_code": validation_code}, as_dict=True)
		return result[0] if result else None

	except Exception as e:
		frappe.log_error(f"Error in search_series_by_atcud: {str(e)}")
		return None


def get_series_health_check():
	"""
	Verificação de saúde das séries portuguesas
	"""
	try:
		query = """
				SELECT 'Total Séries' as metric, \
					   COUNT(*) as value,
                'info' as status
				FROM `tabPortugal Series Configuration`

				UNION ALL

				SELECT 'Séries Ativas' as metric, \
					   COUNT(*) as value,
                'success' as status
				FROM `tabPortugal Series Configuration`
				WHERE is_active = 1

				UNION ALL

				SELECT 'Séries Comunicadas' as metric, \
					   COUNT(*) as value,
                'success' as status
				FROM `tabPortugal Series Configuration`
				WHERE is_communicated = 1

				UNION ALL

				SELECT 'Séries Não Comunicadas' as metric, \
					   COUNT(*) as value,
                CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'success' \
				END as status
            FROM `tabPortugal Series Configuration`
            WHERE is_active = 1 AND is_communicated = 0

            UNION ALL

				SELECT 'Séries com ATCUD' as metric, \
					   COUNT(*) as value,
                'success' as status
				FROM `tabPortugal Series Configuration`
				WHERE validation_code IS NOT NULL AND validation_code != ''

				UNION ALL

				SELECT 'Prefixos Duplicados' as metric, \
					   COUNT(*) as value,
                CASE WHEN COUNT(*) > 0 THEN 'danger' ELSE 'success' \
				END as status
            FROM (
                SELECT prefix
                FROM `tabPortugal Series Configuration`
                WHERE is_active = 1
                GROUP BY prefix
                HAVING COUNT(*) > 1
            ) duplicates \
				"""

		return frappe.db.sql(query, as_dict=True)

	except Exception as e:
		frappe.log_error(f"Error in get_series_health_check: {str(e)}")
		return []


# ========== FUNÇÕES DE SEGURANÇA ==========

def validate_query_permissions(user=None, company=None):
	"""
	Validar permissões para queries de séries
	"""
	try:
		if not user:
			user = frappe.session.user

		# Verificar se usuário tem permissão para Portugal Series Configuration
		if not frappe.has_permission("Portugal Series Configuration", "read", user=user):
			return False

		# Se empresa específica, verificar permissão para a empresa
		if company:
			if not frappe.has_permission("Company", "read", doc=company, user=user):
				return False

		return True

	except Exception:
		return False


def sanitize_query_input(value):
	"""
	Sanitizar entrada para queries
	"""
	try:
		if not value:
			return value

		# Remover caracteres perigosos
		dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]

		sanitized = str(value)
		for char in dangerous_chars:
			sanitized = sanitized.replace(char, "")

		# Limitar tamanho
		return sanitized[:100]

	except Exception:
		return ""


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def get_naming_series_options(doctype, company=None, only_communicated=False):
	"""
	API para obter opções de naming series
	"""
	try:
		# Validar permissões
		if not validate_query_permissions(company=company):
			frappe.throw(_("Insufficient permissions"))

		# Sanitizar entradas
		doctype = sanitize_query_input(doctype)
		company = sanitize_query_input(company) if company else None

		# Obter séries
		series_list = get_portuguese_series_list(
			doctype=doctype,
			company=company,
			include_inactive=False
		)

		# Filtrar apenas comunicadas se solicitado
		if cint(only_communicated):
			series_list = [s for s in series_list if s.is_communicated]

		# Formatar para retorno
		options = []
		for series in series_list:
			naming_series = f"{series.prefix}.####"
			status = "✅ Comunicada" if series.is_communicated else "⚠️ Não Comunicada"

			options.append({
				"value": naming_series,
				"label": f"{series.prefix} - {status}",
				"description": f"Empresa: {series.company}",
				"is_communicated": series.is_communicated,
				"validation_code": series.validation_code
			})

		return {
			"success": True,
			"options": options,
			"total": len(options)
		}

	except Exception as e:
		frappe.log_error(f"Error in get_naming_series_options: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_series_info_by_prefix(prefix, company=None):
	"""
	API para obter informações de uma série por prefixo
	"""
	try:
		# Validar permissões
		if not validate_query_permissions(company=company):
			frappe.throw(_("Insufficient permissions"))

		# Sanitizar entradas
		prefix = sanitize_query_input(prefix)
		company = sanitize_query_input(company) if company else None

		# Obter série
		series = get_series_by_prefix(prefix, company)

		if series:
			return {
				"success": True,
				"series": series
			}
		else:
			return {
				"success": False,
				"message": "Série não encontrada"
			}

	except Exception as e:
		frappe.log_error(f"Error in get_series_info_by_prefix: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_company_series_statistics(company):
	"""
	API para obter estatísticas de séries de uma empresa
	"""
	try:
		# Validar permissões
		if not validate_query_permissions(company=company):
			frappe.throw(_("Insufficient permissions"))

		# Sanitizar entrada
		company = sanitize_query_input(company)

		# Obter estatísticas
		stats = get_series_statistics_by_company(company)
		health = get_series_health_check()

		return {
			"success": True,
			"statistics": stats,
			"health_check": health
		}

	except Exception as e:
		frappe.log_error(f"Error in get_company_series_statistics: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_naming_series_for_doctype(doctype, txt="", searchfield="naming_series", start=0,
								  page_len=20, filters=None):
	"""Query para naming series portuguesas"""
	try:
		if not doctype:
			return []

		# Query simplificada
		conditions = ["document_type = %(doctype)s", "is_active = 1"]
		values = {"doctype": doctype}

		company = filters.get("company") if filters else None
		if company:
			conditions.append("company = %(company)s")
			values["company"] = company

		if txt:
			conditions.append("prefix LIKE %(txt)s")
			values["txt"] = f"%{txt}%"

		query = f"""
            SELECT
                CONCAT(prefix, '.####') as naming_series,
                prefix,
                series_name
            FROM `tabPortugal Series Configuration`
            WHERE {' AND '.join(conditions)}
            ORDER BY prefix ASC
            LIMIT %(start)s, %(page_len)s
        """

		values.update({"start": int(start), "page_len": int(page_len)})
		results = frappe.db.sql(query, values, as_dict=True)

		return [[row.naming_series, f"{row.prefix} - {row.series_name}"] for row in results]

	except Exception as e:
		frappe.log_error(f"Error in get_naming_series_for_doctype: {str(e)}")
		return []
