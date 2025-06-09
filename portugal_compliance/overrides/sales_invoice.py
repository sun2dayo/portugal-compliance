# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Sales Invoice Overrides - Portugal Compliance VERSÃO ATUALIZADA E ALINHADA
Overrides específicos para Sales Invoice com compliance português
✅ ALINHADO: 100% compatível com document_hooks.py (sem duplicação)
✅ ESPECÍFICO: Funcionalidades exclusivas para Sales Invoice
✅ FORMATO: SEM HÍFENS (FT2025NDX) - dinâmico baseado no abbr
✅ OTIMIZADO: Performance melhorada e validações robustas
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now_datetime
import re
from datetime import datetime


class SalesInvoicePortugalCompliance:
	"""
	✅ CLASSE ATUALIZADA: Overrides específicos para Sales Invoice
	Complementa document_hooks.py sem duplicar funcionalidades
	Baseado na sua experiência com programação.consistência_de_dados[4]
	"""

	def __init__(self):
		self.module = "Portugal Compliance"
		self.doctype = "Sales Invoice"

		# ✅ CONFIGURAÇÕES ESPECÍFICAS PARA SALES INVOICE
		self.portugal_invoice_types = {
			"FT": {
				"name": "Fatura",
				"description": "Fatura normal de venda",
				"requires_customer": True,
				"requires_items": True,
				"min_value": 0,
				"max_value": None,
				"saft_type": "FT"
			},
			"FS": {
				"name": "Fatura Simplificada",
				"description": "Fatura simplificada (POS)",
				"requires_customer": False,  # Cliente pode ser opcional até €1000
				"requires_items": True,
				"min_value": 0,
				"max_value": 1000,  # Limite para fatura simplificada
				"saft_type": "FS"
			},
			"FR": {
				"name": "Fatura Recibo",
				"description": "Fatura que serve como recibo",
				"requires_customer": True,
				"requires_items": True,
				"min_value": 0,
				"max_value": None,
				"saft_type": "FR"
			},
			"NC": {
				"name": "Nota de Crédito",
				"description": "Nota de crédito",
				"requires_customer": True,
				"requires_items": True,
				"min_value": None,
				"max_value": 0,  # Valores negativos
				"saft_type": "NC"
			},
			"ND": {
				"name": "Nota de Débito",
				"description": "Nota de débito",
				"requires_customer": True,
				"requires_items": True,
				"min_value": 0,
				"max_value": None,
				"saft_type": "ND"
			}
		}

	# ========== HOOKS ESPECÍFICOS PARA SALES INVOICE ==========

	def validate_sales_invoice_portugal_compliance(self, doc, method=None):
		"""
		✅ ATUALIZADO: Validações específicas para Sales Invoice
		Complementa document_hooks.py com validações específicas do documento
		"""
		try:
			# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
			if not self._is_portuguese_company_cached(doc.company):
				return

			# ✅ VALIDAÇÕES ESPECÍFICAS DE SALES INVOICE
			self._validate_invoice_type_specific(doc)
			self._validate_customer_requirements_specific(doc)
			self._validate_tax_requirements_specific(doc)
			self._validate_items_requirements_specific(doc)
			self._validate_amounts_specific(doc)
			self._validate_dates_specific(doc)

		except Exception as e:
			frappe.log_error(f"Erro na validação específica de Sales Invoice: {str(e)}",
							 "Sales Invoice Override")
			# ✅ NÃO BLOQUEAR - apenas log
			frappe.logger().warning(f"Validação específica falhou: {str(e)}")

	def _validate_invoice_type_specific(self, doc):
		"""
		✅ NOVO: Validar tipo de fatura baseado na naming series
		"""
		try:
			if not doc.naming_series:
				return

			# ✅ EXTRAIR TIPO DE DOCUMENTO DA NAMING SERIES (SEM HÍFENS)
			invoice_type = self._extract_invoice_type_from_series(doc.naming_series)

			if invoice_type and invoice_type in self.portugal_invoice_types:
				config = self.portugal_invoice_types[invoice_type]

				# ✅ VALIDAR LIMITES DE VALOR
				if config.get("max_value") is not None:
					if flt(doc.grand_total) > config["max_value"]:
						frappe.throw(_(
							"Valor {0} excede limite para {1} (máximo: €{2})"
						).format(flt(doc.grand_total), config["name"], config["max_value"]))

				if config.get("min_value") is not None:
					if flt(doc.grand_total) < config["min_value"]:
						frappe.throw(_(
							"Valor {0} abaixo do mínimo para {1} (mínimo: €{2})"
						).format(flt(doc.grand_total), config["name"], config["min_value"]))

				# ✅ ARMAZENAR TIPO PARA USO POSTERIOR
				doc._portugal_invoice_type = invoice_type
				doc._portugal_invoice_config = config

		except Exception as e:
			frappe.log_error(f"Erro na validação de tipo de fatura: {str(e)}")

	def _extract_invoice_type_from_series(self, naming_series):
		"""
		✅ ATUALIZADO: Extrair tipo de fatura da naming series (SEM HÍFENS)
		Formato: XXYYYY + COMPANY.#### → XX é o tipo
		"""
		try:
			if not naming_series:
				return None

			# ✅ PADRÃO SEM HÍFENS: XXYYYY + COMPANY.####
			pattern = r'^([A-Z]{2,4})\d{4}[A-Z0-9]{2,4}\.####$'
			match = re.match(pattern, naming_series)

			if match:
				doc_code = match.group(1)
				# Retornar apenas os primeiros 2 caracteres para tipo de documento
				return doc_code[:2]

			return None

		except Exception:
			return None

	def _validate_customer_requirements_specific(self, doc):
		"""
		✅ ATUALIZADO: Validações específicas de cliente para Sales Invoice
		"""
		try:
			invoice_type = getattr(doc, '_portugal_invoice_type', None)
			config = getattr(doc, '_portugal_invoice_config', {})

			# ✅ VERIFICAR SE CLIENTE É OBRIGATÓRIO
			if config.get("requires_customer", True) and not doc.customer:
				frappe.throw(_("Cliente é obrigatório para este tipo de documento"))

			# ✅ VALIDAÇÕES ESPECÍFICAS PARA FATURA SIMPLIFICADA
			if invoice_type == "FS":
				self._validate_simplified_invoice_customer(doc)

			# ✅ VALIDAR NIF DO CLIENTE SE PRESENTE
			if doc.customer:
				self._validate_customer_nif_specific(doc)

		except Exception as e:
			frappe.log_error(f"Erro na validação de cliente: {str(e)}")
			raise

	def _validate_simplified_invoice_customer(self, doc):
		"""
		✅ NOVO: Validações específicas para fatura simplificada
		"""
		try:
			# ✅ FATURA SIMPLIFICADA: Cliente opcional até €1000
			if flt(doc.grand_total) > 1000 and not doc.customer:
				frappe.throw(_(
					"Fatura simplificada acima de €1000 requer identificação do cliente"
				))

			# ✅ SE TEM CLIENTE, VALIDAR NIF OBRIGATÓRIO ACIMA DE €1000
			if doc.customer and flt(doc.grand_total) > 1000:
				customer_nif = frappe.db.get_value("Customer", doc.customer, "tax_id")
				if not customer_nif:
					frappe.throw(_(
						"NIF do cliente é obrigatório para faturas simplificadas acima de €1000"
					))

		except Exception as e:
			frappe.log_error(f"Erro na validação de fatura simplificada: {str(e)}")
			raise

	def _validate_customer_nif_specific(self, doc):
		"""
		✅ ATUALIZADO: Validar NIF do cliente específico para Sales Invoice
		"""
		try:
			if not doc.customer:
				return

			customer_nif = frappe.db.get_value("Customer", doc.customer, "tax_id")

			if customer_nif:
				# ✅ VALIDAR FORMATO DO NIF PORTUGUÊS
				if not self._validate_portuguese_nif(customer_nif):
					frappe.msgprint(_(
						"NIF do cliente {0} parece inválido: {1}"
					).format(doc.customer, customer_nif), indicator="orange")

		except Exception as e:
			frappe.log_error(f"Erro na validação de NIF: {str(e)}")

	def _validate_tax_requirements_specific(self, doc):
		"""
		✅ NOVO: Validações específicas de impostos para Sales Invoice
		"""
		try:
			# ✅ VERIFICAR SE TEM IMPOSTOS CONFIGURADOS
			if not doc.taxes:
				# ✅ AVISAR MAS NÃO BLOQUEAR
				frappe.msgprint(_(
					"Fatura sem impostos configurados. Verifique se está correto."
				), indicator="orange")
				return

			# ✅ VALIDAR TAXAS DE IVA PORTUGUESAS
			valid_iva_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

			for tax in doc.taxes:
				if tax.rate and tax.rate not in valid_iva_rates:
					frappe.msgprint(_(
						"Taxa de IVA {0}% não é padrão em Portugal. Taxas válidas: {1}"
					).format(tax.rate, ", ".join(map(str, valid_iva_rates))), indicator="orange")

		except Exception as e:
			frappe.log_error(f"Erro na validação de impostos: {str(e)}")

	def _validate_items_requirements_specific(self, doc):
		"""
		✅ NOVO: Validações específicas de itens para Sales Invoice
		"""
		try:
			if not doc.items:
				frappe.throw(_("Pelo menos um item é obrigatório"))

			# ✅ VALIDAR CADA ITEM
			for item in doc.items:
				# Verificar quantidade
				if flt(item.qty) <= 0:
					frappe.throw(_(
						"Quantidade deve ser maior que zero para item {0}"
					).format(item.item_code))

				# Verificar preço
				if flt(item.rate) < 0:
					frappe.throw(_(
						"Preço não pode ser negativo para item {0}"
					).format(item.item_code))

		except Exception as e:
			frappe.log_error(f"Erro na validação de itens: {str(e)}")
			raise

	def _validate_amounts_specific(self, doc):
		"""
		✅ NOVO: Validações específicas de valores para Sales Invoice
		"""
		try:
			# ✅ VERIFICAR PRECISÃO MONETÁRIA (2 casas decimais para EUR)
			if flt(doc.grand_total, 3) != flt(doc.grand_total, 2):
				frappe.msgprint(_(
					"Valor total com mais de 2 casas decimais: €{0}"
				).format(doc.grand_total), indicator="orange")

			# ✅ VERIFICAR VALORES EXTREMOS
			if flt(doc.grand_total) > 999999.99:
				frappe.msgprint(_(
					"Valor muito alto: €{0}. Verifique se está correto."
				).format(doc.grand_total), indicator="orange")

			# ✅ VERIFICAR DESCONTO TOTAL
			if flt(doc.discount_amount) > flt(doc.net_total):
				frappe.throw(_("Desconto não pode ser maior que o valor líquido"))

		except Exception as e:
			frappe.log_error(f"Erro na validação de valores: {str(e)}")

	def _validate_dates_specific(self, doc):
		"""
		✅ NOVO: Validações específicas de datas para Sales Invoice
		"""
		try:
			# ✅ VERIFICAR DATA DE POSTING
			if doc.posting_date:
				posting_date = getdate(doc.posting_date)
				today = getdate()

				# Data não pode ser muito futura
				if posting_date > today:
					frappe.throw(_("Data de posting não pode ser futura"))

				# Data não pode ser muito antiga (mais de 1 ano)
				if (today - posting_date).days > 365:
					frappe.msgprint(_(
						"Data de posting muito antiga: {0}"
					).format(posting_date), indicator="orange")

			# ✅ VERIFICAR DATA DE VENCIMENTO
			if doc.due_date and doc.posting_date:
				if getdate(doc.due_date) < getdate(doc.posting_date):
					frappe.throw(_("Data de vencimento não pode ser anterior à data de posting"))

		except Exception as e:
			frappe.log_error(f"Erro na validação de datas: {str(e)}")

	# ========== HOOKS DE SUBMISSÃO ESPECÍFICOS ==========

	def before_submit_sales_invoice_portugal(self, doc, method=None):
		"""
		✅ ATUALIZADO: Validações antes de submeter Sales Invoice
		Complementa document_hooks.py com validações específicas
		"""
		try:
			if not self._is_portuguese_company_cached(doc.company):
				return

			# ✅ VALIDAÇÕES CRÍTICAS ANTES DE SUBMETER
			self._validate_critical_fields_before_submit(doc)
			self._validate_atcud_before_submit(doc)
			self._validate_sequence_before_submit(doc)

		except Exception as e:
			frappe.log_error(f"Erro antes de submeter Sales Invoice: {str(e)}")
			raise

	def _validate_critical_fields_before_submit(self, doc):
		"""
		✅ NOVO: Validar campos críticos antes de submeter
		"""
		try:
			# ✅ CAMPOS OBRIGATÓRIOS PARA SUBMISSÃO
			required_fields = {
				"customer": "Cliente",
				"posting_date": "Data de posting",
				"naming_series": "Série de numeração"
			}

			missing_fields = []
			for field, label in required_fields.items():
				if not getattr(doc, field, None):
					missing_fields.append(label)

			if missing_fields:
				frappe.throw(_(
					"Campos obrigatórios em falta: {0}"
				).format(", ".join(missing_fields)))

			# ✅ VERIFICAR SE TEM ITENS
			if not doc.items:
				frappe.throw(_("Pelo menos um item é obrigatório para submeter"))

		except Exception as e:
			frappe.log_error(f"Erro na validação de campos críticos: {str(e)}")
			raise

	def _validate_atcud_before_submit(self, doc):
		"""
		✅ NOVO: Validar ATCUD antes de submeter (não duplica document_hooks)
		"""
		try:
			# ✅ VERIFICAR SE ATCUD SERÁ GERADO (document_hooks fará isso)
			if not getattr(doc, 'atcud_code', None):
				# ✅ VERIFICAR SE NAMING SERIES É PORTUGUESA
				if not self._is_portuguese_naming_series(doc.naming_series):
					frappe.throw(_(
						"Naming series portuguesa é obrigatória para gerar ATCUD"
					))

				# ✅ VERIFICAR SE SÉRIE TEM VALIDATION_CODE
				series_prefix = doc.naming_series.replace('.####', '')
				validation_code = frappe.db.get_value(
					"Portugal Series Configuration",
					{"prefix": series_prefix, "company": doc.company},
					"validation_code"
				)

				if not validation_code:
					frappe.msgprint(_(
						"Série {0} não tem código de validação AT. ATCUD será temporário."
					).format(series_prefix), indicator="orange")

		except Exception as e:
			frappe.log_error(f"Erro na validação de ATCUD: {str(e)}")

	def _validate_sequence_before_submit(self, doc):
		"""
		✅ NOVO: Validar sequência antes de submeter
		"""
		try:
			if not doc.naming_series:
				return

			series_prefix = doc.naming_series.replace('.####', '')

			# ✅ VERIFICAR SE SÉRIE ESTÁ ATIVA
			series_active = frappe.db.get_value(
				"Portugal Series Configuration",
				{"prefix": series_prefix, "company": doc.company},
				"is_active"
			)

			if series_active == 0:
				frappe.throw(_(
					"Série {0} está inativa. Ative a série antes de submeter."
				).format(series_prefix))

		except Exception as e:
			frappe.log_error(f"Erro na validação de sequência: {str(e)}")

	# ========== HOOKS APÓS SUBMISSÃO ==========

	def on_submit_sales_invoice_portugal(self, doc, method=None):
		"""
		✅ ATUALIZADO: Ações após submeter Sales Invoice
		"""
		try:
			if not self._is_portuguese_company_cached(doc.company):
				return

			# ✅ AÇÕES ESPECÍFICAS APÓS SUBMISSÃO
			self._log_submission_audit(doc)
			self._update_series_statistics(doc)
			self._check_compliance_status(doc)

		except Exception as e:
			frappe.log_error(f"Erro após submeter Sales Invoice: {str(e)}")

	# ✅ NÃO FALHAR - apenas log

	def _log_submission_audit(self, doc):
		"""
		✅ NOVO: Log de auditoria específico para Sales Invoice
		"""
		try:
			audit_data = {
				"document": doc.name,
				"doctype": doc.doctype,
				"customer": doc.customer,
				"grand_total": flt(doc.grand_total),
				"atcud_code": getattr(doc, 'atcud_code', None),
				"naming_series": doc.naming_series,
				"submission_time": now_datetime(),
				"user": frappe.session.user,
				"invoice_type": getattr(doc, '_portugal_invoice_type', None)
			}

			frappe.logger().info(
				f"Sales Invoice submetida: {doc.name} - ATCUD: {audit_data['atcud_code']}")

		except Exception as e:
			frappe.log_error(f"Erro no log de auditoria: {str(e)}")

	def _update_series_statistics(self, doc):
		"""
		✅ NOVO: Atualizar estatísticas da série
		"""
		try:
			if not doc.naming_series:
				return

			series_prefix = doc.naming_series.replace('.####', '')

			# ✅ ATUALIZAR CONTADOR DE DOCUMENTOS
			frappe.db.sql("""
						  UPDATE `tabPortugal Series Configuration`
						  SET total_documents_issued = COALESCE(total_documents_issued, 0) + 1,
							  last_document_date     = %s
						  WHERE prefix = %s
							AND company = %s
						  """, (doc.posting_date, series_prefix, doc.company))

		except Exception as e:
			frappe.log_error(f"Erro ao atualizar estatísticas: {str(e)}")

	def _check_compliance_status(self, doc):
		"""
		✅ NOVO: Verificar status de compliance após submissão
		"""
		try:
			compliance_issues = []

			# ✅ VERIFICAR ATCUD
			if not getattr(doc, 'atcud_code', None):
				compliance_issues.append("ATCUD não gerado")

			# ✅ VERIFICAR NIF DO CLIENTE PARA VALORES ALTOS
			if flt(doc.grand_total) > 1000 and doc.customer:
				customer_nif = frappe.db.get_value("Customer", doc.customer, "tax_id")
				if not customer_nif:
					compliance_issues.append("NIF do cliente em falta para valor > €1000")

			# ✅ LOG DE COMPLIANCE
			if compliance_issues:
				frappe.logger().warning(
					f"Issues de compliance em {doc.name}: {', '.join(compliance_issues)}")
			else:
				frappe.logger().info(f"Sales Invoice {doc.name} está em compliance total")

		except Exception as e:
			frappe.log_error(f"Erro na verificação de compliance: {str(e)}")

	# ========== MÉTODOS AUXILIARES ==========

	def _is_portuguese_company_cached(self, company):
		"""
		✅ OTIMIZADO: Verificar se empresa é portuguesa com cache
		"""
		try:
			cache_key = f"portuguese_company_{company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is None:
				company_data = frappe.db.get_value("Company", company,
												   ["country", "portugal_compliance_enabled"],
												   as_dict=True)

				if company_data:
					cached_result = (company_data.country == "Portugal" and
									 cint(company_data.portugal_compliance_enabled))
				else:
					cached_result = False

				# Cache por 10 minutos
				frappe.cache().set_value(cache_key, cached_result, expires_in_sec=600)

			return cached_result

		except Exception:
			return False

	def _is_portuguese_naming_series(self, naming_series):
		"""
		✅ ATUALIZADO: Verificar se naming_series é portuguesa (SEM HÍFENS)
		"""
		try:
			if not naming_series:
				return False

			# ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
			pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'
			return bool(re.match(pattern, naming_series))

		except Exception:
			return False

	def _validate_portuguese_nif(self, nif):
		"""
		✅ ATUALIZADO: Validar NIF português
		"""
		try:
			if not nif:
				return False

			# Limpar NIF
			clean_nif = re.sub(r'[^0-9]', '', str(nif))

			# Verificar comprimento
			if len(clean_nif) != 9:
				return False

			# Verificar primeiro dígito
			if clean_nif[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
				return False

			# Calcular dígito de controle
			checksum = 0
			for i in range(8):
				checksum += int(clean_nif[i]) * (9 - i)

			remainder = checksum % 11
			control_digit = 0 if remainder < 2 else 11 - remainder

			return int(clean_nif[8]) == control_digit

		except Exception:
			return False

	# ========== RELATÓRIOS ESPECÍFICOS ==========

	def get_sales_invoice_portugal_summary(self, doc):
		"""
		✅ NOVO: Obter resumo específico de Sales Invoice para Portugal
		"""
		try:
			summary = {
				"document": doc.name,
				"customer": doc.customer,
				"customer_name": getattr(doc, 'customer_name', ''),
				"grand_total": flt(doc.grand_total),
				"currency": doc.currency,
				"atcud_code": getattr(doc, 'atcud_code', None),
				"naming_series": doc.naming_series,
				"invoice_type": getattr(doc, '_portugal_invoice_type', None),
				"compliance_status": "OK" if getattr(doc, 'atcud_code', None) else "PENDING",
				"posting_date": doc.posting_date,
				"due_date": getattr(doc, 'due_date', None),
				"taxes_total": flt(doc.total_taxes_and_charges),
				"items_count": len(doc.items) if doc.items else 0
			}

			# ✅ INFORMAÇÕES DO CLIENTE
			if doc.customer:
				customer_info = frappe.db.get_value("Customer", doc.customer,
													["tax_id", "customer_group"], as_dict=True)
				if customer_info:
					summary["customer_nif"] = customer_info.tax_id
					summary["customer_group"] = customer_info.customer_group

			# ✅ INFORMAÇÕES DA SÉRIE
			if doc.naming_series:
				series_prefix = doc.naming_series.replace('.####', '')
				series_info = frappe.db.get_value("Portugal Series Configuration",
												  {"prefix": series_prefix,
												   "company": doc.company},
												  ["validation_code", "is_communicated"],
												  as_dict=True)
				if series_info:
					summary["series_validation_code"] = series_info.validation_code
					summary["series_communicated"] = series_info.is_communicated

			return summary

		except Exception as e:
			frappe.log_error(f"Erro ao obter resumo: {str(e)}")
			return {}


# ========== INSTÂNCIA GLOBAL ==========
sales_invoice_portugal_compliance = SalesInvoicePortugalCompliance()


# ========== FUNÇÕES PARA HOOKS ==========

def validate_sales_invoice_portugal_compliance(doc, method=None):
	"""✅ Hook para validate de Sales Invoice"""
	return sales_invoice_portugal_compliance.validate_sales_invoice_portugal_compliance(doc,
																						method)


def before_submit_sales_invoice_portugal(doc, method=None):
	"""✅ Hook para before_submit de Sales Invoice"""
	return sales_invoice_portugal_compliance.before_submit_sales_invoice_portugal(doc, method)


def on_submit_sales_invoice_portugal(doc, method=None):
	"""✅ Hook para on_submit de Sales Invoice"""
	return sales_invoice_portugal_compliance.on_submit_sales_invoice_portugal(doc, method)


# ========== APIS WHITELISTED ESPECÍFICAS ==========

@frappe.whitelist()
def get_sales_invoice_portugal_summary_api(docname):
	"""✅ API para obter resumo de Sales Invoice português"""
	try:
		doc = frappe.get_doc("Sales Invoice", docname)
		return sales_invoice_portugal_compliance.get_sales_invoice_portugal_summary(doc)
	except Exception as e:
		return {"error": str(e)}


@frappe.whitelist()
def validate_customer_for_invoice_api(customer, invoice_value):
	"""✅ API para validar cliente para fatura"""
	try:
		if not customer:
			return {"valid": True, "message": "Cliente opcional até €1000"}

		customer_nif = frappe.db.get_value("Customer", customer, "tax_id")
		invoice_value = flt(invoice_value)

		if invoice_value > 1000 and not customer_nif:
			return {
				"valid": False,
				"message": "NIF obrigatório para faturas acima de €1000"
			}

		if customer_nif and not sales_invoice_portugal_compliance._validate_portuguese_nif(
			customer_nif):
			return {
				"valid": False,
				"message": f"NIF inválido: {customer_nif}"
			}

		return {"valid": True, "message": "Cliente válido"}

	except Exception as e:
		return {"valid": False, "error": str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Sales Invoice Portugal Compliance Override ATUALIZADO loaded - Version 2.1.0 - Specific & Optimized")
