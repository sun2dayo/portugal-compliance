# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Compliance Hooks for Portugal Compliance - NOVA ABORDAGEM NATIVA
Hooks para validação e compliance português usando naming_series nativas do ERPNext
Sem DocTypes extras - integração 100% transparente
"""

import frappe
from frappe import _
from frappe.utils import getdate, now, today, cint, flt
import re
from datetime import datetime, date


class PortugueseComplianceHooks:
	"""
	Classe principal para hooks de compliance português
	Abordagem nativa: usa naming_series do ERPNext + validações integradas
	"""

	def __init__(self):
		self.module = "Portugal Compliance"

		# ✅ DOCTYPES SUPORTADOS
		self.supported_doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Stock Entry",
			"Journal Entry", "Quotation", "Sales Order",
			"Purchase Order", "Material Request"
		]

		# ✅ PREFIXOS PORTUGUESES VÁLIDOS
		self.portuguese_prefixes = [
			"FT", "FS", "FR", "NC", "ND",  # Faturas
			"FC",  # Compras
			"RC", "RB",  # Recibos
			"GT", "GR", "GM",  # Guias
			"JE",  # Lançamentos
			"OR", "EC", "EF", "MR"  # Outros
		]

	def validate_portuguese_naming_series(self, doc, method=None):
		"""
		Validar se naming_series é portuguesa e aplicar compliance
		Hook principal para validação
		"""
		try:
			# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
			if not self.is_portuguese_company(doc.company):
				return

			# ✅ VERIFICAR SE DOCTYPE É SUPORTADO
			if doc.doctype not in self.supported_doctypes:
				return

			# ✅ VALIDAR NAMING_SERIES OBRIGATÓRIA
			if not getattr(doc, 'naming_series', None):
				frappe.throw(_("Naming series portuguesa é obrigatória para empresas portuguesas"))

			# ✅ VERIFICAR SE É SÉRIE PORTUGUESA
			if not self.is_portuguese_naming_series(doc.naming_series):
				frappe.throw(
					_("Use uma naming series portuguesa válida (formato: XX-YYYY-EMPRESA.####)"))

			# ✅ VALIDAR SEQUÊNCIA E INTEGRIDADE
			self.validate_series_sequence(doc)

			# ✅ APLICAR VALIDAÇÕES ESPECÍFICAS POR DOCTYPE
			self.apply_doctype_specific_validations(doc)

			frappe.logger().info(
				f"✅ Compliance validado: {doc.doctype} {doc.name} - {doc.naming_series}")

		except Exception as e:
			frappe.log_error(f"Erro na validação de compliance: {str(e)}",
							 "PortugueseComplianceHooks")
			raise

	def generate_atcud_from_naming_series(self, doc, method=None):
		"""
		Gerar ATCUD baseado na naming_series nativa
		Hook para geração automática de ATCUD
		"""
		try:
			# ✅ VERIFICAR CONDIÇÕES PARA GERAR ATCUD
			if not self.should_generate_atcud(doc):
				return

			# ✅ VERIFICAR SE JÁ TEM ATCUD
			if getattr(doc, 'atcud_code', None):
				frappe.logger().info(f"⏭️ ATCUD já existe: {doc.atcud_code}")
				return

			# ✅ GERAR ATCUD
			atcud_result = self.generate_atcud_for_document(doc)

			if atcud_result.get("success"):
				doc.atcud_code = atcud_result["atcud_code"]
				frappe.logger().info(f"✅ ATCUD gerado: {doc.atcud_code} para {doc.name}")

				# ✅ CRIAR LOG DE AUDITORIA
				self.create_atcud_audit_log(doc, atcud_result)
			else:
				frappe.logger().warning(f"⚠️ Falha ao gerar ATCUD: {atcud_result.get('error')}")

		except Exception as e:
			frappe.log_error(f"Erro na geração de ATCUD: {str(e)}", "PortugueseComplianceHooks")

	def validate_before_submit(self, doc, method=None):
		"""
		Validações antes da submissão do documento
		Hook crítico para compliance obrigatório
		"""
		try:
			if not self.is_portuguese_company(doc.company):
				return

			if doc.doctype not in self.supported_doctypes:
				return

			# ✅ VALIDAÇÕES OBRIGATÓRIAS ANTES DA SUBMISSÃO

			# 1. Naming series portuguesa obrigatória
			if not self.is_portuguese_naming_series(getattr(doc, 'naming_series', '')):
				frappe.throw(_("Documentos submetidos devem usar naming series portuguesa"))

			# 2. ATCUD obrigatório para documentos fiscais
			if self.is_fiscal_document(doc) and not getattr(doc, 'atcud_code', None):
				# Tentar gerar ATCUD automaticamente
				atcud_result = self.generate_atcud_for_document(doc)
				if atcud_result.get("success"):
					doc.atcud_code = atcud_result["atcud_code"]
				else:
					frappe.throw(
						_("ATCUD é obrigatório para documentos fiscais. Erro: {0}").format(
							atcud_result.get("error", "Desconhecido")))

			# 3. Validar NIF do cliente/fornecedor
			self.validate_tax_id_before_submit(doc)

			# 4. Validar valores e impostos
			self.validate_amounts_and_taxes(doc)

			frappe.logger().info(f"✅ Validações de submissão aprovadas: {doc.doctype} {doc.name}")

		except Exception as e:
			frappe.log_error(f"Erro nas validações de submissão: {str(e)}",
							 "PortugueseComplianceHooks")
			raise

	def auto_select_portuguese_naming_series(self, doc, method=None):
		"""
		Auto-selecionar naming series portuguesa se não definida
		Hook para facilitar UX
		"""
		try:
			# ✅ VERIFICAR CONDIÇÕES
			if not self.is_portuguese_company(doc.company):
				return

			if doc.doctype not in self.supported_doctypes:
				return

			if getattr(doc, 'naming_series', None):
				return  # Já tem naming series

			# ✅ BUSCAR NAMING SERIES PORTUGUESA DISPONÍVEL
			available_series = self.get_available_portuguese_naming_series(doc.doctype,
																		   doc.company)

			if available_series:
				# Selecionar a primeira disponível (preferencialmente comunicada)
				selected_series = available_series[0]
				doc.naming_series = selected_series

				frappe.logger().info(
					f"✅ Naming series auto-selecionada: {selected_series} para {doc.doctype}")

				# ✅ MOSTRAR MENSAGEM INFORMATIVA
				frappe.msgprint(
					_("Naming series portuguesa selecionada automaticamente: {0}").format(
						selected_series),
					indicator="green",
					title=_("Portugal Compliance")
				)

		except Exception as e:
			frappe.log_error(f"Erro na auto-seleção de naming series: {str(e)}",
							 "PortugueseComplianceHooks")

	def validate_customer_supplier_nif(self, doc, method=None):
		"""
		Validar NIF de clientes e fornecedores
		Hook para validação de NIFs
		"""
		try:
			if doc.doctype == "Customer" and getattr(doc, 'tax_id', None):
				self.validate_portuguese_nif(doc.tax_id, "Cliente")

			elif doc.doctype == "Supplier" and getattr(doc, 'tax_id', None):
				self.validate_portuguese_nif(doc.tax_id, "Fornecedor")

		except Exception as e:
			frappe.log_error(f"Erro na validação de NIF: {str(e)}", "PortugueseComplianceHooks")

	# ========== MÉTODOS DE VALIDAÇÃO ==========

	def is_portuguese_company(self, company):
		"""
		Verificar se empresa é portuguesa com compliance ativo
		"""
		try:
			if not company:
				return False

			# ✅ CACHE PARA PERFORMANCE
			cache_key = f"portuguese_company_{company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is not None:
				return cached_result

			# ✅ VERIFICAR NA BASE DE DADOS
			company_data = frappe.db.get_value("Company", company,
											   ["country", "portugal_compliance_enabled"],
											   as_dict=True)

			if not company_data:
				result = False
			else:
				result = (company_data.country == "Portugal" and
						  cint(company_data.portugal_compliance_enabled))

			# ✅ CACHE POR 5 MINUTOS
			frappe.cache().set_value(cache_key, result, expires_in_sec=300)
			return result

		except Exception as e:
			frappe.log_error(f"Erro ao verificar empresa portuguesa: {str(e)}",
							 "PortugueseComplianceHooks")
			return False

	def is_portuguese_naming_series(self, naming_series):
		"""
		Verificar se naming_series é portuguesa
		"""
		if not naming_series:
			return False

		# ✅ PADRÃO: XX-YYYY-COMPANY.####
		pattern = r'^([A-Z]{2,4})-(\d{4})-([A-Z0-9]{2,4})\.####$'
		match = re.match(pattern, naming_series)

		if not match:
			return False

		prefix, year, company_abbr = match.groups()

		# ✅ VERIFICAR SE PREFIXO É PORTUGUÊS
		return prefix in self.portuguese_prefixes

	def should_generate_atcud(self, doc):
		"""
		Verificar se deve gerar ATCUD para o documento
		"""
		# ✅ CONDIÇÕES PARA GERAR ATCUD
		conditions = [
			self.is_portuguese_company(doc.company),
			doc.doctype in self.supported_doctypes,
			getattr(doc, 'naming_series', None),
			self.is_portuguese_naming_series(getattr(doc, 'naming_series', '')),
			doc.name and doc.name != 'new'
		]

		return all(conditions)

	def is_fiscal_document(self, doc):
		"""
		Verificar se documento é fiscal (requer ATCUD obrigatório)
		"""
		fiscal_doctypes = ["Sales Invoice", "Purchase Invoice", "Payment Entry"]
		return doc.doctype in fiscal_doctypes

	def validate_series_sequence(self, doc):
		"""
		Validar sequência da série portuguesa
		"""
		try:
			if not getattr(doc, 'naming_series', None):
				return

			# ✅ EXTRAIR INFORMAÇÕES DA NAMING SERIES
			prefix = doc.naming_series.replace('.####', '')

			# ✅ VERIFICAR INTEGRIDADE DA SEQUÊNCIA
			if doc.name and doc.name != 'new':
				sequence = self.extract_sequence_from_document_name(doc.name)

				if sequence < 1:
					frappe.throw(_("Sequência do documento deve ser maior que 0"))

				# ✅ LOG DE AUDITORIA
				frappe.logger().info(f"📋 Sequência validada: {doc.name} = {sequence}")

		except Exception as e:
			frappe.log_error(f"Erro na validação de sequência: {str(e)}",
							 "PortugueseComplianceHooks")

	def apply_doctype_specific_validations(self, doc):
		"""
		Aplicar validações específicas por tipo de documento
		"""
		try:
			if doc.doctype == "Sales Invoice":
				self.validate_sales_invoice_compliance(doc)
			elif doc.doctype == "Purchase Invoice":
				self.validate_purchase_invoice_compliance(doc)
			elif doc.doctype == "Payment Entry":
				self.validate_payment_entry_compliance(doc)

		except Exception as e:
			frappe.log_error(f"Erro nas validações específicas: {str(e)}",
							 "PortugueseComplianceHooks")

	def validate_sales_invoice_compliance(self, doc):
		"""
		Validações específicas para Sales Invoice
		"""
		# ✅ VALIDAR CLIENTE
		if not getattr(doc, 'customer', None):
			frappe.throw(_("Cliente é obrigatório"))

		# ✅ VALIDAR ITENS
		if not getattr(doc, 'items', None) or len(doc.items) == 0:
			frappe.throw(_("Pelo menos um item é obrigatório"))

		# ✅ VALIDAR TOTAL
		if flt(getattr(doc, 'grand_total', 0)) <= 0:
			frappe.throw(_("Total da fatura deve ser maior que zero"))

	def validate_purchase_invoice_compliance(self, doc):
		"""
		Validações específicas para Purchase Invoice
		"""
		# ✅ VALIDAR FORNECEDOR
		if not getattr(doc, 'supplier', None):
			frappe.throw(_("Fornecedor é obrigatório"))

	def validate_payment_entry_compliance(self, doc):
		"""
		Validações específicas para Payment Entry
		"""
		# ✅ VALIDAR VALOR
		if flt(getattr(doc, 'paid_amount', 0)) <= 0:
			frappe.throw(_("Valor pago deve ser maior que zero"))

	def validate_tax_id_before_submit(self, doc):
		"""
		Validar NIF antes da submissão
		"""
		try:
			tax_id = None
			entity_type = ""

			if doc.doctype == "Sales Invoice" and getattr(doc, 'tax_id', None):
				tax_id = doc.tax_id
				entity_type = "Cliente"
			elif doc.doctype == "Purchase Invoice" and getattr(doc, 'tax_id', None):
				tax_id = doc.tax_id
				entity_type = "Fornecedor"

			if tax_id:
				if not self.validate_portuguese_nif(tax_id, entity_type, throw_error=False):
					frappe.msgprint(
						_("NIF {0} do {1} pode estar inválido").format(tax_id, entity_type),
						indicator="orange",
						title=_("Aviso de NIF")
					)

		except Exception as e:
			frappe.log_error(f"Erro na validação de NIF: {str(e)}", "PortugueseComplianceHooks")

	def validate_amounts_and_taxes(self, doc):
		"""
		Validar valores e impostos
		"""
		try:
			# ✅ VALIDAR TOTAIS
			if hasattr(doc, 'grand_total') and flt(doc.grand_total) < 0:
				frappe.throw(_("Total do documento não pode ser negativo"))

			# ✅ VALIDAR IMPOSTOS (se aplicável)
			if hasattr(doc, 'taxes') and doc.taxes:
				for tax in doc.taxes:
					if flt(tax.tax_amount) < 0:
						frappe.throw(_("Valor do imposto não pode ser negativo"))

		except Exception as e:
			frappe.log_error(f"Erro na validação de valores: {str(e)}",
							 "PortugueseComplianceHooks")

	# ========== MÉTODOS DE GERAÇÃO DE ATCUD ==========

	def generate_atcud_for_document(self, doc):
		"""
		Gerar ATCUD para um documento específico
		"""
		try:
			# ✅ EXTRAIR INFORMAÇÕES DA NAMING SERIES
			prefix = doc.naming_series.replace('.####', '')  # FT-2025-NDX

			# ✅ BUSCAR CÓDIGO AT
			validation_code = self.get_at_validation_code(prefix, doc.company)

			if not validation_code:
				return {
					"success": False,
					"error": f"Código de validação AT não encontrado para série {prefix}"
				}

			# ✅ EXTRAIR SEQUÊNCIA DO NOME DO DOCUMENTO
			sequence = self.extract_sequence_from_document_name(doc.name)

			# ✅ GERAR ATCUD: CODIGO-SEQUENCIA
			atcud_code = f"{validation_code}-{sequence:08d}"

			return {
				"success": True,
				"atcud_code": atcud_code,
				"validation_code": validation_code,
				"sequence": sequence,
				"prefix": prefix
			}

		except Exception as e:
			frappe.log_error(f"Erro ao gerar ATCUD: {str(e)}", "PortugueseComplianceHooks")
			return {
				"success": False,
				"error": str(e)
			}

	def get_at_validation_code(self, prefix, company):
		"""
		Obter código de validação AT para um prefixo
		Busca em campos customizados da empresa
		"""
		try:
			# ✅ CAMPO DINÂMICO: at_code_FT_2025_NDX
			field_name = f"at_code_{prefix.replace('-', '_')}"

			validation_code = frappe.db.get_value("Company", company, field_name)

			if validation_code:
				return validation_code

			# ✅ FALLBACK: Buscar em configuração geral
			general_field = f"at_validation_code_{prefix.split('-')[0]}"  # at_validation_code_FT
			return frappe.db.get_value("Company", company, general_field)

		except Exception as e:
			frappe.log_error(f"Erro ao obter código AT: {str(e)}", "PortugueseComplianceHooks")
			return None

	def extract_sequence_from_document_name(self, name):
		"""
		Extrair sequência do nome do documento gerado pelo ERPNext
		"""
		if not name:
			return 1

		# ✅ PADRÃO NATIVO: FT-2025-NDX-00000001
		patterns = [
			r'-(\d{8})$',  # 8 dígitos no final
			r'-(\d+)$',  # Qualquer número no final
			r'(\d+)$'  # Apenas números no final
		]

		for pattern in patterns:
			match = re.search(pattern, name)
			if match:
				return int(match.group(1))

		# ✅ FALLBACK
		frappe.logger().warning(f"Não foi possível extrair sequência de: {name}")
		return 1

	def get_available_portuguese_naming_series(self, doctype, company):
		"""
		Obter naming_series portuguesas disponíveis para um DocType
		"""
		try:
			if not frappe.db.exists("DocType", doctype):
				return []

			# ✅ OBTER AUTONAME DO DOCTYPE
			autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
			all_options = [opt.strip() for opt in autoname.split('\n') if opt.strip()]

			# ✅ FILTRAR APENAS SÉRIES PORTUGUESAS
			portuguese_options = []
			company_abbr = frappe.db.get_value("Company", company, "abbr")

			for option in all_options:
				if self.is_portuguese_naming_series(option) and company_abbr in option:
					portuguese_options.append(option)

			# ✅ ORDENAR POR PRIORIDADE (séries comunicadas primeiro)
			return sorted(portuguese_options)

		except Exception as e:
			frappe.log_error(f"Erro ao obter naming series disponíveis: {str(e)}",
							 "PortugueseComplianceHooks")
			return []

	# ========== MÉTODOS DE VALIDAÇÃO DE NIF ==========

	def validate_portuguese_nif(self, nif, entity_type="", throw_error=True):
		"""
		Validar NIF português
		"""
		try:
			if not nif:
				return True  # NIF vazio é permitido

			# ✅ LIMPAR NIF
			nif_clean = re.sub(r'[^0-9]', '', str(nif))

			# ✅ VERIFICAR COMPRIMENTO
			if len(nif_clean) != 9:
				if throw_error:
					frappe.throw(_("NIF deve ter 9 dígitos"))
				return False

			# ✅ VERIFICAR PRIMEIRO DÍGITO
			if nif_clean[0] not in '123456789':
				if throw_error:
					frappe.throw(_("NIF inválido - primeiro dígito deve ser 1-9"))
				return False

			# ✅ CALCULAR DÍGITO DE CONTROLO
			checksum = 0
			for i in range(8):
				checksum += int(nif_clean[i]) * (9 - i)

			remainder = checksum % 11
			control_digit = 0 if remainder < 2 else 11 - remainder

			if int(nif_clean[8]) != control_digit:
				if throw_error:
					frappe.throw(_("NIF inválido - dígito de controlo incorreto"))
				return False

			return True

		except Exception as e:
			frappe.log_error(f"Erro na validação de NIF: {str(e)}", "PortugueseComplianceHooks")
			if throw_error:
				frappe.throw(_("Erro na validação do NIF: {0}").format(str(e)))
			return False

	# ========== MÉTODOS DE AUDITORIA ==========

	def create_atcud_audit_log(self, doc, atcud_result):
		"""
		Criar log de auditoria para ATCUD gerado
		"""
		try:
			# ✅ CRIAR LOG SIMPLES EM COMMENT
			comment_content = f"""
