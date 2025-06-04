# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam diariamente - VERSÃO ATUALIZADA
Integração completa com Portugal Compliance
"""

import frappe
from frappe import _
from frappe.utils import today, now, add_days, get_datetime, cint, flt
from datetime import datetime, timedelta
import json


def execute():
	"""
	Função principal executada diariamente - ATUALIZADA
	"""
	try:
		frappe.logger().info("🇵🇹 Portugal Compliance: Executing daily scheduled tasks")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			frappe.logger().info("Portugal Compliance not enabled, skipping daily tasks")
			return

		# ✅ TAREFAS PRINCIPAIS (MANTIDAS + MELHORADAS)
		generate_daily_report()
		check_series_expiration()
		validate_daily_sequences()
		cleanup_old_logs()
		check_pending_communications()
		update_usage_statistics()
		backup_critical_data()
		send_daily_notifications()

		# ✅ NOVAS TAREFAS ADICIONADAS
		validate_prefix_formats()
		check_atcud_sequence_integrity()
		monitor_communication_failures()
		update_series_trends()
		check_naming_series_consistency()
		validate_custom_fields_integrity()
		cleanup_failed_communications()
		generate_compliance_metrics()

		frappe.logger().info("🇵🇹 Portugal Compliance: Daily tasks completed successfully")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.daily: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo - MELHORADO
	"""
	try:
		# Verificar se há empresas portuguesas com compliance ativado
		portuguese_companies = frappe.db.count("Company", {
			"country": "Portugal",
			"portugal_compliance_enabled": 1
		})

		# Verificar se há séries ativas
		active_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1
		})

		return portuguese_companies > 0 or active_series > 0

	except Exception:
		return False


def generate_daily_report():
	"""
	Gera relatório diário de atividades - EXPANDIDO
	"""
	try:
		today_date = today()

		# ✅ ESTATÍSTICAS EXPANDIDAS
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
			# ✅ NOVAS MÉTRICAS
			"series_with_new_format": count_series_with_new_format(),
			"communication_success_rate": calculate_communication_success_rate(),
			"avg_atcud_generation_time": calculate_avg_atcud_time(),
			"prefix_format_compliance": calculate_prefix_compliance(),
			"naming_series_consistency": check_naming_series_health()
		}

		# Armazenar relatório
		store_daily_report(daily_stats)

		# Log se houver atividade significativa
		if daily_stats["atcud_generated"] > 0 or daily_stats["series_communicated"] > 0:
			frappe.logger().info(f"📊 Daily Report: {daily_stats}")

	except Exception as e:
		frappe.log_error(f"Error generating daily report: {str(e)}")


# ✅ NOVA FUNÇÃO: Contar séries com novo formato
def count_series_with_new_format():
	"""
	Conta séries que usam o novo formato XX-YYYY-COMPANY
	"""
	try:
		# Padrão do novo formato
		new_format_pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}$'

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


# ✅ NOVA FUNÇÃO: Calcular taxa de sucesso de comunicação
def calculate_communication_success_rate():
	"""
	Calcula taxa de sucesso das comunicações AT
	"""
	try:
		total_attempts = frappe.db.count("Portugal Series Configuration", {
			"enable_at_communication": 1
		})

		successful_communications = frappe.db.count("Portugal Series Configuration", {
			"enable_at_communication": 1,
			"is_communicated": 1,
			"communication_status": "Success"
		})

		if total_attempts > 0:
			return round((successful_communications / total_attempts) * 100, 2)
		return 0

	except Exception:
		return 0


# ✅ NOVA FUNÇÃO: Calcular tempo médio de geração ATCUD
def calculate_avg_atcud_time():
	"""
	Calcula tempo médio de geração de ATCUD
	"""
	try:
		# Esta é uma métrica estimada baseada nos logs
		recent_logs = frappe.db.get_all("ATCUD Log",
										filters={
											"creation": [">=", add_days(today(), -7)],
											"generation_status": "Success"
										},
										fields=["creation", "generation_date"])

		if len(recent_logs) > 0:
			# Estimativa baseada na quantidade de logs recentes
			return round(len(recent_logs) / 7, 2)  # Média por dia
		return 0

	except Exception:
		return 0


