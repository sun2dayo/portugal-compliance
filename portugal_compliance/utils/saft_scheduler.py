# -*- coding: utf-8 -*-
# Copyright (c) 2026, NovaDX - Octávio Daio and contributors
# For license information, please see license.txt

"""
Geração automática mensal do ficheiro SAF-T.

A AT não disponibiliza nenhum webservice para upload do ficheiro SAF-T -
o único webservice de faturação existente (perfil WFA, RegisterInvoice,
já implementado em utils/at_invoice_webservice.py) comunica os documentos
um a um, não ficheiros agregados. Quando esse canal está em "Tempo Real"
(Portugal Auth Settings.invoice_communication_method), a obrigação de
comunicar o SAF-T mensal à AT deixa de existir na prática - confirmado
por auditoria direta aos manuais oficiais de integração da AT (2026-09-03,
ver Portugal Auth Settings.saft_communication_method). O ficheiro SAF-T
mensal gerado aqui serve apenas para arquivo e para download/envio ao
contabilista - nunca para submissão automática à AT, que não existe como
webservice.

Esta função não duplica nenhuma lógica de geração: reutiliza o fluxo real
já existente e validado (SAF-T Export Log.after_insert ->
saft_generator.generate_saft_background, que gera o XML, grava-o em disco
e valida-o contra o XSD oficial 1.04_01) - apenas cria o registo, tal como
um utilizador faria manualmente pela UI.
"""

import frappe
from frappe.utils import today, getdate, cint, get_first_day, get_last_day, add_months


def ensure_monthly_saft_generated():
	"""Chamada diariamente (ver hooks.py, scheduler_events["daily"]). Só
	atua no dia do mês configurado em Portugal Auth Settings.saft_send_day
	(omissão: dia 5, o prazo legal), gerando o SAF-T do MÊS ANTERIOR para
	cada empresa portuguesa com compliance ativo. Idempotente: não cria um
	segundo log se já existir um para a mesma empresa/período (Pending,
	In Progress ou Completed), quer tenha sido criado por este scheduler
	quer manualmente pelo utilizador - seguro correr todos os dias, e
	seguro voltar a correr no mesmo dia."""
	send_day = cint(frappe.db.get_single_value("Portugal Auth Settings", "saft_send_day") or 5)
	if getdate(today()).day != send_day:
		return

	companies = frappe.get_all(
		"Company",
		filters={"country": "Portugal", "portugal_compliance_enabled": 1},
		pluck="name",
	)
	if not companies:
		return

	previous_month_date = add_months(getdate(today()), -1)
	from_date = get_first_day(previous_month_date)
	to_date = get_last_day(previous_month_date)

	for company in companies:
		try:
			_ensure_company_saft_generated(company, from_date, to_date)
		except Exception:
			frappe.log_error(
				title="ensure_monthly_saft_generated",
				message=f"Empresa: {company} | Período: {from_date} a {to_date}\n{frappe.get_traceback()}",
			)


def _ensure_company_saft_generated(company, from_date, to_date):
	"""Cria o SAF-T Export Log de uma empresa/período, só se ainda não
	existir um. export_type="Invoicing": o gerador atual (V1, MVP de
	certificação) produz sempre o mesmo âmbito de faturação independente
	do export_type passado (ver saft_generator.py::prepare_context) -
	"Invoicing" é a etiqueta correta para o que é realmente gerado, não
	"Full" (que sugeriria âmbito contabilístico, ainda não implementado)."""
	existing = frappe.db.exists(
		"SAF-T Export Log",
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
			"export_type": "Invoicing",
			"status": ["in", ["Pending", "In Progress", "Completed"]],
		},
	)
	if existing:
		return

	frappe.get_doc({
		"doctype": "SAF-T Export Log",
		"company": company,
		"from_date": from_date,
		"to_date": to_date,
		"export_type": "Invoicing",
		"status": "Pending",
		"export_reason": "Monthly Submission",
	}).insert(ignore_permissions=True)
	frappe.db.commit()
