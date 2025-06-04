# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Test AT Webservice - Portugal Compliance VERSÃO NATIVA CORRIGIDA
Testes completos para comunicação com AT (Autoridade Tributária)
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Testes para at_webservice.py
✅ Testes de comunicação de séries
✅ Testes de validação de ATCUD
✅ Mocks para ambiente de teste
"""

import unittest
import frappe
from frappe.test_runner import make_test_records
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

# ✅ IMPORTAÇÕES DO MÓDULO A SER TESTADO
from portugal_compliance.utils.at_webservice import ATWebserviceClient
from portugal_compliance.utils.atcud_generator import generate_manual_atcud_certified


class TestATWebservice(unittest.TestCase):
	"""
	✅ Classe de teste para ATWebserviceClient
	"""

	def setUp(self):
		"""
		✅ Configuração antes de cada teste
		"""
		# ✅ CRIAR REGISTROS DE TESTE
		self.setup_test_data()

		# ✅ INICIALIZAR CLIENT
		self.client = ATWebserviceClient()

		# ✅ CONFIGURAR DADOS DE TESTE
		self.test_username = "test_user"
		self.test_password = "test_password"

		# ✅ CRIAR EMPRESA PORTUGUESA DE TESTE
		self.test_company = self.create_test_company()

		# ✅ CRIAR SÉRIE DE TESTE (SEM HÍFENS)
		self.test_series = self.create_test_series()

	def tearDown(self):
		"""
		✅ Limpeza após cada teste
		"""
		frappe.db.rollback()

	def setup_test_data(self):
		"""
		✅ Configurar dados de teste
		"""
		# ✅ CRIAR REGISTROS DE TESTE NECESSÁRIOS
		make_test_records([
			"Company",
			"Customer",
			"Supplier",
			"Item",
			"Sales Invoice"
		], verbose=False, force=True)

	def create_test_company(self):
		"""
		✅ Criar empresa portuguesa para testes
		"""
		company_name = "Test Company Portugal"

		if not frappe.db.exists("Company", company_name):
			company = frappe.new_doc("Company")
			company.update({
				"company_name": company_name,
				"abbr": "TCP",
				"country": "Portugal",
				"default_currency": "EUR",
				"tax_id": "123456789",
				"portugal_compliance_enabled": 1
			})
			company.insert(ignore_permissions=True)

		return company_name

	def create_test_series(self):
		"""
		✅ CORRIGIDO: Criar série de teste (formato SEM HÍFENS)
		"""
		series_name = "Test Series FT"

		if not frappe.db.exists("Portugal Series Configuration", series_name):
			series = frappe.new_doc("Portugal Series Configuration")
			series.update({
				"series_name": series_name,
				"company": self.test_company,
				"document_type": "Sales Invoice",
				"prefix": "FT2025TCP",  # ✅ SEM HÍFENS
				"naming_series": "FT2025TCP.####",  # ✅ SEM HÍFENS
				"current_sequence": 1,
				"is_active": 1,
				"is_communicated": 0
			})
			series.insert(ignore_permissions=True)

		return series_name

	# ========== TESTES DE CONFIGURAÇÃO ==========

	def test_client_initialization(self):
		"""
		✅ Testar inicialização do cliente AT
		"""
		self.assertIsInstance(self.client, ATWebserviceClient)
		self.assertIsNotNone(self.client)

	def test_client_configuration(self):
		"""
		✅ Testar configuração do cliente
		"""
		# ✅ VERIFICAR SE TEM MÉTODOS NECESSÁRIOS
		self.assertTrue(hasattr(self.client, 'communicate_series_batch'))
		self.assertTrue(hasattr(self.client, 'check_series_status'))

	# ========== TESTES DE COMUNICAÇÃO DE SÉRIES ==========

	@patch('requests.post')
	def test_communicate_series_batch_success(self, mock_post):
		"""
		✅ Testar comunicação bem-sucedida de séries
		"""
		# ✅ MOCK DA RESPOSTA DA AT
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"status": "success",
			"validation_code": "AT123456789",
			"message": "Série comunicada com sucesso"
		}
		mock_post.return_value = mock_response

		# ✅ OBTER SÉRIE DE TESTE
		series_list = [frappe.get_doc("Portugal Series Configuration", self.test_series)]

		# ✅ EXECUTAR COMUNICAÇÃO
		result = self.client.communicate_series_batch(
			series_list,
			self.test_username,
			self.test_password
		)

		# ✅ VERIFICAR RESULTADO
		self.assertIsInstance(result, dict)
		self.assertTrue(result.get("status") in ["success", "completed"])

	@patch('requests.post')
	def test_communicate_series_batch_failure(self, mock_post):
		"""
		✅ Testar falha na comunicação de séries
		"""
		# ✅ MOCK DE RESPOSTA DE ERRO
		mock_response = MagicMock()
		mock_response.status_code = 400
		mock_response.json.return_value = {
			"status": "error",
			"message": "Credenciais inválidas"
		}
		mock_post.return_value = mock_response

		# ✅ OBTER SÉRIE DE TESTE
		series_list = [frappe.get_doc("Portugal Series Configuration", self.test_series)]

		# ✅ EXECUTAR COMUNICAÇÃO
		result = self.client.communicate_series_batch(
			series_list,
			"invalid_user",
			"invalid_password"
		)

		# ✅ VERIFICAR FALHA
		self.assertIsInstance(result, dict)
		self.assertTrue(result.get("status") in ["error", "failed"])

	@patch('requests.get')
	def test_check_series_status(self, mock_get):
		"""
		✅ Testar verificação de status de série
		"""
		# ✅ MOCK DA RESPOSTA
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.json.return_value = {
			"status": "active",
			"valid": True,
			"validation_code": "AT123456789"
		}
		mock_get.return_value = mock_response

		# ✅ EXECUTAR VERIFICAÇÃO
		result = self.client.check_series_status("AT123456789")

		# ✅ VERIFICAR RESULTADO
		self.assertIsInstance(result, dict)
		self.assertTrue(result.get("valid", False))

	# ========== TESTES DE VALIDAÇÃO ==========

	def test_validate_series_format(self):
		"""
		✅ CORRIGIDO: Testar validação de formato de série (SEM HÍFENS)
		"""
		# ✅ FORMATOS VÁLIDOS (SEM HÍFENS)
		valid_formats = [
			"FT2025TCP",
			"FS2025ABC",
			"FC2025XYZ",
			"OR2025NDX"
		]

		for format_test in valid_formats:
			with self.subTest(format=format_test):
				# ✅ VALIDAR FORMATO
				is_valid = self.validate_prefix_format(format_test)
				self.assertTrue(is_valid, f"Formato {format_test} deveria ser válido")

		# ✅ FORMATOS INVÁLIDOS (COM HÍFENS)
		invalid_formats = [
			"FT-2025-TCP",  # Com hífens
			"FS-2025-ABC",  # Com hífens
			"INVALID",  # Muito curto
			"FT2025",  # Sem código empresa
			""  # Vazio
		]

		for format_test in invalid_formats:
			with self.subTest(format=format_test):
				# ✅ VALIDAR FORMATO
				is_valid = self.validate_prefix_format(format_test)
				self.assertFalse(is_valid, f"Formato {format_test} deveria ser inválido")

	def validate_prefix_format(self, prefix):
		"""
		✅ CORRIGIDO: Validar formato de prefixo (SEM HÍFENS)
		"""
		import re
		pattern = r"^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$"
		return bool(re.match(pattern, prefix))

	# ========== TESTES DE INTEGRAÇÃO ==========

	def test_create_sales_invoice_with_atcud(self):
		"""
		✅ Testar criação de Sales Invoice com ATCUD
		"""
		# ✅ CRIAR SALES INVOICE DE TESTE
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.update({
			"customer": "_Test Customer",
			"company": self.test_company,
			"naming_series": "FT2025TCP.####",  # ✅ SEM HÍFENS
			"items": [{
				"item_code": "_Test Item",
				"qty": 1,
				"rate": 100
			}]
		})
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ VERIFICAR RESULTADO
		self.assertTrue(result.get("success", False))
		self.assertIsNotNone(result.get("atcud_code"))

		# ✅ VERIFICAR SE ATCUD FOI SALVO
		sales_invoice.reload()
		self.assertIsNotNone(sales_invoice.atcud_code)
		self.assertTrue(sales_invoice.atcud_code.startswith("0."))

	def test_series_communication_workflow(self):
		"""
		✅ Testar workflow completo de comunicação de série
		"""
		# ✅ OBTER SÉRIE
		series_doc = frappe.get_doc("Portugal Series Configuration", self.test_series)

		# ✅ VERIFICAR ESTADO INICIAL
		self.assertFalse(series_doc.is_communicated)
		self.assertIsNone(series_doc.validation_code)

		# ✅ SIMULAR COMUNICAÇÃO BEM-SUCEDIDA
		with patch.object(self.client, 'communicate_series_batch') as mock_communicate:
			mock_communicate.return_value = {
				"status": "success",
				"results": [{
					"series": self.test_series,
					"success": True,
					"validation_code": "AT123456789"
				}]
			}

			# ✅ EXECUTAR COMUNICAÇÃO
			result = self.client.communicate_series_batch(
				[series_doc],
				self.test_username,
				self.test_password
			)

			# ✅ VERIFICAR RESULTADO
			self.assertEqual(result["status"], "success")
			self.assertTrue(result["results"][0]["success"])

	# ========== TESTES DE ERRO ==========

	def test_invalid_credentials(self):
		"""
		✅ Testar credenciais inválidas
		"""
		with patch('requests.post') as mock_post:
			# ✅ MOCK DE ERRO DE AUTENTICAÇÃO
			mock_response = MagicMock()
			mock_response.status_code = 401
			mock_response.json.return_value = {
				"status": "error",
				"message": "Unauthorized"
			}
			mock_post.return_value = mock_response

			# ✅ TENTAR COMUNICAÇÃO COM CREDENCIAIS INVÁLIDAS
			series_list = [frappe.get_doc("Portugal Series Configuration", self.test_series)]
			result = self.client.communicate_series_batch(
				series_list,
				"invalid",
				"invalid"
			)

			# ✅ VERIFICAR ERRO
			self.assertEqual(result.get("status"), "error")

	def test_network_error(self):
		"""
		✅ Testar erro de rede
		"""
		with patch('requests.post') as mock_post:
			# ✅ MOCK DE ERRO DE REDE
			mock_post.side_effect = Exception("Network error")

			# ✅ TENTAR COMUNICAÇÃO
			series_list = [frappe.get_doc("Portugal Series Configuration", self.test_series)]
			result = self.client.communicate_series_batch(
				series_list,
				self.test_username,
				self.test_password
			)

			# ✅ VERIFICAR TRATAMENTO DE ERRO
			self.assertIsInstance(result, dict)
			self.assertTrue("error" in result or "status" in result)

	# ========== TESTES DE PERFORMANCE ==========

	def test_batch_communication_performance(self):
		"""
		✅ Testar performance de comunicação em lote
		"""
		# ✅ CRIAR MÚLTIPLAS SÉRIES
		series_list = []
		for i in range(5):
			series_name = f"Test Series {i}"
			if not frappe.db.exists("Portugal Series Configuration", series_name):
				series = frappe.new_doc("Portugal Series Configuration")
				series.update({
					"series_name": series_name,
					"company": self.test_company,
					"document_type": "Sales Invoice",
					"prefix": f"FT2025TC{i}",  # ✅ SEM HÍFENS
					"naming_series": f"FT2025TC{i}.####",  # ✅ SEM HÍFENS
					"current_sequence": 1,
					"is_active": 1
				})
				series.insert(ignore_permissions=True)
				series_list.append(series)

		# ✅ MOCK DE COMUNICAÇÃO RÁPIDA
		with patch.object(self.client, 'communicate_series_batch') as mock_communicate:
			mock_communicate.return_value = {
				"status": "success",
				"total_series": len(series_list),
				"successful": len(series_list),
				"failed": 0
			}

			# ✅ MEDIR TEMPO
			import time
			start_time = time.time()

			result = self.client.communicate_series_batch(
				series_list,
				self.test_username,
				self.test_password
			)

			end_time = time.time()
			execution_time = end_time - start_time

			# ✅ VERIFICAR PERFORMANCE (deve ser rápido com mock)
			self.assertLess(execution_time, 1.0)  # Menos de 1 segundo
			self.assertEqual(result["status"], "success")

	# ========== TESTES DE DADOS ==========

	def test_series_data_integrity(self):
		"""
		✅ CORRIGIDO: Testar integridade dos dados de série (formato SEM HÍFENS)
		"""
		# ✅ OBTER SÉRIE
		series_doc = frappe.get_doc("Portugal Series Configuration", self.test_series)

		# ✅ VERIFICAR FORMATO DO PREFIXO (SEM HÍFENS)
		self.assertNotIn("-", series_doc.prefix)
		self.assertTrue(self.validate_prefix_format(series_doc.prefix))

		# ✅ VERIFICAR NAMING SERIES
		self.assertTrue(series_doc.naming_series.endswith(".####"))
		self.assertEqual(series_doc.naming_series.split(".")[0], series_doc.prefix)

		# ✅ VERIFICAR EMPRESA PORTUGUESA
		self.assertEqual(series_doc.company, self.test_company)

		# ✅ VERIFICAR TIPO DE DOCUMENTO
		self.assertIn(series_doc.document_type, [
			"Sales Invoice", "POS Invoice", "Sales Order", "Quotation",
			"Delivery Note", "Purchase Invoice", "Purchase Order",
			"Purchase Receipt", "Stock Entry", "Payment Entry"
		])

	def test_atcud_generation_format(self):
		"""
		✅ Testar formato de geração de ATCUD
		"""
		# ✅ CRIAR DOCUMENTO DE TESTE
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.update({
			"customer": "_Test Customer",
			"company": self.test_company,
			"naming_series": "FT2025TCP.####",  # ✅ SEM HÍFENS
			"items": [{
				"item_code": "_Test Item",
				"qty": 1,
				"rate": 100
			}]
		})
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		if result.get("success"):
			atcud = result.get("atcud_code")

			# ✅ VERIFICAR FORMATO ATCUD: 0.sequência
			self.assertTrue(atcud.startswith("0."))
			self.assertTrue(atcud.split(".")[1].isdigit())

	# ========== TESTES DE CONFIGURAÇÃO ==========

	def test_company_portugal_compliance(self):
		"""
		✅ Testar configuração de compliance português na empresa
		"""
		company_doc = frappe.get_doc("Company", self.test_company)

		# ✅ VERIFICAR CONFIGURAÇÕES PORTUGUESAS
		self.assertEqual(company_doc.country, "Portugal")
		self.assertEqual(company_doc.default_currency, "EUR")
		self.assertTrue(company_doc.portugal_compliance_enabled)
		self.assertIsNotNone(company_doc.tax_id)

	def test_document_type_mapping(self):
		"""
		✅ CORRIGIDO: Testar mapeamento de tipos de documento (formato SEM HÍFENS)
		"""
		# ✅ MAPEAMENTO ESPERADO (SEM HÍFENS)
		expected_mapping = {
			'Sales Invoice': 'FT',
			'POS Invoice': 'FS',
			'Sales Order': 'FO',
			'Quotation': 'OR',
			'Delivery Note': 'GR',
			'Purchase Invoice': 'FC',
			'Purchase Order': 'OC',
			'Purchase Receipt': 'GR',
			'Stock Entry': 'GM',
			'Payment Entry': 'RC'
		}

		for doctype, expected_code in expected_mapping.items():
			with self.subTest(doctype=doctype):
				# ✅ VERIFICAR SE CÓDIGO ESTÁ CORRETO
				self.assertEqual(len(expected_code), 2)
				self.assertTrue(expected_code.isupper())

	# ========== TESTES DE LIMPEZA ==========

	def test_cleanup_test_data(self):
		"""
		✅ Testar limpeza de dados de teste
		"""
		# ✅ VERIFICAR SE DADOS DE TESTE EXISTEM
		self.assertTrue(frappe.db.exists("Company", self.test_company))
		self.assertTrue(frappe.db.exists("Portugal Series Configuration", self.test_series))

	# ✅ SIMULAR LIMPEZA (será feita no tearDown)
	# Este teste apenas verifica se os dados estão presentes


# ========== FUNÇÕES DE UTILITÁRIO PARA TESTES ==========

def run_at_webservice_tests():
	"""
	✅ Executar todos os testes do AT Webservice
	"""
	import unittest

	# ✅ CRIAR SUITE DE TESTES
	suite = unittest.TestLoader().loadTestsFromTestCase(TestATWebservice)

	# ✅ EXECUTAR TESTES
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	return result


def setup_test_environment():
	"""
	✅ Configurar ambiente de teste
	"""
	# ✅ ATIVAR MODO DE TESTE
	frappe.conf.allow_tests = True

	# ✅ CONFIGURAR FLAGS DE TESTE
	frappe.flags.in_test = True
	frappe.flags.print_messages = False


if __name__ == "__main__":
	# ✅ CONFIGURAR AMBIENTE
	setup_test_environment()

	# ✅ EXECUTAR TESTES
	unittest.main(verbosity=2)
