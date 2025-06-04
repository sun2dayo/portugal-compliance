# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import re


def execute(company_name=None):
	"""Configurar compliance português para empresa específica ou todas as empresas portuguesas"""
	try:
		print(f"🇵🇹 Configurando compliance português para empresas...")

		if company_name:
			# Configurar empresa específica
			setup_single_company(company_name)
		else:
			# Configurar todas as empresas portuguesas
			setup_all_portuguese_companies()

		print("✅ Configuração de empresas concluída!")

	except Exception as e:
		frappe.log_error(f"Erro na configuração de empresas: {str(e)}")
		print(f"❌ Erro na configuração: {str(e)}")
		raise


def setup_all_portuguese_companies():
	"""Configurar compliance para todas as empresas portuguesas"""
	try:
		# Buscar empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id"])

		if not portuguese_companies:
			print("⚠️ Nenhuma empresa portuguesa encontrada")
			return

		print(f"📋 Encontradas {len(portuguese_companies)} empresas portuguesas")

		for company in portuguese_companies:
			try:
				setup_single_company(company.name)
			except Exception as e:
				print(f"❌ Erro ao configurar empresa {company.name}: {str(e)}")
				continue

	except Exception as e:
		print(f"❌ Erro ao buscar empresas portuguesas: {str(e)}")
		raise


def setup_single_company(company_name):
	"""Configurar compliance português para uma empresa específica"""
	try:
		print(f"📋 Configurando empresa: {company_name}")

		# Obter documento da empresa
		company_doc = frappe.get_doc("Company", company_name)

		# 1. Verificar se é empresa portuguesa
		if company_doc.country != "Portugal":
			print(f"⚠️ Empresa {company_name} não é portuguesa (país: {company_doc.country})")
			return

		# 2. Ativar compliance português
		enable_portugal_compliance(company_doc)

		# 3. Validar e configurar NIF
		setup_company_nif(company_doc)

		# 4. Configurar contas contabilísticas portuguesas
		setup_portuguese_accounts(company_doc)

		# 5. Configurar séries documentais padrão
		setup_default_series(company_doc)

		# 6. Configurar impostos portugueses
		setup_portuguese_taxes(company_doc)

		# 7. Configurar configurações regionais
		setup_regional_settings(company_doc)

		# 8. Criar dados de exemplo
		create_sample_data(company_doc)

		print(f"✅ Empresa {company_name} configurada com sucesso")

	except Exception as e:
		print(f"❌ Erro ao configurar empresa {company_name}: {str(e)}")
		raise


def enable_portugal_compliance(company_doc):
	"""Ativar compliance português na empresa"""
	try:
		# Verificar se campo existe
		if not frappe.db.has_column("Company", "portugal_compliance_enabled"):
			print(
				"⚠️ Campo portugal_compliance_enabled não existe - será criado pelos Custom Fields")
			return

		# Ativar compliance se não estiver ativo
		if not company_doc.get("portugal_compliance_enabled"):
			company_doc.db_set("portugal_compliance_enabled", 1, update_modified=False)
			print(f"✅ Compliance português ativado para {company_doc.name}")
		else:
			print(f"✅ Compliance já estava ativo para {company_doc.name}")

	except Exception as e:
		print(f"❌ Erro ao ativar compliance: {str(e)}")


def setup_company_nif(company_doc):
	"""Configurar e validar NIF da empresa"""
	try:
		# Verificar se tem tax_id (NIF)
		if not company_doc.tax_id:
			print(f"⚠️ Empresa {company_doc.name} não tem NIF configurado")
			return

		# Validar formato do NIF português
		nif = company_doc.tax_id.strip()
		if validate_portuguese_nif(nif):
			print(f"✅ NIF válido: {nif}")

			# Configurar campo AT certificate se existir
			if frappe.db.has_column("Company", "at_certificate_number"):
				if not company_doc.get("at_certificate_number"):
					# Sugerir número de certificado baseado no NIF
					suggested_cert = f"AT{nif[:4]}"
					company_doc.db_set("at_certificate_number", suggested_cert,
									   update_modified=False)
					print(f"✅ Certificado AT sugerido: {suggested_cert}")
		else:
			print(f"⚠️ NIF inválido: {nif}")

	except Exception as e:
		print(f"❌ Erro ao configurar NIF: {str(e)}")


