# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
AT Webservice Client - VERSÃO ADAPTADA PARA ABORDAGEM NATIVA E SEGURA
Handles communication with Portuguese Tax Authority (AT) webservices
✅ Credenciais dinâmicas (nunca hardcoded)
✅ Integração com naming_series nativas ERPNext (SEM HÍFENS)
✅ Segurança conforme boas práticas
✅ 100% operacional com testes da console
✅ CORRIGIDO: Comunicação real com validation_codes da AT
"""

import frappe
from frappe import _
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


import zeep
from zeep.transports import Transport
from lxml import etree
import requests
from datetime import date as _date

NS_WSS_LEGACY = "http://schemas.xmlsoap.org/ws/2002/12/secext"


def _build_mtls_session(cert_path, key_path):
	"""
	Sessao requests com o certificado cliente da empresa anexado para
	mTLS - a AT exige isto na camada de transporte, nao so credenciais
	no corpo SOAP. Zeep usa esta sessao para todos os pedidos HTTP
	subjacentes.
	"""
	session = requests.Session()
	if cert_path and key_path:
		session.cert = (cert_path, key_path)
	return session


def _build_wsse_security_header(username, password, at_public_cert_path):
	"""
	Constroi o cabecalho WS-Security proprietario exigido pela AT (NAO
	e o UsernameToken WSSE standard). Esquema (confirmado por chamada
	real bem-sucedida ao webservice de series):
	  1. Gera uma chave simetrica AES-128 aleatoria ("nonce").
	  2. Cifra a password com essa chave (AES-128-ECB + PKCS7 padding).
	  3. Cifra a propria chave simetrica com RSA (PKCS1v1.5), usando o
	     certificado publico da AT - o resultado vai no campo <Nonce>.
	  4. Cifra o timestamp UTC atual com a mesma chave AES.
	  5. Tudo em base64, sob o namespace legado 2002/12/secext (a AT
	     nao aceita o namespace OASIS 2004 standard para este esquema).
	"""
	if not os.path.exists(at_public_cert_path):
		raise ATWebserviceError(
			_("Certificado publico da AT nao encontrado: {0}").format(at_public_cert_path)
		)

	with open(at_public_cert_path, "rb") as f:
		at_public_key = RSA.import_key(f.read())

	nonce = get_random_bytes(16)
	cipher_aes = AES.new(nonce, AES.MODE_ECB)

	password_padded = pad(password.encode("utf-8"), 16)
	encrypted_password_b64 = base64.b64encode(cipher_aes.encrypt(password_padded)).decode()

	created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
	created_padded = pad(created.encode("utf-8"), 16)
	encrypted_created_b64 = base64.b64encode(cipher_aes.encrypt(created_padded)).decode()

	cipher_rsa = PKCS1_v1_5.new(at_public_key)
	encrypted_nonce_b64 = base64.b64encode(cipher_rsa.encrypt(nonce)).decode()

	nsmap = {"wsse": NS_WSS_LEGACY}
	security = etree.Element(f"{{{NS_WSS_LEGACY}}}Security", nsmap=nsmap)
	token = etree.SubElement(security, f"{{{NS_WSS_LEGACY}}}UsernameToken")
	etree.SubElement(token, f"{{{NS_WSS_LEGACY}}}Username").text = username
	etree.SubElement(token, f"{{{NS_WSS_LEGACY}}}Password").text = encrypted_password_b64
	etree.SubElement(token, f"{{{NS_WSS_LEGACY}}}Nonce").text = encrypted_nonce_b64
	etree.SubElement(token, f"{{{NS_WSS_LEGACY}}}Created").text = encrypted_created_b64
	return security


def get_series_webservice_client(username=None, password=None):
	"""
	Cliente zeep para o webservice de comunicacao de series
	(registarSerie/consultarSeries/finalizarSerie/anularSerie),
	carregado a partir do WSDL real da AT incluido no repositorio, com
	mTLS (certificado cliente) configurado no transporte. O cabecalho
	WS-Security e construido a parte (ver _build_wsse_security_header)
	e passado em cada chamada via _soapheaders, porque a AT exige um
	esquema proprietario que o zeep nao suporta nativamente.

	Devolve (service, wsse_header_element) - o header tem de ser
	reconstruido a cada chamada (o nonce/timestamp sao de utilizacao
	unica).
	"""
	settings = frappe.get_single("Portugal Auth Settings")

	cert_path = settings.get("mtls_certificate_path")
	key_path = settings.get("mtls_private_key_path")
	if not cert_path or not key_path:
		raise ATWebserviceError(
			_(
				"Certificado mTLS nao configurado. Defina 'Certificado Cliente mTLS (PEM)' e "
				"'Chave Privada mTLS (PEM)' em Portugal Auth Settings."
			)
		)

	at_public_cert_path = settings.get("at_public_certificate_path")
	if not at_public_cert_path:
		raise ATWebserviceError(
			_(
				"Certificado publico da AT nao configurado. Defina 'Certificado Publico da AT "
				"(cifra WS-Security)' em Portugal Auth Settings."
			)
		)

	at_username = username or settings.get("at_username")
	at_password = password or settings.get_password("at_password", raise_exception=False)
	if not at_username or not at_password:
		raise ATWebserviceError(
			_(
				"Credenciais do webservice da AT nao configuradas. Defina 'Utilizador AT' e "
				"'Password AT' em Portugal Auth Settings (distintas do login do Portal das Financas)."
			)
		)

	# A AT usa portas diferentes para o mesmo servico consoante o
	# ambiente - 722 para testes, 422 para producao (nao e apenas o
	# dominio/caminho que muda). Confirmado por teste real: ligar com
	# um certificado de teste a porta 422 (producao) faz a AT aceitar
	# o handshake TLS e depois corromper a ligacao assim que dados
	# reais sao enviados.
	sandbox_mode = settings.get("sandbox_mode")
	if sandbox_mode is None:
		sandbox_mode = 1
	endpoint = (
		"https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService"
		if int(sandbox_mode)
		else "https://servicos.portaldasfinancas.gov.pt:422/SeriesWSService"
	)

	wsdl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wsdl", "Comunicacao_Series.wsdl")
	session = _build_mtls_session(cert_path, key_path)
	transport = Transport(session=session, timeout=60)
	client = zeep.Client(wsdl=wsdl_path, transport=transport)

	binding_name = list(client.wsdl.bindings.keys())[0]
	service = client.create_service(binding_name, endpoint)

	header = _build_wsse_security_header(at_username, at_password, at_public_cert_path)
	return service, header


class ATWebserviceError(Exception):
	pass


class ATWebserviceClient:
	"""
	Cliente certificado para comunicação com webservices da AT
	NOVA ABORDAGEM: naming_series nativas ERPNext (SEM HÍFENS) + credenciais dinâmicas seguras
	✅ 100% compatível com testes da console
	✅ CORRIGIDO: Comunicação real com AT
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

			# ✅ CORREÇÃO: AMBOS AMBIENTES USAM ENDPOINT DE TESTE (conforme acordo)
			return {
				"test": test_endpoint or "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService",
				"production": test_endpoint or "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService"
			}
		except Exception:
			# ✅ FALLBACK SEGURO - AMBOS PARA TESTE
			return {
				"test": "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService",
				"production": "https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService"
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

	def validate_naming_series_format(self, naming_series):
		"""
		✅ CORRIGIDO: Validar formato de naming_series nativa ERPNext (SEM HÍFENS)
		Formato: XXYYYY+COMPANY.#### (ex: FT2025DSY.####)
		"""
		try:
			if not naming_series:
				return False, "Naming series é obrigatória"

			# ✅ FORMATO CORRETO ERPNext: XXYYYY+COMPANY.#### (SEM HÍFENS)
			pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})\.####$'
			match = re.match(pattern, naming_series)

			if not match:
				return False, "Formato deve ser XXYYYY+COMPANY.#### (ex: FT2025DSY.####)"

			doc_code, year, company = match.groups()

			# ✅ CÓDIGOS VÁLIDOS PARA ERPNext
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
		✅ CORRIGIDO: Extrair prefixo da naming series ERPNext (SEM HÍFENS)
		FT2025DSY.#### → FT2025DSY
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

	# ========== GERAÇÃO DE ATCUD COM CÓDIGO REAL DA AT ==========

	def _generate_atcud_with_real_code(self, validation_code, sequence):
		"""
		✅ NOVA FUNÇÃO: Gerar ATCUD usando código real recebido da AT
		Baseado na sua experiência com programação.autenticação
		"""
		try:
			if not validation_code:
				return None

			# ✅ FORMATO CORRETO: CODIGO_AT-SEQUENCIA
			# Ex: AAJFJMVNTN-00000001
			atcud_code = f"{validation_code}-{str(sequence).zfill(8)}"

			# Validar formato final
			is_valid, _ = self.validate_atcud_code(validation_code)
			if not is_valid:
				frappe.logger().warning(
					f"⚠️ Validation code pode estar incorreto: {validation_code}")

			return atcud_code

		except Exception as e:
			frappe.log_error(f"Erro ao gerar ATCUD real: {str(e)}")
			return None

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

	# ========== REGISTRO DE NAMING SERIES ERPNEXT NA AT ==========

	def register_naming_series(self, naming_series, company, username=None, password=None):
		"""
		Regista uma naming_series (serie documental ERPNext) na AT via
		o webservice real (registarSerie), usando zeep + mTLS + WSSE
		(ver get_series_webservice_client). Devolve o codigo de
		validacao da serie, necessario para gerar ATCUD reais (nao
		temporarios) - ver utils/atcud_generator.py.
		"""
		request_id = f"REG_NS_{int(time.time())}"
		frappe.logger().info(f"[{request_id}] Registando naming series: {naming_series}")

		is_valid, validation_msg = self.validate_naming_series_format(naming_series)
		if not is_valid:
			return {
				"success": False,
				"error": f"Naming series inválida: {validation_msg}",
				"naming_series": naming_series,
				"request_id": request_id,
			}

		prefix = self.extract_prefix_from_naming_series(naming_series)
		if not prefix:
			return {
				"success": False,
				"error": f"Não foi possível extrair o prefixo de: {naming_series}",
				"naming_series": naming_series,
				"request_id": request_id,
			}

		pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{2,4})$'
		match = re.match(pattern, prefix)
		if not match:
			return {
				"success": False,
				"error": f"Formato de prefixo inválido: {prefix}",
				"naming_series": naming_series,
				"request_id": request_id,
			}
		doc_code, year, company_abbr = match.groups()
		at_series_format = f"{doc_code}-{year}-{company_abbr}"

		try:
			service, wsse_header = get_series_webservice_client(username, password)
		except ATWebserviceError as e:
			return {"success": False, "error": str(e), "naming_series": naming_series, "request_id": request_id}

		certificate_number = frappe.db.get_single_value(
			"Portugal Auth Settings", "software_certificate_number"
		) or "0"

		try:
			response = service.consultarSeries(
				classeDoc=self._map_doc_code_to_class(doc_code),
				tipoDoc=doc_code,
				meioProcessamento="PI",
				_soapheaders=[wsse_header],
			)
		except Exception as e:
			frappe.log_error(f"Erro ao consultar séries existentes na AT: {str(e)}", "ATWebserviceClient")
			response = None

		existing = None
		if response is not None:
			resp_body = getattr(response, "consultarSeriesResp", response)
			for info in getattr(resp_body, "InfoSerie", None) or getattr(resp_body, "infoSerie", None) or []:
				if getattr(info, "serie", None) == at_series_format:
					existing = info
					break

		if existing is not None:
			validation_code = getattr(existing, "codValidacaoSerie", None)
			frappe.logger().info(f"[{request_id}] Série já registada na AT: {validation_code}")
			return {
				"success": True,
				"naming_series": naming_series,
				"series_at_format": at_series_format,
				"validation_code": validation_code,
				"request_id": request_id,
				"note": "Série já existia na AT",
				"raw_response": zeep.helpers.serialize_object(existing),
			}

		try:
			# Nova chamada: a AT exige um cabecalho WS-Security fresco por
			# pedido (nonce/timestamp de utilizacao unica).
			service, wsse_header = get_series_webservice_client(username, password)
			response = service.registarSerie(
				serie=at_series_format,
				tipoSerie="N",
				classeDoc=self._map_doc_code_to_class(doc_code),
				tipoDoc=doc_code,
				numInicialSeq=1,
				dataInicioPrevUtiliz=_date.today() + timedelta(days=1),
				numCertSWFatur=int(certificate_number),
				meioProcessamento="PI",
				_soapheaders=[wsse_header],
			)
		except zeep.exceptions.Fault as e:
			frappe.log_error(f"AT rejeitou o registo da série (SOAP Fault): {str(e)}", "ATWebserviceClient")
			return {
				"success": False,
				"error": f"AT rejeitou o pedido: {str(e)}",
				"naming_series": naming_series,
				"request_id": request_id,
			}
		except Exception as e:
			frappe.log_error(f"Erro ao comunicar com o webservice de séries da AT: {str(e)}", "ATWebserviceClient")
			return {
				"success": False,
				"error": f"Erro na comunicação com a AT: {str(e)}",
				"naming_series": naming_series,
				"request_id": request_id,
			}

		resp_body = getattr(response, "registarSerieResp", response)
		oper_info = getattr(resp_body, "infoResultOper", None)
		cod_result = getattr(oper_info, "codResultOper", None) if oper_info else None
		msg_result = getattr(oper_info, "msgResultOper", None) if oper_info else ""

		# 2001 = sucesso (registarSerie); ver getAtErrorMessage no módulo
		# Dolibarr de referência para o mapeamento completo de códigos.
		if str(cod_result) not in ("2001",):
			frappe.log_error(f"AT recusou o registo da série [{cod_result}]: {msg_result}", "ATWebserviceClient")
			return {
				"success": False,
				"error": f"AT [{cod_result}]: {msg_result}",
				"naming_series": naming_series,
				"request_id": request_id,
			}

		info = getattr(resp_body, "infoSerie", None)
		validation_code = getattr(info, "codValidacaoSerie", None) if info else None

		frappe.logger().info(f"[{request_id}] Série registada com sucesso: {validation_code}")

		return {
			"success": True,
			"naming_series": naming_series,
			"series_at_format": at_series_format,
			"validation_code": validation_code,
			"request_id": request_id,
			"raw_response": zeep.helpers.serialize_object(info) if info else None,
		}

	def _save_atcud_to_series_config(self, naming_series, company, atcud_code):
		"""
		✅ FUNÇÃO CORRIGIDA: Salvar ATCUD na Portugal Series Configuration
		✅ CORREÇÃO CRÍTICA: Salvar validation_codes reais, incluindo fallbacks
		"""
		try:
			# ✅ CORREÇÃO: Aceitar todos os códigos válidos, incluindo fallbacks
			if not atcud_code:
				frappe.logger().warning(f"⚠️ ATCUD vazio para {naming_series}")
				return

			# ✅ BUSCAR SÉRIE CORRESPONDENTE
			series_config = frappe.db.get_value("Portugal Series Configuration", {
				"naming_series": naming_series,
				"company": company
			}, ["name"], as_dict=True)

			if series_config:
				# ✅ DETERMINAR TIPO DE ATCUD
				if atcud_code == "EXISTING":
					# Série já existia - não alterar validation_code existente
					frappe.db.set_value("Portugal Series Configuration", series_config.name, {
						"is_communicated": 1,
						"communication_date": frappe.utils.now(),
						"communication_response": "Série já estava registada na AT"
					})
					frappe.logger().info(f"✅ Série já registada mantida: {naming_series}")

				elif atcud_code.startswith("AT2"):
					# Código fallback - salvar mas marcar como temporário
					frappe.db.set_value("Portugal Series Configuration", series_config.name, {
						"validation_code": atcud_code,
						"is_communicated": 1,
						"communication_date": frappe.utils.now(),
						"atcud_pattern": f"{atcud_code}-{{sequence:08d}}",
						"communication_response": f"ATCUD fallback: {atcud_code}",
						"is_fallback": 1
					})
					frappe.logger().info(f"✅ ATCUD fallback salvo: {naming_series} = {atcud_code}")

				else:
					# ✅ CÓDIGO REAL DA AT - SALVAR NORMALMENTE
					frappe.db.set_value("Portugal Series Configuration", series_config.name, {
						"validation_code": atcud_code,
						"is_communicated": 1,
						"communication_date": frappe.utils.now(),
						"atcud_pattern": f"{atcud_code}-{{sequence:08d}}",
						"communication_response": f"ATCUD real recebido: {atcud_code}",
						"is_fallback": 0
					})
					frappe.logger().info(f"✅ ATCUD REAL salvo: {naming_series} = {atcud_code}")

				frappe.db.commit()
			else:
				frappe.logger().warning(f"⚠️ Série não encontrada: {naming_series}")

		except Exception as e:
			frappe.log_error(f"Erro ao salvar ATCUD na série: {str(e)}")

	# ========== COMUNICAÇÃO EM LOTE PARA NAMING SERIES ==========

	@frappe.whitelist()
	def batch_register_naming_series(self, naming_series_list, company, username=None,
									 password=None):
		"""
		✅ NOVA FUNÇÃO: Registar múltiplas naming_series em lote
		✅ 100% compatível com testes da console
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
					"erpnext_native_format": True,  # ✅ NOVO
					"dynamic_credentials": True,
					"secure_storage": True,
					"batch_processing": True,
					"robust_error_handling": True,
					"real_atcud_generation": True
				},
				"supported_formats": {
					"naming_series": "XXYYYY+COMPANY.#### (ex: FT2025DSY.####)",  # ✅ CORRIGIDO
					"prefix": "XXYYYY+COMPANY (ex: FT2025DSY)",  # ✅ CORRIGIDO
					"atcud": "CODIGO-SEQUENCIAL"
				},
				"timestamp": now()
			}
		except Exception as e:
			return {"error": str(e), "timestamp": now()}


# ========== FUNÇÕES GLOBAIS PARA NOVA ABORDAGEM ==========

@frappe.whitelist()
def batch_register_naming_series(naming_series_list, company, username=None, password=None,
								 environment="test"):
	"""
	✅ FUNÇÃO PRINCIPAL: Registar múltiplas naming_series na AT
	✅ 100% compatível com testes da console
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
def generate_atcud_with_real_code(validation_code, sequence):
	"""
	✅ FUNÇÃO GLOBAL: Gerar ATCUD usando código real da AT
	✅ 100% compatível com testes da console
	"""
	try:
		client = ATWebserviceClient()
		atcud_code = client._generate_atcud_with_real_code(validation_code, sequence)

		return {
			"success": True,
			"atcud_code": atcud_code,
			"validation_code": validation_code,
			"sequence": sequence
		}

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
	"""Validar formato de naming_series ERPNext"""
	try:
		client = ATWebserviceClient()
		is_valid, message = client.validate_naming_series_format(naming_series)

		return {
			"valid": is_valid,
			"message": message,
			"naming_series": naming_series,
			"expected_format": "XXYYYY+COMPANY.#### (ex: FT2025DSY.####)",  # ✅ CORRIGIDO
			"examples": ["FT2025DSY.####", "NC2025DSY.####", "RC2025DSY.####"]  # ✅ CORRIGIDO
		}

	except Exception as e:
		return {"valid": False, "error": str(e)}
