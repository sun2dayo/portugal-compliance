# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import os
import json
from datetime import datetime


def execute():
	"""Executado antes da desinstalação do Portugal Compliance - VERSÃO COMPLETA"""
	try:
		print("🇵🇹 Iniciando desinstalação do Portugal Compliance...")

		# 1. Criar backup completo antes da remoção
		create_uninstall_backup()

		# 2. ✅ INTEGRAÇÃO: Usar field_management para limpeza
		cleanup_custom_fields_via_field_management()

		# 3. ✅ INTEGRAÇÃO: Usar series_adapter para limpeza
		cleanup_naming_series_via_series_adapter()

		# 4. Limpar dados específicos do módulo
		cleanup_module_data()

		# 5. Remover configurações personalizadas
		cleanup_custom_configurations()

		# 6. Limpar permissões e roles
		cleanup_permissions_and_roles()

		# 7. Limpar arquivos e cache
		cleanup_files_and_cache()

		# 8. Validar limpeza completa
		validate_cleanup()

		# 9. Mostrar relatório de desinstalação
		show_uninstall_report()

		print("✅ Desinstalação do Portugal Compliance concluída com sucesso!")

	except Exception as e:
		frappe.log_error(f"Erro na desinstalação do Portugal Compliance: {str(e)}")
		print(f"❌ Erro na desinstalação: {str(e)}")
		# Não fazer raise para não impedir a desinstalação
		show_error_report(str(e))


def create_uninstall_backup():
	"""Criar backup completo antes da desinstalação"""
	try:
		print("📦 Criando backup antes da desinstalação...")

		backup_data = {
			"backup_date": frappe.utils.now(),
			"backup_type": "uninstall",
			"module": "Portugal Compliance",
			"custom_fields": {},
			"doctype_data": {},
			"series_configurations": [],
			"atcud_logs": [],
			"company_settings": {},
			"naming_series_backup": {}
		}

		# Backup de Custom Fields
		portugal_fields = frappe.get_all("Custom Field",
										 filters={"module": "Portugal Compliance"},
										 fields=["name", "dt", "fieldname", "label", "fieldtype"])

		for field in portugal_fields:
			field_doc = frappe.get_doc("Custom Field", field.name)
			backup_data["custom_fields"][field.name] = field_doc.as_dict()

		print(f"📋 Backup de {len(portugal_fields)} custom fields")

		# Backup de Portugal Series Configuration
		series_configs = frappe.get_all("Portugal Series Configuration",
										fields=["*"])
		backup_data["series_configurations"] = series_configs
		print(f"📋 Backup de {len(series_configs)} séries portuguesas")

		# Backup de ATCUD Logs (últimos 1000)
		atcud_logs = frappe.get_all("ATCUD Log",
									fields=["*"],
									order_by="creation desc",
									limit=1000)
		backup_data["atcud_logs"] = atcud_logs
		print(f"📋 Backup de {len(atcud_logs)} logs ATCUD")

		# Backup de configurações de empresas
		companies_with_compliance = frappe.get_all("Company",
												   filters={"portugal_compliance_enabled": 1},
												   fields=["name", "portugal_compliance_enabled",
														   "at_certificate_number"])
		backup_data["company_settings"] = companies_with_compliance
		print(f"📋 Backup de {len(companies_with_compliance)} empresas com compliance")

		# Backup de naming series dos DocTypes
		target_doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry",
			"Stock Entry", "Quotation", "Sales Order", "Purchase Order",
			"Material Request"
		]

		for doctype in target_doctypes:
			try:
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname")
				if current_autoname:
					backup_data["naming_series_backup"][doctype] = current_autoname
			except Exception as e:
				print(f"⚠️ Erro ao fazer backup naming series {doctype}: {str(e)}")

		print(f"📋 Backup de naming series de {len(backup_data['naming_series_backup'])} DocTypes")

		# Salvar backup
		try:
			backup_filename = f"portugal_compliance_uninstall_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
			backup_path = frappe.get_site_path("private", "backups", backup_filename)

			# Criar diretório se não existir
			os.makedirs(os.path.dirname(backup_path), exist_ok=True)

			with open(backup_path, 'w', encoding='utf-8') as f:
				json.dump(backup_data, f, indent=2, default=str)

			print(f"💾 Backup salvo em: {backup_path}")

			# Também salvar no cache como fallback
			frappe.cache.set("portugal_compliance_uninstall_backup", backup_data,
							 expires_in_sec=86400)

		except Exception as e:
			print(f"⚠️ Erro ao salvar backup em arquivo: {str(e)}")
			# Salvar apenas no cache
			frappe.cache.set("portugal_compliance_uninstall_backup", backup_data,
							 expires_in_sec=86400)
			print("💾 Backup salvo no cache")

		return backup_data

	except Exception as e:
		print(f"❌ Erro ao criar backup: {str(e)}")
		return {}