def validate_portuguese_nif(nif):
	"""Validar NIF português"""
	try:
		# Remover espaços e caracteres especiais
		nif = re.sub(r'[^0-9]', '', nif)

		# Verificar se tem 9 dígitos
		if len(nif) != 9:
			return False

		# Verificar se começa com dígito válido
		if nif[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			return False

		# Calcular dígito de controlo
		checksum = 0
		for i in range(8):
			checksum += int(nif[i]) * (9 - i)

		remainder = checksum % 11

		if remainder < 2:
			control_digit = 0
		else:
			control_digit = 11 - remainder

		return int(nif[8]) == control_digit

	except:
		return False


def setup_portuguese_accounts(company_doc):
	"""Configurar contas contabilísticas portuguesas"""
	try:
		print(f"📋 Configurando contas para {company_doc.name}")

		# Contas específicas portuguesas que podem ser criadas
		portuguese_accounts = {
			"IVA a Pagar": {
				"account_type": "Tax",
				"parent_account": f"Current Liabilities - {company_doc.abbr}",
				"account_number": "2432"
			},
			"IVA Dedutível": {
				"account_type": "Tax",
				"parent_account": f"Current Assets - {company_doc.abbr}",
				"account_number": "2433"
			},
			"Retenções na Fonte": {
				"account_type": "Tax",
				"parent_account": f"Current Liabilities - {company_doc.abbr}",
				"account_number": "2434"
			}
		}

		for account_name, config in portuguese_accounts.items():
			try:
				full_account_name = f"{account_name} - {company_doc.abbr}"

				if not frappe.db.exists("Account", full_account_name):
					# Verificar se conta pai existe
					if frappe.db.exists("Account", config["parent_account"]):
						account_doc = frappe.get_doc({
							"doctype": "Account",
							"account_name": account_name,
							"parent_account": config["parent_account"],
							"company": company_doc.name,
							"account_type": config["account_type"],
							"account_number": config.get("account_number"),
							"is_group": 0
						})
						account_doc.insert(ignore_permissions=True)
						print(f"✅ Conta criada: {full_account_name}")
					else:
						print(f"⚠️ Conta pai não existe: {config['parent_account']}")
				else:
					print(f"✅ Conta já existe: {full_account_name}")

			except Exception as e:
				print(f"❌ Erro ao criar conta {account_name}: {str(e)}")
				continue

	except Exception as e:
		print(f"❌ Erro ao configurar contas: {str(e)}")


def setup_default_series(company_doc):
	"""Configurar séries documentais padrão para a empresa"""
	try:
		print(f"📋 Configurando séries padrão para {company_doc.name}")

		# Séries padrão portuguesas
		default_series = [
			{
				"series_name": f"FT-2025-{company_doc.abbr}",
				"prefix": f"FT-2025-{company_doc.abbr}",
				"document_type": "Sales Invoice",
				"description": "Faturas de venda"
			},
			{
				"series_name": f"NC-2025-{company_doc.abbr}",
				"prefix": f"NC-2025-{company_doc.abbr}",
				"document_type": "Sales Invoice",
				"description": "Notas de crédito"
			},
			{
				"series_name": f"RC-2025-{company_doc.abbr}",
				"prefix": f"RC-2025-{company_doc.abbr}",
				"document_type": "Payment Entry",
				"description": "Recibos"
			},
			{
				"series_name": f"GT-2025-{company_doc.abbr}",
				"prefix": f"GT-2025-{company_doc.abbr}",
				"document_type": "Delivery Note",
				"description": "Guias de transporte"
			}
		]

		for series_config in default_series:
			try:
				if not frappe.db.exists("Portugal Series Configuration",
										series_config["series_name"]):
					series_doc = frappe.get_doc({
						"doctype": "Portugal Series Configuration",
						"series_name": series_config["series_name"],
						"prefix": series_config["prefix"],
						"document_type": series_config["document_type"],
						"company": company_doc.name,
						"current_sequence": 1,
						"is_active": 1,
						"enable_at_communication": 0,  # Desativado por padrão
						"creation_notes": f"Série criada automaticamente para {company_doc.name}"
					})
					series_doc.insert(ignore_permissions=True)
					print(f"✅ Série criada: {series_config['series_name']}")
				else:
					print(f"✅ Série já existe: {series_config['series_name']}")

			except Exception as e:
				print(f"❌ Erro ao criar série {series_config['series_name']}: {str(e)}")
				continue

	except Exception as e:
		print(f"❌ Erro ao configurar séries: {str(e)}")


def setup_portuguese_taxes(company_doc):
	"""Configurar impostos portugueses"""
	try:
		print(f"📋 Configurando impostos para {company_doc.name}")

		# Impostos portugueses padrão
		portuguese_taxes = [
			{
				"title": "IVA 23%",
				"rate": 23,
				"type": "On Net Total",
				"account_head": f"IVA a Pagar - {company_doc.abbr}"
			},
			{
				"title": "IVA 13%",
				"rate": 13,
				"type": "On Net Total",
				"account_head": f"IVA a Pagar - {company_doc.abbr}"
			},
			{
				"title": "IVA 6%",
				"rate": 6,
				"type": "On Net Total",
				"account_head": f"IVA a Pagar - {company_doc.abbr}"
			},
			{
				"title": "IVA 0%",
				"rate": 0,
				"type": "On Net Total",
				"account_head": f"IVA a Pagar - {company_doc.abbr}"
			}
		]

		for tax_config in portuguese_taxes:
			try:
				tax_name = f"{tax_config['title']} - {company_doc.abbr}"

				if not frappe.db.exists("Account", tax_config["account_head"]):
					print(f"⚠️ Conta de imposto não existe: {tax_config['account_head']}")
					continue

				if not frappe.db.exists("Sales Taxes and Charges Template", tax_name):
					# Criar template de impostos
					tax_template = frappe.get_doc({
						"doctype": "Sales Taxes and Charges Template",
						"title": tax_config["title"],
						"company": company_doc.name,
						"taxes": [{
							"charge_type": tax_config["type"],
							"account_head": tax_config["account_head"],
							"rate": tax_config["rate"],
							"description": f"{tax_config['title']} - Portugal"
						}]
					})
					tax_template.insert(ignore_permissions=True)
					print(f"✅ Imposto criado: {tax_name}")
				else:
					print(f"✅ Imposto já existe: {tax_name}")

			except Exception as e:
				print(f"❌ Erro ao criar imposto {tax_config['title']}: {str(e)}")
				continue

	except Exception as e:
		print(f"❌ Erro ao configurar impostos: {str(e)}")


def setup_regional_settings(company_doc):
	"""Configurar configurações regionais portuguesas"""
	try:
		print(f"📋 Configurando configurações regionais para {company_doc.name}")

		# Configurações regionais portuguesas
		regional_config = {
			"default_currency": "EUR",
			"country": "Portugal",
			"time_zone": "Europe/Lisbon",
			"date_format": "dd/mm/yyyy",
			"time_format": "HH:mm:ss",
			"number_format": "#.###,##",
			"first_day_of_the_week": "Monday"
		}

		# Aplicar configurações se campos existirem
		for field, value in regional_config.items():
			try:
				if hasattr(company_doc, field):
					if not getattr(company_doc, field):
						company_doc.db_set(field, value, update_modified=False)
						print(f"✅ {field}: {value}")
					else:
						print(f"✅ {field} já configurado: {getattr(company_doc, field)}")
			except Exception as e:
				print(f"⚠️ Erro ao configurar {field}: {str(e)}")

	except Exception as e:
		print(f"❌ Erro ao configurar configurações regionais: {str(e)}")


def create_sample_data(company_doc):
	"""Criar dados de exemplo para a empresa"""
	try:
		print(f"📋 Criando dados de exemplo para {company_doc.name}")

		# Criar cliente de exemplo português
		sample_customer_name = "Cliente Exemplo PT"
		if not frappe.db.exists("Customer", sample_customer_name):
			try:
				customer_doc = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": sample_customer_name,
					"customer_type": "Company",
					"customer_group": "Commercial",
					"territory": "Portugal",
					"tax_id": "123456789",  # NIF de exemplo
					"default_company": company_doc.name
				})
				customer_doc.insert(ignore_permissions=True)
				print(f"✅ Cliente de exemplo criado: {sample_customer_name}")
			except Exception as e:
				print(f"❌ Erro ao criar cliente de exemplo: {str(e)}")
		else:
			print(f"✅ Cliente de exemplo já existe: {sample_customer_name}")

		# Criar fornecedor de exemplo português
		sample_supplier_name = "Fornecedor Exemplo PT"
		if not frappe.db.exists("Supplier", sample_supplier_name):
			try:
				supplier_doc = frappe.get_doc({
					"doctype": "Supplier",
					"supplier_name": sample_supplier_name,
					"supplier_type": "Company",
					"supplier_group": "Local",
					"country": "Portugal",
					"tax_id": "987654321",  # NIF de exemplo
					"default_company": company_doc.name
				})
				supplier_doc.insert(ignore_permissions=True)
				print(f"✅ Fornecedor de exemplo criado: {sample_supplier_name}")
			except Exception as e:
				print(f"❌ Erro ao criar fornecedor de exemplo: {str(e)}")
		else:
			print(f"✅ Fornecedor de exemplo já existe: {sample_supplier_name}")

	except Exception as e:
		print(f"❌ Erro ao criar dados de exemplo: {str(e)}")


