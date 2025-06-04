# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, now, cint, flt, formatdate
from datetime import datetime, timedelta


def get_data():
	"""
	Retorna dados do dashboard para Purchase Invoice
	"""
	return {
		"heatmap": True,
		"heatmap_message": _(
			"This is based on the posting date of the Purchase Invoice. See timeline below for details"),
		"fieldname": "supplier",
		"non_standard_fieldnames": {
			"Payment Entry": "party",
			"Purchase Receipt": "supplier",
			"Purchase Order": "supplier",
			"ATCUD Log": "supplier",
			"Portugal Series Configuration": "company"
		},
		"dynamic_links": {
			"supplier": ["Supplier", "supplier"],
			"company": ["Company", "company"]
		},
		"transactions": [
			{
				"label": _("Pre Purchase"),
				"items": ["Request for Quotation", "Supplier Quotation", "Purchase Order"]
			},
			{
				"label": _("Receipt"),
				"items": ["Purchase Receipt", "Purchase Invoice"]
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
				"items": ["Purchase Invoice"]
			}
		]
	}


class PurchaseInvoiceDashboard:
	"""
	Dashboard para Purchase Invoice no Portugal Compliance
	"""

	def __init__(self, purchase_invoice_name):
		self.purchase_invoice_name = purchase_invoice_name
		self.purchase_invoice = None

	def get_context(self):
		"""Retorna dados de contexto para o dashboard"""
		try:
			self.purchase_invoice = frappe.get_doc('Purchase Invoice', self.purchase_invoice_name)

			context = {}
			context['invoice'] = self.purchase_invoice_name
			context['compliance_status'] = self.get_compliance_status()
			context['atcud_info'] = self.get_atcud_info()
			context['series_info'] = self.get_series_info()
			context['tax_compliance'] = self.get_tax_compliance()
			context['supplier_info'] = self.get_supplier_compliance_info()
			context['related_documents'] = self.get_related_documents()
			context['compliance_alerts'] = self.get_compliance_alerts()
			context['saft_status'] = self.get_saft_status()
			context['import_info'] = self.get_import_compliance_info()

			return context

		except Exception as e:
			frappe.log_error(f"Error getting Purchase Invoice dashboard context: {str(e)}")
			return {'error': str(e)}

	def get_compliance_status(self):
		"""Verifica status de compliance da fatura de compra"""
		try:
			if not self.purchase_invoice:
				return {'status': 'error', 'message': _('Invoice not found')}

			# Verificar se empresa tem compliance ativo
			company_compliance = frappe.db.get_value('Company', self.purchase_invoice.company,
													 'portugal_compliance_enabled')

			if not company_compliance:
				return {
					'status': 'not_applicable',
					'message': _('Portugal Compliance not enabled for this company'),
					'color': 'gray'
				}

			# Verificar ATCUD
			if not getattr(self.purchase_invoice, 'atcud_code', None):
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

			# Verificar NIF do fornecedor
			supplier_nif = frappe.db.get_value('Supplier', self.purchase_invoice.supplier,
											   'tax_id')
			if self.is_portuguese_supplier() and not supplier_nif:
				return {
					'status': 'warning',
					'message': _('Portuguese supplier without NIF'),
					'color': 'orange',
					'action': _('Update Supplier NIF')
				}

			# Verificar se é auto-faturação
			if getattr(self.purchase_invoice, 'is_self_billing', False):
				if not self.validate_self_billing():
					return {
						'status': 'warning',
						'message': _('Self-billing validation issues'),
						'color': 'orange',
						'action': _('Review Self-billing')
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
			atcud_code = getattr(self.purchase_invoice, 'atcud_code', None)

			if not atcud_code:
				return {
					'has_atcud': False,
					'message': _('No ATCUD code assigned'),
					'status': 'missing'
				}

			# Obter log do ATCUD
			atcud_log = frappe.db.get_value('ATCUD Log', {
				'atcud_code': atcud_code,
				'document_name': self.purchase_invoice_name
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
			series_name = getattr(self.purchase_invoice, 'naming_series', None)

			if not series_name:
				return {'has_series': False, 'message': _('No naming series found')}

			# Procurar configuração de série portuguesa
			series_config = frappe.db.get_value('Portugal Series Configuration', {
				'series_name': series_name,
				'company': self.purchase_invoice.company,
				'document_type': 'Purchase Invoice'
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
				'has_taxes': bool(self.purchase_invoice.taxes),
				'total_tax_amount': 0,
				'tax_breakdown': [],
				'compliance_issues': [],
				'is_reverse_charge': False,
				'vat_deductible': True
			}

			if self.purchase_invoice.taxes:
				valid_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

				for tax in self.purchase_invoice.taxes:
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

			# Verificar tipo de compra
			if self.is_intracom_purchase():
				if tax_info['total_tax_amount'] == 0:
					tax_info['is_reverse_charge'] = True
				else:
					tax_info['compliance_issues'].append(
						_('Intra-community purchase may require reverse charge')
					)

			if self.is_import_purchase():
				tax_info['compliance_issues'].append(
					_('Import purchase - verify customs documentation')
				)

			return tax_info

		except Exception as e:
			frappe.log_error(f"Error getting tax compliance: {str(e)}")
			return {'error': str(e)}

	def is_portuguese_supplier(self):
		"""Verifica se fornecedor é português"""
		try:
			supplier_country = frappe.db.get_value('Address', {
				'link_name': self.purchase_invoice.supplier,
				'link_doctype': 'Supplier',
				'is_primary_address': 1
			}, 'country')

			return supplier_country == 'Portugal'
		except Exception:
			return False

	def is_intracom_purchase(self):
		"""Verifica se é compra intracomunitária"""
		try:
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Romania", "Slovakia", "Slovenia",
							"Spain", "Sweden"]

			supplier_country = frappe.db.get_value('Address', {
				'link_name': self.purchase_invoice.supplier,
				'link_doctype': 'Supplier',
				'is_primary_address': 1
			}, 'country')

			return supplier_country in eu_countries and supplier_country != 'Portugal'
		except Exception:
			return False

	def is_import_purchase(self):
		"""Verifica se é compra de importação"""
		try:
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
							"Slovenia", "Spain", "Sweden"]

			supplier_country = frappe.db.get_value('Address', {
				'link_name': self.purchase_invoice.supplier,
				'link_doctype': 'Supplier',
				'is_primary_address': 1
			}, 'country')

			return supplier_country and supplier_country not in eu_countries
		except Exception:
			return False

	def validate_self_billing(self):
		"""Valida auto-faturação"""
		try:
			if not getattr(self.purchase_invoice, 'is_self_billing', False):
				return True

			# Verificar se fornecedor autoriza auto-faturação
			supplier_allows = frappe.db.get_value('Supplier', self.purchase_invoice.supplier,
												  'allow_self_billing')

			if not supplier_allows:
				return False

			# Verificar se tem referência ao documento original
			if not getattr(self.purchase_invoice, 'bill_no', None):
				return False

			return True

		except Exception:
			return False

	def get_supplier_compliance_info(self):
		"""Obtém informações de compliance do fornecedor"""
		try:
			supplier_info = {
				'supplier_name': self.purchase_invoice.supplier_name,
				'is_portuguese': self.is_portuguese_supplier(),
				'has_nif': False,
				'nif_valid': False,
				'supplier_type': 'domestic',
				'allows_self_billing': False
			}

			# Obter NIF do fornecedor
			supplier_data = frappe.db.get_value('Supplier', self.purchase_invoice.supplier,
												['tax_id', 'allow_self_billing'], as_dict=True)

			if supplier_data:
				if supplier_data.tax_id:
					supplier_info['has_nif'] = True
					supplier_info['nif'] = supplier_data.tax_id

					if supplier_info['is_portuguese']:
						supplier_info['nif_valid'] = self.validate_portuguese_nif(
							supplier_data.tax_id)

				supplier_info['allows_self_billing'] = supplier_data.allow_self_billing or False

			# Determinar tipo de fornecedor
			if self.is_intracom_purchase():
				supplier_info['supplier_type'] = 'intracom'
			elif self.is_import_purchase():
				supplier_info['supplier_type'] = 'import'

			return supplier_info

		except Exception as e:
			frappe.log_error(f"Error getting supplier compliance info: {str(e)}")
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
				'purchase_receipts': [],
				'payment_entries': [],
				'purchase_orders': [],
				'return_invoices': []
			}

			# Purchase Receipts
			purchase_receipts = frappe.db.get_all('Purchase Receipt Item', {
				'purchase_invoice': self.purchase_invoice_name
			}, ['parent'], distinct=True)

			for pr in purchase_receipts:
				pr_doc = frappe.db.get_value('Purchase Receipt', pr.parent,
											 ['name', 'posting_date', 'atcud_code'], as_dict=True)
				if pr_doc:
					related['purchase_receipts'].append(pr_doc)

			# Payment Entries
			payment_entries = frappe.db.get_all('Payment Entry Reference', {
				'reference_name': self.purchase_invoice_name,
				'reference_doctype': 'Purchase Invoice'
			}, ['parent'])

			for pe in payment_entries:
				pe_doc = frappe.db.get_value('Payment Entry', pe.parent,
											 ['name', 'posting_date', 'paid_amount', 'atcud_code'],
											 as_dict=True)
				if pe_doc:
					related['payment_entries'].append(pe_doc)

			# Purchase Orders
			if hasattr(self.purchase_invoice, 'items'):
				for item in self.purchase_invoice.items:
					if getattr(item, 'purchase_order', None):
						po_doc = frappe.db.get_value('Purchase Order', item.purchase_order,
													 ['name', 'transaction_date', 'grand_total'],
													 as_dict=True)
						if po_doc and po_doc not in related['purchase_orders']:
							related['purchase_orders'].append(po_doc)

			# Return Invoices
			if getattr(self.purchase_invoice, 'is_return', False):
				return_against = getattr(self.purchase_invoice, 'return_against', None)
				if return_against:
					original_doc = frappe.db.get_value('Purchase Invoice', return_against,
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
			if not getattr(self.purchase_invoice, 'atcud_code', None):
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

			# Verificar NIF do fornecedor português
			supplier_info = self.get_supplier_compliance_info()
			if supplier_info.get('is_portuguese') and not supplier_info.get('has_nif'):
				alerts.append({
					'type': 'missing_supplier_nif',
					'message': _('Portuguese supplier without NIF'),
					'severity': 'warning',
					'action': _('Update Supplier NIF')
				})

			# Verificar auto-faturação
			if getattr(self.purchase_invoice, 'is_self_billing', False):
				if not self.validate_self_billing():
					alerts.append({
						'type': 'invalid_self_billing',
						'message': _('Self-billing validation failed'),
						'severity': 'warning',
						'action': _('Review Self-billing Setup')
					})

			# Verificar compra intracomunitária
			if self.is_intracom_purchase():
				tax_info = self.get_tax_compliance()
				if not tax_info.get('is_reverse_charge'):
					alerts.append({
						'type': 'intracom_vat',
						'message': _('Intra-community purchase may require reverse charge'),
						'severity': 'info',
						'action': _('Verify VAT Treatment')
					})

			# Verificar importação
			if self.is_import_purchase():
				alerts.append({
					'type': 'import_documentation',
					'message': _('Import purchase - verify customs documentation'),
					'severity': 'info',
					'action': _('Check Import Documents')
				})

			# Verificar fatura de valor alto
			if self.purchase_invoice.grand_total > 50000:
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
			saft_exports = frappe.db.get_all('SAF-T Export Log', {
				'company': self.purchase_invoice.company,
				'period_start': ['<=', self.purchase_invoice.posting_date],
				'period_end': ['>=', self.purchase_invoice.posting_date],
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

	def get_import_compliance_info(self):
		"""Obtém informações de compliance para importações"""
		try:
			import_info = {
				'is_import': self.is_import_purchase(),
				'is_intracom': self.is_intracom_purchase(),
				'customs_documentation': {},
				'vat_treatment': 'standard'
			}

			if import_info['is_import']:
				# Verificar documentação alfandegária
				customs_fields = ['customs_declaration', 'bill_of_entry', 'customs_value']
				for field in customs_fields:
					value = getattr(self.purchase_invoice, field, None)
					import_info['customs_documentation'][field] = {
						'value': value,
						'has_value': bool(value)
					}

				import_info['vat_treatment'] = 'import_vat'

			elif import_info['is_intracom']:
				# Verificar NIF UE do fornecedor
				supplier_nif = frappe.db.get_value('Supplier', self.purchase_invoice.supplier,
												   'tax_id')
				import_info['supplier_eu_vat'] = supplier_nif
				import_info['vat_treatment'] = 'reverse_charge'

			return import_info

		except Exception as e:
			frappe.log_error(f"Error getting import compliance info: {str(e)}")
			return {'error': str(e)}


@frappe.whitelist()
def get_purchase_invoice_dashboard_data(purchase_invoice):
	"""
	Endpoint para obter dados do dashboard da fatura de compra
	"""
	try:
		dashboard = PurchaseInvoiceDashboard(purchase_invoice)
		return dashboard.get_context()
	except Exception as e:
		frappe.log_error(f"Error getting purchase invoice dashboard data: {str(e)}")
		return {'error': str(e)}


@frappe.whitelist()
def generate_atcud_for_purchase_invoice(purchase_invoice):
	"""
	Gera ATCUD para fatura de compra específica
	"""
	try:
		invoice_doc = frappe.get_doc('Purchase Invoice', purchase_invoice)

		if getattr(invoice_doc, 'atcud_code', None):
			return {'status': 'error', 'message': _('Invoice already has ATCUD code')}

		# Gerar ATCUD
		from portugal_compliance.utils.atcud_generator import ATCUDGenerator
		generator = ATCUDGenerator()

		atcud_code = generator.generate_atcud(
			company=invoice_doc.company,
			series=invoice_doc.naming_series,
			document_number=invoice_doc.name.split('-')[-1],
			document_type='Purchase Invoice'
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
		frappe.log_error(f"Error generating ATCUD for purchase invoice: {str(e)}")
		return {'status': 'error', 'message': str(e)}


@frappe.whitelist()
def validate_supplier_compliance(purchase_invoice):
	"""
	Valida compliance do fornecedor
	"""
	try:
		dashboard = PurchaseInvoiceDashboard(purchase_invoice)
		supplier_info = dashboard.get_supplier_compliance_info()

		issues = []

		if supplier_info.get('is_portuguese') and not supplier_info.get('has_nif'):
			issues.append(_('Portuguese supplier missing NIF'))

		if supplier_info.get('has_nif') and not supplier_info.get('nif_valid'):
			issues.append(_('Invalid NIF format'))

		if dashboard.is_intracom_purchase() and not supplier_info.get('has_nif'):
			issues.append(_('Intra-community supplier missing VAT number'))

		return {
			'status': 'success' if not issues else 'warning',
			'issues': issues,
			'supplier_info': supplier_info
		}

	except Exception as e:
		frappe.log_error(f"Error validating supplier compliance: {str(e)}")
		return {'status': 'error', 'message': str(e)}


@frappe.whitelist()
def get_compliance_summary(purchase_invoice):
	"""
	Endpoint para obter resumo de compliance
	"""
	try:
		dashboard = PurchaseInvoiceDashboard(purchase_invoice)
		return {
			'compliance_status': dashboard.get_compliance_status(),
			'atcud_info': dashboard.get_atcud_info(),
			'supplier_info': dashboard.get_supplier_compliance_info(),
			'import_info': dashboard.get_import_compliance_info(),
			'alerts': dashboard.get_compliance_alerts()
		}
	except Exception as e:
		frappe.log_error(f"Error getting compliance summary: {str(e)}")
		return {'error': str(e)}