def cleanup_custom_fields_via_field_management():
	"""Limpar custom fields usando field_management.py - INTEGRAÇÃO"""
	try:
		print("🗑️ Limpando custom fields via field_management...")

		# ✅ INTEGRAÇÃO: Usar field_management para limpeza
		try:
			from portugal_compliance.utils.field_management import \
				cleanup_portugal_fields_on_uninstall
			result = cleanup_portugal_fields_on_uninstall()

			if result.get("success"):
				print(f"✅ Field management: {result.get('removed_count', 0)} campos removidos")
			else:
				print(f"⚠️ Erro no field management: {result.get('error')}")
				# Fallback para limpeza manual
				cleanup_custom_fields_manual()
		except ImportError:
			print("⚠️ Field management não disponível, usando limpeza manual...")
			cleanup_custom_fields_manual()

	except Exception as e:
		print(f"❌ Erro na limpeza de custom fields: {str(e)}")


def cleanup_custom_fields_manual():
	"""Limpeza manual de custom fields (fallback)"""
	try:
		print("🗑️ Limpeza manual de custom fields...")

		# Remover todos os custom fields do módulo Portugal Compliance
		portugal_fields = frappe.get_all("Custom Field",
										 filters={"module": "Portugal Compliance"},
										 fields=["name", "dt", "fieldname"])

		removed_count = 0
		for field in portugal_fields:
			try:
				frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
				removed_count += 1
				print(f"🗑️ Campo removido: {field.dt}.{field.fieldname}")
			except Exception as e:
				print(f"⚠️ Erro ao remover campo {field.name}: {str(e)}")

		print(f"🗑️ Limpeza manual: {removed_count} campos removidos")

		# Limpar cache após remoção
		frappe.clear_cache()

	except Exception as e:
		print(f"❌ Erro na limpeza manual: {str(e)}")


def cleanup_naming_series_via_series_adapter():
	"""Limpar naming series usando series_adapter.py - INTEGRAÇÃO"""
	try:
		print("🗑️ Limpando naming series via series_adapter...")

		# ✅ INTEGRAÇÃO: Usar series_adapter para limpeza
		try:
			from portugal_compliance.utils.series_adapter import cleanup_naming_series_on_uninstall
			result = cleanup_naming_series_on_uninstall()

			if result.get("success"):
				print(
					f"✅ Series adapter: {result.get('total_removed', 0)} naming series removidas")
			else:
				print(f"⚠️ Erro no series adapter: {result.get('error')}")
				# Fallback para limpeza manual
				cleanup_naming_series_manual()
		except ImportError:
			print("⚠️ Series adapter não disponível, usando limpeza manual...")
			cleanup_naming_series_manual()

	except Exception as e:
		print(f"❌ Erro na limpeza de naming series: {str(e)}")


def cleanup_naming_series_manual():
	"""Limpeza manual de naming series (fallback)"""
	try:
		print("🗑️ Limpeza manual de naming series...")

		# Obter todas as séries portuguesas para identificar naming series
		portuguese_series = frappe.get_all("Portugal Series Configuration",
										   fields=["prefix", "document_type"])

		target_doctypes = set([s.document_type for s in portuguese_series])
		removed_total = 0

		for doctype in target_doctypes:
			try:
				# Obter naming series atuais
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
				current_options = [opt.strip() for opt in current_autoname.split('\n') if
								   opt.strip()]

				# Identificar e remover séries portuguesas
				portuguese_options = []
				for series in portuguese_series:
					if series.document_type == doctype:
						naming_option = f"{series.prefix}.####"
						if naming_option in current_options:
							portuguese_options.append(naming_option)

				if portuguese_options:
					# Remover opções portuguesas
					for option in portuguese_options:
						current_options.remove(option)

					# Atualizar DocType
					new_autoname = '\n'.join(current_options)
					frappe.db.set_value("DocType", doctype, "autoname", new_autoname)
					frappe.clear_cache(doctype=doctype)

					removed_total += len(portuguese_options)
					print(f"🗑️ {doctype}: {len(portuguese_options)} naming series removidas")

			except Exception as e:
				print(f"⚠️ Erro ao limpar naming series {doctype}: {str(e)}")

		print(f"🗑️ Limpeza manual: {removed_total} naming series removidas")

	except Exception as e:
		print(f"❌ Erro na limpeza manual de naming series: {str(e)}")


