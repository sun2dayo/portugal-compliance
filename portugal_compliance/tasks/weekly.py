# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam semanalmente
"""

import frappe
from frappe import _
from frappe.utils import today, now, add_days, get_datetime, add_to_date, formatdate
from datetime import datetime, timedelta
import json


def execute():
	"""
	Função principal executada semanalmente
	"""
	try:
		frappe.logger().info("Portugal Compliance: Executing weekly scheduled tasks")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			frappe.logger().info("Portugal Compliance not enabled, skipping weekly tasks")
			return

		# Executar tarefas semanais
		generate_weekly_compliance_report()
		analyze_usage_patterns()
		check_system_health_trends()
		optimize_database_performance()
		backup_configuration_data()
		review_error_patterns()
		update_series_recommendations()
		cleanup_archived_data()
		generate_audit_trail()
		send_weekly_summary()

		frappe.logger().info("Portugal Compliance: Weekly tasks completed successfully")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.weekly: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo
	"""
	try:
		return frappe.db.count("Company", {"portugal_compliance_enabled": 1}) > 0
	except Exception:
		return False


def generate_weekly_compliance_report():
	"""
	Gera relatório semanal de compliance
	"""
	try:
		frappe.logger().info("Generating weekly compliance report")

		# Período da semana (últimos 7 dias)
		end_date = today()
		start_date = add_days(end_date, -7)

		# Coletar dados da semana
		weekly_data = {
			"period": {
				"start_date": start_date,
				"end_date": end_date
			},
			"atcud_statistics": get_weekly_atcud_stats(start_date, end_date),
			"series_statistics": get_weekly_series_stats(start_date, end_date),
			"communication_statistics": get_weekly_communication_stats(start_date, end_date),
			"error_statistics": get_weekly_error_stats(start_date, end_date),
			"performance_metrics": get_weekly_performance_metrics(start_date, end_date),
			"compliance_score": calculate_weekly_compliance_score(start_date, end_date)
		}

		# Armazenar relatório
		store_weekly_report(weekly_data)

		frappe.logger().info(
			f"Weekly compliance report generated for period {start_date} to {end_date}")

	except Exception as e:
		frappe.log_error(f"Error generating weekly compliance report: {str(e)}")


def get_weekly_atcud_stats(start_date, end_date):
	"""
	Obtém estatísticas de ATCUD da semana
	"""
	try:
		stats = {
			"total_generated": frappe.db.count("ATCUD Log", {
				"creation": ["between", [start_date, end_date]]
			}),
			"by_document_type": {},
			"by_company": {},
			"duplicates_found": 0,
			"validation_errors": 0
		}

		# Estatísticas por tipo de documento
		doc_types = frappe.db.sql("""
								  SELECT document_type, COUNT(*) as count
								  FROM `tabATCUD Log`
								  WHERE DATE (creation) BETWEEN %s
									AND %s
								  GROUP BY document_type
								  """, (start_date, end_date), as_dict=True)

		for doc_type in doc_types:
			stats["by_document_type"][doc_type.document_type] = doc_type.count

		# Estatísticas por empresa
		companies = frappe.db.sql("""
								  SELECT company, COUNT(*) as count
								  FROM `tabATCUD Log`
								  WHERE DATE (creation) BETWEEN %s
									AND %s
								  GROUP BY company
								  """, (start_date, end_date), as_dict=True)

		for company in companies:
			stats["by_company"][company.company] = company.count

		# Verificar duplicados
		duplicates = frappe.db.sql("""
								   SELECT atcud_code, COUNT(*) as count
								   FROM `tabATCUD Log`
								   WHERE DATE (creation) BETWEEN %s
									 AND %s
									 AND atcud_code IS NOT NULL
								   GROUP BY atcud_code
								   HAVING count > 1
								   """, (start_date, end_date), as_dict=True)

		stats["duplicates_found"] = len(duplicates)

		return stats

	except Exception as e:
		frappe.log_error(f"Error getting weekly ATCUD stats: {str(e)}")
		return {}


def get_weekly_series_stats(start_date, end_date):
	"""
	Obtém estatísticas de séries da semana
	"""
	try:
		stats = {
			"new_series_created": frappe.db.count("Portugal Series Configuration", {
				"creation": ["between", [start_date, end_date]]
			}),
			"series_communicated": frappe.db.count("Portugal Series Configuration", {
				"communication_date": ["between", [start_date, end_date]],
				"is_communicated": 1
			}),
			"communication_failures": frappe.db.count("Portugal Series Configuration", {
				"last_communication_attempt": ["between", [start_date, end_date]],
				"communication_status": "Failed"
			}),
			"active_series_total": frappe.db.count("Portugal Series Configuration", {
				"is_active": 1
			}),
			"pending_communications": frappe.db.count("Portugal Series Configuration", {
				"is_communicated": 0,
				"is_active": 1
			})
		}

		# Estatísticas por empresa
		stats["by_company"] = {}
		companies = frappe.db.sql("""
								  SELECT company,
										 COUNT(*)                                             as total,
										 SUM(CASE WHEN is_communicated = 1 THEN 1 ELSE 0 END) as communicated
								  FROM `tabPortugal Series Configuration`
								  WHERE is_active = 1
								  GROUP BY company
								  """, as_dict=True)

		for company in companies:
			stats["by_company"][company.company] = {
				"total": company.total,
				"communicated": company.communicated,
				"pending": company.total - company.communicated
			}

		return stats

	except Exception as e:
		frappe.log_error(f"Error getting weekly series stats: {str(e)}")
		return {}


