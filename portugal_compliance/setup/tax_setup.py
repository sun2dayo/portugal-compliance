# -*- coding: utf-8 -*-
"""
Taxonomia AT de IVA (regiões, taxas, códigos SAF-T) e motivos de
isenção. Ver blueprint aprovado: contas SNC 2433x por taxa (não a
conta genérica "Duties and Taxes"), Custom Fields só em Account (não
duplicados em Item Tax Template), Item Tax Template + Sales Taxes and
Charges Template gerados por empresa na ativação do compliance.
"""
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# ========== TAXONOMIA (região, taxa, código AT) ==========
# As 3 regiões (Continente, Madeira, Açores) são criadas automaticamente
# na ativação do compliance via create_regional_tax_setup_for_company(),
# que itera esta taxonomia chamando setup_tax_templates_for_company por
# região. Também disponível sob pedido (botão "Gerar Séries/Taxas
# Regionais") para empresas já ativas antes desta correção.
AT_TAX_TAXONOMY = {
	"PT": [
		{"rate": 23, "code": "NOR", "label": "Normal", "account_suffix": "1"},
		{"rate": 13, "code": "INT", "label": "Intermédia", "account_suffix": "2"},
		{"rate": 6, "code": "RED", "label": "Reduzida", "account_suffix": "3"},
		{"rate": 0, "code": "ISE", "label": "Isenta", "account_suffix": "4"},
	],
	"PT-MA": [
		{"rate": 22, "code": "NOR", "label": "Normal", "account_suffix": "1"},
		{"rate": 12, "code": "INT", "label": "Intermédia", "account_suffix": "2"},
		{"rate": 5, "code": "RED", "label": "Reduzida", "account_suffix": "3"},
		{"rate": 0, "code": "ISE", "label": "Isenta", "account_suffix": "4"},
	],
	"PT-AC": [
		{"rate": 16, "code": "NOR", "label": "Normal", "account_suffix": "1"},
		{"rate": 9, "code": "INT", "label": "Intermédia", "account_suffix": "2"},
		{"rate": 4, "code": "RED", "label": "Reduzida", "account_suffix": "3"},
		{"rate": 0, "code": "ISE", "label": "Isenta", "account_suffix": "4"},
	],
}

# Prefixo da conta SNC 2433 (Iva liquidado) por região - Continente usa
# o próprio 2433, Madeira/Açores usam blocos seguintes para não colidir.
REGION_ACCOUNT_PREFIX = {"PT": "2433", "PT-MA": "2434", "PT-AC": "2435"}

ACCOUNT_CUSTOM_FIELDS = [
	{
		"fieldname": "at_tax_type",
		"label": "Tipo de Imposto AT",
		"fieldtype": "Select",
		"options": "\nIVA\nIS",
		"insert_after": "account_type",
		"module": "Portugal Compliance",
	},
	{
		"fieldname": "at_tax_region",
		"label": "Região Fiscal AT",
		"fieldtype": "Select",
		"options": "\nPT\nPT-AC\nPT-MA",
		"insert_after": "at_tax_type",
		"module": "Portugal Compliance",
	},
	{
		"fieldname": "at_tax_code",
		"label": "Código de Taxa AT",
		"fieldtype": "Select",
		"options": "\nNOR\nINT\nRED\nISE",
		"insert_after": "at_tax_region",
		"module": "Portugal Compliance",
		"depends_on": "eval:doc.at_tax_type=='IVA'",
	},
	{
		# Verba da Tabela Geral do Imposto do Selo (TGIS) - código livre
		# (ex: "1.1", "17.3.1"), nunca a classificação NOR/INT/RED/ISE de
		# IVA (at_tax_code acima, que só se aplica a contas at_tax_type=
		# "IVA"). Sem tabela de verbas pré-carregada: cada conta de
		# Imposto do Selo tem de ser configurada manualmente com a verba
		# real aplicável ao negócio - nenhum código fiscal é assumido
		# automaticamente (ver saft_generator.py::_line_tax_code, usa
		# "OUT" como reserva só quando este campo fica vazio).
		"fieldname": "at_stamp_duty_verba",
		"label": "Verba TGIS (Imposto do Selo)",
		"fieldtype": "Data",
		"insert_after": "at_tax_code",
		"module": "Portugal Compliance",
		"depends_on": "eval:doc.at_tax_type=='IS'",
	},
	{
		# Tipo de retenção na fonte (IRS/IRC/IS) para contas usadas em
		# linhas de Sales Taxes and Charges com is_tax_withholding_account=1
		# (campo nativo do ERPNext). Independente de at_tax_type - uma
		# conta de retenção não é em si uma conta de IVA/Imposto do Selo.
		# Sem correspondência automática possível a partir do ERPNext
		# (não há forma fiável de inferir IRS vs IRC vs IS a partir da
		# configuração nativa de Tax Withholding Category) - cada conta
		# de retenção tem de ser configurada manualmente. Ver
		# saft_generator.py::_withholding_tax_rows, que só popula
		# WithholdingTaxType no SAF-T quando este campo está preenchido
		# (é opcional no XSD).
		"fieldname": "at_withholding_tax_type",
		"label": "Tipo de Retenção na Fonte AT",
		"fieldtype": "Select",
		"options": "\nIRS\nIRC\nIS",
		"insert_after": "at_stamp_duty_verba",
		"module": "Portugal Compliance",
	},
]

