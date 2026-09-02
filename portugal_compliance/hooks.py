# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt
#HOOKS OPERACIONAL
"""
Hooks Configuration for Portugal Compliance - VERSÃO NATIVA CERTIFICADA
Integra lógica testada da versão anterior com naming_series nativas
✅ Compliance inviolável com séries comunicadas
✅ ATCUD automático conforme legislação portuguesa
✅ Configuração automática completa
"""

from __future__ import unicode_literals
import frappe
from frappe import _

app_name = "portugal_compliance"
app_title = "Portugal Compliance"
app_publisher = "NovaDX - Octávio Daio"
app_description = "Compliance with Portuguese fiscal regulations (ATCUD, SAFT-PT, QR-Code, Digital Signatures, Audit Trail) - Native ERPNext Integration"
app_icon = "octicon octicon-law"
app_color = "green"
app_email = "compliance@novadx.pt"
app_license = "MIT"
app_version = "2.0.0"

# ✅ REQUIRED APPS
required_apps = ["frappe", "erpnext"]

# ✅ INCLUDES CSS/JS - CORRIGIDO E COMPLETO
app_include_css = [
    "/assets/portugal_compliance/css/portugal_compliance.css"
]

app_include_js = [
    "/assets/portugal_compliance/js/portugal_compliance.js"
]
# company.js removido daqui: chama frappe.ui.form.on(), que so existe
# no contexto do Desk. Carregado globalmente (incluindo na pagina de
# login publica) rebentava com "frappe.ui.form.on is not a function".
# Continua correctamente registado abaixo em doctype_js, scoped so ao
# formulario de Company.

web_include_css = [
    "/assets/portugal_compliance/css/portugal_compliance.css"
]

# web_include_js vazio: portugal_compliance.js chama frappe.ui.form.on()
# dentro de init() -> initializeValidators(), que so funciona no contexto
# do Desk (onde a framework de formularios esta totalmente carregada).
# Nas paginas publicas (ex: login), frappe.ui.form existe como objeto mas
# sem o metodo .on(), o que passava a guarda defensiva do ficheiro e
# crashava. Mantido em app_include_js (Desk), removido daqui.
web_include_js = []

# ✅ DOCTYPE JS - CORRIGIDO (era lista, agora é dicionário)
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Purchase Invoice": "public/js/purchase_invoice.js",
	"POS Invoice": "public/js/pos_invoice.js",
	"Quotation": "public/js/quotation.js",
	"Sales Order": "public/js/sales_order.js",
	"Purchase Order": "public/js/purchase_order.js",
	"Payment Entry": "public/js/payment_entry.js",
	"Delivery Note": "public/js/delivery_note.js",
	"Purchase Receipt": "public/js/purchase_receipt.js",
	"Stock Entry": "public/js/stock_entry.js",
	"Journal Entry": "public/js/journal_entry.js",
	"Company": "public/js/company.js",
	"Customer": "public/js/customer.js",
	"Supplier": "public/js/supplier.js"
}

# ✅ INSTALAÇÃO E DESINSTALAÇÃO
after_install = [
    "portugal_compliance.regional.portugal.after_install",
    "portugal_compliance.utils.startup_fixes.run_all_startup_fixes",
    "portugal_compliance.setup.tax_setup.create_at_tax_custom_fields"
]

before_uninstall = "portugal_compliance.regional.portugal.before_uninstall"

# ✅ HOOK PARA ATUALIZAÇÕES
after_app_install = [
    "portugal_compliance.utils.startup_fixes.setup_naming_series_property_setters"
]

# ✅ MIGRATION HOOKS
after_migrate = [
    "portugal_compliance.utils.startup_fixes.fix_customer_search_on_startup",
	"portugal_compliance.utils.startup_fixes.setup_naming_series_property_setters",
	"portugal_compliance.utils.document_hooks.force_track_changes_property_setters",
	"portugal_compliance.utils.document_hooks.set_pos_invoice_default_print_format",
	"portugal_compliance.utils.native_print_format_compliance.ensure_native_print_formats_compliant"
]


