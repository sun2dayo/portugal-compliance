import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cint
from frappe.utils.password import get_decrypted_password
import glob
import os


class PortugalAuthSettings(Document):
	def validate(self):
		self.validate_certificate_path()
		self.validate_webservice_url()

	def on_update(self):
		self.sync_print_settings_for_cancelled_documents()

	def sync_print_settings_for_cancelled_documents(self):
		"""
		Espelha allow_print_cancelled_documents para o campo nativo
		Print Settings.allow_print_for_cancelled - o único ponto do
		Frappe (frontend em model.js::can_print_doc() e backend em
		frappe.www.printview) que decide se um documento anulado pode
		ser impresso. É uma definição global do site (Print Settings é
		Single, sem âmbito por empresa/doctype), por isso escrevemos
		aqui em vez de duplicar a lógica - o administrador só vê e
		controla o toggle a partir desta doctype, nunca precisa de
		saber que o Print Settings nativo existe.

		frappe.db.set_single_value (não doc.save()) para não disparar
		o próprio ciclo de validação/hooks do Print Settings por uma
		alteração puramente de espelho, e só escreve quando o valor
		realmente muda.
		"""
		try:
			desired = 1 if cint(self.allow_print_cancelled_documents) else 0
			current = cint(frappe.db.get_single_value("Print Settings", "allow_print_for_cancelled"))
			if current != desired:
				frappe.db.set_single_value("Print Settings", "allow_print_for_cancelled", desired)
		except Exception as e:
			frappe.log_error(f"Erro ao sincronizar Print Settings.allow_print_for_cancelled: {str(e)}")

	def validate_certificate_path(self):
		"""Valida caminho do certificado"""
		if self.ssl_certificate_path:
			cert_path = get_decrypted_password("Portugal Auth Settings",
											   "Portugal Auth Settings",
											   "ssl_certificate_path")

			if cert_path and not os.path.exists(cert_path):
				frappe.throw(_("Certificate file not found at specified path"))

			if cert_path and not cert_path.endswith('.pfx'):
				frappe.throw(_("Certificate must be a .pfx file"))

	def validate_webservice_url(self):
		"""Valida URL do webservice"""
		if self.at_webservice_url:
			if not self.at_webservice_url.startswith('https://'):
				frappe.throw(_("Webservice URL must use HTTPS"))

			if 'portaldasfinancas.gov.pt' not in self.at_webservice_url:
				frappe.msgprint(_("Warning: Using non-official AT webservice URL"),
								indicator='orange')

	def get_certificate_info(self):
		"""Retorna informações do certificado"""
		try:
			cert_path = get_decrypted_password("Portugal Auth Settings",
											   "Portugal Auth Settings",
											   "ssl_certificate_path")

			if cert_path and os.path.exists(cert_path):
				import ssl
				import datetime

				# Carregar certificado
				with open(cert_path, 'rb') as f:
					cert_data = f.read()

				# Extrair informações básicas
				return {
					"file_size": len(cert_data),
					"file_exists": True,
					"last_modified": datetime.datetime.fromtimestamp(
						os.path.getmtime(cert_path)
					).strftime("%Y-%m-%d %H:%M:%S")
				}
			else:
				return {"file_exists": False}

		except Exception as e:
			frappe.log_error(f"Error getting certificate info: {str(e)}")
			return {"error": str(e)}


# Convencao OFICIAL de pastas para os certificados mTLS/WS-Security
# (2026-09-04, decisao definitiva do utilizador apos recuperacao de um
# reinstall): NAO usar a pasta home do utilizador do bench - um
# ambiente de producao SaaS pode correr o servico web com outro
# utilizador do sistema e perder permissao de leitura sobre um
# ~/.alguma_coisa. As duas pastas abaixo sao pastas de sistema fixas,
# e sao exatamente onde os certificados reais desta instalacao ja
# viviam antes de qualquer automatismo existir (fora do bench/site,
# por isso sobrevivem sempre a um `bench reinstall` - confirmado ao
# recuperar esta mesma instalacao de um reinstall anterior).
CERTIFICATE_AUTODETECT_DIRS = {
	1: "/etc/portugal_compliance/certificates/test",
	0: "/etc/portugal_compliance/certificates/prod",
}

# Padroes de nome de ficheiro dentro de cada pasta. mtls_* usam nome
# fixo (assim se chamam os ficheiros extraidos do .pfx da AT, sem
# rotacao). at_public_certificate_path usa um padrao com wildcard
# porque o certificado publico da AT ja e distribuido com o ano no
# nome (ex: at_public_key_2027.cer, o real desta instalacao) - a AT
# renova este certificado periodicamente, por isso o padrao fixo
# teria de ser manualmente reescrito nesta constante a cada renovacao.
# Com wildcard, basta colocar o novo ficheiro na pasta; se houver mais
# do que um a corresponder, escolhe-se o modificado mais recentemente
# (o certificado novo, presumivelmente acabado de la colocar).
CERTIFICATE_AUTODETECT_FILENAME_PATTERNS = {
	"mtls_certificate_path": "mtls_client_cert.pem",
	"mtls_private_key_path": "mtls_client_key.pem",
	"at_public_certificate_path": "at_public_key*.cer",
}


def _find_certificate(base_dir, pattern):
	if glob.has_magic(pattern):
		matches = glob.glob(os.path.join(base_dir, pattern))
		return max(matches, key=os.path.getmtime) if matches else None
	path = os.path.join(base_dir, pattern)
	return path if os.path.isfile(path) else None


@frappe.whitelist()
def detect_certificate_paths(sandbox_mode):
	"""
	Deteta os certificados mTLS/WS-Security na pasta de sistema do
	modo indicado (sandbox ou producao) e devolve os caminhos
	encontrados - so os que existirem mesmo em disco, nunca um caminho
	adivinhado. Devolve tambem as pastas e os padroes de nome usados
	(campo "dirs"/"patterns"), para o JS poder decidir se um valor ja
	preenchido no formulario e um caminho "gerido" por esta
	autodeteccao (seguro para substituir ao mudar de modo) ou um
	caminho manual do administrador (nunca substituido - ver
	autodetect_certificate_paths() em portugal_auth_settings.js).
	"""
	base_dir = CERTIFICATE_AUTODETECT_DIRS[cint(sandbox_mode)]
	found = {}
	for fieldname, pattern in CERTIFICATE_AUTODETECT_FILENAME_PATTERNS.items():
		path = _find_certificate(base_dir, pattern)
		if path:
			found[fieldname] = path
	return {
		"found": found,
		"dirs": list(CERTIFICATE_AUTODETECT_DIRS.values()),
		"patterns": CERTIFICATE_AUTODETECT_FILENAME_PATTERNS,
	}
