# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Sistema de Email para Portugal Compliance
Baseado na experiência com programação.conformidade_portugal
"""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import today, now, add_days, get_datetime, cint, flt
from frappe.core.doctype.communication.email import make
import json
from datetime import datetime, timedelta


class PortugalComplianceEmailManager:
	"""
	Gerenciador de emails para Portugal Compliance
	Baseado na experiência com programação.processamento_de_documentos
	"""

	def __init__(self):
		self.email_templates = self._load_email_templates()
		self.notification_settings = self._load_notification_settings()

	def _load_email_templates(self):
		"""
		✅ Carrega templates de email para Portugal Compliance
		"""
		return {
			"series_communication_success": {
				"subject": "✅ Série Comunicada à AT com Sucesso - {series_name}",
				"template": "series_communication_success.html"
			},
			"series_communication_failed": {
				"subject": "❌ Falha na Comunicação à AT - {series_name}",
				"template": "series_communication_failed.html"
			},
			"atcud_generation_error": {
				"subject": "⚠️ Erro na Geração de ATCUD - {document_name}",
				"template": "atcud_generation_error.html"
			},
			"compliance_activation": {
				"subject": "🇵🇹 Portugal Compliance Ativado - {company_name}",
				"template": "compliance_activation.html"
			},
			"series_expiry_warning": {
				"subject": "⏰ Série Próxima do Vencimento - {series_name}",
				"template": "series_expiry_warning.html"
			},
			"daily_compliance_report": {
				"subject": "📊 Relatório Diário Portugal Compliance - {date}",
				"template": "daily_compliance_report.html"
			},
			"validation_errors": {
				"subject": "🚨 Erros de Validação Detectados - {company_name}",
				"template": "validation_errors.html"
			},
			"backup_notification": {
				"subject": "💾 Backup Portugal Compliance - {date}",
				"template": "backup_notification.html"
			}
		}

	def _load_notification_settings(self):
		"""
		✅ Carrega configurações de notificação
		"""
		return {
			"send_communication_notifications": True,
			"send_error_notifications": True,
			"send_daily_reports": False,
			"send_expiry_warnings": True,
			"send_validation_errors": True,
			"notification_recipients": self._get_default_recipients()
		}

	def _get_default_recipients(self):
		"""
		✅ Obtém destinatários padrão para notificações
		"""
		try:
			# Buscar usuários com roles relevantes
			users = frappe.db.sql("""
								  SELECT DISTINCT u.email, u.full_name
								  FROM `tabUser` u
										   JOIN `tabUserRole` ur ON u.name = ur.parent
								  WHERE ur.role IN ('System Manager', 'Accounts Manager',
													'Portugal Compliance User')
									AND u.enabled = 1
									AND u.email IS NOT NULL
									AND u.email != ''
								  """, as_dict=True)

			return [{"email": user.email, "name": user.full_name} for user in users]

		except Exception as e:
			frappe.log_error(f"Erro ao obter destinatários padrão: {str(e)}")
			return [{"email": "admin@example.com", "name": "Administrator"}]

	# ========== NOTIFICAÇÕES DE COMUNICAÇÃO AT ==========

	def send_series_communication_success(self, series_name, company, validation_code):
		"""
		✅ Envia notificação de sucesso na comunicação de série
		"""
		try:
			template_data = {
				"series_name": series_name,
				"company": company,
				"validation_code": validation_code,
				"communication_date": now(),
				"next_steps": [
					"A série está agora oficialmente registada na AT",
					"Pode começar a emitir documentos com esta série",
					"O ATCUD será gerado automaticamente para novos documentos"
				]
			}

			self._send_notification(
				"series_communication_success",
				template_data,
				recipients=self._get_company_users(company)
			)

			frappe.logger().info(f"✅ Notificação de sucesso enviada para série {series_name}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação de sucesso: {str(e)}")

	def send_series_communication_failed(self, series_name, company, error_message):
		"""
		✅ Envia notificação de falha na comunicação de série
		"""
		try:
			template_data = {
				"series_name": series_name,
				"company": company,
				"error_message": error_message,
				"failure_date": now(),
				"recommended_actions": [
					"Verificar credenciais AT da empresa",
					"Confirmar conectividade com serviços AT",
					"Tentar comunicação manual através do portal AT",
					"Contactar suporte técnico se problema persistir"
				]
			}

			self._send_notification(
				"series_communication_failed",
				template_data,
				recipients=self._get_company_users(company),
				priority="high"
			)

			frappe.logger().error(f"❌ Notificação de falha enviada para série {series_name}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação de falha: {str(e)}")

	# ========== NOTIFICAÇÕES DE ATCUD ==========

	def send_atcud_generation_error(self, document_type, document_name, company, error_details):
		"""
		✅ Envia notificação de erro na geração de ATCUD
		"""
		try:
			template_data = {
				"document_type": document_type,
				"document_name": document_name,
				"company": company,
				"error_details": error_details,
				"error_date": now(),
				"troubleshooting_steps": [
					"Verificar se série está comunicada à AT",
					"Confirmar que naming_series está configurada corretamente",
					"Verificar se sequência não ultrapassou limite máximo",
					"Tentar gerar ATCUD manualmente"
				]
			}

			self._send_notification(
				"atcud_generation_error",
				template_data,
				recipients=self._get_company_users(company),
				priority="high"
			)

			frappe.logger().error(f"⚠️ Notificação de erro ATCUD enviada para {document_name}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação de erro ATCUD: {str(e)}")

	# ========== NOTIFICAÇÕES DE COMPLIANCE ==========

	def send_compliance_activation_notification(self, company_name, series_created,
												features_enabled):
		"""
		✅ Envia notificação de ativação do compliance
		"""
		try:
			template_data = {
				"company_name": company_name,
				"activation_date": now(),
				"series_created": series_created,
				"features_enabled": features_enabled,
				"next_steps": [
					"Configurar credenciais AT para comunicação de séries",
					"Comunicar séries à AT antes de emitir documentos",
					"Testar geração de ATCUD em documentos de teste",
					"Configurar templates de impostos portugueses"
				]
			}

			self._send_notification(
				"compliance_activation",
				template_data,
				recipients=self._get_company_users(company_name)
			)

			frappe.logger().info(f"🇵🇹 Notificação de ativação enviada para {company_name}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação de ativação: {str(e)}")

	def send_series_expiry_warning(self, series_name, company, expiry_date, days_remaining):
		"""
		✅ Envia aviso de expiração de série
		"""
		try:
			urgency_level = "critical" if days_remaining <= 7 else "warning"

			template_data = {
				"series_name": series_name,
				"company": company,
				"expiry_date": expiry_date,
				"days_remaining": days_remaining,
				"urgency_level": urgency_level,
				"required_actions": [
					"Renovar série junto da AT",
					"Criar nova série para substituição",
					"Atualizar configurações no sistema",
					"Comunicar nova série antes da expiração"
				]
			}

			self._send_notification(
				"series_expiry_warning",
				template_data,
				recipients=self._get_company_users(company),
				priority=urgency_level
			)

			frappe.logger().warning(f"⏰ Aviso de expiração enviado para série {series_name}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar aviso de expiração: {str(e)}")

	# ========== RELATÓRIOS DIÁRIOS ==========

	def send_daily_compliance_report(self, report_data):
		"""
		✅ Envia relatório diário de compliance
		"""
		try:
			if not self.notification_settings.get("send_daily_reports"):
				return

			template_data = {
				"report_date": report_data.get("date", today()),
				"statistics": report_data,
				"summary": self._generate_report_summary(report_data),
				"recommendations": self._generate_recommendations(report_data)
			}

			# Enviar apenas para System Managers
			admin_recipients = [r for r in self.notification_settings["notification_recipients"]
								if self._is_system_manager(r["email"])]

			self._send_notification(
				"daily_compliance_report",
				template_data,
				recipients=admin_recipients
			)

			frappe.logger().info(
				f"📊 Relatório diário enviado para {len(admin_recipients)} destinatários")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar relatório diário: {str(e)}")

	def send_validation_errors_notification(self, company, errors_summary):
		"""
		✅ Envia notificação de erros de validação
		"""
		try:
			if not self.notification_settings.get("send_validation_errors"):
				return

			template_data = {
				"company": company,
				"detection_date": now(),
				"errors_summary": errors_summary,
				"total_errors": len(errors_summary),
				"corrective_actions": self._generate_corrective_actions(errors_summary)
			}

			self._send_notification(
				"validation_errors",
				template_data,
				recipients=self._get_company_users(company),
				priority="high"
			)

			frappe.logger().warning(f"🚨 Notificação de erros enviada para {company}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação de erros: {str(e)}")

	# ========== MÉTODOS AUXILIARES ==========

	def _send_notification(self, template_key, template_data, recipients=None, priority="normal"):
		"""
		✅ Envia notificação usando template especificado
		"""
		try:
			if not recipients:
				recipients = self.notification_settings["notification_recipients"]

			template_config = self.email_templates.get(template_key)
			if not template_config:
				frappe.log_error(f"Template não encontrado: {template_key}")
				return

			# Gerar subject com dados do template
			subject = template_config["subject"].format(**template_data)

			# Gerar conteúdo do email
			email_content = self._generate_email_content(template_key, template_data)

			# Enviar para cada destinatário
			for recipient in recipients:
				try:
					self._send_email(
						recipient["email"],
						subject,
						email_content,
						priority=priority
					)
				except Exception as e:
					frappe.log_error(f"Erro ao enviar email para {recipient['email']}: {str(e)}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar notificação {template_key}: {str(e)}")

	def _generate_email_content(self, template_key, template_data):
		"""
		✅ Gera conteúdo do email baseado no template
		"""
		try:
			# Templates HTML básicos (podem ser expandidos)
			templates = {
				"series_communication_success": self._template_series_success(template_data),
				"series_communication_failed": self._template_series_failed(template_data),
				"atcud_generation_error": self._template_atcud_error(template_data),
				"compliance_activation": self._template_compliance_activation(template_data),
				"series_expiry_warning": self._template_series_expiry(template_data),
				"daily_compliance_report": self._template_daily_report(template_data),
				"validation_errors": self._template_validation_errors(template_data)
			}

			return templates.get(template_key, self._template_default(template_data))

		except Exception as e:
			frappe.log_error(f"Erro ao gerar conteúdo do email: {str(e)}")
			return self._template_default(template_data)

	def _send_email(self, recipient_email, subject, content, priority="normal"):
		"""
		✅ Envia email usando sistema do Frappe
		"""
		try:
			frappe.sendmail(
				recipients=[recipient_email],
				subject=subject,
				message=content,
				delayed=priority != "high",
				retry=3
			)

			frappe.logger().info(f"📧 Email enviado para {recipient_email}: {subject}")

		except Exception as e:
			frappe.log_error(f"Erro ao enviar email para {recipient_email}: {str(e)}")

	def _get_company_users(self, company):
		"""
		✅ Obtém usuários relacionados com uma empresa específica
		"""
		try:
			# Buscar usuários que têm acesso à empresa
			users = frappe.db.sql("""
								  SELECT DISTINCT u.email, u.full_name
								  FROM `tabUser` u
										   JOIN `tabUserRole` ur ON u.name = ur.parent
								  WHERE ur.role IN ('Accounts Manager', 'Accounts User',
													'Portugal Compliance User')
									AND u.enabled = 1
									AND u.email IS NOT NULL
									AND u.email != ''
								  """, as_dict=True)

			if not users:
				# Fallback para destinatários padrão
				return self.notification_settings["notification_recipients"]

			return [{"email": user.email, "name": user.full_name} for user in users]

		except Exception as e:
			frappe.log_error(f"Erro ao obter usuários da empresa {company}: {str(e)}")
			return self.notification_settings["notification_recipients"]

	def _is_system_manager(self, email):
		"""
		✅ Verifica se usuário é System Manager
		"""
		try:
			return frappe.db.exists("UserRole", {
				"parent": email,
				"role": "System Manager"
			})
		except:
			return False

	# ========== TEMPLATES DE EMAIL ==========

	def _template_series_success(self, data):
		"""
		✅ Template para sucesso na comunicação de série
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">✅ Série Comunicada com Sucesso</h2>

            <p>A série <strong>{data['series_name']}</strong> foi comunicada à AT com sucesso!</p>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4>Detalhes da Comunicação:</h4>
                <ul>
                    <li><strong>Empresa:</strong> {data['company']}</li>
                    <li><strong>Código de Validação:</strong> {data['validation_code']}</li>
                    <li><strong>Data:</strong> {data['communication_date']}</li>
                </ul>
            </div>

            <h4>Próximos Passos:</h4>
            <ul>
                {''.join([f"<li>{step}</li>" for step in data['next_steps']])}
            </ul>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_series_failed(self, data):
		"""
		✅ Template para falha na comunicação de série
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">❌ Falha na Comunicação à AT</h2>

            <p>A comunicação da série <strong>{data['series_name']}</strong> à AT falhou.</p>

            <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h4>Detalhes do Erro:</h4>
                <p><strong>Empresa:</strong> {data['company']}</p>
                <p><strong>Data:</strong> {data['failure_date']}</p>
                <p><strong>Erro:</strong> {data['error_message']}</p>
            </div>

            <h4>Ações Recomendadas:</h4>
            <ul>
                {''.join([f"<li>{action}</li>" for action in data['recommended_actions']])}
            </ul>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_atcud_error(self, data):
		"""
		✅ Template para erro na geração de ATCUD
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc107;">⚠️ Erro na Geração de ATCUD</h2>

            <p>Erro ao gerar ATCUD para o documento <strong>{data['document_name']}</strong>.</p>

            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4>Detalhes:</h4>
                <ul>
                    <li><strong>Tipo:</strong> {data['document_type']}</li>
                    <li><strong>Documento:</strong> {data['document_name']}</li>
                    <li><strong>Empresa:</strong> {data['company']}</li>
                    <li><strong>Data:</strong> {data['error_date']}</li>
                    <li><strong>Erro:</strong> {data['error_details']}</li>
                </ul>
            </div>

            <h4>Passos para Resolução:</h4>
            <ol>
                {''.join([f"<li>{step}</li>" for step in data['troubleshooting_steps']])}
            </ol>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_compliance_activation(self, data):
		"""
		✅ Template para ativação do compliance
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">🇵🇹 Portugal Compliance Ativado</h2>

            <p>O Portugal Compliance foi ativado com sucesso para <strong>{data['company_name']}</strong>!</p>

            <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
                <h4>Resumo da Ativação:</h4>
                <ul>
                    <li><strong>Data:</strong> {data['activation_date']}</li>
                    <li><strong>Séries Criadas:</strong> {data['series_created']}</li>
                    <li><strong>Funcionalidades:</strong> {', '.join(data['features_enabled'])}</li>
                </ul>
            </div>

            <h4>Próximos Passos:</h4>
            <ol>
                {''.join([f"<li>{step}</li>" for step in data['next_steps']])}
            </ol>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_series_expiry(self, data):
		"""
		✅ Template para aviso de expiração de série
		"""
		urgency_color = "#dc3545" if data['urgency_level'] == "critical" else "#ffc107"

		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: {urgency_color};">⏰ Série Próxima do Vencimento</h2>

            <p>A série <strong>{data['series_name']}</strong> expira em <strong>{data['days_remaining']} dias</strong>!</p>

            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {urgency_color};">
                <h4>Detalhes:</h4>
                <ul>
                    <li><strong>Série:</strong> {data['series_name']}</li>
                    <li><strong>Empresa:</strong> {data['company']}</li>
                    <li><strong>Data de Expiração:</strong> {data['expiry_date']}</li>
                    <li><strong>Dias Restantes:</strong> {data['days_remaining']}</li>
                </ul>
            </div>

            <h4>Ações Necessárias:</h4>
            <ol>
                {''.join([f"<li>{action}</li>" for action in data['required_actions']])}
            </ol>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_daily_report(self, data):
		"""
		✅ Template para relatório diário
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">📊 Relatório Diário Portugal Compliance</h2>

            <p>Relatório de atividades do dia <strong>{data['report_date']}</strong>.</p>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4>Estatísticas do Dia:</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td><strong>ATCUDs Gerados:</strong></td><td>{data['statistics'].get('atcud_generated', 0)}</td></tr>
                    <tr><td><strong>Séries Comunicadas:</strong></td><td>{data['statistics'].get('series_communicated', 0)}</td></tr>
                    <tr><td><strong>Documentos Processados:</strong></td><td>{data['statistics'].get('documents_processed', 0)}</td></tr>
                    <tr><td><strong>Erros Registados:</strong></td><td>{data['statistics'].get('errors_logged', 0)}</td></tr>
                </table>
            </div>

            <h4>Resumo:</h4>
            <p>{data['summary']}</p>

            <h4>Recomendações:</h4>
            <ul>
                {''.join([f"<li>{rec}</li>" for rec in data['recommendations']])}
            </ul>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_validation_errors(self, data):
		"""
		✅ Template para erros de validação
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">🚨 Erros de Validação Detectados</h2>

            <p>Foram detectados <strong>{data['total_errors']}</strong> erros de validação na empresa <strong>{data['company']}</strong>.</p>

            <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h4>Resumo dos Erros:</h4>
                <ul>
                    {''.join([f"<li>{error}</li>" for error in data['errors_summary']])}
                </ul>
            </div>

            <h4>Ações Corretivas:</h4>
            <ol>
                {''.join([f"<li>{action}</li>" for action in data['corrective_actions']])}
            </ol>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	def _template_default(self, data):
		"""
		✅ Template padrão para notificações
		"""
		return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">Portugal Compliance</h2>

            <p>Notificação do sistema Portugal Compliance.</p>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            </div>

            <p style="color: #6c757d; font-size: 12px;">
                Esta é uma notificação automática do Portugal Compliance.
            </p>
        </div>
        """

	# ========== MÉTODOS DE ANÁLISE ==========

	def _generate_report_summary(self, report_data):
		"""
		✅ Gera resumo do relatório
		"""
		try:
			total_activity = (report_data.get('atcud_generated', 0) +
							  report_data.get('series_communicated', 0) +
							  report_data.get('documents_processed', 0))

			if total_activity == 0:
				return "Dia sem atividade significativa no sistema."
			elif report_data.get('errors_logged', 0) > 0:
				return f"Dia com atividade normal mas {report_data['errors_logged']} erros registados."
			else:
				return f"Dia com atividade normal. Total de {total_activity} operações realizadas."

		except Exception:
			return "Resumo não disponível."

	def _generate_recommendations(self, report_data):
		"""
		✅ Gera recomendações baseadas no relatório
		"""
		recommendations = []

		try:
			if report_data.get('errors_logged', 0) > 5:
				recommendations.append("Investigar causa dos erros frequentes")

			if report_data.get('series_communicated', 0) == 0 and report_data.get(
				'atcud_generated', 0) > 0:
				recommendations.append("Comunicar séries pendentes à AT")

			if report_data.get('documents_processed', 0) > 100:
				recommendations.append("Considerar otimização de performance")

			if not recommendations:
				recommendations.append("Sistema funcionando normalmente")

			return recommendations

		except Exception:
			return ["Recomendações não disponíveis"]

	def _generate_corrective_actions(self, errors_summary):
		"""
		✅ Gera ações corretivas baseadas nos erros
		"""
		actions = []

		try:
			for error in errors_summary:
				if "naming_series" in error.lower():
					actions.append("Verificar configuração de naming series")
				elif "atcud" in error.lower():
					actions.append("Verificar geração de ATCUD")
				elif "communication" in error.lower():
					actions.append("Verificar comunicação com AT")

			if not actions:
				actions.append("Contactar suporte técnico")

			return list(set(actions))  # Remover duplicados

		except Exception:
			return ["Contactar suporte técnico"]


