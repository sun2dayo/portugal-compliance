# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, now, cint, flt, formatdate
from datetime import datetime, timedelta


def get_data():
	"""
	Retorna dados do dashboard para Sales Invoice
	"""
	return {
		"heatmap": True,
		"heatmap_message": _(
			"This is based on the posting date of the Sales Invoice. See timeline below for details"),
		"fieldname": "customer",
		"non_standard_fieldnames": {
			"Payment Entry": "party",
			"Delivery Note": "customer",
			"Sales Order": "customer",
			"ATCUD Log": "customer",
			"Portugal Series Configuration": "company"
		},
		"dynamic_links": {
			"customer": ["Customer", "customer"],
			"company": ["Company", "company"]
		},
		"transactions": [
			{
				"label": _("Pre Sales"),
				"items": ["Quotation", "Sales Order"]
			},
			{
				"label": _("Delivery"),
				"items": ["Delivery Note", "Sales Invoice"]
			},
			{
				"label": _("Payments"),
				"items": ["Payment Entry", "Payment Request"]
			},
			{
				"label": _("Portugal Compliance"),
				"items": ["ATCUD Log", "Portugal Series Configuration"]
			},
			{
				"label": _("Returns"),
				"items": ["Sales Invoice"]
			}
		]
	}


class SalesInvoiceDashboard:
	"""
	Dashboard para Sales Invoice no Portugal Compliance
	"""

	def __init__(self, sales_invoice_name):
		self.sales_invoice_name = sales_invoice_name
		self.sales_invoice = None

	def get_context(self):
		"""Retorna dados de contexto para o dashboard"""
		try:
			self.sales_invoice = frappe.get_doc('Sales Invoice', self.sales_invoice_name)

			context = {}
			context['invoice'] = self.sales_invoice_name
			context['compliance_status'] = self.get_compliance_status()
			context['atcud_info'] = self.get_atcud_info()
			context['series_info'] = self.get_series_info()
			context['tax_compliance'] = self.get_tax_compliance()
			context['customer_info'] = self.get_customer_compliance_info()
			context['related_documents'] = self.get_related_documents()
			context['compliance_alerts'] = self.get_compliance_alerts()
			context['saft_status'] = self.get_saft_status()

			return context

		except Exception as e:
			frappe.log_error(f"Error getting Sales Invoice dashboard context: {str(e)}")
			return {'error': str(e)}

	def get_compliance_status(self):
		"""Verifica status de compliance da fatura"""
		try:
			if not self.sales_invoice:
				return {'status': 'error', 'message': _('Invoice not found')}

			# Verificar se empresa tem compliance ativo
			company_compliance = frappe.db.get_value('Company', self.sales_invoice.company,
													 'portugal_compliance_enabled')

			if not company_compliance:
				return {
					'status': 'not_applicable',
					'message': _('Portugal Compliance not enabled for this company'),
					'color': 'gray'
				}

			# Verificar ATCUD
			if not getattr(self.sales_invoice, 'atcud_code', None):
				return {
					'status': 'non_compliant',
					'message': _('Missing ATCUD code'),
					'color': 'red',
					'action': _('Generate ATCUD')
				}

			# Verificar série portuguesa
			series_info = self.get_series_info()
			if not series_info.get('is_communicated'):
				return {
					'status': 'warning',
					'message': _('Series not communicated with AT'),
					'color': 'orange',
					'action': _('Communicate Series')
				}

			# Verificar NIF do cliente
			customer_nif = frappe.db.get_value('Customer', self.sales_invoice.customer, 'tax_id')
			if self.is_portuguese_customer() and not customer_nif:
				return {
					'status': 'warning',
					'message': _('Portuguese customer without NIF'),
					'color': 'orange',
					'action': _('Update Customer NIF')
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

	def get_atcud_info(self):
		"""Obtém informações do ATCUD"""
		try:
			atcud_code = getattr(self.sales_invoice, 'atcud_code', None)

			if not atcud_code:
				return {
					'has_atcud': False,
					'message': _('No ATCUD code assigned'),
					'status': 'missing'
				}

			# Obter log do ATCUD
			atcud_log = frappe.db.get_value('ATCUD Log', {
				'atcud_code': atcud_code,
				'document_name': self.sales_invoice_name
			}, ['name', 'validation_status', 'generation_method', 'creation'], as_dict=True)

			if atcud_log:
				return {
					'has_atcud': True,
					'atcud_code': atcud_code,
					'validation_status': atcud_log.validation_status,
					'generation_method': atcud_log.generation_method,
					'generated_on': formatdate(atcud_log.creation),
					'log_name': atcud_log.name,
					'status': 'valid' if atcud_log.validation_status == 'Valid' else 'invalid'
				}
			else:
				return {
					'has_atcud': True,
					'atcud_code': atcud_code,
					'status': 'no_log',
					'message': _('ATCUD exists but no log found')
				}

		except Exception as e:
			frappe.log_error(f"Error getting ATCUD info: {str(e)}")
			return {'has_atcud': False, 'error': str(e)}

	def get_series_info(self):
		"""Obtém informações da série portuguesa"""
		try:
			series_name = getattr(self.sales_invoice, 'naming_series', None)

			if not series_name:
				return {'has_series': False, 'message': _('No naming series found')}

			# Procurar configuração de série portuguesa
			series_config = frappe.db.get_value('Portugal Series Configuration', {
				'series_name': series_name,
				'company': self.sales_invoice.company,
				'document_type': 'Sales Invoice'
			}, ['name', 'is_communicated', 'communication_date', 'validation_code',
				'current_number', 'total_documents_issued'], as_dict=True)

			if series_config:
				return {
					'has_series': True,
					'series_name': series_name,
					'is_communicated': series_config.is_communicated,
					'communication_date': formatdate(
						series_config.communication_date) if series_config.communication_date else None,
					'validation_code': series_config.validation_code,
					'current_number': series_config.current_number,
					'total_issued': series_config.total_documents_issued,
					'config_name': series_config.name
				}
			else:
				return {
					'has_series': False,
					'series_name': series_name,
					'message': _('No Portugal series configuration found')
				}

		except Exception as e:
			frappe.log_error(f"Error getting series info: {str(e)}")
			return {'has_series': False, 'error': str(e)}

	def get_tax_compliance(self):
		"""Verifica compliance fiscal"""
		try:
			tax_info = {
				'has_taxes': bool(self.sales_invoice.taxes),
				'total_tax_amount': 0,
				'tax_breakdown': [],
				'compliance_issues': []
			}

			if self.sales_invoice.taxes:
				valid_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

				for tax in self.sales_invoice.taxes:
					tax_rate = tax.rate if hasattr(tax, 'rate') else 0
					tax_amount = tax.tax_amount if hasattr(tax, 'tax_amount') else 0

					tax_info['tax_breakdown'].append({
						'account': tax.account_head,
						'rate': tax_rate,
						'amount': tax_amount
					})

					tax_info['total_tax_amount'] += tax_amount

					# Verificar se taxa é válida
					if tax_rate not in valid_rates:
						tax_info['compliance_issues'].append(
							_('Invalid VAT rate: {0}%').format(tax_rate)
						)

			# Verificar tipo de fatura
			if self.is_intracom_invoice():
				if tax_info['total_tax_amount'] > 0:
					tax_info['compliance_issues'].append(
						_('Intra-community invoice should have 0% VAT')
					)

			if self.is_export_invoice():
				if tax_info['total_tax_amount'] > 0:
					tax_info['compliance_issues'].append(
						_('Export invoice should have 0% VAT')
					)

			return tax_info

		except Exception as e:
			frappe.log_error(f"Error getting tax compliance: {str(e)}")
			return {'error': str(e)}

	def is_portuguese_customer(self):
		"""Verifica se cliente é português"""
		try:
			customer_country = frappe.db.get_value('Address', {
				'link_name': self.sales_invoice.customer,
				'link_doctype': 'Customer',
				'is_primary_address': 1
			}, 'country')

			return customer_country == 'Portugal'
		except Exception:
			return False

	def is_intracom_invoice(self):
		"""Verifica se é fatura intracomunitária"""
		try:
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Romania", "Slovakia", "Slovenia",
							"Spain", "Sweden"]

			customer_country = frappe.db.get_value('Address', {
				'link_name': self.sales_invoice.customer,
				'link_doctype': 'Customer',
				'is_primary_address': 1
			}, 'country')

			return customer_country in eu_countries and customer_country != 'Portugal'
		except Exception:
			return False

	def is_export_invoice(self):
		"""Verifica se é fatura de exportação"""
		try:
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
							"Slovenia", "Spain", "Sweden"]

			customer_country = frappe.db.get_value('Address', {
				'link_name': self.sales_invoice.customer,
				'link_doctype': 'Customer',
				'is_primary_address': 1
			}, 'country')

			return customer_country and customer_country not in eu_countries
		except Exception:
			return False

	def get_customer_compliance_info(self):
		"""Obtém informações de compliance do cliente"""
		try:
			customer_info = {
				'customer_name': self.sales_invoice.customer_name,
				'is_portuguese': self.is_portuguese_customer(),
				'has_nif': False,
				'nif_valid': False,
				'customer_type': 'domestic'
			}

			# Obter NIF do cliente
			customer_nif = frappe.db.get_value('Customer', self.sales_invoice.customer, 'tax_id')

			if customer_nif:
				customer_info['has_nif'] = True
				customer_info['nif'] = customer_nif

				if customer_info['is_portuguese']:
					customer_info['nif_valid'] = self.validate_portuguese_nif(customer_nif)

			# Determinar tipo de cliente
			if self.is_intracom_invoice():
				customer_info['customer_type'] = 'intracom'
			elif self.is_export_invoice():
				customer_info['customer_type'] = 'export'

			return customer_info

		except Exception as e:
			frappe.log_error(f"Error getting customer compliance info: {str(e)}")
			return {'error': str(e)}

	def validate_portuguese_nif(self, nif):
		"""Valida NIF português"""
		try:
			if not nif:
				return False

			import re
			nif = re.sub(r'[^\d]', '', str(nif))

			if len(nif) != 9:
				return False

			if nif[0] not in '123456789':
				return False

			check_sum = 0
			for i in range(8):
				check_sum += int(nif[i]) * (9 - i)

			remainder = check_sum % 11
			check_digit = 0 if remainder < 2 else 11 - remainder

			return int(nif[8]) == check_digit
		except Exception:
			return False

	def get_related_documents(self):
		"""Obtém documentos relacionados"""
		try:
			related = {
				'delivery_notes': [],
				'payment_entries': [],
				'return_invoices': [],
				'sales_orders': []
			}

			# Delivery Notes
			delivery_notes = frappe.db.get_all('Delivery Note Item', {
				'against_sales_invoice': self.sales_invoice_name
			}, ['parent'], distinct=True)

			for dn in delivery_notes:
				dn_doc = frappe.db.get_value('Delivery Note', dn.parent,
											 ['name', 'posting_date', 'atcud_code'], as_dict=True)
				if dn_doc:
					related['delivery_notes'].append(dn_doc)

			# Payment Entries
			payment_entries = frappe.db.get_all('Payment Entry Reference', {
				'reference_name': self.sales_invoice_name,
				'reference_doctype': 'Sales Invoice'
			}, ['parent'])

			for pe in payment_entries:
				pe_doc = frappe.db.get_value('Payment Entry', pe.parent,
											 ['name', 'posting_date', 'paid_amount', 'atcud_code'],
											 as_dict=True)
				if pe_doc:
					related['payment_entries'].append(pe_doc)

			# Return Invoices
			if getattr(self.sales_invoice, 'is_return', False):
				return_against = getattr(self.sales_invoice, 'return_against', None)
				if return_against:
					original_doc = frappe.db.get_value('Sales Invoice', return_against,
													   ['name', 'posting_date', 'grand_total',
														'atcud_code'], as_dict=True)
					if original_doc:
						related['original_invoice'] = original_doc

			return related

		except Exception as e:
			frappe.log_error(f"Error getting related documents: {str(e)}")
			return {}

	def get_compliance_alerts(self):
		"""Obtém alertas de compliance"""
		alerts = []

		try:
			# Verificar ATCUD
			if not getattr(self.sales_invoice, 'atcud_code', None):
				alerts.append({
					'type': 'missing_atcud',
					'message': _('Missing ATCUD code'),
					'severity': 'critical',
					'action': _('Generate ATCUD')
				})

			# Verificar série
			series_info = self.get_series_info()
			if series_info.get('has_series') and not series_info.get('is_communicated'):
				alerts.append({
					'type': 'series_not_communicated',
					'message': _('Series not communicated with AT'),
					'severity': 'warning',
					'action': _('Communicate Series')
				})

			# Verificar NIF do cliente português
			customer_info = self.get_customer_compliance_info()
			if customer_info.get('is_portuguese') and not customer_info.get('has_nif'):
				alerts.append({
					'type': 'missing_customer_nif',
					'message': _('Portuguese customer without NIF'),
					'severity': 'warning',
					'action': _('Update Customer NIF')
				})

			# Verificar fatura de valor alto
			if self.sales_invoice.grand_total > 50000:
				alerts.append({
					'type': 'high_value_invoice',
					'message': _('High value invoice (>€50,000)'),
					'severity': 'info',
					'action': _('Verify Documentation')
				})

			# Verificar compliance fiscal
			tax_compliance = self.get_tax_compliance()
			if tax_compliance.get('compliance_issues'):
				for issue in tax_compliance['compliance_issues']:
					alerts.append({
						'type': 'tax_compliance',
						'message': issue,
						'severity': 'warning',
						'action': _('Review Tax Configuration')
					})

		except Exception as e:
			frappe.log_error(f"Error getting compliance alerts: {str(e)}")
			alerts.append({
				'type': 'system_error',
				'message': _('Error checking compliance'),
				'severity': 'error'
			})

		return alerts

	def get_saft_status(self):
		"""Verifica status SAF-T"""
		try:
			# Verificar se fatura foi incluída em export SAF-T
			invoice_month = self.sales_invoice.posting_date.strftime('%Y-%m')

			saft_exports = frappe.db.get_all('SAF-T Export Log', {
				'company': self.sales_invoice.company,
				'period_start': ['<=', self.sales_invoice.posting_date],
				'period_end': ['>=', self.sales_invoice.posting_date],
				'status': 'Completed'
			}, ['name', 'export_date', 'file_name'])

			if saft_exports:
				return {
					'included_in_saft': True,
					'exports': saft_exports,
					'latest_export': saft_exports[-1] if saft_exports else None
				}
			else:
				return {
					'included_in_saft': False,
					'message': _('Not yet included in SAF-T export'),
					'action': _('Generate SAF-T for period')
				}

		except Exception as e:
			frappe.log_error(f"Error getting SAF-T status: {str(e)}")
			return {'error': str(e)}


