import frappe
from frappe.model.document import Document
from frappe import _
import os
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


class SAFTExportLog(Document):
	def validate(self):
		self.validate_date_range()
		self.validate_export_type()
		self.set_system_info()

	def validate_date_range(self):
		"""Valida intervalo de datas"""
		if self.from_date and self.to_date:
			if frappe.utils.getdate(self.from_date) > frappe.utils.getdate(self.to_date):
				frappe.throw(_("From Date cannot be greater than To Date"))

			# Validar se o período não excede 1 ano
			date_diff = frappe.utils.date_diff(self.to_date, self.from_date)
			if date_diff > 365:
				frappe.throw(_("Export period cannot exceed 365 days"))

	def validate_export_type(self):
		"""Valida tipo de exportação"""
		valid_types = ["Full", "Invoicing", "Accounting", "Movement of Goods", "AT Communication"]
		if self.export_type not in valid_types:
			frappe.throw(_("Invalid export type"))

	def set_system_info(self):
		"""Define informações do sistema"""
		if not self.created_by_user:
			self.created_by_user = frappe.session.user

		if not self.ip_address:
			self.ip_address = frappe.local.request_ip if hasattr(frappe.local,
																 'request_ip') else ""

		if not self.user_agent:
			self.user_agent = frappe.get_request_header("User-Agent") or ""

		if not self.system_version:
			self.system_version = frappe.__version__

		if not self.module_version:
			self.module_version = "1.0.0"  # Versão do módulo Portugal Compliance

	def before_insert(self):
		"""Executado antes de inserir"""
		# Definir nome do arquivo baseado nos parâmetros
		if not self.file_name:
			self.file_name = self.generate_file_name()

		# Definir ano fiscal se não definido
		if not self.fiscal_year and self.from_date:
			self.fiscal_year = frappe.db.get_value("Fiscal Year", {
				"year_start_date": ["<=", self.from_date],
				"year_end_date": [">=", self.from_date]
			})

	def after_insert(self):
		"""Executado após inserir"""
		if self.status == "Pending":
			# Agendar geração do SAF-T em background
			frappe.enqueue(
				'portugal_compliance.utils.saft_generator.generate_saft_background',
				queue='long',
				timeout=1800,  # 30 minutos
				log_name=self.name
			)

	def generate_file_name(self):
		"""Gera nome do arquivo SAF-T"""
		company_abbr = frappe.db.get_value("Company", self.company, "abbr") or "COMP"
		from_date_str = frappe.utils.formatdate(self.from_date, "yyyy-MM-dd")
		to_date_str = frappe.utils.formatdate(self.to_date, "yyyy-MM-dd")

		return f"SAFT-PT_{company_abbr}_{from_date_str}_{to_date_str}_{self.export_type.replace(' ', '_')}.xml"

	def update_file_info(self, file_path, file_content):
		"""Atualiza informações do arquivo gerado"""
		try:
			self.file_path = file_path
			self.file_size = len(file_content.encode('utf-8'))
			self.file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
			self.status = "Completed"
			self.save()

		except Exception as e:
			frappe.log_error(f"Error updating file info: {str(e)}")
			self.status = "Failed"
			self.save()

	def validate_xml_content(self, xml_content):
		"""Valida conteúdo XML contra schema XSD"""
		try:
			# Parse XML
			root = ET.fromstring(xml_content)

			validation_errors = []

			# Verificar namespace
			expected_namespace = "urn:OECD:StandardAuditFile-Tax:PT_1.04_01"
			if root.tag != f"{{{expected_namespace}}}AuditFile":
				validation_errors.append("Invalid root element or namespace")

			# Verificar elementos obrigatórios
			required_elements = ["Header", "MasterFiles"]
			for element in required_elements:
				if root.find(f".//{{{expected_namespace}}}{element}") is None:
					validation_errors.append(f"Required element {element} is missing")

			# Verificar header obrigatório
			header = root.find(f".//{{{expected_namespace}}}Header")
			if header is not None:
				required_header_fields = [
					"AuditFileVersion", "CompanyID", "TaxRegistrationNumber",
					"CompanyName", "FiscalYear", "StartDate", "EndDate"
				]

				for field in required_header_fields:
					if header.find(f".//{{{expected_namespace}}}{field}") is None:
						validation_errors.append(f"Required header field {field} is missing")

			# Atualizar status de validação
			if validation_errors:
				self.xml_validation_status = "Invalid"
				self.xsd_validation_errors = "\n".join(validation_errors)
			else:
				self.xml_validation_status = "Valid"
				self.xsd_validation_errors = ""

			self.save()

			return len(validation_errors) == 0

		except ET.ParseError as e:
			self.xml_validation_status = "Validation Error"
			self.xsd_validation_errors = f"XML Parse Error: {str(e)}"
			self.save()
			return False
		except Exception as e:
			self.xml_validation_status = "Validation Error"
			self.xsd_validation_errors = f"Validation Error: {str(e)}"
			self.save()
			return False

	def submit_to_at(self, username, password):
		"""Submete arquivo à AT"""
		try:
			if self.status != "Completed":
				frappe.throw(_("Cannot submit incomplete export to AT"))

			if not self.file_path or not os.path.exists(self.file_path):
				frappe.throw(_("Export file not found"))

			# Ler conteúdo do arquivo
			with open(self.file_path, 'r', encoding='utf-8') as f:
				file_content = f.read()

			# Submeter via webservice
			from portugal_compliance.utils.at_webservice import ATWebserviceClient

			client = ATWebserviceClient()
			result = client.submit_saft_file(file_content, username, password)

			# Atualizar status de submissão
			self.at_submission_status = "Submitted"
			self.at_submission_date = frappe.utils.now()

			if result.get("status") == "success":
				self.at_submission_status = "Accepted"
				self.at_response_code = result.get("response_code", "")
			else:
				self.at_submission_status = "Rejected"
				self.at_response_code = result.get("error_code", "")

			self.save()

			return result

		except Exception as e:
			self.at_submission_status = "Rejected"
			self.at_response_code = f"Error: {str(e)}"
			self.save()

			frappe.log_error(f"Error submitting SAF-T to AT: {str(e)}")
			return {"status": "error", "message": str(e)}

	def increment_download_count(self):
		"""Incrementa contador de downloads"""
		self.download_count = (self.download_count or 0) + 1
		self.last_downloaded = frappe.utils.now()
		self.save()

	def get_file_content(self):
		"""Retorna conteúdo do arquivo"""
		try:
			if self.file_path and os.path.exists(self.file_path):
				with open(self.file_path, 'r', encoding='utf-8') as f:
					return f.read()
			else:
				frappe.throw(_("Export file not found"))

		except Exception as e:
			frappe.throw(_("Error reading export file: {0}").format(str(e)))

	def delete_file(self):
		"""Remove arquivo do servidor"""
		try:
			if self.file_path and os.path.exists(self.file_path):
				os.remove(self.file_path)
				self.file_path = ""
				self.file_size = 0
				self.file_hash = ""
				self.save()

		except Exception as e:
			frappe.log_error(f"Error deleting SAF-T file: {str(e)}")

	def get_export_summary(self):
		"""Retorna resumo da exportação"""
		return {
			"company": self.company,
			"period": f"{self.from_date} to {self.to_date}",
			"export_type": self.export_type,
			"status": self.status,
			"total_records": self.total_records,
			"file_size_mb": round((self.file_size or 0) / 1024 / 1024, 2),
			"processing_time": self.processing_time,
			"validation_status": self.xml_validation_status,
			"submission_status": self.at_submission_status
		}

	@staticmethod
	def cleanup_old_exports(days=180):
		"""Remove exportações antigas"""
		try:
			cutoff_date = frappe.utils.add_days(frappe.utils.today(), -days)

			old_exports = frappe.get_all("SAF-T Export Log",
										 filters={"creation": ["<", cutoff_date]},
										 fields=["name", "file_path"])

			for export in old_exports:
				# Remover arquivo físico
				if export.file_path and os.path.exists(export.file_path):
					os.remove(export.file_path)

				# Remover registro
				frappe.delete_doc("SAF-T Export Log", export.name)

			frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Error cleaning up old SAF-T exports: {str(e)}")

	@frappe.whitelist()
	def regenerate_export(self):
		"""Regenera exportação SAF-T"""
		try:
			if self.status == "In Progress":
				frappe.throw(_("Export is already in progress"))

			# Resetar status
			self.status = "Pending"
			self.file_path = ""
			self.file_size = 0
			self.file_hash = ""
			self.xml_validation_status = "Not Validated"
			self.xsd_validation_errors = ""
			self.save()

			# Agendar nova geração
			frappe.enqueue(
				'portugal_compliance.utils.saft_generator.generate_saft_background',
				queue='long',
				timeout=1800,
				log_name=self.name
			)

			return {
				"status": "success",
				"message": _("SAF-T export regeneration started")
			}

		except Exception as e:
			return {
				"status": "error",
				"message": str(e)
			}
