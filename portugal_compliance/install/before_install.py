# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Before Install - Portugal Compliance VERSÃO ATUALIZADA E ALINHADA
Executado antes da instalação do Portugal Compliance
✅ ALINHADO: Verificações específicas para compliance português
✅ ATUALIZADO: Validações de Custom Fields e Property Setters
✅ ROBUSTO: Backup completo e preparação de ambiente
✅ COMPATÍVEL: ERPNext 15.x e Frappe 15.x
"""

import frappe
from frappe import _
import os
import json
import sys
from datetime import datetime


def execute():
	"""
	✅ ATUALIZADO: Executado antes da instalação do Portugal Compliance
	Baseado na sua experiência com programação.sistemas_erp[7]
	"""
	try:
		print("🇵🇹 Iniciando pré-instalação do Portugal Compliance ATUALIZADO...")
		print("=" * 70)

		# 1. Verificar pré-requisitos do sistema
		check_system_requirements_enhanced()

		# 2. Verificar versões do Frappe/ERPNext
		check_frappe_erpnext_versions_enhanced()

		# 3. Verificar se há conflitos com outros apps
		check_app_conflicts_enhanced()

		# 4. ✅ NOVO: Verificar empresas portuguesas existentes
		check_existing_portuguese_companies()

		# 5. ✅ NOVO: Verificar Custom Fields conflitantes específicos
		check_portugal_compliance_conflicts()

		# 6. Preparar estrutura de diretórios
		prepare_directory_structure_enhanced()

		# 7. Verificar permissões de arquivo
		check_file_permissions_enhanced()

		# 8. Backup de configurações existentes
		backup_existing_configurations_enhanced()

		# 9. ✅ NOVO: Preparar ambiente para compliance português
		prepare_portugal_compliance_environment()

		# 10. Validar conexão com base de dados
		validate_database_connection_enhanced()

		print("=" * 70)
		print("✅ Pré-instalação do Portugal Compliance concluída com sucesso!")
		print("🚀 Sistema pronto para instalação do compliance português")

	except Exception as e:
		frappe.log_error(f"Erro na pré-instalação do Portugal Compliance: {str(e)}",
						 "Before Install")
		print(f"❌ Erro na pré-instalação: {str(e)}")
		raise


def check_system_requirements_enhanced():
	"""
	✅ MELHORADO: Verificar requisitos específicos para Portugal Compliance
	Baseado na sua experiência com programação.teste_de_ambiente[4]
	"""
	try:
		print("📋 Verificando requisitos do sistema (MELHORADO)...")

		# Verificar Python
		python_version = sys.version_info
		if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
			raise Exception("Python 3.8+ é obrigatório para Portugal Compliance")

		print(
			f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK")

		# ✅ BIBLIOTECAS ESPECÍFICAS PARA PORTUGAL COMPLIANCE
		required_libraries = {
			'cryptography': 'Criptografia para comunicação AT',
			'requests': 'Comunicação HTTP com webservices AT',
			'lxml': 'Processamento XML para SAF-T',
			'qrcode': 'Geração de QR codes para documentos',
			'Pillow': 'Processamento de imagens QR',
			'zeep': 'Cliente SOAP para webservices AT (opcional)',
			'xmltodict': 'Conversão XML para dicionário (opcional)'
		}

		missing_libraries = []
		optional_missing = []

		for lib, description in required_libraries.items():
			try:
				__import__(lib)
				print(f"✅ {lib} - OK ({description})")
			except ImportError:
				if lib in ['zeep', 'xmltodict']:
					optional_missing.append(lib)
					print(f"⚠️ {lib} - OPCIONAL ({description})")
				else:
					missing_libraries.append(lib)
					print(f"❌ {lib} - OBRIGATÓRIO ({description})")

		if missing_libraries:
			print(f"\n❌ Bibliotecas obrigatórias em falta: {', '.join(missing_libraries)}")
			print("💡 Execute: pip install " + " ".join(missing_libraries))
			raise Exception(f"Bibliotecas obrigatórias em falta: {', '.join(missing_libraries)}")

		if optional_missing:
			print(f"\n⚠️ Bibliotecas opcionais em falta: {', '.join(optional_missing)}")
			print("💡 Para funcionalidades avançadas, execute: pip install " + " ".join(
				optional_missing))

		# ✅ VERIFICAR ESPAÇO EM DISCO (mínimo 200MB para compliance)
		import shutil
		free_space = shutil.disk_usage("/").free / (1024 * 1024)  # MB
		if free_space < 200:
			print(f"⚠️ Pouco espaço em disco: {free_space:.1f}MB disponível (mínimo: 200MB)")
		else:
			print(f"✅ Espaço em disco: {free_space:.1f}MB - OK")

		# ✅ VERIFICAR CONECTIVIDADE INTERNET (para AT webservices)
		try:
			import requests
			response = requests.get("https://www.google.com", timeout=5)
			if response.status_code == 200:
				print("✅ Conectividade internet - OK")
			else:
				print("⚠️ Conectividade internet limitada")
		except Exception:
			print("⚠️ Sem conectividade internet - webservices AT podem não funcionar")

	except Exception as e:
		print(f"❌ Erro ao verificar requisitos: {str(e)}")
		raise


def check_frappe_erpnext_versions_enhanced():
	"""
	✅ MELHORADO: Verificar compatibilidade específica com Portugal Compliance
	"""
	try:
		print("\n📋 Verificando compatibilidade Frappe/ERPNext (MELHORADO)...")

		# Verificar versão do Frappe
		frappe_version = frappe.__version__
		print(f"📋 Frappe versão: {frappe_version}")

		# ✅ VERIFICAÇÕES ESPECÍFICAS DE COMPATIBILIDADE
		frappe_major = int(frappe_version.split('.')[0])

		if frappe_major < 15:
			raise Exception(f"Frappe {frappe_version} não é compatível. Versão mínima: 15.0.0")
		elif frappe_major > 15:
			print(
				f"⚠️ Frappe {frappe_version} é mais recente que testado - pode haver incompatibilidades")
		else:
			print("✅ Versão Frappe compatível")

		# Verificar ERPNext
		try:
			import erpnext
			erpnext_version = erpnext.__version__
			print(f"📋 ERPNext versão: {erpnext_version}")

			erpnext_major = int(erpnext_version.split('.')[0])

			if erpnext_major < 15:
				raise Exception(
					f"ERPNext {erpnext_version} não é compatível. Versão mínima: 15.0.0")
			elif erpnext_major > 15:
				print(
					f"⚠️ ERPNext {erpnext_version} é mais recente que testado - pode haver incompatibilidades")
			else:
				print("✅ Versão ERPNext compatível")

			# ✅ VERIFICAR MÓDULOS ESPECÍFICOS DO ERPNEXT
			required_modules = ['accounts', 'selling', 'buying', 'stock']
			for module in required_modules:
				try:
					__import__(f'erpnext.{module}')
					print(f"✅ Módulo ERPNext {module} - OK")
				except ImportError:
					print(f"❌ Módulo ERPNext {module} - FALTANDO")

		except ImportError:
			print("❌ ERPNext não encontrado - Portugal Compliance requer ERPNext")
			raise Exception("ERPNext é obrigatório para Portugal Compliance")

		# ✅ VERIFICAR FUNCIONALIDADES ESPECÍFICAS
		check_specific_frappe_features()

	except Exception as e:
		print(f"❌ Erro ao verificar versões: {str(e)}")
		raise


def check_specific_frappe_features():
	"""
	✅ NOVO: Verificar funcionalidades específicas do Frappe necessárias
	"""
	try:
		print("📋 Verificando funcionalidades específicas do Frappe...")

		# Verificar Custom Fields
		try:
			frappe.get_meta("Custom Field")
			print("✅ Custom Fields - OK")
		except Exception:
			print("❌ Custom Fields não disponível")

		# Verificar Property Setters
		try:
			frappe.get_meta("Property Setter")
			print("✅ Property Setters - OK")
		except Exception:
			print("❌ Property Setters não disponível")

		# Verificar Print Formats
		try:
			frappe.get_meta("Print Format")
			print("✅ Print Formats - OK")
		except Exception:
			print("❌ Print Formats não disponível")

		# Verificar Hooks
		try:
			from frappe.utils import get_hooks
			hooks = get_hooks()
			print("✅ Hooks system - OK")
		except Exception:
			print("❌ Hooks system não disponível")

	except Exception as e:
		print(f"⚠️ Erro ao verificar funcionalidades: {str(e)}")


def check_app_conflicts_enhanced():
	"""
	✅ MELHORADO: Verificar conflitos específicos com Portugal Compliance
	"""
	try:
		print("\n📋 Verificando conflitos com outros apps (MELHORADO)...")

		# ✅ APPS CONFLITANTES ESPECÍFICOS
		conflicting_apps = {
			"portugal_tax": "App de impostos portugueses conflitante",
			"portuguese_compliance": "App de compliance português conflitante",
			"pt_compliance": "App PT compliance conflitante",
			"saft_portugal": "App SAF-T Portugal conflitante",
			"portugal_localization": "Localização portuguesa conflitante",
			"at_compliance": "Compliance AT conflitante"
		}

		installed_apps = frappe.get_installed_apps()
		conflicts = []

		for app, description in conflicting_apps.items():
			if app in installed_apps:
				conflicts.append(f"{app} ({description})")

		if conflicts:
			print("❌ Apps conflitantes detectados:")
			for conflict in conflicts:
				print(f"   - {conflict}")
			print("💡 RECOMENDAÇÃO: Desinstale apps conflitantes antes de continuar")

			# ✅ NÃO FALHAR - APENAS AVISAR
			response = input("Continuar mesmo assim? (s/N): ")
			if response.lower() != 's':
				raise Exception("Instalação cancelada devido a conflitos de apps")
		else:
			print("✅ Nenhum conflito de app detectado")

		# ✅ VERIFICAR CUSTOM FIELDS CONFLITANTES ESPECÍFICOS
		check_conflicting_custom_fields_specific()

	except Exception as e:
		print(f"❌ Erro ao verificar conflitos: {str(e)}")
		if "Instalação cancelada" in str(e):
			raise


def check_conflicting_custom_fields_specific():
	"""
	✅ NOVO: Verificar Custom Fields conflitantes específicos
	"""
	try:
		print("📋 Verificando Custom Fields conflitantes específicos...")

		# ✅ CAMPOS ESPECÍFICOS DO PORTUGAL COMPLIANCE
		portugal_fields = {
			'atcud_code': 'Código ATCUD',
			'portugal_series': 'Série portuguesa',
			'saft_hash': 'Hash SAF-T',
			'qr_code_image': 'QR Code',
			'portugal_compliance_enabled': 'Compliance português ativo',
			'at_username': 'Username AT',
			'at_password': 'Password AT',
			'at_environment': 'Ambiente AT'
		}

		conflicting_fields = frappe.db.sql("""
										   SELECT dt, fieldname, label, module
										   FROM `tabCustom Field`
										   WHERE fieldname IN %(fields)s
											 AND module != 'Portugal Compliance'
										   """, {"fields": list(portugal_fields.keys())},
										   as_dict=True)

		if conflicting_fields:
			print("⚠️ Custom Fields conflitantes encontrados:")
			for field in conflicting_fields:
				expected_desc = portugal_fields.get(field.fieldname, "Campo português")
				print(
					f"   - {field.dt}.{field.fieldname} ({field.label}) - Módulo: {field.module}")
				print(f"     Esperado: {expected_desc}")

			print("\n💡 RECOMENDAÇÃO: Remova ou renomeie campos conflitantes")
			print("💡 Ou configure o módulo conflitante para usar 'Portugal Compliance'")
		else:
			print("✅ Nenhum Custom Field conflitante específico detectado")

	except Exception as e:
		print(f"⚠️ Erro ao verificar Custom Fields: {str(e)}")


def check_existing_portuguese_companies():
	"""
	✅ NOVO: Verificar empresas portuguesas existentes
	Baseado na sua experiência com programação.sistemas_erp[7]
	"""
	try:
		print("\n📋 Verificando empresas portuguesas existentes...")

		# Buscar empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name", "abbr", "tax_id",
													  "portugal_compliance_enabled"])

		if not portuguese_companies:
			print("⚠️ Nenhuma empresa portuguesa encontrada")
			print("💡 Crie pelo menos uma empresa com país = 'Portugal' após a instalação")
			return

		print(f"✅ Encontradas {len(portuguese_companies)} empresas portuguesas:")

		for company in portuguese_companies:
			compliance_status = "✅ Ativo" if company.get(
				'portugal_compliance_enabled') else "⏳ Inativo"
			nif_status = "✅ Tem NIF" if company.get('tax_id') else "❌ Sem NIF"

			print(f"   📋 {company.name} ({company.abbr})")
			print(f"      Compliance: {compliance_status}")
			print(f"      NIF: {nif_status}")

		# ✅ VERIFICAR SE HÁ SÉRIES EXISTENTES
		existing_series = frappe.db.count("Portugal Series Configuration")
		if existing_series > 0:
			print(f"✅ Encontradas {existing_series} séries portuguesas existentes")
		else:
			print("📋 Nenhuma série portuguesa existente - serão criadas após instalação")

	except Exception as e:
		print(f"⚠️ Erro ao verificar empresas portuguesas: {str(e)}")


def check_portugal_compliance_conflicts():
	"""
	✅ NOVO: Verificar conflitos específicos do Portugal Compliance
	"""
	try:
		print("\n📋 Verificando conflitos específicos do Portugal Compliance...")

		# ✅ VERIFICAR PROPERTY SETTERS CONFLITANTES
		conflicting_property_setters = frappe.db.sql("""
													 SELECT doc_type, field_name, property, value
													 FROM `tabProperty Setter`
													 WHERE field_name = 'naming_series'
													   AND property = 'options'
													   AND value LIKE '%FT%'
													   AND value LIKE '%2025%'
													 """, as_dict=True)

		if conflicting_property_setters:
			print("⚠️ Property Setters com séries portuguesas encontrados:")
			for ps in conflicting_property_setters:
				print(f"   - {ps.doc_type}.{ps.field_name}: {ps.value[:50]}...")
			print("💡 Estes podem ser atualizados durante a instalação")
		else:
			print("✅ Nenhum Property Setter conflitante detectado")

		# ✅ VERIFICAR NAMING SERIES EXISTENTES
		existing_naming_series = frappe.db.sql("""
											   SELECT name, prefix
											   FROM `tabNaming Series`
											   WHERE name LIKE '%FT%'
												  OR name LIKE '%FS%'
												  OR name LIKE '%FC%'
												  OR name LIKE '%RC%'
											   """, as_dict=True)

		if existing_naming_series:
			print(f"⚠️ {len(existing_naming_series)} Naming Series portuguesas encontradas:")
			for ns in existing_naming_series[:5]:  # Mostrar apenas primeiras 5
				print(f"   - {ns.name}")
			if len(existing_naming_series) > 5:
				print(f"   ... e mais {len(existing_naming_series) - 5}")
			print("💡 Estas podem ser integradas com o Portugal Compliance")
		else:
			print("✅ Nenhuma Naming Series portuguesa existente")

	except Exception as e:
		print(f"⚠️ Erro ao verificar conflitos específicos: {str(e)}")


def prepare_directory_structure_enhanced():
	"""
	✅ MELHORADO: Preparar estrutura específica para Portugal Compliance
	"""
	try:
		print("\n📋 Preparando estrutura de diretórios (MELHORADA)...")

		# ✅ DIRETÓRIOS ESPECÍFICOS PARA PORTUGAL COMPLIANCE
		base_path = "/home/frappe/frappe-bench"
		required_dirs = [
			# Certificados e credenciais AT
			f"{base_path}/config/certificates/portugal_compliance",
			f"{base_path}/config/certificates/portugal_compliance/at_certificates",
			f"{base_path}/config/certificates/portugal_compliance/at_certificates/test",
			f"{base_path}/config/certificates/portugal_compliance/at_certificates/prod",

			# Logs específicos
			f"{base_path}/logs/portugal_compliance",
			f"{base_path}/logs/portugal_compliance/at_communication",
			f"{base_path}/logs/portugal_compliance/atcud_generation",
			f"{base_path}/logs/portugal_compliance/series_management",

			# Assets e arquivos gerados
			f"{base_path}/sites/assets/portugal_compliance",
			f"{base_path}/sites/assets/portugal_compliance/qr_codes",
			f"{base_path}/sites/assets/portugal_compliance/saft_files",
			f"{base_path}/sites/assets/portugal_compliance/reports",
			f"{base_path}/sites/assets/portugal_compliance/backups",

			# Configurações temporárias
			f"{base_path}/sites/assets/portugal_compliance/temp",
			f"{base_path}/sites/assets/portugal_compliance/cache"
		]

		created_dirs = 0
		for directory in required_dirs:
			try:
				if not os.path.exists(directory):
					os.makedirs(directory, mode=0o755, exist_ok=True)
					print(f"✅ Criado: {directory}")
					created_dirs += 1
				else:
					print(f"✅ Existe: {os.path.basename(directory)}")
			except PermissionError:
				print(f"❌ Sem permissão: {directory}")
			except Exception as e:
				print(f"❌ Erro: {directory} - {str(e)}")

		print(f"📊 Diretórios criados: {created_dirs}")

		# ✅ CRIAR ARQUIVOS DE CONFIGURAÇÃO INICIAIS
		create_initial_config_files(base_path)

	except Exception as e:
		print(f"❌ Erro ao preparar diretórios: {str(e)}")


def create_initial_config_files(base_path):
	"""
	✅ NOVO: Criar arquivos de configuração iniciais
	"""
	try:
		print("📋 Criando arquivos de configuração iniciais...")

		# ✅ ARQUIVO DE CONFIGURAÇÃO AT
		at_config_path = f"{base_path}/config/certificates/portugal_compliance/at_config.json"
		if not os.path.exists(at_config_path):
			at_config = {
				"version": "2.1.0",
				"environments": {
					"test": {
						"base_url": "https://servicos.portaldasfinancas.gov.pt:400/fews/faturas",
						"description": "Ambiente de teste AT"
					},
					"prod": {
						"base_url": "https://servicos.portaldasfinancas.gov.pt:700/fews/faturas",
						"description": "Ambiente de produção AT"
					}
				},
				"created": datetime.now().isoformat(),
				"created_by": "portugal_compliance_installer"
			}

			try:
				with open(at_config_path, 'w') as f:
					json.dump(at_config, f, indent=2)
				print(f"✅ Configuração AT criada: {at_config_path}")
			except Exception as e:
				print(f"❌ Erro ao criar configuração AT: {str(e)}")

		# ✅ ARQUIVO README
		readme_path = f"{base_path}/sites/assets/portugal_compliance/README.md"
		if not os.path.exists(readme_path):
			readme_content = """# Portugal Compliance - Assets

