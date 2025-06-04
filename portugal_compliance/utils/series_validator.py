# utils/series_validator.py
import frappe


def validate_series_setup():
	"""
	Verificar se todas as séries estão configuradas e comunicadas
	"""

	# Tipos de documento obrigatórios
	required_series = {
		'Sales Invoice': ['FT', 'FS', 'FR', 'NC', 'ND'],
		'Purchase Invoice': ['FC'],
		'POS Invoice': ['FS'],
		'Quotation': ['OR'],
		'Sales Order': ['EN'],
		'Purchase Order': ['OC'],
		'Delivery Note': ['GT'],
		'Purchase Receipt': ['GR'],
		'Stock Entry': ['GM'],
		'Journal Entry': ['JE', 'LC'],
		'Payment Entry': ['RC', 'RG']
	}

	results = {}

	for doctype, prefixes in required_series.items():
		results[doctype] = {}

		for prefix in prefixes:
			# Verificar se série existe
			series = frappe.db.get_value(
				'Portugal Series Configuration',
				{'document_type': doctype, 'prefix': prefix},
				['name', 'is_communicated', 'validation_code', 'current_sequence']
			)

			if series:
				results[doctype][prefix] = {
					'exists': True,
					'communicated': bool(series[1]),
					'validation_code': series[2],
					'current_sequence': series[3],
					'status': 'OK' if series[1] and series[2] else 'PENDING'
				}
			else:
				results[doctype][prefix] = {
					'exists': False,
					'status': 'MISSING'
				}

	return results


def check_atcud_generation():
	"""
	Verificar se ATCUD está sendo gerado corretamente
	"""

	# Verificar documentos recentes com ATCUD
	recent_docs = frappe.db.sql("""
								SELECT doctype,
									   name,
									   atcud_code,
									   naming_series,
									   creation
								FROM (SELECT 'Sales Invoice' as doctype,
											 name,
											 atcud_code,
											 naming_series,
											 creation
									  FROM `tabSales Invoice`
									  WHERE docstatus = 1
									  UNION ALL
									  SELECT 'Purchase Invoice' as doctype,
											 name,
											 atcud_code,
											 naming_series,
											 creation
									  FROM `tabPurchase Invoice`
									  WHERE docstatus = 1
									  UNION ALL
									  SELECT 'POS Invoice' as doctype,
											 name,
											 atcud_code,
											 naming_series,
											 creation
									  FROM `tabPOS Invoice`
									  WHERE docstatus = 1) combined
								ORDER BY creation DESC LIMIT 50
								""", as_dict=True)

	atcud_stats = {
		'total_docs': len(recent_docs),
		'with_atcud': len([d for d in recent_docs if d.atcud_code]),
		'without_atcud': len([d for d in recent_docs if not d.atcud_code]),
		'by_doctype': {}
	}

	for doc in recent_docs:
		if doc.doctype not in atcud_stats['by_doctype']:
			atcud_stats['by_doctype'][doc.doctype] = {'total': 0, 'with_atcud': 0}

		atcud_stats['by_doctype'][doc.doctype]['total'] += 1
		if doc.atcud_code:
			atcud_stats['by_doctype'][doc.doctype]['with_atcud'] += 1

	return atcud_stats


def validate_sequential_numbering():
	"""
	Verificar se numeração está sequencial por série
	"""

	series_gaps = {}

	# Verificar cada série ativa
	active_series = frappe.get_all(
		'Portugal Series Configuration',
		filters={'is_active': 1},
		fields=['prefix', 'document_type', 'current_sequence']
	)

	for series in active_series:
		# Buscar documentos desta série
		if series.document_type == 'Sales Invoice':
			docs = frappe.db.get_all(
				'Sales Invoice',
				filters={'naming_series': {'like': f"{series.prefix}%"}},
				fields=['name', 'creation'],
				order_by='creation'
			)
		elif series.document_type == 'Purchase Invoice':
			docs = frappe.db.get_all(
				'Purchase Invoice',
				filters={'naming_series': {'like': f"{series.prefix}%"}},
				fields=['name', 'creation'],
				order_by='creation'
			)
		# ... adicionar outros doctypes

		# Verificar sequência
		if docs:
			numbers = [int(doc.name.split('.')[-1]) for doc in docs if
					   doc.name.split('.')[-1].isdigit()]
			if numbers:
				gaps = []
				for i in range(min(numbers), max(numbers) + 1):
					if i not in numbers:
						gaps.append(i)

				series_gaps[series.prefix] = {
					'total_docs': len(numbers),
					'min_number': min(numbers),
					'max_number': max(numbers),
					'gaps': gaps,
					'has_gaps': len(gaps) > 0
				}

	return series_gaps
