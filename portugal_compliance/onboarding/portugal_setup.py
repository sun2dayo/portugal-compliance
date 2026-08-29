# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Funções de orquestração chamadas pelos passos "Server Action" do
Onboarding (onboarding/portugal_setup.json) - sem argumentos, porque o
mecanismo de validação de step do Frappe invoca o server_action sem
parâmetros, e o Onboarding não sabe qual empresa alvejar.
"""

import frappe


@frappe.whitelist()
def setup_default_series():
	"""
	Passo 3 do Onboarding ("Configurar Naming Series Nativas"). Cria as
	séries portuguesas reais via create_company_series (a mesma via
	oficial usada na ativação automática do compliance e no botão manual
	"Gerar Séries Base") para todas as empresas portuguesas com
	compliance já ativo.

	Nunca usa utils.naming_series_customizer.setup_all_portuguese_naming_series
	(neutralizado em 2026-08-29) - essa via escrevia diretamente em
	DocType.autoname/Property Setter e nunca criava um registo real em
	Portugal Series Configuration, deixando séries "fantasma":
	selecionáveis no formulário mas nunca comunicadas nem rastreadas
	pelo módulo de compliance (auditoria 2026-08-29, depois de confirmar
	que essa via contornava por completo a comunicação à AT).
	"""
	from portugal_compliance.api.company_api import create_company_series

	companies = frappe.get_all(
		"Company",
		filters={"country": "Portugal", "portugal_compliance_enabled": 1},
		fields=["name"],
	)

	if not companies:
		return {
			"success": False,
			"error": "Nenhuma empresa portuguesa com compliance ativo encontrada",
			"created": 0,
		}

	total_created = 0
	errors = []
	for company in companies:
		result = create_company_series(company.name) or {}
		if result.get("success"):
			total_created += result.get("created") or result.get("created_count") or 0
		else:
			errors.append({"company": company.name, "error": result.get("error")})

	return {
		"success": not errors,
		"created": total_created,
		"companies_processed": len(companies),
		"errors": errors,
	}


@frappe.whitelist()
def communicate_default_series():
	"""
	Passo 5 do Onboarding ("Comunicar Séries à AT"). Reutiliza
	company_api.communicate_series_safe - a mesma lógica real por trás
	do botão manual "Comunicar Séries" (company.js) - para todas as
	empresas portuguesas com compliance já ativo. Comunica em bloco
	TODAS as séries pendentes com communication_required=True (FT, a NC
	- que partilha o document_type "Sales Invoice" com a FT, logo cai
	no mesmo filtro -, FS, RC, GT: ver
	regional/portugal.py::PORTUGAL_DOCUMENT_TYPES), nunca só a série
	principal - não obriga o utilizador a ir à lista acionar a Nota de
	Crédito à mão.

	Nunca fabrica um is_communicated=1 sem uma resposta real da AT: não
	existe "mock" que marque uma série como comunicada sem o round-trip
	genuíno ao webservice - isso reproduziria exatamente o mesmo risco
	de "série fantasma" corrigido em 2026-08-29 no escudo de
	naming_series (uma série marcada como comunicada sem nunca ter sido,
	na prática, autorizando ATCUDs reais sobre uma série que a AT nunca
	viu). "Sandbox" aqui significa o ambiente de TESTE real da AT
	(Portugal Auth Settings.sandbox_mode/at_environment), que a
	ATWebserviceClient já usa nativamente e devolve códigos de validação
	genuínos emitidos pela própria AT no seu ambiente de teste - nunca
	um valor inventado localmente.

	Se as credenciais AT ainda não estiverem configuradas em Portugal
	Auth Settings (o Passo 2 do Onboarding é opcional), devolve
	success=False com uma mensagem clara, sem levantar exceção - o
	Onboarding fica com este passo por validar, sem bloquear o resto do
	assistente. O utilizador pode comunicar mais tarde, manualmente
	("Comunicar Séries", menu Comunicação AT da Empresa) ou reexecutando
	este step.
	"""
	from portugal_compliance.api.company_api import communicate_series_safe

	companies = frappe.get_all(
		"Company",
		filters={"country": "Portugal", "portugal_compliance_enabled": 1},
		fields=["name"],
	)

	if not companies:
		return {
			"success": False,
			"error": "Nenhuma empresa portuguesa com compliance ativo encontrada",
			"communicated_series": 0,
		}

	total_communicated = 0
	errors = []
	for company in companies:
		company_doc = frappe.get_doc("Company", company.name)
		result = communicate_series_safe(company_doc, {}) or {}
		if result.get("success"):
			total_communicated += result.get("communicated_count") or 0
		else:
			errors.append({"company": company.name, "error": result.get("error")})

	return {
		"success": not errors,
		"communicated_series": total_communicated,
		"companies_processed": len(companies),
		"errors": errors,
	}
