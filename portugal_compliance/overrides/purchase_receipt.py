# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


class CustomPurchaseReceipt(PurchaseReceipt):
	"""
	Extensão da Purchase Receipt para compliance português
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
			self.validate_supplier_information()
			self.validate_receipt_documentation()
			self.validate_warehouse_information()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_receipt_requirements()
			self.validate_customs_documentation()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()
			self.create_receipt_notification()

	def validate_supplier_information(self):
		"""Valida informações do fornecedor"""
		if self.supplier:
			supplier_tax_id = frappe.db.get_value("Supplier", self.supplier, "tax_id")

			if self.is_portuguese_supplier() and supplier_tax_id:
				if not self.validate_portuguese_nif(supplier_tax_id):
					frappe.throw(_("Invalid Portuguese NIF for supplier '{0}': {1}").format(
						self.supplier, supplier_tax_id
					))

			# Verificar se fornecedor tem endereço completo
			supplier_address = frappe.db.get_value("Address", {
				"link_name": self.supplier,
				"link_doctype": "Supplier",
				"is_primary_address": 1
			}, ["address_line1", "city", "country"], as_dict=True)

			if not supplier_address or not supplier_address.address_line1:
				frappe.msgprint(
					_("Supplier '{0}' should have a complete address for compliance").format(
						self.supplier),
					indicator="orange",
					title=_("Supplier Address")
				)

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

			# Verificar se começa com dígito válido
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

	def validate_receipt_documentation(self):
		"""Valida documentação de receção"""
		# Verificar se tem referência a ordem de compra
		if not getattr(self, 'purchase_order', None):
			frappe.msgprint(
				_("Purchase receipt should reference a purchase order"),
				indicator="orange",
				title=_("Purchase Order Reference")
			)

		# Verificar se tem número de fatura do fornecedor
		if not getattr(self, 'bill_no', None):
			frappe.msgprint(
				_("Supplier invoice number is recommended for purchase receipts"),
				indicator="orange",
				title=_("Supplier Invoice")
			)

		# Verificar data da fatura do fornecedor
		if not getattr(self, 'bill_date', None):
			frappe.msgprint(
				_("Supplier invoice date is recommended for compliance"),
				indicator="orange",
				title=_("Invoice Date")
			)

	def validate_warehouse_information(self):
		"""Valida informações do armazém"""
		warehouses_used = set()

		for item in self.items:
			if item.warehouse:
				warehouses_used.add(item.warehouse)

		# Verificar se todos os armazéns têm endereço
		for warehouse in warehouses_used:
			warehouse_address = frappe.db.get_value("Warehouse", warehouse, "address_line_1")
			if not warehouse_address:
				frappe.msgprint(
					_("Warehouse '{0}' should have an address configured").format(warehouse),
					indicator="orange",
					title=_("Warehouse Address")
				)

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Purchase Receipt",
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
					document_type="Purchase Receipt"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(
					f"Error generating ATCUD for Purchase Receipt {self.name}: {str(e)}")
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
			"document_type": "Purchase Receipt",
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

	def validate_receipt_requirements(self):
		"""Valida requisitos de receção"""
		# Verificar se é importação
		if self.is_import_receipt():
			self.validate_import_requirements()
		else:
			self.validate_domestic_requirements()

		# Verificar qualidade e quantidade
		self.validate_quality_control()

	def is_import_receipt(self):
		"""Verifica se é receção de importação"""
		if not self.supplier:
			return False

		supplier_country = frappe.db.get_value("Address", {
			"link_name": self.supplier,
			"link_doctype": "Supplier",
			"is_primary_address": 1
		}, "country")

		return supplier_country and supplier_country != "Portugal"

	def validate_import_requirements(self):
		"""Valida requisitos para receções de importação"""
		# Verificar documentação alfandegária
		if not getattr(self, 'customs_declaration', None):
			frappe.msgprint(
				_("Customs declaration number is recommended for import receipts"),
				indicator="orange",
				title=_("Import Documentation")
			)

		# Verificar se tem informações de transporte internacional
		if not getattr(self, 'transporter', None):
			frappe.msgprint(
				_("Transporter information is recommended for import receipts"),
				indicator="orange",
				title=_("Transport Information")
			)

		# Verificar se é intracomunitário
		if self.is_intracom_receipt():
			self.validate_intracom_requirements()

	def is_intracom_receipt(self):
		"""Verifica se é receção intracomunitária"""
		if not self.supplier:
			return False

		# Verificar se fornecedor é da UE mas não de Portugal
		eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
						"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
						"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
						"Malta", "Netherlands", "Poland", "Romania", "Slovakia", "Slovenia",
						"Spain", "Sweden"]

		supplier_country = frappe.db.get_value("Address", {
			"link_name": self.supplier,
			"link_doctype": "Supplier",
			"is_primary_address": 1
		}, "country")

		return supplier_country in eu_countries and supplier_country != "Portugal"

	def validate_intracom_requirements(self):
		"""Valida requisitos para receções intracomunitárias"""
		supplier_tax_id = frappe.db.get_value("Supplier", self.supplier, "tax_id")

		if not supplier_tax_id:
			frappe.throw(_("VAT number is required for intra-community purchases"))

		# Verificar se tem número EORI se aplicável
		if not getattr(self, 'eori_number', None):
			frappe.msgprint(
				_("EORI number may be required for intra-community transactions"),
				indicator="orange",
				title=_("EORI Number")
			)

	def validate_domestic_requirements(self):
		"""Valida requisitos para receções nacionais"""
		# Verificar se tem informações básicas de transporte
		if not getattr(self, 'transporter', None) and not getattr(self, 'vehicle_no', None):
			frappe.msgprint(
				_("Transport information is recommended for domestic receipts"),
				indicator="blue",
				title=_("Transport Information")
			)

	def validate_quality_control(self):
		"""Valida controlo de qualidade"""
		# Verificar se itens têm informações de qualidade
		items_without_quality = []

		for item in self.items:
			# Verificar se item requer inspeção de qualidade
			if frappe.db.get_value("Item", item.item_code, "inspection_required_before_purchase"):
				if not getattr(item, 'quality_inspection', None):
					items_without_quality.append(item.item_code)

		if items_without_quality:
			frappe.msgprint(
				_("The following items require quality inspection: {0}").format(
					", ".join(items_without_quality)),
				indicator="orange",
				title=_("Quality Inspection Required")
			)

	def validate_customs_documentation(self):
		"""Valida documentação alfandegária"""
		if self.is_import_receipt():
			# Verificar se tem todos os documentos necessários
			required_docs = []

			if not getattr(self, 'customs_declaration', None):
				required_docs.append("Customs Declaration")

			if not getattr(self, 'bill_of_entry', None):
				required_docs.append("Bill of Entry")

			if required_docs:
				frappe.msgprint(
					_("Missing import documentation: {0}").format(", ".join(required_docs)),
					indicator="orange",
					title=_("Import Documentation")
				)

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Purchase Receipt",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"supplier": self.supplier,
				"supplier_name": self.supplier_name,
				"purchase_order": getattr(self, 'purchase_order', None),
				"bill_no": getattr(self, 'bill_no', None),
				"bill_date": getattr(self, 'bill_date', None),
				"is_import": self.is_import_receipt(),
				"is_intracom": self.is_intracom_receipt(),
				"customs_declaration": getattr(self, 'customs_declaration', None),
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(
				f"Error creating ATCUD log for Purchase Receipt {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Purchase Receipt",
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
				f"Error updating series sequence for Purchase Receipt {self.name}: {str(e)}")

	def create_receipt_notification(self):
		"""Cria notificação de receção se necessário"""
		# Notificar para receções de importação ou alto valor
		if self.is_import_receipt() or self.calculate_total_value() >= 50000:
			try:
				notification_type = "Import Receipt" if self.is_import_receipt() else "High-Value Receipt"

				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _(f"{notification_type} Processed"),
					"email_content": _("Purchase Receipt {0} requires attention").format(
						self.name),
					"for_user": self.owner,
					"type": "Alert",
					"document_type": "Purchase Receipt",
					"document_name": self.name
				}).insert(ignore_permissions=True)

			except Exception as e:
				frappe.log_error(f"Error creating receipt notification for {self.name}: {str(e)}")

	def calculate_total_value(self):
		"""Calcula valor total da receção"""
		total = 0
		for item in self.items:
			total += (item.qty * item.rate)
		return total

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Purchase Receipt",
			"company": self.company,
			"supplier_nif": frappe.db.get_value("Supplier", self.supplier,
												"tax_id") if self.supplier else None,
			"is_portuguese_supplier": self.is_portuguese_supplier(),
			"is_import_receipt": self.is_import_receipt(),
			"is_intracom_receipt": self.is_intracom_receipt(),
			"purchase_order": getattr(self, 'purchase_order', None),
			"supplier_invoice": getattr(self, 'bill_no', None),
			"customs_declaration": getattr(self, 'customs_declaration', None),
			"total_value": self.calculate_total_value(),
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se a receção pode ser cancelada
			if getattr(self, 'atcud_code', None):
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel receipt older than 30 days due to Portuguese regulations"))

			# Verificar se há stock já consumido
			for item in self.items:
				stock_balance = frappe.db.get_value("Bin", {
					"item_code": item.item_code,
					"warehouse": item.warehouse
				}, "actual_qty")

				if stock_balance and stock_balance < item.qty:
					frappe.msgprint(
						_("Item '{0}' may have been partially consumed from stock").format(
							item.item_code),
						indicator="orange",
						title=_("Stock Movement")
					)

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
												   'Purchase receipt cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Purchase Receipt {self.name}: {str(e)}")

	def get_receipt_document_data(self):
		"""Obtém dados para documento de receção"""
		return {
			"receipt_number": self.name,
			"atcud_code": getattr(self, 'atcud_code', None),
			"receipt_date": self.posting_date,
			"supplier_name": self.supplier_name,
			"supplier_invoice": getattr(self, 'bill_no', None),
			"purchase_order": getattr(self, 'purchase_order', None),
			"total_value": self.calculate_total_value(),
			"is_import": self.is_import_receipt(),
			"customs_declaration": getattr(self, 'customs_declaration', None),
			"company_name": frappe.db.get_value("Company", self.company, "company_name"),
			"company_nif": frappe.db.get_value("Company", self.company, "tax_id"),
			"items_summary": [
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount,
					"warehouse": item.warehouse
				}
				for item in self.items
			]
		}
