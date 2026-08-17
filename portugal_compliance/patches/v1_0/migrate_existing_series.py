# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import re
from frappe.utils import cint, now, today
from erpnext.accounts.utils import get_fiscal_year


def execute():
	"""
	✅ CORRIGIDO: Patch para migrar séries existentes para NOVA ABORDAGEM
	Adaptado para naming_series nativa sem campos portugal_series
	"""
	frappe.logger().info("🇵🇹 Iniciando patch: migrate_existing_series - NOVA ABORDAGEM")

	try:
		# ✅ VERIFICAR SE PATCH JÁ FOI EXECUTADO (NOVA ABORDAGEM)
		if frappe.db.exists("Portugal Series Configuration", {"migrated_from_existing": 1}):
			frappe.logger().info("Patch migrate_existing_series (nova abordagem) já foi executado")
			return

		# ✅ MIGRAR SÉRIES USANDO NOVA ABORDAGEM
		migrate_naming_series_new_approach()

		# ✅ MIGRAR DOCUMENTOS EXISTENTES (SEM portugal_series)
		migrate_existing_documents_new_approach()

		# ✅ ATUALIZAR CONFIGURAÇÕES DE EMPRESA
		update_company_settings_new_approach()

		# ✅ CONFIGURAR PROPERTY SETTERS PARA NAMING SERIES
		setup_naming_series_property_setters()

		# ✅ LIMPAR CAMPOS portugal_series ANTIGOS
		cleanup_old_portugal_series_fields()

		# ✅ MARCAR PATCH COMO EXECUTADO
		mark_migration_complete_new_approach()

		frappe.db.commit()
		frappe.logger().info(
			"✅ Patch migrate_existing_series (nova abordagem) executado com sucesso")

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Erro no patch migrate_existing_series (nova abordagem): {str(e)}",
						 "Portugal Compliance Migration")
		raise


def migrate_naming_series_new_approach():
	"""
	✅ CORRIGIDO: Migra séries existentes para Portugal Series Configuration (nova abordagem)
	"""
	try:
		# ✅ DOCTYPES SUPORTADOS PELA NOVA ABORDAGEM
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES

		supported_doctypes = list(PORTUGAL_DOCUMENT_TYPES.keys())
		migrated_count = 0

		for doctype in supported_doctypes:
			try:
				# ✅ OBTER NAMING SERIES EXISTENTES DESTE DOCTYPE
				existing_series = get_existing_naming_series(doctype)

				for series_info in existing_series:
					# ✅ VERIFICAR SE É SÉRIE PORTUGUESA
					if is_portuguese_series_new_approach(series_info['naming_series']):
						# ✅ OBTER EMPRESAS QUE USAM ESTA SÉRIE
						companies = get_companies_using_series_new_approach(doctype, series_info[
							'naming_series'])

						for company in companies:
							# ✅ CRIAR PORTUGAL SERIES CONFIGURATION
							series_name = create_portugal_series_config_new_approach(
								series_info, doctype, company
							)

							if series_name:
								migrated_count += 1
								frappe.logger().info(
									f"✅ Série migrada (nova abordagem): {series_name}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar séries do {doctype}: {str(e)}")

		frappe.logger().info(f"✅ Total de séries migradas (nova abordagem): {migrated_count}")

	except Exception as e:
		frappe.log_error(f"Erro na migração de naming_series: {str(e)}")


def get_existing_naming_series(doctype):
	"""
	✅ NOVO: Obtém naming series existentes de documentos reais
	"""
	try:
		# ✅ BUSCAR NAMING SERIES USADAS EM DOCUMENTOS EXISTENTES
		existing_series = frappe.db.sql(f"""
            SELECT DISTINCT naming_series, COUNT(*) as count
            FROM `tab{doctype}`
            WHERE naming_series IS NOT NULL
            AND naming_series != ''
            AND docstatus != 2
            GROUP BY naming_series
            ORDER BY count DESC
        """, as_dict=True)

		return existing_series

	except Exception as e:
		frappe.log_error(f"Erro ao obter naming series existentes para {doctype}: {str(e)}")
		return []