def cleanup_module_data():
	"""Limpar dados específicos do módulo"""
	try:
		print("🗑️ Limpando dados do módulo...")

		# Lista de DocTypes para limpar (ordem importante para referências)
		doctypes_to_clean = [
			"ATCUD Log",  # Primeiro os logs
			"Portugal Series Configuration"  # Depois as configurações
		]

		total_records_removed = 0

		for doctype in doctypes_to_clean:
			try:
				if frappe.db.exists("DocType", doctype):
					# Contar registros
					count = frappe.db.count(doctype)

					if count > 0:
						# Remover todos os registros
						frappe.db.sql(f"DELETE FROM `tab{doctype}`")
						total_records_removed += count
						print(f"🗑️ {doctype}: {count} registros removidos")
					else:
						print(f"✅ {doctype}: Nenhum registro encontrado")
				else:
					print(f"⚠️ {doctype}: DocType não existe")

			except Exception as e:
				print(f"❌ Erro ao limpar {doctype}: {str(e)}")

		print(f"🗑️ Total de registros removidos: {total_records_removed}")

		# Commit das alterações
		frappe.db.commit()

	except Exception as e:
		print(f"❌ Erro na limpeza de dados do módulo: {str(e)}")


def cleanup_custom_configurations():
	"""Limpar configurações personalizadas"""
	try:
		print("🗑️ Limpando configurações personalizadas...")

		# Remover configurações de empresas
		companies_with_compliance = frappe.get_all("Company",
												   filters={"portugal_compliance_enabled": 1},
												   fields=["name"])

		for company in companies_with_compliance:
			try:
				frappe.db.set_value("Company", company.name, {
					"portugal_compliance_enabled": 0,
					"at_certificate_number": None
				}, update_modified=False)
				print(f"🗑️ Compliance desativado para: {company.name}")
			except Exception as e:
				print(f"⚠️ Erro ao limpar empresa {company.name}: {str(e)}")

		# Remover configurações globais se existirem
		if frappe.db.exists("DocType", "Portugal Compliance Settings"):
			try:
				if frappe.db.exists("Portugal Compliance Settings",
									"Portugal Compliance Settings"):
					frappe.delete_doc("Portugal Compliance Settings",
									  "Portugal Compliance Settings",
									  ignore_permissions=True)
					print("🗑️ Configurações globais removidas")
			except Exception as e:
				print(f"⚠️ Erro ao remover configurações globais: {str(e)}")

		# Remover Property Setters relacionados
		property_setters = frappe.get_all("Property Setter",
										  filters={"module": "Portugal Compliance"},
										  fields=["name"])

		for ps in property_setters:
			try:
				frappe.delete_doc("Property Setter", ps.name, ignore_permissions=True)
				print(f"🗑️ Property Setter removido: {ps.name}")
			except Exception as e:
				print(f"⚠️ Erro ao remover Property Setter {ps.name}: {str(e)}")

	except Exception as e:
		print(f"❌ Erro na limpeza de configurações: {str(e)}")


def cleanup_permissions_and_roles():
	"""Limpar permissões e roles"""
	try:
		print("🗑️ Limpando permissões e roles...")

		# Remover role personalizada
		if frappe.db.exists("Role", "Portugal Compliance User"):
			try:
				# Primeiro remover das atribuições de usuários
				user_roles = frappe.get_all("Has Role",
											filters={"role": "Portugal Compliance User"},
											fields=["name"])

				for ur in user_roles:
					frappe.delete_doc("Has Role", ur.name, ignore_permissions=True)

				# Depois remover a role
				frappe.delete_doc("Role", "Portugal Compliance User", ignore_permissions=True)
				print("🗑️ Role 'Portugal Compliance User' removida")
			except Exception as e:
				print(f"⚠️ Erro ao remover role: {str(e)}")

		# Remover permissões customizadas (se houver)
		custom_perms = frappe.get_all("Custom DocPerm",
									  filters={"module": "Portugal Compliance"},
									  fields=["name"])

		for perm in custom_perms:
			try:
				frappe.delete_doc("Custom DocPerm", perm.name, ignore_permissions=True)
				print(f"🗑️ Permissão customizada removida: {perm.name}")
			except Exception as e:
				print(f"⚠️ Erro ao remover permissão {perm.name}: {str(e)}")

	except Exception as e:
		print(f"❌ Erro na limpeza de permissões: {str(e)}")


