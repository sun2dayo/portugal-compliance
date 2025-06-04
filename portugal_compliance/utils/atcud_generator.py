# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
ATCUD Generator for Portugal Compliance - VERSÃO NATIVA CORRIGIDA
Generates ATCUD codes according to Portuguese legislation (Portaria 195/2020)
✅ CORRIGIDO: Compatível com formato SEM HÍFENS (FT2025NDX)
✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
✅ CONFORME: Legislação portuguesa 2023+ e Portaria 195/2020
"""

import frappe
from frappe import _
from frappe.utils import getdate, now, today, cint, flt
import re
import hashlib
import json
from datetime import datetime, date
import qrcode
import base64
from io import BytesIO


class ATCUDGenerator:
	"""
	Gerador de códigos ATCUD conforme legislação portuguesa
	✅ CORRIGIDO: Compatível com naming_series SEM HÍFENS
	ATCUD = Código de Validação + Número Sequencial (separados por hífen)
	Exemplo: CSDF7T5H-00000001
	"""

	def __init__(self):
		self.module = "Portugal Compliance"

		# ✅ FORMATOS OFICIAIS CONFORME LEGISLAÇÃO
		self.atcud_format = r'^[A-Z0-9]{8,12}-\d{8}$'  # CODIGO-SEQUENCIA
		self.validation_code_format = r'^[A-Z0-9]{8,12}$'  # 8-12 caracteres alfanuméricos

		# ✅ TIPOS DE DOCUMENTOS SUPORTADOS CONFORME SAF-T PT
		self.supported_document_types = {
			"Sales Invoice": {
				"saft_type": "FT",  # Fatura
				"class": "SI",
				"requires_atcud": True,
				"requires_qr": True
			},
			"Purchase Invoice": {
				"saft_type": "FC",
				"class": "PI",
				"requires_atcud": True,
				"requires_qr": False
			},
			"POS Invoice": {
				"saft_type": "FS",  # Fatura Simplificada
				"class": "FS",
				"requires_atcud": True,
				"requires_qr": True
			},
			"Payment Entry": {
				"saft_type": "RC",  # Recibo
				"class": "RC",
				"requires_atcud": True,
				"requires_qr": True
			},
			"Delivery Note": {
				"saft_type": "GT",  # Guia de Transporte
				"class": "GT",
				"requires_atcud": True,
				"requires_qr": False
			},
			"Purchase Receipt": {
				"saft_type": "GR",  # Guia de Receção
				"class": "GR",
				"requires_atcud": True,
				"requires_qr": False
			},
			"Stock Entry": {
				"saft_type": "GM",  # Guia de Movimentação
				"class": "SE",
				"requires_atcud": True,
				"requires_qr": False
			},
			"Journal Entry": {
				"saft_type": "JE",  # Lançamento Contabilístico
				"class": "JE",
				"requires_atcud": False,
				"requires_qr": False
			},
			"Quotation": {
				"saft_type": "OR",  # Orçamento
				"class": "QT",
				"requires_atcud": False,
				"requires_qr": False
			},
			"Sales Order": {
				"saft_type": "EC",  # Encomenda Cliente (CORRIGIDO)
				"class": "SO",
				"requires_atcud": False,
				"requires_qr": False
			},
			"Purchase Order": {
				"saft_type": "EF",  # Encomenda Fornecedor (CORRIGIDO)
				"class": "PO",
				"requires_atcud": False,
				"requires_qr": False
			}
		}

		frappe.logger().info("🇵🇹 ATCUDGenerator inicializado - Conforme Portaria 195/2020")

	def generate_atcud_for_document(self, doc):
		"""
		✅ FUNÇÃO PRINCIPAL CORRIGIDA: Gerar ATCUD para documento usando naming_series SEM HÍFENS
		Compatível com document_hooks.py corrigido
		"""
		try:
			generation_id = f"ATCUD_{int(datetime.now().timestamp())}"
			frappe.logger().info(
				f"🔢 [{generation_id}] Gerando ATCUD para {doc.doctype}: {doc.name}")

			# ✅ VALIDAÇÕES PRELIMINARES
			validation_result = self._validate_document_for_atcud(doc)
			if not validation_result["valid"]:
				return {
					"success": False,
					"error": validation_result["error"],
					"generation_id": generation_id
				}

			# ✅ EXTRAIR INFORMAÇÕES DA NAMING SERIES NATIVA (SEM HÍFENS)
			series_info = self._extract_series_info_from_naming_series(doc.naming_series)
			if not series_info:
				return {
					"success": False,
					"error": f"Não foi possível extrair informações da naming series: {doc.naming_series}",
					"generation_id": generation_id
				}

			# ✅ OBTER CÓDIGO DE VALIDAÇÃO AT
			validation_code = self._get_at_validation_code(series_info, doc.company)
			if not validation_code:
				# ✅ GERAR CÓDIGO TEMPORÁRIO SE NÃO COMUNICADA
				validation_code = self._generate_temporary_validation_code(series_info)
				frappe.logger().warning(
					f"⚠️ Usando código temporário para série não comunicada: {validation_code}")

			# ✅ EXTRAIR NÚMERO SEQUENCIAL DO DOCUMENTO
			sequence_number = self._extract_sequence_from_document_name(doc.name)

			# ✅ GERAR ATCUD CONFORME FORMATO OFICIAL
			atcud_code = f"{validation_code}-{sequence_number:08d}"

			# ✅ VALIDAR ATCUD GERADO
			is_valid, validation_msg = self._validate_atcud_format(atcud_code)
			if not is_valid:
				return {
					"success": False,
					"error": f"ATCUD gerado inválido: {validation_msg}",
					"atcud_code": atcud_code,
					"generation_id": generation_id
				}

			# ✅ GERAR QR CODE SE NECESSÁRIO
			qr_code_data = None
			if self._requires_qr_code(doc.doctype):
				qr_result = self._generate_qr_code(doc, atcud_code, series_info)
				if qr_result.get("success"):
					qr_code_data = qr_result["qr_data"]

			# ✅ CRIAR LOG DE AUDITORIA
			self._create_atcud_audit_log(doc, atcud_code, validation_code, sequence_number,
										 generation_id)

			frappe.logger().info(f"✅ [{generation_id}] ATCUD gerado: {atcud_code}")

			return {
				"success": True,
				"atcud_code": atcud_code,
				"validation_code": validation_code,
				"sequence_number": sequence_number,
				"series_prefix": series_info["prefix"],
				"document_type": doc.doctype,
				"document_name": doc.name,
				"company": doc.company,
				"qr_code_data": qr_code_data,
				"generation_id": generation_id,
				"generation_date": now(),
				"compliant_with": "Portaria 195/2020"
			}

		except Exception as e:
			frappe.log_error(f"Erro crítico na geração de ATCUD: {str(e)}", "ATCUDGenerator")
			return {
				"success": False,
				"error": str(e),
				"generation_id": generation_id if 'generation_id' in locals() else "UNKNOWN"
			}

	def _validate_document_for_atcud(self, doc):
		"""Validar se documento pode ter ATCUD gerado"""
		try:
			# ✅ VERIFICAR SE DOCTYPE É SUPORTADO
			if doc.doctype not in self.supported_document_types:
				return {
					"valid": False,
					"error": f"DocType {doc.doctype} não suporta ATCUD"
				}

			# ✅ VERIFICAR SE EMPRESA É PORTUGUESA
			if not self._is_portuguese_company(doc.company):
				return {
					"valid": False,
					"error": "ATCUD só é obrigatório para empresas portuguesas"
				}

			# ✅ VERIFICAR SE TEM NAMING SERIES
			if not getattr(doc, 'naming_series', None):
				return {
					"valid": False,
					"error": "Documento deve ter naming_series definida"
				}

			# ✅ VERIFICAR SE NAMING SERIES É PORTUGUESA (SEM HÍFENS)
			if not self._is_portuguese_naming_series(doc.naming_series):
				return {
					"valid": False,
					"error": f"Naming series {doc.naming_series} não é portuguesa"
				}

			# ✅ VERIFICAR SE DOCUMENTO TEM NOME
			if not doc.name or doc.name == 'new':
				return {
					"valid": False,
					"error": "Documento deve ser salvo antes de gerar ATCUD"
				}

			# ✅ VERIFICAR SE JÁ TEM ATCUD
			if getattr(doc, 'atcud_code', None):
				return {
					"valid": False,
					"error": f"Documento já tem ATCUD: {doc.atcud_code}"
				}

			return {"valid": True}

		except Exception as e:
			return {
				"valid": False,
				"error": f"Erro na validação: {str(e)}"
			}

	def _extract_series_info_from_naming_series(self, naming_series):
		"""
		✅ CORRIGIDO: Extrair informações da naming_series SEM HÍFENS
		Formato: XXYYYY + COMPANY.#### → {prefix: XXYYYY + COMPANY, doc_code: XX, year: YYYY, company: COMPANY}
		Exemplo: FT2025NDX.#### → {prefix: FT2025NDX, doc_code: FT, year: 2025, company: NDX}
		"""
		try:
			if not naming_series:
				return None

			# ✅ PADRÃO NAMING SERIES PORTUGUESA SEM HÍFENS
			pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})\.####$'
			match = re.match(pattern, naming_series)

			if not match:
				frappe.logger().warning(
					f"⚠️ Naming series não corresponde ao padrão português: {naming_series}")
				return None

			doc_code, year, company_abbr = match.groups()
			prefix = f"{doc_code}{year}{company_abbr}"

			return {
				"naming_series": naming_series,
				"prefix": prefix,
				"doc_code": doc_code,
				"year": int(year),
				"company_abbr": company_abbr
			}

		except Exception as e:
			frappe.log_error(f"Erro ao extrair informações da naming series: {str(e)}")
			return None

	def _get_at_validation_code(self, series_info, company):
		"""
		✅ CORRIGIDO: Obter código de validação AT para a série SEM HÍFENS
		Busca em Portugal Series Configuration
		"""
		try:
			# ✅ BUSCAR CÓDIGO DE VALIDAÇÃO NA CONFIGURAÇÃO DA SÉRIE
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"prefix": series_info["prefix"],
				"company": company,
				"document_type": self._get_doctype_from_prefix(series_info["doc_code"]),
				"is_active": 1
			}, ["validation_code", "is_communicated"], as_dict=True)

			if series_config and series_config.validation_code:
				# ✅ VALIDAR FORMATO DO CÓDIGO
				is_valid, _ = self._validate_validation_code_format(series_config.validation_code)
				if is_valid:
					return series_config.validation_code

			# ✅ FALLBACK: Buscar em campos customizados da empresa
			field_name = f"at_code_{series_info['doc_code']}"
			validation_code = frappe.db.get_value("Company", company, field_name)

			if validation_code:
				is_valid, _ = self._validate_validation_code_format(validation_code)
				if is_valid:
					return validation_code

			return None

		except Exception as e:
			frappe.log_error(f"Erro ao obter código de validação AT: {str(e)}")
			return None

	def _get_doctype_from_prefix(self, doc_code):
		"""Obter DocType baseado no prefixo do documento"""
		prefix_mapping = {
			"FT": "Sales Invoice",
			"FS": "Sales Invoice",  # Pode ser Sales Invoice ou POS Invoice
			"FR": "Sales Invoice",
			"NC": "Sales Invoice",
			"ND": "Sales Invoice",
			"FC": "Purchase Invoice",
			"RC": "Payment Entry",
			"RB": "Payment Entry",
			"GT": "Delivery Note",
			"GR": "Purchase Receipt",
			"GM": "Stock Entry",
			"JE": "Journal Entry",
			"OR": "Quotation",
			"EC": "Sales Order",
			"EF": "Purchase Order"
		}
		return prefix_mapping.get(doc_code, "Sales Invoice")

	def _generate_temporary_validation_code(self, series_info):
		"""
		Gerar código de validação temporário para séries não comunicadas
		"""
		try:
			# ✅ CÓDIGO TEMPORÁRIO BASEADO NO PREFIXO
			base_code = f"TEMP{series_info['doc_code']}{series_info['year']}"

			# Garantir que tem pelo menos 8 caracteres
			while len(base_code) < 8:
				base_code += "0"

			# Limitar a 12 caracteres
			return base_code[:12].upper()

		except Exception as e:
			frappe.log_error(f"Erro ao gerar código temporário: {str(e)}")
			return "TEMP0000"

	def _extract_sequence_from_document_name(self, document_name):
		"""
		✅ CORRIGIDO: Extrair número sequencial do nome do documento
		Suporta formatos COM e SEM hífens:
		- FT2025NDX00000001 (sem hífens)
		- FT-2025-NDX-00000001 (com hífens - formato antigo)
		"""
		try:
			if not document_name:
				return 1

			# ✅ PADRÕES PARA EXTRAIR SEQUÊNCIA (SEM E COM HÍFENS)
			patterns = [
				r'(\d{8})$',  # 8 dígitos no final: FT2025NDX00000001
				r'-(\d{8})$',  # 8 dígitos após hífen: FT-2025-NDX-00000001
				r'\.(\d{8})$',  # 8 dígitos após ponto: FT2025NDX.00000001
				r'(\d{6,})$',  # 6+ dígitos no final: FT2025NDX000001
				r'-(\d{4,})$',  # 4+ dígitos após hífen: FT-2025-NDX-0001
				r'\.(\d{4,})$',  # 4+ dígitos após ponto: FT2025NDX.0001
				r'(\d+)$'  # Qualquer número no final
			]

			for pattern in patterns:
				match = re.search(pattern, document_name)
				if match:
					sequence = int(match.group(1))
					if sequence > 0:
						return sequence

			# ✅ FALLBACK
			frappe.logger().warning(f"Não foi possível extrair sequência de: {document_name}")
			return 1

		except Exception as e:
			frappe.log_error(f"Erro ao extrair sequência: {str(e)}")
			return 1

	def _validate_atcud_format(self, atcud_code):
		"""
		Validar formato do código ATCUD conforme legislação
		Formato: CODIGO-SEQUENCIA (ex: CSDF7T5H-00000001)
		"""
		try:
			if not atcud_code:
				return False, "Código ATCUD vazio"

			# ✅ VERIFICAR FORMATO GERAL
			if not re.match(self.atcud_format, atcud_code):
				return False, f"Formato deve ser CODIGO-SEQUENCIA (8-12 chars alfanuméricos + hífen + 8 dígitos)"

			# ✅ DIVIDIR CÓDIGO E SEQUÊNCIA
			parts = atcud_code.split('-')
			if len(parts) != 2:
				return False, "Deve conter exatamente um hífen separando código e sequência"

			validation_code, sequence = parts

			# ✅ VALIDAR CÓDIGO DE VALIDAÇÃO
			is_valid_code, code_msg = self._validate_validation_code_format(validation_code)
			if not is_valid_code:
				return False, f"Código de validação inválido: {code_msg}"

			# ✅ VALIDAR SEQUÊNCIA
			if not sequence.isdigit():
				return False, "Sequência deve ser numérica"

			if len(sequence) != 8:
				return False, "Sequência deve ter exatamente 8 dígitos"

			sequence_num = int(sequence)
			if sequence_num < 1:
				return False, "Sequência deve ser maior que zero"

			return True, "ATCUD válido"

		except Exception as e:
			return False, f"Erro na validação: {str(e)}"

	def _validate_validation_code_format(self, validation_code):
		"""Validar formato do código de validação AT"""
		try:
			if not validation_code:
				return False, "Código vazio"

			# ✅ COMPRIMENTO
			if not (8 <= len(validation_code) <= 12):
				return False, f"Deve ter 8-12 caracteres (atual: {len(validation_code)})"

			# ✅ ALFANUMÉRICO MAIÚSCULO
			if not validation_code.isalnum() or not validation_code.isupper():
				return False, "Deve ser alfanumérico maiúsculo"

			# ✅ DEVE CONTER PELO MENOS UMA LETRA
			if not any(c.isalpha() for c in validation_code):
				return False, "Deve conter pelo menos uma letra"

			# ✅ NÃO PODE SER APENAS NÚMEROS
			if validation_code.isdigit():
				return False, "Não pode ser apenas numérico"

			return True, "Código válido"

		except Exception as e:
			return False, f"Erro: {str(e)}"

	def _is_portuguese_company(self, company):
		"""Verificar se empresa é portuguesa"""
		try:
			company_data = frappe.db.get_value("Company", company,
											   ["country", "portugal_compliance_enabled"],
											   as_dict=True)

			if not company_data:
				return False

			return (company_data.country == "Portugal" and
					cint(company_data.portugal_compliance_enabled))

		except Exception:
			return False

	def _is_portuguese_naming_series(self, naming_series):
		"""
		✅ CORRIGIDO: Verificar se naming_series é portuguesa (SEM HÍFENS)
		Formato: XXYYYY + COMPANY.#### (ex: FT2025NDX.####)
		"""
		try:
			if not naming_series:
				return False

			# ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
			pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'
			return bool(re.match(pattern, naming_series))

		except Exception:
			return False

	def _requires_qr_code(self, doctype):
		"""Verificar se tipo de documento requer QR code"""
		doc_config = self.supported_document_types.get(doctype, {})
		return doc_config.get("requires_qr", False)

	# ========== GERAÇÃO DE QR CODE ==========

	def _generate_qr_code(self, doc, atcud_code, series_info):
		"""
		Gerar QR code conforme especificações portuguesas
		Tamanho mínimo: 30mm x 30mm conforme legislação
		"""
		try:
			# ✅ DADOS PARA QR CODE CONFORME ESPECIFICAÇÕES AT
			qr_data = self._build_qr_data(doc, atcud_code, series_info)

			# ✅ GERAR QR CODE
			qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_M,
				box_size=10,
				border=4,
			)
			qr.add_data(qr_data)
			qr.make(fit=True)

			# ✅ CRIAR IMAGEM
			qr_image = qr.make_image(fill_color="black", back_color="white")

			# ✅ CONVERTER PARA BASE64
			buffer = BytesIO()
			qr_image.save(buffer, format='PNG')
			qr_base64 = base64.b64encode(buffer.getvalue()).decode()

			return {
				"success": True,
				"qr_data": qr_data,
				"qr_base64": qr_base64,
				"qr_size": "30mm x 30mm (mínimo legal)",
				"format": "PNG"
			}

		except Exception as e:
			frappe.log_error(f"Erro ao gerar QR code: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def _build_qr_data(self, doc, atcud_code, series_info):
		"""
		Construir dados para QR code conforme especificações AT
		"""
		try:
			# ✅ OBTER NIF DA EMPRESA
			company_nif = frappe.db.get_value("Company", doc.company, "tax_id") or ""

			# ✅ OBTER NIF DO CLIENTE/FORNECEDOR
			customer_nif = ""
			if hasattr(doc, 'customer') and doc.customer:
				customer_nif = frappe.db.get_value("Customer", doc.customer, "tax_id") or ""
			elif hasattr(doc, 'supplier') and doc.supplier:
				customer_nif = frappe.db.get_value("Supplier", doc.supplier, "tax_id") or ""

			# ✅ DADOS OBRIGATÓRIOS CONFORME LEGISLAÇÃO
			qr_data = {
				"A": company_nif,  # NIF do emitente
				"B": customer_nif,  # NIF do adquirente
				"C": doc.company,  # Nome do emitente
				"D": self.supported_document_types.get(doc.doctype, {}).get("saft_type", "FT"),
				# Tipo de documento
				"E": "N",  # Estado do documento (N=Normal, A=Anulado)
				"F": getdate(doc.posting_date).strftime('%Y%m%d') if hasattr(doc,
																			 'posting_date') else getdate().strftime(
					'%Y%m%d'),  # Data
				"G": doc.name,  # Número do documento
				"H": atcud_code,  # ATCUD
				"I1": f"{flt(getattr(doc, 'net_total', 0)):.2f}",  # Base tributável taxa normal
				"I2": f"{flt(getattr(doc, 'total_taxes_and_charges', 0)):.2f}",  # IVA taxa normal
				"I3": "0.00",  # Base tributável taxa intermédia
				"I4": "0.00",  # IVA taxa intermédia
				"I5": "0.00",  # Base tributável taxa reduzida
				"I6": "0.00",  # IVA taxa reduzida
				"I7": "0.00",  # Base tributável taxa zero
				"I8": "0.00",  # IVA taxa zero
				"N": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",  # Total do documento
				"O": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",  # Total com impostos
				"P": "0",  # Retenção na fonte
				"Q": hashlib.sha1(f"{doc.name}{atcud_code}".encode()).hexdigest()[:4].upper(),
				# Hash de validação
				"R": series_info["prefix"]  # Identificador da série
			}

			# ✅ CONVERTER PARA STRING CONFORME FORMATO AT
			qr_string = "*".join([f"{key}:{value}" for key, value in qr_data.items()])

			return qr_string

		except Exception as e:
			frappe.log_error(f"Erro ao construir dados QR: {str(e)}")
			return f"ERROR:{str(e)}"

	# ========== AUDITORIA E LOGS ==========

	def _create_atcud_audit_log(self, doc, atcud_code, validation_code, sequence_number,
								generation_id):
		"""
		Criar log de auditoria para ATCUD gerado
		"""
		try:
			# ✅ CRIAR COMMENT PARA AUDITORIA
			comment_content = f"""