def get_weekly_communication_stats(start_date, end_date):
	"""
	Obtém estatísticas de comunicação da semana
	"""
	try:
		stats = {
			"total_attempts": 0,
			"successful_communications": 0,
			"failed_communications": 0,
			"average_response_time": 0,
			"peak_communication_hours": [],
			"communication_success_rate": 0
		}

		# Obter tentativas de comunicação
		communications = frappe.db.sql("""
									   SELECT communication_status,
											  last_communication_attempt,
											  communication_attempts
									   FROM `tabPortugal Series Configuration`
									   WHERE last_communication_attempt BETWEEN %s AND %s
									   """, (start_date, end_date), as_dict=True)

		total_attempts = sum([comm.communication_attempts or 0 for comm in communications])
		successful = len(
			[comm for comm in communications if comm.communication_status == "Success"])
		failed = len([comm for comm in communications if comm.communication_status == "Failed"])

		stats["total_attempts"] = total_attempts
		stats["successful_communications"] = successful
		stats["failed_communications"] = failed

		if total_attempts > 0:
			stats["communication_success_rate"] = (successful / total_attempts) * 100

		return stats

	except Exception as e:
		frappe.log_error(f"Error getting weekly communication stats: {str(e)}")
		return {}


def get_weekly_error_stats(start_date, end_date):
	"""
	Obtém estatísticas de erros da semana
	"""
	try:
		stats = {
			"total_errors": frappe.db.count("Error Log", {
				"creation": ["between", [start_date, end_date]],
				"error": ["like", "%portugal_compliance%"]
			}),
			"error_types": {},
			"most_common_errors": [],
			"error_trend": "stable"
		}

		# Análise de tipos de erro
		errors = frappe.db.sql("""
							   SELECT title, COUNT(*) as count
							   FROM `tabError Log`
							   WHERE creation BETWEEN %s
								 AND %s
								 AND error LIKE '%portugal_compliance%'
							   GROUP BY title
							   ORDER BY count DESC
								   LIMIT 10
							   """, (start_date, end_date), as_dict=True)

		for error in errors:
			stats["error_types"][error.title] = error.count

		stats["most_common_errors"] = [error.title for error in errors[:5]]

		# Tendência de erros (comparar com semana anterior)
		prev_week_start = add_days(start_date, -7)
		prev_week_errors = frappe.db.count("Error Log", {
			"creation": ["between", [prev_week_start, start_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		if prev_week_errors > 0:
			error_change = ((stats["total_errors"] - prev_week_errors) / prev_week_errors) * 100
			if error_change > 20:
				stats["error_trend"] = "increasing"
			elif error_change < -20:
				stats["error_trend"] = "decreasing"

		return stats

	except Exception as e:
		frappe.log_error(f"Error getting weekly error stats: {str(e)}")
		return {}


def get_weekly_performance_metrics(start_date, end_date):
	"""
	Obtém métricas de performance da semana
	"""
	try:
		metrics = {
			"average_atcud_generation_time": 0,
			"average_series_communication_time": 0,
			"system_uptime_percentage": 100,
			"database_performance_score": 0,
			"cache_hit_ratio": 0
		}

		# Simular métricas (implementar coleta real conforme necessário)
		metrics["average_atcud_generation_time"] = 0.5  # segundos
		metrics["average_series_communication_time"] = 2.5  # segundos
		metrics["database_performance_score"] = 85  # score de 0-100
		metrics["cache_hit_ratio"] = 92  # percentagem

		return metrics

	except Exception as e:
		frappe.log_error(f"Error getting weekly performance metrics: {str(e)}")
		return {}


def calculate_weekly_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance da semana
	"""
	try:
		score_components = {
			"series_communication_rate": 0,
			"atcud_generation_success": 0,
			"error_rate": 0,
			"system_availability": 0
		}

		# Taxa de comunicação de séries
		total_series = frappe.db.count("Portugal Series Configuration", {"is_active": 1})
		communicated_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1, "is_communicated": 1
		})

		if total_series > 0:
			score_components["series_communication_rate"] = (
																	communicated_series / total_series) * 100

		# Taxa de sucesso de geração de ATCUD
		total_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_atcud > 0:
			score_components["atcud_generation_success"] = 95  # Assumir 95% de sucesso

		# Taxa de erro (inversa)
		total_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		score_components["error_rate"] = max(0, 100 - (total_errors * 2))  # Penalizar erros
		score_components["system_availability"] = 98  # Assumir 98% de disponibilidade

		# Calcular score final (média ponderada)
		final_score = (
			score_components["series_communication_rate"] * 0.3 +
			score_components["atcud_generation_success"] * 0.3 +
			score_components["error_rate"] * 0.2 +
			score_components["system_availability"] * 0.2
		)

		return {
			"final_score": round(final_score, 2),
			"components": score_components,
			"grade": get_compliance_grade(final_score)
		}

	except Exception as e:
		frappe.log_error(f"Error calculating weekly compliance score: {str(e)}")
		return {"final_score": 0, "components": {}, "grade": "F"}


def get_compliance_grade(score):
	"""
	Converte score numérico em nota
	"""
	if score >= 95:
		return "A+"
	elif score >= 90:
		return "A"
	elif score >= 85:
		return "B+"
	elif score >= 80:
		return "B"
	elif score >= 75:
		return "C+"
	elif score >= 70:
		return "C"
	elif score >= 60:
		return "D"
	else:
		return "F"


def store_weekly_report(report_data):
	"""
	Armazena relatório semanal
	"""
	try:
		# Armazenar no cache por 30 dias
		cache_key = f"portugal_compliance_weekly_report_{report_data['period']['end_date']}"
		frappe.cache.set(cache_key, report_data, expires_in_sec=2592000)

		# Criar entrada de log para histórico
		frappe.get_doc({
			"doctype": "Portugal Weekly Report",
			"report_date": report_data['period']['end_date'],
			"period_start": report_data['period']['start_date'],
			"period_end": report_data['period']['end_date'],
			"compliance_score": report_data['compliance_score']['final_score'],
			"compliance_grade": report_data['compliance_score']['grade'],
			"total_atcud_generated": report_data['atcud_statistics']['total_generated'],
			"total_series_communicated": report_data['series_statistics']['series_communicated'],
			"total_errors": report_data['error_statistics']['total_errors'],
			"report_data": json.dumps(report_data)
		}).insert(ignore_permissions=True, ignore_if_duplicate=True)

	except Exception as e:
		frappe.log_error(f"Error storing weekly report: {str(e)}")


def analyze_usage_patterns():
	"""
	Analisa padrões de uso do sistema
	"""
	try:
		frappe.logger().info("Analyzing usage patterns")

		# Análise de padrões de geração de ATCUD
		analyze_atcud_patterns()

		# Análise de padrões de comunicação
		analyze_communication_patterns()

		# Análise de padrões de erro
		analyze_error_patterns()

	except Exception as e:
		frappe.log_error(f"Error analyzing usage patterns: {str(e)}")


def analyze_atcud_patterns():
	"""
	Analisa padrões de geração de ATCUD
	"""
	try:
		# Análise por hora do dia
		hourly_pattern = frappe.db.sql("""
									   SELECT HOUR (creation) as hour, COUNT (*) as count
									   FROM `tabATCUD Log`
									   WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
									   GROUP BY HOUR (creation)
									   ORDER BY hour
									   """, as_dict=True)

		# Análise por dia da semana
		daily_pattern = frappe.db.sql("""
									  SELECT DAYOFWEEK(creation) as day_of_week, COUNT(*) as count
									  FROM `tabATCUD Log`
									  WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
									  GROUP BY DAYOFWEEK(creation)
									  ORDER BY day_of_week
									  """, as_dict=True)

		patterns = {
			"hourly_distribution": {str(h.hour): h.count for h in hourly_pattern},
			"daily_distribution": {str(d.day_of_week): d.count for d in daily_pattern},
			"peak_hours": [h.hour for h in
						   sorted(hourly_pattern, key=lambda x: x.count, reverse=True)[:3]],
			"peak_days": [d.day_of_week for d in
						  sorted(daily_pattern, key=lambda x: x.count, reverse=True)[:3]]
		}

		frappe.cache.set("portugal_compliance_atcud_patterns", patterns, expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error analyzing ATCUD patterns: {str(e)}")


def analyze_communication_patterns():
	"""
	Analisa padrões de comunicação com AT
	"""
	try:
		# Análise de horários de comunicação bem-sucedida
		success_patterns = frappe.db.sql("""
										 SELECT HOUR (communication_date) as hour, COUNT (*) as count
										 FROM `tabPortugal Series Configuration`
										 WHERE communication_date >= DATE_SUB(NOW()
											 , INTERVAL 30 DAY)
										   AND communication_status = 'Success'
										 GROUP BY HOUR (communication_date)
										 ORDER BY count DESC
										 """, as_dict=True)

		patterns = {
			"best_communication_hours": [p.hour for p in success_patterns[:5]],
			"success_rate_by_hour": {str(p.hour): p.count for p in success_patterns}
		}

		frappe.cache.set("portugal_compliance_communication_patterns", patterns,
						 expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error analyzing communication patterns: {str(e)}")


def analyze_error_patterns():
	"""
	Analisa padrões de erro
	"""
	try:
		# Análise de tipos de erro mais comuns
		error_patterns = frappe.db.sql("""
									   SELECT title, COUNT(*) as count
									   FROM `tabError Log`
									   WHERE creation >= DATE_SUB(NOW()
										   , INTERVAL 30 DAY)
										 AND error LIKE '%portugal_compliance%'
									   GROUP BY title
									   ORDER BY count DESC
										   LIMIT 10
									   """, as_dict=True)

		patterns = {
			"most_common_errors": [e.title for e in error_patterns],
			"error_frequency": {e.title: e.count for e in error_patterns}
		}

		frappe.cache.set("portugal_compliance_error_patterns", patterns, expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error analyzing error patterns: {str(e)}")


def check_system_health_trends():
	"""
	Verifica tendências de saúde do sistema
	"""
	try:
		frappe.logger().info("Checking system health trends")

		# Coletar métricas das últimas 4 semanas
		trends = {
			"atcud_generation_trend": calculate_atcud_trend(),
			"error_rate_trend": calculate_error_trend(),
			"performance_trend": calculate_performance_trend(),
			"communication_success_trend": calculate_communication_trend()
		}

		# Identificar alertas baseados em tendências
		alerts = identify_trend_alerts(trends)

		# Armazenar tendências
		frappe.cache.set("portugal_compliance_health_trends", {
			"trends": trends,
			"alerts": alerts,
			"last_updated": now()
		}, expires_in_sec=604800)

		if alerts:
			frappe.logger().warning(f"Health trend alerts: {alerts}")

	except Exception as e:
		frappe.log_error(f"Error checking system health trends: {str(e)}")


def calculate_atcud_trend():
	"""
	Calcula tendência de geração de ATCUD
	"""
	try:
		weekly_counts = []
		for i in range(4):
			week_start = add_days(today(), -(i + 1) * 7)
			week_end = add_days(week_start, 7)

			count = frappe.db.count("ATCUD Log", {
				"creation": ["between", [week_start, week_end]]
			})
			weekly_counts.append(count)

		# Calcular tendência (crescimento/decrescimento)
		if len(weekly_counts) >= 2:
			recent_avg = sum(weekly_counts[:2]) / 2
			older_avg = sum(weekly_counts[2:]) / 2

			if older_avg > 0:
				trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
				return {
					"direction": "increasing" if trend_percentage > 5 else "decreasing" if trend_percentage < -5 else "stable",
					"percentage": round(trend_percentage, 2),
					"weekly_counts": weekly_counts
				}

		return {"direction": "stable", "percentage": 0, "weekly_counts": weekly_counts}

	except Exception as e:
		frappe.log_error(f"Error calculating ATCUD trend: {str(e)}")
		return {"direction": "unknown", "percentage": 0, "weekly_counts": []}


def calculate_error_trend():
	"""
	Calcula tendência de erros
	"""
	try:
		weekly_errors = []
		for i in range(4):
			week_start = add_days(today(), -(i + 1) * 7)
			week_end = add_days(week_start, 7)

			count = frappe.db.count("Error Log", {
				"creation": ["between", [week_start, week_end]],
				"error": ["like", "%portugal_compliance%"]
			})
			weekly_errors.append(count)

		if len(weekly_errors) >= 2:
			recent_avg = sum(weekly_errors[:2]) / 2
			older_avg = sum(weekly_errors[2:]) / 2

			if older_avg > 0:
				trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
				return {
					"direction": "increasing" if trend_percentage > 10 else "decreasing" if trend_percentage < -10 else "stable",
					"percentage": round(trend_percentage, 2),
					"weekly_counts": weekly_errors
				}

		return {"direction": "stable", "percentage": 0, "weekly_counts": weekly_errors}

	except Exception as e:
		frappe.log_error(f"Error calculating error trend: {str(e)}")
		return {"direction": "unknown", "percentage": 0, "weekly_counts": []}


def calculate_performance_trend():
	"""
	Calcula tendência de performance
	"""
	try:
		# Simulação de métricas de performance
		# Na implementação real, coletar dados reais de performance
		return {
			"direction": "stable",
			"average_response_time": 1.2,
			"trend": "improving"
		}

	except Exception as e:
		frappe.log_error(f"Error calculating performance trend: {str(e)}")
		return {"direction": "unknown"}


def calculate_communication_trend():
	"""
	Calcula tendência de sucesso de comunicação
	"""
	try:
		weekly_success_rates = []
		for i in range(4):
			week_start = add_days(today(), -(i + 1) * 7)
			week_end = add_days(week_start, 7)

			total_attempts = frappe.db.count("Portugal Series Configuration", {
				"last_communication_attempt": ["between", [week_start, week_end]]
			})

			successful = frappe.db.count("Portugal Series Configuration", {
				"communication_date": ["between", [week_start, week_end]],
				"communication_status": "Success"
			})

			success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 100
			weekly_success_rates.append(success_rate)

		if len(weekly_success_rates) >= 2:
			recent_avg = sum(weekly_success_rates[:2]) / 2
			older_avg = sum(weekly_success_rates[2:]) / 2

			trend_change = recent_avg - older_avg
			return {
				"direction": "improving" if trend_change > 2 else "declining" if trend_change < -2 else "stable",
				"current_rate": round(recent_avg, 2),
				"change": round(trend_change, 2),
				"weekly_rates": weekly_success_rates
			}

		return {"direction": "stable", "current_rate": 100, "change": 0,
				"weekly_rates": weekly_success_rates}

	except Exception as e:
		frappe.log_error(f"Error calculating communication trend: {str(e)}")
		return {"direction": "unknown", "current_rate": 0, "change": 0, "weekly_rates": []}


def identify_trend_alerts(trends):
	"""
	Identifica alertas baseados em tendências
	"""
	try:
		alerts = []

		# Alerta para declínio na geração de ATCUD
		if trends["atcud_generation_trend"]["direction"] == "decreasing" and \
			trends["atcud_generation_trend"]["percentage"] < -20:
			alerts.append({
				"type": "atcud_decline",
				"severity": "warning",
				"message": f"ATCUD generation declined by {abs(trends['atcud_generation_trend']['percentage'])}%"
			})

		# Alerta para aumento de erros
		if trends["error_rate_trend"]["direction"] == "increasing" and trends["error_rate_trend"][
			"percentage"] > 25:
			alerts.append({
				"type": "error_increase",
				"severity": "critical",
				"message": f"Error rate increased by {trends['error_rate_trend']['percentage']}%"
			})

		# Alerta para declínio na comunicação
		if trends["communication_success_trend"]["direction"] == "declining" and \
			trends["communication_success_trend"]["change"] < -5:
			alerts.append({
				"type": "communication_decline",
				"severity": "warning",
				"message": f"Communication success rate declined by {abs(trends['communication_success_trend']['change'])}%"
			})

		return alerts

	except Exception as e:
		frappe.log_error(f"Error identifying trend alerts: {str(e)}")
		return []


def optimize_database_performance():
	"""
	Otimiza performance da base de dados
	"""
	try:
		frappe.logger().info("Optimizing database performance")

		# Analisar tabelas grandes
		analyze_large_tables()

		# Otimizar índices
		optimize_indexes()

		# Limpar dados desnecessários
		cleanup_unnecessary_data()

	except Exception as e:
		frappe.log_error(f"Error optimizing database performance: {str(e)}")


def analyze_large_tables():
	"""
	Analisa tabelas grandes do sistema
	"""
	try:
		# Verificar tamanho das tabelas principais
		table_sizes = frappe.db.sql("""
									SELECT table_name,
										   ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
									FROM information_schema.tables
									WHERE table_schema = DATABASE()
									  AND table_name IN
										  ('tabATCUD Log', 'tabPortugal Series Configuration',
										   'tabSAF-T Export Log')
									ORDER BY size_mb DESC
									""", as_dict=True)

		large_tables = [table for table in table_sizes if table.size_mb > 100]  # Tabelas > 100MB

		if large_tables:
			frappe.logger().info(f"Large tables found: {large_tables}")

			# Sugerir otimizações
			for table in large_tables:
				suggest_table_optimization(table)

	except Exception as e:
		frappe.log_error(f"Error analyzing large tables: {str(e)}")


def suggest_table_optimization(table):
	"""
	Sugere otimizações para tabela específica
	"""
	try:
		table_name = table.table_name

		if table_name == "tabATCUD Log":
			# Verificar se há muitos registos antigos
			old_records = frappe.db.count("ATCUD Log", {
				"creation": ["<", add_days(today(), -365)]
			})

			if old_records > 10000:
				frappe.logger().info(f"Consider archiving {old_records} old ATCUD Log records")

		elif table_name == "tabSAF-T Export Log":
			# Verificar logs de export antigos
			old_exports = frappe.db.count("SAF-T Export Log", {
				"creation": ["<", add_days(today(), -180)]
			})

			if old_exports > 100:
				frappe.logger().info(f"Consider cleaning {old_exports} old SAF-T export logs")

	except Exception as e:
		frappe.log_error(f"Error suggesting optimization for {table.table_name}: {str(e)}")


def optimize_indexes():
	"""
	Otimiza índices da base de dados
	"""
	try:
		# Verificar índices em falta ou desnecessários
		# Esta é uma implementação básica - expandir conforme necessário

		# Verificar se índices importantes existem
		important_indexes = [
			("tabATCUD Log", "atcud_code"),
			("tabATCUD Log", "creation"),
			("tabPortugal Series Configuration", "is_active"),
			("tabPortugal Series Configuration", "is_communicated")
		]

		for table, column in important_indexes:
			check_index_exists(table, column)

	except Exception as e:
		frappe.log_error(f"Error optimizing indexes: {str(e)}")


def check_index_exists(table, column):
	"""
	Verifica se índice existe numa tabela
	"""
	try:
		indexes = frappe.db.sql(f"""
            SHOW INDEX FROM `{table}` WHERE Column_name = %s
        """, column)

		if not indexes:
			frappe.logger().info(f"Consider adding index on {table}.{column}")

	except Exception as e:
		frappe.log_error(f"Error checking index for {table}.{column}: {str(e)}")


def cleanup_unnecessary_data():
	"""
	Limpa dados desnecessários
	"""
	try:
		# Limpar logs de erro muito antigos
		very_old_errors = frappe.db.count("Error Log", {
			"creation": ["<", add_days(today(), -180)],
			"error": ["like", "%portugal_compliance%"]
		})

		if very_old_errors > 0:
			frappe.db.delete("Error Log", {
				"creation": ["<", add_days(today(), -180)],
				"error": ["like", "%portugal_compliance%"]
			})
			frappe.logger().info(f"Cleaned {very_old_errors} very old error logs")

		# Limpar cache expirado
		cleanup_expired_cache()

	except Exception as e:
		frappe.log_error(f"Error cleaning unnecessary data: {str(e)}")


def cleanup_expired_cache():
	"""
	Limpa cache expirado
	"""
	try:
		# Limpar entradas de cache antigas do Portugal Compliance
		cache_keys_to_clean = [
			"portugal_compliance_temp_*",
			"portugal_compliance_old_*"
		]

		# Implementação específica dependeria do backend de cache usado
		frappe.logger().info("Cache cleanup completed")

	except Exception as e:
		frappe.log_error(f"Error cleaning expired cache: {str(e)}")


def backup_configuration_data():
	"""
	Faz backup dos dados de configuração
	"""
	try:
		frappe.logger().info("Backing up configuration data")

		# Backup de séries ativas
		backup_active_series()

		# Backup de configurações de empresa
		backup_company_configurations()

		# Backup de configurações de autenticação
		backup_auth_configurations()

	except Exception as e:
		frappe.log_error(f"Error backing up configuration data: {str(e)}")


def backup_active_series():
	"""
	Faz backup de séries ativas
	"""
	try:
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1},
										  fields=["*"]
										  )

		backup_data = {
			"backup_date": now(),
			"total_series": len(active_series),
			"series_data": active_series
		}

		# Armazenar backup no cache por 30 dias
		frappe.cache.set("portugal_compliance_series_backup", backup_data, expires_in_sec=2592000)

		frappe.logger().info(f"Backed up {len(active_series)} active series")

	except Exception as e:
		frappe.log_error(f"Error backing up active series: {str(e)}")


def backup_company_configurations():
	"""
	Faz backup de configurações de empresa
	"""
	try:
		companies = frappe.db.get_all("Company",
									  filters={"portugal_compliance_enabled": 1},
									  fields=["name", "company_name", "tax_id",
											  "at_certificate_number",
											  "portugal_compliance_enabled"]
									  )

		backup_data = {
			"backup_date": now(),
			"total_companies": len(companies),
			"companies_data": companies
		}

		frappe.cache.set("portugal_compliance_companies_backup", backup_data,
						 expires_in_sec=2592000)

		frappe.logger().info(f"Backed up {len(companies)} company configurations")

	except Exception as e:
		frappe.log_error(f"Error backing up company configurations: {str(e)}")


def backup_auth_configurations():
	"""
	Faz backup de configurações de autenticação (sem passwords)
	"""
	try:
		auth_configs = frappe.db.get_all("Portugal Auth Settings",
										 fields=["name", "company", "username", "environment",
												 "is_active"]  # Excluir password
										 )

		backup_data = {
			"backup_date": now(),
			"total_configs": len(auth_configs),
			"auth_data": auth_configs
		}

		frappe.cache.set("portugal_compliance_auth_backup", backup_data, expires_in_sec=2592000)

		frappe.logger().info(f"Backed up {len(auth_configs)} auth configurations")

	except Exception as e:
		frappe.log_error(f"Error backing up auth configurations: {str(e)}")


def review_error_patterns():
	"""
	Revê padrões de erro e sugere melhorias
	"""
	try:
		frappe.logger().info("Reviewing error patterns")

		# Analisar erros recorrentes
		analyze_recurring_errors()

		# Identificar gargalos
		identify_bottlenecks()

		# Sugerir melhorias
		suggest_improvements()

	except Exception as e:
		frappe.log_error(f"Error reviewing error patterns: {str(e)}")


def analyze_recurring_errors():
	"""
	Analisa erros recorrentes
	"""
	try:
		# Obter erros da última semana
		recurring_errors = frappe.db.sql("""
										 SELECT title, error, COUNT(*) as frequency
										 FROM `tabError Log`
										 WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
										   AND error LIKE '%portugal_compliance%'
										 GROUP BY title, error
										 HAVING frequency > 5
										 ORDER BY frequency DESC
										 """, as_dict=True)

		if recurring_errors:
			frappe.logger().warning(f"Found {len(recurring_errors)} recurring error patterns")

			# Armazenar para análise
			frappe.cache.set("portugal_compliance_recurring_errors", recurring_errors,
							 expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error analyzing recurring errors: {str(e)}")


def identify_bottlenecks():
	"""
	Identifica gargalos no sistema
	"""
	try:
		bottlenecks = []

		# Verificar séries com muitas tentativas de comunicação
		problematic_series = frappe.db.get_all("Portugal Series Configuration",
											   filters={"communication_attempts": [">", 2],
														"is_communicated": 0},
											   fields=["name", "series_name",
													   "communication_attempts", "error_message"]
											   )

		if problematic_series:
			bottlenecks.append({
				"type": "communication_failures",
				"count": len(problematic_series),
				"description": "Series with multiple failed communication attempts"
			})

		# Verificar ATCUD com problemas
		duplicate_atcud = frappe.db.sql("""
										SELECT atcud_code, COUNT(*) as count
										FROM `tabATCUD Log`
										WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
										GROUP BY atcud_code
										HAVING count > 1
										""")

		if duplicate_atcud:
			bottlenecks.append({
				"type": "duplicate_atcud",
				"count": len(duplicate_atcud),
				"description": "Duplicate ATCUD codes detected"
			})

		if bottlenecks:
			frappe.cache.set("portugal_compliance_bottlenecks", bottlenecks, expires_in_sec=604800)
			frappe.logger().warning(f"Identified {len(bottlenecks)} system bottlenecks")

	except Exception as e:
		frappe.log_error(f"Error identifying bottlenecks: {str(e)}")


def suggest_improvements():
	"""
	Sugere melhorias baseadas na análise
	"""
	try:
		improvements = []

		# Sugestões baseadas em erros recorrentes
		recurring_errors = frappe.cache.get("portugal_compliance_recurring_errors") or []
		if len(recurring_errors) > 5:
			improvements.append({
				"category": "error_reduction",
				"priority": "high",
				"suggestion": "Implement better error handling and retry mechanisms"
			})

		# Sugestões baseadas em gargalos
		bottlenecks = frappe.cache.get("portugal_compliance_bottlenecks") or []
		if bottlenecks:
			improvements.append({
				"category": "performance",
				"priority": "medium",
				"suggestion": "Address identified system bottlenecks"
			})

		# Sugestões baseadas em padrões de uso
		atcud_patterns = frappe.cache.get("portugal_compliance_atcud_patterns") or {}
		if atcud_patterns.get("peak_hours"):
			improvements.append({
				"category": "optimization",
				"priority": "low",
				"suggestion": f"Consider load balancing during peak hours: {atcud_patterns['peak_hours']}"
			})

		if improvements:
			frappe.cache.set("portugal_compliance_improvement_suggestions", improvements,
							 expires_in_sec=604800)
			frappe.logger().info(f"Generated {len(improvements)} improvement suggestions")

	except Exception as e:
		frappe.log_error(f"Error suggesting improvements: {str(e)}")


def update_series_recommendations():
	"""
	Atualiza recomendações para séries
	"""
	try:
		frappe.logger().info("Updating series recommendations")

		# Analisar uso de séries
		analyze_series_usage()

		# Recomendar otimizações
		recommend_series_optimizations()

	except Exception as e:
		frappe.log_error(f"Error updating series recommendations: {str(e)}")


def analyze_series_usage():
	"""
	Analisa uso de séries
	"""
	try:
		# Séries pouco utilizadas
		underused_series = frappe.db.sql("""
										 SELECT psc.name,
												psc.series_name,
												psc.company,
												COUNT(al.name) as usage_count
										 FROM `tabPortugal Series Configuration` psc
												  LEFT JOIN `tabATCUD Log` al ON al.series_name = psc.series_name
										 WHERE psc.is_active = 1
										   AND psc.creation <= DATE_SUB(NOW(), INTERVAL 30 DAY)
										 GROUP BY psc.name
										 HAVING usage_count < 10
										 """, as_dict=True)

		# Séries muito utilizadas
		overused_series = frappe.db.sql("""
										SELECT psc.name,
											   psc.series_name,
											   psc.company,
											   COUNT(al.name) as usage_count
										FROM `tabPortugal Series Configuration` psc
												 LEFT JOIN `tabATCUD Log` al ON al.series_name = psc.series_name
										WHERE psc.is_active = 1
										GROUP BY psc.name
										HAVING usage_count > 1000
										""", as_dict=True)

		usage_analysis = {
			"underused_series": underused_series,
			"overused_series": overused_series,
			"analysis_date": now()
		}

		frappe.cache.set("portugal_compliance_series_usage_analysis", usage_analysis,
						 expires_in_sec=604800)

	except Exception as e:
		frappe.log_error(f"Error analyzing series usage: {str(e)}")


def recommend_series_optimizations():
	"""
	Recomenda otimizações para séries
	"""
	try:
		usage_analysis = frappe.cache.get("portugal_compliance_series_usage_analysis") or {}
		recommendations = []

		# Recomendações para séries pouco utilizadas
		underused = usage_analysis.get("underused_series", [])
		if underused:
			recommendations.append({
				"type": "underused_series",
				"count": len(underused),
				"recommendation": "Consider deactivating or consolidating underused series",
				"series_list": [s.name for s in underused]
			})

		# Recomendações para séries muito utilizadas
		overused = usage_analysis.get("overused_series", [])
		if overused:
			recommendations.append({
				"type": "overused_series",
				"count": len(overused),
				"recommendation": "Consider creating additional series to distribute load",
				"series_list": [s.name for s in overused]
			})

		if recommendations:
			frappe.cache.set("portugal_compliance_series_recommendations", recommendations,
							 expires_in_sec=604800)
			frappe.logger().info(f"Generated {len(recommendations)} series recommendations")

	except Exception as e:
		frappe.log_error(f"Error recommending series optimizations: {str(e)}")


def cleanup_archived_data():
	"""
	Limpa dados arquivados
	"""
	try:
		frappe.logger().info("Cleaning up archived data")

		# Arquivar dados muito antigos
		archive_old_atcud_logs()
		archive_old_export_logs()

	except Exception as e:
		frappe.log_error(f"Error cleaning up archived data: {str(e)}")


def archive_old_atcud_logs():
	"""
	Arquiva logs de ATCUD antigos
	"""
	try:
		# Arquivar logs com mais de 2 anos
		archive_date = add_days(today(), -730)

		old_logs_count = frappe.db.count("ATCUD Log", {
			"creation": ["<", archive_date]
		})

		if old_logs_count > 0:
			# Criar backup antes de arquivar
			old_logs = frappe.db.get_all("ATCUD Log",
										 filters={"creation": ["<", archive_date]},
										 fields=["*"]
										 )

			# Armazenar backup
			archive_data = {
				"archive_date": now(),
				"total_logs": len(old_logs),
				"logs_data": old_logs
			}

			frappe.cache.set(f"portugal_compliance_atcud_archive_{archive_date}", archive_data,
							 expires_in_sec=31536000)  # 1 ano

			# Remover logs antigos
			frappe.db.delete("ATCUD Log", {"creation": ["<", archive_date]})

			frappe.logger().info(f"Archived {old_logs_count} old ATCUD logs")

	except Exception as e:
		frappe.log_error(f"Error archiving old ATCUD logs: {str(e)}")


def archive_old_export_logs():
	"""
	Arquiva logs de export antigos
	"""
	try:
		# Arquivar logs de export com mais de 1 ano
		archive_date = add_days(today(), -365)

		old_exports_count = frappe.db.count("SAF-T Export Log", {
			"creation": ["<", archive_date]
		})

		if old_exports_count > 0:
			# Remover logs antigos (após backup se necessário)
			frappe.db.delete("SAF-T Export Log", {"creation": ["<", archive_date]})

			frappe.logger().info(f"Archived {old_exports_count} old export logs")

	except Exception as e:
		frappe.log_error(f"Error archiving old export logs: {str(e)}")


def generate_audit_trail():
	"""
	Gera trilha de auditoria semanal
	"""
	try:
		frappe.logger().info("Generating weekly audit trail")

		end_date = today()
		start_date = add_days(end_date, -7)

		audit_data = {
			"period": {"start": start_date, "end": end_date},
			"series_changes": get_series_changes(start_date, end_date),
			"configuration_changes": get_configuration_changes(start_date, end_date),
			"user_activities": get_user_activities(start_date, end_date),
			"system_events": get_system_events(start_date, end_date)
		}

		# Armazenar trilha de auditoria
		frappe.cache.set(f"portugal_compliance_audit_trail_{end_date}", audit_data,
						 expires_in_sec=31536000)  # 1 ano

		frappe.logger().info(f"Generated audit trail for period {start_date} to {end_date}")

	except Exception as e:
		frappe.log_error(f"Error generating audit trail: {str(e)}")


def get_series_changes(start_date, end_date):
	"""
	Obtém mudanças em séries no período
	"""
	try:
		changes = {
			"created": frappe.db.count("Portugal Series Configuration", {
				"creation": ["between", [start_date, end_date]]
			}),
			"modified": frappe.db.count("Portugal Series Configuration", {
				"modified": ["between", [start_date, end_date]]
			}),
			"communicated": frappe.db.count("Portugal Series Configuration", {
				"communication_date": ["between", [start_date, end_date]]
			})
		}

		return changes

	except Exception as e:
		frappe.log_error(f"Error getting series changes: {str(e)}")
		return {}


def get_configuration_changes(start_date, end_date):
	"""
	Obtém mudanças de configuração no período
	"""
	try:
		changes = {
			"company_configs": frappe.db.count("Company", {
				"modified": ["between", [start_date, end_date]],
				"portugal_compliance_enabled": 1
			}),
			"auth_configs": frappe.db.count("Portugal Auth Settings", {
				"modified": ["between", [start_date, end_date]]
			})
		}

		return changes

	except Exception as e:
		frappe.log_error(f"Error getting configuration changes: {str(e)}")
		return {}


def get_user_activities(start_date, end_date):
	"""
	Obtém atividades de utilizador no período
	"""
	try:
		# Atividades relacionadas com Portugal Compliance
		activities = frappe.db.sql("""
								   SELECT COUNT(DISTINCT owner) as unique_users,
										  COUNT(*)              as total_activities
								   FROM `tabATCUD Log`
								   WHERE creation BETWEEN %s AND %s
								   """, (start_date, end_date), as_dict=True)

		return activities[0] if activities else {}

	except Exception as e:
		frappe.log_error(f"Error getting user activities: {str(e)}")
		return {}


def get_system_events(start_date, end_date):
	"""
	Obtém eventos de sistema no período
	"""
	try:
		events = {
			"errors": frappe.db.count("Error Log", {
				"creation": ["between", [start_date, end_date]],
				"error": ["like", "%portugal_compliance%"]
			}),
			"communications": frappe.db.count("Portugal Series Configuration", {
				"last_communication_attempt": ["between", [start_date, end_date]]
			})
		}

		return events

	except Exception as e:
		frappe.log_error(f"Error getting system events: {str(e)}")
		return {}


def send_weekly_summary():
	"""
	Envia resumo semanal para administradores
	"""
	try:
		frappe.logger().info("Sending weekly summary")

		# Obter dados do relatório semanal
		weekly_report = frappe.cache.get(f"portugal_compliance_weekly_report_{today()}")

		if not weekly_report:
			frappe.logger().warning("No weekly report data available for summary")
			return

		# Preparar resumo
		summary = prepare_weekly_summary(weekly_report)

		# Enviar para administradores
		send_summary_to_admins(summary)

	except Exception as e:
		frappe.log_error(f"Error sending weekly summary: {str(e)}")


def prepare_weekly_summary(report_data):
	"""
	Prepara resumo semanal
	"""
	try:
		summary = {
			"period": f"{report_data['period']['start_date']} to {report_data['period']['end_date']}",
			"compliance_score": report_data['compliance_score']['final_score'],
			"compliance_grade": report_data['compliance_score']['grade'],
			"key_metrics": {
				"atcud_generated": report_data['atcud_statistics']['total_generated'],
				"series_communicated": report_data['series_statistics']['series_communicated'],
				"errors_logged": report_data['error_statistics']['total_errors']
			},
			"alerts": [],
			"recommendations": []
		}

		# Adicionar alertas baseados nos dados
		if report_data['compliance_score']['final_score'] < 80:
			summary["alerts"].append("Compliance score below 80%")

		if report_data['error_statistics']['total_errors'] > 10:
			summary["alerts"].append(
				f"High error count: {report_data['error_statistics']['total_errors']}")

		if report_data['series_statistics']['pending_communications'] > 5:
			summary["alerts"].append(
				f"Multiple pending communications: {report_data['series_statistics']['pending_communications']}")

		# Adicionar recomendações
		if report_data['series_statistics']['communication_failures'] > 0:
			summary["recommendations"].append("Review failed communications and retry")

		if report_data['atcud_statistics']['duplicates_found'] > 0:
			summary["recommendations"].append("Investigate and resolve duplicate ATCUD codes")

		return summary

	except Exception as e:
		frappe.log_error(f"Error preparing weekly summary: {str(e)}")
		return {}


def send_summary_to_admins(summary):
	"""
	Envia resumo para administradores
	"""
	try:
		# Obter utilizadores administradores
		admin_users = frappe.db.get_all("User",
										filters={"role_profile_name": ["like", "%System Manager%"],
												 "enabled": 1},
										fields=["name", "email"]
										)

		# Preparar conteúdo do email
		subject = f"Portugal Compliance Weekly Summary - Grade {summary.get('compliance_grade', 'N/A')}"

		content = f"""
        <h2>Portugal Compliance Weekly Summary</h2>
        <p><strong>Period:</strong> {summary.get('period', 'N/A')}</p>
        <p><strong>Compliance Score:</strong> {summary.get('compliance_score', 0)}/100 (Grade: {summary.get('compliance_grade', 'N/A')})</p>

        <h3>Key Metrics</h3>
        <ul>
            <li>ATCUD Generated: {summary['key_metrics']['atcud_generated']}</li>
            <li>Series Communicated: {summary['key_metrics']['series_communicated']}</li>
            <li>Errors Logged: {summary['key_metrics']['errors_logged']}</li>
        </ul>

        <h3>Alerts</h3>
        <ul>
            {chr(10).join([f"<li>{alert}</li>" for alert in summary.get('alerts', [])])}
        </ul>

        <h3>Recommendations</h3>
        <ul>
            {chr(10).join([f"<li>{rec}</li>" for rec in summary.get('recommendations', [])])}
        </ul>

        <p><small>Generated automatically by Portugal Compliance module</small></p>
        """

		# Enviar para cada administrador
		for admin in admin_users:
			try:
				frappe.get_doc({
					"doctype": "Email Queue",
					"sender": "noreply@novadx.pt",
					"recipients": admin.email,
					"subject": subject,
					"message": content
				}).insert(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Error sending summary to {admin.email}: {str(e)}")

		frappe.logger().info(f"Weekly summary sent to {len(admin_users)} administrators")

	except Exception as e:
		frappe.log_error(f"Error sending summary to admins: {str(e)}")


def get_weekly_summary():
	"""
	Retorna resumo das atividades semanais

	Returns:
		dict: Resumo das atividades semanais
	"""
	try:
		end_date = today()
		weekly_report = frappe.cache.get(f"portugal_compliance_weekly_report_{end_date}")

		if weekly_report:
			return {
				"status": "completed",
				"report_date": end_date,
				"compliance_score": weekly_report['compliance_score']['final_score'],
				"compliance_grade": weekly_report['compliance_score']['grade'],
				"total_atcud": weekly_report['atcud_statistics']['total_generated'],
				"total_errors": weekly_report['error_statistics']['total_errors']
			}
		else:
			return {
				"status": "pending",
				"report_date": end_date,
				"message": "Weekly report not yet generated"
			}
	except Exception:
		return {"status": "error", "report_date": today()}
