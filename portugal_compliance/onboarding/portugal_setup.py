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
