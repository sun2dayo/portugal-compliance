# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, cint
from erpnext.accounts.utils import get_fiscal_year
import re


def execute():
	"""
	✅ CORRIGIDO: Patch para configurar séries portuguesas usando NOVA ABORDAGEM
	Adaptado para naming_series nativa sem campos portugal_series
	"""
	frappe.logger().info("🇵🇹 Iniciando patch: setup_portugal_series - NOVA ABORDAGEM")

	try:
		# ✅ VERIFICAR SE PATCH JÁ FOI EXECUTADO (NOVA ABORDAGEM)
		if frappe.db.exists("Portugal Series Configuration", {"prefix": "FT2025DEFAULT"}):
			frappe.logger().info("Patch setup_portugal_series (nova abordagem) já foi executado")
			return

		# Obter todas as empresas portuguesas
		portuguese_companies = get_portuguese_companies()

		if not portuguese_companies:
			frappe.logger().info(
				"Nenhuma empresa portuguesa encontrada. Criando configuração padrão.")
			create_default_company_series()
		else:
			# Criar séries para cada empresa portuguesa
			for company in portuguese_companies:
				create_series_for_company_new_approach(company)

		# ✅ CONFIGURAR APENAS CAMPOS ESSENCIAIS (SEM portugal_series)
		setup_essential_custom_fields()

		# ✅ CONFIGURAR PROPERTY SETTERS ADAPTADOS
		setup_property_setters_new_approach()

		# ✅ CONFIGURAR NAMING SERIES USANDO NOVA ABORDAGEM
		setup_naming_series_new_approach()

		# ✅ TAREFAS PÓS-CONFIGURAÇÃO ADAPTADAS
		post_setup_tasks_new_approach()

		frappe.db.commit()
		frappe.logger().info(
			"✅ Patch setup_portugal_series (nova abordagem) executado com sucesso")

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Erro no patch setup_portugal_series (nova abordagem): {str(e)}",
						 "Portugal Compliance Patch")
		raise


def get_portuguese_companies():
	"""
	Obtém todas as empresas configuradas para Portugal - MANTIDA
	"""
	try:
		companies = frappe.get_all("Company",
								   filters={"country": "Portugal"},
								   fields=["name", "abbr", "tax_id"])
		return companies
	except Exception as e:
		frappe.log_error(f"Erro ao obter empresas portuguesas: {str(e)}")
		return []


def create_default_company_series():
	"""
	✅ CORRIGIDO: Cria séries para empresa padrão usando nova abordagem
	"""
	try:
		# Verificar se existe empresa padrão
		default_company = frappe.db.get_value("Company", {"is_default": 1})

		if not default_company:
			# Criar empresa padrão portuguesa
			default_company = create_default_portuguese_company()

		# Ativar compliance português na empresa padrão
		enable_portugal_compliance(default_company)

		# ✅ CORRIGIDO: Usar nova abordagem
		create_series_for_company_new_approach({"name": default_company, "abbr": "DEFAULT"})

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries padrão: {str(e)}")


def create_default_portuguese_company():
	"""
	Cria empresa padrão portuguesa se não existir - MANTIDA
	"""
	try:
		company_doc = frappe.get_doc({
			"doctype": "Company",
			"company_name": "Empresa Padrão Portugal",
			"abbr": "DEFAULT",
			"country": "Portugal",
			"default_currency": "EUR",
			"is_default": 1,
			"portugal_compliance_enabled": 1
		})
		company_doc.insert(ignore_permissions=True)

		frappe.logger().info(f"Empresa padrão portuguesa criada: {company_doc.name}")
		return company_doc.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar empresa padrão: {str(e)}")
		return None


def enable_portugal_compliance(company_name):
	"""
	Ativa compliance português para uma empresa - MANTIDA
	"""
	try:
		company_doc = frappe.get_doc("Company", company_name)
		company_doc.country = "Portugal"
		company_doc.portugal_compliance_enabled = 1
		company_doc.default_currency = "EUR"
		company_doc.save(ignore_permissions=True)

		frappe.logger().info(f"Compliance português ativado para empresa: {company_name}")

	except Exception as e:
		frappe.log_error(f"Erro ao ativar compliance português: {str(e)}")


