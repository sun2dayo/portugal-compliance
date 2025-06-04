# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam anualmente
"""

import frappe
from frappe import _
from frappe.utils import today, now, add_days, get_datetime, add_to_date, formatdate, \
	get_first_day, get_last_day
from datetime import datetime, timedelta, date
import json
import calendar


def execute():
	"""
	Função principal executada anualmente
	"""
	try:
		frappe.logger().info("Portugal Compliance: Executing yearly scheduled tasks")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			frappe.logger().info("Portugal Compliance not enabled, skipping yearly tasks")
			return

		# Executar tarefas anuais
		generate_annual_compliance_report()
		generate_annual_saft()
		perform_annual_data_archival()
		conduct_annual_compliance_audit()
		review_annual_performance()
		update_regulatory_requirements()
		plan_next_year_compliance()
		generate_executive_annual_summary()
		perform_annual_system_optimization()
		review_and_update_policies()
		conduct_annual_risk_assessment()
		prepare_regulatory_submissions()

		frappe.logger().info("Portugal Compliance: Yearly tasks completed successfully")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.yearly: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo
	"""
	try:
		return frappe.db.count("Company", {"portugal_compliance_enabled": 1}) > 0
	except Exception:
		return False


def generate_annual_compliance_report():
	"""
	Gera relatório anual de compliance
	"""
	try:
		frappe.logger().info("Generating annual compliance report")

		# Ano anterior completo
		current_year = datetime.now().year
		previous_year = current_year - 1
		year_start = date(previous_year, 1, 1)
		year_end = date(previous_year, 12, 31)

		# Coletar dados do ano
		annual_data = {
			"year": previous_year,
			"period": {
				"start_date": year_start,
				"end_date": year_end
			},
			"executive_summary": generate_annual_executive_summary(year_start, year_end),
			"compliance_overview": generate_compliance_overview(year_start, year_end),
			"operational_metrics": calculate_annual_operational_metrics(year_start, year_end),
			"financial_impact": calculate_annual_financial_impact(year_start, year_end),
			"regulatory_compliance": assess_annual_regulatory_compliance(year_start, year_end),
			"risk_management": conduct_annual_risk_review(year_start, year_end),
			"technology_performance": evaluate_technology_performance(year_start, year_end),
			"stakeholder_impact": assess_stakeholder_impact(year_start, year_end),
			"benchmarking": perform_annual_benchmarking(year_start, year_end),
			"strategic_recommendations": generate_strategic_recommendations(year_start, year_end),
			"next_year_planning": create_next_year_plan(current_year)
		}

		# Armazenar relatório
		store_annual_report(annual_data)

		frappe.logger().info(f"Annual compliance report generated for year {previous_year}")

	except Exception as e:
		frappe.log_error(f"Error generating annual compliance report: {str(e)}")


def generate_annual_executive_summary(start_date, end_date):
	"""
	Gera resumo executivo anual
	"""
	try:
		summary = {
			"year_overview": {
				"total_documents_processed": get_annual_document_count(start_date, end_date),
				"total_atcud_generated": frappe.db.count("ATCUD Log", {
					"creation": ["between", [start_date, end_date]]
				}),
				"series_managed": frappe.db.count("Portugal Series Configuration", {
					"creation": ["<=", end_date]
				}),
				"companies_served": frappe.db.count("Company", {
					"portugal_compliance_enabled": 1,
					"creation": ["<=", end_date]
				})
			},
			"key_achievements": get_annual_achievements(start_date, end_date),
			"compliance_score": calculate_annual_compliance_score(start_date, end_date),
			"operational_excellence": measure_operational_excellence(start_date, end_date),
			"strategic_initiatives": review_strategic_initiatives(start_date, end_date),
			"challenges_overcome": identify_challenges_overcome(start_date, end_date),
			"future_outlook": create_future_outlook()
		}

		return summary

	except Exception as e:
		frappe.log_error(f"Error generating annual executive summary: {str(e)}")
		return {}


