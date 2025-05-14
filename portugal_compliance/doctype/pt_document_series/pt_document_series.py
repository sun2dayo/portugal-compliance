# Copyright (c) 2025, Manus Team and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class PTDocumentSeries(Document):
    def autoname(self):
        # Ensure series_name is set, as it's the basis for the name
        if not self.series_name:
            frappe.throw("O Nome da Série (PT) é obrigatório.")
        self.name = self.series_name