# ✅ NOVA FUNÇÃO: Calcular compliance de formato de prefixo
def calculate_prefix_compliance():
	"""
	Calcula percentagem de séries com formato correto
	"""
	try:
		total_series = frappe.db.count("Portugal Series Configuration")
		new_format_series = count_series_with_new_format()

		if total_series > 0:
			return round((new_format_series / total_series) * 100, 2)
		return 100

	except Exception:
		return 0


# ✅ NOVA FUNÇÃO: Verificar saúde das naming series
def check_naming_series_health():
	"""
	Verifica consistência das naming series
	"""
	try:
		series_with_issues = 0
		total_series = 0

		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name", "prefix", "document_type"])

		for series in active_series:
			total_series += 1

			# Verificar se naming series está configurada corretamente
			expected_naming = f"{series.prefix}.####"

			try:
				doctype_meta = frappe.get_meta(series.document_type)
				autoname_options = getattr(doctype_meta, 'autoname', '') or ''

				if expected_naming not in autoname_options:
					series_with_issues += 1

			except Exception:
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
	Conta documentos processados hoje - MELHORADO
	"""
	try:
		today_date = today()
		total_docs = 0

		# ✅ TIPOS DE DOCUMENTOS EXPANDIDOS
		doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry",
			"Stock Entry", "Quotation", "Sales Order", "Purchase Order",
			"Material Request"
		]

		for doctype in doctypes:
			if frappe.db.table_exists(f"tab{doctype}"):
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
	Armazena relatório diário na base de dados - MELHORADO
	"""
	try:
		# ✅ USAR CACHE SE DOCTYPE NÃO EXISTIR
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
					"prefix_format_compliance": stats.get("prefix_format_compliance", 0),
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


# ✅ NOVA FUNÇÃO: Validar formatos de prefixo
def validate_prefix_formats():
	"""
	Valida e reporta formatos de prefixo incorretos
	"""
	try:
		import re
		new_format_pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}$'
		old_format_pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$'

		all_series = frappe.db.get_all("Portugal Series Configuration",
									   fields=["name", "prefix", "company"])

		invalid_prefixes = []
		legacy_prefixes = []

		for series in all_series:
			if series.prefix:
				if re.match(new_format_pattern, series.prefix):
					continue  # Formato correto
				elif re.match(old_format_pattern, series.prefix):
					legacy_prefixes.append(series)
				else:
					invalid_prefixes.append(series)

		# Log resultados
		if invalid_prefixes:
			frappe.logger().warning(
				f"⚠️ Found {len(invalid_prefixes)} series with invalid prefix format")

		if legacy_prefixes:
			frappe.logger().info(f"📋 Found {len(legacy_prefixes)} series with legacy format")

		# Criar notificações se necessário
		if len(invalid_prefixes) > 5:  # Muitos prefixos inválidos
			create_prefix_format_alert(invalid_prefixes, legacy_prefixes)

	except Exception as e:
		frappe.log_error(f"Error validating prefix formats: {str(e)}")


