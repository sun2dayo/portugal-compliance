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
			# Purchase Invoice removida (2026-08-22): ATCUD/assinatura RSA
			# aplicam-se por lei a documentos EMITIDOS a clientes (Portaria
			# 195/2020), nunca a faturas de compra RECEBIDAS de
			# fornecedores. Gerar ATCUD aqui nunca teve base legal - a
			# fatura de compra e da responsabilidade fiscal de quem a
			# emitiu (o fornecedor), nao da novadx. Nunca foi comunicada a
			# serie (nem devia), so o ATCUD/assinatura local eram gerados
			# indevidamente. Ver hooks.py: bloco doc_events["Purchase
			# Invoice"] removido no mesmo commit.
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

		# 5. Templates de impostos + contas SNC 2433x por taxa (Fase 7:
		# taxonomia AT completa, substitui a conta generica "Duties and
		# Taxes" pela conta real do Plano de Contas SNC português)
		from portugal_compliance.setup.tax_setup import setup_tax_templates_for_company
		try:
			results['tax_templates'] = setup_tax_templates_for_company(doc.name, region="PT")
		except Exception as e:
			frappe.log_error(f"Erro ao configurar taxonomia AT de IVA para {doc.name}: {str(e)}")

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

			# Sem isto, processos ja em execucao (workers/gunicorn) mantem
			# a meta antiga em cache - o Select de naming_series ficaria a
			# oferecer/defaultar para as opcoes anteriores ate um restart
			# manual, o que ja causou um problema real (fatura normal
			# criada na serie NC por engano, com cache desatualizada).
			frappe.clear_cache(doctype=doctype)

			return True
		except Exception as e:
			frappe.log_error(f"Erro ao configurar Property Setter para {doctype}: {str(e)}")
			return False

	# ========== HOOKS DE DOCUMENTOS ==========

	def generate_atcud_before_save(self, doc, method=None):
		"""
		Hook principal para gerar ATCUD. Delega para ATCUDGenerator
		(utils/atcud_generator.py), que e o unico gerador de ATCUD do
		modulo - inclui assinatura digital RSA-SHA1, QR code com os
		campos corretos, registo estruturado em ATCUD Log e sequencia
		extraida da naming_series nativa do Frappe.

		Existia anteriormente um segundo gerador aqui mesmo
		(_generate_atcud_with_real_validation_code), com um contador de
		sequencia proprio (o mesmo bug de dessincronizacao ja corrigido
		em ATCUDGenerator) e sem assinatura/QR/log - nunca chamava
		ATCUDGenerator, apesar de este ser claramente o gerador mais
		completo e ser o que o proprio codigo diz estar alinhado com
		document_hooks.py. Mantida como metodo nao utilizado para
		referencia ate a Fase 3 (decisao sobre codigo morto) decidir se
		vale a pena remover.
		"""
		try:
			if not self._should_generate_atcud(doc):
				return

			if not getattr(doc, 'naming_series', None):
				self._auto_select_communicated_series(doc)

			if not getattr(doc, 'naming_series', None):
				return

			from portugal_compliance.utils.atcud_generator import ATCUDGenerator
			result = ATCUDGenerator().generate_atcud_for_document(doc)

			if result.get("success"):
				doc.atcud_code = result["atcud_code"]
				frappe.logger().info(f"✅ ATCUD gerado: {result['atcud_code']}")
			else:
				frappe.log_error(
					f"Falha ao gerar ATCUD para {doc.doctype} {doc.name}: {result.get('error')}",
					"generate_atcud_before_save",
				)

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

			self._validate_tax_exemption_soft(doc)

		except Exception as e:
			frappe.log_error(f"Erro em validate_portugal_compliance: {str(e)}")
			raise

	def _validate_tax_exemption_soft(self, doc):
		"""
		Aviso brando (msgprint, nao bloqueia) se uma linha isenta (0%)
		nao tem motivo de isencao, ou se uma linha com IVA > 0% tem um
		motivo de isencao preenchido por engano. Corre em todo o save,
		incluindo rascunhos - por isso nunca usa frappe.throw aqui (ver
		_validate_tax_exemption_hard, em before_submit, para o bloqueio
		rigido).
		"""
		if doc.doctype not in ("Sales Invoice", "Delivery Note"):
			return
		if not getattr(doc, "items", None):
			return
		try:
			from portugal_compliance.utils.tax_breakdown import get_line_at_tax_codes
			line_codes = get_line_at_tax_codes(doc)
		except Exception as e:
			frappe.log_error(f"Erro ao resolver codigos AT por linha: {str(e)}")
			return

		missing, conflicting = [], []
		for item in doc.items:
			code = line_codes.get(item.name, "NOR")
			has_reason = bool(getattr(item, "at_exemption_reason", None))
			if code == "ISE" and not has_reason:
				missing.append(str(item.item_code or item.idx))
			elif code != "ISE" and has_reason:
				conflicting.append(str(item.item_code or item.idx))

		if missing:
			frappe.msgprint(
				_("Falta o motivo de isenção de IVA (linhas isentas a 0%): {0}").format(", ".join(missing)),
				indicator="orange", alert=True,
			)
		if conflicting:
			frappe.msgprint(
				_("Motivo de isenção preenchido em linha com IVA > 0%: {0}").format(", ".join(conflicting)),
				indicator="orange", alert=True,
			)

	def _validate_tax_exemption_hard(self, doc):
		"""
		Bloqueio rigido (frappe.throw) em before_submit - um documento
		fiscal submetido e imutavel e legalmente vinculativo, por isso
		aqui a falta de motivo de isencao bloqueia mesmo a submissao,
		ao contrario do aviso brando em validate.
		"""
		if doc.doctype not in ("Sales Invoice", "Delivery Note"):
			return
		if not getattr(doc, "items", None):
			return

		from portugal_compliance.utils.tax_breakdown import get_line_at_tax_codes
		line_codes = get_line_at_tax_codes(doc)

		for item in doc.items:
			code = line_codes.get(item.name, "NOR")
			has_reason = bool(getattr(item, "at_exemption_reason", None))
			if code == "ISE" and not has_reason:
				frappe.throw(
					_("Linha {0} ({1}): IVA isento (0%) exige motivo de isenção AT antes de submeter.")
					.format(item.idx, item.item_code)
				)
			if code != "ISE" and has_reason:
				frappe.throw(
					_("Linha {0} ({1}): motivo de isenção preenchido mas a taxa de IVA não é 0%.")
					.format(item.idx, item.item_code)
				)

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

			self._validate_tax_exemption_hard(doc)

			config = self.supported_doctypes[doc.doctype]

			if config.get("fiscal_document") and config.get("requires_atcud"):
				atcud_code = getattr(doc, 'atcud_code', None)
				if not atcud_code:
					frappe.throw(_("ATCUD é obrigatório para documentos fiscais portugueses"))

				# Bloquear submissao com codigo de validacao temporario
				# (gerado quando a serie ainda nao foi comunicada a AT -
				# ver _generate_enhanced_temporary_code). Um documento
				# submetido fica imutavel; deixar passar um ATCUD
				# fabricado significa que a unica forma de corrigir e
				# anular e reemitir, nunca corrigir. A validacao
				# anterior so verificava que o campo nao estava vazio,
				# nao que o codigo era real.
				validation_code = atcud_code.split('-')[0] if '-' in atcud_code else atcud_code
				if validation_code.startswith('TEMP'):
					frappe.throw(
						_(
							"Este documento tem um ATCUD temporário ({0}), gerado porque a série "
							"ainda não foi comunicada à AT. Comunique a série antes de submeter "
							"documentos fiscais - ver Portugal Series Configuration."
						).format(atcud_code)
					)

			if not self._is_portuguese_naming_series(getattr(doc, 'naming_series', '')):
				frappe.throw(_("Naming series portuguesa é obrigatória"))

		except Exception as e:
			frappe.log_error(f"Erro validação submissão: {str(e)}")
			raise

	# ========== HOOKS EM FALTA (referenciados em hooks.py, sem implementacao) ==========

	def generate_atcud_after_insert(self, doc, method=None):
		"""
		Hook de after_insert. Duas responsabilidades:

		1. Escrever o ATCUD Log estruturado (assinatura, QR, cadeia de
		   hash) que generate_atcud_before_save calculou mas nao pode
		   gravar ainda - o ATCUD Log tem uma Dynamic Link para este
		   documento, que so existe de facto na BD a partir daqui
		   (before_save corre antes do db_insert no ciclo de vida do
		   Frappe).
		2. Rede de seguranca: se por algum motivo o documento chegou
		   aqui sem atcud_code (ex: fluxo de bulk insert que saltou
		   before_save), gera agora.
		"""
		try:
			if not self._should_generate_atcud(doc) and not getattr(doc, 'atcud_code', None):
				return

			if getattr(doc, '_portugal_atcud_pending_log', None):
				from portugal_compliance.utils.atcud_generator import ATCUDGenerator
				ATCUDGenerator().persist_pending_atcud_log(doc)
				return

			if getattr(doc, 'atcud_code', None):
				return  # ja gerado e persistido, nada a fazer

			frappe.logger().warning(
				f"ATCUD nao encontrado apos insert para {doc.doctype} {doc.name} - "
				"a gerar agora como rede de seguranca"
			)
			from portugal_compliance.utils.atcud_generator import ATCUDGenerator
			generator = ATCUDGenerator()
			result = generator.generate_atcud_for_document(doc)
			if result.get("success"):
				doc.db_set('atcud_code', result["atcud_code"], update_modified=False)
				generator.persist_pending_atcud_log(doc)

		except Exception as e:
			frappe.log_error(f"Erro em generate_atcud_after_insert: {str(e)}")

	def validate_portugal_compliance_light(self, doc, method=None):
		"""
		Validacao ligeira para documentos pre-fiscais (Quotation, Sales
		Order, Purchase Order, Material Request) - estes documentos nao
		sao fiscais em Portugal e nao precisam de ATCUD, mas convem
		avisar cedo se a serie/empresa nao estiver bem configurada,
		antes de o utilizador chegar a fatura.
		"""
		try:
			if not self._is_portuguese_company(doc.company):
				return

			naming_series = getattr(doc, 'naming_series', None)
			if naming_series and not self._is_portuguese_naming_series(naming_series):
				frappe.msgprint(
					_("Esta série não segue o formato de série portuguesa recomendado."),
					indicator="orange",
					alert=True,
				)
		except Exception as e:
			frappe.log_error(f"Erro em validate_portugal_compliance_light: {str(e)}")

	def validate_customer_nif(self, doc, method=None):
		"""Valida o formato do NIF do cliente quando fornecido."""
		self._validate_party_nif(doc, "Customer")

	def validate_supplier_nif(self, doc, method=None):
		"""Valida o formato do NIF do fornecedor quando fornecido."""
		self._validate_party_nif(doc, "Supplier")

	def _validate_party_nif(self, doc, party_type):
		try:
			tax_id = getattr(doc, 'tax_id', None)
			if not tax_id:
				return

			from portugal_compliance.regional.portugal import validate_portuguese_nif_safe
			result = validate_portuguese_nif_safe(tax_id)
			if not result.get('valid'):
				frappe.msgprint(
					_("NIF de {0} pode estar inválido: {1}").format(party_type, result.get('message', '')),
					indicator="orange",
					alert=True,
				)
		except Exception as e:
			frappe.log_error(f"Erro ao validar NIF de {party_type}: {str(e)}")

	def validate_series_configuration(self, doc, method=None):
		"""
		Validacao de Portugal Series Configuration: prefixo obrigatorio
		e sem duplicar outra serie ativa da mesma empresa/tipo de
		documento/CODIGO (duas series ativas com o mesmo document_code
		confundem qual usar e arriscam ATCUDs inconsistentes).

		A restricao original comparava so empresa+document_type, o que
		impedia estruturalmente a existencia de series dedicadas de
		devolucao (NC para Sales Invoice, ver
		api.company_api.RETURN_DOCUMENT_SERIES) - FT e NC sao o MESMO
		document_type (Sales Invoice) mas tem de poder estar ambas
		ativas em simultaneo, distinguidas pelo document_code. A
		unicidade real que importa e (empresa, document_type,
		document_code) - nao document_type sozinho.
		"""
		try:
			if not getattr(doc, 'prefix', None):
				frappe.throw(_("Prefixo da série é obrigatório"))

			if getattr(doc, 'is_active', 0):
				duplicate = frappe.db.exists(
					"Portugal Series Configuration",
					{
						"company": doc.company,
						"document_type": doc.document_type,
						"document_code": getattr(doc, 'document_code', None),
						"is_active": 1,
						"name": ("!=", doc.name or ""),
					},
				)
				if duplicate:
					frappe.throw(
						_(
							"Já existe uma série ativa para {0} ({1}) na empresa {2} ({3}). "
							"Desative-a antes de ativar esta."
						).format(doc.document_type, getattr(doc, 'document_code', ''), doc.company, duplicate)
					)
		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro em validate_series_configuration: {str(e)}")

	def update_series_pattern(self, doc, method=None):
		"""
		Antes de gravar Portugal Series Configuration, atualiza os
		campos informativos de apresentacao (padrao de nomeacao e
		previsualizacao do ATCUD) a partir do prefixo atual.
		"""
		try:
			if getattr(doc, 'prefix', None):
				doc.naming_pattern = f"{doc.prefix}.####"
				preview_seq = int(doc.current_sequence or 1)
				preview_validation = doc.validation_code or "PENDENTE"
				# Largura da sequência de preview segue sempre o padrão real
				# de naming_pattern (nº de '#'), nunca um número fixo -
				# se o padrão de naming mudar, o preview acompanha sozinho.
				pad_width = doc.naming_pattern.count('#') or 4
				doc.sample_atcud = f"{preview_validation}-{preview_seq:0{pad_width}d}"
				doc.next_sequence_preview = preview_seq
		except Exception as e:
			frappe.log_error(f"Erro em update_series_pattern: {str(e)}")

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
		"""
		✅ OTIMIZADO: Auto-selecionar série comunicada

		Exclui series dedicadas a devolucoes (ver
		api.company_api.RETURN_DOCUMENT_SERIES, ex: NC para Sales
		Invoice) quando o documento NAO e uma devolucao - sem isto, com
		as series FT e NC ambas ativas/comunicadas para o mesmo
		document_type, este limit=1 sem ORDER BY podia devolver
		qualquer uma das duas e atribuir uma fatura normal a serie de
		Nota de Credito. reset_fiscal_fields_on_return_clone (hook
		before_insert) ja trata do caso inverso (devolucao -> serie
		NC), correndo antes desta funcao - para devolucoes,
		doc.naming_series ja vem preenchido e esta funcao nem chega a
		ser chamada.
		"""
		try:
			from portugal_compliance.api.company_api import RETURN_DOCUMENT_SERIES
			return_code = RETURN_DOCUMENT_SERIES.get(doc.doctype, {}).get("code")
			exclude_return_series = bool(return_code) and not getattr(doc, "is_return", 0)

			# Prioridade: Comunicada > Ativa
			for filters in [
				{"is_communicated": 1, "validation_code": ["!=", ""]},
				{"is_active": 1}
			]:
				filters.update({
					"document_type": doc.doctype,
					"company": doc.company
				})
				if exclude_return_series:
					filters["document_code"] = ["!=", return_code]

				series = frappe.get_all("Portugal Series Configuration",
										filters=filters,
										fields=["prefix"],
										order_by="creation asc",
										limit=1)

				if series:
					doc.naming_series = f"{series[0].prefix}.####"
					return

		except Exception as e:
			frappe.log_error(f"Erro em auto_select_communicated_series: {str(e)}")

	def _generate_atcud_with_real_validation_code(self, doc):
		"""
		✅ CORRIGIDO: Gerar ATCUD com código real da AT

		A sequência vem sempre de doc.name (número real e já atribuído
		do documento), nunca de um contador próprio como
		current_sequence+1 - manter um contador paralelo permite
		dessincronização entre o número do ATCUD e o número real do
		documento (mesmo bug já corrigido no caminho automático, ver
		ATCUDGenerator._get_next_sequence_thread_safe). A sequência
		também deixa de ser forçada a 8 dígitos - é a largura real do
		número do documento (ex: "0001"), tal como softwares
		certificados reais (Cegid Vendus, InvoiceXpress) fazem.
		"""
		try:
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"naming_series": doc.naming_series,
				"company": doc.company,
				"document_type": doc.doctype
			}, ["name", "validation_code", "current_sequence"], as_dict=True)

			if not series_config or not series_config.validation_code:
				return None

			seq_match = re.search(r'(\d+)$', doc.name or "")
			sequence_display = seq_match.group(1) if seq_match else "1"
			atcud_code = f"{series_config.validation_code}-{sequence_display}"

			# current_sequence mantido só como valor informativo para a UI
			# (ex: "próxima sequência prevista"), nunca lido de volta para
			# calcular um ATCUD.
			frappe.db.set_value("Portugal Series Configuration",
								series_config.name, "current_sequence", int(sequence_display) + 1)

			return atcud_code

		except Exception as e:
			frappe.log_error(f"Erro ao gerar ATCUD: {str(e)}")
			return None

	def _is_portuguese_naming_series(self, naming_series):
		"""✅ OTIMIZADO: Verificar se naming_series é portuguesa"""
		if not naming_series:
			return False
		pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}\.####$'
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