def validate_company_setup(company_name):
	"""Validar se empresa foi configurada corretamente"""
	try:
		print(f"📋 Validando configuração da empresa {company_name}")

		company_doc = frappe.get_doc("Company", company_name)

		# Verificações essenciais
		checks = {
			"País é Portugal": company_doc.country == "Portugal",
			"Tem NIF": bool(company_doc.tax_id),
			"NIF válido": validate_portuguese_nif(
				company_doc.tax_id) if company_doc.tax_id else False,
			"Compliance ativado": company_doc.get("portugal_compliance_enabled", False),
			"Moeda é EUR": company_doc.default_currency == "EUR"
		}

		# Verificar séries criadas
		series_count = frappe.db.count("Portugal Series Configuration", {"company": company_name})
		checks["Tem séries configuradas"] = series_count > 0

		# Mostrar resultados
		print(f"📋 Validação para {company_name}:")
		for check, result in checks.items():
			status = "✅" if result else "❌"
			print(f"   {status} {check}")

		# Calcular score
		score = sum(checks.values()) / len(checks) * 100
		print(f"📊 Score de configuração: {score:.1f}%")

		return score >= 80  # 80% ou mais considera-se bem configurado

	except Exception as e:
		print(f"❌ Erro na validação: {str(e)}")
		return False