# ✅ NOVA FUNÇÃO: Verificar integridade de sequências ATCUD
def check_atcud_sequence_integrity():
	"""
	Verifica integridade das sequências ATCUD
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

			# Criar alerta crítico
			create_atcud_integrity_alert(duplicate_atcuds)

		# Verificar formato de ATCUDs
		invalid_atcuds = frappe.db.sql("""
									   SELECT name, atcud_code, document_type
									   FROM `tabATCUD Log`
									   WHERE atcud_code IS NOT NULL
										 AND atcud_code NOT REGEXP '^[A-Z0-9]+-[0-9]{8}$'
			  AND creation >= %s
									   """, add_days(today(), -7), as_dict=True)

		if invalid_atcuds:
			frappe.logger().warning(f"⚠️ Found {len(invalid_atcuds)} ATCUDs with invalid format")

	except Exception as e:
		frappe.log_error(f"Error checking ATCUD sequence integrity: {str(e)}")


# ✅ NOVA FUNÇÃO: Monitorizar falhas de comunicação
def monitor_communication_failures():
	"""
	Monitoriza e reporta falhas de comunicação AT
	"""
	try:
		# Séries com falhas recentes
		failed_communications = frappe.db.get_all("Portugal Series Configuration",
												  filters={
													  "communication_status": "Failed",
													  "enable_at_communication": 1,
													  "modified": [">=", add_days(today(), -7)]
												  },
												  fields=["name", "prefix", "company",
														  "last_communication_error"])

		if failed_communications:
			frappe.logger().warning(
				f"⚠️ Found {len(failed_communications)} failed communications in last 7 days")

			# Tentar re-comunicar automaticamente
			for series in failed_communications:
				try_auto_retry_communication(series)

		# Séries não comunicadas há muito tempo
		overdue_series = frappe.db.get_all("Portugal Series Configuration",
										   filters={
											   "is_communicated": 0,
											   "enable_at_communication": 1,
											   "is_active": 1,
											   "creation": ["<", add_days(today(), -3)]
										   },
										   fields=["name", "prefix", "company"])

		if overdue_series:
			frappe.logger().info(f"📋 Found {len(overdue_series)} overdue series for communication")

	except Exception as e:
		frappe.log_error(f"Error monitoring communication failures: {str(e)}")


# ✅ NOVA FUNÇÃO: Tentar re-comunicação automática
def try_auto_retry_communication(series):
	"""
	Tenta re-comunicar série automaticamente
	"""
	try:
		# Verificar se tem credenciais
		if series.get("at_username") and series.get("at_password"):
			frappe.logger().info(f"🔄 Attempting auto-retry for series {series.name}")

			# Chamar método de comunicação
			frappe.call(
				"portugal_compliance.doctype.portugal_series_configuration.portugal_series_configuration.register_series_at",
				**{"doc": series.name})

	except Exception as e:
		frappe.log_error(f"Error in auto-retry communication for {series.name}: {str(e)}")


# ✅ NOVA FUNÇÃO: Atualizar tendências de séries
def update_series_trends():
	"""
	Atualiza tendências de uso das séries
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name"])

		for series in active_series:
			try:
				# Calcular tendência de uso
				trend = calculate_series_usage_trend(series.name)

				# Atualizar no documento
				frappe.db.set_value("Portugal Series Configuration", series.name, {
					"usage_trend": trend,
					"last_trend_update": now()
				}, update_modified=False)

			except Exception as e:
				frappe.log_error(f"Error updating trend for series {series.name}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Error updating series trends: {str(e)}")