# ✅ DOCUMENT EVENTS - VERSÃO CORRIGIDA E SEGURA
# Baseado nos testes bem-sucedidos com programação.teste_no_console
doc_events = {
	# ========== DOCUMENTOS FISCAIS CRÍTICOS ==========
	# NOTA (2026-08-24, correcao "rascunho zombie"): o ATCUD/assinatura/
	# QR Code deixaram de ser gerados em before_save/after_insert (ou
	# seja, em qualquer gravacao de rascunho) e passaram a ser gerados
	# so em on_submit, sempre listado por ultimo nesse evento - depois
	# de qualquer logica nativa do ERPNext e de before_submit_document
	# (validacoes rigidas) ja terem corrido sem erro. Ver
	# document_hooks.generate_atcud_on_submit para o detalhe e o motivo.
	"Sales Invoice": {
		"before_insert": [
			"portugal_compliance.utils.document_hooks.reset_fiscal_fields_on_return_clone",
			"portugal_compliance.utils.document_hooks.before_insert_document"
		],
		"before_save": "portugal_compliance.utils.document_hooks.enforce_fiscal_field_lock",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"before_print": "portugal_compliance.utils.document_hooks.log_document_print",
		"on_submit": [
			"portugal_compliance.utils.document_hooks.generate_atcud_on_submit",
			"portugal_compliance.utils.at_invoice_webservice.enqueue_invoice_communication"
		],
		"on_trash": "portugal_compliance.utils.document_hooks.block_fiscal_document_deletion",
		"on_cancel": [
			"portugal_compliance.utils.document_hooks.log_document_cancellation",
			"portugal_compliance.utils.at_invoice_webservice.enqueue_invoice_cancellation"
		]
	},
	# Purchase Invoice removida deste bloco (2026-08-22): ATCUD/
	# assinatura RSA/series aplicam-se por lei a documentos EMITIDOS a
	# clientes (Portaria 195/2020), nunca a faturas de compra RECEBIDAS
	# de fornecedores - a responsabilidade fiscal desse documento e de
	# quem o emitiu. Nunca teve serie comunicada (nem devia), so o
	# ATCUD/assinatura local eram gerados indevidamente. Ver
	# document_hooks.py: entrada "Purchase Invoice" removida de
	# supported_doctypes no mesmo commit.
	"POS Invoice": {
		"before_insert": [
			"portugal_compliance.utils.document_hooks.reset_fiscal_fields_on_return_clone",
			"portugal_compliance.utils.document_hooks.before_insert_document"
		],
		"before_save": "portugal_compliance.utils.document_hooks.enforce_fiscal_field_lock",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"before_print": "portugal_compliance.utils.document_hooks.log_document_print",
		"on_submit": [
			"portugal_compliance.utils.document_hooks.generate_atcud_on_submit",
			"portugal_compliance.utils.at_invoice_webservice.enqueue_invoice_communication"
		],
		"on_trash": "portugal_compliance.utils.document_hooks.block_fiscal_document_deletion",
		"on_cancel": "portugal_compliance.utils.document_hooks.log_document_cancellation"
	},
	"Payment Entry": {
		"before_insert": "portugal_compliance.utils.document_hooks.before_insert_document",
		"before_save": "portugal_compliance.utils.document_hooks.enforce_fiscal_field_lock",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"before_print": "portugal_compliance.utils.document_hooks.log_document_print",
		"on_submit": "portugal_compliance.utils.document_hooks.generate_atcud_on_submit",
		"on_trash": "portugal_compliance.utils.document_hooks.block_fiscal_document_deletion",
		"on_cancel": "portugal_compliance.utils.document_hooks.log_document_cancellation"
	},

	# ========== DOCUMENTOS DE TRANSPORTE ==========
	"Delivery Note": {
		"before_insert": [
			"portugal_compliance.utils.document_hooks.reset_fiscal_fields_on_return_clone",
			"portugal_compliance.utils.document_hooks.before_insert_document"
		],
		"before_save": "portugal_compliance.utils.document_hooks.enforce_fiscal_field_lock",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": [
			"portugal_compliance.utils.document_hooks.before_submit_document",
			"portugal_compliance.utils.document_hooks.validate_transport_start_time"
		],
		"before_print": "portugal_compliance.utils.document_hooks.log_document_print",
		"on_submit": [
			"portugal_compliance.utils.document_hooks.generate_atcud_on_submit",
			"portugal_compliance.utils.at_transport_webservice.enqueue_transport_communication"
		],
		"on_trash": "portugal_compliance.utils.document_hooks.block_fiscal_document_deletion",
		"on_cancel": "portugal_compliance.utils.document_hooks.log_document_cancellation"
	},
	# Purchase Receipt, Stock Entry e Journal Entry removidos deste bloco
	# (2026-08-22): ATCUD/assinatura RSA aplicam-se por lei a documentos
	# EMITIDOS a terceiros (Portaria 195/2020), nunca a receções de
	# compra, movimentos internos de stock ou lançamentos contabilísticos.
	# Nenhum dos três teve alguma vez série comunicada à AT (nem devia) -
	# Purchase Receipt já era código morto (nunca esteve em
	# supported_doctypes); Stock Entry e Journal Entry geravam ATCUD/
	# assinatura local sem necessidade legal. Ver document_hooks.py:
	# entradas removidas de supported_doctypes no mesmo commit. Os
	# registos já existentes em ATCUD Log destes doctypes mantêm-se
	# intactos para efeitos de auditoria.

	# Quotation/Sales Order/Purchase Order/Material Request: hook de
	# validate removido (2026-08-30). Só existia para mostrar "Esta
	# série não segue o formato de série portuguesa recomendado" -
	# ecoava, do lado do servidor, exatamente a mesma nagging de série
	# fiscal que já tínhamos removido do lado do cliente nestes 5
	# doctypes (ver commit 700e2d6, portugal_compliance.js). Confirmado
	# ao vivo pelo utilizador: aparecia em quase todas as criações/
	# submissões de Quotation, Sales Order e Purchase Order mesmo com
	# série nativa do ERPNext - nao deveria ser mais aplicavel, dado que
	# nenhum destes doctypes é fiscal (ver nota acima) e usar séries
	# nativas passou a ser o comportamento esperado, não um desvio a
	# assinalar. validate_portugal_compliance_light() removida de
	# document_hooks.py no mesmo commit (não tinha mais nenhuma lógica).

	# ========== CONFIGURAÇÃO DA EMPRESA ==========
	"Company": {
		"on_update": "portugal_compliance.utils.document_hooks.setup_company_portugal_compliance",
		# sync_at_credentials removido (2026-08-23) e sync_communication_settings
		# removido (2026-08-30): Company deixou de ter campos de
		# credenciais/métodos de comunicação AT - Portugal Auth Settings é
		# a única fonte de verdade. Ver document_hooks.py.
		"validate": [
			"portugal_compliance.regional.portugal.validate_portugal_company_settings_safe",
			"portugal_compliance.utils.document_hooks.validate_company_fiscal_lock"
		]
	},

	# ========== VALIDAÇÃO DE ENTIDADES ==========
	"Customer": {
		"validate": "portugal_compliance.utils.document_hooks.validate_customer_nif"
	},
	"Supplier": {
		"validate": "portugal_compliance.utils.document_hooks.validate_supplier_nif"
	},

	# ========== CONFIGURAÇÃO DE SÉRIES PORTUGUESAS ==========
	"Portugal Series Configuration": {
		"validate": "portugal_compliance.utils.document_hooks.validate_series_configuration",
		"before_save": "portugal_compliance.utils.document_hooks.update_series_pattern"
	}
}


