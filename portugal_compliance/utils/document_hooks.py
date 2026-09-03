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
from frappe.utils import getdate, now, now_datetime, get_datetime, today, cint, flt
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
				"code": "RG"
			},
			"Delivery Note": {
				"prefixes": ["GT", "GR"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": True,
				"code": "GR"
			},
			# Quotation e Sales Order acrescentados (2026-09-03, correcao
			# de auditoria): removidos do motor em 700e2d6 (2026-08-30)
			# com o entendimento de que nao eram "documentos emitidos a
			# terceiros" ao abrigo da Portaria 195/2020 - interpretacao
			# incompleta, confirmada por fonte oficial da AT (FAQ
			# "Ambito de Aplicacao" de Series/ATCUD, que cita o Decreto-
			# Lei 28/2019: sao "documentos fiscalmente relevantes...
			# quaisquer outros documentos emitidos... suscetiveis de
			# apresentacao ao cliente que possibilitem a conferencia de
			# mercadorias ou de prestacao de servicos, nos quais se
			# incluem as notas de encomenda"). Orcamento tratado da
			# mesma forma pelo mesmo criterio aberto ("nao esta excluido
			# nenhum tipo de documento"), sem fonte oficial que o nomeie
			# à parte mas coberto pelo mesmo principio - e o documento
			# do ponto 5.12 do oficio de certificacao da AT ("orcamento
			# ou fatura pro-forma"). fiscal_document=False (nao geram
			# obrigacao de IVA, tal como a Guia de Transporte acima) mas
			# requires_atcud=True. Codigos OR/NE confirmados no proprio
			# XSD oficial (elemento WorkType, anotacao: "NE para nota de
			# encomenda... OR para orcamento").
			"Quotation": {
				"prefixes": ["OR"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": True,
				"code": "OR"
			},
			"Sales Order": {
				"prefixes": ["NE"],
				"requires_atcud": True,
				"fiscal_document": False,
				"critical": True,
				"code": "NE"
			},
			# Stock Entry e Journal Entry removidos (2026-08-22), mesmo
			# motivo legal da remocao da Purchase Invoice acima: ATCUD e
			# assinatura RSA aplicam-se por lei a documentos EMITIDOS a
			# terceiros (Portaria 195/2020), nunca a movimentos internos de
			# stock ou lancamentos contabilisticos - nenhum dos dois e
			# comunicado a AT nem tem serie comunicavel (nunca teve). Os
			# registos ja existentes em ATCUD Log destes doctypes (gerados
			# antes desta correcao) mantem-se intactos para efeitos de
			# auditoria - so a geracao futura para. Ver hooks.py:
			# doc_events["Stock Entry"] e doc_events["Journal Entry"]
			# removidos no mesmo commit (Purchase Receipt tambem, apesar de
			# nunca ter estado nesta lista - o bloco em hooks.py era
			# codigo morto).
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

			if created_count > 0:
				# ✅ VERIFICAR SE HÁ CREDENCIAIS AT CONFIGURADAS (2026-08-23:
				# passou a ler Portugal Auth Settings - Company deixou de
				# ter campos de credenciais AT proprios)
				auth_settings = frappe.get_single("Portugal Auth Settings")
				has_at_credentials = bool(
					auth_settings.get("at_username")
					and auth_settings.get_password("at_password", raise_exception=False)
				)

				if has_at_credentials:
					# ✅ COM CREDENCIAIS: Oferecer comunicação automática
					frappe.msgprint(
						f"""
						<div style="text-align: center;">
							<h4>🇵🇹 Portugal Compliance Ativado!</h4>
							<div style="margin: 15px 0;">
								✅ {created_count} séries criadas<br>
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
									company: company
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
								✅ Custom fields criados<br>
								✅ Compliance ativo
							</div>
							<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
								<strong>📋 Próximos Passos:</strong><br>
								1. Configure as credenciais AT em Portugal Auth Settings<br>
								2. Use o botão "Comunicar Séries" para comunicar à AT<br>
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

	def validate_company_fiscal_lock(self, doc, method=None):
		"""
		Hook validate de Company (2026-09-01) - "Ponto de Não-Retorno" fiscal
		exigido pela Portaria 363/2010, que proíbe a manipulação ou
		ocultação das regras de faturação.

		Duas responsabilidades distintas, deliberadamente na mesma função
		por serem faces da mesma garantia ("uma empresa portuguesa nunca
		opera fora do motor de compliance"):

		1. Ativação automática: se País = Portugal e o compliance ainda
		   não estava ativo, ativa-o aqui - cobre tanto uma Company nova
		   como uma já existente que muda de País para Portugal. Não
		   duplica o bloqueio já existente para a direção inversa (impedir
		   desativar depois de já ter estado ativo) - esse já existe,
		   incondicional (nem depende de haver documentos fiscais
		   emitidos), em
		   regional/portugal.py::validate_portugal_company_settings_safe.
		   As duas funções juntas fecham o ciclo completo: nunca fica
		   inativo enquanto o País for Portugal, seja qual for o caminho
		   usado para lá chegar.

		2. Bloqueio de País/NIF: uma vez que a empresa já tem pelo menos
		   um documento fiscal submetido (ver has_existing_fiscal_records),
		   alterar o País ou o NIF base corromperia a coerência entre os
		   documentos já assinados/comunicados à AT e a identidade fiscal
		   de quem os emitiu - o ficheiro SAF-T e o próprio ATCUD
		   assumem que esses dois campos nunca mudam depois de um
		   documento existir. Ao contrário do bloqueio de campos fiscais
		   em `enforce_fiscal_field_lock` (por documento, ativa a partir
		   do primeiro documento SUBMETIDO desse documento em concreto),
		   este é ao nível da Company inteira - qualquer documento fiscal
		   já submetido, de qualquer um dos 4 doctypes, bloqueia a
		   alteração destes 2 campos para sempre.
		"""
		if doc.country == "Portugal" and not cint(doc.get("portugal_compliance_enabled")):
			doc.portugal_compliance_enabled = 1
			frappe.msgprint(
				_(
					"Portugal Compliance foi ativado automaticamente por esta empresa "
					"ter o País definido como Portugal - não é permitido operar uma "
					"empresa portuguesa neste sistema sem o motor de compliance fiscal "
					"ativo (Portaria n.º 363/2010)."
				),
				title=_("Compliance Ativado Automaticamente"),
				indicator="blue",
			)

		before = doc.get_doc_before_save()
		if not before:
			return

		if not has_existing_fiscal_records(doc.name):
			return

		if doc.country != before.country or doc.tax_id != before.tax_id:
			frappe.throw(
				_(
					"Ação bloqueada: Já existem documentos fiscais emitidos para esta "
					"Empresa. Para garantir a integridade do ficheiro SAF-T, não é "
					"permitido desativar as regras de compliance, nem alterar o País ou "
					"NIF base."
				),
				title=_("Alteração Bloqueada — Documentos Fiscais Existentes"),
			)

	def _should_activate_compliance(self, doc):
		"""Verificar se deve ativar compliance.

		Auditoria 2026-09-04 (paridade Quotation/Sales Order): esta
		verificacao nunca disparava para uma empresa REALMENTE nova -
		doc._doc_before_save, quando existe durante on_update, reflete
		o estado JA GRAVADO na BD (Document.load_doc_before_save() faz
		um frappe.get_doc fresco), nao o estado antes do insert. E como
		validate_company_fiscal_lock (abaixo) forca
		portugal_compliance_enabled=1 durante validate() - que corre
		antes de on_update, no mesmo ciclo de save() - o valor "antes"
		e o "depois" eram sempre iguais (1 e 1) numa empresa nova com
		Pais=Portugal, mesmo sem o utilizador tocar na checkbox. Nunca
		havia uma transicao 0->1 para detetar, logo as series nunca
		eram criadas automaticamente para NENHUM doctype numa empresa
		portuguesa genuinamente nova - confirmado ao vivo (as series da
		NovaDX vieram do patch historico setup_portugal_series.py, nao
		deste caminho). Corrigido para tambem ativar durante o proprio
		insert() - nao com doc.is_new() (confirmado ao vivo que ja
		devolve False neste ponto: Document.insert() so chama
		run_post_save_methods, que despoleta on_update, DEPOIS de
		limpar "__islocal"/is_new()), mas com doc.flags.in_insert, que
		o proprio Document.insert() mantem True precisamente durante
		essa janela (ver frappe/model/document.py::insert()). Seguro
		porque toda a configuracao em _execute_compliance_setup ja e
		idempotente (verifica existencia antes de criar), pelo que nao
		ha risco de duplicar nada mesmo que esta verificacao dispare
		mais vezes do que estritamente necessario.
		"""
		if not (doc.country == "Portugal" and cint(getattr(doc, 'portugal_compliance_enabled', 0))):
			return False

		if doc.flags.in_insert:
			return True

		before = getattr(doc, '_doc_before_save', None) if hasattr(doc, '_doc_before_save') else None
		return not cint(getattr(before, "portugal_compliance_enabled", 0))

	def _execute_compliance_setup(self, doc):
		"""Executar todas as configurações de compliance"""
		results = {}

		# 1. Criar séries (Portugal Auth Settings > "Criar séries
		# automaticamente", default ativo - mantém o comportamento
		# histórico incondicional; só passa a poder ser desligado pelo
		# administrador, para pré-configurar o ambiente antes de criar
		# séries manualmente via "Configurar Séries").
		auth_settings = frappe.get_single("Portugal Auth Settings")
		if cint(auth_settings.get("auto_create_series", 1)):
			results['series'] = self._create_dynamic_portugal_series_certified(doc)
		else:
			results['series'] = {"success": True, "created": 0, "skipped": True}

		# A restrição das opções de naming_series por empresa deixou de
		# usar Property Setter (Auditoria Fase 0, 2026-08-26):
		# doctype_or_field="DocField"/options não tem dimensão de
		# empresa no Frappe - com mais do que uma empresa portuguesa no
		# mesmo site, a segunda a gravar substituía inteiramente a
		# lista de séries da primeira (nenhuma das duas conseguia usar
		# as suas próprias séries de forma fiável). Substituído por
		# filtragem client-side (ver public/js/portugal_compliance.js::
		# applyNamingSeriesFilter, ligado em company/refresh nos 4
		# ficheiros JS dos doctypes fiscais), que consulta sempre a
		# empresa atualmente selecionada no formulário via
		# queries.series_queries.get_naming_series_options.

		# 2. Custom fields
		self._ensure_custom_fields_exist()

		# 3. Templates de impostos + contas SNC 2433x/2434x/2435x por
		# região+taxa (Fase 7: taxonomia AT completa, substitui a conta
		# generica "Duties and Taxes" pela conta real do Plano de Contas
		# SNC português; até aqui só "Continente" era criado - Madeira/
		# Açores ficavam apenas documentados mas nunca gerados, ver
		# create_regional_tax_setup_for_company)
		from portugal_compliance.setup.tax_setup import create_regional_tax_setup_for_company
		try:
			results['tax_templates'] = create_regional_tax_setup_for_company(doc.name)
		except Exception as e:
			frappe.log_error(f"Erro ao configurar taxonomia AT de IVA para {doc.name}: {str(e)}")

		# 4. Tax Category (2026-08-30, onboarding "Zero Touch"): registos
		# globais (sem campo company) usados pela sugestao automatica de
		# categoria fiscal em Customer/Supplier - ver
		# setup_default_tax_categories() para a auditoria completa de
		# porque so estes 4 nomes (nao os que pareciam "obvios").
		from portugal_compliance.setup.tax_setup import setup_default_tax_categories
		try:
			results['tax_categories'] = setup_default_tax_categories()
		except Exception as e:
			frappe.log_error(f"Erro ao configurar Tax Category para {doc.name}: {str(e)}")

		# 5. POS Settings.invoice_type -> "POS Invoice" (2026-09-03,
		# pedido explicito do utilizador). Todo o motor de compliance
		# desta app (ATCUD/serie FS/Fatura Simplificada/exemption legend/
		# etc.) foi construido e testado a volta do doctype POS Invoice,
		# nao Sales Invoice emitida a partir do ecra do POS - deixar o
		# default de fabrica do ERPNext ("Sales Invoice") faria uma
		# empresa portuguesa nova emitir do POS para uma serie/doctype
		# que este modulo trata como back-office, nao retalho. Ver
		# ensure_pos_invoice_as_default() (guarda de seguranca contra
		# regressao multi-empresa) mais abaixo.
		try:
			results['pos_invoice_type'] = ensure_pos_invoice_as_default()
		except Exception as e:
			frappe.log_error(f"Erro ao configurar Invoice Type do POS para {doc.name}: {str(e)}")

		return results

	def _show_setup_results(self, doc, results):
		"""Mostrar resultados da configuração"""
		created_count = results.get('series', {}).get('created', 0)

		if created_count > 0:
			frappe.msgprint(
				f"🇵🇹 Portugal Compliance ativado!<br>"
				f"✅ {created_count} séries criadas<br>"
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

	# ========== HOOKS DE DOCUMENTOS ==========

	# _setup_automatic_property_setters / _create_or_update_property_setter
	# removidas (Auditoria Fase 0, 2026-08-26) - mesma razão da nota
	# acima: um Property Setter de options em naming_series é global ao
	# DocType, sem dimensão de empresa, e quebra com mais de uma
	# empresa portuguesa ativa no site. A rede de segurança real contra
	# emitir numa série inativa continua intacta e nunca dependeu deste
	# mecanismo - ver _validate_series_not_inactive, que corre sempre
	# em validate() do lado do servidor, independentemente do que a UI
	# mostra no dropdown.

	def generate_atcud_on_submit(self, doc, method=None):
		"""
		Hook de on_submit. Substitui a antiga combinação before_save +
		after_insert (generate_atcud_before_save / generate_atcud_after_insert /
		generate_and_attach_qr_code, removidas - ver hooks.py e a nota no
		fundo deste ficheiro). O ATCUD, a assinatura RSA-SHA1 e o QR Code
		só são gerados agora, no momento em que o documento se torna
		definitivamente imutável (docstatus 0 -> 1) - nunca antes.

		Corre por último na cadeia de on_submit deste doctype (listada
		depois de qualquer outro hook nosso em hooks.py) e sempre depois
		de: (1) qualquer lógica nativa do ERPNext para este evento - o
		Frappe chama sempre o método da própria classe do documento antes
		de disparar os doc_events de apps -, e (2) de before_submit_document
		(validate_portugal_compliance / _validate_tax_exemption_hard, a
		verificação de série comunicada e o formato da naming series), que
		corre sempre antes de on_submit no ciclo de vida do Frappe. Se
		qualquer uma destas validações anteriores rejeitar a submissão,
		esta função nunca chega a correr e a transação inteira (incluindo
		a própria mudança de docstatus) sofre rollback - nenhum ATCUD
		chega a ser queimado.

		Bug corrigido (2026-08-24, "rascunho zombie"): antes desta
		correção, a assinatura corria em before_save/after_insert - ou
		seja, em qualquer gravação de rascunho, muito antes de a
		submissão poder ainda falhar por uma validação de negócio (ex:
		falta do motivo de isenção de IVA, só verificada de forma rígida
		em before_submit). Um rascunho que falhasse essa validação ficava
		com um ATCUD/assinatura reais já gravados, e enforce_fiscal_field_lock
		bloqueava depois qualquer tentativa de corrigir o campo em falta
		("já tem ATCUD... campos fiscais não podem ser alterados") - um
		rascunho preso, não editável nem submetível.
		"""
		try:
			if not self._should_generate_atcud(doc):
				return

			if not getattr(doc, 'naming_series', None):
				self._auto_select_communicated_series(doc)
				if getattr(doc, 'naming_series', None):
					doc.db_set('naming_series', doc.naming_series, update_modified=False)

			if not getattr(doc, 'naming_series', None):
				frappe.throw(_("Série portuguesa é obrigatória para {0}").format(_(doc.doctype)))

			from portugal_compliance.utils.atcud_generator import ATCUDGenerator
			generator = ATCUDGenerator()
			result = generator.generate_atcud_for_document(doc)

			if not result.get("success"):
				frappe.throw(
					_("Não foi possível gerar o ATCUD/assinatura fiscal: {0}").format(result.get("error")),
					title=_("Falha na Assinatura Fiscal"),
				)

			doc.db_set('atcud_code', result["atcud_code"], update_modified=False)

			# QR Code: gerado aqui, uma unica vez, com get_qr_code_data() -
			# a MESMA funcao usada pelos Print Formats reais e pelo
			# registo a AT. So agora e possivel, porque doc.atcud_code so
			# passou a existir no db_set() acima. O valor e injetado em
			# doc._portugal_atcud_pending_log ANTES de
			# persist_pending_atcud_log(), para que ATCUD Log.
			# qr_code_string grave exatamente a mesma string - single
			# source of truth entre o que fica na trilha de auditoria e o
			# que e comunicado/impresso (antes desta correcao,
			# atcud_generator.py::_build_qr_data_optimized() construia um
			# segundo QR, com o mesmo defeito de mapeamento de campos ja
			# corrigido aqui, so para a trilha de auditoria - removida).
			if doc.doctype in FISCAL_IMMUTABLE_DOCTYPES:
				try:
					from portugal_compliance.utils.jinja_methods import get_qr_code_data, generate_qr_code_image
					qr_string = get_qr_code_data(doc=doc)
					if qr_string:
						doc.db_set("qr_code", qr_string, update_modified=False)
						if hasattr(doc, "_portugal_atcud_pending_log"):
							doc._portugal_atcud_pending_log["qr_code_data"] = qr_string
						qr_image = generate_qr_code_image(qr_string, 280)
						if qr_image:
							doc.db_set("qr_code_image", qr_image, update_modified=False)
				except Exception as e:
					frappe.log_error(f"Erro ao gerar QR Code para {doc.doctype} {doc.name}: {str(e)}")

			generator.persist_pending_atcud_log(doc)
			frappe.logger().info(f"✅ ATCUD gerado no submit: {result['atcud_code']}")

			# Nao gravar portugal_compliance_status aqui: nunca existiu
			# como coluna real em nenhum destes doctypes (confirmado
			# contra fixtures/custom_field.json) - so era atribuido em
			# memoria (doc.portugal_compliance_status = ...), nunca
			# persistido. hasattr(doc, campo) e sempre True num Document
			# do Frappe (__getattr__ nunca levanta AttributeError), por
			# isso um db_set aqui rebentava sempre com "Unknown column"
			# assim que se tentou persistir a serio (bug apanhado no
			# teste ao vivo desta correcao, nunca chegou a produção).

		except Exception:
			# Ao contrario da antiga generate_atcud_before_save (que so
			# registava o erro e deixava o rascunho seguir sem ATCUD), uma
			# falha aqui tem de abortar a submissao: e o ultimo ponto onde
			# um documento fiscal pode ainda ser rejeitado antes de ficar
			# imutavel. Relancar garante rollback da transacao completa.
			raise

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
				self._validate_series_not_inactive(doc)
				self._validate_series_registered_in_compliance(doc)
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

		POS Invoice adicionado 2026-08-30 (estava em falta aqui, apesar
		de "POS Invoice Item" ja ter o campo at_exemption_reason desde
		sempre - fixtures/custom_field.json - e de comunicar a AT/entrar
		no SAF-T exatamente como uma Sales Invoice).
		"""
		if doc.doctype not in ("Sales Invoice", "POS Invoice", "Delivery Note", "Quotation", "Sales Order"):
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

		POS Invoice adicionado 2026-08-30: before_submit_document (que
		chama esta funcao) ja corria para POS Invoice - hooks.py tem
		"before_submit" ligado a antes de "on_submit" para este doctype,
		exatamente como Sales Invoice - mas esta funcao devolvia sem
		validar nada por POS Invoice nao estar nesta tupla. Confirmado
		que "POS Invoice Item" ja tem o campo at_exemption_reason
		(fixtures/custom_field.json), por isso a UI ja deixava preencher
		o motivo - so a validacao em si nao estava a exigi-lo.
		"""
		if doc.doctype not in ("Sales Invoice", "POS Invoice", "Delivery Note", "Quotation", "Sales Order"):
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

	# Campo de valor a comparar com o limiar de 1000€, por doctype -
	# Sales Invoice/POS Invoice usam o total da fatura, Payment Entry o
	# valor efetivamente pago (nao tem grand_total).
	_NIF_THRESHOLD_AMOUNT_FIELD = {
		"Sales Invoice": "grand_total",
		"POS Invoice": "grand_total",
		"Payment Entry": "paid_amount",
	}

	def _validate_nif_threshold(self, doc):
		"""
		Bloqueio rigido (frappe.throw) em before_submit - documentos
		acima de 1000€ exigem NIF do cliente/parceiro (regra fiscal
		portuguesa para faturas/recibos nesse escalao).

		Pedido do utilizador (2026-08-30) apos reparar numa
		inconsistencia: o Payment Entry ja bloqueava corretamente
		faturas de Recibo acima de 1000€ sem NIF - mas so no cliente
		(payment_entry.js::validate_before_submit_portuguese, um
		before_submit em JS, contornavel por qualquer chamada direta a
		API que nao passe pelo formulario). A Sales Invoice de origem
		desse Recibo passou incolume pela mesma regra porque nunca a
		teve implementada em lado nenhum - nem cliente, nem servidor
		(confirmado por grep: zero ocorrencias de "1000" em
		sales_invoice.js ou em document_hooks.py antes desta correcao).
		overrides/sales_invoice.py e overrides/payment_entry.py tambem
		nao contam - confirmado em hooks.py que override_doctype_class
		esta vazio ({}) desde a Auditoria Fase 0 (2026-08-26): essas
		classes nunca sao instanciadas, codigo morto.

		Esta e a primeira vez que esta regra existe do lado do
		servidor, para os 3 doctypes onde faz sentido (nao Delivery
		Note - documento de transporte, sem valor monetario/NIF na
		mesma logica de fatura).
		"""
		amount_field = self._NIF_THRESHOLD_AMOUNT_FIELD.get(doc.doctype)
		if not amount_field:
			return

		if flt(getattr(doc, amount_field, 0)) <= 1000:
			return

		if doc.doctype == "Payment Entry":
			party_type = getattr(doc, "party_type", None)
			party = getattr(doc, "party", None)
			if not party_type or not party:
				return
			nif = frappe.db.get_value(party_type, party, "tax_id")
		else:
			customer = getattr(doc, "customer", None)
			if not customer:
				return
			nif = frappe.db.get_value("Customer", customer, "tax_id")

		if not nif:
			frappe.throw(
				_("{0} com valor superior a 1000€ exige NIF do cliente/parceiro antes de submeter.")
				.format(_(doc.doctype)),
				title=_("NIF Obrigatório"),
			)

	def _validate_critical_fields(self, doc):
		"""Validar campos críticos"""
		config = self.supported_doctypes[doc.doctype]
		if config.get("critical") and not getattr(doc, 'naming_series', None):
			frappe.throw(_("Série portuguesa é obrigatória para {0}").format(_(doc.doctype)))

	def _validate_series_not_inactive(self, doc):
		"""
		Bloqueio físico contra emitir um documento numa série que a AT já
		considera fechada (Finalizada) ou nunca aconteceu (Anulada).

		A opção deveria desaparecer do campo Naming Series assim que a
		série fica inativa (ver applyNamingSeriesFilter em
		public/js/portugal_compliance.js, que filtra sempre de fresco a
		partir de Portugal Series Configuration), mas esta validação é
		a rede de segurança real do lado do servidor - não depende de
		nenhum estado client-side já ter sido recarregado (auditoria de
		certificação 2026-08-24: confirmado ao vivo que uma série
		anulada continuava selecionável até um refresh manual, na
		altura em que este filtro ainda era feito por Property Setter).

		Só bloqueia documentos que ainda NÃO têm ATCUD - um documento já
		assinado quando a série ainda estava ativa (ex: a cancelar
		depois de a série ter sido finalizada mais tarde) nunca deve ser
		bloqueado por esta verificação.
		"""
		if getattr(doc, 'atcud_code', None):
			return

		naming_series = getattr(doc, 'naming_series', None)
		if not naming_series:
			return

		prefix = naming_series.replace('.####', '')
		is_active = frappe.db.get_value(
			"Portugal Series Configuration",
			{"prefix": prefix, "company": doc.company},
			"is_active",
		)

		if is_active is not None and not is_active:
			frappe.throw(
				_("A série {0} está Finalizada/Anulada. Comunique uma nova série à AT antes de faturar.").format(prefix),
				title=_("Série Inativa"),
			)

	def _validate_series_registered_in_compliance(self, doc):
		"""
		Escudo definitivo: bloqueia gravar um documento com uma
		naming_series que não está registada em Portugal Series
		Configuration para esta empresa, ou que lá está mas ainda não foi
		comunicada à AT. Fecha a via de "séries fantasma" que
		utils/naming_series_customizer.py podia introduzir (escrita
		direta em DocType.autoname, nunca criava um registo em Portugal
		Series Configuration) - _validate_series_not_inactive (acima) só
		bloqueia séries que EXISTEM e estão is_active=0; uma série que
		nunca existiu como registo passava incólume por essa verificação
		(is_active vinha None, a condição "is_active is not None and not
		is_active" nunca disparava). Auditoria 2026-08-29, depois de
		confirmar que naming_series_customizer.py reintroduzia
		exatamente essa via paralela no Onboarding.

		Âmbito: corre para todos os doctypes em self.supported_doctypes
		(Sales Invoice, POS Invoice, Payment Entry, Delivery Note,
		Quotation, Sales Order desde a Fase 1) - Purchase Order/
		Material Request ficam fora deliberadamente, nunca chamam este
		método (não são fiscais - ver document_hooks.py:supported_doctypes).
		Nota 2026-09-04: este comentário afirmava antes que Quotation/
		Sales Order nunca chamavam este método - desatualizado desde a
		Fase 1, que os tornou doctypes de compliance completo.

		Só documentos ainda sem ATCUD - mesma lógica de
		_validate_series_not_inactive: um documento já assinado nunca
		deve ser bloqueado retroativamente por esta verificação.
		"""
		if getattr(doc, 'atcud_code', None):
			return

		naming_series = getattr(doc, 'naming_series', None)
		if not naming_series:
			return

		prefix = naming_series.replace('.####', '')
		is_communicated = frappe.db.get_value(
			"Portugal Series Configuration",
			{"prefix": prefix, "company": doc.company},
			"is_communicated",
		)

		if not is_communicated:
			frappe.throw(
				_("A série selecionada não está registada ou autorizada no módulo de Compliance AT."),
				title=_("Série Não Autorizada"),
			)

	def before_insert_document(self, doc, method=None):
		"""
		Hook before_insert (2026-08-31). Reaproveita _validate_tax_exemption_hard
		- a mesma validação rígida já usada em before_submit_document -
		mas aqui, antes de Document.insert() chamar set_new_name(), que
		é o passo que atribui/consome definitivamente o número de série
		fiscal (contador atómico nativo do Frappe, nunca decrementa,
		mesmo que o rascunho seja depois apagado).

		Achado ao vivo: uma POS Invoice com uma linha isenta (0%) sem
		motivo de isenção preenchido ficava presa em Rascunho ao falhar
		em before_submit - mas o número da série (ex. FS2026ZB0001) já
		tinha sido consumido no insert() do rascunho, antes de qualquer
		validação correr. O documento seguinte (FS2026ZB0002) submetia
		normalmente, criando um "buraco" na numeração ATCUD da série
		(a sequência do ATCUD vem diretamente do sufixo de doc.name).

		Mover a validação para validate() não resolveria nada - lido em
		frappe/model/document.py::Document.insert(): self.set_new_name()
		corre ANTES de self.run_before_save_methods() (que chama
		validate()). before_insert é o único hook do ciclo de vida que
		corre antes da atribuição do nome, por isso é o único ponto onde
		bloquear aqui evita mesmo o consumo do número.

		Não inclui _validate_nif_threshold aqui de propósito: depende de
		grand_total/paid_amount, só calculados pelo controller nativo do
		ERPNext dentro do seu próprio validate() - ainda não existem de
		forma fiável neste ponto do ciclo de vida. Continua só em
		before_submit_document, como camada de segurança secundária -
		tal como _validate_tax_exemption_hard também continua lá, dupla
		validação deliberada para o caso de um rascunho válido no
		momento da criação ser editado para um estado inválido antes de
		ser submetido.
		"""
		if not self._is_portuguese_company(
			doc.company) or doc.doctype not in self.supported_doctypes:
			return

		# Limpa ATCUD/QR "herdados" por copia de campo (2026-09-04,
		# achado ao vivo): frappe.model.mapper.get_mapped_doc (usado por
		# QUALQUER botao nativo "Make X" - Sales Order -> Sales Invoice,
		# Quotation -> Sales Order, Delivery Note -> Sales Invoice, etc.)
		# copia por omissao qualquer campo com o MESMO NOME entre
		# documento de origem e o novo rascunho, sem saber que
		# atcud_code/qr_code/qr_code_image sao identificadores unicos e
		# assinados, nunca copiaveis. reset_fiscal_fields_on_return_clone
		# ja cobria isto para o caso de devolucao (is_return=1); este
		# bloqueio e mais generico - qualquer documento novo destes
		# doctypes que chegue aqui com atcud_code ja preenchido so pode
		# ser esse tipo de fuga (um documento genuinamente novo nunca
		# tem ATCUD antes do seu proprio submit - ver generate_atcud_on_submit).
		# Confirmado ao vivo: "Make Sales Invoice" a partir de um Sales
		# Order ja assinado tentava reutilizar o MESMO atcud_code na
		# fatura nova, rejeitado por _validate_atcud_uniqueness_certified
		# so na submissao - tarde demais, o rascunho ja tinha sido criado
		# com um ATCUD alheio.
		if doc.is_new():
			for leaked_field in ("atcud_code", "qr_code", "qr_code_image"):
				if getattr(doc, leaked_field, None):
					doc.set(leaked_field, None)

		self._validate_tax_exemption_hard(doc)

	def before_submit_document(self, doc, method=None):
		"""✅ OTIMIZADO: Hook before_submit"""
		try:
			if not self._is_portuguese_company(
				doc.company) or doc.doctype not in self.supported_doctypes:
				return

			self._validate_tax_exemption_hard(doc)
			self._validate_nif_threshold(doc)

			config = self.supported_doctypes[doc.doctype]

			if config.get("requires_atcud"):
				# Escudo de pre-requisitos de assinatura (2026-08-31,
				# pedido explicito do utilizador apos o teste ao vivo da
				# cadeia de hashes): sign_document() ja e chamada em
				# generate_atcud_on_submit, mas essa chamada e
				# deliberadamente permissiva - captura SignatureError,
				# regista em Error Log e deixa o ATCUD continuar sem
				# assinatura (HashCharacters cai para "0"), porque a
				# decisao de bloquear ou nao pertence a uma camada de
				# politica, nao ao gerador de ATCUD em si (ver nota nesse
				# ficheiro). Este e essa camada: reutiliza
				# _load_private_key() - a MESMA verificacao exata que a
				# assinatura real faria dali a poucos passos (caminho
				# preenchido, ficheiro existe, e legivel, contem uma
				# chave PEM valida) - mas aqui, antes da submissao se
				# tornar irreversivel (docstatus 0->1, documento
				# imutavel), a mesma falha passa a bloquear em vez de
				# degradar em silencio.
				#
				# Gate em requires_atcud isolado, nao em
				# "fiscal_document and requires_atcud" como o bloco da
				# serie comunicada acima: Delivery Note tem
				# fiscal_document=False mas requires_atcud=True (nao e
				# fatura, mas tem ATCUD e assinatura por lei na mesma,
				# Portaria 363/2010) - com o gate duplo este escudo
				# nunca teria corrido para guias de transporte.
				from portugal_compliance.utils.signature import _load_private_key, SignatureError
				try:
					_load_private_key()
				except SignatureError as e:
					frappe.throw(
						_(
							"Emissão bloqueada: A Chave Privada de Assinatura Digital não "
							"está configurada no Portugal Auth Settings. O documento não "
							"pode ser selado legalmente."
						) + f" ({str(e)})",
						title=_("Assinatura Digital em Falta"),
					)

			if config.get("fiscal_document") and config.get("requires_atcud"):
				# O ATCUD ainda nao existe nesta fase - so e gerado em
				# on_submit, depois de todas as validacoes (incluindo
				# esta) terem passado (ver generate_atcud_on_submit).
				# Aqui verifica-se, ANTES de assinar, que a serie ja foi
				# comunicada a AT: gerar e assinar um documento numa
				# serie nao comunicada produziria um ATCUD com um codigo
				# de validacao fabricado, e um documento submetido fica
				# imutavel - nunca poderia ser corrigido, so anulado e
				# reemitido. Substitui a antiga verificacao pos-hoc de
				# "atcud_code comeca por TEMP", que so fazia sentido
				# quando a assinatura ja tinha corrido antes de save.
				naming_series = getattr(doc, 'naming_series', None)
				if naming_series:
					prefix = naming_series.replace('.####', '')
					is_communicated = frappe.db.get_value(
						"Portugal Series Configuration",
						{"prefix": prefix, "company": doc.company},
						"is_communicated",
					)
					if not is_communicated:
						frappe.throw(
							_(
								"A série {0} ainda não foi comunicada à AT. Comunique a série "
								"antes de submeter documentos fiscais - ver Portugal Series "
								"Configuration."
							).format(prefix)
						)

			if not self._is_portuguese_naming_series(getattr(doc, 'naming_series', '')):
				frappe.throw(_("Naming series portuguesa é obrigatória"))

		except Exception as e:
			frappe.log_error(f"Erro validação submissão: {str(e)}")
			raise

	def validate_transport_start_time(self, doc, method=None):
		"""
		Hook de before_submit exclusivo da Delivery Note. Bloqueia a
		submissão se a Data/Hora de Início do Transporte
		(at_data_hora_inicio_transporte) estiver preenchida com um
		valor que já não está no futuro.

		Não valida o caso do campo vazio: build_transport_payload()
		usa posting_date/posting_time como fallback nesse caso
		(comportamento aceite de propósito - ver
		at_transport_webservice.py) e a AT já trata esse cenário como
		um alerta não bloqueante (código -100), nunca como erro
		fatal. O que esta validação evita é o utilizador escolher
		manualmente uma data passada: a AT aceita na mesma, mas nunca
		emite um Código de Transporte real (fica "pendente" no PDF) -
		confirmado ao vivo em GR2026ZB0001/GR2026ZB0003.

		Usa frappe.utils.now_datetime()/get_datetime(), nunca
		datetime.now()/utcnow() do Python: o Frappe grava e lê campos
		Datetime sempre no fuso horário de System Settings (neste
		site, Atlantic/Azores), não em UTC nem no fuso do próprio
		servidor - misturar isso teria produzido exatamente o tipo de
		erro de horas que esta validação existe para evitar.
		"""
		if doc.doctype != "Delivery Note":
			return
		if not self._is_portuguese_company(doc.company):
			return

		start_time = getattr(doc, "at_data_hora_inicio_transporte", None)
		if not start_time:
			return

		if get_datetime(start_time) <= now_datetime():
			frappe.throw(
				_(
					"Para comunicar o documento à AT e obter o Código de Transporte, "
					"a Data e Hora de Início do Transporte tem de ser no futuro. "
					"Por favor, atualize o campo antes de submeter."
				),
				title=_("Data de Início de Transporte Inválida"),
			)

	# validate_portugal_compliance_light() removida (2026-08-30): só
	# existia para mostrar "Esta série não segue o formato de série
	# portuguesa recomendado" em Quotation/Sales Order/Purchase Order/
	# Material Request - nenhum destes é fiscal (ver supported_doctypes
	# acima), e usar naming_series nativas do ERPNext nestes doctypes
	# passou a ser o comportamento esperado, não um desvio a assinalar.
	# Ver hooks.py (doc_events destes 4 doctypes, também removidos).

	def validate_customer_nif(self, doc, method=None):
		"""Valida o formato do NIF do cliente quando fornecido e, se
		Portugal Auth Settings > "Exigir NIF do Cliente" estiver ativo,
		bloqueia a gravação de um Cliente português sem NIF."""
		self._validate_party_nif(doc, "Customer")
		self._enforce_required_customer_nif(doc)

	def validate_supplier_nif(self, doc, method=None):
		"""Valida o formato do NIF do fornecedor quando fornecido."""
		self._validate_party_nif(doc, "Supplier")

	def _is_portuguese_party(self, doc, party_type):
		"""
		Determina se um Customer/Supplier é português, para restringir a
		validação de NIF a esses casos (Portugal Auth Settings >
		"Validar NIF"/"Exigir NIF do Cliente").

		Supplier tem campo `country` direto. Customer não tem - o país
		só existe no endereço primário ligado (`customer_primary_address`
		-> Address.country).

		Alterado na Auditoria Fase 0 (2026-08-26): quando não é possível
		determinar o país (sem endereço/país ainda, ex: cliente ou
		fornecedor recém-criado), a omissão passou a ser NÃO português
		(era o inverso). A regra de ouro deste módulo é só alterar
		comportamento nativo quando há prova de que a empresa/entidade é
		portuguesa - assumir português sem endereço bloqueava a criação
		de clientes/fornecedores internacionais sempre que "Exigir NIF
		do Cliente" estivesse ativo em Portugal Auth Settings (um switch
		único, global ao site, sem dimensão de empresa), já que um
		registo novo nunca tem endereço associado no momento da
		primeira gravação.
		"""
		if party_type == "Supplier":
			country = getattr(doc, 'country', None)
			return country == "Portugal"

		address = getattr(doc, 'customer_primary_address', None)
		if not address:
			return False

		country = frappe.db.get_value("Address", address, "country")
		return country == "Portugal"

	def _enforce_required_customer_nif(self, doc):
		auth_settings = frappe.get_single("Portugal Auth Settings")
		if not cint(auth_settings.get("require_customer_nif")):
			return

		if getattr(doc, 'tax_id', None):
			return

		if not self._is_portuguese_party(doc, "Customer"):
			return

		frappe.throw(
			_("NIF é obrigatório para clientes portugueses (Portugal Auth Settings > \"Exigir NIF do Cliente\")."),
			title=_("NIF em Falta"),
		)

	def _validate_party_nif(self, doc, party_type):
		try:
			tax_id = getattr(doc, 'tax_id', None)
			if not tax_id:
				return

			auth_settings = frappe.get_single("Portugal Auth Settings")
			if not cint(auth_settings.get("validate_nif", 1)):
				return

			# 999999990 é o NIF genérico legal ("Consumidor Final") usado
			# quando não há NIF real - já passa o módulo 11 por
			# construção (confirmado: dígitos 9x8 dão resto 0, dígito de
			# controlo 0), mas ignorado aqui explicitamente para não
			# depender disso caso o algoritmo mude no futuro.
			nif_clean = re.sub(r'\D', '', str(tax_id))
			if nif_clean == '999999990':
				return

			if not self._is_portuguese_party(doc, party_type):
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

			self._enforce_communicated_series_immutability(doc)
		except frappe.ValidationError:
			raise
		except Exception as e:
			frappe.log_error(f"Erro em validate_series_configuration: {str(e)}")

	# Campos que identificam de forma inequivoca a serie perante a AT -
	# alterar qualquer um deles depois de comunicada desalinha a
	# geracao local do ATCUD com o que a AT validou, corrompendo a
	# cadeia. is_active incluido por decisao explicita: o estado so
	# deve mudar via finalizar_serie()/anular_serie() (at_webservice.py),
	# que gravam com frappe.db.set_value() direto - nunca passam por
	# esta validacao, por isso nao ficam bloqueados por este check.
	COMMUNICATED_SERIES_LOCKED_FIELDS = (
		"company", "document_type", "prefix", "naming_series",
		"validation_code", "at_environment", "is_communicated",
		"communication_date", "is_active",
	)

	def _enforce_communicated_series_immutability(self, doc):
		"""
		Bloqueio real (nao so client-side) para uma serie ja comunicada
		a AT. So compara contra o estado ANTES desta gravacao - a
		propria transicao de is_communicated de 0 para 1 (a comunicacao
		em si, feita via .save() com validation_code preenchido - ver
		validate() nativo do DocType) nunca e bloqueada, porque nesse
		momento o valor anterior ainda e 0.
		"""
		if doc.is_new():
			return

		before = doc.get_doc_before_save()
		if not before or not getattr(before, 'is_communicated', 0):
			return

		changed_fields = [
			fieldname for fieldname in self.COMMUNICATED_SERIES_LOCKED_FIELDS
			if getattr(doc, fieldname, None) != getattr(before, fieldname, None)
		]
		if changed_fields:
			frappe.throw(
				_(
					"Esta série já foi comunicada à AT - os campos {0} são imutáveis. "
					"Use \"Finalizar Série na AT\" ou \"Anular Série na AT\" para alterar o estado da série."
				).format(", ".join(changed_fields))
			)

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
		"""
		✅ OTIMIZADO: Validar unicidade do ATCUD

		Verificado na Auditoria Fase 0 (2026-08-26, item "Performance/
		Queries Redundantes"): o guard abaixo já garante que o loop de
		frappe.db.exists() por doctype só corre quando atcud_code está
		de facto preenchido - nenhuma alteração necessária aqui.
		"""
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

	# _update_portugal_compliance_fields removida (2026-08-24): unico
	# chamador era generate_atcud_before_save (tambem removida). Ficou
	# orfa - so escrevia portugal_compliance_status, um campo que nunca
	# existiu como coluna real em nenhum doctype fiscal (confirmado
	# contra fixtures/custom_field.json), so em memoria, nunca
	# persistido - nao fazia nada de util mesmo antes de ficar sem
	# chamador.

	# ========== MÉTODOS DE CONFIGURAÇÃO ==========

	def _create_dynamic_portugal_series_certified(self, company_doc):
		"""
		Cria as séries portuguesas base no setup automático da empresa
		(zero-touch): as 4 séries base (FT/FS/RG/GR, via
		_create_series_fallback - ver nota abaixo sobre o nome) e,
		adicionalmente, aprovisiona a(s) série(s) de devolução (NC) via
		api.company_api.ensure_return_series_for_company, para cada
		entrada de RETURN_DOCUMENT_SERIES que não partilhe a série de
		outro doctype (ver "shares_series_with" - ex: POS Invoice reusa
		a NC de Sales Invoice, não precisa de uma própria).

		Auditoria 2026-09-03: antes desta correção, este método
		importava portugal_compliance.regional.portugal.
		setup_all_series_for_company - função que nunca existiu nesse
		módulo (confirmado por grep total ao repositório). O ImportError
		daí resultante era sempre apanhado silenciosamente e caía sempre
		no fallback (_create_series_fallback, só as 4 séries base, sem
		NC). Nenhuma empresa ativada pelo fluxo automático alguma vez
		recebeu a série de devolução por este caminho - só quem clicou
		manualmente em "Gerar Séries Base" (api.company_api.
		setup_all_series_for_company, que já fazia isto corretamente por
		um caminho diferente) ou emitiu uma devolução depois de outro
		código a criar reativamente.

		Nota de arquitetura: NÃO se corrigiu simplesmente para chamar
		api.company_api.setup_all_series_for_company (a função "real" e
		completa que o nome sugeria) - essa função começa precisamente
		por chamar ESTE método (portugal_document_hooks.
		_create_dynamic_portugal_series_certified) para criar as séries
		base, o que teria criado uma recursão infinita direta entre os
		dois ficheiros. Em vez disso, este método replica aqui a mesma
		lógica de aprovisionamento de devolução que
		setup_all_series_for_company já faz depois de delegar as séries
		base - os dois caminhos (automático e botão manual) convergem
		para o mesmo estado final, sem um chamar o outro.
		"""
		try:
			result = self._create_series_fallback(company_doc)

			from portugal_compliance.api.company_api import (
				RETURN_DOCUMENT_SERIES,
				ensure_return_series_for_company,
			)
			for doctype, config in RETURN_DOCUMENT_SERIES.items():
				if "shares_series_with" in config:
					continue
				ensure_return_series_for_company(company_doc.name, doctype)

			return result
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

	# _replace_naming_series_with_portuguese_only / _update_property_setter_for_doctype
	# removidas (Auditoria Fase 0, 2026-08-26): escreviam um Property
	# Setter global (doctype_or_field="DocField", sem dimensão de
	# empresa) nas opções do campo naming_series - com mais do que uma
	# empresa portuguesa no site, a última a gravar substituía
	# inteiramente a lista da anterior. Ver
	# public/js/portugal_compliance.js::applyNamingSeriesFilter para o
	# mecanismo que as substitui (filtragem client-side, sempre
	# consultada de fresco para a empresa selecionada no formulário).

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

	# _setup_tax_templates_for_company / _setup_default_accounts /
	# _get_or_create_iva_account removidas (Auditoria Fase 0,
	# 2026-08-26): nenhuma das três tinha qualquer chamador em todo o
	# repositório (confirmado por grep) - código morto dentro de um
	# ficheiro vivo. O caminho real e ativo para templates de impostos
	# é portugal_compliance.setup.tax_setup.create_regional_tax_setup_for_company
	# (chamado em _execute_compliance_setup acima, itera as 3 regiões via
	# setup_tax_templates_for_company), que usa a taxonomia SNC 2433x/
	# 2434x/2435x real por taxa e região, não a conta genérica "IVA"
	# que este código morto criava - mantê-lo teria sido um risco real
	# se algum dia fosse reativado por engano.


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
		#
		# "shares_series_with" (2026-09-03, pedido explicito do
		# utilizador): POS Invoice nao tem serie NC propria - usa a
		# MESMA serie NC ja aprovisionada para Sales Invoice, em vez de
		# criar uma segunda serie so para devolucoes de retalho. A
		# AT nao distingue "NC de FT" de "NC de FS" (o tipoDoc enviado
		# ao webservice de series e sempre "NC", ver
		# at_webservice.py::_map_doc_code_to_class) - so a numeracao tem
		# de ser sequencial e sem buracos, nao exclusiva por doctype de
		# origem. document_type aqui e o doctype "dono" do registo em
		# Portugal Series Configuration (onde a serie foi criada e
		# comunicada), nao necessariamente doc.doctype.
		from portugal_compliance.api.company_api import RETURN_DOCUMENT_SERIES
		if doc.doctype in RETURN_DOCUMENT_SERIES:
			return_config = RETURN_DOCUMENT_SERIES[doc.doctype]
			return_code = return_config["code"]
			series_owner_doctype = return_config.get("shares_series_with", doc.doctype)
			return_series = frappe.db.get_value(
				"Portugal Series Configuration",
				{
					"company": doc.company,
					"document_type": series_owner_doctype,
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


def generate_atcud_on_submit(doc, method=None):
	"""Hook global para geração de ATCUD - só em on_submit, ver nota no método de classe"""
	return portugal_document_hooks.generate_atcud_on_submit(doc, method)


def validate_portugal_compliance(doc, method=None):
	"""Hook para validate de documentos"""
	return portugal_document_hooks.validate_portugal_compliance(doc, method)


def before_submit_document(doc, method=None):
	"""Hook para before_submit de documentos"""
	return portugal_document_hooks.before_submit_document(doc, method)


def before_insert_document(doc, method=None):
	"""Hook para before_insert de documentos - ver nota no método de classe"""
	return portugal_document_hooks.before_insert_document(doc, method)


def validate_transport_start_time(doc, method=None):
	"""Hook para before_submit da Delivery Note - Data/Hora de Início do Transporte tem de estar no futuro"""
	return portugal_document_hooks.validate_transport_start_time(doc, method)


# Doctypes fiscais efetivamente cobertos pelo motor de compliance (mesmo
# âmbito de FISCAL_IMMUTABLE_DOCTYPES) - usados aqui, não importados dali,
# para não criar uma dependência circular a esta altura do ficheiro.
FISCAL_RECORD_DOCTYPES = ("Sales Invoice", "POS Invoice", "Delivery Note", "Payment Entry")


@frappe.whitelist()
def has_existing_fiscal_records(company):
	"""
	True se a empresa já tem pelo menos um documento fiscal submetido
	(docstatus=1) num dos 4 doctypes fiscais - usada por
	validate_company_fiscal_lock para travar alterações a País/NIF da
	Company depois de já ter emitido documentos reais. `frappe.db.exists`
	pára na primeira ocorrência (não conta o total), suficiente para uma
	pergunta puramente booleana.

	Whitelisted (2026-09-01) para uso direto do client-side
	(company.js::refresh) - o bloqueio real e inatacável já existe no
	servidor (validate_company_fiscal_lock); isto serve apenas para a UI
	aplicar read-only aos campos ANTES do clique, evitando o "falso
	positivo" do diálogo de confirmação client-side disparar sem que a
	alteração possa alguma vez ser gravada. Não expõe informação sensível
	(devolve só um booleano), mas confirma permissão de leitura na
	Company mesmo assim, por defeito em profundidade.
	"""
	if not frappe.has_permission("Company", "read", company):
		frappe.throw(_("Sem permissão para consultar esta empresa"), frappe.PermissionError)
	if not company:
		return False
	for doctype in FISCAL_RECORD_DOCTYPES:
		if frappe.db.exists(doctype, {"company": company, "docstatus": 1}):
			return True
	return False


def validate_company_fiscal_lock(doc, method=None):
	"""Hook para validate de Company - ver nota no método de classe"""
	return portugal_document_hooks.validate_company_fiscal_lock(doc, method)


def setup_company_portugal_compliance(doc, method=None):
	"""
	Hook global para on_update de Company. Faltava esta funcao (hooks.py
	referenciava-a mas so existia como metodo de classe, nunca acessivel
	via frappe.get_attr) - qualquer gravacao de qualquer empresa, PT ou
	nao, crashava com AttributeError assim que a app estava instalada.
	"""
	return portugal_document_hooks.setup_company_portugal_compliance(doc, method)


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


# refresh_property_setters_for_company removida (Auditoria Fase 0,
# 2026-08-26): sem chamadores (confirmado por grep a todo o
# repositório) e expunha _setup_automatic_property_setters, também
# removida - ver nota junto a essa função.


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


# sync_communication_settings removida (2026-08-30): tentava espelhar
# Company.invoice_communication_method/transport_communication_method
# com os campos reais em Portugal Auth Settings (Single), mas só
# corria no validate() da Company - editar Portugal Auth Settings
# diretamente (o ecrã real de configuração AT) nunca propagava de
# volta para a Company, deixando o espelho sistematicamente
# desatualizado (confirmado ao vivo: novadx mostrava "Offline (SAF-T
# Mensal)" na Company enquanto Portugal Auth Settings, a fonte real
# lida por at_invoice_webservice.py/at_transport_webservice.py, tinha
# "Tempo Real (Webservice)"). Os 2 custom fields espelho e o
# saft_export_path (nunca lido em nenhum ponto do código real) foram
# removidos de Company - Portugal Auth Settings é a única fonte de
# verdade, sem duplicação na UI.


# sync_at_credentials removida (2026-08-23): mantinha
# Company.at_username/at_password/at_environment sincronizados nos
# dois sentidos com Portugal Auth Settings - uma mitigacao provisoria
# da duplicacao de credenciais identificada na auditoria. Decisao
# final: eliminar os campos legados da Company (ver
# fixtures/custom_field.json e hooks.py) em vez de os manter
# sincronizados - Portugal Auth Settings passa a ser a unica fonte de
# verdade, sem risco de divergencia por desenho. Ver tambem
# api/company_api.py (botoes "Configurar Credenciais AT"/"Testar
# Conexao AT" removidos no mesmo commit).


# Nota (2026-08-24): generate_and_attach_qr_code (hook de after_insert)
# foi removida - a geracao do QR Code (qr_code/qr_code_image) passou a
# correr dentro de generate_atcud_on_submit, logo a seguir a assinatura,
# porque o QR depende do atcud_code que so existe a partir do submit
# (ver nota "rascunho zombie" em generate_atcud_on_submit). Os print
# formats continuam a calcular o QR fresco no momento da impressao,
# nao dependem deste campo persistido.


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

FISCAL_IMMUTABLE_DOCTYPES = ["Sales Invoice", "Delivery Note", "Payment Entry", "POS Invoice", "Quotation", "Sales Order"]

# Campos cuja alteracao depois de assinado invalidaria a assinatura
# RSA-SHA1 ja calculada (generate_atcud_on_submit so gera o ATCUD uma
# vez, no submit, nunca regenera - sem este bloqueio seria possivel
# editar o total/cliente/data de um documento ja submetido/assinado e
# a assinatura ficava a corresponder a dados que ja nao existem).
FISCAL_LOCK_FIELDS = {
	"Sales Invoice": ["customer", "posting_date", "grand_total", "net_total", "is_return", "naming_series", "atcud_code"],
	"POS Invoice": ["customer", "posting_date", "grand_total", "net_total", "naming_series", "atcud_code"],
	"Delivery Note": ["customer", "posting_date", "naming_series", "is_return", "atcud_code"],
	"Payment Entry": ["party", "posting_date", "paid_amount", "received_amount", "naming_series", "atcud_code"],
	# Quotation usa party_name (Dynamic Link), nunca "customer" - so
	# existe um campo "customer" literal quando quotation_to='Customer',
	# mas fica sempre None nesse caso especifico (confirmado no commit
	# 700e2d6, bug real ja apanhado uma vez: validate_portuguese_quotation()
	# antigo verificava frm.doc.customer, que era sempre undefined).
	"Quotation": ["party_name", "transaction_date", "grand_total", "net_total", "naming_series", "atcud_code"],
	"Sales Order": ["customer", "transaction_date", "grand_total", "net_total", "naming_series", "atcud_code"],
}


def block_fiscal_document_deletion(doc, method=None):
	"""
	Hook de on_trash. Bloqueia eliminacao de qualquer documento fiscal
	que ja tenha ATCUD/assinatura gerados, que esteja anulado
	(docstatus=2) mesmo sem ATCUD, ou que ainda seja rascunho
	(docstatus=0) mas ja tenha consumido um numero de uma serie fiscal
	portuguesa - em qualquer um dos tres casos, o registo tem de
	permanecer.

	Guard de empresa portuguesa acrescentado na Auditoria Fase 0
	(2026-08-26): sem isto, o bloqueio de docstatus=2 (documento
	anulado) aplicava-se a QUALQUER Sales Invoice/POS Invoice/Payment
	Entry/Delivery Note cancelado, de qualquer empresa do site,
	portuguesa ou não - cancelar e depois eliminar é um fluxo legítimo
	do ERPNext fora de Portugal, que este hook alterava globalmente.

	Ramo docstatus=0 acrescentado 2026-08-28 (pedido do utilizador,
	"Proteção da Sequencialidade"): o Frappe atribui o nome definitivo
	via naming_series (ex: RG2026ZB0001) logo no primeiro save de um
	rascunho, nao so na submissao - consome sempre um numero do
	contador da serie em tabSeries, quer o documento venha a ser
	submetido ou nao. Apagar esse rascunho nao devolve o numero ao
	contador (o Frappe nunca decrementa series), criando um buraco na
	sequencia visivel para a AT (ex: RG...0001 nunca existiu, RG...0002
	e o primeiro documento real) - exatamente o tipo de quebra de
	sequencialidade que a Portaria 195/2020 exige poder justificar.
	Nao e preciso verificar aqui se doc.naming_series corresponde a uma
	serie registada em Portugal Series Configuration: qualquer
	documento destes 4 doctypes, de uma empresa portuguesa, que exista
	na base de dados ja passou por
	_validate_series_registered_in_compliance (chamada em validate() -
	ver mais acima nesta classe) - a sua mera existencia aqui garante
	que a serie e genuina.
	"""
	if doc.doctype not in FISCAL_IMMUTABLE_DOCTYPES:
		return

	if not portugal_document_hooks._is_portuguese_company(doc.company):
		return

	if doc.docstatus == 0 and getattr(doc, "naming_series", None):
		frappe.throw(
			_(
				"Documentos de séries fiscais portuguesas não podem ser apagados para preservar "
				"a sequência legal, mesmo em rascunho - {0} {1} já consumiu um número da série "
				"({2}). Submeta o documento e anule-o (Cancelar) para justificar a numeração à AT, "
				"em vez de o eliminar."
			).format(_(doc.doctype), doc.name, doc.naming_series),
			title=_("Eliminação Bloqueada"),
		)

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
	Hook de before_save. Compara com get_doc_before_save() (estado na
	BD antes desta gravacao); se o documento ja tinha ATCUD antes desta
	gravacao, nenhum dos campos fiscais pode ter mudado. Na pratica so
	dispara depois de o documento ter sido submetido (e o unico momento
	em que atcud_code passa a existir - ver generate_atcud_on_submit),
	nunca num rascunho ainda em edicao.
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


def log_document_print(doc, method=None, print_settings=None):
	"""
	Hook de before_print. Regista no Portugal Document Print Log quem
	imprimiu o documento e quando (Requisito 4.3 da auditoria de
	certificação 2026-08-24) - o doctype já existia no módulo mas não
	era alimentado por nenhum hook (confirmado com grep total ao
	repositório antes desta alteração) - a pista de auditoria cobria
	emissão e anulação, mas não impressão/reimpressão.

	before_print corre no mesmo caminho de renderização tanto na
	pré-visualização de impressão como na geração de PDF/download
	(ver frappe.www.printview.get_rendered_template) - cobre os dois
	casos reais de "imprimir" no Frappe, não só um botão específico.
	Nunca bloqueia a impressão em si, mesmo que o registo falhe.
	"""
	if doc.doctype not in FISCAL_IMMUTABLE_DOCTYPES:
		return
	try:
		print_format = frappe.form_dict.get("format") or (print_settings or {}).get("print_format") or ""
		frappe.get_doc({
			"doctype": "Portugal Document Print Log",
			"document_type": doc.doctype,
			"document_name": doc.name,
			"print_format": print_format,
			"printed_by": frappe.session.user,
			"print_datetime": frappe.utils.now_datetime(),
			"atcud_code": getattr(doc, "atcud_code", None) or "",
		}).insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Erro ao registar impressão de {doc.doctype} {doc.name}: {str(e)}")


def _any_active_portuguese_company():
	"""
	True se existir pelo menos uma Company com country="Portugal" e
	portugal_compliance_enabled=1 no site. Guard partilhado pelas
	funções de after_migrate que alteram comportamento nativo do
	ERPNext ao nível do DocType (sem dimensão de empresa possível) -
	acrescentado na Auditoria Fase 0 (2026-08-26): antes corriam
	incondicionalmente em qualquer site com esta app instalada, mesmo
	sem nenhuma empresa portuguesa.
	"""
	return bool(frappe.db.exists("Company", {"country": "Portugal", "portugal_compliance_enabled": 1}))


def force_track_changes_property_setters():
	"""
	Chamada em after_migrate (ver hooks.py). Garante via Property Setter
	que track_changes esta sempre ativo nos doctypes fiscais, mesmo que
	alguem o desligue manualmente no Customize Form - pista de auditoria
	(quem alterou o que e quando) e um requisito de certificacao
	(Portaria 363/2010), nao uma preferencia de UI.

	Só atua se existir pelo menos uma empresa portuguesa com compliance
	ativo (ver _any_active_portuguese_company) - track_changes é uma
	propriedade do DocType inteiro, sem dimensão de empresa, por isso
	não há como restringir isto só às empresas portuguesas sem afetar
	as outras; a alternativa correta é não tocar em nada se não houver
	nenhuma empresa portuguesa no site.
	"""
	if not _any_active_portuguese_company():
		return

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


def set_pos_invoice_default_print_format():
	"""
	Chamada em after_migrate (ver hooks.py). Garante via Property Setter
	que "Fatura Simplificada PT" (talão térmico 80mm) é o print format
	por omissão do DocType POS Invoice.

	Sem isto, os botões "Imprimir Térmica"/"Reimprimir" (POS_invoice.js)
	abrem a vista de impressão nativa do Frappe sem nenhum formato
	pré-selecionado - a vista cai no primeiro formato "standard"
	disponível (normalmente um genérico do ERPNext, sem ATCUD/QR/
	layout térmico), dando uma 2ª via completamente diferente da
	impressa no checkout. Só se aplica a POS Invoice - nunca a Sales
	Invoice, que serve muito mais do que vendas de balcão (fixar aqui
	o formato térmico como omissão global forçaria um talão de 80mm em
	qualquer fatura normal impressa a partir do Desk).

	Só atua se existir pelo menos uma empresa portuguesa com compliance
	ativo (ver _any_active_portuguese_company) - default_print_format é
	uma propriedade do DocType inteiro, sem dimensão de empresa; sem
	este guard, uma empresa não-portuguesa que instale esta app via um
	site multi-empresa passava a ver um talão térmico em português como
	formato por omissão do seu POS Invoice.
	"""
	if not _any_active_portuguese_company():
		return

	try:
		existing = frappe.db.get_value(
			"Property Setter", {"doc_type": "POS Invoice", "property": "default_print_format"}, "name"
		)
		if existing:
			frappe.db.set_value("Property Setter", existing, "value", "Fatura Simplificada PT")
		else:
			frappe.get_doc({
				"doctype": "Property Setter",
				"doctype_or_field": "DocType",
				"doc_type": "POS Invoice",
				"property": "default_print_format",
				"property_type": "Data",
				"value": "Fatura Simplificada PT",
			}).insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Erro ao forçar default_print_format em POS Invoice: {str(e)}")
	frappe.clear_cache()


def ensure_pos_invoice_as_default():
	"""
	Chamada em after_migrate (self-heal) e em
	PortugalDocumentHooks._execute_compliance_setup (ativação zero-touch
	de uma empresa nova). Garante que "POS Settings.invoice_type" (campo
	"Invoice Type Created via POS Screen") fica em "POS Invoice" - todo o
	motor de compliance desta app (ATCUD/série FS/Fatura Simplificada/
	comunicação em tempo real/etc.) foi construído e testado à volta do
	doctype POS Invoice para vendas de balcão, nunca à volta de uma Sales
	Invoice emitida a partir do ecrã do POS.

	MITIGAÇÃO GLOBAL (ler antes de alterar): "POS Settings" é um DocType
	Single - um único registo para o site inteiro, sem dimensão de
	empresa, ao contrário de quase tudo o resto nesta app. Não existe
	equivalente por empresa no ERPNext core (confirmado: nem POS Profile
	tem um campo equivalente) - não há forma de tornar isto seguro para
	multi-empresa sem tocar no core. A mitigação real é: só grava
	"POS Invoice" enquanto o valor ainda for exatamente o default de
	fábrica do ERPNext ("Sales Invoice") - nunca sobrescreve uma escolha
	já feita por um administrador, seja de uma empresa portuguesa ou não.
	Num site com uma empresa portuguesa e outra não-portuguesa a partilhar
	este site, o pior cenário possível é o valor de fábrica do próprio
	ERPNext mudar uma única vez para a sua própria recomendação oficial
	(o texto de ajuda do campo já diz "recommended... POS Invoice") -
	nunca uma preferência humana deliberada a ser pisada. Se este site
	alguma vez tiver uma segunda empresa não-portuguesa que precise
	mesmo de "Sales Invoice" como default, a solução é mudar o valor
	manualmente depois desta função correr uma vez - fica reconhecido e
	nunca mais tocado (idempotente, ver guard abaixo).

	Só atua se existir pelo menos uma empresa portuguesa com compliance
	ativo (ver _any_active_portuguese_company) - mesmo guard já usado em
	set_pos_invoice_default_print_format acima, para o mesmo tipo de
	propriedade global sem dimensão de empresa.
	"""
	if not _any_active_portuguese_company():
		return

	try:
		current_value = frappe.db.get_single_value("POS Settings", "invoice_type")
		if current_value != "Sales Invoice":
			return

		frappe.db.set_single_value("POS Settings", "invoice_type", "POS Invoice")
		frappe.db.commit()
		frappe.logger().info(
			"ensure_pos_invoice_as_default: POS Settings.invoice_type alterado de "
			"'Sales Invoice' (default de fábrica) para 'POS Invoice'"
		)
	except Exception as e:
		frappe.log_error(f"Erro ao definir Invoice Type do POS por omissão: {str(e)}")


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Document Hooks OTIMIZADO loaded - Version 2.1.0 - Clean & Efficient")
