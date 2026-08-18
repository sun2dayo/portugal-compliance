# -*- coding: utf-8 -*-
"""
Resolução de código AT (NOR/INT/RED/ISE) por linha de documento, e
discriminação de base/imposto por código para os campos I1-I8 do QR
Code (Portaria 302/2016). Módulo partilhado entre a validação de
motivo de isenção (document_hooks.py) e a geração do QR Code
(jinja_methods.py) - uma só fonte de verdade, para os dois nunca
dessincronizarem sobre "qual o código AT desta linha".
"""
import frappe
from frappe.utils import flt

VALID_AT_CODES = ("NOR", "INT", "RED", "ISE")


def _get_account_at_codes(account_names):
	"""Uma só query para o código AT de um conjunto de contas."""
	if not account_names:
		return {}
	rows = frappe.get_all(
		"Account", filters={"name": ["in", list(account_names)]},
		fields=["name", "at_tax_code"],
	)
	return {r.name: r.at_tax_code for r in rows}


def _get_item_tax_template_codes(template_names, account_codes_cache):
	"""
	Uma só query às linhas de Item Tax Template Detail envolvidas;
	reaproveita/estende o cache de códigos de Account já carregado
	(evita N+1 tanto em Account como em Item Tax Template).
	"""
	if not template_names:
		return {}
	detail_rows = frappe.get_all(
		"Item Tax Template Detail",
		filters={"parent": ["in", list(template_names)]},
		fields=["parent", "tax_type"],
	)
	missing = {r.tax_type for r in detail_rows if r.tax_type and r.tax_type not in account_codes_cache}
	if missing:
		account_codes_cache.update(_get_account_at_codes(missing))

	template_codes = {}
	for row in detail_rows:
		if row.parent in template_codes:
			continue
		code = account_codes_cache.get(row.tax_type)
		if code in VALID_AT_CODES:
			template_codes[row.parent] = code
	return template_codes


def get_line_at_tax_codes(doc):
	"""
	{item.name: at_tax_code} para cada linha de items do documento.

	Resolução por linha: código do Item Tax Template do próprio
	artigo; se não houver template, ou o template não resolver nenhum
	código válido, cai no código da primeira linha de doc.taxes que
	resolva um código válido - fallback único, o mesmo caminho para
	"sem template" e para "template sem código resolvível" (não dois
	caminhos de fallback diferentes consoante o motivo da falha).
	"""
	tax_rows = getattr(doc, "taxes", None) or []
	item_rows = getattr(doc, "items", None) or []

	account_codes = _get_account_at_codes({r.account_head for r in tax_rows if r.account_head})

	header_fallback_code = None
	for row in tax_rows:
		code = account_codes.get(row.account_head)
		if code in VALID_AT_CODES:
			header_fallback_code = code
			break

	template_names = {i.item_tax_template for i in item_rows if getattr(i, "item_tax_template", None)}
	template_codes = _get_item_tax_template_codes(template_names, account_codes)

	result = {}
	for item in item_rows:
		code = template_codes.get(getattr(item, "item_tax_template", None)) or header_fallback_code or "NOR"
		result[item.name] = code
	return result


def get_tax_breakdown_by_at_code(doc):
	"""
	Discriminação de base tributável e imposto por código AT, para os
	campos I1-I8 do QR Code:
		I1/I2 = NOR, I3/I4 = INT, I5/I6 = RED, I7/I8 = ISE

	Base vem de item.net_amount (já reflete descontos de linha com
	precisão exata ao cêntimo - nunca de tax_amount/rate, que
	acumula erro de arredondamento). Imposto vem de doc.taxes (fonte
	oficial do imposto liquidado). Todas as consultas a Account/Item
	Tax Template são pré-carregadas em lote antes do ciclo por item
	(sem N+1).
	"""
	buckets = {code: {"base": 0.0, "tax": 0.0} for code in VALID_AT_CODES}

	tax_rows = getattr(doc, "taxes", None) or []
	item_rows = getattr(doc, "items", None) or []

	account_codes = _get_account_at_codes({r.account_head for r in tax_rows if r.account_head})
	for row in tax_rows:
		code = account_codes.get(row.account_head)
		if code in buckets:
			buckets[code]["tax"] += flt(row.tax_amount)

	line_codes = get_line_at_tax_codes(doc)
	for item in item_rows:
		code = line_codes.get(item.name, "NOR")
		buckets[code]["base"] += flt(item.net_amount)

	# Reconciliação: o total de imposto por código deve bater certo com
	# o total real da fatura - se não bater, fica registado no Error
	# Log para investigação (não bloqueia a submissão, o QR já foi
	# calculado com o melhor mapeamento possível).
	total_bucket_tax = sum(b["tax"] for b in buckets.values())
	total_doc_tax = flt(getattr(doc, "total_taxes_and_charges", 0))
	if abs(total_bucket_tax - total_doc_tax) > 0.01:
		frappe.log_error(
			f"QR Code: discriminação de imposto por código AT não reconcilia "
			f"com o total do documento ({doc.doctype} {getattr(doc, 'name', '')}): "
			f"soma_buckets={total_bucket_tax:.2f} vs total_taxes_and_charges={total_doc_tax:.2f}",
			"Portugal Compliance - QR Code reconciliação",
		)

	return buckets
