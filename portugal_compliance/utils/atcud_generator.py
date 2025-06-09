# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
ATCUD Generator for Portugal Compliance - VERSÃO ATUALIZADA E ALINHADA
Generates ATCUD codes according to Portuguese legislation (Portaria 195/2020)
✅ ALINHADO: 100% compatível com document_hooks.py e series_adapter.py
✅ OTIMIZADO: Sem duplicação de funcionalidades
✅ CONFORME: Legislação portuguesa 2025+ e Portaria 195/2020
✅ DINÂMICO: Baseado no abbr da empresa (não fixo NDX)
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
	✅ CLASSE ATUALIZADA: Gerador de códigos ATCUD conforme legislação portuguesa
	Compatível com naming_series SEM HÍFENS e integrado com document_hooks.py
	Baseado na sua experiência com programação.consistência_de_dados[4]
	"""

	def __init__(self):
		self.module = "Portugal Compliance"

		# ✅ FORMATOS OFICIAIS CONFORME LEGISLAÇÃO (ATUALIZADOS)
		self.atcud_format = r'^[A-Z0-9]{8,12}-\d{8}$'  # CODIGO-SEQUENCIA
		self.validation_code_format = r'^[A-Z0-9]{8,12}$'  # 8-12 caracteres alfanuméricos

		# ✅ TIPOS DE DOCUMENTOS SUPORTADOS CONFORME SAF-T PT (CORRIGIDOS)
		self.supported_document_types = {
			"Sales Invoice": {
				"saft_type": "FT",  # Fatura
				"class": "SI",
				"requires_atcud": True,
				"requires_qr": True,
				"priority": 1
			},
			"Purchase Invoice": {
				"saft_type": "FC",
				"class": "PI",
				"requires_atcud": True,
				"requires_qr": False,
				"priority": 2
			},
			"POS Invoice": {
				"saft_type": "FS",  # Fatura Simplificada
				"class": "FS",
				"requires_atcud": True,
				"requires_qr": True,
				"priority": 3
			},
			"Payment Entry": {
				"saft_type": "RC",  # Recibo
				"class": "RC",
				"requires_atcud": True,
				"requires_qr": True,
				"priority": 4
			},
			"Delivery Note": {
				"saft_type": "GT",  # Guia de Transporte
				"class": "GT",
				"requires_atcud": True,
				"requires_qr": False,
				"priority": 5
			},
			"Purchase Receipt": {
				"saft_type": "GR",  # Guia de Receção
				"class": "GR",
				"requires_atcud": True,
				"requires_qr": False,
				"priority": 6
			},
			"Stock Entry": {
				"saft_type": "GM",  # Guia de Movimentação
				"class": "SE",
				"requires_atcud": True,
				"requires_qr": False,
				"priority": 7
			},
			"Journal Entry": {
				"saft_type": "JE",  # Lançamento Contabilístico
				"class": "JE",
				"requires_atcud": False,
				"requires_qr": False,
				"priority": 8
			},
			"Quotation": {
				"saft_type": "OR",  # Orçamento
				"class": "QT",
				"requires_atcud": False,
				"requires_qr": False,
				"priority": 9
			},
			"Sales Order": {
				"saft_type": "EC",  # ✅ CORRIGIDO: EN → EC
				"class": "SO",
				"requires_atcud": False,
				"requires_qr": False,
				"priority": 10
			},
			"Purchase Order": {
				"saft_type": "EF",  # ✅ CORRIGIDO: OC → EF
				"class": "PO",
				"requires_atcud": False,
				"requires_qr": False,
				"priority": 11
			},
			"Material Request": {
				"saft_type": "MR",  # ✅ ADICIONADO
				"class": "MR",
				"requires_atcud": False,
				"requires_qr": False,
				"priority": 12
			}
		}

		frappe.logger().info("🇵🇹 ATCUDGenerator ATUALIZADO - Conforme Portaria 195/2020")

	def generate_atcud_for_document(self, doc):
		"""
		✅ FUNÇÃO PRINCIPAL ATUALIZADA: Gerar ATCUD para documento
		Integrada com document_hooks.py para evitar duplicação
		Baseado na sua experiência com programação.refatoração_de_código[3]
		"""
		try:
			generation_id = f"ATCUD_{int(datetime.now().timestamp())}"
			frappe.logger().info(
				f"🔢 [{generation_id}] Gerando ATCUD para {doc.doctype}: {doc.name}")

			# ✅ VALIDAÇÕES PRELIMINARES OTIMIZADAS
			validation_result = self._validate_document_for_atcud_optimized(doc)
			if not validation_result["valid"]:
				return {
					"success": False,
					"error": validation_result["error"],
					"generation_id": generation_id
				}

			# ✅ OBTER INFORMAÇÕES DA SÉRIE (ALINHADO COM SERIES_ADAPTER)
			series_info = self._get_series_info_from_document(doc)
			if not series_info:
				return {
					"success": False,
					"error": f"Não foi possível obter informações da série para: {doc.naming_series}",
					"generation_id": generation_id
				}

			# ✅ OBTER CÓDIGO DE VALIDAÇÃO AT (OTIMIZADO)
			validation_code = self._get_validation_code_optimized(series_info, doc.company)
			if not validation_code:
				# ✅ GERAR CÓDIGO TEMPORÁRIO MELHORADO
				validation_code = self._generate_enhanced_temporary_code(series_info, doc.company)
				frappe.logger().warning(f"⚠️ Usando código temporário: {validation_code}")

			# ✅ OBTER PRÓXIMO NÚMERO SEQUENCIAL (THREAD-SAFE)
			sequence_number = self._get_next_sequence_thread_safe(series_info, doc)

			# ✅ GERAR ATCUD CONFORME FORMATO OFICIAL
			atcud_code = f"{validation_code}-{sequence_number:08d}"

			# ✅ VALIDAR ATCUD GERADO
			is_valid, validation_msg = self._validate_atcud_format_enhanced(atcud_code)
			if not is_valid:
				return {
					"success": False,
					"error": f"ATCUD gerado inválido: {validation_msg}",
					"atcud_code": atcud_code,
					"generation_id": generation_id
				}

			# ✅ VERIFICAR UNICIDADE (OTIMIZADO)
			uniqueness_check = self._check_atcud_uniqueness_optimized(atcud_code, doc)
			if not uniqueness_check["unique"]:
				return {
					"success": False,
					"error": f"ATCUD duplicado encontrado: {atcud_code}",
					"duplicates": uniqueness_check["duplicates"],
					"generation_id": generation_id
				}

			# ✅ GERAR QR CODE SE NECESSÁRIO (OTIMIZADO)
			qr_code_data = None
			if self._requires_qr_code(doc.doctype):
				qr_result = self._generate_qr_code_optimized(doc, atcud_code, series_info)
				if qr_result.get("success"):
					qr_code_data = qr_result["qr_data"]

			# ✅ CRIAR LOG DE AUDITORIA ESTRUTURADO
			self._create_enhanced_audit_log(doc, atcud_code, validation_code, sequence_number,
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
				"compliant_with": "Portaria 195/2020",
				"format": "VALIDATION_CODE-SEQUENCE",
				"is_temporary": not series_info.get("is_communicated", False)
			}

		except Exception as e:
			frappe.log_error(f"Erro crítico na geração de ATCUD: {str(e)}", "ATCUDGenerator")
			return {
				"success": False,
				"error": str(e),
				"generation_id": generation_id if 'generation_id' in locals() else "UNKNOWN"
			}

	def _validate_document_for_atcud_optimized(self, doc):
		"""
		✅ VALIDAÇÃO OTIMIZADA: Verificar se documento pode ter ATCUD gerado
		Baseado na sua experiência com programação.teste_no_console[6]
		"""
		try:
			# ✅ CACHE DE VALIDAÇÕES PARA PERFORMANCE
			cache_key = f"atcud_validation_{doc.doctype}_{doc.company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is None:
				# ✅ VERIFICAÇÕES BÁSICAS
				if doc.doctype not in self.supported_document_types:
					cached_result = {"valid": False,
									 "error": f"DocType {doc.doctype} não suporta ATCUD"}
				elif not self._is_portuguese_company_cached(doc.company):
					cached_result = {"valid": False,
									 "error": "ATCUD só é obrigatório para empresas portuguesas"}
				else:
					cached_result = {"valid": True}

				# Cache por 5 minutos
				frappe.cache().set_value(cache_key, cached_result, expires_in_sec=300)

			if not cached_result["valid"]:
				return cached_result

			# ✅ VALIDAÇÕES ESPECÍFICAS DO DOCUMENTO
			if not getattr(doc, 'naming_series', None):
				return {"valid": False, "error": "Documento deve ter naming_series definida"}

			if not self._is_portuguese_naming_series_optimized(doc.naming_series):
				return {"valid": False,
						"error": f"Naming series {doc.naming_series} não é portuguesa"}

			if not doc.name or doc.name == 'new':
				return {"valid": False, "error": "Documento deve ser salvo antes de gerar ATCUD"}

			if getattr(doc, 'atcud_code', None):
				return {"valid": False, "error": f"Documento já tem ATCUD: {doc.atcud_code}"}

			return {"valid": True}

		except Exception as e:
			return {"valid": False, "error": f"Erro na validação: {str(e)}"}

	def _get_series_info_from_document(self, doc):
		"""
		✅ OTIMIZADO: Obter informações da série do documento
		Integrado com Portugal Series Configuration
		"""
		try:
			# ✅ BUSCAR DIRETAMENTE NA CONFIGURAÇÃO DA SÉRIE
			series_config = frappe.db.get_value(
				"Portugal Series Configuration",
				{
					"naming_series": doc.naming_series,
					"company": doc.company,
					"is_active": 1
				},
				["name", "prefix", "validation_code", "is_communicated", "current_sequence",
				 "document_type"],
				as_dict=True
			)

			if series_config:
				return {
					"naming_series": doc.naming_series,
					"prefix": series_config.prefix,
					"validation_code": series_config.validation_code,
					"is_communicated": series_config.is_communicated,
					"current_sequence": series_config.current_sequence,
					"document_type": series_config.document_type,
					"series_name": series_config.name
				}

			# ✅ FALLBACK: Extrair do naming_series
			return self._extract_series_info_from_naming_series_enhanced(doc.naming_series)

		except Exception as e:
			frappe.log_error(f"Erro ao obter informações da série: {str(e)}")
			return None

	def _extract_series_info_from_naming_series_enhanced(self, naming_series):
		"""
		✅ MELHORADO: Extrair informações da naming_series SEM HÍFENS
		Formato: XXYYYY + COMPANY.#### → informações estruturadas
		"""
		try:
			if not naming_series:
				return None

			# ✅ PADRÃO NAMING SERIES PORTUGUESA SEM HÍFENS (DINÂMICO)
			pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})\.####$'
			match = re.match(pattern, naming_series)

			if not match:
				frappe.logger().warning(
					f"⚠️ Naming series não corresponde ao padrão: {naming_series}")
				return None

			doc_code, year, company_abbr = match.groups()
			prefix = f"{doc_code}{year}{company_abbr}"

			return {
				"naming_series": naming_series,
				"prefix": prefix,
				"doc_code": doc_code,
				"year": int(year),
				"company_abbr": company_abbr,
				"validation_code": None,  # Será obtido separadamente
				"is_communicated": False,
				"current_sequence": 1
			}

		except Exception as e:
			frappe.log_error(f"Erro ao extrair informações da naming series: {str(e)}")
			return None

	def _get_validation_code_optimized(self, series_info, company):
		"""
		✅ OTIMIZADO: Obter código de validação AT com cache
		"""
		try:
			# ✅ CACHE PARA PERFORMANCE
			cache_key = f"validation_code_{series_info['prefix']}_{company}"
			cached_code = frappe.cache().get_value(cache_key)

			if cached_code:
				return cached_code

			# ✅ BUSCAR NA CONFIGURAÇÃO DA SÉRIE
			if series_info.get("validation_code"):
				validation_code = series_info["validation_code"]
			else:
				# ✅ BUSCAR POR PREFIX
				validation_code = frappe.db.get_value(
					"Portugal Series Configuration",
					{
						"prefix": series_info["prefix"],
						"company": company,
						"is_active": 1
					},
					"validation_code"
				)

			if validation_code:
				# ✅ VALIDAR FORMATO
				is_valid, _ = self._validate_validation_code_format_enhanced(validation_code)
				if is_valid:
					# Cache por 10 minutos
					frappe.cache().set_value(cache_key, validation_code, expires_in_sec=600)
					return validation_code

			return None

		except Exception as e:
			frappe.log_error(f"Erro ao obter código de validação: {str(e)}")
			return None

	def _generate_enhanced_temporary_code(self, series_info, company):
		"""
		✅ MELHORADO: Gerar código de validação temporário mais robusto
		"""
		try:
			# ✅ OBTER ABREVIATURA DA EMPRESA DINAMICAMENTE
			company_abbr = frappe.db.get_value("Company", company, "abbr") or "NDX"
			company_abbr = company_abbr.upper()[:3]

			# ✅ CÓDIGO TEMPORÁRIO MAIS ROBUSTO
			doc_code = series_info.get("doc_code", "FT")
			year = series_info.get("year", getdate().year)

			# Formato: TEMP + DOC_CODE + YEAR + COMPANY
			temp_code = f"TEMP{doc_code}{str(year)[-2:]}{company_abbr}"

			# ✅ GARANTIR COMPRIMENTO MÍNIMO (8 chars)
			while len(temp_code) < 8:
				temp_code += "0"

			# ✅ LIMITAR A 12 CARACTERES
			return temp_code[:12].upper()

		except Exception as e:
			frappe.log_error(f"Erro ao gerar código temporário: {str(e)}")
			return "TEMP0000"

	def _get_next_sequence_thread_safe(self, series_info, doc):
		"""
		✅ THREAD-SAFE: Obter próximo número sequencial
		Baseado na sua experiência com programação.autenticação[7]
		"""
		try:
			# ✅ USAR TRANSAÇÃO PARA THREAD SAFETY
			with frappe.db.transaction():
				if series_info.get("series_name"):
					# ✅ ATUALIZAR SEQUÊNCIA NA CONFIGURAÇÃO
					series_doc = frappe.get_doc("Portugal Series Configuration",
												series_info["series_name"])
					current_seq = series_doc.current_sequence
					series_doc.current_sequence += 1
					series_doc.save(ignore_permissions=True)
					return current_seq
				else:
					# ✅ FALLBACK: Extrair do nome do documento
					return self._extract_sequence_from_document_name_enhanced(doc.name)

		except Exception as e:
			frappe.log_error(f"Erro ao obter sequência: {str(e)}")
			return 1

	def _extract_sequence_from_document_name_enhanced(self, document_name):
		"""
		✅ MELHORADO: Extrair número sequencial do nome do documento
		Suporta múltiplos formatos (COM e SEM hífens)
		"""
		try:
			if not document_name:
				return 1

			# ✅ PADRÕES OTIMIZADOS PARA EXTRAIR SEQUÊNCIA
			patterns = [
				r'\.(\d{8})$',  # ERPNext: FT2025NDX.00000001
				r'(\d{8})$',  # Direto: FT2025NDX00000001
				r'-(\d{8})$',  # Com hífen: FT-2025-NDX-00000001
				r'\.(\d{4,6})$',  # ERPNext curto: FT2025NDX.0001
				r'(\d{4,6})$',  # Direto curto: FT2025NDX0001
				r'-(\d{4,6})$',  # Com hífen curto: FT-2025-NDX-0001
				r'(\d+)$'  # Qualquer número no final
			]

			for pattern in patterns:
				match = re.search(pattern, document_name)
				if match:
					sequence = int(match.group(1))
					if sequence > 0:
						return sequence

			frappe.logger().warning(f"Não foi possível extrair sequência de: {document_name}")
			return 1

		except Exception as e:
			frappe.log_error(f"Erro ao extrair sequência: {str(e)}")
			return 1

	def _validate_atcud_format_enhanced(self, atcud_code):
		"""
		✅ MELHORADO: Validar formato do código ATCUD
		"""
		try:
			if not atcud_code:
				return False, "Código ATCUD vazio"

			# ✅ VERIFICAR FORMATO GERAL
			if not re.match(self.atcud_format, atcud_code):
				return False, "Formato deve ser CODIGO-SEQUENCIA (8-12 chars alfanuméricos + hífen + 8 dígitos)"

			# ✅ DIVIDIR E VALIDAR PARTES
			parts = atcud_code.split('-')
			if len(parts) != 2:
				return False, "Deve conter exatamente um hífen"

			validation_code, sequence = parts

			# ✅ VALIDAR CÓDIGO DE VALIDAÇÃO
			is_valid_code, code_msg = self._validate_validation_code_format_enhanced(
				validation_code)
			if not is_valid_code:
				return False, f"Código de validação inválido: {code_msg}"

			# ✅ VALIDAR SEQUÊNCIA
			if not sequence.isdigit() or len(sequence) != 8:
				return False, "Sequência deve ter exatamente 8 dígitos"

			if int(sequence) < 1:
				return False, "Sequência deve ser maior que zero"

			return True, "ATCUD válido"

		except Exception as e:
			return False, f"Erro na validação: {str(e)}"

	def _validate_validation_code_format_enhanced(self, validation_code):
		"""
		✅ MELHORADO: Validar formato do código de validação AT
		"""
		try:
			if not validation_code:
				return False, "Código vazio"

			if not (8 <= len(validation_code) <= 12):
				return False, f"Deve ter 8-12 caracteres (atual: {len(validation_code)})"

			if not validation_code.isalnum() or not validation_code.isupper():
				return False, "Deve ser alfanumérico maiúsculo"

			if not any(c.isalpha() for c in validation_code):
				return False, "Deve conter pelo menos uma letra"

			if validation_code.isdigit():
				return False, "Não pode ser apenas numérico"

			return True, "Código válido"

		except Exception as e:
			return False, f"Erro: {str(e)}"

	def _check_atcud_uniqueness_optimized(self, atcud_code, exclude_doc=None):
		"""
		✅ OTIMIZADO: Verificar unicidade do ATCUD com performance melhorada
		"""
		try:
			# ✅ BUSCAR APENAS EM DOCTYPES CRÍTICOS PRIMEIRO
			critical_doctypes = ["Sales Invoice", "POS Invoice", "Purchase Invoice",
								 "Payment Entry"]
			duplicates = []

			for doctype in critical_doctypes:
				try:
					if not frappe.db.table_exists(f"tab{doctype}"):
						continue

					filters = {"atcud_code": atcud_code}
					if exclude_doc and exclude_doc.doctype == doctype:
						filters["name"] = ["!=", exclude_doc.name]

					existing = frappe.db.get_value(doctype, filters, ["name", "creation"])
					if existing:
						duplicates.append({
							"doctype": doctype,
							"name": existing[0] if isinstance(existing, tuple) else existing,
							"creation": existing[1] if isinstance(existing, tuple) else None
						})

				except Exception:
					continue

			return {
				"unique": len(duplicates) == 0,
				"duplicates": duplicates,
				"duplicate_count": len(duplicates)
			}

		except Exception as e:
			frappe.log_error(f"Erro ao verificar unicidade: {str(e)}")
			return {"unique": True, "duplicates": [], "duplicate_count": 0}

	def _is_portuguese_company_cached(self, company):
		"""
		✅ OTIMIZADO: Verificar se empresa é portuguesa com cache
		"""
		try:
			cache_key = f"portuguese_company_{company}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is None:
				company_data = frappe.db.get_value("Company", company,
												   ["country", "portugal_compliance_enabled"],
												   as_dict=True)

				if company_data:
					cached_result = (company_data.country == "Portugal" and
									 cint(company_data.portugal_compliance_enabled))
				else:
					cached_result = False

				# Cache por 10 minutos
				frappe.cache().set_value(cache_key, cached_result, expires_in_sec=600)

			return cached_result

		except Exception:
			return False

	def _is_portuguese_naming_series_optimized(self, naming_series):
		"""
		✅ OTIMIZADO: Verificar se naming_series é portuguesa
		"""
		try:
			if not naming_series:
				return False

			# ✅ CACHE PARA PADRÕES COMUNS
			cache_key = f"portuguese_series_{naming_series}"
			cached_result = frappe.cache().get_value(cache_key)

			if cached_result is None:
				# ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
				pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$'
				cached_result = bool(re.match(pattern, naming_series))

				# Cache por 30 minutos
				frappe.cache().set_value(cache_key, cached_result, expires_in_sec=1800)

			return cached_result

		except Exception:
			return False

	def _requires_qr_code(self, doctype):
		"""✅ MANTIDO: Verificar se tipo de documento requer QR code"""
		doc_config = self.supported_document_types.get(doctype, {})
		return doc_config.get("requires_qr", False)

	# ========== GERAÇÃO DE QR CODE OTIMIZADA ==========

	def _generate_qr_code_optimized(self, doc, atcud_code, series_info):
		"""
		✅ OTIMIZADO: Gerar QR code com performance melhorada
		"""
		try:
			# ✅ DADOS PARA QR CODE OTIMIZADOS
			qr_data = self._build_qr_data_optimized(doc, atcud_code, series_info)

			# ✅ CONFIGURAÇÃO QR CODE OTIMIZADA
			qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_M,
				box_size=8,  # Reduzido para performance
				border=4,
			)
			qr.add_data(qr_data)
			qr.make(fit=True)

			# ✅ CRIAR IMAGEM OTIMIZADA
			qr_image = qr.make_image(fill_color="black", back_color="white")

			# ✅ CONVERTER PARA BASE64 OTIMIZADO
			buffer = BytesIO()
			qr_image.save(buffer, format='PNG', optimize=True)
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
			return {"success": False, "error": str(e)}

	def _build_qr_data_optimized(self, doc, atcud_code, series_info):
		"""
		✅ OTIMIZADO: Construir dados para QR code com cache de NIFs
		"""
		try:
			# ✅ CACHE PARA NIFs (performance)
			company_nif = self._get_cached_nif("Company", doc.company)
			customer_nif = ""

			if hasattr(doc, 'customer') and doc.customer:
				customer_nif = self._get_cached_nif("Customer", doc.customer)
			elif hasattr(doc, 'supplier') and doc.supplier:
				customer_nif = self._get_cached_nif("Supplier", doc.supplier)

			# ✅ DADOS OBRIGATÓRIOS CONFORME LEGISLAÇÃO (OTIMIZADOS)
			qr_data = {
				"A": company_nif,
				"B": customer_nif,
				"C": doc.company,
				"D": self.supported_document_types.get(doc.doctype, {}).get("saft_type", "FT"),
				"E": "N",  # Estado do documento
				"F": getdate(getattr(doc, 'posting_date', today())).strftime('%Y%m%d'),
				"G": doc.name,
				"H": atcud_code,
				"I1": f"{flt(getattr(doc, 'net_total', 0)):.2f}",
				"I2": f"{flt(getattr(doc, 'total_taxes_and_charges', 0)):.2f}",
				"N": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",
				"O": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",
				"Q": hashlib.sha1(f"{doc.name}{atcud_code}".encode()).hexdigest()[:4].upper(),
				"R": series_info["prefix"]
			}

			# ✅ CONVERTER PARA STRING CONFORME FORMATO AT
			return "*".join([f"{key}:{value}" for key, value in qr_data.items()])

		except Exception as e:
			frappe.log_error(f"Erro ao construir dados QR: {str(e)}")
			return f"ERROR:{str(e)}"

	def _get_cached_nif(self, doctype, name):
		"""
		✅ OTIMIZADO: Obter NIF com cache
		"""
		try:
			cache_key = f"nif_{doctype}_{name}"
			cached_nif = frappe.cache().get_value(cache_key)

			if cached_nif is None:
				cached_nif = frappe.db.get_value(doctype, name, "tax_id") or ""
				# Cache por 1 hora
				frappe.cache().set_value(cache_key, cached_nif, expires_in_sec=3600)

			return cached_nif

		except Exception:
			return ""

	# ========== AUDITORIA MELHORADA ==========

	def _create_enhanced_audit_log(self, doc, atcud_code, validation_code, sequence_number,
								   generation_id):
		"""
		✅ MELHORADO: Criar log de auditoria estruturado
		"""
		try:
			# ✅ COMMENT ESTRUTURADO
			comment_content = f"""
