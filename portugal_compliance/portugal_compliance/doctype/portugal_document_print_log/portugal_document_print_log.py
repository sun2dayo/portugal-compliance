# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PortugalDocumentPrintLog(Document):
	pass


@frappe.whitelist()
def log_document_print(document_type, document_name, print_format=None):
	"""
	Regista uma (re)impressão de um documento fiscal - a AT costuma
	verificar em auditoria se o software regista reimpressões de
	documentos ja emitidos (Portaria n.º 363/2010). Chamado a partir do
	evento de cliente before_print, registado centralmente em
	public/js/portugal_compliance.js para os doctypes fiscais.

	Falha em silencio (nunca bloqueia a impressao em si - um erro aqui
	nao pode impedir o utilizador de imprimir um documento legitimo).
	"""
	try:
		atcud_code = frappe.db.get_value(document_type, document_name, "atcud_code")
		log = frappe.new_doc("Portugal Document Print Log")
		log.document_type = document_type
		log.document_name = document_name
		log.print_format = print_format
		log.printed_by = frappe.session.user
		log.print_datetime = frappe.utils.now()
		log.atcud_code = atcud_code
		log.insert(ignore_permissions=True)
		frappe.db.commit()
		return {"logged": True}
	except Exception as e:
		frappe.log_error(f"Erro ao registar impressão de {document_type} {document_name}: {str(e)}",
						  "PortugalDocumentPrintLog")
		return {"logged": False}
