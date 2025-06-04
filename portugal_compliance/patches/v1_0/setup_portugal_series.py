import frappe
from frappe import _
from frappe.utils import today
from erpnext.accounts.utils import get_fiscal_year



def execute():
	"""
	Patch para configurar séries portuguesas durante instalação/atualização do módulo
	"""
	frappe.logger().info("Iniciando patch: setup_portugal_series")

	try:
		# Verificar se patch já foi executado
		if frappe.db.exists("Portugal Series Configuration", {"series_prefix": "FT-2025-DEFAULT"}):
			frappe.logger().info("Patch setup_portugal_series já foi executado anteriormente")
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
				create_series_for_company(company)

		# Configurar campos customizados se necessário
		setup_custom_fields()

		# Configurar property setters
		setup_property_setters()

		frappe.db.commit()
		frappe.logger().info("Patch setup_portugal_series executado com sucesso")

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Erro no patch setup_portugal_series: {str(e)}",
						 "Portugal Compliance Patch")
		raise


def get_portuguese_companies():
	"""
	Obtém todas as empresas configuradas para Portugal
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
	Cria séries para empresa padrão se não existirem empresas portuguesas
	"""
	try:
		# Verificar se existe empresa padrão
		default_company = frappe.db.get_value("Company", {"is_default": 1})

		if not default_company:
			# Criar empresa padrão portuguesa
			default_company = create_default_portuguese_company()

		# Ativar compliance português na empresa padrão
		enable_portugal_compliance(default_company)

		# Criar séries para empresa padrão
		create_series_for_company({"name": default_company, "abbr": "DEFAULT"})

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries padrão: {str(e)}")


def create_default_portuguese_company():
	"""
	Cria empresa padrão portuguesa se não existir
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
	Ativa compliance português para uma empresa
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


def create_series_for_company(company):
	"""
	Cria séries documentais para uma empresa
	"""
	try:
		company_name = company["name"]
		company_abbr = company.get("abbr", "COMP")

		# Obter ano fiscal atual
		try:
			fiscal_year = get_fiscal_year(today(), company=company_name)[0]
			year = fiscal_year.split("-")[0]
		except:
			year = str(today().year)

		# Definir séries padrão por tipo de documento
		default_series = {
			"Sales Invoice": [
				{"prefix": "FT", "description": "Faturas de Venda"},
				{"prefix": "FS", "description": "Faturas Simplificadas"},
				{"prefix": "FR", "description": "Faturas-Recibo"},
				{"prefix": "NC-FT", "description": "Notas de Crédito"},
				{"prefix": "ND-FT", "description": "Notas de Débito"}
			],
			"Purchase Invoice": [
				{"prefix": "FC", "description": "Faturas de Compra"}
			],
			"Payment Entry": [
				{"prefix": "RC", "description": "Recibos"},
				{"prefix": "RB", "description": "Recibos Bancários"}
			],
			"Delivery Note": [
				{"prefix": "GT", "description": "Guias de Transporte"}
			],
			"Purchase Receipt": [
				{"prefix": "GR", "description": "Guias de Receção"}
			],
			"Journal Entry": [
				{"prefix": "JE", "description": "Lançamentos Contabilísticos"}
			]
		}

		created_series = []

		for doctype, series_list in default_series.items():
			for series_info in series_list:
				series_prefix = f"{series_info['prefix']}-{year}-{company_abbr}"

				# Verificar se série já existe
				if not frappe.db.exists("Portugal Series Configuration", {
					"series_prefix": series_prefix,
					"company": company_name
				}):
					# Criar nova série
					series_doc = frappe.get_doc({
						"doctype": "Portugal Series Configuration",
						"series_prefix": series_prefix,
						"document_type": doctype,
						"company": company_name,
						"current_sequence": 1,
						"is_communicated": 0,
						"description": series_info["description"]
					})

					series_doc.insert(ignore_permissions=True)
					created_series.append(series_prefix)

					frappe.logger().info(f"Série criada: {series_prefix} para {company_name}")

		if created_series:
			frappe.logger().info(
				f"Criadas {len(created_series)} séries para empresa {company_name}")

		return created_series

	except Exception as e:
		frappe.log_error(f"Erro ao criar séries para empresa {company['name']}: {str(e)}")
		return []


def setup_custom_fields():
	"""
	Configura campos customizados necessários
	"""
	try:
		# Verificar se campos já existem
		if frappe.db.exists("Custom Field", "Sales Invoice-atcud_code"):
			frappe.logger().info("Campos customizados já existem")
			return

		# Lista de campos customizados a criar
		custom_fields = [
			{
				"dt": "Sales Invoice",
				"fieldname": "atcud_code",
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"insert_after": "naming_series",
				"read_only": 1,
				"print_hide": 0,
				"bold": 1,
				"description": "Código Único de Documento - obrigatório em Portugal"
			},
			{
				"dt": "Sales Invoice",
				"fieldname": "portugal_series",
				"label": "Portugal Series",
				"fieldtype": "Link",
				"options": "Portugal Series Configuration",
				"insert_after": "atcud_code",
				"reqd": 1,
				"description": "Série portuguesa configurada para este documento"
			},
			{
				"dt": "Company",
				"fieldname": "portugal_compliance_enabled",
				"label": "Portugal Compliance Enabled",
				"fieldtype": "Check",
				"insert_after": "country",
				"default": "0",
				"description": "Ativar conformidade fiscal portuguesa para esta empresa"
			}
		]

		# Criar campos para todos os doctypes suportados
		supported_doctypes = ["Sales Invoice", "Purchase Invoice", "Payment Entry",
							  "Delivery Note", "Purchase Receipt", "Journal Entry"]

		for doctype in supported_doctypes:
			if doctype == "Sales Invoice":
				continue  # Já definido acima

			custom_fields.extend([
				{
					"dt": doctype,
					"fieldname": "atcud_code",
					"label": "ATCUD Code",
					"fieldtype": "Data",
					"insert_after": "naming_series",
					"read_only": 1,
					"print_hide": 0,
					"description": "Código Único de Documento - obrigatório em Portugal"
				},
				{
					"dt": doctype,
					"fieldname": "portugal_series",
					"label": "Portugal Series",
					"fieldtype": "Link",
					"options": "Portugal Series Configuration",
					"insert_after": "atcud_code",
					"reqd": 1,
					"description": "Série portuguesa configurada para este documento"
				}
			])

		# Criar campos customizados
		for field_config in custom_fields:
			field_name = f"{field_config['dt']}-{field_config['fieldname']}"

			if not frappe.db.exists("Custom Field", field_name):
				custom_field = frappe.get_doc({
					"doctype": "Custom Field",
					"name": field_name,
					**field_config
				})
				custom_field.insert(ignore_permissions=True)

				frappe.logger().info(f"Campo customizado criado: {field_name}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar campos customizados: {str(e)}")


def setup_property_setters():
	"""
	Configura property setters para adequar ERPNext ao contexto português
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
			}
		]

		for ps_config in property_setters:
			ps_name = f"{ps_config['doc_type']}-{ps_config['field_name']}-{ps_config['property']}"

			if not frappe.db.exists("Property Setter", ps_name):
				property_setter = frappe.get_doc({
					"doctype": "Property Setter",
					"name": ps_name,
					"property_type": "Data",
					**ps_config
				})
				property_setter.insert(ignore_permissions=True)

				frappe.logger().info(f"Property setter criado: {ps_name}")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar property setters: {str(e)}")