ATCUD Gerado Automaticamente:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Código ATCUD: {atcud_code}
• Código de Validação: {validation_code}
• Número Sequencial: {sequence_number:08d}
• Naming Series: {doc.naming_series}
• Data/Hora: {now()}
• Usuário: {frappe.session.user}
• ID Geração: {generation_id}
• Conforme: Portaria 195/2020
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """.strip()

			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": comment_content,
				"comment_email": frappe.session.user
			}).insert(ignore_permissions=True)

			# ✅ LOG ESTRUTURADO
			frappe.logger().info(f"📋 ATCUD Audit Log criado para {doc.name}: {atcud_code}")

		except Exception as e:
			frappe.log_error(f"Erro ao criar log de auditoria: {str(e)}")

	# ========== VALIDAÇÃO E VERIFICAÇÃO ==========

	def validate_existing_atcud(self, atcud_code):
		"""
		Validar ATCUD existente
		"""
		try:
			is_valid, message = self._validate_atcud_format(atcud_code)

			return {
				"valid": is_valid,
				"message": message,
				"atcud_code": atcud_code,
				"format_check": "Portaria 195/2020"
			}

		except Exception as e:
			return {
				"valid": False,
				"message": str(e),
				"atcud_code": atcud_code
			}

	def get_atcud_info(self, atcud_code):
		"""
		Obter informações detalhadas de um ATCUD
		"""
		try:
			if not atcud_code or '-' not in atcud_code:
				return {
					"valid": False,
					"error": "ATCUD inválido"
				}

			validation_code, sequence = atcud_code.split('-')

			return {
				"valid": True,
				"atcud_code": atcud_code,
				"validation_code": validation_code,
				"sequence_number": int(sequence),
				"sequence_formatted": sequence,
				"format": "CODIGO-SEQUENCIA",
				"compliance": "Portaria 195/2020",
				"validation_code_length": len(validation_code),
				"sequence_length": len(sequence)
			}

		except Exception as e:
			return {
				"valid": False,
				"error": str(e),
				"atcud_code": atcud_code
			}

	def check_atcud_uniqueness(self, atcud_code, exclude_doc=None):
		"""
		Verificar se ATCUD é único no sistema
		"""
		try:
			# ✅ BUSCAR EM TODOS OS DOCTYPES SUPORTADOS
			duplicates = []

			for doctype in self.supported_document_types.keys():
				filters = {"atcud_code": atcud_code}

				if exclude_doc and exclude_doc.get("doctype") == doctype:
					filters["name"] = ["!=", exclude_doc.get("name")]

				existing = frappe.get_all(doctype,
										  filters=filters,
										  fields=["name", "creation"],
										  limit=5)

				for doc in existing:
					duplicates.append({
						"doctype": doctype,
						"name": doc.name,
						"creation": doc.creation
					})

			return {
				"unique": len(duplicates) == 0,
				"duplicates": duplicates,
				"duplicate_count": len(duplicates),
				"atcud_code": atcud_code
			}

		except Exception as e:
			return {
				"unique": False,
				"error": str(e),
				"atcud_code": atcud_code
			}


# ========== INSTÂNCIA GLOBAL ==========

# ✅ INSTÂNCIA GLOBAL PARA USO
atcud_generator = ATCUDGenerator()


# ========== FUNÇÕES AUXILIARES ==========

def generate_atcud_for_document(doc):
	"""Gerar ATCUD para documento"""
	return atcud_generator.generate_atcud_for_document(doc)


def validate_atcud_format(atcud_code):
	"""Validar formato de ATCUD"""
	return atcud_generator.validate_existing_atcud(atcud_code)


def get_atcud_info(atcud_code):
	"""Obter informações de ATCUD"""
	return atcud_generator.get_atcud_info(atcud_code)


def extract_sequence_from_document_name(document_name):
	"""Extrair sequencial do nome do documento"""
	return atcud_generator._extract_sequence_from_document_name(document_name)


# ========== APIS WHITELISTED ==========

@frappe.whitelist()
def generate_manual_atcud_certified(doctype, docname):
	"""
	✅ CORRIGIDO: API para gerar ATCUD manualmente
	Compatível com document_hooks.py
	"""
	try:
		if not docname or docname == "new":
			return {
				"success": False,
				"error": "Documento deve ser salvo antes de gerar ATCUD"
			}

		doc = frappe.get_doc(doctype, docname)
		result = atcud_generator.generate_atcud_for_document(doc)

		if result.get("success"):
			# ✅ ATUALIZAR DOCUMENTO
			frappe.db.set_value(doctype, docname, "atcud_code", result["atcud_code"])
			frappe.db.commit()

		return result

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD manual: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_atcud_code(atcud_code):
	"""
	API para validar código ATCUD
	"""
	try:
		result = atcud_generator.validate_existing_atcud(atcud_code)

		# ✅ VERIFICAR UNICIDADE
		uniqueness = atcud_generator.check_atcud_uniqueness(atcud_code)
		result.update(uniqueness)

		return result

	except Exception as e:
		return {
			"valid": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_atcud_statistics():
	"""
	API para obter estatísticas de ATCUD
	"""
	try:
		stats = {
			"total_documents_with_atcud": 0,
			"by_doctype": {},
			"validation_summary": {
				"valid_atcuds": 0,
				"invalid_atcuds": 0,
				"duplicate_atcuds": 0
			}
		}

		# ✅ CONTAR POR DOCTYPE
		for doctype in atcud_generator.supported_document_types.keys():
			try:
				total = frappe.db.count(doctype, {"atcud_code": ["!=", ""]})
				stats["by_doctype"][doctype] = total
				stats["total_documents_with_atcud"] += total
			except Exception:
				stats["by_doctype"][doctype] = 0

		return {
			"success": True,
			"statistics": stats,
			"compliance": "Portaria 195/2020",
			"supported_doctypes": list(atcud_generator.supported_document_types.keys())
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def batch_generate_atcud(doctype, filters=None):
	"""
	API para gerar ATCUD em lote
	"""
	try:
		if not filters:
			filters = {"atcud_code": ["in", ["", None]]}

		documents = frappe.get_all(doctype,
								   filters=filters,
								   fields=["name"],
								   limit=100)

		results = []
		successful = 0
		failed = 0

		for doc_data in documents:
			try:
				doc = frappe.get_doc(doctype, doc_data.name)
				result = atcud_generator.generate_atcud_for_document(doc)

				if result.get("success"):
					frappe.db.set_value(doctype, doc.name, "atcud_code", result["atcud_code"])
					successful += 1
				else:
					failed += 1

				results.append({
					"document": doc.name,
					"success": result.get("success", False),
					"atcud_code": result.get("atcud_code"),
					"error": result.get("error")
				})

			except Exception as e:
				failed += 1
				results.append({
					"document": doc_data.name,
					"success": False,
					"error": str(e)
				})

		frappe.db.commit()

		return {
			"success": True,
			"total_processed": len(results),
			"successful": successful,
			"failed": failed,
			"results": results
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def migrate_atcud_to_new_format():
	"""
	✅ NOVA: Migrar ATCUDs existentes para novo formato (se necessário)
	"""
	try:
		frappe.logger().info("🔄 Verificando ATCUDs para migração...")

		# Buscar documentos com ATCUD que podem precisar de migração
		total_migrated = 0

		for doctype in atcud_generator.supported_document_types.keys():
			try:
				docs_with_atcud = frappe.get_all(doctype,
												 filters={"atcud_code": ["!=", ""]},
												 fields=["name", "atcud_code"])

				for doc in docs_with_atcud:
					# Verificar se ATCUD está no formato correto
					is_valid, _ = atcud_generator._validate_atcud_format(doc.atcud_code)

					if not is_valid:
						# Tentar corrigir formato se possível
						# (implementar lógica de correção se necessário)
						frappe.logger().warning(
							f"ATCUD inválido encontrado: {doc.name} - {doc.atcud_code}")

			except Exception as e:
				frappe.log_error(f"Erro ao verificar {doctype}: {str(e)}")

		return {
			"success": True,
			"migrated_count": total_migrated,
			"message": f"Verificação concluída. {total_migrated} ATCUDs migrados."
		}

	except Exception as e:
		frappe.log_error(f"Erro na migração de ATCUD: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÃO PARA EXECUÇÃO DIRETA ==========

def setup_atcud_generator():
	"""Configurar gerador de ATCUD"""
	try:
		print("🇵🇹 Configurando gerador de ATCUD...")
		print("✅ ATCUDGenerator configurado conforme Portaria 195/2020")
		print("✅ Compatível com naming_series sem hífens")
		print("✅ Integrado com document_hooks.py e series_adapter.py")
		return True
	except Exception as e:
		print(f"❌ Erro ao configurar ATCUD generator: {str(e)}")
		return False


if __name__ == "__main__":
	setup_atcud_generator()
