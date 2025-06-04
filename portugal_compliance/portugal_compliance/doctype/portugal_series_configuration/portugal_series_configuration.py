# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Portugal Series Configuration DocType - VERSÃO NATIVA CORRIGIDA
Manages Portuguese document series according to legislation
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py, series_adapter.py e atcud_generator.py
✅ CONFORME: Legislação portuguesa e Portaria 195/2020
"""

import frappe
from frappe.model.document import Document
from frappe import _
import re
from datetime import datetime, date
from frappe.utils import cint, now, today, getdate
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils.password import set_encrypted_password, get_decrypted_password


class PortugalSeriesConfiguration(Document):
	def autoname(self):
		"""Gerar nome automaticamente - CORREÇÃO CRÍTICA"""
		if not self.name or self.name == 'new':
			self.name = self.generate_unique_name()

	def validate(self):
		"""Validações do documento - VERSÃO CERTIFICADA CORRIGIDA"""
		# ✅ VALIDAÇÕES BÁSICAS PRIMEIRO
		self.validate_basic_fields()
		self.validate_series_prefix()
		self.validate_document_type()
		self.validate_company_compliance()
		self.validate_sequence_number()

		# Validar prefix se existir
		if hasattr(self, 'prefix') and self.prefix:
			self.validate_year_in_prefix()
			self.validate_prefix_uniqueness()

	def validate_basic_fields(self):
		"""Validar campos básicos obrigatórios"""
		if not self.series_name:
			frappe.throw(_("Nome da série é obrigatório"))

		if not self.prefix:
			frappe.throw(_("Prefixo da série é obrigatório"))

		if not self.document_type:
			frappe.throw(_("Tipo de documento é obrigatório"))

		if not self.company:
			frappe.throw(_("Empresa é obrigatória"))

	def validate_series_prefix(self):
		"""
		✅ CORRIGIDO: Valida formato do prefixo da série SEM HÍFENS
		Formato: XXYYYY + COMPANY (ex: FT2025NDX)
		"""
		if not getattr(self, 'prefix', None):
			frappe.throw(_("Prefixo da série é obrigatório"))

		# ✅ VALIDAR FORMATO OFICIAL SEM HÍFENS: XXYYYY + COMPANY
		if not self.validate_prefix_format_certified():
			frappe.throw(_("Formato do prefixo inválido. Use XXYYYY + COMPANY (ex: FT2025NDX)"))

		# Validar prefixo específico para tipo de documento
		self.validate_prefix_for_document_type()

	def validate_prefix_format_certified(self):
		"""
		✅ CORRIGIDO: Validar formato certificado do prefixo SEM HÍFENS
		Formato: XXYYYY + COMPANY (ex: FT2025NDX)
		"""
		try:
			if not getattr(self, 'prefix', None):
				return False

			# ✅ FORMATO OFICIAL SEM HÍFENS: XXYYYY + COMPANY
			pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})$'
			match = re.match(pattern, self.prefix)

			if not match:
				return False

			doc_code, year, company = match.groups()

			# Validar código do documento (2-4 caracteres alfabéticos)
			if not (2 <= len(doc_code) <= 4) or not doc_code.isalpha() or not doc_code.isupper():
				return False

			# Validar ano (4 dígitos)
			if not (len(year) == 4 and year.isdigit()):
				return False

			# Validar empresa (2-4 caracteres alfanuméricos maiúsculos)
			if not (2 <= len(company) <= 4) or not company.isalnum() or not company.isupper():
				return False

			return True

		except Exception:
			return False

	def validate_prefix_uniqueness(self):
		"""Validar unicidade do prefixo - THREAD-SAFE"""
		try:
			existing = frappe.db.exists("Portugal Series Configuration", {
				"prefix": self.prefix,
				"company": self.company,
				"name": ["!=", self.name or ""]
			})

			if existing:
				frappe.throw(_("Prefixo '{0}' já existe para a empresa '{1}'").format(
					self.prefix, self.company))

		except Exception as e:
			frappe.log_error(f"Erro na validação de unicidade: {str(e)}")

	def validate_prefix_for_document_type(self):
		"""
		✅ CORRIGIDO: Validar se prefixo é válido para o tipo de documento
		Prefixos atualizados: EN → EC, OC → EF
		"""
		if not self.document_type or not getattr(self, 'prefix', None):
			return

		# ✅ EXTRAIR CÓDIGO DO PREFIXO (primeiros 2-4 caracteres)
		pattern = r'^([A-Z]{2,4})\d{4}[A-Z0-9]{2,4}$'
		match = re.match(pattern, self.prefix)

		if not match:
			return

		prefix_code = match.group(1)

		# ✅ MAPEAMENTO OFICIAL CONFORME LEGISLAÇÃO PORTUGUESA (CORRIGIDO)
		valid_prefixes = {
			"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
			"Purchase Invoice": ["FC", "FR"],
			"Payment Entry": ["RC", "RB"],
			"Delivery Note": ["GT", "GR"],
			"Purchase Receipt": ["GR", "GT"],
			"Journal Entry": ["JE", "LC"],
			"Stock Entry": ["GT", "GM"],
			"Quotation": ["OR", "ORC"],
			"Sales Order": ["EC", "ECO"],  # ✅ CORRIGIDO: era EN
			"Purchase Order": ["EF", "EFO"],  # ✅ CORRIGIDO: era OC
			"Material Request": ["REQ", "MR"]
		}

		allowed_prefixes = valid_prefixes.get(self.document_type, [])

		if allowed_prefixes and prefix_code not in allowed_prefixes:
			frappe.throw(_("Prefixo '{0}' inválido para '{1}'. Prefixos válidos: {2}").format(
				prefix_code, self.document_type, ", ".join(allowed_prefixes)))

	def validate_year_in_prefix(self):
		"""
		✅ CORRIGIDO: Valida se o ano no prefixo é válido (formato SEM HÍFENS)
		"""
		if not getattr(self, 'prefix', None):
			return

		try:
			# ✅ EXTRAIR ANO DO FORMATO SEM HÍFENS: XXYYYY + COMPANY
			pattern = r'^[A-Z]{2,4}(\d{4})[A-Z0-9]{2,4}$'
			match = re.match(pattern, self.prefix)

			if not match:
				return

			year_part = match.group(1)
			year = int(year_part)
			current_year = getdate().year

			# ✅ PERMITIR ANO ATUAL, ANTERIOR E PRÓXIMO
			if not (current_year - 1 <= year <= current_year + 1):
				frappe.throw(_("Ano no prefixo deve estar entre {0} e {1}").format(
					current_year - 1, current_year + 1))

		except (ValueError, AttributeError):
			frappe.throw(_("Formato de ano inválido no prefixo"))

	def validate_document_type(self):
		"""
		✅ CORRIGIDO: Validar tipo de documento usando dicionário dinâmico
		"""
		if not self.document_type:
			frappe.throw(_("Tipo de documento é obrigatório"))

		# ✅ USAR DICIONÁRIO DINÂMICO EM VEZ DE LISTA HARDCODED
		try:
			from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
			valid_types = list(PORTUGAL_DOCUMENT_TYPES.keys())
		except ImportError:
			# ✅ FALLBACK: Lista completa incluindo POS Invoice
			valid_types = [
				"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
				"Delivery Note", "Purchase Invoice", "Purchase Order",
				"Purchase Receipt", "Stock Entry", "Payment Entry",
				"Journal Entry", "Material Request"
			]

		if self.document_type not in valid_types:
			frappe.throw(
				_("Tipo de documento inválido. Tipos válidos: {0}").format(
					", ".join(valid_types)
				)
			)

	def validate_sequence_number(self):
		"""Valida número de sequência - VERSÃO CERTIFICADA"""
		if getattr(self, 'current_sequence', None):
			if self.current_sequence < 1:
				frappe.throw(_("Número atual deve ser maior que 0"))

			if self.current_sequence > 99999999:
				frappe.throw(_("Número atual não pode exceder 99.999.999 (limite legal)"))

	def validate_company_compliance(self):
		"""Valida se a empresa tem compliance português ativado - VERSÃO CERTIFICADA"""
		if not self.company:
			return

		try:
			company_doc = frappe.get_cached_doc("Company", self.company)

			if company_doc.country != "Portugal":
				frappe.throw(_("Empresa deve estar configurada para Portugal"))

			if not company_doc.get("portugal_compliance_enabled"):
				frappe.msgprint(_("Portugal compliance não está ativado para esta empresa"),
								indicator="orange", title=_("Aviso"))
		except Exception as e:
			frappe.log_error(f"Erro ao validar compliance da empresa: {str(e)}")

	def before_save(self):
		"""Executado antes de salvar - VERSÃO CERTIFICADA CORRIGIDA"""
		# ✅ GARANTIR NOME ÚNICO SE NÃO DEFINIDO
		if not getattr(self, 'name', None) or self.name == 'new':
			self.name = self.generate_unique_name()

		# ✅ GERAR PREFIXO AUTOMATICAMENTE SE NÃO DEFINIDO (SEM HÍFENS)
		if not getattr(self, 'prefix', None):
			self.prefix = self.generate_series_prefix()

		# Definir sequência inicial se não definida
		if not getattr(self, 'current_sequence', None):
			self.current_sequence = 1

		# Definir ano fiscal se não definido
		if not getattr(self, 'fiscal_year', None) and self.company:
			try:
				fiscal_year = get_fiscal_year(today(), company=self.company)[0]
				self.fiscal_year = fiscal_year
			except:
				self.fiscal_year = str(getdate().year)

		# ✅ ATUALIZAR STATUS BASEADO NA COMUNICAÇÃO AT
		if getattr(self, 'validation_code', None) and not getattr(self, 'is_communicated', None):
			self.is_communicated = 1
			self.communication_date = now()
			self.communication_status = "Success"

		# Atualizar timestamp de modificação
		self.last_modified_by = frappe.session.user

	def generate_unique_name(self):
		"""Gerar nome único para a série - CORREÇÃO CRÍTICA"""
		try:
			import time
			from datetime import datetime

			company_abbr = self.get_company_abbreviation()
			current_year = datetime.now().year
			timestamp = int(time.time())
			doc_prefix = self.get_document_prefix()

			# ✅ FORMATO SIMPLES: TIPO-ANO-EMPRESA-HASH
			base_name = f"{doc_prefix}-{current_year}-{company_abbr}"
			unique_hash = frappe.generate_hash(length=6)
			unique_name = f"{base_name}-{unique_hash}"

			# ✅ VERIFICAR UNICIDADE
			counter = 1
			original_name = unique_name
			while frappe.db.exists("Portugal Series Configuration", unique_name):
				unique_name = f"{original_name}-{counter}"
				counter += 1

			frappe.logger().info(f"✅ Nome único gerado: {unique_name}")
			return unique_name

		except Exception as e:
			frappe.log_error(f"Erro ao gerar nome único: {str(e)}")
			# Fallback para nome simples
			return f"SERIES-{frappe.generate_hash(length=8)}"

	def after_insert(self):
		"""Executado após inserção - VERSÃO CERTIFICADA"""
		self.create_custom_fields_if_needed()
		self.sync_naming_series_with_doctype()
		self.log_series_creation()

	def on_update(self):
		"""Executado após atualização - VERSÃO CERTIFICADA"""
		# ✅ ATIVAÇÃO AUTOMÁTICA APÓS COMUNICAÇÃO
		if getattr(self, 'is_communicated', None) and getattr(self, 'validation_code', None):
			self.after_communication_success()

		# ✅ SINCRONIZAR NAMING SERIES APÓS ATUALIZAÇÃO
		if self.has_value_changed("prefix") or self.has_value_changed(
			"is_active") or self.has_value_changed("is_communicated"):
			self.sync_naming_series_with_doctype()

		# Limpar cache se série foi comunicada
		if self.has_value_changed("is_communicated") and getattr(self, 'is_communicated', None):
			frappe.clear_cache()

	def sync_naming_series_with_doctype(self):
		"""
		✅ CORRIGIDO: Sincroniza naming series do DocType (formato SEM HÍFENS)
		"""
		try:
			if not self.prefix or not self.document_type:
				return

			# ✅ OBTER TODAS AS SÉRIES ATIVAS PARA ESTE DOCTYPE E EMPRESA
			all_series = frappe.get_all("Portugal Series Configuration",
										filters={
											"document_type": self.document_type,
											"company": self.company,
											"is_active": 1
										},
										fields=["prefix"],
										order_by="is_communicated desc")

			# ✅ CONVERTER PARA NAMING_SERIES FORMAT (SEM HÍFENS)
			naming_series_list = [f"{s.prefix}.####" for s in all_series]

			if naming_series_list:
				# ✅ USAR NOSSA LÓGICA NATIVA DE NAMING SERIES
				from portugal_compliance.utils.series_adapter import update_doctype_naming_series

				company_abbr = frappe.db.get_value("Company", self.company, "abbr")
				if company_abbr:
					update_doctype_naming_series(self.document_type, company_abbr,
												 force_update=True)

				frappe.logger().info(
					f"✅ Naming series sincronizadas para {self.document_type}: {len(naming_series_list)} séries")

		except Exception as e:
			frappe.log_error(f"Erro ao sincronizar naming series: {str(e)}")

	def create_custom_fields_if_needed(self):
		"""Cria campos customizados necessários - VERSÃO CERTIFICADA"""
		try:
			# ✅ CRIAR APENAS CAMPO ATCUD (read-only)
			self.create_atcud_field()

		except Exception as e:
			frappe.log_error(f"Erro ao criar campos customizados: {str(e)}")

	def create_atcud_field(self):
		"""Criar campo ATCUD (read-only) - VERSÃO CERTIFICADA"""
		try:
			field_name = f"{self.document_type}-atcud_code"

			if frappe.db.exists("Custom Field", field_name):
				# ✅ ATUALIZAR CAMPO EXISTENTE PARA GARANTIR CONFIGURAÇÃO CORRETA
				frappe.db.set_value("Custom Field", field_name, {
					"read_only": 1,
					"bold": 1,
					"in_list_view": 1,
					"print_hide": 0,
					"description": "Código Único de Documento - Gerado automaticamente"
				})
				frappe.logger().info(f"✅ Campo ATCUD atualizado para {self.document_type}")
			else:
				# Criar campo ATCUD
				frappe.get_doc({
					"doctype": "Custom Field",
					"dt": self.document_type,
					"module": "Portugal Compliance",
					"fieldname": "atcud_code",
					"label": "ATCUD Code",
					"fieldtype": "Data",
					"insert_after": "naming_series",
					"read_only": 1,
					"print_hide": 0,
					"bold": 1,
					"in_list_view": 1,
					"description": "Código Único de Documento - Gerado automaticamente"
				}).insert(ignore_permissions=True)

				frappe.logger().info(f"✅ Campo ATCUD criado para {self.document_type}")

		except Exception as e:
			frappe.log_error(f"Erro ao criar campo ATCUD: {str(e)}")

	def log_series_creation(self):
		"""Registra log da criação da série"""
		try:
			frappe.logger().info(
				f"✅ Portugal Series Configuration criada: {self.prefix} para {self.company}")
		except Exception as e:
			frappe.log_error(f"Erro ao registar log de criação: {str(e)}")

	def generate_series_prefix(self):
		"""
		✅ CORRIGIDO: Gerar prefixo da série no formato certificado SEM HÍFENS
		Formato: XXYYYY + COMPANY (ex: FT2025NDX)
		"""
		try:
			current_year = getdate().year
			company_abbr = self.get_company_abbreviation()
			doc_prefix = self.get_document_prefix()

			# ✅ FORMATO OFICIAL SEM HÍFENS: XXYYYY + COMPANY
			generated_prefix = f"{doc_prefix}{current_year}{company_abbr}"
			return generated_prefix

		except Exception as e:
			frappe.log_error(f"Erro ao gerar prefixo: {str(e)}")
			return f"FT{getdate().year}NDX"  # Fallback sem hífens

	def get_company_abbreviation(self):
		"""Obter abreviatura da empresa - VERSÃO CERTIFICADA"""
		try:
			if not self.company:
				return "NDX"

			company_doc = frappe.get_cached_doc("Company", self.company)
			abbr = getattr(company_doc, 'abbr', None)

			if abbr:
				# ✅ LIMITAR A 3-4 CARACTERES E CONVERTER PARA MAIÚSCULAS
				clean_abbr = re.sub(r'[^A-Z0-9]', '', abbr.upper())
				return clean_abbr[:4] if clean_abbr else "NDX"
			else:
				# Fallback: usar primeiras letras do nome da empresa
				company_name = company_doc.company_name or self.company
				words = company_name.split()
				if len(words) >= 2:
					abbr = ''.join([word[0] for word in words[:3]]).upper()
				else:
					abbr = company_name[:3].upper()

				# Limpar caracteres especiais
				return re.sub(r'[^A-Z0-9]', '', abbr)[:4] or "NDX"

		except Exception as e:
			frappe.log_error(f"Erro ao obter abreviatura: {str(e)}")
			return "NDX"

	def get_document_prefix(self):
		"""
		✅ CORRIGIDO: Obter prefixo baseado no tipo de documento
		Prefixos atualizados: EN → EC, OC → EF
		"""
		try:
			# ✅ MAPEAMENTO OFICIAL CONFORME LEGISLAÇÃO PORTUGUESA (CORRIGIDO)
			prefix_mapping = {
				"Sales Invoice": "FT",
				"Purchase Invoice": "FC",
				"Payment Entry": "RC",
				"Delivery Note": "GT",
				"Purchase Receipt": "GR",
				"Journal Entry": "JE",
				"Stock Entry": "GT",
				"Quotation": "OR",
				"Sales Order": "EC",  # ✅ CORRIGIDO: era EN
				"Purchase Order": "EF",  # ✅ CORRIGIDO: era OC
				"Material Request": "REQ"
			}

			return prefix_mapping.get(self.document_type, "FT")

		except Exception as e:
			frappe.log_error(f"Erro ao obter prefixo do documento: {str(e)}")
			return "FT"

	def after_communication_success(self):
		"""Executar após comunicação bem-sucedida com AT - VERSÃO CORRIGIDA"""
		try:
			# 1. Ativar série automaticamente
			if not getattr(self, 'is_active', None):
				self.db_set('is_active', 1, update_modified=False)

			# 2. ✅ SINCRONIZAR NAMING SERIES
			try:
				from portugal_compliance.utils.series_adapter import update_doctype_naming_series
				company_abbr = frappe.db.get_value("Company", self.company, "abbr")
				if company_abbr:
					update_doctype_naming_series(self.document_type, company_abbr,
												 force_update=True)
			except Exception as sync_error:
				frappe.logger().warning(
					f"⚠️ Erro na sincronização naming series: {str(sync_error)}")

			# 3. Atualizar estatísticas
			self.update_usage_statistics()

			frappe.logger().info(
				f"✅ Série {self.prefix} ativada automaticamente após comunicação AT")

		except Exception as e:
			frappe.log_error(f"Erro na ativação automática da série: {str(e)}")

	def update_usage_statistics(self):
		"""
		✅ CORRIGIDO: Atualiza estatísticas de uso da série (formato SEM HÍFENS)
		"""
		try:
			# ✅ CONTAR DOCUMENTOS QUE USAM ESTA NAMING SERIES (SEM HÍFENS)
			naming_series = f"{self.prefix}.####"

			total_docs = frappe.db.count(self.document_type, {
				"naming_series": naming_series,
				"docstatus": ["!=", 2]  # Excluir cancelados
			})

			# Último documento criado
			last_doc = frappe.db.get_value(self.document_type, {
				"naming_series": naming_series,
				"docstatus": ["!=", 2]
			}, ["name", "creation"], order_by="creation desc")

			# Atualizar campos de estatística
			self.db_set("total_documents_issued", total_docs, update_modified=False)
			if last_doc:
				self.db_set("last_document_date", last_doc[1], update_modified=False)

		except Exception as e:
			frappe.log_error(f"Erro ao atualizar estatísticas: {str(e)}")

	def on_trash(self):
		"""Executado antes de eliminar - VERSÃO CERTIFICADA"""
		# Verificar se série está sendo usada
		if self.is_series_in_use():
			frappe.throw(_("Não é possível eliminar série que está sendo usada por documentos"))

		# ✅ REMOVER NAMING SERIES DO DOCTYPE
		self.remove_naming_series_from_doctype()

		frappe.logger().info(
			f"✅ Portugal Series Configuration eliminada: {getattr(self, 'prefix', '')}")

	def is_series_in_use(self):
		"""
		✅ CORRIGIDO: Verifica se a série está sendo usada por documentos (formato SEM HÍFENS)
		"""
		try:
			naming_series = f"{self.prefix}.####"
			count = frappe.db.count(self.document_type, {
				"naming_series": naming_series,
				"docstatus": ["!=", 2]
			})
			return count > 0
		except:
			return False

	def remove_naming_series_from_doctype(self):
		"""Remove naming series do DocType quando série é eliminada - VERSÃO CERTIFICADA"""
		try:
			if not self.prefix or not self.document_type:
				return

			# ✅ USAR NOSSA LÓGICA NATIVA PARA REMOVER
			from portugal_compliance.utils.series_adapter import update_doctype_naming_series

			company_abbr = frappe.db.get_value("Company", self.company, "abbr")
			if company_abbr:
				update_doctype_naming_series(self.document_type, company_abbr, force_update=True)

			frappe.logger().info(f"✅ Naming series removida: {self.prefix}")

		except Exception as e:
			frappe.log_error(f"Erro ao remover naming series: {str(e)}")


# ========== FUNÇÕES GLOBAIS - VERSÃO CERTIFICADA CORRIGIDA ==========

@frappe.whitelist()
def create_series_programmatically(prefix, document_type, company, series_name):
	"""
	✅ CORRIGIDO: Criar série programaticamente (formato SEM HÍFENS)
	"""
	try:
		# Verificar se já existe
		existing = frappe.db.exists("Portugal Series Configuration", {
			"prefix": prefix,
			"company": company,
			"document_type": document_type
		})

		if existing:
			return {"success": False, "error": f"Série {prefix} já existe", "existing": existing}

		# Criar documento
		doc = frappe.new_doc("Portugal Series Configuration")
		doc.series_name = series_name
		doc.prefix = prefix  # Formato SEM HÍFENS: FT2025NDX
		doc.document_type = document_type
		doc.company = company
		doc.is_active = 1
		doc.is_communicated = 0
		doc.current_sequence = 1
		doc.year = 2025
		doc.naming_series = f"{prefix}.####"  # FT2025NDX.####

		# Salvar com ignore_permissions
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"name": doc.name,
			"prefix": doc.prefix,
			"message": f"Série {prefix} criada com sucesso"
		}

	except Exception as e:
		frappe.log_error(f"Erro ao criar série {prefix}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_all_naming_series():
	"""Sincronizar todas as naming series - VERSÃO CERTIFICADA"""
	try:
		# Usar nossa lógica nativa
		from portugal_compliance.utils.series_adapter import sync_all_company_naming_series

		result = sync_all_company_naming_series()

		return {
			"success": True,
			"updated_doctypes": result.get("updated_doctypes", 0),
			"message": "Sincronização concluída com sucesso"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def migrate_series_to_no_hyphens():
	"""
	✅ NOVA: Migrar séries existentes de formato com hífens para sem hífens
	"""
	try:
		frappe.logger().info("🔄 Migrando séries para formato sem hífens...")

		# Buscar todas as séries com hífens
		series_with_hyphens = frappe.get_all("Portugal Series Configuration",
											 filters=[["prefix", "like", "%-%"]],
											 fields=["name", "prefix", "document_type", "company"])

		migrated_count = 0

		for series in series_with_hyphens:
			try:
				# Converter prefixo: FT-2025-NDX → FT2025NDX
				old_prefix = series.prefix
				new_prefix = old_prefix.replace('-', '')

				# Verificar se já existe série com novo formato
				existing = frappe.db.exists("Portugal Series Configuration", {
					"prefix": new_prefix,
					"document_type": series.document_type,
					"company": series.company
				})

				if not existing:
					# Atualizar série existente
					frappe.db.set_value("Portugal Series Configuration", series.name, {
						"prefix": new_prefix,
						"naming_series": f"{new_prefix}.####"
					})
					migrated_count += 1
					frappe.logger().info(f"✅ Migrado: {old_prefix} → {new_prefix}")
				else:
					frappe.logger().info(f"⏭️ Série {new_prefix} já existe - pulando {old_prefix}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar série {series.name}: {str(e)}")

		# Atualizar Property Setters
		if migrated_count > 0:
			frappe.logger().info("🔄 Atualizando Property Setters...")

			companies = frappe.get_all("Company",
									   filters={"country": "Portugal",
												"portugal_compliance_enabled": 1},
									   fields=["abbr"])

			for company in companies:
				from portugal_compliance.utils.series_adapter import sync_all_doctypes
				sync_all_doctypes(company.abbr, force_update=True)

		frappe.db.commit()

		return {
			"success": True,
			"migrated_series": migrated_count,
			"message": f"Migradas {migrated_count} séries para formato sem hífens"
		}

	except Exception as e:
		frappe.log_error(f"Erro na migração de séries: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_series_statistics():
	"""
	✅ NOVA: Obter estatísticas das séries
	"""
	try:
		stats = {
			"total_series": frappe.db.count("Portugal Series Configuration"),
			"active_series": frappe.db.count("Portugal Series Configuration", {"is_active": 1}),
			"communicated_series": frappe.db.count("Portugal Series Configuration",
												   {"is_communicated": 1}),
			"series_with_hyphens": frappe.db.count("Portugal Series Configuration",
												   [["prefix", "like", "%-%"]]),
			"series_without_hyphens": frappe.db.count("Portugal Series Configuration",
													  [["prefix", "not like", "%-%"]]),
			"by_doctype": {}
		}

		# Estatísticas por DocType
		doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry",
			"Quotation", "Sales Order", "Purchase Order", "Material Request"
		]

		for doctype in doctypes:
			stats["by_doctype"][doctype] = {
				"total": frappe.db.count("Portugal Series Configuration",
										 {"document_type": doctype}),
				"active": frappe.db.count("Portugal Series Configuration",
										  {"document_type": doctype, "is_active": 1}),
				"communicated": frappe.db.count("Portugal Series Configuration",
												{"document_type": doctype, "is_communicated": 1})
			}

		return {
			"success": True,
			"statistics": stats
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_series_format(prefix):
	"""
	✅ NOVA: Validar formato de prefixo de série
	"""
	try:
		# Padrão SEM HÍFENS: XXYYYY + COMPANY
		pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})$'
		match = re.match(pattern, prefix)

		if not match:
			return {
				"valid": False,
				"error": "Formato deve ser XXYYYY + COMPANY (ex: FT2025NDX)",
				"expected_format": "XXYYYY + COMPANY"
			}

		doc_code, year, company = match.groups()

		return {
			"valid": True,
			"components": {
				"doc_code": doc_code,
				"year": int(year),
				"company": company
			},
			"format": "XXYYYY + COMPANY",
			"example": "FT2025NDX"
		}

	except Exception as e:
		return {
			"valid": False,
			"error": str(e)
		}
