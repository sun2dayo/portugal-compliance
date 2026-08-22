# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Ferramentas de diagnóstico de emergência para a comunicação com a AT.

Nascem da Auditoria Comparativa com o módulo de referência Dolibarr
(2026-08-23): a referência tem ~15 scripts devtools persistidos para
cenários exatamente como este (chave/certificado que deixou de
corresponder, ligação que começou a falhar sem alteração de código
aparente). Nós nunca tínhamos nada persistido - cada diagnóstico desta
sessão foi feito ad-hoc. Estas duas funções cobrem os dois cenários de
maior risco, para correr sem programador disponível:

  bench --site <site> execute portugal_compliance.utils.diagnostics.test_at_connection
  bench --site <site> execute portugal_compliance.utils.diagnostics.verify_key_pair

Ver README.md para o guia de uso completo.
"""

import frappe


def test_at_connection():
	"""
	Testa se a configuração atual (mTLS + credenciais WS-Security) é
	suficiente para abrir uma sessão válida com o webservice de séries
	da AT - sem chegar a registar/consultar nada. Não usa rede se os
	certificados/credenciais já estiverem claramente em falta.
	"""
	from portugal_compliance.utils.at_webservice import test_connection

	result = test_connection()

	print("=" * 60)
	print("TESTE DE LIGAÇÃO AT")
	print("=" * 60)
	if result.get("connected"):
		print(f"✅ {result.get('message')}")
		print(f"   Ambiente: {result.get('environment')}")
	else:
		print(f"❌ Falha: {result.get('error')}")
		print(f"   Ambiente: {result.get('environment')}")
	print("=" * 60)
	return result


def verify_key_pair():
	"""
	Verifica matematicamente se a chave privada mTLS e o certificado
	público configurados em Portugal Auth Settings formam um par válido
	- comparando o módulo/expoente da chave pública derivada da chave
	privada com a chave pública embutida no certificado. Um par
	desemparelhado (ex: certificado renovado sem trocar a chave
	privada correspondente) causa sempre "Could not connect to host" ou
	falha de handshake TLS - erro que, visto de fora, é indistinguível
	de um problema de rede/firewall. Este comando isola essa causa em
	segundos, sem precisar de uma ligação de rede real à AT.
	"""
	import os
	from cryptography.hazmat.primitives import serialization
	from cryptography import x509
	from cryptography.hazmat.backends import default_backend

	print("=" * 60)
	print("VERIFICAÇÃO DE PAR DE CHAVES (mTLS)")
	print("=" * 60)

	settings = frappe.get_single("Portugal Auth Settings")
	key_path = settings.get("mtls_private_key_path")
	cert_path = settings.get("mtls_certificate_path")

	result = {"key_path": key_path, "cert_path": cert_path, "match": None, "error": None}

	if not key_path or not os.path.exists(key_path):
		msg = f"Chave privada não encontrada: {key_path}"
		print(f"❌ {msg}")
		result["error"] = msg
		return result

	if not cert_path or not os.path.exists(cert_path):
		msg = f"Certificado público não encontrado: {cert_path}"
		print(f"❌ {msg}")
		result["error"] = msg
		return result

	try:
		with open(key_path, "rb") as f:
			private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

		with open(cert_path, "rb") as f:
			cert_bytes = f.read()
		try:
			cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
		except ValueError:
			cert = x509.load_der_x509_certificate(cert_bytes, default_backend())

		priv_public_numbers = private_key.public_key().public_numbers()
		cert_public_numbers = cert.public_key().public_numbers()

		match = (
			priv_public_numbers.n == cert_public_numbers.n
			and priv_public_numbers.e == cert_public_numbers.e
		)
		result["match"] = match

		expiry = cert.not_valid_after_utc if hasattr(cert, "not_valid_after_utc") else cert.not_valid_after
		print(f"Chave privada: {key_path}")
		print(f"Certificado:   {cert_path}")
		print(f"Certificado válido até: {expiry}")
		if match:
			print("✅ A chave privada e o certificado formam um par válido.")
		else:
			print("❌ A chave privada NÃO corresponde ao certificado (par desemparelhado).")
			print("   Causa típica: certificado renovado sem substituir a chave privada,")
			print("   ou vice-versa. Ver docs/DevOps: renovação de certificado.")

	except Exception as e:
		print(f"❌ Erro ao ler/comparar chave e certificado: {str(e)}")
		result["error"] = str(e)

	print("=" * 60)
	return result
