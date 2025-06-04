# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
ATCUD API - Portugal Compliance VERSÃO NATIVA CORRIGIDA
API para gestão de ATCUD em documentos portugueses
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
✅ APIs completas para geração e validação de ATCUD
✅ Suporte para todos os doctypes portugueses
✅ Logs e auditoria completa de ATCUD
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint
import json
import re
from datetime import datetime

# ✅ IMPORTAÇÕES CORRETAS (baseadas nos arquivos existentes)
from portugal_compliance.utils.atcud_generator import generate_manual_atcud_certified
#from portugal_compliance.utils.series_adapter import get_next_sequence, update_sequence
from portugal_compliance.utils.atcud_generator import generate_manual_atcud_certified

# ========== APIs DE GERAÇÃO DE ATCUD ==========

@frappe.whitelist()
def generate_atcud_for_document(doctype, docname):
	"""
	✅ CORRIGIDO: Gera ATCUD para um documento específico
	"""
	try:
		# ✅ VALIDAR PARÂMETROS
		if not doctype or not docname:
			return {
				"success": False,
				"error": "DocType e DocName são obrigatórios"
			}

		# ✅ VERIFICAR SE DOCUMENTO EXISTE
		if not frappe.db.exists(doctype, docname):
			return {
				"success": False,
				"error": f"Documento {doctype} {docname} não encontrado"
			}

		# ✅ GERAR ATCUD USANDO FUNÇÃO CORRETA
		result = generate_manual_atcud_certified(doctype, docname)

		if result.get("success"):
			return {
				"success": True,
				"atcud_code": result.get("atcud_code"),
				"message": _("ATCUD gerado com sucesso"),
				"document": docname,
				"doctype": doctype
			}
		else:
			return {
				"success": False,
				"error": result.get("error", "Erro desconhecido ao gerar ATCUD")
			}

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD para {doctype} {docname}: {str(e)}",
						 "Generate ATCUD API")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_atcud_format(atcud_code):
	"""
	✅ CORRIGIDO: Valida formato do ATCUD
	"""
	try:
		if not atcud_code:
			return {
				"valid": False,
				"message": _("ATCUD não fornecido")
			}

		# ✅ PADRÃO ATCUD: 0.sequência
		pattern = r"^0\.\d+$"
		is_valid = bool(re.match(pattern, atcud_code))

		return {
			"valid": is_valid,
			"atcud_code": atcud_code,
			"message": _("Formato ATCUD válido") if is_valid else _(
				"Formato ATCUD inválido. Use: 0.sequência")
		}

	except Exception as e:
		frappe.log_error(f"Erro ao validar ATCUD {atcud_code}: {str(e)}", "Validate ATCUD API")
		return {
			"valid": False,
			"error": str(e)
		}


