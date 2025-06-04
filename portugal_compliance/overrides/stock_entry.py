# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class CustomStockEntry(StockEntry):
	"""
	Extensão da Stock Entry para compliance português
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
			self.validate_stock_movement_type()
			self.validate_warehouse_information()
			self.validate_item_information()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_stock_regulations()
			self.validate_valuation_requirements()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()
			self.create_stock_notification()

	def validate_stock_movement_type(self):
		"""Valida tipo de movimento de stock"""
		if not self.stock_entry_type:
			frappe.throw(_("Stock Entry Type is required for Portugal compliance"))

		# Validações específicas por tipo
		if self.stock_entry_type == "Material Issue":
			self.validate_material_issue()
		elif self.stock_entry_type == "Material Receipt":
			self.validate_material_receipt()
		elif self.stock_entry_type == "Material Transfer":
			self.validate_material_transfer()
		elif self.stock_entry_type == "Manufacture":
			self.validate_manufacture_entry()
		elif self.stock_entry_type == "Repack":
			self.validate_repack_entry()

	def validate_material_issue(self):
		"""Valida saída de material"""
		# Verificar se tem armazém de origem
		source_warehouses = set()
		for item in self.items:
			if item.s_warehouse:
				source_warehouses.add(item.s_warehouse)

		if not source_warehouses:
			frappe.throw(_("Material Issue must have source warehouse"))

		# Verificar se tem motivo da saída
		if not self.remarks:
			frappe.msgprint(
				_("Reason for material issue is recommended"),
				indicator="orange",
				title=_("Issue Reason")
			)

	def validate_material_receipt(self):
		"""Valida entrada de material"""
		# Verificar se tem armazém de destino
		target_warehouses = set()
		for item in self.items:
			if item.t_warehouse:
				target_warehouses.add(item.t_warehouse)

		if not target_warehouses:
			frappe.throw(_("Material Receipt must have target warehouse"))

		# Verificar origem do material
		if not getattr(self, 'supplier', None) and not getattr(self, 'from_warehouse', None):
			frappe.msgprint(
				_("Source of material (supplier or warehouse) is recommended"),
				indicator="orange",
				title=_("Material Source")
			)

	def validate_material_transfer(self):
		"""Valida transferência de material"""
		# Verificar se tem armazéns de origem e destino
		transfers_without_source = []
		transfers_without_target = []

		for item in self.items:
			if not item.s_warehouse:
				transfers_without_source.append(item.item_code)
			if not item.t_warehouse:
				transfers_without_target.append(item.item_code)

		if transfers_without_source:
			frappe.throw(_("Items missing source warehouse: {0}").format(
				", ".join(transfers_without_source)))

		if transfers_without_target:
			frappe.throw(_("Items missing target warehouse: {0}").format(
				", ".join(transfers_without_target)))

		# Verificar se armazéns são diferentes
		same_warehouse_transfers = []
		for item in self.items:
			if item.s_warehouse == item.t_warehouse:
				same_warehouse_transfers.append(item.item_code)

		if same_warehouse_transfers:
			frappe.throw(_("Source and target warehouse cannot be the same for items: {0}").format(
				", ".join(same_warehouse_transfers)
			))

	def validate_manufacture_entry(self):
		"""Valida entrada de produção"""
		# Verificar se tem BOM ou Work Order
		if not getattr(self, 'bom_no', None) and not getattr(self, 'work_order', None):
			frappe.msgprint(
				_("BOM or Work Order reference is recommended for manufacture entries"),
				indicator="orange",
				title=_("Production Reference")
			)

		# Verificar se tem itens de entrada e saída
		source_items = [item for item in self.items if item.s_warehouse]
		target_items = [item for item in self.items if item.t_warehouse]

		if not source_items:
			frappe.msgprint(
				_("Manufacture entry should have raw material consumption"),
				indicator="orange",
				title=_("Raw Materials")
			)

		if not target_items:
			frappe.throw(_("Manufacture entry must have finished goods production"))

	def validate_repack_entry(self):
		"""Valida entrada de reembalagem"""
		# Verificar se tem itens de entrada e saída
		source_items = [item for item in self.items if item.s_warehouse]
		target_items = [item for item in self.items if item.t_warehouse]

		if not source_items or not target_items:
			frappe.throw(_("Repack entry must have both source and target items"))

		# Verificar conservação de valor
		source_value = sum([item.amount for item in source_items])
		target_value = sum([item.amount for item in target_items])

		if abs(source_value - target_value) > 0.01:
			frappe.msgprint(
				_("Repack entry should maintain total value (Source: {0}, Target: {1})").format(
					source_value, target_value
				),
				indicator="orange",
				title=_("Value Conservation")
			)

	def validate_warehouse_information(self):
		"""Valida informações de armazém"""
		warehouses_used = set()

		for item in self.items:
			if item.s_warehouse:
				warehouses_used.add(item.s_warehouse)
			if item.t_warehouse:
				warehouses_used.add(item.t_warehouse)

		# Verificar se armazéns têm endereço
		for warehouse in warehouses_used:
			warehouse_address = frappe.db.get_value("Warehouse", warehouse, "address_line_1")
			if not warehouse_address:
				frappe.msgprint(
					_("Warehouse '{0}' should have an address configured").format(warehouse),
					indicator="orange",
					title=_("Warehouse Address")
				)

			# Verificar se armazém está ativo
			warehouse_disabled = frappe.db.get_value("Warehouse", warehouse, "disabled")
			if warehouse_disabled:
				frappe.throw(_("Warehouse '{0}' is disabled").format(warehouse))

	def validate_item_information(self):
		"""Valida informações de itens"""
		for item in self.items:
			if not item.item_code:
				frappe.throw(_("Item Code is required for all stock entries"))

			# Verificar se item existe e está ativo
			item_disabled = frappe.db.get_value("Item", item.item_code, "disabled")
			if item_disabled:
				frappe.throw(_("Item '{0}' is disabled").format(item.item_code))

			# Verificar se item permite movimentos de stock
			maintain_stock = frappe.db.get_value("Item", item.item_code, "maintain_stock")
			if not maintain_stock:
				frappe.throw(_("Item '{0}' does not maintain stock").format(item.item_code))

			# Verificar quantidades
			if item.qty <= 0:
				frappe.throw(_("Quantity must be positive for item '{0}'").format(item.item_code))

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Stock Entry",
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
					document_type="Stock Entry"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(f"Error generating ATCUD for Stock Entry {self.name}: {str(e)}")
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
			"document_type": "Stock Entry",
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

	def validate_stock_regulations(self):
		"""Valida regulamentações de stock"""
		# Verificar se movimento está dentro do período permitido
		self.validate_posting_period()

		# Verificar se não afeta períodos fechados
		self.validate_closed_periods()

		# Verificar limites de valores
		self.validate_value_limits()

	def validate_posting_period(self):
		"""Valida período de lançamento"""
		# Verificar se data não é futura
		from datetime import date

		if self.posting_date > date.today():
			frappe.msgprint(
				_("Future dated stock entries may require special authorization"),
				indicator="orange",
				title=_("Future Date")
			)

	def validate_closed_periods(self):
		"""Valida períodos fechados"""
		# Verificar se período está fechado para stock
		try:
			from erpnext.accounts.utils import get_fiscal_year

			fiscal_year = get_fiscal_year(self.posting_date, company=self.company)

			# Verificar se existe Period Closing Voucher
			period_closing = frappe.db.exists("Period Closing Voucher", {
				"company": self.company,
				"fiscal_year": fiscal_year[0],
				"docstatus": 1
			})

			if period_closing:
				frappe.msgprint(
					_("Stock entry in closed fiscal year '{0}' may require special authorization").format(
						fiscal_year[0]),
					indicator="orange",
					title=_("Closed Period")
				)

		except Exception:
			pass

	def validate_value_limits(self):
		"""Valida limites de valores"""
		total_value = sum([item.amount for item in self.items if item.amount])

		# Alertar para valores muito altos
		if total_value > 500000:  # €500K
			frappe.msgprint(
				_("High-value stock entry (>€500K) may require additional authorization"),
				indicator="orange",
				title=_("High-Value Entry")
			)

	def validate_valuation_requirements(self):
		"""Valida requisitos de avaliação"""
		# Verificar se itens têm avaliação correta
		items_without_rate = []

		for item in self.items:
			if not item.basic_rate and item.amount:
				items_without_rate.append(item.item_code)

		if items_without_rate:
			frappe.msgprint(
				_("Items without valuation rate: {0}").format(", ".join(items_without_rate)),
				indicator="orange",
				title=_("Valuation Rate")
			)

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			# Calcular totais
			total_qty = sum([item.qty for item in self.items])
			total_value = sum([item.amount for item in self.items if item.amount])

			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Stock Entry",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"stock_entry_type": self.stock_entry_type,
				"total_qty": total_qty,
				"total_value": total_value,
				"purpose": self.purpose,
				"from_warehouse": getattr(self, 'from_warehouse', None),
				"to_warehouse": getattr(self, 'to_warehouse', None),
				"work_order": getattr(self, 'work_order', None),
				"bom_no": getattr(self, 'bom_no', None),
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Error creating ATCUD log for Stock Entry {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Stock Entry",
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
				f"Error updating series sequence for Stock Entry {self.name}: {str(e)}")

	def create_stock_notification(self):
		"""Cria notificação de stock se necessário"""
		# Notificar para movimentos de alto valor ou tipos especiais
		total_value = sum([item.amount for item in self.items if item.amount])

		if total_value >= 100000 or self.stock_entry_type in ["Manufacture", "Repack"]:
			try:
				notification_type = self.stock_entry_type if self.stock_entry_type in [
					"Manufacture", "Repack"] else "High-Value Movement"

				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _(f"Stock Entry: {notification_type}"),
					"email_content": _("Stock Entry {0} for €{1} has been processed").format(
						self.name, total_value
					),
					"for_user": self.owner,
					"type": "Alert",
					"document_type": "Stock Entry",
					"document_name": self.name
				}).insert(ignore_permissions=True)

			except Exception as e:
				frappe.log_error(f"Error creating stock notification for {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		total_qty = sum([item.qty for item in self.items])
		total_value = sum([item.amount for item in self.items if item.amount])

		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Stock Entry",
			"company": self.company,
			"stock_entry_type": self.stock_entry_type,
			"purpose": self.purpose,
			"total_qty": total_qty,
			"total_value": total_value,
			"posting_date": self.posting_date,
			"from_warehouse": getattr(self, 'from_warehouse', None),
			"to_warehouse": getattr(self, 'to_warehouse', None),
			"work_order": getattr(self, 'work_order', None),
			"items_count": len(self.items),
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se o movimento pode ser cancelado
			if getattr(self, 'atcud_code', None):
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel stock entry older than 30 days due to Portuguese regulations"))

			# Verificar se há movimentos subsequentes
			for item in self.items:
				if item.s_warehouse:
					subsequent_entries = frappe.db.count("Stock Ledger Entry", {
						"warehouse": item.s_warehouse,
						"item_code": item.item_code,
						"posting_date": [">", self.posting_date]
					})

					if subsequent_entries > 0:
						frappe.msgprint(
							_("Item '{0}' has subsequent stock movements").format(item.item_code),
							indicator="orange",
							title=_("Subsequent Movements")
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
												   'Stock entry cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Stock Entry {self.name}: {str(e)}")

	def get_stock_document_data(self):
		"""Obtém dados para documento de stock"""
		return {
			"stock_entry_number": self.name,
			"atcud_code": getattr(self, 'atcud_code', None),
			"posting_date": self.posting_date,
			"stock_entry_type": self.stock_entry_type,
			"purpose": self.purpose,
			"total_qty": sum([item.qty for item in self.items]),
			"total_value": sum([item.amount for item in self.items if item.amount]),
			"from_warehouse": getattr(self, 'from_warehouse', None),
			"to_warehouse": getattr(self, 'to_warehouse', None),
			"work_order": getattr(self, 'work_order', None),
			"bom_no": getattr(self, 'bom_no', None),
			"company_name": frappe.db.get_value("Company", self.company, "company_name"),
			"company_nif": frappe.db.get_value("Company", self.company, "tax_id"),
			"items_detail": [
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"qty": item.qty,
					"uom": item.uom,
					"rate": item.basic_rate,
					"amount": item.amount,
					"s_warehouse": item.s_warehouse,
					"t_warehouse": item.t_warehouse,
					"batch_no": getattr(item, 'batch_no', None),
					"serial_no": getattr(item, 'serial_no', None)
				}
				for item in self.items
			]
		}
