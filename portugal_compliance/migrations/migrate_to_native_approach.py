# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Migration to Native Approach - Portugal Compliance VERSÃO NATIVA CORRIGIDA
Migração completa para abordagem nativa com formato SEM HÍFENS
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ MIGRAÇÃO: De custom fields para campos nativos
✅ ATUALIZAÇÃO: Todas as séries existentes para formato correto
✅ VALIDAÇÃO: Verificação completa de integridade
✅ BACKUP: Sistema de backup automático antes da migração
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint
import json
import re
import os
from datetime import datetime
import traceback

# ========== CONFIGURAÇÃO DA MIGRAÇÃO ==========

MIGRATION_VERSION = "2.0.0"
MIGRATION_DATE = "2025-06-03"

# ✅ MAPEAMENTO DE TIPOS DE DOCUMENTO (SEM HÍFENS)
DOCUMENT_TYPE_MAPPING = {
	'Sales Invoice': {
		'old_prefix_pattern': r'^FT-\d{4}-[A-Z0-9]+$',
		'new_code': 'FT',
		'description': 'Fatura'
	},
	'POS Invoice': {
		'old_prefix_pattern': r'^FS-\d{4}-[A-Z0-9]+$',
		'new_code': 'FS',
		'description': 'Fatura Simplificada'
	},
	'Sales Order': {
		'old_prefix_pattern': r'^FO-\d{4}-[A-Z0-9]+$',
		'new_code': 'FO',
		'description': 'Fatura-Orçamento'
	},
	'Quotation': {
		'old_prefix_pattern': r'^OR-\d{4}-[A-Z0-9]+$',
		'new_code': 'OR',
		'description': 'Orçamento'
	},
	'Delivery Note': {
		'old_prefix_pattern': r'^GR-\d{4}-[A-Z0-9]+$',
		'new_code': 'GR',
		'description': 'Guia de Remessa'
	},
	'Purchase Invoice': {
		'old_prefix_pattern': r'^FC-\d{4}-[A-Z0-9]+$',
		'new_code': 'FC',
		'description': 'Fatura de Compra'
	},
	'Purchase Order': {
		'old_prefix_pattern': r'^OC-\d{4}-[A-Z0-9]+$',
		'new_code': 'OC',
		'description': 'Ordem de Compra'
	},
	'Purchase Receipt': {
		'old_prefix_pattern': r'^GR-\d{4}-[A-Z0-9]+$',
		'new_code': 'GR',
		'description': 'Guia de Receção'
	},
	'Stock Entry': {
		'old_prefix_pattern': r'^GM-\d{4}-[A-Z0-9]+$',
		'new_code': 'GM',
		'description': 'Guia de Movimentação'
	},
	'Payment Entry': {
		'old_prefix_pattern': r'^RC-\d{4}-[A-Z0-9]+$',
		'new_code': 'RC',
		'description': 'Recibo'
	}
}

# ✅ CAMPOS NATIVOS A SEREM CRIADOS
NATIVE_FIELDS = {
	'atcud_code': {
		'fieldtype': 'Data',
		'label': 'ATCUD Code',
		'read_only': 1,
		'description': 'Código Único de Documento conforme Portaria 195/2020'
	},
	'portugal_compliance_status': {
		'fieldtype': 'Select',
		'label': 'Portugal Compliance Status',
		'options': 'Pending\nCompliant\nNon-Compliant\nError',
		'default': 'Pending',
		'read_only': 1
	},
	'qr_code': {
		'fieldtype': 'Attach Image',
		'label': 'QR Code',
		'read_only': 1,
		'description': 'QR Code gerado automaticamente'
	}
}


# ========== FUNÇÕES PRINCIPAIS DE MIGRAÇÃO ==========