def reset_fiscal_fields_on_return_clone(doc, method=None):
	"""
	Hook before_insert. Quando um documento e criado como devolucao
	(is_return=1) atraves de make_return_doc, o ERPNext CLONA todos os
	campos do documento original para o rascunho - incluindo
	atcud_code, um campo real na Sales Invoice/Purchase Invoice/
	Delivery Note/Purchase Receipt/POS Invoice. Isso quebra a
	devolucao de duas formas: (1) _should_generate_atcud() ve o campo
	ja preenchido e nunca gera um codigo novo, (2)
	_validate_atcud_uniqueness_certified() rejeita a insercao porque
	esse ATCUD ja pertence ao documento original (ainda nao cancelado).
	A Nota de Credito/devolucao tem de ter o seu proprio ATCUD e a sua
	propria cadeia de assinatura RSA-SHA1, nunca herdar a do documento
	que estorna.

	So ha atcud_code para limpar aqui - a assinatura (hash, hash
	control, versao da chave) nunca fica guardada como campo nestes
	doctypes, so em ATCUD Log (decisao de arquitetura para evitar duas
	fontes de verdade); nao ha nada equivalente para limpar quanto a
	esse ponto.
	"""
	if getattr(doc, "is_return", 0) and doc.is_new():
		doc.atcud_code = None

		# Encaminhamento para a serie dedicada de devolucoes (NC), em
		# vez de continuar a consumir a serie normal (FT/naming_series
		# clonado do documento original) - exigido pela Ordem dos
		# Contabilistas, mesmo que a AT tecnicamente aceite series
		# partilhadas desde que a sequencia nao quebre. A serie tem de
		# ja estar aprovisionada E comunicada a AT antes disto (ver
		# api.company_api.ensure_return_series_for_company, chamada no
		# setup da empresa) - nunca criada/forcada aqui, isso emitiria
		# um documento numa serie ilegal (nao comunicada).
		from portugal_compliance.api.company_api import RETURN_DOCUMENT_SERIES
		if doc.doctype in RETURN_DOCUMENT_SERIES:
			return_code = RETURN_DOCUMENT_SERIES[doc.doctype]["code"]
			return_series = frappe.db.get_value(
				"Portugal Series Configuration",
				{
					"company": doc.company,
					"document_type": doc.doctype,
					"document_code": return_code,
					"is_active": 1,
				},
				"naming_series",
			)
			if not return_series:
				frappe.throw(_(
					"Não existe uma série de Nota de Crédito (NC) configurada para {0}. ""Contacte o administrador para aprovisionar e comunicar a série à AT antes de emitir devoluções (ver Portugal Series Configuration)."""
				).format(doc.company))
			doc.naming_series = return_series


