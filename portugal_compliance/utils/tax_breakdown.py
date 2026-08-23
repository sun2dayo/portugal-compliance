# -*- coding: utf-8 -*-
"""
Resolução de código AT (NOR/INT/RED/ISE) e praça fiscal (PT/PT-AC/
PT-MA) por linha de documento, e discriminação de base/imposto por
código+região para os campos I1-I8/J1-J8/K1-K8 do QR Code (Portaria
195/2020) e TaxTable do SAF-T. Módulo partilhado entre a validação de
motivo de isenção (document_hooks.py) e a geração do QR Code
(jinja_methods.py) - uma só fonte de verdade, para os dois nunca
dessincronizarem sobre "qual o código AT/região desta linha".
"""
import frappe
from frappe.utils import flt

VALID_AT_CODES = ("NOR", "INT", "RED", "ISE")

# Ordem de atribuição aos campos I/J/K do QR Code (Continente é sempre
# a praça "I", mesmo que sem valor - Açores/Madeira só ocupam J/K
# quando ha de facto dados dessa regiao no documento).
VALID_REGIONS = ("PT", "PT-AC", "PT-MA")


def _get_account_at_info(account_names):
	"""
	Uma só query para o código AT e a região fiscal (at_tax_region) de
	um conjunto de contas. Contas anteriores ao campo at_tax_region
	(2026-08-24) ficam sem valor - assumidas Continente (PT), a única
	região que existia antes de haver contas regionais dedicadas.
	"""
	if not account_names:
		return {}
	rows = frappe.get_all(
		"Account", filters={"name": ["in", list(account_names)]},
		fields=["name", "at_tax_code", "at_tax_region"],
	)
	return {r.name: {"code": r.at_tax_code, "region": r.at_tax_region or "PT"} for r in rows}


def _get_item_tax_template_info(template_names, account_info_cache):
	"""
	Uma só query às linhas de Item Tax Template Detail envolvidas;
	reaproveita/estende o cache de código+região de Account já
	carregado (evita N+1 tanto em Account como em Item Tax Template).
	"""
	if not template_names:
		return {}
	detail_rows = frappe.get_all(
		"Item Tax Template Detail",
		filters={"parent": ["in", list(template_names)]},
		fields=["parent", "tax_type"],
	)
	missing = {r.tax_type for r in detail_rows if r.tax_type and r.tax_type not in account_info_cache}
	if missing:
		account_info_cache.update(_get_account_at_info(missing))

	template_info = {}
	for row in detail_rows:
		if row.parent in template_info:
			continue
		info = account_info_cache.get(row.tax_type)
		if info and info["code"] in VALID_AT_CODES:
			template_info[row.parent] = info
	return template_info


def get_line_at_tax_info(doc):
	"""
	{item.name: {"code": at_tax_code, "region": at_tax_region}} para
	cada linha de items do documento.

	Resolução por linha: código/região do Item Tax Template do próprio
	artigo; se não houver template, ou o template não resolver nenhum
	código válido, cai no código/região da primeira linha de doc.taxes
	que resolva um código válido - fallback único, o mesmo caminho para
	"sem template" e para "template sem código resolvível" (não dois
	caminhos de fallback diferentes consoante o motivo da falha).
	"""
	tax_rows = getattr(doc, "taxes", None) or []
	item_rows = getattr(doc, "items", None) or []

	account_info = _get_account_at_info({r.account_head for r in tax_rows if r.account_head})

	header_fallback = None
	for row in tax_rows:
		info = account_info.get(row.account_head)
		if info and info["code"] in VALID_AT_CODES:
			header_fallback = info
			break

	template_names = {i.item_tax_template for i in item_rows if getattr(i, "item_tax_template", None)}
	template_info = _get_item_tax_template_info(template_names, account_info)

	default = {"code": "NOR", "region": "PT"}
	result = {}
	for item in item_rows:
		info = template_info.get(getattr(item, "item_tax_template", None)) or header_fallback or default
		result[item.name] = info
	return result