def execute_migration():
	"""
	✅ PRINCIPAL: Executar migração completa para abordagem nativa
	"""
	try:
		frappe.log_error("Iniciando migração para abordagem nativa", "Migration Start")

		# ✅ VERIFICAR PRÉ-REQUISITOS
		if not check_migration_prerequisites():
			return {
				'success': False,
				'error': 'Pré-requisitos não atendidos'
			}

		# ✅ CRIAR BACKUP
		backup_result = create_migration_backup()
		if not backup_result['success']:
			return backup_result

		# ✅ EXECUTAR ETAPAS DA MIGRAÇÃO
		results = {}

		# Etapa 1: Migrar Custom Fields para Nativos
		results['custom_fields'] = migrate_custom_fields_to_native()

		# Etapa 2: Migrar Séries (COM HÍFENS → SEM HÍFENS)
		results['series'] = migrate_series_format()

		# Etapa 3: Migrar Documentos Existentes
		results['documents'] = migrate_existing_documents()

		# Etapa 4: Atualizar Property Setters
		results['property_setters'] = update_property_setters()

		# Etapa 5: Validar Migração
		results['validation'] = validate_migration()

		# ✅ VERIFICAR SE TODAS AS ETAPAS FORAM BEM-SUCEDIDAS
		all_success = all(result.get('success', False) for result in results.values())

		if all_success:
			# ✅ MARCAR MIGRAÇÃO COMO CONCLUÍDA
			mark_migration_completed()

			return {
				'success': True,
				'message': 'Migração concluída com sucesso',
				'results': results,
				'backup_file': backup_result.get('backup_file')
			}
		else:
			# ✅ ROLLBACK EM CASO DE ERRO
			rollback_migration(backup_result.get('backup_file'))

			return {
				'success': False,
				'error': 'Migração falhou, rollback executado',
				'results': results
			}

	except Exception as e:
		frappe.log_error(f"Erro na migração: {str(e)}\n{traceback.format_exc()}",
						 "Migration Error")
		return {
			'success': False,
			'error': str(e)
		}


def check_migration_prerequisites():
	"""
	✅ Verificar pré-requisitos para migração
	"""
	try:
		# ✅ VERIFICAR SE JÁ FOI MIGRADO
		if is_already_migrated():
			frappe.log_error("Sistema já foi migrado para abordagem nativa", "Migration Check")
			return False

		# ✅ VERIFICAR PERMISSÕES
		if not frappe.has_permission("System Settings", "write"):
			frappe.log_error("Usuário não tem permissões para migração", "Migration Check")
			return False

		# ✅ VERIFICAR EMPRESAS PORTUGUESAS
		portuguese_companies = frappe.get_all(
			"Company",
			filters={"country": "Portugal"},
			fields=["name"]
		)

		if not portuguese_companies:
			frappe.log_error("Nenhuma empresa portuguesa encontrada", "Migration Check")
			return False

		# ✅ VERIFICAR CUSTOM FIELDS EXISTENTES
		existing_custom_fields = frappe.get_all(
			"Custom Field",
			filters={
				"fieldname": ["in", ["atcud_code", "portugal_compliance_status"]],
				"dt": ["in", list(DOCUMENT_TYPE_MAPPING.keys())]
			}
		)

		if not existing_custom_fields:
			frappe.log_error("Custom fields não encontrados para migração", "Migration Check")
			return False

		return True

	except Exception as e:
		frappe.log_error(f"Erro ao verificar pré-requisitos: {str(e)}", "Migration Prerequisites")
		return False


def is_already_migrated():
	"""
	✅ Verificar se sistema já foi migrado
	"""
	try:
		# ✅ VERIFICAR SE EXISTE MARCADOR DE MIGRAÇÃO
		migration_marker = frappe.db.get_value(
			"System Settings",
			"System Settings",
			"portugal_compliance_native_migration"
		)

		return migration_marker == MIGRATION_VERSION

	except Exception:
		return False


# ========== MIGRAÇÃO DE CUSTOM FIELDS ==========