def create_series_for_company_new_approach(company):
	"""
	✅ CORRIGIDO: Cria séries usando NOVA ABORDAGEM (sem hífens)
	"""
	try:
		company_name = company["name"]
		company_abbr = company.get("abbr", "COMP")

		# Obter ano atual
		current_year = today().year

		# ✅ DEFINIR SÉRIES USANDO MAPEAMENTO DA NOVA ABORDAGEM
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		created_series = []

		for doctype, doc_info in PORTUGAL_DOCUMENT_TYPES.items():
			try:
				# ✅ FORMATO NOVO: XXYYYY + EMPRESA (sem hífens)
				prefix = f"{doc_info['code']}{current_year}{company_abbr}"
				naming_series = f"{prefix}.####"

				# Verificar se série já existe
				if not frappe.db.exists("Portugal Series Configuration", {
					"prefix": prefix,
					"company": company_name
				}):
					# ✅ CRIAR NOVA SÉRIE COM NOVA ESTRUTURA
					series_doc = frappe.get_doc({
						"doctype": "Portugal Series Configuration",
						"series_name": f"{doc_info['name']} - {prefix}",
						"company": company_name,
						"document_type": doctype,
						"prefix": prefix,
						"naming_series": naming_series,
						"current_sequence": 1,
						"is_active": 1,
						"is_communicated": 0,
						"at_environment": "test",
						"document_code": doc_info['code'],
						"year_code": str(current_year),
						"company_code": company_abbr,
						"naming_pattern": naming_series,
						"atcud_pattern": "0.{sequence}",
						"notes": f"Série criada pelo patch para {doc_info['description']}"
					})

					series_doc.insert(ignore_permissions=True)
					created_series.append(prefix)

					frappe.logger().info(
						f"✅ Série criada (nova abordagem): {prefix} para {company_name}")

			except Exception as e:
				frappe.log_error(f"Erro ao criar série {doctype}: {str(e)}")

		if created_series:
			frappe.logger().info(
				f"✅ Criadas {len(created_series)} séries (nova abordagem) para empresa {company_name}")

		return created_series

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries para empresa {company['name']}: {str(e)}")
		return []


def setup_essential_custom_fields():
	"""
	✅ CORRIGIDO: Configura APENAS campos essenciais (SEM portugal_series)
	"""
	try:
		# ✅ VERIFICAR SE CAMPOS ESSENCIAIS JÁ EXISTEM
		if frappe.db.exists("Custom Field", "Sales Invoice-atcud_code"):
			frappe.logger().info("Campos essenciais já existem")
			return

		# ✅ APENAS CAMPOS ESSENCIAIS (REMOVIDO portugal_series)
		essential_fields = [
			{
				"dt": "Company",
				"fieldname": "portugal_compliance_enabled",
				"label": "Portugal Compliance Enabled",
				"fieldtype": "Check",
				"insert_after": "country",
				"depends_on": "eval:doc.country=='Portugal'",
				"default": "0",
				"description": "Ativar conformidade fiscal portuguesa para esta empresa"
			}
		]

		# ✅ CAMPOS ATCUD PARA DOCUMENTOS SUPORTADOS
		supported_doctypes = [
			"Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry",
			"Quotation", "Sales Order", "Purchase Order", "Material Request"
		]

		for doctype in supported_doctypes:
			essential_fields.append({
				"dt": doctype,
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"bold": 1,
				"in_list_view": 1 if doctype in ["Sales Invoice", "POS Invoice",
												 "Purchase Invoice"] else 0,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa"
			})

		# ✅ CRIAR APENAS CAMPOS ESSENCIAIS
		for field_config in essential_fields:
			field_name = f"{field_config['dt']}-{field_config['fieldname']}"

			if not frappe.db.exists("Custom Field", field_name):
				try:
					custom_field = frappe.get_doc({
						"doctype": "Custom Field",
						"name": field_name,
						"module": "Portugal Compliance",
						**field_config
					})
					custom_field.insert(ignore_permissions=True)

					frappe.logger().info(f"✅ Campo essencial criado: {field_name}")

				except Exception as e:
					frappe.log_error(f"Erro ao criar campo {field_name}: {str(e)}")

		frappe.logger().info("✅ Campos essenciais configurados (sem portugal_series)")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar campos essenciais: {str(e)}")