def update_naming_series():
	"""
	Atualiza opções de naming series para incluir séries portuguesas
	"""
	try:
		# Obter todas as séries criadas
		series = frappe.get_all("Portugal Series Configuration",
								fields=["series_prefix", "document_type"])

		# Agrupar por tipo de documento
		series_by_doctype = {}
		for s in series:
			if s.document_type not in series_by_doctype:
				series_by_doctype[s.document_type] = []
			series_by_doctype[s.document_type].append(f"{s.series_prefix}.####")

		# Atualizar naming series para cada doctype
		for doctype, series_list in series_by_doctype.items():
			try:
				# Obter opções atuais
				current_options = frappe.db.get_value("DocType", doctype, "autoname") or ""
				current_list = [opt.strip() for opt in current_options.split('\n') if opt.strip()]

				# Adicionar novas séries
				for series in series_list:
					if series not in current_list:
						current_list.append(series)

				# Atualizar doctype
				new_options = '\n'.join(current_list)
				frappe.db.set_value("DocType", doctype, "autoname", new_options)

				frappe.logger().info(f"Naming series atualizado para {doctype}")

			except Exception as e:
				frappe.log_error(f"Erro ao atualizar naming series para {doctype}: {str(e)}")

	except Exception as e:
		frappe.log_error(f"Erro ao atualizar naming series: {str(e)}")


def create_default_auth_settings():
	"""
	Cria configurações de autenticação padrão
	"""
	try:
		if not frappe.db.exists("Portugal Auth Settings", "Portugal Auth Settings"):
			auth_settings = frappe.get_doc({
				"doctype": "Portugal Auth Settings",
				"sandbox_mode": 1,
				"at_webservice_url": "https://servicos-test.portaldasfinancas.gov.pt:722/SeriesWSService"
			})
			auth_settings.insert(ignore_permissions=True)

			frappe.logger().info("Configurações de autenticação padrão criadas")

	except Exception as e:
		frappe.log_error(f"Erro ao criar configurações de autenticação: {str(e)}")


def setup_permissions():
	"""
	Configura permissões para os novos doctypes
	"""
	try:
		# Permissões para Portugal Series Configuration
		if not frappe.db.exists("Custom DocPerm", {
			"parent": "Portugal Series Configuration",
			"role": "System Manager"
		}):
			frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": "Portugal Series Configuration",
				"parenttype": "DocType",
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1
			}).insert(ignore_permissions=True)

		# Permissões para ATCUD Log
		if not frappe.db.exists("Custom DocPerm", {
			"parent": "ATCUD Log",
			"role": "Accounts Manager"
		}):
			frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": "ATCUD Log",
				"parenttype": "DocType",
				"role": "Accounts Manager",
				"read": 1,
				"write": 0,
				"create": 0,
				"delete": 0
			}).insert(ignore_permissions=True)

		frappe.logger().info("Permissões configuradas")

	except Exception as e:
		frappe.log_error(f"Erro ao configurar permissões: {str(e)}")


# Executar configurações adicionais
def post_setup_tasks():
	"""
	Tarefas adicionais após configuração principal
	"""
	try:
		# Criar configurações de autenticação
		create_default_auth_settings()

		# Configurar permissões
		setup_permissions()

		# Atualizar naming series
		update_naming_series()

		# Limpar cache
		frappe.clear_cache()

		frappe.logger().info("Tarefas pós-configuração concluídas")

	except Exception as e:
		frappe.log_error(f"Erro nas tarefas pós-configuração: {str(e)}")


# Executar tarefas pós-configuração
post_setup_tasks()
