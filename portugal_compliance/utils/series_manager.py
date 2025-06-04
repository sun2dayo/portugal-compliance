# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Manager for Portugal Compliance - VERSÃO CERTIFICADA OTIMIZADA
Manages Portuguese series for documents with intelligent integration
COMPATÍVEL COM CRIAÇÃO AUTOMÁTICA DE SÉRIES - SEM CONFLITOS
"""

import frappe
from frappe import _
import re
from frappe.utils import cint, today, getdate
from erpnext.accounts.utils import get_fiscal_year


class SeriesManager:
	"""
	Gerenciador de séries portuguesas para documentos
	VERSÃO CORRIGIDA: integrado com document_hooks.py e series_adapter.py
	"""

	def __init__(self):
		self.supported_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'Payment Entry',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry',
			'Quotation', 'Sales Order', 'Purchase Order', 'Material Request'
		]
		self.module = "Portugal Compliance"

	# ========== MÉTODOS PRINCIPAIS OTIMIZADOS ==========

	def set_portugal_series(self, doc, method=None):
		"""
		Define série portuguesa para documento - VERSÃO OTIMIZADA
		Integrado com auto-seleção do sales_invoice.js
		"""
		try:
			# ✅ VERIFICAÇÕES BÁSICAS
			if not self.is_portugal_compliance_enabled(doc.company):
				return

			if doc.doctype not in self.supported_doctypes:
				return

			# ✅ SE JÁ TEM NAMING SERIES PORTUGUESA, NÃO ALTERAR
			if doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																	  doc.company):
				return

			# ✅ BUSCAR SÉRIE PORTUGUESA ATIVA E COMUNICADA
			series_config = self.get_best_series_configuration(doc)

			if series_config:
				# Definir naming series portuguesa
				doc.naming_series = f"{series_config.prefix}.####"

				frappe.logger().info(
					f"✅ Naming series portuguesa {doc.naming_series} atribuída ao documento {doc.doctype}")
			else:
				# ✅ NÃO SUGERIR CRIAÇÃO - DEIXAR PARA CRIAÇÃO AUTOMÁTICA
				frappe.logger().info(
					f"⏭️ Nenhuma série portuguesa encontrada para {doc.doctype} - {doc.company}")

		except Exception as e:
			frappe.log_error(f"Erro ao definir série portuguesa: {str(e)}", "SeriesManager")
		# ✅ NÃO BLOQUEAR O DOCUMENTO - APENAS LOG

	def get_best_series_configuration(self, doc):
		"""
		Obtém a melhor configuração de série para o documento
		VERSÃO OTIMIZADA: prioriza séries comunicadas
		"""
		try:
			# ✅ PRIORIDADE 1: Série comunicada
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"document_type": doc.doctype,
				"company": doc.company,
				"is_active": 1,
				"is_communicated": 1
			}, ["name", "prefix"], order_by="communication_date desc")

			if series_config:
				return frappe.get_doc("Portugal Series Configuration", series_config[0])

			# ✅ PRIORIDADE 2: Série ativa não comunicada
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"document_type": doc.doctype,
				"company": doc.company,
				"is_active": 1,
				"is_communicated": 0
			}, ["name", "prefix"], order_by="creation desc")

			if series_config:
				return frappe.get_doc("Portugal Series Configuration", series_config[0])

			return None

		except Exception as e:
			frappe.log_error(f"Erro ao obter configuração de série: {str(e)}", "SeriesManager")
			return None

	def is_portuguese_naming_series(self, naming_series, company):
		"""
		Verifica se naming series é portuguesa
		"""
		try:
			if not naming_series:
				return False

			# Extrair prefixo
			prefix = naming_series.replace('.####', '')

			# Verificar se existe série portuguesa com este prefixo
			return frappe.db.exists("Portugal Series Configuration", {
				"prefix": prefix,
				"company": company,
				"is_active": 1
			})

		except Exception:
			return False

	def validate_series_sequence(self, doc, method=None):
		"""
		Valida sequência da série - VERSÃO OTIMIZADA
		Apenas para documentos com naming series portuguesa
		"""
		try:
			# ✅ VERIFICAR SE TEM NAMING SERIES PORTUGUESA
			if not (doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																		   doc.company)):
				return

			# ✅ VALIDAR APENAS SE DOCUMENTO FOI NOMEADO
			if not doc.name or doc.name.startswith('new-') or doc.name == 'new':
				return

			# Extrair prefixo e buscar configuração
			prefix = doc.naming_series.replace('.####', '')
			series_config = frappe.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": doc.company
			}, ["name", "current_sequence"], as_dict=True)

			if not series_config:
				return

			# Extrair número do documento
			doc_number = self.extract_document_number(doc.name)
			expected_sequence = series_config.current_sequence

			# ✅ VALIDAÇÃO NÃO BLOQUEANTE
			if doc_number < expected_sequence:
				frappe.logger().warning(
					f"⚠️ Documento {doc.name} tem número {doc_number} menor que sequência esperada {expected_sequence}")
			# ✅ NÃO BLOQUEAR - APENAS WARNING

			# ✅ ATUALIZAR SEQUÊNCIA SE NECESSÁRIO
			if doc_number >= expected_sequence:
				frappe.db.set_value("Portugal Series Configuration", series_config.name,
									"current_sequence", doc_number + 1)

		except Exception as e:
			frappe.log_error(f"Erro na validação de sequência: {str(e)}", "SeriesManager")

	def extract_document_number(self, document_name):
		"""
		Extrai número do documento - VERSÃO MELHORADA
		"""
		if not document_name:
			return 1

		# ✅ PADRÕES PARA EXTRAIR NÚMERO
		patterns = [
			r'-(\d{8})$',  # Padrão português: FT-2025-NDX-00000001
			r'\.(\d+)$',  # Padrão ERPNext: PREFIX.NNNN
			r'-(\d+)$',  # Padrão alternativo: PREFIX-NNNN
			r'(\d+)$'  # Apenas números no final
		]

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return cint(match.group(1))

		# ✅ FALLBACK
		frappe.logger().warning(f"Não foi possível extrair número do documento: {document_name}")
		return 1

	def is_portugal_compliance_enabled(self, company):
		"""
		Verifica se compliance português está ativado - VERSÃO OTIMIZADA
		"""
		try:
			# ✅ CACHE SIMPLES
			cache_key = f"portugal_compliance_{company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is not None:
				return cached_result

			# Verificar na base de dados
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

	# ========== MÉTODOS DE GESTÃO DE SÉRIES OTIMIZADOS ==========

	def get_series_for_document_type(self, doctype, company):
		"""
		Retorna séries disponíveis para um tipo de documento
		VERSÃO OTIMIZADA: ordenada por prioridade
		"""
		try:
			return frappe.get_all("Portugal Series Configuration",
								  filters={
									  "document_type": doctype,
									  "company": company,
									  "is_active": 1
								  },
								  fields=["name", "prefix", "is_communicated",
										  "current_sequence", "validation_code"],
								  order_by="is_communicated desc, communication_date desc")

		except Exception as e:
			frappe.log_error(f"Erro ao obter séries: {str(e)}", "SeriesManager")
			return []

	def get_next_sequence_number(self, series_name):
		"""
		Obtém próximo número da sequência - VERSÃO THREAD-SAFE
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
		Valida formato da série - VERSÃO FLEXÍVEL
		"""
		try:
			if not series_prefix:
				return False

			# ✅ PADRÕES ACEITOS
			patterns = [
				r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}$",  # Português: XX-YYYY-COMPANY
				r"^[A-Z]{2,10}$",  # Simples: XX
				r"^[A-Z]{2,10}-\d{4}$"  # Com ano: XX-YYYY
			]

			for pattern in patterns:
				if re.match(pattern, series_prefix):
					return True

			return False

		except Exception:
			return False

	# ========== CRIAÇÃO DE SÉRIES INTEGRADA ==========

	def create_default_series(self, company, fiscal_year=None):
		"""
		Cria séries padrão para uma empresa - VERSÃO INTEGRADA
		Não conflita com criação automática
		"""
		try:
			# ✅ VERIFICAR SE JÁ EXISTEM SÉRIES
			existing_series = frappe.db.count("Portugal Series Configuration", {
				"company": company,
				"is_active": 1
			})

			if existing_series > 0:
				frappe.logger().info(
					f"⏭️ Empresa {company} já tem {existing_series} séries - não criando padrão")
				return []

			# ✅ USAR SERIES_ADAPTER PARA CRIAR
			try:
				from portugal_compliance.utils.document_hooks import create_dynamic_portugal_series

				result = create_dynamic_portugal_series(company)

				if result.get("success"):
					return result.get("created_series", [])
				else:
					frappe.logger().error(f"Erro na criação automática: {result.get('error')}")
					return []

			except ImportError:
				# ✅ FALLBACK: Criação manual simples
				return self.create_basic_series_fallback(company)

		except Exception as e:
			frappe.log_error(f"Erro ao criar séries padrão: {str(e)}", "SeriesManager")
			return []

	def create_basic_series_fallback(self, company):
		"""
		Fallback para criação básica de séries
		"""
		try:
			year = getdate().year
			company_abbr = frappe.db.get_value("Company", company, "abbr") or "NDX"
			company_abbr = company_abbr.upper()[:4]

			# ✅ SÉRIES BÁSICAS ESSENCIAIS
			basic_series = {
				"Sales Invoice": ["FT"],
				"Purchase Invoice": ["FC"],
				"Payment Entry": ["RC"]
			}

			created_series = []

			for doctype, prefixes in basic_series.items():
				for prefix_code in prefixes:
					prefix = f"{prefix_code}-{year}-{company_abbr}"

					# Verificar se já existe
					if not frappe.db.exists("Portugal Series Configuration", {
						"prefix": prefix,
						"company": company
					}):
						# Criar série básica
						series_doc = frappe.get_doc({
							"doctype": "Portugal Series Configuration",
							"prefix": prefix,
							"document_type": doctype,
							"company": company,
							"current_sequence": 1,
							"is_active": 1,
							"is_communicated": 0,
							"description": f"Série {prefix_code} criada automaticamente"
						})

						series_doc.insert(ignore_permissions=True)
						created_series.append(prefix)

			return created_series

		except Exception as e:
			frappe.log_error(f"Erro no fallback de criação: {str(e)}", "SeriesManager")
			return []

	# ========== ESTATÍSTICAS E RELATÓRIOS ==========

	def get_series_usage_stats(self, series_name):
		"""
		Retorna estatísticas de uso de uma série - VERSÃO COMPLETA
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

			# ✅ PRÓXIMO NÚMERO DISPONÍVEL
			next_number = series_config.current_sequence

			return {
				"series_name": series_name,
				"prefix": series_config.prefix,
				"document_type": series_config.document_type,
				"company": series_config.company,
				"current_sequence": series_config.current_sequence,
				"next_number": next_number,
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
		Resumo de todas as séries de uma empresa
		"""
		try:
			series_list = frappe.get_all("Portugal Series Configuration",
										 filters={"company": company, "is_active": 1},
										 fields=["name", "prefix", "document_type",
												 "is_communicated", "current_sequence"])

			summary = {
				"company": company,
				"total_series": len(series_list),
				"communicated_series": len([s for s in series_list if s.is_communicated]),
				"pending_series": len([s for s in series_list if not s.is_communicated]),
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
						"pending": 0
					}

				summary["by_document_type"][doc_type]["total"] += 1
				if series.is_communicated:
					summary["by_document_type"][doc_type]["communicated"] += 1
				else:
					summary["by_document_type"][doc_type]["pending"] += 1

			return summary

		except Exception as e:
			frappe.log_error(f"Erro ao obter resumo da empresa: {str(e)}", "SeriesManager")
			return {}

	# ========== VALIDAÇÕES E PERMISSÕES ==========

	def validate_series_permissions(self, doc, method=None):
		"""
		Valida permissões de série - VERSÃO OTIMIZADA
		"""
		try:
			# ✅ VERIFICAR APENAS SE TEM NAMING SERIES PORTUGUESA
			if not (doc.naming_series and self.is_portuguese_naming_series(doc.naming_series,
																		   doc.company)):
				return

			# ✅ VERIFICAR PERMISSÃO DA EMPRESA
			if not frappe.has_permission("Company", "read", doc.company):
				frappe.throw(
					_("Sem permissão para usar séries da empresa {0}").format(doc.company))

			# ✅ LOG DE AUDITORIA
			prefix = doc.naming_series.replace('.####', '')
			frappe.logger().info(
				f"👤 Usuário {frappe.session.user} usando série {prefix} da empresa {doc.company}")

		except Exception as e:
			frappe.log_error(f"Erro na validação de permissões: {str(e)}", "SeriesManager")

	def reset_series_sequence(self, series_name, new_start=1):
		"""
		Reinicia sequência de uma série - VERSÃO SEGURA
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

	# ========== MÉTODOS WHITELISTED PARA API ==========

	@frappe.whitelist()
	def bulk_create_series(self, companies, fiscal_year=None):
		"""
		Cria séries em lote para múltiplas empresas
		"""
		try:
			if isinstance(companies, str):
				companies = [companies]

			results = []

			for company in companies:
				try:
					if self.is_portugal_compliance_enabled(company):
						created = self.create_default_series(company, fiscal_year)
						results.append({
							"company": company,
							"created_series": created,
							"status": "success",
							"count": len(created)
						})
					else:
						results.append({
							"company": company,
							"created_series": [],
							"status": "skipped",
							"reason": "Portugal compliance not enabled",
							"count": 0
						})

				except Exception as e:
					results.append({
						"company": company,
						"created_series": [],
						"status": "error",
						"reason": str(e),
						"count": 0
					})

			return {
				"status": "completed",
				"total_companies": len(companies),
				"successful": len([r for r in results if r["status"] == "success"]),
				"results": results
			}

		except Exception as e:
			frappe.log_error(f"Erro na criação em lote: {str(e)}", "SeriesManager")
			return {
				"status": "error",
				"message": str(e)
			}

	@frappe.whitelist()
	def get_series_statistics(self, company=None):
		"""
		API para obter estatísticas de séries
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


# ========== INSTÂNCIA GLOBAL PARA USO ==========

# ✅ INSTÂNCIA GLOBAL
series_manager = SeriesManager()


# ========== FUNÇÕES AUXILIARES PARA HOOKS ==========

def set_portugal_series(doc, method=None):
	"""Hook para definir série portuguesa"""
	return series_manager.set_portugal_series(doc, method)


def validate_series_sequence(doc, method=None):
	"""Hook para validar sequência"""
	return series_manager.validate_series_sequence(doc, method)


def validate_series_permissions(doc, method=None):
	"""Hook para validar permissões"""
	return series_manager.validate_series_permissions(doc, method)


# ========== FUNÇÕES PARA INTEGRAÇÃO ==========

def get_series_for_document_type(doctype, company):
	"""Obter séries para tipo de documento"""
	return series_manager.get_series_for_document_type(doctype, company)


def create_default_series(company, fiscal_year=None):
	"""Criar séries padrão"""
	return series_manager.create_default_series(company, fiscal_year)


def get_series_usage_stats(series_name):
	"""Obter estatísticas de uso"""
	return series_manager.get_series_usage_stats(series_name)


def is_portugal_compliance_enabled(company):
	"""Verificar se compliance está ativo"""
	return series_manager.is_portugal_compliance_enabled(company)
