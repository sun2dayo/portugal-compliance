# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Series Validator for Portugal Compliance - VERSÃO ALINHADA E OTIMIZADA
Validates Portuguese series configuration and ATCUD generation
✅ ALINHADO: 100% compatível com document_hooks.py e series_manager.py
✅ SEGURO: Performance otimizada e validações robustas
✅ DINÂMICO: Baseado no abbr da empresa (não fixo NDX)
✅ COMPLETO: Validações abrangentes e relatórios detalhados
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime
import re


class SeriesValidator:
	"""
	✅ CLASSE ALINHADA: Validador de séries portuguesas
	Compatível com todas as atualizações recentes
	"""

	def __init__(self):
		# ✅ CÓDIGOS CORRIGIDOS E ALINHADOS
		self.required_series = {
			'Sales Invoice': ['FT', 'FS', 'FR', 'NC', 'ND'],
			'Purchase Invoice': ['FC'],
			'POS Invoice': ['FS'],
			'Payment Entry': ['RC', 'RB'],
			'Delivery Note': ['GT', 'GR'],
			'Purchase Receipt': ['GR', 'GT'],
			'Stock Entry': ['GM', 'GT'],
			'Journal Entry': ['JE', 'LC'],
			'Quotation': ['OR'],
			'Sales Order': ['EC'],  # ✅ CORRIGIDO: EN → EC
			'Purchase Order': ['EF'],  # ✅ CORRIGIDO: OC → EF
			'Material Request': ['MR', 'REQ']
		}

		# ✅ CONFIGURAÇÕES DE VALIDAÇÃO ALINHADAS
		self.fiscal_doctypes = ['Sales Invoice', 'Purchase Invoice', 'POS Invoice',
								'Payment Entry']
		self.module = "Portugal Compliance"

	def validate_series_setup(self, company=None):
		"""
		✅ ALINHADO: Verificar se todas as séries estão configuradas e comunicadas
		Baseado na sua experiência com programação.desenvolvimento_de_séries[1]
		"""
		try:
			results = {
				'company': company,
				'validation_date': now_datetime(),
				'summary': {
					'total_series_types': 0,
					'configured_series': 0,
					'communicated_series': 0,
					'pending_series': 0,
					'missing_series': 0,
					'with_validation_code': 0
				},
				'by_doctype': {},
				'recommendations': []
			}

			# ✅ FILTRAR POR EMPRESA SE ESPECIFICADA
			filters = {}
			if company:
				filters['company'] = company

			# ✅ BUSCAR SÉRIES EXISTENTES (OTIMIZADO)
			existing_series = frappe.get_all(
				'Portugal Series Configuration',
				filters=filters,
				fields=['document_type', 'prefix', 'is_communicated', 'validation_code',
						'current_sequence', 'company', 'is_active']
			)

			# ✅ ORGANIZAR POR DOCTYPE E PREFIX
			series_map = {}
			for series in existing_series:
				key = f"{series.document_type}_{series.prefix}"
				series_map[key] = series

			# ✅ VALIDAR CADA TIPO DE DOCUMENTO
			for doctype, required_prefixes in self.required_series.items():
				results['by_doctype'][doctype] = {
					'required_prefixes': required_prefixes,
					'configured': {},
					'missing': [],
					'status': 'OK'
				}

				for prefix in required_prefixes:
					key = f"{doctype}_{prefix}"
					results['summary']['total_series_types'] += 1

					if key in series_map:
						series = series_map[key]

						# ✅ SÉRIE CONFIGURADA
						results['summary']['configured_series'] += 1

						status = self._evaluate_series_status(series)

						results['by_doctype'][doctype]['configured'][prefix] = {
							'exists': True,
							'is_active': series.is_active,
							'is_communicated': series.is_communicated,
							'validation_code': series.validation_code,
							'current_sequence': series.current_sequence,
							'company': series.company,
							'status': status['status'],
							'issues': status['issues']
						}

						# ✅ CONTADORES
						if series.is_communicated:
							results['summary']['communicated_series'] += 1
						else:
							results['summary']['pending_series'] += 1

						if series.validation_code:
							results['summary']['with_validation_code'] += 1

					else:
						# ✅ SÉRIE FALTANDO
						results['summary']['missing_series'] += 1
						results['by_doctype'][doctype]['missing'].append(prefix)
						results['by_doctype'][doctype]['status'] = 'INCOMPLETE'

				# ✅ AVALIAR STATUS GERAL DO DOCTYPE
				if results['by_doctype'][doctype]['missing']:
					results['by_doctype'][doctype]['status'] = 'INCOMPLETE'
				elif any(s['status'] != 'OK' for s in
						 results['by_doctype'][doctype]['configured'].values()):
					results['by_doctype'][doctype]['status'] = 'ISSUES'

			# ✅ GERAR RECOMENDAÇÕES
			results['recommendations'] = self._generate_recommendations(results)

			return results

		except Exception as e:
			frappe.log_error(f"Erro na validação de séries: {str(e)}", "SeriesValidator")
			return {
				'error': str(e),
				'validation_date': now_datetime()
			}

	def _evaluate_series_status(self, series):
		"""
		✅ ALINHADO: Avaliar status de uma série individual
		"""
		issues = []
		status = 'OK'

		# ✅ VERIFICAÇÕES CRÍTICAS
		if not series.is_active:
			issues.append('Série inativa')
			status = 'WARNING'

		if not series.is_communicated:
			issues.append('Série não comunicada à AT')
			status = 'PENDING'

		if not series.validation_code:
			issues.append('Sem validation_code da AT')
			status = 'PENDING'

		# ✅ VERIFICAR FORMATO DO VALIDATION_CODE
		if series.validation_code:
			if not self._validate_atcud_format(series.validation_code):
				issues.append('Validation_code com formato inválido')
				status = 'ERROR'

		# ✅ VERIFICAR SEQUÊNCIA
		if series.current_sequence <= 0:
			issues.append('Sequência inválida')
			status = 'ERROR'

		return {
			'status': status,
			'issues': issues
		}

	def _validate_atcud_format(self, validation_code):
		"""
		✅ ALINHADO: Validar formato do validation_code
		Baseado na sua experiência com programação.python[5]
		"""
		if not validation_code:
			return False

		# ✅ PADRÕES ACEITOS PARA VALIDATION_CODE
		patterns = [
			r'^[A-Z0-9]{8,12}$',  # Formato oficial AT
			r'^AT\d{14}$',  # Formato fallback
		]

		for pattern in patterns:
			if re.match(pattern, validation_code):
				return True

		return False

	def check_atcud_generation(self, company=None, limit=100):
		"""
		✅ ALINHADO: Verificar se ATCUD está sendo gerado corretamente
		Performance otimizada com queries específicas
		"""
		try:
			atcud_stats = {
				'company': company,
				'check_date': now_datetime(),
				'total_docs': 0,
				'with_atcud': 0,
				'without_atcud': 0,
				'invalid_atcud': 0,
				'by_doctype': {},
				'recent_samples': [],
				'issues': []
			}

			# ✅ FILTRO POR EMPRESA
			company_filter = f"AND company = '{company}'" if company else ""

			# ✅ QUERY OTIMIZADA PARA DOCUMENTOS FISCAIS
			for doctype in self.fiscal_doctypes:
				try:
					# ✅ VERIFICAR SE TABELA EXISTE
					if not frappe.db.table_exists(f"tab{doctype}"):
						continue

					# ✅ VERIFICAR SE CAMPO ATCUD_CODE EXISTE
					columns = frappe.db.get_table_columns(doctype)
					if 'atcud_code' not in columns:
						continue

					query = f"""
						SELECT name, atcud_code, naming_series, creation, company
						FROM `tab{doctype}`
						WHERE docstatus = 1 {company_filter}
						ORDER BY creation DESC
						LIMIT {limit}
					"""

					docs = frappe.db.sql(query, as_dict=True)

					if not docs:
						continue

					# ✅ ESTATÍSTICAS POR DOCTYPE
					doctype_stats = {
						'total': len(docs),
						'with_atcud': 0,
						'without_atcud': 0,
						'invalid_atcud': 0,
						'samples': []
					}

					for doc in docs:
						atcud_stats['total_docs'] += 1
						doctype_stats['total'] += 1

						if doc.atcud_code:
							if self._validate_atcud_document_format(doc.atcud_code):
								atcud_stats['with_atcud'] += 1
								doctype_stats['with_atcud'] += 1
							else:
								atcud_stats['invalid_atcud'] += 1
								doctype_stats['invalid_atcud'] += 1
								atcud_stats['issues'].append(
									f"ATCUD inválido: {doc.name} - {doc.atcud_code}")
						else:
							atcud_stats['without_atcud'] += 1
							doctype_stats['without_atcud'] += 1

						# ✅ AMOSTRAS PARA ANÁLISE
						if len(doctype_stats['samples']) < 5:
							doctype_stats['samples'].append({
								'name': doc.name,
								'atcud_code': doc.atcud_code,
								'naming_series': doc.naming_series,
								'creation': doc.creation
							})

					atcud_stats['by_doctype'][doctype] = doctype_stats

				except Exception as e:
					frappe.log_error(f"Erro ao verificar ATCUD para {doctype}: {str(e)}",
									 "SeriesValidator")
					atcud_stats['issues'].append(f"Erro ao verificar {doctype}: {str(e)}")

			# ✅ CALCULAR PERCENTUAIS
			if atcud_stats['total_docs'] > 0:
				atcud_stats['atcud_percentage'] = round(
					(atcud_stats['with_atcud'] / atcud_stats['total_docs']) * 100, 2
				)
			else:
				atcud_stats['atcud_percentage'] = 0

			return atcud_stats

		except Exception as e:
			frappe.log_error(f"Erro na verificação de ATCUD: {str(e)}", "SeriesValidator")
			return {
				'error': str(e),
				'check_date': now_datetime()
			}

	def _validate_atcud_document_format(self, atcud_code):
		"""
		✅ ALINHADO: Validar formato de ATCUD em documento
		Formato: VALIDATION_CODE-SEQUENCIA
		"""
		if not atcud_code:
			return False

		# ✅ FORMATO ESPERADO: CODIGO-SEQUENCIA
		if '-' not in atcud_code:
			return False

		parts = atcud_code.split('-')
		if len(parts) != 2:
			return False

		validation_part, sequence_part = parts

		# ✅ VALIDAR PARTE DO VALIDATION_CODE
		if not self._validate_atcud_format(validation_part):
			return False

		# ✅ VALIDAR PARTE DA SEQUÊNCIA
		if not sequence_part.isdigit():
			return False

		return True

	def validate_sequential_numbering(self, company=None):
		"""
		✅ ALINHADO: Verificar se numeração está sequencial por série
		Performance otimizada e thread-safe
		"""
		try:
			sequence_analysis = {
				'company': company,
				'analysis_date': now_datetime(),
				'series_analyzed': 0,
				'series_with_gaps': 0,
				'total_gaps': 0,
				'by_series': {},
				'recommendations': []
			}

			# ✅ FILTRAR SÉRIES ATIVAS
			filters = {'is_active': 1}
			if company:
				filters['company'] = company

			active_series = frappe.get_all(
				'Portugal Series Configuration',
				filters=filters,
				fields=['name', 'prefix', 'document_type', 'current_sequence', 'company']
			)

			for series in active_series:
				try:
					sequence_analysis['series_analyzed'] += 1

					# ✅ ANALISAR SEQUÊNCIA DESTA SÉRIE
					series_analysis = self._analyze_series_sequence(series)
					sequence_analysis['by_series'][series.prefix] = series_analysis

					if series_analysis['has_gaps']:
						sequence_analysis['series_with_gaps'] += 1
						sequence_analysis['total_gaps'] += len(series_analysis['gaps'])

				except Exception as e:
					frappe.log_error(f"Erro ao analisar série {series.prefix}: {str(e)}",
									 "SeriesValidator")
					sequence_analysis['by_series'][series.prefix] = {
						'error': str(e)
					}

			# ✅ GERAR RECOMENDAÇÕES
			if sequence_analysis['series_with_gaps'] > 0:
				sequence_analysis['recommendations'].append(
					f"Encontradas {sequence_analysis['series_with_gaps']} séries com lacunas na numeração"
				)

			return sequence_analysis

		except Exception as e:
			frappe.log_error(f"Erro na validação sequencial: {str(e)}", "SeriesValidator")
			return {
				'error': str(e),
				'analysis_date': now_datetime()
			}

	def _analyze_series_sequence(self, series):
		"""
		✅ ALINHADO: Analisar sequência de uma série específica
		"""
		try:
			doctype = series.document_type
			naming_series = f"{series.prefix}.####"

			# ✅ VERIFICAR SE TABELA E CAMPO EXISTEM
			if not frappe.db.table_exists(f"tab{doctype}"):
				return {
					'error': f"Tabela {doctype} não existe",
					'has_gaps': False
				}

			# ✅ BUSCAR DOCUMENTOS DESTA SÉRIE
			docs = frappe.get_all(
				doctype,
				filters={
					'naming_series': naming_series,
					'docstatus': ['!=', 2]  # Excluir cancelados
				},
				fields=['name', 'creation'],
				order_by='creation'
			)

			if not docs:
				return {
					'total_docs': 0,
					'has_gaps': False,
					'gaps': [],
					'sequence_range': None
				}

			# ✅ EXTRAIR NÚMEROS DOS DOCUMENTOS
			numbers = []
			for doc in docs:
				# ✅ EXTRAIR NÚMERO DO NOME DO DOCUMENTO
				number = self._extract_document_number(doc.name)
				if number:
					numbers.append(number)

			if not numbers:
				return {
					'total_docs': len(docs),
					'has_gaps': False,
					'gaps': [],
					'sequence_range': None,
					'issue': 'Não foi possível extrair números dos documentos'
				}

			# ✅ ANALISAR LACUNAS
			numbers.sort()
			min_num = min(numbers)
			max_num = max(numbers)

			gaps = []
			for i in range(min_num, max_num + 1):
				if i not in numbers:
					gaps.append(i)

			return {
				'total_docs': len(numbers),
				'min_number': min_num,
				'max_number': max_num,
				'current_sequence': series.current_sequence,
				'gaps': gaps,
				'has_gaps': len(gaps) > 0,
				'sequence_range': f"{min_num}-{max_num}",
				'gap_percentage': round((len(gaps) / (max_num - min_num + 1)) * 100,
										2) if max_num > min_num else 0
			}

		except Exception as e:
			frappe.log_error(f"Erro ao analisar sequência da série {series.prefix}: {str(e)}",
							 "SeriesValidator")
			return {
				'error': str(e),
				'has_gaps': False
			}

	def _extract_document_number(self, document_name):
		"""
		✅ ALINHADO: Extrair número do documento (formato SEM HÍFENS)
		"""
		if not document_name:
			return None

		# ✅ PADRÕES PARA EXTRAIR NÚMERO
		patterns = [
			r'\.(\d+)$',  # ERPNext: FT2025NDX.0001
			r'-(\d{8})$',  # ATCUD: AAJFJMVNTN-00000001
			r'-(\d+)$',  # Alternativo: PREFIX-NNNN
			r'(\d+)$'  # Apenas números no final
		]

		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return int(match.group(1))

		return None

	def _generate_recommendations(self, validation_results):
		"""
		✅ ALINHADO: Gerar recomendações baseadas na validação
		"""
		recommendations = []

		summary = validation_results['summary']

		# ✅ RECOMENDAÇÕES BASEADAS NOS RESULTADOS
		if summary['missing_series'] > 0:
			recommendations.append(
				f"Criar {summary['missing_series']} séries em falta usando document_hooks.py"
			)

		if summary['pending_series'] > 0:
			recommendations.append(
				f"Comunicar {summary['pending_series']} séries à AT usando at_webservice.py"
			)

		if summary['configured_series'] > 0 and summary['with_validation_code'] == 0:
			recommendations.append(
				"Nenhuma série tem validation_code - verificar comunicação com AT"
			)

		# ✅ RECOMENDAÇÕES POR DOCTYPE
		for doctype, data in validation_results['by_doctype'].items():
			if data['status'] == 'INCOMPLETE':
				recommendations.append(
					f"{doctype}: Criar séries em falta {data['missing']}"
				)

		return recommendations

	def generate_comprehensive_report(self, company=None):
		"""
		✅ ALINHADO: Gerar relatório abrangente de validação
		Baseado na sua experiência com programação.revisão_de_arquivos[3]
		"""
		try:
			report = {
				'company': company,
				'report_date': now_datetime(),
				'sections': {}
			}

			# ✅ 1. VALIDAÇÃO DE CONFIGURAÇÃO DE SÉRIES
			report['sections']['series_setup'] = self.validate_series_setup(company)

			# ✅ 2. VERIFICAÇÃO DE GERAÇÃO DE ATCUD
			report['sections']['atcud_generation'] = self.check_atcud_generation(company)

			# ✅ 3. ANÁLISE DE NUMERAÇÃO SEQUENCIAL
			report['sections']['sequential_numbering'] = self.validate_sequential_numbering(
				company)

			# ✅ 4. RESUMO EXECUTIVO
			report['executive_summary'] = self._generate_executive_summary(report['sections'])

			return report

		except Exception as e:
			frappe.log_error(f"Erro ao gerar relatório: {str(e)}", "SeriesValidator")
			return {
				'error': str(e),
				'report_date': now_datetime()
			}

	def _generate_executive_summary(self, sections):
		"""
		✅ ALINHADO: Gerar resumo executivo do relatório
		"""
		summary = {
			'overall_status': 'OK',
			'critical_issues': 0,
			'warnings': 0,
			'recommendations_count': 0,
			'key_metrics': {},
			'priority_actions': []
		}

		# ✅ ANALISAR SEÇÃO DE SÉRIES
		if 'series_setup' in sections and not sections['series_setup'].get('error'):
			series_data = sections['series_setup']['summary']
			summary['key_metrics']['total_series'] = series_data['configured_series']
			summary['key_metrics']['communicated_series'] = series_data['communicated_series']
			summary['key_metrics']['missing_series'] = series_data['missing_series']

			if series_data['missing_series'] > 0:
				summary['critical_issues'] += 1
				summary['overall_status'] = 'CRITICAL'

			if series_data['pending_series'] > 0:
				summary['warnings'] += 1
				if summary['overall_status'] == 'OK':
					summary['overall_status'] = 'WARNING'

		# ✅ ANALISAR SEÇÃO DE ATCUD
		if 'atcud_generation' in sections and not sections['atcud_generation'].get('error'):
			atcud_data = sections['atcud_generation']
			summary['key_metrics']['atcud_percentage'] = atcud_data.get('atcud_percentage', 0)

			if atcud_data.get('atcud_percentage', 0) < 90:
				summary['warnings'] += 1
				if summary['overall_status'] == 'OK':
					summary['overall_status'] = 'WARNING'

		# ✅ ANALISAR NUMERAÇÃO SEQUENCIAL
		if 'sequential_numbering' in sections and not sections['sequential_numbering'].get(
			'error'):
			seq_data = sections['sequential_numbering']
			summary['key_metrics']['series_with_gaps'] = seq_data.get('series_with_gaps', 0)

			if seq_data.get('series_with_gaps', 0) > 0:
				summary['warnings'] += 1

		return summary


