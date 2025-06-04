# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, now, cint, flt
from datetime import datetime, timedelta


def get_data():
	"""
	Retorna dados do dashboard para Company
	"""
	return {
		"heatmap": True,
		"heatmap_message": _(
			"This is based on transactions against this Company. See timeline below for details"),
		"fieldname": "company",
		"non_standard_fieldnames": {
			"Payment Entry": "company",
			"Journal Entry": "company",
			"Asset": "company",
			"Stock Entry": "company",
			"Portugal Series Configuration": "company",
			"ATCUD Log": "company"
		},
		"dynamic_links": {
			"company": ["Company", "company"]
		},
		"transactions": [
			{
				"label": _("Accounting"),
				"items": ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"]
			},
			{
				"label": _("Stock"),
				"items": ["Delivery Note", "Purchase Receipt", "Stock Entry"]
			},
			{
				"label": _("Portugal Compliance"),
				"items": ["Portugal Series Configuration", "ATCUD Log", "SAF-T Export Log"]
			},
			{
				"label": _("Assets"),
				"items": ["Asset"]
			}
		]
	}


class CompanyDashboard:
	"""
	Dashboard para Company no Portugal Compliance
	"""

	def __init__(self, company_name):
		self.company_name = company_name

	def get_context(self):
		"""Retorna dados de contexto para o dashboard"""
		context = {}
		context['company'] = self.company_name
		context['compliance_status'] = self.get_compliance_status()
		context['pending_series'] = self.get_pending_series_count()
		context['recent_atcud_logs'] = self.get_recent_atcud_logs()
		context['alerts'] = self.get_alerts()
		context['statistics'] = self.get_statistics()
		context['series_summary'] = self.get_series_summary()
		context['monthly_trends'] = self.get_monthly_trends()
		return context

	def get_compliance_status(self):
		"""Verifica se a empresa está em compliance"""
		try:
			company = frappe.get_doc('Company', self.company_name)

			if not company.get('portugal_compliance_enabled'):
				return {
					'status': 'disabled',
					'message': _('Portugal Compliance not enabled'),
					'color': 'gray'
				}

			# Verificar se tem NIF
			if not company.tax_id:
				return {
					'status': 'non_compliant',
					'message': _('Missing Tax ID (NIF)'),
					'color': 'red'
				}

			# Verificar séries não comunicadas
			pending_series = self.get_pending_series_count()
			if pending_series > 0:
				return {
					'status': 'warning',
					'message': _('Has {0} pending series communications').format(pending_series),
					'color': 'orange'
				}

			return {
				'status': 'compliant',
				'message': _('Fully Compliant'),
				'color': 'green'
			}

		except Exception as e:
			frappe.log_error(f"Error getting compliance status: {str(e)}")
			return {
				'status': 'error',
				'message': _('Error checking compliance'),
				'color': 'red'
			}

	def get_pending_series_count(self):
		"""Conta séries pendentes de comunicação"""
		try:
			count = frappe.db.count('Portugal Series Configuration', {
				'company': self.company_name,
				'is_communicated': 0,
				'is_active': 1
			})
			return count
		except Exception:
			return 0

	def get_recent_atcud_logs(self):
		"""Obtém logs ATCUD recentes da empresa"""
		try:
			logs = frappe.db.get_all('ATCUD Log',
									 filters={'company': self.company_name},
									 fields=['name', 'atcud_code', 'document_type',
											 'document_name', 'creation', 'validation_status'],
									 order_by='creation desc',
									 limit=10
									 )

			# Formatar dados
			for log in logs:
				log['creation_formatted'] = frappe.utils.format_datetime(log['creation'])
				log['status_color'] = 'green' if log.get('validation_status') == 'Valid' else 'red'

			return logs
		except Exception as e:
			frappe.log_error(f"Error getting recent ATCUD logs: {str(e)}")
			return []

	def get_alerts(self):
		"""Obtém alertas relacionados com a empresa"""
		alerts = []

		try:
			# Verificar certificados a expirar
			company = frappe.get_doc('Company', self.company_name)

			if company.get('certificate_expiry_date'):
				expiry_date = getdate(company.certificate_expiry_date)
				days_to_expiry = (expiry_date - getdate()).days

				if days_to_expiry <= 30:
					alerts.append({
						'type': 'certificate_expiry',
						'message': _('AT Certificate expires in {0} days').format(days_to_expiry),
						'severity': 'critical' if days_to_expiry <= 7 else 'warning',
						'action': _('Renew Certificate')
					})

			# Verificar séries não comunicadas há muito tempo
			old_series = frappe.db.count('Portugal Series Configuration', {
				'company': self.company_name,
				'is_communicated': 0,
				'is_active': 1,
				'creation': ['<', add_days(today(), -7)]
			})

			if old_series > 0:
				alerts.append({
					'type': 'old_series',
					'message': _('Has {0} series pending communication for over 7 days').format(
						old_series),
					'severity': 'warning',
					'action': _('Communicate Series')
				})

			# Verificar erros recentes
			recent_errors = frappe.db.count('Error Log', {
				'creation': ['>=', add_days(today(), -1)],
				'error': ['like', f'%{self.company_name}%']
			})

			if recent_errors > 5:
				alerts.append({
					'type': 'recent_errors',
					'message': _('High error rate: {0} errors in last 24 hours').format(
						recent_errors),
					'severity': 'warning',
					'action': _('Check Error Logs')
				})

		except Exception as e:
			frappe.log_error(f"Error getting alerts: {str(e)}")
			alerts.append({
				'type': 'system_error',
				'message': _('Error loading alerts'),
				'severity': 'error',
				'action': _('Check System')
			})

		return alerts

	def get_statistics(self):
		"""Obtém estatísticas da empresa"""
		try:
			stats = {
				'total_series': frappe.db.count('Portugal Series Configuration', {
					'company': self.company_name
				}),
				'active_series': frappe.db.count('Portugal Series Configuration', {
					'company': self.company_name,
					'is_active': 1
				}),
				'communicated_series': frappe.db.count('Portugal Series Configuration', {
					'company': self.company_name,
					'is_communicated': 1
				}),
				'total_atcud_generated': frappe.db.count('ATCUD Log', {
					'company': self.company_name
				}),
				'atcud_this_month': frappe.db.count('ATCUD Log', {
					'company': self.company_name,
					'creation': ['>=', frappe.utils.get_first_day(today())]
				}),
				'documents_this_month': self.get_documents_count_this_month()
			}

			# Calcular percentagens
			if stats['total_series'] > 0:
				stats['communication_percentage'] = round(
					(stats['communicated_series'] / stats['total_series']) * 100, 1)
			else:
				stats['communication_percentage'] = 0

			return stats

		except Exception as e:
			frappe.log_error(f"Error getting statistics: {str(e)}")
			return {}

	def get_documents_count_this_month(self):
		"""Conta documentos processados este mês"""
		try:
			first_day = frappe.utils.get_first_day(today())

			document_types = ['Sales Invoice', 'Purchase Invoice', 'Payment Entry',
							  'Delivery Note']
			total_count = 0

			for doc_type in document_types:
				if frappe.db.table_exists(f'tab{doc_type}'):
					count = frappe.db.count(doc_type, {
						'company': self.company_name,
						'posting_date': ['>=', first_day],
						'docstatus': 1
					})
					total_count += count

			return total_count

		except Exception as e:
			frappe.log_error(f"Error counting documents this month: {str(e)}")
			return 0

	def get_series_summary(self):
		"""Obtém resumo das séries"""
		try:
			series_data = frappe.db.get_all('Portugal Series Configuration',
											filters={'company': self.company_name},
											fields=['name', 'series_name', 'document_type',
													'is_active', 'is_communicated',
													'current_number', 'total_documents_issued'],
											order_by='document_type, series_name'
											)

			# Agrupar por tipo de documento
			grouped_series = {}
			for series in series_data:
				doc_type = series['document_type']
				if doc_type not in grouped_series:
					grouped_series[doc_type] = []

				series['status'] = self.get_series_status(series)
				grouped_series[doc_type].append(series)

			return grouped_series

		except Exception as e:
			frappe.log_error(f"Error getting series summary: {str(e)}")
			return {}

	def get_series_status(self, series):
		"""Determina status da série"""
		if not series['is_active']:
			return {'status': 'inactive', 'color': 'gray', 'label': _('Inactive')}
		elif not series['is_communicated']:
			return {'status': 'pending', 'color': 'orange', 'label': _('Pending Communication')}
		else:
			return {'status': 'active', 'color': 'green', 'label': _('Active')}

	def get_monthly_trends(self):
		"""Obtém tendências mensais"""
		try:
			# Últimos 6 meses
			trends = []

			for i in range(6):
				month_start = frappe.utils.get_first_day(add_days(today(), -30 * i))
				month_end = frappe.utils.get_last_day(month_start)

				atcud_count = frappe.db.count('ATCUD Log', {
					'company': self.company_name,
					'creation': ['between', [month_start, month_end]]
				})

				trends.append({
					'month': month_start.strftime('%b %Y'),
					'atcud_count': atcud_count,
					'month_start': month_start
				})

			# Ordenar por data
			trends.sort(key=lambda x: x['month_start'])

			return trends

		except Exception as e:
			frappe.log_error(f"Error getting monthly trends: {str(e)}")
			return []