def get_annual_document_count(start_date, end_date):
	"""
	Obtém contagem anual de documentos
	"""
	try:
		document_types = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
		]

		total_count = 0
		breakdown = {}

		for doc_type in document_types:
			if frappe.db.table_exists(f"tab{doc_type}"):
				count = frappe.db.count(doc_type, {
					"posting_date": ["between", [start_date, end_date]],
					"atcud_code": ["is", "set"]
				})
				breakdown[doc_type] = count
				total_count += count

		return {
			"total": total_count,
			"breakdown": breakdown,
			"daily_average": round(total_count / 365, 2),
			"monthly_average": round(total_count / 12, 2)
		}

	except Exception as e:
		frappe.log_error(f"Error getting annual document count: {str(e)}")
		return {"total": 0, "breakdown": {}, "daily_average": 0, "monthly_average": 0}


def get_annual_achievements(start_date, end_date):
	"""
	Obtém conquistas anuais
	"""
	try:
		achievements = []

		# Milestone de documentos processados
		total_docs = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_docs >= 100000:
			achievements.append(f"Processed over {total_docs:,} documents with ATCUD compliance")
		elif total_docs >= 50000:
			achievements.append(f"Successfully processed {total_docs:,} documents")
		elif total_docs >= 10000:
			achievements.append(f"Achieved {total_docs:,} document processing milestone")

		# Zero incidentes críticos
		critical_incidents = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"],
			"title": ["like", "%critical%"]
		})

		if critical_incidents == 0:
			achievements.append(
				"Maintained zero critical compliance incidents throughout the year")

		# Alta disponibilidade do sistema
		total_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		if total_errors < 100:
			achievements.append("Achieved excellent system reliability with minimal errors")

		# Comunicação de séries bem-sucedida
		successful_communications = frappe.db.count("Portugal Series Configuration", {
			"communication_date": ["between", [start_date, end_date]],
			"communication_status": "Success"
		})

		if successful_communications >= 100:
			achievements.append(
				f"Successfully communicated {successful_communications} series with AT")

		# Compliance score alto
		compliance_score = calculate_annual_compliance_score(start_date, end_date)
		if compliance_score.get("overall_score", 0) >= 95:
			achievements.append(
				f"Maintained excellent compliance score of {compliance_score['overall_score']:.1f}%")

		return achievements

	except Exception as e:
		frappe.log_error(f"Error getting annual achievements: {str(e)}")
		return []


def calculate_annual_compliance_score(start_date, end_date):
	"""
	Calcula score de compliance anual
	"""
	try:
		# Componentes do score
		components = {
			"document_compliance": calculate_document_compliance_annual(start_date, end_date),
			"series_compliance": calculate_series_compliance_annual(start_date, end_date),
			"communication_compliance": calculate_communication_compliance_annual(start_date,
																				  end_date),
			"data_integrity": calculate_data_integrity_annual(start_date, end_date),
			"regulatory_adherence": calculate_regulatory_adherence_annual(start_date, end_date),
			"system_reliability": calculate_system_reliability_annual(start_date, end_date)
		}

		# Pesos para cada componente
		weights = {
			"document_compliance": 0.25,
			"series_compliance": 0.20,
			"communication_compliance": 0.15,
			"data_integrity": 0.15,
			"regulatory_adherence": 0.15,
			"system_reliability": 0.10
		}

		# Calcular score ponderado
		overall_score = sum(components[key] * weights[key] for key in components.keys())

		return {
			"overall_score": round(overall_score, 2),
			"components": components,
			"grade": get_compliance_grade(overall_score),
			"year_over_year_change": calculate_year_over_year_change(start_date, end_date)
		}

	except Exception as e:
		frappe.log_error(f"Error calculating annual compliance score: {str(e)}")
		return {"overall_score": 0, "components": {}, "grade": "F"}


def calculate_document_compliance_annual(start_date, end_date):
	"""
	Calcula compliance de documentos anual
	"""
	try:
		# Documentos que deveriam ter ATCUD
		total_docs = 0
		docs_with_atcud = 0

		document_types = ["Sales Invoice", "Purchase Invoice", "Payment Entry"]

		for doc_type in document_types:
			if frappe.db.table_exists(f"tab{doc_type}"):
				total = frappe.db.count(doc_type, {
					"posting_date": ["between", [start_date, end_date]],
					"docstatus": 1
				})

				with_atcud = frappe.db.count(doc_type, {
					"posting_date": ["between", [start_date, end_date]],
					"docstatus": 1,
					"atcud_code": ["is", "set"]
				})

				total_docs += total
				docs_with_atcud += with_atcud

		if total_docs > 0:
			return (docs_with_atcud / total_docs) * 100

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating document compliance annual: {str(e)}")
		return 0


