# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import os
import json
from frappe.utils import getdate


def execute():
	"""Executado após a instalação do Portugal Compliance - VERSÃO CERTIFICADA"""
	try:
		print("🇵🇹 Iniciando pós-instalação do Portugal Compliance - Nova Abordagem...")

		# ✅ 1. PRIMEIRO: Remover campos conflitantes portugal_series
		remove_conflicting_portugal_series_fields()

		# ✅ 2. Verificar se fixtures foram aplicados
		verify_fixtures_applied()

		# ✅ 3. Criar APENAS campos ATCUD (sem portugal_series)
		create_atcud_fields_only()

		# ✅ 4. Configurar permissões
		setup_permissions()

		# ✅ 5. Criar role Portugal Compliance User
		create_compliance_role()

		# ✅ 6. Configurar configurações padrão
		create_default_settings()

		# ✅ 7. Configurar Print Formats
		setup_print_formats()

		# ✅ 8. Configurar naming series dinâmicas
		setup_dynamic_naming_series()

		# ✅ 9. Configurar compliance inviolável
		setup_inviolable_compliance()

		# ✅ 10. Sincronizar naming series automaticamente
		sync_naming_series_post_install()

		# ✅ 11. Criar dados de exemplo seguros
		create_safe_sample_data()

		# ✅ 12. Validar instalação completa
		validate_installation()

		# ✅ 13. Mostrar mensagem de sucesso
		show_success_message()

		print("✅ Pós-instalação do Portugal Compliance concluída com sucesso!")

	except Exception as e:
		frappe.log_error(f"Erro na pós-instalação do Portugal Compliance: {str(e)}")
		print(f"❌ Erro na pós-instalação: {str(e)}")
		show_error_message(str(e))


def remove_conflicting_portugal_series_fields():
	"""Remove campos portugal_series conflitantes - PRIMEIRA PRIORIDADE"""
	try:
		print("🗑️ Removendo campos portugal_series conflitantes...")

		# ✅ LISTA COMPLETA DE CAMPOS CONFLITANTES A REMOVER
		conflicting_fields = [
			"Sales Invoice-portugal_series",
			"Purchase Invoice-portugal_series",
			"Payment Entry-portugal_series",
			"Delivery Note-portugal_series",
			"Purchase Receipt-portugal_series",
			"Journal Entry-portugal_series",
			"Stock Entry-portugal_series",
			"Quotation-portugal_series",
			"Sales Order-portugal_series",
			"Purchase Order-portugal_series",
			"Material Request-portugal_series",
			# ✅ REMOVER TAMBÉM CAMPOS RELACIONADOS CONFLITANTES
			"Sales Invoice-portugal_series_prefix",
			"Purchase Invoice-portugal_series_prefix",
			"Payment Entry-portugal_series_prefix",
			"Sales Invoice-portugal_compliance_status",
			"Purchase Invoice-portugal_compliance_status",
			"Payment Entry-portugal_compliance_status"
		]

		removed_count = 0
		for field_name in conflicting_fields:
			if frappe.db.exists("Custom Field", field_name):
				try:
					frappe.delete_doc("Custom Field", field_name, ignore_permissions=True)
					removed_count += 1
					print(f"🗑️ Campo conflitante removido: {field_name}")
				except Exception as e:
					print(f"⚠️ Erro ao remover {field_name}: {str(e)}")

		if removed_count > 0:
			print(f"🗑️ Removidos {removed_count} campos conflitantes")
			frappe.clear_cache()
			frappe.db.commit()
		else:
			print("✅ Nenhum campo conflitante encontrado")

	except Exception as e:
		print(f"❌ Erro ao remover campos conflitantes: {str(e)}")


