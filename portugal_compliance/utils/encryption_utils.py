import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password, set_encrypted_password
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib
import secrets


class EncryptionUtils:
	def __init__(self):
		self.encryption_key = self._get_encryption_key()
		self.fernet = Fernet(self.encryption_key)

	def _get_encryption_key(self):
		"""
		Obtém chave de encriptação do site_config.json ou gera uma nova
		"""
		try:
			# Tentar obter chave do site_config
			site_config = frappe.get_site_config()
			encryption_key = site_config.get('portugal_compliance_encryption_key')

			if not encryption_key:
				# Gerar nova chave se não existir
				encryption_key = self._generate_encryption_key()
				self._save_encryption_key(encryption_key)

			# Converter para formato Fernet se necessário
			if isinstance(encryption_key, str):
				# Derivar chave usando PBKDF2
				kdf = PBKDF2HMAC(
					algorithm=hashes.SHA256(),
					length=32,
					salt=b'portugal_compliance_salt',
					iterations=100000,
				)
				key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
				return key

			return encryption_key

		except Exception as e:
			frappe.log_error(f"Erro ao obter chave de encriptação: {str(e)}", "Encryption Utils")
			# Usar chave padrão como fallback (não recomendado para produção)
			return Fernet.generate_key()

	def _generate_encryption_key(self):
		"""
		Gera nova chave de encriptação segura
		"""
		return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

	def _save_encryption_key(self, key):
		"""
		Salva chave de encriptação no site_config.json
		"""
		try:
			frappe.conf.portugal_compliance_encryption_key = key
			frappe.conf.save()
		except Exception as e:
			frappe.log_error(f"Erro ao salvar chave de encriptação: {str(e)}", "Encryption Utils")

	def encrypt_data(self, data):
		"""
		Encripta dados usando Fernet (AES 128 em modo CBC com HMAC SHA256)
		"""
		try:
			if not data:
				return data

			# Converter para string se necessário
			if not isinstance(data, str):
				data = str(data)

			# Encriptar dados
			encrypted_data = self.fernet.encrypt(data.encode('utf-8'))

			# Retornar como string base64
			return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

		except Exception as e:
			frappe.log_error(f"Erro ao encriptar dados: {str(e)}", "Encryption Utils")
			return data

	def decrypt_data(self, encrypted_data):
		"""
		Desencripta dados usando Fernet
		"""
		try:
			if not encrypted_data:
				return encrypted_data

			# Decodificar base64
			encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))

			# Desencriptar dados
			decrypted_data = self.fernet.decrypt(encrypted_bytes)

			return decrypted_data.decode('utf-8')

		except Exception as e:
			frappe.log_error(f"Erro ao desencriptar dados: {str(e)}", "Encryption Utils")
			return encrypted_data

	def encrypt_sensitive_field(self, doctype, docname, fieldname, value):
		"""
		Encripta campo sensível usando sistema nativo do Frappe
		"""
		try:
			if not value:
				return

			# Usar sistema de passwords do Frappe para campos sensíveis
			set_encrypted_password(doctype, docname, value, fieldname)

		except Exception as e:
			frappe.log_error(f"Erro ao encriptar campo sensível: {str(e)}", "Encryption Utils")

	def decrypt_sensitive_field(self, doctype, docname, fieldname):
		"""
		Desencripta campo sensível usando sistema nativo do Frappe
		"""
		try:
			return get_decrypted_password(doctype, docname, fieldname)

		except Exception as e:
			frappe.log_error(f"Erro ao desencriptar campo sensível: {str(e)}", "Encryption Utils")
			return None

	def hash_data(self, data, algorithm='sha256'):
		"""
		Gera hash dos dados para verificação de integridade
		"""
		try:
			if not data:
				return None

			# Converter para string se necessário
			if not isinstance(data, str):
				data = str(data)

			# Gerar hash
			if algorithm == 'sha256':
				return hashlib.sha256(data.encode('utf-8')).hexdigest()
			elif algorithm == 'md5':
				return hashlib.md5(data.encode('utf-8')).hexdigest()
			else:
				raise ValueError(f"Algoritmo de hash não suportado: {algorithm}")

		except Exception as e:
			frappe.log_error(f"Erro ao gerar hash: {str(e)}", "Encryption Utils")
			return None

	def verify_hash(self, data, hash_value, algorithm='sha256'):
		"""
		Verifica se hash corresponde aos dados
		"""
		try:
			calculated_hash = self.hash_data(data, algorithm)
			return calculated_hash == hash_value

		except Exception as e:
			frappe.log_error(f"Erro ao verificar hash: {str(e)}", "Encryption Utils")
			return False

	def encrypt_atcud_validation_code(self, validation_code):
		"""
		Encripta código de validação ATCUD
		"""
		return self.encrypt_data(validation_code)

	def decrypt_atcud_validation_code(self, encrypted_code):
		"""
		Desencripta código de validação ATCUD
		"""
		return self.decrypt_data(encrypted_code)

	def encrypt_certificate_data(self, certificate_content):
		"""
		Encripta conteúdo de certificado SSL
		"""
		try:
			# Para certificados, usar encriptação mais forte
			return self.encrypt_data(certificate_content)

		except Exception as e:
			frappe.log_error(f"Erro ao encriptar certificado: {str(e)}", "Encryption Utils")
			return certificate_content

	def decrypt_certificate_data(self, encrypted_certificate):
		"""
		Desencripta conteúdo de certificado SSL
		"""
		try:
			return self.decrypt_data(encrypted_certificate)

		except Exception as e:
			frappe.log_error(f"Erro ao desencriptar certificado: {str(e)}", "Encryption Utils")
			return encrypted_certificate

	def generate_secure_token(self, length=32):
		"""
		Gera token seguro para sessões ou identificadores únicos
		"""
		try:
			return secrets.token_urlsafe(length)

		except Exception as e:
			frappe.log_error(f"Erro ao gerar token seguro: {str(e)}", "Encryption Utils")
			return None

	def encrypt_document_hash(self, document_content):
		"""
		Gera hash encriptado para integridade de documentos SAF-T
		"""
		try:
			# Gerar hash SHA-256 do conteúdo
			content_hash = self.hash_data(document_content, 'sha256')

			# Encriptar o hash para proteção adicional
			return self.encrypt_data(content_hash)

		except Exception as e:
			frappe.log_error(f"Erro ao encriptar hash do documento: {str(e)}", "Encryption Utils")
			return None

	def verify_document_integrity(self, document_content, encrypted_hash):
		"""
		Verifica integridade de documento usando hash encriptado
		"""
		try:
			# Desencriptar hash armazenado
			stored_hash = self.decrypt_data(encrypted_hash)

			# Calcular hash atual do documento
			current_hash = self.hash_data(document_content, 'sha256')

			return stored_hash == current_hash

		except Exception as e:
			frappe.log_error(f"Erro ao verificar integridade do documento: {str(e)}",
							 "Encryption Utils")
			return False

	def secure_delete_key(self):
		"""
		Remove chave de encriptação de forma segura (para rotação de chaves)
		"""
		try:
			# Remover chave do site_config
			if hasattr(frappe.conf, 'portugal_compliance_encryption_key'):
				delattr(frappe.conf, 'portugal_compliance_encryption_key')
				frappe.conf.save()

			# Limpar variáveis da memória
			self.encryption_key = None
			self.fernet = None

			return True

		except Exception as e:
			frappe.log_error(f"Erro ao remover chave de encriptação: {str(e)}", "Encryption Utils")
			return False

	def rotate_encryption_key(self):
		"""
		Rotaciona chave de encriptação (gera nova chave)
		"""
		try:
			# Gerar nova chave
			new_key = self._generate_encryption_key()

			# Salvar nova chave
			self._save_encryption_key(new_key)

			# Atualizar instância atual
			self.encryption_key = self._get_encryption_key()
			self.fernet = Fernet(self.encryption_key)

			frappe.logger().info("Chave de encriptação rotacionada com sucesso")
			return True

		except Exception as e:
			frappe.log_error(f"Erro ao rotacionar chave de encriptação: {str(e)}",
							 "Encryption Utils")
			return False

	@frappe.whitelist()
	def test_encryption(self, test_data="Portugal Compliance Test"):
		"""
		Testa funcionalidade de encriptação - método whitelisted para debugging
		"""
		try:
			# Encriptar dados de teste
			encrypted = self.encrypt_data(test_data)

			# Desencriptar dados
			decrypted = self.decrypt_data(encrypted)

			# Verificar se dados são iguais
			success = test_data == decrypted

			return {
				"status": "success" if success else "error",
				"original": test_data,
				"encrypted": encrypted[:50] + "..." if len(encrypted) > 50 else encrypted,
				"decrypted": decrypted,
				"match": success
			}

		except Exception as e:
			return {
				"status": "error",
				"message": str(e)
			}