def generate_atcud_before_save(doc, method=None):
	"""Hook global para geração de ATCUD"""
	return portugal_document_hooks.generate_atcud_before_save(doc, method)


def validate_portugal_compliance(doc, method=None):
	"""Hook para validate de documentos"""
	return portugal_document_hooks.validate_portugal_compliance(doc, method)


def before_submit_document(doc, method=None):
	"""Hook para before_submit de documentos"""
	return portugal_document_hooks.before_submit_document(doc, method)


def setup_company_portugal_compliance(doc, method=None):
	"""
	Hook global para on_update de Company. Faltava esta funcao (hooks.py
	referenciava-a mas so existia como metodo de classe, nunca acessivel
	via frappe.get_attr) - qualquer gravacao de qualquer empresa, PT ou
	nao, crashava com AttributeError assim que a app estava instalada.
	"""
	return portugal_document_hooks.setup_company_portugal_compliance(doc, method)


def generate_atcud_after_insert(doc, method=None):
	"""Hook para after_insert de documentos fiscais"""
	return portugal_document_hooks.generate_atcud_after_insert(doc, method)


def validate_portugal_compliance_light(doc, method=None):
	"""Hook para validate de documentos pre-fiscais (Quotation, Sales/Purchase Order, Material Request)"""
	return portugal_document_hooks.validate_portugal_compliance_light(doc, method)