def is_portuguese_series_new_approach(naming_series):
	"""
	✅ CORRIGIDO: Verifica se naming_series é portuguesa (nova abordagem)
	"""
	try:
		if not naming_series:
			return False

		# ✅ PADRÕES PORTUGUESES (NOVO E ANTIGO)
		# Novo: FT2025DSY.####
		new_pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}\.####$'
		# Antigo: FT-.YYYY.-.####, FT-####, FT.####
		old_patterns = [
			r'^(FT|FS|FC|RC|GR|GT|JE|NC|ND|OR|EC|EF|MR)-',
			r'^(FT|FS|FC|RC|GR|GT|JE|NC|ND|OR|EC|EF|MR)\.',
			r'^(FT|FS|FC|RC|GR|GT|JE|NC|ND|OR|EC|EF|MR)\.####$'
		]

		# ✅ VERIFICAR PADRÃO NOVO
		if re.match(new_pattern, naming_series):
			return True

		# ✅ VERIFICAR PADRÕES ANTIGOS
		for pattern in old_patterns:
			if re.match(pattern, naming_series):
				return True

		return False

	except Exception:
		return False


def get_companies_using_series_new_approach(doctype, naming_series):
	"""
	✅ CORRIGIDO: Obtém empresas que usam naming_series específica
	"""
	try:
		# ✅ PROCURAR DOCUMENTOS QUE USAM ESTA NAMING_SERIES
		companies = frappe.db.sql(f"""
            SELECT DISTINCT company, COUNT(*) as doc_count
            FROM `tab{doctype}`
            WHERE naming_series = %s
            AND docstatus != 2
            AND company IS NOT NULL
            GROUP BY company
            ORDER BY doc_count DESC
        """, (naming_series,), as_dict=True)

		if not companies:
			# ✅ SE NÃO ENCONTROU, USAR EMPRESAS PORTUGUESAS
			companies = frappe.get_all("Company",
									   filters={"country": "Portugal"},
									   fields=["name as company"])

		return [c["company"] for c in companies]

	except Exception as e:
		frappe.log_error(f"Erro ao obter empresas para série {naming_series}: {str(e)}")
		return []


def create_portugal_series_config_new_approach(series_info, doctype, company):
	"""
	✅ CORRIGIDO: Cria Portugal Series Configuration (nova abordagem)
	"""
	try:
		naming_series = series_info['naming_series']

		# ✅ EXTRAIR OU GERAR PREFIXO (NOVA ABORDAGEM)
		prefix = extract_or_generate_prefix_new_approach(naming_series, doctype, company)

		if not prefix:
			return None

		# ✅ VERIFICAR SE JÁ EXISTE
		if frappe.db.exists("Portugal Series Configuration", {
			"prefix": prefix,
			"company": company,
			"document_type": doctype
		}):
			return None

		# ✅ OBTER SEQUÊNCIA ATUAL
		current_sequence = get_current_sequence_new_approach(doctype, company, naming_series)

		# ✅ OBTER INFORMAÇÕES DO DOCUMENTO
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
		doc_info = PORTUGAL_DOCUMENT_TYPES.get(doctype, {
			"code": extract_code_from_naming_series(naming_series),
			"name": doctype,
			"description": f"Migrado de {naming_series}"
		})

		# ✅ CRIAR NOVA CONFIGURAÇÃO (FORMATO NOVO)
		series_doc = frappe.get_doc({
			"doctype": "Portugal Series Configuration",
			"series_name": f"{doc_info['name']} - {prefix}",
			"company": company,
			"document_type": doctype,
			"prefix": prefix,
			"naming_series": f"{prefix}.####",  # ✅ FORMATO NOVO
			"current_sequence": current_sequence,
			"is_active": 1,
			"is_communicated": 0,
			"at_environment": "test",
			"document_code": doc_info.get('code', prefix[:2]),
			"year_code": str(today().year),
			"company_code": frappe.db.get_value("Company", company, "abbr") or "COMP",
			"naming_pattern": f"{prefix}.####",
			"atcud_pattern": "0.{sequence}",
			"migrated_from_existing": 1,
			"original_naming_series": naming_series,
			"notes": f"Migrado de naming_series: {naming_series}"
		})

		series_doc.insert(ignore_permissions=True)

		frappe.logger().info(f"✅ Portugal Series Configuration criada: {series_doc.name}")
		return series_doc.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar configuração de série: {str(e)}")
		return None


