# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Naming Series Customizer for Portugal Compliance - NOVA ABORDAGEM NATIVA
Customiza naming_series nativas do ERPNext para formato português
Sem DocTypes extras - usa lógica 100% nativa do ERPNext
"""

import frappe
from frappe import _
from frappe.utils import getdate, now, today, cint
import re
from datetime import datetime, date


class PortugueseNamingSeriesCustomizer:
	"""
	Customizador de naming_series portuguesas
	Abordagem nativa: modifica diretamente os DocTypes do ERPNext
	"""

	def __init__(self):
		self.module = "Portugal Compliance"

		# ✅ MAPEAMENTO COMPLETO: DocType → Prefixos portugueses
		self.portuguese_series = {
			"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
			"Purchase Invoice": ["FC"],
			"Payment Entry": ["RC", "RB"],
			"Delivery Note": ["GT"],
			"Purchase Receipt": ["GR"],
			"Stock Entry": ["GM"],
			"Journal Entry": ["JE"],
			"Quotation": ["OR"],
			"Sales Order": ["EC"],
			"Purchase Order": ["EF"],
			"Material Request": ["MR"]
		}

		# ✅ DESCRIÇÕES DOS PREFIXOS
		self.prefix_descriptions = {
			"FT": "Fatura de Venda",
			"FS": "Fatura Simplificada",
			"FR": "Fatura Recibo",
			"NC": "Nota de Crédito",
			"ND": "Nota de Débito",
			"FC": "Fatura de Compra",
			"RC": "Recibo",
			"RB": "Recibo Bancário",
			"GT": "Guia de Transporte",
			"GR": "Guia de Receção",
			"GM": "Guia de Movimentação",
			"JE": "Lançamento Contabilístico",
			"OR": "Orçamento",
			"EC": "Encomenda de Cliente",
			"EF": "Encomenda a Fornecedor",
			"MR": "Requisição de Material"
		}

	def setup_portuguese_naming_series(self, year=None, companies=None):
		"""
		Configurar naming_series portuguesas diretamente nos DocTypes
		"""
		try:
			if not year:
				year = getdate().year

			# ✅ BUSCAR EMPRESAS PORTUGUESAS
			if not companies:
				companies = frappe.get_all("Company",
										   filters={
											   "country": "Portugal",
											   "portugal_compliance_enabled": 1
										   },
										   fields=["name", "abbr"])

			if not companies:
				frappe.logger().warning(
					"⚠️ Nenhuma empresa portuguesa com compliance ativo encontrada")
				return {"success": False, "error": "Nenhuma empresa portuguesa encontrada"}

			results = {
				"success": True,
				"updated_doctypes": 0,
				"total_series_added": 0,
				"companies_processed": len(companies),
				"details": {}
			}

			# ✅ PROCESSAR CADA DOCTYPE
			for doctype, prefixes in self.portuguese_series.items():
				try:
					# Verificar se DocType existe
					if not frappe.db.exists("DocType", doctype):
						frappe.logger().warning(f"⚠️ DocType {doctype} não existe")
						continue

					# Gerar naming_series portuguesas para este DocType
					naming_options = []

					for prefix in prefixes:
						for company in companies:
							# ✅ FORMATO NATIVO: FT-2025-NDX.####
							naming_series = f"{prefix}-{year}-{company.abbr}.####"
							naming_options.append(naming_series)

					if naming_options:
						# ✅ ATUALIZAR AUTONAME DO DOCTYPE
						updated_count = self.update_doctype_autoname(doctype, naming_options)

						if updated_count > 0:
							results["updated_doctypes"] += 1
							results["total_series_added"] += updated_count
							results["details"][doctype] = {
								"series_added": updated_count,
								"prefixes": prefixes
							}

							frappe.logger().info(
								f"✅ {doctype}: {updated_count} séries portuguesas adicionadas")

				except Exception as e:
					frappe.log_error(f"Erro ao processar {doctype}: {str(e)}",
									 "PortugueseNamingSeriesCustomizer")
					results["details"][doctype] = {"error": str(e)}

			# ✅ COMMIT DAS ALTERAÇÕES
			frappe.db.commit()

			frappe.logger().info(
				f"✅ Setup concluído: {results['updated_doctypes']} DocTypes, {results['total_series_added']} séries")

			return results

		except Exception as e:
			frappe.log_error(f"Erro no setup de naming series: {str(e)}",
							 "PortugueseNamingSeriesCustomizer")
			return {"success": False, "error": str(e)}

	def update_doctype_autoname(self, doctype, new_naming_options):
		"""
		Atualizar autoname de um DocType com novas opções portuguesas
		"""
		try:
			# ✅ OBTER AUTONAME ATUAL
			current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
			current_options = [opt.strip() for opt in current_autoname.split('\n') if opt.strip()]

			# ✅ ADICIONAR APENAS NOVAS OPÇÕES
			added_count = 0
			for option in new_naming_options:
				if option not in current_options:
					current_options.append(option)
					added_count += 1

			if added_count > 0:
				# ✅ APLICAR NAMING_SERIES NATIVAS
				new_autoname = '\n'.join(sorted(current_options))
				frappe.db.set_value("DocType", doctype, "autoname", new_autoname)

				# ✅ ATUALIZAR PROPERTY SETTER
				self.update_naming_series_property_setter(doctype, new_autoname)

				# ✅ LIMPAR CACHE
				frappe.clear_cache(doctype=doctype)

				return added_count
			else:
				return 0

		except Exception as e:
			frappe.log_error(f"Erro ao atualizar autoname de {doctype}: {str(e)}",
							 "PortugueseNamingSeriesCustomizer")
			return 0

	def update_naming_series_property_setter(self, doctype, autoname_value):
		"""
		Atualizar Property Setter para naming_series
		"""
		try:
			ps_name = f"{doctype}-naming_series-options"

			if frappe.db.exists("Property Setter", ps_name):
				# ✅ ATUALIZAR EXISTENTE
				frappe.db.set_value("Property Setter", ps_name, "value", autoname_value)
				frappe.logger().info(f"✅ Property Setter atualizado: {ps_name}")
			else:
				# ✅ CRIAR NOVO
				ps_doc = frappe.get_doc({
					"doctype": "Property Setter",
					"name": ps_name,
					"doc_type": doctype,
					"field_name": "naming_series",
					"property": "options",
					"property_type": "Text",
					"value": autoname_value,
					"doctype_or_field": "DocField",
					"module": self.module
				})
				ps_doc.insert(ignore_permissions=True)
				frappe.logger().info(f"✅ Property Setter criado: {ps_name}")

			return True

		except Exception as e:
			frappe.log_error(f"Erro ao atualizar Property Setter para {doctype}: {str(e)}",
							 "PortugueseNamingSeriesCustomizer")
			return False

	def remove_portuguese_naming_series(self, doctype=None, companies=None):
		"""
		Remover naming_series portuguesas de um ou todos os DocTypes
		"""
		try:
			doctypes_to_clean = [doctype] if doctype else list(self.portuguese_series.keys())

			if not companies:
				companies = frappe.get_all("Company",
										   filters={"country": "Portugal"},
										   fields=["abbr"])

			results = {
				"success": True,
				"cleaned_doctypes": 0,
				"total_series_removed": 0,
				"details": {}
			}

			for dt in doctypes_to_clean:
				try:
					if not frappe.db.exists("DocType", dt):
						continue

					# ✅ OBTER AUTONAME ATUAL
					current_autoname = frappe.db.get_value("DocType", dt, "autoname") or ""
					current_options = [opt.strip() for opt in current_autoname.split('\n') if
									   opt.strip()]

					# ✅ REMOVER OPÇÕES PORTUGUESAS
					removed_count = 0
					remaining_options = []

					for option in current_options:
						is_portuguese = False
						for company in companies:
							if f"-{company.abbr}." in option:
								is_portuguese = True
								break

						if not is_portuguese:
							remaining_options.append(option)
						else:
							removed_count += 1

					if removed_count > 0:
						# ✅ ATUALIZAR AUTONAME
						new_autoname = '\n'.join(sorted(remaining_options))
						frappe.db.set_value("DocType", dt, "autoname", new_autoname)

						# ✅ ATUALIZAR PROPERTY SETTER
						if remaining_options:
							self.update_naming_series_property_setter(dt, new_autoname)
						else:
							self.remove_naming_series_property_setter(dt)

						frappe.clear_cache(doctype=dt)

						results["cleaned_doctypes"] += 1
						results["total_series_removed"] += removed_count
						results["details"][dt] = {"series_removed": removed_count}

						frappe.logger().info(
							f"🧹 {dt}: {removed_count} séries portuguesas removidas")

				except Exception as e:
					frappe.log_error(f"Erro ao limpar {dt}: {str(e)}",
									 "PortugueseNamingSeriesCustomizer")
					results["details"][dt] = {"error": str(e)}

			frappe.db.commit()
			return results

		except Exception as e:
			frappe.log_error(f"Erro na limpeza: {str(e)}", "PortugueseNamingSeriesCustomizer")
			return {"success": False, "error": str(e)}

	def remove_naming_series_property_setter(self, doctype):
		"""
		Remover Property Setter de naming_series
		"""
		try:
			ps_name = f"{doctype}-naming_series-options"
			if frappe.db.exists("Property Setter", ps_name):
				frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True)
				frappe.logger().info(f"🗑️ Property Setter removido: {ps_name}")
			return True
		except Exception as e:
			frappe.log_error(f"Erro ao remover Property Setter: {str(e)}",
							 "PortugueseNamingSeriesCustomizer")
			return False

	def validate_portuguese_naming_series(self, naming_series):
		"""
		Validar se naming_series é portuguesa
		"""
		if not naming_series:
			return False

		# ✅ PADRÃO: XX-YYYY-COMPANY.####
		pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{1,4}\.####$'
		return bool(re.match(pattern, naming_series))

	def get_portuguese_companies(self):
		"""
		Obter empresas portuguesas com compliance ativo
		"""
		return frappe.get_all("Company",
							  filters={
								  "country": "Portugal",
								  "portugal_compliance_enabled": 1
							  },
							  fields=["name", "abbr"])

	def get_naming_series_statistics(self):
		"""
		Obter estatísticas das naming_series portuguesas
		"""
		try:
			stats = {
				"total_doctypes": len(self.portuguese_series),
				"doctypes_with_portuguese_series": 0,
				"total_portuguese_series": 0,
				"companies": len(self.get_portuguese_companies()),
				"details": {}
			}

			for doctype in self.portuguese_series.keys():
				if frappe.db.exists("DocType", doctype):
					current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
					current_options = [opt.strip() for opt in current_autoname.split('\n') if
									   opt.strip()]

					portuguese_count = 0
					for option in current_options:
						if self.validate_portuguese_naming_series(option):
							portuguese_count += 1

					if portuguese_count > 0:
						stats["doctypes_with_portuguese_series"] += 1
						stats["total_portuguese_series"] += portuguese_count

					stats["details"][doctype] = {
						"total_options": len(current_options),
						"portuguese_options": portuguese_count
					}

			return stats

		except Exception as e:
			frappe.log_error(f"Erro ao obter estatísticas: {str(e)}",
							 "PortugueseNamingSeriesCustomizer")
			return {}


# ========== INSTÂNCIA GLOBAL ==========

# ✅ INSTÂNCIA GLOBAL PARA USO
portuguese_naming_customizer = PortugueseNamingSeriesCustomizer()


# ========== FUNÇÕES AUXILIARES PARA USO EXTERNO ==========

def setup_portuguese_naming_series(year=None, companies=None):
	"""Configurar naming_series portuguesas"""
	return portuguese_naming_customizer.setup_portuguese_naming_series(year, companies)


def remove_portuguese_naming_series(doctype=None, companies=None):
	"""Remover naming_series portuguesas"""
	return portuguese_naming_customizer.remove_portuguese_naming_series(doctype, companies)


def validate_portuguese_naming_series(naming_series):
	"""Validar se naming_series é portuguesa"""
	return portuguese_naming_customizer.validate_portuguese_naming_series(naming_series)


def get_naming_series_statistics():
	"""Obter estatísticas das naming_series"""
	return portuguese_naming_customizer.get_naming_series_statistics()


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def setup_naming_series_for_company(company_name):
	"""
	API para configurar naming_series para uma empresa específica
	"""
	try:
		company_data = frappe.get_value("Company", company_name,
										["name", "abbr", "country", "portugal_compliance_enabled"],
										as_dict=True)

		if not company_data:
			return {"success": False, "error": f"Empresa {company_name} não encontrada"}

		if company_data.country != "Portugal":
			return {"success": False, "error": "Empresa não é portuguesa"}

		if not company_data.portugal_compliance_enabled:
			return {"success": False, "error": "Portugal compliance não está ativo"}

		# ✅ CONFIGURAR PARA ESTA EMPRESA
		result = setup_portuguese_naming_series(companies=[company_data])
		return result

	except Exception as e:
		frappe.log_error(f"Erro ao configurar naming series para empresa: {str(e)}",
						 "PortugueseNamingSeriesCustomizer")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def setup_all_portuguese_naming_series():
	"""
	API para configurar naming_series para todas as empresas portuguesas
	"""
	try:
		result = setup_portuguese_naming_series()
		return result
	except Exception as e:
		frappe.log_error(f"Erro ao configurar todas as naming series: {str(e)}",
						 "PortugueseNamingSeriesCustomizer")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_portuguese_naming_statistics():
	"""
	API para obter estatísticas das naming_series portuguesas
	"""
	try:
		stats = get_naming_series_statistics()
		return {"success": True, "statistics": stats}
	except Exception as e:
		frappe.log_error(f"Erro ao obter estatísticas: {str(e)}",
						 "PortugueseNamingSeriesCustomizer")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def cleanup_portuguese_naming_series():
	"""
	API para limpar naming_series portuguesas
	"""
	try:
		result = remove_portuguese_naming_series()
		return result
	except Exception as e:
		frappe.log_error(f"Erro na limpeza: {str(e)}", "PortugueseNamingSeriesCustomizer")
		return {"success": False, "error": str(e)}


# ========== FUNÇÃO PARA EXECUÇÃO DIRETA ==========

def execute_setup():
	"""Executar configuração das naming_series portuguesas"""
	try:
		print("🇵🇹 Configurando naming_series portuguesas...")
		result = setup_portuguese_naming_series()

		if result.get("success"):
			print(
				f"✅ Sucesso: {result['updated_doctypes']} DocTypes, {result['total_series_added']} séries")
		else:
			print(f"❌ Erro: {result.get('error')}")

		return result
	except Exception as e:
		print(f"❌ Erro crítico: {str(e)}")
		return {"success": False, "error": str(e)}


# ========== EXECUÇÃO AUTOMÁTICA ==========

if __name__ == "__main__":
	execute_setup()
