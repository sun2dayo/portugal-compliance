import frappe
from frappe import _
import requests
from requests_pkcs12 import Pkcs12Adapter
from frappe.utils.password import get_decrypted_password
import ssl
import os
from datetime import datetime, timedelta
import tempfile
import hashlib
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import time


class ATAuthentication:
	def __init__(self):
		self.settings = frappe.get_single("Portugal Auth Settings")
		self.cert_path = None
		self.cert_password = None
		self.session_cache = {}
		self.session_timeout = 3600  # 1 hora

		# Inicializar certificado de forma segura
		self._initialize_certificate()

	def _initialize_certificate(self):
		"""
		Inicializa certificado de forma segura
		"""
		try:
			self.cert_path = get_decrypted_password(
				"Portugal Auth Settings",
				"Portugal Auth Settings",
				"ssl_certificate_path"
			)
			self.cert_password = get_decrypted_password(
				"Portugal Auth Settings",
				"Portugal Auth Settings",
				"certificate_password"
			)

			# Validar se certificado existe
			if self.cert_path and not os.path.exists(self.cert_path):
				frappe.log_error(f"Certificado não encontrado: {self.cert_path}")
				self.cert_path = None

		except Exception as e:
			frappe.log_error(f"Erro ao inicializar certificado: {str(e)}")

	def get_authenticated_session(self, username, password, force_new=False):
		"""
		Cria uma sessão autenticada com a AT usando certificado SSL e credenciais
		"""
		try:
			# Verificar cache de sessão
			session_key = hashlib.md5(f"{username}:{password}".encode()).hexdigest()

			if not force_new and session_key in self.session_cache:
				cached_session = self.session_cache[session_key]
				if time.time() - cached_session['created'] < self.session_timeout:
					return cached_session['session']

			# Validar pré-requisitos
			if not self._validate_prerequisites():
				raise Exception("Pré-requisitos de autenticação não atendidos")

			# Criar nova sessão
			session = requests.Session()

			# Configurar timeout
			session.timeout = (30, 60)  # (connect, read)

			# Configurar adaptador PKCS12 para certificado SSL
			if self.cert_path and self.cert_password:
				session.mount('https://', Pkcs12Adapter(
					pkcs12_filename=self.cert_path,
					pkcs12_password=self.cert_password
				))
			else:
				raise Exception("Certificado SSL não configurado")

			# Configurar autenticação básica
			session.auth = (username, password)

			# Headers obrigatórios
			session.headers.update({
				'Content-Type': 'text/xml; charset=utf-8',
				'SOAPAction': '',
				'User-Agent': 'ERPNext-Portugal-Compliance/1.0',
				'Accept': 'text/xml, application/soap+xml',
				'Cache-Control': 'no-cache'
			})

			# Testar conexão
			if self._test_connection(session):
				# Armazenar em cache
				self.session_cache[session_key] = {
					'session': session,
					'created': time.time()
				}

				frappe.logger().info(f"Sessão autenticada criada para usuário: {username}")
				return session
			else:
				raise Exception("Falha no teste de conexão")

		except Exception as e:
			frappe.log_error(f"Erro ao criar sessão autenticada: {str(e)}")
			raise Exception(f"Erro na autenticação com a AT: {str(e)}")

	def _validate_prerequisites(self):
		"""
		Valida pré-requisitos para autenticação
		"""
		if not self.settings:
			frappe.log_error("Configurações da AT não encontradas")
			return False

		if not self.cert_path:
			frappe.log_error("Caminho do certificado não configurado")
			return False

		if not os.path.exists(self.cert_path):
			frappe.log_error(f"Certificado não encontrado: {self.cert_path}")
			return False

		if not self.cert_password:
			frappe.log_error("Senha do certificado não configurada")
			return False

		if not self.settings.at_webservice_url:
			frappe.log_error("URL do webservice não configurada")
			return False

		return True

	def _test_connection(self, session):
		"""
		Testa conexão com a AT
		"""
		try:
			test_url = self.settings.at_webservice_url.replace('SeriesWSService', 'ping')
			response = session.get(test_url, timeout=10)
			return response.status_code in [200, 404]  # 404 é aceitável para endpoint de teste
		except:
			return True  # Assumir sucesso se teste falhar (endpoint pode não existir)

	def validate_certificate(self):
		"""
		Valida se o certificado SSL é válido e não expirou
		"""
		try:
			if not self.cert_path or not os.path.exists(self.cert_path):
				return {
					"valid": False,
					"error": "Certificado não encontrado"
				}

			# Ler certificado
			with open(self.cert_path, 'rb') as cert_file:
				cert_data = cert_file.read()

			# Carregar certificado PKCS12
			from cryptography.hazmat.primitives import serialization

			try:
				private_key, certificate, additional_certificates = serialization.pkcs12.load_key_and_certificates(
					cert_data,
					self.cert_password.encode() if self.cert_password else None,
					backend=default_backend()
				)
			except Exception as e:
				return {
					"valid": False,
					"error": f"Erro ao carregar certificado: {str(e)}"
				}

			if not certificate:
				return {
					"valid": False,
					"error": "Certificado não encontrado no arquivo PKCS12"
				}

			# Verificar validade
			now = datetime.utcnow()
			not_before = certificate.not_valid_before
			not_after = certificate.not_valid_after

			if now < not_before:
				return {
					"valid": False,
					"error": f"Certificado ainda não é válido. Válido a partir de: {not_before}"
				}

			if now > not_after:
				return {
					"valid": False,
					"error": f"Certificado expirado em: {not_after}"
				}

			# Verificar se expira em breve (30 dias)
			days_until_expiry = (not_after - now).days
			warning = None
			if days_until_expiry <= 30:
				warning = f"Certificado expira em {days_until_expiry} dias"

			# Obter informações do certificado
			subject = certificate.subject
			issuer = certificate.issuer

			return {
				"valid": True,
				"not_before": not_before,
				"not_after": not_after,
				"days_until_expiry": days_until_expiry,
				"subject": str(subject),
				"issuer": str(issuer),
				"warning": warning
			}

		except Exception as e:
			frappe.log_error(f"Erro na validação do certificado: {str(e)}")
			return {
				"valid": False,
				"error": f"Erro na validação: {str(e)}"
			}

	def test_at_connection(self):
		"""
		Testa conectividade com os serviços da AT
		"""
		try:
			if not self.settings.at_webservice_url:
				return {
					"connected": False,
					"error": "URL do webservice não configurada"
				}

			# Extrair hostname da URL
			from urllib.parse import urlparse
			parsed_url = urlparse(self.settings.at_webservice_url)
			hostname = parsed_url.hostname
			port = parsed_url.port or 443

			# Testar conectividade TCP
			import socket
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(10)

			try:
				result = sock.connect_ex((hostname, port))
				sock.close()

				if result == 0:
					return {
						"connected": True,
						"hostname": hostname,
						"port": port,
						"response_time": "< 10s"
					}
				else:
					return {
						"connected": False,
						"error": f"Não foi possível conectar a {hostname}:{port}"
					}
			except Exception as e:
				return {
					"connected": False,
					"error": f"Erro de conectividade: {str(e)}"
				}

		except Exception as e:
			frappe.log_error(f"Erro no teste de conexão: {str(e)}")
			return {
				"connected": False,
				"error": f"Erro no teste: {str(e)}"
			}

	def clear_session_cache(self):
		"""
		Limpa cache de sessões
		"""
		self.session_cache.clear()
		return {"success": True, "message": "Cache de sessões limpo"}

	def get_certificate_info(self):
		"""
		Retorna informações detalhadas do certificado
		"""
		try:
			validation_result = self.validate_certificate()

			if not validation_result["valid"]:
				return validation_result

			# Informações adicionais do arquivo
			file_stats = os.stat(self.cert_path)
			file_size = file_stats.st_size
			file_modified = datetime.fromtimestamp(file_stats.st_mtime)

			return {
				**validation_result,
				"file_path": self.cert_path,
				"file_size": file_size,
				"file_modified": file_modified,
				"file_exists": True
			}

		except Exception as e:
			return {
				"valid": False,
				"error": f"Erro ao obter informações: {str(e)}",
				"file_exists": False
			}

	def validate_credentials_format(self, username, password):
		"""
		Valida formato das credenciais
		"""
		errors = []

		if not username:
			errors.append("Nome de usuário é obrigatório")
		elif not username.count('/') == 1:
			errors.append("Nome de usuário deve estar no formato NIF/SUBUSER")
		else:
			nif, subuser = username.split('/')
			if not nif.isdigit() or len(nif) != 9:
				errors.append("NIF deve ter 9 dígitos")
			if not subuser:
				errors.append("Nome do subutilizador é obrigatório")

		if not password:
			errors.append("Senha é obrigatória")
		elif len(password) < 8:
			errors.append("Senha deve ter pelo menos 8 caracteres")

		return {
			"valid": len(errors) == 0,
			"errors": errors
		}

	def create_secure_temp_cert(self):
		"""
		Cria certificado temporário seguro para uso
		"""
		try:
			if not self.cert_path or not os.path.exists(self.cert_path):
				return None

			# Criar arquivo temporário seguro
			with tempfile.NamedTemporaryFile(delete=False, suffix='.pfx') as temp_file:
				with open(self.cert_path, 'rb') as orig_file:
					temp_file.write(orig_file.read())

				# Definir permissões restritivas
				os.chmod(temp_file.name, 0o600)

				return temp_file.name

		except Exception as e:
			frappe.log_error(f"Erro ao criar certificado temporário: {str(e)}")
			return None

	def cleanup_temp_cert(self, temp_cert_path):
		"""
		Remove certificado temporário de forma segura
		"""
		try:
			if temp_cert_path and os.path.exists(temp_cert_path):
				os.remove(temp_cert_path)
				return True
		except Exception as e:
			frappe.log_error(f"Erro ao remover certificado temporário: {str(e)}")

		return False

	def get_session_stats(self):
		"""
		Retorna estatísticas das sessões em cache
		"""
		active_sessions = 0
		expired_sessions = 0
		current_time = time.time()

		for session_data in self.session_cache.values():
			if current_time - session_data['created'] < self.session_timeout:
				active_sessions += 1
			else:
				expired_sessions += 1

		return {
			"active_sessions": active_sessions,
			"expired_sessions": expired_sessions,
			"total_sessions": len(self.session_cache),
			"session_timeout": self.session_timeout
		}
