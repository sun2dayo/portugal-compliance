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


def setup_naming_series_property_setters(app_name=None):
	"""
	Neutralizada (Auditoria Fase 0, 2026-08-26), mantida como no-op
	seguro só para não quebrar a chamada em hooks.py::after_migrate e
	em run_all_startup_fixes.

	Criava um Property Setter por empresa (nome
	f"{doctype}-naming_series-options-{company.abbr}"), mas o Frappe
	resolve as opções de um campo Select por doc_type+field_name+
	property - não pela parte final do nome do Property Setter. Com
	mais do que uma empresa portuguesa no site, existiam múltiplos
	Property Setter a competir pelo mesmo alvo (doc_type=doctype,
	field_name="naming_series", property="options"), com resultado
	dependente da ordem de leitura do cache de metadata do Frappe - o
	mesmo problema de fundo do Property Setter único usado noutros
	pontos do módulo (ver document_hooks.py e series_adapter.py::
	sync_property_setter_standard). Substituído por filtragem
	client-side, sempre consultada de fresco para a empresa
	selecionada no formulário (ver
	public/js/portugal_compliance.js::applyNamingSeriesFilter).
	"""
	return


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


# fix_naming_series_property_setters removida (Auditoria Fase 0,
# 2026-08-26): sem chamadores em todo o repositório (confirmado por
# grep) - código morto que escrevia o mesmo Property Setter global já
# neutralizado noutros pontos do módulo (ver
# series_adapter.py::sync_property_setter_standard).


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
