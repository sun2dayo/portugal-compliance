# -*- coding: utf-8 -*-
"""
Assinatura digital de documentos fiscais e cadeia de hash por serie
documental, conforme Portaria 363/2010 e legislacao associada.

Nao existia nenhuma implementacao disto no modulo antes desta fase -
encryption_utils.py so fazia encriptacao simetrica (Fernet) de dados
em repouso, o que nao satisfaz o requisito legal.

Especificacao de referencia: extraida do modulo Dolibarr
"complianceportugal" (NovaDX), que ja opera em producao e cujo
CHANGELOG documenta correcoes feitas em resposta a rejeicoes reais
da AT. Os pontos-chave replicados aqui:

  - Algoritmo: RSA-SHA1 (PKCS#1 v1.5), chave privada RSA, output em
    Base64.
  - Cadeia: cada documento assina uma string que inclui a hash Base64
    do documento ANTERIOR da MESMA serie. Vazio ("") se for o
    primeiro documento da serie. Misturar series invalida a cadeia.
  - String a assinar: "DataDoc;DataSistema;Referencia;Total;HashAnterior"
    - o formato exato de cada campo varia por tipo de documento,
      ver DOCUMENT_SIGNING_SPEC abaixo.
  - Hash control: 4 caracteres da assinatura Base64, posicoes 1, 11,
    21, 31 (1-indexed) - usados no campo Q do QR code.

Nota: a chave de assinatura e distinta da chave/certificado usado
para mTLS na comunicacao com o webservice da AT (ver Portugal Auth
Settings). Usar a mesma chave para os dois fins foi um erro do
modulo Dolibarr numa versao anterior (ver CHANGELOG dele, "Dual Key
Architecture") - nao repetir aqui.
"""

import base64

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, flt

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature


class SignatureError(Exception):
	pass


# ---------------------------------------------------------------------------
# Especificacao da string a assinar, por tipo de documento.
# Campos:
#   doc_code       -> prefixo usado na "Referencia" (ex: "FT", "NC", "GT")
#   date_field     -> campo do doc usado como DataDoc (formato YYYY-MM-DD)
#   system_date_field -> campo do doc usado como DataSistema
#                        (formato YYYY-MM-DDTHH:MM:SS)
#   total_field    -> campo do doc usado como Total (2 casas decimais);
#                     None => Total fixo "0.00" (caso das guias de
#                     transporte, conforme spec de referencia)
#   total_absolute -> se True, usar sempre valor absoluto/positivo
#                     (Portaria 302/2016, caso das notas de credito)
# ---------------------------------------------------------------------------
DOCUMENT_SIGNING_SPEC = {
	"Sales Invoice": {
		"doc_code": "FT",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": "grand_total",
		"total_absolute": True,
	},
	"Purchase Invoice": {
		"doc_code": "FC",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": "grand_total",
		"total_absolute": True,
	},
	"POS Invoice": {
		"doc_code": "FS",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": "grand_total",
		"total_absolute": True,
	},
	"Payment Entry": {
		"doc_code": "RC",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": "paid_amount",
		"total_absolute": True,
	},
	"Delivery Note": {
		"doc_code": "GT",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": None,  # guias de transporte: Total fixo 0.00
		"total_absolute": False,
	},
	"Purchase Receipt": {
		"doc_code": "GR",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": None,
		"total_absolute": False,
	},
	"Stock Entry": {
		"doc_code": "GM",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": None,
		"total_absolute": False,
	},
	"Journal Entry": {
		"doc_code": "LC",
		"date_field": "posting_date",
		"system_date_field": "creation",
		"total_field": "total_debit",
		"total_absolute": True,
	},
}


def get_signing_spec(doctype):
	return DOCUMENT_SIGNING_SPEC.get(doctype)


def build_data_to_sign(doc, spec, series_prefix, sequence_number, previous_hash):
	"""
	Constroi a string "DataDoc;DataSistema;Referencia;Total;HashAnterior"
	para o documento, seguindo a especificacao do tipo de documento.
	"""
	doc_date_raw = doc.get(spec["date_field"])
	if not doc_date_raw:
		raise SignatureError(
			_("Documento {0} sem {1} definido - necessario para a assinatura digital").format(
				doc.name, spec["date_field"]
			)
		)
	data_doc = getdate(doc_date_raw).strftime("%Y-%m-%d")

	system_date_raw = doc.get(spec["system_date_field"]) or frappe.utils.now()
	data_sistema = get_datetime(system_date_raw).strftime("%Y-%m-%dT%H:%M:%S")

	referencia = f"{spec['doc_code']} {series_prefix}/{sequence_number}"

	if spec["total_field"] is None:
		total = "0.00"
	else:
		total_value = flt(doc.get(spec["total_field"]) or 0)
		if spec.get("total_absolute"):
			total_value = abs(total_value)
		total = f"{total_value:.2f}"

	return f"{data_doc};{data_sistema};{referencia};{total};{previous_hash or ''}"


