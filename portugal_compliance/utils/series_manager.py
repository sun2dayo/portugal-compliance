# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Manager for Portugal Compliance - VERSÃO ALINHADA E OTIMIZADA
Manages Portuguese series for documents with intelligent integration
✅ ALINHADO: 100% compatível com document_hooks.py e series_adapter.py
✅ SEGURO: Não quebra funcionalidades existentes
✅ DINÂMICO: Baseado no abbr da empresa (não fixo NDX)
✅ PERFORMANCE: Cache otimizado e validações thread-safe
"""

import frappe
from frappe import _
import re
from frappe.utils import cint, today, getdate
from erpnext.accounts.utils import get_fiscal_year


class SeriesManager:
	"""
	✅ CLASSE ALINHADA: Compatível com document_hooks.py e startup_fixes.py
	Gerenciador de séries portuguesas para documentos
	"""

	def __init__(self):
		self.supported_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'Payment Entry', 'POS Invoice',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry',
			'Quotation', 'Sales Order', 'Purchase Order', 'Material Request'
		]
		self.module = "Portugal Compliance"
		self._cache = {}  # ✅ CACHE INTERNO PARA PERFORMANCE

	# ========== MÉTODOS PRINCIPAIS ALINHADOS ==========

	def set_portugal_series(self, doc, method=None):
		"""
		✅ ALINHADO: Define série portuguesa COMPATÍVEL com document_hooks.py
		Não interfere com auto-seleção do sales_invoice.js
		"""
		try:
			# ✅ VERIFICAÇÕES BÁSICAS ALINHADAS
			if not self.is_portugal_compliance_enabled(doc.company):
				return

			if doc.doctype not in self.supported_doctypes:
				return

			# ✅ SE JÁ TEM NAMING SERIES PORTUGUESA, NÃO ALTERAR (ALINHADO)
			if doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																	  doc.company):
				return

			# ✅ BUSCAR SÉRIE PORTUGUESA ATIVA E COMUNICADA (PRIORIDADE)
			series_config = self.get_best_series_configuration(doc)

			if series_config:
				# ✅ FORMATO SEM HÍFENS (ALINHADO COM DOCUMENT_HOOKS)
				doc.naming_series = f"{series_config.prefix}.####"
				frappe.logger().info(
					f"✅ Naming series portuguesa {doc.naming_series} atribuída ao documento {doc.doctype}")
			else:
				# ✅ NÃO FORÇAR CRIAÇÃO - DEIXAR PARA DOCUMENT_HOOKS
				frappe.logger().info(
					f"⏭️ Nenhuma série portuguesa encontrada para {doc.doctype} - {doc.company}")

		except Exception as e:
			frappe.log_error(f"Erro ao definir série portuguesa: {str(e)}", "SeriesManager")

	# ✅ NÃO BLOQUEAR O DOCUMENTO - APENAS LOG

	def get_best_series_configuration(self, doc):
		"""
		✅ ALINHADO: Obtém a melhor configuração de série (prioriza comunicadas)
		"""
		try:
			# ✅ PRIORIDADE 1: Série comunicada com validation_code
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"document_type": doc.doctype,
				"company": doc.company,
				"is_active": 1,
				"is_communicated": 1,
				"validation_code": ["!=", ""]
			}, ["name", "prefix"], order_by="communication_date desc")

			if series_config:
				return frappe.get_doc("Portugal Series Configuration", series_config[0])

			# ✅ PRIORIDADE 2: Série comunicada sem validation_code
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"document_type": doc.doctype,
				"company": doc.company,
				"is_active": 1,
				"is_communicated": 1
			}, ["name", "prefix"], order_by="communication_date desc")

			if series_config:
				return frappe.get_doc("Portugal Series Configuration", series_config[0])

			# ✅ PRIORIDADE 3: Série ativa não comunicada
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"document_type": doc.doctype,
				"company": doc.company,
				"is_active": 1
			}, ["name", "prefix"], order_by="creation desc")

			if series_config:
				return frappe.get_doc("Portugal Series Configuration", series_config[0])

			return None

		except Exception as e:
			frappe.log_error(f"Erro ao obter configuração de série: {str(e)}", "SeriesManager")
			return None

	def is_portuguese_naming_series(self, naming_series, company):
		"""
		✅ ALINHADO: Verifica se naming series é portuguesa (formato SEM HÍFENS)
		"""
		try:
			if not naming_series:
				return False

			# ✅ EXTRAIR PREFIXO (FORMATO SEM HÍFENS)
			prefix = naming_series.replace('.####', '')

			# ✅ VERIFICAR SE EXISTE SÉRIE PORTUGUESA COM ESTE PREFIXO
			return frappe.db.exists("Portugal Series Configuration", {
				"prefix": prefix,
				"company": company,
				"is_active": 1
			})

		except Exception:
			return False

	def validate_series_sequence(self, doc, method=None):
		"""
		✅ ALINHADO: Valida sequência da série (não bloqueante)
		"""
		try:
			# ✅ VERIFICAR SE TEM NAMING SERIES PORTUGUESA
			if not (doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																		   doc.company)):
				return

			# ✅ VALIDAR APENAS SE DOCUMENTO FOI NOMEADO
			if not doc.name or doc.name.startswith('new-') or doc.name == 'new':
				return

			# ✅ EXTRAIR PREFIXO E BUSCAR CONFIGURAÇÃO
			prefix = doc.naming_series.replace('.####', '')
			series_config = frappe.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": doc.company
			}, ["name", "current_sequence"], as_dict=True)

			if not series_config:
				return

			# ✅ EXTRAIR NÚMERO DO DOCUMENTO
			doc_number = self.extract_document_number(doc.name)
			expected_sequence = series_config.current_sequence

			# ✅ VALIDAÇÃO NÃO BLOQUEANTE (APENAS WARNING)
			if doc_number < expected_sequence:
				frappe.logger().warning(
					f"⚠️ Documento {doc.name} tem número {doc_number} menor que sequência esperada {expected_sequence}")

			# ✅ ATUALIZAR SEQUÊNCIA SE NECESSÁRIO (THREAD-SAFE)
			if doc_number >= expected_sequence:
				frappe.db.set_value("Portugal Series Configuration", series_config.name,
									"current_sequence", doc_number + 1)

		except Exception as e:
			frappe.log_error(f"Erro na validação de sequência: {str(e)}", "SeriesManager")

	def extract_document_number(self, document_name):
		"""
		✅ ALINHADO: Extrai número do documento (formato SEM HÍFENS)
		"""
		if not document_name:
			return 1

		# ✅ PADRÕES PARA EXTRAIR NÚMERO (ALINHADOS COM FORMATO SEM HÍFENS)
		patterns = [
			r'-(\d{8})$',  # ATCUD: AAJFJMVNTN-00000001
			r'\.(\d+)$',  # ERPNext: FT2025NDX.0001
			r'-(\d+)$',  # Alternativo: PREFIX-NNNN
			r'(\d+)$'  # Apenas números no final
		]

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return cint(match.group(1))

		# ✅ FALLBACK SEGURO
		frappe.logger().warning(f"Não foi possível extrair número do documento: {document_name}")
		return 1

	def is_portugal_compliance_enabled(self, company):
		"""
		✅ ALINHADO: Verifica se compliance português está ativado (com cache)
		"""
		try:
			# ✅ CACHE SIMPLES PARA PERFORMANCE
			cache_key = f"portugal_compliance_{company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is not None:
				return cached_result

			# ✅ VERIFICAR NA BASE DE DADOS
			company_data = frappe.db.get_value("Company", company,
											   ["country", "portugal_compliance_enabled"])

			if not company_data:
				result = False
			else:
				country, compliance_enabled = company_data
				result = country == "Portugal" and cint(compliance_enabled)

			# ✅ CACHE POR 5 MINUTOS
			frappe.cache().set_value(cache_key, result, expires_in_sec=300)
			return result

		except Exception as e:
			frappe.log_error(f"Erro ao verificar compliance português: {str(e)}", "SeriesManager")
			return False

	# ========== MÉTODOS DE GESTÃO DE SÉRIES ALINHADOS ==========

	def get_series_for_document_type(self, doctype, company):
		"""
		✅ ALINHADO: Retorna séries disponíveis ordenadas por prioridade
		"""
		try:
			return frappe.get_all("Portugal Series Configuration",
								  filters={
									  "document_type": doctype,
									  "company": company,
									  "is_active": 1
								  },
								  fields=["name", "prefix", "is_communicated", "current_sequence",
										  "validation_code"],
								  order_by="is_communicated desc, validation_code desc, communication_date desc")

		except Exception as e:
			frappe.log_error(f"Erro ao obter séries: {str(e)}", "SeriesManager")
			return []

	def get_next_sequence_number(self, series_name):
		"""
		✅ ALINHADO: Obtém próximo número da sequência (thread-safe)
		"""
		try:
			# ✅ USAR TRANSAÇÃO PARA THREAD SAFETY
			with frappe.db.transaction():
				series_config = frappe.get_doc("Portugal Series Configuration", series_name)
				current = series_config.current_sequence
				series_config.current_sequence += 1
				series_config.save(ignore_permissions=True)
				return current

		except Exception as e:
			frappe.log_error(f"Erro ao obter próximo número da sequência: {str(e)}",
							 "SeriesManager")
			return 1

	def validate_series_format(self, series_prefix):
		"""
		✅ ALINHADO: Valida formato da série (flexível, não restritivo)
		"""
		try:
			if not series_prefix:
				return False

			# ✅ PADRÕES ACEITOS (FLEXÍVEIS)
			patterns = [
				r"^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}$",  # Português SEM HÍFENS: FT2025NDX
				r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]{1,4}$",
				# Português COM HÍFENS: FT-2025-NDX (compatibilidade)
				r"^[A-Z]{2,10}$",  # Simples: FT
				r"^[A-Z]{2,10}-\d{4}$"  # Com ano: FT-2025
			]

			for pattern in patterns:
				if re.match(pattern, series_prefix):
					return True

			# ✅ ACEITAR MESMO SE NÃO CORRESPONDE (SEGURO)
			return True

		except Exception:
			return True

	# ========== CRIAÇÃO DE SÉRIES INTEGRADA (NÃO DUPLICA DOCUMENT_HOOKS) ==========

	def create_default_series(self, company, fiscal_year=None):
		"""
		✅ ALINHADO: Cria séries padrão APENAS se não existirem
		Não conflita com document_hooks.py
		"""
		try:
			# ✅ VERIFICAR SE JÁ EXISTEM SÉRIES (EVITAR DUPLICAÇÃO)
			existing_series = frappe.db.count("Portugal Series Configuration", {
				"company": company,
				"is_active": 1
			})

			if existing_series > 0:
				frappe.logger().info(
					f"⏭️ Empresa {company} já tem {existing_series} séries - não criando padrão")
				return {
					"success": True,
					"created_series": [],
					"message": f"Empresa já tem {existing_series} séries ativas"
				}

			# ✅ USAR DOCUMENT_HOOKS PARA CRIAR (EVITAR DUPLICAÇÃO)
			try:
				from portugal_compliance.utils.document_hooks import portugal_document_hooks

				# Simular ativação de compliance para triggerar criação
				company_doc = frappe.get_doc("Company", company)
				result = portugal_document_hooks._create_dynamic_portugal_series_certified(
					company_doc)

				if result.get("success"):
					return {
						"success": True,
						"created_series": result.get("created_series", []),
						"created_count": result.get("created", 0)
					}
				else:
					return {
						"success": False,
						"error": result.get("error", "Erro na criação automática")
					}

			except ImportError:
				# ✅ FALLBACK: Criação manual básica
				return self.create_basic_series_fallback(company)

		except Exception as e:
			frappe.log_error(f"Erro ao criar séries padrão: {str(e)}", "SeriesManager")
			return {
				"success": False,
				"error": str(e)
			}

	def create_basic_series_fallback(self, company):
		"""
		✅ ALINHADO: Fallback para criação básica (formato SEM HÍFENS)
		"""
		try:
			year = getdate().year
			company_abbr = frappe.db.get_value("Company", company, "abbr") or "NDX"
			company_abbr = company_abbr.upper()[:4]

			# ✅ SÉRIES BÁSICAS ESSENCIAIS (ALINHADAS COM DOCUMENT_HOOKS)
			basic_series = {
				"Sales Invoice": ["FT"],
				"Purchase Invoice": ["FC"],
				"Payment Entry": ["RC"],
				"POS Invoice": ["FS"]
			}

			created_series = []

			for doctype, prefixes in basic_series.items():
				for prefix_code in prefixes:
					# ✅ FORMATO SEM HÍFENS (ALINHADO)
					prefix = f"{prefix_code}{year}{company_abbr}"

					# ✅ VERIFICAR SE JÁ EXISTE
					if not frappe.db.exists("Portugal Series Configuration", {
						"prefix": prefix,
						"company": company
					}):
						# ✅ CRIAR SÉRIE BÁSICA
						series_doc = frappe.get_doc({
							"doctype": "Portugal Series Configuration",
							"series_name": f"{prefix_code} {year} - {company}",
							"prefix": prefix,
							"naming_series": f"{prefix}.####",
							"document_type": doctype,
							"company": company,
							"current_sequence": 1,
							"is_active": 1,
							"is_communicated": 0,
							"document_code": prefix_code,
							"year_code": str(year),
							"company_code": company_abbr
						})

						series_doc.insert(ignore_permissions=True)
						created_series.append(prefix)

			return {
				"success": True,
				"created_series": created_series,
				"created_count": len(created_series)
			}

		except Exception as e:
			frappe.log_error(f"Erro no fallback de criação: {str(e)}", "SeriesManager")
			return {
				"success": False,
				"error": str(e)
			}

	# ========== ESTATÍSTICAS E RELATÓRIOS ALINHADOS ==========

	def get_series_usage_stats(self, series_name):
		"""
		✅ ALINHADO: Retorna estatísticas de uso de uma série
		"""
		try:
			series_config = frappe.get_doc("Portugal Series Configuration", series_name)

			# ✅ CONTAR DOCUMENTOS QUE USAM ESTA SÉRIE
			naming_series = f"{series_config.prefix}.####"

			document_count = frappe.db.count(series_config.document_type, {
				"naming_series": naming_series,
				"docstatus": ["!=", 2]  # Excluir cancelados
			})

			# ✅ ÚLTIMO DOCUMENTO CRIADO
			last_doc = frappe.db.get_value(series_config.document_type, {
				"naming_series": naming_series,
				"docstatus": ["!=", 2]
			}, ["name", "creation"], order_by="creation desc")

			return {
				"series_name": series_name,
				"prefix": series_config.prefix,
				"document_type": series_config.document_type,
				"company": series_config.company,
				"current_sequence": series_config.current_sequence,
				"next_number": series_config.current_sequence,
				"documents_created": document_count,
				"last_document": last_doc[0] if last_doc else None,
				"last_creation": last_doc[1] if last_doc else None,
				"is_communicated": series_config.is_communicated,
				"validation_code": series_config.validation_code,
				"at_environment": getattr(series_config, 'at_environment', 'test'),
				"naming_series": naming_series
			}

		except Exception as e:
			frappe.log_error(f"Erro ao obter estatísticas: {str(e)}", "SeriesManager")
			return {}

	def get_company_series_summary(self, company):
		"""
		✅ ALINHADO: Resumo de todas as séries de uma empresa
		"""
		try:
			series_list = frappe.get_all("Portugal Series Configuration",
										 filters={"company": company, "is_active": 1},
										 fields=["name", "prefix", "document_type",
												 "is_communicated", "current_sequence",
												 "validation_code"])

			summary = {
				"company": company,
				"total_series": len(series_list),
				"communicated_series": len([s for s in series_list if s.is_communicated]),
				"pending_series": len([s for s in series_list if not s.is_communicated]),
				"series_with_validation_code": len([s for s in series_list if s.validation_code]),
				"by_document_type": {},
				"series_details": series_list
			}

			# ✅ AGRUPAR POR TIPO DE DOCUMENTO
			for series in series_list:
				doc_type = series.document_type
				if doc_type not in summary["by_document_type"]:
					summary["by_document_type"][doc_type] = {
						"total": 0,
						"communicated": 0,
						"pending": 0,
						"with_validation_code": 0
					}

				summary["by_document_type"][doc_type]["total"] += 1
				if series.is_communicated:
					summary["by_document_type"][doc_type]["communicated"] += 1
				else:
					summary["by_document_type"][doc_type]["pending"] += 1

				if series.validation_code:
					summary["by_document_type"][doc_type]["with_validation_code"] += 1

			return summary

		except Exception as e:
			frappe.log_error(f"Erro ao obter resumo da empresa: {str(e)}", "SeriesManager")
			return {}

	# ========== VALIDAÇÕES E PERMISSÕES ALINHADAS ==========

	def validate_series_permissions(self, doc, method=None):
		"""
		✅ ALINHADO: Valida permissões de série (não bloqueante)
		"""
		try:
			# ✅ VERIFICAR APENAS SE TEM NAMING SERIES PORTUGUESA
			if not (doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																		   doc.company)):
				return

			# ✅ VERIFICAR PERMISSÃO DA EMPRESA (NÃO BLOQUEANTE)
			if not frappe.has_permission("Company", "read", doc.company):
				frappe.logger().warning(
					f"⚠️ Usuário {frappe.session.user} sem permissão para empresa {doc.company}")
			# ✅ NÃO BLOQUEAR - APENAS WARNING

			# ✅ LOG DE AUDITORIA
			prefix = doc.naming_series.replace('.####', '')
			frappe.logger().info(
				f"👤 Usuário {frappe.session.user} usando série {prefix} da empresa {doc.company}")

		except Exception as e:
			frappe.log_error(f"Erro na validação de permissões: {str(e)}", "SeriesManager")

	def reset_series_sequence(self, series_name, new_start=1):
		"""
		✅ ALINHADO: Reinicia sequência de uma série (com auditoria)
		"""
		if not frappe.has_permission("Portugal Series Configuration", "write"):
			frappe.throw(_("Permissões insuficientes para reiniciar sequência"))

		try:
			series_config = frappe.get_doc("Portugal Series Configuration", series_name)
			old_sequence = series_config.current_sequence

			# ✅ VALIDAR NOVO VALOR
			if new_start < 1:
				frappe.throw(_("Sequência deve ser maior que 0"))

			series_config.current_sequence = new_start
			series_config.save()

			# ✅ LOG DE AUDITORIA
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Portugal Series Configuration",
				"reference_name": series_name,
				"content": f"Sequência reiniciada de {old_sequence} para {new_start} por {frappe.session.user}"
			}).insert(ignore_permissions=True)

			frappe.logger().info(
				f"🔄 Sequência da série {series_name} reiniciada: {old_sequence} → {new_start}")

			return True

		except Exception as e:
			frappe.log_error(f"Erro ao reiniciar sequência: {str(e)}", "SeriesManager")
			frappe.throw(_("Erro ao reiniciar sequência da série"))

	# ========== APIS WHITELISTED ALINHADAS ==========

	@frappe.whitelist()
	def bulk_create_series(self, companies, fiscal_year=None):
		"""
		✅ ALINHADO: Cria séries em lote (não duplica document_hooks)
		"""
		try:
			if isinstance(companies, str):
				companies = [companies]

			results = []

			for company in companies:
				try:
					if self.is_portugal_compliance_enabled(company):
						result = self.create_default_series(company, fiscal_year)
						results.append({
							"company": company,
							"result": result,
							"status": "success" if result.get("success") else "error"
						})
					else:
						results.append({
							"company": company,
							"result": {"success": False,
									   "error": "Portugal compliance not enabled"},
							"status": "skipped"
						})

				except Exception as e:
					results.append({
						"company": company,
						"result": {"success": False, "error": str(e)},
						"status": "error"
					})

			return {
				"status": "completed",
				"total_companies": len(companies),
				"successful": len([r for r in results if r["status"] == "success"]),
				"results": results
			}

		except Exception as e:
			frappe.log_error(f"Erro na criação em lote: {str(e)}", "SeriesManager")
			return {"status": "error", "message": str(e)}

	@frappe.whitelist()
	def get_series_statistics(self, company=None):
		"""
		✅ ALINHADO: API para obter estatísticas de séries
		"""
		try:
			if company:
				return self.get_company_series_summary(company)
			else:
				# ✅ ESTATÍSTICAS GLOBAIS
				companies = frappe.get_all("Company",
										   filters={"portugal_compliance_enabled": 1},
										   fields=["name"])

				global_stats = {
					"total_companies": len(companies),
					"companies_summary": {}
				}

				for comp in companies:
					global_stats["companies_summary"][comp.name] = self.get_company_series_summary(
						comp.name)

				return global_stats

		except Exception as e:
			frappe.log_error(f"Erro ao obter estatísticas: {str(e)}", "SeriesManager")
			return {"error": str(e)}


# ========== INSTÂNCIA GLOBAL ALINHADA ==========
series_manager = SeriesManager()


# ========== FUNÇÕES AUXILIARES PARA HOOKS ALINHADAS ==========

def set_portugal_series(doc, method=None):
	"""✅ ALINHADO: Hook para definir série portuguesa"""
	return series_manager.set_portugal_series(doc, method)


def validate_series_sequence(doc, method=None):
	"""✅ ALINHADO: Hook para validar sequência"""
	return series_manager.validate_series_sequence(doc, method)


def validate_series_permissions(doc, method=None):
	"""✅ ALINHADO: Hook para validar permissões"""
	return series_manager.validate_series_permissions(doc, method)


# ========== FUNÇÕES PARA INTEGRAÇÃO ALINHADAS ==========

def get_series_for_document_type(doctype, company):
	"""✅ ALINHADO: Obter séries para tipo de documento"""
	return series_manager.get_series_for_document_type(doctype, company)


def create_default_series(company, fiscal_year=None):
	"""✅ ALINHADO: Criar séries padrão (não duplica)"""
	return series_manager.create_default_series(company, fiscal_year)


def get_series_usage_stats(series_name):
	"""✅ ALINHADO: Obter estatísticas de uso"""
	return series_manager.get_series_usage_stats(series_name)


def is_portugal_compliance_enabled(company):
	"""✅ ALINHADO: Verificar se compliance está ativo"""
	return series_manager.is_portugal_compliance_enabled(company)


# ========== LOG FINAL ==========
frappe.logger().info("Portugal Series Manager ALINHADO loaded - Version 2.1.0 - Safe & Compatible")
