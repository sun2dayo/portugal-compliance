# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import re
from datetime import datetime, date
from frappe.utils import getdate, get_datetime, flt, cint


class DocumentValidator:
	def __init__(self):
		# ✅ ADAPTADO: Usar doctypes suportados pela nova abordagem
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
		self.supported_doctypes = list(PORTUGAL_DOCUMENT_TYPES.keys())

		self.validation_rules = self._load_validation_rules()

	def _load_validation_rules(self):
		"""
		✅ ADAPTADO: Carrega regras de validação específicas para Portugal (nova abordagem)
		"""
		return {
			"nif_validation": True,
			"atcud_required": True,
			"naming_series_required": True,  # ✅ CORRIGIDO: naming_series em vez de series
			"sequential_numbering": True,
			"tax_validation": True,
			"currency_validation": True,
			"date_validation": True,
			"portuguese_series_validation": True  # ✅ NOVO: Validação de séries portuguesas
		}

	def validate_document(self, doc, method=None):
		"""
		✅ ADAPTADO: Validação principal do documento para conformidade portuguesa (nova abordagem)
		"""
		try:
			# Verificar se validação é necessária
			if not self._should_validate(doc):
				return True

			validation_results = []

			# ✅ EXECUTAR TODAS AS VALIDAÇÕES (ADAPTADAS)
			validation_results.extend(self.validate_company_compliance(doc))
			validation_results.extend(self.validate_naming_series_new_approach(doc))  # ✅ CORRIGIDO
			validation_results.extend(self.validate_atcud_new_approach(doc))  # ✅ CORRIGIDO
			validation_results.extend(self.validate_customer_supplier_data(doc))
			validation_results.extend(self.validate_tax_information(doc))
			validation_results.extend(self.validate_currency_and_amounts(doc))
			validation_results.extend(self.validate_dates(doc))
			validation_results.extend(
				self.validate_sequential_numbering_new_approach(doc))  # ✅ CORRIGIDO

			# Processar resultados
			errors = [r for r in validation_results if r["type"] == "error"]
			warnings = [r for r in validation_results if r["type"] == "warning"]

			# Log das validações
			self._log_validation_results(doc, validation_results)

			# Mostrar warnings
			for warning in warnings:
				frappe.msgprint(warning["message"], indicator="orange", title=_("Aviso"))

			# Bloquear se houver erros
			if errors:
				error_messages = [error["message"] for error in errors]
				frappe.throw(
					_("Erros de validação encontrados:\n{0}").format("\n".join(error_messages)))

			return True

		except Exception as e:
			frappe.log_error(f"Erro na validação do documento {doc.name}: {str(e)}")
			frappe.throw(_("Erro na validação do documento: {0}").format(str(e)))

	def _should_validate(self, doc):
		"""
		✅ MANTIDA: Verifica se o documento deve ser validado
		"""
		# Verificar se é doctype suportado
		if doc.doctype not in self.supported_doctypes:
			return False

		# Verificar se empresa tem compliance português ativado
		try:
			company_doc = frappe.get_doc("Company", doc.company)
			return (company_doc.get("country") == "Portugal" and
					company_doc.get("portugal_compliance_enabled", 0))
		except:
			return False

	def validate_company_compliance(self, doc):
		"""
		✅ MANTIDA: Valida configurações de compliance da empresa
		"""
		results = []

		try:
			company_doc = frappe.get_doc("Company", doc.company)

			# Verificar se país é Portugal
			if company_doc.country != "Portugal":
				results.append({
					"type": "error",
					"field": "company",
					"message": _("Empresa deve estar configurada para Portugal")
				})

			# Verificar se compliance está ativado
			if not company_doc.get("portugal_compliance_enabled"):
				results.append({
					"type": "warning",
					"field": "company",
					"message": _("Compliance português não está ativado para esta empresa")
				})

			# Verificar NIF da empresa
			if not company_doc.tax_id:
				results.append({
					"type": "error",
					"field": "company",
					"message": _("NIF da empresa não está configurado")
				})
			elif not self.validate_nif(company_doc.tax_id):
				results.append({
					"type": "error",
					"field": "company",
					"message": _("NIF da empresa é inválido")
				})

			# Verificar certificado AT
			if not company_doc.get("at_certificate_number"):
				results.append({
					"type": "warning",
					"field": "company",
					"message": _("Número do certificado AT não está configurado")
				})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "company",
				"message": _("Erro ao validar dados da empresa: {0}").format(str(e))
			})

		return results

	def validate_naming_series_new_approach(self, doc):
		"""
		✅ CORRIGIDO: Valida naming_series do documento (nova abordagem)
		"""
		results = []

		try:
			# ✅ VERIFICAR SE TEM NAMING_SERIES PORTUGUESA
			if not hasattr(doc, 'naming_series') or not doc.naming_series:
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Naming series portuguesa não está definida para este documento")
				})
				return results

			# ✅ VERIFICAR SE É SÉRIE PORTUGUESA VÁLIDA
			if not self._is_portuguese_naming_series(doc.naming_series):
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Naming series {0} não é uma série portuguesa válida").format(
						doc.naming_series)
				})
				return results

			# ✅ BUSCAR CONFIGURAÇÃO DA SÉRIE
			series_config = self._get_series_configuration(doc.naming_series, doc.company,
														   doc.doctype)

			if not series_config:
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Configuração não encontrada para série {0}").format(
						doc.naming_series)
				})
				return results

			# ✅ VERIFICAR SE SÉRIE ESTÁ COMUNICADA
			if not series_config.get("is_communicated"):
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Série {0} não foi comunicada à AT").format(
						series_config.get("prefix"))
				})

			# ✅ VERIFICAR SE TIPO DE DOCUMENTO CORRESPONDE
			if series_config.get("document_type") != doc.doctype:
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Série {0} não é válida para documentos do tipo {1}").format(
						series_config.get("prefix"), doc.doctype
					)
				})

			# ✅ VERIFICAR SE EMPRESA CORRESPONDE
			if series_config.get("company") != doc.company:
				results.append({
					"type": "error",
					"field": "naming_series",
					"message": _("Série {0} não pertence à empresa {1}").format(
						series_config.get("prefix"), doc.company
					)
				})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "naming_series",
				"message": _("Erro ao validar naming series do documento: {0}").format(str(e))
			})

		return results

	def _is_portuguese_naming_series(self, naming_series):
		"""
		✅ NOVO: Verifica se naming_series é portuguesa
		"""
		try:
			if not naming_series:
				return False

			# ✅ PADRÕES PORTUGUESES (NOVO E ANTIGO)
			new_pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'  # FT2025DSY.####
			old_patterns = [
				r'^(FT|FS|FC|RC|GR|GT|JE|NC|ND|OR|EC|EF|MR)-',
				r'^(FT|FS|FC|RC|GR|GT|JE|NC|ND|OR|EC|EF|MR)\.',
			]

			# Verificar padrão novo
			if re.match(new_pattern, naming_series):
				return True

			# Verificar padrões antigos
			for pattern in old_patterns:
				if re.match(pattern, naming_series):
					return True

			return False

		except Exception:
			return False

	def _get_series_configuration(self, naming_series, company, doctype):
		"""
		✅ NOVO: Obtém configuração da série baseada na naming_series
		"""
		try:
			# ✅ EXTRAIR PREFIXO DA NAMING_SERIES
			prefix = naming_series.replace('.####', '')

			# ✅ BUSCAR CONFIGURAÇÃO
			config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": company,
				"document_type": doctype
			}, ["name", "prefix", "is_communicated", "document_type", "company"], as_dict=True)

			return config

		except Exception as e:
			frappe.log_error(f"Erro ao obter configuração da série: {str(e)}")
			return None

	def validate_atcud_new_approach(self, doc):
		"""
		✅ CORRIGIDO: Valida ATCUD do documento (nova abordagem)
		"""
		results = []

		try:
			# Verificar se ATCUD é obrigatório para documento submetido
			if hasattr(doc, 'docstatus') and doc.docstatus == 1:
				if not hasattr(doc, 'atcud_code') or not doc.atcud_code:
					results.append({
						"type": "error",
						"field": "atcud_code",
						"message": _("ATCUD é obrigatório para documentos submetidos")
					})
					return results

				# ✅ VALIDAR FORMATO DO ATCUD (NOVO FORMATO: 0.SEQUENCIAL)
				if not self.validate_atcud_format_new_approach(doc.atcud_code):
					results.append({
						"type": "error",
						"field": "atcud_code",
						"message": _(
							"Formato do ATCUD é inválido: {0}. Use formato: 0.SEQUENCIAL").format(
							doc.atcud_code)
					})

				# ✅ VERIFICAR SE ATCUD CORRESPONDE AO TIPO DE DOCUMENTO
				prefix_validation = self.validate_atcud_prefix_new_approach(doc.atcud_code,
																			doc.doctype,
																			doc.naming_series)
				if not prefix_validation["valid"]:
					results.append({
						"type": "warning",
						"field": "atcud_code",
						"message": prefix_validation["message"]
					})

				# Verificar unicidade do ATCUD
				duplicate_check = self.check_atcud_uniqueness(doc.atcud_code, doc.name)
				if not duplicate_check["unique"]:
					results.append({
						"type": "error",
						"field": "atcud_code",
						"message": _("ATCUD {0} já está em uso no documento {1}").format(
							doc.atcud_code, duplicate_check["existing_document"]
						)
					})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "atcud_code",
				"message": _("Erro ao validar ATCUD: {0}").format(str(e))
			})

		return results

	def validate_atcud_format_new_approach(self, atcud):
		"""
		✅ CORRIGIDO: Valida formato do ATCUD (nova abordagem: 0.SEQUENCIAL)
		"""
		if not atcud:
			return False

		# ✅ FORMATO NOVO: 0.SEQUENCIAL (conforme Portaria 195/2020)
		pattern = r"^0\.\d+$"
		return bool(re.match(pattern, atcud.strip()))

	def validate_atcud_prefix_new_approach(self, atcud, doctype, naming_series):
		"""
		✅ CORRIGIDO: Valida se ATCUD corresponde à naming_series (nova abordagem)
		"""
		if not atcud or not naming_series:
			return {"valid": False, "message": "ATCUD ou naming_series não fornecidos"}

		try:
			# ✅ EXTRAIR PREFIXO DA NAMING_SERIES
			prefix = naming_series.replace('.####', '')

			# ✅ OBTER CÓDIGO DO PREFIXO
			if '-' in prefix:
				# Formato antigo: FT-2025-DSY
				code = prefix.split('-')[0]
			else:
				# Formato novo: FT2025DSY
				code_match = re.match(r'^([A-Z]{2,4})', prefix)
				code = code_match.group(1) if code_match else ""

			# ✅ VERIFICAR CÓDIGOS VÁLIDOS POR DOCTYPE
			from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
			doc_info = PORTUGAL_DOCUMENT_TYPES.get(doctype)

			if doc_info and code != doc_info.get('code'):
				return {
					"valid": False,
					"message": _(
						"Código da série '{0}' não corresponde ao esperado '{1}' para {2}").format(
						code, doc_info.get('code'), doctype
					)
				}

			return {"valid": True}

		except Exception as e:
			return {"valid": False, "message": f"Erro na validação: {str(e)}"}

	def validate_customer_supplier_data(self, doc):
		"""
		✅ MANTIDA: Valida dados de clientes/fornecedores
		"""
		results = []

		try:
			# Validar cliente (para faturas de venda)
			if hasattr(doc, 'customer') and doc.customer:
				customer_doc = frappe.get_doc("Customer", doc.customer)

				# Verificar NIF do cliente se necessário
				if self._requires_customer_nif(doc):
					if not customer_doc.tax_id:
						results.append({
							"type": "error",
							"field": "customer",
							"message": _(
								"NIF do cliente é obrigatório para este tipo de documento")
						})
					elif not self.validate_nif(customer_doc.tax_id):
						results.append({
							"type": "error",
							"field": "customer",
							"message": _("NIF do cliente é inválido: {0}").format(
								customer_doc.tax_id)
						})

			# Validar fornecedor (para faturas de compra)
			if hasattr(doc, 'supplier') and doc.supplier:
				supplier_doc = frappe.get_doc("Supplier", doc.supplier)

				if not supplier_doc.tax_id:
					results.append({
						"type": "warning",
						"field": "supplier",
						"message": _("NIF do fornecedor não está configurado")
					})
				elif not self.validate_nif(supplier_doc.tax_id):
					results.append({
						"type": "warning",
						"field": "supplier",
						"message": _("NIF do fornecedor é inválido: {0}").format(
							supplier_doc.tax_id)
					})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "customer_supplier",
				"message": _("Erro ao validar dados de cliente/fornecedor: {0}").format(str(e))
			})

		return results

	def validate_tax_information(self, doc):
		"""
		✅ MANTIDA: Valida informações de impostos
		"""
		results = []

		try:
			# Verificar se tem itens com impostos
			if hasattr(doc, 'items'):
				for item in doc.items:
					# Verificar se item tem template de impostos
					if not item.get('item_tax_template'):
						results.append({
							"type": "warning",
							"field": f"items[{item.idx}].item_tax_template",
							"message": _("Item {0} não tem template de impostos definido").format(
								item.item_code)
						})

			# Verificar impostos totais
			if hasattr(doc, 'taxes'):
				for tax in doc.taxes:
					# Verificar se conta de imposto é válida
					if not frappe.db.exists("Account", tax.account_head):
						results.append({
							"type": "error",
							"field": f"taxes[{tax.idx}].account_head",
							"message": _("Conta de imposto não existe: {0}").format(
								tax.account_head)
						})

			# Verificar se total de impostos está correto
			if hasattr(doc, 'total_taxes_and_charges') and hasattr(doc, 'net_total'):
				expected_total = flt(doc.net_total) + flt(doc.total_taxes_and_charges)
				if abs(flt(doc.grand_total) - expected_total) > 0.01:
					results.append({
						"type": "warning",
						"field": "grand_total",
						"message": _(
							"Total geral pode estar incorreto. Verificar cálculo de impostos.")
					})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "taxes",
				"message": _("Erro ao validar impostos: {0}").format(str(e))
			})

		return results

	def validate_currency_and_amounts(self, doc):
		"""
		✅ MANTIDA: Valida moeda e valores
		"""
		results = []

		try:
			# Verificar se moeda é EUR para Portugal
			if hasattr(doc, 'currency') and doc.currency != "EUR":
				results.append({
					"type": "warning",
					"field": "currency",
					"message": _("Moeda recomendada para Portugal é EUR. Moeda atual: {0}").format(
						doc.currency)
				})

			# Verificar valores negativos
			if hasattr(doc, 'grand_total') and flt(doc.grand_total) < 0:
				results.append({
					"type": "warning",
					"field": "grand_total",
					"message": _("Total geral é negativo. Verificar se deve ser nota de crédito.")
				})

			# Verificar precisão de valores
			if hasattr(doc, 'items'):
				for item in doc.items:
					if hasattr(item, 'rate') and item.rate:
						# Verificar se rate tem mais de 4 casas decimais
						rate_str = str(flt(item.rate))
						if '.' in rate_str and len(rate_str.split('.')[1]) > 4:
							results.append({
								"type": "warning",
								"field": f"items[{item.idx}].rate",
								"message": _(
									"Preço do item {0} tem mais de 4 casas decimais").format(
									item.item_code)
							})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "currency_amounts",
				"message": _("Erro ao validar moeda e valores: {0}").format(str(e))
			})

		return results

	def validate_dates(self, doc):
		"""
		✅ MANTIDA: Valida datas do documento
		"""
		results = []

		try:
			# Verificar data de lançamento
			if hasattr(doc, 'posting_date'):
				posting_date = getdate(doc.posting_date)
				today = getdate()

				# Verificar se data não é futura
				if posting_date > today:
					results.append({
						"type": "warning",
						"field": "posting_date",
						"message": _("Data de lançamento é futura: {0}").format(posting_date)
					})

				# Verificar se data não é muito antiga (mais de 1 ano)
				from datetime import timedelta
				one_year_ago = today - timedelta(days=365)
				if posting_date < one_year_ago:
					results.append({
						"type": "warning",
						"field": "posting_date",
						"message": _("Data de lançamento é muito antiga: {0}").format(posting_date)
					})

			# Verificar data de vencimento
			if hasattr(doc, 'due_date') and hasattr(doc, 'posting_date'):
				if doc.due_date and doc.posting_date:
					due_date = getdate(doc.due_date)
					posting_date = getdate(doc.posting_date)

					if due_date < posting_date:
						results.append({
							"type": "error",
							"field": "due_date",
							"message": _(
								"Data de vencimento não pode ser anterior à data de lançamento")
						})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "dates",
				"message": _("Erro ao validar datas: {0}").format(str(e))
			})

		return results

	def validate_sequential_numbering_new_approach(self, doc):
		"""
		✅ CORRIGIDO: Valida numeração sequencial (nova abordagem)
		"""
		results = []

		try:
			if not hasattr(doc, 'naming_series') or not doc.naming_series:
				return results

			# ✅ OBTER CONFIGURAÇÃO DA SÉRIE USANDO NAMING_SERIES
			series_config = self._get_series_configuration(doc.naming_series, doc.company,
														   doc.doctype)

			if not series_config:
				return results

			# Extrair número do documento
			doc_number = self._extract_document_number(doc.name)

			# ✅ BUSCAR SEQUÊNCIA ATUAL DA CONFIGURAÇÃO
			current_sequence = frappe.db.get_value("Portugal Series Configuration",
												   series_config["name"], "current_sequence")

			# Verificar se número está dentro da sequência esperada
			if current_sequence and doc_number < current_sequence - 100:  # Tolerância de 100
				results.append({
					"type": "warning",
					"field": "name",
					"message": _("Número do documento {0} pode estar fora de sequência").format(
						doc_number)
				})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "sequential_numbering",
				"message": _("Erro ao validar numeração sequencial: {0}").format(str(e))
			})

		return results

	def validate_nif(self, nif):
		"""
		✅ MANTIDA: Valida NIF português
		"""
		if not nif:
			return False

		# Remover espaços e caracteres não numéricos
		nif = re.sub(r'\D', '', str(nif))

		# Verificar comprimento
		if len(nif) != 9:
			return False

		# Verificar primeiro dígito
		first_digit = int(nif[0])
		valid_first_digits = [1, 2, 3, 5, 6, 7, 8, 9]

		if first_digit not in valid_first_digits:
			return False

		# Calcular dígito de controle
		total = 0
		for i in range(8):
			total += int(nif[i]) * (9 - i)

		remainder = total % 11
		check_digit = 0 if remainder < 2 else 11 - remainder

		return check_digit == int(nif[8])

	def check_atcud_uniqueness(self, atcud, current_doc_name):
		"""
		✅ MANTIDA: Verifica unicidade do ATCUD
		"""
		if not atcud:
			return {"unique": True}

		# Procurar ATCUD duplicado em todos os doctypes suportados
		for doctype in self.supported_doctypes:
			existing = frappe.db.get_value(doctype, {
				"atcud_code": atcud,
				"name": ["!=", current_doc_name],
				"docstatus": ["!=", 2]  # Excluir cancelados
			})

			if existing:
				return {
					"unique": False,
					"existing_document": existing
				}

		return {"unique": True}

	def _requires_customer_nif(self, doc):
		"""
		✅ MANTIDA: Verifica se NIF do cliente é obrigatório
		"""
		# NIF obrigatório para faturas acima de €1000 ou se cliente é empresa
		if hasattr(doc, 'grand_total') and flt(doc.grand_total) > 1000:
			return True

		if hasattr(doc, 'customer') and doc.customer:
			customer_doc = frappe.get_doc("Customer", doc.customer)
			if customer_doc.customer_type == "Company":
				return True

		return False

	def _extract_document_number(self, document_name):
		"""
		✅ MANTIDA: Extrai número do documento
		"""
		if not document_name:
			return 0

		patterns = [r'\.(\d+)$', r'-(\d+)$', r'(\d+)$']

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return cint(match.group(1))

		return 0

	def _log_validation_results(self, doc, results):
		"""
		✅ MANTIDA: Registra resultados da validação
		"""
		try:
			if results:
				frappe.logger().info(
					f"Validação do documento {doc.name}: {len(results)} resultados")

				for result in results:
					if result["type"] == "error":
						frappe.logger().error(
							f"Erro de validação em {doc.name}: {result['message']}")
					elif result["type"] == "warning":
						frappe.logger().warning(
							f"Aviso de validação em {doc.name}: {result['message']}")

		except Exception as e:
			frappe.log_error(f"Erro ao registrar resultados de validação: {str(e)}")

	def get_validation_summary(self, company=None, from_date=None, to_date=None):
		"""
		✅ ADAPTADO: Retorna resumo das validações realizadas (nova abordagem)
		"""
		try:
			summary = {
				"status": "success",
				"total_documents_validated": 0,
				"errors_found": 0,
				"warnings_found": 0,
				"naming_series_issues": 0,
				"atcud_issues": 0,
				"compliance_rate": 0
			}

			# ✅ ESTATÍSTICAS BASEADAS NA NOVA ABORDAGEM
			if company:
				# Contar documentos com naming_series portuguesa
				for doctype in self.supported_doctypes:
					try:
						count = frappe.db.count(doctype, {
							"company": company,
							"naming_series": ["like", "%####"]
						})
						summary["total_documents_validated"] += count
					except:
						continue

				# Contar documentos com ATCUD
				atcud_count = 0
				for doctype in self.supported_doctypes:
					try:
						count = frappe.db.count(doctype, {
							"company": company,
							"atcud_code": ["is", "set"]
						})
						atcud_count += count
					except:
						continue

				# Calcular taxa de compliance
				if summary["total_documents_validated"] > 0:
					summary["compliance_rate"] = round(
						(atcud_count / summary["total_documents_validated"]) * 100, 2
					)

			return summary

		except Exception as e:
			return {
				"status": "error",
				"message": str(e)
			}


