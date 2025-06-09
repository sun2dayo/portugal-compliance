# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
ATCUD API - Portugal Compliance VERSÃO ALINHADA E CORRIGIDA
API para gestão de ATCUD em documentos portugueses
✅ ALINHADO: 100% compatível com document_hooks.py e at_webservice.py
✅ CORRIGIDO: Importações e validações corretas
✅ FORMATO: VALIDATION_CODE-SEQUENCE (formato real AT)
✅ DINÂMICO: Baseado no abbr da empresa
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint
import json
import re
from datetime import datetime

# ========== IMPORTAÇÕES CORRIGIDAS ==========

# ✅ IMPORTAÇÕES CORRETAS (baseadas nos arquivos reais)
from portugal_compliance.utils.document_hooks import generate_manual_atcud_certified


# ========== APIs DE GERAÇÃO DE ATCUD CORRIGIDAS ==========

@frappe.whitelist()
def generate_atcud_for_document(doctype, docname):
	"""
	✅ CORRIGIDO: Gera ATCUD para um documento específico
	Baseado na sua experiência com programação.python[2]
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

		# ✅ GERAR ATCUD USANDO FUNÇÃO CORRETA DO DOCUMENT_HOOKS
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
	✅ CORRIGIDO: Valida formato do ATCUD (formato real AT)
	Baseado na sua experiência com programação.autenticação[3]
	"""
	try:
		if not atcud_code:
			return {
				"valid": False,
				"message": _("ATCUD não fornecido")
			}

		# ✅ PADRÕES ATCUD REAIS (não 0.sequência)
		patterns = [
			r"^[A-Z0-9]{8,12}-\d{8}$",  # Formato AT: AAJFJMVNTN-00000001
			r"^AT\d{14}$"  # Formato fallback: AT20250608003854
		]

		is_valid = any(re.match(pattern, atcud_code.strip()) for pattern in patterns)

		return {
			"valid": is_valid,
			"atcud_code": atcud_code,
			"message": _("Formato ATCUD válido") if is_valid else _(
				"Formato ATCUD inválido. Use: VALIDATION_CODE-SEQUENCE (ex: AAJFJMVNTN-00000001)")
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
		if doc.atcud_code and not cint(force):
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
	Baseado na sua experiência com programação.revisão_de_arquivos[6]
	"""
	try:
		# ✅ VALIDAR DOCTYPE
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Stock Entry", "Journal Entry",
			"Quotation", "Sales Order", "Purchase Order", "Material Request"
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

		# ✅ VERIFICAR SE TABELA E CAMPO EXISTEM
		if not frappe.db.table_exists(f"tab{doctype}"):
			return {
				"success": False,
				"error": f"Tabela {doctype} não existe"
			}

		columns = frappe.db.get_table_columns(doctype)
		if 'atcud_code' not in columns:
			return {
				"success": False,
				"error": f"Campo atcud_code não existe em {doctype}"
			}

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
			"success_rate": round((successful / len(documents)) * 100, 2),
			"results": results
		}

	except Exception as e:
		frappe.log_error(f"Erro na geração em lote de ATCUD: {str(e)}", "Bulk Generate ATCUD API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE ESTATÍSTICAS CORRIGIDAS ==========

@frappe.whitelist()
def get_atcud_statistics(company=None, date_from=None, date_to=None):
	"""
	✅ CORRIGIDO: Obter estatísticas de ATCUD (otimizado)
	Baseado na sua experiência com programação.teste_no_console[8]
	"""
	try:
		# ✅ CONSTRUIR FILTROS
		base_filters = {}
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
			"documents_with_atcud": 0,
			"by_doctype": {},
			"by_company": {},
			"by_series": {},
			"date_range": {
				"from": date_from,
				"to": date_to
			}
		}

		# ✅ DOCTYPES SUPORTADOS (apenas com campo atcud_code)
		supported_doctypes = ["Sales Invoice", "Purchase Invoice", "POS Invoice", "Payment Entry"]

		for doctype in supported_doctypes:
			try:
				# ✅ VERIFICAR SE TABELA E CAMPO EXISTEM
				if not frappe.db.table_exists(f"tab{doctype}"):
					continue

				columns = frappe.db.get_table_columns(doctype)
				if 'atcud_code' not in columns:
					continue

				# ✅ CONTAR TOTAL
				total = frappe.db.count(doctype, base_filters)
				stats["total_documents"] += total

				# ✅ CONTAR COM ATCUD
				atcud_filters = dict(base_filters)
				atcud_filters['atcud_code'] = ['!=', '']
				with_atcud = frappe.db.count(doctype, atcud_filters)
				stats["documents_with_atcud"] += with_atcud

				stats["by_doctype"][doctype] = {
					"total": total,
					"with_atcud": with_atcud,
					"atcud_rate": round((with_atcud / total * 100), 2) if total > 0 else 0
				}

				# ✅ ESTATÍSTICAS DETALHADAS (amostra)
				if with_atcud > 0:
					sample_docs = frappe.get_all(
						doctype,
						filters=atcud_filters,
						fields=["company", "naming_series"],
						limit=100
					)

					for doc in sample_docs:
						# Por empresa
						if doc.company not in stats["by_company"]:
							stats["by_company"][doc.company] = 0
						stats["by_company"][doc.company] += 1

						# Por série
						if doc.naming_series not in stats["by_series"]:
							stats["by_series"][doc.naming_series] = 0
						stats["by_series"][doc.naming_series] += 1

			except Exception as e:
				stats["by_doctype"][doctype] = {"error": str(e)}

		# ✅ CALCULAR TAXA GERAL
		if stats["total_documents"] > 0:
			stats["atcud_rate"] = round(
				(stats["documents_with_atcud"] / stats["total_documents"]) * 100, 2)
		else:
			stats["atcud_rate"] = 0

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


# ========== APIs DE VALIDAÇÃO CORRIGIDAS ==========

@frappe.whitelist()
def validate_document_for_atcud(doctype, docname):
	"""
	✅ CORRIGIDO: Validar se documento pode ter ATCUD gerado
	Baseado na sua experiência com programação.refatoração_de_código[7]
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
		warnings = []

		# ✅ VERIFICAR SE É DOCTYPE SUPORTADO
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Stock Entry", "Journal Entry",
			"Quotation", "Sales Order", "Purchase Order", "Material Request"
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
				warnings.append("Formato de naming series não padrão")

		# ✅ VERIFICAR SE JÁ TEM ATCUD
		if doc.atcud_code:
			if validate_atcud_format(doc.atcud_code).get("valid"):
				warnings.append(f"Documento já possui ATCUD válido: {doc.atcud_code}")
			else:
				issues.append(f"Documento tem ATCUD inválido: {doc.atcud_code}")

		# ✅ VERIFICAR EMPRESA PORTUGUESA
		if hasattr(doc, 'company'):
			try:
				company_doc = frappe.get_cached_doc("Company", doc.company)
				if company_doc.country != "Portugal":
					issues.append("Empresa deve ser portuguesa")
				elif not getattr(company_doc, 'portugal_compliance_enabled', 0):
					issues.append("Portugal Compliance não está ativo na empresa")
			except:
				warnings.append("Não foi possível verificar empresa")

		return {
			"valid": len(issues) == 0,
			"issues": issues,
			"warnings": warnings,
			"document": docname,
			"doctype": doctype,
			"current_atcud": getattr(doc, 'atcud_code', None),
			"naming_series": getattr(doc, 'naming_series', None),
			"can_generate": len(issues) == 0 and not doc.atcud_code
		}

	except Exception as e:
		frappe.log_error(f"Erro ao validar documento: {str(e)}", "Validate Document API")
		return {
			"valid": False,
			"error": str(e)
		}


# ========== APIs DE SÉRIES CORRIGIDAS ==========

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
		if cint(mask):
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


@frappe.whitelist()
def get_series_next_atcud(series_name):
	"""
	✅ CORRIGIDO: Obter próximo ATCUD (formato real AT)
	"""
	try:
		# ✅ BUSCAR DADOS DA SÉRIE
		series_info = frappe.db.get_value(
			"Portugal Series Configuration",
			{"name": series_name, "is_active": 1},
			["current_sequence", "prefix", "naming_series", "validation_code"],
			as_dict=True
		)

		if not series_info:
			return {
				"success": False,
				"error": "Série não encontrada ou inativa"
			}

		# ✅ CALCULAR PRÓXIMO ATCUD (formato real)
		sequence = series_info.current_sequence or 1

		if series_info.validation_code:
			# ✅ FORMATO REAL AT: VALIDATION_CODE-SEQUENCE
			next_atcud = f"{series_info.validation_code}-{sequence:08d}"
		else:
			# ✅ FALLBACK: Série não comunicada
			next_atcud = f"PENDING-{sequence:08d}"

		return {
			"success": True,
			"series_name": series_name,
			"prefix": series_info.prefix,
			"naming_series": series_info.naming_series,
			"validation_code": series_info.validation_code,
			"next_sequence": sequence,
			"next_atcud": next_atcud,
			"is_communicated": bool(series_info.validation_code)
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter próximo ATCUD: {str(e)}", "Get Next ATCUD API")
		return {"success": False, "error": str(e)}


# ========== APIs DE RELATÓRIOS CORRIGIDAS ==========

@frappe.whitelist()
def get_atcud_report(company=None, doctype=None, date_from=None, date_to=None):
	"""
	✅ CORRIGIDO: Gerar relatório completo de ATCUD
	"""
	try:
		# ✅ OBTER ESTATÍSTICAS
		stats_result = get_atcud_statistics(company, date_from, date_to)
		if not stats_result.get("success"):
			return stats_result

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
			"summary": {
				"total_documents": stats_result.get("statistics", {}).get("total_documents", 0),
				"documents_with_atcud": stats_result.get("statistics", {}).get(
					"documents_with_atcud", 0),
				"atcud_rate": stats_result.get("statistics", {}).get("atcud_rate", 0)
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


# ========== LOG FINAL ==========
frappe.logger().info("ATCUD API ALINHADO loaded - Version 2.1.0 - Fully Corrected & Compatible")
