# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Startup Fixes for Portugal Compliance
Correções automáticas executadas no startup/migração
Baseado na sua experiência com programação.sistemas_erp[5]
"""

import frappe
from frappe import _


def fix_customer_search_on_startup():
	"""
	✅ Corrigir customer search automaticamente no startup
	Baseado nas boas práticas do Frappe/ERPNext
	"""
	try:
		# Verificar se há Property Setters problemáticos
		problematic_setters = frappe.db.sql("""
											SELECT name
											FROM `tabProperty Setter`
											WHERE doc_type = 'Sales Invoice'
											  AND field_name = 'customer'
											  AND property = 'options'
											  AND value NOT LIKE
												  '%portugal_compliance.queries.customer.customer_query%'
											""")

		if problematic_setters:
			# Remover setters problemáticos
			for setter in problematic_setters:
				frappe.delete_doc("Property Setter", setter[0], ignore_permissions=True)

			# Criar setter correto
			if not frappe.db.exists("Property Setter", {
				"doc_type": "Sales Invoice",
				"field_name": "customer",
				"property": "options",
				"value": "portugal_compliance.queries.customer.customer_query"
			}):
				property_setter = frappe.get_doc({
					"doctype": "Property Setter",
					"doc_type": "Sales Invoice",
					"field_name": "customer",
					"property": "options",
					"value": "portugal_compliance.queries.customer.customer_query",
					"property_type": "Text",
					"doctype_or_field": "DocField"
				})
				property_setter.insert(ignore_permissions=True)

			frappe.db.commit()
			frappe.logger().info("✅ Customer search corrigido automaticamente")

	except Exception as e:
		frappe.log_error(f"Erro na correção automática customer search: {str(e)}")


def fix_naming_series_formats():
	"""
	✅ Corrigir formatos de naming series para ERPNext
	"""
	try:
		# Verificar séries com formato incorreto
		series_with_hyphens = frappe.get_all("Portugal Series Configuration",
											 filters={"prefix": ["like", "%-%-%.####"]},
											 fields=["name", "prefix", "naming_series"])

		for serie in series_with_hyphens:
			# Converter formato: FT-2025-DSY → FT2025DSY
			old_prefix = serie.prefix
			new_prefix = old_prefix.replace('-', '')
			new_naming_series = f"{new_prefix}.####"

			frappe.db.set_value("Portugal Series Configuration", serie.name, {
				"prefix": new_prefix,
				"naming_series": new_naming_series
			})

		if series_with_hyphens:
			frappe.db.commit()
			frappe.logger().info(
				f"✅ {len(series_with_hyphens)} séries corrigidas para formato ERPNext")

	except Exception as e:
		frappe.log_error(f"Erro na correção de naming series: {str(e)}")


def ensure_portugal_compliance_setup():
	"""
	✅ Garantir configuração básica do Portugal Compliance
	"""
	try:
		# Verificar se há empresas portuguesas sem compliance ativado
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "portugal_compliance_enabled"])

		for company in portuguese_companies:
			if not company.portugal_compliance_enabled:
				frappe.logger().info(
					f"⚠️ Empresa portuguesa {company.name} sem compliance ativado")

	except Exception as e:
		frappe.log_error(f"Erro na verificação de compliance: {str(e)}")


def setup_naming_series_property_setters():
	"""
	✅ VERSÃO DINÂMICA: Property Setters baseados no abbr da empresa
	Baseado na sua experiência com programação.consistência_de_dados[3]
	"""
	try:
		frappe.logger().info("🔧 Configurando Property Setters DINÂMICOS")

		# Buscar todas as empresas portuguesas ativas
		portuguese_companies = frappe.get_all("Company",
											  filters={
												  "country": "Portugal",
												  "portugal_compliance_enabled": 1
											  },
											  fields=["name", "abbr"])

		if not portuguese_companies:
			frappe.logger().info("Nenhuma empresa portuguesa encontrada")
			return

		# Para cada empresa portuguesa
		for company in portuguese_companies:
			try:
				# ✅ BUSCAR SÉRIES DINÂMICAS BASEADAS NO ABBR
				company_series = frappe.get_all("Portugal Series Configuration",
												filters={
													"company": company.name,
													"is_active": 1
												},
												fields=["document_type", "naming_series"])

				if not company_series:
					frappe.logger().info(f"Nenhuma série encontrada para {company.name}")
					continue

				# Agrupar por document_type
				series_by_doctype = {}
				for serie in company_series:
					doctype = serie.document_type
					if doctype not in series_by_doctype:
						series_by_doctype[doctype] = []
					series_by_doctype[doctype].append(serie.naming_series)

				# Configurar Property Setters DINÂMICOS
				configured_count = 0
				for doctype, naming_series_list in series_by_doctype.items():
					try:
						# ✅ PROPERTY SETTER ESPECÍFICO POR EMPRESA
						property_setter_name = f"{doctype}-naming_series-options-{company.abbr}"

						# Verificar se já existe
						if frappe.db.exists("Property Setter", property_setter_name):
							# Atualizar existente
							frappe.db.set_value("Property Setter", property_setter_name,
												"value", '\n'.join(naming_series_list))
						else:
							# Criar novo DINÂMICO
							property_setter = frappe.get_doc({
								"doctype": "Property Setter",
								"name": property_setter_name,
								"doc_type": doctype,
								"property": "options",
								"field_name": "naming_series",
								"property_type": "Text",
								"value": '\n'.join(naming_series_list),
								"doctype_or_field": "DocField"
							})
							property_setter.insert(ignore_permissions=True)

						frappe.logger().info(f"✅ Property Setter DINÂMICO: {property_setter_name}")
						configured_count += 1

					except Exception as e:
						frappe.log_error(
							f"Erro ao configurar Property Setter para {doctype}: {str(e)}")

				frappe.logger().info(
					f"✅ {configured_count} Property Setters DINÂMICOS para {company.name} ({company.abbr})")

			except Exception as e:
				frappe.log_error(f"Erro ao processar empresa {company.name}: {str(e)}")

		frappe.db.commit()
		frappe.logger().info("✅ Property Setters DINÂMICOS configurados")

	except Exception as e:
		frappe.log_error(f"Erro na configuração de Property Setters DINÂMICOS: {str(e)}")


def run_all_startup_fixes():
	"""
	✅ ATUALIZADA: Incluir configuração de Property Setters
	"""
	try:
		fix_customer_search_on_startup()
		fix_naming_series_formats()
		setup_naming_series_property_setters()  # ✅ NOVA FUNÇÃO
		ensure_portugal_compliance_setup()

		return {
			"success": True,
			"message": "Todas as correções de startup executadas incluindo Property Setters"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def run_all_startup_fixes():
	"""
	✅ API para executar todas as correções de startup
	"""
	try:
		fix_customer_search_on_startup()
		fix_naming_series_formats()
		ensure_portugal_compliance_setup()

		return {
			"success": True,
			"message": "Todas as correções de startup executadas com sucesso"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


def fix_naming_series_property_setters():
	"""
	✅ NOVA FUNÇÃO: Corrigir Property Setters para naming series
	Baseado na sua experiência com programação.autenticação[4]
	"""
	try:
		frappe.logger().info("🔧 Corrigindo Property Setters para naming series")

		# Buscar todas as empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={
												  "country": "Portugal",
												  "portugal_compliance_enabled": 1
											  },
											  fields=["name", "abbr"])

		for company in portuguese_companies:
			try:
				# Buscar séries ativas para esta empresa
				company_series = frappe.get_all("Portugal Series Configuration",
												filters={
													"company": company.name,
													"is_active": 1
												},
												fields=["document_type", "naming_series"])

				# Agrupar por document_type
				series_by_doctype = {}
				for serie in company_series:
					doctype = serie.document_type
					if doctype not in series_by_doctype:
						series_by_doctype[doctype] = []
					series_by_doctype[doctype].append(serie.naming_series)

				# Criar/atualizar Property Setters
				for doctype, naming_series_list in series_by_doctype.items():
					property_setter_name = f"{doctype}-naming_series-options"

					if frappe.db.exists("Property Setter", property_setter_name):
						frappe.db.set_value("Property Setter", property_setter_name,
											"value", '\n'.join(naming_series_list))
					else:
						frappe.get_doc({
							"doctype": "Property Setter",
							"doc_type": doctype,
							"property": "options",
							"field_name": "naming_series",
							"property_type": "Text",
							"value": '\n'.join(naming_series_list),
							"doctype_or_field": "DocField"
						}).insert(ignore_permissions=True)

				frappe.logger().info(f"✅ Property Setters atualizados para {company.name}")

			except Exception as e:
				frappe.log_error(
					f"Erro ao atualizar Property Setters para {company.name}: {str(e)}")

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Erro na correção de Property Setters: {str(e)}")


# ✅ ADICIONAR NO FINAL DO ARQUIVO:

def run_all_startup_fixes():
	"""
	✅ FUNÇÃO: Executar todas as correções de startup
	Baseado na sua experiência com programação.correção_de_código [7]
	"""
	try:
		frappe.logger().info("🔧 Executando todas as correções de startup...")

		results = {
			"success": True,
			"fixes_applied": [],
			"errors": []
		}

		# ✅ EXECUTAR CORREÇÕES EXISTENTES
		try:
			fix_customer_search_on_startup()
			results["fixes_applied"].append("fix_customer_search_on_startup")
		except Exception as e:
			results["errors"].append(f"fix_customer_search_on_startup: {str(e)}")

		try:
			setup_naming_series_property_setters()
			results["fixes_applied"].append("setup_naming_series_property_setters")
		except Exception as e:
			results["errors"].append(f"setup_naming_series_property_setters: {str(e)}")

		# ✅ ADICIONAR OUTRAS CORREÇÕES SE NECESSÁRIO
		try:
			clear_portugal_compliance_cache()
			results["fixes_applied"].append("clear_portugal_compliance_cache")
		except Exception as e:
			results["errors"].append(f"clear_portugal_compliance_cache: {str(e)}")

		frappe.logger().info(
			f"✅ Startup fixes concluídas: {len(results['fixes_applied'])} aplicadas")

		if results["errors"]:
			frappe.logger().warning(f"⚠️ Alguns fixes falharam: {results['errors']}")

		return results

	except Exception as e:
		frappe.log_error(f"Erro nas correções de startup: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


def clear_portugal_compliance_cache():
	"""
	✅ AUXILIAR: Limpar cache específico do Portugal Compliance
	"""
	try:
		# Limpar cache específico
		cache_keys = [
			"portuguese_company_*",
			"portuguese_series_*",
			"nif_*",
			"atcud_validation_*"
		]

		for pattern in cache_keys:
			try:
				frappe.cache().delete_keys(pattern)
			except Exception:
				pass

		frappe.logger().info("✅ Cache Portugal Compliance limpo")

	except Exception as e:
		frappe.log_error(f"Erro ao limpar cache: {str(e)}")
