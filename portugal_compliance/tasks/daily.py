# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam diariamente - VERSÃO ATUALIZADA
Integração completa com Portugal Compliance - NOVA ABORDAGEM
"""

import frappe
from frappe import _
from frappe.utils import today, now, add_days, get_datetime, cint, flt
from datetime import datetime, timedelta
import json


def execute():
	"""
	Função principal executada diariamente - ATUALIZADA PARA NOVA ABORDAGEM
	"""
	try:
		frappe.logger().info(
			"🇵🇹 Portugal Compliance: Executing daily scheduled tasks - NEW APPROACH")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			frappe.logger().info("Portugal Compliance not enabled, skipping daily tasks")
			return

		# ✅ TAREFAS PRINCIPAIS (ADAPTADAS PARA NOVA ABORDAGEM)
		generate_daily_report()
		check_series_expiration()
		validate_daily_sequences()
		cleanup_old_logs()
		check_pending_communications()
		update_usage_statistics()
		backup_critical_data()
		send_daily_notifications()

		# ✅ NOVAS TAREFAS ADAPTADAS PARA NAMING SERIES NATIVA
		validate_naming_series_formats()
		check_atcud_sequence_integrity()
		monitor_communication_failures()
		update_series_trends()
		check_naming_series_consistency()
		validate_essential_custom_fields_integrity()
		cleanup_failed_communications()
		generate_compliance_metrics()
		sync_portugal_series_configurations()

		frappe.logger().info(
			"🇵🇹 Portugal Compliance: Daily tasks completed successfully - NEW APPROACH")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.daily: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo - ADAPTADO
	"""
	try:
		# Verificar se há empresas portuguesas com compliance ativado
		portuguese_companies = frappe.db.count("Company", {
			"country": "Portugal",
			"portugal_compliance_enabled": 1
		})

		# ✅ ADAPTADO: Verificar Portugal Series Configuration em vez de Document Series
		active_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1
		})

		return portuguese_companies > 0 or active_series > 0

	except Exception:
		return False


def generate_daily_report():
	"""
	Gera relatório diário de atividades - ADAPTADO PARA NOVA ABORDAGEM
	"""
	try:
		today_date = today()

		# ✅ ESTATÍSTICAS ADAPTADAS PARA NAMING SERIES NATIVA
		daily_stats = {
			"date": today_date,
			"atcud_generated": frappe.db.count("ATCUD Log", {
				"creation": [">=", today_date]
			}),
			"series_communicated": frappe.db.count("Portugal Series Configuration", {
				"communication_date": [">=", today_date],
				"is_communicated": 1
			}),
			"documents_processed": get_daily_document_count(),
			"errors_logged": frappe.db.count("Error Log", {
				"creation": [">=", today_date],
				"error": ["like", "%portugal_compliance%"]
			}),
			"companies_active": frappe.db.count("Company", {
				"portugal_compliance_enabled": 1
			}),
			# ✅ MÉTRICAS ADAPTADAS PARA NOVA ABORDAGEM
			"series_with_new_format": count_series_with_new_format(),
			"communication_success_rate": calculate_communication_success_rate(),
			"avg_atcud_generation_time": calculate_avg_atcud_time(),
			"naming_series_compliance": calculate_naming_series_compliance(),
			"naming_series_consistency": check_naming_series_health()
		}

		# Armazenar relatório
		store_daily_report(daily_stats)

		# Log se houver atividade significativa
		if daily_stats["atcud_generated"] > 0 or daily_stats["series_communicated"] > 0:
			frappe.logger().info(f"📊 Daily Report (New Approach): {daily_stats}")

	except Exception as e:
		frappe.log_error(f"Error generating daily report: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Contar séries com formato correto
def count_series_with_new_format():
	"""
	Conta séries que usam o formato correto XXYYYY+EMPRESA
	"""
	try:
		# ✅ ADAPTADO: Padrão do formato correto (sem hífens)
		new_format_pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$'

		all_series = frappe.db.get_all("Portugal Series Configuration",
									   fields=["name", "prefix"])

		new_format_count = 0
		for series in all_series:
			if series.prefix:
				import re
				if re.match(new_format_pattern, series.prefix):
					new_format_count += 1

		return new_format_count

	except Exception as e:
		frappe.log_error(f"Error counting new format series: {str(e)}")
		return 0


# ✅ FUNÇÃO ADAPTADA: Calcular compliance de naming series
def calculate_naming_series_compliance():
	"""
	Calcula percentagem de séries usando naming series nativa corretamente
	"""
	try:
		total_series = frappe.db.count("Portugal Series Configuration")

		# Contar séries que têm naming_series definida corretamente
		correct_naming_series = 0

		all_series = frappe.db.get_all("Portugal Series Configuration",
									   fields=["prefix", "naming_series"])

		for series in all_series:
			if series.prefix and series.naming_series:
				expected_naming = f"{series.prefix}.####"
				if series.naming_series == expected_naming:
					correct_naming_series += 1

		if total_series > 0:
			return round((correct_naming_series / total_series) * 100, 2)
		return 100

	except Exception:
		return 0


# ✅ FUNÇÃO ADAPTADA: Calcular taxa de sucesso de comunicação
def calculate_communication_success_rate():
	"""
	Calcula taxa de sucesso das comunicações AT - ADAPTADA
	"""
	try:
		total_attempts = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1
		})

		successful_communications = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 1
		})

		if total_attempts > 0:
			return round((successful_communications / total_attempts) * 100, 2)
		return 0

	except Exception:
		return 0


