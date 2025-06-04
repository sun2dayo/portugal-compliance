# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam em todos os eventos do scheduler
"""

import frappe
from frappe import _
from frappe.utils import now, get_datetime


def execute():
	"""
	Função principal executada em todos os eventos do scheduler
	"""
	try:
		# Log de execução
		frappe.logger().info("Portugal Compliance: Executing 'all' scheduled task")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			return

		# Tarefas que devem executar sempre
		check_system_health()
		update_cache_if_needed()
		log_system_metrics()

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.all: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo

	Returns:
		bool: True se ativo, False caso contrário
	"""
	try:
		# Verificar se existe pelo menos uma empresa com compliance ativo
		companies_with_compliance = frappe.db.count("Company", {
			"portugal_compliance_enabled": 1
		})

		return companies_with_compliance > 0

	except Exception:
		return False


def check_system_health():
	"""
	Verifica saúde geral do sistema Portugal Compliance
	"""
	try:
		# Verificar conectividade básica
		check_database_connectivity()

		# Verificar integridade de dados críticos
		check_critical_data_integrity()

		# Verificar configurações básicas
		check_basic_configurations()

	except Exception as e:
		frappe.log_error(f"Error in system health check: {str(e)}")


def check_database_connectivity():
	"""
	Verifica conectividade com a base de dados
	"""
	try:
		# Teste simples de conectividade
		frappe.db.sql("SELECT 1")

		# Verificar se tabelas críticas existem
		critical_tables = [
			"tabPortugal Series Configuration",
			"tabATCUD Log",
			"tabSAF-T Export Log"
		]

		for table in critical_tables:
			if not frappe.db.table_exists(table):
				frappe.log_error(f"Critical table missing: {table}")

	except Exception as e:
		frappe.log_error(f"Database connectivity check failed: {str(e)}")


def check_critical_data_integrity():
	"""
	Verifica integridade de dados críticos
	"""
	try:
		# Verificar séries sem ATCUD
		series_without_atcud = frappe.db.sql("""
											 SELECT name
											 FROM `tabPortugal Series Configuration`
											 WHERE is_communicated = 1
											   AND validation_code IS NULL
											 """)

		if series_without_atcud:
			frappe.log_error(f"Found {len(series_without_atcud)} series without validation code")

		# Verificar documentos com ATCUD duplicado
		duplicate_atcud = frappe.db.sql("""
										SELECT atcud_code, COUNT(*) as count
										FROM `tabATCUD Log`
										WHERE atcud_code IS NOT NULL
										GROUP BY atcud_code
										HAVING count > 1
										""")

		if duplicate_atcud:
			frappe.log_error(f"Found {len(duplicate_atcud)} duplicate ATCUD codes")

	except Exception as e:
		frappe.log_error(f"Data integrity check failed: {str(e)}")


def check_basic_configurations():
	"""
	Verifica configurações básicas do sistema
	"""
	try:
		# Verificar empresas portuguesas sem NIF
		companies_without_nif = frappe.db.sql("""
											  SELECT name
											  FROM `tabCompany`
											  WHERE country = 'Portugal'
												AND (tax_id IS NULL OR tax_id = '')
											  """)

		if companies_without_nif:
			frappe.log_error(
				f"Found {len(companies_without_nif)} Portuguese companies without NIF")

		# Verificar configurações de compliance
		companies_with_compliance = frappe.db.count("Company", {
			"portugal_compliance_enabled": 1,
			"country": "Portugal"
		})

		if companies_with_compliance == 0:
			frappe.logger().warning("No Portuguese companies with compliance enabled")

	except Exception as e:
		frappe.log_error(f"Configuration check failed: {str(e)}")


def update_cache_if_needed():
	"""
	Atualiza cache se necessário
	"""
	try:
		# Verificar se cache precisa ser atualizado
		last_cache_update = frappe.cache.get("portugal_compliance_last_cache_update")
		current_time = get_datetime()

		# Atualizar cache a cada 5 minutos
		if not last_cache_update or (current_time - get_datetime(last_cache_update)).seconds > 300:
			# Atualizar cache de séries ativas
			update_active_series_cache()

			# Atualizar cache de configurações
			update_configurations_cache()

			# Marcar última atualização
			frappe.cache.set("portugal_compliance_last_cache_update", now())

	except Exception as e:
		frappe.log_error(f"Cache update failed: {str(e)}")


