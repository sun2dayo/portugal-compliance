import frappe
from frappe.model.document import Document


class ATTaxExemption(Document):
	def validate(self):
		if self.code:
			self.code = self.code.strip().upper()