def validate_customer_nif(doc, method=None):
	"""Hook para validate de Customer"""
	return portugal_document_hooks.validate_customer_nif(doc, method)


def validate_supplier_nif(doc, method=None):
	"""Hook para validate de Supplier"""
	return portugal_document_hooks.validate_supplier_nif(doc, method)


def validate_series_configuration(doc, method=None):
	"""Hook para validate de Portugal Series Configuration"""
	return portugal_document_hooks.validate_series_configuration(doc, method)


def update_series_pattern(doc, method=None):
	"""Hook para before_save de Portugal Series Configuration"""
	return portugal_document_hooks.update_series_pattern(doc, method)


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def generate_manual_atcud_certified(doctype, docname):
	"""
	API para gerar ATCUD manualmente. Ponto de escrita partilhado por
	varios endpoints (generate_atcud_for_document, regenerate_atcud,
	bulk_generate_atcud) e tambem diretamente alcancavel - por isso o
	controlo de permissao tem de estar aqui, nao so nos chamadores.
	"""
	try:
		if not frappe.has_permission(doctype, "write", docname):
			return {"success": False, "error": "Sem permissão para gerar ATCUD neste documento"}

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


def sync_communication_settings(doc, method=None):
	"""
	Hook de validate da Company. Portugal Auth Settings e um Single (uma
	so configuracao no site) - e a fonte real que o codigo dos
	webservices le (at_invoice_webservice.py, at_transport_webservice.py),
	mas ate agora so era visivel/editavel no proprio formulario de
	Portugal Auth Settings, nao no ecra da Company onde o resto das
	credenciais AT esta. Este hook faz de ponte nos dois sentidos:

	  - Se o utilizador mudou invoice_communication_method/
	    transport_communication_method na Company, escreve o novo valor
	    em Portugal Auth Settings (fonte real usada pelo codigo).
	  - Se o campo na Company ainda esta vazio (primeira vez que este
	    campo aparece num registo ja existente, ou uma segunda empresa
	    que nunca tocou nisto), mostra o valor atualmente configurado em
	    vez de aparecer em branco.

	Nota: por Portugal Auth Settings ser Single, o metodo de comunicacao
	e partilhado por todas as empresas do site - se houver mais do que
	uma empresa portuguesa ativa neste site, a ultima a gravar este
	campo e que prevalece. Nao e um problema para o site atual (uma so
	empresa, novadx), mas fica registado aqui para nao ser esquecido se
	um dia houver multi-empresa real.
	"""
	if not cint(getattr(doc, "portugal_compliance_enabled", 0)):
		return

	try:
		current_invoice = frappe.db.get_single_value("Portugal Auth Settings", "invoice_communication_method")
		current_transport = frappe.db.get_single_value("Portugal Auth Settings", "transport_communication_method")

		new_invoice = getattr(doc, "invoice_communication_method", None)
		if new_invoice and new_invoice != current_invoice:
			frappe.db.set_single_value("Portugal Auth Settings", "invoice_communication_method", new_invoice)
		elif not new_invoice:
			doc.invoice_communication_method = current_invoice or "Offline (SAF-T Mensal)"

		new_transport = getattr(doc, "transport_communication_method", None)
		if new_transport and new_transport != current_transport:
			frappe.db.set_single_value("Portugal Auth Settings", "transport_communication_method", new_transport)
		elif not new_transport:
			doc.transport_communication_method = current_transport or "Tempo Real (Webservice)"
	except Exception as e:
		frappe.log_error(f"Erro em sync_communication_settings: {str(e)}")


