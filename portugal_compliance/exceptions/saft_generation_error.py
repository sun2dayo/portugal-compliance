# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Exceções personalizadas para geração de ficheiros SAF-T (PT)
"""

import frappe
from frappe import _


class SAFTGenerationError(Exception):
	"""
	Exceção base para erros na geração de ficheiros SAF-T
	"""

	def __init__(self, message=None, error_code=None, details=None):
		if message is None:
			message = _("Error generating SAF-T file")

		self.error_code = error_code
		self.details = details or {}

		# Log do erro para debugging
		frappe.log_error(
			title=f"SAF-T Generation Error: {error_code or 'Unknown'}",
			message=f"Message: {message}\nDetails: {self.details}"
		)

		super().__init__(message)

	def __str__(self):
		if self.error_code:
			return f"[{self.error_code}] {super().__str__()}"
		return super().__str__()


class SAFTValidationError(SAFTGenerationError):
	"""
	Exceção para erros de validação de dados SAF-T
	"""

	def __init__(self, message=None, field=None, value=None, validation_rule=None):
		if message is None:
			message = _("SAF-T data validation error")

		details = {
			"field": field,
			"value": value,
			"validation_rule": validation_rule
		}
		super().__init__(message, error_code="SAFT_VALIDATION_ERROR", details=details)

		# Atributos específicos para validação
		self.field = field
		self.value = value
		self.validation_rule = validation_rule


class SAFTXMLError(SAFTGenerationError):
	"""
	Exceção para erros na estrutura XML do SAF-T
	"""

	def __init__(self, message=None, xml_element=None, xml_content=None):
		if message is None:
			message = _("SAF-T XML structure error")

		details = {
			"xml_element": xml_element,
			"xml_content": xml_content[:500] if xml_content else None  # Limitar tamanho do log
		}
		super().__init__(message, error_code="SAFT_XML_ERROR", details=details)

		# Atributos específicos para XML
		self.xml_element = xml_element
		self.xml_content = xml_content


class SAFTCompanyError(SAFTGenerationError):
	"""
	Exceção para erros relacionados com dados da empresa no SAF-T
	"""

	def __init__(self, message=None, company=None, missing_field=None):
		if message is None:
			message = _("SAF-T company data error")

		details = {
			"company": company,
			"missing_field": missing_field
		}
		super().__init__(message, error_code="SAFT_COMPANY_ERROR", details=details)

		# Atributos específicos para empresa
		self.company = company
		self.missing_field = missing_field


class SAFTDateRangeError(SAFTGenerationError):
	"""
	Exceção para erros de intervalo de datas no SAF-T
	"""

	def __init__(self, message=None, start_date=None, end_date=None):
		if message is None:
			message = _("SAF-T date range error")

		details = {
			"start_date": str(start_date) if start_date else None,
			"end_date": str(end_date) if end_date else None
		}
		super().__init__(message, error_code="SAFT_DATE_RANGE_ERROR", details=details)

		# Atributos específicos para datas
		self.start_date = start_date
		self.end_date = end_date


class SAFTDataIntegrityError(SAFTGenerationError):
	"""
	Exceção para erros de integridade de dados no SAF-T
	"""

	def __init__(self, message=None, doctype=None, document_name=None, integrity_check=None):
		if message is None:
			message = _("SAF-T data integrity error")

		details = {
			"doctype": doctype,
			"document_name": document_name,
			"integrity_check": integrity_check
		}
		super().__init__(message, error_code="SAFT_DATA_INTEGRITY_ERROR", details=details)

		# Atributos específicos para integridade
		self.doctype = doctype
		self.document_name = document_name
		self.integrity_check = integrity_check


class SAFTSchemaError(SAFTGenerationError):
	"""
	Exceção para erros de conformidade com schema XSD do SAF-T
	"""

	def __init__(self, message=None, schema_version=None, validation_errors=None):
		if message is None:
			message = _("SAF-T schema validation error")

		details = {
			"schema_version": schema_version,
			"validation_errors": validation_errors
		}
		super().__init__(message, error_code="SAFT_SCHEMA_ERROR", details=details)

		# Atributos específicos para schema
		self.schema_version = schema_version
		self.validation_errors = validation_errors


class SAFTFileSizeError(SAFTGenerationError):
	"""
	Exceção para erros relacionados com tamanho de ficheiro SAF-T
	"""

	def __init__(self, message=None, file_size=None, max_size=None):
		if message is None:
			message = _("SAF-T file size error")

		details = {
			"file_size": file_size,
			"max_size": max_size
		}
		super().__init__(message, error_code="SAFT_FILE_SIZE_ERROR", details=details)

		# Atributos específicos para tamanho
		self.file_size = file_size
		self.max_size = max_size


class SAFTEncodingError(SAFTGenerationError):
	"""
	Exceção para erros de codificação de caracteres no SAF-T
	"""

	def __init__(self, message=None, encoding=None, problematic_content=None):
		if message is None:
			message = _("SAF-T encoding error")

		details = {
			"encoding": encoding,
			"problematic_content": problematic_content[:100] if problematic_content else None
		}
		super().__init__(message, error_code="SAFT_ENCODING_ERROR", details=details)

		# Atributos específicos para encoding
		self.encoding = encoding
		self.problematic_content = problematic_content


class SAFTTaxError(SAFTGenerationError):
	"""
	Exceção para erros relacionados com impostos no SAF-T
	"""

	def __init__(self, message=None, tax_code=None, tax_rate=None, document=None):
		if message is None:
			message = _("SAF-T tax information error")

		details = {
			"tax_code": tax_code,
			"tax_rate": tax_rate,
			"document": document
		}
		super().__init__(message, error_code="SAFT_TAX_ERROR", details=details)

		# Atributos específicos para impostos
		self.tax_code = tax_code
		self.tax_rate = tax_rate
		self.document = document


# Funções utilitárias para validação SAF-T

def validate_company_data_for_saft(company):
	"""
	Valida dados da empresa necessários para SAF-T

	Args:
		company (str): Nome da empresa

	Raises:
		SAFTCompanyError: Se dados da empresa estiverem incompletos
	"""
	if not company:
		raise SAFTCompanyError(
			message=_("Company name is required for SAF-T generation"),
			company=company,
			missing_field="company_name"
		)

	# Verificar se empresa existe
	if not frappe.db.exists("Company", company):
		raise SAFTCompanyError(
			message=_("Company '{0}' does not exist").format(company),
			company=company,
			missing_field="company_existence"
		)

	# Verificar campos obrigatórios
	required_fields = {
		"tax_id": _("Tax ID (NIF)"),
		"company_name": _("Company Name"),
		"default_currency": _("Default Currency")
	}

	company_data = frappe.db.get_value("Company", company, list(required_fields.keys()),
									   as_dict=True)

	for field, label in required_fields.items():
		if not company_data.get(field):
			raise SAFTCompanyError(
				message=_("Company '{0}' is missing required field: {1}").format(company, label),
				company=company,
				missing_field=field
			)


def validate_date_range_for_saft(start_date, end_date):
	"""
	Valida intervalo de datas para geração de SAF-T

	Args:
		start_date (date): Data de início
		end_date (date): Data de fim

	Raises:
		SAFTDateRangeError: Se intervalo de datas for inválido
	"""
	if not start_date or not end_date:
		raise SAFTDateRangeError(
			message=_("Start date and end date are required"),
			start_date=start_date,
			end_date=end_date
		)

	if start_date > end_date:
		raise SAFTDateRangeError(
			message=_("Start date cannot be after end date"),
			start_date=start_date,
			end_date=end_date
		)

	# Verificar se o período não é muito longo (máximo 1 ano)
	from datetime import timedelta
	max_period = timedelta(days=366)  # Incluir anos bissextos

	if (end_date - start_date) > max_period:
		raise SAFTDateRangeError(
			message=_("Date range cannot exceed one year"),
			start_date=start_date,
			end_date=end_date
		)


def validate_xml_structure(xml_content):
	"""
	Valida estrutura básica do XML SAF-T

	Args:
		xml_content (str): Conteúdo XML a validar

	Raises:
		SAFTXMLError: Se estrutura XML for inválida
	"""
	if not xml_content:
		raise SAFTXMLError(
			message=_("XML content cannot be empty"),
			xml_content=xml_content
		)

	# Verificar se começa com declaração XML
	if not xml_content.strip().startswith('<?xml'):
		raise SAFTXMLError(
			message=_("XML must start with XML declaration"),
			xml_content=xml_content[:100]
		)

	# Verificar elementos obrigatórios
	required_elements = [
		'<AuditFile',
		'<Header>',
		'<MasterFiles>',
		'<SourceDocuments>'
	]

	for element in required_elements:
		if element not in xml_content:
			raise SAFTXMLError(
				message=_("Missing required XML element: {0}").format(element),
				xml_element=element,
				xml_content=xml_content[:500]
			)


def validate_saft_schema(xml_content, schema_version="1.04_01"):
	"""
	Valida XML contra schema XSD do SAF-T

	Args:
		xml_content (str): Conteúdo XML
		schema_version (str): Versão do schema

	Raises:
		SAFTSchemaError: Se validação de schema falhar
	"""
	try:
		import lxml.etree as ET
		from lxml import etree

		# Carregar schema XSD
		schema_path = frappe.get_app_path("portugal_compliance", "xsd",
										  f"saftpt{schema_version}.xsd")

		if not frappe.os.path.exists(schema_path):
			raise SAFTSchemaError(
				message=_("SAF-T schema file not found: {0}").format(schema_path),
				schema_version=schema_version
			)

		with open(schema_path, 'r', encoding='utf-8') as schema_file:
			schema_doc = etree.parse(schema_file)
			schema = etree.XMLSchema(schema_doc)

		# Validar XML
		xml_doc = etree.fromstring(xml_content.encode('utf-8'))

		if not schema.validate(xml_doc):
			validation_errors = [str(error) for error in schema.error_log]
			raise SAFTSchemaError(
				message=_("SAF-T XML does not conform to schema"),
				schema_version=schema_version,
				validation_errors=validation_errors
			)

	except ImportError:
		frappe.log_error("lxml not available for SAF-T schema validation")
	except Exception as e:
		if not isinstance(e, SAFTSchemaError):
			raise SAFTSchemaError(
				message=_("Error validating SAF-T schema: {0}").format(str(e)),
				schema_version=schema_version
			)
		raise


def check_saft_file_size(xml_content, max_size_mb=100):
	"""
	Verifica tamanho do ficheiro SAF-T

	Args:
		xml_content (str): Conteúdo XML
		max_size_mb (int): Tamanho máximo em MB

	Raises:
		SAFTFileSizeError: Se ficheiro for muito grande
	"""
	file_size_bytes = len(xml_content.encode('utf-8'))
	file_size_mb = file_size_bytes / (1024 * 1024)

	if file_size_mb > max_size_mb:
		raise SAFTFileSizeError(
			message=_("SAF-T file size ({0:.2f} MB) exceeds maximum allowed ({1} MB)").format(
				file_size_mb, max_size_mb
			),
			file_size=file_size_mb,
			max_size=max_size_mb
		)


def validate_tax_information(tax_data):
	"""
	Valida informações de impostos para SAF-T

	Args:
		tax_data (dict): Dados de imposto

	Raises:
		SAFTTaxError: Se informações de imposto forem inválidas
	"""
	required_fields = ["tax_code", "tax_rate", "tax_type"]

	for field in required_fields:
		if field not in tax_data or tax_data[field] is None:
			raise SAFTTaxError(
				message=_("Missing required tax field: {0}").format(field),
				tax_code=tax_data.get("tax_code"),
				tax_rate=tax_data.get("tax_rate")
			)

	# Validar taxa de IVA
	tax_rate = tax_data.get("tax_rate", 0)
	valid_rates = [0, 6, 13, 23]  # Taxas válidas em Portugal

	if tax_rate not in valid_rates:
		raise SAFTTaxError(
			message=_("Invalid VAT rate: {0}%. Valid rates: {1}").format(
				tax_rate, ", ".join(map(str, valid_rates))
			),
			tax_code=tax_data.get("tax_code"),
			tax_rate=tax_rate
		)


# Exemplo de uso:
"""
try:
    validate_company_data_for_saft("Test Company")
    validate_date_range_for_saft(start_date, end_date)
    xml_content = generate_saft_xml(...)
    validate_xml_structure(xml_content)
    validate_saft_schema(xml_content)
    check_saft_file_size(xml_content)
except SAFTGenerationError as e:
    frappe.throw(str(e))
"""
