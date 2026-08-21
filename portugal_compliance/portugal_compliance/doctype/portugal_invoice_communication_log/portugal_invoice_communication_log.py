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
		horária. Mesmo padrao de permissao explicita de escrita usado em
		ATCUD Log / SAF-T Export Log (o dispacho whitelisted so exige
		leitura por omissao).
		"""
		self.check_permission("write")

		from portugal_compliance.utils.at_invoice_webservice import register_invoice

		return register_invoice(self.document_type, self.document_name, log_name=self.name)
