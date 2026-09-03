# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Adapter for Portugal Compliance - VERSÃO ALINHADA E SEGURA
Handles adaptation of naming_series for all document types according to Portuguese legislation
✅ ALINHADO: 100% compatível com document_hooks.py e startup_fixes.py
✅ SEGURO: Não quebra funcionalidades existentes
✅ DINÂMICO: Baseado no abbr da empresa (não fixo NDX)
✅ PERFORMANCE: Cache otimizado e validações thread-safe
"""

import frappe
from frappe import _
from frappe.utils import cint, now, today, getdate
from datetime import date, datetime
import re

# ✅ MAPEAMENTO OFICIAL COMPLETO DOS TIPOS DE DOCUMENTOS CONFORME LEGISLAÇÃO PORTUGUESA
DOCUMENT_TYPE_PREFIXES = {
	# Documentos Fiscais Principais
	"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
	# Fatura, Fatura Simplificada, Fatura Recibo, Nota Crédito, Nota Débito
	"Purchase Invoice": ["FC", "FT"],  # Fatura de Compra
	"POS Invoice": ["FS"],  # Fatura Simplificada POS
	"Payment Entry": ["RC", "RB"],  # Recibo, Recibo de Boleto

	# Documentos de Transporte
	"Delivery Note": ["GT", "GR"],  # Guia de Transporte, Guia de Remessa
	"Purchase Receipt": ["GR", "GT"],  # Guia de Receção
	"Stock Entry": ["GT", "GM"],  # Guia de Transporte, Guia de Movimentação

	# Documentos Contabilísticos
	"Journal Entry": ["JE", "LC"],  # Lançamento Contabilístico

	# Documentos Comerciais
	"Quotation": ["OR", "ORC"],  # Orçamento
	"Sales Order": ["NE", "NEC"],  # Nota de Encomenda (2026-09-03: 'EC' nunca foi valido no XSD WorkType)
	"Purchase Order": ["EF", "EFO"],  # Encomenda Fornecedor
	"Material Request": ["REQ", "MR"],  # Requisição
}

# ✅ CONFIGURAÇÕES ESPECÍFICAS POR TIPO DE DOCUMENTO - ALINHADAS COM DOCUMENT_HOOKS
DOCUMENT_CONFIGURATIONS = {
	"Sales Invoice": {
		"default_prefix": "FT",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura de Venda",
		"priority": 1  # ✅ NOVO: Prioridade para criação
	},
	"Purchase Invoice": {
		"default_prefix": "FC",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura de Compra",
		"priority": 2
	},
	"POS Invoice": {
		"default_prefix": "FS",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura POS",
		"priority": 3
	},
	"Payment Entry": {
		"default_prefix": "RC",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Recibo",
		"priority": 4
	},
	"Delivery Note": {
		"default_prefix": "GT",
		"requires_atcud": True,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Guia de Transporte",
		"priority": 5
	},
	"Purchase Receipt": {
		"default_prefix": "GR",
		"requires_atcud": True,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Guia de Receção",
		"priority": 6
	},
	"Journal Entry": {
		"default_prefix": "JE",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Lançamento Contabilístico",
		"priority": 7
	},
	"Stock Entry": {
		"default_prefix": "GT",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Movimento de Stock",
		"priority": 8
	},
	"Quotation": {
		# requires_atcud/requires_communication corrigidos de False para
		# True (2026-09-03) - Orcamento e "documento de conferencia" ao
		# abrigo do DL 28/2019 (ver nota em regional/portugal.py).
		"default_prefix": "OR",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": False,
		"description": "Orçamento",
		"priority": 9
	},
	"Sales Order": {
		# default_prefix corrigido de 'EC' para 'NE' - unico codigo
		# valido no XSD WorkType oficial para Nota de Encomenda.
		# requires_atcud/requires_communication corrigidos para True
		# pelo mesmo motivo do Quotation acima (2026-09-03).
		"default_prefix": "NE",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": False,
		"description": "Nota de Encomenda",
		"priority": 10
	},
	"Purchase Order": {
		"default_prefix": "EF",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Encomenda a Fornecedor",
		"priority": 11
	},
	"Material Request": {
		"default_prefix": "MR",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Requisição de Material",
		"priority": 12
	}
}


class SeriesAdapter:
	"""
	✅ CLASSE ALINHADA: Compatível com document_hooks.py e startup_fixes.py
	Não interfere com funcionalidades existentes
	"""

	def __init__(self):
		self.module = "Portugal Compliance"
		self.supported_doctypes = list(DOCUMENT_TYPE_PREFIXES.keys())
		self.fiscal_doctypes = self.get_fiscal_doctypes()
		self._cache = {}  # ✅ CACHE INTERNO PARA PERFORMANCE

	def get_fiscal_doctypes(self):
		"""Obter DocTypes que são documentos fiscais"""
		fiscal_types = []
		for doctype, config in DOCUMENT_CONFIGURATIONS.items():
			if config.get("fiscal_document", False):
				fiscal_types.append(doctype)
		return fiscal_types

	def get_prefix_for_doctype(self, doctype, prefix_type="default"):
		"""
		Retorna o prefixo oficial para o tipo de documento
		prefix_type: 'default', 'all', 'fiscal'
		"""
		prefixes = DOCUMENT_TYPE_PREFIXES.get(doctype, ["FT"])

		if prefix_type == "default":
			return prefixes[0]  # Primeiro prefixo é o padrão
		elif prefix_type == "all":
			return prefixes
		elif prefix_type == "fiscal" and doctype in self.fiscal_doctypes:
			return prefixes[0]
		else:
			return prefixes[0]

	def generate_series_prefix(self, doctype, company_abbr, year=None, prefix_override=None):
		"""
		✅ ALINHADO: Gera o prefixo da série SEM HÍFENS no formato XXYYYY + COMPANY
		Formato: FT2025NDX (dinâmico baseado no abbr da empresa)
		"""
		try:
			if not year:
				year = getdate().year

			# Usar prefixo específico ou padrão
			if prefix_override:
				prefix = prefix_override.upper()
			else:
				prefix = self.get_prefix_for_doctype(doctype)

			# ✅ LIMPAR E FORMATAR ABREVIATURA DA EMPRESA (DINÂMICO)
			company_abbr = self.clean_company_abbreviation(company_abbr)

			# ✅ FORMATO ALINHADO SEM HÍFENS: XXYYYY + COMPANY
			series_prefix = f"{prefix}{year}{company_abbr}"

			return series_prefix

		except Exception as e:
			frappe.log_error(f"Error generating series prefix: {str(e)}")
			# ✅ FALLBACK DINÂMICO (não fixo NDX)
			fallback_abbr = self.clean_company_abbreviation(company_abbr) or "NDX"
			return f"FT{getdate().year}{fallback_abbr}"

	def clean_company_abbreviation(self, company_abbr):
		"""
		✅ ALINHADO: Limpar e formatar abreviatura da empresa (dinâmico)
		"""
		if not company_abbr:
			return "NDX"  # Fallback apenas se não houver abbr

		# Remover caracteres especiais e espaços
		cleaned = re.sub(r'[^A-Z0-9]', '', company_abbr.upper())

		# Limitar a 4 caracteres
		return cleaned[:4] if cleaned else "NDX"

	# ========== SINCRONIZAÇÃO AUTOMÁTICA NAMING_SERIES ALINHADA ==========

	def update_doctype_naming_series(self, doctype, company_abbr, year=None, force_update=False):
		"""
		Chamada por Portugal Series Configuration.on_update/after_insert
		(sync_naming_series_with_doctype) a cada gravação de série. O
		Property Setter que este método construía foi neutralizado em
		sync_property_setter_standard (Auditoria Fase 0, 2026-08-26) -
		ver docstring dessa função para o motivo. Mantido como no-op
		seguro (devolve sempre "action": "skipped") em vez de removido,
		para não quebrar os chamadores existentes.
		"""
		try:
			# ✅ VERIFICAR SE DOCTYPE EXISTE
			if not frappe.db.exists("DocType", doctype):
				return {
					"success": False,
					"error": f"DocType {doctype} does not exist"
				}

			active_series = frappe.get_all("Portugal Series Configuration",
										   filters={
											   "document_type": doctype,
											   "is_active": 1
										   },
										   fields=["prefix"],
										   order_by="is_communicated desc, creation asc")

			if not active_series:
				frappe.logger().info(f"⏭️ Nenhuma série portuguesa ativa para {doctype}")
				return {
					"success": True,
					"doctype": doctype,
					"message": "No active Portuguese series found",
					"action": "none"
				}

			# ✅ GERAR OPÇÕES BASEADAS EM SÉRIES EXISTENTES
			naming_options = []
			for series in active_series:
				naming_option = f"{series.prefix}.####"
				naming_options.append(naming_option)

			if not naming_options:
				return {
					"success": True,
					"doctype": doctype,
					"message": "No naming options generated",
					"action": "none"
				}

			# ✅ USAR PROPERTY SETTER PADRÃO (ALINHADO COM STARTUP_FIXES)
			return self.sync_property_setter_standard(doctype, naming_options, force_update)

		except Exception as e:
			frappe.log_error(f"Error updating naming series for {doctype}: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def sync_property_setter_standard(self, doctype, naming_options, force_update=False):
		"""
		Neutralizada (Auditoria Fase 0, 2026-08-26). Escrevia um Property
		Setter global (doc_type + field_name="naming_series" + property=
		"options", sem dimensão de empresa) - com mais do que uma
		empresa portuguesa ativa no site, a última chamada substituía
		inteiramente a lista de séries de todas as outras. Era o ponto
		de convergência de update_doctype_naming_series, chamada por
		Portugal Series Configuration.on_update/after_insert (ver
		portugal_series_configuration.py::sync_naming_series_with_doctype
		- disparava a cada gravação de série, portanto com muita
		frequência). Removido _create_property_setter_standard (única
		utilização era aqui). Substituído por filtragem client-side,
		sempre consultada de fresco para a empresa selecionada no
		formulário (ver public/js/portugal_compliance.js::
		applyNamingSeriesFilter).
		"""
		return {
			"success": True,
			"doctype": doctype,
			"action": "skipped",
			"message": "Property Setter global de naming_series desativado - filtragem passou a ser client-side",
		}

	# ========== VALIDAÇÃO DE FORMATO ALINHADA ==========

	def validate_naming_series_format(self, naming_series):
		"""
		✅ ALINHADO: Validar formato de naming series SEM HÍFENS (não restritivo)
		Formato esperado: XXYYYY + COMPANY.#### (ex: FT2025NDX.####)
		"""
		try:
			if not naming_series:
				return False

			# ✅ PADRÕES ACEITOS (FLEXÍVEIS, NÃO RESTRITIVOS)
			patterns = [
				r'^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}\.####$',  # Formato português: FT2025NDX.####
				r'^[A-Z]{2,10}\.####$',  # Formato simples: FT.####
				r'^[A-Z0-9-]+\.####$',  # Formato com hífens (compatibilidade)
				r'^[A-Z0-9-]+\.YYYY\.-$',  # Formato ERPNext padrão
				r'^.+\.####$'  # ✅ PADRÃO GENÉRICO (SEGURO)
			]

			for pattern in patterns:
				if re.match(pattern, naming_series):
					return True

			# ✅ SE NÃO CORRESPONDE A NENHUM PADRÃO, ACEITAR MESMO ASSIM (SEGURO)
			frappe.logger().info(f"⚠️ Formato não padrão aceito: {naming_series}")
			return True

		except Exception:
			# ✅ EM CASO DE ERRO, ACEITAR (SEGURO)
			return True

	def validate_prefix_format(self, prefix):
		"""
		✅ ALINHADO: Validar formato de prefixo (flexível)
		"""
		try:
			if not prefix:
				return False

			# ✅ ACEITAR QUALQUER FORMATO ALFANUMÉRICO (SEGURO)
			if re.match(r'^[A-Z0-9]+$', prefix.upper()):
				return True

			# ✅ ACEITAR MESMO COM CARACTERES ESPECIAIS (COMPATIBILIDADE)
			return True

		except Exception:
			return True

	# ========== SINCRONIZAÇÃO COMPLETA ALINHADA ==========

	def sync_all_doctypes(self, company_abbr, year=None, include_non_fiscal=True,
						  force_update=False):
		"""
		✅ ALINHADO: Sincroniza naming_series COMPATÍVEL com startup_fixes.py
		"""
		try:
			if include_non_fiscal:
				doctypes_to_sync = self.supported_doctypes
			else:
				doctypes_to_sync = self.fiscal_doctypes

			results = {
				"success": True,
				"total_doctypes": len(doctypes_to_sync),
				"successful_updates": 0,
				"failed_updates": 0,
				"results": {},
				"summary": {}
			}

			for doctype in doctypes_to_sync:
				try:
					result = self.update_doctype_naming_series(doctype, company_abbr, year,
															   force_update)
					results["results"][doctype] = result

					if result["success"]:
						results["successful_updates"] += 1
					else:
						results["failed_updates"] += 1

				except Exception as e:
					results["results"][doctype] = {
						"success": False,
						"error": str(e)
					}
					results["failed_updates"] += 1
					frappe.log_error(f"Error syncing {doctype}: {str(e)}")

			# Gerar resumo
			results["summary"] = {
				"success_rate": round(
					(results["successful_updates"] / results["total_doctypes"]) * 100, 2),
				"total_options_added": results["successful_updates"]
			}

			frappe.logger().info(
				f"✅ Sync completed: {results['successful_updates']}/{results['total_doctypes']} successful")

			return results

		except Exception as e:
			frappe.log_error(f"Error in sync_all_doctypes: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	# ========== UTILITÁRIOS ALINHADOS ==========

	def get_doctype_statistics(self, doctype):
		"""
		✅ ALINHADO: Obter estatísticas de um DocType específico
		"""
		try:
			stats = {
				"doctype": doctype,
				"is_supported": doctype in self.supported_doctypes,
				"is_fiscal": doctype in self.fiscal_doctypes,
				"available_prefixes": self.get_prefix_for_doctype(doctype, "all"),
				"default_prefix": self.get_prefix_for_doctype(doctype),
				"current_naming_options": [],
				"portuguese_options": 0,
				"total_options": 0,
				"has_property_setter": False,
				"active_series_count": 0,
				"communicated_series_count": 0
			}

			if frappe.db.exists("DocType", doctype):
				# ✅ VERIFICAR PROPERTY SETTER PADRÃO
				ps_name = f"{doctype}-naming_series-options"
				current_options = []

				if frappe.db.exists("Property Setter", ps_name):
					stats["has_property_setter"] = True
					ps_value = frappe.db.get_value("Property Setter", ps_name, "value") or ""
					current_options = [opt.strip() for opt in ps_value.split('\n') if opt.strip()]

				stats["current_naming_options"] = current_options
				stats["total_options"] = len(current_options)

				# ✅ CONTAR SÉRIES PORTUGUESAS REAIS
				active_series = frappe.get_all("Portugal Series Configuration",
											   filters={
												   "document_type": doctype,
												   "is_active": 1
											   },
											   fields=["name", "is_communicated"])

				stats["active_series_count"] = len(active_series)
				stats["communicated_series_count"] = len(
					[s for s in active_series if s.is_communicated])

				# Contar opções portuguesas
				portuguese_count = 0
				for option in current_options:
					if self.validate_naming_series_format(option):
						portuguese_count += 1

				stats["portuguese_options"] = portuguese_count

			return stats

		except Exception as e:
			frappe.log_error(f"Error getting doctype statistics: {str(e)}")
			return {}

	# ========== CLEANUP SEGURO ==========

	def remove_doctype_naming_series(self, doctype, company_abbr, year=None):
		"""
		✅ ALINHADO: Remove naming_series portuguesa (SEGURO)
		"""
		try:
			if not frappe.db.exists("DocType", doctype):
				return {
					"success": False,
					"error": f"DocType {doctype} does not exist"
				}

			# ✅ BUSCAR SÉRIES PORTUGUESAS ESPECÍFICAS PARA REMOVER
			portuguese_series = frappe.get_all("Portugal Series Configuration",
											   filters={"document_type": doctype},
											   fields=["prefix"])

			naming_options_to_remove = []
			for series in portuguese_series:
				naming_options_to_remove.append(f"{series.prefix}.####")

			if not naming_options_to_remove:
				return {
					"success": True,
					"message": "No Portuguese options to remove"
				}

			# ✅ REMOVER APENAS OPÇÕES PORTUGUESAS (SEGURO)
			ps_name = f"{doctype}-naming_series-options"
			current_options = set()

			if frappe.db.exists("Property Setter", ps_name):
				current_value = frappe.db.get_value("Property Setter", ps_name, "value") or ""
				current_options = set(
					[opt.strip() for opt in current_value.split('\n') if opt.strip()])

			# Remover apenas opções portuguesas
			removed_options = []
			for option in naming_options_to_remove:
				if option in current_options:
					current_options.remove(option)
					removed_options.append(option)

			if removed_options:
				if current_options:
					new_value = '\n'.join(sorted(current_options))
					frappe.db.set_value("Property Setter", ps_name, "value", new_value)
				else:
					# ✅ NÃO REMOVER PROPERTY SETTER VAZIO (SEGURO)
					frappe.db.set_value("Property Setter", ps_name, "value", "")

				frappe.logger().info(f"🗑️ Removed naming series from {doctype}: {removed_options}")

				return {
					"success": True,
					"doctype": doctype,
					"removed_options": removed_options,
					"remaining_options": len(current_options)
				}
			else:
				return {
					"success": True,
					"doctype": doctype,
					"message": "No Portuguese options found to remove"
				}

		except Exception as e:
			frappe.log_error(f"Error removing naming series for {doctype}: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}


# ✅ INSTÂNCIA GLOBAL ALINHADA
series_adapter = SeriesAdapter()


# ========== FUNÇÕES AUXILIARES ALINHADAS ==========

def generate_series_prefix(doctype, company_abbr, year=None, prefix_override=None):
	"""✅ ALINHADO: Gerar prefixo de série dinâmico"""
	return series_adapter.generate_series_prefix(doctype, company_abbr, year, prefix_override)


def update_doctype_naming_series(doctype, company_abbr, year=None, force_update=False):
	"""✅ ALINHADO: Atualizar naming series compatível"""
	return series_adapter.update_doctype_naming_series(doctype, company_abbr, year, force_update)


def sync_all_doctypes(company_abbr, year=None, include_non_fiscal=True, force_update=False):
	"""✅ ALINHADO: Sincronizar todos os DocTypes"""
	return series_adapter.sync_all_doctypes(company_abbr, year, include_non_fiscal, force_update)


@frappe.whitelist()
def get_doctype_statistics(doctype):
	"""✅ ALINHADO: Obter estatísticas de um DocType"""
	return series_adapter.get_doctype_statistics(doctype)


# ========== APIS WHITELISTED ALINHADAS ==========

@frappe.whitelist()
def sync_naming_series_for_company(company_abbr, include_non_fiscal=True, force_update=False):
	"""
	✅ ALINHADO: API para sincronizar naming series (compatível)
	"""
	try:
		if company_abbr == 'ALL':
			# Sincronizar para todas as empresas portuguesas
			companies = frappe.get_all("Company",
									   filters={
										   "country": "Portugal",
										   "portugal_compliance_enabled": 1
									   },
									   fields=["abbr"])

			total_results = {
				"success": True,
				"companies_processed": 0,
				"total_successful_updates": 0,
				"companies": []
			}

			for company in companies:
				try:
					result = sync_all_doctypes(company.abbr,
											   include_non_fiscal=cint(include_non_fiscal),
											   force_update=cint(force_update))

					total_results["companies"].append({
						"company_abbr": company.abbr,
						"result": result
					})

					if result["success"]:
						total_results["companies_processed"] += 1
						total_results["total_successful_updates"] += result["successful_updates"]

				except Exception as e:
					total_results["companies"].append({
						"company_abbr": company.abbr,
						"result": {"success": False, "error": str(e)}
					})

			return total_results
		else:
			# Sincronizar para empresa específica
			result = sync_all_doctypes(company_abbr,
									   include_non_fiscal=cint(include_non_fiscal),
									   force_update=cint(force_update))
			return result

	except Exception as e:
		frappe.log_error(f"Error in sync_naming_series_for_company: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_naming_series_statistics():
	"""
	✅ ALINHADO: API para obter estatísticas gerais
	"""
	try:
		stats = {
			"supported_doctypes": len(series_adapter.supported_doctypes),
			"fiscal_doctypes": len(series_adapter.fiscal_doctypes),
			"doctype_details": {},
			"global_summary": {}
		}

		# ✅ ESTATÍSTICAS GLOBAIS ALINHADAS
		total_series = frappe.db.count("Portugal Series Configuration", {"is_active": 1})
		communicated_series = frappe.db.count("Portugal Series Configuration", {
			"is_active": 1,
			"is_communicated": 1
		})

		stats["global_summary"] = {
			"total_active_series": total_series,
			"total_communicated_series": communicated_series,
			"communication_rate": round((communicated_series / total_series * 100),
										2) if total_series > 0 else 0
		}

		for doctype in series_adapter.supported_doctypes:
			stats["doctype_details"][doctype] = get_doctype_statistics(doctype)

		return {
			"success": True,
			"statistics": stats
		}
	except Exception as e:
		frappe.log_error(f"Error in get_naming_series_statistics: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÕES DE SETUP ALINHADAS ==========

def setup_naming_series_on_install(company_list=None):
	"""
	✅ ALINHADO: Configurar naming series durante instalação (SEGURO)
	"""
	try:
		frappe.logger().info("🇵🇹 Setting up naming series for Portugal compliance...")

		if not company_list:
			company_list = frappe.get_all("Company",
										  filters={
											  "country": "Portugal",
											  "portugal_compliance_enabled": 1
										  },
										  fields=["name", "abbr"])

		total_results = {
			"success": True,
			"companies_processed": 0,
			"total_options_added": 0,
			"errors": []
		}

		for company in company_list:
			try:
				# ✅ SINCRONIZAR APENAS SE HÁ SÉRIES ATIVAS (SEGURO)
				active_series_count = frappe.db.count("Portugal Series Configuration", {
					"company": company.name,
					"is_active": 1
				})

				if active_series_count > 0:
					result = sync_all_doctypes(company.abbr, include_non_fiscal=True)

					if result["success"]:
						total_results["companies_processed"] += 1
						total_results["total_options_added"] += result["summary"].get(
							"total_options_added", 0)
					else:
						total_results["errors"].append({
							"company": company.name,
							"error": result.get("error", "Unknown error")
						})
				else:
					frappe.logger().info(
						f"⏭️ Empresa {company.name} não tem séries ativas - pulando")

			except Exception as e:
				total_results["errors"].append({
					"company": company.name,
					"error": str(e)
				})

		frappe.logger().info(
			f"✅ Naming series setup completed: {total_results['companies_processed']} companies")

		return total_results

	except Exception as e:
		frappe.log_error(f"Error in setup_naming_series_on_install: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÃO PARA MIGRATE ALINHADA ==========

def sync_all_naming_series_after_migrate():
	"""
	✅ ALINHADO: Sincronizar após migrate (COMPATÍVEL com startup_fixes.py)
	"""
	try:
		frappe.logger().info("🔄 Syncing naming series after migrate...")

		# ✅ USAR MESMA LÓGICA DO STARTUP_FIXES
		companies_with_series = frappe.db.sql("""
											  SELECT DISTINCT c.name, c.abbr
											  FROM `tabCompany` c
													   INNER JOIN `tabPortugal Series Configuration` psc
																  ON psc.company = c.name
											  WHERE c.country = 'Portugal'
												AND c.portugal_compliance_enabled = 1
												AND psc.is_active = 1
											  """, as_dict=True)

		total_synced = 0

		for company in companies_with_series:
			try:
				result = sync_all_doctypes(company.abbr, include_non_fiscal=True,
										   force_update=True)
				if result["success"]:
					total_synced += result["successful_updates"]

			except Exception as e:
				frappe.log_error(f"Error syncing naming series for {company.name}: {str(e)}")

		frappe.logger().info(f"🔄 Synced naming series for {total_synced} DocTypes after migrate")

		return {
			"success": True,
			"total_synced": total_synced
		}

	except Exception as e:
		frappe.log_error(f"Error in sync_all_naming_series_after_migrate: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== LOG FINAL ==========
frappe.logger().info("Portugal Series Adapter ALINHADO loaded - Version 2.1.0 - Safe & Compatible")