def migrate_custom_fields_to_native():
	"""
	✅ Migrar Custom Fields para campos nativos
	"""
	try:
		results = {
			'success': True,
			'migrated_fields': [],
			'errors': []
		}

		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			try:
				# ✅ MIGRAR CAMPOS PARA ESTE DOCTYPE
				doctype_result = migrate_doctype_custom_fields(doctype)
				results['migrated_fields'].extend(doctype_result.get('fields', []))

				if not doctype_result.get('success'):
					results['errors'].append(f"Erro em {doctype}: {doctype_result.get('error')}")

			except Exception as e:
				results['errors'].append(f"Erro ao migrar {doctype}: {str(e)}")

		if results['errors']:
			results['success'] = False

		return results

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def migrate_doctype_custom_fields(doctype):
	"""
	✅ Migrar custom fields de um doctype específico
	"""
	try:
		migrated_fields = []

		for field_name, field_config in NATIVE_FIELDS.items():
			try:
				# ✅ VERIFICAR SE CUSTOM FIELD EXISTE
				custom_field = frappe.db.get_value(
					"Custom Field",
					{"dt": doctype, "fieldname": field_name},
					["name", "label", "fieldtype"],
					as_dict=True
				)

				if custom_field:
					# ✅ CRIAR CAMPO NATIVO NO DOCTYPE
					create_native_field(doctype, field_name, field_config)

					# ✅ MIGRAR DADOS DO CUSTOM FIELD
					migrate_field_data(doctype, field_name)

					# ✅ REMOVER CUSTOM FIELD
					frappe.delete_doc("Custom Field", custom_field.name, ignore_permissions=True)

					migrated_fields.append({
						'doctype': doctype,
						'field_name': field_name,
						'custom_field_name': custom_field.name
					})

			except Exception as e:
				frappe.log_error(f"Erro ao migrar campo {field_name} em {doctype}: {str(e)}")

		return {
			'success': True,
			'fields': migrated_fields
		}

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def create_native_field(doctype, field_name, field_config):
	"""
	✅ Criar campo nativo no DocType
	"""
	try:
		# ✅ OBTER META DO DOCTYPE
		meta = frappe.get_meta(doctype)

		# ✅ VERIFICAR SE CAMPO JÁ EXISTE
		if meta.has_field(field_name):
			return True

		# ✅ ADICIONAR CAMPO AO DOCTYPE
		frappe.db.sql(f"""
            INSERT INTO `tabDocField`
            (name, parent, parenttype, parentfield, fieldname, fieldtype, label,
             read_only, description, options, default_value, idx)
            VALUES
            (%(name)s, %(parent)s, 'DocType', 'fields', %(fieldname)s, %(fieldtype)s,
             %(label)s, %(read_only)s, %(description)s, %(options)s, %(default)s,
             (SELECT COALESCE(MAX(idx), 0) + 1 FROM `tabDocField` WHERE parent = %(parent)s))
        """, {
			'name': frappe.generate_hash(length=10),
			'parent': doctype,
			'fieldname': field_name,
			'fieldtype': field_config['fieldtype'],
			'label': field_config['label'],
			'read_only': field_config.get('read_only', 0),
			'description': field_config.get('description', ''),
			'options': field_config.get('options', ''),
			'default': field_config.get('default', '')
		})

		# ✅ LIMPAR CACHE
		frappe.clear_cache(doctype=doctype)

		return True

	except Exception as e:
		frappe.log_error(f"Erro ao criar campo nativo {field_name} em {doctype}: {str(e)}")
		return False