def extract_or_generate_prefix_new_approach(naming_series, doctype, company):
	"""
	✅ NOVO: Extrai ou gera prefixo no formato novo (sem hífens)
	"""
	try:
		# ✅ OBTER ABREVIATURA DA EMPRESA
		company_abbr = frappe.db.get_value("Company", company, "abbr") or "COMP"
		current_year = today().year

		# ✅ TENTAR EXTRAIR CÓDIGO DA NAMING_SERIES EXISTENTE
		code = extract_code_from_naming_series(naming_series)

		if not code:
			# ✅ USAR CÓDIGO PADRÃO DO DOCTYPE
			from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
			doc_info = PORTUGAL_DOCUMENT_TYPES.get(doctype)
			code = doc_info['code'] if doc_info else doctype[:2].upper()

		# ✅ GERAR PREFIXO NO FORMATO NOVO: XXYYYY + EMPRESA
		prefix = f"{code}{current_year}{company_abbr}"

		return prefix

	except Exception as e:
		frappe.log_error(f"Erro ao extrair/gerar prefixo: {str(e)}")
		return None


def extract_code_from_naming_series(naming_series):
	"""
	✅ NOVO: Extrai código da naming_series existente
	"""
	try:
		# ✅ PADRÕES PARA EXTRAIR CÓDIGO
		patterns = [
			r'^([A-Z]{2,4})\d{4}[A-Z0-9]{1,4}\.####$',  # FT2025DSY.####
			r'^([A-Z]{2,4})-',  # FT-YYYY-####
			r'^([A-Z]{2,4})\.',  # FT.####
			r'^([A-Z]{2,4})$',  # FT
			r'^([A-Z]{2,4})'  # FT qualquer coisa
		]

		for pattern in patterns:
			match = re.match(pattern, naming_series)
			if match:
				return match.group(1)

		return None

	except Exception:
		return None


def get_current_sequence_new_approach(doctype, company, naming_series):
	"""
	✅ CORRIGIDO: Obtém sequência atual baseada em documentos existentes
	"""
	try:
		# ✅ PROCURAR ÚLTIMO DOCUMENTO COM ESTA NAMING_SERIES
		last_doc = frappe.db.sql(f"""
            SELECT name
            FROM `tab{doctype}`
            WHERE company = %s
            AND naming_series = %s
            AND docstatus != 2
            ORDER BY creation DESC
            LIMIT 1
        """, (company, naming_series), as_dict=True)

		if last_doc:
			# ✅ EXTRAIR NÚMERO DO ÚLTIMO DOCUMENTO
			doc_name = last_doc[0]["name"]
			number = extract_document_number_new_approach(doc_name)
			return number + 1

		return 1

	except Exception as e:
		frappe.log_error(f"Erro ao obter sequência atual: {str(e)}")
		return 1


def extract_document_number_new_approach(document_name):
	"""
	✅ CORRIGIDO: Extrai número do documento (nova abordagem)
	"""
	try:
		# ✅ PADRÕES PARA EXTRAIR NÚMERO
		patterns = [
			r'\.(\d+)$',  # .000001
			r'-(\d+)$',  # -000001
			r'(\d+)$',  # 000001
			r'[A-Z]+(\d+)$'  # FT2025DSY000001
		]

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return cint(match.group(1))

		return 0

	except Exception:
		return 0