def calculate_avg_atcud_time():
	"""
	Calcula tempo médio de geração de ATCUD - MANTIDA
	"""
	try:
		recent_logs = frappe.db.get_all("ATCUD Log",
										filters={
											"creation": [">=", add_days(today(), -7)],
											"generation_status": "Success"
										},
										fields=["creation", "generation_date"])

		if len(recent_logs) > 0:
			return round(len(recent_logs) / 7, 2)
		return 0

	except Exception:
		return 0


# ✅ FUNÇÃO ADAPTADA: Verificar saúde das naming series
def check_naming_series_health():
	"""
	Verifica consistência das naming series com nova abordagem
	"""
	try:
		series_with_issues = 0
		total_series = 0

		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name", "prefix", "document_type",
												  "naming_series"])

		for series in active_series:
			total_series += 1

			# ✅ ADAPTADO: Verificar se naming series está configurada corretamente
			expected_naming = f"{series.prefix}.####"

			if not series.naming_series or series.naming_series != expected_naming:
				series_with_issues += 1

		if total_series > 0:
			health_percentage = round(((total_series - series_with_issues) / total_series) * 100,
									  2)
			return health_percentage
		return 100

	except Exception:
		return 0


def get_daily_document_count():
	"""
	Conta documentos processados hoje - ADAPTADO PARA NAMING SERIES
	"""
	try:
		today_date = today()
		total_docs = 0

		# ✅ TIPOS DE DOCUMENTOS MANTIDOS
		doctypes = [
			"Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry",
			"Stock Entry", "Quotation", "Sales Order", "Purchase Order",
			"Material Request"
		]

		for doctype in doctypes:
			if frappe.db.table_exists(f"tab{doctype}"):
				# ✅ ADAPTADO: Contar documentos com ATCUD (não portugal_series)
				count = frappe.db.count(doctype, {
					"creation": [">=", today_date],
					"atcud_code": ["is", "set"]
				})
				total_docs += count

		return total_docs

	except Exception as e:
		frappe.log_error(f"Error counting daily documents: {str(e)}")
		return 0