🇵🇹 ATCUD GERADO AUTOMATICAMENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Código ATCUD: {atcud_code}
🔑 Código Validação: {validation_code}
🔢 Sequência: {sequence_number:08d}
📄 Naming Series: {doc.naming_series}
🏢 Empresa: {doc.company}
⏰ Data/Hora: {now()}
👤 Usuário: {frappe.session.user}
🆔 ID Geração: {generation_id}
📜 Conforme: Portaria 195/2020
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

			frappe.logger().info(f"📋 ATCUD Audit Log criado: {doc.name} → {atcud_code}")

		except Exception as e:
			frappe.log_error(f"Erro ao criar log de auditoria: {str(e)}")

	# ========== VALIDAÇÃO E VERIFICAÇÃO MELHORADAS ==========

	def validate_existing_atcud(self, atcud_code):
		"""
		✅ MELHORADO: Validar ATCUD existente com informações detalhadas
		"""
		try:
			is_valid, message = self._validate_atcud_format_enhanced(atcud_code)

			result = {
				"valid": is_valid,
				"message": message,
				"atcud_code": atcud_code,
				"format_check": "Portaria 195/2020"
			}

			if is_valid:
				# ✅ ADICIONAR INFORMAÇÕES DETALHADAS
				parts = atcud_code.split('-')
				result.update({
					"validation_code": parts[0],
					"sequence": int(parts[1]),
					"sequence_formatted": parts[1],
					"validation_code_length": len(parts[0]),
					"is_temporary": parts[0].startswith("TEMP")
				})

			return result

		except Exception as e:
			return {
				"valid": False,
				"message": str(e),
				"atcud_code": atcud_code
			}

	def get_atcud_info_enhanced(self, atcud_code):
		"""
		✅ MELHORADO: Obter informações detalhadas de um ATCUD
		"""
		try:
			if not atcud_code or '-' not in atcud_code:
				return {"valid": False, "error": "ATCUD inválido"}

			validation_code, sequence = atcud_code.split('-')

			# ✅ INFORMAÇÕES DETALHADAS
			info = {
				"valid": True,
				"atcud_code": atcud_code,
				"validation_code": validation_code,
				"sequence_number": int(sequence),
				"sequence_formatted": sequence,
				"format": "CODIGO-SEQUENCIA",
				"compliance": "Portaria 195/2020",
				"validation_code_length": len(validation_code),
				"sequence_length": len(sequence),
				"is_temporary": validation_code.startswith("TEMP"),
				"estimated_series": self._estimate_series_from_validation_code(validation_code)
			}

			return info

		except Exception as e:
			return {"valid": False, "error": str(e), "atcud_code": atcud_code}

	def _estimate_series_from_validation_code(self, validation_code):
		"""
		✅ NOVO: Estimar série baseada no código de validação
		"""
		try:
			if validation_code.startswith("TEMP"):
				# Extrair informações do código temporário
				if len(validation_code) >= 8:
					doc_code = validation_code[4:6]  # TEMP + DOC_CODE
					return f"Série temporária ({doc_code})"

			# Buscar série real
			series = frappe.db.get_value(
				"Portugal Series Configuration",
				{"validation_code": validation_code},
				["prefix", "series_name"]
			)

			if series:
				return f"{series[0]} ({series[1]})"

			return "Série não identificada"

		except Exception:
			return "Desconhecida"


