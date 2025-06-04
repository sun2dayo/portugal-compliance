# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import os


def execute():
	"""Executado antes da instalação do Portugal Compliance"""
	try:
		print("🇵🇹 Iniciando pré-instalação do Portugal Compliance...")

		# 1. Verificar pré-requisitos do sistema
		check_system_requirements()

		# 2. Verificar versões do Frappe/ERPNext
		check_frappe_erpnext_versions()

		# 3. Verificar se há conflitos com outros apps
		check_app_conflicts()

		# 4. Preparar estrutura de diretórios
		prepare_directory_structure()

		# 5. Verificar permissões de arquivo
		check_file_permissions()

		# 6. Backup de configurações existentes
		backup_existing_configurations()

		print("✅ Pré-instalação concluída com sucesso!")

	except Exception as e:
		frappe.log_error(f"Erro na pré-instalação do Portugal Compliance: {str(e)}")
		print(f"❌ Erro na pré-instalação: {str(e)}")
		raise


def check_system_requirements():
	"""Verificar se o sistema atende aos requisitos mínimos"""
	try:
		print("📋 Verificando requisitos do sistema...")

		# Verificar Python
		import sys
		python_version = sys.version_info
		if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
			raise Exception("Python 3.8+ é obrigatório para Portugal Compliance")

		print(f"✅ Python {python_version.major}.{python_version.minor} - OK")

		# Verificar bibliotecas necessárias
		required_libraries = [
			'cryptography',
			'requests',
			'lxml',
			'qrcode',
			'Pillow'
		]

		missing_libraries = []
		for lib in required_libraries:
			try:
				__import__(lib)
				print(f"✅ {lib} - OK")
			except ImportError:
				missing_libraries.append(lib)
				print(f"❌ {lib} - FALTANDO")

		if missing_libraries:
			print(f"⚠️ Bibliotecas em falta: {', '.join(missing_libraries)}")
			print("💡 Execute: pip install " + " ".join(missing_libraries))

		# Verificar espaço em disco (mínimo 100MB)
		import shutil
		free_space = shutil.disk_usage("/").free / (1024 * 1024)  # MB
		if free_space < 100:
			print(f"⚠️ Pouco espaço em disco: {free_space:.1f}MB disponível")
		else:
			print(f"✅ Espaço em disco: {free_space:.1f}MB - OK")

	except Exception as e:
		print(f"❌ Erro ao verificar requisitos: {str(e)}")
		raise


def check_frappe_erpnext_versions():
	"""Verificar versões compatíveis do Frappe e ERPNext"""
	try:
		print("📋 Verificando versões Frappe/ERPNext...")

		# Verificar versão do Frappe
		frappe_version = frappe.__version__
		print(f"📋 Frappe versão: {frappe_version}")

		# Versões mínimas suportadas
		min_frappe_version = "15.0.0"
		min_erpnext_version = "15.0.0"

		# Verificar se ERPNext está instalado
		try:
			import erpnext
			erpnext_version = erpnext.__version__
			print(f"📋 ERPNext versão: {erpnext_version}")

			# Verificar compatibilidade (versão simplificada)
			if not erpnext_version.startswith("15."):
				print(f"⚠️ ERPNext {erpnext_version} pode não ser totalmente compatível")
				print("💡 Versão recomendada: ERPNext 15.x")
			else:
				print("✅ Versão ERPNext compatível")

		except ImportError:
			print("⚠️ ERPNext não encontrado - algumas funcionalidades podem não funcionar")

		# Verificar compatibilidade do Frappe
		if not frappe_version.startswith("15."):
			print(f"⚠️ Frappe {frappe_version} pode não ser totalmente compatível")
			print("💡 Versão recomendada: Frappe 15.x")
		else:
			print("✅ Versão Frappe compatível")

	except Exception as e:
		print(f"❌ Erro ao verificar versões: {str(e)}")
	# Não falhar por causa de versões - apenas avisar


