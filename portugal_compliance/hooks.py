app_name = "portugal_compliance"
app_title = "Portugal Compliance"
app_publisher = "NovaDX - Octávio Daio"
app_description = "Compliance with Portuguese fiscal regulations (ATCUD, SAFT-PT, Digital Signatures)."
app_email = "app@novadx.eu"
app_license = "gpl-3.0"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/portugal_compliance/css/portugal_compliance.css"
# app_include_js = "/assets/portugal_compliance/js/portugal_compliance.js"

# include js, css files in header of web_ όταν.html
# web_include_css = "/assets/portugal_compliance/css/portugal_compliance.css"
# web_include_js = "/assets/portugal_compliance/js/portugal_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "portugal_compliance/public/scss/website"

# include js, css files in header of web form theme
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#   "methods": "portugal_compliance.utils.jinja_methods",
#   "filters": "portugal_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "portugal_compliance.install.before_install"
# after_install = "portugal_compliance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "portugal_compliance.uninstall.before_uninstall"
# after_uninstall = "portugal_compliance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being integrated is given as static value
# Put static values if required for integration
# Format given below is example
# integration_setup = {
#   "my_app": {
#       "enable_integration": 1,
#       "another_value": 2
#   }
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#   "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ----------------
# Hook on document methods and events
doc_events = {
    "Sales Invoice": {
        "on_submit": [
            "portugal_compliance.api.signing_utils.process_sales_invoice_signature",
            "portugal_compliance.api.qrcode_atcud_utils.process_document_atcud_and_qr"
        ],
		# "validate": "portugal_compliance.portugal_compliance.api.signing_utils.validate_sales_invoice_for_signing",
		# "on_cancel": "portugal_compliance.portugal_compliance.api.signing_utils.handle_invoice_cancellation_log"
    }
}


    # Add other relevant doctypes like 'Credit Note', 'Delivery Note' etc.
    # "Credit Note": {
    #     "on_submit": [
    #         "portugal_compliance.portugal_compliance.api.signing_utils.process_credit_note_signature",
    #         "portugal_compliance.portugal_compliance.api.qrcode_atcud_utils.process_document_atcud_and_qr"
    #      ]
    # },
    # "Delivery Note": {
    #    "on_submit": [
    #         "portugal_compliance.portugal_compliance.api.signing_utils.process_delivery_note_signature",
    #         "portugal_compliance.portugal_compliance.api.qrcode_atcud_utils.process_document_atcud_and_qr"
    #      ]
    # }


# Scheduled Tasks
# ----------------

# scheduler_events = {
#   "all": [
#       "portugal_compliance.tasks.all"
#   ],
#   "daily": [
#       "portugal_compliance.tasks.daily"
#   ],
#   "hourly": [
#       "portugal_compliance.tasks.hourly"
#   ],
#   "weekly": [
#       "portugal_compliance.tasks.weekly"
#   ],
#   "monthly": [
#       "portugal_compliance.tasks.monthly"
#   ],
# }

# Testing
# -------

# before_tests = "portugal_compliance.install.before_tests"

# Overriding Methods
# --------------------
#
# override_whitelisted_methods = {
#   "frappe.desk.doctype.event.event.get_events": "portugal_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#   "Task": "portugal_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------
# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["portugal_compliance.utils.before_request"]
# after_request = ["portugal_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["portugal_compliance.utils.before_job"]
# after_job = ["portugal_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#   {
#       "doctype": "{doctype_name}",
#       "filter_by": "{filter_by}",
#       "redact_fields": ["{field_1}", "{field_2}"],
#       "partial": 1, # PII doesn't form part of critical data so can be removed without breaking integrity
#   },
#   {
#       "doctype": "{doctype_name}",
#       "filter_by": "{filter_by}",
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_name}",
#       "filter_by": "{filter_by}",
#       "field_mapping": {"field_1": "{field_2}"}
#   },
#   {
#       "doctype": "User",
#       "filter_by": "name",
#       "redact_fields": ["email", "mobile_no"]
#   }
# ]

# Fixtures
# --------
# Adding Custom Fields to standard DocTypes for Portugal Compliance
fixtures = [
    {"dt": "Custom Field", "filters": [
        ["module", "=", "Portugal Compliance"]
    ]},
    {"dt": "Property Setter", "filters": [
        ["module", "=", "Portugal Compliance"]
    ]}
]

# Caching
# --------

# Cache methods in this app. Define path to methods like so:
# "portugal_compliance.utils.get_cache_key": 300, # cache for 5 minutes
# cache_keys = {}

# Required Apps
# -------------
#required_apps = ["erpnext"]


add_to_apps_screen = 1