# ========== INSTÂNCIA GLOBAL ==========

# ✅ Instância global para uso em hooks e APIs
email_manager = PortugalComplianceEmailManager()


# ========== FUNÇÕES GLOBAIS PARA HOOKS ==========

def send_series_communication_notification(series_name, company, success, details):
	"""
	✅ Função global para notificações de comunicação de série
	"""
	try:
		if success:
			email_manager.send_series_communication_success(
				series_name, company, details.get('validation_code')
			)
		else:
			email_manager.send_series_communication_failed(
				series_name, company, details.get('error_message')
			)
	except Exception as e:
		frappe.log_error(f"Erro ao enviar notificação de comunicação: {str(e)}")


def send_atcud_error_notification(document_type, document_name, company, error_details):
	"""
	✅ Função global para notificações de erro ATCUD
	"""
	try:
		email_manager.send_atcud_generation_error(
			document_type, document_name, company, error_details
		)
	except Exception as e:
		frappe.log_error(f"Erro ao enviar notificação de erro ATCUD: {str(e)}")


def send_compliance_activation_notification(company_name, series_created, features_enabled):
	"""
	✅ Função global para notificações de ativação
	"""
	try:
		email_manager.send_compliance_activation_notification(
			company_name, series_created, features_enabled
		)
	except Exception as e:
		frappe.log_error(f"Erro ao enviar notificação de ativação: {str(e)}")


