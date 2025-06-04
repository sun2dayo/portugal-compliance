import frappe
from frappe import _
from frappe.utils import getdate, formatdate, now, get_site_path
import os
import hashlib
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import time
from datetime import datetime


class SAFTGenerator:
	def __init__(self):
		self.template_path = os.path.join(
			frappe.get_app_path("portugal_compliance"),
			"templates", "saf_t"
		)
		self.records_count = 0

	def generate_saft(self, company, from_date, to_date, export_type="full"):
		"""
		Gera arquivo SAF-T XML para empresa e período especificado
		"""
		try:
			start_time = time.time()

			# Converter datas para objetos date
			from_date = getdate(from_date)
			to_date = getdate(to_date)

			# Obter dados da empresa
			company_doc = frappe.get_doc("Company", company)

			# Preparar contexto para template
			context = self.prepare_context(company_doc, from_date, to_date, export_type)

			# Carregar e renderizar template
			saft_xml = self.render_template(context)

			# Validar XML gerado
			if self.validate_xml_structure(saft_xml):
				processing_time = time.time() - start_time
				frappe.publish_realtime('saft_generation_progress', {
					'status': 'completed',
					'processing_time': processing_time
				})

				return saft_xml
			else:
				raise Exception("XML gerado não passou na validação")

		except Exception as e:
			frappe.log_error(f"Erro na geração SAF-T: {str(e)}")
			raise

	def prepare_context(self, company_doc, from_date, to_date, export_type):
		"""
		Prepara contexto com todos os dados necessários para o template
		"""
		context = {
			# Header information
			"company": company_doc,
			"from_date": from_date,
			"to_date": to_date,
			"start_date": formatdate(from_date, "yyyy-MM-dd"),
			"end_date": formatdate(to_date, "yyyy-MM-dd"),
			"fiscal_year": from_date.year,
			"generation_date": formatdate(now(), "yyyy-MM-dd"),
			"generation_time": now(),
			"certificate_number": company_doc.get("at_certificate_number", ""),
			"export_type": export_type,

			# Master files
			"customers": self.get_customers_data(company_doc.name, from_date, to_date),
			"suppliers": self.get_suppliers_data(company_doc.name, from_date, to_date),
			"products": self.get_products_data(company_doc.name, from_date, to_date),
			"tax_table": self.get_tax_table_data(company_doc.name),

			# Source documents
			"sales_invoices": self.get_sales_invoices_data(company_doc.name, from_date, to_date),
			"purchase_invoices": self.get_purchase_invoices_data(company_doc.name, from_date,
																 to_date),
			"payments": self.get_payments_data(company_doc.name, from_date, to_date),

			# Accounting data (if export_type includes accounting)
			"chart_of_accounts": self.get_chart_of_accounts(company_doc.name) if export_type in [
				"full", "accounting"] else [],
			"journal_entries": self.get_journal_entries_data(company_doc.name, from_date,
															 to_date) if export_type in ["full",
																						 "accounting"] else [],

			# Movement of goods (if export_type includes movement)
			"stock_movements": self.get_stock_movements_data(company_doc.name, from_date,
															 to_date) if export_type in ["full",
																						 "movement"] else []
		}

		return context

	def get_customers_data(self, company, from_date, to_date):
		"""
		Obtém dados dos clientes
		"""
		customers = frappe.db.sql("""
								  SELECT DISTINCT c.name,
												  c.customer_name,
												  c.tax_id,
												  c.customer_type,
												  a.address_line1,
												  a.address_line2,
												  a.city,
												  a.pincode,
												  a.country,
												  con.email_id,
												  con.phone
								  FROM `tabCustomer` c
										   LEFT JOIN `tabDynamic Link` dl
													 ON dl.link_name = c.name AND dl.link_doctype = 'Customer'
										   LEFT JOIN `tabAddress` a
													 ON a.name = dl.parent AND dl.parenttype = 'Address'
										   LEFT JOIN `tabContact` con ON con.name = (SELECT parent
																					 FROM `tabDynamic Link`
																					 WHERE link_name = c.name
																					   AND link_doctype = 'Customer'
																					   AND parenttype = 'Contact'
									  LIMIT 1
									  )
								  WHERE EXISTS (
									  SELECT 1 FROM `tabSales Invoice` si
									  WHERE si.customer = c.name
									AND si.company = %s
									AND si.posting_date BETWEEN %s
									AND %s
									AND si.docstatus = 1
									  )
								  ORDER BY c.name
								  """, (company, from_date, to_date), as_dict=True)

		return customers

	def get_suppliers_data(self, company, from_date, to_date):
		"""
		Obtém dados dos fornecedores
		"""
		suppliers = frappe.db.sql("""
								  SELECT DISTINCT s.name,
												  s.supplier_name,
												  s.tax_id,
												  s.supplier_type,
												  a.address_line1,
												  a.address_line2,
												  a.city,
												  a.pincode,
												  a.country,
												  con.email_id,
												  con.phone
								  FROM `tabSupplier` s
										   LEFT JOIN `tabDynamic Link` dl
													 ON dl.link_name = s.name AND dl.link_doctype = 'Supplier'
										   LEFT JOIN `tabAddress` a
													 ON a.name = dl.parent AND dl.parenttype = 'Address'
										   LEFT JOIN `tabContact` con ON con.name = (SELECT parent
																					 FROM `tabDynamic Link`
																					 WHERE link_name = s.name
																					   AND link_doctype = 'Supplier'
																					   AND parenttype = 'Contact'
									  LIMIT 1
									  )
								  WHERE EXISTS (
									  SELECT 1 FROM `tabPurchase Invoice` pi
									  WHERE pi.supplier = s.name
									AND pi.company = %s
									AND pi.posting_date BETWEEN %s
									AND %s
									AND pi.docstatus = 1
									  )
								  ORDER BY s.name
								  """, (company, from_date, to_date), as_dict=True)

		return suppliers

	def get_products_data(self, company, from_date, to_date):
		"""
		Obtém dados dos produtos/serviços
		"""
		products = frappe.db.sql("""
								 SELECT DISTINCT i.name,
												 i.item_name,
												 i.item_code,
												 i.description,
												 i.item_group,
												 i.stock_uom,
												 i.is_stock_item,
												 i.has_variants
								 FROM `tabItem` i
								 WHERE EXISTS (SELECT 1
											   FROM `tabSales Invoice Item` sii
														INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
											   WHERE sii.item_code = i.item_code
												 AND si.company = %s
												 AND si.posting_date BETWEEN %s AND %s
												 AND si.docstatus = 1)
									OR EXISTS (SELECT 1
											   FROM `tabPurchase Invoice Item` pii
														INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
											   WHERE pii.item_code = i.item_code
												 AND pi.company = %s
												 AND pi.posting_date BETWEEN %s AND %s
												 AND pi.docstatus = 1)
								 ORDER BY i.item_code
								 """, (company, from_date, to_date, company, from_date, to_date),
								 as_dict=True)

		return products

	def get_tax_table_data(self, company):
		"""
		Obtém tabela de impostos
		"""
		tax_rates = frappe.db.sql("""
								  SELECT DISTINCT at.account_head, at.rate, at.description
								  FROM `tabAccount` a
										   INNER JOIN `tabSales Taxes and Charges` at
								  ON at.account_head = a.name
								  WHERE a.company = %s
									AND a.account_type = 'Tax'
									AND a.is_group = 0
								  ORDER BY at.rate
								  """, (company,), as_dict=True)

		return tax_rates

	def get_sales_invoices_data(self, company, from_date, to_date):
		"""
		Obtém dados das faturas de venda
		"""
		invoices = frappe.db.sql("""
								 SELECT si.name,
										si.customer,
										si.posting_date,
										si.due_date,
										si.total,
										si.grand_total,
										si.outstanding_amount,
										si.currency,
										si.conversion_rate,
										si.status,
										si.atcud_code,
										si.portugal_series,
										sii.item_code,
										sii.item_name,
										sii.qty,
										sii.rate,
										sii.amount,
										sii.base_amount
								 FROM `tabSales Invoice` si
										  INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
								 WHERE si.company = %s
								   AND si.posting_date BETWEEN %s AND %s
								   AND si.docstatus = 1
								 ORDER BY si.posting_date, si.name
								 """, (company, from_date, to_date), as_dict=True)

		# Agrupar itens por fatura
		grouped_invoices = {}
		for invoice in invoices:
			invoice_id = invoice.name
			if invoice_id not in grouped_invoices:
				grouped_invoices[invoice_id] = {
					'header': {
						'name': invoice.name,
						'customer': invoice.customer,
						'posting_date': invoice.posting_date,
						'due_date': invoice.due_date,
						'total': invoice.total,
						'grand_total': invoice.grand_total,
						'outstanding_amount': invoice.outstanding_amount,
						'currency': invoice.currency,
						'conversion_rate': invoice.conversion_rate,
						'status': invoice.status,
						'atcud_code': invoice.atcud_code,
						'portugal_series': invoice.portugal_series
					},
					'items': []
				}

			grouped_invoices[invoice_id]['items'].append({
				'item_code': invoice.item_code,
				'item_name': invoice.item_name,
				'qty': invoice.qty,
				'rate': invoice.rate,
				'amount': invoice.amount,
				'base_amount': invoice.base_amount
			})

		self.records_count += len(grouped_invoices)
		return list(grouped_invoices.values())

	def get_purchase_invoices_data(self, company, from_date, to_date):
		"""
		Obtém dados das faturas de compra
		"""
		invoices = frappe.db.sql("""
								 SELECT pi.name,
										pi.supplier,
										pi.posting_date,
										pi.due_date,
										pi.total,
										pi.grand_total,
										pi.outstanding_amount,
										pi.currency,
										pi.conversion_rate,
										pi.status,
										pi.atcud_code,
										pi.portugal_series,
										pii.item_code,
										pii.item_name,
										pii.qty,
										pii.rate,
										pii.amount,
										pii.base_amount
								 FROM `tabPurchase Invoice` pi
										  INNER JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
								 WHERE pi.company = %s
								   AND pi.posting_date BETWEEN %s AND %s
								   AND pi.docstatus = 1
								 ORDER BY pi.posting_date, pi.name
								 """, (company, from_date, to_date), as_dict=True)

		# Agrupar itens por fatura
		grouped_invoices = {}
		for invoice in invoices:
			invoice_id = invoice.name
			if invoice_id not in grouped_invoices:
				grouped_invoices[invoice_id] = {
					'header': {
						'name': invoice.name,
						'supplier': invoice.supplier,
						'posting_date': invoice.posting_date,
						'due_date': invoice.due_date,
						'total': invoice.total,
						'grand_total': invoice.grand_total,
						'outstanding_amount': invoice.outstanding_amount,
						'currency': invoice.currency,
						'conversion_rate': invoice.conversion_rate,
						'status': invoice.status,
						'atcud_code': invoice.atcud_code,
						'portugal_series': invoice.portugal_series
					},
					'items': []
				}

			grouped_invoices[invoice_id]['items'].append({
				'item_code': invoice.item_code,
				'item_name': invoice.item_name,
				'qty': invoice.qty,
				'rate': invoice.rate,
				'amount': invoice.amount,
				'base_amount': invoice.base_amount
			})

		self.records_count += len(grouped_invoices)
		return list(grouped_invoices.values())

	def get_payments_data(self, company, from_date, to_date):
		"""
		Obtém dados dos pagamentos
		"""
		payments = frappe.db.sql("""
								 SELECT pe.name,
										pe.payment_type,
										pe.party_type,
										pe.party,
										pe.posting_date,
										pe.paid_amount,
										pe.received_amount,
										pe.reference_no,
										pe.reference_date,
										pe.mode_of_payment,
										pe.atcud_code,
										pe.portugal_series
								 FROM `tabPayment Entry` pe
								 WHERE pe.company = %s
								   AND pe.posting_date BETWEEN %s AND %s
								   AND pe.docstatus = 1
								 ORDER BY pe.posting_date, pe.name
								 """, (company, from_date, to_date), as_dict=True)

		self.records_count += len(payments)
		return payments

	def get_chart_of_accounts(self, company):
		"""
		Obtém plano de contas
		"""
		accounts = frappe.db.sql("""
								 SELECT name,
										account_name,
										account_number,
										account_type,
										parent_account,
										is_group,
										account_currency
								 FROM `tabAccount`
								 WHERE company = %s
								 ORDER BY account_number, name
								 """, (company,), as_dict=True)

		return accounts

	def get_journal_entries_data(self, company, from_date, to_date):
		"""
		Obtém lançamentos contabilísticos
		"""
		journal_entries = frappe.db.sql("""
										SELECT je.name,
											   je.posting_date,
											   je.voucher_type,
											   je.user_remark,
											   jea.account,
											   jea.debit_in_account_currency,
											   jea.credit_in_account_currency,
											   jea.against_account,
											   jea.reference_type,
											   jea.reference_name
										FROM `tabJournal Entry` je
												 INNER JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
										WHERE je.company = %s
										  AND je.posting_date BETWEEN %s AND %s
										  AND je.docstatus = 1
										ORDER BY je.posting_date, je.name
										""", (company, from_date, to_date), as_dict=True)

		return journal_entries

	def get_stock_movements_data(self, company, from_date, to_date):
		"""
		Obtém movimentos de stock
		"""
		stock_movements = frappe.db.sql("""
										SELECT sle.item_code,
											   sle.warehouse,
											   sle.posting_date,
											   sle.posting_time,
											   sle.voucher_type,
											   sle.voucher_no,
											   sle.actual_qty,
											   sle.qty_after_transaction,
											   sle.valuation_rate,
											   sle.stock_value_difference
										FROM `tabStock Ledger Entry` sle
										WHERE sle.company = %s
										  AND sle.posting_date BETWEEN %s AND %s
										  AND sle.is_cancelled = 0
										ORDER BY sle.posting_date, sle.posting_time, sle.name
										""", (company, from_date, to_date), as_dict=True)

		return stock_movements

	def render_template(self, context):
		"""
		Renderiza template SAF-T com contexto fornecido
		"""
		env = Environment(
			loader=FileSystemLoader(self.template_path),
			autoescape=False,
			trim_blocks=True,
			lstrip_blocks=True
		)

		# Adicionar filtros customizados
		env.filters['format_date'] = self.format_date_filter
		env.filters['format_decimal'] = self.format_decimal_filter
		env.filters['escape_xml'] = self.escape_xml_filter

		template = env.get_template('main.xml')
		return template.render(context)

	def format_date_filter(self, date_value):
		"""
		Filtro para formatação de datas no formato SAF-T
		"""
		if not date_value:
			return ""

		if isinstance(date_value, str):
			date_value = getdate(date_value)

		return date_value.strftime("%Y-%m-%d")

	def format_decimal_filter(self, value, decimals=2):
		"""
		Filtro para formatação de valores decimais
		"""
		if value is None:
			return "0.00"

		return f"{float(value):.{decimals}f}"

	def escape_xml_filter(self, value):
		"""
		Filtro para escape de caracteres XML
		"""
		if not value:
			return ""

		value = str(value)
		value = value.replace("&", "&amp;")
		value = value.replace("<", "&lt;")
		value = value.replace(">", "&gt;")
		value = value.replace('"', "&quot;")
		value = value.replace("'", "&apos;")

		return value

	def validate_xml_structure(self, xml_content):
		"""
		Valida estrutura básica do XML SAF-T
		"""
		try:
			root = ET.fromstring(xml_content)

			# Verificar namespace
			expected_namespace = "urn:OECD:StandardAuditFile-Tax:PT_1.04_01"
			if root.tag != f"{{{expected_namespace}}}AuditFile":
				return False

			# Verificar elementos obrigatórios
			required_elements = ["Header", "MasterFiles"]
			for element in required_elements:
				if root.find(f".//{{{expected_namespace}}}{element}") is None:
					return False

			return True

		except ET.ParseError:
			return False

	def get_records_count(self):
		"""
		Retorna número total de registros processados
		"""
		return self.records_count

	def save_saft_file(self, xml_content, company, from_date, to_date):
		"""
		Salva arquivo SAF-T no sistema de arquivos
		"""
		filename = f"SAFT-PT_{company}_{from_date}_{to_date}.xml"

		# Criar diretório se não existir
		export_dir = os.path.join(get_site_path(), "private", "files", "saft_exports")
		os.makedirs(export_dir, exist_ok=True)

		file_path = os.path.join(export_dir, filename)

		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(xml_content)

		return file_path

	def generate_file_hash(self, xml_content):
		"""
		Gera hash SHA256 do conteúdo XML
		"""
		return hashlib.sha256(xml_content.encode('utf-8')).hexdigest()


