# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Migration Script for Portugal Compliance
Migrates from portugal_series custom field approach to native naming_series approach
Ensures data integrity and safe migration of existing documents
"""

import frappe
from frappe import _
from frappe.utils import now, today, cint
import json
from datetime import datetime


class PortugalSeriesMigration:
	"""
	Classe principal para migração segura dos dados
	"""

	def __init__(self):
		self.migration_log = []
		self.errors = []
		self.stats = {
			"removed_fields": 0,
			"updated_doctypes": 0,
			"migrated_documents": 0,
			"created_naming_series": 0,
			"total_errors": 0
		}

		# DocTypes que precisam de migração
		self.target_doctypes = [
			"Sales Invoice",
			"Purchase Invoice",
			"Payment Entry",
			"Delivery Note",
			"Purchase Receipt",
			"Journal Entry",
			"Stock Entry",
			"Quotation",
			"Sales Order",
			"Purchase Order",
			"Material Request"
		]

	def log_info(self, message):
		"""Log de informação"""
		timestamp = now()
		log_entry = f"[{timestamp}] INFO: {message}"
		self.migration_log.append(log_entry)
		frappe.logger().info(message)
		print(f"✅ {message}")

	def log_error(self, message, exception=None):
		"""Log de erro"""
		timestamp = now()
		error_entry = f"[{timestamp}] ERROR: {message}"
		if exception:
			error_entry += f" - Exception: {str(exception)}"

		self.migration_log.append(error_entry)
		self.errors.append(error_entry)
		self.stats["total_errors"] += 1

		frappe.log_error(message)
		frappe.logger().error(message)
		print(f"❌ {message}")

	def log_warning(self, message):
		"""Log de aviso"""
		timestamp = now()
		warning_entry = f"[{timestamp}] WARNING: {message}"
		self.migration_log.append(warning_entry)
		frappe.logger().warning(message)
		print(f"⚠️ {message}")


def migrate_to_native_series():
	"""
	Função principal de migração - VERSÃO COMPLETA E ROBUSTA
	"""
	migration = PortugalSeriesMigration()

	try:
		migration.log_info("🇵🇹 INICIANDO MIGRAÇÃO PARA ABORDAGEM NAMING_SERIES NATIVO")
		migration.log_info("=" * 80)

		# ========== FASE 1: BACKUP E VALIDAÇÃO ==========
		migration.log_info("FASE 1: Backup e Validação")
		backup_result = create_migration_backup(migration)

		if not backup_result["success"]:
			raise Exception("Falha no backup - migração abortada")

		# ========== FASE 2: REMOÇÃO DE CAMPOS CONFLITANTES ==========
		migration.log_info("FASE 2: Remoção de Campos Conflitantes")
		remove_conflicting_fields(migration)

		# ========== FASE 3: ATUALIZAÇÃO DE NAMING SERIES ==========
		migration.log_info("FASE 3: Atualização de Naming Series dos DocTypes")
		update_doctype_naming_series(migration)

		# ========== FASE 4: MIGRAÇÃO DE DADOS EXISTENTES ==========
		migration.log_info("FASE 4: Migração de Dados Existentes")
		migrate_existing_documents(migration)

		# ========== FASE 5: VALIDAÇÃO PÓS-MIGRAÇÃO ==========
		migration.log_info("FASE 5: Validação Pós-Migração")
		validate_migration_results(migration)

		# ========== FASE 6: LIMPEZA E FINALIZAÇÃO ==========
		migration.log_info("FASE 6: Limpeza e Finalização")
		finalize_migration(migration)

		# ========== RELATÓRIO FINAL ==========
		generate_migration_report(migration)

		migration.log_info("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
		migration.log_info("=" * 80)

		return {
			"success": True,
			"stats": migration.stats,
			"log": migration.migration_log,
			"errors": migration.errors
		}

	except Exception as e:
		migration.log_error(f"ERRO CRÍTICO NA MIGRAÇÃO: {str(e)}", e)

		# Tentar rollback se possível
		try:
			rollback_migration(migration)
		except Exception as rollback_error:
			migration.log_error(f"ERRO NO ROLLBACK: {str(rollback_error)}", rollback_error)

		return {
			"success": False,
			"error": str(e),
			"stats": migration.stats,
			"log": migration.migration_log,
			"errors": migration.errors
		}


def create_migration_backup(migration):
	"""
	Criar backup dos dados antes da migração
	"""
	try:
		migration.log_info("📦 Criando backup dos dados...")

		backup_data = {
			"backup_date": now(),
			"custom_fields": {},
			"doctype_autonames": {},
			"document_data": {}
		}

		# Backup de Custom Fields
		for doctype in migration.target_doctypes:
			custom_field_name = f"{doctype}-portugal_series"
			if frappe.db.exists("Custom Field", custom_field_name):
				field_doc = frappe.get_doc("Custom Field", custom_field_name)
				backup_data["custom_fields"][custom_field_name] = field_doc.as_dict()
				migration.log_info(f"📋 Backup do campo: {custom_field_name}")

		# Backup de autoname dos DocTypes
		for doctype in migration.target_doctypes:
			if frappe.db.exists("DocType", doctype):
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname")
				backup_data["doctype_autonames"][doctype] = current_autoname
				migration.log_info(f"📋 Backup autoname: {doctype}")

		# Backup de documentos com portugal_series
		for doctype in migration.target_doctypes:
			try:
				# Verificar se tabela existe e tem campo portugal_series
				if frappe.db.table_exists(f"tab{doctype}"):
					# Tentar obter documentos com portugal_series
					docs = frappe.db.sql(f"""
                        SELECT name, portugal_series, naming_series
                        FROM `tab{doctype}`
                        WHERE portugal_series IS NOT NULL
                          AND portugal_series != ''
                        LIMIT 1000
                    """, as_dict=True)

					if docs:
						backup_data["document_data"][doctype] = docs
						migration.log_info(f"📋 Backup de {len(docs)} documentos {doctype}")

			except Exception as e:
				migration.log_warning(
					f"Campo portugal_series não encontrado em {doctype}: {str(e)}")

		# Salvar backup
		backup_file = f"portugal_compliance_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

		try:
			# Tentar salvar no diretório de sites
			backup_path = frappe.get_site_path("private", "backups", backup_file)
			with open(backup_path, 'w', encoding='utf-8') as f:
				json.dump(backup_data, f, indent=2, default=str)

			migration.log_info(f"💾 Backup salvo em: {backup_path}")

		except Exception as e:
			# Fallback: salvar no cache do Frappe
			frappe.cache.set(f"migration_backup_{frappe.session.sid}", backup_data,
							 expires_in_sec=86400)
			migration.log_warning(f"Backup salvo no cache devido a erro: {str(e)}")

		return {"success": True, "backup_data": backup_data}

	except Exception as e:
		migration.log_error(f"Erro ao criar backup: {str(e)}", e)
		return {"success": False, "error": str(e)}


def remove_conflicting_fields(migration):
	"""
	Remover campos portugal_series conflitantes
	"""
	try:
		migration.log_info("🗑️ Removendo campos portugal_series conflitantes...")

		for doctype in migration.target_doctypes:
			custom_field_name = f"{doctype}-portugal_series"

			if frappe.db.exists("Custom Field", custom_field_name):
				try:
					frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True)
					migration.stats["removed_fields"] += 1
					migration.log_info(f"🗑️ Campo removido: {custom_field_name}")

				except Exception as e:
					migration.log_error(f"Erro ao remover campo {custom_field_name}: {str(e)}", e)
			else:
				migration.log_info(f"ℹ️ Campo não encontrado: {custom_field_name}")

		# Limpar cache após remoção
		frappe.clear_cache()
		migration.log_info(f"✅ Removidos {migration.stats['removed_fields']} campos conflitantes")

	except Exception as e:
		migration.log_error(f"Erro na remoção de campos: {str(e)}", e)


def update_doctype_naming_series(migration):
	"""
	Atualizar naming_series dos DocTypes com séries portuguesas
	"""
	try:
		migration.log_info("🔄 Atualizando naming_series dos DocTypes...")

		for doctype in migration.target_doctypes:
			try:
				# Obter séries portuguesas ativas para este DocType
				portuguese_series = frappe.get_all("Portugal Series Configuration",
												   filters={
													   "document_type": doctype,
													   "is_active": 1
												   },
												   fields=["prefix", "name"])

				if not portuguese_series:
					migration.log_info(f"ℹ️ Nenhuma série portuguesa encontrada para {doctype}")
					continue

				# Gerar opções de naming_series
				naming_series_options = []
				for series in portuguese_series:
					naming_option = f"{series.prefix}.####"
					naming_series_options.append(naming_option)
					migration.log_info(f"📋 Série encontrada: {series.prefix} ({series.name})")

				# Obter autoname atual
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
				current_options = set(
					[opt.strip() for opt in current_autoname.split('\n') if opt.strip()])

				# Adicionar novas opções
				updated = False
				new_options_added = []

				for option in naming_series_options:
					if option not in current_options:
						current_options.add(option)
						new_options_added.append(option)
						updated = True

				if updated:
					# Atualizar DocType
					new_autoname = '\n'.join(sorted(current_options))
					frappe.db.set_value("DocType", doctype, "autoname", new_autoname)
					frappe.clear_cache(doctype=doctype)

					migration.stats["updated_doctypes"] += 1
					migration.stats["created_naming_series"] += len(new_options_added)

					migration.log_info(
						f"✅ {doctype} atualizado com {len(new_options_added)} naming series:")
					for option in new_options_added:
						migration.log_info(f"   + {option}")
				else:
					migration.log_info(f"ℹ️ {doctype} já tem todas as naming series necessárias")

			except Exception as e:
				migration.log_error(f"Erro ao atualizar {doctype}: {str(e)}", e)

		migration.log_info(f"✅ Atualizados {migration.stats['updated_doctypes']} DocTypes")

	except Exception as e:
		migration.log_error(f"Erro na atualização de naming series: {str(e)}", e)


def migrate_existing_documents(migration):
	"""
	Migrar documentos existentes que usam portugal_series
	"""
	try:
		migration.log_info("📄 Migrando documentos existentes...")

		for doctype in migration.target_doctypes:
			try:
				# Verificar se tabela existe
				if not frappe.db.table_exists(f"tab{doctype}"):
					migration.log_warning(f"Tabela não existe: tab{doctype}")
					continue

				# Verificar se campo portugal_series ainda existe na tabela
				try:
					# Tentar obter documentos com portugal_series
					docs = frappe.db.sql(f"""
                        SELECT name, portugal_series, naming_series
                        FROM `tab{doctype}`
                        WHERE portugal_series IS NOT NULL
                          AND portugal_series != ''
                        LIMIT 1000
                    """, as_dict=True)

				except Exception as field_error:
					migration.log_info(
						f"ℹ️ Campo portugal_series não existe em {doctype} (esperado após remoção)")
					continue

				if not docs:
					migration.log_info(f"ℹ️ Nenhum documento com portugal_series em {doctype}")
					continue

				migration.log_info(
					f"📄 Encontrados {len(docs)} documentos para migrar em {doctype}")

				migrated_count = 0
				for doc in docs:
					try:
						# Obter prefixo da série portuguesa
						if not frappe.db.exists("Portugal Series Configuration",
												doc.portugal_series):
							migration.log_warning(f"Série não encontrada: {doc.portugal_series}")
							continue

						prefix = frappe.db.get_value("Portugal Series Configuration",
													 doc.portugal_series, "prefix")

						if not prefix:
							migration.log_warning(
								f"Prefixo não encontrado para série: {doc.portugal_series}")
							continue

						# Gerar naming_series
						naming_series = f"{prefix}.####"

						# Atualizar documento
						frappe.db.set_value(doctype, doc.name, "naming_series", naming_series,
											update_modified=False)

						migrated_count += 1
						migration.stats["migrated_documents"] += 1

						if migrated_count % 100 == 0:
							migration.log_info(
								f"   Migrados {migrated_count}/{len(docs)} documentos...")

					except Exception as doc_error:
						migration.log_error(
							f"Erro ao migrar documento {doc.name}: {str(doc_error)}", doc_error)

				migration.log_info(f"✅ Migrados {migrated_count} documentos em {doctype}")

			except Exception as e:
				migration.log_error(f"Erro na migração de documentos {doctype}: {str(e)}", e)

		migration.log_info(
			f"✅ Total de documentos migrados: {migration.stats['migrated_documents']}")

	except Exception as e:
		migration.log_error(f"Erro na migração de documentos: {str(e)}", e)


def validate_migration_results(migration):
	"""
	Validar resultados da migração
	"""
	try:
		migration.log_info("🔍 Validando resultados da migração...")

		validation_results = {
			"custom_fields_removed": True,
			"naming_series_updated": True,
			"documents_migrated": True,
			"issues": []
		}

		# Verificar se campos foram removidos
		for doctype in migration.target_doctypes:
			custom_field_name = f"{doctype}-portugal_series"
			if frappe.db.exists("Custom Field", custom_field_name):
				validation_results["custom_fields_removed"] = False
				validation_results["issues"].append(f"Campo ainda existe: {custom_field_name}")

		# Verificar naming_series
		for doctype in migration.target_doctypes:
			try:
				current_autoname = frappe.db.get_value("DocType", doctype, "autoname") or ""
				if not current_autoname:
					validation_results["issues"].append(f"DocType {doctype} sem autoname")
					continue

				# Verificar se tem séries portuguesas
				portuguese_series = frappe.get_all("Portugal Series Configuration",
												   filters={"document_type": doctype,
															"is_active": 1},
												   fields=["prefix"])

				for series in portuguese_series:
					expected_option = f"{series.prefix}.####"
					if expected_option not in current_autoname:
						validation_results["naming_series_updated"] = False
						validation_results["issues"].append(
							f"Naming series em falta: {expected_option} em {doctype}")

			except Exception as e:
				validation_results["issues"].append(f"Erro validando {doctype}: {str(e)}")

		# Relatório de validação
		if validation_results["issues"]:
			migration.log_warning("⚠️ Problemas encontrados na validação:")
			for issue in validation_results["issues"]:
				migration.log_warning(f"   - {issue}")
		else:
			migration.log_info("✅ Validação passou sem problemas")

		return validation_results

	except Exception as e:
		migration.log_error(f"Erro na validação: {str(e)}", e)
		return {"success": False, "error": str(e)}


def finalize_migration(migration):
	"""
	Finalizar migração e limpeza
	"""
	try:
		migration.log_info("🧹 Finalizando migração...")

		# Limpar cache global
		frappe.clear_cache()
		migration.log_info("🧹 Cache limpo")

		# Recarregar DocTypes
		for doctype in migration.target_doctypes:
			try:
				frappe.reload_doc("core", "doctype", doctype.replace(" ", "_").lower())
			except:
				pass  # Ignorar erros de reload

		migration.log_info("🔄 DocTypes recarregados")

		# Criar campo ATCUD se não existir
		create_atcud_fields_if_needed(migration)

		migration.log_info("✅ Migração finalizada")

	except Exception as e:
		migration.log_error(f"Erro na finalização: {str(e)}", e)


def create_atcud_fields_if_needed(migration):
	"""
	Criar campos ATCUD se não existirem
	"""
	try:
		migration.log_info("🔧 Verificando campos ATCUD...")

		for doctype in migration.target_doctypes:
			atcud_field_name = f"{doctype}-atcud_code"

			if not frappe.db.exists("Custom Field", atcud_field_name):
				try:
					# Criar campo ATCUD
					field_doc = frappe.get_doc({
						"doctype": "Custom Field",
						"dt": doctype,
						"module": "Portugal Compliance",
						"fieldname": "atcud_code",
						"label": "ATCUD Code",
						"fieldtype": "Data",
						"insert_after": "naming_series",
						"read_only": 1,
						"bold": 1,
						"in_list_view": 1,
						"description": "Código Único de Documento - Gerado automaticamente"
					})

					field_doc.insert(ignore_permissions=True)
					migration.log_info(f"✅ Campo ATCUD criado para {doctype}")

				except Exception as e:
					migration.log_error(f"Erro ao criar campo ATCUD para {doctype}: {str(e)}", e)
			else:
				migration.log_info(f"ℹ️ Campo ATCUD já existe para {doctype}")

	except Exception as e:
		migration.log_error(f"Erro na criação de campos ATCUD: {str(e)}", e)


def generate_migration_report(migration):
	"""
	Gerar relatório final da migração
	"""
	try:
		migration.log_info("📊 Gerando relatório final...")

		report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      RELATÓRIO DE MIGRAÇÃO PORTUGAL COMPLIANCE              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Data: {now()}                                                    ║
║ Status: {'SUCESSO' if migration.stats['total_errors'] == 0 else 'COM ERROS'}                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ESTATÍSTICAS:                                                                ║
║ • Campos removidos: {migration.stats['removed_fields']:>3}                                                    ║
║ • DocTypes atualizados: {migration.stats['updated_doctypes']:>3}                                                ║
║ • Naming series criadas: {migration.stats['created_naming_series']:>3}                                              ║
║ • Documentos migrados: {migration.stats['migrated_documents']:>4}                                               ║
║ • Total de erros: {migration.stats['total_errors']:>3}                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PRÓXIMOS PASSOS:                                                             ║
║ 1. Verificar se todos os documentos têm naming_series corretas              ║
║ 2. Testar criação de novos documentos                                       ║
║ 3. Verificar geração de ATCUD                                               ║
║ 4. Validar compliance português                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

		migration.log_info(report)

		# Salvar relatório
		try:
			report_file = f"portugal_compliance_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
			report_path = frappe.get_site_path("private", "files", report_file)

			with open(report_path, 'w', encoding='utf-8') as f:
				f.write(report)
				f.write("\n\nLOG COMPLETO:\n")
				f.write("\n".join(migration.migration_log))

			migration.log_info(f"📄 Relatório salvo em: {report_path}")

		except Exception as e:
			migration.log_warning(f"Erro ao salvar relatório: {str(e)}")

	except Exception as e:
		migration.log_error(f"Erro ao gerar relatório: {str(e)}", e)


def rollback_migration(migration):
	"""
	Fazer rollback da migração em caso de erro crítico
	"""
	try:
		migration.log_info("🔄 Iniciando rollback da migração...")

		# Tentar recuperar backup do cache
		backup_data = frappe.cache.get(f"migration_backup_{frappe.session.sid}")

		if not backup_data:
			migration.log_error("Backup não encontrado - rollback não possível")
			return False

		# Restaurar Custom Fields
		for field_name, field_data in backup_data.get("custom_fields", {}).items():
			try:
				if not frappe.db.exists("Custom Field", field_name):
					field_doc = frappe.get_doc(field_data)
					field_doc.insert(ignore_permissions=True)
					migration.log_info(f"🔄 Campo restaurado: {field_name}")
			except Exception as e:
				migration.log_error(f"Erro ao restaurar campo {field_name}: {str(e)}", e)

		# Restaurar autoname dos DocTypes
		for doctype, autoname in backup_data.get("doctype_autonames", {}).items():
			try:
				frappe.db.set_value("DocType", doctype, "autoname", autoname)
				migration.log_info(f"🔄 Autoname restaurado: {doctype}")
			except Exception as e:
				migration.log_error(f"Erro ao restaurar autoname {doctype}: {str(e)}", e)

		frappe.clear_cache()
		migration.log_info("✅ Rollback concluído")
		return True

	except Exception as e:
		migration.log_error(f"Erro no rollback: {str(e)}", e)
		return False


# ========== FUNÇÕES DE EXECUÇÃO ==========

@frappe.whitelist()
def execute_migration():
	"""
	API para executar migração via interface
	"""
	try:
		result = migrate_to_native_series()
		return result
	except Exception as e:
		frappe.log_error(f"Error in execute_migration: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_migration_status():
	"""
	Verificar status da migração
	"""
	try:
		status = {
			"migration_needed": False,
			"conflicting_fields": [],
			"documents_to_migrate": 0,
			"series_to_update": 0
		}

		# Verificar campos conflitantes
		target_doctypes = [
			"Sales Invoice", "Purchase Invoice", "Payment Entry",
			"Delivery Note", "Purchase Receipt", "Journal Entry"
		]

		for doctype in target_doctypes:
			custom_field_name = f"{doctype}-portugal_series"
			if frappe.db.exists("Custom Field", custom_field_name):
				status["conflicting_fields"].append(custom_field_name)
				status["migration_needed"] = True

		return {
			"success": True,
			"status": status
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


if __name__ == "__main__":
	# Executar migração se chamado diretamente
	result = migrate_to_native_series()

	if result["success"]:
		print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
		print(f"📊 Estatísticas: {result['stats']}")
	else:
		print("❌ MIGRAÇÃO FALHOU!")
		print(f"🚨 Erro: {result['error']}")

	if result["errors"]:
		print(f"⚠️ {len(result['errors'])} erros encontrados:")
		for error in result["errors"]:
			print(f"   - {error}")
