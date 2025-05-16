# Copyright (c) 2025, Manus Team and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr, now_datetime, get_datetime_str
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
import base64
from portugal_compliance.doctype.pt_compliance_settings.pt_compliance_settings import PTComplianceSettings
from frappe.modules.utils import load_doctype_module  # adicione esta importação no topo se ainda não tiver

def get_pt_compliance_settings_cached():
    if not hasattr(frappe.local, "pt_compliance_settings_cache"):
        load_doctype_module("PT Compliance Settings", "portugal_compliance")
        frappe.local.pt_compliance_settings_cache = frappe.get_doc("PT Compliance Settings", "PT Compliance Settings")
    return frappe.local.pt_compliance_settings_cache


def get_private_key():
    """Loads the private key from the path and password specified in PT Compliance Settings."""
    settings = get_pt_compliance_settings_cached()
    private_key_path = settings.get("private_key_path")
    password = settings.get("private_key_password")

    if not private_key_path:
        frappe.throw("Caminho para a chave privada não configurado nas Definições de Conformidade PT.")

    try:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=password.encode() if password else None,
            )
        return private_key
    except FileNotFoundError:
        frappe.log_error(f"Ficheiro da chave privada não encontrado em: {private_key_path}", "Assinatura Digital PT")
        frappe.throw(f"Ficheiro da chave privada não encontrado em: {private_key_path}. Verifique as configurações.")
    except Exception as e:
        frappe.log_error(f"Erro ao carregar chave privada: {e}", "Assinatura Digital PT")
        frappe.throw(f"Erro ao carregar chave privada: {e}")

def generate_string_to_sign(doc_posting_date_str, doc_emission_datetime_str, doc_unique_id, doc_grand_total, previous_hash):
    """Generates the string to be signed according to AT specifications.
    Formato: DataDeEmissao;DataHoraDeEmissao;IdentificadorUnicoDoc;ValorTotalComImpostos;HashAnterior
    """
    string_parts = [
        cstr(doc_posting_date_str),                     # Data de emissão do documento (AAAA-MM-DD)
        cstr(doc_emission_datetime_str),                # Data e hora da emissão (AAAA-MM-DDTHH:MM:SS)
        cstr(doc_unique_id),                            # Identificador único do documento (Série + Número Sequencial)
        f"{doc_grand_total:.2f}",                      # Valor total do documento (com impostos, formatado com 2 casas decimais)
        cstr(previous_hash)                             # Hash da assinatura do documento fiscalmente relevante anterior
    ]
    return ";".join(string_parts)

