frappe.ui.form.on('SAF-T Export Log', {
    refresh: function(frm) {
        // Tornar formulário somente leitura após criação
        if (!frm.doc.__islocal) {
            frm.disable_save();
        }

        // Adicionar indicadores de status
        add_status_indicators(frm);

        // Adicionar botões de ação
        add_action_buttons(frm);

        // Configurar cores dos campos
        set_field_colors(frm);

        // Auto-refresh para exports em progresso
        if (frm.doc.status === 'Pending' || frm.doc.status === 'In Progress') {
            setTimeout(() => {
                frm.reload_doc();
            }, 15000); // Refresh a cada 15 segundos
        }

        // Mostrar estatísticas se disponíveis
        if (frm.doc.status === 'Completed') {
            show_export_statistics(frm);
        }
    },

    status: function(frm) {
        set_field_colors(frm);
    },

    from_date: function(frm) {
        validate_date_range(frm);
    },

    to_date: function(frm) {
        validate_date_range(frm);
    },

    company: function(frm) {
        if (frm.doc.company && !frm.doc.fiscal_year) {
            // Auto-detectar ano fiscal baseado na data
            if (frm.doc.from_date) {
                frappe.call({
                    method: 'frappe.utils.get_fiscal_year',
                    args: {
                        date: frm.doc.from_date,
                        company: frm.doc.company
                    },
                    callback: function(r) {
                        if (r.message) {
                            frm.set_value('fiscal_year', r.message[0]);
                        }
                    }
                });
            }
        }
    }
});

function add_status_indicators(frm) {
    // Limpar indicadores existentes
    frm.dashboard.clear_headline();

    // Indicadores baseados no status
    const status_config = {
        'Pending': { color: 'orange', text: __('Export Pending') },
        'In Progress': { color: 'blue', text: __('Export in Progress') },
        'Completed': { color: 'green', text: __('Export Completed') },
        'Failed': { color: 'red', text: __('Export Failed') },
        'Cancelled': { color: 'grey', text: __('Export Cancelled') }
    };

    const config = status_config[frm.doc.status];
    if (config) {
        frm.dashboard.add_indicator(config.text, config.color);
    }

    // Indicadores adicionais para exports completos
    if (frm.doc.status === 'Completed') {
        // Tamanho do arquivo
        if (frm.doc.file_size) {
            const size_mb = (frm.doc.file_size / 1024 / 1024).toFixed(2);
            frm.dashboard.add_indicator(__('File Size: {0} MB', [size_mb]), 'blue');
        }

        // Tempo de processamento
        if (frm.doc.processing_time) {
            const time_text = frm.doc.processing_time < 60 ?
                __('Processing Time: {0}s', [frm.doc.processing_time.toFixed(1)]) :
                __('Processing Time: {0}m', [(frm.doc.processing_time / 60).toFixed(1)]);
            frm.dashboard.add_indicator(time_text, 'blue');
        }

        // Status de validação
        if (frm.doc.xml_validation_status === 'Valid') {
            frm.dashboard.add_indicator(__('XML Valid'), 'green');
        } else if (frm.doc.xml_validation_status === 'Invalid') {
            frm.dashboard.add_indicator(__('XML Invalid'), 'red');
        }

        // Status de submissão à AT
        if (frm.doc.at_submission_status === 'Accepted') {
            frm.dashboard.add_indicator(__('AT Accepted'), 'green');
        } else if (frm.doc.at_submission_status === 'Rejected') {
            frm.dashboard.add_indicator(__('AT Rejected'), 'red');
        }
    }
}