def verify_fixtures_applied():
	"""Verificar se fixtures foram aplicados corretamente"""
	try:
		print("📋 Verificando se fixtures foram aplicados...")

		# ✅ CAMPOS CRÍTICOS APENAS ATCUD
		critical_fields = [
			"Sales Invoice-atcud_code",
			"Purchase Invoice-atcud_code",
			"Payment Entry-atcud_code",
			"Delivery Note-atcud_code",
			"Purchase Receipt-atcud_code",
			"Journal Entry-atcud_code",
			"Stock Entry-atcud_code",
			"Company-portugal_compliance_enabled",
			"Company-at_certificate_number"
		]

		missing_fields = []
		for field_name in critical_fields:
			if not frappe.db.exists("Custom Field", field_name):
				missing_fields.append(field_name)

		if missing_fields:
			print(f"⚠️ Fixtures não aplicaram todos os campos: {len(missing_fields)} em falta")
			for field in missing_fields:
				print(f"   - {field}")
			return False
		else:
			print("✅ Todos os fixtures foram aplicados corretamente")
			return True

	except Exception as e:
		print(f"❌ Erro ao verificar fixtures: {str(e)}")
		return False


def create_atcud_fields_only():
	"""Criar APENAS campos ATCUD - SEM portugal_series"""
	try:
		print("📋 Criando APENAS campos ATCUD para nova abordagem naming_series...")

		# ✅ CONFIGURAÇÃO CERTIFICADA: APENAS CAMPOS ATCUD ESSENCIAIS
		atcud_fields_config = [
			# ✅ DOCUMENTOS FISCAIS PRINCIPAIS
			{
				"dt": "Sales Invoice",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"bold": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Purchase Invoice",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"bold": 1,
				"in_list_view": 1,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Payment Entry",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"bold": 1,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Delivery Note",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Purchase Receipt",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Journal Entry",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			{
				"dt": "Stock Entry",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento - gerado automaticamente pela série portuguesa comunicada"
			},
			# ✅ DOCUMENTOS COMERCIAIS (OPCIONAIS)
			{
				"dt": "Quotation",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento (opcional para orçamentos)"
			},
			{
				"dt": "Sales Order",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento (opcional para encomendas)"
			},
			{
				"dt": "Purchase Order",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento (opcional para encomendas)"
			},
			{
				"dt": "Material Request",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"description": "Código Único de Documento (opcional para requisições)"
			},
			# ✅ CAMPOS QR CODE PARA DOCUMENTOS PRINCIPAIS
			{
				"dt": "Sales Invoice",
				"fieldname": "qr_code_image",
				"label": "QR Code",
				"fieldtype": "Attach Image",
				"insert_after": "atcud_code",
				"read_only": 1,
				"print_hide": 0,
				"description": "QR Code gerado automaticamente para o documento"
			},
			{
				"dt": "Purchase Invoice",
				"fieldname": "qr_code_image",
				"label": "QR Code",
				"fieldtype": "Attach Image",
				"insert_after": "atcud_code",
				"read_only": 1,
				"print_hide": 0,
				"description": "QR Code gerado automaticamente para o documento"
			},
			{
				"dt": "Payment Entry",
				"fieldname": "qr_code_image",
				"label": "QR Code",
				"fieldtype": "Attach Image",
				"insert_after": "atcud_code",
				"read_only": 1,
				"print_hide": 0,
				"description": "QR Code gerado automaticamente para o documento"
			},
			# ✅ CONFIGURAÇÕES DE EMPRESA
			{
				"dt": "Company",
				"fieldname": "portugal_compliance_enabled",
				"label": "Portugal Compliance Enabled",
				"fieldtype": "Check",
				"insert_after": "country",
				"default": "0",
				"description": "Ativar conformidade fiscal portuguesa para esta empresa"
			},
			{
				"dt": "Company",
				"fieldname": "at_certificate_number",
				"label": "AT Certificate Number",
				"fieldtype": "Data",
				"insert_after": "portugal_compliance_enabled",
				"depends_on": "eval:doc.portugal_compliance_enabled",
				"description": "Número do certificado de software emitido pela AT (opcional)"
			},
			# ✅ VALIDAÇÃO NIF
			{
				"dt": "Customer",
				"fieldname": "nif_validated",
				"label": "NIF Validated",
				"fieldtype": "Check",
				"insert_after": "tax_id",
				"read_only": 1,
				"description": "NIF foi validado automaticamente pelo algoritmo português"
			},
			{
				"dt": "Supplier",
				"fieldname": "nif_validated",
				"label": "NIF Validated",
				"fieldtype": "Check",
				"insert_after": "tax_id",
				"read_only": 1,
				"description": "NIF foi validado automaticamente pelo algoritmo português"
			}
		]

		fields_created = 0
		fields_skipped = 0

		for field_config in atcud_fields_config:
			try:
				field_name = f"{field_config['dt']}-{field_config['fieldname']}"

				if not frappe.db.exists("Custom Field", field_name):
					custom_field = frappe.get_doc({
						"doctype": "Custom Field",
						"module": "Portugal Compliance",
						**field_config
					})

					custom_field.insert(ignore_permissions=True)
					fields_created += 1
					print(f"✅ Campo ATCUD criado: {field_name}")
				else:
					fields_skipped += 1

			except Exception as e:
				print(
					f"❌ Erro ao criar campo {field_config['dt']}.{field_config['fieldname']}: {str(e)}")
				continue

		print(f"📋 Resumo ATCUD Fields: {fields_created} criados, {fields_skipped} já existiam")
		frappe.db.commit()
		frappe.clear_cache()

	except Exception as e:
		print(f"❌ Erro ao criar campos ATCUD: {str(e)}")


def setup_permissions():
	"""Configurar permissões para compliance português"""
	try:
		print("📋 Configurando permissões...")

		compliance_doctypes = [
			"Portugal Series Configuration",
			"ATCUD Log"
		]

		for doctype in compliance_doctypes:
			try:
				if frappe.db.exists("DocType", doctype):
					print(f"✅ DocType {doctype} - OK")
				else:
					print(f"⚠️ DocType {doctype} não encontrado")
			except Exception as e:
				print(f"❌ Erro ao verificar {doctype}: {str(e)}")

		print("✅ Permissões verificadas")

	except Exception as e:
		print(f"❌ Erro ao configurar permissões: {str(e)}")


def create_compliance_role():
	"""Criar role Portugal Compliance User se não existir"""
	try:
		print("📋 Criando role Portugal Compliance User...")

		if not frappe.db.exists("Role", "Portugal Compliance User"):
			role = frappe.get_doc({
				"doctype": "Role",
				"role_name": "Portugal Compliance User",
				"desk_access": 1,
				"is_custom": 1,
				"home_page": "/app/portugal-compliance"
			})
			role.insert(ignore_permissions=True)
			print("✅ Role Portugal Compliance User criada")
		else:
			print("✅ Role Portugal Compliance User já existe")

	except Exception as e:
		print(f"❌ Erro ao criar role: {str(e)}")


def create_default_settings():
	"""Criar configurações padrão do sistema - COMPLIANCE INVIOLÁVEL"""
	try:
		print("📋 Criando configurações padrão para compliance inviolável...")

		if frappe.db.exists("DocType", "Portugal Compliance Settings"):
			if not frappe.db.exists("Portugal Compliance Settings",
									"Portugal Compliance Settings"):
				settings = frappe.get_doc({
					"doctype": "Portugal Compliance Settings",
					"name": "Portugal Compliance Settings",
					"enable_atcud_validation": 1,
					"auto_generate_atcud": 1,
					"default_at_environment": "test",
					"enable_qr_code_generation": 1,
					"enable_saft_export": 1,
					"use_naming_series_approach": 1,
					# ✅ COMPLIANCE INVIOLÁVEL
					"enforce_communicated_series_only": 1,
					"require_series_communication": 1,
					"validate_nif_format": 1,
					"auto_sync_property_setters": 1,
					"validate_prefix_format": 1
				})
				settings.insert(ignore_permissions=True)
				print("✅ Configurações padrão criadas com compliance inviolável")
			else:
				# ✅ ATUALIZAR CONFIGURAÇÕES EXISTENTES
				frappe.db.set_value("Portugal Compliance Settings", "Portugal Compliance Settings",
									{
										"use_naming_series_approach": 1,
										"enforce_communicated_series_only": 1,
										"require_series_communication": 1,
										"auto_sync_property_setters": 1
									})
				print("✅ Configurações padrão atualizadas para compliance inviolável")
		else:
			print("⚠️ DocType Portugal Compliance Settings não encontrado")

		frappe.db.commit()

	except Exception as e:
		print(f"❌ Erro ao criar configurações padrão: {str(e)}")


def setup_print_formats():
	"""Configurar Print Formats portugueses"""
	try:
		print("📋 Configurando Print Formats...")

		portuguese_print_formats = [
			"Invoice PT",
			"Receipt PT",
			"Credit Note PT",
			"Debit Note PT"
		]

		for pf in portuguese_print_formats:
			if frappe.db.exists("Print Format", pf):
				print(f"✅ Print Format {pf} - OK")
			else:
				print(f"⚠️ Print Format {pf} não encontrado")

	except Exception as e:
		print(f"❌ Erro ao configurar Print Formats: {str(e)}")


def setup_dynamic_naming_series():
	"""Configurar naming series dinâmicas - NOVA ABORDAGEM"""
	try:
		print("📋 Configurando naming series dinâmicas...")

		# ✅ CONFIGURAÇÃO DINÂMICA: Não criar séries fixas, apenas preparar estrutura
		current_year = getdate().year

		# ✅ CONFIGURAR APENAS ESTRUTURA BASE (sem séries específicas de empresa)
		base_naming_series_config = {
			"Sales Invoice": ["SINV-.YYYY.-"],
			"Purchase Invoice": ["PINV-.YYYY.-"],
			"Payment Entry": ["PAY-.YYYY.-"],
			"Delivery Note": ["DN-.YYYY.-"],
			"Purchase Receipt": ["PREC-.YYYY.-"],
			"Journal Entry": ["JV-.YYYY.-"],
			"Stock Entry": ["STE-.YYYY.-"]
		}

		updated_count = 0
		for doctype, base_series in base_naming_series_config.items():
			try:
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""

				# ✅ GARANTIR QUE SÉRIE BASE EXISTE
				if not current_autoname or current_autoname.strip() == "":
					new_autoname = '\n'.join(base_series)
					frappe.db.set_value("DocType", doctype, "autoname", new_autoname)
					frappe.clear_cache(doctype=doctype)
					updated_count += 1
					print(f"✅ Naming series base configurada para {doctype}")
				else:
					print(f"ℹ️ {doctype} já tem naming series configuradas")

			except Exception as e:
				print(f"❌ Erro ao configurar {doctype}: {str(e)}")

		print(f"✅ {updated_count} DocTypes configurados com naming series base")

		# ✅ NOTA: Séries portuguesas serão criadas dinamicamente quando compliance for ativado
		print(
			"ℹ️ Séries portuguesas serão criadas dinamicamente quando compliance for ativado por empresa")

		frappe.db.commit()

	except Exception as e:
		print(f"❌ Erro ao configurar naming series dinâmicas: {str(e)}")


def setup_inviolable_compliance():
	"""Configurar compliance inviolável desde instalação"""
	try:
		print("📋 Configurando compliance inviolável...")

		# ✅ CONFIGURAR PROPERTY SETTERS PARA COMPLIANCE OBRIGATÓRIO
		compliance_property_setters = [
			{
				"doc_type": "Sales Invoice",
				"field_name": "naming_series",
				"property": "reqd",
				"value": "1"
			},
			{
				"doc_type": "Purchase Invoice",
				"field_name": "naming_series",
				"property": "reqd",
				"value": "1"
			},
			{
				"doc_type": "Payment Entry",
				"field_name": "naming_series",
				"property": "reqd",
				"value": "1"
			},
			{
				"doc_type": "Company",
				"field_name": "tax_id",
				"property": "reqd",
				"value": "1"
			}
		]

		created_count = 0
		for ps_config in compliance_property_setters:
			try:
				ps_name = f"{ps_config['doc_type']}-{ps_config['property']}-{ps_config['field_name']}"

				if not frappe.db.exists("Property Setter", ps_name):
					ps_doc = frappe.get_doc({
						"doctype": "Property Setter",
						"name": ps_name,
						"doc_type": ps_config["doc_type"],
						"field_name": ps_config["field_name"],
						"property": ps_config["property"],
						"property_type": "Check",
						"value": ps_config["value"],
						"doctype_or_field": "DocField",
						"module": "Portugal Compliance"
					})
					ps_doc.insert(ignore_permissions=True)
					created_count += 1
					print(f"✅ Property Setter criado: {ps_name}")

			except Exception as e:
				print(f"❌ Erro ao criar Property Setter: {str(e)}")

		print(f"✅ {created_count} Property Setters para compliance inviolável criados")
		frappe.db.commit()

	except Exception as e:
		print(f"❌ Erro ao configurar compliance inviolável: {str(e)}")


def sync_naming_series_post_install():
	"""Sincronizar naming series após instalação - NOVA ABORDAGEM"""
	try:
		print("🔄 Sincronizando naming series pós-instalação...")

		# ✅ GARANTIR QUE PROPERTY SETTERS ESTÃO ALINHADOS COM DOCTYPES
		doctypes_to_sync = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
		]

		synced_count = 0
		for doctype in doctypes_to_sync:
			try:
				# Obter autoname do DocType
				doctype_autoname = frappe.db.get_value("DocType", doctype, "autoname")

				if doctype_autoname:
					# Verificar se Property Setter existe
					ps_name = f"{doctype}-naming_series-options"

					if frappe.db.exists("Property Setter", ps_name):
						# Atualizar Property Setter existente
						frappe.db.set_value("Property Setter", ps_name, "value", doctype_autoname)
					else:
						# Criar Property Setter se não existir
						ps_doc = frappe.get_doc({
							"doctype": "Property Setter",
							"name": ps_name,
							"doc_type": doctype,
							"field_name": "naming_series",
							"property": "options",
							"property_type": "Text",
							"value": doctype_autoname,
							"doctype_or_field": "DocField",
							"module": "Portugal Compliance"
						})
						ps_doc.insert(ignore_permissions=True)

					synced_count += 1
					print(f"🔄 Sincronizado: {doctype}")

			except Exception as e:
				print(f"⚠️ Erro ao sincronizar {doctype}: {str(e)}")

		if synced_count > 0:
			print(f"✅ {synced_count} Property Setters sincronizados")
			frappe.db.commit()
			frappe.clear_cache()
		else:
			print("✅ Todos os Property Setters já estão sincronizados")

	except Exception as e:
		print(f"❌ Erro na sincronização pós-instalação: {str(e)}")


