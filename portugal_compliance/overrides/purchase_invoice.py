# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class CustomPurchaseInvoice(PurchaseInvoice):
	"""
	Extensão da Purchase Invoice para compliance português
	"""

	def validate(self):
		super().validate()
		self.validate_portugal_compliance()

	def before_submit(self):
		super().before_submit()
		self.ensure_portugal_compliance_before_submit()

	def on_submit(self):
		super().on_submit()
		self.update_portugal_compliance_data()

	def validate_portugal_compliance(self):
		"""Validações específicas para Portugal"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.validate_supplier_nif()
			self.validate_tax_information()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_fiscal_requirements()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()

	def validate_supplier_nif(self):
		"""Valida NIF do fornecedor"""
		if self.supplier:
			supplier_tax_id = frappe.db.get_value("Supplier", self.supplier, "tax_id")

			if not supplier_tax_id:
				frappe.msgprint(
					_("Supplier '{0}' does not have a Tax ID (NIF) configured").format(
						self.supplier),
					indicator="orange",
					title=_("Missing Tax ID")
				)
			else:
				# Validar formato do NIF português se for fornecedor português
				if self.is_portuguese_supplier():
					if not self.validate_portuguese_nif(supplier_tax_id):
						frappe.throw(_("Invalid Portuguese NIF for supplier '{0}': {1}").format(
							self.supplier, supplier_tax_id
						))

	def is_portuguese_supplier(self):
		"""Verifica se o fornecedor é português"""
		if not self.supplier:
			return False

		# Verificar país do fornecedor através do endereço
		supplier_address = frappe.db.get_value("Address", {
			"link_name": self.supplier,
			"link_doctype": "Supplier",
			"is_primary_address": 1
		}, "country")

		return supplier_address == "Portugal"

	def validate_portuguese_nif(self, nif):
		"""Valida NIF português"""
		try:
			if not nif:
				return False

			# Remover espaços e caracteres não numéricos
			import re
			nif = re.sub(r'[^\d]', '', str(nif))

			# Verificar se tem 9 dígitos
			if len(nif) != 9:
				return False

			# Verificar se começa com dígito válido para empresas
			if nif[0] not in '123456789':
				return False

			# Calcular dígito de controlo
			check_sum = 0
			for i in range(8):
				check_sum += int(nif[i]) * (9 - i)

			remainder = check_sum % 11

			if remainder < 2:
				check_digit = 0
			else:
				check_digit = 11 - remainder

			return int(nif[8]) == check_digit

		except Exception:
			return False

	def validate_tax_information(self):
		"""Valida informações fiscais"""
		if not self.taxes:
			frappe.msgprint(
				_("No tax information found. Please ensure tax rates are correctly applied."),
				indicator="orange",
				title=_("Tax Information")
			)
			return

		# Verificar se as taxas de IVA são válidas para Portugal
		valid_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

		for tax in self.taxes:
			if hasattr(tax, 'rate') and tax.rate is not None:
				if tax.rate not in valid_rates:
					frappe.msgprint(
						_("Tax rate {0}% may not be valid for Portugal. Valid rates: {1}").format(
							tax.rate, ", ".join(map(str, valid_rates))
						),
						indicator="orange",
						title=_("Tax Rate Warning")
					)

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série para este tipo de documento"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Purchase Invoice",
			"company": self.company,
			"is_active": 1
		})

		if not series_config:
			frappe.msgprint(
				_("No Portugal series configuration found for series '{0}'. Please configure the series.").format(
					self.naming_series
				),
				indicator="orange",
				title=_("Series Configuration")
			)

	def ensure_atcud_code(self):
		"""Garante que o documento tem código ATCUD"""
		if not getattr(self, 'atcud_code', None):
			try:
				from portugal_compliance.utils.atcud_generator import ATCUDGenerator

				generator = ATCUDGenerator()
				self.atcud_code = generator.generate_atcud(
					company=self.company,
					series=self.naming_series,
					document_number=self.get_document_number(),
					document_type="Purchase Invoice"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(
					f"Error generating ATCUD for Purchase Invoice {self.name}: {str(e)}")
				frappe.throw(
					_("Failed to generate ATCUD code. Please try again or contact administrator."))

	def get_document_number(self):
		"""Obtém número do documento da série"""
		if not self.name:
			return 1

		try:
			# Extrair número da série
			import re
			match = re.search(r'(\d+)$', self.name)
			if match:
				return int(match.group(1))
			return 1
		except:
			return 1

	def validate_document_series(self):
		"""Valida série do documento"""
		if not self.naming_series:
			frappe.throw(_("Document series is required for Portugal compliance"))

		# Verificar se a série está comunicada com a AT
		series_config = frappe.db.get_value("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Purchase Invoice",
			"company": self.company
		}, ["is_communicated", "validation_code"], as_dict=True)

		if series_config and not series_config.is_communicated:
			frappe.msgprint(
				_("Series '{0}' is not yet communicated with AT. Please communicate the series first.").format(
					self.naming_series
				),
				indicator="orange",
				title=_("Series Not Communicated")
			)

	def validate_fiscal_requirements(self):
		"""Valida requisitos fiscais"""
		# Verificar se é auto-faturação
		if getattr(self, 'is_self_billing', False):
			self.validate_self_billing_requirements()

		# Verificar se tem referência a documento original (se for nota de crédito)
		if self.is_return and not getattr(self, 'return_against', None):
			frappe.throw(_("Return document must reference the original invoice"))

	def validate_self_billing_requirements(self):
		"""Valida requisitos de auto-faturação"""
		if not self.supplier:
			frappe.throw(_("Supplier is required for self-billing invoices"))

		# Verificar se o fornecedor tem autorização para auto-faturação
		supplier_self_billing = frappe.db.get_value("Supplier", self.supplier,
													"allow_self_billing")

		if not supplier_self_billing:
			frappe.throw(
				_("Supplier '{0}' is not authorized for self-billing").format(self.supplier))

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Purchase Invoice",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"document_total": self.grand_total,
				"supplier": self.supplier,
				"supplier_name": self.supplier_name,
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(
				f"Error creating ATCUD log for Purchase Invoice {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Purchase Invoice",
				"company": self.company
			}, "name")

			if series_config:
				current_number = self.get_document_number()
				frappe.db.set_value("Portugal Series Configuration", series_config, {
					"current_number": current_number,
					"last_used_date": self.posting_date
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating series sequence for Purchase Invoice {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Purchase Invoice",
			"company": self.company,
			"supplier_nif": frappe.db.get_value("Supplier", self.supplier,
												"tax_id") if self.supplier else None,
			"is_portuguese_supplier": self.is_portuguese_supplier(),
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se o documento pode ser cancelado conforme regulamentação portuguesa
			if getattr(self, 'atcud_code', None):
				# Documentos com ATCUD têm restrições de cancelamento
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel document older than 30 days due to Portuguese regulations"))

	def on_cancel(self):
		"""Ações após cancelamento"""
		super().on_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.update_atcud_log_on_cancel()

	def update_atcud_log_on_cancel(self):
		"""Atualiza log ATCUD após cancelamento"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			# Marcar log como cancelado
			atcud_log = frappe.db.exists("ATCUD Log", {
				"atcud_code": self.atcud_code,
				"document_name": self.name
			})

			if atcud_log:
				frappe.db.set_value("ATCUD Log", atcud_log, {
					"validation_status": "Cancelled",
					"cancellation_date": frappe.utils.now(),
					"cancellation_reason": getattr(self, 'reason_for_cancellation',
												   'Document cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Purchase Invoice {self.name}: {str(e)}")
