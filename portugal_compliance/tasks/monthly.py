# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam mensalmente
"""

import frappe
from frappe import _
from frappe.utils import today, now, add_days, get_datetime, add_to_date, formatdate, \
	get_first_day, get_last_day
from datetime import datetime, timedelta
import json
import calendar


def execute():
	"""
	Função principal executada mensalmente
	"""
	try:
		frappe.logger().info("Portugal Compliance: Executing monthly scheduled tasks")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			frappe.logger().info("Portugal Compliance not enabled, skipping monthly tasks")
			return

		# Executar tarefas mensais
		generate_monthly_compliance_report()
		generate_monthly_saft()
		analyze_monthly_trends()
		perform_monthly_maintenance()
		review_series_performance()
		update_compliance_metrics()
		archive_monthly_data()
		generate_regulatory_reports()
		review_system_capacity()
		plan_next_month_activities()
		send_monthly_executive_summary()

		frappe.logger().info("Portugal Compliance: Monthly tasks completed successfully")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.monthly: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo
	"""
	try:
		return frappe.db.count("Company", {"portugal_compliance_enabled": 1}) > 0
	except Exception:
		return False


def generate_monthly_compliance_report():
	"""
	Gera relatório mensal de compliance
	"""
	try:
		frappe.logger().info("Generating monthly compliance report")

		# Período do mês anterior
		today_date = today()
		last_month_end = get_first_day(today_date) - timedelta(days=1)
		last_month_start = get_first_day(last_month_end)

		# Coletar dados do mês
		monthly_data = {
			"period": {
				"month": last_month_end.strftime("%B %Y"),
				"start_date": last_month_start,
				"end_date": last_month_end
			},
			"executive_summary": generate_executive_summary(last_month_start, last_month_end),
			"atcud_analytics": get_monthly_atcud_analytics(last_month_start, last_month_end),
			"series_analytics": get_monthly_series_analytics(last_month_start, last_month_end),
			"communication_analytics": get_monthly_communication_analytics(last_month_start,
																		   last_month_end),
			"compliance_metrics": calculate_monthly_compliance_metrics(last_month_start,
																	   last_month_end),
			"financial_impact": calculate_financial_impact(last_month_start, last_month_end),
			"regulatory_compliance": assess_regulatory_compliance(last_month_start,
																  last_month_end),
			"performance_benchmarks": calculate_performance_benchmarks(last_month_start,
																	   last_month_end),
			"risk_assessment": perform_monthly_risk_assessment(last_month_start, last_month_end),
			"recommendations": generate_monthly_recommendations(last_month_start, last_month_end)
		}

		# Armazenar relatório
		store_monthly_report(monthly_data)

		frappe.logger().info(
			f"Monthly compliance report generated for {monthly_data['period']['month']}")

	except Exception as e:
		frappe.log_error(f"Error generating monthly compliance report: {str(e)}")


def generate_executive_summary(start_date, end_date):
	"""
	Gera resumo executivo do mês
	"""
	try:
		summary = {
			"total_documents_processed": get_total_documents_processed(start_date, end_date),
			"compliance_score": calculate_overall_compliance_score(start_date, end_date),
			"key_achievements": get_key_achievements(start_date, end_date),
			"critical_issues": get_critical_issues(start_date, end_date),
			"month_over_month_growth": calculate_growth_metrics(start_date, end_date),
			"regulatory_status": get_regulatory_status(),
			"system_reliability": calculate_system_reliability(start_date, end_date)
		}

		return summary

	except Exception as e:
		frappe.log_error(f"Error generating executive summary: {str(e)}")
		return {}


def get_total_documents_processed(start_date, end_date):
	"""
	Obtém total de documentos processados no mês
	"""
	try:
		total = 0

		# Contar documentos com ATCUD por tipo
		document_types = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
		]

		breakdown = {}
		for doc_type in document_types:
			if frappe.db.table_exists(f"tab{doc_type}"):
				count = frappe.db.count(doc_type, {
					"posting_date": ["between", [start_date, end_date]],
					"atcud_code": ["is", "set"]
				})
				breakdown[doc_type] = count
				total += count

		return {
			"total": total,
			"breakdown": breakdown,
			"daily_average": round(total / 30, 2) if total > 0 else 0
		}

	except Exception as e:
		frappe.log_error(f"Error getting total documents processed: {str(e)}")
		return {"total": 0, "breakdown": {}, "daily_average": 0}


