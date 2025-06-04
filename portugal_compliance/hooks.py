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
    "/assets/portugal_compliance/js/portugal_compliance.js",
    "/assets/portugal_compliance/js/company.js"
]

web_include_css = [
    "/assets/portugal_compliance/css/portugal_compliance.css"
]

web_include_js = [
    "/assets/portugal_compliance/js/portugal_compliance.js",
    "/assets/portugal_compliance/js/company.js"
]

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
after_install = "portugal_compliance.regional.portugal.after_install"
before_uninstall = "portugal_compliance.regional.portugal.before_uninstall"

# ✅ MIGRATION HOOKS
#after_migrate = "portugal_compliance.utils.migrate_to_native_approach.sync_all_naming_series_after_migrate"

# ✅ DOCUMENT EVENTS - CORRIGIDO (estrutura simplificada)
doc_events = {
	# ========== DOCUMENTOS FISCAIS CRÍTICOS ==========
	"Sales Invoice": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},
	"Purchase Invoice": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},
	"POS Invoice": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},
	"Payment Entry": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},

	# ========== DOCUMENTOS DE TRANSPORTE ==========
	"Delivery Note": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},
	"Purchase Receipt": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},
	"Stock Entry": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},

	# ========== DOCUMENTOS CONTABILÍSTICOS ==========
	"Journal Entry": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
		"before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
		"after_insert": "portugal_compliance.utils.document_hooks.generate_atcud_after_insert"
	},

	# ========== DOCUMENTOS COMERCIAIS ==========
	"Quotation": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance"
	},
	"Sales Order": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance"
	},
	"Purchase Order": {
		"before_save": "portugal_compliance.utils.document_hooks.set_portugal_series_and_atcud",
		"validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance"
	},

	# ========== CONFIGURAÇÃO DA EMPRESA ==========
	"Company": {
		"on_update": "portugal_compliance.utils.document_hooks.setup_company_portugal_compliance",
		"validate": "portugal_compliance.regional.portugal.validate_portugal_company_settings"
	},

	# ========== VALIDAÇÃO DE ENTIDADES ==========
	"Customer": {
		"validate": "portugal_compliance.utils.document_hooks.validate_customer_nif"
	},
	"Supplier": {
		"validate": "portugal_compliance.utils.document_hooks.validate_supplier_nif"
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
override_doctype_class = {
	"Sales Invoice": "portugal_compliance.overrides.sales_invoice.CustomSalesInvoice"
}

# ✅ OVERRIDE WHITELISTED METHODS
override_whitelisted_methods = {
	"frappe.core.doctype.communication.email.make": "portugal_compliance.email.make_portugal_compliant_email"
}

# ✅ SCHEDULED TASKS
#scheduler_events = {
#	"daily": [
#		"portugal_compliance.utils.maintenance.daily_compliance_check",
#		"portugal_compliance.utils.maintenance.validate_atcud_integrity"
#	],
#	"weekly": [
#		"portugal_compliance.utils.maintenance.weekly_series_sync"
#	],
#	"monthly": [
#		"portugal_compliance.utils.maintenance.monthly_compliance_audit"
#	]
#}

# ✅ FIXTURES - SIMPLIFICADO
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["module", "in", ["Portugal Compliance"]]
		]
	}
]

# ✅ JINJA METHODS - ESSENCIAIS
jinja = {
	"methods": [
		# ✅ MÉTODOS ATCUD
		"portugal_compliance.utils.jinja_methods.get_atcud_code",
		"portugal_compliance.utils.jinja_methods.format_atcud_display",

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

		# ✅ MÉTODOS DE DOCUMENTOS
		"portugal_compliance.utils.jinja_methods.get_document_type_description",
		"portugal_compliance.utils.jinja_methods.format_tax_breakdown",

		# ✅ MÉTODOS QR CODE
		"portugal_compliance.utils.jinja_methods.get_qr_code_data",
		"portugal_compliance.utils.jinja_methods.generate_qr_code_image"
	]
}

# ✅ BACKGROUND JOBS
background_jobs = {
	"portugal_compliance.utils.at_webservice.batch_register_naming_series": {"timeout": 1800},
	"portugal_compliance.utils.atcud_generator.batch_generate_atcud": {"timeout": 1200}
}

# ✅ REGIONAL SETTINGS
regional_overrides = {
	"Portugal": {
		"get_series": "portugal_compliance.regional.portugal.get_series",
		"validate_tax_id": "portugal_compliance.utils.validation.validate_portuguese_nif",
		"get_tax_template": "portugal_compliance.regional.portugal.get_tax_template_for_transaction",
		"format_currency": "portugal_compliance.utils.formatting.format_portuguese_currency",
		"currency": "EUR",
		"date_format": "dd/MM/yyyy",
		"time_format": "HH:mm:ss",
		"number_format": "#.###,##",
		"first_day_of_the_week": "Monday"
	}
}

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
startup_hooks = [
	"portugal_compliance.utils.startup.validate_portugal_compliance_setup"
]

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

# ✅ WEBSITE CONTEXT
website_context = {
	"favicon": "/assets/portugal_compliance/images/favicon.ico",
	"splash_image": "/assets/portugal_compliance/images/portugal_compliance_logo.png"
}

# ✅ CALENDARS
calendars = ["ATCUD Log"]

# ✅ DASHBOARD DATA
dashboard_data = {
	"Portugal Compliance": "portugal_compliance.dashboards.get_dashboard_data"
}

# ✅ STANDARD QUERIES
standard_queries = {
	"Customer": "portugal_compliance.queries.customer_query",
	"Supplier": "portugal_compliance.queries.supplier_query"
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