def get_company_setup_summary():
	"""Obter resumo de configuração de todas as empresas portuguesas"""
	try:
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id"])

		summary = {
			"total_companies": len(portuguese_companies),
			"configured_companies": 0,
			"companies_with_series": 0,
			"companies_with_compliance": 0
		}

		for company in portuguese_companies:
			# Verificar se tem compliance ativado
			if frappe.db.has_column("Company", "portugal_compliance_enabled"):
				compliance_enabled = frappe.db.get_value("Company", company.name,
														 "portugal_compliance_enabled")
				if compliance_enabled:
					summary["companies_with_compliance"] += 1

			# Verificar se tem séries
			series_count = frappe.db.count("Portugal Series Configuration",
										   {"company": company.name})
			if series_count > 0:
				summary["companies_with_series"] += 1

			# Verificar configuração geral
			if validate_company_setup(company.name):
				summary["configured_companies"] += 1

		return summary

	except Exception as e:
		print(f"❌ Erro ao obter resumo: {str(e)}")
		return {}


# Função principal chamada pelo hooks.py
def setup_company_portugal_compliance(doc, method):
	"""Hook chamado quando empresa é inserida/atualizada"""
	try:
		if doc.country == "Portugal":
			print(f"🇵🇹 Configurando compliance português para nova empresa: {doc.name}")
			setup_single_company(doc.name)
	except Exception as e:
		frappe.log_error(f"Erro no hook de empresa: {str(e)}")


# Função para chamada manual
def setup_all_companies():
	"""Função para configurar todas as empresas (chamada manual)"""
	execute()