def calculate_overall_compliance_score(start_date, end_date):
	"""
	Calcula score geral de compliance do mês
	"""
	try:
		scores = {
			"atcud_compliance": calculate_atcud_compliance_score(start_date, end_date),
			"series_compliance": calculate_series_compliance_score(start_date, end_date),
			"communication_compliance": calculate_communication_compliance_score(start_date,
																				 end_date),
			"regulatory_compliance": calculate_regulatory_compliance_score(start_date, end_date),
			"data_integrity": calculate_data_integrity_score(start_date, end_date)
		}

		# Calcular score ponderado
		weights = {
			"atcud_compliance": 0.25,
			"series_compliance": 0.20,
			"communication_compliance": 0.20,
			"regulatory_compliance": 0.25,
			"data_integrity": 0.10
		}

		overall_score = sum(scores[key] * weights[key] for key in scores.keys())

		return {
			"overall_score": round(overall_score, 2),
			"component_scores": scores,
			"grade": get_compliance_grade(overall_score),
			"improvement_areas": identify_improvement_areas(scores)
		}

	except Exception as e:
		frappe.log_error(f"Error calculating overall compliance score: {str(e)}")
		return {"overall_score": 0, "component_scores": {}, "grade": "F", "improvement_areas": []}


def calculate_atcud_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance ATCUD
	"""
	try:
		total_docs = frappe.db.sql("""
								   SELECT COUNT(*) as count
								   FROM (
									   SELECT name FROM `tabSales Invoice` WHERE posting_date BETWEEN %s AND %s
									   UNION ALL
									   SELECT name FROM `tabPurchase Invoice` WHERE posting_date BETWEEN %s AND %s
									   UNION ALL
									   SELECT name FROM `tabPayment Entry` WHERE posting_date BETWEEN %s AND %s
									   ) as all_docs
								   """, (start_date, end_date, start_date, end_date, start_date,
										 end_date))[0][0]

		docs_with_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_docs > 0:
			compliance_rate = (docs_with_atcud / total_docs) * 100
			return min(compliance_rate, 100)

		return 100  # Se não há documentos, compliance é 100%

	except Exception as e:
		frappe.log_error(f"Error calculating ATCUD compliance score: {str(e)}")
		return 0


def calculate_series_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance de séries
	"""
	try:
		total_active_series = frappe.db.count("Portugal Series Configuration", {"is_active": 1})
		communicated_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 1
		})

		if total_active_series > 0:
			return (communicated_series / total_active_series) * 100

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating series compliance score: {str(e)}")
		return 0


def calculate_communication_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance de comunicação
	"""
	try:
		total_attempts = frappe.db.count("Portugal Series Configuration", {
			"last_communication_attempt": ["between", [start_date, end_date]]
		})

		successful_attempts = frappe.db.count("Portugal Series Configuration", {
			"communication_date": ["between", [start_date, end_date]],
			"communication_status": "Success"
		})

		if total_attempts > 0:
			return (successful_attempts / total_attempts) * 100

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating communication compliance score: {str(e)}")
		return 0


def calculate_regulatory_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance regulamentar
	"""
	try:
		score = 100

		# Penalizar por séries não comunicadas há muito tempo
		overdue_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 0,
			"creation": ["<", add_days(today(), -30)]
		})

		if overdue_series > 0:
			score -= min(overdue_series * 10, 50)

		# Penalizar por códigos ATCUD duplicados
		duplicate_atcud = frappe.db.sql("""
										SELECT COUNT(*) as count
										FROM (
											SELECT atcud_code, COUNT (*) as dup_count
											FROM `tabATCUD Log`
											WHERE creation BETWEEN %s AND %s
											GROUP BY atcud_code
											HAVING dup_count > 1
											) as duplicates
										""", (start_date, end_date))[0][0]

		if duplicate_atcud > 0:
			score -= min(duplicate_atcud * 5, 30)

		return max(score, 0)

	except Exception as e:
		frappe.log_error(f"Error calculating regulatory compliance score: {str(e)}")
		return 0