def migrate_existing_documents_new_approach():
	"""
	✅ CORRIGIDO: Migra documentos existentes (SEM usar campo portugal_series)
	"""
	try:
		# ✅ OBTER TODAS AS SÉRIES CRIADAS
		series_configs = frappe.get_all("Portugal Series Configuration",
										filters={"migrated_from_existing": 1},
										fields=["name", "document_type", "company",
												"original_naming_series", "prefix"])

		migrated_docs = 0

		for config in series_configs:
			try:
				# ✅ GERAR ATCUD PARA DOCUMENTOS EXISTENTES (SEM ATUALIZAR portugal_series)
				docs_to_update = frappe.db.sql(f"""
                    SELECT name, naming_series
                    FROM `tab{config["document_type"]}`
                    WHERE company = %s
                    AND naming_series = %s
                    AND (atcud_code IS NULL OR atcud_code = '')
                    AND docstatus != 2
                    ORDER BY creation ASC
                    LIMIT 100
                """, (config["company"], config["original_naming_series"]), as_dict=True)

				for doc in docs_to_update:
					try:
						# ✅ GERAR ATCUD PARA DOCUMENTO EXISTENTE
						atcud_code = generate_atcud_for_existing_document(doc, config)

						if atcud_code:
							# ✅ ATUALIZAR APENAS ATCUD_CODE (NÃO portugal_series)
							frappe.db.set_value(config["document_type"], doc["name"],
												"atcud_code", atcud_code)
							migrated_docs += 1

					except Exception as e:
						frappe.log_error(f"Erro ao migrar documento {doc['name']}: {str(e)}")

				if len(docs_to_update) > 0:
					frappe.logger().info(
						f"✅ Migrados {len(docs_to_update)} documentos para série {config['name']}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar documentos da série {config['name']}: {str(e)}")

		frappe.logger().info(f"✅ Total de documentos migrados (nova abordagem): {migrated_docs}")

	except Exception as e:
		frappe.log_error(f"Erro na migração de documentos: {str(e)}")


def generate_atcud_for_existing_document(doc, config):
	"""
	✅ NOVO: Gera ATCUD para documento existente
	"""
	try:
		# ✅ EXTRAIR SEQUENCIAL DO NOME DO DOCUMENTO
		sequence = extract_document_number_new_approach(doc["name"])

		if sequence > 0:
			# ✅ FORMATO NOVO: 0.SEQUENCIAL
			atcud_code = f"0.{sequence}"
			return atcud_code

		return None

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD para documento {doc['name']}: {str(e)}")
		return None


def setup_naming_series_property_setters():
	"""
	✅ NOVO: Configura Property Setters para naming_series
	"""
	try:
		# ✅ OBTER SÉRIES AGRUPADAS POR DOCTYPE
		series_by_doctype = {}

		all_series = frappe.get_all("Portugal Series Configuration",
									filters={"is_active": 1},
									fields=["naming_series", "document_type"])

		for series in all_series:
			if series.document_type not in series_by_doctype:
				series_by_doctype[series.document_type] = []
			if series.naming_series not in series_by_doctype[series.document_type]:
				series_by_doctype[series.document_type].append(series.naming_series)

		# ✅ CRIAR PROPERTY SETTERS
		for doctype, naming_series_list in series_by_doctype.items():
			try:
				ps_name = f"{doctype}-naming_series-options"

				# ✅ ATUALIZAR OU CRIAR PROPERTY SETTER
				naming_options = '\n'.join(naming_series_list)

				if frappe.db.exists("Property Setter", ps_name):
					# ✅ ATUALIZAR EXISTENTE
					frappe.db.set_value("Property Setter", ps_name, "value", naming_options)
				else:
					# ✅ CRIAR NOVO
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
					f"✅ Property Setter configurado para {doctype}: {len(naming_series_list)} opções")

			except Exception as e:
				frappe.log_error(f"Erro ao configurar Property Setter para {doctype}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar Property Setters: {str(e)}")


