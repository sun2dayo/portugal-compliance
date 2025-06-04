frappe.ui.form.on('Portugal Auth Settings', {
    refresh: function(frm) {
        // Adicionar botões de ação
        frm.add_custom_button(__('Test Connection'), function() {
            test_at_connection(frm);
        }, __('Actions'));

        frm.add_custom_button(__('Validate Certificate'), function() {
            validate_certificate(frm);
        }, __('Actions'));

        frm.add_custom_button(__('Clear Session Tokens'), function() {
            clear_session_tokens(frm);
        }, __('Actions'));

        // Indicadores de status
        if (frm.doc.ssl_certificate_path) {
            frm.dashboard.add_indicator(__('Certificate Configured'), 'green');
        } else {
            frm.dashboard.add_indicator(__('Certificate Missing'), 'red');
        }

        if (frm.doc.sandbox_mode) {
            frm.dashboard.add_indicator(__('Sandbox Mode'), 'orange');
        } else {
            frm.dashboard.add_indicator(__('Production Mode'), 'blue');
        }

        // Avisos de segurança
        if (!frm.doc.sandbox_mode) {
            frm.dashboard.add_comment(__('Warning: You are in production mode. Ensure all configurations are correct.'), 'red');
        }
    },

    sandbox_mode: function(frm) {
        // Atualizar URL do webservice baseado no modo
        if (frm.doc.sandbox_mode) {
            frm.set_value('at_webservice_url', 'https://servicos-test.portaldasfinancas.gov.pt:722/SeriesWSService');
        } else {
            frm.set_value('at_webservice_url', 'https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService');
        }
    },

    ssl_certificate_path: function(frm) {
        // Validar caminho do certificado
        if (frm.doc.ssl_certificate_path) {
            validate_certificate_path(frm.doc.ssl_certificate_path);
        }
    }
});

function test_at_connection(frm) {
    frappe.show_alert({
        message: __('Testing connection to AT...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'portugal_compliance.utils.at_webservice.test_connection',
        args: {
            webservice_url: frm.doc.at_webservice_url,
            sandbox_mode: frm.doc.sandbox_mode
        },
        callback: function(r) {
            if (r.message && r.message.connected) {
                frappe.msgprint({
                    title: __('Connection Test Successful'),
                    message: __('Successfully connected to AT webservice'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Test Failed'),
                    message: r.message ? r.message.error : __('Failed to connect to AT webservice'),
                    indicator: 'red'
                });
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('Connection Error'),
                message: __('Error testing connection to AT webservice'),
                indicator: 'red'
            });
        }
    });
}

function validate_certificate(frm) {
    if (!frm.doc.ssl_certificate_path) {
        frappe.msgprint({
            title: __('Certificate Path Missing'),
            message: __('Please configure SSL certificate path first'),
            indicator: 'red'
        });
        return;
    }

    frappe.call({
        method: 'portugal_compliance.utils.at_authentication.validate_certificate',
        callback: function(r) {
            if (r.message && r.message.valid) {
                frappe.msgprint({
                    title: __('Certificate Valid'),
                    message: __('SSL certificate is valid and properly configured'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Certificate Invalid'),
                    message: r.message ? r.message.error : __('SSL certificate validation failed'),
                    indicator: 'red'
                });
            }
        }
    });
}

function validate_certificate_path(path) {
    if (!path.endsWith('.pfx')) {
        frappe.msgprint({
            title: __('Invalid Certificate Format'),
            message: __('Certificate file must be in .pfx format'),
            indicator: 'orange'
        });
    }
}

function clear_session_tokens(frm) {
    frappe.confirm(
        __('Are you sure you want to clear all session tokens? This will require re-authentication for all active sessions.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.utils.at_authentication.clear_session_tokens',
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('Session Tokens Cleared'),
                            message: __('All session tokens have been cleared successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}
