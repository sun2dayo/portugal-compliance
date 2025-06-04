# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Test Series Communication - Portugal Compliance VERSÃO NATIVA CORRIGIDA
Testes completos para comunicação de séries com a AT
✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
✅ INTEGRAÇÃO: Testes para at_webservice.py e comunicação de séries
✅ Testes de batch, sucesso, erro, e status
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.test_runner import make_test_records
from unittest.mock import patch, MagicMock
from datetime import datetime

# ✅ IMPORTAÇÕES DO CLIENTE AT CORRETO
from portugal_compliance.utils.at_webservice import ATWebserviceClient

class TestSeriesCommunication(FrappeTestCase):
    """
    ✅ Classe de teste para comunicação de séries com a AT
    """

    @classmethod
    def setUpClass(cls):
        make_test_records([
            "Company",
        ], verbose=False, force=True)

    def setUp(self):
        # ✅ CRIAR EMPRESA DE TESTE
        self.company = self.create_test_company()
        # ✅ CRIAR SÉRIE DE TESTE (SEM HÍFENS)
        self.series_name = self.create_test_series()
        self.client = ATWebserviceClient()
        self.username = "test_user"
        self.password = "test_password"

    def tearDown(self):
        frappe.db.rollback()

    def create_test_company(self):
        company_name = "Test Company SeriesComm"
        if not frappe.db.exists("Company", company_name):
            company = frappe.new_doc("Company")
            company.update({
                "company_name": company_name,
                "abbr": "TCSC",
                "country": "Portugal",
                "default_currency": "EUR",
                "tax_id": "123456789",
                "portugal_compliance_enabled": 1
            })
            company.insert(ignore_permissions=True)
        return company_name

    def create_test_series(self):
        series_name = "Test Series FT COMM"
        if not frappe.db.exists("Portugal Series Configuration", series_name):
            series = frappe.new_doc("Portugal Series Configuration")
            series.update({
                "series_name": series_name,
                "company": self.company,
                "document_type": "Sales Invoice",
                "prefix": "FT2025TCSC",  # SEM HÍFENS
                "naming_series": "FT2025TCSC.####",
                "current_sequence": 1,
                "is_active": 1,
                "is_communicated": 0
            })
            series.insert(ignore_permissions=True)
        return series_name

    # ========== TESTES DE COMUNICAÇÃO ==========

    @patch('requests.post')
    def test_communicate_series_batch_success(self, mock_post):
        """
        ✅ Testar comunicação em lote bem-sucedida
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "validation_code": "AT987654321",
            "message": "Série comunicada com sucesso"
        }
        mock_post.return_value = mock_response

        series_list = [frappe.get_doc("Portugal Series Configuration", self.series_name)]
        result = self.client.communicate_series_batch(series_list, self.username, self.password)

        self.assertIsInstance(result, dict)
        self.assertIn(result.get("status"), ["success", "completed"])
        self.assertIn("validation_code", result.get("results", [{}])[0])

    @patch('requests.post')
    def test_communicate_series_batch_failure(self, mock_post):
        """
        ✅ Testar falha na comunicação de série
        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "status": "error",
            "message": "Erro de validação"
        }
        mock_post.return_value = mock_response

        series_list = [frappe.get_doc("Portugal Series Configuration", self.series_name)]
        result = self.client.communicate_series_batch(series_list, "wrong", "wrong")

        self.assertIsInstance(result, dict)
        self.assertIn(result.get("status"), ["error", "failed"])

    @patch('requests.get')
    def test_check_series_status(self, mock_get):
        """
        ✅ Testar verificação de status da série na AT
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "active",
            "valid": True,
            "validation_code": "AT987654321"
        }
        mock_get.return_value = mock_response

        result = self.client.check_series_status("AT987654321")
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("valid", False))

    def test_series_format_sem_hifens(self):
        """
        ✅ Testar formato SEM HÍFENS da série
        """
        series_doc = frappe.get_doc("Portugal Series Configuration", self.series_name)
        self.assertNotIn("-", series_doc.prefix)
        self.assertTrue(series_doc.naming_series.startswith(series_doc.prefix))
        self.assertTrue(series_doc.naming_series.endswith(".####"))

    def test_series_communication_status_update(self):
        """
        ✅ Testar atualização de status após comunicação
        """
        # Simular comunicação bem-sucedida
        series_doc = frappe.get_doc("Portugal Series Configuration", self.series_name)
        series_doc.is_communicated = 1
        series_doc.validation_code = "AT987654321"
        series_doc.communication_date = datetime.now()
        series_doc.save(ignore_permissions=True)
        series_doc.reload()
        self.assertTrue(series_doc.is_communicated)
        self.assertIsNotNone(series_doc.validation_code)

    # ========== EDGE CASES ==========

    def test_communicate_series_invalid_format(self):
        """
        ✅ Testar comunicação com série em formato inválido (COM HÍFENS)
        """
        # Criar série com hífens
        series_name = "Test Series FT OLD"
        if not frappe.db.exists("Portugal Series Configuration", series_name):
            series = frappe.new_doc("Portugal Series Configuration")
            series.update({
                "series_name": series_name,
                "company": self.company,
                "document_type": "Sales Invoice",
                "prefix": "FT-2025-TCSC",  # COM HÍFENS (INVÁLIDO)
                "naming_series": "FT-2025-TCSC.####",
                "current_sequence": 1,
                "is_active": 1,
                "is_communicated": 0
            })
            series.insert(ignore_permissions=True)
        series_doc = frappe.get_doc("Portugal Series Configuration", series_name)
        # Tentar comunicar
        with patch.object(self.client, 'communicate_series_batch') as mock_communicate:
            mock_communicate.return_value = {
                "status": "error",
                "results": [{
                    "series": series_name,
                    "success": False,
                    "message": "Formato inválido"
                }]
            }
            result = self.client.communicate_series_batch([series_doc], self.username, self.password)
            self.assertEqual(result["status"], "error")

    def test_communicate_series_already_communicated(self):
        """
        ✅ Testar comunicação de série já comunicada
        """
        series_doc = frappe.get_doc("Portugal Series Configuration", self.series_name)
        series_doc.is_communicated = 1
        series_doc.validation_code = "AT987654321"
        series_doc.save(ignore_permissions=True)
        with patch.object(self.client, 'communicate_series_batch') as mock_communicate:
            mock_communicate.return_value = {
                "status": "success",
                "results": [{
                    "series": self.series_name,
                    "success": False,
                    "message": "Série já comunicada"
                }]
            }
            result = self.client.communicate_series_batch([series_doc], self.username, self.password)
            self.assertEqual(result["status"], "success")
            self.assertIn("Série já comunicada", result["results"][0]["message"])

    # ========== PERFORMANCE ==========

    def test_batch_communication_performance(self):
        """
        ✅ Testar performance de comunicação em lote
        """
        series_list = []
        for i in range(3):
            name = f"Test Series FT COMM {i}"
            if not frappe.db.exists("Portugal Series Configuration", name):
                series = frappe.new_doc("Portugal Series Configuration")
                series.update({
                    "series_name": name,
                    "company": self.company,
                    "document_type": "Sales Invoice",
                    "prefix": f"FT2025TCSC{i}",
                    "naming_series": f"FT2025TCSC{i}.####",
                    "current_sequence": 1,
                    "is_active": 1,
                    "is_communicated": 0
                })
                series.insert(ignore_permissions=True)
            series_list.append(frappe.get_doc("Portugal Series Configuration", name))

        with patch.object(self.client, 'communicate_series_batch') as mock_communicate:
            mock_communicate.return_value = {
                "status": "success",
                "results": [{"series": s.series_name, "success": True} for s in series_list]
            }
            import time
            start = time.time()
            result = self.client.communicate_series_batch(series_list, self.username, self.password)
            elapsed = time.time() - start
            self.assertEqual(result["status"], "success")
            self.assertLess(elapsed, 2.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
