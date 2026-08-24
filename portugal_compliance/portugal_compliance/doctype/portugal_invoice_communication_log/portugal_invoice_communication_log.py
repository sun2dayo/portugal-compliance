import frappe
from frappe.model.document import Document


class PortugalInvoiceCommunicationLog(Document):
	def validate(self):
		self.validate_document_reference()

	def validate_document_reference(self):
		if self.document_type and self.document_name:
			if not frappe.db.exists(self.document_type, self.document_name):
				frappe.throw(
					frappe._("Documento referenciado {0} {1} não existe").format(
						self.document_type, self.document_name
					)
				)

	@frappe.whitelist()
	def retry_now(self):
		"""
		Tenta reenviar imediatamente, ignorando o agendamento da tarefa
		horária. Ja nao usa check_permission("write"): este DocType
		deixou de ter Write concedido a qualquer role (2026-08-24,
		imutabilidade dos registos de comunicacao AT) - manter essa
		verificacao aqui bloquearia este metodo para sempre.
		frappe.only_for() restringe pela mesma role (System Manager) que
		antes era a unica com Write, sem depender da permissao de
		escrita do DocType; register_invoice()/_write_log() continuam a
		gravar com ignore_permissions=True explicito.
		"""
		frappe.only_for("System Manager")

		from portugal_compliance.utils.at_invoice_webservice import register_invoice

		return register_invoice(self.document_type, self.document_name, log_name=self.name)