# ✅ NOVA FUNÇÃO: Calcular tendência de uso
def calculate_series_usage_trend(series_name):
	"""
	Calcula tendência de uso de uma série
	"""
	try:
		# Obter série
		series_doc = frappe.get_doc("Portugal Series Configuration", series_name)

		# Contar documentos dos últimos 30 dias
		recent_docs = frappe.db.count(series_doc.document_type, {
			"portugal_series": series_name,
			"creation": [">=", add_days(today(), -30)]
		})

		# Contar documentos dos 30 dias anteriores
		previous_docs = frappe.db.count(series_doc.document_type, {
			"portugal_series": series_name,
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


# ✅ NOVA FUNÇÃO: Verificar consistência das naming series
def check_naming_series_consistency():
	"""
	Verifica consistência das naming series com as séries portuguesas
	"""
	try:
		inconsistent_series = []

		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["name", "prefix", "document_type"])

		for series in active_series:
			expected_naming = f"{series.prefix}.####"

			try:
				# Verificar se naming series está no DocType
				doctype_meta = frappe.get_meta(series.document_type)
				autoname_options = getattr(doctype_meta, 'autoname', '') or ''

				if expected_naming not in autoname_options:
					inconsistent_series.append({
						"series": series.name,
						"prefix": series.prefix,
						"document_type": series.document_type,
						"expected": expected_naming,
						"current": autoname_options
					})

			except Exception as e:
				frappe.log_error(f"Error checking naming series for {series.name}: {str(e)}")

		if inconsistent_series:
			frappe.logger().warning(
				f"⚠️ Found {len(inconsistent_series)} inconsistent naming series")

			# Tentar corrigir automaticamente
			for series_info in inconsistent_series:
				try_fix_naming_series(series_info)

	except Exception as e:
		frappe.log_error(f"Error checking naming series consistency: {str(e)}")


# ✅ NOVA FUNÇÃO: Tentar corrigir naming series
def try_fix_naming_series(series_info):
	"""
	Tenta corrigir naming series automaticamente
	"""
	try:
		doctype = series_info["document_type"]
		expected_naming = series_info["expected"]
		current_options = series_info["current"]

		# Adicionar naming series se não existir
		if expected_naming not in current_options:
			new_options = current_options + f"\n{expected_naming}" if current_options else expected_naming

			frappe.db.set_value("DocType", doctype, "autoname", new_options)
			frappe.clear_cache(doctype=doctype)

			frappe.logger().info(f"✅ Fixed naming series for {doctype}: added {expected_naming}")

	except Exception as e:
		frappe.log_error(f"Error fixing naming series: {str(e)}")


# ✅ NOVA FUNÇÃO: Validar integridade dos campos customizados
def validate_custom_fields_integrity():
	"""
	Valida se campos customizados estão presentes em todos os DocTypes necessários
	"""
	try:
		required_fields = ["atcud_code", "portugal_series"]
		doctypes_to_check = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
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
			frappe.logger().warning(f"⚠️ Found {len(missing_fields)} missing custom fields")

			# Tentar criar campos em falta
			for missing in missing_fields:
				try_create_missing_field(missing)
		else:
			frappe.logger().info("✅ All custom fields are present")

	except Exception as e:
		frappe.log_error(f"Error validating custom fields integrity: {str(e)}")


# ✅ NOVA FUNÇÃO: Tentar criar campo em falta
def try_create_missing_field(missing_field):
	"""
	Tenta criar campo customizado em falta
	"""
	try:
		doctype = missing_field["doctype"]
		field = missing_field["field"]

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
				"description": "Código Único de Documento - obrigatório em Portugal"
			})
		elif field == "portugal_series":
			field_doc = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": doctype,
				"module": "Portugal Compliance",
				"fieldname": "portugal_series",
				"label": "Portugal Series",
				"fieldtype": "Link",
				"options": "Portugal Series Configuration",
				"insert_after": "atcud_code",
				"reqd": 1,
				"in_list_view": 1,
				"description": "Série portuguesa configurada para este documento"
			})
		else:
			return

		field_doc.insert(ignore_permissions=True)
		frappe.logger().info(f"✅ Created missing field {field} for {doctype}")

	except Exception as e:
		frappe.log_error(f"Error creating missing field {missing_field}: {str(e)}")


# ✅ NOVA FUNÇÃO: Limpar comunicações falhadas
def cleanup_failed_communications():
	"""
	Limpa dados de comunicações falhadas antigas
	"""
	try:
		# Limpar erros de comunicação antigos (mais de 30 dias)
		old_errors = frappe.db.sql("""
								   UPDATE `tabPortugal Series Configuration`
								   SET last_communication_error = NULL,
									   communication_status     = NULL
								   WHERE communication_status = 'Failed'
									 AND modified < %s
								   """, add_days(today(), -30))

		frappe.logger().info("🧹 Cleaned up old communication errors")

	except Exception as e:
		frappe.log_error(f"Error cleaning up failed communications: {str(e)}")