# Funções utilitárias globais
def encrypt_portugal_data(data):
	"""
	Função global para encriptar dados relacionados com Portugal Compliance
	"""
	utils = EncryptionUtils()
	return utils.encrypt_data(data)


def decrypt_portugal_data(encrypted_data):
	"""
	Função global para desencriptar dados relacionados com Portugal Compliance
	"""
	utils = EncryptionUtils()
	return utils.decrypt_data(encrypted_data)


def encrypt_validation_code(validation_code):
	"""
	Função específica para encriptar códigos de validação ATCUD
	"""
	utils = EncryptionUtils()
	return utils.encrypt_atcud_validation_code(validation_code)


def decrypt_validation_code(encrypted_code):
	"""
	Função específica para desencriptar códigos de validação ATCUD
	"""
	utils = EncryptionUtils()
	return utils.decrypt_atcud_validation_code(encrypted_code)


def generate_document_hash(document_content):
	"""
	Gera hash seguro para documentos SAF-T
	"""
	utils = EncryptionUtils()
	return utils.encrypt_document_hash(document_content)


def verify_document_hash(document_content, stored_hash):
	"""
	Verifica integridade de documento SAF-T
	"""
	utils = EncryptionUtils()
	return utils.verify_document_integrity(document_content, stored_hash)


# Hook para inicialização do módulo
def setup_encryption():
	"""
	Configura encriptação durante instalação do módulo
	"""
	try:
		utils = EncryptionUtils()

		# Testar encriptação
		test_result = utils.test_encryption()

		if test_result["status"] == "success":
			frappe.logger().info(
				"Sistema de encriptação Portugal Compliance configurado com sucesso")
		else:
			frappe.log_error("Falha na configuração do sistema de encriptação", "Encryption Utils")

	except Exception as e:
		frappe.log_error(f"Erro na configuração da encriptação: {str(e)}", "Encryption Utils")
