import unittest
import frappe
from unittest.mock import patch, MagicMock, mock_open
import xml.etree.ElementTree as ET
from datetime import datetime, date
from portugal_compliance.utils.saft_generator import SAFTGenerator
from portugal_compliance.exceptions import SAFTGenerationError


class TestSAFTGenerator(unittest.TestCase):
	"""
	Testes para o gerador de ficheiros SAF-T (PT)
	"""

	def setUp(self):
		"""Configuração inicial para cada teste"""
		self.generator = SAFTGenerator()
		self.test_company = "Test Company"
		self.test_start_date = date(2025, 1, 1)
		self.test_end_date = date(2025, 12, 31)
		self.test_fiscal_year = "2025"

		# Dados de teste para empresa
		self.test_company_data = {
			"company_name": "Test Company Lda",
			"tax_id": "999999999",
			"default_currency": "EUR"
		}

		# Dados de teste para endereço
		self.test_address_data = {
			"address_line1": "Rua de Teste 123",
			"address_line2": "1º Andar",
			"city": "Lisboa",
			"pincode": "1000-001",
			"country": "Portugal",
			"country_code": "PT"
		}

	def tearDown(self):
		"""Limpeza após cada teste"""
		pass

	def test_generate_saft_valid_parameters(self):
		"""Testa geração de SAF-T com parâmetros válidos"""
		with patch.object(self.generator, '_collect_data') as mock_collect, \
			patch.object(self.generator, '_generate_xml') as mock_generate:
			mock_collect.return_value = {"test": "data"}
			mock_generate.return_value = "<xml>test</xml>"

			# Executar teste
			result = self.generator.generate_saft(
				company=self.test_company,
				start_date=self.test_start_date,
				end_date=self.test_end_date
			)

			# Verificações
			self.assertIsInstance(result, str)
			self.assertIn("<xml>", result)
			mock_collect.assert_called_once()
			mock_generate.assert_called_once()

	def test_generate_saft_invalid_company(self):
		"""Testa geração de SAF-T com empresa inválida"""
		# Executar teste e verificar exceção
		with self.assertRaises(SAFTGenerationError):
			self.generator.generate_saft(
				company="",  # Empresa vazia
				start_date=self.test_start_date,
				end_date=self.test_end_date
			)

	def test_generate_saft_invalid_date_range(self):
		"""Testa geração de SAF-T com intervalo de datas inválido"""
		# Data de fim anterior à data de início
		invalid_end_date = date(2024, 12, 31)

		# Executar teste e verificar exceção
		with self.assertRaises(SAFTGenerationError):
			self.generator.generate_saft(
				company=self.test_company,
				start_date=self.test_start_date,
				end_date=invalid_end_date
			)

	@patch('frappe.db.get_value')
	def test_validate_company_data_valid(self, mock_get_value):
		"""Testa validação de dados da empresa válidos"""
		# Mock dos dados da empresa
		mock_get_value.side_effect = [
			self.test_company_data["company_name"],
			self.test_company_data["tax_id"],
			self.test_company_data["default_currency"]
		]

		# Executar teste
		result = self.generator._validate_company_data(self.test_company)

		# Verificações
		self.assertTrue(result)
		self.assertEqual(mock_get_value.call_count, 3)

	@patch('frappe.db.get_value')
	def test_validate_company_data_missing_tax_id(self, mock_get_value):
		"""Testa validação de empresa sem NIF"""
		# Mock retornando None para tax_id
		mock_get_value.side_effect = [
			self.test_company_data["company_name"],
			None,  # NIF em falta
			self.test_company_data["default_currency"]
		]

		# Executar teste e verificar exceção
		with self.assertRaises(SAFTGenerationError):
			self.generator._validate_company_data(self.test_company)

	@patch('frappe.get_all')
	def test_collect_chart_of_accounts(self, mock_get_all):
		"""Testa recolha do plano de contas"""
		# Mock dos dados das contas
		mock_accounts = [
			{
				"name": "1000",
				"account_name": "Caixa",
				"account_type": "Asset",
				"parent_account": "10",
				"creation": datetime(2025, 1, 1)
			},
			{
				"name": "2000",
				"account_name": "Fornecedores",
				"account_type": "Liability",
				"parent_account": "20",
				"creation": datetime(2025, 1, 1)
			}
		]
		mock_get_all.return_value = mock_accounts

		# Executar teste
		result = self.generator._collect_chart_of_accounts(self.test_company)

		# Verificações
		self.assertEqual(len(result), 2)
		self.assertEqual(result[0]["account_name"], "Caixa")
		self.assertEqual(result[1]["account_name"], "Fornecedores")
		mock_get_all.assert_called_once()

	@patch('frappe.get_all')
	def test_collect_customers(self, mock_get_all):
		"""Testa recolha de dados de clientes"""
		# Mock dos dados dos clientes
		mock_customers = [
			{
				"name": "CUST-001",
				"customer_name": "Cliente Teste Lda",
				"tax_id": "123456789",
				"creation": datetime(2025, 1, 1)
			}
		]
		mock_get_all.return_value = mock_customers

		# Executar teste
		result = self.generator._collect_customers(self.test_company)

		# Verificações
		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["customer_name"], "Cliente Teste Lda")
		mock_get_all.assert_called_once()

	@patch('frappe.get_all')
	def test_collect_suppliers(self, mock_get_all):
		"""Testa recolha de dados de fornecedores"""
		# Mock dos dados dos fornecedores
		mock_suppliers = [
			{
				"name": "SUPP-001",
				"supplier_name": "Fornecedor Teste Lda",
				"tax_id": "987654321",
				"creation": datetime(2025, 1, 1)
			}
		]
		mock_get_all.return_value = mock_suppliers

		# Executar teste
		result = self.generator._collect_suppliers(self.test_company)

		# Verificações
		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["supplier_name"], "Fornecedor Teste Lda")
		mock_get_all.assert_called_once()

	@patch('frappe.get_all')
	def test_collect_sales_invoices(self, mock_get_all):
		"""Testa recolha de faturas de venda"""
		# Mock das faturas de venda
		mock_invoices = [
			{
				"name": "SINV-2025-001",
				"customer": "CUST-001",
				"posting_date": date(2025, 6, 15),
				"grand_total": 1000.00,
				"atcud_code": "ATCUD123-4",
				"docstatus": 1
			}
		]
		mock_get_all.return_value = mock_invoices

		# Executar teste
		result = self.generator._collect_sales_invoices(
			self.test_company,
			self.test_start_date,
			self.test_end_date
		)

		# Verificações
		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["name"], "SINV-2025-001")
		mock_get_all.assert_called_once()

	@patch('frappe.get_all')
	def test_collect_purchase_invoices(self, mock_get_all):
		"""Testa recolha de faturas de compra"""
		# Mock das faturas de compra
		mock_invoices = [
			{
				"name": "PINV-2025-001",
				"supplier": "SUPP-001",
				"posting_date": date(2025, 6, 15),
				"grand_total": 500.00,
				"atcud_code": "ATCUD567-8",
				"docstatus": 1
			}
		]
		mock_get_all.return_value = mock_invoices

		# Executar teste
		result = self.generator._collect_purchase_invoices(
			self.test_company,
			self.test_start_date,
			self.test_end_date
		)

		# Verificações
		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["name"], "PINV-2025-001")
		mock_get_all.assert_called_once()

	@patch('frappe.get_all')
	def test_collect_payments(self, mock_get_all):
		"""Testa recolha de pagamentos"""
		# Mock dos pagamentos
		mock_payments = [
			{
				"name": "PAY-2025-001",
				"party": "CUST-001",
				"party_type": "Customer",
				"posting_date": date(2025, 6, 20),
				"paid_amount": 1000.00,
				"atcud_code": "ATCUD789-0",
				"docstatus": 1
			}
		]
		mock_get_all.return_value = mock_payments

		# Executar teste
		result = self.generator._collect_payments(
			self.test_company,
			self.test_start_date,
			self.test_end_date
		)

		# Verificações
		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["name"], "PAY-2025-001")
		mock_get_all.assert_called_once()

	def test_generate_xml_structure(self):
		"""Testa estrutura do XML gerado"""
		# Dados de teste mínimos
		test_data = {
			"company": self.test_company_data,
			"company_address": self.test_address_data,
			"chart_of_accounts": [],
			"customers": [],
			"suppliers": [],
			"items": [],
			"sales_invoices": [],
			"purchase_invoices": [],
			"payments": [],
			"stock_entries": []
		}

		# Executar teste
		xml_content = self.generator._generate_xml(test_data)

		# Verificações de estrutura XML
		self.assertIsInstance(xml_content, str)
		self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', xml_content)
		self.assertIn('<AuditFile', xml_content)
		self.assertIn('<Header>', xml_content)
		self.assertIn('<MasterFiles>', xml_content)
		self.assertIn('<SourceDocuments>', xml_content)

	def test_validate_xml_structure(self):
		"""Testa validação da estrutura XML"""
		# XML válido de teste
		valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <AuditFile xmlns="urn:OECD:StandardAuditFile-Tax:PT_1.04_01">
            <Header>
                <AuditFileVersion>1.04_01</AuditFileVersion>
                <CompanyID>999999999</CompanyID>
            </Header>
        </AuditFile>'''

		# Executar teste
		result = self.generator._validate_xml_structure(valid_xml)

		# Verificações
		self.assertTrue(result)

	def test_validate_xml_structure_invalid(self):
		"""Testa validação de XML inválido"""
		# XML inválido (malformado)
		invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <AuditFile>
            <Header>
                <AuditFileVersion>1.04_01</AuditFileVersion>
            <!-- Tag não fechada
        </AuditFile>'''

		# Executar teste
		result = self.generator._validate_xml_structure(invalid_xml)

		# Verificações
		self.assertFalse(result)

	def test_calculate_totals(self):
		"""Testa cálculo de totais"""
		# Dados de teste
		test_invoices = [
			{"grand_total": 1000.00, "total_taxes_and_charges": 230.00},
			{"grand_total": 500.00, "total_taxes_and_charges": 115.00},
			{"grand_total": 750.00, "total_taxes_and_charges": 172.50}
		]

		# Executar teste
		totals = self.generator._calculate_totals(test_invoices)

		# Verificações
		self.assertEqual(totals["total_debit"], 2250.00)
		self.assertEqual(totals["total_credit"], 0.00)
		self.assertEqual(totals["total_tax"], 517.50)

	def test_format_date_for_saft(self):
		"""Testa formatação de data para SAF-T"""
		test_date = date(2025, 6, 15)

		# Executar teste
		formatted_date = self.generator._format_date_for_saft(test_date)

		# Verificações
		self.assertEqual(formatted_date, "2025-06-15")

	def test_format_datetime_for_saft(self):
		"""Testa formatação de datetime para SAF-T"""
		test_datetime = datetime(2025, 6, 15, 14, 30, 45)

		# Executar teste
		formatted_datetime = self.generator._format_datetime_for_saft(test_datetime)

		# Verificações
		self.assertEqual(formatted_datetime, "2025-06-15T14:30:45")

	def test_escape_xml_content(self):
		"""Testa escape de conteúdo XML"""
		test_content = "Empresa & Filhos Lda < > \" '"

		# Executar teste
		escaped_content = self.generator._escape_xml_content(test_content)

		# Verificações
		self.assertIn("&amp;", escaped_content)
		self.assertIn("&lt;", escaped_content)
		self.assertIn("&gt;", escaped_content)
		self.assertIn("&quot;", escaped_content)
		self.assertIn("&#x27;", escaped_content)

	@patch('builtins.open', new_callable=mock_open)
	def test_save_saft_file(self, mock_file):
		"""Testa gravação de ficheiro SAF-T"""
		test_xml = "<xml>test content</xml>"
		test_filename = "saft_test.xml"

		# Executar teste
		result = self.generator.save_saft_file(test_xml, test_filename)

		# Verificações
		self.assertTrue(result)
		mock_file.assert_called_once_with(test_filename, 'w', encoding='utf-8')
		mock_file().write.assert_called_once_with(test_xml)

	def test_get_saft_filename(self):
		"""Testa geração de nome de ficheiro SAF-T"""
		# Executar teste
		filename = self.generator.get_saft_filename(
			self.test_company,
			self.test_start_date,
			self.test_end_date
		)

		# Verificações
		self.assertIsInstance(filename, str)
		self.assertIn("SAF-T", filename)
		self.assertIn("2025", filename)
		self.assertIn(".xml", filename)

	def test_performance_large_dataset(self):
		"""Testa performance com dataset grande"""
		import time

		# Simular dataset grande
		large_dataset = {
			"company": self.test_company_data,
			"company_address": self.test_address_data,
			"chart_of_accounts": [{"name": f"ACC-{i}"} for i in range(1000)],
			"customers": [{"name": f"CUST-{i}"} for i in range(500)],
			"suppliers": [{"name": f"SUPP-{i}"} for i in range(200)],
			"items": [{"name": f"ITEM-{i}"} for i in range(1000)],
			"sales_invoices": [{"name": f"SINV-{i}"} for i in range(2000)],
			"purchase_invoices": [{"name": f"PINV-{i}"} for i in range(500)],
			"payments": [{"name": f"PAY-{i}"} for i in range(1000)],
			"stock_entries": [{"name": f"STE-{i}"} for i in range(300)]
		}

		start_time = time.time()

		# Executar teste
		xml_content = self.generator._generate_xml(large_dataset)

		end_time = time.time()
		execution_time = end_time - start_time

		# Verificações
		self.assertIsInstance(xml_content, str)
		self.assertLess(execution_time, 30.0)  # Deve executar em menos de 30 segundos

	def test_memory_usage_optimization(self):
		"""Testa otimização de uso de memória"""
		import sys

		# Medir uso de memória inicial
		initial_size = sys.getsizeof(self.generator)

		# Simular processamento de dados grandes
		large_data = {"test": "x" * 1000000}  # 1MB de dados
		self.generator._process_large_data(large_data)

		# Medir uso de memória após processamento
		final_size = sys.getsizeof(self.generator)

		# Verificar que não há vazamentos significativos de memória
		memory_increase = final_size - initial_size
		self.assertLess(memory_increase, 100000)  # Menos de 100KB de aumento


if __name__ == '__main__':
	unittest.main(verbosity=2)
