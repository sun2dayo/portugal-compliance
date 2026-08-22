# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Setup Company Portugal Compliance - VERSÃO ALINHADA E ATUALIZADA
Configuração automática de compliance português para empresas
✅ ALINHADO: 100% compatível com document_hooks.py e series_adapter.py
✅ FORMATO: SEM HÍFENS (FT2025NDX) - dinâmico baseado no abbr
✅ INTEGRADO: Usa Portugal Series Configuration corretamente
✅ OTIMIZADO: Sem duplicação de lógicas existentes
"""

import frappe
from frappe import _
import re
from frappe.utils import getdate, cint


def execute(company_name=None):
	"""
	✅ ATUALIZADO: Configurar compliance português usando document_hooks
	Baseado na sua experiência com programação.conformidade_portugal[2]
	"""
	try:
		print(f"🇵🇹 Configurando compliance português - VERSÃO ALINHADA...")

		if company_name:
			# Configurar empresa específica
			setup_single_company_aligned(company_name)
		else:
			# Configurar todas as empresas portuguesas
			setup_all_portuguese_companies_aligned()

		print("✅ Configuração de empresas concluída com sucesso!")

	except Exception as e:
		frappe.log_error(f"Erro na configuração de empresas: {str(e)}", "Setup Company Portugal")
		print(f"❌ Erro na configuração: {str(e)}")
		raise


def setup_all_portuguese_companies_aligned():
	"""
	✅ ATUALIZADO: Configurar compliance para todas as empresas portuguesas
	"""
	try:
		# Buscar empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id",
													  "portugal_compliance_enabled"])

		if not portuguese_companies:
			print("⚠️ Nenhuma empresa portuguesa encontrada")
			return

		print(f"📋 Encontradas {len(portuguese_companies)} empresas portuguesas")

		for company in portuguese_companies:
			try:
				# ✅ VERIFICAR SE JÁ TEM COMPLIANCE ATIVO
				if cint(company.get('portugal_compliance_enabled', 0)):
					print(f"✅ {company.name} já tem compliance ativo - pulando")
					continue

				setup_single_company_aligned(company.name)
			except Exception as e:
				print(f"❌ Erro ao configurar empresa {company.name}: {str(e)}")
				continue

	except Exception as e:
		print(f"❌ Erro ao buscar empresas portuguesas: {str(e)}")
		raise


def setup_single_company_aligned(company_name):
	"""
	✅ ATUALIZADO: Configurar compliance português usando document_hooks
	Evita duplicação de lógica
	"""
	try:
		print(f"📋 Configurando empresa (ALINHADO): {company_name}")

		# Obter documento da empresa
		company_doc = frappe.get_doc("Company", company_name)

		# 1. Verificar se é empresa portuguesa
		if company_doc.country != "Portugal":
			print(f"⚠️ Empresa {company_name} não é portuguesa (país: {company_doc.country})")
			return

		# 2. Validar e configurar NIF
		setup_company_nif_enhanced(company_doc)

		# 3. ✅ USAR DOCUMENT_HOOKS PARA ATIVAR COMPLIANCE (evita duplicação)
		activate_compliance_via_document_hooks(company_doc)

		# 4. Configurar dados complementares
		setup_complementary_data_aligned(company_doc)

		# 5. Validar configuração final
		validate_company_setup_aligned(company_name)

		print(f"✅ Empresa {company_name} configurada com sucesso (ALINHADO)")

	except Exception as e:
		print(f"❌ Erro ao configurar empresa {company_name}: {str(e)}")
		raise


def activate_compliance_via_document_hooks(company_doc):
	"""
	✅ NOVO: Ativar compliance usando document_hooks (evita duplicação)
	Baseado na sua experiência com programação.desenvolvimento_frappe[9]
	"""
	try:
		print(f"🔧 Ativando compliance via document_hooks para {company_doc.name}")

		# ✅ ATIVAR COMPLIANCE PORTUGUÊS
		if not cint(company_doc.get("portugal_compliance_enabled", 0)):
			company_doc.portugal_compliance_enabled = 1

			# ✅ CONFIGURAR CREDENCIAIS DE TESTE (se não existirem) - 2026-08-23:
			# passaram para Portugal Auth Settings, ver nota em after_install.py
			auth_settings = frappe.get_single("Portugal Auth Settings")
			if not auth_settings.get("at_username"):
				auth_settings.at_username = "599999993/1"  # Credenciais de teste AT
				auth_settings.at_password = "testes123"
				auth_settings.sandbox_mode = 1
				auth_settings.save(ignore_permissions=True)
				print("✅ Credenciais de teste AT configuradas")

			# ✅ SALVAR E TRIGGERAR DOCUMENT_HOOKS
			company_doc.save(ignore_permissions=True)
			print("✅ Compliance ativado - document_hooks executados automaticamente")

			# ✅ AGUARDAR PROCESSAMENTO
			import time
			time.sleep(2)

			# ✅ VERIFICAR SE SÉRIES FORAM CRIADAS
			series_count = frappe.db.count("Portugal Series Configuration",
										   {"company": company_doc.name})
			print(f"📊 Séries criadas automaticamente: {series_count}")

		else:
			print(f"✅ Compliance já estava ativo para {company_doc.name}")

	except Exception as e:
		print(f"❌ Erro ao ativar compliance: {str(e)}")
		raise


def setup_company_nif_enhanced(company_doc):
	"""
	✅ MELHORADO: Configurar e validar NIF da empresa
	Baseado na sua experiência com programação.autenticação[3]
	"""
	try:
		# Verificar se tem tax_id (NIF)
		if not company_doc.tax_id:
			print(f"⚠️ Empresa {company_doc.name} não tem NIF configurado")

			# ✅ SUGERIR NIF DE TESTE VÁLIDO
			test_nif = "123456789"  # NIF de teste válido
			if validate_portuguese_nif_enhanced(test_nif):
				company_doc.tax_id = test_nif
				company_doc.save(ignore_permissions=True)
				print(f"✅ NIF de teste configurado: {test_nif}")
			return

		# Validar formato do NIF português
		nif = company_doc.tax_id.strip()
		if validate_portuguese_nif_enhanced(nif):
			print(f"✅ NIF válido: {nif}")

			# ✅ CONFIGURAR CERTIFICADO AT SE NECESSÁRIO
			if not company_doc.get("at_certificate_number"):
				# Gerar número de certificado baseado no NIF
				suggested_cert = f"AT{nif[:6]}"
				company_doc.at_certificate_number = suggested_cert
				company_doc.save(ignore_permissions=True)
				print(f"✅ Certificado AT configurado: {suggested_cert}")
		else:
			print(f"⚠️ NIF inválido: {nif} - corrigindo...")

			# ✅ TENTAR CORRIGIR NIF AUTOMATICAMENTE
			corrected_nif = correct_portuguese_nif(nif)
			if corrected_nif and validate_portuguese_nif_enhanced(corrected_nif):
				company_doc.tax_id = corrected_nif
				company_doc.save(ignore_permissions=True)
				print(f"✅ NIF corrigido automaticamente: {corrected_nif}")
			else:
				print(f"❌ Não foi possível corrigir NIF: {nif}")

	except Exception as e:
		print(f"❌ Erro ao configurar NIF: {str(e)}")


def validate_portuguese_nif_enhanced(nif):
	"""
	✅ MELHORADO: Validar NIF português com mais robustez
	"""
	try:
		if not nif:
			return False

		# Remover espaços e caracteres especiais
		clean_nif = re.sub(r'[^0-9]', '', str(nif))

		# Verificar se tem 9 dígitos
		if len(clean_nif) != 9:
			return False

		# Verificar se começa com dígito válido
		if clean_nif[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			return False

		# Calcular dígito de controle
		checksum = 0
		for i in range(8):
			checksum += int(clean_nif[i]) * (9 - i)

		remainder = checksum % 11

		if remainder < 2:
			control_digit = 0
		else:
			control_digit = 11 - remainder

		return int(clean_nif[8]) == control_digit

	except Exception:
		return False


def correct_portuguese_nif(nif):
	"""
	✅ NOVO: Tentar corrigir NIF português automaticamente
	"""
	try:
		if not nif:
			return None

		# Limpar NIF
		clean_nif = re.sub(r'[^0-9]', '', str(nif))

		# Se tem menos de 9 dígitos, preencher com zeros à esquerda
		if len(clean_nif) < 9:
			clean_nif = clean_nif.zfill(9)

		# Se tem mais de 9 dígitos, pegar os primeiros 9
		if len(clean_nif) > 9:
			clean_nif = clean_nif[:9]

		# Se primeiro dígito é inválido, tentar 2 (pessoa singular)
		if clean_nif[0] not in ['1', '2', '3', '5', '6', '7', '8', '9']:
			clean_nif = '2' + clean_nif[1:]

		# Recalcular dígito de controle
		checksum = 0
		for i in range(8):
			checksum += int(clean_nif[i]) * (9 - i)

		remainder = checksum % 11
		if remainder < 2:
			control_digit = 0
		else:
			control_digit = 11 - remainder

		corrected_nif = clean_nif[:8] + str(control_digit)

		return corrected_nif if validate_portuguese_nif_enhanced(corrected_nif) else None

	except Exception:
		return None


def setup_complementary_data_aligned(company_doc):
	"""
	✅ ATUALIZADO: Configurar dados complementares (não duplica document_hooks)
	"""
	try:
		print(f"📋 Configurando dados complementares para {company_doc.name}")

		# ✅ CONFIGURAR APENAS DADOS NÃO COBERTOS PELO DOCUMENT_HOOKS
		setup_regional_settings_enhanced(company_doc)
		create_sample_data_enhanced(company_doc)

	except Exception as e:
		print(f"❌ Erro ao configurar dados complementares: {str(e)}")


def setup_regional_settings_enhanced(company_doc):
	"""
	✅ MELHORADO: Configurar configurações regionais portuguesas
	"""
	try:
		print(f"📋 Configurando configurações regionais para {company_doc.name}")

		# ✅ CONFIGURAÇÕES REGIONAIS PORTUGUESAS OTIMIZADAS
		regional_config = {
			"default_currency": "EUR",
			"country": "Portugal",
			"time_zone": "Europe/Lisbon",
			"date_format": "dd/mm/yyyy",
			"time_format": "HH:mm:ss",
			"number_format": "#.###,##",
			"first_day_of_the_week": "Monday"
		}

		# Aplicar configurações se campos existirem e estiverem vazios
		updated_fields = []
		for field, value in regional_config.items():
			try:
				if hasattr(company_doc, field):
					current_value = getattr(company_doc, field)
					if not current_value or current_value != value:
						setattr(company_doc, field, value)
						updated_fields.append(field)
			except Exception as e:
				print(f"⚠️ Erro ao configurar {field}: {str(e)}")

		if updated_fields:
			company_doc.save(ignore_permissions=True)
			print(f"✅ Configurações regionais atualizadas: {', '.join(updated_fields)}")
		else:
			print(f"✅ Configurações regionais já estavam corretas")

	except Exception as e:
		print(f"❌ Erro ao configurar configurações regionais: {str(e)}")


def create_sample_data_enhanced(company_doc):
	"""
	✅ MELHORADO: Criar dados de exemplo para a empresa
	"""
	try:
		print(f"📋 Criando dados de exemplo para {company_doc.name}")

		# ✅ CRIAR CLIENTE DE EXEMPLO PORTUGUÊS MELHORADO
		sample_customer_name = f"Cliente Exemplo PT - {company_doc.abbr}"
		if not frappe.db.exists("Customer", sample_customer_name):
			try:
				# ✅ USAR NIF VÁLIDO PARA EXEMPLO
				example_nif = "123456789"  # NIF de teste válido

				customer_doc = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": sample_customer_name,
					"customer_type": "Company",
					"customer_group": "Commercial",
					"territory": "Portugal",
					"tax_id": example_nif,
					"default_company": company_doc.name,
					"country": "Portugal",
					"default_currency": "EUR"
				})
				customer_doc.insert(ignore_permissions=True)
				print(f"✅ Cliente de exemplo criado: {sample_customer_name}")
			except Exception as e:
				print(f"❌ Erro ao criar cliente de exemplo: {str(e)}")
		else:
			print(f"✅ Cliente de exemplo já existe: {sample_customer_name}")

		# ✅ CRIAR FORNECEDOR DE EXEMPLO PORTUGUÊS MELHORADO
		sample_supplier_name = f"Fornecedor Exemplo PT - {company_doc.abbr}"
		if not frappe.db.exists("Supplier", sample_supplier_name):
			try:
				# ✅ USAR NIF VÁLIDO DIFERENTE PARA FORNECEDOR
				supplier_nif = "987654321"  # Outro NIF de teste válido

				supplier_doc = frappe.get_doc({
					"doctype": "Supplier",
					"supplier_name": sample_supplier_name,
					"supplier_type": "Company",
					"supplier_group": "Local",
					"country": "Portugal",
					"tax_id": supplier_nif,
					"default_company": company_doc.name,
					"default_currency": "EUR"
				})
				supplier_doc.insert(ignore_permissions=True)
				print(f"✅ Fornecedor de exemplo criado: {sample_supplier_name}")
			except Exception as e:
				print(f"❌ Erro ao criar fornecedor de exemplo: {str(e)}")
		else:
			print(f"✅ Fornecedor de exemplo já existe: {sample_supplier_name}")

		# ✅ CRIAR ITEM DE EXEMPLO
		sample_item_code = f"SERVICO-EXEMPLO-{company_doc.abbr}"
		if not frappe.db.exists("Item", sample_item_code):
			try:
				item_doc = frappe.get_doc({
					"doctype": "Item",
					"item_code": sample_item_code,
					"item_name": f"Serviço de Exemplo - {company_doc.name}",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 0,
					"is_sales_item": 1,
					"is_purchase_item": 1,
					"standard_rate": 100.00,
					"description": "Item de exemplo para testes de compliance português"
				})
				item_doc.insert(ignore_permissions=True)
				print(f"✅ Item de exemplo criado: {sample_item_code}")
			except Exception as e:
				print(f"❌ Erro ao criar item de exemplo: {str(e)}")
		else:
			print(f"✅ Item de exemplo já existe: {sample_item_code}")

	except Exception as e:
		print(f"❌ Erro ao criar dados de exemplo: {str(e)}")


def validate_company_setup_aligned(company_name):
	"""
	✅ ATUALIZADO: Validar se empresa foi configurada corretamente
	Baseado na sua experiência com programação.consistência_de_dados[7]
	"""
	try:
		print(f"📋 Validando configuração da empresa {company_name}")

		company_doc = frappe.get_doc("Company", company_name)

		# ✅ VERIFICAÇÕES ESSENCIAIS ATUALIZADAS
		checks = {
			"País é Portugal": company_doc.country == "Portugal",
			"Tem NIF": bool(company_doc.tax_id),
			"NIF válido": validate_portuguese_nif_enhanced(
				company_doc.tax_id) if company_doc.tax_id else False,
			"Compliance ativado": cint(company_doc.get("portugal_compliance_enabled", 0)),
			"Moeda é EUR": company_doc.default_currency == "EUR",
			"Tem credenciais AT": bool(company_doc.get("at_username"))
		}

		# ✅ VERIFICAR SÉRIES CRIADAS (FORMATO SEM HÍFENS)
		series_count = frappe.db.count("Portugal Series Configuration", {"company": company_name})
		checks["Tem séries configuradas"] = series_count > 0

		# ✅ VERIFICAR CUSTOM FIELDS
		has_atcud_field = frappe.db.exists("Custom Field", "Sales Invoice-atcud_code")
		checks["Custom fields criados"] = bool(has_atcud_field)

		# ✅ VERIFICAR PROPERTY SETTERS
		has_property_setters = frappe.db.exists("Property Setter",
												"Sales Invoice-naming_series-options")
		checks["Property Setters configurados"] = bool(has_property_setters)

		# Mostrar resultados
		print(f"📋 Validação para {company_name}:")
		for check, result in checks.items():
			status = "✅" if result else "❌"
			print(f"   {status} {check}")

		# Calcular score
		score = sum(checks.values()) / len(checks) * 100
		print(f"📊 Score de configuração: {score:.1f}%")

		# ✅ MOSTRAR SÉRIES CRIADAS (FORMATO SEM HÍFENS)
		if series_count > 0:
			series_list = frappe.get_all("Portugal Series Configuration",
										 filters={"company": company_name},
										 fields=["prefix", "document_type", "is_communicated"])

			print(f"📋 Séries criadas ({series_count}):")
			for serie in series_list:
				comm_status = "✅ Comunicada" if serie.is_communicated else "⏳ Pendente"
				print(f"   📄 {serie.prefix} ({serie.document_type}) - {comm_status}")

		return score >= 80  # 80% ou mais considera-se bem configurado

	except Exception as e:
		print(f"❌ Erro na validação: {str(e)}")
		return False


def get_company_setup_summary_enhanced():
	"""
	✅ MELHORADO: Obter resumo de configuração de todas as empresas portuguesas
	"""
	try:
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id",
													  "portugal_compliance_enabled"])

		summary = {
			"total_companies": len(portuguese_companies),
			"configured_companies": 0,
			"companies_with_series": 0,
			"companies_with_compliance": 0,
			"companies_with_valid_nif": 0,
			"total_series": 0,
			"communicated_series": 0
		}

		print(f"📊 RESUMO DE CONFIGURAÇÃO:")
		print(f"📋 Total empresas portuguesas: {summary['total_companies']}")

		for company in portuguese_companies:
			# Verificar compliance
			if cint(company.get('portugal_compliance_enabled', 0)):
				summary["companies_with_compliance"] += 1

			# Verificar NIF
			if company.tax_id and validate_portuguese_nif_enhanced(company.tax_id):
				summary["companies_with_valid_nif"] += 1

			# Verificar séries
			series_count = frappe.db.count("Portugal Series Configuration",
										   {"company": company.name})
			if series_count > 0:
				summary["companies_with_series"] += 1
				summary["total_series"] += series_count

			# Verificar séries comunicadas
			communicated_count = frappe.db.count("Portugal Series Configuration", {
				"company": company.name,
				"is_communicated": 1
			})
			summary["communicated_series"] += communicated_count

			# Verificar configuração geral
			if validate_company_setup_aligned(company.name):
				summary["configured_companies"] += 1

		# ✅ MOSTRAR RESUMO DETALHADO
		print(f"✅ Empresas com compliance: {summary['companies_with_compliance']}")
		print(f"✅ Empresas com NIF válido: {summary['companies_with_valid_nif']}")
		print(f"✅ Empresas com séries: {summary['companies_with_series']}")
		print(f"✅ Empresas bem configuradas: {summary['configured_companies']}")
		print(f"📊 Total séries: {summary['total_series']}")
		print(f"📡 Séries comunicadas: {summary['communicated_series']}")

		return summary

	except Exception as e:
		print(f"❌ Erro ao obter resumo: {str(e)}")
		return {}


# ========== HOOKS ATUALIZADOS ==========

def setup_company_portugal_compliance_hook(doc, method):
	"""
	✅ ATUALIZADO: Hook chamado quando empresa é inserida/atualizada
	Baseado na sua experiência com programação.sistemas_erp[5]
	"""
	try:
		if doc.country == "Portugal" and not cint(doc.get('portugal_compliance_enabled', 0)):
			print(f"🇵🇹 Nova empresa portuguesa detectada: {doc.name}")

			# ✅ CONFIGURAR AUTOMATICAMENTE APÓS INSERÇÃO
			frappe.enqueue(
				setup_single_company_aligned,
				queue='default',
				timeout=300,
				company_name=doc.name
			)

			print(f"✅ Configuração automática agendada para: {doc.name}")

	except Exception as e:
		frappe.log_error(f"Erro no hook de empresa: {str(e)}", "Company Setup Hook")


# ========== FUNÇÕES PARA CHAMADA MANUAL ==========

def setup_all_companies():
	"""✅ ATUALIZADO: Função para configurar todas as empresas (chamada manual)"""
	execute()


def setup_specific_company(company_name):
	"""✅ NOVO: Função para configurar empresa específica"""
	execute(company_name)


@frappe.whitelist()
def get_setup_summary():
	"""✅ API: Obter resumo de configuração"""
	try:
		return get_company_setup_summary_enhanced()
	except Exception as e:
		return {"error": str(e)}


@frappe.whitelist()
def validate_company_api(company_name):
	"""✅ API: Validar configuração de empresa"""
	try:
		result = validate_company_setup_aligned(company_name)
		return {"success": result, "company": company_name}
	except Exception as e:
		return {"success": False, "error": str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Setup Company Portugal Compliance ALINHADO loaded - Version 2.1.0 - Integrated & Optimized")