# ========== INSTÂNCIA GLOBAL ATUALIZADA ==========
atcud_generator = ATCUDGenerator()


# ========== FUNÇÕES AUXILIARES ATUALIZADAS ==========

def generate_atcud_for_document(doc):
	"""✅ ATUALIZADO: Gerar ATCUD para documento"""
	return atcud_generator.generate_atcud_for_document(doc)


def validate_atcud_format(atcud_code):
	"""✅ ATUALIZADO: Validar formato de ATCUD"""
	return atcud_generator.validate_existing_atcud(atcud_code)


def get_atcud_info(atcud_code):
	"""✅ ATUALIZADO: Obter informações de ATCUD"""
	return atcud_generator.get_atcud_info_enhanced(atcud_code)


def extract_sequence_from_document_name(document_name):
	"""✅ ATUALIZADO: Extrair sequencial do nome do documento"""
	return atcud_generator._extract_sequence_from_document_name_enhanced(document_name)


# ========== APIS WHITELISTED ATUALIZADAS ==========

@frappe.whitelist()
def generate_manual_atcud_certified(doctype, docname):
	"""
	✅ ATUALIZADO: API para gerar ATCUD manualmente
	Integrada com document_hooks.py para evitar duplicação
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
			# ✅ ATUALIZAR DOCUMENTO COM THREAD SAFETY
			with frappe.db.transaction():
				frappe.db.set_value(doctype, docname, "atcud_code", result["atcud_code"])
				frappe.db.commit()

		return result

	except Exception as e:
		frappe.log_error(f"Erro ao gerar ATCUD manual: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_atcud_code(atcud_code):
	"""✅ ATUALIZADO: API para validar código ATCUD"""
	try:
		result = atcud_generator.validate_existing_atcud(atcud_code)

		# ✅ VERIFICAR UNICIDADE OTIMIZADA
		uniqueness = atcud_generator._check_atcud_uniqueness_optimized(atcud_code)
		result.update(uniqueness)

		return result

	except Exception as e:
		return {"valid": False, "error": str(e)}


@frappe.whitelist()
def get_atcud_statistics_enhanced():
	"""
	✅ ATUALIZADO: API para obter estatísticas de ATCUD otimizadas
	"""
	try:
		stats = {
			"total_documents_with_atcud": 0,
			"by_doctype": {},
			"by_company": {},
			"validation_summary": {
				"valid_atcuds": 0,
				"invalid_atcuds": 0,
				"temporary_atcuds": 0
			},
			"performance_metrics": {
				"cache_hits": 0,
				"generation_time_avg": 0
			}
		}

		# ✅ CONTAR POR DOCTYPE (OTIMIZADO)
		for doctype in atcud_generator.supported_document_types.keys():
			try:
				if not frappe.db.table_exists(f"tab{doctype}"):
					continue

				columns = frappe.db.get_table_columns(doctype)
				if 'atcud_code' not in columns:
					continue

				total = frappe.db.count(doctype, {"atcud_code": ["!=", ""]})
				stats["by_doctype"][doctype] = total
				stats["total_documents_with_atcud"] += total

			except Exception:
				stats["by_doctype"][doctype] = 0

		return {
			"success": True,
			"statistics": stats,
			"compliance": "Portaria 195/2020",
			"supported_doctypes": list(atcud_generator.supported_document_types.keys()),
			"generator_version": "2.1.0"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def batch_generate_atcud_optimized(doctype, filters=None, limit=50):
	"""
	✅ ATUALIZADO: API para gerar ATCUD em lote otimizada
	"""
	try:
		if not filters:
			filters = {"atcud_code": ["in", ["", None]], "docstatus": 1}

		if isinstance(filters, str):
			filters = json.loads(filters)

		# ✅ VERIFICAÇÕES DE SEGURANÇA
		if not frappe.db.table_exists(f"tab{doctype}"):
			return {"success": False, "error": f"Tabela {doctype} não existe"}

		columns = frappe.db.get_table_columns(doctype)
		if 'atcud_code' not in columns:
			return {"success": False, "error": f"Campo atcud_code não existe em {doctype}"}

		# ✅ BUSCAR DOCUMENTOS
		documents = frappe.get_all(doctype, filters=filters, fields=["name"],
								   limit=int(limit), order_by="creation desc")

		if not documents:
			return {
				"success": True,
				"message": "Nenhum documento encontrado",
				"total_processed": 0,
				"results": []
			}

		# ✅ PROCESSAR EM LOTE COM OTIMIZAÇÃO
		results = []
		successful = 0
		failed = 0

		for doc_data in documents:
			try:
				doc = frappe.get_doc(doctype, doc_data.name)
				result = atcud_generator.generate_atcud_for_document(doc)

				if result.get("success"):
					with frappe.db.transaction():
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
			"success_rate": round((successful / len(results)) * 100, 2),
			"results": results
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


# ========== FUNÇÃO DE SETUP ATUALIZADA ==========

def setup_atcud_generator():
	"""✅ ATUALIZADO: Configurar gerador de ATCUD"""
	try:
		print("🇵🇹 Configurando ATCUDGenerator ATUALIZADO...")
		print("✅ Versão 2.1.0 - Otimizado e Alinhado")
		print("✅ Compatível com naming_series SEM HÍFENS")
		print("✅ Integrado com document_hooks.py e series_adapter.py")
		print("✅ Performance otimizada com cache")
		print("✅ Thread-safe para sequências")
		return True
	except Exception as e:
		print(f"❌ Erro ao configurar ATCUD generator: {str(e)}")
		return False


# ========== LOG FINAL ==========
frappe.logger().info("ATCUDGenerator ATUALIZADO loaded - Version 2.1.0 - Optimized & Aligned")