def send_daily_report(report_data):
	"""
	✅ Função global para relatório diário
	"""
	try:
		email_manager.send_daily_compliance_report(report_data)
	except Exception as e:
		frappe.log_error(f"Erro ao enviar relatório diário: {str(e)}")


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
@rate_limit(limit=5, seconds=3600)
def test_email_notification(template_key, recipient_email):
	"""
	✅ API para testar notificações de email

	Envia um email real a partir da conta de correio do site - restrito
	a System Manager para nao ser usado para abusar da reputacao de
	envio do site (spam/teste de infraestrutura de phishing).
	"""
	try:
		if "System Manager" not in frappe.get_roles():
			return {"success": False, "error": "Apenas System Manager pode enviar emails de teste"}

		test_data = {
			"series_name": "FT2025DSY",
			"company": "Empresa Teste",
			"validation_code": "TEST123",
			"communication_date": now(),
			"next_steps": ["Teste concluído com sucesso"]
		}

		email_manager._send_notification(
			template_key,
			test_data,
			recipients=[{"email": recipient_email, "name": "Teste"}]
		)

		return {"success": True, "message": "Email de teste enviado"}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_notification_settings(settings):
	"""
	✅ API para atualizar configurações de notificação

	Muta um objeto de configuracao partilhado por todo o site -
	restrito a System Manager.
	"""
	try:
		if "System Manager" not in frappe.get_roles():
			return {"success": False, "error": "Apenas System Manager pode alterar estas configurações"}

		if isinstance(settings, str):
			settings = json.loads(settings)

		email_manager.notification_settings.update(settings)

		return {"success": True, "message": "Configurações atualizadas"}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_notification_settings():
	"""
	✅ API para obter configurações de notificação
	"""
	try:
		return {
			"success": True,
			"settings": email_manager.notification_settings
		}
	except Exception as e:
		return {"success": False, "error": str(e)}


# ========== LOG DE INICIALIZAÇÃO ==========
frappe.logger().info("Portugal Compliance Email System loaded - Version 2.0.0")