def setup_property_setters_new_approach():
	"""
	✅ CORRIGIDO: Configura property setters adaptados para nova abordagem
	"""
	try:
		property_setters = [
			{
				"doc_type": "Sales Invoice",
				"field_name": "currency",
				"property": "default",
				"value": "EUR"
			},
			{
				"doc_type": "Purchase Invoice",
				"field_name": "currency",
				"property": "default",
				"value": "EUR"
			},
			{
				"doc_type": "Company",
				"field_name": "country",
				"property": "default",
				"value": "Portugal"
			},
			{
				"doc_type": "Customer",
				"field_name": "tax_id",
				"property": "label",
				"value": "NIF"
			},
			{
				"doc_type": "Supplier",
				"field_name": "tax_id",
				"property": "label",
				"value": "NIF"
			},
			# ✅ NOVO: Property setter para Company
			{
				"doc_type": "Company",
				"field_name": "default_currency",
				"property": "default",
				"value": "EUR"
			}
		]

		for ps_config in property_setters:
			ps_name = f"{ps_config['doc_type']}-{ps_config['field_name']}-{ps_config['property']}"

			if not frappe.db.exists("Property Setter", ps_name):
				try:
					property_setter = frappe.get_doc({
						"doctype": "Property Setter",
						"name": ps_name,
						"property_type": "Data",
						"doctype_or_field": "DocField",
						**ps_config
					})
					property_setter.insert(ignore_permissions=True)

					frappe.logger().info(f"✅ Property setter criado: {ps_name}")

				except Exception as e:
					frappe.log_error(f"Erro ao criar property setter {ps_name}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar property setters: {str(e)}")


def setup_naming_series_new_approach():
	"""
	✅ NOVO: Configura naming series usando Property Setters (nova abordagem)
	"""
	try:
		# ✅ OBTER TODAS AS SÉRIES CRIADAS
		series = frappe.get_all("Portugal Series Configuration",
								fields=["naming_series", "document_type"])

		# ✅ AGRUPAR POR TIPO DE DOCUMENTO
		series_by_doctype = {}
		for s in series:
			if s.document_type not in series_by_doctype:
				series_by_doctype[s.document_type] = []
			if s.naming_series not in series_by_doctype[s.document_type]:
				series_by_doctype[s.document_type].append(s.naming_series)

		# ✅ CRIAR PROPERTY SETTERS PARA NAMING SERIES
		for doctype, series_list in series_by_doctype.items():
			try:
				ps_name = f"{doctype}-naming_series-options"

				if not frappe.db.exists("Property Setter", ps_name):
					# ✅ CRIAR PROPERTY SETTER COM OPÇÕES DE NAMING SERIES
					naming_options = '\n'.join(series_list)

					property_setter = frappe.get_doc({
						"doctype": "Property Setter",
						"name": ps_name,
						"doc_type": doctype,
						"property": "options",
						"field_name": "naming_series",
						"property_type": "Text",
						"value": naming_options,
						"doctype_or_field": "DocField"
					})
					property_setter.insert(ignore_permissions=True)

					frappe.logger().info(
						f"✅ Naming series configurado para {doctype}: {len(series_list)} opções")

			except Exception as e:
				frappe.log_error(f"Erro ao configurar naming series para {doctype}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar naming series: {str(e)}")


def create_default_auth_settings():
	"""
	✅ ADAPTADO: Cria configurações de autenticação padrão
	"""
	try:
		# ✅ VERIFICAR SE DOCTYPE EXISTE
		if not frappe.db.exists("DocType", "Portugal Auth Settings"):
			frappe.logger().info(
				"DocType Portugal Auth Settings não existe - pulando configuração")
			return

		if not frappe.db.exists("Portugal Auth Settings", "Portugal Auth Settings"):
			auth_settings = frappe.get_doc({
				"doctype": "Portugal Auth Settings",
				"sandbox_mode": 1,
				"at_webservice_url": "https://servicos-test.portaldasfinancas.gov.pt:722/SeriesWSService"
			})
			auth_settings.insert(ignore_permissions=True)

			frappe.logger().info("✅ Configurações de autenticação padrão criadas")

	except Exception as e:
		frappe.log_error(f"Erro ao criar configurações de autenticação: {str(e)}")