# ---------------------------------------------------------------------------
# Carregamento da chave privada e assinatura
# ---------------------------------------------------------------------------

def _load_private_key():
	"""
	Carrega a chave privada RSA configurada em Portugal Auth Settings
	para assinatura de documentos (distinta da chave do webservice).
	"""
	settings = frappe.get_single("Portugal Auth Settings")
	key_path = settings.get("invoice_signing_key_path")

	if not key_path:
		raise SignatureError(
			_(
				"Chave privada de assinatura nao configurada. "
				"Defina 'Caminho da Chave Privada (PEM)' em Portugal Auth Settings."
			)
		)

	try:
		with open(key_path, "rb") as key_file:
			key_bytes = key_file.read()
	except OSError as e:
		raise SignatureError(
			_("Nao foi possivel ler a chave privada em {0}: {1}").format(key_path, str(e))
		)

	password = settings.get_password("invoice_signing_key_password", raise_exception=False)
	password_bytes = password.encode("utf-8") if password else None

	try:
		return serialization.load_pem_private_key(key_bytes, password=password_bytes)
	except (ValueError, TypeError) as e:
		raise SignatureError(_("Falha ao carregar a chave privada: {0}").format(str(e)))


def _extract_hash_control(signature_b64):
	"""
	4 caracteres da assinatura Base64 nas posicoes 1, 11, 21, 31
	(1-indexed, conforme especificacao do QR code da AT).
	"""
	positions_1_indexed = (1, 11, 21, 31)
	chars = []
	for pos in positions_1_indexed:
		idx = pos - 1
		if idx < len(signature_b64):
			chars.append(signature_b64[idx])
	return "".join(chars)


def _lock_series_for_signing(series_configuration):
	"""
	Bloqueio pessimista (SELECT ... FOR UPDATE) na linha da serie, para
	serializar a leitura da hash anterior entre documentos concorrentes
	da MESMA serie.

	Sem isto ha uma janela de corrida real: o ATCUD Log so e escrito em
	after_insert (ver document_hooks.generate_atcud_after_insert), nao
	aqui - se dois documentos da mesma serie forem submetidos quase em
	simultaneo, o segundo pode ler a "ultima hash" ANTES do primeiro ter
	terminado o commit da sua propria transacao (pedidos Frappe correm
	em transacoes separadas, cada um so visivel aos outros apos commit),
	e os dois ficam com o mesmo HashAnterior - quebra a cadeia sequencial
	exigida pela Portaria 363/2010.

	A alocacao do proprio numero de sequencia (doc.name) ja e segura -
	usa o contador atomico nativo do Frappe (ver
	atcud_generator._get_next_sequence_thread_safe) - o problema e
	especificamente a leitura da hash anterior, que este lock resolve:
	ao bloquear a linha da serie logo no inicio da assinatura e so a
	libertar no commit da transacao (fim do pedido), o segundo pedido
	fica bloqueado na leitura ate o primeiro terminar por completo,
	incluindo a escrita do seu proprio ATCUD Log em after_insert.
	"""
	if not series_configuration:
		frappe.logger().warning(
			"Assinatura sem series_configuration - bloqueio de concorrencia nao aplicado"
		)
		return
	frappe.db.sql(
		"SELECT name FROM `tabPortugal Series Configuration` WHERE name = %s FOR UPDATE",
		series_configuration,
	)


def get_previous_signature_hash(series_configuration, before_sequence_number):
	"""
	Obtem a hash de assinatura do documento anterior na MESMA serie
	(o de maior sequence_number ainda inferior ao atual). Vazio se
	nao existir nenhum (primeiro documento da serie).

	Adquire primeiro o lock de serie (ver _lock_series_for_signing) -
	tem de ser feito ANTES desta leitura, nao depois, para que o lock
	esteja mesmo a proteger o valor lido.
	"""
	_lock_series_for_signing(series_configuration)

	previous = frappe.db.get_value(
		"ATCUD Log",
		{
			"series_used": series_configuration,
			"sequence_number": ("<", before_sequence_number),
			"generation_status": "Success",
		},
		"signature_hash",
		order_by="sequence_number desc",
	)
	return previous or ""


