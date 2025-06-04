# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Exceções personalizadas para geração de códigos ATCUD
"""

import frappe
from frappe import _


class ATCUDGenerationError(Exception):
	"""
	Exceção base para erros na geração de códigos ATCUD
	"""

	def __init__(self, message=None, error_code=None, details=None):
		if message is None:
			message = _("Error generating ATCUD code")

		self.error_code = error_code
		self.details = details or {}

		# Log do erro para debugging
		frappe.log_error(
			title=f"ATCUD Generation Error: {error_code or 'Unknown'}",
			message=f"Message: {message}\nDetails: {self.details}"
		)

		super().__init__(message)

	def __str__(self):
		if self.error_code:
			return f"[{self.error_code}] {super().__str__()}"
		return super().__str__()


class ATCUDValidationError(ATCUDGenerationError):
	"""
	Exceção para erros de validação de dados para geração de ATCUD
	"""

	def __init__(self, message=None, field=None, value=None, expected_format=None):
		if message is None:
			message = _("ATCUD validation error")

		details = {
			"field": field,
			"value": value,
			"expected_format": expected_format
		}
		super().__init__(message, error_code="ATCUD_VALIDATION_ERROR", details=details)

		# Atributos específicos para validação
		self.field = field
		self.value = value
		self.expected_format = expected_format


class ATCUDSeriesError(ATCUDGenerationError):
	"""
	Exceção para erros relacionados com séries documentais na geração de ATCUD
	"""

	def __init__(self, message=None, series_prefix=None, document_type=None):
		if message is None:
			message = _("ATCUD series error")

		details = {
			"series_prefix": series_prefix,
			"document_type": document_type
		}
		super().__init__(message, error_code="ATCUD_SERIES_ERROR", details=details)

		# Atributos específicos para séries
		self.series_prefix = series_prefix
		self.document_type = document_type


class ATCUDCompanyError(ATCUDGenerationError):
	"""
	Exceção para erros relacionados com dados da empresa na geração de ATCUD
	"""

	def __init__(self, message=None, company=None, missing_field=None):
		if message is None:
			message = _("ATCUD company configuration error")

		details = {
			"company": company,
			"missing_field": missing_field
		}
		super().__init__(message, error_code="ATCUD_COMPANY_ERROR", details=details)

		# Atributos específicos para empresa
		self.company = company
		self.missing_field = missing_field


class ATCUDSequenceError(ATCUDGenerationError):
	"""
	Exceção para erros na geração de sequência do ATCUD
	"""

	def __init__(self, message=None, document_number=None, sequence_type=None):
		if message is None:
			message = _("ATCUD sequence generation error")

		details = {
			"document_number": document_number,
			"sequence_type": sequence_type
		}
		super().__init__(message, error_code="ATCUD_SEQUENCE_ERROR", details=details)

		# Atributos específicos para sequência
		self.document_number = document_number
		self.sequence_type = sequence_type


class ATCUDChecksumError(ATCUDGenerationError):
	"""
	Exceção para erros no cálculo do dígito de verificação do ATCUD
	"""

	def __init__(self, message=None, validation_data=None, calculated_checksum=None):
		if message is None:
			message = _("ATCUD checksum calculation error")

		details = {
			"validation_data": validation_data,
			"calculated_checksum": calculated_checksum
		}
		super().__init__(message, error_code="ATCUD_CHECKSUM_ERROR", details=details)

		# Atributos específicos para checksum
		self.validation_data = validation_data
		self.calculated_checksum = calculated_checksum


class ATCUDFormatError(ATCUDGenerationError):
	"""
	Exceção para erros de formato do código ATCUD gerado
	"""

	def __init__(self, message=None, generated_code=None, expected_pattern=None):
		if message is None:
			message = _("ATCUD format error")

		details = {
			"generated_code": generated_code,
			"expected_pattern": expected_pattern
		}
		super().__init__(message, error_code="ATCUD_FORMAT_ERROR", details=details)

		# Atributos específicos para formato
		self.generated_code = generated_code
		self.expected_pattern = expected_pattern


class ATCUDDuplicateError(ATCUDGenerationError):
	"""
	Exceção para códigos ATCUD duplicados
	"""

	def __init__(self, message=None, atcud_code=None, existing_document=None):
		if message is None:
			message = _("Duplicate ATCUD code detected")

		details = {
			"atcud_code": atcud_code,
			"existing_document": existing_document
		}
		super().__init__(message, error_code="ATCUD_DUPLICATE_ERROR", details=details)

		# Atributos específicos para duplicação
		self.atcud_code = atcud_code
		self.existing_document = existing_document


class ATCUDConfigurationError(ATCUDGenerationError):
	"""
	Exceção para erros de configuração do sistema ATCUD
	"""

	def __init__(self, message=None, configuration_field=None, current_value=None):
		if message is None:
			message = _("ATCUD system configuration error")

		details = {
			"configuration_field": configuration_field,
			"current_value": current_value
		}
		super().__init__(message, error_code="ATCUD_CONFIG_ERROR", details=details)

		# Atributos específicos para configuração
		self.configuration_field = configuration_field
		self.current_value = current_value


# Funções utilitárias para tratamento de erros ATCUD

def validate_series_format(series_prefix):
	"""
	Valida formato da série e lança exceção específica se inválido

	Args:
		series_prefix (str): Prefixo da série a validar

	Raises:
		ATCUDSeriesError: Se o formato da série for inválido
	"""
	import re

	if not series_prefix:
		raise ATCUDSeriesError(
			message=_("Series prefix cannot be empty"),
			series_prefix=series_prefix
		)

	# Formato: XX-YYYY-COMPANY
	pattern = r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$"
	if not re.match(pattern, series_prefix):
		raise ATCUDSeriesError(
			message=_("Invalid series prefix format. Expected: XX-YYYY-COMPANY"),
			series_prefix=series_prefix
		)


def validate_company_data(company):
	"""
	Valida dados da empresa necessários para ATCUD

	Args:
		company (str): Nome da empresa

	Raises:
		ATCUDCompanyError: Se dados da empresa estiverem incompletos
	"""
	if not company:
		raise ATCUDCompanyError(
			message=_("Company name is required for ATCUD generation"),
			company=company,
			missing_field="company_name"
		)

	# Verificar se empresa existe
	if not frappe.db.exists("Company", company):
		raise ATCUDCompanyError(
			message=_("Company '{0}' does not exist").format(company),
			company=company,
			missing_field="company_existence"
		)

	# Verificar NIF da empresa
	tax_id = frappe.db.get_value("Company", company, "tax_id")
	if not tax_id:
		raise ATCUDCompanyError(
			message=_("Company '{0}' does not have a tax ID configured").format(company),
			company=company,
			missing_field="tax_id"
		)


def validate_document_number(document_number):
	"""
	Valida número do documento para geração de ATCUD

	Args:
		document_number (int): Número do documento

	Raises:
		ATCUDSequenceError: Se número do documento for inválido
	"""
	if not isinstance(document_number, int) or document_number <= 0:
		raise ATCUDSequenceError(
			message=_("Document number must be a positive integer"),
			document_number=document_number,
			sequence_type="document_number"
		)

	if document_number > 99999999:
		raise ATCUDSequenceError(
			message=_("Document number cannot exceed 99,999,999"),
			document_number=document_number,
			sequence_type="document_number"
		)


def validate_atcud_format(atcud_code):
	"""
	Valida formato do código ATCUD gerado

	Args:
		atcud_code (str): Código ATCUD a validar

	Raises:
		ATCUDFormatError: Se formato do ATCUD for inválido
	"""
	import re

	if not atcud_code:
		raise ATCUDFormatError(
			message=_("ATCUD code cannot be empty"),
			generated_code=atcud_code
		)

	# Formato: SEQUENCIA-DIGITO
	pattern = r"^[A-Z0-9]+-\d$"
	if not re.match(pattern, atcud_code):
		raise ATCUDFormatError(
			message=_("Invalid ATCUD format. Expected: SEQUENCE-DIGIT"),
			generated_code=atcud_code,
			expected_pattern=pattern
		)


def check_atcud_uniqueness(atcud_code, exclude_document=None):
	"""
	Verifica se código ATCUD é único no sistema

	Args:
		atcud_code (str): Código ATCUD a verificar
		exclude_document (str): Documento a excluir da verificação

	Raises:
		ATCUDDuplicateError: Se código ATCUD já existir
	"""
	# Lista de doctypes que podem ter ATCUD
	doctypes_with_atcud = [
		"Sales Invoice", "Purchase Invoice", "Payment Entry",
		"Delivery Note", "Purchase Receipt", "Journal Entry", "Stock Entry"
	]

	for doctype in doctypes_with_atcud:
		filters = {"atcud_code": atcud_code}
		if exclude_document:
			filters["name"] = ["!=", exclude_document]

		existing = frappe.db.exists(doctype, filters)
		if existing:
			raise ATCUDDuplicateError(
				message=_("ATCUD code '{0}' already exists in {1} '{2}'").format(
					atcud_code, doctype, existing
				),
				atcud_code=atcud_code,
				existing_document=existing
			)


# Exemplo de uso:
"""
try:
    validate_series_format("FT-2025-COMP")
    validate_company_data("Test Company")
    validate_document_number(123)
    atcud = generate_atcud_code(...)
    validate_atcud_format(atcud)
    check_atcud_uniqueness(atcud)
except ATCUDGenerationError as e:
    frappe.throw(str(e))
"""
