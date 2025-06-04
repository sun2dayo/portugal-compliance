"""
Módulo de integração AT - criado para evitar erros de importação nos fixtures e hooks.
Implemente aqui as funções referenciadas nos hooks e DocTypes.
"""
# portugal_compliance/utils/at_integration.py

def before_save_sales_invoice(doc, method): pass
def validate_atcud_before_submit(doc, method): pass
def on_submit_sales_invoice(doc, method): pass
def on_cancel_document(doc, method): pass
def before_save_purchase_invoice(doc, method): pass
def on_submit_purchase_invoice(doc, method): pass
def before_save_payment_entry(doc, method): pass
def on_submit_payment_entry(doc, method): pass
def before_save_delivery_note(doc, method): pass
def on_submit_delivery_note(doc, method): pass
def before_save_purchase_receipt(doc, method): pass
def on_submit_purchase_receipt(doc, method): pass
def before_save_journal_entry(doc, method): pass
def on_submit_journal_entry(doc, method): pass
def before_save_stock_entry(doc, method): pass
def on_submit_stock_entry(doc, method): pass
def on_update_company(doc, method): pass
def after_insert_series_config(doc, method): pass
def on_update_series_config(doc, method): pass
def before_save_series_config(doc, method): pass
def on_trash_series_config(doc, method): pass
def after_insert_atcud_log(doc, method): pass
def on_update_atcud_log(doc, method): pass