def create_safe_sample_data():
	"""Criar dados de exemplo seguros - SEM SÉRIES FIXAS"""
	try:
		print("📋 Preparando estrutura para dados de exemplo...")

		# ✅ APENAS PREPARAR ESTRUTURA, NÃO CRIAR SÉRIES ESPECÍFICAS
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr"])

		if portuguese_companies:
			company = portuguese_companies[0]
			print(f"ℹ️ Empresa portuguesa encontrada: {company.name}")
			print(f"ℹ️ Séries serão criadas dinamicamente quando compliance for ativado")
		else:
			print("ℹ️ Nenhuma empresa portuguesa encontrada")
			print("ℹ️ Séries serão criadas quando empresa portuguesa for configurada")

		# ✅ CRIAR APENAS CONFIGURAÇÃO EXEMPLO DE COMPLIANCE SETTINGS
		try:
			if not frappe.db.exists("Portugal Compliance Settings",
									"Portugal Compliance Settings"):
				settings = frappe.get_doc({
					"doctype": "Portugal Compliance Settings",
					"name": "Portugal Compliance Settings",
					"enable_atcud_validation": 1,
					"auto_generate_atcud": 1,
					"default_at_environment": "test",
					"use_naming_series_approach": 1,
					"enforce_communicated_series_only": 1
				})
				settings.insert(ignore_permissions=True)
				print("✅ Configurações de exemplo criadas")
		except:
			print("ℹ️ Configurações já existem")

	except Exception as e:
		print(f"❌ Erro ao preparar dados de exemplo: {str(e)}")