def migrate_field_data(doctype, field_name):
	"""
	✅ Migrar dados do custom field para campo nativo
	"""
	try:
		# ✅ VERIFICAR SE TABELA TEM O CAMPO
		table_name = f"tab{doctype}"

		# ✅ VERIFICAR SE COLUNA EXISTE
		columns = frappe.db.sql(f"SHOW COLUMNS FROM `{table_name}` LIKE '{field_name}'")

		if not columns:
			# ✅ ADICIONAR COLUNA SE NÃO EXISTIR
			field_config = NATIVE_FIELDS[field_name]
			column_type = get_column_type(field_config['fieldtype'])

			frappe.db.sql(f"ALTER TABLE `{table_name}` ADD COLUMN `{field_name}` {column_type}")

		# ✅ OS DADOS JÁ ESTÃO NA TABELA PRINCIPAL, NÃO PRECISA MIGRAR
		return True

	except Exception as e:
		frappe.log_error(f"Erro ao migrar dados do campo {field_name}: {str(e)}")
		return False


def get_column_type(fieldtype):
	"""
	✅ Obter tipo de coluna MySQL baseado no fieldtype
	"""
	type_mapping = {
		'Data': 'VARCHAR(140)',
		'Select': 'VARCHAR(140)',
		'Attach Image': 'TEXT',
		'Text': 'TEXT',
		'Long Text': 'LONGTEXT',
		'Check': 'INT(1)',
		'Int': 'INT(11)',
		'Float': 'DECIMAL(18,6)'
	}

	return type_mapping.get(fieldtype, 'VARCHAR(140)')


# ========== MIGRAÇÃO DE SÉRIES ==========

def migrate_series_format():
	"""
	✅ CORRIGIDO: Migrar séries de COM HÍFENS para SEM HÍFENS
	"""
	try:
		results = {
			'success': True,
			'migrated_series': [],
			'errors': []
		}

		# ✅ BUSCAR SÉRIES COM FORMATO ANTIGO (COM HÍFENS)
		old_series = frappe.get_all(
			"Portugal Series Configuration",
			filters={
				"prefix": ["like", "%-%"]  # Séries com hífens
			},
			fields=["name", "prefix", "naming_series", "document_type", "company"]
		)

		for series in old_series:
			try:
				# ✅ CONVERTER PREFIXO PARA FORMATO SEM HÍFENS
				new_prefix = convert_prefix_format(series.prefix)
				new_naming_series = f"{new_prefix}.####"

				# ✅ ATUALIZAR SÉRIE
				frappe.db.set_value(
					"Portugal Series Configuration",
					series.name,
					{
						"prefix": new_prefix,
						"naming_series": new_naming_series
					}
				)

				# ✅ ATUALIZAR DOCUMENTOS QUE USAM ESTA SÉRIE
				update_documents_naming_series(series.naming_series, new_naming_series,
											   series.document_type)

				results['migrated_series'].append({
					'name': series.name,
					'old_prefix': series.prefix,
					'new_prefix': new_prefix,
					'old_naming_series': series.naming_series,
					'new_naming_series': new_naming_series,
					'document_type': series.document_type
				})

			except Exception as e:
				results['errors'].append(f"Erro ao migrar série {series.name}: {str(e)}")

		if results['errors']:
			results['success'] = False

		return results

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def convert_prefix_format(old_prefix):
	"""
	✅ CORRIGIDO: Converter prefixo de COM HÍFENS para SEM HÍFENS
	"""
	try:
		# ✅ REMOVER HÍFENS: FT-2025-NDX → FT2025NDX
		new_prefix = old_prefix.replace('-', '')

		# ✅ VALIDAR FORMATO RESULTANTE
		pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$'
		if not re.match(pattern, new_prefix):
			raise ValueError(f"Formato inválido após conversão: {new_prefix}")

		return new_prefix

	except Exception as e:
		frappe.log_error(f"Erro ao converter prefixo {old_prefix}: {str(e)}")
		return old_prefix


def update_documents_naming_series(old_naming_series, new_naming_series, document_type):
	"""
	✅ Atualizar naming series nos documentos existentes
	"""
	try:
		# ✅ ATUALIZAR DOCUMENTOS
		frappe.db.sql(f"""
            UPDATE `tab{document_type}`
            SET naming_series = %s
            WHERE naming_series = %s
        """, (new_naming_series, old_naming_series))

		# ✅ COMMIT PARA GARANTIR PERSISTÊNCIA
		frappe.db.commit()

		return True

	except Exception as e:
		frappe.log_error(f"Erro ao atualizar naming series em {document_type}: {str(e)}")
		return False


