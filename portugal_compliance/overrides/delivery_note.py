# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote


class CustomDeliveryNote(DeliveryNote):
	"""
	Extensão da Delivery Note para compliance português
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
			self.validate_customer_information()
			self.validate_transport_information()
			self.validate_delivery_address()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_transport_requirements()
			self.validate_delivery_documentation()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()
			self.create_transport_notification()

	def validate_customer_information(self):
		"""Valida informações do cliente"""
		if self.customer:
			customer_tax_id = frappe.db.get_value("Customer", self.customer, "tax_id")

			if self.is_portuguese_customer() and customer_tax_id:
				if not self.validate_portuguese_nif(customer_tax_id):
					frappe.throw(_("Invalid Portuguese NIF for customer '{0}': {1}").format(
						self.customer, customer_tax_id
					))

	def is_portuguese_customer(self):
		"""Verifica se o cliente é português"""
		if not self.customer:
			return False

		# Verificar país do cliente através do endereço
		customer_address = frappe.db.get_value("Address", {
			"link_name": self.customer,
			"link_doctype": "Customer",
			"is_primary_address": 1
		}, "country")

		return customer_address == "Portugal"

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

	def validate_transport_information(self):
		"""Valida informações de transporte"""
		# Verificar se tem informações de transporte obrigatórias
		if not getattr(self, 'transporter', None) and not getattr(self, 'vehicle_no', None):
			frappe.msgprint(
				_("Transport information (transporter or vehicle) is recommended for delivery notes"),
				indicator="orange",
				title=_("Transport Information")
			)

		# Verificar se tem data e hora de início de transporte
		if not getattr(self, 'lr_date', None):
			frappe.msgprint(
				_("Transport date is recommended for compliance with transport regulations"),
				indicator="orange",
				title=_("Transport Date")
			)

	def validate_delivery_address(self):
		"""Valida endereço de entrega"""
		if not self.shipping_address_name:
			frappe.msgprint(
				_("Shipping address is required for delivery notes"),
				indicator="orange",
				title=_("Shipping Address")
			)
			return

		# Verificar se o endereço de entrega está completo
		shipping_address = frappe.db.get_value("Address", self.shipping_address_name,
											   ["address_line1", "city", "pincode", "country"],
											   as_dict=True)

		if shipping_address:
			missing_fields = []
			if not shipping_address.address_line1:
				missing_fields.append("Address Line 1")
			if not shipping_address.city:
				missing_fields.append("City")
			if not shipping_address.pincode:
				missing_fields.append("Postal Code")

			if missing_fields:
				frappe.msgprint(
					_("Shipping address is missing: {0}").format(", ".join(missing_fields)),
					indicator="orange",
					title=_("Incomplete Address")
				)

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Delivery Note",
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
					document_type="Delivery Note"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(f"Error generating ATCUD for Delivery Note {self.name}: {str(e)}")
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
			"document_type": "Delivery Note",
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

	def validate_transport_requirements(self):
		"""Valida requisitos de transporte"""
		# Verificar se é transporte nacional ou internacional
		if self.is_international_delivery():
			self.validate_international_transport_requirements()
		else:
			self.validate_national_transport_requirements()

		# Verificar peso e volume se aplicável
		self.validate_cargo_information()

	def is_international_delivery(self):
		"""Verifica se é entrega internacional"""
		if not self.shipping_address_name:
			return False

		delivery_country = frappe.db.get_value("Address", self.shipping_address_name, "country")
		return delivery_country and delivery_country != "Portugal"

	def validate_international_transport_requirements(self):
		"""Valida requisitos para transporte internacional"""
		# Verificar documentação internacional
		if not getattr(self, 'transporter', None):
			frappe.msgprint(
				_("Transporter information is required for international deliveries"),
				indicator="orange",
				title=_("International Transport")
			)

		# Verificar se tem informações alfandegárias
		if not getattr(self, 'customs_declaration', None):
			frappe.msgprint(
				_("Customs declaration may be required for international deliveries"),
				indicator="orange",
				title=_("Customs Documentation")
			)

	def validate_national_transport_requirements(self):
		"""Valida requisitos para transporte nacional"""
		# Verificar se tem informações básicas de transporte
		if not getattr(self, 'transporter', None) and not getattr(self, 'vehicle_no', None):
			frappe.msgprint(
				_("Transport information is recommended for national deliveries"),
				indicator="blue",
				title=_("Transport Information")
			)

	def validate_cargo_information(self):
		"""Valida informações da carga"""
		total_weight = 0
		total_volume = 0

		for item in self.items:
			if hasattr(item, 'weight_per_unit') and item.weight_per_unit:
				total_weight += (item.weight_per_unit * item.qty)

			if hasattr(item, 'volume_per_unit') and item.volume_per_unit:
				total_volume += (item.volume_per_unit * item.qty)

		# Armazenar totais calculados
		if total_weight > 0:
			self.total_net_weight = total_weight

		# Verificar limites de peso para diferentes tipos de transporte
		if total_weight > 3500:  # 3.5 toneladas
			frappe.msgprint(
				_("Heavy cargo (>{0}kg) may require special transport license").format(3500),
				indicator="orange",
				title=_("Heavy Cargo")
			)

	def validate_delivery_documentation(self):
		"""Valida documentação de entrega"""
		# Verificar se tem referência a fatura
		if not getattr(self, 'against_sales_invoice', None):
			frappe.msgprint(
				_("Delivery note should reference a sales invoice"),
				indicator="orange",
				title=_("Invoice Reference")
			)

		# Verificar se tem instruções de entrega
		if not getattr(self, 'instructions', None):
			frappe.msgprint(
				_("Delivery instructions are recommended"),
				indicator="blue",
				title=_("Delivery Instructions")
			)

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Delivery Note",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"customer": self.customer,
				"customer_name": self.customer_name,
				"delivery_address": self.shipping_address_name,
				"transporter": getattr(self, 'transporter', None),
				"vehicle_no": getattr(self, 'vehicle_no', None),
				"total_weight": getattr(self, 'total_net_weight', 0),
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Error creating ATCUD log for Delivery Note {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Delivery Note",
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
				f"Error updating series sequence for Delivery Note {self.name}: {str(e)}")

	def create_transport_notification(self):
		"""Cria notificação de transporte se necessário"""
		# Notificar para entregas internacionais ou carga pesada
		if self.is_international_delivery() or (getattr(self, 'total_net_weight', 0) > 1000):
			try:
				notification_type = "International Delivery" if self.is_international_delivery() else "Heavy Cargo Delivery"

				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _(f"{notification_type} Processed"),
					"email_content": _("Delivery Note {0} requires special attention").format(
						self.name),
					"for_user": self.owner,
					"type": "Alert",
					"document_type": "Delivery Note",
					"document_name": self.name
				}).insert(ignore_permissions=True)

			except Exception as e:
				frappe.log_error(
					f"Error creating transport notification for {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Delivery Note",
			"company": self.company,
			"customer_nif": frappe.db.get_value("Customer", self.customer,
												"tax_id") if self.customer else None,
			"is_portuguese_customer": self.is_portuguese_customer(),
			"is_international_delivery": self.is_international_delivery(),
			"delivery_address": self.shipping_address_name,
			"transporter": getattr(self, 'transporter', None),
			"vehicle_number": getattr(self, 'vehicle_no', None),
			"total_weight": getattr(self, 'total_net_weight', 0),
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se a guia pode ser cancelada
			if getattr(self, 'atcud_code', None):
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel delivery note older than 30 days due to Portuguese regulations"))

			# Verificar se já foi entregue
			if getattr(self, 'status', None) == "Delivered":
				frappe.msgprint(
					_("Cancelling a delivered shipment may require additional documentation"),
					indicator="orange",
					title=_("Delivered Shipment")
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
												   'Delivery note cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Delivery Note {self.name}: {str(e)}")

	def get_transport_document_data(self):
		"""Obtém dados para documento de transporte"""
		return {
			"transport_document_number": self.name,
			"atcud_code": getattr(self, 'atcud_code', None),
			"transport_date": self.posting_date,
			"customer_name": self.customer_name,
			"delivery_address": self.shipping_address_name,
			"transporter": getattr(self, 'transporter', None),
			"vehicle_number": getattr(self, 'vehicle_no', None),
			"driver_name": getattr(self, 'driver_name', None),
			"total_weight": getattr(self, 'total_net_weight', 0),
			"company_name": frappe.db.get_value("Company", self.company, "company_name"),
			"company_nif": frappe.db.get_value("Company", self.company, "tax_id"),
			"items_summary": [
				{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"qty": item.qty,
					"weight": getattr(item, 'weight_per_unit', 0) * item.qty
				}
				for item in self.items
			]
		}