def cleanup_old_portugal_series_fields():
	"""
	✅ NOVO: Limpar campos portugal_series antigos
	"""
	try:
		# ✅ BUSCAR E REMOVER CUSTOM FIELDS portugal_series
		old_fields = frappe.db.sql("""
								   SELECT name, dt
								   FROM `tabCustom Field`
								   WHERE fieldname = 'portugal_series'
								   """, as_dict=True)

		removed_count = 0
		for field in old_fields:
			try:
				frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
				removed_count += 1
				frappe.logger().info(f"✅ Campo portugal_series removido de {field.dt}")
			except Exception as e:
				frappe.log_error(f"Erro ao remover campo {field.name}: {str(e)}")

		if removed_count > 0:
			frappe.logger().info(f"✅ Total de campos portugal_series removidos: {removed_count}")

		# ✅ REMOVER PROPERTY SETTERS portugal_series
		old_property_setters = frappe.db.sql("""
											 SELECT name, doc_type
											 FROM `tabProperty Setter`
											 WHERE field_name = 'portugal_series'
											 """, as_dict=True)

		removed_ps = 0
		for ps in old_property_setters:
			try:
				frappe.delete_doc("Property Setter", ps.name, ignore_permissions=True)
				removed_ps += 1
				frappe.logger().info(
					f"✅ Property Setter portugal_series removido de {ps.doc_type}")
			except Exception as e:
				frappe.log_error(f"Erro ao remover Property Setter {ps.name}: {str(e)}")

		if removed_ps > 0:
			frappe.logger().info(
				f"✅ Total de Property Setters portugal_series removidos: {removed_ps}")

	except Exception as e:
		frappe.log_error(f"Erro na limpeza de campos antigos: {str(e)}")


def update_company_settings_new_approach():
	"""
	✅ CORRIGIDO: Atualiza configurações das empresas portuguesas
	"""
	try:
		# ✅ OBTER EMPRESAS PORTUGUESAS
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name"])

		for company in portuguese_companies:
			try:
				company_doc = frappe.get_doc("Company", company["name"])

				# ✅ ATIVAR COMPLIANCE PORTUGUÊS
				if not company_doc.get("portugal_compliance_enabled"):
					company_doc.portugal_compliance_enabled = 1

				# ✅ CONFIGURAR DEFAULTS PORTUGUESES
				if not company_doc.default_currency:
					company_doc.default_currency = "EUR"

				company_doc.save(ignore_permissions=True)

				frappe.logger().info(f"✅ Compliance português ativado para {company['name']}")

			except Exception as e:
				frappe.log_error(f"Erro ao atualizar empresa {company['name']}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao atualizar configurações de empresas: {str(e)}")


def mark_migration_complete_new_approach():
	"""
	✅ CORRIGIDO: Marca migração como completa (nova abordagem)
	"""
	try:
		# ✅ CRIAR REGISTRO DE CONTROLE DA MIGRAÇÃO
		control_prefix = f"MIGRATION{today().year}COMPLETE"

		if not frappe.db.exists("Portugal Series Configuration", {"prefix": control_prefix}):
			default_company = frappe.db.get_value("Company",
												  {"is_default": 1}) or "Default Company"

			control_doc = frappe.get_doc({
				"doctype": "Portugal Series Configuration",
				"series_name": "Controle de Migração - Nova Abordagem",
				"company": default_company,
				"document_type": "Sales Invoice",
				"prefix": control_prefix,
				"naming_series": f"{control_prefix}.####",
				"current_sequence": 1,
				"is_active": 0,  # ✅ INATIVO (apenas controle)
				"is_communicated": 0,
				"migrated_from_existing": 1,
				"notes": "Registro de controle - migração para nova abordagem concluída",
				"document_code": "CTRL",
				"year_code": str(today().year),
				"company_code": "MIGR"
			})
			control_doc.insert(ignore_permissions=True)

			frappe.logger().info("✅ Migração marcada como completa (nova abordagem)")

	except Exception as e:
		frappe.log_error(f"Erro ao marcar migração como completa: {str(e)}")


