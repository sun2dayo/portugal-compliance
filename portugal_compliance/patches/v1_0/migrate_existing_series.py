import frappe
from frappe import _
import re
from frappe.utils import cint, now, today
from erpnext.accounts.utils import get_fiscal_year



def execute():
	"""
	Patch para migrar séries existentes para o novo sistema Portugal Series Configuration
	"""
	frappe.logger().info("Iniciando patch: migrate_existing_series")

	try:
		# Verificar se patch já foi executado
		if frappe.db.exists("Portugal Series Configuration", {"migrated_from_existing": 1}):
			frappe.logger().info("Patch migrate_existing_series já foi executado anteriormente")
			return

		# Migrar séries de naming_series existentes
		migrate_naming_series()

		# Migrar dados de documentos existentes
		migrate_existing_documents()

		# Atualizar configurações de empresa
		update_company_settings()

		# Marcar patch como executado
		mark_migration_complete()

		frappe.db.commit()
		frappe.logger().info("Patch migrate_existing_series executado com sucesso")

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Erro no patch migrate_existing_series: {str(e)}",
						 "Portugal Compliance Migration")
		raise


def migrate_naming_series():
	"""
	Migra séries existentes de naming_series para Portugal Series Configuration
	"""
	try:
		# Doctypes suportados para migração
		supported_doctypes = [
			'Sales Invoice', 'Purchase Invoice', 'Payment Entry',
			'Delivery Note', 'Purchase Receipt', 'Journal Entry'
		]

		migrated_count = 0

		for doctype in supported_doctypes:
			try:
				# Obter naming_series atual do doctype
				current_naming = frappe.db.get_value("DocType", doctype, "autoname")

				if not current_naming:
					continue

				# Parse das opções de naming_series
				series_options = [opt.strip() for opt in current_naming.split('\n') if opt.strip()]

				for series_option in series_options:
					# Extrair prefixo da série (ex: "FT-.YYYY.-.####" -> "FT")
					prefix = extract_series_prefix(series_option)

					if prefix and is_portuguese_series(prefix):
						# Obter empresas que usam esta série
						companies = get_companies_using_series(doctype, series_option)

						for company in companies:
							# Criar Portugal Series Configuration se não existir
							series_name = create_portugal_series_config(
								prefix, doctype, company, series_option
							)

							if series_name:
								migrated_count += 1
								frappe.logger().info(f"Série migrada: {series_name}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar séries do {doctype}: {str(e)}")

		frappe.logger().info(f"Total de séries migradas: {migrated_count}")

	except Exception as e:
		frappe.log_error(f"Erro na migração de naming_series: {str(e)}")


def extract_series_prefix(series_option):
	"""
	Extrai prefixo da série do formato naming_series
	"""
	try:
		# Padrões comuns: "FT-.YYYY.-.####", "FT-####", "FT.####"
		patterns = [
			r'^([A-Z]{2,4})-',  # FT-YYYY-####
			r'^([A-Z]{2,4})\.',  # FT.####
			r'^([A-Z]{2,4})$'  # FT
		]

		for pattern in patterns:
			match = re.match(pattern, series_option)
			if match:
				return match.group(1)

		return None

	except Exception:
		return None


def is_portuguese_series(prefix):
	"""
	Verifica se o prefixo corresponde a uma série portuguesa
	"""
	portuguese_prefixes = [
		'FT', 'FS', 'FR', 'FC', 'RC', 'RB', 'GT', 'GR', 'JE', 'NC', 'ND'
	]
	return prefix in portuguese_prefixes


def get_companies_using_series(doctype, series_option):
	"""
	Obtém empresas que têm documentos usando esta série
	"""
	try:
		# Procurar documentos que usam esta série
		companies = frappe.db.sql("""
            SELECT DISTINCT company
            FROM `tab{doctype}`
            WHERE naming_series = %s
            AND docstatus != 2
            LIMIT 10
        """.format(doctype=doctype), (series_option,), as_dict=True)

		if not companies:
			# Se não encontrou documentos, usar empresas portuguesas
			companies = frappe.get_all("Company",
									   filters={"country": "Portugal"},
									   fields=["name as company"])

		return [c["company"] for c in companies]

	except Exception as e:
		frappe.log_error(f"Erro ao obter empresas para série {series_option}: {str(e)}")
		return []


def create_portugal_series_config(prefix, doctype, company, original_series):
	"""
	Cria configuração de série portuguesa
	"""
	try:
		# Obter ano fiscal atual
		try:
			fiscal_year = get_fiscal_year(today(), company=company)[0]
			year = fiscal_year.split("-")[0]
		except:
			year = str(today().year)

		# Obter abreviação da empresa
		company_abbr = frappe.db.get_value("Company", company, "abbr") or "COMP"

		# Gerar nome da série portuguesa
		series_prefix = f"{prefix}-{year}-{company_abbr}"

		# Verificar se já existe
		if frappe.db.exists("Portugal Series Configuration", {
			"series_prefix": series_prefix,
			"company": company
		}):
			return None

		# Obter sequência atual baseada em documentos existentes
		current_sequence = get_current_sequence(doctype, company, original_series)

		# Criar nova configuração
		series_doc = frappe.get_doc({
			"doctype": "Portugal Series Configuration",
			"series_prefix": series_prefix,
			"document_type": doctype,
			"company": company,
			"current_sequence": current_sequence,
			"is_communicated": 0,
			"migrated_from_existing": 1,
			"original_series": original_series
		})

		series_doc.insert(ignore_permissions=True)

		return series_doc.name

	except Exception as e:
		frappe.log_error(f"Erro ao criar configuração de série: {str(e)}")
		return None


