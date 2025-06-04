# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry


class CustomJournalEntry(JournalEntry):
	"""
	Extensão da Journal Entry para compliance português
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
			self.validate_accounting_entries()
			self.validate_party_information()
			self.validate_journal_type()
			self.ensure_series_configuration()

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.ensure_atcud_code()
			self.validate_document_series()
			self.validate_accounting_regulations()
			self.validate_period_restrictions()

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão"""
		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			self.create_atcud_log()
			self.update_series_sequence()
			self.create_accounting_notification()

	def validate_accounting_entries(self):
		"""Valida lançamentos contabilísticos"""
		if not self.accounts:
			frappe.throw(_("Journal Entry must have at least one accounting entry"))

		# Verificar se débitos = créditos
		total_debit = sum([d.debit_in_account_currency for d in self.accounts])
		total_credit = sum([d.credit_in_account_currency for d in self.accounts])

		if abs(total_debit - total_credit) > 0.01:
			frappe.throw(_("Total Debit must equal Total Credit"))

		# Verificar contas válidas
		for account in self.accounts:
			if not account.account:
				frappe.throw(_("Account is required for all entries"))

			# Verificar se conta existe e está ativa
			account_status = frappe.db.get_value("Account", account.account, "disabled")
			if account_status:
				frappe.throw(_("Account '{0}' is disabled").format(account.account))

	def validate_party_information(self):
		"""Valida informações de terceiros"""
		for account in self.accounts:
			if account.party_type and account.party:
				# Validar NIF se for entidade portuguesa
				if account.party_type in ["Customer", "Supplier"]:
					party_tax_id = frappe.db.get_value(account.party_type, account.party, "tax_id")

					if self.is_portuguese_party(account.party_type,
												account.party) and party_tax_id:
						if not self.validate_portuguese_nif(party_tax_id):
							frappe.throw(_("Invalid Portuguese NIF for {0} '{1}': {2}").format(
								account.party_type.lower(), account.party, party_tax_id
							))

	def is_portuguese_party(self, party_type, party):
		"""Verifica se a entidade é portuguesa"""
		if not party or not party_type:
			return False

		# Verificar país através do endereço
		party_address = frappe.db.get_value("Address", {
			"link_name": party,
			"link_doctype": party_type,
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

	def validate_journal_type(self):
		"""Valida tipo de lançamento"""
		if not self.voucher_type:
			frappe.throw(_("Journal Entry Type is required"))

		# Validações específicas por tipo
		if self.voucher_type == "Opening Entry":
			self.validate_opening_entry()
		elif self.voucher_type == "Closing Entry":
			self.validate_closing_entry()
		elif self.voucher_type == "Bank Entry":
			self.validate_bank_entry()
		elif self.voucher_type == "Cash Entry":
			self.validate_cash_entry()

	def validate_opening_entry(self):
		"""Valida lançamento de abertura"""
		# Verificar se é início de período fiscal
		from erpnext.accounts.utils import get_fiscal_year

		try:
			fiscal_year = get_fiscal_year(self.posting_date, company=self.company)
			fy_start_date = fiscal_year[1]

			if self.posting_date != fy_start_date:
				frappe.msgprint(
					_("Opening entries should typically be posted on fiscal year start date"),
					indicator="orange",
					title=_("Opening Entry Date")
				)
		except Exception:
			pass

	def validate_closing_entry(self):
		"""Valida lançamento de encerramento"""
		# Verificar se é fim de período fiscal
		from erpnext.accounts.utils import get_fiscal_year

		try:
			fiscal_year = get_fiscal_year(self.posting_date, company=self.company)
			fy_end_date = fiscal_year[2]

			if self.posting_date != fy_end_date:
				frappe.msgprint(
					_("Closing entries should typically be posted on fiscal year end date"),
					indicator="orange",
					title=_("Closing Entry Date")
				)
		except Exception:
			pass

	def validate_bank_entry(self):
		"""Valida lançamento bancário"""
		bank_accounts = []

		for account in self.accounts:
			account_type = frappe.db.get_value("Account", account.account, "account_type")
			if account_type == "Bank":
				bank_accounts.append(account.account)

		if not bank_accounts:
			frappe.msgprint(
				_("Bank Entry should include at least one bank account"),
				indicator="orange",
				title=_("Bank Entry")
			)

	def validate_cash_entry(self):
		"""Valida lançamento de caixa"""
		cash_accounts = []

		for account in self.accounts:
			account_type = frappe.db.get_value("Account", account.account, "account_type")
			if account_type == "Cash":
				cash_accounts.append(account.account)

		if not cash_accounts:
			frappe.msgprint(
				_("Cash Entry should include at least one cash account"),
				indicator="orange",
				title=_("Cash Entry")
			)

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série"""
		if not self.naming_series:
			return

		# Verificar se existe configuração de série portuguesa
		series_config = frappe.db.exists("Portugal Series Configuration", {
			"series_name": self.naming_series,
			"document_type": "Journal Entry",
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
					document_type="Journal Entry"
				)

				frappe.msgprint(
					_("ATCUD code generated: {0}").format(self.atcud_code),
					indicator="green",
					title=_("ATCUD Generated")
				)

			except Exception as e:
				frappe.log_error(f"Error generating ATCUD for Journal Entry {self.name}: {str(e)}")
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
			"document_type": "Journal Entry",
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

	def validate_accounting_regulations(self):
		"""Valida regulamentações contabilísticas"""
		# Verificar se lançamento está dentro do período permitido
		self.validate_posting_period()

		# Verificar se não modifica períodos fechados
		self.validate_closed_periods()

		# Verificar limites de valores
		self.validate_amount_limits()

	def validate_posting_period(self):
		"""Valida período de lançamento"""
		# Verificar se data não é futura (exceto para alguns tipos)
		from datetime import date

		if self.posting_date > date.today():
			if self.voucher_type not in ["Opening Entry", "Closing Entry"]:
				frappe.msgprint(
					_("Future dated entries may require special authorization"),
					indicator="orange",
					title=_("Future Date")
				)

	def validate_closed_periods(self):
		"""Valida períodos fechados"""
		# Verificar se período está fechado
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
				frappe.throw(_("Cannot create journal entry in closed fiscal year '{0}'").format(
					fiscal_year[0]))

		except Exception:
			pass

	def validate_amount_limits(self):
		"""Valida limites de valores"""
		total_amount = sum([d.debit_in_account_currency for d in self.accounts])

		# Alertar para valores muito altos
		if total_amount > 1000000:  # €1M
			frappe.msgprint(
				_("High-value journal entry (>€1M) may require additional authorization"),
				indicator="orange",
				title=_("High-Value Entry")
			)

	def validate_period_restrictions(self):
		"""Valida restrições de período"""
		# Verificar se não está a modificar lançamentos de períodos anteriores
		if hasattr(self, '_doc_before_save'):
			old_posting_date = getattr(self._doc_before_save, 'posting_date', None)

			if old_posting_date and old_posting_date != self.posting_date:
				from datetime import datetime, timedelta

				# Não permitir alteração de data para mais de 30 dias atrás
				days_diff = (datetime.now().date() - self.posting_date).days

				if days_diff > 30:
					frappe.throw(_("Cannot change posting date to more than 30 days in the past"))

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			# Calcular totais
			total_debit = sum([d.debit_in_account_currency for d in self.accounts])
			total_credit = sum([d.credit_in_account_currency for d in self.accounts])

			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Journal Entry",
				"document_name": self.name,
				"company": self.company,
				"series_name": self.naming_series,
				"document_date": self.posting_date,
				"voucher_type": self.voucher_type,
				"total_debit": total_debit,
				"total_credit": total_credit,
				"user_remark": self.user_remark,
				"validation_status": "Valid",
				"generation_method": "Automatic"
			})
			atcud_log.insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Error creating ATCUD log for Journal Entry {self.name}: {str(e)}")

	def update_series_sequence(self):
		"""Atualiza sequência da série"""
		if not self.naming_series:
			return

		try:
			# Atualizar contador da série
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"series_name": self.naming_series,
				"document_type": "Journal Entry",
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
				f"Error updating series sequence for Journal Entry {self.name}: {str(e)}")

	def create_accounting_notification(self):
		"""Cria notificação contabilística se necessário"""
		# Notificar para lançamentos de alto valor ou tipos especiais
		total_amount = sum([d.debit_in_account_currency for d in self.accounts])

		if total_amount >= 100000 or self.voucher_type in ["Opening Entry", "Closing Entry"]:
			try:
				notification_type = f"{self.voucher_type}" if self.voucher_type in [
					"Opening Entry", "Closing Entry"] else "High-Value Entry"

				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": _(f"Journal Entry: {notification_type}"),
					"email_content": _("Journal Entry {0} for €{1} has been posted").format(
						self.name, total_amount
					),
					"for_user": self.owner,
					"type": "Alert",
					"document_type": "Journal Entry",
					"document_name": self.name
				}).insert(ignore_permissions=True)

			except Exception as e:
				frappe.log_error(
					f"Error creating accounting notification for {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português"""
		total_debit = sum([d.debit_in_account_currency for d in self.accounts])
		total_credit = sum([d.credit_in_account_currency for d in self.accounts])

		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"series_name": self.naming_series,
			"document_type": "Journal Entry",
			"company": self.company,
			"voucher_type": self.voucher_type,
			"total_debit": total_debit,
			"total_credit": total_credit,
			"posting_date": self.posting_date,
			"user_remark": self.user_remark,
			"accounts_count": len(self.accounts),
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending"
		}

	def validate_before_cancel(self):
		"""Validações antes do cancelamento"""
		super().validate_before_cancel()

		if self.company and frappe.db.get_value("Company", self.company,
												"portugal_compliance_enabled"):
			# Verificar se o lançamento pode ser cancelado
			if getattr(self, 'atcud_code', None):
				from datetime import datetime, timedelta

				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel journal entry older than 30 days due to Portuguese regulations"))

			# Verificar se não afeta períodos fechados
			try:
				from erpnext.accounts.utils import get_fiscal_year

				fiscal_year = get_fiscal_year(self.posting_date, company=self.company)

				period_closing = frappe.db.exists("Period Closing Voucher", {
					"company": self.company,
					"fiscal_year": fiscal_year[0],
					"docstatus": 1
				})

				if period_closing:
					frappe.throw(_("Cannot cancel journal entry in closed fiscal year"))

			except Exception:
				pass

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
												   'Journal entry cancelled')
				})

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Journal Entry {self.name}: {str(e)}")

	def get_accounting_document_data(self):
		"""Obtém dados para documento contabilístico"""
		return {
			"journal_entry_number": self.name,
			"atcud_code": getattr(self, 'atcud_code', None),
			"posting_date": self.posting_date,
			"voucher_type": self.voucher_type,
			"user_remark": self.user_remark,
			"total_debit": sum([d.debit_in_account_currency for d in self.accounts]),
			"total_credit": sum([d.credit_in_account_currency for d in self.accounts]),
			"company_name": frappe.db.get_value("Company", self.company, "company_name"),
			"company_nif": frappe.db.get_value("Company", self.company, "tax_id"),
			"accounts_detail": [
				{
					"account": account.account,
					"account_name": frappe.db.get_value("Account", account.account,
														"account_name"),
					"debit": account.debit_in_account_currency,
					"credit": account.credit_in_account_currency,
					"party_type": account.party_type,
					"party": account.party,
					"reference_type": account.reference_type,
					"reference_name": account.reference_name
				}
				for account in self.accounts
			]
		}