@frappe.whitelist()
def get_company_dashboard_data(company):
	"""
	Endpoint para obter dados do dashboard da empresa
	"""
	try:
		dashboard = CompanyDashboard(company)
		return dashboard.get_context()
	except Exception as e:
		frappe.log_error(f"Error getting company dashboard data: {str(e)}")
		return {'error': str(e)}


@frappe.whitelist()
def get_compliance_summary(company):
	"""
	Endpoint para obter resumo de compliance
	"""
	try:
		dashboard = CompanyDashboard(company)
		return {
			'compliance_status': dashboard.get_compliance_status(),
			'statistics': dashboard.get_statistics(),
			'alerts': dashboard.get_alerts()
		}
	except Exception as e:
		frappe.log_error(f"Error getting compliance summary: {str(e)}")
		return {'error': str(e)}


@frappe.whitelist()
def refresh_dashboard_cache(company):
	"""
	Limpa cache do dashboard da empresa
	"""
	try:
		cache_keys = [
			f'company_dashboard_{company}',
			f'compliance_status_{company}',
			f'series_summary_{company}'
		]

		for key in cache_keys:
			frappe.cache.delete(key)

		return {'status': 'success', 'message': _('Dashboard cache refreshed')}
	except Exception as e:
		frappe.log_error(f"Error refreshing dashboard cache: {str(e)}")
		return {'status': 'error', 'message': str(e)}


