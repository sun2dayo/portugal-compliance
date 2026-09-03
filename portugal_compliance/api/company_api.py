# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Company API - Portugal Compliance VERSÃO ROBUSTA
APIs para gestão de configurações de empresa portuguesa
✅ Configuração de compliance português
✅ Criação automática de séries
✅ Validação de empresas portuguesas
✅ MELHORADO: Validação robusta de erros e logging detalhado
"""

import frappe
from frappe import _
import json
import traceback
from datetime import datetime

# ✅ IMPORTAR FUNÇÕES REAIS (Fase 6: setup_all_series_for_company e
# is_portuguese_company NUNCA existiram em regional/portugal.py sob
# esses nomes - o ImportError disparava sempre, silenciosamente, e o
# fallback de setup_all_series_for_company devolvia sempre um erro
# "Função não disponível" ao utilizador, confirmado ao vivo no GUI).
from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
from portugal_compliance.utils.document_hooks import portugal_document_hooks


def is_portuguese_company(company):
	try:
		company_doc = frappe.get_doc('Company', company)
		return company_doc.country == 'Portugal'
	except Exception:
		return False


def setup_all_series_for_company(company):
	"""
	Cria todas as séries portuguesas para uma empresa - usa a mesma
	implementação real já usada com sucesso por
	series_api.create_series_for_company.
	"""
	try:
		company_doc = frappe.get_doc("Company", company)
		result = portugal_document_hooks._create_dynamic_portugal_series_certified(company_doc)
		# Serie(s) dedicada(s) a devolucoes (Nota de Credito, NC) - tem
		# de ser aprovisionada e comunicada a AT ja aqui, no setup, nunca
		# criada/forcada na hora de emitir uma devolucao (ver
		# reset_fiscal_fields_on_return_clone em utils/document_hooks.py,
		# que so ENCAMINHA para esta serie, nunca a cria).
		#
		# "shares_series_with": entradas que reutilizam a serie de outro
		# doctype (ex: POS Invoice reutiliza a NC de Sales Invoice) nunca
		# chamam ensure_return_series_for_company aqui - criar uma
		# segunda serie com o mesmo document_code="NC" colidiria com o
		# prefixo ja existente (validate_prefix_uniqueness e por
		# prefixo+empresa, nao por document_type). Nao ha nada para
		# aprovisionar para estas entradas: a serie partilhada ja foi
		# criada quando a entrada "dona" (ex: Sales Invoice) foi
		# processada, mais acima neste mesmo loop.
		for doctype, config in RETURN_DOCUMENT_SERIES.items():
			if "shares_series_with" in config:
				continue
			ensure_return_series_for_company(company, doctype)
		return result
	except Exception as e:
		frappe.log_error(f"Erro ao criar séries para {company}: {str(e)}", "Company API Series Setup")
		return {"success": False, "error": str(e)}


# Doctypes cujas devolucoes (is_return=1) tem de usar uma serie AT
# propria, distinta da serie normal - exigencia da Ordem dos
# Contabilistas (a AT tecnicamente aceita series partilhadas desde
# que a sequencia nao quebre, mas misturar FT/NC gera entropia na
# auditoria).
#
# POS Invoice (2026-09-03, pedido explicito do utilizador): NAO tem
# serie NC propria - partilha a mesma serie ja aprovisionada para
# Sales Invoice ("shares_series_with"). A AT nao distingue "NC de FT"
# de "NC de FS": o tipoDoc enviado ao webservice de series e sempre
# "NC" (ver at_webservice.py::_map_doc_code_to_class), so a numeracao
# tem de ser sequencial e sem buracos - nao exclusiva por doctype de
# origem. Uma loja (POS) e o back-office podem legitimamente emitir
# notas de credito na mesma sequencia partilhada.
#
# Extensivel a Purchase Invoice (ND, Nota de Debito) se vier a ser
# necessario - nao implementado agora porque nao foi pedido.
RETURN_DOCUMENT_SERIES = {
	"Sales Invoice": {"code": "NC", "name": "Nota de Crédito"},
	"POS Invoice": {"code": "NC", "name": "Nota de Crédito", "shares_series_with": "Sales Invoice"},
}


def ensure_return_series_for_company(company, doctype="Sales Invoice"):
	"""
	Aprovisiona (se ainda nao existir) e comunica a AT a serie dedicada
	de devolucoes para o doctype indicado - PRE-REQUISITO legal
	(Portaria 195/2020) antes de qualquer documento poder ser emitido
	nessa serie: todas as series tem de ser comunicadas e obter o
	codigo de validacao da AT antes de gerar ATCUDs reais. Idempotente
	- seguro chamar em cada setup/ativacao de empresa.

	Comunicacao com a AT e best-effort: se falhar aqui (rede em baixo,
	etc), a serie fica criada mas is_communicated=0 - a tarefa horaria
	ja existente (tasks.hourly.try_series_communication, via
	process_failed_communications) reprocessa qualquer serie ativa
	nao comunicada automaticamente, sem necessidade de logica de
	retry propria aqui.
	"""
	return_info = RETURN_DOCUMENT_SERIES.get(doctype)
	if not return_info:
		return None

	company_doc = frappe.get_doc("Company", company)
	company_abbr = company_doc.abbr or company[:3].upper()
	current_year = datetime.now().year
	code = return_info["code"]
	prefix = f"{code}{current_year}{company_abbr}"

	series_name = frappe.db.get_value(
		"Portugal Series Configuration",
		{"company": company, "document_type": doctype, "document_code": code},
		"name",
	)

	if not series_name:
		series_doc = frappe.new_doc("Portugal Series Configuration")
		series_doc.update({
			"series_name": f"{return_info['name']} - {prefix}",
			"company": company,
			"document_type": doctype,
			"prefix": prefix,
			"naming_series": f"{prefix}.####",
			"current_sequence": 1,
			"is_active": 1,
			"is_communicated": 0,
			"document_code": code,
			"year_code": str(current_year),
			"company_code": company_abbr,
		})
		series_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		series_name = series_doc.name
		frappe.logger().info(f"Série de devolução criada: {series_name} ({prefix})")

		# _update_property_setter_for_doctype removida (Auditoria Fase 0,
		# 2026-08-26) - a série NC recém-criada fica visível de imediato
		# porque o dropdown de naming_series passou a ser filtrado
		# client-side, de fresco, em cada refresh/mudança de empresa do
		# formulário (ver public/js/portugal_compliance.js::
		# applyNamingSeriesFilter). Não há mais nenhuma lista estática
		# a regenerar nem risco de ordem desatualizada.

	try:
		series_doc = frappe.get_doc("Portugal Series Configuration", series_name)
		if not series_doc.is_communicated:
			from portugal_compliance.utils.at_webservice import ATWebserviceClient
			client = ATWebserviceClient()
			result = client.register_naming_series(series_doc.naming_series, company)
			if result.get("success"):
				series_doc.is_communicated = 1
				series_doc.communication_date = frappe.utils.now()
				series_doc.validation_code = result.get("validation_code")
				series_doc.communication_response = json.dumps(result.get("raw_response"), ensure_ascii=False, default=str)
				# Mesmo criterio de at_webservice.py::get_series_webservice_client()
				# para decidir a porta real usada (722 testes / 422 producao) -
				# sandbox_mode e a fonte de verdade sobre o ambiente realmente
				# usado nesta chamada SOAP, nao o default do campo.
				sandbox_mode = frappe.db.get_single_value("Portugal Auth Settings", "sandbox_mode")
				series_doc.at_environment = "Teste" if (sandbox_mode is None or int(sandbox_mode)) else "Produção"
				series_doc.flags.ignore_validate = True
				series_doc.save(ignore_permissions=True)
				frappe.db.commit()
			else:
				frappe.log_error(f"AT recusou a série de devolução {series_name}: {result.get('error')}", "PortugalReturnSeries")
	except Exception as e:
		frappe.log_error(f"Falha ao comunicar série de devolução {series_name}: {str(e)}", "PortugalReturnSeries")

	return series_name

@frappe.whitelist()
def save_company_settings(company_settings):
	"""
	✅ CORRIGIDO: Salvar configurações sem desativar compliance
	"""
	try:
		if isinstance(company_settings, str):
			company_settings = json.loads(company_settings)

		company_name = company_settings.get('company')
		action = company_settings.get('action', 'save_settings')

		if not company_name:
			return {'success': False, 'error': 'Nome da empresa é obrigatório'}

		# ✅ CONTROLO DE ACESSO: sem isto, qualquer utilizador autenticado
		# conseguia reescrever credenciais AT de qualquer empresa
		if not frappe.has_permission("Company", "write", company_name):
			frappe.throw(_("Sem permissão para alterar configurações desta empresa"), frappe.PermissionError)

		# ✅ OBTER EMPRESA SEM TRIGGERAR VALIDAÇÕES
		company_doc = frappe.get_doc("Company", company_name)

		# ✅ PRESERVAR ESTADO DE COMPLIANCE
		original_compliance = company_doc.portugal_compliance_enabled

		# ✅ PROCESSAR AÇÕES ESPECÍFICAS
		# 'save_at_credentials' e 'test_at_connection' removidas (2026-08-23):
		# Portugal Auth Settings é a única fonte de verdade para credenciais
		# AT - configurar/testar faz-se lá, não na Company. Ver nota em
		# document_hooks.sync_at_credentials (removida no mesmo commit).
		if action == 'communicate_all_series':
			return communicate_series_safe(company_doc, company_settings)
		else:
			# ✅ SALVAR CONFIGURAÇÕES GERAIS
			return save_general_settings_safe(company_doc, company_settings, original_compliance)

	except Exception as e:
		frappe.log_error(f"Erro em save_company_settings: {str(e)}")
		return {'success': False, 'error': str(e)}


def communicate_series_safe(company_doc, settings):
	"""
	✅ CORRIGIDO: Comunicar séries sem métodos inexistentes

	save_at_credentials_safe removida (2026-08-23): gravava
	Company.at_username/at_password/at_environment, campos legados
	eliminados - Portugal Auth Settings é agora a única fonte de
	verdade para credenciais AT (configuráveis lá, não na Company).
	"""
	try:
		# ✅ PRESERVAR COMPLIANCE
		original_compliance = company_doc.portugal_compliance_enabled

		# ✅ VERIFICAR CREDENCIAIS EM PORTUGAL AUTH SETTINGS (fonte real
		# usada por ATWebserviceClient/register_naming_series - a
		# verificacao aqui e so uma mensagem de erro mais cedo e mais
		# clara do que deixar a chamada ao webservice falhar mais tarde)
		auth_settings = frappe.get_single("Portugal Auth Settings")
		if not auth_settings.get("at_username") or not auth_settings.get_password(
			"at_password", raise_exception=False
		):
			return {
				'success': False,
				'error': 'Credenciais AT não configuradas em Portugal Auth Settings.'
			}

		# ✅ BUSCAR SÉRIES NÃO COMUNICADAS (só tipos que a AT realmente aceita
		# pré-comunicar - ver PORTUGAL_DOCUMENT_TYPES.communication_required;
		# tentar comunicar os restantes causa sempre rejeição AT [4046])
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		all_pending_series = frappe.get_all(
			"Portugal Series Configuration",
			filters={
				"company": company_doc.name,
				"is_active": 1,
				"is_communicated": 0
			},
			fields=["name", "prefix", "document_type"]
		)
		series_to_communicate = [
			s for s in all_pending_series
			if PORTUGAL_DOCUMENT_TYPES.get(s.document_type, {}).get("communication_required", False)
		]

		if not series_to_communicate:
			return {
				'success': True,
				'message': 'Todas as séries já estão comunicadas',
				'communicated_count': 0
			}

		# ✅ COMUNICAÇÃO REAL COM A AT (ATWebserviceClient.register_naming_series
		# - a mesma usada pelo resto da app desde a Fase 2)
		from portugal_compliance.utils.at_webservice import ATWebserviceClient
		client = ATWebserviceClient()

		# Mesmo criterio de at_webservice.py::get_series_webservice_client()
		# para decidir a porta real usada (722 testes / 422 producao) - lido
		# uma unica vez para o lote, nao muda a meio de uma comunicacao.
		sandbox_mode = frappe.db.get_single_value("Portugal Auth Settings", "sandbox_mode")
		at_environment = "Teste" if (sandbox_mode is None or int(sandbox_mode)) else "Produção"

		communicated_count = 0
		for series in series_to_communicate:
			try:
				series_doc = frappe.get_doc("Portugal Series Configuration", series.name)
				if not series_doc.naming_series:
					frappe.log_error(f"Série {series.name} sem naming_series associada")
					continue

				result = client.register_naming_series(series_doc.naming_series, company_doc.name)

				if result.get("success"):
					series_doc.is_communicated = 1
					series_doc.communication_date = frappe.utils.now()
					series_doc.validation_code = result.get("validation_code")
					series_doc.communication_response = json.dumps(result.get("raw_response"), ensure_ascii=False, default=str)
					series_doc.at_environment = at_environment
					series_doc.flags.ignore_validate = True
					series_doc.save(ignore_permissions=True)
					communicated_count += 1
				else:
					frappe.log_error(f"AT recusou a série {series.name}: {result.get('error')}")

			except Exception as e:
				frappe.log_error(f"Erro ao comunicar série {series.name}: {str(e)}")

		# ✅ GARANTIR COMPLIANCE SEM SAVE DA COMPANY
		if original_compliance:
			frappe.db.set_value("Company", company_doc.name, "portugal_compliance_enabled", 1)

		frappe.db.commit()

		return {
			'success': True,
			'message': f'{communicated_count} séries comunicadas com sucesso',
			'communicated_count': communicated_count,
			'total_series': len(series_to_communicate)
		}

	except Exception as e:
		frappe.log_error(f"Erro na comunicação de séries: {str(e)}")
		return {'success': False, 'error': str(e)}


def save_general_settings_safe(company_doc, settings, original_compliance):
	"""
	✅ CORRIGIDO: Salvar configurações sem métodos inexistentes
	"""
	try:
		# ✅ APLICAR APENAS CAMPOS SEGUROS
		# at_username/at_password/at_environment/at_certificate_number
		# removidos (2026-08-23) - campos legados eliminados da Company,
		# ver nota em communicate_series_safe.
		safe_fields = ['portugal_compliance_enabled']

		for key, value in settings.items():
			if key in safe_fields and hasattr(company_doc, key):
				setattr(company_doc, key, value)

		# ✅ PRESERVAR COMPLIANCE
		company_doc.portugal_compliance_enabled = original_compliance

		# ✅ SALVAR COM MÁXIMO BYPASS
		# ERPNext core (Company.on_update) le self.update_default_account,
		# que só é definido em Company.validate() - com ignore_validate=True
		# esse validate() não corre, por isso definimos aqui para evitar
		# AttributeError em on_update().
		company_doc.update_default_account = False
		company_doc.flags.ignore_validate = True
		company_doc.flags.ignore_permissions = True
		company_doc.flags.ignore_mandatory = True
		company_doc.flags.ignore_links = True
		company_doc.save()

		frappe.db.commit()

		return {
			'success': True,
			'message': 'Configurações salvas com sucesso',
			'compliance_preserved': True
		}

	except Exception as e:
		frappe.log_error(f"Erro ao salvar configurações: {str(e)}")
		return {'success': False, 'error': str(e)}


# test_at_connection_safe removida (2026-08-23): testava mTLS/
# credenciais construindo get_series_webservice_client(), que já lê
# Portugal Auth Settings diretamente - o "Testar Ligação" nativo desse
# doctype (portugal_auth_settings.js) cobre exatamente isto, sem
# depender de campos da Company.


@frappe.whitelist()
def get_company_compliance_status(company):
	"""
	✅ CORRIGIDO: Obter status de compliance da empresa
	"""
	try:
		# ✅ VALIDAÇÃO DE ENTRADA
		if not company:
			return {'success': False, 'error': 'Nome da empresa é obrigatório'}

		if not isinstance(company, str):
			return {'success': False, 'error': 'Nome da empresa deve ser uma string'}

		# ✅ VERIFICAR SE EMPRESA EXISTE
		if not frappe.db.exists('Company', company):
			return {'success': False, 'error': f'Empresa "{company}" não encontrada'}

		if not frappe.has_permission("Company", "read", company):
			frappe.throw(_("Sem permissão para consultar esta empresa"), frappe.PermissionError)

		# ✅ OBTER DOCUMENTO DA EMPRESA COM TRATAMENTO DE ERRO
		try:
			company_doc = frappe.get_doc('Company', company)
		except Exception as e:
			frappe.log_error(f"Erro ao obter empresa {company}: {str(e)}", "Company API Error")
			return {'success': False, 'error': 'Erro ao acessar dados da empresa'}

		# ✅ VERIFICAR STATUS COM VALORES PADRÃO
		is_portuguese = getattr(company_doc, 'country', '') == 'Portugal'

		# ✅ VERIFICAR SE CAMPO EXISTE ANTES DE ACESSAR
		compliance_enabled = False
		if hasattr(company_doc, 'portugal_compliance_enabled'):
			compliance_enabled = getattr(company_doc, 'portugal_compliance_enabled', False)

		# ✅ CONTAR SÉRIES COM TRATAMENTO DE ERRO ROBUSTO
		series_count = 0
		communicated_series = 0
		active_series = 0

		try:
			# Verificar se tabela existe
			if frappe.db.table_exists('Portugal Series Configuration'):
				series_count = frappe.db.count('Portugal Series Configuration',
											   {'company': company})
				communicated_series = frappe.db.count('Portugal Series Configuration', {
					'company': company,
					'is_communicated': 1
				})
				active_series = frappe.db.count('Portugal Series Configuration', {
					'company': company,
					'is_active': 1
				})
		except Exception as e:
			frappe.log_error(f"Erro ao contar séries para {company}: {str(e)}",
							 "Series Count Error")
		# Manter valores padrão (0)

		# ✅ OBTER INFORMAÇÕES BÁSICAS COM VALORES PADRÃO
		tax_id = getattr(company_doc, 'tax_id', '')
		default_currency = getattr(company_doc, 'default_currency', '')
		abbr = getattr(company_doc, 'abbr', '')
		company_name = getattr(company_doc, 'company_name', company)

		# ✅ VALIDAÇÃO SIMPLES SEM FUNÇÃO EXTERNA
		can_enable_compliance = (
			is_portuguese and
			bool(tax_id) and
			bool(abbr) and
			bool(company_name)
		)

		compliance_issues = []
		if not is_portuguese:
			compliance_issues.append('Empresa deve ser portuguesa')
		if not tax_id:
			compliance_issues.append('NIF é obrigatório')
		if not abbr:
			compliance_issues.append('Abreviatura é obrigatória')

		return {
			'success': True,
			'company': company,
			'company_name': company_name,
			'is_portuguese': is_portuguese,
			'compliance_enabled': compliance_enabled,
			'series_count': series_count,
			'communicated_series': communicated_series,
			'active_series': active_series,
			'can_enable_compliance': can_enable_compliance,
			'compliance_issues': compliance_issues,
			'tax_id': tax_id,
			'default_currency': default_currency,
			'abbr': abbr
		}

	except Exception as e:
		frappe.log_error(
			f"Erro geral ao obter status de compliance: {str(e)}\n{traceback.format_exc()}",
			"Compliance Status Error")
		return {
			'success': False,
			'error': f'Erro interno do servidor: {str(e)}',
			'company': company if 'company' in locals() else 'Desconhecida'
		}

@frappe.whitelist()
def create_company_series(company, document_types=None):
	"""
	✅ MELHORADO: Criar séries para empresa específica
	"""
	try:
		# ✅ VALIDAÇÃO DE ENTRADA
		if not company:
			return {'success': False, 'error': 'Nome da empresa é obrigatório'}

		if not isinstance(company, str):
			return {'success': False, 'error': 'Nome da empresa deve ser uma string'}

		# ✅ VERIFICAR SE EMPRESA EXISTE
		if not frappe.db.exists('Company', company):
			return {'success': False, 'error': f'Empresa "{company}" não encontrada'}

		# ✅ VERIFICAR PERMISSÕES
		if not frappe.has_permission('Portugal Series Configuration', 'create'):
			return {'success': False, 'error': 'Sem permissão para criar séries'}

		# ✅ VERIFICAR SE É EMPRESA PORTUGUESA
		try:
			if not is_portuguese_company(company):
				return {'success': False,
						'error': 'Apenas empresas portuguesas podem ter séries de compliance'}
		except Exception as e:
			frappe.log_error(f"Erro ao verificar empresa portuguesa {company}: {str(e)}",
							 "Portuguese Company Check Error")
			return {'success': False, 'error': 'Erro ao validar empresa portuguesa'}

		# ✅ OBTER DADOS DA EMPRESA
		try:
			company_doc = frappe.get_doc('Company', company)
			company_abbr = company_doc.abbr or company[:3].upper()
		except Exception as e:
			frappe.log_error(f"Erro ao obter dados da empresa {company}: {str(e)}",
							 "Company Data Error")
			return {'success': False, 'error': 'Erro ao acessar dados da empresa'}

		# ✅ CRIAR SÉRIES
		created_series = []
		errors = []

		if document_types:
			# ✅ CRIAR SÉRIES ESPECÍFICAS
			try:
				if isinstance(document_types, str):
					document_types = json.loads(document_types)

				if not isinstance(document_types, list):
					return {'success': False, 'error': 'document_types deve ser uma lista'}

			except json.JSONDecodeError as e:
				return {'success': False, 'error': f'JSON inválido para document_types: {str(e)}'}

			# ✅ VALIDAR TIPOS DE DOCUMENTO
			invalid_types = [dt for dt in document_types if dt not in PORTUGAL_DOCUMENT_TYPES]
			if invalid_types:
				return {
					'success': False,
					'error': f'Tipos de documento inválidos: {", ".join(invalid_types)}'
				}

			current_year = datetime.now().year

			for doctype in document_types:
				try:
					doc_info = PORTUGAL_DOCUMENT_TYPES[doctype]
					prefix = f"{doc_info['code']}{current_year}{company_abbr}"
					naming_series = f"{prefix}.####"

					# ✅ VERIFICAR SE JÁ EXISTE
					existing = frappe.db.exists("Portugal Series Configuration", {
						"prefix": prefix,
						"company": company
					})

					if existing:
						errors.append(f"Série {prefix} já existe para {doctype}")
						continue

					# ✅ CRIAR SÉRIE
					series_doc = frappe.new_doc("Portugal Series Configuration")
					series_doc.update({
						"series_name": f"{doc_info['name']} - {prefix}",
						"company": company,
						"document_type": doctype,
						"prefix": prefix,
						"naming_series": naming_series,
						"current_sequence": 1,
						"is_active": 1,
						"is_communicated": 0,
						"document_code": doc_info['code'],
						"year_code": str(current_year),
						"company_code": company_abbr
					})

					series_doc.insert(ignore_permissions=True)
					created_series.append({
						'name': series_doc.name,
						'prefix': prefix,
						'document_type': doctype,
						'naming_series': naming_series
					})

				except Exception as e:
					error_msg = f"Erro ao criar série para {doctype}: {str(e)}"
					errors.append(error_msg)
					frappe.log_error(f"{error_msg}\n{traceback.format_exc()}",
									 "Series Creation Error")

			# ✅ COMMIT SE HOUVER SÉRIES CRIADAS
			if created_series:
				frappe.db.commit()

			result = {
				'success': len(created_series) > 0,
				'created_count': len(created_series),
				'created_series': created_series,
				'errors': errors,
				'message': f'Criadas {len(created_series)} séries com sucesso'
			}

		else:
			# ✅ CRIAR TODAS AS SÉRIES
			try:
				result = setup_all_series_for_company(company)
				if not result:
					return {'success': False, 'error': 'Falha ao criar séries - resultado vazio'}

				if not result.get('success'):
					return {
						'success': False,
						'error': result.get('error', 'Erro desconhecido ao criar séries')
					}

			except Exception as e:
				frappe.log_error(
					f"Erro ao criar todas as séries para {company}: {str(e)}\n{traceback.format_exc()}",
					"All Series Creation Error")
				return {'success': False, 'error': f'Erro ao criar todas as séries: {str(e)}'}

		return result

	except Exception as e:
		frappe.log_error(f"Erro geral ao criar séries: {str(e)}\n{traceback.format_exc()}",
						 "Create Series General Error")
		return {'success': False, 'error': f'Erro interno: {str(e)}'}


@frappe.whitelist()
def generate_regional_tax_setup(company):
	"""
	✅ NOVA: Botão manual "Gerar Séries/Taxas Regionais" - gera os
	templates de IVA (Sales Taxes and Charges Template + Item Tax
	Template + contas SNC 2433x/2434x/2435x) das 3 regiões AT
	(Continente, Madeira, Açores) para uma empresa já ativa que só
	tenha os templates de Continente (criados antes desta correção -
	ver create_regional_tax_setup_for_company). Idempotente, seguro
	reexecutar em qualquer estado.
	"""
	try:
		if not company:
			return {'success': False, 'error': 'Nome da empresa é obrigatório'}

		if not frappe.db.exists('Company', company):
			return {'success': False, 'error': f'Empresa "{company}" não encontrada'}

		if not frappe.has_permission("Company", "write", company):
			frappe.throw(_("Sem permissão para configurar esta empresa"), frappe.PermissionError)

		from portugal_compliance.setup.tax_setup import create_regional_tax_setup_for_company
		created = create_regional_tax_setup_for_company(company)

		errors = {
			region: result["error"] for region, result in created.items()
			if isinstance(result, dict) and "error" in result
		}
		total_created = sum(len(result) for result in created.values() if isinstance(result, list))

		return {
			'success': not errors,
			'created': created,
			'total_created': total_created,
			'errors': errors,
			'message': f'{total_created} templates novos criados nas 3 regiões' if not errors
					   else f'Concluído com erros: {", ".join(errors)}',
		}
	except Exception as e:
		frappe.log_error(
			f"Erro ao gerar taxas regionais para {company}: {str(e)}\n{traceback.format_exc()}",
			"Regional Tax Setup Error")
		return {'success': False, 'error': f'Erro interno: {str(e)}'}


@frappe.whitelist()
def validate_company_for_compliance(company):
	"""
	✅ MELHORADO: Validar se empresa pode ativar compliance português
	"""
	try:
		# ✅ VALIDAÇÃO DE ENTRADA
		if not company:
			return {'valid': False, 'error': 'Nome da empresa é obrigatório'}

		if not isinstance(company, str):
			return {'valid': False, 'error': 'Nome da empresa deve ser uma string'}

		# ✅ VERIFICAR SE EMPRESA EXISTE
		if not frappe.db.exists('Company', company):
			return {'valid': False, 'error': f'Empresa "{company}" não encontrada'}

		if not frappe.has_permission("Company", "read", company):
			frappe.throw(_("Sem permissão para consultar esta empresa"), frappe.PermissionError)

		# ✅ OBTER DOCUMENTO DA EMPRESA
		try:
			company_doc = frappe.get_doc('Company', company)
		except Exception as e:
			frappe.log_error(f"Erro ao obter empresa {company}: {str(e)}",
							 "Company Validation Error")
			return {'valid': False, 'error': 'Erro ao acessar dados da empresa'}

		return validate_company_for_compliance_internal(company_doc)

	except Exception as e:
		frappe.log_error(
			f"Erro geral na validação de compliance: {str(e)}\n{traceback.format_exc()}",
			"Compliance Validation Error")
		return {'valid': False, 'error': f'Erro interno: {str(e)}'}


def validate_company_for_compliance_internal(company_doc):
	"""
	✅ NOVA: Validação interna de compliance (reutilizável)
	"""
	issues = []
	warnings = []

	try:
		# ✅ VERIFICAR PAÍS
		if not company_doc.country:
			issues.append('País da empresa não está definido')
		elif company_doc.country != 'Portugal':
			issues.append('Empresa deve ser portuguesa')

		# ✅ VERIFICAR NIF
		if not company_doc.tax_id:
			issues.append('NIF da empresa é obrigatório')
		else:
			# Validação básica de formato NIF
			nif_clean = company_doc.tax_id.replace(' ', '').replace('-', '')
			if not nif_clean.isdigit() or len(nif_clean) != 9:
				issues.append('NIF deve ter 9 dígitos numéricos')

		# ✅ VERIFICAR ABREVIATURA
		if not company_doc.abbr:
			issues.append('Abreviatura da empresa é obrigatória')
		elif len(company_doc.abbr) < 1 or len(company_doc.abbr) > 4:
			issues.append('Abreviatura deve ter entre 1 e 4 caracteres')

		# ✅ VERIFICAR MOEDA (WARNING)
		if company_doc.default_currency and company_doc.default_currency != 'EUR':
			warnings.append('Recomenda-se usar EUR como moeda padrão')

		# ✅ VERIFICAR NOME DA EMPRESA
		if not company_doc.company_name or len(company_doc.company_name.strip()) == 0:
			issues.append('Nome da empresa é obrigatório')

		return {
			'valid': len(issues) == 0,
			'issues': issues,
			'warnings': warnings,
			'company': company_doc.name
		}

	except Exception as e:
		frappe.log_error(f"Erro na validação interna: {str(e)}", "Internal Validation Error")
		return {
			'valid': False,
			'issues': [f'Erro na validação: {str(e)}'],
			'warnings': [],
			'company': company_doc.name if company_doc else 'Desconhecida'
		}


@frappe.whitelist()
def get_available_document_types():
	"""
	✅ NOVA: Obter tipos de documento disponíveis para séries
	"""
	try:
		document_types = []

		for doctype, info in PORTUGAL_DOCUMENT_TYPES.items():
			document_types.append({
				'doctype': doctype,
				'code': info['code'],
				'name': info['name'],
				'description': info['description'],
				'communication_required': info.get('communication_required', True),
				'atcud_required': info.get('atcud_required', True)
			})

		return {
			'success': True,
			'document_types': document_types,
			'total_count': len(document_types)
		}

	except Exception as e:
		frappe.log_error(f"Erro ao obter tipos de documento: {str(e)}", "Document Types Error")
		return {'success': False, 'error': str(e)}


@frappe.whitelist()
def delete_company_series(company, series_names=None):
	"""
	✅ NOVA: Deletar séries da empresa
	"""
	try:
		# ✅ VALIDAÇÃO DE ENTRADA
		if not company:
			return {'success': False, 'error': 'Nome da empresa é obrigatório'}

		# ✅ VERIFICAR PERMISSÕES
		if not frappe.has_permission('Portugal Series Configuration', 'delete'):
			return {'success': False, 'error': 'Sem permissão para deletar séries'}

		# ✅ CONSTRUIR FILTROS
		filters = {'company': company}

		if series_names:
			if isinstance(series_names, str):
				series_names = json.loads(series_names)
			filters['name'] = ['in', series_names]

		# ✅ BUSCAR SÉRIES
		series_to_delete = frappe.get_all('Portugal Series Configuration',
										  filters=filters,
										  fields=['name', 'prefix', 'is_communicated'])

		if not series_to_delete:
			return {'success': False, 'error': 'Nenhuma série encontrada para deletar'}

		# ✅ VERIFICAR SÉRIES COMUNICADAS
		communicated_series = [s for s in series_to_delete if s.is_communicated]
		if communicated_series:
			return {
				'success': False,
				'error': f'Não é possível deletar séries comunicadas: {", ".join([s.prefix for s in communicated_series])}'
			}

		# ✅ DELETAR SÉRIES
		deleted_count = 0
		errors = []

		for series in series_to_delete:
			try:
				frappe.delete_doc('Portugal Series Configuration', series.name, force=True)
				deleted_count += 1
			except Exception as e:
				errors.append(f"Erro ao deletar {series.prefix}: {str(e)}")

		# ✅ COMMIT SE HOUVER DELEÇÕES
		if deleted_count > 0:
			frappe.db.commit()

		return {
			'success': deleted_count > 0,
			'deleted_count': deleted_count,
			'errors': errors,
			'message': f'Deletadas {deleted_count} séries com sucesso'
		}

	except Exception as e:
		frappe.log_error(f"Erro ao deletar séries: {str(e)}\n{traceback.format_exc()}",
						 "Delete Series Error")
		return {'success': False, 'error': f'Erro interno: {str(e)}'}


# ========== CONSOLE LOG PARA DEBUG ==========
frappe.logger().info("Company API loaded - Version 2.0.0 - Robust Error Handling")
