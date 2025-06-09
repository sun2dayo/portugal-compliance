# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Queries for Portugal Compliance
Baseado na sua experiência com programação.autenticação[2]
"""

import frappe
from frappe import _
from frappe.utils import cstr

@frappe.whitelist()
def customer_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    ✅ Query para busca de clientes com validações portuguesas
    Baseado na sua experiência com programação.conformidade_portugal[5]
    """
    try:
        # ✅ QUERY PADRÃO PARA CUSTOMER
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
        frappe.log_error(f"Erro em customer_query: {str(e)}")
        # ✅ FALLBACK: Query básica
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
    ✅ Query para busca de fornecedores
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
        frappe.log_error(f"Erro em supplier_query: {str(e)}")
        return []

@frappe.whitelist()
def item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    ✅ Query para busca de itens
    """
    try:
        return frappe.db.sql("""
            SELECT name, item_name, item_group
            FROM `tabItem`
            WHERE (item_name LIKE %(txt)s OR name LIKE %(txt)s OR item_code LIKE %(txt)s)
            AND disabled = 0
            ORDER BY item_name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)

    except Exception as e:
        frappe.log_error(f"Erro em item_query: {str(e)}")
        return []