def check_app_conflicts():
	"""Verificar conflitos com outros apps instalados"""
	try:
		print("📋 Verificando conflitos com outros apps...")

		# Lista de apps que podem causar conflitos
		conflicting_apps = [
			"portugal_tax",
			"portuguese_compliance",
			"pt_compliance",
			"saft_portugal"
		]

		installed_apps = frappe.get_installed_apps()
		conflicts = [app for app in conflicting_apps if app in installed_apps]

		if conflicts:
			print(f"⚠️ Apps conflitantes detectados: {', '.join(conflicts)}")
			print("💡 Considere desinstalar apps conflitantes antes de continuar")
		else:
			print("✅ Nenhum conflito de app detectado")

		# Verificar se há Custom Fields conflitantes
		conflicting_fields = frappe.db.sql("""
										   SELECT dt, fieldname, label
										   FROM `tabCustom Field`
										   WHERE fieldname IN ('atcud_code', 'portugal_series', 'saft_hash')
											 AND module != 'Portugal Compliance'
										   """, as_dict=True)

		if conflicting_fields:
			print("⚠️ Custom Fields conflitantes encontrados:")
			for field in conflicting_fields:
				print(f"   - {field.dt}.{field.fieldname} ({field.label})")
			print("💡 Estes campos podem causar conflitos")
		else:
			print("✅ Nenhum Custom Field conflitante detectado")

	except Exception as e:
		print(f"❌ Erro ao verificar conflitos: {str(e)}")
	# Não falhar - apenas avisar


def prepare_directory_structure():
	"""Preparar estrutura de diretórios necessária"""
	try:
		print("📋 Preparando estrutura de diretórios...")

		# Diretórios necessários
		required_dirs = [
			"/home/frappe/frappe-bench/config/certificates/portugal_compliance",
			"/home/frappe/frappe-bench/config/certificates/portugal_compliance/at_certificates",
			"/home/frappe/frappe-bench/config/certificates/portugal_compliance/at_certificates/test",
			"/home/frappe/frappe-bench/config/certificates/portugal_compliance/at_certificates/prod",
			"/home/frappe/frappe-bench/logs/portugal_compliance",
			"/home/frappe/frappe-bench/sites/assets/portugal_compliance",
			"/home/frappe/frappe-bench/sites/assets/portugal_compliance/qr_codes",
			"/home/frappe/frappe-bench/sites/assets/portugal_compliance/saft_files"
		]

		for directory in required_dirs:
			try:
				if not os.path.exists(directory):
					os.makedirs(directory, mode=0o755, exist_ok=True)
					print(f"✅ Diretório criado: {directory}")
				else:
					print(f"✅ Diretório existe: {directory}")
			except PermissionError:
				print(f"❌ Sem permissão para criar: {directory}")
			except Exception as e:
				print(f"❌ Erro ao criar {directory}: {str(e)}")

		# Criar arquivo .gitkeep para manter diretórios vazios
		gitkeep_dirs = [
			"/home/frappe/frappe-bench/sites/assets/portugal_compliance/qr_codes",
			"/home/frappe/frappe-bench/sites/assets/portugal_compliance/saft_files"
		]

		for directory in gitkeep_dirs:
			gitkeep_file = os.path.join(directory, ".gitkeep")
			try:
				if not os.path.exists(gitkeep_file):
					with open(gitkeep_file, 'w') as f:
						f.write("# Manter diretório no git\n")
					print(f"✅ .gitkeep criado: {gitkeep_file}")
			except Exception as e:
				print(f"❌ Erro ao criar .gitkeep: {str(e)}")

	except Exception as e:
		print(f"❌ Erro ao preparar diretórios: {str(e)}")
	# Não falhar - diretórios podem ser criados depois


def check_file_permissions():
	"""Verificar permissões de arquivo necessárias"""
	try:
		print("📋 Verificando permissões de arquivo...")

		# Verificar permissões do diretório do site
		site_path = frappe.utils.get_site_path()

		# Verificar se pode escrever no diretório do site
		test_file = os.path.join(site_path, "test_permissions.tmp")
		try:
			with open(test_file, 'w') as f:
				f.write("test")
			os.remove(test_file)
			print("✅ Permissões de escrita no site - OK")
		except Exception as e:
			print(f"❌ Sem permissões de escrita no site: {str(e)}")

		# Verificar permissões do diretório de apps
		apps_path = "/home/frappe/frappe-bench/apps"
		if os.access(apps_path, os.R_OK):
			print("✅ Permissões de leitura em apps - OK")
		else:
			print("❌ Sem permissões de leitura em apps")

		# Verificar permissões do diretório de sites
		sites_path = "/home/frappe/frappe-bench/sites"
		if os.access(sites_path, os.W_OK):
			print("✅ Permissões de escrita em sites - OK")
		else:
			print("❌ Sem permissões de escrita em sites")

	except Exception as e:
		print(f"❌ Erro ao verificar permissões: {str(e)}")