function add_action_buttons(frm) {
    // Botão para download do arquivo
    if (frm.doc.status === 'Completed' && frm.doc.file_path) {
        frm.add_custom_button(__('Download SAF-T File'), function() {
            download_saft_file(frm);
        }, __('Actions'));
    }

    // Botão para validar XML
    if (frm.doc.status === 'Completed' && frm.doc.xml_validation_status === 'Not Validated') {
        frm.add_custom_button(__('Validate XML'), function() {
            validate_xml(frm);
        }, __('Actions'));
    }

    // Botão para submeter à AT
    if (frm.doc.status === 'Completed' && frm.doc.xml_validation_status === 'Valid' &&
        frm.doc.at_submission_status === 'Not Submitted') {
        frm.add_custom_button(__('Submit to AT'), function() {
            submit_to_at(frm);
        }, __('Actions'));
    }

    // Botão para regenerar export
    if (frm.doc.status === 'Failed' || frm.doc.status === 'Cancelled') {
        frm.add_custom_button(__('Regenerate Export'), function() {
            regenerate_export(frm);
        }, __('Actions'));
    }

    // Botão para cancelar export em progresso
    if (frm.doc.status === 'Pending' || frm.doc.status === 'In Progress') {
        frm.add_custom_button(__('Cancel Export'), function() {
            cancel_export(frm);
        }, __('Actions'));
    }

    // Botão para ver logs relacionados
    frm.add_custom_button(__('View Export Logs'), function() {
        frappe.set_route('List', 'SAF-T Export Log', {
            'company': frm.doc.company,
            'from_date': ['>=', frm.doc.from_date],
            'to_date': ['<=', frm.doc.to_date]
        });
    }, __('Reports'));

    // Botão para exportar estatísticas
    if (frm.doc.status === 'Completed') {
        frm.add_custom_button(__('Export Statistics'), function() {
            export_statistics(frm);
        }, __('Reports'));
    }
}

function set_field_colors(frm) {
    // Cores baseadas no status
    const status_colors = {
        'Pending': 'orange',
        'In Progress': 'blue',
        'Completed': 'green',
        'Failed': 'red',
        'Cancelled': 'grey'
    };

    const color = status_colors[frm.doc.status] || 'grey';

    // Aplicar cor ao campo de status
    frm.get_field('status').$wrapper.find('.control-input').css({
        'border-left': `4px solid var(--${color}-500)`,
        'background-color': `var(--${color}-50)`
    });

    // Destacar validação XML
    if (frm.doc.xml_validation_status === 'Valid') {
        frm.get_field('xml_validation_status').$wrapper.find('.control-input').css({
            'background-color': 'var(--green-50)'
        });
    } else if (frm.doc.xml_validation_status === 'Invalid') {
        frm.get_field('xml_validation_status').$wrapper.find('.control-input').css({
            'background-color': 'var(--red-50)'
        });
    }
}

function validate_date_range(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        const from_date = new Date(frm.doc.from_date);
        const to_date = new Date(frm.doc.to_date);

        if (from_date > to_date) {
            frappe.msgprint({
                title: __('Invalid Date Range'),
                message: __('From Date cannot be greater than To Date'),
                indicator: 'red'
            });
            frm.set_value('to_date', '');
        }

        // Verificar se período não excede 1 ano
        const diff_days = (to_date - from_date) / (1000 * 60 * 60 * 24);
        if (diff_days > 365) {
            frappe.msgprint({
                title: __('Date Range Too Large'),
                message: __('Export period cannot exceed 365 days'),
                indicator: 'orange'
            });
        }
    }
}