def sync_at_credentials(doc, method=None):
	"""
	Hook de validate da Company (junto de sync_communication_settings).

	Consolida a duplicacao de credenciais AT identificada na auditoria:
	Company.at_username/at_password/at_environment (usado pelo caminho
	mais antigo de company_api.py - botoes "Configurar Credenciais AT"/
	"Comunicar Series" no ecra da Company) e Portugal Auth Settings.
	at_username/at_password/sandbox_mode (fonte real lida por TODOS os
	webservices atuais: at_webservice.py, at_invoice_webservice.py,
	at_transport_webservice.py) sao dois locais distintos para a mesma
	informacao, sem garantia de estarem sincronizados.

	Em vez de eliminar um dos dois (quebraria o botao "Comunicar
	Series" ja em uso), este hook mantem-nos sincronizados nos dois
	sentidos - a Company continua a ser onde o utilizador mexe, mas o
	valor propaga sempre para Portugal Auth Settings, e vice-versa
	quando o campo na Company ainda esta vazio.

	Nota sobre o ambiente: Company usa at_environment (Select
	test/production), Portugal Auth Settings usa sandbox_mode (Check) -
	mapeados um para o outro (test <-> 1, production <-> 0).
	"""
	if not cint(getattr(doc, "portugal_compliance_enabled", 0)):
		return

	try:
		settings = frappe.get_single("Portugal Auth Settings")
		settings_dirty = False

		new_username = getattr(doc, "at_username", None)
		if new_username and new_username != settings.at_username:
			settings.at_username = new_username
			settings_dirty = True
		elif not new_username and settings.at_username:
			doc.at_username = settings.at_username

		new_password = doc.get_password("at_password", raise_exception=False)
		current_password = settings.get_password("at_password", raise_exception=False)
		if new_password and new_password != current_password:
			settings.at_password = new_password
			settings_dirty = True
		elif not new_password and current_password:
			doc.at_password = current_password

		new_environment = getattr(doc, "at_environment", None)
		if new_environment:
			new_sandbox = 1 if new_environment == "test" else 0
			if cint(settings.sandbox_mode) != new_sandbox:
				settings.sandbox_mode = new_sandbox
				settings_dirty = True
		else:
			doc.at_environment = "test" if cint(settings.sandbox_mode) else "production"

		if settings_dirty:
			settings.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Erro em sync_at_credentials: {str(e)}")


