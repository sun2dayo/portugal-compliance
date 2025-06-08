# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, cint, now, today, flt
from erpnext.accounts.utils import get_fiscal_year
import re


class PortugalDocumentSeries(Document):
	def validate(self):
		"""
		✅ ADAPTADO: Validações alinhadas com nova abordagem
		"""
		self.validate_series_name()
		self.validate_prefix_format_new()
		self.validate_document_type()
		self.check_duplicate_series()
		self.validate_sequence_number()
		self.validate_company_compliance()
		self.validate_prefix_for_document_type_new()
		self.sync_with_portugal_series_configuration()

	def sync_with_portugal_series_configuration(self):
		"""
		✅ NOVO: Sincronizar com Portugal Series Configuration
		"""
		try:
			# Buscar configuração correspondente
			config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": self.prefix,
				"company": self.company,
				"document_type": self.document_type
			}, ["name", "validation_code", "is_communicated"], as_dict=True)

			if config:
				# Sincronizar dados
				self.validation_code = config.validation_code
				self.is_communicated = config.is_communicated
				self.series_configuration = config.name

				frappe.logger().info(
					f"✅ Sincronizado com Portugal Series Configuration: {config.name}")
			else:
				# Criar configuração se não existir
				self.create_portugal_series_configuration()

		except Exception as e:
			frappe.log_error(f"Erro na sincronização: {str(e)}")

	def create_portugal_series_configuration(self):
		"""
		✅ NOVO: Criar Portugal Series Configuration correspondente
		"""
		try:
			config = frappe.get_doc({
				"doctype": "Portugal Series Configuration",
				"series_name": self.series_name,
				"company": self.company,
				"document_type": self.document_type,
				"prefix": self.prefix,
				"naming_series": f"{self.prefix}.####",
				"current_sequence": self.current_number or 1,
				"is_active": 1,
				"is_communicated": getattr(self, 'is_communicated', 0),
				"document_code": self.prefix.split('-')[0] if '-' in self.prefix else self.prefix[
																					  :2],
				"year_code": str(getdate().year),
				"company_code": self.company[:3].upper()
			})

			config.insert(ignore_permissions=True)
			self.series_configuration = config.name

			frappe.logger().info(f"✅ Portugal Series Configuration criada: {config.name}")

		except Exception as e:
			frappe.log_error(f"Erro ao criar configuração: {str(e)}")

	def validate_prefix_format_new(self):
		"""
		✅ ADAPTADO: Validar formato compatível com nova abordagem
		"""
		if not self.prefix:
			frappe.throw(_("Series prefix is required"))

		# ✅ ACEITAR AMBOS OS FORMATOS:
		# Novo: XXYYYY + COMPANY (ex: FT2025DSY)
		# Antigo: XX-YYYY-COMPANY (ex: FT-2025-DSY)

		new_pattern = r"^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$"  # FT2025DSY
		old_pattern = r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$"  # FT-2025-DSY

		if not (re.match(new_pattern, self.prefix) or re.match(old_pattern, self.prefix)):
			frappe.throw(
				_("Formato de prefixo inválido. Use: XXYYYY+EMPRESA (ex: FT2025DSY) ou XX-YYYY-EMPRESA (ex: FT-2025-DSY)"))

		# Validar ano no prefixo
		self.validate_year_in_prefix_new()

	def validate_year_in_prefix_new(self):
		"""
		✅ ADAPTADO: Validar ano em ambos os formatos
		"""
		if not getattr(self, 'prefix', None):
			return

		try:
			# Extrair ano do prefixo
			if '-' in self.prefix:
				# Formato antigo: FT-2025-DSY
				prefix_parts = self.prefix.split('-')
				if len(prefix_parts) >= 2:
					year_part = prefix_parts[1]
			else:
				# Formato novo: FT2025DSY
				year_match = re.search(r'\d{4}', self.prefix)
				if year_match:
					year_part = year_match.group()
				else:
					return

			year = int(year_part)
			current_year = getdate().year

			if not (current_year - 1 <= year <= current_year + 1):
				frappe.throw(_("O ano no prefixo deve estar entre {0} e {1}").format(
					current_year - 1, current_year + 1
				))

		except (IndexError, ValueError):
			return

	def validate_prefix_for_document_type_new(self):
		"""
		✅ ADAPTADO: Validações alinhadas com nova abordagem
		"""
		if not self.document_type or not self.prefix:
			return

		# ✅ USAR MAPEAMENTO DA NOVA ABORDAGEM
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		if self.document_type in PORTUGAL_DOCUMENT_TYPES:
			valid_code = PORTUGAL_DOCUMENT_TYPES[self.document_type]['code']

			# Extrair código do prefixo
			if '-' in self.prefix:
				prefix_code = self.prefix.split('-')[0]
			else:
				prefix_code = re.match(r'^[A-Z]{2,4}', self.prefix).group() if re.match(
					r'^[A-Z]{2,4}', self.prefix) else ""

			if prefix_code != valid_code:
				frappe.throw(
					_("Prefixo '{0}' inválido para '{1}'. Use: {2}").format(
						prefix_code, self.document_type, valid_code
					))

	def validate_series_name(self):
		"""Valida nome único da série"""
		if not self.series_name:
			frappe.throw(_("Series name is required"))

		# Verificar se nome é único
		if frappe.db.exists("Portugal Document Series", {
			"series_name": self.series_name,
			"name": ["!=", self.name or ""]
		}):
			frappe.throw(_("Series name '{0}' already exists").format(self.series_name))

	def validate_document_type(self):
		"""
		✅ ADAPTADO: Usar tipos da nova abordagem
		"""
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		valid_types = list(PORTUGAL_DOCUMENT_TYPES.keys())

		if self.document_type not in valid_types:
			frappe.throw(
				_("Invalid document type. Valid types: {0}").format(", ".join(valid_types)))

	def validate_sequence_number(self):
		"""Valida número de sequência"""
		if self.current_number and self.current_number < 1:
			frappe.throw(_("Current number must be greater than 0"))

		if self.current_number and self.current_number > 99999999:
			frappe.throw(_("Current number cannot exceed 99,999,999"))

	def validate_company_compliance(self):
		"""Valida se a empresa tem compliance português ativado"""
		if not self.company:
			return

		try:
			company_doc = frappe.get_doc("Company", self.company)

			if company_doc.country != "Portugal":
				frappe.throw(_("Company must be configured for Portugal"))

			if not company_doc.get("portugal_compliance_enabled"):
				frappe.msgprint(_("Portugal compliance is not enabled for this company"),
								indicator="orange", title=_("Warning"))
		except Exception as e:
			frappe.log_error(f"Error validating company compliance: {str(e)}")

	def check_duplicate_series(self):
		"""Verifica duplicação de séries"""
		if not self.prefix or not self.company:
			return

		filters = {
			"prefix": self.prefix,
			"company": self.company,
			"name": ["!=", self.name or ""]
		}

		existing = frappe.db.exists("Portugal Document Series", filters)

		if existing:
			frappe.throw(_("Series prefix '{0}' already exists for company '{1}'").format(
				self.prefix, self.company
			))

	def before_save(self):
		"""Executado antes de salvar"""
		# Definir sequência inicial se não definida
		if not self.current_number:
			self.current_number = 1

		# Definir ano fiscal se não definido
		if not self.fiscal_year and self.company:
			try:
				fiscal_year = get_fiscal_year(today(), company=self.company)[0]
				self.fiscal_year = fiscal_year
			except:
				pass

		# Auto-gerar series_name se não definido
		if not self.series_name:
			self.series_name = f"{self.prefix}-{self.document_type.replace(' ', '')}"

		# Atualizar campos de auditoria
		if not self.created_by_user:
			self.created_by_user = frappe.session.user

		self.last_modified_by_user = frappe.session.user

	def after_insert(self):
		"""
		✅ ADAPTADO: Não criar custom fields (nova abordagem usa hooks)
		"""
		self.log_series_creation()
		self.update_usage_trend()

	def on_update(self):
		"""Executado após atualização"""
		if self.validation_code:
			self.update_usage_statistics()

		# Sincronizar com Portugal Series Configuration
		self.sync_with_portugal_series_configuration()

		# Limpar cache se série foi atualizada
		if self.has_value_changed("validation_code"):
			frappe.clear_cache()

	# ========== MÉTODOS DE GERAÇÃO DE ATCUD ADAPTADOS ==========

	@frappe.whitelist()
	def generate_atcud_for_document(self, document_sequence=None):
		"""
		✅ ADAPTADO: Gerar ATCUD usando nova abordagem
		"""
		try:
			if not self.validation_code:
				frappe.throw(
					_("Série não tem código de validação AT. Configure primeiro a comunicação."))

			# Usar sequência fornecida ou obter próxima
			if document_sequence is None:
				document_sequence = self.get_next_number()

			# ✅ FORMATO NOVO: 0.SEQUENCIAL (conforme Portaria 195/2020)
			atcud_code = f"0.{document_sequence}"
			atcud_display = f"ATCUD:{atcud_code}"

			return {
				"success": True,
				"atcud_code": atcud_code,  # Ex: 0.1
				"atcud_display": atcud_display,  # Ex: ATCUD:0.1
				"validation_code": self.validation_code,
				"sequence_number": document_sequence,
				"series_name": self.series_name
			}

		except Exception as e:
			frappe.log_error(f"Error generating ATCUD: {str(e)}")
			return {"success": False, "error": str(e)}

	def get_next_number(self):
		"""Obtém próximo número da sequência de forma thread-safe"""
		try:
			# Usar transação para evitar conflitos
			frappe.db.sql("SELECT GET_LOCK(%s, 10)", (f"series_lock_{self.name}",))

			current = self.current_number
			self.current_number += 1
			self.save(ignore_permissions=True)

			frappe.db.sql("SELECT RELEASE_LOCK(%s)", (f"series_lock_{self.name}",))

			return current

		except Exception as e:
			frappe.log_error(f"Error getting next number: {str(e)}")
			frappe.db.sql("SELECT RELEASE_LOCK(%s)", (f"series_lock_{self.name}",))
			return self.current_number

	# ========== MÉTODOS DE ESTATÍSTICAS (SIMPLIFICADOS) ==========

	def update_usage_statistics(self):
		"""Atualiza estatísticas de uso da série"""
		try:
			# Contar documentos que usam esta série via naming_series
			naming_series = f"{self.prefix}.####"

			total_docs = frappe.db.count(self.document_type, {
				"naming_series": naming_series,
				"company": self.company,
				"docstatus": ["!=", 2]
			})

			# Atualizar usando db_set para evitar loops
			self.db_set("total_documents_issued", total_docs, update_modified=False)

			# Calcular uso médio mensal
			monthly_usage = self.calculate_monthly_usage()
			if monthly_usage:
				self.db_set("average_monthly_usage", monthly_usage, update_modified=False)

			# Atualizar tendência
			self.update_usage_trend()

		except Exception as e:
			frappe.log_error(f"Error updating usage statistics: {str(e)}")

	def calculate_monthly_usage(self):
		"""Calcula uso médio mensal"""
		try:
			from dateutil.relativedelta import relativedelta

			end_date = today()
			start_date = end_date - relativedelta(months=12)
			naming_series = f"{self.prefix}.####"

			monthly_counts = frappe.db.sql("""
                SELECT
                    YEAR(posting_date) as year,
                    MONTH(posting_date) as month,
                    COUNT(*) as count
                FROM `tab{doctype}`
                WHERE naming_series = %s
                AND company = %s
                AND posting_date BETWEEN %s AND %s
                AND docstatus != 2
                GROUP BY YEAR(posting_date), MONTH(posting_date)
            """.format(doctype=self.document_type),
										   (naming_series, self.company, start_date, end_date),
										   as_dict=True)

			if monthly_counts:
				total_docs = sum(month['count'] for month in monthly_counts)
				months_with_data = len(monthly_counts)
				return flt(total_docs / months_with_data, 2) if months_with_data > 0 else 0

			return 0

		except Exception as e:
			frappe.log_error(f"Error calculating monthly usage: {str(e)}")
			return 0

	def update_usage_trend(self):
		"""Atualiza tendência de uso"""
		try:
			if not self.total_documents_issued:
				trend = "New"
			elif self.total_documents_issued < 10:
				trend = "New"
			else:
				trend = "Stable"

			self.db_set("usage_trend", trend, update_modified=False)

		except Exception as e:
			frappe.log_error(f"Error updating usage trend: {str(e)}")

	def log_series_creation(self):
		"""Registra log da criação da série"""
		try:
			frappe.logger().info(
				f"Portugal Document Series created: {self.series_name} ({self.prefix}) for {self.company}")
		except Exception as e:
			frappe.log_error(f"Error logging series creation: {str(e)}")

	@frappe.whitelist()
	def reset_sequence(self, new_start=1):
		"""Reinicia sequência da série"""
		if not frappe.has_permission(self.doctype, "write"):
			frappe.throw(_("Insufficient permissions to reset sequence"))

		old_number = self.current_number
		self.current_number = cint(new_start)
		self.save()

		# Sincronizar com Portugal Series Configuration
		if hasattr(self, 'series_configuration') and self.series_configuration:
			try:
				config = frappe.get_doc("Portugal Series Configuration", self.series_configuration)
				config.current_sequence = cint(new_start)
				config.save(ignore_permissions=True)
			except:
				pass

		frappe.msgprint(
			_("Sequence reset successfully from {0} to {1}").format(old_number, new_start))

	def on_trash(self):
		"""Executado antes de eliminar"""
		# Verificar se série está sendo usada
		if self.is_series_in_use():
			frappe.throw(_("Cannot delete series that is being used by documents"))

		# Eliminar Portugal Series Configuration correspondente
		if hasattr(self, 'series_configuration') and self.series_configuration:
			try:
				frappe.delete_doc("Portugal Series Configuration", self.series_configuration,
								  ignore_permissions=True)
			except:
				pass

		frappe.logger().info(f"Portugal Document Series deleted: {self.series_name}")

	def is_series_in_use(self):
		"""Verifica se a série está sendo usada por documentos"""
		try:
			naming_series = f"{self.prefix}.####"
			count = frappe.db.count(self.document_type, {
				"naming_series": naming_series,
				"company": self.company,
				"docstatus": ["!=", 2]
			})
			return count > 0
		except:
			return False