Este diretório contém arquivos gerados pelo Portugal Compliance:

## Estrutura:
- `qr_codes/` - QR codes gerados para documentos
- `saft_files/` - Arquivos SAF-T exportados
- `reports/` - Relatórios de compliance
- `backups/` - Backups de configurações
- `temp/` - Arquivos temporários
- `cache/` - Cache de dados

## Manutenção:
- Arquivos em `temp/` podem ser removidos periodicamente
- Backups em `backups/` devem ser preservados
- QR codes e SAF-T files são importantes para auditoria

Gerado automaticamente pelo Portugal Compliance v2.1.0
"""

			try:
				with open(readme_path, 'w') as f:
					f.write(readme_content)
				print(f"✅ README criado: {readme_path}")
			except Exception as e:
				print(f"❌ Erro ao criar README: {str(e)}")

	except Exception as e:
		print(f"⚠️ Erro ao criar arquivos de configuração: {str(e)}")


def check_file_permissions_enhanced():
	"""
	✅ MELHORADO: Verificar permissões específicas para Portugal Compliance
	"""
	try:
		print("\n📋 Verificando permissões de arquivo (MELHORADAS)...")

		# ✅ VERIFICAÇÕES ESPECÍFICAS
		checks = [
			{
				"path": frappe.utils.get_site_path(),
				"permission": os.W_OK,
				"description": "Escrita no site"
			},
			{
				"path": "/home/frappe/frappe-bench/apps",
				"permission": os.R_OK,
				"description": "Leitura em apps"
			},
			{
				"path": "/home/frappe/frappe-bench/sites",
				"permission": os.W_OK,
				"description": "Escrita em sites"
			},
			{
				"path": "/home/frappe/frappe-bench/logs",
				"permission": os.W_OK,
				"description": "Escrita em logs"
			}
		]

		all_ok = True
		for check in checks:
			if os.path.exists(check["path"]) and os.access(check["path"], check["permission"]):
				print(f"✅ {check['description']} - OK")
			else:
				print(f"❌ {check['description']} - FALHOU")
				all_ok = False

		# ✅ TESTE DE ESCRITA ESPECÍFICO
		test_file = os.path.join(frappe.utils.get_site_path(), "portugal_compliance_test.tmp")
		try:
			with open(test_file, 'w') as f:
				f.write("Portugal Compliance test file")
			os.remove(test_file)
			print("✅ Teste de escrita específico - OK")
		except Exception as e:
			print(f"❌ Teste de escrita específico - FALHOU: {str(e)}")
			all_ok = False

		if not all_ok:
			print("⚠️ Algumas permissões podem causar problemas durante a instalação")

	except Exception as e:
		print(f"❌ Erro ao verificar permissões: {str(e)}")


def backup_existing_configurations_enhanced():
	"""
	✅ MELHORADO: Backup específico para Portugal Compliance
	Baseado na sua experiência com programação.revisão_de_arquivos[3]
	"""
	try:
		print("\n📋 Fazendo backup de configurações (MELHORADO)...")

		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		backup_dir = f"/home/frappe/frappe-bench/logs/portugal_compliance"

		# ✅ BACKUP ESPECÍFICO DE CUSTOM FIELDS
		backup_custom_fields_specific(backup_dir, timestamp)

		# ✅ BACKUP DE PROPERTY SETTERS
		backup_property_setters_specific(backup_dir, timestamp)

		# ✅ BACKUP DE NAMING SERIES
		backup_naming_series_specific(backup_dir, timestamp)

		# ✅ BACKUP DE EMPRESAS PORTUGUESAS
		backup_portuguese_companies(backup_dir, timestamp)

		print("✅ Backup de configurações específicas concluído")

	except Exception as e:
		print(f"❌ Erro ao fazer backup: {str(e)}")


def backup_custom_fields_specific(backup_dir, timestamp):
	"""✅ NOVO: Backup específico de Custom Fields"""
	try:
		# Campos que podem ser afetados
		target_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'POS Invoice', 'Payment Entry',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry',
			'Company', 'Customer', 'Supplier'
		]

		existing_fields = frappe.db.sql("""
										SELECT name,
											   dt,
											   fieldname,
											   label,
											   fieldtype,
											   options,
											   insert_after, module
										FROM `tabCustom Field`
										WHERE dt IN %(doctypes)s
										""", {"doctypes": target_doctypes}, as_dict=True)

		if existing_fields:
			backup_file = f"{backup_dir}/custom_fields_backup_{timestamp}.json"
			backup_data = {
				"timestamp": timestamp,
				"app": "portugal_compliance",
				"type": "custom_fields_backup",
				"total_fields": len(existing_fields),
				"data": existing_fields
			}

			with open(backup_file, 'w') as f:
				json.dump(backup_data, f, indent=2, default=str)

			print(f"✅ Backup Custom Fields: {len(existing_fields)} campos salvos")

	except Exception as e:
		print(f"⚠️ Erro no backup Custom Fields: {str(e)}")


def backup_property_setters_specific(backup_dir, timestamp):
	"""✅ NOVO: Backup específico de Property Setters"""
	try:
		property_setters = frappe.db.sql("""
										 SELECT name, doc_type, field_name, property, value
										 FROM `tabProperty Setter`
										 WHERE field_name = 'naming_series'
										   AND property = 'options'
										 """, as_dict=True)

		if property_setters:
			backup_file = f"{backup_dir}/property_setters_backup_{timestamp}.json"
			backup_data = {
				"timestamp": timestamp,
				"type": "property_setters_backup",
				"total_setters": len(property_setters),
				"data": property_setters
			}

			with open(backup_file, 'w') as f:
				json.dump(backup_data, f, indent=2, default=str)

			print(f"✅ Backup Property Setters: {len(property_setters)} setters salvos")

	except Exception as e:
		print(f"⚠️ Erro no backup Property Setters: {str(e)}")


def backup_naming_series_specific(backup_dir, timestamp):
	"""✅ NOVO: Backup específico de Naming Series"""
	try:
		naming_series = frappe.db.sql("""
									  SELECT name, prefix, current
									  FROM `tabNaming Series`
									  WHERE name LIKE '%FT%'
										 OR name LIKE '%FS%'
										 OR name LIKE '%FC%'
										 OR name LIKE '%RC%'
									  """, as_dict=True)

		if naming_series:
			backup_file = f"{backup_dir}/naming_series_backup_{timestamp}.json"
			backup_data = {
				"timestamp": timestamp,
				"type": "naming_series_backup",
				"total_series": len(naming_series),
				"data": naming_series
			}

			with open(backup_file, 'w') as f:
				json.dump(backup_data, f, indent=2, default=str)

			print(f"✅ Backup Naming Series: {len(naming_series)} séries salvas")

	except Exception as e:
		print(f"⚠️ Erro no backup Naming Series: {str(e)}")


def backup_portuguese_companies(backup_dir, timestamp):
	"""✅ NOVO: Backup de empresas portuguesas"""
	try:
		companies = frappe.db.sql("""
								  SELECT name,
										 company_name,
										 abbr,
										 country,
										 tax_id,
										 default_currency,
										 portugal_compliance_enabled,
										 at_username,
										 at_environment
								  FROM `tabCompany`
								  WHERE country = 'Portugal'
								  """, as_dict=True)

		if companies:
			backup_file = f"{backup_dir}/portuguese_companies_backup_{timestamp}.json"
			backup_data = {
				"timestamp": timestamp,
				"type": "portuguese_companies_backup",
				"total_companies": len(companies),
				"data": companies
			}

			with open(backup_file, 'w') as f:
				json.dump(backup_data, f, indent=2, default=str)

			print(f"✅ Backup Empresas PT: {len(companies)} empresas salvas")

	except Exception as e:
		print(f"⚠️ Erro no backup empresas: {str(e)}")


def prepare_portugal_compliance_environment():
	"""
	✅ CORRIGIDO: Preparar ambiente específico para Portugal Compliance
	"""
	try:
		print("\n📋 Preparando ambiente Portugal Compliance...")

		# ✅ ADICIONAR TIMESTAMP LOCAL
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

		# ✅ VERIFICAR TIMEZONE
		try:
			import time
			current_tz = time.tzname[0]
			if 'WET' in current_tz or 'WEST' in current_tz or 'Europe/Lisbon' in str(current_tz):
				print("✅ Timezone português detectado")
			else:
				print(f"⚠️ Timezone atual: {current_tz} (recomendado: Europe/Lisbon)")
		except Exception:
			print("⚠️ Não foi possível verificar timezone")

		# ✅ VERIFICAR LOCALE
		try:
			import locale
			current_locale = locale.getlocale()
			if any('pt' in str(loc).lower() for loc in current_locale if loc):
				print("✅ Locale português detectado")
			else:
				print(f"⚠️ Locale atual: {current_locale} (recomendado: pt_PT.UTF-8)")
		except Exception:
			print("⚠️ Não foi possível verificar locale")

		# ✅ PREPARAR CACHE ESPECÍFICO (CORRIGIDO)
		try:
			cache_dir = "/home/frappe/frappe-bench/sites/assets/portugal_compliance/cache"
			cache_files = [
				"nif_validation_cache.json",
				"at_communication_cache.json",
				"series_validation_cache.json"
			]

			for cache_file in cache_files:
				cache_path = os.path.join(cache_dir, cache_file)
				if not os.path.exists(cache_path):
					with open(cache_path, 'w') as f:
						json.dump({"created": timestamp, "data": {}},
								  f)  # ✅ TIMESTAMP AGORA DEFINIDO

			print("✅ Cache específico preparado")

		except Exception as e:
			print(f"⚠️ Erro ao preparar cache: {str(e)}")

		print("✅ Ambiente Portugal Compliance preparado")

	except Exception as e:
		print(f"⚠️ Erro ao preparar ambiente: {str(e)}")


def validate_database_connection_enhanced():
	"""
	✅ MELHORADO: Validar conexão específica para Portugal Compliance
	Baseado na sua experiência com programação.autenticação[2]
	"""
	try:
		print("\n📋 Validando conexão com base de dados (MELHORADA)...")

		# Testar conexão básica
		frappe.db.sql("SELECT 1")
		print("✅ Conexão básica - OK")

		# ✅ VERIFICAR PERMISSÕES ESPECÍFICAS
		permissions_tests = [
			{
				"test": "CREATE TEMPORARY TABLE portugal_test (id INT)",
				"cleanup": "DROP TEMPORARY TABLE portugal_test",
				"description": "Criação de tabelas"
			},
			{
				"test": "SELECT COUNT(*) FROM `tabDocType` WHERE name = 'Company'",
				"description": "Leitura de DocTypes"
			},
			{
				"test": "SELECT COUNT(*) FROM `tabCustom Field` LIMIT 1",
				"description": "Acesso a Custom Fields"
			}
		]

		for test in permissions_tests:
			try:
				frappe.db.sql(test["test"])
				if "cleanup" in test:
					frappe.db.sql(test["cleanup"])
				print(f"✅ {test['description']} - OK")
			except Exception as e:
				print(f"❌ {test['description']} - FALHOU: {str(e)}")

		# ✅ TESTAR CRIAÇÃO DE CUSTOM FIELD ESPECÍFICO
		test_custom_field_creation()

		print("✅ Validação de base de dados concluída")

	except Exception as e:
		print(f"❌ Erro na validação da base de dados: {str(e)}")
		raise


def test_custom_field_creation():
	"""✅ NOVO: Testar criação de Custom Field específico"""
	try:
		test_field_name = "Company-portugal_compliance_test_field"

		# Verificar se já existe
		if frappe.db.exists("Custom Field", test_field_name):
			frappe.delete_doc("Custom Field", test_field_name, ignore_permissions=True)

		# Criar campo de teste
		test_field = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Company",
			"fieldname": "portugal_compliance_test_field",
			"label": "Portugal Compliance Test",
			"fieldtype": "Check",
			"insert_after": "company_name",
			"hidden": 1,
			"description": "Campo de teste para Portugal Compliance - será removido"
		})
		test_field.insert(ignore_permissions=True)

		# Remover campo de teste
		frappe.delete_doc("Custom Field", test_field.name, ignore_permissions=True)

		print("✅ Criação de Custom Fields - OK")

	except Exception as e:
		print(f"❌ Criação de Custom Fields - FALHOU: {str(e)}")
		raise Exception("Sem permissões para criar Custom Fields")


# ========== FUNÇÃO PRINCIPAL ==========

def before_install():
	"""
	✅ FUNÇÃO PRINCIPAL: Chamada pelo hooks.py antes da instalação
	Baseado na sua experiência com programação.correção_de_código[5]
	"""
	try:
		execute()
		return True
	except Exception as e:
		print(f"\n❌ PRÉ-INSTALAÇÃO FALHOU: {str(e)}")
		print("💡 Corrija os problemas acima antes de continuar com a instalação")
		return False


# ========== LOG FINAL ==========
if __name__ == "__main__":
	print("🇵🇹 Portugal Compliance - Before Install Script")
	print("Executando verificações de pré-instalação...")
	success = before_install()
	if success:
		print("✅ Pré-instalação concluída com sucesso!")
	else:
		print("❌ Pré-instalação falhou!")

frappe.logger().info(
	"Portugal Compliance Before Install ATUALIZADO loaded - Version 2.1.0 - Enhanced & Comprehensive")