# Adicionar estas funções ao final do ficheiro

def get_dashboard_data(data=None):
	"""
	Função principal para compatibilidade com sistema de dashboards do Frappe
	"""
	return get_data()


@frappe.whitelist()
def get_dashboard_chart_data(chart_name, company=None, from_date=None, to_date=None):
	"""
	Função para obter dados de gráficos do dashboard
	"""
	try:
		if not company:
			company = frappe.defaults.get_user_default("Company")

		dashboard = CompanyDashboard(company)

		if chart_name == "compliance_trends":
			return dashboard.get_monthly_trends()
		elif chart_name == "series_summary":
			return dashboard.get_series_summary()
		elif chart_name == "atcud_statistics":
			recent_logs = dashboard.get_recent_atcud_logs()
			return {"data": recent_logs}
		else:
			return {"data": []}

	except Exception as e:
		frappe.log_error(f"Error getting dashboard chart data: {str(e)}")
		return {"data": []}


# Função de compatibilidade
def get_data():
	"""
	Retorna dados do dashboard para Company (função original)
	"""
	return {
		"heatmap": True,
		"heatmap_message": _(
			"This is based on transactions against this Company. See timeline below for details"),
		"fieldname": "company",
		"non_standard_fieldnames": {
			"Payment Entry": "company",
			"Journal Entry": "company",
			"Asset": "company",
			"Stock Entry": "company",
			"Portugal Series Configuration": "company",
			"ATCUD Log": "company"
		},
		"dynamic_links": {
			"company": ["Company", "company"]
		},
		"transactions": [
			{
				"label": _("Accounting"),
				"items": ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"]
			},
			{
				"label": _("Stock"),
				"items": ["Delivery Note", "Purchase Receipt", "Stock Entry"]
			},
			{
				"label": _("Portugal Compliance"),
				"items": ["Portugal Series Configuration", "ATCUD Log", "SAF-T Export Log"]
			},
			{
				"label": _("Assets"),
				"items": ["Asset"]
			}
		]
	}
