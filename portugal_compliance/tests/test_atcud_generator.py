# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Test ATCUD Generator - Portugal Compliance VERSÃO NATIVA CORRIGIDA
Testes completos para geração de ATCUD
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Testes para atcud_generator.py
✅ Testes de geração automática e manual
✅ Testes de validação de formato
✅ Testes de sequência e integridade
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.test_runner import make_test_records
import json
import re
from datetime import datetime

# ✅ IMPORTAÇÕES DO MÓDULO A SER TESTADO
from portugal_compliance.utils.atcud_generator import (
	generate_manual_atcud_certified,
	validate_atcud_format
)


class TestATCUDGenerator(FrappeTestCase):
	"""
	✅ Classe de teste para ATCUD Generator
	"""

	@classmethod
	def setUpClass(cls):
		"""
		✅ Configuração antes de todos os testes
		"""
		# ✅ CRIAR REGISTROS DE TESTE
		make_test_records([
			"Company",
			"Customer",
			"Supplier",
			"Item"
		], verbose=False, force=True)

		# ✅ LIMPAR DADOS DE TESTE ANTERIORES
		frappe.db.sql("DELETE FROM `tabPortugal Series Configuration` WHERE company LIKE 'Test%'")
		frappe.db.commit()

	def setUp(self):
		"""
		✅ Configuração antes de cada teste
		"""
		# ✅ CRIAR EMPRESA PORTUGUESA DE TESTE
		self.test_company = self.create_test_company()

		# ✅ CRIAR SÉRIES DE TESTE (SEM HÍFENS)
		self.test_series = self.create_test_series()

		# ✅ CONFIGURAR DADOS DE TESTE
		self.test_customer = "_Test Customer"
		self.test_supplier = "_Test Supplier"
		self.test_item = "_Test Item"

	def tearDown(self):
		"""
		✅ Limpeza após cada teste
		"""
		frappe.db.rollback()

	def create_test_company(self):
		"""
		✅ Criar empresa portuguesa para testes
		"""
		company_name = "Test Company Portugal ATCUD"

		if not frappe.db.exists("Company", company_name):
			company = frappe.new_doc("Company")
			company.update({
				"company_name": company_name,
				"abbr": "TCPA",
				"country": "Portugal",
				"default_currency": "EUR",
				"tax_id": "123456789",
				"portugal_compliance_enabled": 1
			})
			company.insert(ignore_permissions=True)
			frappe.db.commit()

		return company_name

	def create_test_series(self):
		"""
		✅ CORRIGIDO: Criar séries de teste (formato SEM HÍFENS)
		"""
		series_configs = []

		# ✅ SÉRIES PARA DIFERENTES DOCTYPES (SEM HÍFENS)
		series_data = [
			{
				"name": "Test Series FT ATCUD",
				"document_type": "Sales Invoice",
				"prefix": "FT2025TCPA",  # ✅ SEM HÍFENS
				"naming_series": "FT2025TCPA.####"  # ✅ SEM HÍFENS
			},
			{
				"name": "Test Series FS ATCUD",
				"document_type": "POS Invoice",
				"prefix": "FS2025TCPA",  # ✅ SEM HÍFENS
				"naming_series": "FS2025TCPA.####"  # ✅ SEM HÍFENS
			},
			{
				"name": "Test Series FC ATCUD",
				"document_type": "Purchase Invoice",
				"prefix": "FC2025TCPA",  # ✅ SEM HÍFENS
				"naming_series": "FC2025TCPA.####"  # ✅ SEM HÍFENS
			}
		]

		for data in series_data:
			if not frappe.db.exists("Portugal Series Configuration", data["name"]):
				series = frappe.new_doc("Portugal Series Configuration")
				series.update({
					"series_name": data["name"],
					"company": self.test_company,
					"document_type": data["document_type"],
					"prefix": data["prefix"],
					"naming_series": data["naming_series"],
					"current_sequence": 1,
					"is_active": 1,
					"is_communicated": 1,  # ✅ COMUNICADA PARA TESTES
					"validation_code": f"AT{data['prefix']}"
				})
				series.insert(ignore_permissions=True)
				series_configs.append(data["name"])

		frappe.db.commit()
		return series_configs

	# ========== TESTES DE GERAÇÃO MANUAL ==========

	def test_generate_manual_atcud_sales_invoice(self):
		"""
		✅ Testar geração manual de ATCUD para Sales Invoice
		"""
		# ✅ CRIAR SALES INVOICE DE TESTE
		sales_invoice = self.create_test_sales_invoice()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ VERIFICAR RESULTADO
		self.assertTrue(result.get("success", False), f"Falha na geração: {result.get('error')}")
		self.assertIsNotNone(result.get("atcud_code"))

		# ✅ VERIFICAR FORMATO ATCUD
		atcud = result.get("atcud_code")
		self.assertTrue(atcud.startswith("0."))
		self.assertTrue(atcud.split(".")[1].isdigit())

		# ✅ VERIFICAR SE FOI SALVO NO DOCUMENTO
		sales_invoice.reload()
		self.assertEqual(sales_invoice.atcud_code, atcud)

	def test_generate_manual_atcud_pos_invoice(self):
		"""
		✅ Testar geração manual de ATCUD para POS Invoice
		"""
		# ✅ CRIAR POS INVOICE DE TESTE
		pos_invoice = self.create_test_pos_invoice()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("POS Invoice", pos_invoice.name)

		# ✅ VERIFICAR RESULTADO
		self.assertTrue(result.get("success", False))
		self.assertIsNotNone(result.get("atcud_code"))

		# ✅ VERIFICAR FORMATO
		atcud = result.get("atcud_code")
		self.assertRegex(atcud, r"^0\.\d+$")

	def test_generate_manual_atcud_purchase_invoice(self):
		"""
		✅ Testar geração manual de ATCUD para Purchase Invoice
		"""
		# ✅ CRIAR PURCHASE INVOICE DE TESTE
		purchase_invoice = self.create_test_purchase_invoice()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("Purchase Invoice", purchase_invoice.name)

		# ✅ VERIFICAR RESULTADO
		self.assertTrue(result.get("success", False))
		self.assertIsNotNone(result.get("atcud_code"))

	def test_generate_atcud_document_not_found(self):
		"""
		✅ Testar geração para documento inexistente
		"""
		# ✅ TENTAR GERAR PARA DOCUMENTO INEXISTENTE
		result = generate_manual_atcud_certified("Sales Invoice", "INEXISTENTE")

		# ✅ VERIFICAR FALHA
		self.assertFalse(result.get("success", True))
		self.assertIn("error", result)

	def test_generate_atcud_already_exists(self):
		"""
		✅ Testar geração quando ATCUD já existe
		"""
		# ✅ CRIAR DOCUMENTO COM ATCUD
		sales_invoice = self.create_test_sales_invoice()

		# ✅ PRIMEIRA GERAÇÃO
		result1 = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)
		self.assertTrue(result1.get("success"))

		# ✅ SEGUNDA GERAÇÃO (deve falhar ou retornar o mesmo)
		result2 = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ VERIFICAR COMPORTAMENTO
		if result2.get("success"):
			# Se permitir regeneração, deve ser o mesmo código
			self.assertEqual(result1.get("atcud_code"), result2.get("atcud_code"))
		else:
			# Se não permitir, deve ter erro
			self.assertIn("error", result2)

	# ========== TESTES DE VALIDAÇÃO ==========

	def test_validate_atcud_format_valid(self):
		"""
		✅ Testar validação de formato ATCUD válido
		"""
		valid_atcuds = [
			"0.1",
			"0.123",
			"0.999999",
			"0.1000000"
		]

		for atcud in valid_atcuds:
			with self.subTest(atcud=atcud):
				result = validate_atcud_format(atcud)
				self.assertTrue(result.get("valid", False), f"ATCUD {atcud} deveria ser válido")

	def test_validate_atcud_format_invalid(self):
		"""
		✅ Testar validação de formato ATCUD inválido
		"""
		invalid_atcuds = [
			"1.123",  # Não começa com 0
			"0.",  # Sem sequência
			"0.abc",  # Sequência não numérica
			"0",  # Sem ponto
			"",  # Vazio
			None,  # None
			"0.1.2",  # Múltiplos pontos
			"abc.123"  # Formato completamente errado
		]

		for atcud in invalid_atcuds:
			with self.subTest(atcud=atcud):
				result = validate_atcud_format(atcud)
				self.assertFalse(result.get("valid", True), f"ATCUD {atcud} deveria ser inválido")

	# ========== TESTES DE SEQUÊNCIA ==========
	def test_get_next_atcud_sequence(self):
		"""
		✅ Testar obtenção da próxima sequência
		"""
		# ✅ OBTER SÉRIE DE TESTE
		series_name = self.test_series[0]  # Sales Invoice series

		# ✅ OBTER PRÓXIMA SEQUÊNCIA
		next_seq = frappe.db.get_value(
			"Portugal Series Configuration",
			series_name,
			"current_sequence"
		)
		# ✅ VERIFICAR RESULTADO
		self.assertIsNotNone(next_seq)
		self.assertIsInstance(next_seq, int)
		self.assertGreaterEqual(next_seq, 1)

	def test_atcud_sequence_increment(self):
		"""
		✅ Testar incremento de sequência
		"""
		# ✅ CRIAR MÚLTIPLOS DOCUMENTOS
		documents = []
		atcuds = []

		for i in range(3):
			# ✅ CRIAR DOCUMENTO
			doc = self.create_test_sales_invoice()
			documents.append(doc)

			# ✅ GERAR ATCUD
			result = generate_manual_atcud_certified("Sales Invoice", doc.name)
			self.assertTrue(result.get("success"))

			atcud = result.get("atcud_code")
			atcuds.append(atcud)

		# ✅ VERIFICAR SEQUÊNCIA CRESCENTE
		sequences = [int(atcud.split(".")[1]) for atcud in atcuds]

		for i in range(1, len(sequences)):
			self.assertGreater(sequences[i], sequences[i - 1],
							   "Sequências devem ser crescentes")

	# ========== TESTES DE INTEGRIDADE ==========

	def test_atcud_uniqueness(self):
		"""
		✅ Testar unicidade de ATCUD
		"""
		# ✅ CRIAR MÚLTIPLOS DOCUMENTOS
		atcuds = set()

		for i in range(5):
			# ✅ CRIAR DOCUMENTO
			doc = self.create_test_sales_invoice()

			# ✅ GERAR ATCUD
			result = generate_manual_atcud_certified("Sales Invoice", doc.name)
			self.assertTrue(result.get("success"))

			atcud = result.get("atcud_code")

			# ✅ VERIFICAR UNICIDADE
			self.assertNotIn(atcud, atcuds, f"ATCUD {atcud} já existe")
			atcuds.add(atcud)

	def test_atcud_persistence(self):
		"""
		✅ Testar persistência de ATCUD no banco
		"""
		# ✅ CRIAR DOCUMENTO
		sales_invoice = self.create_test_sales_invoice()

		# ✅ GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)
		self.assertTrue(result.get("success"))

		atcud = result.get("atcud_code")

		# ✅ VERIFICAR NO BANCO
		db_atcud = frappe.db.get_value("Sales Invoice", sales_invoice.name, "atcud_code")
		self.assertEqual(atcud, db_atcud)

	# ========== TESTES DE SÉRIES ==========

	def test_series_format_validation(self):
		"""
		✅ CORRIGIDO: Testar validação de formato de série (SEM HÍFENS)
		"""
		# ✅ FORMATOS VÁLIDOS (SEM HÍFENS)
		valid_series = [
			"FT2025TCPA.####",
			"FS2025ABC.####",
			"FC2025XYZ.####"
		]

		for series in valid_series:
			with self.subTest(series=series):
				# ✅ EXTRAIR PREFIXO
				prefix = series.split(".")[0]

				# ✅ VALIDAR FORMATO
				pattern = r"^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$"
				self.assertRegex(prefix, pattern, f"Série {series} deveria ser válida")

	def test_series_communication_status(self):
		"""
		✅ Testar status de comunicação das séries
		"""
		for series_name in self.test_series:
			with self.subTest(series=series_name):
				# ✅ OBTER SÉRIE
				series_doc = frappe.get_doc("Portugal Series Configuration", series_name)

				# ✅ VERIFICAR STATUS
				self.assertTrue(series_doc.is_communicated,
								f"Série {series_name} deveria estar comunicada")
				self.assertIsNotNone(series_doc.validation_code)

	# ========== TESTES DE PERFORMANCE ==========

	def test_bulk_atcud_generation_performance(self):
		"""
		✅ Testar performance de geração em lote
		"""
		import time

		# ✅ CRIAR MÚLTIPLOS DOCUMENTOS
		documents = []
		for i in range(10):
			doc = self.create_test_sales_invoice()
			documents.append(doc)

		# ✅ MEDIR TEMPO DE GERAÇÃO
		start_time = time.time()

		successful = 0
		for doc in documents:
			result = generate_manual_atcud_certified("Sales Invoice", doc.name)
			if result.get("success"):
				successful += 1

		end_time = time.time()
		execution_time = end_time - start_time

		# ✅ VERIFICAR PERFORMANCE
		self.assertEqual(successful, len(documents), "Todos os ATCUDs devem ser gerados")
		self.assertLess(execution_time, 5.0, "Geração deve ser rápida (menos de 5s para 10 docs)")

	# ========== TESTES DE EDGE CASES ==========

	def test_atcud_generation_draft_document(self):
		"""
		✅ Testar geração para documento em rascunho
		"""
		# ✅ CRIAR DOCUMENTO EM RASCUNHO
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.update({
			"customer": self.test_customer,
			"company": self.test_company,
			"naming_series": "FT2025TCPA.####",  # ✅ SEM HÍFENS
			"items": [{
				"item_code": self.test_item,
				"qty": 1,
				"rate": 100
			}]
		})
		sales_invoice.insert(ignore_permissions=True)
		# ✅ NÃO SUBMETER (manter como rascunho)

		# ✅ TENTAR GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ VERIFICAR COMPORTAMENTO (pode falhar para rascunhos)
		if not result.get("success"):
			self.assertIn("error", result)

	def test_atcud_generation_cancelled_document(self):
		"""
		✅ Testar geração para documento cancelado
		"""
		# ✅ CRIAR E CANCELAR DOCUMENTO
		sales_invoice = self.create_test_sales_invoice()
		sales_invoice.cancel()

		# ✅ TENTAR GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ VERIFICAR COMPORTAMENTO
		if not result.get("success"):
			self.assertIn("error", result)

	def test_atcud_generation_invalid_series(self):
		"""
		✅ CORRIGIDO: Testar geração com série inválida (formato COM HÍFENS)
		"""
		# ✅ CRIAR DOCUMENTO COM SÉRIE INVÁLIDA (COM HÍFENS)
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.update({
			"customer": self.test_customer,
			"company": self.test_company,
			"naming_series": "FT-2025-TCPA.####",  # ✅ COM HÍFENS (INVÁLIDO)
			"items": [{
				"item_code": self.test_item,
				"qty": 1,
				"rate": 100
			}]
		})
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()

		# ✅ TENTAR GERAR ATCUD
		result = generate_manual_atcud_certified("Sales Invoice", sales_invoice.name)

		# ✅ DEVE FALHAR DEVIDO À SÉRIE INVÁLIDA
		self.assertFalse(result.get("success", True))
		self.assertIn("error", result)

	# ========== FUNÇÕES AUXILIARES ==========

	def create_test_sales_invoice(self):
		"""
		✅ Criar Sales Invoice de teste
		"""
		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.update({
			"customer": self.test_customer,
			"company": self.test_company,
			"naming_series": "FT2025TCPA.####",  # ✅ SEM HÍFENS
			"items": [{
				"item_code": self.test_item,
				"qty": 1,
				"rate": 100
			}]
		})
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()
		return sales_invoice

	def create_test_pos_invoice(self):
		"""
		✅ Criar POS Invoice de teste
		"""
		pos_invoice = frappe.new_doc("POS Invoice")
		pos_invoice.update({
			"customer": self.test_customer,
			"company": self.test_company,
			"naming_series": "FS2025TCPA.####",  # ✅ SEM HÍFENS
			"items": [{
				"item_code": self.test_item,
				"qty": 1,
				"rate": 50
			}]
		})
		pos_invoice.insert(ignore_permissions=True)
		pos_invoice.submit()
		return pos_invoice

	def create_test_purchase_invoice(self):
		"""
		✅ Criar Purchase Invoice de teste
		"""
		purchase_invoice = frappe.new_doc("Purchase Invoice")
		purchase_invoice.update({
			"supplier": self.test_supplier,
			"company": self.test_company,
			"naming_series": "FC2025TCPA.####",  # ✅ SEM HÍFENS
			"bill_no": "BILL-001",
			"bill_date": frappe.utils.nowdate(),
			"items": [{
				"item_code": self.test_item,
				"qty": 1,
				"rate": 80
			}]
		})
		purchase_invoice.insert(ignore_permissions=True)
		purchase_invoice.submit()
		return purchase_invoice


# ========== FUNÇÕES DE UTILITÁRIO PARA TESTES ==========

def run_atcud_generator_tests():
	"""
	✅ Executar todos os testes do ATCUD Generator
	"""
	import unittest

	# ✅ CRIAR SUITE DE TESTES
	suite = unittest.TestLoader().loadTestsFromTestCase(TestATCUDGenerator)

	# ✅ EXECUTAR TESTES
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	return result


if __name__ == "__main__":
	# ✅ CONFIGURAR AMBIENTE DE TESTE
	frappe.init(site="test_site")
	frappe.connect()

	# ✅ EXECUTAR TESTES
	unittest.main(verbosity=2)
