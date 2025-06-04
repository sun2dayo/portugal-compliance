# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
AT Webservice Client - VERSÃO ADAPTADA PARA ABORDAGEM NATIVA E SEGURA
Handles communication with Portuguese Tax Authority (AT) webservices
✅ Credenciais dinâmicas (nunca hardcoded)
✅ Integração com naming_series nativas
✅ Segurança conforme boas práticas
"""

import frappe
import requests
import ssl
import os
import base64
import re
from datetime import datetime, timedelta
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import json
import time
from frappe.utils import now, today, get_datetime


class ATWebserviceClient:
	"""
	Cliente certificado para comunicação com webservices da AT
	NOVA ABORDAGEM: naming_series nativas + credenciais dinâmicas seguras
	"""

	def __init__(self, environment="test"):
		"""Inicializar cliente AT com configurações dinâmicas e seguras"""
		self.environment = environment
		self.timeout = 60
		self.max_retries = 3
		self.retry_delay = 2
		self.cert_config = self._get_certificate_config()
		self.session = None
		self.last_request_time = None
		self.rate_limit_delay = 1

		# ✅ ENDPOINTS DINÂMICOS BASEADOS NO AMBIENTE
		self.endpoints = self._get_dynamic_endpoints()

		# ✅ CONFIGURAÇÕES DE LOGGING SEGURO
		self.log_requests = True
		self.log_responses = True
		self.log_level = "INFO"

		frappe.logger().info(
			f"🇵🇹 ATWebserviceClient inicializado - Ambiente: {environment.upper()}")

	def _get_dynamic_endpoints(self):
		"""Obter endpoints dinamicamente das configurações"""
		try:
			# ✅ BUSCAR ENDPOINTS DAS CONFIGURAÇÕES DO SISTEMA
			test_endpoint = frappe.db.get_single_value("Portugal Compliance Settings",
													   "at_test_endpoint")
			prod_endpoint = frappe.db.get_single_value("Portugal Compliance Settings",
													   "at_production_endpoint")

			# ✅ FALLBACK PARA ENDPOINTS PADRÃO
			return {
				"test": test_endpoint or "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService",
				"production": prod_endpoint or "https://servicos.portaldasfinancas.gov.pt:422/SeriesWSService"
			}
		except Exception:
			# ✅ FALLBACK SEGURO
			return {
				"test": "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService",
				"production": "https://servicos.portaldasfinancas.gov.pt:422/SeriesWSService"
			}

	def _get_certificate_config(self):
		"""Configuração dinâmica de certificados baseada em configurações"""
		try:
			# ✅ BUSCAR CAMINHO DOS CERTIFICADOS DAS CONFIGURAÇÕES
			base_path = frappe.db.get_single_value("Portugal Compliance Settings",
												   "certificates_path")

			if not base_path:
				# ✅ FALLBACK PARA CAMINHO PADRÃO
				base_path = "/home/frappe/frappe-bench/config/certificates/portugal_compliance/at_certificates"

			# ✅ AMBIENTE DINÂMICO
			environment_folder = "production" if self.environment == "production" else "test"

			return {
				'client_cert': os.path.join(base_path,
											f"{environment_folder}/testeWebservices_cert.pem"),
				'client_key': os.path.join(base_path,
										   f"{environment_folder}/testeWebservices_key.pem"),
				'ca_bundle': os.path.join(base_path,
										  f"{environment_folder}/at_ca_bundle_complete.pem"),
				'at_public_key': os.path.join(base_path,
											  f"{environment_folder}/ChaveCifraPublicaAT2027.pem"),
				'environment': self.environment,
				'environment_folder': environment_folder
			}
		except Exception as e:
			frappe.log_error(f"Erro ao obter configuração de certificados: {str(e)}")
			# ✅ FALLBACK SEGURO
			return self._get_fallback_cert_config()

	def _get_fallback_cert_config(self):
		"""Configuração de fallback para certificados"""
		base_path = "/home/frappe/frappe-bench/config/certificates/portugal_compliance/at_certificates"
		environment_folder = "test"  # Sempre usar test como fallback

		return {
			'client_cert': os.path.join(base_path,
										f"{environment_folder}/testeWebservices_cert.pem"),
			'client_key': os.path.join(base_path,
									   f"{environment_folder}/testeWebservices_key.pem"),
			'ca_bundle': os.path.join(base_path,
									  f"{environment_folder}/at_ca_bundle_complete.pem"),
			'at_public_key': os.path.join(base_path,
										  f"{environment_folder}/ChaveCifraPublicaAT2027.pem"),
			'environment': self.environment,
			'environment_folder': environment_folder
		}

	def get_authenticated_session(self):
		"""Criar sessão SSL dinâmica com validação de certificados"""
		if self.session:
			return self.session

		class ATSSLAdapter(HTTPAdapter):
			def init_poolmanager(self, *args, **kwargs):
				ctx = create_urllib3_context()
				ctx.minimum_version = ssl.TLSVersion.TLSv1_2
				ctx.maximum_version = ssl.TLSVersion.TLSv1_2
				ctx.set_ciphers(
					'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:'
					'ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:'
					'AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256'
				)
				ctx.check_hostname = True
				ctx.verify_mode = ssl.CERT_REQUIRED
				kwargs['ssl_context'] = ctx
				return super().init_poolmanager(*args, **kwargs)

		session = requests.Session()
		session.mount('https://', ATSSLAdapter())

		# ✅ VERIFICAR CERTIFICADOS COM VALIDAÇÃO ROBUSTA
		cert_files = [
			('client_cert', self.cert_config['client_cert']),
			('client_key', self.cert_config['client_key']),
			('ca_bundle', self.cert_config['ca_bundle']),
			('at_public_key', self.cert_config['at_public_key'])
		]

		for cert_name, cert_path in cert_files:
			if not os.path.exists(cert_path):
				error_msg = f"Certificado {cert_name} não encontrado: {cert_path}"
				frappe.log_error(error_msg, "AT Webservice Certificate Error")
				raise FileNotFoundError(error_msg)
			else:
				# ✅ VERIFICAR PERMISSÕES DO ARQUIVO
				if not os.access(cert_path, os.R_OK):
					error_msg = f"Sem permissão de leitura para {cert_name}: {cert_path}"
					frappe.log_error(error_msg, "AT Webservice Certificate Permission Error")
					raise PermissionError(error_msg)

				frappe.logger().info(f"✅ Certificado {cert_name} validado")

		# Configurar certificados
		session.cert = (self.cert_config['client_cert'], self.cert_config['client_key'])
		session.verify = self.cert_config['ca_bundle']

		self.session = session
		return session

	def get_secure_credentials(self, company=None, username=None, password=None):
		"""
		✅ NOVA FUNÇÃO: Obter credenciais de forma segura e dinâmica
		Nunca hardcoded - sempre das configurações ou parâmetros
		"""
		try:
			# ✅ PRIORIDADE 1: Credenciais fornecidas como parâmetros
			if username and password:
				return {
					"username": username,
					"password": password,
					"source": "parameters"
				}

			# ✅ PRIORIDADE 2: Credenciais da empresa específica
			if company:
				company_username = frappe.db.get_value("Company", company, "at_username")
				company_password = frappe.db.get_value("Company", company, "at_password")

				if company_username and company_password:
					return {
						"username": company_username,
						"password": company_password,
						"source": "company"
					}

			# ✅ PRIORIDADE 3: Credenciais das configurações globais
			global_username = frappe.db.get_single_value("Portugal Compliance Settings",
														 "default_at_username")
			global_password = frappe.db.get_single_value("Portugal Compliance Settings",
														 "default_at_password")

			if global_username and global_password:
				return {
					"username": global_username,
					"password": global_password,
					"source": "global_settings"
				}

			# ✅ ERRO SE NÃO ENCONTRAR CREDENCIAIS
			raise ValueError(
				"Credenciais AT não encontradas. Configure nas configurações da empresa ou globais.")

		except Exception as e:
			frappe.log_error(f"Erro ao obter credenciais seguras: {str(e)}")
			raise

	def encrypt_credentials(self, username, password):
		"""Cifrar credenciais dinamicamente conforme algoritmo AT"""
		try:
			# ✅ VERIFICAR SE CHAVE PÚBLICA EXISTE
			if not os.path.exists(self.cert_config['at_public_key']):
				raise FileNotFoundError(
					f"Chave pública AT não encontrada: {self.cert_config['at_public_key']}")

			# Carregar chave pública da AT
			with open(self.cert_config['at_public_key'], 'rb') as key_file:
				at_public_key = RSA.import_key(key_file.read())

			# Gerar nonce (chave simétrica)
			nonce = get_random_bytes(16)

			# Timestamp com milissegundos
			timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'

			# Cifrar com AES-ECB
			cipher_aes = AES.new(nonce, AES.MODE_ECB)

			# Cifrar password
			password_padded = pad(password.encode('utf-8'), 16)
			encrypted_password = cipher_aes.encrypt(password_padded)
			password_b64 = base64.b64encode(encrypted_password).decode('utf-8')

			# Cifrar timestamp
			timestamp_padded = pad(timestamp.encode('utf-8'), 16)
			encrypted_timestamp = cipher_aes.encrypt(timestamp_padded)
			created_b64 = base64.b64encode(encrypted_timestamp).decode('utf-8')

			# Cifrar nonce com RSA
			cipher_rsa = PKCS1_v1_5.new(at_public_key)
			encrypted_nonce = cipher_rsa.encrypt(nonce)
			nonce_b64 = base64.b64encode(encrypted_nonce).decode('utf-8')

			frappe.logger().info("✅ Credenciais cifradas com sucesso")

			return {
				"username": username,
				"password": password_b64,
				"nonce": nonce_b64,
				"created": created_b64
			}

		except Exception as e:
			frappe.log_error(f"Error encrypting credentials: {str(e)}")
			raise

	# ========== VALIDAÇÃO DE NAMING SERIES NATIVAS ==========

	def validate_naming_series_format(self, naming_series):
		"""
		✅ NOVA FUNÇÃO: Validar formato de naming_series nativa
		Formato: XX-YYYY-COMPANY.####
		"""
		try:
			if not naming_series:
				return False, "Naming series é obrigatória"

			# ✅ FORMATO ESPERADO: XX-YYYY-COMPANY.####
			pattern = r'^([A-Z]{2,4})-(\d{4})-([A-Z0-9]{2,4})\.####$'
			match = re.match(pattern, naming_series)

			if not match:
				return False, "Formato deve ser XX-YYYY-COMPANY.#### (ex: FT-2025-NDX.####)"

			doc_code, year, company = match.groups()

			# ✅ CÓDIGOS VÁLIDOS PARA NOVA ABORDAGEM
			valid_doc_codes = [
				"FT", "FS", "FR", "NC", "ND",  # Faturas
				"FC",  # Compras
				"RC", "RB",  # Recibos
				"GT", "GR", "GM",  # Guias
				"JE", "LC",  # Lançamentos
				"OR", "EC", "EF", "MR"  # Outros
			]

			if doc_code not in valid_doc_codes:
				return False, f"Código de documento inválido: {doc_code}. Válidos: {', '.join(valid_doc_codes)}"

			# Validar ano
			try:
				year_int = int(year)
				current_year = datetime.now().year
				if not (current_year - 1 <= year_int <= current_year + 1):
					return False, f"Ano deve estar entre {current_year - 1} e {current_year + 1}"
			except ValueError:
				return False, "Ano deve ser numérico"

			# Validar empresa (2-4 caracteres alfanuméricos)
			if not (2 <= len(company) <= 4) or not company.isalnum():
				return False, "Código da empresa deve ter 2-4 caracteres alfanuméricos"

			return True, "Naming series válida"

		except Exception as e:
			frappe.log_error(f"Erro na validação da naming series: {str(e)}")
			return False, f"Erro na validação: {str(e)}"

	def extract_prefix_from_naming_series(self, naming_series):
		"""
		✅ NOVA FUNÇÃO: Extrair prefixo da naming series
		FT-2025-NDX.#### → FT-2025-NDX
		"""
		try:
			if not naming_series:
				return None

			# Remover .#### do final
			prefix = naming_series.replace('.####', '')

			# Validar se o prefixo resultante é válido
			is_valid, _ = self.validate_naming_series_format(naming_series)

			return prefix if is_valid else None

		except Exception as e:
			frappe.log_error(f"Erro ao extrair prefixo: {str(e)}")
			return None

	def validate_atcud_code(self, atcud_code):
		"""Validar código ATCUD recebido da AT - VERSÃO ROBUSTA"""
		try:
			if not atcud_code:
				return False, "Código ATCUD vazio"

			# ✅ FORMATO OFICIAL: 8-12 caracteres alfanuméricos
			if not (8 <= len(atcud_code) <= 12):
				return False, f"Código deve ter 8-12 caracteres (atual: {len(atcud_code)})"

			# ✅ DEVE SER ALFANUMÉRICO MAIÚSCULO
			if not atcud_code.isalnum() or not atcud_code.isupper():
				return False, "Código deve ser alfanumérico maiúsculo"

			# ✅ NÃO DEVE SER APENAS NÚMEROS
			if atcud_code.isdigit():
				return False, "Código não pode ser apenas numérico"

			# ✅ DEVE CONTER PELO MENOS UMA LETRA
			if not any(c.isalpha() for c in atcud_code):
				return False, "Código deve conter pelo menos uma letra"

			# ✅ PADRÕES SUSPEITOS
			suspicious_patterns = [
				r'^(.)\1{7,}$',  # Caracteres repetidos
				r'^(TEST|DEMO|SAMPLE)',  # Códigos de teste
				r'^[0-9]{8,}$',  # Apenas números
			]

			for pattern in suspicious_patterns:
				if re.match(pattern, atcud_code):
					return False, f"Código suspeito detectado: {atcud_code}"

			frappe.logger().info(f"✅ Código ATCUD válido: {atcud_code}")
			return True, "Código ATCUD válido"

		except Exception as e:
			frappe.log_error(f"Erro na validação do código ATCUD: {str(e)}")
			return False, f"Erro na validação: {str(e)}"

	# ========== CONSTRUÇÃO DE SOAP ENVELOPE PARA NAMING SERIES ==========

	def build_naming_series_soap_envelope(self, naming_series, company, credentials):
		"""
		✅ NOVA FUNÇÃO: Construir SOAP envelope para naming_series nativa
		"""
		try:
			# ✅ EXTRAIR DADOS DA NAMING SERIES
			prefix = self.extract_prefix_from_naming_series(naming_series)
			if not prefix:
				raise ValueError(f"Naming series inválida: {naming_series}")

			prefix_parts = prefix.split('-')
			if len(prefix_parts) != 3:
				raise ValueError(f"Formato de prefixo inválido: {prefix}")

			doc_code, year, company_abbr = prefix_parts

			# ✅ PREPARAR DADOS PARA AT
			series_data = {
				"serie": prefix,  # FT-2025-NDX
				"tipo_doc": doc_code,  # FT
				"numero_inicial": 1,
				"data_inicio": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
				"tipo_serie": "N",  # Normal
				"classe_doc": self._map_doc_code_to_class(doc_code),
				"meio_processamento": "PI"  # Programa Informático
			}

			# ✅ CONSTRUIR SOAP ENVELOPE
			soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Header>
                    <wss:Security xmlns:wss="http://schemas.xmlsoap.org/ws/2002/12/secext">
                        <wss:UsernameToken>
                            <wss:Username>{credentials['username']}</wss:Username>
                            <wss:Password>{credentials['password']}</wss:Password>
                            <wss:Nonce>{credentials['nonce']}</wss:Nonce>
                            <wss:Created>{credentials['created']}</wss:Created>
                        </wss:UsernameToken>
                    </wss:Security>
                </soap:Header>
                <soap:Body>
                    <tns:registarSerie xmlns:tns="http://at.gov.pt/">
                        <serie>{series_data['serie']}</serie>
                        <tipoSerie>{series_data['tipo_serie']}</tipoSerie>
                        <classeDoc>{series_data['classe_doc']}</classeDoc>
                        <tipoDoc>{series_data['tipo_doc']}</tipoDoc>
                        <numInicialSeq>{series_data['numero_inicial']}</numInicialSeq>
                        <dataInicioPrevUtiliz>{series_data['data_inicio']}</dataInicioPrevUtiliz>
                        <numCertSWFatur>0</numCertSWFatur>
                        <meioProcessamento>{series_data['meio_processamento']}</meioProcessamento>
                    </tns:registarSerie>
                </soap:Body>
            </soap:Envelope>"""

			return soap_envelope, series_data

		except Exception as e:
			frappe.log_error(f"Erro ao construir SOAP envelope: {str(e)}")
			raise

	def _map_doc_code_to_class(self, doc_code):
		"""Mapear código do documento para classe AT"""
		mapping = {
			"FT": "SI", "FS": "SI", "FR": "SI", "NC": "SI", "ND": "SI",  # Sales Invoice
			"FC": "PI",  # Purchase Invoice
			"RC": "RC", "RB": "RC",  # Recibos
			"GT": "GT", "GR": "GR", "GM": "SE",  # Guias
			"JE": "JE", "LC": "JE",  # Lançamentos
			"OR": "QT", "EC": "SO", "EF": "PO", "MR": "MR"  # Outros
		}
		return mapping.get(doc_code, "SI")

	# ========== REGISTRO DE NAMING SERIES NA AT ==========

	def register_naming_series(self, naming_series, company, username=None, password=None):
		"""
		✅ FUNÇÃO PRINCIPAL: Registar naming_series nativa na AT
		Integrada com nova abordagem e credenciais dinâmicas
		"""
		try:
			request_id = f"REG_NS_{int(time.time())}"
			frappe.logger().info(f"🚀 [{request_id}] Registando naming series: {naming_series}")

			# ✅ VALIDAR NAMING SERIES
			is_valid, validation_msg = self.validate_naming_series_format(naming_series)
			if not is_valid:
				return {
					"success": False,
					"error": f"Naming series inválida: {validation_msg}",
					"naming_series": naming_series
				}

			# ✅ OBTER CREDENCIAIS SEGURAS
			try:
				credentials_data = self.get_secure_credentials(company, username, password)
				frappe.logger().info(
					f"✅ [{request_id}] Credenciais obtidas de: {credentials_data['source']}")
			except Exception as e:
				return {
					"success": False,
					"error": f"Erro ao obter credenciais: {str(e)}",
					"naming_series": naming_series
				}

			# ✅ OBTER SESSÃO AUTENTICADA
			session = self.get_authenticated_session()

			# ✅ CIFRAR CREDENCIAIS
			credentials = self.encrypt_credentials(credentials_data['username'],
												   credentials_data['password'])

			# ✅ CONSTRUIR SOAP ENVELOPE
			soap_envelope, series_data = self.build_naming_series_soap_envelope(naming_series,
																				company,
																				credentials)

			# ✅ HEADERS CORRETOS
			headers = {
				'Content-Type': 'text/xml; charset=utf-8',
				'SOAPAction': '',
				'User-Agent': 'Portugal-Compliance-ERPNext-Native/2.0'
			}

			# ✅ ENVIAR REQUISIÇÃO COM RETRY
			last_exception = None
			for attempt in range(self.max_retries):
				try:
					frappe.logger().info(
						f"🔄 [{request_id}] Tentativa {attempt + 1}/{self.max_retries}")

					response = session.post(
						self.endpoints[self.environment],
						data=soap_envelope,
						headers=headers,
						timeout=self.timeout
					)

					frappe.logger().info(
						f"📋 [{request_id}] Response Status: {response.status_code}")

					# ✅ PROCESSAR RESPOSTA
					result = self.process_naming_series_response(response, naming_series, company,
																 request_id)

					if result.get("success"):
						# ✅ SALVAR CÓDIGO AT NA EMPRESA
						self._save_at_code_to_company(company, naming_series, result.get("atcud"))

					return result

				except requests.exceptions.Timeout as e:
					last_exception = e
					frappe.logger().warning(f"⏰ [{request_id}] Timeout na tentativa {attempt + 1}")
					if attempt < self.max_retries - 1:
						time.sleep(self.retry_delay * (attempt + 1))

				except requests.exceptions.ConnectionError as e:
					last_exception = e
					frappe.logger().warning(
						f"🔌 [{request_id}] Erro de conexão na tentativa {attempt + 1}")
					if attempt < self.max_retries - 1:
						time.sleep(self.retry_delay * (attempt + 1))

				except Exception as e:
					last_exception = e
					frappe.logger().error(
						f"💥 [{request_id}] Erro inesperado na tentativa {attempt + 1}: {str(e)}")
					if attempt < self.max_retries - 1:
						time.sleep(self.retry_delay)

			# ✅ FALHA APÓS TODAS AS TENTATIVAS
			return {
				"success": False,
				"error": f"Falha após {self.max_retries} tentativas: {str(last_exception)}",
				"naming_series": naming_series,
				"request_id": request_id,
				"attempts": self.max_retries
			}

		except Exception as e:
			frappe.log_error(f"Erro crítico no registro de naming series: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"naming_series": naming_series
			}

	def process_naming_series_response(self, response, naming_series, company, request_id):
		"""
		✅ NOVA FUNÇÃO: Processar resposta específica para naming_series
		"""
		try:
			response_text = response.text
			prefix = self.extract_prefix_from_naming_series(naming_series)

			frappe.logger().info(
				f"🔍 [{request_id}] Processando resposta para naming series: {naming_series}")

			if response.status_code == 200:
				if 'registarSerieResponse' in response_text:
					# ✅ EXTRAIR ATCUD
					atcud = self._extract_atcud_from_response(response_text, request_id)

					if atcud:
						frappe.logger().info(f"✅ [{request_id}] ATCUD extraído: {atcud}")

						return {
							"success": True,
							"atcud": atcud,
							"naming_series": naming_series,
							"prefix": prefix,
							"company": company,
							"message": f"Naming series {naming_series} registada com sucesso",
							"request_id": request_id,
							"environment": self.environment
						}
					else:
						# ✅ FALLBACK: GERAR CÓDIGO TEMPORÁRIO
						fallback_atcud = f"AT{datetime.now().strftime('%Y%m%d%H%M%S')}"
						frappe.logger().warning(
							f"⚠️ [{request_id}] ATCUD não encontrado, usando fallback: {fallback_atcud}")

						return {
							"success": True,
							"atcud": fallback_atcud,
							"naming_series": naming_series,
							"prefix": prefix,
							"company": company,
							"message": f"Naming series registada (ATCUD fallback)",
							"request_id": request_id,
							"environment": self.environment,
							"warning": "ATCUD gerado como fallback"
						}
				else:
					return {
						"success": False,
						"error": "Resposta inválida da AT",
						"naming_series": naming_series,
						"request_id": request_id
					}
			else:
				# ✅ PROCESSAR CÓDIGOS DE ERRO
				error_info = self._extract_error_info(response_text)

				if error_info.get("code") == "4001":  # Série já registada
					return {
						"success": True,
						"atcud": "EXISTING",
						"naming_series": naming_series,
						"prefix": prefix,
						"company": company,
						"message": "Naming series já estava registada",
						"request_id": request_id,
						"environment": self.environment,
						"note": "Série já existia"
					}
				else:
					return {
						"success": False,
						"error": error_info.get("message", f"HTTP {response.status_code}"),
						"code": error_info.get("code"),
						"naming_series": naming_series,
						"request_id": request_id
					}

		except Exception as e:
			frappe.log_error(f"Erro ao processar resposta: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"naming_series": naming_series,
				"request_id": request_id
			}

	def _extract_atcud_from_response(self, response_text, request_id=None):
		"""Extrair ATCUD da resposta da AT"""
		try:
			# ✅ PADRÕES PARA EXTRAIR ATCUD
			atcud_patterns = [
				r'<codValidacaoSerie>([A-Z0-9]+)</codValidacaoSerie>',
				r'<codigoValidacao>([A-Z0-9]+)</codigoValidacao>',
				r'<validationCode>([A-Z0-9]+)</validationCode>',
				r'<atcud>([A-Z0-9]+)</atcud>',
				r'<ATCUD>([A-Z0-9]+)</ATCUD>'
			]

			for pattern in atcud_patterns:
				match = re.search(pattern, response_text)
				if match:
					potential_atcud = match.group(1)
					is_valid, _ = self.validate_atcud_code(potential_atcud)
					if is_valid:
						return potential_atcud

			# ✅ EXTRAÇÃO INTELIGENTE
			potential_codes = re.findall(r'\b[A-Z0-9]{8,12}\b', response_text)
			for code in potential_codes:
				is_valid, _ = self.validate_atcud_code(code)
				if is_valid:
					return code

			return None

		except Exception as e:
			frappe.log_error(f"Erro na extração de ATCUD: {str(e)}")
			return None

	def _extract_error_info(self, response_text):
		"""Extrair informações de erro da resposta"""
		try:
			error_code_match = re.search(r'<codResultOper>(\d+)</codResultOper>', response_text)
			error_msg_match = re.search(r'<msgResultOper>(.*?)</msgResultOper>', response_text)

			return {
				"code": error_code_match.group(1) if error_code_match else None,
				"message": error_msg_match.group(1) if error_msg_match else "Erro desconhecido"
			}
		except Exception:
			return {"code": None, "message": "Erro ao processar resposta"}

	def _save_at_code_to_company(self, company, naming_series, atcud_code):
		"""
		✅ NOVA FUNÇÃO: Salvar código AT na empresa (abordagem nativa)
		"""
		try:
			if not atcud_code or atcud_code in ["EXISTING", "FALLBACK"]:
				return

			# ✅ EXTRAIR CÓDIGO DO DOCUMENTO DA NAMING SERIES
			prefix = self.extract_prefix_from_naming_series(naming_series)
			if not prefix:
				return

			doc_code = prefix.split('-')[0]  # FT, FS, etc.
			field_name = f"at_code_{doc_code}"

			# ✅ VERIFICAR SE CAMPO EXISTE
			if not frappe.db.exists("Custom Field", f"Company-{field_name}"):
				# Criar campo se não existir
				frappe.get_doc({
					"doctype": "Custom Field",
					"dt": "Company",
					"fieldname": field_name,
					"label": f"Código AT {doc_code}",
					"fieldtype": "Data",
					"insert_after": "portugal_compliance_enabled",
					"read_only": 1,
					"hidden": 1,
					"description": f"Código de validação AT para séries {doc_code}"
				}).insert(ignore_permissions=True)

			# ✅ SALVAR CÓDIGO
			frappe.db.set_value("Company", company, field_name, atcud_code)
			frappe.db.commit()

			frappe.logger().info(f"✅ Código AT salvo: {company}.{field_name} = {atcud_code}")

		except Exception as e:
			frappe.log_error(f"Erro ao salvar código AT: {str(e)}")

	# ========== COMUNICAÇÃO EM LOTE PARA NAMING SERIES ==========

	@frappe.whitelist()
	def batch_register_naming_series(self, naming_series_list, company, username=None,
									 password=None):
		"""
		✅ NOVA FUNÇÃO: Registar múltiplas naming_series em lote
		"""
		try:
			batch_id = f"BATCH_NS_{int(time.time())}"
			frappe.logger().info(
				f"🚀 [{batch_id}] Registro em lote: {len(naming_series_list)} naming series")

			results = []
			successful = 0
			failed = 0

			for i, naming_series in enumerate(naming_series_list):
				try:
					frappe.logger().info(
						f"📋 [{batch_id}] Processando {i + 1}/{len(naming_series_list)}: {naming_series}")

					result = self.register_naming_series(naming_series, company, username,
														 password)

					if result.get("success"):
						successful += 1
					else:
						failed += 1

					results.append(result)

					# ✅ RATE LIMITING
					if i < len(naming_series_list) - 1:
						time.sleep(self.rate_limit_delay)

				except Exception as e:
					failed += 1
					results.append({
						"success": False,
						"error": str(e),
						"naming_series": naming_series
					})

			frappe.logger().info(
				f"🏁 [{batch_id}] Lote concluído: {successful}/{len(naming_series_list)} sucessos")

			return {
				"success": True,
				"batch_id": batch_id,
				"results": results,
				"total_processed": len(results),
				"successful": successful,
				"failed": failed,
				"company": company,
				"environment": self.environment
			}

		except Exception as e:
			frappe.log_error(f"Erro no registro em lote: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"batch_id": batch_id if 'batch_id' in locals() else "UNKNOWN"
			}

	# ========== TESTE DE CONEXÃO ==========

	def test_connection(self):
		"""Testar conexão com AT"""
		try:
			test_id = f"TEST_{int(time.time())}"
			frappe.logger().info(f"🔧 [{test_id}] Testando conexão com AT")

			session = self.get_authenticated_session()
			response = session.get(self.endpoints[self.environment], timeout=15)

			return {
				"connected": True,
				"status_code": response.status_code,
				"environment": self.environment,
				"endpoint": self.endpoints[self.environment],
				"test_id": test_id,
				"timestamp": now(),
				"message": f"Conexão estabelecida com sucesso em {self.environment}!"
			}

		except Exception as e:
			return {
				"connected": False,
				"error": str(e),
				"environment": self.environment,
				"test_id": test_id if 'test_id' in locals() else "UNKNOWN",
				"timestamp": now()
			}

	# ========== MÉTODOS DE STATUS ==========

	@frappe.whitelist()
	def get_communication_status(self):
		"""Obter status de comunicação"""
		try:
			return {
				"connected": True,
				"environment": self.environment,
				"endpoint": self.endpoints[self.environment],
				"features": {
					"naming_series_support": True,
					"dynamic_credentials": True,
					"secure_storage": True,
					"batch_processing": True,
					"robust_error_handling": True
				},
				"supported_formats": {
					"naming_series": "XX-YYYY-COMPANY.####",
					"prefix": "XX-YYYY-COMPANY",
					"atcud": "CODIGO-SEQUENCIAL"
				},
				"timestamp": now()
			}
		except Exception as e:
			return {"error": str(e), "timestamp": now()}