def sign_document(doc, series_prefix, series_configuration, sequence_number):
	"""
	Assina digitalmente um documento fiscal, encadeado com o
	documento anterior da mesma serie.

	Retorna dict: signature_hash (base64), hash_control (4 chars),
	previous_signature_hash, data_to_sign (para auditoria), key_version.
	"""
	spec = get_signing_spec(doc.doctype)
	if not spec:
		raise SignatureError(
			_("Assinatura digital nao suportada para o tipo de documento {0}").format(doc.doctype)
		)

	previous_hash = get_previous_signature_hash(series_configuration, sequence_number)
	data_to_sign = build_data_to_sign(doc, spec, series_prefix, sequence_number, previous_hash)

	private_key = _load_private_key()

	try:
		signature_bytes = private_key.sign(
			data_to_sign.encode("utf-8"),
			padding.PKCS1v15(),
			hashes.SHA1(),
		)
	except Exception as e:
		raise SignatureError(_("Falha ao assinar o documento: {0}").format(str(e)))

	signature_hash = base64.b64encode(signature_bytes).decode("ascii")

	settings = frappe.get_single("Portugal Auth Settings")
	key_version = settings.get("invoice_signing_key_version") or "1"

	return {
		"signature_hash": signature_hash,
		"hash_control": _extract_hash_control(signature_hash),
		"previous_signature_hash": previous_hash,
		"data_to_sign": data_to_sign,
		"key_version": key_version,
	}


@frappe.whitelist()
def verify_signing_key_configured():
	"""
	Metodo whitelisted para a UI verificar se a chave de assinatura
	esta configurada, sem expor o caminho/password a utilizadores sem
	permissao para ver Portugal Auth Settings.
	"""
	if not frappe.has_permission("Portugal Auth Settings", "read"):
		frappe.throw(_("Sem permissao"), frappe.PermissionError)

	settings = frappe.get_single("Portugal Auth Settings")
	key_path = settings.get("invoice_signing_key_path")
	return {"configured": bool(key_path)}


# ---------------------------------------------------------------------------
# Verificacao da cadeia de assinaturas (Requisito 2.4 da auditoria de
# certificacao 2026-08-24) - nao existia nenhuma forma de confirmar, a
# posteriori, que a cadeia RSA-SHA1 gerada por sign_document() e
# realmente integra. Reconstroi cada data_to_sign a partir do
# documento (que a inviolabilidade em document_hooks.py garante nao
# ter mudado desde a assinatura) e verifica com a chave publica
# derivada da mesma chave privada usada para assinar.
# ---------------------------------------------------------------------------

def _get_public_key():
	private_key = _load_private_key()
	return private_key.public_key()


def _verify_single_entry(log, public_key, expected_previous_hash):
	"""
	Verifica uma entrada do ATCUD Log: continuidade da cadeia
	(previous_signature_hash bate com a hash do documento anterior) e
	validade criptografica da assinatura (RSA-SHA1 contra a chave
	publica). Devolve um dict de resultado, nunca lanca excecao - o
	chamador decide o que fazer com uma entrada invalida, o resto da
	cadeia continua a ser verificado.
	"""
	result = {
		"sequence_number": log.sequence_number,
		"document_type": log.document_type,
		"document_name": log.document_name,
		"atcud_code": log.atcud_code,
		"chain_ok": None,
		"signature_ok": None,
		"error": None,
	}

	result["chain_ok"] = (log.previous_signature_hash or "") == (expected_previous_hash or "")
	if not result["chain_ok"]:
		result["error"] = _(
			"Hash anterior não corresponde à assinatura do documento anterior da série "
			"(esperado {0}, encontrado {1}) - cadeia quebrada."
		).format(expected_previous_hash or "(vazio)", log.previous_signature_hash or "(vazio)")

	try:
		doc = frappe.get_doc(log.document_type, log.document_name)
		spec = get_signing_spec(doc.doctype)
		if not spec:
			raise SignatureError(_("Doctype {0} sem especificação de assinatura").format(doc.doctype))

		series_prefix = frappe.db.get_value("Portugal Series Configuration", log.series_used, "prefix")
		if not series_prefix:
			raise SignatureError(_("Série {0} não encontrada").format(log.series_used))

		data_to_sign = build_data_to_sign(
			doc, spec, series_prefix, log.sequence_number, log.previous_signature_hash
		)

		signature_bytes = base64.b64decode(log.signature_hash)
		public_key.verify(
			signature_bytes,
			data_to_sign.encode("utf-8"),
			padding.PKCS1v15(),
			hashes.SHA1(),
		)
		result["signature_ok"] = True

	except InvalidSignature:
		result["signature_ok"] = False
		result["error"] = (result["error"] + " " if result["error"] else "") + _(
			"Assinatura RSA inválida para os dados atuais do documento - documento pode ter "
			"sido alterado após a assinatura, ou a assinatura foi corrompida/forjada."
		)
	except frappe.DoesNotExistError:
		result["signature_ok"] = False
		result["error"] = (result["error"] + " " if result["error"] else "") + _(
			"Documento {0} {1} não existe mais na base de dados - viola a inviolabilidade "
			"fiscal (Portaria 363/2010)."
		).format(log.document_type, log.document_name)
	except Exception as e:
		result["signature_ok"] = False
		result["error"] = (result["error"] + " " if result["error"] else "") + str(e)

	return result


