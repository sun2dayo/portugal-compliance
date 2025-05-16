# Copyright (c) 2025, Manus Team and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr, now_datetime, get_datetime_str, get_date_str
import qrcode
import io
import base64

# Assuming signing_utils.py is in the same directory or accessible in python path
# from .signing_utils import get_pt_compliance_settings_cached, extract_signature_characters
# For direct execution or testing, you might need to adjust imports if not running within Frappe context
# For Frappe app structure, relative imports from the same app/module are fine.

def get_active_pt_document_series(erpnext_naming_series, at_document_type, posting_date_str):
    """Fetches the active PT Document Series configuration for the given ERPNext series and AT doc type."""
    filters = {
        "erpnext_naming_series": erpnext_naming_series,
        "at_document_type": at_document_type,
        "is_active": 1,
        "valid_from": ["<=", posting_date_str],
    }
    # Optional: Add valid_until filter if used
    # "valid_until": [">=", posting_date_str],

    series_settings = frappe.get_all(
        "PT Document Series",
        filters=filters,
        fields=["name", "at_series_validation_code"],
        order_by="valid_from desc",
        limit_page_length=1
    )
    if series_settings:
        return series_settings[0]
    return None

def generate_atcud(doc):
    """Generates the ATCUD for a given document.
       ATCUD = ATSeriesValidationCode-DocumentSequentialNumber
    """
    if not doc.get("naming_series") or not doc.get("name") or not doc.get("posting_date"):
        frappe.log_warning("ATCUD: Campos obrigatórios (naming_series, name, posting_date) em falta no documento.", doc.name, "QRCode/ATCUD PT")
        return None

    # Determine AT Document Type (this might need more sophisticated mapping or a field on the doc itself)
    # For now, assuming Sales Invoice is FT. This needs to be robust.
    at_doc_type_map = {
        "Sales Invoice": "FT",
        "Credit Note": "NC",
        # Add other mappings
    }
    at_document_type = at_doc_type_map.get(doc.doctype)
    if not at_document_type:
        frappe.log_warning(f"ATCUD: Tipo de documento AT não mapeado para {doc.doctype}", doc.name, "QRCode/ATCUD PT")
        return None

    posting_date_str = get_date_str(doc.posting_date)
    series_config = get_active_pt_document_series(doc.naming_series, at_document_type, posting_date_str)

    if not series_config or not series_config.at_series_validation_code:
        frappe.log_warning(f"ATCUD: Configuração da Série PT (com código de validação AT) não encontrada ou incompleta para {doc.naming_series} / {at_document_type}", doc.name, "QRCode/ATCUD PT")
        return None
    
    validation_code = series_config.at_series_validation_code
    
    # Extract sequential number from doc.name (assuming format like SERIES/YYYY/##### or SERIES-#####)
    # This needs to be robust based on actual naming series format.
    sequential_number = doc.name.split("/")[-1].split("-")[-1]
    try:
        # Ensure it's a number, remove leading zeros if any for AT spec (confirm this requirement)
        sequential_number = str(int(sequential_number)) 
    except ValueError:
        frappe.log_error(f"ATCUD: Não foi possível extrair o número sequencial de {doc.name}", doc.name, "QRCode/ATCUD PT")
        return None

    atcud = f"{validation_code}-{sequential_number}"
    return atcud