# ✅ PERMISSIONS
permission_query_conditions = {
	"Portugal Series Configuration": "portugal_compliance.queries.has_permission_for_series.get_permission_query_conditions",
	"ATCUD Log": "portugal_compliance.queries.has_permission_for_atcud.get_permission_query_conditions"
}

has_permission = {
	"Portugal Series Configuration": "portugal_compliance.queries.has_permission_for_series.has_permission",
	"ATCUD Log": "portugal_compliance.queries.has_permission_for_atcud.has_permission"
}

# ✅ OVERRIDE DOCTYPE CLASS
# override_doctype_class removido: apontava para
# "portugal_compliance.overrides.sales_invoice.CustomSalesInvoice", uma
# classe que nunca existiu (a classe real chama-se
# SalesInvoicePortugalCompliance, nao subclassa SalesInvoice e nunca e
# instanciada em lado nenhum do codigo). A validacao/geracao de ATCUD
# para Sales Invoice ja e feita via doc_events (document_hooks.py),
# que e o mecanismo correto para isto - override_doctype_class so
# deve ser usado quando e mesmo preciso substituir metodos do
# controller, e nesse caso so uma app pode ser "dona" do doctype.
override_doctype_class = {}

# ✅ OVERRIDE WHITELISTED METHODS
# override_whitelisted_methods removido (Auditoria Fase 0, 2026-08-26):
# apontava para "portugal_compliance.email.make_portugal_compliant_email",
# uma funcao que nunca existiu em email.py. frappe.handler resolve
# override_whitelisted_methods em TODOS os pedidos a
# frappe.core.doctype.communication.email.make (usado pelo botao nativo
# "New Email"/"Compose Email", disponivel em praticamente todos os
# doctypes) - confirmado ao vivo que isto rebentava com AttributeError
# em qualquer tentativa de enviar email a partir do Desk, em qualquer
# empresa do site, portuguesa ou nao. Nao ha nenhuma customizacao real
# de email por tras deste override para recuperar - so remover.
override_whitelisted_methods = {}