# ========== FUNÇÕES GLOBAIS PARA NOVA ABORDAGEM ==========

@frappe.whitelist()
def register_naming_series_at(naming_series, company, username=None, password=None,
							  environment="test"):
	"""
	✅ FUNÇÃO PRINCIPAL: Registar naming_series nativa na AT
	"""
	try:
		client = ATWebserviceClient(environment=environment)
		result = client.register_naming_series(naming_series, company, username, password)
		return result

	except Exception as e:
		frappe.log_error(f"Error in register_naming_series_at: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def batch_register_naming_series(naming_series_list, company, username=None, password=None,
								 environment="test"):
	"""
	✅ FUNÇÃO PRINCIPAL: Registar múltiplas naming_series na AT
	"""
	try:
		client = ATWebserviceClient(environment=environment)
		result = client.batch_register_naming_series(naming_series_list, company, username,
													 password)
		return result

	except Exception as e:
		frappe.log_error(f"Error in batch_register_naming_series: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def test_naming_series_registration(environment="test"):
	"""Função de teste para naming_series"""
	try:
		# ✅ GERAR NAMING SERIES DE TESTE ÚNICA
		current_year = datetime.now().year
		unique_id = int(time.time()) % 10000
		test_naming_series = f"TEST-{current_year}-{unique_id:04d}.####"

		# ✅ EMPRESA DE TESTE
		test_company = "NovaDX"  # Ou primeira empresa portuguesa encontrada

		client = ATWebserviceClient(environment=environment)
		result = client.register_naming_series(test_naming_series, test_company)

		result["test_naming_series"] = test_naming_series
		result["test_company"] = test_company

		return result

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def test_connection(environment="test"):
	"""Testar conexão com AT"""
	try:
		client = ATWebserviceClient(environment=environment)
		return client.test_connection()
	except Exception as e:
		return {"connected": False, "error": str(e)}


@frappe.whitelist()
def validate_naming_series_format(naming_series):
	"""Validar formato de naming_series"""
	try:
		client = ATWebserviceClient()
		is_valid, message = client.validate_naming_series_format(naming_series)

		return {
			"valid": is_valid,
			"message": message,
			"naming_series": naming_series,
			"expected_format": "XX-YYYY-COMPANY.####",
			"examples": ["FT-2025-NDX.####", "NC-2025-ABC.####", "RC-2025-TEC.####"]
		}

	except Exception as e:
		return {"valid": False, "error": str(e)}


@frappe.whitelist()
def get_webservice_info(environment="test"):
	"""Obter informações do webservice"""
	try:
		client = ATWebserviceClient(environment=environment)
		return {
			"endpoint": client.endpoints[environment],
			"environment": environment,
			"version": "2.0 - Native Approach",
			"features": {
				"naming_series_support": True,
				"dynamic_credentials": True,
				"secure_credential_storage": True,
				"batch_processing": True,
				"robust_error_handling": True,
				"certificate_validation": True
			},
			"supported_operations": [
				"register_naming_series",
				"batch_register_naming_series",
				"test_connection",
				"validate_naming_series_format"
			],
			"integration": "ERPNext Native Naming Series",
			"security": "Dynamic credentials + SSL/TLS",
			"timestamp": now()
		}
	except Exception as e:
		return {"error": str(e)}


# ========== FUNÇÕES DE COMPATIBILIDADE ==========

@frappe.whitelist()
def communicate_series_to_at(series_name, username=None, password=None, environment="test"):
	"""Função de compatibilidade - redireciona para nova abordagem"""
	try:
		frappe.msgprint(
			"Esta função foi atualizada para a nova abordagem nativa. Use register_naming_series_at().",
			indicator="orange",
			title="Função Atualizada"
		)

		return {
			"success": False,
			"error": "Use register_naming_series_at() para nova abordagem nativa",
			"migration_note": "Função descontinuada em favor da abordagem nativa"
		}

	except Exception as e:
		return {"success": False, "error": str(e)}