@frappe.whitelist()
def verify_signature_chain(series_configuration=None, company=None):
	"""
	Verifica a integridade completa da cadeia de assinaturas RSA-SHA1
	de uma série (series_configuration) ou de todas as séries de uma
	empresa (company). Sem nenhum dos dois parâmetros, verifica todas
	as séries de todas as empresas.

	Devolve um resumo por série com o detalhe de cada documento -
	pensado para ser corrido sob pedido por um auditor (via API, bench
	execute, ou um botão na UI), não em cada submissão de documento.
	"""
	if not frappe.has_permission("ATCUD Log", "read"):
		frappe.throw(_("Sem permissão"), frappe.PermissionError)

	filters = {"generation_status": "Success"}
	if series_configuration:
		filters["series_used"] = series_configuration
	elif company:
		filters["company"] = company

	logs = frappe.get_all(
		"ATCUD Log",
		filters=filters,
		fields=["name", "series_used", "sequence_number", "document_type", "document_name",
				"atcud_code", "signature_hash", "previous_signature_hash"],
		order_by="series_used, sequence_number asc",
	)

	if not logs:
		return {"success": True, "series_checked": 0, "documents_checked": 0,
				"broken_chains": 0, "invalid_signatures": 0, "series": {}}

	try:
		public_key = _get_public_key()
	except SignatureError as e:
		return {"success": False, "error": str(e)}

	series_results = {}
	for log in logs:
		series_results.setdefault(log.series_used, {"entries": [], "expected_previous": ""})

	documents_checked = 0
	broken_chains = 0
	invalid_signatures = 0

	for log in logs:
		bucket = series_results[log.series_used]
		entry_result = _verify_single_entry(log, public_key, bucket["expected_previous"])
		bucket["entries"].append(entry_result)
		bucket["expected_previous"] = log.signature_hash

		documents_checked += 1
		if not entry_result["chain_ok"]:
			broken_chains += 1
		if entry_result["signature_ok"] is False:
			invalid_signatures += 1

	for series_name, bucket in series_results.items():
		bucket["total"] = len(bucket["entries"])
		bucket["chain_ok"] = all(e["chain_ok"] for e in bucket["entries"])
		bucket["signatures_ok"] = all(e["signature_ok"] for e in bucket["entries"])
		del bucket["expected_previous"]

	return {
		"success": broken_chains == 0 and invalid_signatures == 0,
		"series_checked": len(series_results),
		"documents_checked": documents_checked,
		"broken_chains": broken_chains,
		"invalid_signatures": invalid_signatures,
		"series": series_results,
	}


@frappe.whitelist()
def export_signing_public_key():
	"""
	Exporta a chave pública correspondente à chave privada de
	assinatura configurada, em PEM (Requisito 2.3 da auditoria de
	certificação 2026-08-24). A chave pública não precisa de
	armazenamento próprio - é sempre derivável da privada já
	protegida em Portugal Auth Settings - mas o requisito pede um
	artefacto que possa ser entregue a um auditor ou arquivado, daí
	este utilitário em vez de um campo persistido (evita ter duas
	cópias da mesma informação a poderem divergir).
	"""
	if not frappe.has_permission("Portugal Auth Settings", "read"):
		frappe.throw(_("Sem permissão"), frappe.PermissionError)

	public_key = _get_public_key()
	pem_bytes = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo,
	)
	settings = frappe.get_single("Portugal Auth Settings")
	return {
		"public_key_pem": pem_bytes.decode("ascii"),
		"key_version": settings.get("invoice_signing_key_version") or "1",
	}