# ========== MIGRAÇÃO DE DOCUMENTOS ==========

def migrate_existing_documents():
	"""
	✅ Migrar documentos existentes para nova estrutura
	"""
	try:
		results = {
			'success': True,
			'migrated_documents': 0,
			'errors': []
		}

		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			try:
				# ✅ MIGRAR DOCUMENTOS DESTE TIPO
				doctype_result = migrate_doctype_documents(doctype)
				results['migrated_documents'] += doctype_result.get('count', 0)

				if doctype_result.get('errors'):
					results['errors'].extend(doctype_result['errors'])

			except Exception as e:
				results['errors'].append(f"Erro ao migrar documentos {doctype}: {str(e)}")

		if results['errors']:
			results['success'] = False

		return results

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def migrate_doctype_documents(doctype):
	"""
	✅ Migrar documentos de um tipo específico
	"""
	try:
		# ✅ BUSCAR DOCUMENTOS SEM ATCUD
		documents = frappe.get_all(
			doctype,
			filters={
				"docstatus": 1,
				"atcud_code": ["in", ["", None]]
			},
			fields=["name", "naming_series"],
			limit=1000
		)

		migrated_count = 0
		errors = []

		for doc in documents:
			try:
				# ✅ GERAR ATCUD PARA DOCUMENTO
				from portugal_compliance.utils.atcud_generator import \
					generate_manual_atcud_certified

				result = generate_manual_atcud_certified(doctype, doc.name)

				if result.get('success'):
					migrated_count += 1
				else:
					errors.append(f"Erro ao gerar ATCUD para {doc.name}: {result.get('error')}")

			except Exception as e:
				errors.append(f"Erro ao processar documento {doc.name}: {str(e)}")

		return {
			'success': len(errors) == 0,
			'count': migrated_count,
			'errors': errors
		}

	except Exception as e:
		return {
			'success': False,
			'error': str(e),
			'count': 0,
			'errors': [str(e)]
		}


# ========== ATUALIZAÇÃO DE PROPERTY SETTERS ==========

def update_property_setters():
	"""
	✅ CORRIGIDO: Atualizar Property Setters para formato SEM HÍFENS
	"""
	try:
		results = {
			'success': True,
			'updated_properties': [],
			'errors': []
		}

		# ✅ ATUALIZAR NAMING SERIES OPTIONS
		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			try:
				# ✅ BUSCAR PROPERTY SETTER DE NAMING SERIES
				property_setter = frappe.db.get_value(
					"Property Setter",
					{
						"doc_type": doctype,
						"field_name": "naming_series",
						"property": "options"
					},
					"name"
				)

				if property_setter:
					# ✅ ATUALIZAR OPÇÕES PARA FORMATO SEM HÍFENS
					doc_info = DOCUMENT_TYPE_MAPPING[doctype]
					new_options = generate_naming_series_options(doc_info['new_code'])

					frappe.db.set_value(
						"Property Setter",
						property_setter,
						"value",
						new_options
					)

					results['updated_properties'].append({
						'doctype': doctype,
						'property': 'naming_series_options',
						'property_setter': property_setter
					})

			except Exception as e:
				results['errors'].append(
					f"Erro ao atualizar property setter para {doctype}: {str(e)}")

		if results['errors']:
			results['success'] = False

		return results

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def generate_naming_series_options(doc_code):
	"""
	✅ CORRIGIDO: Gerar opções de naming series (formato SEM HÍFENS)
	"""
	current_year = datetime.now().year

	# ✅ EXEMPLOS SEM HÍFENS
	options = [
		f"{doc_code}{current_year}NDX.####",
		f"{doc_code}{current_year}ABC.####",
		f"{doc_code}{current_year}XYZ.####"
	]

	return "\n".join(options)


