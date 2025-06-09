# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series API - Portugal Compliance VERSÃO ALINHADA E CORRIGIDA
API para gestão de séries portuguesas
✅ ALINHADO: 100% compatível com document_hooks.py e at_webservice.py
✅ CORRIGIDO: Importações e métodos corretos
✅ FORMATO: SEM HÍFENS consistente (FT2025NDX)
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
from portugal_compliance.utils.at_webservice import ATWebserviceClient
from portugal_compliance.utils.document_hooks import portugal_document_hooks


# ========== APIs DE COMUNICAÇÃO COM AT CORRIGIDAS ==========

@frappe.whitelist()
def communicate_series_to_at(username=None, password=None, series_names=None, company=None):
	"""
	✅ CORRIGIDO: API para comunicar séries à AT (usando métodos reais)
	Baseado na sua experiência com programação.autenticação[2]
	"""
	try:
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

			series_to_communicate = []
			for name in series_names:
				try:
					series_doc = frappe.get_doc("Portugal Series Configuration", name)
					if not series_doc.is_communicated:
						series_to_communicate.append(series_doc.naming_series)
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
				fields=["naming_series", "company"]
			)

			series_to_communicate = [s.naming_series for s in series_list]

		if not series_to_communicate:
			return {
				"success": False,
				"error": "Nenhuma série ativa para comunicar"
			}

		# ✅ COMUNICAR À AT (usando método real do ATWebserviceClient)
		client = ATWebserviceClient()
		results = []
		successful = 0
		failed = 0

		for naming_series in series_to_communicate:
			try:
				# ✅ USAR MÉTODO REAL: register_naming_series
				result = client.register_naming_series(naming_series, company, username, password)

				if result.get("success"):
					successful += 1
				else:
					failed += 1

				results.append({
					"naming_series": naming_series,
					"result": result
				})

			except Exception as e:
				failed += 1
				results.append({
					"naming_series": naming_series,
					"result": {"success": False, "error": str(e)}
				})

		return {
			"success": True,
			"total_series": len(series_to_communicate),
			"successful": successful,
			"failed": failed,
			"results": results
		}

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
	✅ CORRIGIDO: Verificar status das séries (usando dados locais)
	"""
	try:
		# ✅ OBTER SÉRIES
		filters = {}
		if series_name:
			filters["name"] = series_name
		if company:
			filters["company"] = company

		series_list = frappe.get_all(
			"Portugal Series Configuration",
			filters=filters,
			fields=["name", "prefix", "validation_code", "communication_date",
					"is_communicated", "naming_series", "company"]
		)

		if not series_list:
			return {
				"success": False,
				"error": "Nenhuma série encontrada"
			}

		# ✅ VERIFICAR STATUS LOCAL (sem chamada AT desnecessária)
		results = []
		for series in series_list:
			status_info = {
				"series": series.name,
				"prefix": series.prefix,
				"naming_series": series.naming_series,
				"validation_code": series.validation_code,
				"is_communicated": series.is_communicated,
				"communication_date": series.communication_date,
				"status": "Comunicada" if series.is_communicated else "Não Comunicada",
				"valid": bool(series.validation_code),
				"last_check": get_datetime()
			}
			results.append(status_info)

		return {
			"success": True,
			"results": results,
			"checked_at": get_datetime()
		}

	except Exception as e:
		frappe.log_error(f"Erro ao verificar status: {str(e)}", "Series Status Check")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE GESTÃO DE SÉRIES CORRIGIDAS ==========

@frappe.whitelist()
def get_series_status(company=None, document_type=None):
	"""
	✅ CORRIGIDO: Retorna status das séries (formato SEM HÍFENS)
	Baseado na sua experiência com programação.consistência_de_dados[4]
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
			elif not s.validation_code:
				s.status = "Sem Validation Code"
				s.status_color = "red"
			else:
				s.status = "Ativa e Comunicada"
				s.status_color = "green"

			# ✅ PRÓXIMO NÚMERO
			s.next_number = s.current_sequence

			# ✅ FORMATO VALIDADO (SEM HÍFENS)
			s.format_valid = validate_series_format_internal(s.prefix)

		return {
			"success": True,
			"series": series,
			"total_count": len(series),
			"active_count": len([s for s in series if s.is_active]),
			"communicated_count": len([s for s in series if s.is_communicated]),
			"with_validation_code": len([s for s in series if s.validation_code])
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
	✅ CORRIGIDO: Criar séries usando document_hooks (evita duplicação)
	Baseado na sua experiência com programação.refatoração_de_código[7]
	"""
	try:
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

		# ✅ USAR DOCUMENT_HOOKS PARA CRIAR (evita duplicação)
		result = portugal_document_hooks._create_dynamic_portugal_series_certified(company_doc)

		if result.get("success"):
			return {
				"success": True,
				"created_count": result.get("created", 0),
				"created_series": result.get("created_series", []),
				"message": f"Criadas {result.get('created', 0)} séries para {company}"
			}
		else:
			return {
				"success": False,
				"error": result.get("error", "Erro na criação de séries")
			}

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries: {str(e)}", "Create Series API")
		return {
			"success": False,
			"error": str(e)
		}


# ========== APIs DE ATCUD CORRIGIDAS ==========

@frappe.whitelist()
def generate_atcud_for_document(doctype, docname):
	"""
	✅ CORRIGIDO: Gerar ATCUD usando document_hooks
	"""
	try:
		from portugal_compliance.utils.document_hooks import generate_manual_atcud_certified

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
	✅ CORRIGIDO: Validar formato de ATCUD (formato real AT)
	"""
	try:
		if not atcud_code:
			return {
				"success": False,
				"valid": False,
				"message": "ATCUD não fornecido"
			}

		# ✅ PADRÃO ATCUD REAL: VALIDATION_CODE-SEQUENCE
		patterns = [
			r"^[A-Z0-9]{8,12}-\d{8}$",  # Formato AT: AAJFJMVNTN-00000001
			r"^AT\d{14}$"  # Formato fallback: AT20250608003854
		]

		valid = any(re.match(pattern, atcud_code) for pattern in patterns)

		return {
			"success": True,
			"valid": valid,
			"message": "Formato válido" if valid else "Formato inválido. Use: VALIDATION_CODE-SEQUENCE",
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
	✅ CORRIGIDO: Obter estatísticas de ATCUD (otimizado)
	"""
	try:
		# ✅ CONSTRUIR FILTROS
		filters = {}
		if company:
			filters["company"] = company

		if date_from:
			filters["creation"] = [">=", date_from]

		if date_to:
			if "creation" in filters:
				filters["creation"] = ["between", [date_from, date_to]]
			else:
				filters["creation"] = ["<=", date_to]

		# ✅ DOCTYPES SUPORTADOS (apenas com campo atcud_code)
		supported_doctypes = ["Sales Invoice", "Purchase Invoice", "POS Invoice", "Payment Entry"]

		total_documents = 0
		documents_with_atcud = 0
		by_doctype = {}

		for doctype in supported_doctypes:
			try:
				# ✅ VERIFICAR SE TABELA E CAMPO EXISTEM
				if not frappe.db.table_exists(f"tab{doctype}"):
					continue

				columns = frappe.db.get_table_columns(doctype)
				if 'atcud_code' not in columns:
					continue

				# ✅ CONTAR TOTAL
				total = frappe.db.count(doctype, filters)
				total_documents += total

				# ✅ CONTAR COM ATCUD
				atcud_filters = dict(filters)
				atcud_filters['atcud_code'] = ['!=', '']
				with_atcud = frappe.db.count(doctype, atcud_filters)
				documents_with_atcud += with_atcud

				by_doctype[doctype] = {
					"total": total,
					"with_atcud": with_atcud,
					"atcud_rate": round((with_atcud / total * 100), 2) if total > 0 else 0
				}

			except Exception as e:
				by_doctype[doctype] = {"error": str(e)}

		return {
			"success": True,
			"statistics": {
				"total_documents": total_documents,
				"documents_with_atcud": documents_with_atcud,
				"atcud_rate": round((documents_with_atcud / total_documents * 100),
									2) if total_documents > 0 else 0,
				"by_doctype": by_doctype,
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


# ========== APIs DE RELATÓRIOS OTIMIZADAS ==========

@frappe.whitelist()
def get_series_report(company=None, include_stats=True):
	"""
	✅ CORRIGIDO: Gerar relatório completo de séries (otimizado)
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
					# ✅ VERIFICAR SE TABELA EXISTE
					if not frappe.db.table_exists(f"tab{series.document_type}"):
						series.documents_count = 0
						series.submitted_count = 0
						series.draft_count = 0
						continue

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
				"with_validation_code": len([s for s in series_data if s.validation_code]),
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


# ========== APIs DE UTILITÁRIOS CORRIGIDAS ==========

@frappe.whitelist()
def get_available_document_types():
	"""
	✅ CORRIGIDO: Obter tipos de documento (usando dados reais)
	"""
	try:
		# ✅ TIPOS DE DOCUMENTO BASEADOS NO DOCUMENT_HOOKS
		document_types = [
			{
				"doctype": "Sales Invoice",
				"code": "FT",
				"name": "Fatura de Venda",
				"description": "Documentos de venda a clientes",
				"communication_required": True,
				"atcud_required": True
			},
			{
				"doctype": "Purchase Invoice",
				"code": "FC",
				"name": "Fatura de Compra",
				"description": "Documentos de compra a fornecedores",
				"communication_required": True,
				"atcud_required": True
			},
			{
				"doctype": "POS Invoice",
				"code": "FS",
				"name": "Fatura Simplificada",
				"description": "Faturas POS simplificadas",
				"communication_required": True,
				"atcud_required": True
			},
			{
				"doctype": "Payment Entry",
				"code": "RC",
				"name": "Recibo",
				"description": "Recibos de pagamento",
				"communication_required": True,
				"atcud_required": True
			}
		]

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
	✅ MANTIDO: Obter empresas portuguesas com compliance ativo
	"""
	try:
		companies = frappe.get_all(
			"Company",
			filters={
				"country": "Portugal",
				"portugal_compliance_enabled": 1
			},
			fields=["name", "company_name", "tax_id", "default_currency", "abbr"],
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
	✅ CORRIGIDO: Testar geração de série (usando dados reais)
	"""
	try:
		# ✅ VERIFICAR SE SÉRIE EXISTE
		if not frappe.db.exists("Portugal Series Configuration", series_name):
			return {
				"success": False,
				"error": "Série não encontrada"
			}

		# ✅ OBTER DADOS DA SÉRIE
		series_doc = frappe.get_doc("Portugal Series Configuration", series_name)

		# ✅ SIMULAR GERAÇÃO
		test_result = {
			"success": True,
			"series_name": series_name,
			"prefix": series_doc.prefix,
			"naming_series": series_doc.naming_series,
			"current_sequence": series_doc.current_sequence,
			"next_document": f"{series_doc.prefix}.{series_doc.current_sequence:04d}",
			"is_communicated": series_doc.is_communicated,
			"validation_code": series_doc.validation_code,
			"test_atcud": f"{series_doc.validation_code}-{series_doc.current_sequence:08d}" if series_doc.validation_code else None
		}

		return test_result

	except Exception as e:
		frappe.log_error(f"Erro ao testar série: {str(e)}", "Test Series Generation")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def communicate_series_batch(username=None, password=None, company=None, environment="test"):
	"""
	✅ NOVA FUNÇÃO: Comunicar múltiplas séries em lote (eficiente)
	Baseado na sua experiência com programação.conformidade_portugal[2]
	"""
	try:
		# ✅ VALIDAR CREDENCIAIS
		if not username or not password:
			return {
				"success": False,
				"error": "Username e password são obrigatórios"
			}

		# ✅ BUSCAR TODAS AS SÉRIES NÃO COMUNICADAS
		filters = {
			"is_communicated": 0,
			"is_active": 1
		}
		if company:
			filters["company"] = company

		series_to_communicate = frappe.get_all(
			"Portugal Series Configuration",
			filters=filters,
			fields=["name", "naming_series", "company", "document_type", "prefix"],
			order_by="company, document_type"
		)

		if not series_to_communicate:
			return {
				"success": False,
				"error": "Nenhuma série ativa para comunicar"
			}

		# ✅ AGRUPAR POR EMPRESA PARA EFICIÊNCIA
		series_by_company = {}
		for serie in series_to_communicate:
			comp = serie.company
			if comp not in series_by_company:
				series_by_company[comp] = []
			series_by_company[comp].append(serie)

		# ✅ COMUNICAR EM LOTE POR EMPRESA
		from portugal_compliance.utils.at_webservice import batch_register_naming_series

		batch_results = []
		total_successful = 0
		total_failed = 0

		for comp, company_series in series_by_company.items():
			try:
				# ✅ PREPARAR LISTA DE NAMING SERIES
				naming_series_list = [s.naming_series for s in company_series]

				frappe.logger().info(f"🚀 Comunicando {len(naming_series_list)} séries para {comp}")

				# ✅ COMUNICAÇÃO EM LOTE (mais eficiente)
				batch_result = batch_register_naming_series(
					naming_series_list, comp, username, password, environment
				)

				if batch_result.get("success"):
					successful_count = batch_result.get("successful", 0)
					failed_count = batch_result.get("failed", 0)

					total_successful += successful_count
					total_failed += failed_count

					batch_results.append({
						"company": comp,
						"series_count": len(naming_series_list),
						"successful": successful_count,
						"failed": failed_count,
						"results": batch_result.get("results", [])
					})
				else:
					total_failed += len(naming_series_list)
					batch_results.append({
						"company": comp,
						"series_count": len(naming_series_list),
						"successful": 0,
						"failed": len(naming_series_list),
						"error": batch_result.get("error", "Erro desconhecido")
					})

			except Exception as e:
				total_failed += len(company_series)
				batch_results.append({
					"company": comp,
					"series_count": len(company_series),
					"successful": 0,
					"failed": len(company_series),
					"error": str(e)
				})

		return {
			"success": True,
			"batch_communication": True,
			"total_series": len(series_to_communicate),
			"total_successful": total_successful,
			"total_failed": total_failed,
			"success_rate": round((total_successful / len(series_to_communicate)) * 100, 2),
			"companies_processed": len(series_by_company),
			"results_by_company": batch_results,
			"environment": environment
		}

	except Exception as e:
		frappe.log_error(f"Erro na comunicação em lote: {str(e)}", "Batch Series Communication")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def communicate_all_company_series(company, username=None, password=None, environment="test"):
	"""
	✅ NOVA FUNÇÃO: Comunicar todas as séries de uma empresa específica
	Ideal para quando se ativa Portugal Compliance
	"""
	try:
		# ✅ VERIFICAR SE EMPRESA TEM COMPLIANCE ATIVO
		company_doc = frappe.get_doc("Company", company)
		if not getattr(company_doc, 'portugal_compliance_enabled', 0):
			return {
				"success": False,
				"error": f"Portugal Compliance não está ativo para {company}"
			}

		# ✅ BUSCAR SÉRIES DA EMPRESA
		company_series = frappe.get_all(
			"Portugal Series Configuration",
			filters={
				"company": company,
				"is_active": 1,
				"is_communicated": 0
			},
			fields=["name", "naming_series", "document_type", "prefix"]
		)

		if not company_series:
			return {
				"success": True,
				"message": f"Todas as séries de {company} já estão comunicadas",
				"series_count": 0
			}

		# ✅ COMUNICAR EM LOTE
		from portugal_compliance.utils.at_webservice import batch_register_naming_series

		naming_series_list = [s.naming_series for s in company_series]

		result = batch_register_naming_series(
			naming_series_list, company, username, password, environment
		)

		if result.get("success"):
			return {
				"success": True,
				"company": company,
				"series_communicated": result.get("successful", 0),
				"series_failed": result.get("failed", 0),
				"total_series": len(naming_series_list),
				"success_rate": round(
					(result.get("successful", 0) / len(naming_series_list)) * 100, 2),
				"results": result.get("results", []),
				"message": f"Comunicação em lote concluída para {company}"
			}
		else:
			return {
				"success": False,
				"error": result.get("error", "Erro na comunicação em lote"),
				"company": company
			}

	except Exception as e:
		frappe.log_error(f"Erro ao comunicar séries da empresa: {str(e)}",
						 "Company Series Communication")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def auto_communicate_after_compliance_activation(company, username=None, password=None):
	"""
	✅ NOVA FUNÇÃO: Auto-comunicar após ativação de compliance
	Chamada automaticamente quando Portugal Compliance é ativado
	"""
	try:
		frappe.logger().info(f"🚀 Auto-comunicação iniciada para {company}")

		# ✅ AGUARDAR UM POUCO PARA GARANTIR QUE SÉRIES FORAM CRIADAS
		import time
		time.sleep(2)

		# ✅ COMUNICAR TODAS AS SÉRIES DA EMPRESA
		result = communicate_all_company_series(company, username, password)

		if result.get("success"):
			# ✅ LOG DE SUCESSO
			frappe.logger().info(
				f"✅ Auto-comunicação concluída para {company}: {result.get('series_communicated', 0)} séries")

			# ✅ NOTIFICAR USUÁRIO
			frappe.publish_realtime(
				"compliance_communication_complete",
				{
					"company": company,
					"series_communicated": result.get("series_communicated", 0),
					"message": "Séries comunicadas automaticamente à AT"
				},
				user=frappe.session.user
			)

		return result

	except Exception as e:
		frappe.log_error(f"Erro na auto-comunicação: {str(e)}", "Auto Communication")
		return {
			"success": False,
			"error": str(e)
		}


# ========== LOG FINAL ==========
frappe.logger().info("Series API ALINHADO loaded - Version 2.1.0 - Compatible & Corrected")
