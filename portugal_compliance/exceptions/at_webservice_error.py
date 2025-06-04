# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Exceções personalizadas para o webservice da Autoridade Tributária (AT)
"""

import frappe
from frappe import _


class ATWebserviceError(Exception):
	"""
	Exceção base para erros relacionados com o webservice da Autoridade Tributária (AT)
	"""

	def __init__(self, message=None, error_code=None, details=None):
		if message is None:
			message = _("Unknown error in AT webservice")

		self.error_code = error_code
		self.details = details or {}

		# Log do erro para debugging
		frappe.log_error(
			title=f"AT Webservice Error: {error_code or 'Unknown'}",
			message=f"Message: {message}\nDetails: {self.details}"
		)

		super().__init__(message)

	def __str__(self):
		if self.error_code:
			return f"[{self.error_code}] {super().__str__()}"
		return super().__str__()


class ATAuthenticationError(ATWebserviceError):
	"""
	Exceção para erros de autenticação com o webservice da AT
	"""

	def __init__(self, message=None, username=None):
		if message is None:
			message = _("Authentication failed with AT webservice")

		details = {"username": username} if username else {}
		super().__init__(message, error_code="AUTH_ERROR", details=details)


class ATCommunicationError(ATWebserviceError):
	"""
	Exceção para erros de comunicação com o webservice da AT
	"""

	def __init__(self, message=None, status_code=None, response_data=None):
		if message is None:
			message = _("Communication error with AT webservice")

		details = {
			"status_code": status_code,
			"response_data": response_data
		}
		super().__init__(message, error_code="COMM_ERROR", details=details)


class ATValidationError(ATWebserviceError):
	"""
	Exceção para erros de validação de dados enviados para a AT
	"""

	def __init__(self, message=None, field=None, value=None):
		if message is None:
			message = _("Data validation error for AT webservice")

		details = {
			"field": field,
			"value": value
		}
		super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class ATSeriesError(ATWebserviceError):
	"""
	Exceção para erros específicos de séries documentais
	"""

	def __init__(self, message=None, series_prefix=None, operation=None):
		if message is None:
			message = _("Series operation error with AT webservice")

		details = {
			"series_prefix": series_prefix,
			"operation": operation
		}
		super().__init__(message, error_code="SERIES_ERROR", details=details)


class ATTimeoutError(ATWebserviceError):
	"""
	Exceção para timeouts na comunicação com a AT
	"""

	def __init__(self, message=None, timeout_duration=None):
		if message is None:
			message = _("Timeout error communicating with AT webservice")

		details = {"timeout_duration": timeout_duration}
		super().__init__(message, error_code="TIMEOUT_ERROR", details=details)


class ATRateLimitError(ATWebserviceError):
	"""
	Exceção para erros de rate limiting da AT
	"""

	def __init__(self, message=None, retry_after=None):
		if message is None:
			message = _("Rate limit exceeded for AT webservice")

		details = {"retry_after": retry_after}
		super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details)


class ATMaintenanceError(ATWebserviceError):
	"""
	Exceção para quando o webservice da AT está em manutenção
	"""

	def __init__(self, message=None, maintenance_until=None):
		if message is None:
			message = _("AT webservice is under maintenance")

		details = {"maintenance_until": maintenance_until}
		super().__init__(message, error_code="MAINTENANCE_ERROR", details=details)


class ATCertificateError(ATWebserviceError):
	"""
	Exceção para erros relacionados com certificados SSL/TLS
	"""

	def __init__(self, message=None, certificate_info=None):
		if message is None:
			message = _("SSL/TLS certificate error with AT webservice")

		details = {"certificate_info": certificate_info}
		super().__init__(message, error_code="CERTIFICATE_ERROR", details=details)


# Mapeamento de códigos de erro HTTP para exceções específicas
HTTP_ERROR_MAPPING = {
	400: ATValidationError,
	401: ATAuthenticationError,
	403: ATAuthenticationError,
	408: ATTimeoutError,
	429: ATRateLimitError,
	500: ATWebserviceError,
	502: ATCommunicationError,
	503: ATMaintenanceError,
	504: ATTimeoutError
}


def handle_at_error(response=None, error_message=None, **kwargs):
	"""
	Função utilitária para tratar erros da AT e lançar a exceção apropriada

	Args:
		response: Objeto de resposta HTTP
		error_message: Mensagem de erro personalizada
		**kwargs: Argumentos adicionais para a exceção

	Raises:
		ATWebserviceError: Exceção apropriada baseada no tipo de erro
	"""
	if response is not None:
		status_code = getattr(response, 'status_code', None)

		if status_code in HTTP_ERROR_MAPPING:
			exception_class = HTTP_ERROR_MAPPING[status_code]

			# Tentar extrair mensagem de erro da resposta
			try:
				response_data = response.json() if hasattr(response, 'json') else {}
				at_error_message = response_data.get('message') or response_data.get('error')

				if at_error_message:
					error_message = at_error_message
			except:
				pass

			raise exception_class(
				message=error_message,
				status_code=status_code,
				response_data=getattr(response, 'text', None),
				**kwargs
			)

	# Fallback para erro genérico
	raise ATWebserviceError(message=error_message, **kwargs)


def log_at_error(error, context=None):
	"""
	Função para registar erros da AT no sistema de logs do Frappe

	Args:
		error: Exceção ATWebserviceError
		context: Contexto adicional sobre o erro
	"""
	error_data = {
		"error_type": type(error).__name__,
		"error_message": str(error),
		"error_code": getattr(error, 'error_code', None),
		"details": getattr(error, 'details', {}),
		"context": context or {}
	}

	frappe.log_error(
		title=f"AT Webservice Error: {error_data['error_type']}",
		message=frappe.as_json(error_data, indent=2)
	)


# Exemplo de uso das exceções:
"""
try:
    # Comunicação com AT
    response = communicate_with_at()
except requests.exceptions.Timeout:
    raise ATTimeoutError("Request timeout after 30 seconds", timeout_duration=30)
except requests.exceptions.ConnectionError:
    raise ATCommunicationError("Failed to connect to AT webservice")
except Exception as e:
    handle_at_error(error_message=str(e))
"""
