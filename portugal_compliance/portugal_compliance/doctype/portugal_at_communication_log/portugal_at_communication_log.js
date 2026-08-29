// -*- coding: utf-8 -*-
// Copyright (c) 2026, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

frappe.ui.form.on('Portugal AT Communication Log', {
	refresh: function (frm) {
		// Botão de reenvio manual - só faz sentido num registo já
		// gravado e num estado que indica que a comunicação com a AT
		// ainda não teve sucesso. O backend (retry_now, no controller
		// Python) já existia e já era chamado pela tarefa horária de
		// retry - só faltava um botão na interface para o disparar sem
		// esperar pelo agendamento (next_retry_date pode estar a horas
		// de distância).
		if (!frm.doc.__islocal && ['Failed', 'Retrying'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Reenviar Agora (Retry)'), function () {
				frappe.confirm(
					__(
						'Forçar já o reenvio de {0} {1} à AT, sem esperar pelo próximo agendamento ({2})?',
						[
							frm.doc.document_type,
							frm.doc.document_name,
							frm.doc.next_retry_date ? frappe.datetime.str_to_user(frm.doc.next_retry_date) : __('não definido'),
						]
					),
					function () {
						frappe.call({
							method: 'retry_now',
							doc: frm.doc,
							freeze: true,
							freeze_message: __('A reenviar à AT...'),
							callback: function () {
								frm.reload_doc();
								if (frm.doc.status === 'Success') {
									frappe.show_alert({
										message: __('Reenviado com sucesso: {0}', [frm.doc.at_response_message || frm.doc.at_response_code]),
										indicator: 'green',
									});
								} else {
									frappe.show_alert({
										message: __('Ainda sem sucesso ({0}): {1}', [frm.doc.status, frm.doc.at_response_message || __('sem mensagem')]),
										indicator: 'orange',
									});
								}
							},
						});
					}
				);
			}, __('Portugal Compliance')).addClass('btn-primary');
		}
	},
});