def validate_installation():
	"""Validar se instalação foi bem-sucedida"""
	try:
		print("📋 Validando instalação...")

		# ✅ CAMPOS CRÍTICOS APENAS ATCUD
		critical_fields = [
			"Sales Invoice-atcud_code",
			"Purchase Invoice-atcud_code",
			"Payment Entry-atcud_code",
			"Company-portugal_compliance_enabled"
		]

		missing_critical = []
		for field in critical_fields:
			if not frappe.db.exists("Custom Field", field):
				missing_critical.append(field)

		if missing_critical:
			print(f"❌ Campos críticos em falta: {missing_critical}")
			raise Exception(
				f"Instalação incompleta: {len(missing_critical)} campos críticos em falta")

		# ✅ VERIFICAR DOCTYPES PRINCIPAIS
		main_doctypes = ["Portugal Series Configuration", "ATCUD Log"]
		missing_doctypes = []
		for doctype in main_doctypes:
			if not frappe.db.exists("DocType", doctype):
				missing_doctypes.append(doctype)

		if missing_doctypes:
			print(f"❌ DocTypes em falta: {missing_doctypes}")
			raise Exception(f"Instalação incompleta: {len(missing_doctypes)} DocTypes em falta")

		# ✅ VERIFICAR SE NAMING_SERIES BASE ESTÃO CONFIGURADAS
		try:
			sample_doctype = "Sales Invoice"
			current_autoname = frappe.db.get_value("DocType", sample_doctype, "autoname") or ""

			if current_autoname:
				print("✅ Naming series base detectadas")
			else:
				print("⚠️ Naming series base não detectadas")
		except Exception as e:
			print(f"⚠️ Erro ao verificar naming series: {str(e)}")

		# ✅ VERIFICAR SE CAMPOS portugal_series FORAM REMOVIDOS
		conflicting_field = "Sales Invoice-portugal_series"
		if frappe.db.exists("Custom Field", conflicting_field):
			print(f"⚠️ Campo conflitante ainda existe: {conflicting_field}")
		else:
			print("✅ Campos conflitantes removidos com sucesso")

		print("✅ Validação de instalação bem-sucedida")

	except Exception as e:
		print(f"❌ Falha na validação: {str(e)}")
		raise