def cleanup_files_and_cache():
	"""Limpar arquivos e cache"""
	try:
		print("🗑️ Limpando arquivos e cache...")

		# Limpar cache completo
		frappe.clear_cache()
		print("🗑️ Cache limpo")

		# Limpar cache específico do módulo
		cache_keys_to_remove = [
			"portugal_compliance_*",
			"atcud_*",
			"portuguese_series_*"
		]

		for key_pattern in cache_keys_to_remove:
			try:
				# Frappe não tem wildcard delete, então tentamos algumas chaves conhecidas
				specific_keys = [
					"portugal_compliance_settings",
					"atcud_validation_cache",
					"portuguese_series_cache"
				]

				for key in specific_keys:
					frappe.cache.delete(key)
			except Exception as e:
				print(f"⚠️ Erro ao limpar cache {key_pattern}: {str(e)}")

		# Remover arquivos temporários (se existirem)
		try:
			temp_files_path = frappe.get_site_path("private", "files", "portugal_compliance")
			if os.path.exists(temp_files_path):
				import shutil
				shutil.rmtree(temp_files_path)
				print("🗑️ Arquivos temporários removidos")
		except Exception as e:
			print(f"⚠️ Erro ao remover arquivos temporários: {str(e)}")

	except Exception as e:
		print(f"❌ Erro na limpeza de arquivos: {str(e)}")


def validate_cleanup():
	"""Validar se limpeza foi bem-sucedida"""
	try:
		print("🔍 Validando limpeza...")

		validation_results = {
			"custom_fields_remaining": 0,
			"series_configurations_remaining": 0,
			"atcud_logs_remaining": 0,
			"companies_with_compliance": 0,
			"naming_series_remaining": 0,
			"issues": []
		}

		# Verificar custom fields restantes
		remaining_fields = frappe.db.count("Custom Field", {"module": "Portugal Compliance"})
		validation_results["custom_fields_remaining"] = remaining_fields
		if remaining_fields > 0:
			validation_results["issues"].append(f"{remaining_fields} custom fields ainda existem")

		# Verificar séries restantes
		if frappe.db.exists("DocType", "Portugal Series Configuration"):
			remaining_series = frappe.db.count("Portugal Series Configuration")
			validation_results["series_configurations_remaining"] = remaining_series
			if remaining_series > 0:
				validation_results["issues"].append(f"{remaining_series} séries ainda existem")

		# Verificar logs restantes
		if frappe.db.exists("DocType", "ATCUD Log"):
			remaining_logs = frappe.db.count("ATCUD Log")
			validation_results["atcud_logs_remaining"] = remaining_logs
			if remaining_logs > 0:
				validation_results["issues"].append(f"{remaining_logs} logs ATCUD ainda existem")

		# Verificar empresas com compliance
		companies_with_compliance = frappe.db.count("Company", {"portugal_compliance_enabled": 1})
		validation_results["companies_with_compliance"] = companies_with_compliance
		if companies_with_compliance > 0:
			validation_results["issues"].append(
				f"{companies_with_compliance} empresas ainda têm compliance ativo")

		# Verificar naming series portuguesas restantes
		target_doctypes = ["Sales Invoice", "Purchase Invoice", "Payment Entry"]
		portuguese_naming_count = 0

		for doctype in target_doctypes:
			try:
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
				# Procurar por padrões portugueses
				if "FT-" in current_autoname or "NC-" in current_autoname or "RC-" in current_autoname:
					portuguese_naming_count += 1
			except Exception:
				pass

		validation_results["naming_series_remaining"] = portuguese_naming_count
		if portuguese_naming_count > 0:
			validation_results["issues"].append(
				f"{portuguese_naming_count} DocTypes ainda têm naming series portuguesas")

		# Relatório de validação
		if validation_results["issues"]:
			print("⚠️ Problemas encontrados na validação:")
			for issue in validation_results["issues"]:
				print(f"   - {issue}")
		else:
			print("✅ Validação passou - limpeza completa")

		return validation_results

	except Exception as e:
		print(f"❌ Erro na validação: {str(e)}")
		return {"error": str(e)}


def show_uninstall_report():
	"""Mostrar relatório de desinstalação"""
	try:
		validation = validate_cleanup()

		report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RELATÓRIO DE DESINSTALAÇÃO PORTUGAL COMPLIANCE           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Data: {frappe.utils.now()}                                      ║
