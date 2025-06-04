# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series API - Portugal Compliance VERSÃO NATIVA CORRIGIDA
API para gestão de séries portuguesas
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
✅ APIs completas para comunicação com AT
✅ Validação de séries portuguesas
✅ Gestão completa de séries e ATCUD
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint
import json
import re
from datetime import datetime

# ========== CORREÇÃO DAS IMPORTAÇÕES ==========

# ❌ INCORRETO (não existe):
# from portugal_compliance.utils.at_communication import ATCommunicationClient

# ✅ CORRETO (baseado no código original):
from portugal_compliance.utils.at_webservice import ATWebserviceClient


# ========== APIs DE COMUNICAÇÃO COM AT CORRIGIDAS ==========

@frappe.whitelist()
def communicate_series_to_at(username=None, password=None, series_names=None, company=None):
	"""
	✅ CORRIGIDO: API para comunicar séries à AT (usando ATWebserviceClient correto)
	"""
	try:
		# ✅ IMPORTAÇÃO CORRETA
		from portugal_compliance.utils.at_webservice import ATWebserviceClient

		# ✅ VALIDAR PARÂMETROS
		if not username or not password:
			return {
				"success": False,
				"error": "Username e password são obrigatórios para comunicação com AT"
			}

		# ✅ OBTER SÉRIES PARA COMUNICAR
		if series_names:
			if isinstance(series_names, str):
				series_names = json.loads(series_names)

			series_list = []
			for name in series_names:
				try:
					series_doc = frappe.get_doc("Portugal Series Configuration", name)
					series_list.append(series_doc)
				except frappe.DoesNotExistError:
					continue
		else:
			# ✅ BUSCAR SÉRIES NÃO COMUNICADAS
			filters = {"is_communicated": 0, "is_active": 1}
			if company:
				filters["company"] = company

			series_list = frappe.get_all(
				"Portugal Series Configuration",
				filters=filters,
				as_list=False  # ✅ COMO NO CÓDIGO ORIGINAL
			)

		if not series_list:
			return {
				"success": False,
				"error": "Nenhuma série ativa para comunicar"
			}

		# ✅ COMUNICAR À AT (usando método original)
		client = ATWebserviceClient()
		result = client.communicate_series_batch(series_list, username, password)

		return result

	except Exception as e:
		frappe.log_error(f"Erro na API de comunicação de séries: {str(e)}",
						 "Series Communication API")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_series_at_status(series_name=None, company=None):
	"""
	✅ CORRIGIDO: Verificar status das séries na AT (usando ATWebserviceClient)
	"""
	try:
		# ✅ IMPORTAÇÃO CORRETA
		from portugal_compliance.utils.at_webservice import ATWebserviceClient

		# ✅ OBTER SÉRIES
		filters = {"is_communicated": 1}
		if series_name:
			filters["name"] = series_name
		if company:
			filters["company"] = company

		series_list = frappe.get_all(
			"Portugal Series Configuration",
			filters=filters,
			fields=["name", "prefix", "validation_code", "communication_date"]
		)

		if not series_list:
			return {
				"success": False,
				"error": "Nenhuma série comunicada encontrada"
			}

		# ✅ VERIFICAR STATUS NA AT
		client = ATWebserviceClient()
		results = []

		for series in series_list:
			try:
				# ✅ USAR MÉTODO DISPONÍVEL NO ATWebserviceClient
				status = client.check_series_status(series.validation_code)
				results.append({
					"series": series.name,
					"prefix": series.prefix,
					"validation_code": series.validation_code,
					"status": status.get("status"),
					"valid": status.get("valid", False),
					"last_check": get_datetime()
				})
			except Exception as e:
				results.append({
					"series": series.name,
					"prefix": series.prefix,
					"error": str(e)
				})

		return {
			"success": True,
			"results": results,
			"checked_at": get_datetime()
		}

	except Exception as e:
		frappe.log_error(f"Erro ao verificar status AT: {str(e)}", "AT Status Check")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE GESTÃO DE SÉRIES ==========