EXEMPTION_REASON_FIELD = {
	"fieldname": "at_exemption_reason",
	"label": "Motivo de Isenção AT",
	"fieldtype": "Link",
	"options": "AT Tax Exemption",
	"insert_after": "item_tax_template",
	"description": "Obrigatório quando a taxa de IVA desta linha é 0% (Portaria 302/2016)",
	"module": "Portugal Compliance",
}


def create_at_tax_custom_fields():
	"""
	Custom Fields da taxonomia AT. Idempotente (create_custom_fields
	só cria o que ainda não existe). Chamado a partir de after_install
	e disponível para reexecução manual em sites já instalados.
	"""
	create_custom_fields({"Account": ACCOUNT_CUSTOM_FIELDS}, ignore_validate=True)
	create_custom_fields({
		"Sales Invoice Item": [EXEMPTION_REASON_FIELD],
		"Delivery Note Item": [EXEMPTION_REASON_FIELD],
	}, ignore_validate=True)


def _get_or_create_snc_tax_account(company, region, spec):
	"""
	Devolve (criando se necessário) a sub-conta SNC 2433x para esta
	região+taxa, convertendo 2433/2434/2435 de conta-folha para
	conta-grupo na primeira utilização. Ver análise: 2433 já existe
	no Plano de Contas SNC carregado pelo ERPNext para País=Portugal,
	mas como conta-folha única e sem tagging - nunca fora usada pelo
	setup anterior, que caía antes na conta genérica "Duties and Taxes".
	"""
	company_abbr = frappe.get_cached_value("Company", company, "abbr")
	parent_prefix = REGION_ACCOUNT_PREFIX[region]
	parent_name = None

	# Localizar a conta-pai pelo número de conta (mais fiável que o nome,
	# que inclui o abbr da empresa e pode variar).
	parent_candidates = frappe.get_all(
		"Account",
		filters={"company": company, "account_number": parent_prefix},
		fields=["name", "is_group"],
		limit=1,
	)
	if not parent_candidates:
		frappe.log_error(
			f"Conta SNC {parent_prefix} não encontrada para {company} - "
			f"o Plano de Contas SNC pode não estar carregado (verifique "
			f"Company.chart_of_accounts).",
			"Portugal Compliance - Tax Setup",
		)
		return None

	parent = parent_candidates[0]
	if not parent.is_group:
		frappe.db.set_value("Account", parent.name, "is_group", 1)
		frappe.db.commit()
	parent_name = parent.name

	account_number = f"{parent_prefix}{spec['account_suffix']}"
	account_name = f"{account_number} - IVA Liquidado {spec['rate']}% {spec['label']} - {company_abbr}"

	existing = frappe.get_all(
		"Account",
		filters={"company": company, "account_number": account_number},
		fields=["name"],
		limit=1,
	)
	if existing:
		return existing[0].name

	acc = frappe.get_doc({
		"doctype": "Account",
		"account_name": f"IVA Liquidado {spec['rate']}% {spec['label']}",
		"account_number": account_number,
		"company": company,
		"parent_account": parent_name,
		"account_type": "Tax",
		"is_group": 0,
		"at_tax_type": "IVA",
		"at_tax_region": region,
		"at_tax_code": spec["code"],
	})
	acc.insert(ignore_permissions=True)
	return acc.name