# Função para job em background
def generate_saft_background(log_name):
	"""
	Gera SAF-T em background job
	"""
	try:
		export_log = frappe.get_doc("SAF-T Export Log", log_name)
		export_log.status = "In Progress"
		export_log.save()

		generator = SAFTGenerator()

		# Gerar SAF-T
		saft_xml = generator.generate_saft(
			export_log.company,
			export_log.from_date,
			export_log.to_date,
			export_log.export_type
		)

		# Salvar arquivo
		file_path = generator.save_saft_file(
			saft_xml,
			export_log.company,
			export_log.from_date,
			export_log.to_date
		)

		# Atualizar log
		export_log.file_path = file_path
		export_log.file_size = len(saft_xml.encode('utf-8'))
		export_log.file_hash = generator.generate_file_hash(saft_xml)
		export_log.total_records = generator.get_records_count()
		export_log.status = "Completed"
		export_log.save()

		# Notificar conclusão
		frappe.publish_realtime('saft_export_completed', {
			'export_log_name': log_name,
			'filename': os.path.basename(file_path)
		})

	except Exception as e:
		frappe.log_error(f"Erro na geração SAF-T background: {str(e)}")

		export_log = frappe.get_doc("SAF-T Export Log", log_name)
		export_log.status = "Failed"
		export_log.save()

		frappe.publish_realtime('saft_export_failed', {
			'export_log_name': log_name,
			'error': str(e)
		})
