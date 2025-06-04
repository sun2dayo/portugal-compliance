# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Tarefas que executam de hora em hora
"""

import frappe
from frappe import _
from frappe.utils import now, get_datetime, add_to_date, cint
from datetime import datetime, timedelta
import requests


def execute():
	"""
	Função principal executada de hora em hora
	"""
	try:
		frappe.logger().info("Portugal Compliance: Executing hourly scheduled tasks")

		# Verificar se o módulo está ativo
		if not is_portugal_compliance_enabled():
			return

		# Executar tarefas horárias
		check_at_connectivity()
		sync_pending_series()
		monitor_system_performance()
		process_failed_communications()
		update_real_time_cache()
		check_certificate_status()
		validate_recent_atcud()
		cleanup_temporary_files()

		frappe.logger().info("Portugal Compliance: Hourly tasks completed successfully")

	except Exception as e:
		frappe.log_error(f"Error in portugal_compliance.tasks.hourly: {str(e)}")


def is_portugal_compliance_enabled():
	"""
	Verifica se o módulo Portugal Compliance está ativo
	"""
	try:
		return frappe.db.count("Company", {"portugal_compliance_enabled": 1}) > 0
	except Exception:
		return False


def check_at_connectivity():
	"""
	Verifica conectividade com webservices da AT
	"""
	try:
		frappe.logger().info("Checking AT webservice connectivity")

		# URLs dos webservices da AT
		at_endpoints = [
			"https://servicos.portaldasfinancas.gov.pt/sgdtws/documentosTransporte",
			"https://servicos.portaldasfinancas.gov.pt/fews/faturas"
		]

		connectivity_status = {}

		for endpoint in at_endpoints:
			try:
				response = requests.get(endpoint, timeout=10)
				connectivity_status[endpoint] = {
					"status": "online" if response.status_code in [200, 401, 403] else "offline",
					"response_time": response.elapsed.total_seconds(),
					"status_code": response.status_code,
					"checked_at": now()
				}
			except requests.exceptions.Timeout:
				connectivity_status[endpoint] = {
					"status": "timeout",
					"error": "Request timeout",
					"checked_at": now()
				}
			except requests.exceptions.ConnectionError:
				connectivity_status[endpoint] = {
					"status": "offline",
					"error": "Connection error",
					"checked_at": now()
				}
			except Exception as e:
				connectivity_status[endpoint] = {
					"status": "error",
					"error": str(e),
					"checked_at": now()
				}

		# Armazenar status no cache
		frappe.cache.set("portugal_compliance_at_connectivity", connectivity_status,
						 expires_in_sec=3600)

		# Log se houver problemas
		offline_services = [url for url, status in connectivity_status.items() if
							status["status"] != "online"]
		if offline_services:
			frappe.logger().warning(f"AT services offline: {offline_services}")

	except Exception as e:
		frappe.log_error(f"Error checking AT connectivity: {str(e)}")


def sync_pending_series():
	"""
	Sincroniza séries pendentes com a AT
	"""
	try:
		frappe.logger().info("Syncing pending series with AT")

		# Obter séries pendentes de comunicação
		pending_series = frappe.db.get_all("Portugal Series Configuration",
										   filters={
											   "is_communicated": 0,
											   "is_active": 1,
											   "communication_attempts": ["<", 3]
											   # Máximo 3 tentativas
										   },
										   fields=["name", "series_name", "company",
												   "communication_attempts",
												   "last_communication_attempt"]
										   )

		for series in pending_series:
			# Verificar se já passou tempo suficiente desde última tentativa
			if should_retry_communication(series):
				try_series_communication(series)

		if pending_series:
			frappe.logger().info(f"Processed {len(pending_series)} pending series")

	except Exception as e:
		frappe.log_error(f"Error syncing pending series: {str(e)}")


def should_retry_communication(series):
	"""
	Verifica se deve tentar comunicar série novamente
	"""
	try:
		if not series.last_communication_attempt:
			return True

		# Aguardar pelo menos 1 hora entre tentativas
		last_attempt = get_datetime(series.last_communication_attempt)
		now_time = get_datetime(now())

		return (now_time - last_attempt).seconds >= 3600

	except Exception:
		return True


def try_series_communication(series):
	"""
	Tenta comunicar série com a AT
	"""
	try:
		# Verificar se existem credenciais
		auth_settings = frappe.db.get_value("Portugal Auth Settings",
											series.company, ["username", "password"], as_dict=True)

		if not auth_settings or not auth_settings.username:
			frappe.logger().warning(f"No credentials for company {series.company}")
			return

		# Incrementar contador de tentativas
		frappe.db.set_value("Portugal Series Configuration", series.name, {
			"communication_attempts": (series.communication_attempts or 0) + 1,
			"last_communication_attempt": now()
		})

		# Aqui seria feita a comunicação real com a AT
		# Por agora, simular sucesso/falha
		communication_result = simulate_at_communication(series)

		if communication_result["success"]:
			frappe.db.set_value("Portugal Series Configuration", series.name, {
				"is_communicated": 1,
				"communication_date": now(),
				"validation_code": communication_result.get("validation_code"),
				"communication_status": "Success"
			})
			frappe.logger().info(f"Successfully communicated series {series.name}")
		else:
			frappe.db.set_value("Portugal Series Configuration", series.name, {
				"communication_status": "Failed",
				"error_message": communication_result.get("error")
			})
			frappe.logger().error(
				f"Failed to communicate series {series.name}: {communication_result.get('error')}")

	except Exception as e:
		frappe.log_error(f"Error communicating series {series.name}: {str(e)}")


def simulate_at_communication(series):
	"""
	Simula comunicação com AT (substituir por implementação real)
	"""
	try:
		# Simulação - na realidade seria chamada ao webservice
		import random

		if random.random() > 0.2:  # 80% de sucesso
			return {
				"success": True,
				"validation_code": f"ATCUD{random.randint(100000, 999999)}"
			}
		else:
			return {
				"success": False,
				"error": "Simulated AT communication error"
			}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


def monitor_system_performance():
	"""
	Monitoriza performance do sistema
	"""
	try:
		# Verificar uso de CPU e memória
		import psutil

		system_metrics = {
			"timestamp": now(),
			"cpu_percent": psutil.cpu_percent(interval=1),
			"memory_percent": psutil.virtual_memory().percent,
			"disk_usage": psutil.disk_usage('/').percent
		}

		# Verificar performance da base de dados
		db_metrics = check_database_performance()
		system_metrics.update(db_metrics)

		# Armazenar métricas
		frappe.cache.set("portugal_compliance_system_metrics", system_metrics, expires_in_sec=3600)

		# Alertar se performance estiver degradada
		if system_metrics["cpu_percent"] > 80 or system_metrics["memory_percent"] > 85:
			frappe.logger().warning(
				f"High system resource usage: CPU {system_metrics['cpu_percent']}%, Memory {system_metrics['memory_percent']}%")

	except ImportError:
		# psutil não disponível
		frappe.logger().info("psutil not available for system monitoring")
	except Exception as e:
		frappe.log_error(f"Error monitoring system performance: {str(e)}")


def check_database_performance():
	"""
	Verifica performance da base de dados
	"""
	try:
		start_time = datetime.now()

		# Teste simples de performance
		frappe.db.sql("SELECT COUNT(*) FROM `tabPortugal Series Configuration`")

		query_time = (datetime.now() - start_time).total_seconds()

		return {
			"db_query_time": query_time,
			"db_status": "healthy" if query_time < 1.0 else "slow"
		}

	except Exception as e:
		return {
			"db_query_time": None,
			"db_status": "error",
			"db_error": str(e)
		}


def process_failed_communications():
	"""
	Processa comunicações falhadas
	"""
	try:
		# Séries com comunicação falhada há mais de 1 hora
		failed_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={
											  "communication_status": "Failed",
											  "is_active": 1,
											  "last_communication_attempt": ["<",
																			 add_to_date(now(),
																						 hours=-1)]
										  },
										  fields=["name", "series_name", "company",
												  "error_message", "communication_attempts"]
										  )

		for series in failed_series:
			# Tentar novamente se não excedeu limite de tentativas
			if (series.communication_attempts or 0) < 3:
				try_series_communication(series)
			else:
				# Marcar como necessita intervenção manual
				frappe.db.set_value("Portugal Series Configuration", series.name, {
					"communication_status": "Manual Intervention Required"
				})

				# Criar notificação para administradores
				create_manual_intervention_notification(series)

		if failed_series:
			frappe.logger().info(f"Processed {len(failed_series)} failed communications")

	except Exception as e:
		frappe.log_error(f"Error processing failed communications: {str(e)}")


def create_manual_intervention_notification(series):
	"""
	Cria notificação para intervenção manual
	"""
	try:
		# Obter utilizadores administradores
		admin_users = frappe.db.get_all("User",
										filters={
											"role_profile_name": ["like", "%System Manager%"]},
										fields=["name"]
										)

		message = _(
			"Series '{0}' requires manual intervention. Communication failed after multiple attempts.").format(
			series.series_name
		)

		for user in admin_users:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": _("Portugal Compliance: Manual Intervention Required"),
				"email_content": message,
				"for_user": user.name,
				"type": "Alert",
				"document_type": "Portugal Series Configuration",
				"document_name": series.name
			}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Error creating manual intervention notification: {str(e)}")


def update_real_time_cache():
	"""
	Atualiza cache em tempo real
	"""
	try:
		# Cache de séries ativas
		active_series = frappe.db.get_all("Portugal Series Configuration",
										  filters={"is_active": 1, "is_communicated": 1},
										  fields=["name", "series_name", "prefix",
												  "current_number", "company"]
										  )

		# Organizar por empresa
		series_by_company = {}
		for series in active_series:
			company = series.company
			if company not in series_by_company:
				series_by_company[company] = []
			series_by_company[company].append(series)

		frappe.cache.set("portugal_compliance_active_series_realtime", series_by_company,
						 expires_in_sec=3600)

		# Cache de estatísticas horárias
		hourly_stats = {
			"timestamp": now(),
			"active_series": len(active_series),
			"pending_communications": frappe.db.count("Portugal Series Configuration", {
				"is_communicated": 0, "is_active": 1
			}),
			"failed_communications": frappe.db.count("Portugal Series Configuration", {
				"communication_status": "Failed"
			})
		}

		frappe.cache.set("portugal_compliance_hourly_stats", hourly_stats, expires_in_sec=3600)

	except Exception as e:
		frappe.log_error(f"Error updating real-time cache: {str(e)}")


def check_certificate_status():
	"""
	Verifica status dos certificados
	"""
	try:
		# Verificar certificados que expiram em breve
		companies_with_certs = frappe.db.get_all("Company",
												 filters={"portugal_compliance_enabled": 1,
														  "at_certificate_number": ["is", "set"]},
												 fields=["name", "at_certificate_number",
														 "certificate_expiry_date"]
												 )

		for company in companies_with_certs:
			if company.certificate_expiry_date:
				days_until_expiry = (
						get_datetime(company.certificate_expiry_date) - get_datetime(now())).days

				if days_until_expiry <= 30:
					create_certificate_expiry_alert(company, days_until_expiry)

	except Exception as e:
		frappe.log_error(f"Error checking certificate status: {str(e)}")


def create_certificate_expiry_alert(company, days_until_expiry):
	"""
	Cria alerta de expiração de certificado
	"""
	try:
		severity = "critical" if days_until_expiry <= 7 else "warning"

		message = _("AT Certificate for company '{0}' expires in {1} days").format(
			company.name, days_until_expiry
		)

		# Criar log de erro para rastreamento
		frappe.log_error(message, "Certificate Expiry Alert")

	except Exception as e:
		frappe.log_error(f"Error creating certificate expiry alert: {str(e)}")


def validate_recent_atcud():
	"""
	Valida códigos ATCUD gerados na última hora
	"""
	try:
		# Obter ATCUDs gerados na última hora
		one_hour_ago = add_to_date(now(), hours=-1)

		recent_atcud = frappe.db.get_all("ATCUD Log",
										 filters={"creation": [">=", one_hour_ago]},
										 fields=["name", "atcud_code", "document_type",
												 "document_name"]
										 )

		# Verificar duplicados
		atcud_codes = [log.atcud_code for log in recent_atcud if log.atcud_code]
		duplicates = [code for code in set(atcud_codes) if atcud_codes.count(code) > 1]

		if duplicates:
			frappe.log_error(f"Duplicate ATCUD codes found in last hour: {duplicates}",
							 "ATCUD Validation")

		frappe.logger().info(f"Validated {len(recent_atcud)} recent ATCUD codes")

	except Exception as e:
		frappe.log_error(f"Error validating recent ATCUD: {str(e)}")


def cleanup_temporary_files():
	"""
	Limpa ficheiros temporários
	"""
	try:
		import os
		import glob

		# Limpar ficheiros temporários de SAF-T
		temp_patterns = [
			"/tmp/saft_*.xml",
			"/tmp/portugal_compliance_*.tmp"
		]

		files_cleaned = 0
		for pattern in temp_patterns:
			for file_path in glob.glob(pattern):
				try:
					# Verificar se ficheiro tem mais de 1 hora
					file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
					if file_age.seconds > 3600:
						os.remove(file_path)
						files_cleaned += 1
				except Exception:
					pass

		if files_cleaned > 0:
			frappe.logger().info(f"Cleaned up {files_cleaned} temporary files")

	except Exception as e:
		frappe.log_error(f"Error cleaning up temporary files: {str(e)}")


def get_hourly_summary():
	"""
	Retorna resumo das atividades horárias

	Returns:
		dict: Resumo das atividades
	"""
	try:
		return {
			"timestamp": now(),
			"at_connectivity": frappe.cache.get("portugal_compliance_at_connectivity"),
			"system_metrics": frappe.cache.get("portugal_compliance_system_metrics"),
			"hourly_stats": frappe.cache.get("portugal_compliance_hourly_stats"),
			"status": "healthy"
		}
	except Exception:
		return {"status": "error", "timestamp": now()}