@frappe.whitelist()
def get_series_status(company=None, document_type=None):
	"""
	✅ CORRIGIDO: Retorna status das séries configuradas (formato SEM HÍFENS)
	"""
	try:
		# ✅ CONSTRUIR FILTROS
		filters = {}
		if company:
			filters["company"] = company
		if document_type:
			filters["document_type"] = document_type

		# ✅ BUSCAR SÉRIES
		series = frappe.get_all(
			"Portugal Series Configuration",
			filters=filters,
			fields=[
				"name", "series_name", "company", "document_type",
				"prefix", "naming_series", "is_active", "is_communicated",
				"current_sequence", "total_documents_issued",
				"communication_date", "validation_code", "last_document_date"
			],
			order_by="company, document_type, prefix"
		)

		# ✅ ENRIQUECER COM INFORMAÇÕES ADICIONAIS
		for s in series:
			# ✅ STATUS GERAL
			if not s.is_active:
				s.status = "Inativa"
				s.status_color = "gray"
			elif not s.is_communicated:
				s.status = "Não Comunicada"
				s.status_color = "orange"
			else:
				s.status = "Ativa"
				s.status_color = "green"

			# ✅ PRÓXIMO NÚMERO
			s.next_number = f"{s.prefix}{s.current_sequence:04d}"

			# ✅ FORMATO VALIDADO (SEM HÍFENS)
			s.format_valid = validate_series_format_internal(s.prefix)

		return {
			"success": True,
			"series": series,
			"total_count": len(series),
			"active_count": len([s for s in series if s.is_active]),
			"communicated_count": len([s for s in series if s.is_communicated])
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter status das séries: {str(e)}", "Get Series Status")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_series_format(series_prefix):
	"""
	✅ CORRIGIDO: Valida formato da série (SEM HÍFENS)
	"""
	try:
		result = validate_series_format_internal(series_prefix)
		return {
			"success": True,
			"valid": result["valid"],
			"message": result["message"],
			"prefix": series_prefix
		}
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


def validate_series_format_internal(series_prefix):
	"""
	✅ CORRIGIDO: Validação interna do formato (SEM HÍFENS)
	"""
	if not series_prefix:
		return {"valid": False, "message": "Prefixo não fornecido"}

	# ✅ PADRÃO SEM HÍFENS: XXYYYY + EMPRESA (ex: FT2025NDX)
	pattern = r"^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$"

	if not re.match(pattern, series_prefix):
		return {
			"valid": False,
			"message": "Formato inválido. Use: XXYYYY + EMPRESA (ex: FT2025NDX)"
		}

	# ✅ VALIDAÇÕES ADICIONAIS
	if len(series_prefix) < 8:
		return {
			"valid": False,
			"message": "Prefixo muito curto (mínimo 8 caracteres)"
		}

	if len(series_prefix) > 12:
		return {
			"valid": False,
			"message": "Prefixo muito longo (máximo 12 caracteres)"
		}

	return {
		"valid": True,
		"message": "Formato válido"
	}


@frappe.whitelist()
def create_series_for_company(company, document_types=None):
	"""
	✅ NOVA: Criar séries automaticamente para empresa
	"""
	try:
		from portugal_compliance.regional.portugal import setup_all_series_for_company

		# ✅ VALIDAR EMPRESA
		if not company:
			return {
				"success": False,
				"error": "Empresa é obrigatória"
			}

		# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
		company_doc = frappe.get_doc("Company", company)
		if company_doc.country != "Portugal":
			return {
				"success": False,
				"error": "Apenas empresas portuguesas podem ter séries de compliance"
			}

		# ✅ CRIAR SÉRIES
		if document_types:
			if isinstance(document_types, str):
				document_types = json.loads(document_types)

			# ✅ CRIAR SÉRIES ESPECÍFICAS
			result = create_specific_series(company, document_types)
		else:
			# ✅ CRIAR TODAS AS SÉRIES
			result = setup_all_series_for_company(company)

		return result

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries: {str(e)}", "Create Series API")
		return {
			"success": False,
			"error": str(e)
		}


def create_specific_series(company, document_types):
	"""
	✅ NOVA: Criar séries específicas para tipos de documento
	"""
	from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

	created_series = []
	current_year = datetime.now().year
	company_code = company[:3].upper()

	for doctype in document_types:
		if doctype not in PORTUGAL_DOCUMENT_TYPES:
			continue

		doc_info = PORTUGAL_DOCUMENT_TYPES[doctype]

		try:
			# ✅ GERAR PREFIXO SEM HÍFENS
			prefix = f"{doc_info['code']}{current_year}{company_code}"
			naming_series = f"{prefix}.####"

			# ✅ VERIFICAR SE JÁ EXISTE
			if frappe.db.exists("Portugal Series Configuration",
								{"prefix": prefix, "company": company}):
				continue

			# ✅ CRIAR SÉRIE
			series_doc = frappe.new_doc("Portugal Series Configuration")
			series_doc.update({
				"series_name": f"{doc_info['name']} - {prefix}",
				"company": company,
				"document_type": doctype,
				"prefix": prefix,
				"naming_series": naming_series,
				"current_sequence": 1,
				"is_active": 1,
				"is_communicated": 0
			})

			series_doc.insert(ignore_permissions=True)
			created_series.append({
				"name": series_doc.name,
				"document_type": doctype,
				"prefix": prefix,
				"naming_series": naming_series
			})

		except Exception as e:
			frappe.log_error(f"Erro ao criar série {doctype}: {str(e)}")

	return {
		"success": True,
		"created_count": len(created_series),
		"created_series": created_series
	}


# ========== APIs DE ATCUD ==========

@frappe.whitelist()
def generate_atcud_for_document(doctype, docname):
	"""
	✅ NOVA: Gerar ATCUD para documento específico
	"""
	try:
		from portugal_compliance.utils.atcud_generator import generate_manual_atcud_certified

		result = generate_manual_atcud_certified(doctype, docname)
		return result

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD: {str(e)}", "Generate ATCUD API")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_atcud_format(atcud_code):
	"""
	✅ NOVA: Validar formato de ATCUD
	"""
	try:
		if not atcud_code:
			return {
				"success": False,
				"valid": False,
				"message": "ATCUD não fornecido"
			}

		# ✅ PADRÃO ATCUD: 0.sequência
		pattern = r"^0\.\d+$"
		valid = bool(re.match(pattern, atcud_code))

		return {
			"success": True,
			"valid": valid,
			"message": "Formato válido" if valid else "Formato inválido. Use: 0.sequência",
			"atcud": atcud_code
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_atcud_statistics(company=None, date_from=None, date_to=None):
	"""
	✅ NOVA: Obter estatísticas de ATCUD
	"""
	try:
		# ✅ CONSTRUIR FILTROS
		filters = {"atcud_code": ["!=", ""]}

		if company:
			filters["company"] = company

		if date_from:
			filters["creation"] = [">=", date_from]

		if date_to:
			if "creation" in filters:
				filters["creation"] = ["between", [date_from, date_to]]
			else:
				filters["creation"] = ["<=", date_to]

		# ✅ BUSCAR DOCUMENTOS COM ATCUD
		documents_with_atcud = []

		# ✅ DOCTYPES SUPORTADOS
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		]

		for doctype in supported_doctypes:
			try:
				docs = frappe.get_all(
					doctype,
					filters=filters,
					fields=["name", "atcud_code", "creation", "docstatus", "naming_series"],
					limit=1000
				)

				for doc in docs:
					doc.doctype = doctype
					documents_with_atcud.append(doc)

			except Exception:
				continue

		# ✅ COMPILAR ESTATÍSTICAS
		total_documents = len(documents_with_atcud)
		submitted_documents = len([d for d in documents_with_atcud if d.docstatus == 1])

		# ✅ ESTATÍSTICAS POR DOCTYPE
		by_doctype = {}
		for doc in documents_with_atcud:
			if doc.doctype not in by_doctype:
				by_doctype[doc.doctype] = {"count": 0, "submitted": 0}
			by_doctype[doc.doctype]["count"] += 1
			if doc.docstatus == 1:
				by_doctype[doc.doctype]["submitted"] += 1

		# ✅ ESTATÍSTICAS POR SÉRIE
		by_series = {}
		for doc in documents_with_atcud:
			series = doc.naming_series
			if series not in by_series:
				by_series[series] = {"count": 0, "submitted": 0}
			by_series[series]["count"] += 1
			if doc.docstatus == 1:
				by_series[series]["submitted"] += 1

		return {
			"success": True,
			"statistics": {
				"total_documents": total_documents,
				"submitted_documents": submitted_documents,
				"draft_documents": total_documents - submitted_documents,
				"by_doctype": by_doctype,
				"by_series": by_series,
				"date_range": {
					"from": date_from,
					"to": date_to
				}
			}
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter estatísticas ATCUD: {str(e)}", "ATCUD Statistics")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE RELATÓRIOS ==========

@frappe.whitelist()
def get_series_report(company=None, include_stats=True):
	"""
	✅ NOVA: Gerar relatório completo de séries
	"""
	try:
		# ✅ OBTER SÉRIES
		series_result = get_series_status(company)
		if not series_result.get("success"):
			return series_result

		series_data = series_result["series"]

		# ✅ INCLUIR ESTATÍSTICAS SE SOLICITADO
		if include_stats:
			for series in series_data:
				try:
					# ✅ BUSCAR DOCUMENTOS DA SÉRIE
					docs_count = frappe.db.count(
						series.document_type,
						{"naming_series": series.naming_series}
					)

					submitted_count = frappe.db.count(
						series.document_type,
						{"naming_series": series.naming_series, "docstatus": 1}
					)

					series.documents_count = docs_count
					series.submitted_count = submitted_count
					series.draft_count = docs_count - submitted_count

				except Exception:
					series.documents_count = 0
					series.submitted_count = 0
					series.draft_count = 0

		# ✅ COMPILAR RELATÓRIO
		report = {
			"company": company,
			"generated_at": get_datetime(),
			"series_data": series_data,
			"summary": {
				"total_series": len(series_data),
				"active_series": len([s for s in series_data if s.is_active]),
				"communicated_series": len([s for s in series_data if s.is_communicated]),
				"total_documents": sum(getattr(s, 'documents_count', 0) for s in series_data),
				"submitted_documents": sum(getattr(s, 'submitted_count', 0) for s in series_data)
			}
		}

		return {
			"success": True,
			"report": report
		}

	except Exception as e:
		frappe.log_error(f"Erro ao gerar relatório: {str(e)}", "Series Report")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def export_series_data(company=None, format="json"):
	"""
	✅ NOVA: Exportar dados das séries
	"""
	try:
		# ✅ OBTER RELATÓRIO COMPLETO
		report_result = get_series_report(company, include_stats=True)
		if not report_result.get("success"):
			return report_result

		report_data = report_result["report"]

		# ✅ FORMATAR DADOS PARA EXPORTAÇÃO
		if format.lower() == "csv":
			# ✅ CONVERTER PARA CSV
			import csv
			import io

			output = io.StringIO()
			writer = csv.writer(output)

			# ✅ CABEÇALHO
			writer.writerow([
				"Nome da Série", "Empresa", "Tipo de Documento", "Prefixo",
				"Naming Series", "Ativa", "Comunicada", "Sequência Atual",
				"Total Documentos", "Documentos Submetidos"
			])

			# ✅ DADOS
			for series in report_data["series_data"]:
				writer.writerow([
					series.series_name, series.company, series.document_type,
					series.prefix, series.naming_series, series.is_active,
					series.is_communicated, series.current_sequence,
					getattr(series, 'documents_count', 0),
					getattr(series, 'submitted_count', 0)
				])

			csv_data = output.getvalue()
			output.close()

			return {
				"success": True,
				"format": "csv",
				"data": csv_data,
				"filename": f"series_export_{company or 'all'}_{nowdate()}.csv"
			}

		else:
			# ✅ RETORNAR JSON
			return {
				"success": True,
				"format": "json",
				"data": report_data,
				"filename": f"series_export_{company or 'all'}_{nowdate()}.json"
			}

	except Exception as e:
		frappe.log_error(f"Erro ao exportar dados: {str(e)}", "Export Series Data")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE UTILITÁRIOS ==========

@frappe.whitelist()
def get_available_document_types():
	"""
	✅ NOVA: Obter tipos de documento disponíveis
	"""
	try:
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		document_types = []
		for doctype, info in PORTUGAL_DOCUMENT_TYPES.items():
			document_types.append({
				"doctype": doctype,
				"code": info["code"],
				"name": info["name"],
				"description": info["description"],
				"communication_required": info.get("communication_required", False),
				"atcud_required": info.get("atcud_required", False)
			})

		return {
			"success": True,
			"document_types": document_types
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_portugal_companies():
	"""
	✅ NOVA: Obter empresas portuguesas com compliance ativo
	"""
	try:
		companies = frappe.get_all(
			"Company",
			filters={
				"country": "Portugal",
				"portugal_compliance_enabled": 1
			},
			fields=["name", "company_name", "tax_id", "default_currency"],
			order_by="company_name"
		)

		return {
			"success": True,
			"companies": companies
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def test_series_generation(series_name):
	"""
	✅ NOVA: Testar geração de série
	"""
	try:
		from portugal_compliance.utils.series_adapter import test_series_generation as test_gen

		result = test_gen(series_name)
		return result

	except Exception as e:
		frappe.log_error(f"Erro ao testar série: {str(e)}", "Test Series Generation")
		return {
			"success": False,
			"error": str(e)
		}


# ========== CONSOLE LOG PARA DEBUG ==========
frappe.logger().info("Series API loaded - Version 2.0.0 - Format WITHOUT HYPHENS")
