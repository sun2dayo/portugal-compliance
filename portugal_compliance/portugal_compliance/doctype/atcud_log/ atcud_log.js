frappe.ui.form.on('ATCUD Log', {
    refresh: function(frm) {
        // Tornar formulário somente leitura
        frm.disable_save();

        // Adicionar indicadores de status
        add_status_indicators(frm);

        // Adicionar botões de ação
        add_action_buttons(frm);

        // Configurar cores dos campos baseado no status
        set_field_colors(frm);

        // Auto-refresh para logs pendentes
        if (frm.doc.generation_status === 'Pending' || frm.doc.generation_status === 'Retrying') {
            setTimeout(() => {
                frm.reload_doc();
            }, 10000); // Refresh a cada 10 segundos
        }
    },

    generation_status: function(frm) {
        set_field_colors(frm);
    }
});

function add_status_indicators(frm) {
    // Limpar indicadores existentes
    frm.dashboard.clear_headline();

    switch(frm.doc.generation_status) {
        case 'Success':
            frm.dashboard.add_indicator(__('ATCUD Generated Successfully'), 'green');
            break;
        case 'Failed':
            frm.dashboard.add_indicator(__('ATCUD Generation Failed'), 'red');
            if (frm.doc.retry_count > 0) {
                frm.dashboard.add_indicator(__('Retry Count: {0}', [frm.doc.retry_count]), 'orange');
            }
            break;
        case 'Pending':
            frm.dashboard.add_indicator(__('ATCUD Generation Pending'), 'orange');
            break;
        case 'Retrying':
            frm.dashboard.add_indicator(__('Retrying ATCUD Generation'), 'blue');
            break;
    }

    // Indicador de tempo de processamento
    if (frm.doc.processing_time) {
        let time_text = frm.doc.processing_time < 1 ?
            __('Processing Time: {0}ms', [Math.round(frm.doc.processing_time * 1000)]) :
            __('Processing Time: {0}s', [frm.doc.processing_time.toFixed(2)]);
        frm.dashboard.add_indicator(time_text, 'blue');
    }
}

function add_action_buttons(frm) {
    // Botão para ver documento original
    if (frm.doc.document_name && frm.doc.document_type) {
        frm.add_custom_button(__('View Original Document'), function() {
            frappe.set_route('Form', frm.doc.document_type, frm.doc.document_name);
        }, __('Actions'));
    }

    // Botão para regenerar ATCUD (apenas para falhas)
    if (frm.doc.generation_status === 'Failed') {
        frm.add_custom_button(__('Retry Generation'), function() {
            retry_atcud_generation(frm);
        }, __('Actions'));
    }

    // Botão para copiar ATCUD (apenas para sucessos)
    if (frm.doc.generation_status === 'Success' && frm.doc.atcud_code) {
        frm.add_custom_button(__('Copy ATCUD'), function() {
            copy_to_clipboard(frm.doc.atcud_code);
            frappe.show_alert({
                message: __('ATCUD copied to clipboard'),
                indicator: 'green'
            });
        }, __('Actions'));
    }

    // Botão para ver logs relacionados
    frm.add_custom_button(__('View Related Logs'), function() {
        frappe.set_route('List', 'ATCUD Log', {
            'document_type': frm.doc.document_type,
            'document_name': frm.doc.document_name
        });
    }, __('Actions'));

    // Botão para exportar detalhes (para debugging)
    if (frm.doc.generation_status === 'Failed') {
        frm.add_custom_button(__('Export Error Details'), function() {
            export_error_details(frm);
        }, __('Debug'));
    }
}

function set_field_colors(frm) {
    // Definir cores dos campos baseado no status
    const status_colors = {
        'Success': 'green',
        'Failed': 'red',
        'Pending': 'orange',
        'Retrying': 'blue'
    };

    const color = status_colors[frm.doc.generation_status] || 'grey';

    // Aplicar cor ao campo de status
    frm.get_field('generation_status').$wrapper.find('.control-input').css({
        'border-left': `4px solid var(--${color}-500)`,
        'background-color': `var(--${color}-50)`
    });

    // Destacar campo ATCUD se gerado com sucesso
    if (frm.doc.generation_status === 'Success' && frm.doc.atcud_code) {
        frm.get_field('atcud_code').$wrapper.find('.control-input').css({
            'background-color': 'var(--green-50)',
            'font-weight': 'bold'
        });
    }
}

function retry_atcud_generation(frm) {
    frappe.confirm(
        __('Are you sure you want to retry ATCUD generation for this document?'),
        function() {
            frappe.show_alert({
                message: __('Retrying ATCUD generation...'),
                indicator: 'blue'
            });

            frappe.call({
                method: 'retry_generation',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('ATCUD regenerated successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Retry Failed'),
                            message: r.message ? r.message.message : __('Unknown error occurred'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('Retry Error'),
                        message: __('Error occurred while retrying ATCUD generation'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function copy_to_clipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback para navegadores mais antigos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    }
}

function export_error_details(frm) {
    const error_data = {
        document_type: frm.doc.document_type,
        document_name: frm.doc.document_name,
        atcud_code: frm.doc.atcud_code,
        generation_status: frm.doc.generation_status,
        error_message: frm.doc.error_message,
        error_traceback: frm.doc.error_traceback,
        retry_count: frm.doc.retry_count,
        generation_date: frm.doc.generation_date,
        system_info: {
            erpnext_version: frm.doc.erpnext_version,
            module_version: frm.doc.module_version,
            user_agent: frm.doc.user_agent
        }
    };

    const blob = new Blob([JSON.stringify(error_data, null, 2)], {
        type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `atcud_error_${frm.doc.name}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    frappe.show_alert({
        message: __('Error details exported successfully'),
        indicator: 'green'
    });
}

// Função para formatar data/hora em português
function format_datetime_pt(datetime) {
    if (!datetime) return '';

    const date = new Date(datetime);
    return date.toLocaleString('pt-PT', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Auto-refresh para logs em processamento
frappe.realtime.on('atcud_log_update', function(data) {
    if (cur_frm && cur_frm.doc.name === data.log_name) {
        cur_frm.reload_doc();
    }
});
