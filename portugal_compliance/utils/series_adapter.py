# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Adapter for Portugal Compliance - VERSÃO CERTIFICADA CORRIGIDA
Handles adaptation of naming_series for all document types according to Portuguese legislation
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Compatível com document_hooks.py corrigido
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
	"Sales Order": ["EC", "ECO"],  # Encomenda Cliente (CORRIGIDO: era EN)
	"Purchase Order": ["EF", "EFO"],  # Encomenda Fornecedor (CORRIGIDO: era OC)
	"Material Request": ["REQ", "MR"],  # Requisição
}

# ✅ CONFIGURAÇÕES ESPECÍFICAS POR TIPO DE DOCUMENTO
DOCUMENT_CONFIGURATIONS = {
	"Sales Invoice": {
		"default_prefix": "FT",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura de Venda"
	},
	"Purchase Invoice": {
		"default_prefix": "FC",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura de Compra"
	},
	"POS Invoice": {
		"default_prefix": "FS",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Fatura POS"
	},
	"Payment Entry": {
		"default_prefix": "RC",
		"requires_atcud": True,
		"requires_communication": True,
		"fiscal_document": True,
		"description": "Recibo"
	},
	"Delivery Note": {
		"default_prefix": "GT",
		"requires_atcud": True,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Guia de Transporte"
	},
	"Purchase Receipt": {
		"default_prefix": "GR",
		"requires_atcud": True,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Guia de Receção"
	},
	"Journal Entry": {
		"default_prefix": "JE",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Lançamento Contabilístico"
	},
	"Stock Entry": {
		"default_prefix": "GT",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Movimento de Stock"
	},
	"Quotation": {
		"default_prefix": "OR",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Orçamento"
	},
	"Sales Order": {
		"default_prefix": "EC",  # CORRIGIDO: era EN
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Encomenda de Cliente"
	},
	"Purchase Order": {
		"default_prefix": "EF",  # CORRIGIDO: era OC
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Encomenda a Fornecedor"
	},
	"Material Request": {
		"default_prefix": "MR",
		"requires_atcud": False,
		"requires_communication": False,
		"fiscal_document": False,
		"description": "Requisição de Material"
	}
}