# ✅ SCHEDULED TASKS
# Liga o subsistema tasks/ (Fase 3) - estava construido mas nunca
# tinha sido ativado. O bloco anterior (comentado) apontava para
# portugal_compliance.utils.maintenance, um modulo que nunca existiu
# neste repositorio; substituido pelos modulos reais em tasks/.
scheduler_events = {
	"all": ["portugal_compliance.tasks.all.execute"],
	"hourly": ["portugal_compliance.tasks.hourly.execute"],
	"daily": ["portugal_compliance.tasks.daily.execute"],
	"weekly": ["portugal_compliance.tasks.weekly.execute"],
	"monthly": ["portugal_compliance.tasks.monthly.execute"],
	"yearly": ["portugal_compliance.tasks.yearly.execute"]
}

#  FIXTURES - SIMPLIFICADO
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["module", "in", ["Portugal Compliance"]]
		]
	},
	{
		# Motivos de isenção de IVA (M01, M02...) - taxonomia AT, dados
		# de referência estáticos, corretamente geridos como fixture em
		# vez de lógica de instalação (ver blueprint da Fase 7).
		"dt": "AT Tax Exemption"
	},
	{
		# Print Format Factura PT (Fase 6) precisa de ficar aqui para
		# sobreviver a uma reinstalacao limpa da app - sem isto, o
		# QR Code na fatura impressa desaparecia em qualquer site novo.
		"dt": "Print Format",
		"filters": [
			["module", "in", ["Portugal Compliance"]]
		]
	},
	{
		# Workspace de navegacao central do modulo - sem isto, uma
		# reinstalacao limpa da app deixava o utilizador sem o
		# workspace, obrigado a procurar Logs/Settings na pesquisa.
		"dt": "Workspace",
		"filters": [
			["module", "=", "Portugal Compliance"]
		]
	},
	{
		# Property Setters do modulo: read_only/description do campo
		# atcud_code, default de portugal_compliance_enabled, e o
		# default_print_format dos 3 doctypes com Print Format proprio
		# (Sales Invoice -> Factura PT, POS Invoice ->
		# Fatura Simplificada PT, Payment Entry -> Recibo PT) - sem
		# isto, uma reinstalacao limpa da app perdia o Print Format
		# predefinido e o utilizador via o print generico do Frappe em
		# vez do documento fiscal certificado.
		# Filtro por "name" (nao por doc_type/property) para nao
		# arrastar Property Setters de outras apps/configuracoes do
		# site - so exporta exatamente os que este modulo cria.
		"dt": "Property Setter",
		"filters": [
			["name", "in", [
				"Sales Invoice-atcud_code-read_only",
				"Sales Invoice-atcud_code-description",
				"POS Invoice-atcud_code-read_only",
				"Purchase Invoice-atcud_code-read_only",
				"Payment Entry-atcud_code-read_only",
				"Company-portugal_compliance_enabled-default",
				"Sales Invoice-main-default_print_format",
				"POS Invoice-main-default_print_format",
				"Payment Entry-main-default_print_format",
				"Delivery Note-main-default_print_format",
			]]
		]
	},
	{
		# Workspace Sidebar + Desktop Icon: sem estes dois registos o
		# Workspace "Portugal Compliance" existe mas fica invisivel no
		# ecra inicial do Desk (bug encontrado em 2026-08-22) - o Frappe
		# v16 só descobre um Workspace automaticamente via
		# `bench new-site` (create_workspace_sidebar_for_workspaces /
		# create_desktop_icons_from_workspace correm uma única vez nesse
		# momento); instalar a app num site já existente nunca gera
		# estes dois registos. Exportados por `app` para não arrastar os
		# equivalentes nativos do frappe/erpnext.
		"dt": "Workspace Sidebar",
		"filters": [
			["app", "=", "portugal_compliance"]
		]
	},
	{
		"dt": "Desktop Icon",
		"filters": [
			["app", "=", "portugal_compliance"]
		]
	}
]

