# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Customer Query for Portugal Compliance - ENGLISH NAMING CONVENTION
Baseado na sua experiência com programação.sistemas_erp[3]
"""

import frappe
from frappe import _

@frappe.whitelist()
def customer_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    ✅ ENGLISH: Query for customer search with Portuguese validations
    Uses native naming series format (without hyphens)
    """
    try:
        return frappe.db.sql("""
            SELECT name, customer_name, customer_group, tax_id
            FROM `tabCustomer`
            WHERE (customer_name LIKE %(txt)s OR name LIKE %(txt)s OR tax_id LIKE %(txt)s)
            AND disabled = 0
            ORDER BY
                CASE WHEN name LIKE %(txt)s THEN 0 ELSE 1 END,
                customer_name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)

    except Exception as e:
        frappe.log_error(f"Error in customer_query: {str(e)}")
        return frappe.db.sql("""
            SELECT name, customer_name, customer_group
            FROM `tabCustomer`
            WHERE customer_name LIKE %(txt)s
            AND disabled = 0
            ORDER BY customer_name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)

@frappe.whitelist()
def supplier_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    ✅ ENGLISH: Query for supplier search with Portuguese validations
    """
    try:
        return frappe.db.sql("""
            SELECT name, supplier_name, supplier_group, tax_id
            FROM `tabSupplier`
            WHERE (supplier_name LIKE %(txt)s OR name LIKE %(txt)s OR tax_id LIKE %(txt)s)
            AND disabled = 0
            ORDER BY supplier_name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)

    except Exception as e:
        frappe.log_error(f"Error in supplier_query: {str(e)}")
        return []
