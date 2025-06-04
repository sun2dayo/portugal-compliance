# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, cint, now, today, flt
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils.password import set_encrypted_password, get_decrypted_password
import re


class PortugalDocumentSeries(Document):
	def validate(self):
		"""Validações do documento"""
		self.validate_series_name()
		self.validate_prefix_format()
		self.validate_document_type()
		self.check_duplicate_series()
		self.validate_sequence_number()
		self.validate_company_compliance()
		self.validate_prefix_for_document_type()
		self.validate_series_configuration_link()

	def validate_series_configuration_link(self):
		"""Validar ligação com Portugal Series Configuration"""
		# ✅ CORREÇÃO: Verificar se campo existe antes de acessar
		series_config = getattr(self, 'series_configuration', None)

		if series_config:
			try:
				# Verificar se a configuração existe e está comunicada
				config = frappe.get_doc("Portugal Series Configuration", series_config)

				if not config.is_communicated:
					frappe.throw(
						_("A configuração da série '{0}' ainda não foi comunicada à AT").format(
							config.series_name))

				if not config.validation_code:
					frappe.throw(
						_("A configuração da série '{0}' não tem código ATCUD válido").format(
							config.series_name))

				# Sincronizar dados da configuração
				self.validation_code = config.validation_code
				self.at_environment = config.at_environment
				self.communication_date = config.communication_date

			except frappe.DoesNotExistError:
				frappe.throw(_("Configuração de série '{0}' não encontrada").format(series_config))
		else:
			# Campo não existe ou está vazio - não é crítico
			frappe.logger().info("Campo series_configuration não existe ou está vazio")

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

	def validate_prefix_format(self):
		"""Valida formato do prefixo da série"""
		if not self.prefix:
			frappe.throw(_("Series prefix is required"))

		# Formato: XX-YYYY-COMPANY ou XXX-YYYY-COMPANY
		pattern = r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$"
		if not re.match(pattern, self.prefix):
			frappe.throw(_("Invalid prefix format. Use: XX-YYYY-COMPANY (e.g., FT-2025-COMP)"))

		# Validar ano no prefixo
		self.validate_year_in_prefix()

	def validate_year_in_prefix(self):
		"""Valida se o ano no prefixo é válido"""
		if not getattr(self, 'prefix', None):
			return

		try:
			prefix_parts = self.prefix.split('-')
			if len(prefix_parts) < 2:
				return

			year_part = prefix_parts[1]
			year = int(year_part)

			current_year = getdate().year

			if not (current_year - 1 <= year <= current_year + 1):
				frappe.throw(_("O ano no prefixo deve estar entre {0} e {1}").format(
					current_year - 1, current_year + 1
				))

		except (IndexError, ValueError):
			return

	def validate_prefix_for_document_type(self):
		"""Valida se o prefixo é adequado para o tipo de documento"""
		if not self.document_type or not self.prefix:
			return

		# Mapeamento expandido de prefixos válidos por tipo de documento
		valid_prefixes = {
			"Sales Invoice": ["FT", "FS", "FR", "NC", "ND"],
			"Purchase Invoice": ["FC", "FT"],
			"Payment Entry": ["RC", "RB"],
			"Delivery Note": ["GT", "GR"],
			"Purchase Receipt": ["GR", "GT"],
			"Journal Entry": ["JE"],
			"Stock Entry": ["GT"],
			"Quotation": ["OR", "ORC"],
			"Sales Order": ["EC", "ECO"],
			"Purchase Order": ["EF", "EFO"],
			"Material Request": ["REQ", "MR"]
		}

		prefix_code = self.prefix.split('-')[0]
		document_prefixes = valid_prefixes.get(self.document_type, [])

		if document_prefixes and prefix_code not in document_prefixes:
			frappe.throw(
				_("Invalid prefix '{0}' for document type '{1}'. Valid prefixes: {2}").format(
					prefix_code, self.document_type, ", ".join(document_prefixes)
				))

	def validate_document_type(self):
		"""Valida tipo de documento - EXPANDIDO para legislação portuguesa"""
		valid_types = [
			# Documentos obrigatórios ATCUD
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry",
			# Documentos adicionais compliance
			"Quotation", "Sales Order", "Purchase Order", "Material Request"
		]

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
		"""Executado após inserção"""
		self.create_custom_fields_if_needed()
		self.log_series_creation()
		self.update_usage_trend()

	def on_update(self):
		"""Executado após atualização"""
		if self.validation_code:
			self.update_naming_series()
			self.update_usage_statistics()

		# Limpar cache se série foi atualizada
		if self.has_value_changed("validation_code"):
			frappe.clear_cache()

	def update_naming_series(self):
		"""Atualiza naming series do doctype"""
		try:
			# Obter opções atuais de naming series
			current_options = frappe.db.get_value("DocType", self.document_type, "autoname") or ""
			current_list = [opt.strip() for opt in current_options.split('\n') if opt.strip()]

			# Adicionar nova série se não existir
			new_series = f"{self.prefix}.####"
			if new_series not in current_list:
				current_list.append(new_series)

				# Atualizar DocType
				new_options = '\n'.join(current_list)
				frappe.db.set_value("DocType", self.document_type, "autoname", new_options)

				# Limpar cache do DocType
				frappe.clear_cache(doctype=self.document_type)

				frappe.logger().info(
					f"Naming series updated for {self.document_type}: {new_series}")

		except Exception as e:
			frappe.log_error(f"Error updating naming series: {str(e)}", "Portugal Document Series")

	def create_custom_fields_if_needed(self):
		"""✅ SOLUÇÃO DEFINITIVA: Criar campos para TODOS os DocTypes da legislação portuguesa"""
		try:
			# ========== CONFIGURAÇÃO COMPLETA DOS DOCTYPES ==========
			doctypes_config = [
				# Documentos obrigatórios ATCUD (Decreto-Lei n.º 28/2019)
				{
					"doctype": "Sales Invoice",
					"insert_after": "naming_series",
					"portugal_series_reqd": 1,
					"atcud_reqd": 1,
					"priority": "high"
				},
				{
					"doctype": "Purchase Invoice",
					"insert_after": "naming_series",
					"portugal_series_reqd": 1,
					"atcud_reqd": 1,
					"priority": "high"
				},
				{
					"doctype": "Payment Entry",
					"insert_after": "naming_series",
					"portugal_series_reqd": 1,
					"atcud_reqd": 1,
					"priority": "high"
				},
				{
					"doctype": "Delivery Note",
					"insert_after": "naming_series",
					"portugal_series_reqd": 1,
					"atcud_reqd": 1,
					"priority": "high"
				},
				{
					"doctype": "Purchase Receipt",
					"insert_after": "naming_series",
					"portugal_series_reqd": 1,
					"atcud_reqd": 1,
					"priority": "high"
				},
				{
					"doctype": "Journal Entry",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 1,
					"priority": "medium"
				},
				{
					"doctype": "Stock Entry",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 1,
					"priority": "medium"
				},
				# Documentos adicionais compliance
				{
					"doctype": "Quotation",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 0,
					"priority": "low"
				},
				{
					"doctype": "Sales Order",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 0,
					"priority": "low"
				},
				{
					"doctype": "Purchase Order",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 0,
					"priority": "low"
				},
				{
					"doctype": "Material Request",
					"insert_after": "naming_series",
					"portugal_series_reqd": 0,
					"atcud_reqd": 0,
					"priority": "low"
				}
			]

			# ========== CRIAR CAMPOS PARA TODOS OS DOCTYPES ==========
			for config in doctypes_config:
				try:
					doctype = config["doctype"]

					# ✅ 1. CAMPO PORTUGAL_SERIES
					series_field_name = f"{doctype}-portugal_series"
					if not frappe.db.exists("Custom Field", series_field_name):
						portugal_series_field = frappe.get_doc({
							"doctype": "Custom Field",
							"dt": doctype,
							"fieldname": "portugal_series",
							"label": "Portugal Series",
							"fieldtype": "Link",
							"options": "Portugal Document Series",
							"insert_after": config["insert_after"],
							"reqd": config["portugal_series_reqd"],
							"in_list_view": 1 if config["portugal_series_reqd"] else 0,
							"bold": 1 if config["portugal_series_reqd"] else 0,
							"description": f"Série portuguesa para compliance fiscal - {config['priority']} priority"
						})
						portugal_series_field.insert(ignore_permissions=True)
						frappe.logger().info(f"✅ Campo portugal_series criado para {doctype}")

					# ✅ 2. CAMPO ATCUD_CODE
					atcud_field_name = f"{doctype}-atcud_code"
					if not frappe.db.exists("Custom Field", atcud_field_name):
						atcud_field = frappe.get_doc({
							"doctype": "Custom Field",
							"dt": doctype,
							"fieldname": "atcud_code",
							"label": "ATCUD Code",
							"fieldtype": "Data",
							"insert_after": "portugal_series",
							"read_only": 1,
							"print_hide": 0,
							"bold": 1 if config["atcud_reqd"] else 0,
							"in_list_view": 1 if config["atcud_reqd"] else 0,
							"description": "Código Único de Documento - obrigatório em Portugal"
						})
						atcud_field.insert(ignore_permissions=True)
						frappe.logger().info(f"✅ Campo atcud_code criado para {doctype}")

					# ✅ 3. CAMPO ATCUD_DISPLAY (para impressão)
					atcud_display_field_name = f"{doctype}-atcud_display"
					if not frappe.db.exists("Custom Field", atcud_display_field_name):
						atcud_display_field = frappe.get_doc({
							"doctype": "Custom Field",
							"dt": doctype,
							"fieldname": "atcud_display",
							"label": "ATCUD Display",
							"fieldtype": "Data",
							"insert_after": "atcud_code",
							"read_only": 1,
							"print_hide": 0,
							"hidden": 1,  # Oculto na interface, visível na impressão
							"description": "ATCUD formatado para exibição (ATCUD:CODIGO-NUMERO)"
						})
						atcud_display_field.insert(ignore_permissions=True)
						frappe.logger().info(f"✅ Campo atcud_display criado para {doctype}")

					# ✅ 4. CAMPO PORTUGAL_COMPLIANCE_STATUS
					compliance_field_name = f"{doctype}-portugal_compliance_status"
					if not frappe.db.exists("Custom Field", compliance_field_name):
						compliance_field = frappe.get_doc({
							"doctype": "Custom Field",
							"dt": doctype,
							"fieldname": "portugal_compliance_status",
							"label": "Portugal Compliance Status",
							"fieldtype": "Select",
							"options": "Pending\nCompliant\nNon-Compliant\nExempt",
							"insert_after": "atcud_display",
							"default": "Pending",
							"read_only": 1,
							"hidden": 1,
							"description": "Status de compliance português para este documento"
						})
						compliance_field.insert(ignore_permissions=True)
						frappe.logger().info(
							f"✅ Campo portugal_compliance_status criado para {doctype}")

					frappe.logger().info(f"🎯 Todos os campos criados com sucesso para {doctype}")

				except Exception as e:
					frappe.log_error(f"❌ Erro ao criar campos para {config['doctype']}: {str(e)}",
									 "Portugal Document Series - Custom Fields")
					# Continuar com próximo DocType mesmo se um falhar
					continue

			# ========== COMMIT E LIMPEZA DE CACHE ==========
			frappe.db.commit()
			frappe.clear_cache()

			frappe.logger().info("🎉 TODOS os campos customizados criados com sucesso!")
			frappe.logger().info(
				"📋 DocTypes atualizados: Sales Invoice, Purchase Invoice, Payment Entry, Delivery Note, Purchase Receipt, Journal Entry, Stock Entry, Quotation, Sales Order, Purchase Order, Material Request")

		except Exception as e:
			frappe.log_error(f"❌ Erro geral ao criar campos customizados: {str(e)}",
							 "Portugal Document Series - Custom Fields")

	# ========== MÉTODOS DE GERAÇÃO DE ATCUD PARA DOCUMENTOS ==========

	@frappe.whitelist()
	def generate_atcud_for_document(self, document_sequence=None):
		"""Gerar ATCUD completo para documento específico - CORRIGIDO"""
		try:
			if not self.validation_code:
				frappe.throw(
					_("Série não tem código de validação AT. Configure primeiro a comunicação."))

			# Usar sequência fornecida ou obter próxima
			if document_sequence is None:
				document_sequence = self.get_next_number()

			# ✅ FORMATO OFICIAL CORRETO: CODIGO_VALIDACAO-NUMERO_SEQUENCIAL
			# Baseado nos search results: "TES123TE-4561"
			validation_code = str(self.validation_code).strip()
			sequence_formatted = f"{document_sequence:08d}"  # 8 dígitos com zeros à esquerda

			atcud_code = f"{validation_code}-{sequence_formatted}"
			atcud_display = f"ATCUD:{atcud_code}"

			# Validar formato gerado
			if not self.validate_atcud_format(atcud_code):
				frappe.throw(_("Erro na geração do ATCUD: formato inválido"))

			return {
				"success": True,
				"atcud_code": atcud_code,  # Ex: AAJFJ6VHXK-00000001
				"atcud_display": atcud_display,  # Ex: ATCUD:AAJFJ6VHXK-00000001
				"validation_code": validation_code,  # Ex: AAJFJ6VHXK
				"sequence_number": document_sequence,
				"series_name": self.series_name
			}

		except Exception as e:
			frappe.log_error(f"Error generating ATCUD: {str(e)}")
			return {"success": False, "error": str(e)}

	def validate_atcud_format(self, atcud_code):
		"""Validar formato do ATCUD gerado"""
		try:
			# Baseado nos search results: deve ter hífen separando código e sequência
			if "-" not in atcud_code:
				return False

			parts = atcud_code.split("-")
			if len(parts) != 2:
				return False

			validation_code, sequence = parts

			# Código de validação: 8+ caracteres, sem 0 e 1, sem acentos
			if len(validation_code) < 8:
				return False

			# Sequência: deve ser numérica
			try:
				int(sequence)
				return True
			except ValueError:
				return False

		except Exception:
			return False

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

	# ========== MÉTODOS DE ESTATÍSTICAS (mantidos do código original) ==========

	def update_usage_statistics(self):
		"""Atualiza estatísticas de uso da série"""
		try:
			# Contar documentos que usam esta série
			total_docs = frappe.db.count(self.document_type, {
				"portugal_series": self.name,
				"docstatus": ["!=", 2]  # Excluir cancelados
			})

			# Último documento criado
			last_doc_data = frappe.db.get_value(self.document_type, {
				"portugal_series": self.name,
				"docstatus": ["!=", 2]
			}, ["creation", "posting_date"], order_by="creation desc")

			# Calcular uso médio mensal
			monthly_usage = self.calculate_monthly_usage()

			# Calcular projeção anual
			annual_projection = self.calculate_annual_projection(monthly_usage)

			# Atualizar campos usando db_set para evitar loops
			self.db_set("total_documents_issued", total_docs, update_modified=False)

			if last_doc_data:
				last_date = last_doc_data[1] if last_doc_data[1] else last_doc_data[0].date()
				self.db_set("last_document_date", last_date, update_modified=False)

			if monthly_usage:
				self.db_set("average_monthly_usage", monthly_usage, update_modified=False)

			if annual_projection:
				self.db_set("projected_annual_usage", annual_projection, update_modified=False)

			# Atualizar tendência de uso
			self.update_usage_trend()

		except Exception as e:
			frappe.log_error(f"Error updating usage statistics: {str(e)}")

	def calculate_monthly_usage(self):
		"""Calcula uso médio mensal"""
		try:
			from dateutil.relativedelta import relativedelta

			end_date = today()
			start_date = end_date - relativedelta(months=12)

			monthly_counts = frappe.db.sql("""
                SELECT
                    YEAR(posting_date) as year,
                    MONTH(posting_date) as month,
                    COUNT(*) as count
                FROM `tab{doctype}`
                WHERE portugal_series = %s
                AND posting_date BETWEEN %s AND %s
                AND docstatus != 2
                GROUP BY YEAR(posting_date), MONTH(posting_date)
            """.format(doctype=self.document_type), (self.name, start_date, end_date),
										   as_dict=True)

			if monthly_counts:
				total_docs = sum(month['count'] for month in monthly_counts)
				months_with_data = len(monthly_counts)
				return flt(total_docs / months_with_data, 2) if months_with_data > 0 else 0

			return 0

		except Exception as e:
			frappe.log_error(f"Error calculating monthly usage: {str(e)}")
			return 0

	def calculate_annual_projection(self, monthly_usage):
		"""Calcula projeção anual baseada no uso médio mensal"""
		try:
			if monthly_usage:
				return cint(monthly_usage * 12)
			return 0
		except:
			return 0

	def update_usage_trend(self):
		"""Atualiza tendência de uso"""
		try:
			if not self.total_documents_issued:
				trend = "New"
			elif self.total_documents_issued < 10:
				trend = "New"
			elif self.average_monthly_usage:
				# Comparar últimos 3 meses com 3 meses anteriores
				recent_usage = self.get_recent_usage(3)
				previous_usage = self.get_previous_usage(3, 6)

				if recent_usage > previous_usage * 1.1:
					trend = "Increasing"
				elif recent_usage < previous_usage * 0.9:
					trend = "Decreasing"
				else:
					trend = "Stable"
			else:
				trend = "Stable"

			self.db_set("usage_trend", trend, update_modified=False)

		except Exception as e:
			frappe.log_error(f"Error updating usage trend: {str(e)}")

	def get_recent_usage(self, months):
		"""Obtém uso dos últimos N meses"""
		try:
			from dateutil.relativedelta import relativedelta

			end_date = today()
			start_date = end_date - relativedelta(months=months)

			count = frappe.db.count(self.document_type, {
				"portugal_series": self.name,
				"posting_date": ["between", [start_date, end_date]],
				"docstatus": ["!=", 2]
			})

			return count
		except:
			return 0

	def get_previous_usage(self, months, offset):
		"""Obtém uso de período anterior"""
		try:
			from dateutil.relativedelta import relativedelta

			end_date = today() - relativedelta(months=offset)
			start_date = end_date - relativedelta(months=months)

			count = frappe.db.count(self.document_type, {
				"portugal_series": self.name,
				"posting_date": ["between", [start_date, end_date]],
				"docstatus": ["!=", 2]
			})

			return count
		except:
			return 0

	# ========== MÉTODOS AUXILIARES ==========

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

		# Log da ação
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"content": f"Sequence reset from {old_number} to {new_start} by {frappe.session.user}"
		}).insert(ignore_permissions=True)

		frappe.msgprint(
			_("Sequence reset successfully from {0} to {1}").format(old_number, new_start))

	@frappe.whitelist()
	def get_usage_statistics(self):
		"""Retorna estatísticas detalhadas de uso"""
		try:
			stats = {
				"series_name": self.series_name,
				"prefix": self.prefix,
				"document_type": self.document_type,
				"current_number": self.current_number,
				"validation_code": self.validation_code,
				"total_documents": self.total_documents_issued or 0,
				"last_document_date": self.last_document_date,
				"average_monthly_usage": self.average_monthly_usage or 0,
				"projected_annual_usage": self.projected_annual_usage or 0,
				"usage_trend": self.usage_trend or "New",
				"available_numbers": 99999999 - (self.current_number or 1)
			}

			# Obter último documento
			if self.total_documents_issued and self.total_documents_issued > 0:
				last_doc = frappe.db.get_value(self.document_type, {
					"portugal_series": self.name,
					"docstatus": ["!=", 2]
				}, ["name", "creation"], order_by="creation desc")

				if last_doc:
					stats["last_document"] = {
						"name": last_doc[0],
						"creation": last_doc[1]
					}

			return stats

		except Exception as e:
			frappe.log_error(f"Error getting usage statistics: {str(e)}")
			return {}

	def on_trash(self):
		"""Executado antes de eliminar"""
		# Verificar se série está sendo usada
		if self.is_series_in_use():
			frappe.throw(_("Cannot delete series that is being used by documents"))

		# Log da eliminação
		frappe.logger().info(f"Portugal Document Series deleted: {self.series_name}")

	def is_series_in_use(self):
		"""Verifica se a série está sendo usada por documentos"""
		try:
			count = frappe.db.count(self.document_type, {
				"portugal_series": self.name,
				"docstatus": ["!=", 2]
			})
			return count > 0
		except:
			return False

	@frappe.whitelist()
	def get_usage_stats(self):
		"""Método whitelisted para compatibilidade com JS"""
		return self.get_usage_statistics()

	# ========== MÉTODOS DE COMPLIANCE AUTOMÁTICO ==========

	@frappe.whitelist()
	def validate_all_documents_compliance(self):
		"""Validar compliance de todos os documentos desta série"""
		try:
			# Buscar todos os documentos desta série
			documents = frappe.get_all(self.document_type,
									   filters={"portugal_series": self.name,
												"docstatus": ["!=", 2]},
									   fields=["name", "atcud_code", "portugal_compliance_status"])

			compliance_stats = {
				"total": len(documents),
				"compliant": 0,
				"non_compliant": 0,
				"pending": 0
			}

			for doc in documents:
				if doc.get("atcud_code") and doc.get("portugal_compliance_status") == "Compliant":
					compliance_stats["compliant"] += 1
				elif not doc.get("atcud_code"):
					compliance_stats["non_compliant"] += 1
				else:
					compliance_stats["pending"] += 1

			return {
				"success": True,
				"compliance_stats": compliance_stats,
				"compliance_rate": (
						compliance_stats["compliant"] / compliance_stats["total"] * 100) if
				compliance_stats["total"] > 0 else 0
			}

		except Exception as e:
			frappe.log_error(f"Error validating documents compliance: {str(e)}")
			return {"success": False, "error": str(e)}


# ========== FUNÇÕES GLOBAIS PARA INTEGRAÇÃO COM DOCUMENTOS ==========

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
def create_all_custom_fields():
	"""API para criar campos customizados em todos os DocTypes (uso manual)"""
	try:
		# Criar uma série temporária apenas para executar o método
		temp_series = frappe.new_doc("Portugal Document Series")
		temp_series.create_custom_fields_if_needed()

		return {"success": True, "message": "Todos os campos customizados foram criados"}
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_portugal_compliance_setup():
	"""Validar se setup de compliance português está correto"""
	try:
		# Verificar se todos os campos existem
		required_doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
		]

		missing_fields = []
		for doctype in required_doctypes:
			if not frappe.db.has_column(doctype, "portugal_series"):
				missing_fields.append(f"{doctype}.portugal_series")
			if not frappe.db.has_column(doctype, "atcud_code"):
				missing_fields.append(f"{doctype}.atcud_code")

		return {
			"success": len(missing_fields) == 0,
			"missing_fields": missing_fields,
			"message": "Setup completo" if len(
				missing_fields) == 0 else f"Faltam {len(missing_fields)} campos"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}