def generate_and_attach_qr_code(doc, method=None):
	"""
	Hook de after_insert (corre a seguir a generate_atcud_after_insert,
	depois do ATCUD Log real estar persistido). Gera o QR Code (string
	no formato AT + imagem PNG) e grava-o no proprio documento -
	qr_code (novo) e qr_code_image existiam como campos ha muito, mas
	nenhum codigo os preenchia de facto: o QR so era calculado em
	memoria no momento da impressao, direto no template
	(get_qr_code_data/generate_qr_code_image chamados inline). Isto
	tornava invisivel para qualquer widget de estado que o documento
	esta de facto conforme - o painel de compliance da POS Invoice
	(public/js/pos_invoice.js) verifica frm.doc.qr_code, e mostrava
	sempre "QR Code Pendente" mesmo num documento já assinado e com
	ATCUD real, porque esse campo nunca existia.

	Nao altera os print formats existentes (continuam a calcular o QR
	fresco no momento da impressao, ja testado) - isto e apenas um
	registo persistido, para o painel de estado e para qualquer
	inspecao/auditoria futura ao documento.
	"""
	if doc.doctype not in FISCAL_IMMUTABLE_DOCTYPES:
		return
	if not getattr(doc, "atcud_code", None):
		return
	try:
		from portugal_compliance.utils.jinja_methods import get_qr_code_data, generate_qr_code_image

		qr_string = get_qr_code_data(doc=doc)
		if not qr_string:
			return
		doc.db_set("qr_code", qr_string, update_modified=False)

		qr_image = generate_qr_code_image(qr_string, 280)
		if qr_image:
			doc.db_set("qr_code_image", qr_image, update_modified=False)
	except Exception as e:
		frappe.log_error(f"Erro ao gerar QR Code para {doc.doctype} {doc.name}: {str(e)}")