# ========== VALIDAÇÃO DA MIGRAÇÃO ==========

def validate_migration():
	"""
	✅ Validar se migração foi bem-sucedida
	"""
	try:
		validation_results = {
			'success': True,
			'checks': [],
			'errors': []
		}

		# ✅ VERIFICAR CUSTOM FIELDS REMOVIDOS
		custom_fields_check = validate_custom_fields_removed()
		validation_results['checks'].append(custom_fields_check)

		# ✅ VERIFICAR SÉRIES MIGRADAS
		series_check = validate_series_migrated()
		validation_results['checks'].append(series_check)

		# ✅ VERIFICAR DOCUMENTOS COM ATCUD
		documents_check = validate_documents_atcud()
		validation_results['checks'].append(documents_check)

		# ✅ VERIFICAR PROPERTY SETTERS
		properties_check = validate_property_setters()
		validation_results['checks'].append(properties_check)

		# ✅ COMPILAR ERROS
		for check in validation_results['checks']:
			if not check['success']:
				validation_results['errors'].extend(check.get('errors', []))

		if validation_results['errors']:
			validation_results['success'] = False

		return validation_results

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def validate_custom_fields_removed():
	"""
	✅ Validar se custom fields foram removidos
	"""
	try:
		remaining_custom_fields = frappe.get_all(
			"Custom Field",
			filters={
				"fieldname": ["in", list(NATIVE_FIELDS.keys())],
				"dt": ["in", list(DOCUMENT_TYPE_MAPPING.keys())]
			}
		)

		return {
			'success': len(remaining_custom_fields) == 0,
			'check_name': 'Custom Fields Removed',
			'remaining_count': len(remaining_custom_fields),
			'errors': [
				f"Custom fields ainda existem: {len(remaining_custom_fields)}"] if remaining_custom_fields else []
		}

	except Exception as e:
		return {
			'success': False,
			'check_name': 'Custom Fields Removed',
			'error': str(e),
			'errors': [str(e)]
		}


def validate_series_migrated():
	"""
	✅ CORRIGIDO: Validar se séries foram migradas para formato SEM HÍFENS
	"""
	try:
		# ✅ BUSCAR SÉRIES COM FORMATO ANTIGO (COM HÍFENS)
		old_format_series = frappe.get_all(
			"Portugal Series Configuration",
			filters={
				"prefix": ["like", "%-%"]  # Séries ainda com hífens
			}
		)

		return {
			'success': len(old_format_series) == 0,
			'check_name': 'Series Format Migrated',
			'old_format_count': len(old_format_series),
			'errors': [
				f"Séries ainda com formato antigo: {len(old_format_series)}"] if old_format_series else []
		}

	except Exception as e:
		return {
			'success': False,
			'check_name': 'Series Format Migrated',
			'error': str(e),
			'errors': [str(e)]
		}


def validate_documents_atcud():
	"""
	✅ Validar se documentos têm ATCUD
	"""
	try:
		total_without_atcud = 0

		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			count = frappe.db.count(
				doctype,
				{
					"docstatus": 1,
					"atcud_code": ["in", ["", None]]
				}
			)
			total_without_atcud += count

		return {
			'success': total_without_atcud == 0,
			'check_name': 'Documents ATCUD',
			'without_atcud_count': total_without_atcud,
			'errors': [
				f"Documentos sem ATCUD: {total_without_atcud}"] if total_without_atcud > 0 else []
		}

	except Exception as e:
		return {
			'success': False,
			'check_name': 'Documents ATCUD',
			'error': str(e),
			'errors': [str(e)]
		}


