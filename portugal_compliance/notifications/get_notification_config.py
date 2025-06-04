# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_notification_config():
    return {
        "for_doctype": {},
        "for_module_doctypes": {
            "Portugal Compliance": "red"
        }
    }