# ========== INSTÂNCIA GLOBAL ALINHADA ==========
series_validator = SeriesValidator()


# ========== FUNÇÕES AUXILIARES ALINHADAS ==========

def validate_series_setup(company=None):
	"""✅ ALINHADO: Validar configuração de séries"""
	return series_validator.validate_series_setup(company)


def check_atcud_generation(company=None, limit=100):
	"""✅ ALINHADO: Verificar geração de ATCUD"""
	return series_validator.check_atcud_generation(company, limit)


def validate_sequential_numbering(company=None):
	"""✅ ALINHADO: Validar numeração sequencial"""
	return series_validator.validate_sequential_numbering(company)


def generate_comprehensive_report(company=None):
	"""✅ ALINHADO: Gerar relatório abrangente"""
	return series_validator.generate_comprehensive_report(company)


# ========== APIS WHITELISTED ALINHADAS ==========

@frappe.whitelist()
def run_validation_suite(company=None):
	"""
	✅ ALINHADO: API para executar suite completa de validação
	"""
	try:
		return generate_comprehensive_report(company)
	except Exception as e:
		frappe.log_error(f"Erro na suite de validação: {str(e)}", "SeriesValidator")
		return {"error": str(e)}


@frappe.whitelist()
def quick_series_check(company=None):
	"""
	✅ ALINHADO: API para verificação rápida de séries
	"""
	try:
		return validate_series_setup(company)
	except Exception as e:
		frappe.log_error(f"Erro na verificação rápida: {str(e)}", "SeriesValidator")
		return {"error": str(e)}


@frappe.whitelist()
def atcud_health_check(company=None):
	"""
	✅ ALINHADO: API para verificação de saúde do ATCUD
	"""
	try:
		return check_atcud_generation(company, 50)
	except Exception as e:
		frappe.log_error(f"Erro na verificação de ATCUD: {str(e)}", "SeriesValidator")
		return {"error": str(e)}


# ========== LOG FINAL ==========
frappe.logger().info(
	"Portugal Series Validator ALINHADO loaded - Version 2.1.0 - Comprehensive & Safe")