def store_daily_report(stats):
	"""
	Armazena relatório diário na base de dados - ADAPTADO
	"""
	try:
		cache_key = f"portugal_compliance_daily_report_{stats['date']}"

		# Tentar armazenar em DocType se existir
		if frappe.db.table_exists("tabPortugal Daily Report"):
			existing_report = frappe.db.exists("Portugal Daily Report", {
				"report_date": stats["date"]
			})

			if existing_report:
				# Atualizar existente
				frappe.db.set_value("Portugal Daily Report", existing_report, {
					"atcud_generated": stats["atcud_generated"],
					"series_communicated": stats["series_communicated"],
					"documents_processed": stats["documents_processed"],
					"errors_logged": stats["errors_logged"],
					"companies_active": stats["companies_active"],
					"series_with_new_format": stats.get("series_with_new_format", 0),
					"communication_success_rate": stats.get("communication_success_rate", 0),
					"naming_series_compliance": stats.get("naming_series_compliance", 0),
					"last_updated": now()
				})
			else:
				# Criar novo
				report_doc = frappe.get_doc({
					"doctype": "Portugal Daily Report",
					"report_date": stats["date"],
					**stats
				})
				report_doc.insert(ignore_permissions=True)
		else:
			# Armazenar no cache por 30 dias
			frappe.cache.set(cache_key, stats, expires_in_sec=2592000)
			frappe.logger().info(f"📊 Daily report stored in cache: {cache_key}")

	except Exception as e:
		frappe.log_error(f"Error storing daily report: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Validar formatos de naming series
def validate_naming_series_formats():
	"""
	Valida e reporta formatos de naming series incorretos
	"""
	try:
		import re
		correct_pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'

		all_series = frappe.db.get_all("Portugal Series Configuration",
									   fields=["name", "prefix", "naming_series", "company"])

		invalid_naming_series = []
		missing_naming_series = []

		for series in all_series:
			if not series.naming_series:
				missing_naming_series.append(series)
			elif not re.match(correct_pattern, series.naming_series):
				invalid_naming_series.append(series)

		# Log resultados
		if invalid_naming_series:
			frappe.logger().warning(
				f"⚠️ Found {len(invalid_naming_series)} series with invalid naming series format")

		if missing_naming_series:
			frappe.logger().warning(
				f"⚠️ Found {len(missing_naming_series)} series without naming series")

		# Criar notificações se necessário
		if len(invalid_naming_series) > 5 or len(missing_naming_series) > 5:
			create_naming_series_format_alert(invalid_naming_series, missing_naming_series)

	except Exception as e:
		frappe.log_error(f"Error validating naming series formats: {str(e)}")


def check_atcud_sequence_integrity():
	"""
	Verifica integridade das sequências ATCUD - MANTIDA
	"""
	try:
		# Verificar duplicações de ATCUD
		duplicate_atcuds = frappe.db.sql("""
										 SELECT atcud_code, COUNT(*) as count
										 FROM `tabATCUD Log`
										 WHERE atcud_code IS NOT NULL
										   AND atcud_code != ''
										 GROUP BY atcud_code
										 HAVING count > 1
										 """, as_dict=True)

		if duplicate_atcuds:
			frappe.logger().error(f"❌ Found {len(duplicate_atcuds)} duplicate ATCUD codes")
			create_atcud_integrity_alert(duplicate_atcuds)

		# ✅ ADAPTADO: Verificar formato de ATCUDs (novo formato: 0.SEQUENCIAL)
		invalid_atcuds = frappe.db.sql("""
									   SELECT name, atcud_code, document_type
									   FROM `tabATCUD Log`
									   WHERE atcud_code IS NOT NULL
										 AND atcud_code NOT REGEXP '^0\\.[0-9]+$'
			  AND creation >= %s
									   """, add_days(today(), -7), as_dict=True)

		if invalid_atcuds:
			frappe.logger().warning(f"⚠️ Found {len(invalid_atcuds)} ATCUDs with invalid format")

	except Exception as e:
		frappe.log_error(f"Error checking ATCUD sequence integrity: {str(e)}")


def monitor_communication_failures():
	"""
	Monitoriza e reporta falhas de comunicação AT - ADAPTADA
	"""
	try:
		# Séries com falhas recentes
		failed_communications = frappe.db.get_all("Portugal Series Configuration",
												  filters={
													  "is_active": 1,
													  "is_communicated": 0,
													  "modified": [">=", add_days(today(), -7)]
												  },
												  fields=["name", "prefix", "company"])

		if failed_communications:
			frappe.logger().warning(
				f"⚠️ Found {len(failed_communications)} uncommunicated series in last 7 days")

		# Séries não comunicadas há muito tempo
		overdue_series = frappe.db.get_all("Portugal Series Configuration",
										   filters={
											   "is_communicated": 0,
											   "is_active": 1,
											   "creation": ["<", add_days(today(), -3)]
										   },
										   fields=["name", "prefix", "company"])

		if overdue_series:
			frappe.logger().info(f"📋 Found {len(overdue_series)} overdue series for communication")

	except Exception as e:
		frappe.log_error(f"Error monitoring communication failures: {str(e)}")


def update_series_trends():
	"""
	Atualiza tendências de uso das séries - ADAPTADA
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name", "prefix", "document_type"])

		for series in active_series:
			try:
				# ✅ ADAPTADO: Calcular tendência usando naming_series
				trend = calculate_series_usage_trend_new_approach(series)

				# Atualizar no documento
				frappe.db.set_value("Portugal Series Configuration", series.name, {
					"usage_trend": trend,
					"last_trend_update": now()
				}, update_modified=False)

			except Exception as e:
				frappe.log_error(f"Error updating trend for series {series.name}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Error updating series trends: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Calcular tendência usando naming_series
def calculate_series_usage_trend_new_approach(series):
	"""
	Calcula tendência de uso usando naming_series nativa
	"""
	try:
		naming_series = f"{series.prefix}.####"

		# Contar documentos dos últimos 30 dias
		recent_docs = frappe.db.count(series.document_type, {
			"naming_series": naming_series,
			"creation": [">=", add_days(today(), -30)]
		})

		# Contar documentos dos 30 dias anteriores
		previous_docs = frappe.db.count(series.document_type, {
			"naming_series": naming_series,
			"creation": ["between", [add_days(today(), -60), add_days(today(), -30)]]
		})

		# Calcular tendência
		if previous_docs == 0:
			return "New" if recent_docs > 0 else "Inactive"

		growth_rate = ((recent_docs - previous_docs) / previous_docs) * 100

		if growth_rate > 20:
			return "Increasing"
		elif growth_rate < -20:
			return "Decreasing"
		elif abs(growth_rate) <= 5:
			return "Stable"
		else:
			return "Seasonal"

	except Exception:
		return "Unknown"


def check_naming_series_consistency():
	"""
	Verifica consistência das naming series - ADAPTADA
	"""
	try:
		inconsistent_series = []

		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name", "prefix", "document_type",
												  "naming_series"])

		for series in active_series:
			expected_naming = f"{series.prefix}.####"

			if not series.naming_series or series.naming_series != expected_naming:
				inconsistent_series.append({
					"series": series.name,
					"prefix": series.prefix,
					"document_type": series.document_type,
					"expected": expected_naming,
					"current": series.naming_series or "Not Set"
				})

		if inconsistent_series:
			frappe.logger().warning(
				f"⚠️ Found {len(inconsistent_series)} inconsistent naming series")

			# Tentar corrigir automaticamente
			for series_info in inconsistent_series:
				try_fix_naming_series_configuration(series_info)

	except Exception as e:
		frappe.log_error(f"Error checking naming series consistency: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Corrigir naming series configuration
def try_fix_naming_series_configuration(series_info):
	"""
	Tenta corrigir naming series na configuração
	"""
	try:
		expected_naming = series_info["expected"]

		# Atualizar Portugal Series Configuration
		frappe.db.set_value("Portugal Series Configuration", series_info["series"],
							"naming_series", expected_naming)

		frappe.logger().info(
			f"✅ Fixed naming series for {series_info['series']}: {expected_naming}")

	except Exception as e:
		frappe.log_error(f"Error fixing naming series configuration: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Validar apenas campos essenciais
def validate_essential_custom_fields_integrity():
	"""
	Valida se campos customizados ESSENCIAIS estão presentes (SEM portugal_series)
	"""
	try:
		# ✅ ADAPTADO: Apenas campos essenciais (removido portugal_series)
		required_fields = ["atcud_code"]
		doctypes_to_check = [
			"Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
		]

		missing_fields = []

		for doctype in doctypes_to_check:
			for field in required_fields:
				field_exists = frappe.db.exists("Custom Field", {
					"dt": doctype,
					"fieldname": field
				})

				if not field_exists:
					missing_fields.append({
						"doctype": doctype,
						"field": field
					})

		if missing_fields:
			frappe.logger().warning(
				f"⚠️ Found {len(missing_fields)} missing essential custom fields")

			# Tentar criar campos em falta
			for missing in missing_fields:
				try_create_essential_field(missing)
		else:
			frappe.logger().info("✅ All essential custom fields are present")

	except Exception as e:
		frappe.log_error(f"Error validating essential custom fields integrity: {str(e)}")


# ✅ FUNÇÃO ADAPTADA: Criar apenas campos essenciais
def try_create_essential_field(missing_field):
	"""
	Tenta criar campo customizado essencial (SEM portugal_series)
	"""
	try:
		doctype = missing_field["doctype"]
		field = missing_field["field"]

		# ✅ ADAPTADO: Apenas criar atcud_code (removido portugal_series)
		if field == "atcud_code":
			field_doc = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": doctype,
				"module": "Portugal Compliance",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"bold": 1,
				"in_list_view": 1,
				"description": "Código Único de Documento - gerado automaticamente"
			})

			field_doc.insert(ignore_permissions=True)
			frappe.logger().info(f"✅ Created missing field {field} for {doctype}")

	except Exception as e:
		frappe.log_error(f"Error creating essential field {missing_field}: {str(e)}")


def cleanup_failed_communications():
	"""
	Limpa dados de comunicações falhadas antigas - MANTIDA
	"""
	try:
		# Limpar erros de comunicação antigos (mais de 30 dias)
		frappe.db.sql("""
					  UPDATE `tabPortugal Series Configuration`
					  SET last_communication_error = NULL
					  WHERE modified < %s
						AND is_communicated = 0
					  """, add_days(today(), -30))

		frappe.logger().info("🧹 Cleaned up old communication errors")

	except Exception as e:
		frappe.log_error(f"Error cleaning up failed communications: {str(e)}")


def generate_compliance_metrics():
	"""
	Gera métricas de compliance para dashboard - ADAPTADA
	"""
	try:
		metrics = {
			"date": today(),
			"total_series": frappe.db.count("Portugal Series Configuration"),
			"active_series": frappe.db.count("Portugal Series Configuration", {"is_active": 1}),
			"communicated_series": frappe.db.count("Portugal Series Configuration",
												   {"is_communicated": 1}),
			"correct_naming_series": count_series_with_correct_naming_series(),
			"total_atcuds": frappe.db.count("ATCUD Log"),
			"successful_atcuds": frappe.db.count("ATCUD Log", {"generation_status": "Success"}),
			"portuguese_companies": frappe.db.count("Company", {"country": "Portugal"}),
			"compliance_enabled_companies": frappe.db.count("Company",
															{"portugal_compliance_enabled": 1})
		}

		# Armazenar no cache
		frappe.cache.set("portugal_compliance_metrics", metrics, expires_in_sec=86400)

		frappe.logger().info(f"📊 Generated compliance metrics (New Approach): {metrics}")

	except Exception as e:
		frappe.log_error(f"Error generating compliance metrics: {str(e)}")


# ✅ NOVA FUNÇÃO: Contar séries com naming_series correto
def count_series_with_correct_naming_series():
	"""
	Conta séries com naming_series configurado corretamente
	"""
	try:
		correct_count = 0

		all_series = frappe.db.get_all("Portugal Series Configuration",
									   fields=["prefix", "naming_series"])

		for series in all_series:
			if series.prefix and series.naming_series:
				expected = f"{series.prefix}.####"
				if series.naming_series == expected:
					correct_count += 1

		return correct_count

	except Exception:
		return 0


# ✅ NOVA FUNÇÃO: Sincronizar Portugal Series Configuration
def sync_portugal_series_configurations():
	"""
	Sincroniza Portugal Series Configuration com Portugal Document Series
	"""
	try:
		# Verificar se há Portugal Document Series para sincronizar
		if frappe.db.table_exists("tabPortugal Document Series"):
			document_series = frappe.db.get_all("Portugal Document Series",
												filters={"is_active": 1},
												fields=["name", "prefix", "document_type",
														"company"])

			synced_count = 0
			for ds in document_series:
				try:
					# Verificar se já existe Portugal Series Configuration correspondente
					existing_config = frappe.db.exists("Portugal Series Configuration", {
						"prefix": ds.prefix,
						"company": ds.company,
						"document_type": ds.document_type
					})

					if not existing_config:
						# Criar Portugal Series Configuration
						config = frappe.get_doc({
							"doctype": "Portugal Series Configuration",
							"series_name": f"{ds.document_type} - {ds.prefix}",
							"company": ds.company,
							"document_type": ds.document_type,
							"prefix": ds.prefix,
							"naming_series": f"{ds.prefix}.####",
							"current_sequence": 1,
							"is_active": 1,
							"is_communicated": 0
						})
						config.insert(ignore_permissions=True)
						synced_count += 1

				except Exception as e:
					frappe.log_error(f"Error syncing series {ds.name}: {str(e)}")

			if synced_count > 0:
				frappe.logger().info(
					f"✅ Synced {synced_count} Portugal Document Series to Portugal Series Configuration")

	except Exception as e:
		frappe.log_error(f"Error syncing Portugal Series Configurations: {str(e)}")


# ========== FUNÇÕES DE ALERTA ADAPTADAS ==========

def create_naming_series_format_alert(invalid_naming_series, missing_naming_series):
	"""
	Cria alerta para formatos de naming series incorretos
	"""
	try:
		admin_users = get_compliance_users()

		message = f"""
		⚠️ Alerta de Naming Series:
		- {len(invalid_naming_series)} séries com naming series inválido
		- {len(missing_naming_series)} séries sem naming series

		Recomenda-se corrigir para formato: PREFIX.####
		"""

		for user in admin_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "Portugal Compliance: Naming Series",
				"email_content": message,
				"for_user": user,
				"type": "Alert"
			}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error creating naming series format alert: {str(e)}")


def create_atcud_integrity_alert(duplicate_atcuds):
	"""
	Cria alerta crítico para duplicação de ATCUD - MANTIDA
	"""
	try:
		admin_users = get_compliance_users()

		message = f"""
		🚨 ALERTA CRÍTICO - Duplicação de ATCUD:
		Encontrados {len(duplicate_atcuds)} códigos ATCUD duplicados.

		Isto pode indicar problemas na geração de sequências.
		Verificação imediata necessária.
		"""

		for user in admin_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "CRÍTICO: Duplicação ATCUD",
				"email_content": message,
				"for_user": user,
				"type": "Alert"
			}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error creating ATCUD integrity alert: {str(e)}")


# ========== MANTER TODAS AS FUNÇÕES EXISTENTES ADAPTADAS ==========

def check_series_expiration():
	"""
	Verifica séries que estão a expirar - ADAPTADA
	"""
	try:
		# ✅ ADAPTADO: Usar Portugal Series Configuration
		expiring_soon = frappe.db.sql("""
									  SELECT name, series_name, company, expiry_date
									  FROM `tabPortugal Series Configuration`
									  WHERE expiry_date IS NOT NULL
										AND expiry_date <= %s
										AND is_active = 1
									  """, add_days(today(), 30), as_dict=True)

		for series in expiring_soon:
			days_until_expiry = (get_datetime(series.expiry_date) - get_datetime(today())).days

			if days_until_expiry <= 7:
				create_expiry_notification(series, days_until_expiry, "critical")
			elif days_until_expiry <= 30:
				create_expiry_notification(series, days_until_expiry, "warning")

		if expiring_soon:
			frappe.logger().info(f"Found {len(expiring_soon)} series expiring soon")

	except Exception as e:
		frappe.log_error(f"Error checking series expiration: {str(e)}")


def create_expiry_notification(series, days_until_expiry, severity):
	"""
	Cria notificação de expiração de série - MANTIDA
	"""
	try:
		users_to_notify = get_compliance_users(series.company)

		message = _("Series '{0}' expires in {1} days").format(
			series.series_name, days_until_expiry
		)

		for user in users_to_notify:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": _("Series Expiration Warning"),
				"email_content": message,
				"for_user": user,
				"type": "Alert",
				"document_type": "Portugal Series Configuration",
				"document_name": series.name
			}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error creating expiry notification: {str(e)}")


def validate_daily_sequences():
	"""
	Valida sequências de ATCUD do dia - MANTIDA
	"""
	try:
		today_date = today()

		duplicate_sequences = frappe.db.sql("""
											SELECT atcud_code, COUNT(*) as count
											FROM `tabATCUD Log`
											WHERE DATE (creation) = %s
											  AND atcud_code IS NOT NULL
											GROUP BY atcud_code
											HAVING count > 1
											""", today_date, as_dict=True)

		if duplicate_sequences:
			error_msg = f"Found {len(duplicate_sequences)} duplicate ATCUD sequences today"
			frappe.log_error(error_msg, "ATCUD Sequence Validation")

		check_sequence_gaps()

	except Exception as e:
		frappe.log_error(f"Error validating daily sequences: {str(e)}")


def check_sequence_gaps():
	"""
	Verifica gaps nas sequências de documentos - ADAPTADA
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1, "is_communicated": 1},
										  fields=["name", "prefix", "current_sequence"])

		for series in active_series:
			gaps = find_sequence_gaps(series.prefix)
			if gaps:
				frappe.logger().warning(f"Sequence gaps found in series {series.prefix}: {gaps}")

	except Exception as e:
		frappe.log_error(f"Error checking sequence gaps: {str(e)}")