def validate_property_setters():
	"""
	✅ CORRIGIDO: Validar se property setters foram atualizados (formato SEM HÍFENS)
	"""
	try:
		invalid_properties = 0

		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			# ✅ VERIFICAR NAMING SERIES OPTIONS
			options = frappe.db.get_value(
				"Property Setter",
				{
					"doc_type": doctype,
					"field_name": "naming_series",
					"property": "options"
				},
				"value"
			)

			if options and "-" in options:  # Ainda tem hífens
				invalid_properties += 1

		return {
			'success': invalid_properties == 0,
			'check_name': 'Property Setters Updated',
			'invalid_count': invalid_properties,
			'errors': [
				f"Property setters com formato antigo: {invalid_properties}"] if invalid_properties > 0 else []
		}

	except Exception as e:
		return {
			'success': False,
			'check_name': 'Property Setters Updated',
			'error': str(e),
			'errors': [str(e)]
		}


# ========== BACKUP E ROLLBACK ==========

def create_migration_backup():
	"""
	✅ Criar backup antes da migração
	"""
	try:
		backup_data = {
			'migration_version': MIGRATION_VERSION,
			'migration_date': MIGRATION_DATE,
			'backup_timestamp': get_datetime(),
			'custom_fields': [],
			'series_configurations': [],
			'property_setters': []
		}

		# ✅ BACKUP CUSTOM FIELDS
		custom_fields = frappe.get_all(
			"Custom Field",
			filters={
				"fieldname": ["in", list(NATIVE_FIELDS.keys())],
				"dt": ["in", list(DOCUMENT_TYPE_MAPPING.keys())]
			},
			fields=["*"]
		)
		backup_data['custom_fields'] = custom_fields

		# ✅ BACKUP SERIES CONFIGURATIONS
		series_configs = frappe.get_all(
			"Portugal Series Configuration",
			fields=["*"]
		)
		backup_data['series_configurations'] = series_configs

		# ✅ BACKUP PROPERTY SETTERS
		property_setters = frappe.get_all(
			"Property Setter",
			filters={
				"doc_type": ["in", list(DOCUMENT_TYPE_MAPPING.keys())],
				"field_name": "naming_series"
			},
			fields=["*"]
		)
		backup_data['property_setters'] = property_setters

		# ✅ SALVAR BACKUP
		backup_file = f"migration_backup_{MIGRATION_DATE}_{datetime.now().strftime('%H%M%S')}.json"
		backup_path = os.path.join(frappe.get_site_path(), "private", "backups", backup_file)

		# ✅ CRIAR DIRETÓRIO SE NÃO EXISTIR
		os.makedirs(os.path.dirname(backup_path), exist_ok=True)

		with open(backup_path, 'w', encoding='utf-8') as f:
			json.dump(backup_data, f, indent=2, default=str)

		return {
			'success': True,
			'backup_file': backup_file,
			'backup_path': backup_path
		}

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


def rollback_migration(backup_file):
	"""
	✅ Fazer rollback da migração
	"""
	try:
		if not backup_file:
			return False

		backup_path = os.path.join(frappe.get_site_path(), "private", "backups", backup_file)

		if not os.path.exists(backup_path):
			return False

		# ✅ CARREGAR BACKUP
		with open(backup_path, 'r', encoding='utf-8') as f:
			backup_data = json.load(f)

		# ✅ RESTAURAR CUSTOM FIELDS
		for cf_data in backup_data.get('custom_fields', []):
			try:
				if not frappe.db.exists("Custom Field", cf_data['name']):
					cf_doc = frappe.new_doc("Custom Field")
					cf_doc.update(cf_data)
					cf_doc.insert(ignore_permissions=True)
			except Exception:
				pass

		# ✅ RESTAURAR SERIES CONFIGURATIONS
		for series_data in backup_data.get('series_configurations', []):
			try:
				if frappe.db.exists("Portugal Series Configuration", series_data['name']):
					frappe.db.set_value(
						"Portugal Series Configuration",
						series_data['name'],
						{
							'prefix': series_data['prefix'],
							'naming_series': series_data['naming_series']
						}
					)
			except Exception:
				pass

		# ✅ RESTAURAR PROPERTY SETTERS
		for ps_data in backup_data.get('property_setters', []):
			try:
				if frappe.db.exists("Property Setter", ps_data['name']):
					frappe.db.set_value("Property Setter", ps_data['name'], "value",
										ps_data['value'])
			except Exception:
				pass

		frappe.db.commit()
		return True

	except Exception as e:
		frappe.log_error(f"Erro no rollback: {str(e)}", "Migration Rollback")
		return False


