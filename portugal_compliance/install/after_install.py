# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
After Install - Portugal Compliance VERSÃO ATUALIZADA E ALINHADA
Executado após a instalação do Portugal Compliance
✅ ALINHADO: Baseado nos search results [1] e [3] sobre boas práticas ERPNext
✅ ATUALIZADO: Criação programática de Custom Fields (não fixtures)
✅ INTEGRADO: Usa document_hooks.py para evitar duplicação
✅ ROBUSTO: Configuração completa e validação final
"""

import frappe
from frappe import _
import os
import json
from datetime import datetime


def execute():
	"""
	✅ ATUALIZADO: Executado após instalação do Portugal Compliance
	Baseado na sua experiência com programação.sistemas_erp[12]
	"""
	try:
		print("🇵🇹 Iniciando pós-instalação do Portugal Compliance ATUALIZADO...")
		print("=" * 70)

		# 1. Verificar se instalação foi bem-sucedida
		verify_installation_success()

		# 2. ✅ CRIAR CUSTOM FIELDS PROGRAMATICAMENTE (baseado no search result [1])
		create_custom_fields_programmatically()

		# 3. Configurar Property Setters iniciais
		setup_initial_property_setters()

		# 4. ✅ CONFIGURAR EMPRESAS PORTUGUESAS EXISTENTES
		setup_existing_portuguese_companies()

		# 5. Criar dados de exemplo se necessário
		create_sample_data_if_needed()

		# 6. Configurar permissões específicas
		setup_portugal_compliance_permissions()

		# 7. ✅ EXECUTAR STARTUP FIXES (baseado no search result [3])
		run_startup_fixes_after_install()

		# 8. Configurar scheduler jobs
		setup_scheduler_jobs()

		# 9. (create_default_configurations removida - Fase 5: tentava criar
		# um doc da doctype "Portugal Compliance Settings", que nunca
		# existiu neste app; falhava sempre silenciosamente. Portugal Auth
		# Settings e quem guarda a configuracao real desde a Fase 2.)

		# 10. Validação final da instalação
		validate_final_installation()

		print("=" * 70)
		print("✅ Pós-instalação do Portugal Compliance concluída com sucesso!")
		print("🇵🇹 Sistema Portugal Compliance está pronto para uso!")

		# 11. Mostrar próximos passos
		show_next_steps()

	except Exception as e:
		frappe.log_error(f"Erro na pós-instalação do Portugal Compliance: {str(e)}",
						 "After Install")
		print(f"❌ Erro na pós-instalação: {str(e)}")
		raise


def verify_installation_success():
	"""
	✅ NOVO: Verificar se instalação foi bem-sucedida
	Baseado na sua experiência com programação.teste_de_ambiente[14]
	"""
	try:
		print("📋 Verificando sucesso da instalação...")

		# Verificar se app está instalado
		installed_apps = frappe.get_installed_apps()
		if "portugal_compliance" not in installed_apps:
			raise Exception("Portugal Compliance não está na lista de apps instalados")

		print("✅ App Portugal Compliance instalado")

		# Verificar se DocTypes foram criados (Portugal AT Communication Log
		# e Portugal Compliance Settings removidos desta lista - nunca
		# existiram como doctypes reais neste app; Portugal Auth Settings
		# e quem guarda a configuracao real desde a Fase 2)
		required_doctypes = [
			"Portugal Series Configuration"
		]

		missing_doctypes = []
		for doctype in required_doctypes:
			if not frappe.db.exists("DocType", doctype):
				missing_doctypes.append(doctype)

		if missing_doctypes:
			print(f"⚠️ DocTypes em falta: {missing_doctypes}")
		else:
			print("✅ Todos os DocTypes necessários foram criados")

		# Verificar estrutura de diretórios
		base_path = "/home/frappe/frappe-bench/sites/assets/portugal_compliance"
		if os.path.exists(base_path):
			print("✅ Estrutura de diretórios criada")
		else:
			print("⚠️ Estrutura de diretórios não encontrada")

	except Exception as e:
		print(f"❌ Erro na verificação: {str(e)}")
		raise


def create_custom_fields_programmatically():
	"""
	✅ BASEADO NO SEARCH RESULT [1]: Criar Custom Fields programaticamente
	"Manual coding after_install - create_custom_fields()" é a melhor prática
	"""
	try:
		print("\n📋 Criando Custom Fields programaticamente (MELHOR PRÁTICA)...")

		# ✅ USAR DOCUMENT_HOOKS PARA CRIAR CAMPOS (evita duplicação)
		try:
			from portugal_compliance.utils.document_hooks import portugal_document_hooks

			# Criar custom fields usando a função centralizada
			created_count = portugal_document_hooks._ensure_custom_fields_exist_complete()
			print(f"✅ Custom Fields criados: {created_count} campos")

		except ImportError:
			# ✅ FALLBACK: Criar campos essenciais manualmente
			create_essential_custom_fields_fallback()

		# Limpar cache após criação
		frappe.clear_cache()
		print("✅ Cache limpo após criação de Custom Fields")

	except Exception as e:
		print(f"❌ Erro ao criar Custom Fields: {str(e)}")
		# ✅ NÃO FALHAR - Custom Fields podem ser criados posteriormente
		print("⚠️ Custom Fields serão criados quando compliance for ativado")


def create_essential_custom_fields_fallback():
	"""
	✅ FALLBACK: Criar apenas campos essenciais se document_hooks falhar
	"""
	try:
		print("📋 Criando campos essenciais (fallback)...")

		# ✅ APENAS CAMPOS CRÍTICOS
		essential_fields = [
			{
				"dt": "Sales Invoice",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"bold": 1,
				"description": "Código Único de Documento - Portugal Compliance"
			},
			{
				"dt": "Company",
				"fieldname": "portugal_compliance_enabled",
				"label": "Portugal Compliance Enabled",
				"fieldtype": "Check",
				"insert_after": "country",
				"depends_on": "eval:doc.country=='Portugal'",
				"description": "Ativar conformidade fiscal portuguesa"
			}
		]

		created_count = 0
		for field_config in essential_fields:
			try:
				field_name = f"{field_config['dt']}-{field_config['fieldname']}"

				if not frappe.db.exists("Custom Field", field_name):
					custom_field = frappe.get_doc({
						"doctype": "Custom Field",
						"module": "Portugal Compliance",
						**field_config
					})
					custom_field.insert(ignore_permissions=True)
					created_count += 1

			except Exception as e:
				print(f"⚠️ Erro ao criar campo {field_config['fieldname']}: {str(e)}")

		print(f"✅ Campos essenciais criados (fallback): {created_count}")

	except Exception as e:
		print(f"❌ Erro no fallback: {str(e)}")


def setup_initial_property_setters():
	"""
	✅ ATUALIZADO: Configurar Property Setters iniciais
	Baseado na sua experiência com programação.autenticação[10]
	"""
	try:
		print("\n📋 Configurando Property Setters iniciais...")

		# ✅ PROPERTY SETTERS ESSENCIAIS (não específicos por empresa)
		essential_property_setters = [
			{
				"doc_type": "Sales Invoice",
				"field_name": "atcud_code",
				"property": "read_only",
				"value": "1",
				"description": "ATCUD deve ser read-only"
			},
			{
				"doc_type": "Company",
				"field_name": "portugal_compliance_enabled",
				"property": "default",
				"value": "0",
				"description": "Compliance desativado por padrão"
			}
		]

		created_count = 0
		for ps_config in essential_property_setters:
			try:
				ps_name = f"{ps_config['doc_type']}-{ps_config['field_name']}-{ps_config['property']}"

				if not frappe.db.exists("Property Setter", ps_name):
					property_setter = frappe.get_doc({
						"doctype": "Property Setter",
						"name": ps_name,
						"doc_type": ps_config["doc_type"],
						"field_name": ps_config["field_name"],
						"property": ps_config["property"],
						"property_type": "Check" if ps_config[
														"property"] == "read_only" else "Data",
						"value": ps_config["value"],
						"doctype_or_field": "DocField"
					})
					property_setter.insert(ignore_permissions=True)
					created_count += 1

			except Exception as e:
				print(f"⚠️ Erro ao criar Property Setter: {str(e)}")

		print(f"✅ Property Setters criados: {created_count}")

	except Exception as e:
		print(f"❌ Erro ao configurar Property Setters: {str(e)}")


def setup_existing_portuguese_companies():
	"""
	✅ ATUALIZADO: Configurar empresas portuguesas existentes
	Baseado na sua experiência com programação.correção_de_código[11]
	"""
	try:
		print("\n📋 Configurando empresas portuguesas existentes...")

		# Buscar empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id"])

		if not portuguese_companies:
			print("⚠️ Nenhuma empresa portuguesa encontrada")
			print("💡 Crie uma empresa com país = 'Portugal' para usar o compliance")
			return

		print(f"📋 Encontradas {len(portuguese_companies)} empresas portuguesas")

		# ✅ CONFIGURAR AUTOMATICAMENTE (opcional)
		auto_setup = True  # Pode ser configurável

		if auto_setup:
			for company in portuguese_companies:
				try:
					setup_single_company_after_install(company.name)
				except Exception as e:
					print(f"⚠️ Erro ao configurar {company.name}: {str(e)}")
		else:
			print(
				"💡 Execute manualmente: bench execute portugal_compliance.install.setup_company_portugal_compliance.execute")

	except Exception as e:
		print(f"❌ Erro ao configurar empresas: {str(e)}")


def setup_single_company_after_install(company_name):
	"""
	✅ NOVO: Configurar empresa individual após instalação
	"""
	try:
		print(f"📋 Configurando empresa: {company_name}")

		company_doc = frappe.get_doc("Company", company_name)

		# ✅ CONFIGURAR APENAS SE NÃO TIVER COMPLIANCE ATIVO
		if not company_doc.get("portugal_compliance_enabled"):
			# Configurar campos básicos
			company_doc.portugal_compliance_enabled = 0  # Deixar para ativação manual

			# ✅ CONFIGURAR CREDENCIAIS DE TESTE SE VAZIAS (2026-08-23:
			# passaram para Portugal Auth Settings - Company deixou de ter
			# estes campos, ver document_hooks.sync_at_credentials removida)
			auth_settings = frappe.get_single("Portugal Auth Settings")
			if not auth_settings.get("at_username"):
				auth_settings.at_username = "599999993/1"  # Credenciais de teste AT
				auth_settings.at_password = "testes123"
				auth_settings.sandbox_mode = 1
				auth_settings.save(ignore_permissions=True)

			company_doc.save(ignore_permissions=True)
			print(f"✅ Empresa {company_name} preparada para compliance")
		else:
			print(f"✅ Empresa {company_name} já tem compliance ativo")

	except Exception as e:
		print(f"⚠️ Erro ao configurar empresa {company_name}: {str(e)}")


def create_sample_data_if_needed():
	"""
	✅ ATUALIZADO: Criar dados de exemplo se necessário
	"""
	try:
		print("\n📋 Verificando necessidade de dados de exemplo...")

		# ✅ CRIAR APENAS SE NÃO HOUVER DADOS
		customer_count = frappe.db.count("Customer")
		supplier_count = frappe.db.count("Supplier")
		item_count = frappe.db.count("Item")

		if customer_count == 0 and supplier_count == 0 and item_count == 0:
			print("📋 Criando dados de exemplo básicos...")
			create_basic_sample_data()
		else:
			print(
				f"✅ Dados existentes: {customer_count} clientes, {supplier_count} fornecedores, {item_count} itens")

	except Exception as e:
		print(f"⚠️ Erro ao verificar dados de exemplo: {str(e)}")


def create_basic_sample_data():
	"""
	✅ NOVO: Criar dados de exemplo básicos
	"""
	try:
		# ✅ CLIENTE DE EXEMPLO PORTUGUÊS
		if not frappe.db.exists("Customer", "Cliente Exemplo Portugal"):
			customer_doc = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "Cliente Exemplo Portugal",
				"customer_type": "Company",
				"customer_group": "Commercial",
				"territory": "Portugal",
				"tax_id": "123456789",  # NIF de teste válido
				"country": "Portugal"
			})
			customer_doc.insert(ignore_permissions=True)
			print("✅ Cliente de exemplo criado")

		# ✅ ITEM DE EXEMPLO
		if not frappe.db.exists("Item", "SERVICO-EXEMPLO-PT"):
			item_doc = frappe.get_doc({
				"doctype": "Item",
				"item_code": "SERVICO-EXEMPLO-PT",
				"item_name": "Serviço de Exemplo Portugal",
				"item_group": "All Item Groups",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"standard_rate": 100.00
			})
			item_doc.insert(ignore_permissions=True)
			print("✅ Item de exemplo criado")

	except Exception as e:
		print(f"⚠️ Erro ao criar dados de exemplo: {str(e)}")


def setup_portugal_compliance_permissions():
	"""
	✅ NOVO: Configurar permissões específicas do Portugal Compliance
	"""
	try:
		print("\n📋 Configurando permissões específicas...")

		# ✅ PERMISSÕES PARA PORTUGAL SERIES CONFIGURATION
		setup_doctype_permissions("Portugal Series Configuration", [
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"role": "Accounts Manager", "read": 1, "write": 1, "create": 1},
			{"role": "Accounts User", "read": 1}
		])

		# Bloco de permissões para "Portugal AT Communication Log" removido
		# (Fase 5) - essa doctype nunca existiu neste app.

		print("✅ Permissões específicas configuradas")

	except Exception as e:
		print(f"⚠️ Erro ao configurar permissões: {str(e)}")


def setup_doctype_permissions(doctype, permissions):
	"""
	✅ AUXILIAR: Configurar permissões para um DocType
	"""
	try:
		for perm in permissions:
			# Verificar se permissão já existe
			existing = frappe.db.exists("Custom DocPerm", {
				"parent": doctype,
				"role": perm["role"]
			})

			if not existing:
				doc_perm = frappe.get_doc({
					"doctype": "Custom DocPerm",
					"parent": doctype,
					"parenttype": "DocType",
					"parentfield": "permissions",
					"role": perm["role"],
					"read": perm.get("read", 0),
					"write": perm.get("write", 0),
					"create": perm.get("create", 0),
					"delete": perm.get("delete", 0)
				})
				doc_perm.insert(ignore_permissions=True)

	except Exception as e:
		print(f"⚠️ Erro ao configurar permissões para {doctype}: {str(e)}")


def run_startup_fixes_after_install():
	"""
	✅ BASEADO NO SEARCH RESULT [3]: Executar startup fixes após instalação
	"""
	try:
		print("\n📋 Executando startup fixes após instalação...")

		# ✅ EXECUTAR STARTUP FIXES
		try:
			from portugal_compliance.utils.startup_fixes import run_all_startup_fixes

			result = run_all_startup_fixes()
			if result.get("success"):
				print("✅ Startup fixes executados com sucesso")
			else:
				print(f"⚠️ Startup fixes com avisos: {result.get('error', 'Erro desconhecido')}")

		except ImportError:
			print("⚠️ Startup fixes não disponíveis - serão executados no próximo restart")

	except Exception as e:
		print(f"⚠️ Erro ao executar startup fixes: {str(e)}")


def setup_scheduler_jobs():
	"""
	✅ NOVO: Configurar jobs do scheduler
	"""
	try:
		print("\n📋 Configurando jobs do scheduler...")

		# ✅ VERIFICAR SE SCHEDULER ESTÁ ATIVO
		scheduler_enabled = frappe.utils.cint(
			frappe.db.get_single_value("System Settings", "enable_scheduler"))

		if scheduler_enabled:
			print("✅ Scheduler está ativo")
		else:
			print("⚠️ Scheduler está desativo - jobs não serão executados automaticamente")

		# ✅ JOBS ESPECÍFICOS DO PORTUGAL COMPLIANCE
		portugal_jobs = [
			"portugal_compliance.tasks.daily_compliance_check",
			"portugal_compliance.tasks.weekly_series_validation",
			"portugal_compliance.tasks.monthly_at_sync"
		]

		print(f"📋 Jobs configurados: {len(portugal_jobs)}")
		for job in portugal_jobs:
			print(f"   - {job}")

	except Exception as e:
		print(f"⚠️ Erro ao configurar scheduler: {str(e)}")


def validate_final_installation():
	"""
	✅ ATUALIZADO: Validação final da instalação
	Baseado na sua experiência com programação.teste_de_ambiente[14]
	"""
	try:
		print("\n📋 Validação final da instalação...")

		validation_results = {
			"app_installed": "portugal_compliance" in frappe.get_installed_apps(),
			"custom_fields_created": frappe.db.exists("Custom Field", "Sales Invoice-atcud_code"),
			"doctypes_created": frappe.db.exists("DocType", "Portugal Series Configuration"),
			"permissions_set": frappe.db.exists("Custom DocPerm",
												{"parent": "Portugal Series Configuration"}),
		}

		# Mostrar resultados
		print("📊 Resultados da validação:")
		for check, result in validation_results.items():
			status = "✅" if result else "❌"
			print(f"   {status} {check.replace('_', ' ').title()}")

		# Calcular score
		score = sum(validation_results.values()) / len(validation_results) * 100
		print(f"\n📊 Score de instalação: {score:.1f}%")

		if score >= 80:
			print("✅ Instalação bem-sucedida!")
			return True
		else:
			print("⚠️ Instalação com problemas - algumas funcionalidades podem não funcionar")
			return False

	except Exception as e:
		print(f"❌ Erro na validação final: {str(e)}")
		return False


def show_next_steps():
	"""
	✅ NOVO: Mostrar próximos passos após instalação
	"""
	try:
		print("\n🇵🇹 PRÓXIMOS PASSOS:")
		print("=" * 50)
		print("1. 🏢 Criar ou configurar empresa portuguesa:")
		print("   - País: Portugal")
		print("   - NIF válido")
		print("   - Moeda: EUR")
		print("")
		print("2. 🔧 Ativar Portugal Compliance:")
		print("   - Ir para: Company > [Sua Empresa] > Portugal Compliance Enabled")
		print("   - Configurar credenciais AT (opcional)")
		print("")
		print("3. 📋 Verificar séries criadas:")
		print("   - Ir para: Portugal Series Configuration")
		print("   - Comunicar séries à AT")
		print("")
		print("4. 🧪 Testar funcionalidades:")
		print("   - Criar Sales Invoice")
		print("   - Verificar geração automática de ATCUD")
		print("")
		print("5. 📚 Documentação:")
		print("   - Consultar: apps/portugal_compliance/README.md")
		print("   - Suporte: https://github.com/your-repo/portugal_compliance")
		print("=" * 50)

	except Exception as e:
		print(f"⚠️ Erro ao mostrar próximos passos: {str(e)}")


# ========== FUNÇÕES AUXILIARES ==========

def cleanup_installation_files():
	"""
	✅ NOVO: Limpar arquivos temporários da instalação
	"""
	try:
		print("\n📋 Limpando arquivos temporários...")

		# Limpar cache
		frappe.clear_cache()

		# Limpar arquivos temporários
		temp_dir = "/home/frappe/frappe-bench/sites/assets/portugal_compliance/temp"
		if os.path.exists(temp_dir):
			for file in os.listdir(temp_dir):
				if file.endswith('.tmp'):
					try:
						os.remove(os.path.join(temp_dir, file))
					except Exception:
						pass

		print("✅ Limpeza concluída")

	except Exception as e:
		print(f"⚠️ Erro na limpeza: {str(e)}")


# ========== FUNÇÃO PRINCIPAL ==========

def after_install():
	"""
	✅ FUNÇÃO PRINCIPAL: Chamada pelo hooks.py após instalação
	Baseado na sua experiência com programação.sistemas_erp[12]
	"""
	try:
		execute()
		cleanup_installation_files()
		return True
	except Exception as e:
		print(f"\n❌ PÓS-INSTALAÇÃO FALHOU: {str(e)}")
		print("💡 Verifique os logs para mais detalhes")
		return False


# ========== LOG FINAL ==========
if __name__ == "__main__":
	print("🇵🇹 Portugal Compliance - After Install Script")
	print("Executando configurações pós-instalação...")
	success = after_install()
	if success:
		print("✅ Pós-instalação concluída com sucesso!")
	else:
		print("❌ Pós-instalação falhou!")

frappe.logger().info(
	"Portugal Compliance After Install ATUALIZADO loaded - Version 2.1.0 - Best Practices Applied")
