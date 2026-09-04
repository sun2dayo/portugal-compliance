import frappe
from frappe.model.document import Document
from frappe import _
import re
import time
from datetime import datetime, timedelta


class ATCUDLog(Document):
	def validate(self):
		self.validate_atcud_format()
		self.validate_document_reference()
		self.set_system_info()

	def validate_atcud_format(self):
		"""Valida formato do ATCUD - CORRIGIDO conforme documentação AT"""
		if not self.atcud_code or self.generation_status != "Success":
			return

		import re

		# Padrões válidos conforme documentação oficial AT
		valid_patterns = [
			r"^[A-Z0-9]{8,12}$",  # Código AT puro: AAJFJ6VHXK
			r"^[A-Z0-9]{8,12}-\d{1,8}$",  # Código + sequencial: AAJFJ6VHXK-00000001
			r"^ATCUD:[A-Z0-9]{8,12}-\d{1,8}$",  # Formato display: ATCUD:AAJFJ6VHXK-00000001
			r"^[A-Z]{2,4}-ATCUD:[A-Z0-9]{8,12}-\d{1,8}$"  # Formato antigo (compatibilidade)
		]

		# Verificar se corresponde a algum padrão válido
		is_valid = any(re.match(pattern, self.atcud_code) for pattern in valid_patterns)

		if not is_valid:
			frappe.throw(_(
				"Formato ATCUD inválido: {0}. "
				"Formatos aceitos: "
				"Código AT (ex: AAJFJ6VHXK), "
				"Código completo (ex: AAJFJ6VHXK-00000001), "
				"ou formato display (ex: ATCUD:AAJFJ6VHXK-00000001)"
			).format(self.atcud_code))

	def validate_document_reference(self):
		"""Valida referência ao documento"""
		if self.document_type and self.document_name:
			if not frappe.db.exists(self.document_type, self.document_name):
				frappe.throw(_("Referenced document {0} {1} does not exist").format(
					self.document_type, self.document_name
				))

	def set_system_info(self):
		"""
		Define informacoes do sistema. Defensivo em relacao ao contexto
		de execucao: ATCUD Log e frequentemente criado fora de um
		pedido HTTP (bench execute, background jobs, migrations) - IP
		e User-Agent so fazem sentido quando ha um pedido web real.
		"""
		if not self.created_by_user:
			self.created_by_user = frappe.session.user

		if not self.ip_address:
			try:
				self.ip_address = frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else ""
			except RuntimeError:
				self.ip_address = ""

		if not self.user_agent:
			try:
				self.user_agent = frappe.get_request_header("User-Agent") or ""
			except RuntimeError:
				self.user_agent = ""

		if not self.erpnext_version:
			self.erpnext_version = frappe.__version__

		if not self.module_version:
			self.module_version = "1.0.0"  # Versão do módulo Portugal Compliance

	def before_insert(self):
		"""Executado antes de inserir"""
		# Verificar se já existe log de sucesso para este documento
		if self.generation_status == "Success":
			existing = frappe.db.exists("ATCUD Log", {
				"document_type": self.document_type,
				"document_name": self.document_name,
				"generation_status": "Success",
				"name": ["!=", self.name or ""]
			})

			if existing:
				frappe.throw(_("ATCUD already successfully generated for document {0} {1}").format(
					self.document_type, self.document_name
				))

		# Definir data de geração se não definida
		if not self.generation_date:
			self.generation_date = frappe.utils.now()

	def after_insert(self):
		"""Executado após inserir"""
		if self.generation_status == "Failed":
			self.handle_failure()
		elif self.generation_status == "Success":
			self.handle_success()

	def handle_failure(self):
		"""Trata falhas na geração do ATCUD"""
		try:
			# Incrementar contador de tentativas
			self.retry_count = (self.retry_count or 0) + 1

			# Agendar próxima tentativa (backoff exponencial)
			if self.retry_count < 5:  # Máximo 5 tentativas
				delay_minutes = min(2 ** self.retry_count, 60)  # Max 60 minutos
				self.next_retry_date = frappe.utils.add_to_date(
					frappe.utils.now(),
					minutes=delay_minutes
				)
				# ATCUD Log deixou de ter Write para qualquer role
				# (2026-08-24, imutabilidade dos registos criptograficos) -
				# este save() corre dentro de after_insert(), no mesmo
				# fluxo do insert(ignore_permissions=True) original, mas
				# explicito aqui para nao depender de o flag persistir
				# implicitamente na instancia.
				self.save(ignore_permissions=True)

				# Agendar job para retry
				frappe.enqueue(
					'portugal_compliance.utils.atcud_generator.retry_atcud_generation',
					queue='long',
					timeout=300,
					log_name=self.name,
					eta=self.next_retry_date
				)

			# Enviar notificação de erro para administradores
			self.send_error_notification()

		except Exception as e:
			frappe.log_error(f"Error handling ATCUD failure: {str(e)}")

	def handle_success(self):
		"""Trata sucesso na geração do ATCUD"""
		try:
			# Atualizar estatísticas da série
			#
			# frappe.db.set_value (nao frappe.get_doc(...).save()) e
			# deliberado, nao um atalho: Portugal Series Configuration usa
			# autoname "field:prefix", e Document.save() corre sempre
			# _sync_autoname_field() no fim, que forca o campo "prefix" a
			# ficar igual a "name" - mesmo quando "prefix" ja estava
			# correto e "name" e um identificador de hash historico
			# diferente (ex: name="NE-2026-ZC-d0f92d", prefix="NE2026ZC").
			# Cada chamada anterior a series_doc.save() aqui corrompia
			# silenciosamente o prefix real da serie so por incrementar um
			# contador - e o prefix e o que entra na assinatura RSA de
			# cada documento (ver signature.py::build_data_to_sign), por
			# isso a corrupcao invalidava retroativamente a assinatura de
			# TODOS os documentos ja emitidos nessa serie assim que o
			# segundo documento era gerado. Encontrado 2026-09-05 via
			# verify_signature_chain() a reportar assinaturas invalidas em
			# Sales Order - confirmado por prova criptografica (a
			# assinatura original so verifica com o prefix limpo,
			# nunca com o "name" hash). set_value escreve so os 2 campos
			# pedidos, sem tocar em "prefix" nem correr autoname/hooks.
			if self.series_used:
				current_total = frappe.db.get_value(
					"Portugal Series Configuration", self.series_used, "total_documents_issued"
				) or 0
				frappe.db.set_value(
					"Portugal Series Configuration",
					self.series_used,
					{
						"total_documents_issued": current_total + 1,
						"last_document_date": self.document_date or frappe.utils.today(),
					},
				)

			# Limpar logs de falha anteriores para este documento
			frappe.db.sql("""
						  DELETE
						  FROM `tabATCUD Log`
						  WHERE document_type = %s
							AND document_name = %s
							AND generation_status = 'Failed'
							AND name != %s
						  """, (self.document_type, self.document_name, self.name))

		except Exception as e:
			frappe.log_error(f"Error handling ATCUD success: {str(e)}")

	def send_error_notification(self):
		"""Envia notificação de erro"""
		try:
			if self.retry_count >= 3:  # Só notificar após 3 tentativas
				subject = _("ATCUD Generation Failed - {0} {1}").format(
					self.document_type, self.document_name
				)

				message = f"""
                <h3>ATCUD Generation Failed</h3>
                <p><strong>Document:</strong> {self.document_type} - {self.document_name}</p>
                <p><strong>Company:</strong> {self.company}</p>
                <p><strong>Error:</strong> {self.error_message}</p>
                <p><strong>Retry Count:</strong> {self.retry_count}</p>
                <p><strong>Next Retry:</strong> {self.next_retry_date or 'No more retries'}</p>
                <hr>
                <p><em>Please check the ATCUD Log for more details.</em></p>
                """

				# Enviar para administradores do sistema
				recipients = [user.email for user in frappe.get_all("User",
																	filters={
																		"role_profile_name": "System Manager",
																		"enabled": 1},
																	fields=["email"]
																	) if user.email]

				if recipients:
					frappe.sendmail(
						recipients=recipients,
						subject=subject,
						message=message,
						header=["ATCUD Generation Error", "red"]
					)

		except Exception as e:
			frappe.log_error(f"Error sending ATCUD error notification: {str(e)}")

	@frappe.whitelist()
	def retry_generation(self):
		"""Tenta regenerar ATCUD manualmente"""
		try:
			# O dispacho de metodos whitelisted do Frappe so exige permissao
			# de LEITURA no documento antes de invocar este metodo - como
			# isto escreve no log e no documento original, exige-se
			# explicitamente uma role privilegiada. Nao usa mais
			# check_permission("write"): ATCUD Log deixou de ter Write
			# concedido a qualquer role (2026-08-24, imutabilidade dos
			# registos criptograficos) - manter essa verificacao aqui
			# bloquearia este metodo para sempre. frappe.only_for()
			# restringe pela mesma role (System Manager) que antes era a
			# unica com Write, sem depender da permissao de escrita do
			# DocType; os self.save() abaixo continuam seguros porque
			# usam ignore_permissions=True explicitamente.
			frappe.only_for("System Manager")

			from portugal_compliance.utils.atcud_generator import ATCUDGenerator

			# Obter documento original
			doc = frappe.get_doc(self.document_type, self.document_name)

			# Tentar gerar ATCUD novamente
			generator = ATCUDGenerator()
			start_time = time.time()

			result = generator.generate_atcud_for_document(doc)
			if not result.get("success"):
				frappe.throw(result.get("error") or _("Falha ao gerar ATCUD"))

			processing_time = time.time() - start_time

			# Atualizar este log
			self.generation_status = "Success"
			self.atcud_code = doc.atcud_code
			self.processing_time = processing_time
			self.error_message = ""
			self.error_traceback = ""
			self.save(ignore_permissions=True)

			return {
				"status": "success",
				"message": _("ATCUD regenerated successfully"),
				"atcud": doc.atcud_code
			}

		except Exception as e:
			# Atualizar log com novo erro
			self.error_message = str(e)
			self.last_retry_date = frappe.utils.now()
			self.save(ignore_permissions=True)

			return {
				"status": "error",
				"message": str(e)
			}

	def get_document_link(self):
		"""Retorna link para o documento original"""
		if self.document_type and self.document_name:
			return f"/app/{self.document_type.lower().replace(' ', '-')}/{self.document_name}"
		return ""

	@staticmethod
	def cleanup_old_logs(days=90):
		"""Remove logs antigos"""
		try:
			cutoff_date = frappe.utils.add_days(frappe.utils.today(), -days)

			# Manter logs de sucesso por mais tempo, remover logs de falha mais cedo
			frappe.db.sql("""
						  DELETE
						  FROM `tabATCUD Log`
						  WHERE creation < %s
							AND (
							  (generation_status = 'Failed' AND creation < %s) OR
							  (generation_status != 'Failed' AND creation < %s)
							  )
						  """, (cutoff_date, frappe.utils.add_days(cutoff_date, 60), cutoff_date))

			frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Error cleaning up ATCUD logs: {str(e)}")