# ========== FUNÇÕES GLOBAIS ADAPTADAS ==========

@frappe.whitelist()
def get_atcud_for_document(series_name, document_sequence=None):
	"""API global para gerar ATCUD para documento específico"""
	try:
		series_doc = frappe.get_doc("Portugal Document Series", series_name)
		return series_doc.generate_atcud_for_document(document_sequence)
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_series_for_document_type(document_type, company=None):
	"""Obter séries disponíveis para tipo de documento"""
	try:
		filters = {"document_type": document_type, "is_active": 1}
		if company:
			filters["company"] = company

		series = frappe.get_all("Portugal Document Series",
								filters=filters,
								fields=["name", "series_name", "prefix", "validation_code",
										"current_number"])

		return {"success": True, "series": series}
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_all_series_with_configuration():
	"""
	✅ NOVO: Sincronizar todas as séries com Portugal Series Configuration
	"""
	try:
		series_list = frappe.get_all("Portugal Document Series",
									 fields=["name"])

		synced_count = 0
		for series in series_list:
			try:
				series_doc = frappe.get_doc("Portugal Document Series", series.name)
				series_doc.sync_with_portugal_series_configuration()
				synced_count += 1
			except Exception as e:
				frappe.log_error(f"Erro ao sincronizar série {series.name}: {str(e)}")

		return {
			"success": True,
			"message": f"{synced_count} séries sincronizadas com sucesso",
			"synced_count": synced_count
		}

	except Exception as e:
		return {"success": False, "error": str(e)}