@frappe.whitelist()
def regenerate_atcud(doctype, docname, force=False):
	"""
	✅ CORRIGIDO: Regenera ATCUD para um documento
	"""
	try:
		# ✅ VERIFICAR SE DOCUMENTO EXISTE
		if not frappe.db.exists(doctype, docname):
			return {
				"success": False,
				"error": f"Documento {doctype} {docname} não encontrado"
			}

		# ✅ OBTER DOCUMENTO
		doc = frappe.get_doc(doctype, docname)

		# ✅ VERIFICAR SE JÁ TEM ATCUD
		if doc.atcud_code and not force:
			return {
				"success": False,
				"error": "Documento já possui ATCUD. Use force=True para regenerar",
				"existing_atcud": doc.atcud_code
			}

		# ✅ LIMPAR ATCUD EXISTENTE
		old_atcud = doc.atcud_code
		doc.atcud_code = ""
		doc.save(ignore_permissions=True)

		# ✅ GERAR NOVO ATCUD
		result = generate_manual_atcud_certified(doctype, docname)

		if result.get("success"):
			return {
				"success": True,
				"old_atcud": old_atcud,
				"new_atcud": result.get("atcud_code"),
				"message": _("ATCUD regenerado com sucesso"),
				"document": docname
			}
		else:
			return {
				"success": False,
				"error": result.get("error", "Erro ao regenerar ATCUD")
			}

	except Exception as e:
		frappe.log_error(f"Erro ao regenerar ATCUD para {doctype} {docname}: {str(e)}",
						 "Regenerate ATCUD API")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def bulk_generate_atcud(doctype, filters=None, limit=50):
	"""
	✅ CORRIGIDO: Gera ATCUD em lote para documentos
	"""
	try:
		# ✅ VALIDAR DOCTYPE
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		]

		if doctype not in supported_doctypes:
			return {
				"success": False,
				"error": f"DocType {doctype} não suportado para ATCUD"
			}

		# ✅ PROCESSAR FILTROS
		if filters:
			if isinstance(filters, str):
				filters = json.loads(filters)
		else:
			filters = {}

		# ✅ ADICIONAR FILTRO PARA DOCUMENTOS SEM ATCUD
		filters.update({
			"atcud_code": ["in", ["", None]],
			"docstatus": 1  # Apenas documentos submetidos
		})

		# ✅ BUSCAR DOCUMENTOS
		documents = frappe.get_all(
			doctype,
			filters=filters,
			fields=["name", "naming_series"],
			limit=int(limit),
			order_by="creation desc"
		)

		if not documents:
			return {
				"success": True,
				"message": "Nenhum documento encontrado para processar",
				"total_processed": 0,
				"results": []
			}

		# ✅ PROCESSAR DOCUMENTOS
		results = []
		successful = 0
		failed = 0

		for doc_info in documents:
			try:
				result = generate_manual_atcud_certified(doctype, doc_info.name)

				if result.get("success"):
					results.append({
						"document": doc_info.name,
						"status": "success",
						"atcud_code": result.get("atcud_code"),
						"naming_series": doc_info.naming_series
					})
					successful += 1
				else:
					results.append({
						"document": doc_info.name,
						"status": "error",
						"error": result.get("error", "Erro desconhecido"),
						"naming_series": doc_info.naming_series
					})
					failed += 1

			except Exception as e:
				results.append({
					"document": doc_info.name,
					"status": "error",
					"error": str(e),
					"naming_series": doc_info.naming_series
				})
				failed += 1

		return {
			"success": True,
			"message": f"Processados {len(documents)} documentos",
			"total_processed": len(documents),
			"successful": successful,
			"failed": failed,
			"results": results
		}

	except Exception as e:
		frappe.log_error(f"Erro na geração em lote de ATCUD: {str(e)}", "Bulk Generate ATCUD API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE LOGS E AUDITORIA ==========

@frappe.whitelist()
def get_atcud_logs(filters=None, limit=100):
	"""
	✅ CORRIGIDO: Retorna logs de geração de ATCUD
	"""
	try:
		# ✅ PROCESSAR FILTROS
		if filters:
			if isinstance(filters, str):
				filters = json.loads(filters)
		else:
			filters = {}

		# ✅ BUSCAR LOGS (usando Error Log como base)
		logs = frappe.get_all(
			"Error Log",
			filters={
				"method": ["like", "%atcud%"],
				**filters
			},
			fields=["name", "creation", "method", "error"],
			order_by="creation desc",
			limit=int(limit)
		)

		# ✅ BUSCAR DOCUMENTOS COM ATCUD PARA ESTATÍSTICAS
		atcud_stats = get_atcud_statistics_internal()

		return {
			"success": True,
			"logs": logs,
			"statistics": atcud_stats,
			"total_logs": len(logs)
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter logs ATCUD: {str(e)}", "Get ATCUD Logs API")
		return {
			"success": False,
			"error": str(e)
		}


def get_atcud_statistics_internal():
	"""
	✅ NOVA: Obter estatísticas internas de ATCUD
	"""
	try:
		stats = {
			"total_documents_with_atcud": 0,
			"by_doctype": {},
			"recent_generations": []
		}

		# ✅ DOCTYPES SUPORTADOS
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		]

		for doctype in supported_doctypes:
			try:
				# ✅ CONTAR DOCUMENTOS COM ATCUD
				count = frappe.db.count(
					doctype,
					{"atcud_code": ["!=", ""]}
				)

				stats["by_doctype"][doctype] = count
				stats["total_documents_with_atcud"] += count

				# ✅ BUSCAR GERAÇÕES RECENTES
				recent = frappe.get_all(
					doctype,
					filters={"atcud_code": ["!=", ""]},
					fields=["name", "atcud_code", "creation"],
					order_by="creation desc",
					limit=5
				)

				for doc in recent:
					doc.doctype = doctype
					stats["recent_generations"].append(doc)

			except Exception:
				stats["by_doctype"][doctype] = 0

		# ✅ ORDENAR GERAÇÕES RECENTES
		stats["recent_generations"] = sorted(
			stats["recent_generations"],
			key=lambda x: x.creation,
			reverse=True
		)[:20]

		return stats

	except Exception as e:
		frappe.log_error(f"Erro ao obter estatísticas ATCUD: {str(e)}")
		return {}


@frappe.whitelist()
def get_atcud_statistics(company=None, date_from=None, date_to=None):
	"""
	✅ NOVA: API pública para estatísticas de ATCUD
	"""
	try:
		# ✅ CONSTRUIR FILTROS
		base_filters = {"atcud_code": ["!=", ""]}

		if company:
			base_filters["company"] = company

		if date_from:
			base_filters["creation"] = [">=", date_from]

		if date_to:
			if "creation" in base_filters:
				base_filters["creation"] = ["between", [date_from, date_to]]
			else:
				base_filters["creation"] = ["<=", date_to]

		# ✅ OBTER ESTATÍSTICAS
		stats = {
			"total_documents": 0,
			"by_doctype": {},
			"by_company": {},
			"by_series": {},
			"date_range": {
				"from": date_from,
				"to": date_to
			}
		}

		# ✅ DOCTYPES SUPORTADOS
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		]

		for doctype in supported_doctypes:
			try:
				# ✅ BUSCAR DOCUMENTOS
				docs = frappe.get_all(
					doctype,
					filters=base_filters,
					fields=["name", "atcud_code", "company", "naming_series", "creation"],
					limit=1000
				)

				stats["by_doctype"][doctype] = len(docs)
				stats["total_documents"] += len(docs)

				# ✅ ESTATÍSTICAS POR EMPRESA
				for doc in docs:
					if doc.company not in stats["by_company"]:
						stats["by_company"][doc.company] = 0
					stats["by_company"][doc.company] += 1

					# ✅ ESTATÍSTICAS POR SÉRIE
					if doc.naming_series not in stats["by_series"]:
						stats["by_series"][doc.naming_series] = 0
					stats["by_series"][doc.naming_series] += 1

			except Exception:
				stats["by_doctype"][doctype] = 0

		return {
			"success": True,
			"statistics": stats
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter estatísticas ATCUD: {str(e)}", "ATCUD Statistics API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE SÉRIES ==========

@frappe.whitelist()
def get_series_validation_code(series_name, mask=True):
	"""
	✅ CORRIGIDO: Retorna código de validação de uma série
	"""
	try:
		# ✅ VERIFICAR SE SÉRIE EXISTE
		if not frappe.db.exists("Portugal Series Configuration", series_name):
			return {
				"success": False,
				"error": f"Série {series_name} não encontrada"
			}

		# ✅ OBTER SÉRIE
		series = frappe.get_doc("Portugal Series Configuration", series_name)

		if not series.validation_code:
			return {
				"success": False,
				"error": "Código de validação não encontrado",
				"is_communicated": series.is_communicated
			}

		# ✅ MASCARAR CÓDIGO PARA SEGURANÇA
		if mask:
			masked_code = series.validation_code[:4] + "*" * (len(series.validation_code) - 4)
		else:
			# ✅ VERIFICAR PERMISSÕES PARA CÓDIGO COMPLETO
			if not frappe.has_permission("Portugal Series Configuration", "write"):
				return {
					"success": False,
					"error": "Permissão insuficiente para ver código completo"
				}
			masked_code = series.validation_code

		return {
			"success": True,
			"validation_code": masked_code,
			"is_communicated": series.is_communicated,
			"communication_date": series.communication_date,
			"series_name": series.series_name,
			"prefix": series.prefix
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter código de validação: {str(e)}", "Get Validation Code API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APENAS ESTA CORREÇÃO É NECESSÁRIA ==========

@frappe.whitelist()
def get_series_next_atcud(series_name):
	"""
	✅ FINAL: Obter próximo ATCUD (sem funções auxiliares)
	"""
	try:
		# ✅ BUSCAR DADOS DA SÉRIE EM UMA QUERY
		series_info = frappe.db.get_value(
			"Portugal Series Configuration",
			{"name": series_name, "is_active": 1},
			["current_sequence", "prefix", "naming_series"],
			as_dict=True
		)

		if not series_info:
			return {
				"success": False,
				"error": "Série não encontrada ou inativa"
			}

		# ✅ CALCULAR PRÓXIMO ATCUD
		sequence = series_info.current_sequence or 1
		next_atcud = f"0.{sequence}"

		return {
			"success": True,
			"series_name": series_name,
			"prefix": series_info.prefix,
			"naming_series": series_info.naming_series,
			"next_sequence": sequence,
			"next_atcud": next_atcud
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter próximo ATCUD: {str(e)}")
		return {"success": False, "error": str(e)}


# ========== APIs DE VALIDAÇÃO ==========

@frappe.whitelist()
def validate_document_for_atcud(doctype, docname):
	"""
	✅ NOVA: Validar se documento pode ter ATCUD gerado
	"""
	try:
		# ✅ VERIFICAR SE DOCUMENTO EXISTE
		if not frappe.db.exists(doctype, docname):
			return {
				"valid": False,
				"error": f"Documento {doctype} {docname} não encontrado"
			}

		# ✅ OBTER DOCUMENTO
		doc = frappe.get_doc(doctype, docname)

		# ✅ VALIDAÇÕES
		issues = []

		# ✅ VERIFICAR SE É DOCTYPE SUPORTADO
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		]

		if doctype not in supported_doctypes:
			issues.append(f"DocType {doctype} não suportado para ATCUD")

		# ✅ VERIFICAR SE DOCUMENTO ESTÁ SUBMETIDO
		if doc.docstatus != 1:
			issues.append("Documento deve estar submetido para gerar ATCUD")

		# ✅ VERIFICAR NAMING SERIES
		if not doc.naming_series:
			issues.append("Naming series não definida")
		else:
			# ✅ VERIFICAR FORMATO DA SÉRIE (SEM HÍFENS)
			pattern = r"^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$"
			if not re.match(pattern, doc.naming_series):
				issues.append("Formato de naming series inválido")

		# ✅ VERIFICAR SE JÁ TEM ATCUD
		if doc.atcud_code:
			issues.append(f"Documento já possui ATCUD: {doc.atcud_code}")

		# ✅ VERIFICAR EMPRESA PORTUGUESA
		if hasattr(doc, 'company'):
			company_doc = frappe.get_cached_doc("Company", doc.company)
			if company_doc.country != "Portugal":
				issues.append("Empresa deve ser portuguesa")

		return {
			"valid": len(issues) == 0,
			"issues": issues,
			"document": docname,
			"doctype": doctype,
			"current_atcud": getattr(doc, 'atcud_code', None),
			"naming_series": getattr(doc, 'naming_series', None)
		}

	except Exception as e:
		frappe.log_error(f"Erro ao validar documento: {str(e)}", "Validate Document API")
		return {
			"valid": False,
			"error": str(e)
		}


# ========== APIs DE RELATÓRIOS ==========

@frappe.whitelist()
def get_atcud_report(company=None, doctype=None, date_from=None, date_to=None):
	"""
	✅ NOVA: Gerar relatório completo de ATCUD
	"""
	try:
		# ✅ OBTER ESTATÍSTICAS
		stats_result = get_atcud_statistics(company, date_from, date_to)
		if not stats_result.get("success"):
			return stats_result

		# ✅ OBTER LOGS
		logs_result = get_atcud_logs({"creation": [">=", date_from]} if date_from else None)

		# ✅ COMPILAR RELATÓRIO
		report = {
			"generated_at": get_datetime(),
			"filters": {
				"company": company,
				"doctype": doctype,
				"date_from": date_from,
				"date_to": date_to
			},
			"statistics": stats_result.get("statistics", {}),
			"logs_summary": {
				"total_logs": logs_result.get("total_logs", 0),
				"recent_logs": logs_result.get("logs", [])[:10]
			}
		}

		return {
			"success": True,
			"report": report
		}

	except Exception as e:
		frappe.log_error(f"Erro ao gerar relatório ATCUD: {str(e)}", "ATCUD Report API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== CONSOLE LOG PARA DEBUG ==========
frappe.logger().info("ATCUD API loaded - Version 2.0.0 - Fully Corrected")