║ Status: {'SUCESSO' if not validation.get('issues') else 'COM PENDÊNCIAS'}                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ITENS REMOVIDOS:                                                             ║
║ ✅ Custom Fields do módulo Portugal Compliance                              ║
║ ✅ Naming series portuguesas dos DocTypes                                   ║
║ ✅ Configurações de séries documentais                                      ║
║ ✅ Logs ATCUD                                                               ║
║ ✅ Configurações de empresas                                                ║
║ ✅ Roles e permissões personalizadas                                        ║
║ ✅ Cache e arquivos temporários                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ESTATÍSTICAS FINAIS:                                                         ║
║ • Custom Fields restantes: {validation.get('custom_fields_remaining', 0):>3}                                      ║
║ • Séries restantes: {validation.get('series_configurations_remaining', 0):>3}                                           ║
║ • Logs ATCUD restantes: {validation.get('atcud_logs_remaining', 0):>3}                                         ║
║ • Empresas com compliance: {validation.get('companies_with_compliance', 0):>3}                                    ║
║ • DocTypes com naming PT: {validation.get('naming_series_remaining', 0):>3}                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ BACKUP CRIADO:                                                               ║
║ 📦 Backup completo salvo antes da remoção                                   ║
║ 📁 Localização: private/backups/                                            ║
║ 💾 Cache: portugal_compliance_uninstall_backup                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ INTEGRAÇÃO FIELD_MANAGEMENT:                                                 ║
║ ✅ Limpeza automática via field_management.py                               ║
║ ✅ Remoção segura de todos os custom fields                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ INTEGRAÇÃO SERIES_ADAPTER:                                                   ║
║ ✅ Limpeza automática via series_adapter.py                                 ║
║ ✅ Remoção de naming series portuguesas                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

		print(report)

		# Mostrar issues se houver
		if validation.get("issues"):
			print("\n⚠️ PENDÊNCIAS ENCONTRADAS:")
			for issue in validation["issues"]:
				print(f"   - {issue}")
			print("\nEssas pendências podem ser normais se outros módulos dependem desses dados.")

	except Exception as e:
		print(f"❌ Erro ao gerar relatório: {str(e)}")


def show_error_report(error_message):
	"""Mostrar relatório de erro na desinstalação"""
	try:
		error_report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      ERRO NA DESINSTALAÇÃO PORTUGAL COMPLIANCE              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Data: {frappe.utils.now()}                                      ║
║ Status: ERRO                                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ERRO ENCONTRADO:                                                             ║
║ {error_message[:70]:<70} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ AÇÕES RECOMENDADAS:                                                          ║
║ 1. Verificar logs detalhados do sistema                                     ║
║ 2. Executar limpeza manual se necessário                                    ║
║ 3. Contactar suporte: app@novadx.pt                                         ║
║ 4. Backup foi criado antes do erro                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ BACKUP DISPONÍVEL:                                                           ║
║ 📦 Cache: portugal_compliance_uninstall_backup                              ║
║ 📁 Arquivo: private/backups/portugal_compliance_uninstall_backup_*.json     ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

		print(error_report)

	except Exception as e:
		print(f"❌ Erro ao mostrar relatório de erro: {str(e)}")


# Função principal chamada pelo hooks.py
def before_uninstall():
	"""Função principal de pré-desinstalação"""
	execute()


# ✅ FUNÇÕES AUXILIARES PARA LIMPEZA MANUAL (SE NECESSÁRIO)

def manual_cleanup_all():
	"""Limpeza manual completa (para uso em caso de emergência)"""
	try:
		print("🆘 Executando limpeza manual completa...")

		# Executar todas as funções de limpeza
		cleanup_custom_fields_manual()
		cleanup_naming_series_manual()
		cleanup_module_data()
		cleanup_custom_configurations()
		cleanup_permissions_and_roles()
		cleanup_files_and_cache()

		print("✅ Limpeza manual completa concluída")

	except Exception as e:
		print(f"❌ Erro na limpeza manual: {str(e)}")


@frappe.whitelist()
def emergency_cleanup():
	"""API para limpeza de emergência (apenas System Manager)"""
	if not frappe.has_permission("System Manager"):
		frappe.throw("Acesso negado")

	try:
		manual_cleanup_all()
		return {"success": True, "message": "Limpeza de emergência concluída"}
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_cleanup_status():
	"""API para verificar status de limpeza"""
	try:
		return validate_cleanup()
	except Exception as e:
		return {"error": str(e)}