def get_line_at_tax_codes(doc):
	"""
	{item.name: at_tax_code} para cada linha de items do documento -
	wrapper de get_line_at_tax_info() para os chamadores que só
	precisam do código de taxa (ex: validação de motivo de isenção em
	document_hooks.py), sem se preocuparem com região fiscal.
	"""
	return {name: info["code"] for name, info in get_line_at_tax_info(doc).items()}


def _new_region_buckets():
	return {code: {"base": 0.0, "tax": 0.0} for code in VALID_AT_CODES}


def get_tax_breakdown_by_at_code(doc):
	"""
	Discriminação de base tributável e imposto por código AT e por
	praça fiscal, para os campos I1-I8 (Continente), J1-J8 (2ª praça)
	e K1-K8 (3ª praça) do QR Code, e para a TaxTable do SAF-T:
		I/J/K 1/2 = NOR, 3/4 = INT, 5/6 = RED, 7/8 = ISE

	Devolve {"PT": {...}, "PT-AC": {...}, "PT-MA": {...}} - só as
	regiões com dados reais aparecem, exceto "PT" que está sempre
	presente (mesmo a zeros) porque o QR Code exige pelo menos um
	espaço fiscal (campo I é sempre obrigatório).

	Antes desta função só existia uma região implícita (tudo caía
	sempre em "I", nunca em J/K) - auditoria de certificação
	2026-08-24: as contas SNC regionais (2434 Madeira, 2435 Açores) já
	existiam em tax_setup.py mas a discriminação do QR Code/SAF-T
	nunca as distinguia de Continente.

	Base vem de item.net_amount (já reflete descontos de linha com
	precisão exata ao cêntimo - nunca de tax_amount/rate, que
	acumula erro de arredondamento). Imposto vem de doc.taxes (fonte
	oficial do imposto liquidado). Todas as consultas a Account/Item
	Tax Template são pré-carregadas em lote antes do ciclo por item
	(sem N+1).
	"""
	regions = {"PT": _new_region_buckets()}

	tax_rows = getattr(doc, "taxes", None) or []
	item_rows = getattr(doc, "items", None) or []

	account_info = _get_account_at_info({r.account_head for r in tax_rows if r.account_head})
	for row in tax_rows:
		info = account_info.get(row.account_head)
		if not info or info["code"] not in VALID_AT_CODES:
			continue
		region = info["region"] if info["region"] in VALID_REGIONS else "PT"
		regions.setdefault(region, _new_region_buckets())
		regions[region][info["code"]]["tax"] += flt(row.tax_amount)

	line_info = get_line_at_tax_info(doc)
	for item in item_rows:
		info = line_info.get(item.name, {"code": "NOR", "region": "PT"})
		region = info["region"] if info["region"] in VALID_REGIONS else "PT"
		regions.setdefault(region, _new_region_buckets())
		regions[region][info["code"]]["base"] += flt(item.net_amount)

	# Reconciliação: o total de imposto por código+região deve bater
	# certo com o total real da fatura - se não bater, fica registado
	# no Error Log para investigação (não bloqueia a submissão, o QR
	# já foi calculado com o melhor mapeamento possível).
	total_bucket_tax = sum(b["tax"] for buckets in regions.values() for b in buckets.values())
	total_doc_tax = flt(getattr(doc, "total_taxes_and_charges", 0))
	if abs(total_bucket_tax - total_doc_tax) > 0.01:
		frappe.log_error(
			f"QR Code: discriminação de imposto por código AT não reconcilia "
			f"com o total do documento ({doc.doctype} {getattr(doc, 'name', '')}): "
			f"soma_buckets={total_bucket_tax:.2f} vs total_taxes_and_charges={total_doc_tax:.2f}",
			"Portugal Compliance - QR Code reconciliação",
		)

	return regions
