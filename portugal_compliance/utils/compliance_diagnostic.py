# utils/compliance_diagnostic.py
import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def run_compliance_diagnostic():
	"""
	Executar diagnóstico completo do Portugal Compliance
	"""

	diagnostic = {
		'timestamp': now_datetime(),
		'series_validation': validate_series_setup(),
		'atcud_generation': check_atcud_generation(),
		'sequential_numbering': validate_sequential_numbering(),
		'company_setup': validate_company_setup(),
		'recommendations': []
	}

	# Gerar recomendações
	diagnostic['recommendations'] = generate_recommendations(diagnostic)

	return diagnostic


def validate_company_setup():
	"""
	Verificar configuração das empresas portuguesas
	"""

	portuguese_companies = frappe.get_all(
		'Company',
		filters={'country': 'Portugal'},
		fields=['name', 'portugal_compliance_enabled', 'at_environment', 'tax_id']
	)

	company_status = {}

	for company in portuguese_companies:
		company_status[company.name] = {
			'compliance_enabled': bool(company.portugal_compliance_enabled),
			'has_nif': bool(company.tax_id),
			'at_environment': company.at_environment or 'Not Set',
			'series_count': frappe.db.count(
				'Portugal Series Configuration',
				{'company': company.name}
			),
			'status': 'OK' if company.portugal_compliance_enabled and company.tax_id else 'INCOMPLETE'
		}

	return company_status


def generate_recommendations(diagnostic):
	"""
	Gerar recomendações baseadas no diagnóstico
	"""

	recommendations = []

	# Verificar séries não comunicadas
	for doctype, series in diagnostic['series_validation'].items():
		for prefix, info in series.items():
			if info.get('exists') and not info.get('communicated'):
				recommendations.append({
					'priority': 'HIGH',
					'type': 'SERIES_COMMUNICATION',
					'message': f"Comunicar série {prefix} para {doctype} à AT",
					'action': f"Aceder a Portugal Series Configuration e comunicar série {prefix}"
				})
			elif not info.get('exists'):
				recommendations.append({
					'priority': 'CRITICAL',
					'type': 'MISSING_SERIES',
					'message': f"Criar série {prefix} para {doctype}",
					'action': f"Executar setup automático ou criar manualmente"
				})

	# Verificar ATCUD
	atcud_stats = diagnostic['atcud_generation']
	if atcud_stats['without_atcud'] > 0:
		recommendations.append({
			'priority': 'HIGH',
			'type': 'ATCUD_MISSING',
			'message': f"{atcud_stats['without_atcud']} documentos sem ATCUD",
			'action': "Verificar hooks de geração automática de ATCUD"
		})

	# Verificar gaps na numeração
	#for prefix, gaps_info in diagnostic['sequential_numbering'].items():
	#	if gaps_info['has_gaps']:
	#		recommendations.append({
		#			'priority': 'MEDIUM',
		#			'type': 'NUMBERING_GAPS',
		#			'message': f"Série {prefix} tem {len(gaps_info['gaps'])} gaps na numeração",
		#			'action': "Investigar documentos cancelados ou problemas na sequência"
	#		})

	#return recommendations