def setup_tax_templates_for_company(company, region="PT"):
	"""
	Cria, para uma região, as sub-contas SNC 2433x, os Sales Taxes and
	Charges Template e os Item Tax Template por taxa - tudo já ligado
	aos Custom Fields da taxonomia AT. Idempotente.
	"""
	if region not in AT_TAX_TAXONOMY:
		frappe.throw(_("Região fiscal desconhecida: {0}").format(region))

	created = []
	for spec in AT_TAX_TAXONOMY[region]:
		account = _get_or_create_snc_tax_account(company, region, spec)
		if not account:
			continue

		region_suffix = "" if region == "PT" else f" {region}"
		template_title = f"IVA {spec['rate']}% {spec['label']}{region_suffix} - {company}"

		# frappe.db.exists(doctype, name) verificaria pela CHAVE PRIMÁRIA -
		# mas Sales Taxes and Charges Template/Item Tax Template sobrescrevem
		# autoname() para name = f"{title} - {company_abbr}" (ver
		# erpnext/accounts/doctype/.../*.py), nunca == title sozinho. Um
		# exists() por name comparado com template_title (sem abbr) nunca
		# encontra o registo já criado - ficava sempre False e tentava
		# reinserir, só não rebentando à primeira chamada (ativação,
		# corre uma única vez) porque nunca havia colisão ainda; expôs-se
		# como IntegrityError assim que passou a haver uma via de
		# reexecução real (botão manual / reativação de Madeira-Açores,
		# 2026-08-29). Filtrar pelo campo title (não pela chave) é
		# imune ao sufixo de abbr gerado no autoname.
		if not frappe.db.exists("Sales Taxes and Charges Template", {"title": template_title, "company": company}):
			frappe.get_doc({
				"doctype": "Sales Taxes and Charges Template",
				"title": template_title,
				"company": company,
				"taxes": [{
					"charge_type": "On Net Total",
					"account_head": account,
					"description": f"IVA {spec['rate']}% ({spec['label']})",
					"rate": spec["rate"],
				}],
			}).insert(ignore_permissions=True)
			created.append(template_title)

		if not frappe.db.exists("Item Tax Template", {"title": template_title, "company": company}):
			frappe.get_doc({
				"doctype": "Item Tax Template",
				"title": template_title,
				"company": company,
				"taxes": [{"tax_type": account, "tax_rate": spec["rate"]}],
			}).insert(ignore_permissions=True)

	frappe.db.commit()
	return created


def create_regional_tax_setup_for_company(company):
	"""
	Cria os templates fiscais das 3 regiões AT (Continente, Madeira,
	Açores) para uma empresa - reutiliza setup_tax_templates_for_company,
	só remove a limitação anterior de "Continente incondicional". Chamada
	tanto pela ativação automática do compliance (_execute_compliance_setup)
	como pelo botão manual "Gerar Séries/Taxas Regionais" (para empresas
	já ativas que só tenham os 4 templates de Continente). Idempotente -
	seguro reexecutar em qualquer estado.
	"""
	created = {}
	for region in AT_TAX_TAXONOMY:
		try:
			created[region] = setup_tax_templates_for_company(company, region=region)
		except Exception as e:
			frappe.log_error(
				f"Erro ao configurar taxonomia AT de IVA ({region}) para {company}: {str(e)}",
				"Portugal Compliance - Tax Setup",
			)
			created[region] = {"error": str(e)}
	return created


# ========== TAX CATEGORY (sugestão automática em Customer/Supplier) ==========
# Nomes exatos que public/js/customer.js::suggest_tax_category e
# public/js/supplier.js::suggest_tax_category procuram via
# frappe.client.get_value antes de sugerir frm.tax_category (2026-08-30,
# auditoria pre-implementacao: confirmado por grep que NENHUM outro
# ponto do codigo - nomeadamente document_hooks.py, onde vive a
# validacao de NIF>1000e - depende de Tax Category existir; e uma
# conveniencia cosmetica de UI, que ate aqui degradava em silencio
# (a sugestao simplesmente nunca aparecia) quando os registos nao
# existiam, sem nunca bloquear nada).
DEFAULT_TAX_CATEGORIES = [
	"Portugal - Individual",
	"Portugal - Empresa",
	"Portugal - Geral",
	"Portugal - Fornecedor",
]


def setup_default_tax_categories():
	"""
	Garante que os 4 registos de Tax Category usados pela sugestao
	automatica de categoria fiscal (Customer/Supplier, ao definir
	Território/País = Portugal) existem - sem isto, a app exigia que o
	utilizador os criasse manualmente para a sugestao funcionar, o que
	nao e aceitavel num onboarding "Zero Touch" de SaaS.

	Tax Category e um doctype global do ERPNext (so title/disabled, sem
	campo company) - por isso esta funcao nao recebe nem precisa de
	parametro de empresa; corre uma vez, com efeito para o site
	inteiro, chamada a partir de _execute_compliance_setup() sempre que
	o compliance e ativado para qualquer empresa. Idempotente via
	frappe.db.exists - seguro chamar em todas as ativacoes.
	"""
	created = []
	for title in DEFAULT_TAX_CATEGORIES:
		if frappe.db.exists("Tax Category", title):
			continue
		try:
			frappe.get_doc({
				"doctype": "Tax Category",
				"title": title,
			}).insert(ignore_permissions=True)
			created.append(title)
		except Exception as e:
			frappe.log_error(
				f"Erro ao criar Tax Category '{title}': {str(e)}",
				"Portugal Compliance - Tax Setup",
			)
	return {"created": created}