# ========== INVIOLABILIDADE (Portaria n.º 363/2010) ==========
#
# Um documento fiscal certificado nunca pode ser apagado da base de
# dados nem ter os seus campos fiscais alterados depois de assinado -
# a unica forma legal de o desfazer e a anulacao documentada
# (Cancelar) ou a emissao de um documento de estorno (ex: Nota de
# Credito). O Frappe ja bloqueia nativamente apagar um documento
# SUBMETIDO (docstatus=1), mas permite livremente apagar rascunhos e
# documentos ja ANULADOS (docstatus=2) - e exatamente aqui que um
# documento com ATCUD/assinatura real podia desaparecer sem deixar
# rasto. Delivery Note nao entra nesta lista porque a comunicacao a AT
# ja a torna auditavel do lado deles (ATDocCodeID), mas o pedido do
# utilizador foi explicito nestes 4 doctypes - mantido tal como pedido.

FISCAL_IMMUTABLE_DOCTYPES = ["Sales Invoice", "Delivery Note", "Payment Entry", "POS Invoice"]

# Campos cuja alteracao depois de assinado invalidaria a assinatura
# RSA-SHA1 ja calculada (generate_atcud_before_save so gera o ATCUD
# uma vez, nunca regenera - sem este bloqueio seria possivel editar o
# total/cliente/data de um rascunho DEPOIS de assinado e a assinatura
# ficava a corresponder a dados que ja nao existem).
FISCAL_LOCK_FIELDS = {
	"Sales Invoice": ["customer", "posting_date", "grand_total", "net_total", "is_return", "naming_series", "atcud_code"],
	"POS Invoice": ["customer", "posting_date", "grand_total", "net_total", "naming_series", "atcud_code"],
	"Delivery Note": ["customer", "posting_date", "naming_series", "is_return", "atcud_code"],
	"Payment Entry": ["party", "posting_date", "paid_amount", "received_amount", "naming_series", "atcud_code"],
}


