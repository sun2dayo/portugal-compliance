# -*- coding: utf-8 -*-
# Copyright (c) 2025, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Field Management Utilities for Portugal Compliance - VERSÃO CERTIFICADA
Handles creation, update, and management of custom fields
Updated for naming_series approach - only ATCUD field needed, company-specific configuration
"""

import frappe
from frappe import _
from frappe.utils import cint, now, today, getdate
from frappe.model.document import Document
import json
import re


class PortugalFieldManager:
	"""
	Classe principal para gestão de campos customizados - VERSÃO CERTIFICADA
	Nova abordagem: apenas campo ATCUD (read-only), configuração por empresa, cleanup automático
	"""

	def __init__(self):
		self.module = "Portugal Compliance"
		self.required_fields = self.get_required_fields_config()
		self.supported_doctypes = self.get_supported_doctypes()
		self.conflicting_fields = self.get_conflicting_fields()

	def get_required_fields_config(self):
		"""
		Configuração dos campos obrigatórios - APENAS ATCUD PARA NOVA ABORDAGEM
		"""
		return {
			"atcud_code": {
				"label": "ATCUD Code",
				"fieldtype": "Data",
				"read_only": 1,
				"bold": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"print_hide": 0,
				"description": "Código Único de Documento - Gerado automaticamente pela série portuguesa comunicada",
				"insert_after": "naming_series",
				"mandatory_depends_on": None,
				"hidden": 0,
				"reqd": 0,
				"default": None,
				"options": None,
				"length": 20,
				"precision": None,
				"allow_on_submit": 0,
				"unique": 0,
				"search_index": 1,
				"report_hide": 0,
				"ignore_user_permissions": 0,
				"no_copy": 1,
				"translatable": 0,
				"depends_on": None,
				"mandatory_depends_on": None,
				"read_only_depends_on": None,
				"hidden_depends_on": None
			},
			"qr_code_image": {
				"label": "QR Code",
				"fieldtype": "Attach Image",
				"read_only": 1,
				"bold": 0,
				"in_list_view": 0,
				"print_hide": 0,
				"description": "QR Code gerado automaticamente para o documento",
				"insert_after": "atcud_code",
				"hidden": 0,
				"reqd": 0,
				"allow_on_submit": 0,
				"no_copy": 1,
				"translatable": 0,
				"depends_on": "eval:doc.atcud_code",
				"applicable_doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry",
										"Delivery Note", "Purchase Receipt"]
			},
			"saft_hash": {
				"label": "SAF-T Hash",
				"fieldtype": "Data",
				"read_only": 1,
				"bold": 0,
				"in_list_view": 0,
				"print_hide": 1,
				"hidden": 1,
				"description": "Hash do documento para exportação SAF-T",
				"insert_after": "qr_code_image",
				"reqd": 0,
				"allow_on_submit": 0,
				"no_copy": 1,
				"translatable": 0,
				"length": 64,
				"applicable_doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry"]
			}
		}

	def get_supported_doctypes(self):
		"""
		DocTypes que precisam de campos de compliance português
		"""
		return [
			"Sales Invoice",
			"Purchase Invoice",
			"Payment Entry",
			"Delivery Note",
			"Purchase Receipt",
			"Journal Entry",
			"Stock Entry",
			"Quotation",
			"Sales Order",
			"Purchase Order",
			"Material Request"
		]

	def get_conflicting_fields(self):
		"""
		Campos conflitantes da abordagem antiga que devem ser removidos
		"""
		return [
			"portugal_series",
			"portugal_series_prefix",
			"portugal_compliance_status",
			"portugal_compliance_date",
			"series_validation_code",
			"at_series_code",
			"portugal_document_type",
			"series_environment"
		]

	def get_company_specific_fields(self):
		"""
		Campos específicos para configuração por empresa
		"""
		return {
			"Company": {
				"portugal_compliance_enabled": {
					"label": "Portugal Compliance Enabled",
					"fieldtype": "Check",
					"insert_after": "country",
					"default": "0",
					"description": "Ativar conformidade fiscal portuguesa para esta empresa",
					"depends_on": "eval:doc.country=='Portugal'"
				},
				"at_certificate_number": {
					"label": "AT Certificate Number",
					"fieldtype": "Data",
					"insert_after": "portugal_compliance_enabled",
					"depends_on": "eval:doc.portugal_compliance_enabled",
					"description": "Número do certificado de software emitido pela AT (opcional)",
					"length": 20
				},
				"portugal_compliance_settings": {
					"label": "Portugal Compliance Settings",
					"fieldtype": "Section Break",
					"insert_after": "at_certificate_number",
					"depends_on": "eval:doc.portugal_compliance_enabled",
					"collapsible": 1
				},
				"default_at_environment": {
					"label": "Default AT Environment",
					"fieldtype": "Select",
					"options": "test\nproduction",
					"default": "test",
					"insert_after": "portugal_compliance_settings",
					"depends_on": "eval:doc.portugal_compliance_enabled",
					"description": "Ambiente padrão para comunicação com AT"
				}
			},
			"Customer": {
				"nif_validated": {
					"label": "NIF Validated",
					"fieldtype": "Check",
					"insert_after": "tax_id",
					"read_only": 1,
					"description": "NIF foi validado automaticamente pelo algoritmo português"
				}
			},
			"Supplier": {
				"nif_validated": {
					"label": "NIF Validated",
					"fieldtype": "Check",
					"insert_after": "tax_id",
					"read_only": 1,
					"description": "NIF foi validado automaticamente pelo algoritmo português"
				}
			}
		}

	# ========== CRIAÇÃO DE CAMPOS ==========

	def create_all_fields(self, force_recreate=False, company_specific=True):
		"""
		Criar todos os campos necessários para todos os DocTypes
		"""
		try:
			results = {
				"success": True,
				"created_fields": [],
				"updated_fields": [],
				"removed_fields": [],
				"errors": [],
				"total_doctypes": len(self.supported_doctypes),
				"total_fields": len(self.required_fields),
				"company_fields_created": 0
			}

			# ✅ PRIMEIRO: Remover campos conflitantes
			cleanup_result = self.remove_conflicting_fields()
			results["removed_fields"] = cleanup_result.get("removed_fields", [])

			# ✅ SEGUNDO: Criar campos principais para DocTypes
			for doctype in self.supported_doctypes:
				try:
					doctype_result = self.create_fields_for_doctype(doctype, force_recreate)

					if doctype_result["success"]:
						results["created_fields"].extend(doctype_result.get("created", []))
						results["updated_fields"].extend(doctype_result.get("updated", []))
					else:
						results["errors"].append({
							"doctype": doctype,
							"error": doctype_result.get("error", "Unknown error")
						})

				except Exception as e:
					results["errors"].append({
						"doctype": doctype,
						"error": str(e)
					})
					frappe.log_error(f"Error creating fields for {doctype}: {str(e)}")

			# ✅ TERCEIRO: Criar campos específicos por empresa
			if company_specific:
				company_result = self.create_company_specific_fields(force_recreate)
				results["company_fields_created"] = company_result.get("created_count", 0)
				results["created_fields"].extend(company_result.get("created_fields", []))

			# ✅ QUARTO: Limpar cache
			frappe.clear_cache()

			# Log resultado
			frappe.logger().info(
				f"✅ Field creation completed: {len(results['created_fields'])} created, "
				f"{len(results['updated_fields'])} updated, {len(results['removed_fields'])} removed, "
				f"{len(results['errors'])} errors")

			return results

		except Exception as e:
			frappe.log_error(f"Error in create_all_fields: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"created_fields": [],
				"updated_fields": [],
				"removed_fields": [],
				"errors": []
			}

	def create_fields_for_doctype(self, doctype, force_recreate=False):
		"""
		Criar campos para um DocType específico
		"""
		try:
			result = {
				"success": True,
				"doctype": doctype,
				"created": [],
				"updated": [],
				"skipped": []
			}

			# Verificar se DocType existe
			if not frappe.db.exists("DocType", doctype):
				return {
					"success": False,
					"error": f"DocType {doctype} does not exist"
				}

			# Criar cada campo obrigatório
			for fieldname, field_config in self.required_fields.items():
				try:
					# ✅ VERIFICAR SE CAMPO É APLICÁVEL A ESTE DOCTYPE
					applicable_doctypes = field_config.get("applicable_doctypes")
					if applicable_doctypes and doctype not in applicable_doctypes:
						result["skipped"].append(f"{doctype}-{fieldname}")
						continue

					field_result = self.create_single_field(doctype, fieldname, field_config,
															force_recreate)

					if field_result["action"] == "created":
						result["created"].append(field_result["field_name"])
					elif field_result["action"] == "updated":
						result["updated"].append(field_result["field_name"])
					elif field_result["action"] == "skipped":
						result["skipped"].append(field_result["field_name"])

				except Exception as e:
					frappe.log_error(f"Error creating field {fieldname} for {doctype}: {str(e)}")
					result["success"] = False
					result["error"] = str(e)

			return result

		except Exception as e:
			return {
				"success": False,
				"error": str(e)
			}

	def create_single_field(self, doctype, fieldname, field_config, force_recreate=False):
		"""
		Criar um campo específico
		"""
		try:
			custom_field_name = f"{doctype}-{fieldname}"

			# Verificar se campo já existe
			existing_field = frappe.db.exists("Custom Field", custom_field_name)

			if existing_field and not force_recreate:
				# Campo existe - verificar se precisa atualização
				if self.field_needs_update(existing_field, field_config):
					self.update_existing_field(existing_field, field_config)
					return {
						"action": "updated",
						"field_name": custom_field_name,
						"message": "Field updated successfully"
					}
				else:
					return {
						"action": "skipped",
						"field_name": custom_field_name,
						"message": "Field already exists and is up to date"
					}

			elif existing_field and force_recreate:
				# Remover campo existente para recriar
				frappe.delete_doc("Custom Field", existing_field, ignore_permissions=True)
				frappe.logger().info(
					f"🗑️ Removed existing field for recreation: {custom_field_name}")

			# Criar novo campo
			field_doc = self.build_field_document(doctype, fieldname, field_config)
			field_doc.insert(ignore_permissions=True)

			frappe.logger().info(f"✅ Created field: {custom_field_name}")

			return {
				"action": "created",
				"field_name": custom_field_name,
				"message": "Field created successfully"
			}

		except Exception as e:
			frappe.log_error(f"Error creating field {fieldname} for {doctype}: {str(e)}")
			return {
				"action": "error",
				"field_name": f"{doctype}-{fieldname}",
				"error": str(e)
			}

	def build_field_document(self, doctype, fieldname, field_config):
		"""
		Construir documento do campo customizado
		"""
		field_doc = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": doctype,
			"module": self.module,
			"fieldname": fieldname,
			"label": field_config["label"],
			"fieldtype": field_config["fieldtype"],
			"insert_after": field_config.get("insert_after", "naming_series"),
			"read_only": field_config.get("read_only", 0),
			"bold": field_config.get("bold", 0),
			"in_list_view": field_config.get("in_list_view", 0),
			"in_standard_filter": field_config.get("in_standard_filter", 0),
			"print_hide": field_config.get("print_hide", 0),
			"description": field_config.get("description", ""),
			"mandatory_depends_on": field_config.get("mandatory_depends_on"),
			"hidden": field_config.get("hidden", 0),
			"reqd": field_config.get("reqd", 0),
			"default": field_config.get("default"),
			"options": field_config.get("options"),
			"length": field_config.get("length"),
			"precision": field_config.get("precision"),
			"allow_on_submit": field_config.get("allow_on_submit", 0),
			"unique": field_config.get("unique", 0),
			"search_index": field_config.get("search_index", 0),
			"report_hide": field_config.get("report_hide", 0),
			"ignore_user_permissions": field_config.get("ignore_user_permissions", 0),
			"no_copy": field_config.get("no_copy", 0),
			"translatable": field_config.get("translatable", 0),
			"depends_on": field_config.get("depends_on"),
			"read_only_depends_on": field_config.get("read_only_depends_on"),
			"hidden_depends_on": field_config.get("hidden_depends_on"),
			"collapsible": field_config.get("collapsible", 0)
		})

		return field_doc

	# ========== CAMPOS ESPECÍFICOS POR EMPRESA ==========

	def create_company_specific_fields(self, force_recreate=False):
		"""
		Criar campos específicos para configuração por empresa
		"""
		try:
			result = {
				"success": True,
				"created_fields": [],
				"updated_fields": [],
				"created_count": 0,
				"errors": []
			}

			company_fields = self.get_company_specific_fields()

			for doctype, fields_config in company_fields.items():
				try:
					# Verificar se DocType existe
					if not frappe.db.exists("DocType", doctype):
						continue

					for fieldname, field_config in fields_config.items():
						try:
							field_result = self.create_single_field(doctype, fieldname,
																	field_config, force_recreate)

							if field_result["action"] == "created":
								result["created_fields"].append(field_result["field_name"])
								result["created_count"] += 1
							elif field_result["action"] == "updated":
								result["updated_fields"].append(field_result["field_name"])

						except Exception as e:
							result["errors"].append({
								"doctype": doctype,
								"fieldname": fieldname,
								"error": str(e)
							})

				except Exception as e:
					result["errors"].append({
						"doctype": doctype,
						"error": str(e)
					})

			frappe.logger().info(f"✅ Company-specific fields: {result['created_count']} created")

			return result

		except Exception as e:
			frappe.log_error(f"Error creating company-specific fields: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"created_fields": [],
				"created_count": 0
			}

	# ========== REMOÇÃO DE CAMPOS CONFLITANTES ==========

	def remove_conflicting_fields(self):
		"""
		Remover campos conflitantes da abordagem antiga - VERSÃO ROBUSTA
		"""
		try:
			result = {
				"success": True,
				"removed_fields": [],
				"removed_count": 0,
				"errors": []
			}

			# ✅ REMOVER CAMPOS CONFLITANTES DE TODOS OS DOCTYPES
			for doctype in self.supported_doctypes:
				for fieldname in self.conflicting_fields:
					custom_field_name = f"{doctype}-{fieldname}"

					if frappe.db.exists("Custom Field", custom_field_name):
						try:
							frappe.delete_doc("Custom Field", custom_field_name,
											  ignore_permissions=True)
							result["removed_fields"].append(custom_field_name)
							result["removed_count"] += 1
							frappe.logger().info(
								f"🗑️ Removed conflicting field: {custom_field_name}")
						except Exception as e:
							result["errors"].append({
								"field": custom_field_name,
								"error": str(e)
							})
							frappe.log_error(
								f"Error removing conflicting field {custom_field_name}: {str(e)}")

			# ✅ REMOVER TAMBÉM PROPERTY SETTERS CONFLITANTES
			conflicting_property_setters = [
				"Sales Invoice-portugal_series-options",
				"Purchase Invoice-portugal_series-options",
				"Payment Entry-portugal_series-options"
			]

			for ps_name in conflicting_property_setters:
				if frappe.db.exists("Property Setter", ps_name):
					try:
						frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True)
						result["removed_fields"].append(f"PS: {ps_name}")
						result["removed_count"] += 1
						frappe.logger().info(f"🗑️ Removed conflicting Property Setter: {ps_name}")
					except Exception as e:
						result["errors"].append({
							"property_setter": ps_name,
							"error": str(e)
						})

			frappe.logger().info(
				f"🗑️ Cleanup completed: {result['removed_count']} conflicting items removed")

			return result

		except Exception as e:
			frappe.log_error(f"Error removing conflicting fields: {str(e)}")
			return {
				"success": False,
				"error": str(e),
				"removed_fields": [],
				"removed_count": 0
			}

	def cleanup_fields_for_company(self, company):
		"""
		Cleanup específico de campos quando empresa desativa compliance
		"""
		try:
			result = {
				"success": True,
				"cleaned_fields": [],
				"reset_values": 0
			}

			# ✅ LIMPAR VALORES DOS CAMPOS ATCUD PARA DOCUMENTOS DA EMPRESA
			for doctype in self.supported_doctypes:
				try:
					# Limpar valores ATCUD para documentos não submetidos
					updated_count = frappe.db.sql(f"""
						UPDATE `tab{doctype}`
						SET atcud_code = NULL, qr_code_image = NULL, saft_hash = NULL
						WHERE company = %s AND docstatus = 0
					""", (company,))

					if updated_count:
						result["reset_values"] += updated_count[0] if updated_count else 0
						result["cleaned_fields"].append(
							f"{doctype}: {updated_count[0] if updated_count else 0} records")

				except Exception as e:
					frappe.log_error(f"Error cleaning {doctype} for company {company}: {str(e)}")

			frappe.logger().info(
				f"🧹 Company cleanup completed: {result['reset_values']} records cleaned")

			return result

		except Exception as e:
			frappe.log_error(f"Error in cleanup_fields_for_company: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	# ========== VALIDAÇÃO E ATUALIZAÇÃO ==========

	def field_needs_update(self, existing_field_name, field_config):
		"""
		Verificar se campo existente precisa de atualização
		"""
		try:
			existing_field = frappe.get_doc("Custom Field", existing_field_name)

			# Campos críticos para verificar
			critical_fields = [
				"label", "fieldtype", "read_only", "bold",
				"in_list_view", "in_standard_filter", "description", "reqd", "depends_on"
			]

			for field in critical_fields:
				current_value = getattr(existing_field, field, None)
				expected_value = field_config.get(field)

				# Normalizar valores None e ""
				if current_value is None:
					current_value = ""
				if expected_value is None:
					expected_value = ""

				if str(current_value) != str(expected_value):
					frappe.logger().info(
						f"🔄 Field {existing_field_name} needs update: {field} ({current_value} -> {expected_value})")
					return True

			return False

		except Exception as e:
			frappe.log_error(f"Error checking field update need: {str(e)}")
			return False

	def update_existing_field(self, existing_field_name, field_config):
		"""
		Atualizar campo existente
		"""
		try:
			existing_field = frappe.get_doc("Custom Field", existing_field_name)

			# Atualizar propriedades
			for key, value in field_config.items():
				if hasattr(existing_field, key) and value is not None:
					setattr(existing_field, key, value)

			existing_field.save(ignore_permissions=True)
			frappe.logger().info(f"🔄 Updated field: {existing_field_name}")

		except Exception as e:
			frappe.log_error(f"Error updating field {existing_field_name}: {str(e)}")

	def validate_field_integrity(self):
		"""
		Validar integridade dos campos customizados
		"""
		try:
			validation_results = {
				"success": True,
				"total_doctypes": len(self.supported_doctypes),
				"valid_doctypes": 0,
				"missing_fields": [],
				"invalid_fields": [],
				"conflicting_fields_found": [],
				"recommendations": []
			}

			# ✅ VERIFICAR CAMPOS OBRIGATÓRIOS
			for doctype in self.supported_doctypes:
				doctype_valid = True

				for fieldname, field_config in self.required_fields.items():
					# Verificar aplicabilidade
					applicable_doctypes = field_config.get("applicable_doctypes")
					if applicable_doctypes and doctype not in applicable_doctypes:
						continue

					custom_field_name = f"{doctype}-{fieldname}"

					if not frappe.db.exists("Custom Field", custom_field_name):
						validation_results["missing_fields"].append({
							"doctype": doctype,
							"fieldname": fieldname,
							"field_name": custom_field_name
						})
						doctype_valid = False
					else:
						# Verificar se campo está configurado corretamente
						if not self.validate_field_configuration(custom_field_name, field_config):
							validation_results["invalid_fields"].append({
								"doctype": doctype,
								"fieldname": fieldname,
								"field_name": custom_field_name
							})
							doctype_valid = False

				if doctype_valid:
					validation_results["valid_doctypes"] += 1

			# ✅ VERIFICAR CAMPOS CONFLITANTES
			for doctype in self.supported_doctypes:
				for fieldname in self.conflicting_fields:
					custom_field_name = f"{doctype}-{fieldname}"
					if frappe.db.exists("Custom Field", custom_field_name):
						validation_results["conflicting_fields_found"].append({
							"doctype": doctype,
							"fieldname": fieldname,
							"field_name": custom_field_name
						})

			# Gerar recomendações
			if validation_results["missing_fields"]:
				validation_results["recommendations"].append(
					f"Create {len(validation_results['missing_fields'])} missing fields"
				)

			if validation_results["invalid_fields"]:
				validation_results["recommendations"].append(
					f"Update {len(validation_results['invalid_fields'])} invalid fields"
				)

			if validation_results["conflicting_fields_found"]:
				validation_results["recommendations"].append(
					f"Remove {len(validation_results['conflicting_fields_found'])} conflicting fields"
				)

			if (not validation_results["missing_fields"] and
				not validation_results["invalid_fields"] and
				not validation_results["conflicting_fields_found"]):
				validation_results["recommendations"].append("All fields are properly configured")

			return validation_results

		except Exception as e:
			frappe.log_error(f"Error validating field integrity: {str(e)}")
			return {
				"success": False,
				"error": str(e)
			}

	def validate_field_configuration(self, custom_field_name, expected_config):
		"""
		Validar configuração de um campo específico
		"""
		try:
			field_doc = frappe.get_doc("Custom Field", custom_field_name)

			# Verificar propriedades críticas
			critical_properties = ["fieldtype", "read_only", "bold"]

			for prop in critical_properties:
				current_value = getattr(field_doc, prop, None)
				expected_value = expected_config.get(prop)

				if current_value != expected_value:
					return False

			return True

		except Exception:
			return False

	# ========== ESTATÍSTICAS E RELATÓRIOS ==========

	def get_field_usage_statistics(self):
		"""
		Obter estatísticas de uso dos campos
		"""
		try:
			stats = {
				"total_doctypes": len(self.supported_doctypes),
				"total_fields": len(self.required_fields),
				"field_usage": {},
				"doctype_coverage": {},
				"company_fields": {},
				"conflicting_fields_detected": 0
			}

			# ✅ ESTATÍSTICAS POR CAMPO
			for fieldname in self.required_fields.keys():
				field_stats = {
					"total_instances": 0,
					"doctypes_with_field": 0,
					"doctypes_missing_field": 0,
					"applicable_doctypes": 0
				}

				for doctype in self.supported_doctypes:
					# Verificar aplicabilidade
					field_config = self.required_fields[fieldname]
					applicable_doctypes = field_config.get("applicable_doctypes")

					if applicable_doctypes and doctype not in applicable_doctypes:
						continue

					field_stats["applicable_doctypes"] += 1
					custom_field_name = f"{doctype}-{fieldname}"

					if frappe.db.exists("Custom Field", custom_field_name):
						field_stats["doctypes_with_field"] += 1
						field_stats["total_instances"] += 1
					else:
						field_stats["doctypes_missing_field"] += 1

				stats["field_usage"][fieldname] = field_stats

			# ✅ ESTATÍSTICAS POR DOCTYPE
			for doctype in self.supported_doctypes:
				doctype_stats = {
					"total_applicable_fields": 0,
					"fields_present": 0,
					"fields_missing": 0,
					"coverage_percentage": 0
				}

				for fieldname, field_config in self.required_fields.items():
					# Verificar aplicabilidade
					applicable_doctypes = field_config.get("applicable_doctypes")
					if applicable_doctypes and doctype not in applicable_doctypes:
						continue

					doctype_stats["total_applicable_fields"] += 1
					custom_field_name = f"{doctype}-{fieldname}"

					if frappe.db.exists("Custom Field", custom_field_name):
						doctype_stats["fields_present"] += 1
					else:
						doctype_stats["fields_missing"] += 1

				if doctype_stats["total_applicable_fields"] > 0:
					doctype_stats["coverage_percentage"] = round(
						(doctype_stats["fields_present"] / doctype_stats[
							"total_applicable_fields"]) * 100, 2
					)

				stats["doctype_coverage"][doctype] = doctype_stats

			# ✅ ESTATÍSTICAS DE CAMPOS DA EMPRESA
			company_fields = self.get_company_specific_fields()
			for doctype, fields_config in company_fields.items():
				company_field_stats = {
					"total_fields": len(fields_config),
					"fields_present": 0,
					"fields_missing": 0
				}

				for fieldname in fields_config.keys():
					custom_field_name = f"{doctype}-{fieldname}"
					if frappe.db.exists("Custom Field", custom_field_name):
						company_field_stats["fields_present"] += 1
					else:
						company_field_stats["fields_missing"] += 1

				stats["company_fields"][doctype] = company_field_stats

			# ✅ DETECTAR CAMPOS CONFLITANTES
			for doctype in self.supported_doctypes:
				for fieldname in self.conflicting_fields:
					custom_field_name = f"{doctype}-{fieldname}"
					if frappe.db.exists("Custom Field", custom_field_name):
						stats["conflicting_fields_detected"] += 1

			return stats

		except Exception as e:
			frappe.log_error(f"Error getting field usage statistics: {str(e)}")
			return {}

	def export_field_configuration(self):
		"""
		Exportar configuração atual dos campos
		"""
		try:
			export_data = {
				"export_date": now(),
				"module": self.module,
				"supported_doctypes": self.supported_doctypes,
				"required_fields": self.required_fields,
				"company_specific_fields": self.get_company_specific_fields(),
				"conflicting_fields": self.conflicting_fields,
				"current_fields": {},
				"statistics": self.get_field_usage_statistics()
			}

			# ✅ CAMPOS ATUAIS POR DOCTYPE
			for doctype in self.supported_doctypes:
				export_data["current_fields"][doctype] = {}

				for fieldname in self.required_fields.keys():
					custom_field_name = f"{doctype}-{fieldname}"

					if frappe.db.exists("Custom Field", custom_field_name):
						field_doc = frappe.get_doc("Custom Field", custom_field_name)
						export_data["current_fields"][doctype][fieldname] = {
							"exists": True,
							"label": field_doc.label,
							"fieldtype": field_doc.fieldtype,
							"read_only": field_doc.read_only,
							"bold": field_doc.bold,
							"in_list_view": field_doc.in_list_view,
							"description": field_doc.description,
							"insert_after": field_doc.insert_after
						}
					else:
						export_data["current_fields"][doctype][fieldname] = {
							"exists": False
						}

			return export_data

		except Exception as e:
			frappe.log_error(f"Error exporting field configuration: {str(e)}")
			return {}


# ========== INSTÂNCIA GLOBAL ==========
field_manager = PortugalFieldManager()


# ========== FUNÇÕES GLOBAIS ==========

@frappe.whitelist()
def create_all_portugal_fields(force_recreate=False, company_specific=True):
	"""
	API para criar todos os campos portugueses
	"""
	try:
		result = field_manager.create_all_fields(cint(force_recreate), cint(company_specific))

		return {
			"success": result["success"],
			"message": f"Created {len(result['created_fields'])} fields, updated {len(result['updated_fields'])} fields, removed {len(result['removed_fields'])} conflicting fields",
			"details": result
		}

	except Exception as e:
		frappe.log_error(f"Error in create_all_portugal_fields: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def create_fields_for_doctype(doctype, force_recreate=False):
	"""
	API para criar campos para DocType específico
	"""
	try:
		result = field_manager.create_fields_for_doctype(doctype, cint(force_recreate))
		return result

	except Exception as e:
		frappe.log_error(f"Error in create_fields_for_doctype: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def remove_conflicting_fields():
	"""
	API para remover campos conflitantes
	"""
	try:
		result = field_manager.remove_conflicting_fields()
		return result

	except Exception as e:
		frappe.log_error(f"Error in remove_conflicting_fields: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def cleanup_fields_for_company(company):
	"""
	API para cleanup de campos quando empresa desativa compliance
	"""
	try:
		result = field_manager.cleanup_fields_for_company(company)
		return result

	except Exception as e:
		frappe.log_error(f"Error in cleanup_fields_for_company: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_field_integrity():
	"""
	API para validar integridade dos campos
	"""
	try:
		result = field_manager.validate_field_integrity()
		return result

	except Exception as e:
		frappe.log_error(f"Error in validate_field_integrity: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_field_usage_statistics():
	"""
	API para obter estatísticas de uso dos campos
	"""
	try:
		stats = field_manager.get_field_usage_statistics()
		return {
			"success": True,
			"statistics": stats
		}

	except Exception as e:
		frappe.log_error(f"Error in get_field_usage_statistics: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def export_field_configuration():
	"""
	API para exportar configuração dos campos
	"""
	try:
		export_data = field_manager.export_field_configuration()
		return {
			"success": True,
			"export_data": export_data
		}

	except Exception as e:
		frappe.log_error(f"Error in export_field_configuration: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def create_company_specific_fields(force_recreate=False):
	"""
	API para criar campos específicos da empresa
	"""
	try:
		result = field_manager.create_company_specific_fields(cint(force_recreate))
		return result

	except Exception as e:
		frappe.log_error(f"Error in create_company_specific_fields: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== FUNÇÕES DE SETUP/CLEANUP ==========

def setup_portugal_fields_on_install():
	"""
	Configurar campos portugueses durante instalação
	"""
	try:
		frappe.logger().info("🇵🇹 Setting up Portugal compliance fields...")

		# Criar todos os campos
		result = field_manager.create_all_fields(force_recreate=False, company_specific=True)

		if result["success"]:
			frappe.logger().info(
				f"✅ Portugal fields setup completed: {len(result['created_fields'])} created, "
				f"{len(result['removed_fields'])} conflicting fields removed")
		else:
			frappe.logger().error(f"❌ Portugal fields setup failed: {result.get('error')}")

		return result

	except Exception as e:
		frappe.log_error(f"Error in setup_portugal_fields_on_install: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


def cleanup_portugal_fields_on_uninstall():
	"""
	Limpar campos portugueses durante desinstalação
	"""
	try:
		frappe.logger().info("🧹 Cleaning up Portugal compliance fields...")

		removed_count = 0

		# ✅ REMOVER CAMPOS PRINCIPAIS
		for doctype in field_manager.supported_doctypes:
			for fieldname in field_manager.required_fields.keys():
				custom_field_name = f"{doctype}-{fieldname}"

				if frappe.db.exists("Custom Field", custom_field_name):
					try:
						frappe.delete_doc("Custom Field", custom_field_name,
										  ignore_permissions=True)
						removed_count += 1
					except Exception as e:
						frappe.log_error(f"Error removing field {custom_field_name}: {str(e)}")

		# ✅ REMOVER CAMPOS ESPECÍFICOS DA EMPRESA
		company_fields = field_manager.get_company_specific_fields()
		for doctype, fields_config in company_fields.items():
			for fieldname in fields_config.keys():
				custom_field_name = f"{doctype}-{fieldname}"

				if frappe.db.exists("Custom Field", custom_field_name):
					try:
						frappe.delete_doc("Custom Field", custom_field_name,
										  ignore_permissions=True)
						removed_count += 1
					except Exception as e:
						frappe.log_error(
							f"Error removing company field {custom_field_name}: {str(e)}")

		frappe.logger().info(f"🧹 Removed {removed_count} Portugal compliance fields")

		return {
			"success": True,
			"removed_count": removed_count
		}

	except Exception as e:
		frappe.log_error(f"Error in cleanup_portugal_fields_on_uninstall: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


# ========== UTILITÁRIOS ==========

def get_portugal_field_status(doctype, fieldname):
	"""
	Verificar status de um campo específico
	"""
	try:
		custom_field_name = f"{doctype}-{fieldname}"

		if frappe.db.exists("Custom Field", custom_field_name):
			field_doc = frappe.get_doc("Custom Field", custom_field_name)
			return {
				"exists": True,
				"name": custom_field_name,
				"label": field_doc.label,
				"fieldtype": field_doc.fieldtype,
				"read_only": field_doc.read_only,
				"module": field_doc.module
			}
		else:
			return {
				"exists": False,
				"name": custom_field_name
			}

	except Exception as e:
		return {
			"exists": False,
			"error": str(e)
		}


def is_portugal_field_required(doctype):
	"""
	Verificar se DocType precisa de campos portugueses
	"""
	return doctype in field_manager.supported_doctypes


def get_conflicting_fields_for_doctype(doctype):
	"""
	Obter campos conflitantes para um DocType específico
	"""
	try:
		conflicting = []
		for fieldname in field_manager.conflicting_fields:
			custom_field_name = f"{doctype}-{fieldname}"
			if frappe.db.exists("Custom Field", custom_field_name):
				conflicting.append({
					"field_name": custom_field_name,
					"fieldname": fieldname,
					"doctype": doctype
				})

		return conflicting

	except Exception as e:
		frappe.log_error(f"Error getting conflicting fields for {doctype}: {str(e)}")
		return []


def validate_portugal_field_dependencies():
	"""
	Validar dependências dos campos portugueses
	"""
	try:
		validation_results = {
			"success": True,
			"missing_dependencies": [],
			"invalid_configurations": [],
			"recommendations": []
		}

		# Verificar se DocTypes necessários existem
		for doctype in field_manager.supported_doctypes:
			if not frappe.db.exists("DocType", doctype):
				validation_results["missing_dependencies"].append({
					"type": "DocType",
					"name": doctype,
					"issue": "DocType does not exist"
				})

		# Verificar configurações específicas
		for doctype in ["Company", "Customer", "Supplier"]:
			if not frappe.db.exists("DocType", doctype):
				validation_results["missing_dependencies"].append({
					"type": "DocType",
					"name": doctype,
					"issue": "Required for company-specific fields"
				})

		# Gerar recomendações
		if validation_results["missing_dependencies"]:
			validation_results["success"] = False
			validation_results["recommendations"].append(
				"Install missing DocTypes or modules before setting up Portugal compliance"
			)

		return validation_results

	except Exception as e:
		frappe.log_error(f"Error validating field dependencies: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}