def mark_migration_completed():
	"""
	✅ Marcar migração como concluída
	"""
	try:
		# ✅ MARCAR NO SYSTEM SETTINGS
		frappe.db.set_value(
			"System Settings",
			"System Settings",
			"portugal_compliance_native_migration",
			MIGRATION_VERSION
		)

		# ✅ CRIAR LOG DE MIGRAÇÃO
		migration_log = frappe.new_doc("Error Log")
		migration_log.update({
			"method": "portugal_compliance.migrations.migrate_to_native_approach",
			"error": f"Migração para abordagem nativa concluída com sucesso - Versão {MIGRATION_VERSION}"
		})
		migration_log.insert(ignore_permissions=True)

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Erro ao marcar migração como concluída: {str(e)}")


# ========== FUNÇÕES DE UTILITÁRIO ==========

@frappe.whitelist()
def run_migration():
	"""
	✅ API pública para executar migração
	"""
	if not frappe.has_permission("System Settings", "write"):
		frappe.throw(_("Permissão insuficiente para executar migração"))

	return execute_migration()


@frappe.whitelist()
def check_migration_status():
	"""
	✅ API para verificar status da migração
	"""
	try:
		is_migrated = is_already_migrated()

		if is_migrated:
			return {
				'migrated': True,
				'version': MIGRATION_VERSION,
				'message': 'Sistema já migrado para abordagem nativa'
			}
		else:
			# ✅ VERIFICAR PRÉ-REQUISITOS
			can_migrate = check_migration_prerequisites()

			return {
				'migrated': False,
				'can_migrate': can_migrate,
				'message': 'Migração necessária' if can_migrate else 'Pré-requisitos não atendidos'
			}

	except Exception as e:
		return {
			'error': str(e)
		}


@frappe.whitelist()
def get_migration_preview():
	"""
	✅ API para preview da migração
	"""
	try:
		preview = {
			'custom_fields_to_migrate': [],
			'series_to_migrate': [],
			'documents_to_migrate': 0
		}

		# ✅ CUSTOM FIELDS
		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			custom_fields = frappe.get_all(
				"Custom Field",
				filters={
					"dt": doctype,
					"fieldname": ["in", list(NATIVE_FIELDS.keys())]
				},
				fields=["name", "fieldname", "label"]
			)
			preview['custom_fields_to_migrate'].extend(custom_fields)

		# ✅ SÉRIES COM FORMATO ANTIGO
		old_series = frappe.get_all(
			"Portugal Series Configuration",
			filters={"prefix": ["like", "%-%"]},
			fields=["name", "prefix", "naming_series", "document_type"]
		)

		for series in old_series:
			series['new_prefix'] = convert_prefix_format(series.prefix)
			series['new_naming_series'] = f"{series['new_prefix']}.####"

		preview['series_to_migrate'] = old_series

		# ✅ DOCUMENTOS SEM ATCUD
		total_docs = 0
		for doctype in DOCUMENT_TYPE_MAPPING.keys():
			count = frappe.db.count(
				doctype,
				{
					"docstatus": 1,
					"atcud_code": ["in", ["", None]]
				}
			)
			total_docs += count

		preview['documents_to_migrate'] = total_docs

		return {
			'success': True,
			'preview': preview
		}

	except Exception as e:
		return {
			'success': False,
			'error': str(e)
		}


# ========== CONSOLE LOG PARA DEBUG ==========
frappe.logger().info(
	"Migration to Native Approach loaded - Version 2.0.0 - Format WITHOUT HYPHENS")