# ✅ JINJA METHODS - ESSENCIAIS
jinja = {
	"methods": [
		# ✅ MÉTODOS ATCUD
		"portugal_compliance.utils.jinja_methods.get_atcud_code",
		"portugal_compliance.utils.jinja_methods.format_atcud_display",
		"portugal_compliance.utils.jinja_methods.get_signature_hash_control",
		"portugal_compliance.utils.jinja_methods.get_document_title",

		# ✅ MÉTODOS NAMING_SERIES
		"portugal_compliance.utils.jinja_methods.get_naming_series",
		"portugal_compliance.utils.jinja_methods.get_series_prefix",
		"portugal_compliance.utils.jinja_methods.is_portuguese_series",

		# ✅ MÉTODOS DE FORMATAÇÃO
		"portugal_compliance.utils.jinja_methods.format_portuguese_date",
		"portugal_compliance.utils.jinja_methods.format_portuguese_currency",

		# ✅ MÉTODOS DE VALIDAÇÃO
		"portugal_compliance.utils.jinja_methods.validate_portuguese_nif",
		"portugal_compliance.utils.jinja_methods.get_company_nif",
		"portugal_compliance.utils.jinja_methods.get_customer_nif",
		"portugal_compliance.utils.jinja_methods.get_supplier_nif",

		# ✅ MÉTODOS DE ENDEREÇOS
		"portugal_compliance.utils.jinja_methods.get_company_address_formatted",
		"portugal_compliance.utils.jinja_methods.get_party_address_formatted",

		# ✅ MÉTODOS DE DOCUMENTOS
		"portugal_compliance.utils.jinja_methods.get_document_type_description",
		"portugal_compliance.utils.jinja_methods.get_item_effective_tax_rate",
		"portugal_compliance.utils.tax_breakdown.get_tax_breakdown_by_at_code",
		"portugal_compliance.utils.jinja_methods.format_tax_breakdown",

		# ✅ MÉTODOS QR CODE
		"portugal_compliance.utils.jinja_methods.get_qr_code_data",
		"portugal_compliance.utils.jinja_methods.generate_qr_code_image",

		# ✅ RODAPÉ LEGAL - versão dos módulos (frappe.get_attr não está
		# disponível no sandbox Jinja dos Print Formats)
		"portugal_compliance.utils.jinja_methods.get_compliance_version_notice"
	]
}