# ========== INSTÂNCIA GLOBAL PARA HOOKS ==========

# ✅ INSTÂNCIA GLOBAL PARA USO EM HOOKS
document_validator = DocumentValidator()


# ========== FUNÇÕES GLOBAIS PARA HOOKS ==========

def validate_document_compliance(doc, method=None):
	"""
	✅ Função global para validação de compliance (nova abordagem)
	"""
	return document_validator.validate_document(doc, method)


def validate_naming_series_compliance(doc, method=None):
	"""
	✅ Função específica para validação de naming_series
	"""
	return document_validator.validate_naming_series_new_approach(doc)


def validate_atcud_compliance(doc, method=None):
	"""
	✅ Função específica para validação de ATCUD
	"""
	return document_validator.validate_atcud_new_approach(doc)


# ========== FUNÇÕES DE UTILIDADE ==========

@frappe.whitelist()
def get_validation_summary_api(company=None, from_date=None, to_date=None):
	"""
	✅ API para obter resumo de validações
	"""
	try:
		return document_validator.get_validation_summary(company, from_date, to_date)
	except Exception as e:
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def validate_nif_api(nif):
	"""
	✅ API para validar NIF
	"""
	try:
		return document_validator.validate_nif(nif)
	except Exception as e:
		frappe.log_error(f"Erro na validação de NIF: {str(e)}")
		return False


@frappe.whitelist()
def check_document_compliance(doctype, docname):
	"""
	✅ API para verificar compliance de documento específico
	"""
	try:
		doc = frappe.get_doc(doctype, docname)
		validator = DocumentValidator()

		# Executar validação sem bloquear
		results = []
		results.extend(validator.validate_naming_series_new_approach(doc))
		results.extend(validator.validate_atcud_new_approach(doc))

		errors = [r for r in results if r["type"] == "error"]
		warnings = [r for r in results if r["type"] == "warning"]

		return {
			"success": True,
			"compliant": len(errors) == 0,
			"errors": errors,
			"warnings": warnings,
			"total_issues": len(errors) + len(warnings)
		}

	except Exception as e:
		return {"success": False, "error": str(e)}
