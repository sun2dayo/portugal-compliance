import frappe
from frappe import _
import re
from datetime import datetime, date
from frappe.utils import getdate, get_datetime, flt, cint


class DocumentValidator:
	def __init__(self):
		self.supported_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'Payment Entry',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry'
		]
		self.validation_rules = self._load_validation_rules()

	def _load_validation_rules(self):
		"""
		Carrega regras de validação específicas para Portugal
		"""
		return {
			"nif_validation": True,
			"atcud_required": True,
			"series_required": True,
			"sequential_numbering": True,
			"tax_validation": True,
			"currency_validation": True,
			"date_validation": True
		}

	def validate_document(self, doc, method=None):
		"""
		Validação principal do documento para conformidade portuguesa
		"""
		try:
			# Verificar se validação é necessária
			if not self._should_validate(doc):
				return True

			validation_results = []

			# Executar todas as validações
			validation_results.extend(self.validate_company_compliance(doc))
			validation_results.extend(self.validate_document_series(doc))
			validation_results.extend(self.validate_atcud(doc))
			validation_results.extend(self.validate_customer_supplier_data(doc))
			validation_results.extend(self.validate_tax_information(doc))
			validation_results.extend(self.validate_currency_and_amounts(doc))
			validation_results.extend(self.validate_dates(doc))
			validation_results.extend(self.validate_sequential_numbering(doc))

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
		Verifica se o documento deve ser validado
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
		Valida configurações de compliance da empresa
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

	def validate_document_series(self, doc):
		"""
		Valida série do documento
		"""
		results = []

		try:
			# Verificar se tem série portuguesa
			if not hasattr(doc, 'portugal_series') or not doc.portugal_series:
				results.append({
					"type": "error",
					"field": "portugal_series",
					"message": _("Série portuguesa não está definida para este documento")
				})
				return results

			# Verificar se série existe e está comunicada
			series_doc = frappe.get_doc("Portugal Series Configuration", doc.portugal_series)

			if not series_doc.is_communicated:
				results.append({
					"type": "error",
					"field": "portugal_series",
					"message": _("Série {0} não foi comunicada à AT").format(
						series_doc.series_prefix)
				})

			# Verificar se tipo de documento corresponde
			if series_doc.document_type != doc.doctype:
				results.append({
					"type": "error",
					"field": "portugal_series",
					"message": _("Série {0} não é válida para documentos do tipo {1}").format(
						series_doc.series_prefix, doc.doctype
					)
				})

			# Verificar se empresa corresponde
			if series_doc.company != doc.company:
				results.append({
					"type": "error",
					"field": "portugal_series",
					"message": _("Série {0} não pertence à empresa {1}").format(
						series_doc.series_prefix, doc.company
					)
				})

		except Exception as e:
			results.append({
				"type": "error",
				"field": "portugal_series",
				"message": _("Erro ao validar série do documento: {0}").format(str(e))
			})

		return results

	def validate_atcud(self, doc):
		"""
		Valida ATCUD do documento
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

				# Validar formato do ATCUD
				if not self.validate_atcud_format(doc.atcud_code):
					results.append({
						"type": "error",
						"field": "atcud_code",
						"message": _("Formato do ATCUD é inválido: {0}").format(doc.atcud_code)
					})

				# Verificar se ATCUD corresponde ao tipo de documento
				prefix_validation = self.validate_atcud_prefix(doc.atcud_code, doc.doctype)
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

	def validate_customer_supplier_data(self, doc):
		"""
		Valida dados de clientes/fornecedores
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
		Valida informações de impostos
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
		Valida moeda e valores
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
		Valida datas do documento
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

	def validate_sequential_numbering(self, doc):
		"""
		Valida numeração sequencial
		"""
		results = []

		try:
			if not hasattr(doc, 'portugal_series') or not doc.portugal_series:
				return results

			# Obter configuração da série
			series_doc = frappe.get_doc("Portugal Series Configuration", doc.portugal_series)

			# Extrair número do documento
			doc_number = self._extract_document_number(doc.name)

			# Verificar se número está dentro da sequência esperada
			if doc_number < series_doc.current_sequence - 100:  # Tolerância de 100
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
		Valida NIF português
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

	def validate_atcud_format(self, atcud):
		"""
		Valida formato do ATCUD
		"""
		if not atcud:
			return False

		pattern = r"^[A-Z]{2,4}-ATCUD:[A-Z0-9]{8,}-\d{8}$"
		return bool(re.match(pattern, atcud.strip()))

	def validate_atcud_prefix(self, atcud, doctype):
		"""
		Valida se prefixo do ATCUD corresponde ao tipo de documento
		"""
		if not atcud:
			return {"valid": False, "message": "ATCUD não fornecido"}

		prefix = atcud.split('-')[0]

		expected_prefixes = {
			"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
			"Purchase Invoice": ["FC", "FT"],
			"Payment Entry": ["RC", "RB"],
			"Delivery Note": ["GT", "GR"],
			"Purchase Receipt": ["GR", "GT"],
			"Journal Entry": ["JE"]
		}

		valid_prefixes = expected_prefixes.get(doctype, [])

		if valid_prefixes and prefix not in valid_prefixes:
			return {
				"valid": False,
				"message": _(
					"Prefixo ATCUD '{0}' não é válido para {1}. Prefixos válidos: {2}").format(
					prefix, doctype, ", ".join(valid_prefixes)
				)
			}

		return {"valid": True}

	def check_atcud_uniqueness(self, atcud, current_doc_name):
		"""
		Verifica unicidade do ATCUD
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
		Verifica se NIF do cliente é obrigatório
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
		Extrai número do documento
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
		Registra resultados da validação
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
		Retorna resumo das validações realizadas
		"""
		try:
			# Esta função pode ser expandida para incluir estatísticas
			# de validações realizadas, erros encontrados, etc.
			return {
				"status": "success",
				"message": "Funcionalidade de resumo será implementada"
			}

		except Exception as e:
			return {
				"status": "error",
				"message": str(e)
			}