def update_active_series_cache():
	"""
	Atualiza cache de séries ativas
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1, "is_communicated": 1},
										  fields=["name", "series_name", "prefix", "document_type",
												  "company"]
										  )

		# Organizar por empresa e tipo de documento
		series_by_company = {}
		for series in active_series:
			company = series.get("company")
			doc_type = series.get("document_type")

			if company not in series_by_company:
				series_by_company[company] = {}

			if doc_type not in series_by_company[company]:
				series_by_company[company][doc_type] = []

			series_by_company[company][doc_type].append(series)

		# Armazenar no cache
		frappe.cache.set("portugal_compliance_active_series", series_by_company,
						 expires_in_sec=3600)

	except Exception as e:
		frappe.log_error(f"Active series cache update failed: {str(e)}")


def update_configurations_cache():
	"""
	Atualiza cache de configurações
	"""
	try:
		# Cache de empresas com compliance ativo
		companies_with_compliance = frappe.db.get_all("Company",
													  filters={"portugal_compliance_enabled": 1},
													  fields=["name", "company_name", "tax_id",
															  "at_certificate_number"]
													  )

		frappe.cache.set("portugal_compliance_companies", companies_with_compliance,
						 expires_in_sec=3600)

		# Cache de configurações globais
		global_config = {
			"total_companies": len(companies_with_compliance),
			"last_update": now(),
			"system_status": "active"
		}

		frappe.cache.set("portugal_compliance_global_config", global_config, expires_in_sec=3600)

	except Exception as e:
		frappe.log_error(f"Configurations cache update failed: {str(e)}")


def log_system_metrics():
	"""
	Regista métricas do sistema
	"""
	try:
		# Contar documentos processados hoje
		from frappe.utils import today

		today_date = today()

		metrics = {
			"date": today_date,
			"timestamp": now(),
			"atcud_generated_today": frappe.db.count("ATCUD Log", {
				"creation": [">=", today_date]
			}),
			"series_communicated_today": frappe.db.count("Portugal Series Configuration", {
				"communication_date": [">=", today_date],
				"is_communicated": 1
			}),
			"active_series_total": frappe.db.count("Portugal Series Configuration", {
				"is_active": 1
			}),
			"companies_with_compliance": frappe.db.count("Company", {
				"portugal_compliance_enabled": 1
			})
		}

		# Armazenar métricas no cache (apenas para consulta rápida)
		frappe.cache.set("portugal_compliance_daily_metrics", metrics, expires_in_sec=86400)

		# Log apenas se houver atividade significativa
		if metrics["atcud_generated_today"] > 0 or metrics["series_communicated_today"] > 0:
			frappe.logger().info(f"Portugal Compliance Daily Metrics: {metrics}")

	except Exception as e:
		frappe.log_error(f"System metrics logging failed: {str(e)}")


def cleanup_temporary_data():
	"""
	Limpa dados temporários se necessário
	"""
	try:
		# Limpar cache expirado
		expired_cache_keys = [
			"portugal_compliance_temp_*",
			"atcud_generation_temp_*"
		]

		for key_pattern in expired_cache_keys:
			# Frappe não tem wildcard delete, então usar método alternativo
			pass  # Implementar se necessário

	except Exception as e:
		frappe.log_error(f"Temporary data cleanup failed: {str(e)}")


# Função de utilidade para outras tarefas
def get_system_status():
	"""
	Retorna status atual do sistema

	Returns:
		dict: Status do sistema
	"""
	try:
		return {
			"status": "healthy" if is_portugal_compliance_enabled() else "inactive",
			"last_check": now(),
			"companies_active": frappe.db.count("Company", {"portugal_compliance_enabled": 1}),
			"series_active": frappe.db.count("Portugal Series Configuration", {"is_active": 1})
		}
	except Exception:
		return {"status": "error", "last_check": now()}
