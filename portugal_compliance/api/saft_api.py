import frappe
from frappe import _
import json
from datetime import datetime
from portugal_compliance.utils.saft_generator import SAFTGenerator
import xml.etree.ElementTree as ET


@frappe.whitelist()
def generate_saft_export(company, from_date, to_date, export_type="full"):
	"""
	Gera exportação SAF-T para período específico
	"""
	try:
		generator = SAFTGenerator()

		# Validar datas
		from_date = frappe.utils.getdate(from_date)
		to_date = frappe.utils.getdate(to_date)

		if from_date > to_date:
			return {
				"status": "error",
				"message": _("From date cannot be greater than to date")
			}

		# Gerar SAF-T
		saft_data = generator.generate_saft(company, from_date, to_date, export_type)

		# Criar log de exportação
		export_log = frappe.get_doc({
			"doctype": "SAF-T Export Log",
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
			"export_type": export_type,
			"status": "Completed",
			"file_size": len(saft_data.encode('utf-8')),
			"records_count": generator.get_records_count()
		})
		export_log.insert()

		return {
			"status": "success",
			"saft_data": saft_data,
			"export_log": export_log.name,
			"message": _("SAF-T generated successfully")
		}

	except Exception as e:
		frappe.log_error(f"Error generating SAF-T: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def validate_saft_xml(xml_content):
	"""
	Valida XML SAF-T contra schema XSD
	"""
	try:
		# Parse XML
		root = ET.fromstring(xml_content)

		# Validações básicas
		validations = []

		# Verificar namespace
		if root.tag != "{urn:OECD:StandardAuditFile-Tax:PT_1.04_01}AuditFile":
			validations.append({
				"type": "error",
				"message": "Invalid root element or namespace"
			})

		# Verificar header obrigatório
		header = root.find(".//{urn:OECD:StandardAuditFile-Tax:PT_1.04_01}Header")
		if header is None:
			validations.append({
				"type": "error",
				"message": "Header element is required"
			})

		# Verificar campos obrigatórios no header
		required_fields = ["AuditFileVersion", "CompanyID", "TaxRegistrationNumber"]
		for field in required_fields:
			if header.find(f".//{{{root.nsmap[None]}}}{field}") is None:
				validations.append({
					"type": "error",
					"message": f"Required field {field} is missing in Header"
				})

		return {
			"status": "success",
			"valid": len([v for v in validations if v["type"] == "error"]) == 0,
			"validations": validations
		}

	except ET.ParseError as e:
		return {
			"status": "error",
			"message": f"XML Parse Error: {str(e)}"
		}
	except Exception as e:
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def get_saft_export_logs(filters=None):
	"""
	Retorna logs de exportação SAF-T
	"""
	if filters:
		filters = json.loads(filters)
	else:
		filters = {}

	logs = frappe.get_all("SAF-T Export Log",
						  filters=filters,
						  fields=["name", "company", "from_date", "to_date",
								  "export_type", "status", "creation", "file_size"],
						  order_by="creation desc",
						  limit=50)

	return logs


@frappe.whitelist()
def download_saft_file(export_log_name):
	"""
	Prepara arquivo SAF-T para download
	"""
	try:
		export_log = frappe.get_doc("SAF-T Export Log", export_log_name)

		if export_log.status != "Completed":
			return {
				"status": "error",
				"message": _("Export not completed")
			}

		# Regenerar SAF-T se necessário
		generator = SAFTGenerator()
		saft_data = generator.generate_saft(
			export_log.company,
			export_log.from_date,
			export_log.to_date,
			export_log.export_type
		)

		# Criar arquivo temporário
		filename = f"SAFT-PT_{export_log.company}_{export_log.from_date}_{export_log.to_date}.xml"

		return {
			"status": "success",
			"filename": filename,
			"content": saft_data,
			"content_type": "application/xml"
		}

	except Exception as e:
		frappe.log_error(f"Error downloading SAF-T: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def get_saft_statistics(company, from_date, to_date):
	"""
	Retorna estatísticas para período SAF-T
	"""
	try:
		from_date = frappe.utils.getdate(from_date)
		to_date = frappe.utils.getdate(to_date)

		# Contar documentos por tipo
		sales_invoices = frappe.db.count("Sales Invoice", {
			"company": company,
			"posting_date": ["between", [from_date, to_date]],
			"docstatus": 1
		})

		purchase_invoices = frappe.db.count("Purchase Invoice", {
			"company": company,
			"posting_date": ["between", [from_date, to_date]],
			"docstatus": 1
		})

		payments = frappe.db.count("Payment Entry", {
			"company": company,
			"posting_date": ["between", [from_date, to_date]],
			"docstatus": 1
		})

		return {
			"status": "success",
			"statistics": {
				"sales_invoices": sales_invoices,
				"purchase_invoices": purchase_invoices,
				"payments": payments,
				"total_documents": sales_invoices + purchase_invoices + payments
			}
		}

	except Exception as e:
		return {
			"status": "error",
			"message": str(e)
		}