def validate_migration_success():
	"""
	✅ NOVO: Validar sucesso da migração
	"""
	try:
		# ✅ CONTAR SÉRIES MIGRADAS
		migrated_series = frappe.db.count("Portugal Series Configuration",
										  {"migrated_from_existing": 1})

		# ✅ CONTAR DOCUMENTOS COM ATCUD
		total_docs_with_atcud = 0
		doctypes = ["Sales Invoice", "POS Invoice", "Purchase Invoice", "Payment Entry"]

		for doctype in doctypes:
			try:
				count = frappe.db.sql(f"""
                    SELECT COUNT(*) FROM `tab{doctype}`
                    WHERE atcud_code IS NOT NULL AND atcud_code != ''
                """)[0][0]
				total_docs_with_atcud += count
			except:
				continue

		# ✅ VERIFICAR CAMPOS portugal_series REMOVIDOS
		remaining_portugal_series_fields = frappe.db.count("Custom Field",
														   {"fieldname": "portugal_series"})

		frappe.logger().info(f"""
        📊 VALIDAÇÃO DA MIGRAÇÃO (NOVA ABORDAGEM):
        ✅ Séries migradas: {migrated_series}
        ✅ Documentos com ATCUD: {total_docs_with_atcud}
        ✅ Campos portugal_series restantes: {remaining_portugal_series_fields}
        """)

		return {
			"migrated_series": migrated_series,
			"docs_with_atcud": total_docs_with_atcud,
			"remaining_old_fields": remaining_portugal_series_fields
		}

	except Exception as e:
		frappe.log_error(f"Erro na validação da migração: {str(e)}")
		return None


# ========== FUNÇÕES DE ROLLBACK ADAPTADAS ==========

def rollback_migration_new_approach():
	"""
	✅ CORRIGIDO: Função para reverter migração (nova abordagem)
	"""
	try:
		frappe.logger().info("🔄 Iniciando rollback da migração (nova abordagem)")

		# ✅ REMOVER TODAS AS SÉRIES MIGRADAS
		migrated_series = frappe.get_all("Portugal Series Configuration",
										 filters={"migrated_from_existing": 1})

		for series in migrated_series:
			frappe.delete_doc("Portugal Series Configuration", series["name"],
							  ignore_permissions=True)

		# ✅ LIMPAR ATCUD_CODE DOS DOCUMENTOS (NÃO portugal_series)
		doctypes = ['Sales Invoice', 'POS Invoice', 'Purchase Invoice', 'Payment Entry',
					'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry']

		for doctype in doctypes:
			try:
				frappe.db.sql(
					f"UPDATE `tab{doctype}` SET atcud_code = NULL WHERE atcud_code IS NOT NULL")
			except:
				continue

		# ✅ REMOVER PROPERTY SETTERS CRIADOS
		property_setters = frappe.get_all("Property Setter",
										  filters={"field_name": "naming_series"})

		for ps in property_setters:
			try:
				frappe.delete_doc("Property Setter", ps["name"], ignore_permissions=True)
			except:
				continue

		frappe.db.commit()
		frappe.logger().info("✅ Rollback da migração (nova abordagem) executado")

	except Exception as e:
		frappe.log_error(f"Erro no rollback da migração: {str(e)}")


# ========== FUNÇÃO DE TESTE ==========

def test_migration_new_approach():
	"""
	✅ NOVO: Testar migração sem executar
	"""
	try:
		frappe.logger().info("🧪 TESTE DA MIGRAÇÃO (NOVA ABORDAGEM)")

		# ✅ SIMULAR MIGRAÇÃO
		from portugal_compliance.regional.portugal import PORTUGAL_DOCUMENT_TYPES
		supported_doctypes = list(PORTUGAL_DOCUMENT_TYPES.keys())

		test_results = {}

		for doctype in supported_doctypes:
			existing_series = get_existing_naming_series(doctype)
			portuguese_series = [s for s in existing_series if
								 is_portuguese_series_new_approach(s['naming_series'])]

			test_results[doctype] = {
				"total_series": len(existing_series),
				"portuguese_series": len(portuguese_series),
				"series_list": [s['naming_series'] for s in portuguese_series]
			}

		frappe.logger().info(f"📊 Resultado do teste: {test_results}")
		return test_results

	except Exception as e:
		frappe.log_error(f"Erro no teste da migração: {str(e)}")
		return None