def build_qr_code_string(doc, atcud_val, signature_chars_val):
    """Builds the string content for the QR Code as per AT specifications."""
    settings = frappe.get_doc("PT Compliance Settings") # Using direct get_doc as settings are unlikely to change mid-request

    # Helper to get NIF, defaulting to "999999990" (Consumidor Final) if not found or not Portuguese
    def get_nif(party_nif_field, party_country_field):
        nif = doc.get(party_nif_field)
        country = doc.get(party_country_field)
        # Assuming Portuguese NIFs are 9 digits. This validation might need to be more robust.
        if country == "Portugal" and nif and len(nif) == 9 and nif.isdigit():
            return nif
        return "999999990"

    # A: NIF do emitente (Empresa)
    company_nif = settings.producer_nif # This should be the company's NIF, not software producer. Fetch from Company DocType.
    company_doc = frappe.get_doc("Company", doc.company)
    issuer_nif = company_doc.tax_id if company_doc.tax_id else "999999990" # Fallback, but company must have NIF

    # B: NIF do adquirente
    # Assuming customer NIF is in 'tax_id' and country in 'customer_primary_address.country' or similar
    # This needs to be adapted based on actual field names for customer NIF and country
    customer_nif = get_nif("tax_id", "country") # Placeholder: doc.tax_id, doc.customer_address.country
    if doc.doctype == "Sales Invoice" and doc.customer:
        customer_doc = frappe.get_doc("Customer", doc.customer)
        # Attempt to get NIF from customer, then from primary billing address
        cust_tax_id = customer_doc.tax_id
        cust_country = customer_doc.country # Assuming customer has a country field
        if not (cust_tax_id and cust_country == "Portugal") and customer_doc.customer_primary_address:
            addr = frappe.get_doc("Address", customer_doc.customer_primary_address)
            cust_tax_id = addr.tax_id if addr.tax_id else cust_tax_id # Prioritize address NIF if available
            cust_country = addr.country
        
        customer_nif = "999999990"
        if cust_country == "Portugal" and cust_tax_id and len(cust_tax_id) == 9 and cust_tax_id.isdigit():
            customer_nif = cust_tax_id
        elif not cust_tax_id: # If no NIF at all, and not explicitly foreign, assume Consumidor Final
             customer_nif = "999999990"
        # If foreign, it might be different, AT spec says "NIF do adquirente (Países fora UE: 0)" - check this

    # C: País do adquirente (ISO 3166-1 alpha-2)
    # This needs to be robustly fetched based on customer's address
    customer_country_code = "PT" # Default, needs to be fetched
    if doc.doctype == "Sales Invoice" and doc.customer:
        # Similar logic as above to get country code
        pass # Placeholder for fetching actual customer country code

    # D: Tipo de documento (código AT)
    # This mapping needs to be comprehensive
    doc_type_at_map = {"Sales Invoice": "FT", "Credit Note": "NC", "Sales Receipt": "FR", "Simplified Invoice": "FS"}
    document_type_at = doc_type_at_map.get(doc.doctype, "")

    # E: Estado do documento (N-Normal, A-Anulado, F-Faturado(rascunho?), R-Rascunho)
    # For submitted docs, it's Normal. If it's a cancellation (Credit Note), it's still Normal for the NC itself.
    # The original invoice would be marked as Cancelled in SAF-T, but QR is for the current doc.
    document_status_at = "N" if doc.docstatus == 1 else "R" # Simplified
    if doc.is_return == 1 and doc.doctype == "Sales Invoice": # Credit Note
        document_status_at = "N" # A Credit Note is a normal document

    # F: Data de emissão do documento (AAAA-MM-DD)
    posting_date_str = get_date_str(doc.posting_date)

    # G: Identificador único do documento (Série/Número)
    document_unique_id = doc.name

    # H: ATCUD
    atcud = atcud_val if atcud_val else ""

    # I: Campos de IVA - This is complex and requires iterating through taxes table
    # For simplicity, placeholders. Real implementation needs to sum bases and totals per AT tax rate code (RED, INT, NOR, ISE)
    # These should come from doc.taxes table, mapping tax rates to AT codes.
    # Example: doc.taxes might have items with account_head like "VAT 13% - PT" or similar.
    # We need a mapping from these tax accounts/rates to AT's I1-I8 fields.
    # This is a simplified placeholder. Actual calculation is crucial.
    total_base_iva_ise = 0.00
    total_base_iva_red = 0.00
    total_iva_red = 0.00
    total_base_iva_int = 0.00
    total_iva_int = 0.00
    total_base_iva_nor = 0.00
    total_iva_nor = 0.00
    # I8: Total de IVA não sujeito ou isento (outras menções) - This might be different from I1

    # Iterate through doc.taxes to populate IVA fields
    # This requires knowing how tax rates are mapped to PT categories (RED, INT, NOR, ISE)
    # This is a CRITICAL part and needs accurate implementation based on Tax Rules and Item Tax Templates.
    # Placeholder logic:
    for tax_row in doc.get("taxes", []):
        # Example: if tax_row.account_head contains "IVA Normal - PT" or rate is 23%
        # total_base_iva_nor += tax_row.tax_amount_after_discount_amount / (tax_row.rate / 100) if tax_row.rate else 0
        # total_iva_nor += tax_row.tax_amount_after_discount_amount
        # Similar for RED (6%), INT (13%), ISE (0% but with specific reason)
        pass # This needs full implementation

    # N: Total de Imposto do Selo (se aplicável)
    total_imposto_selo = 0.00 # Fetch if applicable

    # O: Total do documento (com impostos)
    total_document_gross = doc.grand_total

    # P: Retenções na fonte (se aplicável)
    total_retencoes = 0.00 # Fetch if applicable

    # Q: Os 4 caracteres da assinatura digital do documento
    signature_chars = signature_chars_val if signature_chars_val else ""

    # R: Número do certificado do software atribuído pela AT
    software_certificate_no = settings.software_certificate_number

    qr_fields = [
        f"A:{issuer_nif}",
        f"B:{customer_nif}",
        f"C:{customer_country_code}",
        f"D:{document_type_at}",
        f"E:{document_status_at}",
        f"F:{posting_date_str}",
        f"G:{document_unique_id}",
        f"H:{atcud}",
        f"I1:{total_base_iva_ise:.2f}",
        f"I2:{total_base_iva_red:.2f}",
        f"I3:{total_iva_red:.2f}",
        f"I4:{total_base_iva_int:.2f}",
        f"I5:{total_iva_int:.2f}",
        f"I6:{total_base_iva_nor:.2f}",
        f"I7:{total_iva_nor:.2f}",
        # I8 is missing in this simplified version
        f"N:{total_imposto_selo:.2f}",
        f"O:{total_document_gross:.2f}",
        f"P:{total_retencoes:.2f}",
        f"Q:{signature_chars}",
        f"R:{software_certificate_no}"
    ]
    return "*".join(qr_fields)