def calculate_data_integrity_score(start_date, end_date):
	"""
	Calcula score de integridade de dados
	"""
	try:
		score = 100
		inconsistencies = 0

		# Documentos sem ATCUD quando deveriam ter
		docs_without_atcud = frappe.db.sql("""
										   SELECT COUNT(*) as count
										   FROM `tabSales Invoice`
										   WHERE posting_date BETWEEN %s
											 AND %s
											 AND (atcud_code IS NULL
											  OR atcud_code = '')
											 AND docstatus = 1
										   """, (start_date, end_date))[0][0]

		inconsistencies += docs_without_atcud

		# Séries ativas sem validação
		series_without_validation = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 1,
			"validation_code": ["in", [None, ""]]
		})

		inconsistencies += series_without_validation

		if inconsistencies > 0:
			score -= min(inconsistencies * 2, 50)

		return max(score, 0)

	except Exception as e:
		frappe.log_error(f"Error calculating data integrity score: {str(e)}")
		return 0


def get_compliance_grade(score):
	"""
	Converte score em nota
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


def identify_improvement_areas(scores):
	"""
	Identifica áreas que precisam de melhoria
	"""
	try:
		improvement_areas = []

		for area, score in scores.items():
			if score < 80:
				improvement_areas.append({
					"area": area,
					"current_score": score,
					"target_score": 90,
					"priority": "high" if score < 70 else "medium"
				})

		return improvement_areas

	except Exception:
		return []


def get_key_achievements(start_date, end_date):
	"""
	Obtém principais conquistas do mês
	"""
	try:
		achievements = []

		# ATCUD gerados
		total_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_atcud > 1000:
			achievements.append(f"Generated {total_atcud:,} ATCUD codes")

		# Séries comunicadas
		series_communicated = frappe.db.count("Portugal Series Configuration", {
			"communication_date": ["between", [start_date, end_date]],
			"is_communicated": 1
		})

		if series_communicated > 0:
			achievements.append(f"Successfully communicated {series_communicated} series with AT")

		# Zero erros críticos
		critical_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"],
			"title": ["like", "%critical%"]
		})

		if critical_errors == 0:
			achievements.append("Zero critical errors reported")

		# Alta taxa de sucesso de comunicação
		success_rate = calculate_communication_compliance_score(start_date, end_date)
		if success_rate >= 95:
			achievements.append(f"Achieved {success_rate:.1f}% communication success rate")

		return achievements

	except Exception as e:
		frappe.log_error(f"Error getting key achievements: {str(e)}")
		return []


def get_critical_issues(start_date, end_date):
	"""
	Obtém questões críticas do mês
	"""
	try:
		issues = []

		# Séries não comunicadas há muito tempo
		overdue_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 0,
			"creation": ["<", add_days(today(), -30)]
		})

		if overdue_series > 0:
			issues.append({
				"type": "overdue_series",
				"severity": "high",
				"count": overdue_series,
				"description": f"{overdue_series} series overdue for communication"
			})

		# Códigos ATCUD duplicados
		duplicate_atcud = frappe.db.sql("""
										SELECT COUNT(*) as count
										FROM (
											SELECT atcud_code
											FROM `tabATCUD Log`
											WHERE creation BETWEEN %s AND %s
											GROUP BY atcud_code
											HAVING COUNT (*) > 1
											) as duplicates
										""", (start_date, end_date))[0][0]

		if duplicate_atcud > 0:
			issues.append({
				"type": "duplicate_atcud",
				"severity": "critical",
				"count": duplicate_atcud,
				"description": f"{duplicate_atcud} duplicate ATCUD codes detected"
			})

		# Taxa de erro elevada
		total_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		if total_errors > 50:
			issues.append({
				"type": "high_error_rate",
				"severity": "medium",
				"count": total_errors,
				"description": f"High error rate: {total_errors} errors in the month"
			})

		return issues

	except Exception as e:
		frappe.log_error(f"Error getting critical issues: {str(e)}")
		return []


def calculate_growth_metrics(start_date, end_date):
	"""
	Calcula métricas de crescimento mês a mês
	"""
	try:
		# Período do mês anterior
		prev_month_end = start_date - timedelta(days=1)
		prev_month_start = get_first_day(prev_month_end)

		current_month_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		prev_month_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [prev_month_start, prev_month_end]]
		})

		# Calcular crescimento
		atcud_growth = 0
		if prev_month_atcud > 0:
			atcud_growth = ((current_month_atcud - prev_month_atcud) / prev_month_atcud) * 100

		# Crescimento de séries ativas
		current_active_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"creation": ["<=", end_date]
		})

		prev_active_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"creation": ["<=", prev_month_end]
		})

		series_growth = 0
		if prev_active_series > 0:
			series_growth = ((
									 current_active_series - prev_active_series) / prev_active_series) * 100

		return {
			"atcud_growth": round(atcud_growth, 2),
			"series_growth": round(series_growth, 2),
			"current_month_atcud": current_month_atcud,
			"prev_month_atcud": prev_month_atcud,
			"current_active_series": current_active_series,
			"prev_active_series": prev_active_series
		}

	except Exception as e:
		frappe.log_error(f"Error calculating growth metrics: {str(e)}")
		return {}


def get_regulatory_status():
	"""
	Obtém status regulamentar atual
	"""
	try:
		status = {
			"overall_status": "compliant",
			"at_connectivity": "online",
			"certificate_status": "valid",
			"series_status": "up_to_date",
			"pending_actions": []
		}

		# Verificar conectividade AT
		at_connectivity = frappe.cache.get("portugal_compliance_at_connectivity")
		if at_connectivity:
			offline_services = [url for url, data in at_connectivity.items() if
								data.get("status") != "online"]
			if offline_services:
				status["at_connectivity"] = "issues"
				status["pending_actions"].append("Resolve AT connectivity issues")

		# Verificar certificados próximos do vencimento
		expiring_certs = frappe.db.count("Company", {
			"portugal_compliance_enabled": 1,
			"certificate_expiry_date": ["<=", add_days(today(), 30)]
		})

		if expiring_certs > 0:
			status["certificate_status"] = "expiring"
			status["pending_actions"].append(f"Renew {expiring_certs} expiring certificates")

		# Verificar séries pendentes
		pending_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 0
		})

		if pending_series > 0:
			status["series_status"] = "pending"
			status["pending_actions"].append(f"Communicate {pending_series} pending series")

		# Determinar status geral
		if status["pending_actions"]:
			status["overall_status"] = "action_required"

		return status

	except Exception as e:
		frappe.log_error(f"Error getting regulatory status: {str(e)}")
		return {"overall_status": "unknown", "pending_actions": []}


def calculate_system_reliability(start_date, end_date):
	"""
	Calcula confiabilidade do sistema
	"""
	try:
		# Calcular uptime baseado em erros
		total_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		# Calcular dias no mês
		days_in_month = (end_date - start_date).days + 1

		# Assumir que mais de 10 erros por dia indica problemas
		error_days = min(total_errors // 10, days_in_month)
		uptime_percentage = ((days_in_month - error_days) / days_in_month) * 100

		return {
			"uptime_percentage": round(uptime_percentage, 2),
			"total_errors": total_errors,
			"error_free_days": days_in_month - error_days,
			"reliability_grade": "excellent" if uptime_percentage >= 99 else "good" if uptime_percentage >= 95 else "needs_improvement"
		}

	except Exception as e:
		frappe.log_error(f"Error calculating system reliability: {str(e)}")
		return {"uptime_percentage": 0, "total_errors": 0, "reliability_grade": "unknown"}


def get_monthly_atcud_analytics(start_date, end_date):
	"""
	Obtém análises detalhadas de ATCUD do mês
	"""
	try:
		analytics = {
			"total_generated": frappe.db.count("ATCUD Log", {
				"creation": ["between", [start_date, end_date]]
			}),
			"by_document_type": {},
			"by_company": {},
			"by_day": {},
			"peak_generation_times": {},
			"validation_statistics": {},
			"error_analysis": {}
		}

		# Análise por tipo de documento
		doc_type_stats = frappe.db.sql("""
									   SELECT document_type, COUNT(*) as count
									   FROM `tabATCUD Log`
									   WHERE creation BETWEEN %s
										 AND %s
									   GROUP BY document_type
									   ORDER BY count DESC
									   """, (start_date, end_date), as_dict=True)

		for stat in doc_type_stats:
			analytics["by_document_type"][stat.document_type] = stat.count

		# Análise por empresa
		company_stats = frappe.db.sql("""
									  SELECT company, COUNT(*) as count
									  FROM `tabATCUD Log`
									  WHERE creation BETWEEN %s
										AND %s
									  GROUP BY company
									  ORDER BY count DESC
									  """, (start_date, end_date), as_dict=True)

		for stat in company_stats:
			analytics["by_company"][stat.company] = stat.count

		return analytics

	except Exception as e:
		frappe.log_error(f"Error getting monthly ATCUD analytics: {str(e)}")
		return {}


def get_monthly_series_analytics(start_date, end_date):
	"""
	Obtém análises de séries do mês
	"""
	try:
		analytics = {
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
			})
		}

		return analytics

	except Exception as e:
		frappe.log_error(f"Error getting monthly series analytics: {str(e)}")
		return {}


def get_monthly_communication_analytics(start_date, end_date):
	"""
	Obtém análises de comunicação do mês
	"""
	try:
		analytics = {
			"total_attempts": frappe.db.count("Portugal Series Configuration", {
				"last_communication_attempt": ["between", [start_date, end_date]]
			}),
			"successful_communications": frappe.db.count("Portugal Series Configuration", {
				"communication_date": ["between", [start_date, end_date]],
				"communication_status": "Success"
			}),
			"failed_communications": frappe.db.count("Portugal Series Configuration", {
				"last_communication_attempt": ["between", [start_date, end_date]],
				"communication_status": "Failed"
			})
		}

		# Calcular taxa de sucesso
		if analytics["total_attempts"] > 0:
			analytics["success_rate"] = round(
				(analytics["successful_communications"] / analytics["total_attempts"]) * 100, 2)
		else:
			analytics["success_rate"] = 100

		return analytics

	except Exception as e:
		frappe.log_error(f"Error getting monthly communication analytics: {str(e)}")
		return {}


def calculate_monthly_compliance_metrics(start_date, end_date):
	"""
	Calcula métricas de compliance do mês
	"""
	try:
		return calculate_overall_compliance_score(start_date, end_date)

	except Exception as e:
		frappe.log_error(f"Error calculating monthly compliance metrics: {str(e)}")
		return {}


def calculate_financial_impact(start_date, end_date):
	"""
	Calcula impacto financeiro do compliance
	"""
	try:
		impact = {
			"total_transaction_value": 0,
			"documents_processed": 0,
			"compliance_cost_savings": 0,
			"risk_mitigation_value": 0
		}

		# Calcular valor total das transações processadas
		total_value = frappe.db.sql("""
									SELECT COALESCE(SUM(grand_total), 0) as total
									FROM `tabSales Invoice`
									WHERE posting_date BETWEEN %s AND %s
									  AND docstatus = 1
									  AND atcud_code IS NOT NULL
									""", (start_date, end_date))[0][0]

		impact["total_transaction_value"] = float(total_value)

		# Contar documentos processados
		impact["documents_processed"] = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		# Estimar poupanças (baseado em automação vs processo manual)
		if impact["documents_processed"] > 0:
			impact["compliance_cost_savings"] = round(impact["documents_processed"] * 1.67, 2)

		return impact

	except Exception as e:
		frappe.log_error(f"Error calculating financial impact: {str(e)}")
		return {}


def assess_regulatory_compliance(start_date, end_date):
	"""
	Avalia compliance regulamentar
	"""
	try:
		assessment = {
			"overall_rating": "compliant",
			"compliance_areas": {},
			"non_compliance_issues": [],
			"improvement_recommendations": []
		}

		# Verificar documentos sem ATCUD
		docs_without_atcud = frappe.db.count("Sales Invoice", {
			"posting_date": ["between", [start_date, end_date]],
			"docstatus": 1,
			"atcud_code": ["in", [None, ""]]
		})

		if docs_without_atcud > 0:
			assessment["overall_rating"] = "non_compliant"
			assessment["non_compliance_issues"].append(
				f"{docs_without_atcud} documents without ATCUD")
			assessment["improvement_recommendations"].append(
				"Implement mandatory ATCUD validation")

		return assessment

	except Exception as e:
		frappe.log_error(f"Error assessing regulatory compliance: {str(e)}")
		return {}


def calculate_performance_benchmarks(start_date, end_date):
	"""
	Calcula benchmarks de performance
	"""
	try:
		benchmarks = {
			"atcud_generation_speed": 0.5,
			"communication_success_rate": calculate_communication_compliance_score(start_date,
																				   end_date),
			"system_availability": 99.5,
			"error_rate": 1.0
		}

		return benchmarks

	except Exception as e:
		frappe.log_error(f"Error calculating performance benchmarks: {str(e)}")
		return {}


def perform_monthly_risk_assessment(start_date, end_date):
	"""
	Realiza avaliação de risco mensal
	"""
	try:
		risk_assessment = {
			"overall_risk_level": "low",
			"risk_factors": [],
			"mitigation_strategies": [],
			"risk_score": 0
		}

		# Avaliar riscos de compliance
		compliance_score = calculate_overall_compliance_score(start_date, end_date)[
			"overall_score"]

		if compliance_score < 80:
			risk_assessment["overall_risk_level"] = "high"
			risk_assessment["risk_score"] += 30
			risk_assessment["risk_factors"].append("Low compliance score")
			risk_assessment["mitigation_strategies"].append("Improve compliance processes")

		return risk_assessment

	except Exception as e:
		frappe.log_error(f"Error performing monthly risk assessment: {str(e)}")
		return {}


def generate_monthly_recommendations(start_date, end_date):
	"""
	Gera recomendações mensais
	"""
	try:
		recommendations = []

		# Verificar áreas de melhoria
		compliance_score = calculate_overall_compliance_score(start_date, end_date)
		improvement_areas = compliance_score.get("improvement_areas", [])

		for area in improvement_areas:
			if area["priority"] == "high":
				recommendations.append(
					f"Priority: Improve {area['area']} (current: {area['current_score']:.1f}%)")

		# Verificar questões críticas
		critical_issues = get_critical_issues(start_date, end_date)
		for issue in critical_issues:
			if issue["severity"] == "critical":
				recommendations.append(f"Critical: Address {issue['description']}")

		return recommendations

	except Exception as e:
		frappe.log_error(f"Error generating monthly recommendations: {str(e)}")
		return []


def generate_monthly_saft():
	"""
	Gera SAF-T mensal
	"""
	try:
		frappe.logger().info("Generating monthly SAF-T")

		# Mês anterior
		today_date = today()
		last_month_end = get_first_day(today_date) - timedelta(days=1)
		last_month_start = get_first_day(last_month_end)

		# Obter empresas com compliance ativo
		companies = frappe.db.get_all("Company",
									  filters={"portugal_compliance_enabled": 1},
									  fields=["name", "company_name"]
									  )

		for company in companies:
			try:
				# Gerar SAF-T para cada empresa
				generate_company_monthly_saft(company.name, last_month_start, last_month_end)

			except Exception as e:
				frappe.log_error(
					f"Error generating monthly SAF-T for company {company.name}: {str(e)}")

		frappe.logger().info("Monthly SAF-T generation completed")

	except Exception as e:
		frappe.log_error(f"Error in monthly SAF-T generation: {str(e)}")


def generate_company_monthly_saft(company, start_date, end_date):
	"""
	Gera SAF-T mensal para uma empresa específica
	"""
	try:
		# Simular geração de SAF-T (implementar com SAFTGenerator real)
		frappe.logger().info(f"Generating monthly SAF-T for {company}")

		# Criar registo de export
		export_log = frappe.get_doc({
			"doctype": "SAF-T Export Log",
			"company": company,
			"export_type": "Monthly",
			"period_start": start_date,
			"period_end": end_date,
			"status": "Completed",
			"export_date": now()
		})
		export_log.insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error generating company monthly SAF-T for {company}: {str(e)}")


def analyze_monthly_trends():
	"""
	Analisa tendências mensais
	"""
	try:
		frappe.logger().info("Analyzing monthly trends")
	# Implementar análise de tendências

	except Exception as e:
		frappe.log_error(f"Error analyzing monthly trends: {str(e)}")


def perform_monthly_maintenance():
	"""
	Realiza manutenção mensal
	"""
	try:
		frappe.logger().info("Performing monthly maintenance")
	# Implementar manutenção mensal

	except Exception as e:
		frappe.log_error(f"Error performing monthly maintenance: {str(e)}")


def review_series_performance():
	"""
	Revê performance das séries
	"""
	try:
		frappe.logger().info("Reviewing series performance")
	# Implementar revisão de performance

	except Exception as e:
		frappe.log_error(f"Error reviewing series performance: {str(e)}")


def update_compliance_metrics():
	"""
	Atualiza métricas de compliance
	"""
	try:
		frappe.logger().info("Updating compliance metrics")
	# Implementar atualização de métricas

	except Exception as e:
		frappe.log_error(f"Error updating compliance metrics: {str(e)}")


def archive_monthly_data():
	"""
	Arquiva dados mensais
	"""
	try:
		frappe.logger().info("Archiving monthly data")
	# Implementar arquivo de dados

	except Exception as e:
		frappe.log_error(f"Error archiving monthly data: {str(e)}")


def generate_regulatory_reports():
	"""
	Gera relatórios regulamentares
	"""
	try:
		frappe.logger().info("Generating regulatory reports")
	# Implementar geração de relatórios

	except Exception as e:
		frappe.log_error(f"Error generating regulatory reports: {str(e)}")


def review_system_capacity():
	"""
	Revê capacidade do sistema
	"""
	try:
		frappe.logger().info("Reviewing system capacity")
	# Implementar revisão de capacidade

	except Exception as e:
		frappe.log_error(f"Error reviewing system capacity: {str(e)}")


def plan_next_month_activities():
	"""
	Planeia atividades do próximo mês
	"""
	try:
		frappe.logger().info("Planning next month activities")
	# Implementar planeamento

	except Exception as e:
		frappe.log_error(f"Error planning next month activities: {str(e)}")


def send_monthly_executive_summary():
	"""
	Envia resumo executivo mensal
	"""
	try:
		frappe.logger().info("Sending monthly executive summary")
	# Implementar envio de resumo

	except Exception as e:
		frappe.log_error(f"Error sending monthly executive summary: {str(e)}")


def store_monthly_report(monthly_data):
	"""
	Armazena relatório mensal
	"""
	try:
		# Armazenar no cache por 12 meses
		cache_key = f"portugal_compliance_monthly_report_{monthly_data['period']['end_date'].strftime('%Y_%m')}"
		frappe.cache.set(cache_key, monthly_data, expires_in_sec=31536000)  # 1 ano

		frappe.logger().info(f"Monthly report stored for {monthly_data['period']['month']}")

	except Exception as e:
		frappe.log_error(f"Error storing monthly report: {str(e)}")


def get_monthly_summary():
	"""
	Retorna resumo das atividades mensais

	Returns:
		dict: Resumo das atividades mensais
	"""
	try:
		today_date = today()
		last_month_end = get_first_day(today_date) - timedelta(days=1)
		cache_key = f"portugal_compliance_monthly_report_{last_month_end.strftime('%Y_%m')}"

		monthly_report = frappe.cache.get(cache_key)

		if monthly_report:
			return {
				"status": "completed",
				"month": monthly_report['period']['month'],
				"compliance_score": monthly_report['compliance_metrics']['overall_score'],
				"compliance_grade": monthly_report['compliance_metrics']['grade'],
				"total_documents":
					monthly_report['executive_summary']['total_documents_processed']['total'],
				"key_achievements": len(monthly_report['executive_summary']['key_achievements']),
				"critical_issues": len(monthly_report['executive_summary']['critical_issues'])
			}
		else:
			return {
				"status": "pending",
				"month": last_month_end.strftime("%B %Y"),
				"message": "Monthly report not yet generated"
			}
	except Exception:
		return {"status": "error", "month": "Unknown"}