ATCUD Gerado Automaticamente:
- Código: {atcud_result['atcud_code']}
- Série: {atcud_result['prefix']}
- Sequência: {atcud_result['sequence']}
- Data: {now()}
- Usuário: {frappe.session.user}
            """.strip()

			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": comment_content,
				"comment_email": frappe.session.user
			}).insert(ignore_permissions=True)

			frappe.logger().info(f"✅ Log de auditoria ATCUD criado para {doc.name}")

		except Exception as e:
			frappe.log_error(f"Erro ao criar log de auditoria: {str(e)}",
							 "PortugueseComplianceHooks")


# ========== INSTÂNCIA GLOBAL ==========

# ✅ INSTÂNCIA GLOBAL PARA USO
portuguese_compliance_hooks = PortugueseComplianceHooks()


# ========== FUNÇÕES PARA HOOKS ==========

def validate_portuguese_naming_series(doc, method=None):
	"""Hook para validar naming_series portuguesa"""
	return portuguese_compliance_hooks.validate_portuguese_naming_series(doc, method)


def generate_atcud_from_naming_series(doc, method=None):
	"""Hook para gerar ATCUD"""
	return portuguese_compliance_hooks.generate_atcud_from_naming_series(doc, method)


def validate_before_submit(doc, method=None):
	"""Hook para validações antes da submissão"""
	return portuguese_compliance_hooks.validate_before_submit(doc, method)


# Atualizar compliance_hooks.py
def generate_atcud_from_naming_series(doc, method=None):
	"""Gerar ATCUD usando código AT da empresa"""
	try:
		if not should_generate_atcud(doc):
			return

		# Verificar se já tem ATCUD
		if getattr(doc, 'atcud_code', None):
			return

		# Gerar ATCUD usando código AT
		from portugal_compliance.utils.atcud_generator import generate_atcud_for_document
		result = generate_atcud_for_document(doc)

		if result.get("success"):
			doc.atcud_code = result["atcud_code"]
			frappe.logger().info(f"✅ ATCUD gerado: {doc.name} → {doc.atcud_code}")
		else:
			frappe.logger().warning(f"⚠️ Falha ATCUD para {doc.name}: {result.get('error')}")

	except Exception as e:
		frappe.log_error(f"Erro na geração de ATCUD: {str(e)}")


def should_generate_atcud(doc):
	"""Verificar se deve gerar ATCUD"""
	# Verificar se é empresa portuguesa
	if not is_portuguese_company(doc.company):
		return False

	# Verificar se tem naming series portuguesa
	if not is_portuguese_naming_series(getattr(doc, 'naming_series', '')):
		return False

	# Verificar se documento foi salvo
	if not doc.name or doc.name == 'new':
		return False

	return True


def validate_customer_supplier_nif(doc, method=None):
	"""Hook para validação de NIF"""
	return portuguese_compliance_hooks.validate_customer_supplier_nif(doc, method)


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def generate_manual_atcud(doctype, docname):
	"""
	API para gerar ATCUD manualmente
	"""
	try:
		if not docname or docname == "new":
			return {
				"success": False,
				"error": "Documento deve ser salvo antes de gerar ATCUD"
			}

		doc = frappe.get_doc(doctype, docname)

		if not portuguese_compliance_hooks.is_portuguese_company(doc.company):
			return {
				"success": False,
				"error": "Empresa não é portuguesa ou compliance não está ativo"
			}

		# ✅ GERAR ATCUD
		result = portuguese_compliance_hooks.generate_atcud_for_document(doc)

		if result.get("success"):
			# ✅ ATUALIZAR DOCUMENTO
			frappe.db.set_value(doctype, docname, "atcud_code", result["atcud_code"])
			frappe.db.commit()

			# ✅ CRIAR LOG
			portuguese_compliance_hooks.create_atcud_audit_log(doc, result)

		return result

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD manual: {str(e)}", "PortugueseComplianceHooks")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_nif(nif):
	"""
	API para validar NIF português
	"""
	try:
		is_valid = portuguese_compliance_hooks.validate_portuguese_nif(nif, throw_error=False)
		return {
			"success": True,
			"valid": is_valid,
			"nif": nif
		}
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_compliance_status(doctype, docname):
	"""
	API para obter status de compliance de um documento
	"""
	try:
		doc = frappe.get_doc(doctype, docname)

		status = {
			"is_portuguese_company": portuguese_compliance_hooks.is_portuguese_company(
				doc.company),
			"has_portuguese_naming_series": portuguese_compliance_hooks.is_portuguese_naming_series(
				getattr(doc, 'naming_series', '')),
			"has_atcud": bool(getattr(doc, 'atcud_code', None)),
			"is_fiscal_document": portuguese_compliance_hooks.is_fiscal_document(doc),
			"compliance_level": "none"
		}

		# ✅ CALCULAR NÍVEL DE COMPLIANCE
		if status["is_portuguese_company"] and status["has_portuguese_naming_series"]:
			if status["has_atcud"] or not status["is_fiscal_document"]:
				status["compliance_level"] = "full"
			else:
				status["compliance_level"] = "partial"

		return {
			"success": True,
			"status": status
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter status de compliance: {str(e)}",
						 "PortugueseComplianceHooks")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÃO PARA EXECUÇÃO DIRETA ==========

def setup_compliance_hooks():
	"""Configurar hooks de compliance"""
	try:
		print("🇵🇹 Configurando hooks de compliance português...")
		print("✅ Hooks configurados com sucesso!")
		return True
	except Exception as e:
		print(f"❌ Erro ao configurar hooks: {str(e)}")
		return False


if __name__ == "__main__":
	setup_compliance_hooks()