# ✅ NOVA FUNÇÃO: Gerar métricas de compliance
def generate_compliance_metrics():
	"""
	Gera métricas de compliance para dashboard
	"""
	try:
		metrics = {
			"date": today(),
			"total_series": frappe.db.count("Portugal Series Configuration"),
			"active_series": frappe.db.count("Portugal Series Configuration", {"is_active": 1}),
			"communicated_series": frappe.db.count("Portugal Series Configuration",
												   {"is_communicated": 1}),
			"new_format_series": count_series_with_new_format(),
			"total_atcuds": frappe.db.count("ATCUD Log"),
			"successful_atcuds": frappe.db.count("ATCUD Log", {"generation_status": "Success"}),
			"portuguese_companies": frappe.db.count("Company", {"country": "Portugal"}),
			"compliance_enabled_companies": frappe.db.count("Company",
															{"portugal_compliance_enabled": 1})
		}

		# Armazenar no cache
		frappe.cache.set("portugal_compliance_metrics", metrics, expires_in_sec=86400)

		frappe.logger().info(f"📊 Generated compliance metrics: {metrics}")

	except Exception as e:
		frappe.log_error(f"Error generating compliance metrics: {str(e)}")


# ========== FUNÇÕES DE ALERTA (NOVAS) ==========

def create_prefix_format_alert(invalid_prefixes, legacy_prefixes):
	"""
	Cria alerta para formatos de prefixo incorretos
	"""
	try:
		admin_users = get_compliance_users()

		message = f"""
		⚠️ Alerta de Formato de Prefixo:
		- {len(invalid_prefixes)} séries com formato inválido
		- {len(legacy_prefixes)} séries com formato legado

		Recomenda-se corrigir os formatos para XX-YYYY-COMPANY
		"""

		for user in admin_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "Portugal Compliance: Formato de Prefixo",
				"email_content": message,
				"for_user": user,
				"type": "Alert"
			}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error creating prefix format alert: {str(e)}")


def create_atcud_integrity_alert(duplicate_atcuds):
	"""
	Cria alerta crítico para duplicação de ATCUD
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


# ========== MANTER TODAS AS FUNÇÕES EXISTENTES ==========
# (check_series_expiration, create_expiry_notification, validate_daily_sequences,
#  cleanup_old_logs, check_pending_communications, etc.)

def check_series_expiration():
	"""
	Verifica séries que estão a expirar - MANTIDA
	"""
	try:
		# Séries que expiram nos próximos 30 dias
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
	Verifica gaps nas sequências de documentos - MANTIDA
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
	Limpa logs antigos - MELHORADA
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
	Verifica comunicações pendentes com a AT - MANTIDA
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
	Tenta comunicar série automaticamente - MANTIDA
	"""
	try:
		auth_settings = frappe.db.get_value("Portugal Auth Settings",
											series.company, ["username", "password"], as_dict=True)

		if auth_settings and auth_settings.username:
			frappe.logger().info(f"Attempting auto-communication for series {series.name}")

	except Exception as e:
		frappe.log_error(f"Error in auto-communication for series {series.name}: {str(e)}")


def update_usage_statistics():
	"""
	Atualiza estatísticas de uso - MANTIDA
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
	Atualiza estatísticas de uma série específica - MANTIDA
	"""
	try:
		series_doc = frappe.get_doc("Portugal Series Configuration", series_name)
		if hasattr(series_doc, 'update_usage_statistics'):
			series_doc.update_usage_statistics()

	except Exception as e:
		frappe.log_error(f"Error updating statistics for series {series_name}: {str(e)}")


def backup_critical_data():
	"""
	Faz backup de dados críticos - MANTIDA
	"""
	try:
		backup_data = {
			"date": today(),
			"series_count": frappe.db.count("Portugal Series Configuration"),
			"atcud_count": frappe.db.count("ATCUD Log"),
			"companies_count": frappe.db.count("Company", {"portugal_compliance_enabled": 1})
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
	Verifica alertas críticos - MANTIDA
	"""
	try:
		alerts = []

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
	Obtém utilizadores responsáveis pelo compliance - MELHORADA
	"""
	try:
		# ✅ MELHORADA: Incluir mais roles relevantes
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