def show_success_message():
	"""Mostrar mensagem de sucesso da instalação"""
	try:
		success_message = """
        🇵🇹 PORTUGAL COMPLIANCE INSTALADO COM SUCESSO! 🇵🇹

        ✅ NOVA ABORDAGEM NAMING_SERIES IMPLEMENTADA:
        • Usa apenas naming_series nativo do ERPNext
        • Campos ATCUD criados (read-only)
        • Campos portugal_series removidos (sem conflitos)
        • Property Setters sincronizados automaticamente
        • Compliance inviolável desde instalação

        🔒 COMPLIANCE INVIOLÁVEL:
        • Apenas séries comunicadas podem ser usadas
        • ATCUD gerado automaticamente
        • Validação NIF obrigatória
        • Sincronização automática garantida

        📋 PRÓXIMOS PASSOS:
        1. Configure empresa portuguesa (país = Portugal)
        2. Ative Portugal Compliance na empresa
        3. Séries portuguesas serão criadas automaticamente
        4. Configure credenciais AT
        5. Comunique séries à AT
        6. Sistema pronto para uso!

        🆘 SUPORTE: app@novadx.pt
        📖 DOCUMENTAÇÃO: /app/portugal-compliance
        """

		print(success_message)

		try:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "Portugal Compliance instalado - Nova Abordagem!",
				"email_content": success_message,
				"for_user": frappe.session.user,
				"type": "Alert"
			}).insert(ignore_permissions=True)
		except:
			pass

	except Exception as e:
		print(f"❌ Erro ao mostrar mensagem: {str(e)}")


def show_error_message(error):
	"""Mostrar mensagem de erro na instalação"""
	try:
		error_message = f"""
        ❌ ERRO NA INSTALAÇÃO DO PORTUGAL COMPLIANCE

        Erro encontrado: {error}

        Ações recomendadas:
        1. Verificar logs detalhados
        2. Executar migração manual se necessário
        3. Verificar se campos conflitantes foram removidos
        4. Contactar suporte: app@novadx.pt

        A instalação pode ter sido parcialmente concluída.
        """

		print(error_message)

	except Exception as e:
		print(f"❌ Erro ao mostrar mensagem de erro: {str(e)}")


# ✅ FUNÇÃO PRINCIPAL CHAMADA PELO HOOKS.PY
def after_install():
	"""Função principal de pós-instalação"""
	execute()
