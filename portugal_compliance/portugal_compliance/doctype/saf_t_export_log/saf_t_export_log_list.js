frappe.listview_settings['SAF-T Export Log'] = {
	add_fields: ['status', 'company', 'from_date', 'to_date'],

	// Botão de download por linha (2026-09-05, pedido do utilizador -
	// "seria premium" poder descarregar sem abrir cada registo).
	// Reutiliza exatamente a mesma chamada e lógica de blob já usadas
	// no botão "Download SAF-T File" do formulário
	// (saf_t_export_log.js::download_saft_file) - o ficheiro não é um
	// Attach nativo do Frappe (é regenerado on-the-fly pelo endpoint),
	// por isso não existe um URL direto para um <a href> simples.
	button: {
		show: function (doc) {
			return doc.status === 'Completed';
		},
		get_label: function () {
			return __('Download');
		},
		get_description: function (doc) {
			return __('Descarregar o ficheiro SAF-T de {0}', [doc.name]);
		},
		action: function (doc) {
			frappe.call({
				method: 'portugal_compliance.api.saft_api.download_saft_file',
				args: { export_log_name: doc.name },
				callback: function (r) {
					if (r.message && r.message.status === 'success') {
						const blob = new Blob([r.message.content], { type: r.message.content_type });
						const url = URL.createObjectURL(blob);
						const a = document.createElement('a');
						a.href = url;
						a.download = r.message.filename;
						document.body.appendChild(a);
						a.click();
						document.body.removeChild(a);
						URL.revokeObjectURL(url);

						// frappe.call({ doc: {...} }) resolve o documento
						// via frappe.get_doc() do lado do CLIENTE (cache
						// local do Form) - na List View o documento nunca
						// foi carregado para essa cache, por isso vinha
						// undefined e o pedido seguia com corpo vazio
						// (erro real visto ao testar: "orjson.
						// JSONDecodeError: ... zero-length, empty
						// document"). run_doc_method com dt/dn explicitos
						// poe o SERVIDOR a carregar o documento, sem
						// depender de nada ja estar em cache no browser.
						frappe.call({
							method: 'run_doc_method',
							args: {
								dt: 'SAF-T Export Log',
								dn: doc.name,
								method: 'increment_download_count',
							},
						});

						frappe.show_alert({
							message: __('SAF-T file downloaded successfully'),
							indicator: 'green',
						});
					} else {
						frappe.msgprint({
							title: __('Download Error'),
							message: r.message ? r.message.message : __('Error downloading file'),
							indicator: 'red',
						});
					}
				},
			});
		},
	},
};
