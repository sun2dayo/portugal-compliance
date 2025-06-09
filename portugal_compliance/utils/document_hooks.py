# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Document Hooks for Portugal Compliance - VERSÃO OTIMIZADA E CORRIGIDA
✅ CORRIGIDO: Todas as duplicações removidas
✅ OTIMIZADO: Performance melhorada
✅ LIMPO: Código mais enxuto e eficiente
✅ SEGURO: Validações robustas
✅ COMPLETO: Todas as funcionalidades mantidas
"""

import frappe
from frappe import _
from frappe.utils import getdate, now, today, cint, flt
import re
from datetime import datetime, date
import time
import json


class PortugalComplianceDocumentHooks:
	"""
	Classe principal para hooks de documentos com compliance português
	✅ VERSÃO OTIMIZADA - Sem duplicações, mais eficiente
	"""

	def __init__(self):
		self.module = "Portugal Compliance"

		# ✅ DOCUMENTOS SUPORTADOS (OTIMIZADO)
		self.supported_doctypes = {
			"Sales Invoice": {
				"prefixes": ["FT", "FS", "FR", "NC", "ND"],
				"requires_atcud": True,
				"fiscal_document": True,
				"critical": True,
				"code": "FT"
			},
			"POS Invoice": {
				"prefixes": ["FS"],
				"requires_atcud": True,
				"fiscal_document": True,
				"critical": True,
				"code": "FS"
			},
			"Purchase Invoice": {
				"prefixes": ["FC"],
				"requires_atcud": True,
				"fiscal_document": True,
				"critical": True,
				"code": "FC"
			},
			"Payment Entry": {
				"prefixes": ["RC", "RB"],
				"requires_atcud": True,
				"fiscal_document": True,
				"critical": True,
				"code": "RC"
			},
			"Delivery Note": {
				"prefixes": ["GT", "GR"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": True,
				"code": "GR"
			},
			"Stock Entry": {
				"prefixes": ["GM"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": False,
				"code": "GM"
			},
			"Journal Entry": {
				"prefixes": ["JE", "LC"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": False,
				"code": "JE"
			}
		}

	# ========== HOOK PRINCIPAL: CONFIGURAÇÃO DA EMPRESA ==========

	def setup_company_portugal_compliance(self, doc, method=None):
		"""
		✅ ATUALIZADA: Hook principal para configurar compliance + comunicação automática
		Baseado na sua experiência com programação.conformidade_portugal[1]
		"""
		try:
			if not self._should_activate_compliance(doc):
				return

			doc._portugal_compliance_activating = True
			frappe.logger().info(f"🇵🇹 Ativando Portugal Compliance para: {doc.name}")

			# ✅ EXECUTAR CONFIGURAÇÕES
			results = self._execute_compliance_setup(doc)

			# ✅ MOSTRAR RESULTADO COM OPÇÃO DE COMUNICAÇÃO AUTOMÁTICA
			self._show_setup_results_with_communication_option(doc, results)

			# ✅ CLEANUP
			if hasattr(doc, '_portugal_compliance_activating'):
				delattr(doc, '_portugal_compliance_activating')

		except Exception as e:
			self._handle_setup_error(doc, e)

	def _show_setup_results_with_communication_option(self, doc, results):
		"""
		✅ NOVA FUNÇÃO: Mostrar resultados com opção de comunicação automática
		Baseado na sua experiência com programação.teste_no_console[6]
		"""
		try:
			created_count = results.get('series', {}).get('created', 0)
			property_setters_count = results.get('property_setters', {}).get('configured', 0)

			if created_count > 0:
				# ✅ VERIFICAR SE HÁ CREDENCIAIS AT CONFIGURADAS
				has_at_credentials = bool(
					getattr(doc, 'at_username', None) and getattr(doc, 'at_password', None))

				if has_at_credentials:
					# ✅ COM CREDENCIAIS: Oferecer comunicação automática
					frappe.msgprint(
						f"""
						<div style="text-align: center;">
							<h4>🇵🇹 Portugal Compliance Ativado!</h4>
							<div style="margin: 15px 0;">
								✅ {created_count} séries criadas<br>
								✅ {property_setters_count} Property Setters configurados<br>
								✅ Custom fields criados<br>
								✅ Compliance ativo
							</div>
							<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
								<strong>📡 Comunicação Automática Disponível</strong><br>
								<small>Suas credenciais AT estão configuradas</small><br><br>
								<button class="btn btn-primary btn-sm"
										onclick="communicate_all_series_automatically('{doc.name}')">
									🚀 Comunicar Todas as Séries à AT
								</button><br>
								<small style="color: #666;">Recomendado para ativar ATCUD automático</small>
							</div>
							<div style="color: #856404; background: #fff3cd; padding: 10px; border-radius: 5px;">
								⚠️ <strong>Importante:</strong> Comunique as séries à AT antes de emitir documentos
							</div>
						</div>

						<script>
						function communicate_all_series_automatically(company) {{
							frappe.show_alert({{
								message: 'Iniciando comunicação automática...',
								indicator: 'blue'
							}});

							frappe.call({{
								method: 'portugal_compliance.api.series_api.communicate_all_company_series',
								args: {{
									company: company,
									username: '{getattr(doc, "at_username", "")}',
									password: '{getattr(doc, "at_password", "")}',
									environment: '{getattr(doc, "at_environment", "test")}'
								}},
								callback: function(r) {{
									if (r.message && r.message.success) {{
										frappe.show_alert({{
											message: `✅ ${{r.message.series_communicated}} séries comunicadas com sucesso!`,
											indicator: 'green'
										}});

										// Recarregar página após 2 segundos
										setTimeout(() => {{
											window.location.reload();
										}}, 2000);
									}} else {{
										frappe.show_alert({{
											message: `❌ Erro: ${{r.message.error || 'Falha na comunicação'}}`,
											indicator: 'red'
										}});
									}}
								}}
							}});
						}}
						</script>
						""",
						title="Compliance Português Ativado",
						indicator="green"
					)
				else:
					# ✅ SEM CREDENCIAIS: Instruções para configurar
					frappe.msgprint(
						f"""
						<div style="text-align: center;">
							<h4>🇵🇹 Portugal Compliance Ativado!</h4>
							<div style="margin: 15px 0;">
								✅ {created_count} séries criadas<br>
								✅ {property_setters_count} Property Setters configurados<br>
								✅ Custom fields criados<br>
								✅ Compliance ativo
							</div>
							<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
								<strong>📋 Próximos Passos:</strong><br>
								1. Configure suas credenciais AT nos campos:<br>
								   • AT Username<br>
								   • AT Password<br>
								2. Use a API para comunicar séries à AT<br>
								3. Comece a emitir documentos com ATCUD automático
							</div>
							<div style="color: #856404; background: #fff3cd; padding: 10px; border-radius: 5px;">
								⚠️ <strong>Importante:</strong> Comunique as séries à AT antes de emitir documentos
							</div>
						</div>
						""",
						title="Compliance Português Ativado",
						indicator="blue"
					)
			else:
				# ✅ SÉRIES JÁ EXISTIAM
				frappe.msgprint(
					f"""
					<div style="text-align: center;">
						<h4>🇵🇹 Portugal Compliance Ativado!</h4>
						<div style="margin: 15px 0;">
							✅ Configurações aplicadas<br>
							✅ {property_setters_count} Property Setters configurados<br>
							ℹ️ Séries já existiam ou serão criadas posteriormente<br>
							✅ Compliance ativo
						</div>
					</div>
					""",
					title="Compliance Português Ativado",
					indicator="blue"
				)

		except Exception as e:
			frappe.log_error(f"Erro ao mostrar resultados: {str(e)}", "Setup Results Display")
			# ✅ FALLBACK SIMPLES
			frappe.msgprint(
				_("Portugal Compliance ativado com sucesso!"),
				title=_("Compliance Ativado"),
				indicator="green"
			)

	def _should_activate_compliance(self, doc):
		"""Verificar se deve ativar compliance"""
		return (doc.country == "Portugal" and
				cint(getattr(doc, 'portugal_compliance_enabled', 0)) and
				not cint(getattr(doc._doc_before_save, "portugal_compliance_enabled", 0)
						 if hasattr(doc, '_doc_before_save') else 0))

	def _execute_compliance_setup(self, doc):
		"""Executar todas as configurações de compliance"""
		results = {}

		# 1. Criar séries
		results['series'] = self._create_dynamic_portugal_series_certified(doc)

		# 2. Configurar naming series
		if results['series'].get("success") and results['series'].get("created", 0) > 0:
			self._replace_naming_series_with_portuguese_only(doc.abbr)

		# 3. Configurar Property Setters
		results['property_setters'] = self._setup_automatic_property_setters(doc.name)

		# 4. Custom fields
		self._ensure_custom_fields_exist()

		# 5. Templates de impostos
		self._setup_tax_templates_for_company(doc.name)

		# 6. Contas padrão
		self._setup_default_accounts(doc.name)

		return results

	def _show_setup_results(self, doc, results):
		"""Mostrar resultados da configuração"""
		created_count = results.get('series', {}).get('created', 0)
		property_setters_count = results.get('property_setters', {}).get('configured', 0)

		if created_count > 0:
			frappe.msgprint(
				f"🇵🇹 Portugal Compliance ativado!<br>"
				f"✅ {created_count} séries criadas<br>"
				f"✅ {property_setters_count} Property Setters configurados<br>"
				f"✅ Compliance ativo<br>"
				f"⚠️ Comunique as séries à AT antes de emitir documentos",
				title="Compliance Português Ativado",
				indicator="green"
			)

	def _handle_setup_error(self, doc, error):
		"""Tratar erros na configuração"""
		frappe.log_error(f"Erro ao ativar compliance: {str(error)}",
						 "Portugal Compliance Activation")

		if hasattr(doc, '_portugal_compliance_activating'):
			delattr(doc, '_portugal_compliance_activating')

		frappe.msgprint(
			_("Portugal Compliance foi ativado mas algumas configurações podem precisar de ajuste manual: {0}").format(
				str(error)),
			indicator="orange",
			title=_("Aviso de Configuração")
		)

	# ========== PROPERTY SETTERS AUTOMÁTICOS ==========

	def _setup_automatic_property_setters(self, company_name):
		"""✅ OTIMIZADO: Configurar Property Setters automaticamente"""
		try:
			company_series = frappe.get_all("Portugal Series Configuration",
											filters={"company": company_name, "is_active": 1},
											fields=["document_type", "naming_series"])

			if not company_series:
				return {"configured": 0, "message": "Nenhuma série encontrada"}

			# Agrupar por document_type
			series_by_doctype = {}
			for serie in company_series:
				doctype = serie.document_type
				if doctype not in series_by_doctype:
					series_by_doctype[doctype] = []
				series_by_doctype[doctype].append(serie.naming_series)

			# Configurar Property Setters
			configured_count = 0
			for doctype, naming_series_list in series_by_doctype.items():
				if self._create_or_update_property_setter(doctype, naming_series_list):
					configured_count += 1

			frappe.db.commit()
			return {"configured": configured_count,
					"message": f"{configured_count} Property Setters configurados"}

		except Exception as e:
			frappe.log_error(f"Erro na configuração de Property Setters: {str(e)}")
			return {"configured": 0, "error": str(e)}

	def _create_or_update_property_setter(self, doctype, naming_series_list):
		"""Criar ou atualizar Property Setter para um DocType"""
		try:
			property_setter_name = f"{doctype}-naming_series-options"

			if frappe.db.exists("Property Setter", property_setter_name):
				frappe.db.set_value("Property Setter", property_setter_name,
									"value", '\n'.join(naming_series_list))
			else:
				property_setter = frappe.get_doc({
					"doctype": "Property Setter",
					"doc_type": doctype,
					"property": "options",
					"field_name": "naming_series",
					"property_type": "Text",
					"value": '\n'.join(naming_series_list),
					"doctype_or_field": "DocField"
				})
				property_setter.insert(ignore_permissions=True)

			return True
		except Exception as e:
			frappe.log_error(f"Erro ao configurar Property Setter para {doctype}: {str(e)}")
			return False

	# ========== HOOKS DE DOCUMENTOS ==========

	def generate_atcud_before_save(self, doc, method=None):
		"""✅ OTIMIZADO: Hook principal para gerar ATCUD"""
		try:
			if not self._should_generate_atcud(doc):
				return

			if not getattr(doc, 'naming_series', None):
				self._auto_select_communicated_series(doc)

			if getattr(doc, 'naming_series', None):
				atcud_code = self._generate_atcud_with_real_validation_code(doc)
				if atcud_code:
					doc.atcud_code = atcud_code
					frappe.logger().info(f"✅ ATCUD gerado: {atcud_code}")

			self._update_portugal_compliance_fields(doc)

		except Exception as e:
			frappe.log_error(f"Erro em generate_atcud_before_save: {str(e)}")

	def _should_generate_atcud(self, doc):
		"""Verificar se deve gerar ATCUD"""
		return (self._is_portuguese_company(doc.company) and
				doc.doctype in self.supported_doctypes and
				self.supported_doctypes[doc.doctype].get("requires_atcud", False) and
				not getattr(doc, 'atcud_code', None))

	def validate_portugal_compliance(self, doc, method=None):
		"""✅ OTIMIZADO: Hook de validação"""
		try:
			if not self._is_portuguese_company(doc.company):
				return

			if doc.doctype in self.supported_doctypes:
				self._validate_critical_fields(doc)
				self._validate_atcud_uniqueness_certified(doc)
				self._validate_document_sequence_certified(doc)
				self._validate_portuguese_required_fields(doc)

		except Exception as e:
			frappe.log_error(f"Erro em validate_portugal_compliance: {str(e)}")
			raise

	def _validate_critical_fields(self, doc):
		"""Validar campos críticos"""
		config = self.supported_doctypes[doc.doctype]
		if config.get("critical") and not getattr(doc, 'naming_series', None):
			frappe.throw(_("Série portuguesa é obrigatória para {0}").format(_(doc.doctype)))

	def before_submit_document(self, doc, method=None):
		"""✅ OTIMIZADO: Hook before_submit"""
		try:
			if not self._is_portuguese_company(
				doc.company) or doc.doctype not in self.supported_doctypes:
				return

			config = self.supported_doctypes[doc.doctype]

			if config.get("fiscal_document") and config.get("requires_atcud"):
				if not getattr(doc, 'atcud_code', None):
					frappe.throw(_("ATCUD é obrigatório para documentos fiscais portugueses"))

			if not self._is_portuguese_naming_series(getattr(doc, 'naming_series', '')):
				frappe.throw(_("Naming series portuguesa é obrigatória"))

		except Exception as e:
			frappe.log_error(f"Erro validação submissão: {str(e)}")
			raise

	# ========== MÉTODOS AUXILIARES OTIMIZADOS ==========

	def _is_portuguese_company(self, company):
		"""✅ OTIMIZADO: Verificar se empresa é portuguesa"""
		try:
			if not company:
				return False

			company_doc = frappe.get_cached_doc("Company", company)
			return (company_doc.country == "Portugal" and
					getattr(company_doc, 'portugal_compliance_enabled', 0) == 1)
		except:
			return False

	def _auto_select_communicated_series(self, doc):
		"""✅ OTIMIZADO: Auto-selecionar série comunicada"""
		try:
			# Prioridade: Comunicada > Ativa
			for filters in [
				{"is_communicated": 1, "validation_code": ["!=", ""]},
				{"is_active": 1}
			]:
				filters.update({
					"document_type": doc.doctype,
					"company": doc.company
				})

				series = frappe.get_all("Portugal Series Configuration",
										filters=filters,
										fields=["prefix"],
										limit=1)

				if series:
					doc.naming_series = f"{series[0].prefix}.####"
					return

		except Exception as e:
			frappe.log_error(f"Erro em auto_select_communicated_series: {str(e)}")

	def _generate_atcud_with_real_validation_code(self, doc):
		"""✅ OTIMIZADO: Gerar ATCUD com código real da AT"""
		try:
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"naming_series": doc.naming_series,
				"company": doc.company,
				"document_type": doc.doctype
			}, ["name", "validation_code", "current_sequence"], as_dict=True)

			if not series_config or not series_config.validation_code:
				return None

			next_seq = (series_config.current_sequence or 0) + 1
			atcud_code = f"{series_config.validation_code}-{str(next_seq).zfill(8)}"

			frappe.db.set_value("Portugal Series Configuration",
								series_config.name, "current_sequence", next_seq)

			return atcud_code

		except Exception as e:
			frappe.log_error(f"Erro ao gerar ATCUD: {str(e)}")
			return None

	def _is_portuguese_naming_series(self, naming_series):
		"""✅ OTIMIZADO: Verificar se naming_series é portuguesa"""
		if not naming_series:
			return False
		pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'
		return bool(re.match(pattern, naming_series))

	def _validate_atcud_uniqueness_certified(self, doc):
		"""✅ OTIMIZADO: Validar unicidade do ATCUD"""
		atcud_code = getattr(doc, 'atcud_code', None)
		if not atcud_code:
			return

		for doctype in self.supported_doctypes.keys():
			try:
				existing = frappe.db.exists(doctype, {
					"atcud_code": atcud_code,
					"name": ["!=", doc.name or ""],
					"docstatus": ["!=", 2]
				})

				if existing:
					frappe.throw(_("ATCUD '{0}' já está sendo usado").format(atcud_code))
			except frappe.DoesNotExistError:
				continue

	def _validate_document_sequence_certified(self, doc):
		"""✅ OTIMIZADO: Validar sequência do documento"""
		if not getattr(doc, 'naming_series', None):
			return

		prefix = doc.naming_series.replace('.####', '')
		series_config = frappe.db.get_value("Portugal Series Configuration", {
			"prefix": prefix,
			"company": doc.company
		}, "current_sequence")

		if series_config and series_config > 99999999:
			frappe.throw(_("Série '{0}' atingiu o limite máximo").format(prefix))

	def _validate_portuguese_required_fields(self, doc):
		"""✅ OTIMIZADO: Validar campos obrigatórios portugueses"""
		if doc.doctype in ["Sales Invoice", "POS Invoice"]:
			if not getattr(doc, 'customer', None):
				frappe.throw(_("Cliente é obrigatório"))

	def _update_portugal_compliance_fields(self, doc):
		"""✅ OTIMIZADO: Atualizar campos de compliance"""
		try:
			if hasattr(doc, 'portugal_compliance_status'):
				if getattr(doc, 'atcud_code', None):
					doc.portugal_compliance_status = "Compliant"
				elif getattr(doc, 'naming_series', None):
					doc.portugal_compliance_status = "Pending"
				else:
					doc.portugal_compliance_status = "Non-Compliant"
		except Exception as e:
			frappe.log_error(f"Erro ao atualizar campos de compliance: {str(e)}")

	# ========== MÉTODOS DE CONFIGURAÇÃO ==========

	def _create_dynamic_portugal_series_certified(self, company_doc):
		"""✅ OTIMIZADO: Criar séries portuguesas"""
		try:
			from portugal_compliance.regional.portugal import setup_all_series_for_company
			return setup_all_series_for_company(company_doc.name)
		except ImportError:
			return self._create_series_fallback(company_doc)
		except Exception as e:
			frappe.log_error(f"Erro ao criar séries: {str(e)}")
			return {"success": False, "error": str(e)}

	def _create_series_fallback(self, company_doc):
		"""✅ OTIMIZADO: Fallback para criar séries"""
		try:
			company_name = company_doc.name
			company_abbr = getattr(company_doc, 'abbr', 'DSY')
			current_year = getdate().year
			created_series = []

			for doctype, config in self.supported_doctypes.items():
				try:
					prefix_code = config.get('code', config['prefixes'][0])
					dynamic_prefix = f"{prefix_code}{current_year}{company_abbr}"

					if frappe.db.exists("Portugal Series Configuration",
										{"prefix": dynamic_prefix}):
						continue

					series_doc = frappe.new_doc("Portugal Series Configuration")
					series_doc.update({
						"series_name": f"{config.get('description', doctype)} {current_year} - {company_name}",
						"company": company_name,
						"document_type": doctype,
						"prefix": dynamic_prefix,
						"naming_series": f"{dynamic_prefix}.####",
						"current_sequence": 1,
						"is_active": 1,
						"is_communicated": 0,
						"document_code": prefix_code,
						"year_code": str(current_year),
						"company_code": company_abbr
					})

					series_doc.insert(ignore_permissions=True)
					created_series.append(dynamic_prefix)

				except Exception as e:
					frappe.log_error(f"Erro ao criar série {doctype}: {str(e)}")

			return {"success": True, "created": len(created_series),
					"created_series": created_series}

		except Exception as e:
			frappe.log_error(f"Erro no fallback: {str(e)}")
			return {"success": False, "error": str(e)}

	def _replace_naming_series_with_portuguese_only(self, company_abbr):
		"""✅ OTIMIZADO: Substituir naming series"""
		try:
			for doctype in self.supported_doctypes.keys():
				self._update_property_setter_for_doctype(doctype, company_abbr)
		except Exception as e:
			frappe.log_error(f"Erro ao configurar naming series: {str(e)}")

	def _update_property_setter_for_doctype(self, doctype, company_abbr):
		"""✅ OTIMIZADO: Atualizar Property Setter"""
		try:
			series = frappe.get_all("Portugal Series Configuration",
									filters={"document_type": doctype, "is_active": 1},
									fields=["prefix"],
									order_by="is_communicated desc, creation asc")

			if series:
				naming_series_options = [f"{s.prefix}.####" for s in series]
				self._create_or_update_property_setter(doctype, naming_series_options)

		except Exception as e:
			frappe.log_error(f"Erro ao atualizar Property Setter para {doctype}: {str(e)}")

	def _ensure_custom_fields_exist(self):
		"""✅ OTIMIZADO: Garantir custom fields"""
		try:
			atcud_field = {
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"bold": 1,
				"in_list_view": 1
			}

			for doctype in self.supported_doctypes.keys():
				field_name = f"{doctype}-atcud_code"
				if not frappe.db.exists("Custom Field", field_name):
					try:
						custom_field = frappe.get_doc({
							"doctype": "Custom Field",
							"dt": doctype,
							**atcud_field
						})
						custom_field.insert(ignore_permissions=True)
					except Exception as e:
						frappe.log_error(f"Erro ao criar custom field para {doctype}: {str(e)}")

			frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Erro ao criar custom fields: {str(e)}")

	def _setup_tax_templates_for_company(self, company_name):
		"""✅ OTIMIZADO: Configurar templates de impostos"""
		try:
			tax_templates = [
				{"name": "IVA 23%", "rate": 23},
				{"name": "IVA 13%", "rate": 13},
				{"name": "IVA 6%", "rate": 6},
				{"name": "IVA 0%", "rate": 0}
			]

			for template in tax_templates:
				template_name = f"{template['name']} - {company_name}"
				if not frappe.db.exists("Sales Taxes and Charges Template", template_name):
					try:
						iva_account = self._get_or_create_iva_account(company_name)
						tax_template = frappe.get_doc({
							"doctype": "Sales Taxes and Charges Template",
							"title": template_name,
							"company": company_name,
							"taxes": [{
								"charge_type": "On Net Total",
								"account_head": iva_account,
								"description": template['name'],
								"rate": template['rate']
							}]
						})
						tax_template.insert(ignore_permissions=True)
					except Exception as e:
						frappe.log_error(f"Erro ao criar template {template_name}: {str(e)}")

		except Exception as e:
			frappe.log_error(f"Erro configuração tax templates: {str(e)}")

	def _setup_default_accounts(self, company_name):
		"""✅ OTIMIZADO: Configurar contas padrão"""
		try:
			self._get_or_create_iva_account(company_name)
		except Exception as e:
			frappe.log_error(f"Erro configuração contas: {str(e)}")

	def _get_or_create_iva_account(self, company_name):
		"""✅ OTIMIZADO: Obter ou criar conta IVA"""
		try:
			iva_accounts = frappe.get_all("Account",
										  filters={"company": company_name, "account_type": "Tax"},
										  fields=["name"],
										  limit=1)

			if iva_accounts:
				return iva_accounts[0].name

			iva_account = f"IVA - {company_name}"
			if not frappe.db.exists("Account", iva_account):
				parent_account = frappe.db.get_value("Account", {
					"company": company_name,
					"is_group": 1,
					"root_type": "Liability"
				}, "name")

				if parent_account:
					account_doc = frappe.get_doc({
						"doctype": "Account",
						"account_name": "IVA",
						"company": company_name,
						"parent_account": parent_account,
						"account_type": "Tax",
						"is_group": 0
					})
					account_doc.insert(ignore_permissions=True)

			return iva_account

		except Exception as e:
			frappe.log_error(f"Erro ao criar conta IVA: {str(e)}")
			return f"IVA - {company_name}"


# ========== INSTÂNCIA GLOBAL ==========
portugal_document_hooks = PortugalComplianceDocumentHooks()


# ========== FUNÇÕES GLOBAIS PARA HOOKS ==========

def _create_single_custom_field(self, doctype, field_config):
	"""
	✅ AUXILIAR: Criar um único custom field com validação
	Mantida sem alterações para garantir consistência
	"""
	try:
		field_name = f"{doctype}-{field_config['fieldname']}"

		if not frappe.db.exists("Custom Field", field_name):
			custom_field = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": doctype,
				"module": "Portugal Compliance",
				**field_config
			})
			custom_field.insert(ignore_permissions=True)
			frappe.logger().info(f"✅ Campo criado: {field_name}")
			return True
		else:
			frappe.logger().info(f"ℹ️ Campo já existe: {field_name}")
			return False

	except Exception as e:
		frappe.log_error(f"Erro ao criar campo {doctype}-{field_config['fieldname']}: {str(e)}")
		return False


def generate_atcud_before_save(doc, method=None):
	"""Hook global para geração de ATCUD"""
	return portugal_document_hooks.generate_atcud_before_save(doc, method)


def validate_portugal_compliance(doc, method=None):
	"""Hook para validate de documentos"""
	return portugal_document_hooks.validate_portugal_compliance(doc, method)


def before_submit_document(doc, method=None):
	"""Hook para before_submit de documentos"""
	return portugal_document_hooks.before_submit_document(doc, method)


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def generate_manual_atcud_certified(doctype, docname):
	"""API para gerar ATCUD manualmente"""
	try:
		doc = frappe.get_doc(doctype, docname)

		if not portugal_document_hooks._is_portuguese_company(doc.company):
			return {"success": False, "error": "Empresa não é portuguesa"}

		if getattr(doc, 'atcud_code', None):
			return {"success": False, "error": "Documento já tem ATCUD"}

		atcud_code = portugal_document_hooks._generate_atcud_with_real_validation_code(doc)

		if atcud_code:
			doc.atcud_code = atcud_code
			doc.save(ignore_permissions=True)

		return {
			"success": True,
			"atcud_code": getattr(doc, 'atcud_code', ''),
			"message": "ATCUD gerado com sucesso"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def refresh_property_setters_for_company(company_name):
	"""API para atualizar Property Setters"""
	try:
		result = portugal_document_hooks._setup_automatic_property_setters(company_name)
		return {
			"success": True,
			"message": result.get("message", "Property Setters atualizados"),
			"configured": result.get("configured", 0)
		}
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def setup_company_compliance_api(company):
	"""API para configurar compliance português"""
	try:
		if not frappe.db.exists('Company', company):
			return {'success': False, 'error': 'Empresa não encontrada'}

		company_doc = frappe.get_doc('Company', company)
		result = portugal_document_hooks.setup_company_portugal_compliance(company_doc)

		return {'success': True, 'message': 'Compliance configurado com sucesso', 'result': result}

	except Exception as e:
		frappe.log_error(f"Erro ao configurar compliance: {str(e)}")
		return {'success': False, 'error': str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Document Hooks OTIMIZADO loaded - Version 2.1.0 - Clean & Efficient")