def backup_existing_configurations():
	"""Fazer backup de configurações existentes que podem ser alteradas"""
	try:
		print("📋 Fazendo backup de configurações existentes...")

		# Backup de Custom Fields existentes que podem ser modificados
		existing_fields = frappe.db.sql("""
										SELECT name, dt, fieldname, label, fieldtype, options
										FROM `tabCustom Field`
										WHERE dt IN ('Sales Invoice', 'Purchase Invoice',
													 'Payment Entry',
													 'Delivery Note', 'Purchase Receipt',
													 'Journal Entry',
													 'Stock Entry', 'Company')
										  AND fieldname IN ('naming_series', 'tax_id')
										""", as_dict=True)

		if existing_fields:
			backup_data = {
				"timestamp": frappe.utils.now(),
				"app": "portugal_compliance",
				"type": "custom_fields_backup",
				"data": existing_fields
			}

			# Salvar backup em arquivo
			backup_file = f"/home/frappe/frappe-bench/logs/portugal_compliance/custom_fields_backup_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.json"
			try:
				import json
				with open(backup_file, 'w') as f:
					json.dump(backup_data, f, indent=2, default=str)
				print(f"✅ Backup criado: {backup_file}")
			except Exception as e:
				print(f"❌ Erro ao criar backup: {str(e)}")

		# Backup de Print Formats que podem ser alterados
		existing_print_formats = frappe.db.sql("""
											   SELECT name, doc_type, print_format_builder, html
											   FROM `tabPrint Format`
											   WHERE doc_type IN
													 ('Sales Invoice', 'Purchase Invoice',
													  'Payment Entry')
												 AND standard = 'No'
											   """, as_dict=True)

		if existing_print_formats:
			print(f"📋 {len(existing_print_formats)} Print Formats customizados encontrados")
			print("💡 Considere fazer backup manual dos Print Formats importantes")

		print("✅ Backup de configurações concluído")

	except Exception as e:
		print(f"❌ Erro ao fazer backup: {str(e)}")
	# Não falhar por causa de backup


def validate_database_connection():
	"""Validar conexão com a base de dados"""
	try:
		print("📋 Validando conexão com a base de dados...")

		# Testar conexão básica
		frappe.db.sql("SELECT 1")
		print("✅ Conexão com base de dados - OK")

		# Verificar permissões de criação de tabelas
		try:
			frappe.db.sql("CREATE TEMPORARY TABLE test_permissions (id INT)")
			frappe.db.sql("DROP TEMPORARY TABLE test_permissions")
			print("✅ Permissões de criação de tabelas - OK")
		except Exception as e:
			print(f"❌ Sem permissões para criar tabelas: {str(e)}")

		# Verificar se pode criar Custom Fields
		try:
			test_field_exists = frappe.db.exists("Custom Field",
												 "Company-test_portugal_compliance")
			if not test_field_exists:
				# Tentar criar campo de teste
				test_field = frappe.get_doc({
					"doctype": "Custom Field",
					"dt": "Company",
					"fieldname": "test_portugal_compliance",
					"label": "Test Portugal Compliance",
					"fieldtype": "Check",
					"insert_after": "company_name",
					"hidden": 1
				})
				test_field.insert(ignore_permissions=True)

				# Remover campo de teste
				frappe.delete_doc("Custom Field", test_field.name, ignore_permissions=True)
				print("✅ Permissões para Custom Fields - OK")
			else:
				print("✅ Custom Fields podem ser criados - OK")

		except Exception as e:
			print(f"❌ Erro ao testar Custom Fields: {str(e)}")

	except Exception as e:
		print(f"❌ Erro na validação da base de dados: {str(e)}")
		raise  # Falhar se não conseguir conectar à DB


# Função principal chamada pelo hooks.py
def before_install():
	"""Função principal de pré-instalação"""
	execute()