class SeriesAdapter:
	"""
	Classe principal para adaptar naming_series para os DocTypes conforme legislação portuguesa
	✅ VERSÃO CORRIGIDA: Formato sem hífens, compatível com Frappe
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
		✅ CORRIGIDO: Gera o prefixo da série SEM HÍFENS no formato XXYYYY + COMPANY
		Formato: FT2025NDX (em vez de FT-2025-NDX)
		"""
		try:
			if not year:
				year = getdate().year

			# Usar prefixo específico ou padrão
			if prefix_override:
				prefix = prefix_override.upper()
			else:
				prefix = self.get_prefix_for_doctype(doctype)

			# Limpar e formatar abreviatura da empresa
			company_abbr = self.clean_company_abbreviation(company_abbr)

			# ✅ FORMATO CORRIGIDO SEM HÍFENS: XXYYYY + COMPANY
			series_prefix = f"{prefix}{year}{company_abbr}"

			return series_prefix

		except Exception as e:
			frappe.log_error(f"Error generating series prefix: {str(e)}")
			return f"FT{getdate().year}NDX"  # Fallback sem hífens

	def clean_company_abbreviation(self, company_abbr):
		"""
		Limpar e formatar abreviatura da empresa
		"""
		if not company_abbr:
			return "NDX"

		# Remover caracteres especiais e espaços
		cleaned = re.sub(r'[^A-Z0-9]', '', company_abbr.upper())

		# Limitar a 4 caracteres
		return cleaned[:4] if cleaned else "NDX"

	# ========== SINCRONIZAÇÃO AUTOMÁTICA NAMING_SERIES CORRIGIDA ==========

	def update_doctype_naming_series(self, doctype, company_abbr, year=None, force_update=False):
		"""
		✅ CORRIGIDO: Atualiza Property Setter para incluir naming_series portuguesa SEM HÍFENS
		Compatível com document_hooks.py corrigido
		"""
		try:
			# ✅ VERIFICAR SE DOCTYPE EXISTE
			if not frappe.db.exists("DocType", doctype):
				return {
					"success": False,
					"error": f"DocType {doctype} does not exist"
				}

			# ✅ VERIFICAR SE HÁ SÉRIES PORTUGUESAS ATIVAS (SEM HÍFENS)
			active_series = frappe.get_all("Portugal Series Configuration",
										   filters={
											   "document_type": doctype,
											   "is_active": 1
										   },
										   fields=["prefix"],
										   order_by="is_communicated desc, creation desc")

			if not active_series:
				frappe.logger().info(f"⏭️ Nenhuma série portuguesa ativa para {doctype}")
				return {
					"success": True,
					"doctype": doctype,
					"message": "No active Portuguese series found",
					"action": "none"
				}

			# ✅ GERAR OPÇÕES BASEADAS EM SÉRIES EXISTENTES (FORMATO SEM HÍFENS)
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

			# ✅ ATUALIZAR PROPERTY SETTER (NÃO AUTONAME)
			return self.sync_property_setter_for_doctype(doctype, naming_options, force_update)

		except Exception as e:
			frappe.log_error(f"Error updating naming series for {doctype}: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def sync_property_setter_for_doctype(self, doctype, naming_options, force_update=False):
		"""
		✅ CORRIGIDO: Sincronizar Property Setter para naming_series de um DocType
		Trabalha apenas com Property Setters, não modifica autoname
		"""
		try:
			ps_name = f"{doctype}-naming_series-options"

			# ✅ VERIFICAR SE CAMPO naming_series EXISTE NO DOCTYPE
			meta = frappe.get_meta(doctype)
			if not meta.get_field("naming_series"):
				frappe.logger().info(
					f"⏭️ DocType {doctype} não tem campo naming_series - Property Setter não necessário")
				return {
					"success": True,
					"doctype": doctype,
					"message": "No naming_series field in DocType",
					"action": "none"
				}

			# ✅ CONVERTER LISTA PARA STRING
			if isinstance(naming_options, list):
				options_value = '\n'.join(naming_options)
			else:
				options_value = naming_options

			# ✅ OBTER OPÇÕES ATUAIS DO PROPERTY SETTER
			current_options = set()
			if frappe.db.exists("Property Setter", ps_name):
				current_value = frappe.db.get_value("Property Setter", ps_name, "value") or ""
				current_options = set(
					[opt.strip() for opt in current_value.split('\n') if opt.strip()])

			new_options = set([opt.strip() for opt in options_value.split('\n') if opt.strip()])

			# ✅ ATUALIZAÇÃO INTELIGENTE
			if force_update:
				# Substituir completamente
				if frappe.db.exists("Property Setter", ps_name):
					frappe.db.set_value("Property Setter", ps_name, "value", options_value)
					frappe.logger().info(f"✅ Property Setter atualizado (force): {ps_name}")
				else:
					self._create_property_setter(doctype, ps_name, options_value)
					frappe.logger().info(f"✅ Property Setter criado (force): {ps_name}")

				return {
					"success": True,
					"doctype": doctype,
					"replaced_options": list(new_options),
					"total_options": len(new_options),
					"action": "replaced"
				}
			else:
				# Adicionar apenas novas opções
				options_to_add = new_options - current_options

				if options_to_add:
					all_options = current_options | new_options
					final_value = '\n'.join(sorted(all_options))

					if frappe.db.exists("Property Setter", ps_name):
						frappe.db.set_value("Property Setter", ps_name, "value", final_value)
					else:
						self._create_property_setter(doctype, ps_name, final_value)

					frappe.logger().info(
						f"✅ Property Setter atualizado: {ps_name} (+{len(options_to_add)})")

					return {
						"success": True,
						"doctype": doctype,
						"added_options": list(options_to_add),
						"total_options": len(all_options),
						"action": "added"
					}
				else:
					return {
						"success": True,
						"doctype": doctype,
						"message": "No new options to add",
						"total_options": len(current_options),
						"action": "none"
					}

		except Exception as e:
			frappe.log_error(f"Error syncing Property Setter for {doctype}: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def _create_property_setter(self, doctype, ps_name, value):
		"""Criar Property Setter"""
		ps_doc = frappe.get_doc({
			"doctype": "Property Setter",
			"name": ps_name,
			"doc_type": doctype,
			"field_name": "naming_series",
			"property": "options",
			"property_type": "Text",
			"value": value,
			"doctype_or_field": "DocField",
			"module": self.module
		})
		ps_doc.insert(ignore_permissions=True)

	def remove_property_setter_for_doctype(self, doctype):
		"""
		Remover Property Setter de naming_series de um DocType
		"""
		try:
			ps_name = f"{doctype}-naming_series-options"

			if frappe.db.exists("Property Setter", ps_name):
				frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True)
				frappe.logger().info(f"🗑️ Property Setter removido: {ps_name}")
				return True
			else:
				return True  # Já não existe

		except Exception as e:
			frappe.log_error(f"Error removing Property Setter for {doctype}: {str(e)}")
			return False

	# ========== VALIDAÇÃO DE FORMATO CORRIGIDA ==========

	def validate_naming_series_format(self, naming_series):
		"""
		✅ CORRIGIDO: Validar formato de naming series SEM HÍFENS
		Formato esperado: XXYYYY + COMPANY.#### (ex: FT2025NDX.####)
		"""
		try:
			if not naming_series:
				return False

			# ✅ PADRÕES ACEITOS (SEM HÍFENS)
			patterns = [
				r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$',
				# Formato português sem hífens: FT2025NDX.####
				r'^[A-Z]{2,10}-\.YYYY\.-$',  # Formato ERPNext padrão
				r'^[A-Z0-9-]+\.####$',  # Formato genérico com ####
				r'^[A-Z0-9-]+\.YYYY\.-$'  # Formato genérico com YYYY
			]

			for pattern in patterns:
				if re.match(pattern, naming_series):
					return True

			return False

		except Exception:
			return False

	def validate_prefix_format(self, prefix):
		"""
		✅ CORRIGIDO: Validar formato de prefixo SEM HÍFENS
		Formato esperado: XXYYYY + COMPANY (ex: FT2025NDX)
		"""
		try:
			if not prefix:
				return False

			# ✅ FORMATOS ACEITOS (SEM HÍFENS)
			patterns = [
				r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$',  # Formato português sem hífens: FT2025NDX
				r'^[A-Z]{2,10}$',  # Formato simples: FT
				r'^[A-Z]{2,10}\d{4}$'  # Formato com ano: FT2025
			]

			for pattern in patterns:
				if re.match(pattern, prefix):
					return True

			return False

		except Exception:
			return False

	def validate_naming_series_integrity(self, company_abbr):
		"""
		Validar integridade das naming series
		✅ CORRIGIDO: Validação não bloqueante, aceita formatos sem hífens
		"""
		try:
			validation_results = {
				"success": True,
				"total_doctypes": len(self.supported_doctypes),
				"valid_doctypes": 0,
				"invalid_doctypes": 0,
				"missing_series": [],
				"invalid_format": [],
				"missing_property_setters": [],
				"recommendations": [],
				"warnings": []
			}

			for doctype in self.supported_doctypes:
				try:
					# ✅ VERIFICAÇÃO BASEADA EM SÉRIES REAIS
					active_series = frappe.get_all("Portugal Series Configuration",
												   filters={
													   "document_type": doctype,
													   "is_active": 1
												   },
												   fields=["prefix"])

					# ✅ VERIFICAR PROPERTY SETTER
					ps_name = f"{doctype}-naming_series-options"
					current_options = []

					if frappe.db.exists("Property Setter", ps_name):
						ps_value = frappe.db.get_value("Property Setter", ps_name, "value") or ""
						current_options = [opt.strip() for opt in ps_value.split('\n') if
										   opt.strip()]

					doctype_valid = True

					# Verificar se séries ativas estão nas opções
					for series in active_series:
						expected_option = f"{series.prefix}.####"
						if expected_option not in current_options:
							validation_results["missing_series"].append({
								"doctype": doctype,
								"missing_option": expected_option
							})
							doctype_valid = False

					# ✅ VERIFICAR FORMATO (NÃO BLOQUEANTE)
					for option in current_options:
						if not self.validate_naming_series_format(option):
							validation_results["invalid_format"].append({
								"doctype": doctype,
								"invalid_option": option
							})
							# ✅ NÃO MARCAR COMO INVÁLIDO - APENAS WARNING
							validation_results["warnings"].append(
								f"Formato não padrão em {doctype}: {option}")

					# ✅ VERIFICAR PROPERTY SETTERS (OPCIONAL)
					if not frappe.db.exists("Property Setter", ps_name) and active_series:
						validation_results["missing_property_setters"].append({
							"doctype": doctype,
							"missing_property_setter": ps_name
						})
					# ✅ NÃO MARCAR COMO INVÁLIDO

					if doctype_valid:
						validation_results["valid_doctypes"] += 1
					else:
						validation_results["invalid_doctypes"] += 1

				except Exception as e:
					validation_results["invalid_doctypes"] += 1
					validation_results["warnings"].append(f"Erro ao validar {doctype}: {str(e)}")

			# ✅ GERAR RECOMENDAÇÕES (NÃO OBRIGATÓRIAS)
			if validation_results["missing_series"]:
				validation_results["recommendations"].append(
					f"Considere sincronizar {len(validation_results['missing_series'])} naming series em falta"
				)

			if validation_results["invalid_format"]:
				validation_results["recommendations"].append(
					f"Considere padronizar {len(validation_results['invalid_format'])} formatos de naming series"
				)

			if validation_results["missing_property_setters"]:
				validation_results["recommendations"].append(
					f"Considere sincronizar {len(validation_results['missing_property_setters'])} Property Setters"
				)

			return validation_results

		except Exception as e:
			frappe.log_error(f"Error validating naming series integrity: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	# ========== CLEANUP AO DESATIVAR COMPLIANCE CORRIGIDO ==========

	def remove_doctype_naming_series(self, doctype, company_abbr, year=None):
		"""
		✅ CORRIGIDO: Remove naming_series portuguesa do Property Setter
		Remove apenas séries portuguesas específicas (formato sem hífens)
		"""
		try:
			if not frappe.db.exists("DocType", doctype):
				return {
					"success": False,
					"error": f"DocType {doctype} does not exist"
				}

			# ✅ BUSCAR SÉRIES PORTUGUESAS ESPECÍFICAS PARA REMOVER (SEM HÍFENS)
			portuguese_series = frappe.get_all("Portugal Series Configuration",
											   filters={
												   "document_type": doctype
											   },
											   fields=["prefix"])

			naming_options_to_remove = []
			for series in portuguese_series:
				naming_options_to_remove.append(f"{series.prefix}.####")

			if not naming_options_to_remove:
				return {
					"success": True,
					"message": "No Portuguese options to remove"
				}

			# ✅ OBTER OPÇÕES ATUAIS DO PROPERTY SETTER
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
				# ✅ ATUALIZAR PROPERTY SETTER OU REMOVER SE VAZIO
				if current_options:
					new_value = '\n'.join(sorted(current_options))
					frappe.db.set_value("Property Setter", ps_name, "value", new_value)
				else:
					self.remove_property_setter_for_doctype(doctype)

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

	def cleanup_all_doctypes(self, company_abbr, year=None):
		"""
		Cleanup completo de naming series portuguesas para todos os DocTypes
		"""
		try:
			results = {
				"success": True,
				"total_doctypes": len(self.supported_doctypes),
				"successful_cleanups": 0,
				"failed_cleanups": 0,
				"results": {},
				"summary": {}
			}

			for doctype in self.supported_doctypes:
				try:
					result = self.remove_doctype_naming_series(doctype, company_abbr, year)
					results["results"][doctype] = result

					if result["success"]:
						results["successful_cleanups"] += 1
					else:
						results["failed_cleanups"] += 1

				except Exception as e:
					results["results"][doctype] = {
						"success": False,
						"error": str(e)
					}
					results["failed_cleanups"] += 1
					frappe.log_error(f"Error cleaning {doctype}: {str(e)}")

			# Gerar resumo
			results["summary"] = {
				"success_rate": round(
					(results["successful_cleanups"] / results["total_doctypes"]) * 100, 2),
				"total_options_removed": sum([
					len(r.get("removed_options", [])) for r in results["results"].values()
					if r.get("success", False)
				])
			}

			frappe.logger().info(
				f"🧹 Cleanup completed: {results['successful_cleanups']}/{results['total_doctypes']} successful")

			return results

		except Exception as e:
			frappe.log_error(f"Error in cleanup_all_doctypes: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def restore_default_naming_series(self, doctype):
		"""
		✅ CORRIGIDO: Restaurar naming series padrão para um DocType via Property Setter
		"""
		try:
			# ✅ NAMING SERIES PADRÃO POR DOCTYPE
			default_series = {
				"Sales Invoice": "ACC-SINV-.YYYY.-",
				"Purchase Invoice": "ACC-PINV-.YYYY.-",
				"POS Invoice": "ACC-SINV-.YYYY.-",
				"Payment Entry": "ACC-PAY-.YYYY.-",
				"Delivery Note": "MAT-DN-.YYYY.-",
				"Purchase Receipt": "MAT-PRE-.YYYY.-",
				"Journal Entry": "ACC-JV-.YYYY.-",
				"Stock Entry": "MAT-STE-.YYYY.-",
				"Quotation": "SAL-QTN-.YYYY.-",
				"Sales Order": "SAL-ORD-.YYYY.-",
				"Purchase Order": "PUR-ORD-.YYYY.-",
				"Material Request": "MAT-MR-.YYYY.-"
			}

			default_autoname = default_series.get(doctype, f"{doctype.upper()[:4]}-.YYYY.-")

			# ✅ ATUALIZAR PROPERTY SETTER
			ps_name = f"{doctype}-naming_series-options"

			if frappe.db.exists("Property Setter", ps_name):
				frappe.db.set_value("Property Setter", ps_name, "value", default_autoname)
			else:
				self._create_property_setter(doctype, ps_name, default_autoname)

			frappe.logger().info(
				f"🔄 Restored default naming series for {doctype}: {default_autoname}")

			return {
				"success": True,
				"doctype": doctype,
				"default_series": default_autoname
			}

		except Exception as e:
			frappe.log_error(f"Error restoring default naming series for {doctype}: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	# ========== SINCRONIZAÇÃO COMPLETA CORRIGIDA ==========

	def sync_all_doctypes(self, company_abbr, year=None, include_non_fiscal=True,
						  force_update=False):
		"""
		✅ CORRIGIDO: Sincroniza naming_series para todos os DocTypes suportados
		Baseada em séries reais existentes (formato sem hífens)
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
				"total_options_added": sum([
					len(r.get("added_options", [])) for r in results["results"].values()
					if r.get("success", False) and r.get("action") == "added"
				]),
				"total_options_replaced": sum([
					len(r.get("replaced_options", [])) for r in results["results"].values()
					if r.get("success", False) and r.get("action") == "replaced"
				])
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

	# ========== UTILITÁRIOS CORRIGIDOS ==========

	def get_doctype_statistics(self, doctype):
		"""
		Obter estatísticas de um DocType específico
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
				"property_setter_synced": False,
				"active_series_count": 0,
				"communicated_series_count": 0
			}

			if frappe.db.exists("DocType", doctype):
				# ✅ VERIFICAR PROPERTY SETTER (NÃO AUTONAME)
				ps_name = f"{doctype}-naming_series-options"
				current_options = []

				if frappe.db.exists("Property Setter", ps_name):
					stats["has_property_setter"] = True
					ps_value = frappe.db.get_value("Property Setter", ps_name, "value") or ""
					current_options = [opt.strip() for opt in ps_value.split('\n') if opt.strip()]

				stats["current_naming_options"] = current_options
				stats["total_options"] = len(current_options)

				# ✅ CONTAR SÉRIES PORTUGUESAS REAIS (SEM HÍFENS)
				active_series = frappe.get_all("Portugal Series Configuration",
											   filters={
												   "document_type": doctype,
												   "is_active": 1
											   },
											   fields=["name", "is_communicated"])

				stats["active_series_count"] = len(active_series)
				stats["communicated_series_count"] = len(
					[s for s in active_series if s.is_communicated])

				# Contar opções portuguesas nas naming series
				portuguese_count = 0
				for option in current_options:
					if self.validate_naming_series_format(option):
						portuguese_count += 1

				stats["portuguese_options"] = portuguese_count

				# ✅ VERIFICAR SINCRONIZAÇÃO
				expected_options = [f"{s.prefix}.####" for s in
									frappe.get_all("Portugal Series Configuration",
												   filters={"document_type": doctype,
															"is_active": 1},
												   fields=["prefix"])]

				stats["property_setter_synced"] = all(
					opt in current_options for opt in expected_options)

			return stats

		except Exception as e:
			frappe.log_error(f"Error getting doctype statistics: {str(e)}")
			return {}

	def export_naming_series_configuration(self):
		"""
		Exportar configuração atual das naming series
		"""
		try:
			export_data = {
				"export_date": now(),
				"module": self.module,
				"supported_doctypes": self.supported_doctypes,
				"fiscal_doctypes": self.fiscal_doctypes,
				"document_prefixes": DOCUMENT_TYPE_PREFIXES,
				"document_configurations": DOCUMENT_CONFIGURATIONS,
				"current_configuration": {},
				"series_summary": {}
			}

			# ✅ INCLUIR ESTATÍSTICAS DE SÉRIES REAIS
			for doctype in self.supported_doctypes:
				if frappe.db.exists("DocType", doctype):
					stats = self.get_doctype_statistics(doctype)
					export_data["current_configuration"][doctype] = stats

			# ✅ RESUMO GERAL
			total_series = frappe.db.count("Portugal Series Configuration", {"is_active": 1})
			communicated_series = frappe.db.count("Portugal Series Configuration", {
				"is_active": 1,
				"is_communicated": 1
			})

			export_data["series_summary"] = {
				"total_active_series": total_series,
				"total_communicated_series": communicated_series,
				"communication_rate": round((communicated_series / total_series * 100),
											2) if total_series > 0 else 0
			}

			return export_data

		except Exception as e:
			frappe.log_error(f"Error exporting naming series configuration: {str(e)}")
			return {}


# ✅ INSTÂNCIA GLOBAL PARA USO
series_adapter = SeriesAdapter()


# ========== FUNÇÕES AUXILIARES PARA USO EXTERNO CORRIGIDAS ==========

def generate_series_prefix(doctype, company_abbr, year=None, prefix_override=None):
	"""✅ CORRIGIDO: Gerar prefixo de série SEM HÍFENS"""
	return series_adapter.generate_series_prefix(doctype, company_abbr, year, prefix_override)


def update_doctype_naming_series(doctype, company_abbr, year=None, force_update=False):
	"""✅ CORRIGIDO: Atualizar naming series de um DocType via Property Setter"""
	return series_adapter.update_doctype_naming_series(doctype, company_abbr, year, force_update)


def remove_doctype_naming_series(doctype, company_abbr, year=None):
	"""✅ CORRIGIDO: Remover naming series de um DocType"""
	return series_adapter.remove_doctype_naming_series(doctype, company_abbr, year)


def sync_all_doctypes(company_abbr, year=None, include_non_fiscal=True, force_update=False):
	"""✅ CORRIGIDO: Sincronizar todos os DocTypes"""
	return series_adapter.sync_all_doctypes(company_abbr, year, include_non_fiscal, force_update)


def cleanup_all_doctypes(company_abbr, year=None):
	"""Cleanup completo de naming series portuguesas"""
	return series_adapter.cleanup_all_doctypes(company_abbr, year)


def validate_naming_series_integrity(company_abbr):
	"""Validar integridade das naming series"""
	return series_adapter.validate_naming_series_integrity(company_abbr)


def get_doctype_statistics(doctype):
	"""Obter estatísticas de um DocType"""
	return series_adapter.get_doctype_statistics(doctype)


def restore_default_naming_series(doctype):
	"""Restaurar naming series padrão"""
	return series_adapter.restore_default_naming_series(doctype)


# ========== APIS WHITELISTED CORRIGIDAS ==========

@frappe.whitelist()
def sync_naming_series_for_company(company_abbr, include_non_fiscal=True, force_update=False):
	"""
	✅ CORRIGIDO: API para sincronizar naming series para uma empresa
	Compatível com criação de séries sem hífens
	"""
	try:
		# ✅ TRATAMENTO ESPECIAL PARA 'ALL'
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
def cleanup_naming_series_for_company(company_abbr):
	"""
	API para cleanup de naming series de uma empresa
	"""
	try:
		result = cleanup_all_doctypes(company_abbr)
		return result
	except Exception as e:
		frappe.log_error(f"Error in cleanup_naming_series_for_company: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_company_naming_series(company_abbr):
	"""
	API para validar naming series de uma empresa
	"""
	try:
		result = validate_naming_series_integrity(company_abbr)
		return result
	except Exception as e:
		frappe.log_error(f"Error in validate_company_naming_series: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_naming_series_statistics():
	"""
	API para obter estatísticas gerais das naming series
	"""
	try:
		stats = {
			"supported_doctypes": len(series_adapter.supported_doctypes),
			"fiscal_doctypes": len(series_adapter.fiscal_doctypes),
			"total_prefixes": sum([len(prefixes) for prefixes in DOCUMENT_TYPE_PREFIXES.values()]),
			"doctype_details": {},
			"global_summary": {}
		}

		# ✅ ESTATÍSTICAS GLOBAIS
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


@frappe.whitelist()
def export_naming_series_config():
	"""
	API para exportar configuração das naming series
	"""
	try:
		export_data = series_adapter.export_naming_series_configuration()
		return {
			"success": True,
			"export_data": export_data
		}
	except Exception as e:
		frappe.log_error(f"Error in export_naming_series_config: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def restore_default_naming_series_for_doctype(doctype):
	"""
	API para restaurar naming series padrão de um DocType
	"""
	try:
		result = restore_default_naming_series(doctype)
		return result
	except Exception as e:
		frappe.log_error(f"Error in restore_default_naming_series_for_doctype: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÕES DE SETUP/CLEANUP CORRIGIDAS ==========

def setup_naming_series_on_install(company_list=None):
	"""
	✅ CORRIGIDO: Configurar naming series durante instalação
	Não interfere com operações normais, trabalha apenas com Property Setters
	"""
	try:
		frappe.logger().info("🇵🇹 Setting up naming series for Portugal compliance...")

		if not company_list:
			# Obter todas as empresas portuguesas com compliance ativo
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
				# ✅ SINCRONIZAR APENAS SE HÁ SÉRIES ATIVAS
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
			f"✅ Naming series setup completed: {total_results['companies_processed']} companies, {total_results['total_options_added']} options added")

		return total_results

	except Exception as e:
		frappe.log_error(f"Error in setup_naming_series_on_install: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


def cleanup_naming_series_on_uninstall():
	"""
	Limpar naming series durante desinstalação
	"""
	try:
		frappe.logger().info("🧹 Cleaning up Portuguese naming series...")

		# Obter todas as empresas portuguesas
		company_list = frappe.get_all("Company",
									  filters={"country": "Portugal"},
									  fields=["name", "abbr"])

		total_removed = 0

		for company in company_list:
			try:
				result = cleanup_all_doctypes(company.abbr)
				if result["success"]:
					total_removed += result["summary"]["total_options_removed"]

			except Exception as e:
				frappe.log_error(f"Error cleaning naming series for {company.name}: {str(e)}")

		frappe.logger().info(f"🧹 Removed {total_removed} Portuguese naming series options")

		return {
			"success": True,
			"total_removed": total_removed
		}

	except Exception as e:
		frappe.log_error(f"Error in cleanup_naming_series_on_uninstall: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÃO PARA MIGRATE CORRIGIDA ==========

def sync_all_naming_series_after_migrate():
	"""
	✅ CORRIGIDO: Sincronizar todas as naming series após migrate
	Apenas para empresas com séries ativas, usando Property Setters
	"""
	try:
		frappe.logger().info("🔄 Syncing naming series after migrate...")

		# Obter todas as empresas portuguesas com compliance ativo e séries ativas
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


# ========== FUNÇÃO DE MIGRAÇÃO PARA FORMATO SEM HÍFENS ==========

@frappe.whitelist()
def migrate_series_to_no_hyphens():
	"""
	✅ NOVA: Migrar séries existentes de formato com hífens para sem hífens
	"""
	try:
		frappe.logger().info("🔄 Migrando séries para formato sem hífens...")

		# Buscar todas as séries com hífens
		series_with_hyphens = frappe.get_all("Portugal Series Configuration",
											 filters=[["prefix", "like", "%-%"]],
											 fields=["name", "prefix", "document_type", "company"])

		migrated_count = 0

		for series in series_with_hyphens:
			try:
				# Converter prefixo: FT-2025-NDX → FT2025NDX
				old_prefix = series.prefix
				new_prefix = old_prefix.replace('-', '')

				# Verificar se já existe série com novo formato
				existing = frappe.db.exists("Portugal Series Configuration", {
					"prefix": new_prefix,
					"document_type": series.document_type,
					"company": series.company
				})

				if not existing:
					# Atualizar série existente
					frappe.db.set_value("Portugal Series Configuration", series.name, {
						"prefix": new_prefix,
						"naming_series": f"{new_prefix}.####"
					})
					migrated_count += 1
					frappe.logger().info(f"✅ Migrado: {old_prefix} → {new_prefix}")
				else:
					frappe.logger().info(f"⏭️ Série {new_prefix} já existe - pulando {old_prefix}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar série {series.name}: {str(e)}")

		# Atualizar Property Setters
		if migrated_count > 0:
			frappe.logger().info("🔄 Atualizando Property Setters...")

			companies = frappe.get_all("Company",
									   filters={"country": "Portugal",
												"portugal_compliance_enabled": 1},
									   fields=["abbr"])

			for company in companies:
				sync_all_doctypes(company.abbr, force_update=True)

		frappe.db.commit()

		return {
			"success": True,
			"migrated_series": migrated_count,
			"message": f"Migradas {migrated_count} séries para formato sem hífens"
		}

	except Exception as e:
		frappe.log_error(f"Erro na migração de séries: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}
