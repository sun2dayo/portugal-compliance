# api.py - NOVO ARQUIVO
import frappe
from frappe import _


@frappe.whitelist()
def communicate_series_batch(company, username, password, environment, series_list):
	"""API para comunicar séries em lote"""
	try:
		from portugal_compliance.utils.at_webservice import batch_register_naming_series

		# Obter naming series da empresa
		naming_series_list = get_naming_series_for_doctypes(company, series_list)

		# Comunicar à AT
		result = batch_register_naming_series(naming_series_list, company, username, password,
											  environment)

		# Salvar códigos AT na empresa
		if result.get("success"):
			save_at_codes_to_company(company, result.get("results", []))

		return result

	except Exception as e:
		frappe.log_error(f"Erro na comunicação em lote: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_company_naming_series(company):
	"""Obter naming series de uma empresa"""
	try:
		from portugal_compliance.utils.naming_series_customizer import get_naming_series_statistics

		stats = get_naming_series_statistics()
		company_abbr = frappe.db.get_value("Company", company, "abbr")

		# Filtrar séries da empresa
		company_series = {}
		for doctype, data in stats.get("statistics", {}).get("details", {}).items():
			company_series[doctype] = {
				"total_options": data.get("total_options", 0),
				"portuguese_options": data.get("portuguese_options", 0)
			}

		return company_series

	except Exception as e:
		return {"error": str(e)}


def get_naming_series_for_doctypes(company, doctypes):
	"""Obter naming series específicas para DocTypes"""
	naming_series = []
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	current_year = frappe.utils.getdate().year

	# Mapeamento DocType → Prefixos
	doctype_prefixes = {
		"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
		"Purchase Invoice": ["FC"],
		"Payment Entry": ["RC", "RB"],
		"Delivery Note": ["GT"],
		"Purchase Receipt": ["GR"],
		"Stock Entry": ["GM"]
	}

	for doctype in doctypes:
		if doctype in doctype_prefixes:
			for prefix in doctype_prefixes[doctype]:
				naming_series.append(f"{prefix}-{current_year}-{company_abbr}.####")

	return naming_series


def save_at_codes_to_company(company, results):
	"""Salvar códigos AT recebidos na empresa"""
	try:
		for result in results:
			if result.get("success") and result.get("atcud"):
				# Extrair prefixo da naming series
				naming_series = result.get("naming_series", "")
				prefix = naming_series.replace(".####", "").split("-")[0] if naming_series else ""

				if prefix:
					field_name = f"at_code_{prefix}"
					frappe.db.set_value("Company", company, field_name, result["atcud"])

		frappe.db.commit()
		frappe.logger().info(f"✅ Códigos AT salvos para empresa: {company}")

	except Exception as e:
		frappe.log_error(f"Erro ao salvar códigos AT: {str(e)}")


@frappe.whitelist()
def get_all_company_naming_series(company):
	"""Obter todas as naming series de uma empresa"""
	try:
		# Todos os DocTypes suportados
		all_doctypes = ["Sales Invoice", "Purchase Invoice", "Payment Entry",
						"Delivery Note", "Purchase Receipt", "Stock Entry"]

		return get_naming_series_for_doctypes(company, all_doctypes)

	except Exception as e:
		return {"error": str(e)}


# api.py
@frappe.whitelist()
def recreate_portugal_workspace():
	"""API para recriar workspace Portugal Compliance"""
	try:
		# Remover workspace existente
		if frappe.db.exists("Workspace", "Portugal Compliance"):
			frappe.delete_doc("Workspace", "Portugal Compliance", ignore_permissions=True)

		# Criar novo workspace
		from portugal_compliance.regional.portugal import create_portugal_workspace
		create_portugal_workspace()

		return {
			"success": True,
			"message": "Workspace Portugal Compliance recriado com sucesso"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_workspace_status():
	"""Verificar status do workspace"""
	try:
		workspace_exists = frappe.db.exists("Workspace", "Portugal Compliance")

		if workspace_exists:
			workspace = frappe.get_doc("Workspace", "Portugal Compliance")
			return {
				"exists": True,
				"name": workspace.name,
				"title": workspace.title,
				"public": workspace.public,
				"shortcuts_count": len(workspace.shortcuts),
				"links_count": len(workspace.links)
			}
		else:
			return {"exists": False}

	except Exception as e:
		return {"error": str(e)}