def setup_permissions():
	"""
	✅ ADAPTADO: Configura permissões para os doctypes
	"""
	try:
		# ✅ PERMISSÕES PARA PORTUGAL SERIES CONFIGURATION
		permissions_config = [
			{
				"doctype": "Portugal Series Configuration",
				"role": "System Manager",
				"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
			},
			{
				"doctype": "Portugal Series Configuration",
				"role": "Accounts Manager",
				"perms": {"read": 1, "write": 1, "create": 1, "delete": 0}
			},
			{
				"doctype": "Portugal Series Configuration",
				"role": "Accounts User",
				"perms": {"read": 1, "write": 0, "create": 0, "delete": 0}
			}
		]

		# ✅ ADICIONAR PERMISSÕES PARA ATCUD LOG SE EXISTIR
		if frappe.db.exists("DocType", "ATCUD Log"):
			permissions_config.extend([
				{
					"doctype": "ATCUD Log",
					"role": "System Manager",
					"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
				},
				{
					"doctype": "ATCUD Log",
					"role": "Accounts Manager",
					"perms": {"read": 1, "write": 0, "create": 0, "delete": 0}
				}
			])

		for perm_config in permissions_config:
			try:
				# ✅ VERIFICAR SE PERMISSÃO JÁ EXISTE
				existing_perm = frappe.db.exists("Custom DocPerm", {
					"parent": perm_config["doctype"],
					"role": perm_config["role"]
				})

				if not existing_perm:
					custom_perm = frappe.get_doc({
						"doctype": "Custom DocPerm",
						"parent": perm_config["doctype"],
						"parenttype": "DocType",
						"role": perm_config["role"],
						**perm_config["perms"]
					})
					custom_perm.insert(ignore_permissions=True)

					frappe.logger().info(
						f"✅ Permissão criada: {perm_config['doctype']} - {perm_config['role']}")

			except Exception as e:
				frappe.log_error(f"Erro ao criar permissão: {str(e)}")

		frappe.logger().info("✅ Permissões configuradas")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar permissões: {str(e)}")


def post_setup_tasks_new_approach():
	"""
	✅ ADAPTADO: Tarefas pós-configuração para nova abordagem
	"""
	try:
		# ✅ CRIAR CONFIGURAÇÕES DE AUTENTICAÇÃO
		create_default_auth_settings()

		# ✅ CONFIGURAR PERMISSÕES
		setup_permissions()

		# ✅ CONFIGURAR NAMING SERIES
		setup_naming_series_new_approach()

		# ✅ CRIAR CONFIGURAÇÕES INICIAIS DE EMPRESA
		setup_initial_company_configs()

		# ✅ LIMPAR CACHE
		frappe.clear_cache()

		frappe.logger().info("✅ Tarefas pós-configuração (nova abordagem) concluídas")

	except Exception as e:
		frappe.log_error(f"Erro nas tarefas pós-configuração: {str(e)}")


def setup_initial_company_configs():
	"""
	✅ NOVO: Configurações iniciais para empresas portuguesas
	"""
	try:
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name"])

		for company in portuguese_companies:
			try:
				company_doc = frappe.get_doc("Company", company.name)

				# ✅ CONFIGURAR DEFAULTS PORTUGUESES
				if not company_doc.default_currency:
					company_doc.default_currency = "EUR"

				if not getattr(company_doc, 'portugal_compliance_enabled', None):
					company_doc.portugal_compliance_enabled = 1

				company_doc.save(ignore_permissions=True)

				frappe.logger().info(f"✅ Configurações iniciais aplicadas: {company.name}")

			except Exception as e:
				frappe.log_error(f"Erro ao configurar empresa {company.name}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro nas configurações iniciais: {str(e)}")


def cleanup_old_portugal_series_fields():
	"""
	✅ NOVO: Limpar campos portugal_series antigos se existirem
	"""
	try:
		# ✅ BUSCAR E REMOVER CAMPOS portugal_series ANTIGOS
		old_fields = frappe.db.sql("""
								   SELECT name
								   FROM `tabCustom Field`
								   WHERE fieldname = 'portugal_series'
								   """, as_dict=True)

		removed_count = 0
		for field in old_fields:
			try:
				frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
				removed_count += 1
			except:
				pass

		if removed_count > 0:
			frappe.logger().info(f"✅ Removidos {removed_count} campos portugal_series antigos")

		# ✅ REMOVER PROPERTY SETTERS ANTIGOS
		old_property_setters = frappe.db.sql("""
											 SELECT name
											 FROM `tabProperty Setter`
											 WHERE field_name = 'portugal_series'
											 """, as_dict=True)

		removed_ps = 0
		for ps in old_property_setters:
			try:
				frappe.delete_doc("Property Setter", ps.name, ignore_permissions=True)
				removed_ps += 1
			except:
				pass

		if removed_ps > 0:
			frappe.logger().info(
				f"✅ Removidos {removed_ps} property setters portugal_series antigos")

	except Exception as e:
		frappe.log_error(f"Erro na limpeza de campos antigos: {str(e)}")


# ========== EXECUTAR LIMPEZA NO FINAL ==========
def execute_final_cleanup():
	"""
	✅ NOVO: Executar limpeza final
	"""
	try:
		cleanup_old_portugal_series_fields()
		frappe.logger().info("✅ Limpeza final concluída")
	except Exception as e:
		frappe.log_error(f"Erro na limpeza final: {str(e)}")

# ========== ADICIONAR LIMPEZA AO EXECUTE PRINCIPAL ==========
# Adicionar no final da função execute():
# execute_final_cleanup()