def generate_qr_code_image_base64(qr_string_content):
    """Generates a QR Code image from the string content and returns it as Base64."""
    if not qr_string_content:
        return None
    img = qrcode.make(qr_string_content)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"


def process_document_atcud_and_qr(doc, method=None):
    """Processes ATCUD and QR Code generation for a document."""
    # This function would be called from a hook, likely before_save or on_submit (if ATCUD is stable then)
    # Or before_print if QR code is generated on demand for printing.

    # 1. Generate ATCUD
    atcud = generate_atcud(doc)
    if atcud:
        frappe.db.set_value(doc.doctype, doc.name, "custom_atcud", atcud, update_modified=False)
    else:
        # Handle missing ATCUD - log or prevent submission if critical
        frappe.log_warning(f"Não foi possível gerar ATCUD para {doc.doctype} {doc.name}", doc.name, "QRCode/ATCUD PT")
        # Potentially set custom_atcud to empty or a specific error marker
        frappe.db.set_value(doc.doctype, doc.name, "custom_atcud", "ERRO_ATCUD", update_modified=False)

    # 2. Build QR Code String
    # Signature characters are needed. They are set by the signing_utils.py hook (on_submit).
    # This means QR code string finalization might need to happen after signature chars are available.
    # Or, QR code is generated with placeholder for Q: field, and Q: is updated later, or QR is regenerated.
    # For now, assume signature_chars are available on the doc (e.g. from a previous step or if this hook runs after signing hook)
    
    signature_chars = doc.get("custom_signature_chars") # This field is set by signing_utils
    if not signature_chars and doc.docstatus == 1: # If submitted and no sig chars, something is wrong
        frappe.log_warning(f"Caracteres da assinatura em falta para {doc.doctype} {doc.name} ao gerar QR.", doc.name, "QRCode/ATCUD PT")
        # signature_chars = "AAAA" # Placeholder if absolutely needed, but indicates an issue

    qr_code_content_string = build_qr_code_string(doc, atcud, signature_chars)
    if qr_code_content_string:
        frappe.db.set_value(doc.doctype, doc.name, "custom_qr_code_string", qr_code_content_string, update_modified=False)
        # The actual image generation for display can be done on demand in the print format
        # using this custom_qr_code_string field.
        # qr_image_b64 = generate_qr_code_image_base64(qr_code_content_string)
        # frappe.db.set_value(doc.doctype, doc.name, "custom_qr_code_image_b64", qr_image_b64, update_modified=False)
        frappe.log_info(f"Conteúdo do QRCode gerado para {doc.doctype} {doc.name}")
    else:
        frappe.log_warning(f"Não foi possível gerar o conteúdo do QRCode para {doc.doctype} {doc.name}", doc.name, "QRCode/ATCUD PT")

