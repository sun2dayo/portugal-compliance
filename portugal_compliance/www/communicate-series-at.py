# www/communicate-series-at.py
import frappe
from frappe import _


def get_context(context):
	context.title = "Comunicação de Séries à AT"

	# Obter empresas portuguesas
	companies = frappe.get_all("Company",
							   filters={"country": "Portugal", "portugal_compliance_enabled": 1},
							   fields=["name", "abbr", "at_username", "at_environment"])

	# Obter naming series disponíveis
	naming_series = get_available_naming_series()

	context.companies = companies
	context.naming_series = naming_series

	return context


def get_available_naming_series():
	"""Obter naming series portuguesas disponíveis"""
	from portugal_compliance.utils.naming_series_customizer import get_naming_series_statistics
	stats = get_naming_series_statistics()
	return stats.get("statistics", {})