function show_export_statistics(frm) {
    if (frm.doc.total_records > 0) {
        const stats_html = `
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${frm.doc.total_records || 0}</h5>
                            <p class="card-text">${__('Total Records')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${frm.doc.sales_invoices_count || 0}</h5>
                            <p class="card-text">${__('Sales Invoices')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${frm.doc.purchase_invoices_count || 0}</h5>
                            <p class="card-text">${__('Purchase Invoices')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${frm.doc.payment_entries_count || 0}</h5>
                            <p class="card-text">${__('Payment Entries')}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        frm.dashboard.add_section(stats_html, __('Export Statistics'));
    }
}

function download_saft_file(frm) {
    frappe.call({
        method: 'portugal_compliance.api.saft_api.download_saft_file',
        args: {
            export_log_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                // Criar blob e fazer download
                const blob = new Blob([r.message.content], {
                    type: r.message.content_type
                });

                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = r.message.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                // Incrementar contador de downloads
                frappe.call({
                    method: 'increment_download_count',
                    doc: frm.doc,
                    callback: function() {
                        frm.reload_doc();
                    }
                });

                frappe.show_alert({
                    message: __('SAF-T file downloaded successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Download Error'),
                    message: r.message ? r.message.message : __('Error downloading file'),
                    indicator: 'red'
                });
            }
        }
    });
}

function validate_xml(frm) {
    frappe.show_alert({
        message: __('Validating XML...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'portugal_compliance.api.saft_api.validate_saft_xml',
        args: {
            export_log_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                if (r.message.valid) {
                    frappe.show_alert({
                        message: __('XML validation successful'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('XML Validation Failed'),
                        message: r.message.validations.map(v => v.message).join('<br>'),
                        indicator: 'red'
                    });
                }
                frm.reload_doc();
            }
        }
    });
}

function submit_to_at(frm) {
    frappe.prompt([
        {
            label: __('AT Username'),
            fieldname: 'username',
            fieldtype: 'Data',
            reqd: 1,
            description: __('Portal das Finanças username')
        },
        {
            label: __('AT Password'),
            fieldname: 'password',
            fieldtype: 'Password',
            reqd: 1,
            description: __('Portal das Finanças password')
        }
    ], function(values) {
        frappe.show_alert({
            message: __('Submitting to AT...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'submit_to_at',
            doc: frm.doc,
            args: {
                username: values.username,
                password: values.password
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('Successfully submitted to AT'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('AT Submission Failed'),
                        message: r.message ? r.message.message : __('Unknown error'),
                        indicator: 'red'
                    });
                }
                frm.reload_doc();
            }
        });
    }, __('Submit SAF-T to AT'));
}

function regenerate_export(frm) {
    frappe.confirm(
        __('Are you sure you want to regenerate this SAF-T export? This will overwrite the existing file.'),
        function() {
            frappe.call({
                method: 'regenerate_export',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Export regeneration started'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Regeneration Failed'),
                            message: r.message ? r.message.message : __('Unknown error'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function cancel_export(frm) {
    frappe.confirm(
        __('Are you sure you want to cancel this export?'),
        function() {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'SAF-T Export Log',
                    name: frm.doc.name,
                    fieldname: 'status',
                    value: 'Cancelled'
                },
                callback: function() {
                    frappe.show_alert({
                        message: __('Export cancelled'),
                        indicator: 'orange'
                    });
                    frm.reload_doc();
                }
            });
        }
    );
}

function export_statistics(frm) {
    const stats = {
        export_details: {
            company: frm.doc.company,
            period: `${frm.doc.from_date} to ${frm.doc.to_date}`,
            export_type: frm.doc.export_type,
            file_size_mb: ((frm.doc.file_size || 0) / 1024 / 1024).toFixed(2)
        },
        record_counts: {
            total_records: frm.doc.total_records || 0,
            sales_invoices: frm.doc.sales_invoices_count || 0,
            purchase_invoices: frm.doc.purchase_invoices_count || 0,
            payment_entries: frm.doc.payment_entries_count || 0,
            journal_entries: frm.doc.journal_entries_count || 0
        },
        processing_info: {
            processing_time_seconds: frm.doc.processing_time || 0,
            validation_status: frm.doc.xml_validation_status,
            submission_status: frm.doc.at_submission_status
        }
    };

    const blob = new Blob([JSON.stringify(stats, null, 2)], {
        type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `saft_export_statistics_${frm.doc.name}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    frappe.show_alert({
        message: __('Statistics exported successfully'),
        indicator: 'green'
    });
}

// Realtime updates para status do export
frappe.realtime.on('saft_export_update', function(data) {
    if (cur_frm && cur_frm.doc.name === data.export_log_name) {
        cur_frm.reload_doc();
    }
});