def block_fiscal_document_deletion(doc, method=None):
	"""
	Hook de on_trash. Bloqueia eliminacao de qualquer documento fiscal
	que ja tenha ATCUD/assinatura gerados, ou que esteja anulado
	(docstatus=2) mesmo sem ATCUD - o registo tem de permanecer.
	"""
	if doc.doctype not in FISCAL_IMMUTABLE_DOCTYPES:
		return

	if getattr(doc, "atcud_code", None):
		frappe.throw(
			_(
				"{0} {1} não pode ser eliminado: já tem ATCUD/assinatura fiscal gerados ({2}). "
				"Documentos assinados são invioláveis (Portaria n.º 363/2010) - anule o documento "
				"(Cancelar) ou emita um documento de estorno (ex: Nota de Crédito) em vez de o apagar."
			).format(_(doc.doctype), doc.name, doc.atcud_code),
			title=_("Eliminação Bloqueada"),
		)

	if doc.docstatus == 2:
		frappe.throw(
			_(
				"{0} {1} está anulado e não pode ser eliminado - o registo tem de permanecer na "
				"base de dados para efeitos de auditoria, mesmo sem ATCUD."
			).format(_(doc.doctype), doc.name),
			title=_("Eliminação Bloqueada"),
		)


def enforce_fiscal_field_lock(doc, method=None):
	"""
	Hook de before_save - tem de correr ANTES de
	generate_atcud_before_save no mesmo evento (ver ordem em hooks.py).
	Compara com get_doc_before_save() (estado na BD antes desta
	gravacao); se o documento ja tinha ATCUD antes desta gravacao,
	nenhum dos campos fiscais pode ter mudado.
	"""
	if doc.doctype not in FISCAL_LOCK_FIELDS or doc.is_new():
		return

	before = doc.get_doc_before_save()
	if not before or not getattr(before, "atcud_code", None):
		return

	changed = [f for f in FISCAL_LOCK_FIELDS[doc.doctype] if doc.get(f) != before.get(f)]
	if changed:
		frappe.throw(
			_(
				"{0} {1} já tem ATCUD/assinatura gerados ({2}) - os campos fiscais {3} não podem "
				"ser alterados (Portaria 195/2020). Anule o documento e emita um novo em vez de "
				"corrigir os valores diretamente."
			).format(_(doc.doctype), doc.name, before.atcud_code, ", ".join(changed)),
			title=_("Alteração Bloqueada"),
		)


def log_document_cancellation(doc, method=None):
	"""
	Hook de on_cancel. Nao bloqueia - anular e a via legal para desfazer
	um documento fiscal em Portugal. So deixa um registo explicito e
	visivel na timeline do documento com o ATCUD anulado, mais facil de
	encontrar numa auditoria do que vasculhar o historico de versoes do
	Track Changes.
	"""
	if doc.doctype not in FISCAL_IMMUTABLE_DOCTYPES:
		return
	if not getattr(doc, "atcud_code", None):
		return
	try:
		doc.add_comment(
			"Info",
			_(
				"Documento anulado por {0}. O ATCUD {1} mantém-se registado para efeitos de "
				"auditoria - o registo original não foi nem pode ser eliminado."
			).format(frappe.session.user, doc.atcud_code),
		)
	except Exception as e:
		frappe.log_error(f"Erro ao registar anulação de {doc.doctype} {doc.name}: {str(e)}")


def force_track_changes_property_setters():
	"""
	Chamada em after_migrate (ver hooks.py). Garante via Property Setter
	que track_changes esta sempre ativo nos doctypes fiscais, mesmo que
	alguem o desligue manualmente no Customize Form - pista de auditoria
	(quem alterou o que e quando) e um requisito de certificacao
	(Portaria 363/2010), nao uma preferencia de UI.
	"""
	for doctype in FISCAL_IMMUTABLE_DOCTYPES:
		try:
			existing = frappe.db.get_value(
				"Property Setter", {"doc_type": doctype, "property": "track_changes"}, "name"
			)
			if existing:
				frappe.db.set_value("Property Setter", existing, "value", "1")
			else:
				frappe.get_doc({
					"doctype": "Property Setter",
					"doctype_or_field": "DocType",
					"doc_type": doctype,
					"property": "track_changes",
					"property_type": "Check",
					"value": "1",
				}).insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Erro ao forçar track_changes em {doctype}: {str(e)}")
	frappe.clear_cache()


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Document Hooks OTIMIZADO loaded - Version 2.1.0 - Clean & Efficient")
