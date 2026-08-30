import frappe
from frappe import _
from frappe.utils import getdate, formatdate, now, get_site_path, flt, cint
import os
import json
import hashlib
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import time
from datetime import datetime


class SAFTGenerator:
	def __init__(self):
		self.template_path = os.path.join(
			frappe.get_app_path("portugal_compliance"),
			"templates", "saft_t"
		)
		self.records_count = 0
		# Contadores por categoria (2026-08-24): records_count sozinho ja
		# alimentava SAF-T Export Log.total_records, mas as colunas
		# sales_invoices_count/payment_entries_count do mesmo log nunca
		# eram escritas em lado nenhum - ficavam sempre a 0 mesmo num
		# export com faturas reais incluidas. Purchase Invoice/Journal
		# Entry ficam de fora do ambito deste gerador (nunca contam aqui)
		# e mantem-se corretamente a 0.
		self.sales_invoices_count = 0
		self.payments_count = 0

	def _get_line_tax_rate(self, item_tax_template, invoice_tax_rate=None):
		"""
		Taxa de IVA efetiva da linha, com a MESMA logica usada no print
		format (ver jinja_methods.get_item_effective_tax_rate): taxa do
		Item Tax Template proprio do artigo quando definido (faturas de
		taxa mista), senao a taxa do cabecalho da fatura.

		A versao anterior lia o campo `item_tax_rate` (um JSON em cache
		que o ERPNext mantem por linha) e usava sempre o primeiro valor
		do dicionario - esse cache fica desatualizado quando o template
		de imposto do artigo muda (o mesmo problema de "templates antigos"
		ja identificado no print format), e foi isso que fez a FT2026N0005
		reportar Isento (0%) no SAF-T para uma linha que a fatura real
		mostra a 23%. Ir buscar a taxa ao Item Tax Template Detail (fonte
		primaria) em vez do cache evita repetir o mesmo erro aqui.
		"""
		if item_tax_template:
			rate = frappe.db.get_value(
				"Item Tax Template Detail", {"parent": item_tax_template}, "tax_rate"
			)
			if rate is not None:
				return flt(rate)
		if invoice_tax_rate is not None:
			return flt(invoice_tax_rate)
		return 23.0

	def _get_line_tax_code(self, rate):
		"""Codigo de imposto SAF-T por faixa de taxa (categorias padrao PT)."""
		if rate <= 0:
			return "ISE"
		if rate < 10:
			return "RED"
		if rate < 20:
			return "INT"
		return "NOR"

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

	def _country_code(self, country_name):
		"""
		AddressStructure exige codigo ISO 3166-1 alpha-2, mas o ERPNext
		guarda o nome completo do pais (ex: "Portugal") no campo
		`country` da Address. O doctype Country do proprio Frappe ja tem
		esse mapeamento (campo `code`) - so faltava usa-lo.
		"""
		if not country_name:
			return "PT"
		code = frappe.db.get_value("Country", country_name, "code")
		return code.upper() if code else "PT"

	def _get_company_address(self, company):
		"""
		Morada principal da empresa. Company nao tem um campo proprio -
		a ligacao e feita via Dynamic Link (Address->Company), o mesmo
		mecanismo generico usado para clientes/fornecedores.
		"""
		address_name = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Company", "link_name": company, "parenttype": "Address"},
			"parent",
		)
		return frappe.get_doc("Address", address_name) if address_name else None

	def prepare_context(self, company_doc, from_date, to_date, export_type):
		"""
		Prepara contexto com todos os dados necessários para o template.

		V1 (MVP de certificacao): estritamente o que o XSD 1.04_01 exige
		como obrigatorio - ver auditoria de lacunas. GeneralLedgerAccounts,
		MovementOfGoods e todos os campos so opcionais foram deixados de
		fora desta passagem (ver decisoes documentadas nas notas abaixo).
		"""
		company_address = self._get_company_address(company_doc.name)

		# Falhar cedo com mensagem clara em vez de deixar o XML ser gerado
		# com AddressDetail/City/PostalCode vazios e so descobrir o
		# problema tarde, na validacao XSD (minLength=1 nesses 3 campos) -
		# foi exatamente isso que aconteceu com o export SAFT-EXP-2026-0006
		# da NovaDX (2026-08-30): Company sem nenhuma Address associada.
		if not company_address:
			frappe.throw(_(
				"A empresa {0} não tem morada fiscal configurada. "
				"Adicione uma Morada (Address) à empresa - com Rua, Cidade "
				"e Código Postal preenchidos - antes de gerar o SAF-T."
			).format(company_doc.name))

		missing_fields = []
		if not (company_address.address_line1 or "").strip():
			missing_fields.append(_("Rua/Morada"))
		if not (company_address.city or "").strip():
			missing_fields.append(_("Cidade"))
		if not (company_address.pincode or "").strip():
			missing_fields.append(_("Código Postal"))
		if missing_fields:
			frappe.throw(_(
				"A morada fiscal da empresa {0} está incompleta. "
				"Campo(s) em falta em {1}: {2}."
			).format(company_doc.name, company_address.name, ", ".join(missing_fields)))

		context = {
			# Header information
			"company": company_doc,
			"company_address": company_address,
			"company_address_country_code": self._country_code(company_address.country) if company_address else "PT",
			"from_date": from_date,
			"to_date": to_date,
			"fiscal_year": from_date.year,
			"creation_date": frappe.utils.now_datetime(),
			"erpnext_version": frappe.__version__,
			"tax_accounting_basis": "F",  # Faturacao (sem contabilidade integrada - ver GeneralLedgerEntries)
			"tax_entity": "Global",
			"software_certificate_number": frappe.db.get_single_value(
				"Portugal Auth Settings", "software_certificate_number"
			) or "0",

			# Master files
			"customers": self.get_customers_data(company_doc.name, from_date, to_date),
			"suppliers": self.get_suppliers_data(company_doc.name, from_date, to_date),
			"products": self.get_products_data(company_doc.name, from_date, to_date),
			"tax_table": self.get_tax_table_data(company_doc.name),

			# Source documents
			"sales_invoices": (sales_invoices := self.get_sales_invoices_data(company_doc.name, from_date, to_date)),
			# TotalDebit/TotalCredit do lote (SAFmonetaryType, nunca
			# negativo) - somados ao nivel da LINHA (debit_credit),
			# nao do total da fatura, para lidar corretamente com o
			# caso (hoje teorico no ERPNext, mas nao impossivel) de uma
			# fatura com linhas de credito e debito misturadas.
			"sales_invoices_total_debit": sum(
				line.amount for inv in sales_invoices for line in inv.lines if line.debit_credit == "D"
			),
			"sales_invoices_total_credit": sum(
				line.amount for inv in sales_invoices for line in inv.lines if line.debit_credit == "C"
			),
			"payments": self.get_payments_data(company_doc.name, from_date, to_date),
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
												  c.at_is_self_billing,
												  pa.account AS default_receivable_account,
												  a.address_line1,
												  a.address_line2,
												  a.city,
												  a.pincode,
												  a.country
								  FROM `tabCustomer` c
										   LEFT JOIN `tabAddress` a
													 ON a.name = (
														 SELECT dl.parent FROM `tabDynamic Link` dl
														 WHERE dl.link_name = c.name AND dl.link_doctype = 'Customer'
														   AND dl.parenttype = 'Address'
														 ORDER BY dl.parent LIMIT 1
													 )
									   LEFT JOIN `tabParty Account` pa
										 ON pa.parent = c.name AND pa.parenttype = 'Customer' AND pa.company = %s
								  WHERE EXISTS (
									  SELECT 1 FROM `tabSales Invoice` si
									  WHERE si.customer = c.name
										AND si.company = %s
										AND si.posting_date BETWEEN %s AND %s
										AND si.docstatus IN (1, 2)
								  )
								  ORDER BY c.name
								  """, (company, company, from_date, to_date), as_dict=True)
		# docstatus IN (1, 2): desde que get_sales_invoices_data passou
		# a incluir faturas anuladas (docstatus=2) no SourceDocuments,
		# o cliente dessa fatura tem de constar do MasterFiles tambem -
		# senao o CustomerID referenciado na fatura anulada aponta para
		# um cliente inexistente no ficheiro (keyref invalido, XSD
		# rejeita o ficheiro inteiro). So aconteceria com um cliente
		# cuja UNICA fatura no periodo estivesse anulada.

		for row in customers:
			row["country_code"] = self._country_code(row.country)

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
												  pa.account AS default_payable_account,
												  a.address_line1,
												  a.address_line2,
												  a.city,
												  a.pincode,
												  a.country
								  FROM `tabSupplier` s
										   LEFT JOIN `tabAddress` a
													 ON a.name = (
														 SELECT dl.parent FROM `tabDynamic Link` dl
														 WHERE dl.link_name = s.name AND dl.link_doctype = 'Supplier'
														   AND dl.parenttype = 'Address'
														 ORDER BY dl.parent LIMIT 1
													 )
									   LEFT JOIN `tabParty Account` pa
										 ON pa.parent = s.name AND pa.parenttype = 'Supplier' AND pa.company = %s
								  WHERE EXISTS (
									  SELECT 1 FROM `tabPurchase Invoice` pi
									  WHERE pi.supplier = s.name
										AND pi.company = %s
										AND pi.posting_date BETWEEN %s AND %s
										AND pi.docstatus = 1
								  )
								  ORDER BY s.name
								  """, (company, company, from_date, to_date), as_dict=True)

		for row in suppliers:
			row["country_code"] = self._country_code(row.country)

		return suppliers

	def get_products_data(self, company, from_date, to_date):
		"""
		Obtém dados dos produtos/serviços
		"""
		products = frappe.db.sql("""
								 SELECT DISTINCT i.name,
												 i.item_name,
												 i.item_code,
												 i.item_group,
												 i.is_stock_item
								 FROM `tabItem` i
								 WHERE EXISTS (SELECT 1
											   FROM `tabSales Invoice Item` sii
														INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
											   WHERE sii.item_code = i.item_code
												 AND si.company = %s
												 AND si.posting_date BETWEEN %s AND %s
												 AND si.docstatus = 1)
								 ORDER BY i.item_code
								 """, (company, from_date, to_date), as_dict=True)

		return products

	def get_tax_table_data(self, company):
		"""
		Obtém tabela de impostos - com TaxCode real (RED/INT/NOR/ISE) e
		praça fiscal real (a.at_tax_region), nao o nome livre da conta
		contabilistica nem "PT" fixo. As contas SNC regionais (Açores/
		Madeira, ver setup/tax_setup.py) já guardam a região desde a
		criação - antes esta tabela mestra reportava sempre
		TaxCountryRegion="PT" para qualquer taxa, mesmo uma conta
		criada explicitamente para Madeira/Açores (auditoria de
		certificação 2026-08-24).
		"""
		from portugal_compliance.utils.tax_breakdown import VALID_AT_CODES

		tax_rates = frappe.db.sql("""
								  SELECT DISTINCT at.rate, at.description, a.at_tax_region AS region,
												  a.at_tax_code AS account_tax_code
								  FROM `tabAccount` a
										   INNER JOIN `tabSales Taxes and Charges` at
								  ON at.account_head = a.name
								  WHERE a.company = %s
									AND a.account_type = 'Tax'
									AND a.is_group = 0
								  ORDER BY at.rate
								  """, (company,), as_dict=True)

		for row in tax_rates:
			# Código real da conta (setup/tax_setup.py) quando disponível -
			# só cai na faixa de percentagem para contas legadas sem
			# at_tax_code (anteriores a 2026-08-24). Faixa de percentagem
			# sozinha confunde regiões (ex: Normal dos Açores a 16% caía em
			# "Intermédia").
			row["tax_code"] = row.pop("account_tax_code") or None
			if row["tax_code"] not in VALID_AT_CODES:
				row["tax_code"] = self._get_line_tax_code(flt(row["rate"]))
			row["region"] = row["region"] or "PT"

		return tax_rates

	def _get_signatures_by_invoice(self, invoice_names, doctype="Sales Invoice"):
		"""
		Assinaturas RSA-SHA1 reais (ver utils/signature.py), ja geradas
		no submit de cada fatura e guardadas em ATCUD Log. O SAF-T so
		liga a este dado - a assinatura em si nao e gerada aqui.
		"""
		if not invoice_names:
			return {}
		rows = frappe.db.sql("""
							 SELECT document_name, signature_hash, sequence_number
							 FROM `tabATCUD Log`
							 WHERE document_type = %(doctype)s
							   AND document_name IN %(names)s
							 """, {"doctype": doctype, "names": invoice_names}, as_dict=True)
		return {r.document_name: r for r in rows}

	def _format_invoice_no(self, invoice_name, sequence_number, doc_code="FT"):
		"""
		Formato "PREFIXO SERIE/NUMERO" (ex: "FT FT2026N/5") exigido pelo
		XSD para InvoiceNo - confirmado no gerador SAF-T do modulo
		Dolibarr de referencia (formatSaftDocNumber), ja validado contra
		rejeicoes reais da AT. sequence_number vem do ATCUD Log (fonte
		fiavel); se nao existir (fatura sem ATCUD), cai no fallback de
		extrair os digitos finais do proprio nome do documento.

		doc_code (FT/NC/...) tinha ficado fixo em "FT" - com a serie NC
		agora real (ver reset_fiscal_fields_on_return_clone), uma Nota
		de Credito tem de reportar "NC", nao "FT", ou a AT rejeita o
		documento por inconsistencia entre a serie usada e o tipo
		declarado.
		"""
		import re
		if sequence_number is None:
			match = re.match(r"^(.*?)(\d+)$", invoice_name)
			series_prefix, sequence_number = (match.groups() if match else (invoice_name, 0))
			sequence_number = int(sequence_number)
		else:
			suffix = str(sequence_number).zfill(4)
			series_prefix = invoice_name[:-len(suffix)] if invoice_name.endswith(suffix) else invoice_name
		return f"{doc_code} {series_prefix}/{sequence_number}"

	def get_sales_invoices_data(self, company, from_date, to_date, doctype="Sales Invoice"):
		"""
		Obtém dados das faturas de venda. Devolve uma lista achatada de
		objetos por fatura (cada um com `.items`), no formato que os
		templates Jinja esperam diretamente - a versao anterior embrulhava
		tudo num nivel 'header' que nao corresponde ao que source_documents.xml
		le (invoice.name, invoice.posting_date, etc. direto no objeto).

		doctype: "Sales Invoice" (omissao) ou "POS Invoice" - mesma
		estrutura de colunas nos dois (POS Invoice foi desenhado pelo
		ERPNext como variante leve de Sales Invoice), reutilizada aqui
		para o webservice em tempo real tambem funcionar quando POS
		Settings.invoice_type="POS Invoice" (a outra bifurcacao nativa
		do POS). doctype nunca vem de input do utilizador - so das 2
		constantes internas acima, por isso interpolar diretamente no
		nome da tabela e seguro.
		"""
		item_doctype = f"{doctype} Item"
		rows = frappe.db.sql(f"""
							 SELECT si.name,
									si.customer,
									si.posting_date,
									si.due_date,
									si.creation,
									si.net_total,
									si.total_taxes_and_charges,
									si.grand_total,
									si.currency,
									si.conversion_rate,
									si.docstatus,
									si.owner,
									si.atcud_code,
									si.naming_series,
									si.is_return,
									si.return_against,
									si.shipping_address_name,
									si.customer_address,
									sii.item_code,
									sii.item_name,
									sii.description,
									sii.qty,
									sii.uom,
									sii.rate,
									sii.amount,
									sii.item_tax_template,
									sii.at_exemption_reason
							 FROM `tab{doctype}` si
									  INNER JOIN `tab{item_doctype}` sii ON sii.parent = si.name
							 WHERE si.company = %s
							   AND si.posting_date BETWEEN %s AND %s
							   AND si.docstatus IN (1, 2)
							 ORDER BY si.posting_date, si.name
							 """, (company, from_date, to_date), as_dict=True)
		# docstatus IN (1, 2): faturas anuladas (docstatus=2) tem de
		# constar no SAF-T com InvoiceStatus=A e valores fiscais a
		# 0.00 - a lei portuguesa exige o registo da anulacao, nao a
		# sua omissao. Antes desta correcao, uma fatura anulada
		# simplesmente desaparecia do ficheiro, como se nunca tivesse
		# existido - o ATCUD/assinatura originais continuavam validos
		# no sistema (nunca sao apagados, ver inviolabilidade em
		# document_hooks.py) mas o SAF-T nao refletia a anulacao.

		signatures = self._get_signatures_by_invoice(list({r.name for r in rows}), doctype=doctype)
		invoice_names = list({r.name for r in rows})
		fallback_rates = {}
		header_account = {}
		if invoice_names:
			for t in frappe.db.sql("""
									SELECT parent, rate, account_head FROM `tabSales Taxes and Charges`
									WHERE parent IN %(names)s AND rate > 0
									ORDER BY idx
									""", {"names": invoice_names}, as_dict=True):
				fallback_rates.setdefault(t.parent, t.rate)
				header_account.setdefault(t.parent, t.account_head)

		# Região fiscal (PT/PT-AC/PT-MA) por linha: mesma resolução
		# estrutural (Account.at_tax_region) já usada no QR Code e na
		# TaxTable mestra (tax_breakdown.py), não uma segunda lógica
		# paralela baseada em faixas de percentagem - _get_line_tax_code
		# já classifica NOR/INT/RED/ISE por faixa de taxa (aceitável
		# para a categoria, que é sobre a taxa em si), mas a REGIÃO
		# nunca deve ser adivinhada a partir de um número: duas praças
		# fiscais podem partilhar a mesma percentagem hoje, ou convergir
		# no futuro, e nada nessa faixa indica de que conta a taxa veio
		# (auditoria de certificação 2026-08-24, questão levantada após
		# comparação com InvoiceXpress/Odoo l10n_pt).
		from portugal_compliance.utils.tax_breakdown import get_account_at_info, get_item_tax_template_info, VALID_AT_CODES

		template_names = {r.item_tax_template for r in rows if r.item_tax_template}
		# account_info começa só com as contas do cabeçalho (fallback);
		# get_item_tax_template_info() estende o mesmo cache com as
		# contas dos templates conforme precisa (via Item Tax Template
		# Detail.tax_type, que é o nome da Account real) - sem N+1.
		account_info = get_account_at_info({a for a in header_account.values() if a})
		template_info = get_item_tax_template_info(template_names, account_info)

		def _line_tax_info(item_tax_template, invoice_name):
			info = template_info.get(item_tax_template)
			if not info:
				header_acc = header_account.get(invoice_name)
				info = account_info.get(header_acc) if header_acc else None
			return info or {}

		def _line_region(item_tax_template, invoice_name):
			region = _line_tax_info(item_tax_template, invoice_name).get("region")
			return region if region else "PT"

		def _line_tax_code(item_tax_template, invoice_name, rate):
			"""
			Código AT real da conta/template (at_tax_code, já correto por
			região - ver setup/tax_setup.py) quando resolvível; só cai na
			classificação por faixa de percentagem (_get_line_tax_code)
			quando não há conta/template AT associável (contas legadas
			anteriores ao campo at_tax_region). A faixa de percentagem
			sozinha confunde regiões: a taxa Normal dos Açores (16%) caía
			na faixa "Intermédia" (<20%) do Continente - passou a ser um
			bug real assim que Açores/Madeira passaram a ser gerados
			automaticamente (ver setup/tax_setup.py::
			create_regional_tax_setup_for_company).
			"""
			info = _line_tax_info(item_tax_template, invoice_name)
			if info.get("tax_type") == "IS":
				# Imposto do Selo: o código é a verba da TGIS
				# (at_stamp_duty_verba, texto livre - ex: "1.1", "17.3.1"),
				# nunca a classificação NOR/INT/RED/ISE de IVA. "OUT"
				# (Outro) é o código de reserva do XSD quando a verba
				# ainda não foi configurada na conta.
				return info.get("verba") or "OUT"
			code = info.get("code")
			return code if code in VALID_AT_CODES else self._get_line_tax_code(rate)

		def _line_tax_type(item_tax_template, invoice_name):
			return _line_tax_info(item_tax_template, invoice_name).get("tax_type") or "IVA"

		series_code_cache = {}

		def _document_code_for(naming_series, is_return):
			"""
			Codigo real do tipo de documento (FT/NC) a partir da serie
			realmente usada (Portugal Series Configuration), nao um
			literal fixo - agora que existe uma serie NC dedicada e
			comunicada (ver api.company_api.RETURN_DOCUMENT_SERIES).
			Fallback para is_return se a serie nao tiver document_code
			por algum motivo (nunca deveria acontecer para series
			criadas por este modulo, mas evita um None a espalhar-se).
			"""
			if naming_series not in series_code_cache:
				series_code_cache[naming_series] = frappe.db.get_value(
					"Portugal Series Configuration", {"naming_series": naming_series}, "document_code"
				)
			default_code = "FS" if doctype == "POS Invoice" else "FT"
			return series_code_cache[naming_series] or ("NC" if is_return else default_code)

		original_doc_cache = {}

		def _original_document_reference(return_against):
			"""
			Para uma Nota de Credito (return_against preenchido), a AT
			exige a referencia ao documento original no formato
			"ATCUD_ORIGINAL NUMERO_ORIGINAL" (ex: "AAJFJ23MT8-0001 FT
			FT2026N/1"). sequence_number vem do ATCUD Log do ORIGINAL,
			nao do documento atual - por isso o mesmo helper de
			formatacao (_format_invoice_no) e reutilizado aqui com os
			dados do original.
			"""
			if not return_against:
				return None
			if return_against not in original_doc_cache:
				orig = frappe.db.get_value(
					doctype, return_against,
					["atcud_code", "naming_series", "is_return"], as_dict=True,
				)
				if not orig:
					original_doc_cache[return_against] = None
				else:
					orig_sig = self._get_signatures_by_invoice([return_against], doctype=doctype).get(return_against)
					orig_doc_code = _document_code_for(orig.naming_series, orig.is_return)
					orig_invoice_no = self._format_invoice_no(
						return_against, orig_sig.sequence_number if orig_sig else None, orig_doc_code
					)
					original_doc_cache[return_against] = f"{orig.atcud_code or ''} {orig_invoice_no}".strip()
			return original_doc_cache[return_against]

		address_cache = {}

		def _address_dict(address_name):
			"""
			Morada (ShipTo/ShipFrom) no formato CustomerAddressStructure
			exigido pelo XSD - AddressDetail/City/PostalCode/Country
			nunca podem ir vazios (minLength=1), por isso o fallback
			"Desconhecido" quando o ERPNext nao tem o dado preenchido.
			"""
			if not address_name:
				return None
			if address_name not in address_cache:
				addr = frappe.db.get_value(
					"Address", address_name,
					["address_line1", "address_line2", "city", "pincode", "country"], as_dict=True,
				)
				if not addr:
					address_cache[address_name] = None
				else:
					detail = ((addr.address_line1 or "") + " " + (addr.address_line2 or "")).strip()
					address_cache[address_name] = frappe._dict({
						"address_detail": detail or "Desconhecido",
						"city": addr.city or "Desconhecido",
						"postal_code": addr.pincode or "Desconhecido",
						"country_code": self._country_code(addr.country),
					})
			return address_cache[address_name]

		self_billing_cache = {}

		def _self_billing(customer):
			if customer not in self_billing_cache:
				self_billing_cache[customer] = cint(
					frappe.db.get_value("Customer", customer, "at_is_self_billing")
				)
			return self_billing_cache[customer]

		def _withholding_tax_rows(invoice_name):
			"""
			Linhas de Sales Taxes and Charges marcadas como retencao na
			fonte (is_tax_withholding_account=1 - campo nativo do
			ERPNext, criado quando uma Tax Withholding Category e
			aplicada). WithholdingTaxType (IRS/IRC/IS) nao tem
			correspondencia automatica fiavel a partir da configuracao
			nativa do ERPNext (Tax Withholding Category) - vem do custom
			field Account.at_withholding_tax_type (setup/tax_setup.py),
			que cada conta de retencao tem de ter configurado manualmente.
			So populado no SAF-T quando preenchido (campo opcional no
			XSD) - nunca adivinhado.
			"""
			rows = frappe.db.sql("""
								 SELECT description, tax_amount, account_head
								 FROM `tabSales Taxes and Charges`
								 WHERE parent = %s AND is_tax_withholding_account = 1
								 """, (invoice_name,), as_dict=True)
			account_names = {r.account_head for r in rows if r.account_head}
			wh_types = {}
			if account_names:
				wh_types = {
					a.name: a.at_withholding_tax_type
					for a in frappe.get_all(
						"Account", filters={"name": ["in", list(account_names)]},
						fields=["name", "at_withholding_tax_type"],
					)
				}
			return [
				frappe._dict({
					"description": r.description or "",
					"amount": abs(flt(r.tax_amount)),
					"withholding_tax_type": wh_types.get(r.account_head) or "",
				})
				for r in rows if r.tax_amount
			]

		invoices = {}
		for row in rows:
			if row.name not in invoices:
				sig = signatures.get(row.name)
				doc_code = _document_code_for(row.naming_series, row.is_return)
				invoice = frappe._dict(row.copy())
				invoice["signature_hash"] = sig.signature_hash if (sig and sig.signature_hash) else "0"
				invoice["hash_control"] = "1" if (sig and sig.signature_hash) else "0"
				invoice["invoice_type"] = doc_code
				invoice["invoice_no"] = self._format_invoice_no(
					row.name, sig.sequence_number if sig else None, doc_code
				)
				# SAFmonetaryType (XSD) nao permite negativos - uma Nota
				# de Credito tem estes campos negativos no ERPNext; o
				# sentido (credito/estorno) e comunicado pelo
				# InvoiceType=NC e pelo DebitAmount/CreditAmount por
				# linha (ver abaixo), nunca por um total negativo.
				#
				# Documento anulado (docstatus=2): Base e Imposto vao a
				# 0.00 (exigencia legal) - o ATCUD/Hash abaixo
				# mantêm-se os originais, prova de que o documento foi
				# mesmo assinado antes de ser anulado.
				is_cancelled = row.docstatus == 2
				invoice["tax_payable"] = 0.0 if is_cancelled else abs(flt(row.total_taxes_and_charges))
				invoice["net_total_abs"] = 0.0 if is_cancelled else abs(flt(row.net_total))
				invoice["gross_total_abs"] = 0.0 if is_cancelled else abs(flt(row.grand_total))
				invoice["original_document_reference"] = _original_document_reference(row.return_against)
				invoice["ship_to"] = _address_dict(row.shipping_address_name)
				invoice["self_billing_indicator"] = _self_billing(row.customer)
				invoice["withholding_tax"] = _withholding_tax_rows(row.name)
				invoice["lines"] = []
				invoices[row.name] = invoice

			tax_rate = self._get_line_tax_rate(row.item_tax_template, fallback_rates.get(row.name))
			exemption_reason = ""
			if tax_rate <= 0 and row.at_exemption_reason:
				exemption_reason = frappe.db.get_value(
					"AT Tax Exemption", row.at_exemption_reason, "description"
				) or row.at_exemption_reason
			signed_amount = flt(row.amount)
			abs_amount = 0.0 if row.docstatus == 2 else abs(signed_amount)
			invoices[row.name]["lines"].append(frappe._dict({
				"item_code": row.item_code,
				"item_name": row.item_name,
				"description": row.description,
				"qty": abs(flt(row.qty)),
				"uom": row.uom,
				"rate": row.rate,
				"amount": abs_amount,
				"debit_credit": "D" if signed_amount < 0 else "C",
				"tax_percentage": tax_rate,
				"tax_type": _line_tax_type(row.item_tax_template, row.name),
				"tax_code": _line_tax_code(row.item_tax_template, row.name, tax_rate),
				"tax_region": _line_region(row.item_tax_template, row.name),
				"tax_amount": abs_amount * tax_rate / 100,
				"tax_exemption_code": row.at_exemption_reason or "",
				"tax_exemption_reason": exemption_reason,
			}))

		self.records_count += len(invoices)
		self.sales_invoices_count += len(invoices)
		return list(invoices.values())

	def get_payments_data(self, company, from_date, to_date):
		"""
		Obtém dados dos pagamentos, incluindo as linhas de referencia a
		documentos de origem (Payment Entry Reference) que o SAF-T exige
		por linha - a versao anterior so lia o cabecalho do Payment Entry
		e nunca carregava as referencias.
		"""
		names = frappe.db.sql_list("""
								   SELECT name FROM `tabPayment Entry`
								   WHERE company = %s AND posting_date BETWEEN %s AND %s
									 AND docstatus = 1
								   ORDER BY posting_date, name
								   """, (company, from_date, to_date))

		# PaymentType (RC/RG) e um campo legal distinto de PaymentRefNo,
		# sem qualquer relacao com o sentido do pagamento (Receber vs
		# Pagar) - confirmado na documentacao do proprio XSD
		# (SAFTPTPaymentType): "RC para Recibo emitido no ambito do
		# regime de IVA de Caixa (...), RG para Outros recibos
		# emitidos". Usar Receive/Pay aqui (versao anterior) reportava
		# RC a qualquer recebimento normal, mesmo sem a empresa estar
		# no regime de Caixa - auditoria de certificacao 2026-08-24,
		# depois de comparar com o modulo l10n_pt_certification do
		# Odoo/OCA e confirmar contra o texto oficial do XSD.
		cash_vat_scheme = cint(frappe.db.get_single_value("Portugal Auth Settings", "cash_vat_scheme"))
		saft_payment_type = "RC" if cash_vat_scheme else "RG"

		# Taxa oficial por região+código (mesma taxonomia usada para criar
		# as contas/templates - setup/tax_setup.py) para atribuir a
		# TaxPercentage real a cada grupo de imposto de uma fatura de
		# origem, em vez de recalcular a partir de valores arredondados.
		from portugal_compliance.setup.tax_setup import AT_TAX_TAXONOMY
		from portugal_compliance.utils.tax_breakdown import get_tax_breakdown_by_at_code
		rate_by_region_code = {
			(region, spec["code"]): spec["rate"]
			for region, specs in AT_TAX_TAXONOMY.items() for spec in specs
		}

		invoice_tax_groups_cache = {}

		def _invoice_tax_groups(reference_doctype, reference_name):
			"""
			Grupos (região, código AT) com a base tributável real da
			fatura de origem referenciada, para atribuir ao recibo a taxa/
			código/região reais em vez dos literais fixos NOR/0.00/PT
			(auditoria de certificação 2026-08-24/backlog V1.2.0). Só
			resolvível para Sales Invoice/POS Invoice, que são os
			doctypes com Item Tax Template - outras origens (ex: Journal
			Entry) ficam sem grupos e caem no fallback exempt/M99 abaixo,
			igual ao comportamento anterior.
			"""
			if reference_doctype not in ("Sales Invoice", "POS Invoice") or not reference_name:
				return []
			cache_key = (reference_doctype, reference_name)
			if cache_key in invoice_tax_groups_cache:
				return invoice_tax_groups_cache[cache_key]

			try:
				invoice_doc = frappe.get_doc(reference_doctype, reference_name)
				breakdown = get_tax_breakdown_by_at_code(invoice_doc)
			except Exception as e:
				frappe.log_error(
					f"Erro ao calcular grupos de imposto da fatura {reference_name} para recibo: {str(e)}",
					"Portugal Compliance - Payment Tax Granularity",
				)
				invoice_tax_groups_cache[cache_key] = []
				return []

			groups = []
			for region, buckets in breakdown.items():
				for code, values in buckets.items():
					base = flt(values.get("base"))
					if base <= 0:
						continue
					groups.append({
						"region": region,
						"code": code,
						"base": base,
						"rate": rate_by_region_code.get((region, code), 0.0),
					})
			invoice_tax_groups_cache[cache_key] = groups
			return groups

		series_code_cache = {}

		def _payment_doc_code(naming_series):
			"""
			Codigo real da serie (Portugal Series Configuration.document_code),
			nao Receive/Pay - mesma logica estrutural de
			_document_code_for() usada para Sales Invoice/Nota de
			Credito. Todas as series de Payment Entry sao "RC" neste
			modulo (identificador da serie, nao classificacao fiscal do
			regime - ver saft_payment_type acima, que e o campo
			realmente ligado ao regime de IVA de Caixa).
			"""
			if naming_series not in series_code_cache:
				series_code_cache[naming_series] = frappe.db.get_value(
					"Portugal Series Configuration", {"naming_series": naming_series}, "document_code"
				)
			return series_code_cache[naming_series] or "RC"

		payments = []
		for name in names:
			pe = frappe.get_doc("Payment Entry", name)
			# PaymentRefNo exige o mesmo formato "CODIGO SERIE/SEQUENCIA"
			# que InvoiceNo (ver _format_invoice_no) - pe.name sozinho
			# ("RC2026N0001") nao bate com o pattern do XSD
			# ([^ ]+ [^/^ ]+/[0-9]+), confirmado ao validar contra o
			# schema real (auditoria de certificacao 2026-08-24).
			pe.saft_ref_no = self._format_invoice_no(pe.name, None, _payment_doc_code(pe.naming_series))
			pe.saft_payment_type = saft_payment_type
			pe.saft_references = []
			for ref in pe.references:
				invoice_date = frappe.db.get_value(ref.reference_doctype, ref.reference_name, "posting_date") \
					if ref.reference_doctype and ref.reference_name else None
				invoice_date = invoice_date or pe.posting_date

				groups = _invoice_tax_groups(ref.reference_doctype, ref.reference_name)
				if groups:
					# Divide o valor alocado do recibo pelas taxas reais da
					# fatura de origem, proporcional à base de cada grupo -
					# uma fatura de taxa mista gera uma <Line> por grupo. O
					# último grupo recebe o resto exato (evita desvio de
					# arredondamento entre a soma das linhas e o total
					# alocado).
					total_base = sum(g["base"] for g in groups)
					remaining = flt(ref.allocated_amount)
					for i, g in enumerate(groups):
						if i == len(groups) - 1:
							share = remaining
						else:
							share = flt(ref.allocated_amount) * (g["base"] / total_base) if total_base else 0.0
							remaining -= share
						pe.saft_references.append(frappe._dict({
							"reference_name": ref.reference_name,
							"allocated_amount": share,
							"invoice_date": invoice_date,
							"tax_code": g["code"],
							"tax_percentage": g["rate"],
							"tax_region": g["region"],
							"is_exempt": g["code"] == "ISE",
						}))
				else:
					# Fallback (referencia nao resolvivel, ex: Journal
					# Entry) - mantem o comportamento anterior: assume-se
					# isento/M99, nunca inventa uma taxa nao-zero sem
					# origem real.
					pe.saft_references.append(frappe._dict({
						"reference_name": ref.reference_name,
						"allocated_amount": ref.allocated_amount,
						"invoice_date": invoice_date,
						"tax_code": "NOR",
						"tax_percentage": 0.0,
						"tax_region": "PT",
						"is_exempt": True,
					}))
			# O XSD exige SourceDocumentID (OriginatingON+InvoiceDate)
			# em TODA a Line de um Payment - nao ha forma valida de
			# representar um recebimento sem nenhuma fatura alocada
			# (ex: adiantamento ainda por reconciliar) neste schema.
			# Confirmado ao validar contra o XSD real: sem este filtro,
			# um Payment Entry sem references gera uma Line sem
			# SourceDocumentID e falha a validacao. Excluido do SAF-T
			# ate estar reconciliado - continua a ter ATCUD/assinatura
			# local normalmente, so nao entra no ficheiro enquanto nao
			# tiver documento de origem para referenciar.
			if not pe.saft_references:
				continue
			payments.append(pe)

		self.records_count += len(payments)
		self.payments_count += len(payments)
		return payments

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
		# sales_invoices_count/payment_entries_count nunca eram escritos
		# antes (2026-08-24) - a UI mostrava sempre 0 mesmo com faturas/
		# recibos reais incluidos no ficheiro. purchase_invoices_count/
		# journal_entries_count mantem-se corretamente a 0 (fora do
		# ambito deste gerador).
		export_log.sales_invoices_count = generator.sales_invoices_count
		export_log.payment_entries_count = generator.payments_count

		# Validacao XSD real contra o schema oficial da AT (Requisito 1.4
		# da auditoria de certificacao 2026-08-24) - antes disto o ficheiro
		# era sempre marcado "Completed" sem nunca ser validado contra o
		# saftpt1.04_01.xsd bundled. Um ficheiro invalido agora fica
		# "Failed" com os erros reais do schema, e download_saft_file (ver
		# api/saft_api.py) ja recusa descarregar qualquer export que nao
		# esteja "Completed".
		is_valid = export_log.validate_xml_content(saft_xml)
		if not is_valid:
			export_log.status = "Failed"
			export_log.save()

			frappe.publish_realtime('saft_export_failed', {
				'export_log_name': log_name,
				'error': _('Ficheiro SAF-T gerado não é válido contra o schema XSD oficial - ver Erros de Validação XSD.')
			})
			return

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