def get_current_sequence(doctype, company, series_option):
	"""
	Obtém sequência atual baseada em documentos existentes
	"""
	try:
		# Procurar último documento com esta série
		last_doc = frappe.db.sql("""
            SELECT name
            FROM `tab{doctype}`
            WHERE company = %s
            AND naming_series = %s
            AND docstatus != 2
            ORDER BY creation DESC
            LIMIT 1
        """.format(doctype=doctype), (company, series_option), as_dict=True)

		if last_doc:
			# Extrair número do último documento
			doc_name = last_doc[0]["name"]
			number = extract_document_number(doc_name)
			return number + 1

		return 1

	except Exception as e:
		frappe.log_error(f"Erro ao obter sequência atual: {str(e)}")
		return 1


def extract_document_number(document_name):
	"""
	Extrai número do documento
	"""
	try:
		patterns = [r'\.(\d+)$', r'-(\d+)$', r'(\d+)$']

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return cint(match.group(1))

		return 0

	except Exception:
		return 0


def migrate_existing_documents():
	"""
	Migra documentos existentes para usar Portugal Series
	"""
	try:
		# Obter todas as séries criadas
		series_configs = frappe.get_all("Portugal Series Configuration",
										filters={"migrated_from_existing": 1},
										fields=["name", "document_type", "company",
												"original_series"])

		migrated_docs = 0

		for config in series_configs:
			try:
				# Atualizar documentos existentes
				frappe.db.sql("""
                    UPDATE `tab{doctype}`
                    SET portugal_series = %s
                    WHERE company = %s
                    AND naming_series = %s
                    AND (portugal_series IS NULL OR portugal_series = '')
                """.format(doctype=config["document_type"]),
							  (config["name"], config["company"], config["original_series"]))

				# Contar documentos atualizados
				count = frappe.db.sql("""
                    SELECT COUNT(*) as count
                    FROM `tab{doctype}`
                    WHERE portugal_series = %s
                """.format(doctype=config["document_type"]), (config["name"],))[0][0]

				migrated_docs += count

				if count > 0:
					frappe.logger().info(
						f"Migrados {count} documentos para série {config['name']}")

			except Exception as e:
				frappe.log_error(f"Erro ao migrar documentos da série {config['name']}: {str(e)}")

		frappe.logger().info(f"Total de documentos migrados: {migrated_docs}")

	except Exception as e:
		frappe.log_error(f"Erro na migração de documentos: {str(e)}")


def update_company_settings():
	"""
	Atualiza configurações das empresas portuguesas
	"""
	try:
		# Obter empresas portuguesas
		portuguese_companies = frappe.get_all("Company",
											  filters={"country": "Portugal"},
											  fields=["name"])

		for company in portuguese_companies:
			try:
				company_doc = frappe.get_doc("Company", company["name"])

				# Ativar compliance português se não estiver ativo
				if not company_doc.get("portugal_compliance_enabled"):
					company_doc.portugal_compliance_enabled = 1
					company_doc.save(ignore_permissions=True)

					frappe.logger().info(f"Compliance português ativado para {company['name']}")

			except Exception as e:
				frappe.log_error(f"Erro ao atualizar empresa {company['name']}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao atualizar configurações de empresas: {str(e)}")


def mark_migration_complete():
	"""
	Marca migração como completa criando registro de controle
	"""
	try:
		# Criar registro de controle da migração
		if not frappe.db.exists("Portugal Series Configuration",
								{"series_prefix": "MIGRATION-COMPLETE"}):
			control_doc = frappe.get_doc({
				"doctype": "Portugal Series Configuration",
				"series_prefix": "MIGRATION-COMPLETE",
				"document_type": "Sales Invoice",
				"company": frappe.db.get_value("Company", {"is_default": 1}) or "Default Company",
				"current_sequence": 1,
				"is_communicated": 0,
				"migrated_from_existing": 1,
				"description": "Registro de controle - migração concluída"
			})
			control_doc.insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Erro ao marcar migração como completa: {str(e)}")


def cleanup_old_data():
	"""
	Limpeza opcional de dados antigos (executar com cuidado)
	"""
	try:
		# Esta função pode ser usada para limpar dados antigos
		# após confirmação de que a migração foi bem-sucedida

		# Exemplo: remover séries antigas que não são mais usadas
		# ATENÇÃO: Só executar após verificação manual

		frappe.logger().info(
			"Limpeza de dados antigos - função disponível mas não executada automaticamente")

	except Exception as e:
		frappe.log_error(f"Erro na limpeza de dados antigos: {str(e)}")


# Função auxiliar para rollback em caso de problemas
def rollback_migration():
	"""
	Função para reverter migração em caso de problemas
	"""
	try:
		# Remover todas as séries migradas
		migrated_series = frappe.get_all("Portugal Series Configuration",
										 filters={"migrated_from_existing": 1})

		for series in migrated_series:
			frappe.delete_doc("Portugal Series Configuration", series["name"],
							  ignore_permissions=True)

		# Limpar campo portugal_series dos documentos
		doctypes = ['Sales Invoice', 'Purchase Invoice', 'Payment Entry',
					'Delivery Note', 'Purchase Receipt', 'Journal Entry']

		for doctype in doctypes:
			frappe.db.sql(f"UPDATE `tab{doctype}` SET portugal_series = NULL")

		frappe.db.commit()
		frappe.logger().info("Rollback da migração executado")

	except Exception as e:
		frappe.log_error(f"Erro no rollback da migração: {str(e)}")
