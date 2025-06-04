# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
import re
from datetime import datetime, timedelta
from frappe.utils import now, today, getdate, cint


class CustomSalesInvoice(SalesInvoice):
	"""
	Extensão da Sales Invoice para compliance português - NOVA ABORDAGEM COM NAMING_SERIES
	Integração completa com Portugal Compliance usando apenas campo nativo
	"""

	def validate(self):
		"""Override do método validate com tratamento de erros robusto"""
		try:
			super().validate()
			if self.is_portugal_compliance_enabled():
				self.validate_portugal_compliance()
		except frappe.ValidationError:
			# Re-raise ValidationError (são intencionais)
			raise
		except Exception as e:
			frappe.log_error(f"Erro crítico no validate da Sales Invoice {self.name}: {str(e)}")
			frappe.throw(_("Erro inesperado na validação do documento: {0}").format(str(e)))

	def before_save(self):
		"""Override do método before_save com tratamento de erros robusto"""
		try:
			super().before_save()
			if self.is_portugal_compliance_enabled():
				self.auto_configure_portugal_compliance()
		except Exception as e:
			frappe.log_error(f"Erro no before_save da Sales Invoice {self.name}: {str(e)}")
			# Não quebrar fluxo - before_save pode ser sensível
			frappe.logger().warning(f"⚠️ Erro na auto-configuração Portugal Compliance: {str(e)}")

	def before_submit(self):
		"""Override do método before_submit com tratamento de erros robusto"""
		try:
			super().before_submit()
			if self.is_portugal_compliance_enabled():
				self.ensure_portugal_compliance_before_submit()
		except frappe.ValidationError:
			# Re-raise ValidationError (são intencionais)
			raise
		except Exception as e:
			frappe.log_error(
				f"Erro crítico no before_submit da Sales Invoice {self.name}: {str(e)}")
			frappe.throw(
				_("Erro na validação de compliance antes da submissão: {0}").format(str(e)))

	def on_submit(self):
		"""Override do método on_submit com tratamento de erros robusto"""
		try:
			super().on_submit()
			if self.is_portugal_compliance_enabled():
				self.update_portugal_compliance_data()
		except Exception as e:
			frappe.log_error(f"Erro no on_submit da Sales Invoice {self.name}: {str(e)}")
			# Não quebrar fluxo - documento já foi submetido
			frappe.logger().warning(f"⚠️ Erro na atualização de dados de compliance: {str(e)}")

	def validate_portugal_compliance(self):
		"""Validações específicas para Portugal - VERSÃO CERTIFICADA COM TRATAMENTO DE ERROS"""
		try:
			# ✅ VERIFICAÇÃO INICIAL - Sair silenciosamente se não for empresa portuguesa
			if not self.is_portugal_compliance_enabled():
				return

			frappe.logger().info(
				f"🇵🇹 Iniciando validações Portugal Compliance para {self.name or 'NEW'}")

			# ✅ BLOCO 1: Validações de Cliente (Críticas)
			try:
				self.validate_customer_nif()
			except Exception as e:
				frappe.log_error(f"Erro na validação NIF do cliente: {str(e)}")
				frappe.throw(_("Erro na validação do NIF do cliente: {0}").format(str(e)))

			# ✅ BLOCO 2: Validações de Impostos (Críticas)
			try:
				self.validate_tax_information()
			except Exception as e:
				frappe.log_error(f"Erro na validação de impostos: {str(e)}")
				frappe.throw(_("Erro na validação de impostos: {0}").format(str(e)))

			# ✅ BLOCO 3: Validações de Tipo de Fatura (Críticas)
			try:
				self.validate_invoice_type()
			except Exception as e:
				frappe.log_error(f"Erro na validação do tipo de fatura: {str(e)}")
				frappe.throw(_("Erro na validação do tipo de fatura: {0}").format(str(e)))

			# ✅ BLOCO 4: Validações de Configuração de Série (Críticas)
			try:
				self.ensure_series_configuration()
			except Exception as e:
				frappe.log_error(f"Erro na configuração de série: {str(e)}")
				frappe.throw(_("Erro na configuração de série: {0}").format(str(e)))

			# ✅ BLOCO 5: Validações NAMING_SERIES (Críticas - Nova Abordagem)
			try:
				self.validate_naming_series_field()
			except Exception as e:
				frappe.log_error(f"Erro na validação naming_series: {str(e)}")
				frappe.throw(_("Erro na validação da série portuguesa: {0}").format(str(e)))

			# ✅ BLOCO 6: Validações ATCUD (Críticas se série comunicada)
			try:
				self.validate_atcud_format()
			except Exception as e:
				frappe.log_error(f"Erro na validação ATCUD: {str(e)}")
				# ⚠️ ATCUD pode ser gerado automaticamente - não quebrar fluxo
				frappe.msgprint(
					_("Aviso ATCUD: {0}. ATCUD será gerado automaticamente.").format(str(e)),
					indicator="orange",
					alert=True
				)

			# ✅ BLOCO 7: Validações de Sequência (Não críticas)
			try:
				self.validate_invoice_sequence()
			except Exception as e:
				frappe.log_error(f"Erro na validação de sequência: {str(e)}")
				# ⚠️ Sequência é informativa - não quebrar fluxo
				frappe.msgprint(
					_("Aviso de sequência: {0}").format(str(e)),
					indicator="orange",
					alert=True
				)

			# ✅ BLOCO 8: Validações Adicionais (Não críticas)
			try:
				self.validate_additional_portugal_requirements()
			except Exception as e:
				frappe.log_error(f"Erro em validações adicionais: {str(e)}")
				# ⚠️ Validações adicionais são opcionais
				frappe.logger().warning(f"⚠️ Validações adicionais falharam: {str(e)}")

			# ✅ SUCESSO: Log de conclusão
			frappe.logger().info(
				f"✅ Validações Portugal Compliance concluídas com sucesso para {self.name or 'NEW'}")

		except frappe.ValidationError:
			# ✅ Re-raise ValidationError (são intencionais)
			raise

		except Exception as e:
			# ✅ ERRO CRÍTICO INESPERADO
			error_msg = f"Erro crítico nas validações Portugal Compliance: {str(e)}"
			frappe.log_error(error_msg)
			frappe.throw(_(error_msg))

	def validate_additional_portugal_requirements(self):
		"""Validações adicionais específicas para Portugal - NÃO CRÍTICAS"""
		try:
			# ✅ VALIDAR MOEDA EUR (Recomendado)
			if self.currency and self.currency != 'EUR':
				frappe.msgprint(
					_("Recomenda-se usar moeda EUR para faturas em Portugal"),
					indicator="orange",
					alert=True
				)

			# ✅ VALIDAR DATA DE VENCIMENTO (Recomendado)
			if not self.due_date:
				frappe.msgprint(
					_("Data de vencimento é recomendada para faturas portuguesas"),
					indicator="orange",
					alert=True
				)

			# ✅ VALIDAR TERMOS DE PAGAMENTO (Informativo)
			if not self.payment_terms_template:
				frappe.logger().info("ℹ️ Termos de pagamento não definidos")

			# ✅ VALIDAR ENDEREÇO COMPLETO (Recomendado)
			if self.customer_address:
				self.validate_customer_address_completeness()

		except Exception as e:
			# ✅ NÃO QUEBRAR FLUXO - apenas logar
			frappe.logger().warning(f"⚠️ Validações adicionais Portugal: {str(e)}")

	def validate_customer_address_completeness(self):
		"""Validar completude do endereço do cliente"""
		try:
			if not self.customer_address:
				return

			address_doc = frappe.get_doc("Address", self.customer_address)

			missing_fields = []
			if not address_doc.address_line1:
				missing_fields.append("Linha de endereço 1")
			if not address_doc.city:
				missing_fields.append("Cidade")
			if not address_doc.pincode:
				missing_fields.append("Código postal")
			if not address_doc.country:
				missing_fields.append("País")

			if missing_fields:
				frappe.msgprint(
					_("Endereço incompleto. Campos em falta: {0}").format(
						", ".join(missing_fields)),
					indicator="orange",
					alert=True
				)

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação de endereço: {str(e)}")

	def validate_naming_series_field(self):
		"""Validar campo naming_series - VERSÃO CERTIFICADA PARA NOVA ABORDAGEM"""
		try:
			# ✅ VERIFICAR SE NAMING_SERIES ESTÁ DEFINIDA
			if not self.naming_series:
				frappe.throw(_("Naming series portuguesa é obrigatória para empresas portuguesas"))

			# ✅ VERIFICAR SE É SÉRIE PORTUGUESA VÁLIDA
			if not self.is_portuguese_naming_series():
				frappe.throw(_("Naming series selecionada não é uma série portuguesa válida"))

			# ✅ VERIFICAR SE SÉRIE ESTÁ COMUNICADA À AT
			if not self.is_naming_series_communicated():
				frappe.throw(_("Apenas séries comunicadas à AT podem ser usadas"))

			# ✅ VERIFICAR FORMATO DO PREFIXO
			prefix = self.get_series_prefix_from_naming_series()
			if not self.validate_prefix_format(prefix):
				frappe.throw(_("Formato do prefixo da série é inválido: {0}").format(prefix))

			frappe.logger().info(f"✅ Naming series validada: {self.naming_series}")

		except Exception as e:
			frappe.log_error(f"Erro na validação naming_series: {str(e)}")
			raise

	def validate_atcud_format(self):
		"""Validar formato ATCUD - VERSÃO CERTIFICADA"""
		try:
			# ✅ SE NÃO TEM ATCUD, VERIFICAR SE É OBRIGATÓRIO
			if not self.atcud_code:
				if self.is_naming_series_communicated():
					# ⚠️ ATCUD será gerado automaticamente - não quebrar
					frappe.logger().info(
						"ℹ️ ATCUD será gerado automaticamente para série comunicada")
					return
				else:
					# ✅ Série não comunicada - ATCUD não é obrigatório
					return

			# ✅ SE TEM ATCUD, VALIDAR FORMATO
			if not self.validate_atcud_code_format(self.atcud_code):
				frappe.throw(_("Formato ATCUD inválido: {0}").format(self.atcud_code))

			# ✅ VERIFICAR UNICIDADE DO ATCUD
			if not self.is_atcud_unique():
				frappe.throw(_("ATCUD '{0}' já está sendo usado").format(self.atcud_code))

			frappe.logger().info(f"✅ ATCUD validado: {self.atcud_code}")

		except Exception as e:
			frappe.log_error(f"Erro na validação ATCUD: {str(e)}")
			raise

	def validate_invoice_sequence(self):
		"""Validar sequência da fatura - NÃO CRÍTICA"""
		try:
			if not self.name or self.name == 'new':
				return  # Documento ainda não tem nome

			# ✅ EXTRAIR SEQUÊNCIA DO NOME
			sequence = self.extract_sequence_from_name()
			if sequence:
				# ✅ VERIFICAR SE SEQUÊNCIA ESTÁ DENTRO DO LIMITE
				if sequence > 99999999:
					frappe.msgprint(
						_("Sequência {0} próxima do limite legal (99.999.999)").format(sequence),
						indicator="orange",
						alert=True
					)

			frappe.logger().info(f"✅ Sequência validada: {sequence}")

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação de sequência: {str(e)}")

	# ✅ NÃO QUEBRAR FLUXO - sequência é informativa

	def extract_sequence_from_name(self):
		"""Extrair número sequencial do nome do documento"""
		try:
			if not self.name:
				return None

			# ✅ PADRÃO: FT-2025-NDX-000001
			parts = self.name.split('-')
			if len(parts) >= 2:
				last_part = parts[-1]
				if last_part.isdigit():
					return int(last_part)

			return None

		except Exception:
			return None

	def ensure_portugal_compliance_before_submit(self):
		"""Garante compliance antes da submissão - ATUALIZADA COM TRATAMENTO DE ERROS"""
		try:
			if not self.is_portugal_compliance_enabled():
				return

			frappe.logger().info(
				f"🔒 Verificando compliance antes da submissão: {self.name or 'NEW'}")

			# ✅ VALIDAÇÕES CRÍTICAS ANTES DA SUBMISSÃO
			critical_validations = [
				("ensure_atcud_code", "Geração de ATCUD"),
				("validate_document_series", "Validação de série"),
				("validate_fiscal_requirements", "Requisitos fiscais"),
				("validate_invoice_limits", "Limites de faturação")
			]

			for method_name, description in critical_validations:
				try:
					method = getattr(self, method_name)
					method()
					frappe.logger().info(f"✅ {description} - OK")
				except Exception as e:
					frappe.log_error(f"Erro em {description}: {str(e)}")
					frappe.throw(_("Erro em {0}: {1}").format(description, str(e)))

			# ✅ VALIDAÇÕES NÃO CRÍTICAS
			non_critical_validations = [
				("validate_qr_code_requirements", "Requisitos QR Code"),
				("validate_digital_signature_requirements", "Assinatura digital"),
				("ensure_naming_series_consistency", "Consistência naming series")
			]

			for method_name, description in non_critical_validations:
				try:
					method = getattr(self, method_name)
					method()
					frappe.logger().info(f"✅ {description} - OK")
				except Exception as e:
					frappe.log_error(f"Aviso em {description}: {str(e)}")
					frappe.msgprint(
						_("Aviso em {0}: {1}").format(description, str(e)),
						indicator="orange",
						alert=True
					)

			frappe.logger().info(f"🔒 Compliance verificado com sucesso para {self.name or 'NEW'}")

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro crítico na verificação de compliance: {str(e)}")
			frappe.throw(_("Erro na verificação de compliance: {0}").format(str(e)))

	def update_portugal_compliance_data(self):
		"""Atualiza dados de compliance após submissão - ATUALIZADA COM TRATAMENTO DE ERROS"""
		try:
			if not self.is_portugal_compliance_enabled():
				return

			frappe.logger().info(f"📊 Atualizando dados de compliance: {self.name}")

			# ✅ ATUALIZAÇÕES CRÍTICAS
			critical_updates = [
				("create_atcud_log", "Log ATCUD"),
				("update_series_sequence", "Sequência da série")
			]

			for method_name, description in critical_updates:
				try:
					method = getattr(self, method_name)
					method()
					frappe.logger().info(f"✅ {description} - Atualizado")
				except Exception as e:
					frappe.log_error(f"Erro em {description}: {str(e)}")
			# Não quebrar fluxo - documento já foi submetido

			# ✅ ATUALIZAÇÕES NÃO CRÍTICAS
			non_critical_updates = [
				("create_invoice_notification", "Notificações"),
				("update_series_statistics", "Estatísticas da série"),
				("create_compliance_audit_trail", "Trilha de auditoria"),
				("generate_qr_code_data", "Dados QR Code")
			]

			for method_name, description in non_critical_updates:
				try:
					method = getattr(self, method_name)
					method()
					frappe.logger().info(f"✅ {description} - Atualizado")
				except Exception as e:
					frappe.log_error(f"Erro não crítico em {description}: {str(e)}")
			# Continuar com outras atualizações

			frappe.logger().info(f"📊 Dados de compliance atualizados com sucesso: {self.name}")

		except Exception as e:
			frappe.log_error(f"Erro geral na atualização de compliance: {str(e)}")

	# Não quebrar fluxo - documento já foi submetido

	# ✅ FUNÇÃO MANTIDA: Verificar se compliance português está ativo
	def is_portugal_compliance_enabled(self):
		"""Verifica se compliance português está ativo para a empresa"""
		try:
			if not self.company:
				return False

			company_doc = frappe.get_cached_doc("Company", self.company)
			return (company_doc.country == "Portugal" and
					getattr(company_doc, 'portugal_compliance_enabled', False))
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar compliance da empresa: {str(e)}")
			return False

	# ✅ NOVA FUNÇÃO: Auto-configurar compliance português usando naming_series
	def auto_configure_portugal_compliance(self):
		"""Auto-configura campos de compliance português usando naming_series"""
		try:
			if not self.is_portugal_compliance_enabled():
				return

			frappe.logger().info(f"🔧 Auto-configurando Portugal Compliance: {self.name or 'NEW'}")

			# Auto-selecionar naming series portuguesa se não definida
			if not getattr(self, 'naming_series', None):
				self.auto_select_portuguese_naming_series()

			# Gerar ATCUD se naming series está definida mas ATCUD não
			if (getattr(self, 'naming_series', None) and
				not getattr(self, 'atcud_code', None)):
				self.auto_generate_atcud()

		except Exception as e:
			frappe.log_error(f"Error in auto_configure_portugal_compliance: {str(e)}")

	# Não quebrar fluxo - auto-configuração é opcional

	# ✅ NOVA FUNÇÃO: Auto-selecionar naming series portuguesa
	def auto_select_portuguese_naming_series(self):
		"""Auto-seleciona naming series portuguesa ativa"""
		try:
			# Buscar série ativa comunicada para Sales Invoice
			active_series = frappe.get_all("Portugal Series Configuration",
										   filters={
											   "document_type": "Sales Invoice",
											   "company": self.company,
											   "is_active": 1,
											   "is_communicated": 1
										   },
										   fields=["prefix"],
										   order_by="communication_date desc",
										   limit=1)

			if active_series:
				self.naming_series = f"{active_series[0].prefix}.####"
				frappe.logger().info(f"✅ Auto-selected naming series: {self.naming_series}")
			else:
				# Buscar série ativa não comunicada
				fallback_series = frappe.get_all("Portugal Series Configuration",
												 filters={
													 "document_type": "Sales Invoice",
													 "company": self.company,
													 "is_active": 1
												 },
												 fields=["prefix"],
												 limit=1)

				if fallback_series:
					self.naming_series = f"{fallback_series[0].prefix}.####"
					frappe.logger().info(
						f"⚠️ Selected non-communicated series: {self.naming_series}")

		except Exception as e:
			frappe.log_error(f"Error auto-selecting naming series: {str(e)}")

	# ✅ NOVA FUNÇÃO: Auto-gerar ATCUD usando naming_series
	def auto_generate_atcud(self):
		"""Auto-gera ATCUD se naming series está configurada"""
		try:
			if not getattr(self, 'naming_series', None):
				return

			# Chamar função do backend para gerar ATCUD
			result = frappe.call("portugal_compliance.utils.document_hooks.generate_manual_atcud",
								 args={
									 "doctype": "Sales Invoice",
									 "docname": self.name or "new"
								 })

			if result and result.get("success"):
				self.atcud_code = result.get("atcud_code")
				frappe.logger().info(f"✅ ATCUD auto-gerado: {self.atcud_code}")

		except Exception as e:
			frappe.log_error(f"Error auto-generating ATCUD: {str(e)}")

	def is_portuguese_naming_series(self):
		"""Verificar se naming series é portuguesa"""
		try:
			if not self.naming_series:
				return False

			prefix = self.naming_series.replace('.####', '')
			return frappe.db.exists("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company,
				"document_type": "Sales Invoice",
				"is_active": 1
			})

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar naming series portuguesa: {str(e)}")
			return False

	def is_naming_series_communicated(self):
		"""Verificar se naming series está comunicada"""
		try:
			if not self.naming_series:
				return False

			prefix = self.naming_series.replace('.####', '')
			return frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, "is_communicated") or False

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar comunicação da série: {str(e)}")
			return False

	def get_series_prefix_from_naming_series(self):
		"""Obter prefixo da série a partir da naming series"""
		try:
			if not self.naming_series:
				return None
			return self.naming_series.replace('.####', '')
		except Exception:
			return None

	def validate_prefix_format(self, prefix):
		"""Validar formato do prefixo XX-YYYY-COMPANY"""
		try:
			if not prefix:
				return False
			pattern = r'^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}$'
			return bool(re.match(pattern, prefix))
		except Exception:
			return False

	def validate_atcud_code_format(self, atcud_code):
		"""Validar formato do código ATCUD"""
		try:
			if not atcud_code:
				return False
			# ✅ FORMATO OFICIAL: 8-12 caracteres alfanuméricos
			if not (8 <= len(atcud_code) <= 12):
				return False
			if not atcud_code.isalnum() or not atcud_code.isupper():
				return False
			return True
		except Exception:
			return False

	def is_atcud_unique(self):
		"""Verificar unicidade do ATCUD"""
		try:
			if not self.atcud_code:
				return True

			existing = frappe.db.exists("Sales Invoice", {
				"atcud_code": self.atcud_code,
				"name": ["!=", self.name or ""],
				"docstatus": ["!=", 2]
			})

			return not existing

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar unicidade ATCUD: {str(e)}")
			return True

	def validate_customer_nif(self):
		"""Valida NIF do cliente - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not self.customer:
				return

			customer_tax_id = frappe.db.get_value("Customer", self.customer, "tax_id")

			if not customer_tax_id and self.is_portuguese_customer():
				frappe.msgprint(
					_("Customer '{0}' does not have a Tax ID (NIF) configured").format(
						self.customer),
					indicator="orange",
					title=_("Missing Tax ID")
				)
			elif customer_tax_id and self.is_portuguese_customer():
				# ✅ VALIDAÇÃO MELHORADA DO NIF
				if not self.validate_portuguese_nif(customer_tax_id):
					frappe.throw(_("Invalid Portuguese NIF for customer '{0}': {1}").format(
						self.customer, customer_tax_id
					))
				else:
					# NIF válido - adicionar ao campo tax_id da fatura se não estiver
					if not getattr(self, 'tax_id', None):
						self.tax_id = customer_tax_id

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação NIF do cliente: {str(e)}")
			frappe.throw(_("Erro na validação do NIF do cliente: {0}").format(str(e)))

	def is_portuguese_customer(self):
		"""Verifica se o cliente é português - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not self.customer:
				return False

			# Verificar país do cliente através do endereço primário
			customer_address = frappe.db.get_value("Address", {
				"link_name": self.customer,
				"link_doctype": "Customer",
				"is_primary_address": 1
			}, "country")

			# Se não tem endereço primário, verificar qualquer endereço
			if not customer_address:
				customer_address = frappe.db.get_value("Address", {
					"link_name": self.customer,
					"link_doctype": "Customer"
				}, "country")

			return customer_address == "Portugal"

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar se cliente é português: {str(e)}")
			return False

	def validate_portuguese_nif(self, nif):
		"""Valida NIF português - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not nif:
				return False

			# Remover espaços e caracteres não numéricos
			nif = re.sub(r'[^\d]', '', str(nif))

			# Verificar se tem 9 dígitos
			if len(nif) != 9:
				return False

			# ✅ CORREÇÃO: Verificar se começa com dígito válido
			if nif[0] not in '123456789':  # Primeiro dígito deve estar nesta lista
				return False

			# Calcular dígito de controlo
			check_sum = 0
			for i in range(8):
				check_sum += int(nif[i]) * (9 - i)

			remainder = check_sum % 11

			if remainder < 2:
				check_digit = 0
			else:
				check_digit = 11 - remainder

			# ✅ CORREÇÃO: Comparar com o 9º dígito
			return int(nif[8]) == check_digit

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação do NIF: {str(e)}")
			return False

	def validate_tax_information(self):
		"""Valida informações fiscais - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not self.taxes:
				frappe.msgprint(
					_("No tax information found. Please ensure VAT rates are correctly applied."),
					indicator="orange",
					title=_("Tax Information")
				)
				return

			# ✅ TAXAS ATUALIZADAS PARA 2025
			valid_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

			for tax in self.taxes:
				if hasattr(tax, 'rate') and tax.rate is not None:
					if tax.rate not in valid_rates:
						frappe.msgprint(
							_("VAT rate {0}% may not be valid for Portugal. Valid rates: {1}").format(
								tax.rate, ", ".join(map(str, valid_rates))
							),
							indicator="orange",
							title=_("VAT Rate Warning")
						)

			# ✅ VALIDAÇÃO ADICIONAL: Verificar se IVA está correto para tipo de cliente
			if self.is_intracom_invoice():
				self.validate_intracom_vat_rates()
			elif self.is_export_invoice():
				self.validate_export_vat_rates()

		except Exception as e:
			frappe.log_error(f"Erro na validação de impostos: {str(e)}")
			frappe.throw(_("Erro na validação de impostos: {0}").format(str(e)))

	# ✅ NOVA FUNÇÃO: Validar taxas IVA para intracomunitário
	def validate_intracom_vat_rates(self):
		"""Valida taxas de IVA para faturas intracomunitárias"""
		try:
			for tax in self.taxes:
				if hasattr(tax, 'rate') and tax.rate > 0:
					frappe.msgprint(
						_("Intra-community transactions should typically have 0% VAT"),
						indicator="orange",
						title=_("Intra-community VAT")
					)
					break
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação IVA intracomunitário: {str(e)}")

	# ✅ NOVA FUNÇÃO: Validar taxas IVA para exportação
	def validate_export_vat_rates(self):
		"""Valida taxas de IVA para faturas de exportação"""
		try:
			for tax in self.taxes:
				if hasattr(tax, 'rate') and tax.rate > 0:
					frappe.msgprint(
						_("Export transactions should typically have 0% VAT"),
						indicator="orange",
						title=_("Export VAT")
					)
					break
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação IVA exportação: {str(e)}")

	def validate_invoice_type(self):
		"""Valida tipo de fatura - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			# ✅ LIMITE ATUALIZADO PARA FATURA SIMPLIFICADA (€1,000)
			if self.grand_total <= 1000 and not getattr(self, 'customer_address', None):
				frappe.msgprint(
					_("Invoice may qualify as simplified invoice (≤€1,000 without customer address)"),
					indicator="blue",
					title=_("Simplified Invoice")
				)

			# Verificar se é nota de crédito
			if self.is_return and not getattr(self, 'return_against', None):
				frappe.throw(_("Credit note must reference the original invoice"))

			# ✅ NOVA VALIDAÇÃO: Verificar se requer QR Code
			if self.grand_total > 0:
				self.validate_qr_code_requirements()

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação do tipo de fatura: {str(e)}")
			frappe.throw(_("Erro na validação do tipo de fatura: {0}").format(str(e)))

	# ✅ NOVA FUNÇÃO: Validar requisitos QR Code
	def validate_qr_code_requirements(self):
		"""Valida requisitos de QR Code (obrigatório desde 2022)"""
		try:
			# QR Code é obrigatório para todas as faturas em Portugal
			if not getattr(self, 'qr_code', None):
				frappe.msgprint(
					_("QR Code is mandatory for all invoices in Portugal since 2022"),
					indicator="orange",
					title=_("QR Code Required")
				)
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação QR Code: {str(e)}")

	# ✅ NOVA FUNÇÃO: Validar requisitos assinatura digital
	def validate_digital_signature_requirements(self):
		"""Valida requisitos de assinatura digital"""
		try:
			# Assinatura digital obrigatória para valores altos
			if self.grand_total > 100000:
				frappe.msgprint(
					_("High-value invoice (>€100,000) may require qualified electronic signature"),
					indicator="orange",
					title=_("Digital Signature Required")
				)
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação assinatura digital: {str(e)}")

	# ✅ NOVA FUNÇÃO: Garantir consistência naming series
	def ensure_naming_series_consistency(self):
		"""Garante consistência da naming series com série portuguesa"""
		try:
			if not getattr(self, 'naming_series', None):
				return

			# Extrair prefixo da naming series
			prefix = self.naming_series.replace('.####', '')

			# Verificar se existe configuração portuguesa
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, ["name"], as_dict=True)

			if not series_config:
				frappe.logger().warning(
					f"⚠️ Naming series {self.naming_series} não tem configuração portuguesa")

		except Exception as e:
			frappe.log_error(f"Error ensuring naming series consistency: {str(e)}")

	def ensure_series_configuration(self):
		"""Garante que existe configuração de série - ATUALIZADA PARA NAMING_SERIES COM TRATAMENTO DE ERROS"""
		try:
			if not self.naming_series:
				return

			# Extrair prefixo da naming series
			prefix = self.naming_series.replace('.####', '')

			# Verificar se existe configuração portuguesa
			series_config = frappe.db.exists("Portugal Series Configuration", {
				"prefix": prefix,
				"document_type": "Sales Invoice",
				"company": self.company,
				"is_active": 1
			})

			if not series_config:
				frappe.msgprint(
					_("No Portugal series configuration found for series '{0}'. Please configure the series.").format(
						self.naming_series
					),
					indicator="orange",
					title=_("Series Configuration")
				)

		except Exception as e:
			frappe.log_error(f"Erro na configuração de série: {str(e)}")
			frappe.throw(_("Erro na configuração de série: {0}").format(str(e)))

	def ensure_atcud_code(self):
		"""Garante que o documento tem código ATCUD - ATUALIZADA PARA NAMING_SERIES COM TRATAMENTO DE ERROS"""
		try:
			if getattr(self, 'atcud_code', None):
				return  # Já tem ATCUD

			if not getattr(self, 'naming_series', None):
				frappe.logger().warning(
					"⚠️ Naming series não definida - ATCUD não pode ser gerado")
				return

			# Extrair prefixo da naming series
			prefix = self.naming_series.replace('.####', '')

			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, ["validation_code", "name"], as_dict=True)

			if series_config and series_config.validation_code:
				# Gerar ATCUD usando a série portuguesa
				result = frappe.call(
					"portugal_compliance.utils.document_hooks.generate_manual_atcud",
					args={
						"doctype": "Sales Invoice",
						"docname": self.name or "new"
					})

				if result and result.get("success"):
					self.atcud_code = result["atcud_code"]
					frappe.msgprint(
						_("ATCUD code generated: {0}").format(self.atcud_code),
						indicator="green",
						title=_("ATCUD Generated")
					)
				else:
					error_msg = result.get("error") if result else "Unknown error"
					frappe.throw(_("Failed to generate ATCUD: {0}").format(error_msg))
			else:
				frappe.msgprint(
					_("Series '{0}' is not communicated with AT. ATCUD cannot be generated.").format(
						prefix),
					indicator="orange",
					title=_("Series Not Communicated")
				)

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Error generating ATCUD for Sales Invoice {self.name}: {str(e)}")
			frappe.throw(
				_("Failed to generate ATCUD code. Please try again or contact administrator."))

	def get_document_number(self):
		"""Obtém número do documento da série - ATUALIZADA COM TRATAMENTO DE ERROS"""
		try:
			if not self.name:
				# Para documentos novos, obter próximo número da série
				if getattr(self, 'naming_series', None):
					prefix = self.naming_series.replace('.####', '')
					series_config = frappe.db.get_value("Portugal Series Configuration", {
						"prefix": prefix,
						"company": self.company
					}, "current_sequence")
					return series_config or 1
				return 1

			# Extrair número da série do nome do documento
			match = re.search(r'(\d+)$', self.name)
			if match:
				return int(match.group(1))
			return 1
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao obter número do documento: {str(e)}")
			return 1

	def validate_document_series(self):
		"""Valida série do documento - ATUALIZADA PARA NAMING_SERIES COM TRATAMENTO DE ERROS"""
		try:
			if not self.naming_series:
				frappe.throw(_("Document series is required for Portugal compliance"))

			# Extrair prefixo da naming series
			prefix = self.naming_series.replace('.####', '')

			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, ["is_communicated", "validation_code"], as_dict=True)

			if series_config:
				if not series_config.is_communicated:
					frappe.msgprint(
						_("Series '{0}' is not yet communicated with AT. Please communicate the series first.").format(
							prefix),
						indicator="orange",
						title=_("Series Not Communicated")
					)
				elif not series_config.validation_code:
					frappe.msgprint(
						_("Series '{0}' does not have a validation code from AT.").format(prefix),
						indicator="orange",
						title=_("Missing Validation Code")
					)

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação da série do documento: {str(e)}")
			frappe.throw(_("Erro na validação da série do documento: {0}").format(str(e)))

	def validate_fiscal_requirements(self):
		"""Valida requisitos fiscais - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			# Verificar se é fatura intracomunitária
			if self.is_intracom_invoice():
				self.validate_intracom_requirements()

			# Verificar se é exportação
			if self.is_export_invoice():
				self.validate_export_requirements()

			# Verificar regime de IVA de caixa
			if getattr(self, 'is_cash_vat', False):
				self.validate_cash_vat_requirements()

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação de requisitos fiscais: {str(e)}")
			frappe.throw(_("Erro na validação de requisitos fiscais: {0}").format(str(e)))

	def is_intracom_invoice(self):
		"""Verifica se é fatura intracomunitária - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not self.customer:
				return False

			# Verificar se cliente é da UE mas não de Portugal
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Romania", "Slovakia", "Slovenia",
							"Spain", "Sweden"]

			customer_country = frappe.db.get_value("Address", {
				"link_name": self.customer,
				"link_doctype": "Customer",
				"is_primary_address": 1
			}, "country")

			return customer_country in eu_countries and customer_country != "Portugal"

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar fatura intracomunitária: {str(e)}")
			return False

	def is_export_invoice(self):
		"""Verifica se é fatura de exportação - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			if not self.customer:
				return False

			customer_country = frappe.db.get_value("Address", {
				"link_name": self.customer,
				"link_doctype": "Customer",
				"is_primary_address": 1
			}, "country")

			# Países fora da UE
			eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
							"Czech Republic",
							"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
							"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
							"Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
							"Slovenia", "Spain", "Sweden"]

			return customer_country and customer_country not in eu_countries

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao verificar fatura de exportação: {str(e)}")
			return False

	def validate_intracom_requirements(self):
		"""Valida requisitos para faturas intracomunitárias - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			customer_tax_id = frappe.db.get_value("Customer", self.customer, "tax_id")

			if not customer_tax_id:
				frappe.throw(_("VAT number is required for intra-community transactions"))

			# Verificar se IVA é 0%
			for tax in self.taxes:
				if hasattr(tax, 'rate') and tax.rate > 0:
					frappe.msgprint(
						_("Intra-community transactions should typically have 0% VAT"),
						indicator="orange",
						title=_("Intra-community VAT")
					)
					break

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação de requisitos intracomunitários: {str(e)}")
			frappe.throw(
				_("Erro na validação de requisitos intracomunitários: {0}").format(str(e)))

	def validate_export_requirements(self):
		"""Valida requisitos para faturas de exportação - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			# Verificar se IVA é 0%
			for tax in self.taxes:
				if hasattr(tax, 'rate') and tax.rate > 0:
					frappe.msgprint(
						_("Export transactions should typically have 0% VAT"),
						indicator="orange",
						title=_("Export VAT")
					)
					break

			# Verificar se tem informações de transporte
			if not getattr(self, 'shipping_address_name', None):
				frappe.msgprint(
					_("Shipping address is recommended for export transactions"),
					indicator="orange",
					title=_("Export Documentation")
				)

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro na validação de requisitos de exportação: {str(e)}")

	def validate_cash_vat_requirements(self):
		"""Valida requisitos do regime de IVA de caixa - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			# Verificar se empresa está no regime de IVA de caixa
			company_cash_vat = frappe.db.get_value("Company", self.company, "cash_vat_scheme")

			if not company_cash_vat:
				frappe.throw(_("Company is not registered for cash VAT scheme"))

			# Verificar limites do regime
			if self.grand_total > 50000:
				frappe.msgprint(
					_("Cash VAT scheme may have limitations for high-value transactions"),
					indicator="orange",
					title=_("Cash VAT Limit")
				)

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação de IVA de caixa: {str(e)}")
			frappe.throw(_("Erro na validação de IVA de caixa: {0}").format(str(e)))

	def validate_invoice_limits(self):
		"""Valida limites de faturação - MANTIDA COM TRATAMENTO DE ERROS"""
		try:
			# ✅ LIMITE ATUALIZADO: €1,000 para fatura simplificada
			if self.grand_total > 1000 and getattr(self, 'is_simplified_invoice', False):
				frappe.throw(_("Simplified invoices cannot exceed €1,000"))

			# ✅ LIMITE ATUALIZADO: €100,000 para assinatura digital
			if self.grand_total > 100000:
				frappe.msgprint(
					_("High-value invoice (>€100,000) may require qualified electronic signature"),
					indicator="orange",
					title=_("High-Value Invoice")
				)

			# ✅ NOVA VALIDAÇÃO: Limite para software certificado
			if self.grand_total > 50000:
				frappe.msgprint(
					_("Companies with turnover >€50,000 must use certified invoicing software"),
					indicator="blue",
					title=_("Certified Software Required")
				)

		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro na validação de limites de faturação: {str(e)}")
			frappe.throw(_("Erro na validação de limites de faturação: {0}").format(str(e)))

	def create_atcud_log(self):
		"""Cria log do ATCUD gerado - ATUALIZADA PARA NAMING_SERIES COM TRATAMENTO DE ERROS"""
		try:
			if not getattr(self, 'atcud_code', None):
				return

			# ✅ LOG EXPANDIDO COM NAMING_SERIES
			atcud_log = frappe.get_doc({
				"doctype": "ATCUD Log",
				"atcud_code": self.atcud_code,
				"document_type": "Sales Invoice",
				"document_name": self.name,
				"company": self.company,
				"series_used": self.get_series_name_from_naming_series(),
				"generation_date": frappe.utils.today(),
				"sequence_number": self.get_document_number(),
				"validation_code_used": self.get_validation_code_from_atcud(),
				"document_date": self.posting_date,
				"document_total": self.grand_total,
				"customer": self.customer,
				"customer_name": self.customer_name,
				"customer_nif": frappe.db.get_value("Customer", self.customer,
													"tax_id") if self.customer else None,
				"is_return": self.is_return,
				"return_against": getattr(self, 'return_against', None),
				"generation_status": "Success",
				"generation_method": "Automatic",
				"environment_used": self.get_series_environment(),
				"description": f"ATCUD gerado automaticamente para Sales Invoice {self.name}"
			})
			atcud_log.insert(ignore_permissions=True)
			frappe.logger().info(f"✅ ATCUD log criado: {self.atcud_code}")

		except Exception as e:
			frappe.log_error(f"Error creating ATCUD log for Sales Invoice {self.name}: {str(e)}")

	# ✅ NOVA FUNÇÃO: Obter nome da série a partir da naming series
	def get_series_name_from_naming_series(self):
		"""Obtém nome da série portuguesa a partir da naming series"""
		try:
			if not getattr(self, 'naming_series', None):
				return self.naming_series or "Unknown"

			prefix = self.naming_series.replace('.####', '')
			series_name = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, "name")

			return series_name or prefix

		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao obter nome da série: {str(e)}")
			return self.naming_series or "Unknown"

	# ✅ FUNÇÃO MANTIDA: Extrair código de validação do ATCUD
	def get_validation_code_from_atcud(self):
		"""Extrai código de validação do ATCUD"""
		try:
			if not getattr(self, 'atcud_code', None):
				return None

			# ATCUD formato: CODIGO-NNNNNNNN
			return self.atcud_code.split('-')[0]
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao extrair código de validação: {str(e)}")
			return None

	# ✅ NOVA FUNÇÃO: Obter ambiente da série usando naming_series
	def get_series_environment(self):
		"""Obtém ambiente da série (test/production) usando naming_series"""
		try:
			if getattr(self, 'naming_series', None):
				prefix = self.naming_series.replace('.####', '')
				return frappe.db.get_value("Portugal Series Configuration", {
					"prefix": prefix,
					"company": self.company
				}, "at_environment") or "test"
			return "test"
		except Exception as e:
			frappe.logger().warning(f"⚠️ Erro ao obter ambiente da série: {str(e)}")
			return "test"

	def update_series_sequence(self):
		"""Atualiza sequência da série - ATUALIZADA PARA NAMING_SERIES COM TRATAMENTO DE ERROS"""
		try:
			if not getattr(self, 'naming_series', None):
				return

			# ✅ USAR NAMING_SERIES EM VEZ DE PORTUGAL_SERIES
			prefix = self.naming_series.replace('.####', '')
			current_number = self.get_document_number()

			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": prefix,
				"company": self.company
			}, "name")

			if series_config:
				frappe.db.set_value("Portugal Series Configuration", series_config, {
					"current_sequence": current_number + 1,  # Próximo número
					"last_used_date": self.posting_date,
					"total_documents_issued": frappe.db.get_value("Portugal Series Configuration",
																  series_config,
																  "total_documents_issued") + 1
				}, update_modified=False)

				frappe.logger().info(
					f"✅ Updated series sequence: {prefix} -> {current_number + 1}")

		except Exception as e:
			frappe.log_error(
				f"Error updating series sequence for Sales Invoice {self.name}: {str(e)}")

	# ✅ NOVA FUNÇÃO: Atualizar estatísticas da série usando naming_series
	def update_series_statistics(self):
		"""Atualiza estatísticas de uso da série usando naming_series"""
		try:
			if getattr(self, 'naming_series', None):
				prefix = self.naming_series.replace('.####', '')
				series_name = frappe.db.get_value("Portugal Series Configuration", {
					"prefix": prefix,
					"company": self.company
				}, "name")

				if series_name:
					series_doc = frappe.get_doc("Portugal Series Configuration", series_name)
					if hasattr(series_doc, 'update_usage_statistics'):
						series_doc.update_usage_statistics()

		except Exception as e:
			frappe.log_error(f"Error updating series statistics: {str(e)}")

	# ✅ FUNÇÃO MANTIDA: Criar trilha de auditoria
	def create_compliance_audit_trail(self):
		"""Cria trilha de auditoria para compliance"""
		try:
			audit_data = {
				"document_type": "Sales Invoice",
				"document_name": self.name,
				"company": self.company,
				"naming_series": getattr(self, 'naming_series', None),
				"atcud_code": getattr(self, 'atcud_code', None),
				"customer_nif": frappe.db.get_value("Customer", self.customer,
													"tax_id") if self.customer else None,
				"invoice_total": self.grand_total,
				"compliance_status": "compliant" if getattr(self, 'atcud_code',
															None) else "pending",
				"submission_date": frappe.utils.now(),
				"user": frappe.session.user
			}

			# Armazenar no cache por 1 ano
			cache_key = f"compliance_audit_{self.name}"
			frappe.cache.set(cache_key, audit_data, expires_in_sec=31536000)

		except Exception as e:
			frappe.log_error(f"Error creating compliance audit trail: {str(e)}")

	# ✅ FUNÇÃO MANTIDA: Gerar dados QR Code
	def generate_qr_code_data(self):
		"""Gera dados para QR Code (obrigatório desde 2022)"""
		try:
			qr_data = {
				"A": frappe.db.get_value("Company", self.company, "tax_id"),  # NIF emissor
				"B": frappe.db.get_value("Customer", self.customer,
										 "tax_id") if self.customer else "",  # NIF cliente
				"C": self.country if hasattr(self, 'country') else "PT",  # País
				"D": self.doctype,  # Tipo documento
				"E": "N",  # Estado documento
				"F": self.posting_date.strftime("%Y%m%d"),  # Data documento
				"G": self.name,  # Identificação única
				"H": getattr(self, 'atcud_code', ""),  # ATCUD
				"I1": f"{self.net_total:.2f}",  # Total sem impostos
				"I2": f"{self.total_taxes_and_charges:.2f}",  # Total impostos
				"I3": f"{self.total_taxes_and_charges:.2f}",  # Total impostos (repetido)
				"I4": f"{self.grand_total:.2f}",  # Total com impostos
				"J1": "PT",  # País
				"J2": f"{self.posting_date.strftime('%Y-%m-%d')} {frappe.utils.now_datetime().strftime('%H:%M:%S')}",
				# Data/hora
				"J3": f"{self.name}",  # Identificação
				"J4": "",  # Espaço para assinatura
				"K1": "",  # Espaço para outras informações
				"K2": "",
				"K3": "",
				"K4": "",
				"L": "1",  # Versão
				"M": "",  # Hash
				"N": f"{self.grand_total:.2f}",  # Valor total
				"O": f"{self.grand_total:.2f}",  # Valor pago
				"P": "0.00",  # Troco
				"Q": "",  # Hash documento anterior
				"R": "1"  # Número sequencial
			}

			# Construir string QR Code
			qr_string = ";".join([f"{k}:{v}" for k, v in qr_data.items() if v])

			# Armazenar no documento (se campo existir)
			if hasattr(self, 'qr_code_data'):
				self.qr_code_data = qr_string

		except Exception as e:
			frappe.log_error(f"Error generating QR code data: {str(e)}")

	def create_invoice_notification(self):
		"""Cria notificação de fatura se necessário - ATUALIZADA"""
		try:
			# ✅ NOTIFICAÇÕES ATUALIZADAS PARA NAMING_SERIES
			notifications = []

			# Fatura de alto valor
			if self.grand_total >= 50000:
				notifications.append({
					"subject": _("High-Value Invoice Created"),
					"message": _("Invoice {0} for €{1} has been created").format(self.name,
																				 self.grand_total),
					"type": "Alert"
				})

			# Fatura sem ATCUD
			if not getattr(self, 'atcud_code', None):
				notifications.append({
					"subject": _("Invoice Without ATCUD"),
					"message": _("Invoice {0} was created without ATCUD code").format(self.name),
					"type": "Warning"
				})

			# Série não comunicada
			if getattr(self, 'naming_series', None):
				prefix = self.naming_series.replace('.####', '')
				series_communicated = frappe.db.get_value("Portugal Series Configuration", {
					"prefix": prefix,
					"company": self.company
				}, "is_communicated")

				if not series_communicated:
					notifications.append({
						"subject": _("Series Not Communicated"),
						"message": _("Invoice {0} uses non-communicated series").format(self.name),
						"type": "Warning"
					})

			# Criar notificações
			for notification in notifications:
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": notification["subject"],
					"email_content": notification["message"],
					"for_user": self.owner,
					"type": notification["type"],
					"document_type": "Sales Invoice",
					"document_name": self.name
				}).insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Error creating invoice notification for {self.name}: {str(e)}")

	def get_portugal_compliance_data(self):
		"""Retorna dados de compliance português - ATUALIZADA PARA NAMING_SERIES"""
		return {
			"atcud_code": getattr(self, 'atcud_code', None),
			"naming_series": getattr(self, 'naming_series', None),
			"series_prefix": self.naming_series.replace('.####', '') if getattr(self,
																				'naming_series',
																				None) else None,
			"document_type": "Sales Invoice",
			"company": self.company,
			"customer_nif": frappe.db.get_value("Customer", self.customer,
												"tax_id") if self.customer else None,
			"is_portuguese_customer": self.is_portuguese_customer(),
			"is_intracom": self.is_intracom_invoice(),
			"is_export": self.is_export_invoice(),
			"invoice_total": self.grand_total,
			"compliance_status": "compliant" if getattr(self, 'atcud_code', None) else "pending",
			"qr_code_required": True,  # Obrigatório desde 2022
			"digital_signature_required": self.grand_total > 100000,
			"series_communicated": self.is_series_communicated(),
			"validation_code": self.get_validation_code_from_atcud(),
			"environment": self.get_series_environment()
		}

	# ✅ NOVA FUNÇÃO: Verificar se série está comunicada usando naming_series
	def is_series_communicated(self):
		"""Verifica se série está comunicada com AT usando naming_series"""
		try:
			if getattr(self, 'naming_series', None):
				prefix = self.naming_series.replace('.####', '')
				return frappe.db.get_value("Portugal Series Configuration", {
					"prefix": prefix,
					"company": self.company
				}, "is_communicated") or False
			return False
		except Exception:
			return False

	def validate_before_cancel(self):
		"""Validações antes do cancelamento - MANTIDA"""
		super().validate_before_cancel()

		if self.is_portugal_compliance_enabled():
			# ✅ VALIDAÇÃO MELHORADA: 30 dias para cancelamento
			if getattr(self, 'atcud_code', None):
				posting_datetime = datetime.combine(self.posting_date, datetime.min.time())
				days_since_posting = (datetime.now() - posting_datetime).days

				if days_since_posting > 30:
					frappe.throw(
						_("Cannot cancel invoice older than 30 days due to Portuguese regulations"))

			# Verificar se há pagamentos relacionados
			payments = frappe.db.get_all("Payment Entry Reference", {
				"reference_name": self.name,
				"reference_doctype": "Sales Invoice"
			}, ["parent"])

			if payments:
				frappe.msgprint(
					_("This invoice has related payments. Cancellation will affect payment entries."),
					indicator="orange",
					title=_("Related Payments")
				)

	def on_cancel(self):
		"""Ações após cancelamento - MANTIDA"""
		super().on_cancel()

		if self.is_portugal_compliance_enabled():
			self.update_atcud_log_on_cancel()
			# ✅ NOVA AÇÃO: Atualizar estatísticas da série
			self.update_series_statistics_on_cancel()

	def update_atcud_log_on_cancel(self):
		"""Atualiza log ATCUD após cancelamento - MANTIDA"""
		if not getattr(self, 'atcud_code', None):
			return

		try:
			# Marcar log como cancelado
			atcud_log = frappe.db.exists("ATCUD Log", {
				"atcud_code": self.atcud_code,
				"document_name": self.name
			})

			if atcud_log:
				frappe.db.set_value("ATCUD Log", atcud_log, {
					"generation_status": "Cancelled",
					"cancellation_date": frappe.utils.now(),
					"cancellation_reason": getattr(self, 'reason_for_cancellation',
												   'Invoice cancelled'),
					"cancelled_by": frappe.session.user
				}, update_modified=False)

				frappe.logger().info(f"✅ ATCUD log updated on cancel: {self.atcud_code}")

		except Exception as e:
			frappe.log_error(
				f"Error updating ATCUD log on cancel for Sales Invoice {self.name}: {str(e)}")

	# ✅ NOVA FUNÇÃO: Atualizar estatísticas ao cancelar usando naming_series
	def update_series_statistics_on_cancel(self):
		"""Atualiza estatísticas da série após cancelamento usando naming_series"""
		try:
			if getattr(self, 'naming_series', None):
				prefix = self.naming_series.replace('.####', '')
				series_name = frappe.db.get_value("Portugal Series Configuration", {
					"prefix": prefix,
					"company": self.company
				}, "name")

				if series_name:
					# Decrementar contador de documentos emitidos
					current_count = frappe.db.get_value("Portugal Series Configuration",
														series_name, "total_documents_issued") or 0

					if current_count > 0:
						frappe.db.set_value("Portugal Series Configuration", series_name,
											"total_documents_issued", current_count - 1,
											update_modified=False)

		except Exception as e:
			frappe.log_error(f"Error updating series statistics on cancel: {str(e)}")