def calculate_document_data_hash(data_string_for_hash):
    """Calculates the SHA-256 hash of the provided data string (for chaining)."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data_string_for_hash.encode("utf-8"))
    return base64.b64encode(digest.finalize()).decode("utf-8")

def sign_string(data_to_sign_str):
    """Signs the data string using the private key and returns the Base64 encoded signature."""
    private_key = get_private_key()
    signature = private_key.sign(
        data_to_sign_str.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256() # Using SHA-256 as a secure default. Verify against AT specs.
    )
    return base64.b64encode(signature).decode("utf-8")

def extract_signature_characters(base64_signature_str):
    """Extracts the 1st, 11th, 21st, and 31st characters from the Base64 signature string."""
    if not base64_signature_str or len(base64_signature_str) < 31:
        frappe.log_warning("Assinatura demasiado curta para extrair caracteres.", base64_signature_str, "Assinatura Digital PT")
        return ""

    chars = [
        base64_signature_str[0],
        base64_signature_str[10],
        base64_signature_str[20],
        base64_signature_str[30]
    ]
    return "-".join(chars)

def get_previous_document_hash(doc_series, current_doc_name, doctype_name, posting_date):
    """Fetches the hash of the previously submitted document in the same series and fiscal year.
       Returns '0' if it's the first document of the series in the fiscal year.
    """
    # Assuming fiscal year is based on posting_date
    # This logic might need refinement based on how series are defined (e.g., per year or continuous)
    # For now, we filter by naming_series and ensure it's before the current document.
    filters = {
        "naming_series": doc_series,
        "docstatus": 1, # Submitted documents
        "name": ["!=", current_doc_name],
        "posting_date": ["<=", posting_date] # Ensure we only look at docs up to the current one's date
    }

    # Order by posting_date desc, then creation desc to get the latest one before current
    # If posting_date is the same, creation timestamp will break ties.
    previous_docs = frappe.get_list(
        doctype_name,
        filters=filters,
        fields=["name", "custom_document_hash", "posting_date", "creation"],
        order_by="posting_date desc, creation desc, name desc",
        limit_page_length=1
    )

    if previous_docs:
        # Further check if the found doc is indeed before the current one if posting_dates are same
        if previous_docs[0].posting_date == posting_date:
            current_doc_creation = frappe.db.get_value(doctype_name, current_doc_name, "creation")
            if previous_docs[0].creation >= current_doc_creation:
                 # This case should ideally not happen if current_doc_name is excluded and order is correct
                 # but as a safeguard, if it's not strictly before, consider it the first.
                 return "0"
        return previous_docs[0].custom_document_hash
    else:
        return "0"

def process_sales_invoice_signature(doc, method=None):
    """Processes the digital signature for a Sales Invoice upon submission."""
    settings = get_pt_compliance_settings_cached()
    if not settings.get("private_key_path"):
        frappe.log_info("Assinatura Digital PT: Chave privada não configurada. A assinatura não será processada.", doc.name, "Assinatura Digital PT")
        return

    try:
        # 1. Get Previous Document Hash H(Dn-1)
        # Ensure doc.posting_date is in 'YYYY-MM-DD' string format for comparison and usage
        posting_date_str = cstr(doc.posting_date)
        previous_hash = get_previous_document_hash(doc.naming_series, doc.name, doc.doctype, doc.posting_date)

        # 2. Prepare data for the signature string
        # Emission datetime: Use doc.creation for now, assuming submission is close to creation.
        # AT might require a specific timezone or format. Frappe's get_datetime_str is usually UTC.
        emission_datetime_str = get_datetime_str(doc.creation).replace(" ", "T")
        doc_unique_id = doc.name # Typically includes series and number

        # 3. Construct the string to be signed
        string_to_be_signed = generate_string_to_sign(
            posting_date_str,
            emission_datetime_str,
            doc_unique_id,
            doc.grand_total,
            previous_hash
        )

        # 4. Sign the string
        signature_base64 = sign_string(string_to_be_signed)

        # 5. Calculate the hash of the current document's data H(Dn) for chaining
        # This hash is of the document's key data *before* the previous hash is involved in the signature string.
        current_doc_data_for_chain_hash_string = f"{posting_date_str};{emission_datetime_str};{doc_unique_id};{doc.grand_total:.2f}"
        current_document_chain_hash = calculate_document_data_hash(current_doc_data_for_chain_hash_string)

        # 6. Extract characters for printing
        signature_chars_for_print = extract_signature_characters(signature_base64)

        # 7. Store these values in custom fields on the document
        # Using frappe.db.set_value to avoid triggering hooks again if called in on_submit
        frappe.db.set_value(doc.doctype, doc.name, "custom_digital_signature", signature_base64, update_modified=False)
        frappe.db.set_value(doc.doctype, doc.name, "custom_document_hash", current_document_chain_hash, update_modified=False)
        frappe.db.set_value(doc.doctype, doc.name, "custom_previous_document_hash", previous_hash, update_modified=False)
        frappe.db.set_value(doc.doctype, doc.name, "custom_signature_chars", signature_chars_for_print, update_modified=False)

        frappe.log_info(f"Assinatura digital processada para {doc.doctype} {doc.name}", context_str=f"Assinatura: {signature_chars_for_print}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Erro ao processar assinatura digital para {doc.name}")
        # Optionally, re-throw or show a message to the user depending on desired behavior
        # frappe.throw(f"Erro ao processar assinatura digital: {e}")

