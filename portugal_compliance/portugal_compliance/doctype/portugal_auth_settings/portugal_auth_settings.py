import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cint
from frappe.utils.password import get_decrypted_password
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