def calculate_series_compliance_annual(start_date, end_date):
	"""
	Calcula compliance de séries anual
	"""
	try:
		total_series = frappe.db.count("Portugal Series Configuration", {
			"creation": ["<=", end_date],
			"is_active": 1
		})

		communicated_series = frappe.db.count("Portugal Series Configuration", {
			"creation": ["<=", end_date],
			"is_active": 1,
			"is_communicated": 1
		})

		if total_series > 0:
			return (communicated_series / total_series) * 100

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating series compliance annual: {str(e)}")
		return 0


def calculate_communication_compliance_annual(start_date, end_date):
	"""
	Calcula compliance de comunicação anual
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
		frappe.log_error(f"Error calculating communication compliance annual: {str(e)}")
		return 0


def calculate_data_integrity_annual(start_date, end_date):
	"""
	Calcula integridade de dados anual
	"""
	try:
		# Verificar duplicados ATCUD
		duplicates = frappe.db.sql("""
								   SELECT COUNT(*) as count
								   FROM (
									   SELECT atcud_code
									   FROM `tabATCUD Log`
									   WHERE creation BETWEEN %s AND %s
									   GROUP BY atcud_code
									   HAVING COUNT (*) > 1
									   ) as dup
								   """, (start_date, end_date))[0][0]

		total_atcud = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_atcud > 0:
			integrity_score = max(0, 100 - (duplicates / total_atcud * 100))
			return integrity_score

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating data integrity annual: {str(e)}")
		return 0


def calculate_regulatory_adherence_annual(start_date, end_date):
	"""
	Calcula aderência regulamentar anual
	"""
	try:
		score = 100

		# Penalizar por séries não comunicadas
		uncommunicated_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 0,
			"creation": ["<", add_days(end_date, -30)]
		})

		if uncommunicated_series > 0:
			score -= min(uncommunicated_series * 5, 50)

		# Penalizar por documentos sem ATCUD
		docs_without_atcud = frappe.db.count("Sales Invoice", {
			"posting_date": ["between", [start_date, end_date]],
			"docstatus": 1,
			"atcud_code": ["in", [None, ""]]
		})

		total_docs = frappe.db.count("Sales Invoice", {
			"posting_date": ["between", [start_date, end_date]],
			"docstatus": 1
		})

		if total_docs > 0:
			non_compliance_rate = (docs_without_atcud / total_docs) * 100
			score -= min(non_compliance_rate * 2, 30)

		return max(score, 0)

	except Exception as e:
		frappe.log_error(f"Error calculating regulatory adherence annual: {str(e)}")
		return 0


def calculate_system_reliability_annual(start_date, end_date):
	"""
	Calcula confiabilidade do sistema anual
	"""
	try:
		total_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"]
		})

		total_operations = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_operations > 0:
			error_rate = (total_errors / total_operations) * 100
			reliability_score = max(0, 100 - error_rate * 10)
			return reliability_score

		return 100

	except Exception as e:
		frappe.log_error(f"Error calculating system reliability annual: {str(e)}")
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


def calculate_year_over_year_change(start_date, end_date):
	"""
	Calcula mudança ano a ano
	"""
	try:
		# Período do ano anterior
		prev_year_start = date(start_date.year - 1, 1, 1)
		prev_year_end = date(start_date.year - 1, 12, 31)

		# Score do ano atual
		current_score = calculate_annual_compliance_score(start_date, end_date)["overall_score"]

		# Score do ano anterior
		prev_score = calculate_annual_compliance_score(prev_year_start, prev_year_end)[
			"overall_score"]

		if prev_score > 0:
			change = current_score - prev_score
			change_percentage = (change / prev_score) * 100

			return {
				"absolute_change": round(change, 2),
				"percentage_change": round(change_percentage, 2),
				"trend": "improving" if change > 0 else "declining" if change < 0 else "stable"
			}

		return {"absolute_change": 0, "percentage_change": 0, "trend": "stable"}

	except Exception as e:
		frappe.log_error(f"Error calculating year over year change: {str(e)}")
		return {"absolute_change": 0, "percentage_change": 0, "trend": "unknown"}


def generate_annual_saft():
	"""
	Gera SAF-T anual
	"""
	try:
		frappe.logger().info("Generating annual SAF-T export")

		# Ano anterior completo
		current_year = datetime.now().year
		previous_year = current_year - 1
		year_start = date(previous_year, 1, 1)
		year_end = date(previous_year, 12, 31)

		# Obter empresas com compliance ativo
		companies = frappe.db.get_all("Company",
									  filters={"portugal_compliance_enabled": 1},
									  fields=["name", "company_name"]
									  )

		for company in companies:
			try:
				# Gerar SAF-T para cada empresa
				generate_company_annual_saft(company.name, year_start, year_end, previous_year)

			except Exception as e:
				frappe.log_error(
					f"Error generating annual SAF-T for company {company.name}: {str(e)}")

		frappe.logger().info(f"Annual SAF-T generation completed for year {previous_year}")

	except Exception as e:
		frappe.log_error(f"Error in annual SAF-T generation: {str(e)}")


def generate_company_annual_saft(company, start_date, end_date, year):
	"""
	Gera SAF-T anual para uma empresa específica
	"""
	try:
		from portugal_compliance.utils.saft_generator import SAFTGenerator

		# Criar instância do gerador
		saft_generator = SAFTGenerator()

		# Gerar SAF-T
		saft_xml = saft_generator.generate_saft(
			company=company,
			start_date=start_date,
			end_date=end_date
		)

		# Criar registo de export
		export_log = frappe.get_doc({
			"doctype": "SAF-T Export Log",
			"company": company,
			"export_type": "Annual",
			"period_start": start_date,
			"period_end": end_date,
			"year": year,
			"status": "Completed",
			"file_size": len(saft_xml.encode('utf-8')),
			"export_date": now()
		})
		export_log.insert(ignore_permissions=True)

		# Guardar ficheiro
		filename = f"SAF-T_{company}_{year}_Annual.xml"
		file_path = f"/tmp/{filename}"

		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(saft_xml)

		frappe.logger().info(f"Annual SAF-T generated for {company}: {filename}")

	except Exception as e:
		frappe.log_error(f"Error generating company annual SAF-T for {company}: {str(e)}")


def perform_annual_data_archival():
	"""
	Realiza arquivo anual de dados
	"""
	try:
		frappe.logger().info("Performing annual data archival")

		# Definir período de retenção (10 anos para dados fiscais)
		retention_date = add_days(today(), -3650)  # 10 anos

		# Arquivar diferentes tipos de dados
		archive_old_atcud_logs(retention_date)
		archive_old_error_logs(retention_date)
		archive_old_export_logs(retention_date)
		archive_old_communication_logs(retention_date)

		# Otimizar base de dados após arquivo
		optimize_database_after_archival()

		frappe.logger().info("Annual data archival completed")

	except Exception as e:
		frappe.log_error(f"Error performing annual data archival: {str(e)}")


def archive_old_atcud_logs(retention_date):
	"""
	Arquiva logs de ATCUD antigos
	"""
	try:
		# Contar registos a arquivar
		old_logs_count = frappe.db.count("ATCUD Log", {
			"creation": ["<", retention_date]
		})

		if old_logs_count > 0:
			# Criar backup antes de arquivar
			old_logs = frappe.db.get_all("ATCUD Log",
										 filters={"creation": ["<", retention_date]},
										 fields=["*"]
										 )

			# Armazenar backup
			archive_data = {
				"archive_date": now(),
				"retention_date": retention_date,
				"total_logs": len(old_logs),
				"logs_data": old_logs
			}

			# Guardar arquivo (implementar storage adequado)
			archive_filename = f"atcud_archive_{retention_date.strftime('%Y%m%d')}.json"
			with open(f"/tmp/{archive_filename}", 'w') as f:
				json.dump(archive_data, f, default=str, indent=2)

			# Remover logs antigos
			frappe.db.delete("ATCUD Log", {"creation": ["<", retention_date]})

			frappe.logger().info(f"Archived {old_logs_count} old ATCUD logs")

	except Exception as e:
		frappe.log_error(f"Error archiving old ATCUD logs: {str(e)}")


def archive_old_error_logs(retention_date):
	"""
	Arquiva logs de erro antigos
	"""
	try:
		# Manter apenas erros relacionados com Portugal Compliance
		old_errors_count = frappe.db.count("Error Log", {
			"creation": ["<", retention_date],
			"error": ["like", "%portugal_compliance%"]
		})

		if old_errors_count > 0:
			frappe.db.delete("Error Log", {
				"creation": ["<", retention_date],
				"error": ["like", "%portugal_compliance%"]
			})

			frappe.logger().info(f"Archived {old_errors_count} old error logs")

	except Exception as e:
		frappe.log_error(f"Error archiving old error logs: {str(e)}")


def archive_old_export_logs(retention_date):
	"""
	Arquiva logs de export antigos
	"""
	try:
		old_exports_count = frappe.db.count("SAF-T Export Log", {
			"creation": ["<", retention_date]
		})

		if old_exports_count > 0:
			# Manter registo mas remover ficheiros grandes
			frappe.db.set_value("SAF-T Export Log",
								{"creation": ["<", retention_date]},
								"file_content", None
								)

			frappe.logger().info(f"Archived content of {old_exports_count} old export logs")

	except Exception as e:
		frappe.log_error(f"Error archiving old export logs: {str(e)}")


def archive_old_communication_logs(retention_date):
	"""
	Arquiva logs de comunicação antigos
	"""
	try:
		# Limpar tentativas de comunicação muito antigas
		old_attempts = frappe.db.sql("""
									 UPDATE `tabPortugal Series Configuration`
									 SET last_communication_attempt = NULL,
										 communication_attempts     = 0,
										 error_message              = NULL
									 WHERE last_communication_attempt < %s
									   AND is_communicated = 1
									 """, retention_date)

		frappe.logger().info("Cleaned old communication attempts")

	except Exception as e:
		frappe.log_error(f"Error archiving old communication logs: {str(e)}")


def optimize_database_after_archival():
	"""
	Otimiza base de dados após arquivo
	"""
	try:
		# Otimizar tabelas principais
		tables_to_optimize = [
			"tabATCUD Log",
			"tabError Log",
			"tabSAF-T Export Log",
			"tabPortugal Series Configuration"
		]

		for table in tables_to_optimize:
			try:
				frappe.db.sql(f"OPTIMIZE TABLE `{table}`")
			except Exception as e:
				frappe.log_error(f"Error optimizing table {table}: {str(e)}")

		frappe.logger().info("Database optimization completed")

	except Exception as e:
		frappe.log_error(f"Error optimizing database: {str(e)}")


def conduct_annual_compliance_audit():
	"""
	Conduz auditoria anual de compliance
	"""
	try:
		frappe.logger().info("Conducting annual compliance audit")

		# Ano anterior
		current_year = datetime.now().year
		previous_year = current_year - 1
		year_start = date(previous_year, 1, 1)
		year_end = date(previous_year, 12, 31)

		audit_results = {
			"audit_year": previous_year,
			"audit_date": now(),
			"compliance_areas": {},
			"findings": [],
			"recommendations": [],
			"overall_assessment": ""
		}

		# Auditar diferentes áreas
		audit_results["compliance_areas"]["atcud_compliance"] = audit_atcud_compliance(year_start,
																					   year_end)
		audit_results["compliance_areas"]["series_management"] = audit_series_management(
			year_start, year_end)
		audit_results["compliance_areas"]["data_integrity"] = audit_data_integrity(year_start,
																				   year_end)
		audit_results["compliance_areas"]["regulatory_adherence"] = audit_regulatory_adherence(
			year_start, year_end)
		audit_results["compliance_areas"]["system_security"] = audit_system_security(year_start,
																					 year_end)

		# Compilar descobertas e recomendações
		compile_audit_findings(audit_results)

		# Armazenar resultados da auditoria
		store_audit_results(audit_results)

		frappe.logger().info(f"Annual compliance audit completed for year {previous_year}")

	except Exception as e:
		frappe.log_error(f"Error conducting annual compliance audit: {str(e)}")


def audit_atcud_compliance(start_date, end_date):
	"""
	Auditoria de compliance ATCUD
	"""
	try:
		audit_result = {
			"status": "compliant",
			"score": 100,
			"issues": [],
			"recommendations": []
		}

		# Verificar documentos sem ATCUD
		docs_without_atcud = frappe.db.count("Sales Invoice", {
			"posting_date": ["between", [start_date, end_date]],
			"docstatus": 1,
			"atcud_code": ["in", [None, ""]]
		})

		total_docs = frappe.db.count("Sales Invoice", {
			"posting_date": ["between", [start_date, end_date]],
			"docstatus": 1
		})

		if total_docs > 0:
			compliance_rate = ((total_docs - docs_without_atcud) / total_docs) * 100
			audit_result["score"] = round(compliance_rate, 2)

			if compliance_rate < 100:
				audit_result[
					"status"] = "non_compliant" if compliance_rate < 95 else "minor_issues"
				audit_result["issues"].append(
					f"{docs_without_atcud} documents without ATCUD ({100 - compliance_rate:.1f}% non-compliance)")
				audit_result["recommendations"].append(
					"Implement mandatory ATCUD validation before document submission")

		# Verificar duplicados
		duplicates = frappe.db.sql("""
								   SELECT COUNT(*) as count
								   FROM (
									   SELECT atcud_code
									   FROM `tabATCUD Log`
									   WHERE creation BETWEEN %s AND %s
									   GROUP BY atcud_code
									   HAVING COUNT (*) > 1
									   ) as dup
								   """, (start_date, end_date))[0][0]

		if duplicates > 0:
			audit_result["status"] = "non_compliant"
			audit_result["score"] -= min(duplicates * 5, 50)
			audit_result["issues"].append(f"{duplicates} duplicate ATCUD codes detected")
			audit_result["recommendations"].append(
				"Implement stronger uniqueness validation for ATCUD generation")

		return audit_result

	except Exception as e:
		frappe.log_error(f"Error auditing ATCUD compliance: {str(e)}")
		return {"status": "error", "score": 0, "issues": ["Audit failed"], "recommendations": []}


def audit_series_management(start_date, end_date):
	"""
	Auditoria de gestão de séries
	"""
	try:
		audit_result = {
			"status": "compliant",
			"score": 100,
			"issues": [],
			"recommendations": []
		}

		# Verificar séries não comunicadas
		uncommunicated_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 0
		})

		total_active_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1
		})

		if total_active_series > 0:
			communication_rate = ((
										  total_active_series - uncommunicated_series) / total_active_series) * 100

			if communication_rate < 100:
				audit_result["score"] = round(communication_rate, 2)
				if communication_rate < 95:
					audit_result["status"] = "non_compliant"
				audit_result["issues"].append(
					f"{uncommunicated_series} active series not communicated with AT")
				audit_result["recommendations"].append(
					"Establish automated series communication process")

		# Verificar falhas de comunicação
		failed_communications = frappe.db.count("Portugal Series Configuration", {
			"communication_status": "Failed",
			"last_communication_attempt": ["between", [start_date, end_date]]
		})

		if failed_communications > 0:
			audit_result["issues"].append(
				f"{failed_communications} series with communication failures")
			audit_result["recommendations"].append(
				"Implement robust retry mechanism for failed communications")

		return audit_result

	except Exception as e:
		frappe.log_error(f"Error auditing series management: {str(e)}")
		return {"status": "error", "score": 0, "issues": ["Audit failed"], "recommendations": []}


def audit_data_integrity(start_date, end_date):
	"""
	Auditoria de integridade de dados
	"""
	try:
		audit_result = {
			"status": "compliant",
			"score": 100,
			"issues": [],
			"recommendations": []
		}

		# Verificar consistência de dados
		inconsistencies = 0

		# Documentos com ATCUD mas sem registo no log
		docs_with_atcud = frappe.db.sql("""
										SELECT COUNT(*) as count
										FROM `tabSales Invoice`
										WHERE posting_date BETWEEN %s
										  AND %s
										  AND atcud_code IS NOT NULL
										  AND atcud_code != ''
										  AND atcud_code NOT IN (
											SELECT DISTINCT atcud_code
											FROM `tabATCUD Log`
											WHERE atcud_code IS NOT NULL
											)
										""", (start_date, end_date))[0][0]

		inconsistencies += docs_with_atcud

		if docs_with_atcud > 0:
			audit_result["issues"].append(
				f"{docs_with_atcud} documents with ATCUD but no log entry")

		# Logs ATCUD sem documento correspondente
		orphaned_logs = frappe.db.sql("""
									  SELECT COUNT(*) as count
									  FROM `tabATCUD Log`
									  WHERE creation BETWEEN %s
										AND %s
										AND document_name NOT IN (
										  SELECT name FROM `tabSales Invoice`
										  UNION
										  SELECT name FROM `tabPurchase Invoice`
										  UNION
										  SELECT name FROM `tabPayment Entry`
										  )
									  """, (start_date, end_date))[0][0]

		inconsistencies += orphaned_logs

		if orphaned_logs > 0:
			audit_result["issues"].append(f"{orphaned_logs} orphaned ATCUD log entries")

		# Calcular score baseado em inconsistências
		total_records = frappe.db.count("ATCUD Log", {
			"creation": ["between", [start_date, end_date]]
		})

		if total_records > 0 and inconsistencies > 0:
			integrity_score = max(0, 100 - (inconsistencies / total_records * 100))
			audit_result["score"] = round(integrity_score, 2)

			if integrity_score < 95:
				audit_result[
					"status"] = "non_compliant" if integrity_score < 90 else "minor_issues"
				audit_result["recommendations"].append(
					"Implement data consistency validation processes")

		return audit_result

	except Exception as e:
		frappe.log_error(f"Error auditing data integrity: {str(e)}")
		return {"status": "error", "score": 0, "issues": ["Audit failed"], "recommendations": []}


def audit_regulatory_adherence(start_date, end_date):
	"""
	Auditoria de aderência regulamentar
	"""
	try:
		audit_result = {
			"status": "compliant",
			"score": 100,
			"issues": [],
			"recommendations": []
		}

		# Verificar cumprimento de prazos regulamentares
		# Séries devem ser comunicadas dentro de 7 dias
		overdue_series = frappe.db.sql("""
									   SELECT COUNT(*) as count
									   FROM `tabPortugal Series Configuration`
									   WHERE is_active = 1
										 AND is_communicated = 0
										 AND DATEDIFF(NOW()
										   , creation)
										   > 7
									   """)[0][0]

		if overdue_series > 0:
			audit_result["status"] = "non_compliant"
			audit_result["score"] -= min(overdue_series * 10, 50)
			audit_result["issues"].append(
				f"{overdue_series} series overdue for communication (>7 days)")
			audit_result["recommendations"].append(
				"Establish automated communication workflow with deadline monitoring")

		# Verificar SAF-T mensal
		months_without_saft = check_monthly_saft_compliance(start_date, end_date)

		if months_without_saft > 0:
			audit_result["status"] = "non_compliant"
			audit_result["score"] -= min(months_without_saft * 15, 60)
			audit_result["issues"].append(f"{months_without_saft} months without SAF-T export")
			audit_result["recommendations"].append("Implement automated monthly SAF-T generation")

		return audit_result

	except Exception as e:
		frappe.log_error(f"Error auditing regulatory adherence: {str(e)}")
		return {"status": "error", "score": 0, "issues": ["Audit failed"], "recommendations": []}


def check_monthly_saft_compliance(start_date, end_date):
	"""
	Verifica compliance de SAF-T mensal
	"""
	try:
		months_without_saft = 0
		current_date = start_date

		while current_date <= end_date:
			month_start = get_first_day(current_date)
			month_end = get_last_day(current_date)

			# Verificar se existe SAF-T para este mês
			saft_exists = frappe.db.exists("SAF-T Export Log", {
				"period_start": month_start,
				"period_end": month_end,
				"status": "Completed"
			})

			if not saft_exists:
				months_without_saft += 1

			# Próximo mês
			if current_date.month == 12:
				current_date = date(current_date.year + 1, 1, 1)
			else:
				current_date = date(current_date.year, current_date.month + 1, 1)

		return months_without_saft

	except Exception as e:
		frappe.log_error(f"Error checking monthly SAF-T compliance: {str(e)}")
		return 0


def audit_system_security(start_date, end_date):
	"""
	Auditoria de segurança do sistema
	"""
	try:
		audit_result = {
			"status": "compliant",
			"score": 100,
			"issues": [],
			"recommendations": []
		}

		# Verificar tentativas de acesso não autorizadas
		security_errors = frappe.db.count("Error Log", {
			"creation": ["between", [start_date, end_date]],
			"error": ["like", "%portugal_compliance%"],
			"title": ["like", "%security%"]
		})

		if security_errors > 0:
			audit_result["issues"].append(f"{security_errors} security-related errors detected")
			audit_result["recommendations"].append("Review and strengthen security measures")

		# Verificar uso de credenciais
		companies_without_secure_auth = frappe.db.count("Portugal Auth Settings", {
			"password": ["like", "%test%"]  # Passwords óbvias
		})

		if companies_without_secure_auth > 0:
			audit_result["status"] = "non_compliant"
			audit_result["score"] -= 30
			audit_result["issues"].append(
				f"{companies_without_secure_auth} companies with weak authentication")
			audit_result["recommendations"].append(
				"Implement strong password policies and secure credential storage")

		return audit_result

	except Exception as e:
		frappe.log_error(f"Error auditing system security: {str(e)}")
		return {"status": "error", "score": 0, "issues": ["Audit failed"], "recommendations": []}


def compile_audit_findings(audit_results):
	"""
	Compila descobertas da auditoria
	"""
	try:
		all_issues = []
		all_recommendations = []

		for area, result in audit_results["compliance_areas"].items():
			all_issues.extend(result.get("issues", []))
			all_recommendations.extend(result.get("recommendations", []))

		audit_results["findings"] = all_issues
		audit_results["recommendations"] = list(set(all_recommendations))  # Remove duplicados

		# Determinar avaliação geral
		non_compliant_areas = len(
			[area for area, result in audit_results["compliance_areas"].items()
			 if result.get("status") == "non_compliant"])

		if non_compliant_areas == 0:
			audit_results["overall_assessment"] = "fully_compliant"
		elif non_compliant_areas <= 2:
			audit_results["overall_assessment"] = "mostly_compliant"
		else:
			audit_results["overall_assessment"] = "non_compliant"

	except Exception as e:
		frappe.log_error(f"Error compiling audit findings: {str(e)}")


def store_audit_results(audit_results):
	"""
	Armazena resultados da auditoria
	"""
	try:
		# Criar documento de auditoria
		audit_doc = frappe.get_doc({
			"doctype": "Portugal Compliance Audit",
			"audit_year": audit_results["audit_year"],
			"audit_date": audit_results["audit_date"],
			"overall_assessment": audit_results["overall_assessment"],
			"total_findings": len(audit_results["findings"]),
			"total_recommendations": len(audit_results["recommendations"]),
			"audit_results": json.dumps(audit_results, default=str, indent=2)
		})
		audit_doc.insert(ignore_permissions=True)

		# Armazenar no cache por 5 anos
		cache_key = f"portugal_compliance_annual_audit_{audit_results['audit_year']}"
		frappe.cache.set(cache_key, audit_results, expires_in_sec=157680000)  # 5 anos

		frappe.logger().info(f"Audit results stored for year {audit_results['audit_year']}")

	except Exception as e:
		frappe.log_error(f"Error storing audit results: {str(e)}")


def store_annual_report(annual_data):
	"""
	Armazena relatório anual
	"""
	try:
		# Armazenar no cache por 10 anos
		cache_key = f"portugal_compliance_annual_report_{annual_data['year']}"
		frappe.cache.set(cache_key, annual_data, expires_in_sec=315360000)  # 10 anos

		# Criar ficheiro de backup
		filename = f"portugal_compliance_annual_report_{annual_data['year']}.json"
		filepath = f"/tmp/{filename}"

		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(annual_data, f, default=str, indent=2)

		frappe.logger().info(f"Annual report stored for year {annual_data['year']}")

	except Exception as e:
		frappe.log_error(f"Error storing annual report: {str(e)}")


def get_yearly_summary():
	"""
	Retorna resumo das atividades anuais

	Returns:
		dict: Resumo das atividades anuais
	"""
	try:
		current_year = datetime.now().year
		previous_year = current_year - 1

		annual_report = frappe.cache.get(f"portugal_compliance_annual_report_{previous_year}")

		if annual_report:
			return {
				"status": "completed",
				"year": previous_year,
				"compliance_score": annual_report['executive_summary']['compliance_score'][
					'overall_score'],
				"total_documents": annual_report['executive_summary']['year_overview'][
					'total_documents_processed']['total'],
				"key_achievements": len(annual_report['executive_summary']['key_achievements']),
				"report_date": annual_report['period']['end_date']
			}
		else:
			return {
				"status": "pending",
				"year": previous_year,
				"message": "Annual report not yet generated"
			}
	except Exception:
		return {"status": "error", "year": datetime.now().year - 1}