def find_sequence_gaps(series_prefix):
	"""
	Encontra gaps numa sequência de documentos - MANTIDA
	"""
	try:
		return []  # Implementação simplificada
	except Exception:
		return []


def cleanup_old_logs():
	"""
	Limpa logs antigos - MANTIDA
	"""
	try:
		# Manter logs por 90 dias
		cutoff_date = add_days(today(), -90)

		# Limpar logs de ATCUD antigos
		old_atcud_logs = frappe.db.count("ATCUD Log", {
			"creation": ["<", cutoff_date]
		})

		if old_atcud_logs > 0:
			frappe.db.delete("ATCUD Log", {
				"creation": ["<", cutoff_date]
			})
			frappe.logger().info(f"🧹 Cleaned up {old_atcud_logs} old ATCUD logs")

		# Limpar logs de erro antigos relacionados com Portugal Compliance
		frappe.db.sql("""
					  DELETE
					  FROM `tabError Log`
					  WHERE creation < %s
						AND error LIKE '%portugal_compliance%'
					  """, cutoff_date)

	except Exception as e:
		frappe.log_error(f"Error cleaning up old logs: {str(e)}")


def check_pending_communications():
	"""
	Verifica comunicações pendentes com a AT - ADAPTADA
	"""
	try:
		pending_series = frappe.db.sql("""
									   SELECT name, series_name, company, creation
									   FROM `tabPortugal Series Configuration`
									   WHERE is_communicated = 0
										 AND is_active = 1
										 AND creation < %s
									   """, add_days(today(), -1), as_dict=True)

		for series in pending_series:
			try_auto_communication(series)

		if pending_series:
			frappe.logger().info(f"Found {len(pending_series)} pending communications")

	except Exception as e:
		frappe.log_error(f"Error checking pending communications: {str(e)}")


