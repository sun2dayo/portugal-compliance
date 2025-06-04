# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def get_data():
    return {
        "Portugal Compliance": {
            "color": "green",
            "icon": "octicon octicon-law",
            "type": "module",
            "label": _("Portugal Compliance"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Portugal Series Configuration",
                    "label": _("Series Configuration"),
                    "description": _("Configure document series for AT communication")
                },
                {
                    "type": "doctype",
                    "name": "Portugal Auth Settings",
                    "label": _("Auth Settings"),
                    "description": _("Configure AT authentication settings")
                },
                {
                    "type": "doctype",
                    "name": "ATCUD Log",
                    "label": _("ATCUD Log"),
                    "description": _("View ATCUD generation logs")
                },
                {
                    "type": "doctype",
                    "name": "SAF-T Export Log",
                    "label": _("SAF-T Export Log"),
                    "description": _("View SAF-T export history")
                },
                {
                    "type": "page",
                    "name": "portugal-compliance-dashboard",
                    "label": _("Compliance Dashboard"),
                    "description": _("Portugal compliance overview")
                },
                {
                    "type": "report",
                    "name": "Portugal Tax Report",
                    "label": _("Tax Report"),
                    "description": _("Generate Portugal tax reports")
                }
            ]
        }
    }
