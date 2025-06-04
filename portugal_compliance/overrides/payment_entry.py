# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry


class CustomPaymentEntry(PaymentEntry):
	"""
	Extensão da Payment Entry para compliance português
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
			self.validate_payment_method()
			self.validate_party_information()
			self.validate_bank_account_information()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_payment_regulations()
			self.validate_cash_payment_limits()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()
			self.create_payment_notification()

	def validate_payment_method(self):
		"""Valida método de pagamento"""
		if not self.mode_of_payment:
			frappe.throw(_("Payment method is required for Portugal compliance"))

		# Verificar se o método de pagamento é válido
		valid_methods = ["Cash", "Bank Draft", "Credit Card", "Cheque", "Wire Transfer",
						 "Online Payment"]

		if self.mode_of_payment not in valid_methods:
			frappe.msgprint(
				_("Payment method '{0}' may require additional validation for Portuguese regulations").format(
					self.mode_of_payment
				),
				indicator="orange",
				title=_("Payment Method Warning")
			)

	def validate_party_information(self):
		"""Valida informações da entidade"""
		if not self.party:
			frappe.throw(_("Party is required for payment entry"))

		# Validar NIF se for entidade portuguesa
		if self.party_type in ["Customer", "Supplier"]:
			party_tax_id = frappe.db.get_value(self.party_type, self.party, "tax_id")

			if self.is_portuguese_party() and party_tax_id:
				if not self.validate_portuguese_nif(party_tax_id):
					frappe.throw(_("Invalid Portuguese NIF for {0} '{1}': {2}").format(
						self.party_type.lower(), self.party, party_tax_id
					))

	def is_portuguese_party(self):
		"""Verifica se a entidade é portuguesa"""
		if not self.party or not self.party_type:
			return False

		# Verificar país através do endereço
		party_address = frappe.db.get_value("Address", {
			"link_name": self.party,
			"link_doctype": self.party_type,
			"is_primary_address": 1
		}, "country")

		return party_address == "Portugal"

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

	def validate_bank_account_information(self):
		"""Valida informações da conta bancária"""
		if self.payment_type == "Pay" and self.paid_from:
			# Verificar se a conta bancária tem IBAN válido
			bank_account = frappe.db.get_value("Bank Account", self.paid_from, "iban")
			if bank_account and not self.validate_portuguese_iban(bank_account):
				frappe.msgprint(
					_("IBAN format may be invalid for account '{0}'").format(self.paid_from),
					indicator="orange",
					title=_("IBAN Warning")
				)

		if self.payment_type == "Receive" and self.paid_to:
			# Verificar conta de destino
			bank_account = frappe.db.get_value("Bank Account", self.paid_to, "iban")
			if bank_account and not self.validate_portuguese_iban(bank_account):
				frappe.msgprint(
					_("IBAN format may be invalid for account '{0}'").format(self.paid_to),
					indicator="orange",
					title=_("IBAN Warning")
				)

	def validate_portuguese_iban(self, iban):
		"""Valida IBAN português"""
		try:
			if not iban:
				return False

			# Remover espaços e converter para maiúsculas
			import re
			iban = re.sub(r'[^\w]', '', iban.upper())

			# IBAN português deve começar com PT e ter 25 caracteres
			if not iban.startswith('PT') or len(iban) != 25:
				return False

			# Validação básica do formato
			return True

		except Exception:
			return False

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Payment Entry",
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
					document_type="Payment Entry"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(f"Error generating ATCUD for Payment Entry {self.name}: {str(e)}")
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
			"document_type": "Payment Entry",
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

	def validate_payment_regulations(self):
		"""Valida regulamentações de pagamento"""
		# Verificar se é pagamento internacional
		if self.is_international_payment():
			self.validate_international_payment_requirements()

		# Verificar limites de pagamento em dinheiro
		if self.mode_of_payment == "Cash":
			self.validate_cash_payment_limits()

		# Verificar se requer documentação adicional
		if self.paid_amount >= 10000:  # Pagamentos acima de €10,000
			self.validate_large_payment_requirements()

	def is_international_payment(self):
		"""Verifica se é pagamento internacional"""
		if not self.party or not self.party_type:
			return False

		party_country = frappe.db.get_value("Address", {
			"link_name": self.party,
			"link_doctype": self.party_type,
			"is_primary_address": 1
		}, "country")

		return party_country and party_country != "Portugal"

	def validate_international_payment_requirements(self):
		"""Valida requisitos para pagamentos internacionais"""
		if not self.reference_no:
			frappe.msgprint(
				_("Reference number is recommended for international payments"),
				indicator="orange",
				title=_("International Payment")
			)

		# Verificar se tem informações bancárias completas
		if self.payment_type == "Pay" and self.paid_from:
			bank_swift = frappe.db.get_value("Bank Account", self.paid_from, "swift_number")
			if not bank_swift:
				frappe.msgprint(
					_("SWIFT code is required for international payments"),
					indicator="orange",
					title=_("Missing SWIFT Code")
				)

	def validate_cash_payment_limits(self):
		"""Valida limites de pagamento em dinheiro"""
		if self.mode_of_payment != "Cash":
			return

		# Limite legal para pagamentos em dinheiro em Portugal: €1,000
		cash_limit = 1000.0

		if self.paid_amount > cash_limit:
			frappe.throw(_("Cash payments cannot exceed €{0} according to Portuguese law").format(
				cash_limit))

		# Aviso para valores próximos do limite
		if self.paid_amount > cash_limit * 0.8:
			frappe.msgprint(
				_("Cash payment of €{0} is close to the legal limit of €{1}").format(
					self.paid_amount, cash_limit
				),
				indicator="orange",
				title=_("Cash Payment Warning")
			)

	def validate_large_payment_requirements(self):
		"""Valida requisitos para pagamentos grandes"""
		# Pagamentos acima de €10,000 podem requerer documentação adicional
		if not self.remarks:
			frappe.msgprint(
				_("Large payments (>€10,000) should include detailed remarks for compliance"),
				indicator="orange",
				title=_("Large Payment")
			)

		# Verificar se tem referências adequadas
		if not self.reference_no and not self.reference_date:
			frappe.msgprint(
				_("Large payments should include reference number and date"),
				indicator="orange",
				title=_("Payment References")
			)

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Payment Entry",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"document_total": self.paid_amount,
				"party_type": self.party_type,
				"party": self.party,
				"party_name": self.party_name,
				"payment_type": self.payment_type,
				"mode_of_payment": self.mode_of_payment,
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Error creating ATCUD log for Payment Entry {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Payment Entry",
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
				f"Error updating series sequence for Payment Entry {self.name}: {str(e)}")

	def create_payment_notification(self):
		"""Cria notificação de pagamento se necessário"""
		# Notificar para pagamentos grandes ou internacionais
		if self.paid_amount >= 10000 or self.is_international_payment():
			try:
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _("Large/International Payment Processed"),
					"email_content": _("Payment {0} for €{1} has been processed").format(
						self.name, self.paid_amount
					),
					"for_user": self.owner,
					"type": "Alert",
					"document_type": "Payment Entry",
					"document_name": self.name
				}).insert(ignore_permissions=True)

			except Exception as e:
				frappe.log_error(f"Error creating payment notification for {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Payment Entry",
			"company": self.company,
			"party_type": self.party_type,
			"party": self.party,
			"party_nif": frappe.db.get_value(self.party_type, self.party,
											 "tax_id") if self.party and self.party_type else None,
			"is_portuguese_party": self.is_portuguese_party(),
			"is_international_payment": self.is_international_payment(),
			"payment_method": self.mode_of_payment,
			"payment_amount": self.paid_amount,
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se o pagamento pode ser cancelado
			if getattr(self, 'atcud_code', None):
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel payment older than 30 days due to Portuguese regulations"))

			# Verificar se há documentos relacionados
			if self.references:
				for ref in self.references:
					if ref.allocated_amount > 0:
						frappe.msgprint(
							_("Cancelling this payment will affect document '{0}'").format(
								ref.reference_name),
							indicator="orange",
							title=_("Related Documents")
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
												   'Payment cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Payment Entry {self.name}: {str(e)}")

	def get_payment_receipt_data(self):
		"""Obtém dados para recibo de pagamento"""
		return {
			"receipt_number": self.name,
			"atcud_code": getattr(self, 'atcud_code', None),
			"payment_date": self.posting_date,
			"payment_amount": self.paid_amount,
			"currency": self.paid_to_account_currency,
			"party_name": self.party_name,
			"payment_method": self.mode_of_payment,
			"reference_number": self.reference_no,
			"company_name": frappe.db.get_value("Company", self.company, "company_name"),
			"company_nif": frappe.db.get_value("Company", self.company, "tax_id")
		}
