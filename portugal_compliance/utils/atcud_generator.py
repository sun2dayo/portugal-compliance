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
		self.atcud_format = r'^[A-Z0-9]{8,12}-\d{1,12}$'  # CODIGO-SEQUENCIA (sequencia = largura real do documento, sem minimo de digitos fixo pela AT)
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
			# String que preserva a largura original do numero do documento
			# (ex: "0001") - usada no ATCUD em vez do inteiro reformatado.
			sequence_display = self._extract_sequence_string_from_document_name(doc.name)

			# ✅ GERAR ATCUD CONFORME FORMATO OFICIAL (sequencia = numero real
			# do documento, sem padding artificial - ver exemplos reais de
			# mercado no commit que introduziu esta correcao)
			atcud_code = f"{validation_code}-{sequence_display}"

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

			# ✅ ASSINATURA DIGITAL RSA-SHA1 + CADEIA DE HASH (antes do QR:
			# o campo Q do QR depende do resultado da assinatura)
			signature_result = None
			try:
				from portugal_compliance.utils.signature import sign_document, SignatureError
				signature_result = sign_document(
					doc,
					series_prefix=series_info["prefix"],
					series_configuration=series_info.get("series_name"),
					sequence_number=sequence_number,
				)
			except SignatureError as e:
				frappe.log_error(f"Assinatura digital nao disponivel: {str(e)}", "ATCUDGenerator")
			except Exception as e:
				frappe.log_error(f"Erro inesperado na assinatura digital: {str(e)}", "ATCUDGenerator")

			# ✅ GERAR QR CODE SE NECESSÁRIO (OTIMIZADO)
			qr_code_data = None
			if self._requires_qr_code(doc.doctype):
				qr_result = self._generate_qr_code_optimized(doc, atcud_code, series_info, signature_result)
				if qr_result.get("success"):
					qr_code_data = qr_result["qr_data"]

			# NOTA: o ATCUD Log so e escrito em after_insert
			# (ver document_hooks.generate_atcud_after_insert), nunca aqui.
			# Esta funcao corre tipicamente em before_save, antes do
			# documento existir de facto na BD - o ATCUD Log tem uma
			# Dynamic Link para o documento, que falha a validacao se o
			# documento ainda nao foi commitado (db_insert so acontece
			# depois de before_save no ciclo de vida do Frappe).
			doc._portugal_atcud_pending_log = {
				"atcud_code": atcud_code,
				"validation_code": validation_code,
				"sequence_number": sequence_number,
				"generation_id": generation_id,
				"series_info": series_info,
				"signature_result": signature_result,
				"qr_code_data": qr_code_data,
			}

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
				"signature_hash": signature_result["signature_hash"] if signature_result else None,
				"signature_hash_control": signature_result["hash_control"] if signature_result else None,
				"generation_id": generation_id,
				"generation_date": now(),
				"compliant_with": "Portaria 195/2020 e Portaria 363/2010",
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
			pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{1,4})\.####$'
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

	def _extract_sequence_string_from_document_name(self, document_name):
		"""
		Extrai a sequencia do nome do documento como STRING, preservando
		a largura/padding original (ex: "0001", nao o inteiro 1) - o
		ATCUD deve mostrar exatamente os mesmos digitos que o proprio
		numero do documento, sem reformatar para uma largura fixa
		(confirmado contra exemplos reais de mercado: Cegid Vendus usa
		5 digitos, InvoiceXpress usa 7 - nao existe uma largura fixa
		exigida pela AT, o ATCUD so espelha o numero real do documento).
		"""
		if not document_name:
			return "1"
		patterns = [r'\.(\d+)$', r'-(\d+)$', r'(\d+)$']
		for pattern in patterns:
			match = re.search(pattern, document_name)
			if match:
				return match.group(1)
		return "1"

	def _get_next_sequence_thread_safe(self, series_info, doc):
		"""
		A sequência do ATCUD é sempre extraída de doc.name, nunca de um
		contador próprio. doc.name já foi atribuído pelo motor nativo de
		naming_series do Frappe (tabela tabSeries) no momento do insert,
		antes deste hook correr - é a única fonte de verdade para "qual é
		o número real deste documento na sua série".

		Manter um contador paralelo (como fazia a versão anterior, via
		Portugal Series Configuration.current_sequence) permite que o
		número do ATCUD e o número real do documento dessincronizem -
		ex: um documento cancelado antes de submeter incrementa o
		contador nativo do Frappe mas não necessariamente o contador
		próprio, ou vice-versa numa condição de corrida.

		current_sequence em Portugal Series Configuration é mantido só
		como campo informativo (ver _update_series_display_sequence),
		nunca como fonte de cálculo.
		"""
		sequence = self._extract_sequence_from_document_name_enhanced(doc.name)

		if series_info.get("series_name"):
			self._update_series_display_sequence(series_info["series_name"], sequence, doc)

		return sequence

	def _update_series_display_sequence(self, series_name, sequence, doc):
		"""
		Atualiza current_sequence em Portugal Series Configuration como
		valor informativo para a UI (ex: "próxima sequência prevista").
		Nunca deve ser lido de volta para calcular um ATCUD - ver
		_get_next_sequence_thread_safe.
		"""
		try:
			frappe.db.set_value(
				"Portugal Series Configuration",
				series_name,
				{
					"current_sequence": sequence + 1,
					"total_documents_issued": sequence,
					"last_document_date": frappe.utils.nowdate(),
					"last_document_name": doc.name,
				},
				update_modified=False,
			)
		except Exception as e:
			# Informativo apenas - uma falha aqui nunca deve impedir a
			# geracao do ATCUD, que ja tem o numero certo em `sequence`.
			frappe.log_error(f"Erro ao atualizar sequência informativa: {str(e)}")

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

			# ✅ VALIDAR SEQUÊNCIA (largura variável - espelha o número real
			# do documento, não uma largura fixa imposta pela AT)
			if not sequence.isdigit() or not (1 <= len(sequence) <= 12):
				return False, "Sequência deve ter entre 1 e 12 dígitos"

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
				pattern = r'^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}\.####$'
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

	def _generate_qr_code_optimized(self, doc, atcud_code, series_info, signature_result=None):
		"""
		Gerar imagem do QR code a partir da string de dados construida
		por _build_qr_data_optimized (que agora recebe o resultado da
		assinatura digital para o campo Q).
		"""
		try:
			qr_data = self._build_qr_data_optimized(doc, atcud_code, series_info, signature_result)

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

	def _build_qr_data_optimized(self, doc, atcud_code, series_info, signature_result=None):
		"""
		Construir a string de dados do QR code conforme a Portaria
		195/2020. Campos corrigidos nesta fase (estavam errados desde a
		versao anterior - ver auditoria):

		  C - pais do ADQUIRENTE (ISO 3166-1), nao o nome da empresa
		  E - estado real do documento (N/A/S), nao fixo em "N"
		  N - total de IMPOSTO isolado, nao duplicado do total geral
		  Q - 4 caracteres da assinatura digital real (posicoes 1/11/21/31),
		      nao um hash arbitrario sem relacao com o documento
		  R - numero de certificado do software, nao o prefixo da serie
		"""
		try:
			company_nif = self._get_cached_nif("Company", doc.company)
			customer_nif = ""
			customer_country = "PT"

			if hasattr(doc, 'customer') and doc.customer:
				customer_nif = self._get_cached_nif("Customer", doc.customer)
				customer_country = self._get_party_country("Customer", doc.customer)
			elif hasattr(doc, 'supplier') and doc.supplier:
				customer_nif = self._get_cached_nif("Supplier", doc.supplier)
				customer_country = self._get_party_country("Supplier", doc.supplier)

			if not customer_nif:
				customer_nif = "999999990"  # Consumidor final, conforme especificacao

			tax_breakdown = self._get_qr_tax_breakdown(doc)

			certificate_number = frappe.db.get_single_value(
				"Portugal Auth Settings", "software_certificate_number"
			) or "0"

			if signature_result and signature_result.get("hash_control"):
				hash_control = signature_result["hash_control"]
			else:
				# Sem assinatura configurada ainda: nao inventar um hash -
				# deixar vazio e visivel como incompleto, em vez de um
				# valor que parece uma assinatura real sem o ser.
				hash_control = ""

			qr_data = {
				"A": company_nif,
				"B": customer_nif,
				"C": self._normalize_country_code(customer_country),
				"D": self.supported_document_types.get(doc.doctype, {}).get("saft_type", "FT"),
				"E": self._get_document_status_code(doc),
				"F": getdate(getattr(doc, 'posting_date', today())).strftime('%Y%m%d'),
				"G": f"{self.supported_document_types.get(doc.doctype, {}).get('saft_type', 'FT')} {series_info['prefix']}/{doc.name}",
				"H": atcud_code,
				**tax_breakdown,
				"N": f"{flt(tax_breakdown.get('_total_tax', 0)):.2f}",
				"O": f"{flt(getattr(doc, 'grand_total', 0)):.2f}",
				"Q": hash_control,
				"R": str(certificate_number),
			}
			qr_data.pop("_total_tax", None)

			return "*".join([f"{key}:{value}" for key, value in qr_data.items() if value != ""])

		except Exception as e:
			frappe.log_error(f"Erro ao construir dados QR: {str(e)}")
			return f"ERROR:{str(e)}"

	def _get_party_country(self, doctype, name):
		"""
		Pais do cliente/fornecedor via o endereco default (padrao
		correto do ERPNext - Customer/Supplier nao tem campo pais
		proprio, vive no endereco ligado via Dynamic Link).
		"""
		try:
			from frappe.contacts.doctype.address.address import get_default_address
			address_name = get_default_address(doctype, name)
			if address_name:
				country = frappe.db.get_value("Address", address_name, "country")
				if country:
					return country
		except Exception:
			pass
		return "Portugal"

	def _normalize_country_code(self, country):
		"""Converte nome de pais do Frappe (ex: 'Portugal') para ISO 3166-1 alpha-2."""
		if not country:
			return "PT"
		if len(country) == 2:
			return country.upper()
		code = frappe.db.get_value("Country", country, "code")
		return code.upper() if code else "PT"

	def _get_document_status_code(self, doc):
		"""N Normal, A Anulado, S Autofaturacao - conforme especificacao do QR."""
		if getattr(doc, "docstatus", 1) == 2:
			return "A"
		if getattr(doc, "is_return", 0):
			return "A"
		if getattr(doc, "custom_is_self_billing", 0):
			return "S"
		return "N"

	def _get_qr_tax_breakdown(self, doc):
		"""
		Agrega os totais tributaveis por taxa de IVA (campos I isento,
		J reduzida, K intermedia, L normal) e devolve tambem o total de
		imposto isolado (campo N, via chave interna _total_tax).
		Le a taxa efetiva de cada linha via item_tax_template /
		Sales Taxes and Charges, em vez de assumir uma taxa fixa.
		"""
		buckets = {"I": 0.0, "J": 0.0, "K": 0.0, "L": 0.0}
		total_tax = 0.0

		items = getattr(doc, "items", None) or []
		tax_rows = getattr(doc, "taxes", None) or []
		total_taxable = sum(flt(getattr(item, "net_amount", 0) or getattr(item, "amount", 0)) for item in items) or flt(getattr(doc, "net_total", 0))
		total_tax = flt(getattr(doc, "total_taxes_and_charges", 0))

		if not items:
			buckets["L"] = flt(getattr(doc, "net_total", 0))
			return {"I": f"{buckets['I']:.2f}", "J": f"{buckets['J']:.2f}", "K": f"{buckets['K']:.2f}", "L": f"{buckets['L']:.2f}", "_total_tax": total_tax}

		for item in items:
			rate = self._get_item_effective_tax_rate(item, tax_rows)
			taxable_amount = flt(getattr(item, "net_amount", None) if getattr(item, "net_amount", None) is not None else getattr(item, "amount", 0))

			if rate <= 0:
				buckets["I"] += taxable_amount
			elif rate < 10:
				buckets["J"] += taxable_amount
			elif rate < 20:
				buckets["K"] += taxable_amount
			else:
				buckets["L"] += taxable_amount

		return {
			"I": f"{buckets['I']:.2f}",
			"J": f"{buckets['J']:.2f}",
			"K": f"{buckets['K']:.2f}",
			"L": f"{buckets['L']:.2f}",
			"_total_tax": total_tax,
		}

	def _get_item_effective_tax_rate(self, item, tax_rows):
		"""
		Obtem a taxa de IVA efetiva de uma linha. Prioridade:
		1. item_tax_rate (JSON por conta fiscal, campo nativo do ERPNext)
		2. taxa da primeira linha de Sales/Purchase Taxes and Charges
		   aplicavel (fallback quando o item nao tem override proprio)
		"""
		item_tax_rate = getattr(item, "item_tax_rate", None)
		if item_tax_rate:
			try:
				rates = json.loads(item_tax_rate) if isinstance(item_tax_rate, str) else item_tax_rate
				if rates:
					return flt(list(rates.values())[0])
			except (ValueError, TypeError):
				pass

		for tax_row in tax_rows:
			rate = getattr(tax_row, "rate", None)
			if rate:
				return flt(rate)

		return 23.0  # taxa normal em Portugal continental, ultimo recurso

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

	def persist_pending_atcud_log(self, doc):
		"""
		Escreve o ATCUD Log a partir do resultado calculado por
		generate_atcud_for_document (guardado em
		doc._portugal_atcud_pending_log). Chamar em after_insert,
		quando o documento ja existe na BD e a Dynamic Link do ATCUD
		Log consegue validar contra ele.
		"""
		pending = getattr(doc, "_portugal_atcud_pending_log", None)
		if not pending:
			return
		self._create_enhanced_audit_log(
			doc,
			pending["atcud_code"],
			pending["validation_code"],
			pending["sequence_number"],
			pending["generation_id"],
			pending["series_info"],
			pending["signature_result"],
			pending["qr_code_data"],
		)
		delattr(doc, "_portugal_atcud_pending_log")

	def _create_enhanced_audit_log(self, doc, atcud_code, validation_code, sequence_number,
								   generation_id, series_info=None, signature_result=None,
								   qr_code_data=None):
		"""
		Cria um registo estruturado em ATCUD Log (necessario para o
		encadeamento de hash entre documentos - ver signature.py,
		get_previous_signature_hash) e um Comment legivel no documento
		para visibilidade rapida.
		"""
		try:
			# String de sequencia com a largura real do documento (ex:
			# "0001") - sequence_number aqui e so o inteiro, ja sem o padding
			# original, que so existe na string calculada em
			# generate_atcud_for_document (fora do ambito desta funcao).
			sequence_display = self._extract_sequence_string_from_document_name(doc.name)

			log_doc = frappe.get_doc({
				"doctype": "ATCUD Log",
				"naming_series": "ATCUD-LOG-.YYYY.-.####",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"document_date": getattr(doc, "posting_date", None) or frappe.utils.nowdate(),
				"company": doc.company,
				"series_used": series_info.get("series_name") if series_info else None,
				"atcud_code": atcud_code,
				"validation_code_used": validation_code,
				"sequence_number": sequence_number,
				"generation_status": "Success",
				"generation_date": now(),
				"created_by_user": frappe.session.user,
			})

			if signature_result:
				log_doc.signature_hash = signature_result.get("signature_hash")
				log_doc.previous_signature_hash = signature_result.get("previous_signature_hash")
				log_doc.signature_hash_control = signature_result.get("hash_control")
				log_doc.signing_key_version = signature_result.get("key_version")

			if qr_code_data:
				log_doc.qr_code_string = qr_code_data

			log_doc.insert(ignore_permissions=True)

			comment_lines = [
				"ATCUD gerado automaticamente",
				f"Codigo ATCUD: {atcud_code}",
				f"Codigo Validacao: {validation_code}",
				f"Sequencia: {sequence_display}",
				f"Empresa: {doc.company}",
				f"Data/Hora: {now()}",
			]
			if signature_result:
				comment_lines.append(f"Hash control (QR): {signature_result.get('hash_control', '')}")
			else:
				comment_lines.append("Assinatura digital NAO gerada - configure a chave em Portugal Auth Settings")
			comment_lines.append("Conforme: Portaria 195/2020 e Portaria 363/2010")

			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": "<br>".join(comment_lines),
				"comment_email": frappe.session.user
			}).insert(ignore_permissions=True)

			frappe.logger().info(f"ATCUD Log criado: {doc.name} -> {atcud_code}")

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