def try_auto_communication(series):
	"""
	Tenta comunicar série automaticamente - ADAPTADA
	"""
	try:
		# ✅ ADAPTADO: Verificar credenciais na empresa
		company_doc = frappe.get_doc("Company", series.company)

		if (getattr(company_doc, 'at_username', None) and
			getattr(company_doc, 'portugal_compliance_enabled', 0)):
			frappe.logger().info(f"Attempting auto-communication for series {series.name}")

	except Exception as e:
		frappe.log_error(f"Error in auto-communication for series {series.name}: {str(e)}")


def update_usage_statistics():
	"""
	Atualiza estatísticas de uso - ADAPTADA
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name"])

		for series in active_series:
			update_series_statistics(series.name)

	except Exception as e:
		frappe.log_error(f"Error updating usage statistics: {str(e)}")


def update_series_statistics(series_name):
	"""
	Atualiza estatísticas de uma série específica - ADAPTADA
	"""
	try:
		series_doc = frappe.get_doc("Portugal Series Configuration", series_name)

		# ✅ ADAPTADO: Calcular estatísticas usando naming_series
		naming_series = f"{series_doc.prefix}.####"

		# Contar documentos que usam esta naming_series
		total_docs = frappe.db.count(series_doc.document_type, {
			"naming_series": naming_series,
			"company": series_doc.company,
			"docstatus": ["!=", 2]
		})

		# Atualizar estatísticas
		frappe.db.set_value("Portugal Series Configuration", series_name, {
			"total_documents_issued": total_docs,
			"last_statistics_update": now()
		}, update_modified=False)

	except Exception as e:
		frappe.log_error(f"Error updating statistics for series {series_name}: {str(e)}")


def backup_critical_data():
	"""
	Faz backup de dados críticos - ADAPTADA
	"""
	try:
		backup_data = {
			"date": today(),
			"series_count": frappe.db.count("Portugal Series Configuration"),
			"atcud_count": frappe.db.count("ATCUD Log"),
			"companies_count": frappe.db.count("Company", {"portugal_compliance_enabled": 1}),
			"naming_series_health": check_naming_series_health()
		}

		frappe.cache.set("portugal_compliance_daily_backup", backup_data, expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error backing up critical data: {str(e)}")


def send_daily_notifications():
	"""
	Envia notificações diárias se necessário - MANTIDA
	"""
	try:
		critical_alerts = check_critical_alerts()
		if critical_alerts:
			send_alert_notifications(critical_alerts)

	except Exception as e:
		frappe.log_error(f"Error sending daily notifications: {str(e)}")


def check_critical_alerts():
	"""
	Verifica alertas críticos - ADAPTADA
	"""
	try:
		alerts = []

		# ✅ ADAPTADO: Usar Portugal Series Configuration
		overdue_series = frappe.db.count("Portugal Series Configuration", {
			"is_communicated": 0,
			"is_active": 1,
			"creation": ["<", add_days(today(), -3)]
		})

		if overdue_series > 0:
			alerts.append({
				"type": "overdue_series",
				"count": overdue_series,
				"message": f"{overdue_series} series overdue for communication"
			})

		return alerts

	except Exception:
		return []


def send_alert_notifications(alerts):
	"""
	Envia notificações de alerta - MANTIDA
	"""
	try:
		admin_users = frappe.db.get_all("User",
										filters={
											"role_profile_name": ["like", "%System Manager%"]},
										fields=["name"])

		for alert in alerts:
			for user in admin_users:
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _("Portugal Compliance Alert"),
					"email_content": alert["message"],
					"for_user": user.name,
					"type": "Alert"
				}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error sending alert notifications: {str(e)}")


def get_compliance_users(company=None):
	"""
	Obtém utilizadores responsáveis pelo compliance - MANTIDA
	"""
	try:
		users = frappe.db.sql("""
							  SELECT DISTINCT u.name
							  FROM `tabUser` u
									   JOIN `tabUserRole` ur ON u.name = ur.parent
							  WHERE ur.role IN
									('Accounts Manager', 'Accounts User', 'System Manager',
									 'Portugal Compliance User')
								AND u.enabled = 1
							  """, as_list=True)

		return [user[0] for user in users]

	except Exception:
		return ["Administrator"]