# ✅ BACKGROUND JOBS
background_jobs = {
	"portugal_compliance.utils.at_webservice.batch_register_naming_series": {"timeout": 1800},
	"portugal_compliance.utils.atcud_generator.batch_generate_atcud_optimized": {"timeout": 1200}
}

# regional_overrides removido (Fase 3): a estrutura de chaves nao
# correspondia ao mecanismo real do ERPNext (erpnext.allow_regional
# exige que a chave seja o caminho completo de uma funcao do core
# decorada com esse decorator - aqui eram nomes soltos como
# "get_series"/"currency", que nunca correspondem a nada). Nunca
# esteve funcional. Reimplementar a serio requer identificar quais
# funcoes do core ERPNext precisam mesmo de override para Portugal.

# ✅ WEBSITE SETTINGS
website_route_rules = [
	{"from_route": "/portugal-compliance/<path:app_path>", "to_route": "portugal-compliance"}
]

# ✅ DOMAINS
domains = {
	"Portugal Compliance": "portugal_compliance"
}

# ✅ BOOT SESSION
#boot_session = "portugal_compliance.utils.boot.boot_session"

# ✅ STARTUP HOOKS
# startup_hooks removido: nao e uma chave de hook consumida pelo
# Frappe core, e o ficheiro utils/startup.py (distinto de
# utils/startup_fixes.py, que esse existe) nunca existiu.

# ✅ SOUNDS
#sounds = [
#	{"name": "atcud-generated", "src": "/assets/portugal_compliance/sounds/success.mp3"},
#	{"name": "series-communicated", "src": "/assets/portugal_compliance/sounds/communication.mp3"},
#	{"name": "compliance-error", "src": "/assets/portugal_compliance/sounds/error.mp3"}
#]

# ✅ AUTO CANCEL EXEMPTED DOCTYPES
auto_cancel_exempted_doctypes = ["Auto Repeat", "ATCUD Log", "Portugal Series Configuration"]

# ✅ TRANSLATION FILES
translation_files = [
	"apps/portugal_compliance/translations"
]

# ✅ DEFAULT MAIL FOOTER
default_mail_footer = """
    <div style="padding: 7px; text-align: right; color: #888">
        <small>Enviado via Portugal Compliance para ERPNext</small>
    </div>
"""

# ✅ NOTIFICATION CONFIG
#notification_config = "portugal_compliance.notifications.get_notification_config"

# website_context removido (Fase 5): favicon.ico e
# portugal_compliance_logo.png nunca existiram no disco (referencias
# partidas desde sempre). O unico ficheiro de imagem real disponivel
# no repositorio (at_logo.png.tmp) e o logotipo oficial da Autoridade
# Tributaria - nao deve ser reutilizado aqui, pois sugeriria afiliacao
# oficial do governo com este software de terceiros.

# ✅ CALENDARS
calendars = ["ATCUD Log"]

# ✅ DASHBOARD DATA
dashboard_data = {
	"Portugal Compliance": "portugal_compliance.dashboards.company.get_dashboard_data"
}

# ✅ STANDARD QUERIES
standard_queries = {
	"Customer": "portugal_compliance.queries.customer.customer_query",
	"Supplier": "portugal_compliance.queries.customer.supplier_query"
}

# ✅ PORTAL MENU ITEMS
portal_menu_items = [
	{
		"title": "Documentos Fiscais",
		"route": "/compliance/documents",
		"reference_doctype": "Sales Invoice",
		"role": "Customer"
	}
]
# ✅ WHITELISTED METHODS - MANUAL (SOLUÇÃO PARA BUG DO DECORATOR)
whitelisted_methods = [
    "portugal_compliance.api.company_api.create_company_series",
    "portugal_compliance.api.company_api.get_company_compliance_status",
    "portugal_compliance.api.company_api.save_company_settings",
    "portugal_compliance.api.company_api.validate_company_for_compliance",
    "portugal_compliance.api.company_api.delete_company_series",
    "portugal_compliance.api.company_api.get_available_document_types",
    "portugal_compliance.utils.jinja_methods.validate_portuguese_nif"
]