@frappe.whitelist()
def get_sales_invoice_dashboard_data(sales_invoice):
	"""
	Endpoint para obter dados do dashboard da fatura
	"""
	try:
		dashboard = SalesInvoiceDashboard(sales_invoice)
		return dashboard.get_context()
	except Exception as e:
		frappe.log_error(f"Error getting sales invoice dashboard data: {str(e)}")
		return {'error': str(e)}


@frappe.whitelist()
def generate_atcud_for_invoice(sales_invoice):
	"""
	Gera ATCUD para fatura específica
	"""
	try:
		invoice_doc = frappe.get_doc('Sales Invoice', sales_invoice)

		if getattr(invoice_doc, 'atcud_code', None):
			return {'status': 'error', 'message': _('Invoice already has ATCUD code')}

		# Gerar ATCUD
		from portugal_compliance.utils.atcud_generator import ATCUDGenerator
		generator = ATCUDGenerator()

		atcud_code = generator.generate_atcud(
			company=invoice_doc.company,
			series=invoice_doc.naming_series,
			document_number=invoice_doc.name.split('-')[-1],
			document_type='Sales Invoice'
		)

		# Atualizar fatura
		invoice_doc.atcud_code = atcud_code
		invoice_doc.save()

		return {
			'status': 'success',
			'message': _('ATCUD generated successfully'),
			'atcud_code': atcud_code
		}

	except Exception as e:
		frappe.log_error(f"Error generating ATCUD for invoice: {str(e)}")
		return {'status': 'error', 'message': str(e)}


@frappe.whitelist()
def get_compliance_summary(sales_invoice):
	"""
	Endpoint para obter resumo de compliance
	"""
	try:
		dashboard = SalesInvoiceDashboard(sales_invoice)
		return {
			'compliance_status': dashboard.get_compliance_status(),
			'atcud_info': dashboard.get_atcud_info(),
			'alerts': dashboard.get_compliance_alerts()
		}
	except Exception as e:
		frappe.log_error(f"Error getting compliance summary: {str(e)}")
		return {'error': str(e)}
