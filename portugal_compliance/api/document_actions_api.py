# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Document Actions API - Portugal Compliance

Acoes de ciclo de vida para Quotation/Sales Order chamadas pelos
botoes dedicados de public/js/quotation.js e public/js/sales_order.js
("Renovar Validade", "Duplicar Orcamento", "Atualizar Prazo",
"Duplicar Encomenda").

2026-09-04: este modulo nunca existiu. Os 4 botoes acima ja estavam
completamente construidos no lado do cliente (dialogo, validacao,
frappe.call) mas apontavam para
"portugal_compliance.api.<nome_da_funcao>" - um caminho plano que
nunca correspondeu a nenhum ficheiro (nao existe
api/__init__.py::<nome>, nem nenhum outro modulo com essas funcoes,
confirmado por grep a todo o repositorio). Clicar em qualquer um dos
4 botoes rebentava sempre com um erro do servidor. Encontrado durante
a auditoria de paridade Quotation/Sales Order, corrigido agora.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today


@frappe.whitelist()
def renew_quotation_validity(quotation, new_valid_till, reason=None):
	"""Atualiza Quotation.valid_till, incluindo em orcamentos ja
	submetidos (valid_till nao tem allow_on_submit no DocType nativo -
	confirmado no JSON da ERPNext - por isso usa frappe.db.set_value
	em vez de doc.save(), que seria sempre rejeitado com "not allowed
	to edit... after submission" para um orcamento submetido). O
	ATCUD/assinatura ja gerados no orcamento nao sao afetados - a
	validade e um campo de negocio, nao um dos campos cobertos pela
	assinatura fiscal.
	"""
	if not frappe.has_permission("Quotation", "write", quotation):
		frappe.throw(_("Sem permissão para alterar este orçamento"), frappe.PermissionError)

	try:
		if getdate(new_valid_till) < getdate(today()):
			return {"success": False, "error": _("A nova data de validade não pode ser no passado")}

		frappe.db.set_value("Quotation", quotation, "valid_till", getdate(new_valid_till))

		doc = frappe.get_doc("Quotation", quotation)
		comment = _("Validade renovada para {0}.").format(frappe.utils.format_date(new_valid_till))
		if reason:
			comment += " " + _("Motivo: {0}").format(reason)
		doc.add_comment("Info", comment)

		frappe.db.commit()
		return {"success": True}
	except Exception as e:
		frappe.log_error(f"Erro ao renovar validade do orçamento {quotation}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def duplicate_quotation(quotation):
	"""Cria um novo Quotation em rascunho, copia de `quotation`.
	frappe.copy_doc() + insert() passa pelo ciclo de vida normal de
	insercao - document_hooks.before_insert_document (before_insert,
	registado para Quotation em hooks.py) ja limpa atcud_code/
	qr_code/qr_code_image no documento novo automaticamente, o mesmo
	mecanismo que protege qualquer "Make X" nativo - nao precisa de
	nenhuma limpeza extra aqui.
	"""
	if not frappe.has_permission("Quotation", "read", quotation):
		frappe.throw(_("Sem permissão para aceder a este orçamento"), frappe.PermissionError)
	if not frappe.has_permission("Quotation", "create"):
		frappe.throw(_("Sem permissão para criar orçamentos"), frappe.PermissionError)

	try:
		source = frappe.get_doc("Quotation", quotation)
		new_doc = frappe.copy_doc(source)
		new_doc.insert()
		frappe.db.commit()
		return {"success": True, "new_quotation": new_doc.name}
	except Exception as e:
		frappe.log_error(f"Erro ao duplicar orçamento {quotation}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_sales_order_delivery_date(sales_order, new_delivery_date, reason=None):
	"""Atualiza Sales Order.delivery_date (e a mesma data em cada
	Sales Order Item.delivery_date). Ambos os campos ja tem
	allow_on_submit=1 no DocType nativo (confirmado no JSON da
	ERPNext) - doc.save() funciona diretamente mesmo com a encomenda
	submetida, sem precisar de frappe.db.set_value. Os itens tem de
	ser atualizados tambem: confirmado ao vivo que
	SalesOrder.validate_delivery_date() (core da ERPNext, corre em
	todo validate()) recalcula sempre o campo do cabecalho a partir do
	maximo das datas de entrega dos itens - só mudar o campo do
	cabecalho era imediatamente revertido pelo proprio save(), sem
	erro nenhum (parecia funcionar, mas o valor nunca mudava).
	"""
	if not frappe.has_permission("Sales Order", "write", sales_order):
		frappe.throw(_("Sem permissão para alterar esta encomenda"), frappe.PermissionError)

	try:
		if getdate(new_delivery_date) < getdate(today()):
			return {"success": False, "error": _("A nova data de entrega não pode ser no passado")}

		doc = frappe.get_doc("Sales Order", sales_order)
		doc.delivery_date = getdate(new_delivery_date)
		for item in doc.items:
			item.delivery_date = getdate(new_delivery_date)
		doc.save()

		comment = _("Data de entrega atualizada para {0}.").format(frappe.utils.format_date(new_delivery_date))
		if reason:
			comment += " " + _("Motivo: {0}").format(reason)
		doc.add_comment("Info", comment)

		frappe.db.commit()
		return {"success": True}
	except Exception as e:
		frappe.log_error(f"Erro ao atualizar data de entrega da encomenda {sales_order}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def duplicate_sales_order(sales_order):
	"""Cria uma nova Sales Order em rascunho, copia de `sales_order`.
	Mesma nota de duplicate_quotation acima sobre before_insert_document
	ja limpar os campos fiscais herdados automaticamente.
	"""
	if not frappe.has_permission("Sales Order", "read", sales_order):
		frappe.throw(_("Sem permissão para aceder a esta encomenda"), frappe.PermissionError)
	if not frappe.has_permission("Sales Order", "create"):
		frappe.throw(_("Sem permissão para criar encomendas"), frappe.PermissionError)

	try:
		source = frappe.get_doc("Sales Order", sales_order)
		new_doc = frappe.copy_doc(source)
		new_doc.insert()
		frappe.db.commit()
		return {"success": True, "new_sales_order": new_doc.name}
	except Exception as e:
		frappe.log_error(f"Erro ao duplicar encomenda {sales_order}: {str(e)}")
		return {"success": False, "error": str(e)}
