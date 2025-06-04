/**
 * Portugal Compliance Module - VERSÃO CERTIFICADA UNIFICADA
 * Handles global functionality for Portugal fiscal compliance
 * Integra toda a lógica: global, company, validações, etc.
 */
// ✅ VERIFICAÇÃO DE SEGURANÇA - ADICIONAR NO INÍCIO DO ARQUIVO
if (typeof frappe === 'undefined') {
    console.error('Frappe não está carregado');
    throw new Error('Frappe framework não disponível');
}

// ✅ INICIALIZAÇÃO SEGURA
window.portugal_compliance = window.portugal_compliance || {};

// ✅ VERIFICAR SE JQUERY ESTÁ DISPONÍVEL
if (typeof $ === 'undefined') {
    console.error('jQuery não está carregado');
    throw new Error('jQuery não disponível');
}

// ✅ AGUARDAR CARREGAMENTO COMPLETO
$(document).ready(function() {
    console.log('Portugal Compliance JS carregado com sucesso');

    // Inicializar apenas se frappe.ui estiver disponível
    if (frappe && frappe.ui && frappe.ui.form) {
        // Seu código de inicialização aqui
        portugal_compliance.init();
    } else {
        console.warn('Frappe UI não está pronto, aguardando...');
        setTimeout(function() {
            if (frappe && frappe.ui && frappe.ui.form) {
                portugal_compliance.init();
            }
        }, 1000);
    }
});

// Global namespace for Portugal Compliance
window.portugal_compliance = {
    version: '2.0.0',
    initialized: false,

    // Configuration
    config: {
        atcud_pattern: /^[A-Z0-9]{8,12}$/,
        nif_pattern: /^\d{9}$/,
        series_pattern: /^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}$/,
        supported_doctypes: [
            'Sales Invoice', 'Purchase Invoice', 'Payment Entry',
            'Delivery Note', 'Purchase Receipt', 'Journal Entry', 'Stock Entry',
            'Quotation', 'Sales Order', 'Purchase Order', 'Material Request'
        ]
    },

    // ========== INICIALIZAÇÃO ==========

    init: function() {
        if (this.initialized) return;

        console.log('🇵🇹 Initializing Portugal Compliance Module v' + this.version);

        // Setup global event listeners
        this.setupGlobalEvents();

        // Initialize validators
        this.initializeValidators();

        // Setup real-time updates
        this.setupRealtimeUpdates();

        // Initialize company module
        this.company.init();

        this.initialized = true;
        console.log('✅ Portugal Compliance Module initialized successfully');
    },

    // ========== EVENTOS GLOBAIS ==========

    setupGlobalEvents: function() {
        const self = this;

        // Listen for form refresh events
        $(document).on('form-refresh', function(e, frm) {
            if (self.isSupportedDoctype(frm.doctype)) {
                self.enhanceForm(frm);
            }

            // Company-specific enhancements
            if (frm.doctype === 'Company') {
                self.company.enhance_form(frm);
            }
        });

        // Listen for document save events
        $(document).on('before-save', function(e, frm) {
            if (self.isSupportedDoctype(frm.doctype)) {
                self.validateBeforeSave(frm);
            }
        });

        // Listen for naming series changes
        $(document).on('naming-series-changed', function(e, frm) {
            if (self.isSupportedDoctype(frm.doctype)) {
                self.onNamingSeriesChange(frm);
            }
        });
    },

    setupRealtimeUpdates: function() {
        // Listen for ATCUD generation updates
        frappe.realtime.on('atcud_generated', function(data) {
            if (cur_frm && cur_frm.doc.name === data.document_name) {
                cur_frm.reload_doc();
                frappe.show_alert({
                    message: __('ATCUD generated: {0}', [data.atcud]),
                    indicator: 'green'
                });
            }
        });

        // Listen for series communication updates
        frappe.realtime.on('series_communicated', function(data) {
            frappe.show_alert({
                message: __('Series {0} communicated to AT successfully', [data.series]),
                indicator: 'green'
            });

            // Refresh current form if it's related
            if (cur_frm && cur_frm.doc.company === data.company) {
                cur_frm.refresh();
            }
        });

        // Listen for compliance status updates
        frappe.realtime.on('compliance_status_changed', function(data) {
            if (cur_frm && cur_frm.doc.company === data.company) {
                portugal_compliance.company.update_visual_feedback(cur_frm);
            }
        });
    },

    // ========== VALIDADORES GLOBAIS ==========

    initializeValidators: function() {
        const self = this;

        // NIF validator for Customer
        frappe.ui.form.on('Customer', {
            tax_id: function(frm) {
                if (frm.doc.tax_id) {
                    self.validateNIF(frm.doc.tax_id, function(is_valid) {
                        self.showNIFValidationResult(frm, is_valid);
                    });
                }
            }
        });

        // NIF validator for Supplier
        frappe.ui.form.on('Supplier', {
            tax_id: function(frm) {
                if (frm.doc.tax_id) {
                    self.validateNIF(frm.doc.tax_id, function(is_valid) {
                        self.showNIFValidationResult(frm, is_valid);
                    });
                }
            }
        });

        // ATCUD validator for supported doctypes
        this.config.supported_doctypes.forEach(function(doctype) {
            frappe.ui.form.on(doctype, {
                atcud_code: function(frm) {
                    if (frm.doc.atcud_code) {
                        self.validateATCUD(frm.doc.atcud_code, function(is_valid) {
                            self.showATCUDValidationResult(frm, is_valid);
                        });
                    }
                }
            });
        });
    },

    // ========== FUNCIONALIDADES PRINCIPAIS ==========

    isSupportedDoctype: function(doctype) {
        return this.config.supported_doctypes.includes(doctype);
    },

    enhanceForm: function(frm) {
        // Add ATCUD indicator
        this.addATCUDIndicator(frm);

        // Add compliance status
        this.addComplianceStatus(frm);

        // Add quick actions
        this.addQuickActions(frm);

        // Add Portugal-specific styling
        this.addPortugalStyling(frm);
    },

    addATCUDIndicator: function(frm) {
        if (frm.doc.atcud_code) {
            frm.dashboard.add_indicator(__('🆔 ATCUD: {0}', [frm.doc.atcud_code]), 'green');
        } else if (frm.doc.docstatus === 1) {
            frm.dashboard.add_indicator(__('❌ ATCUD Missing'), 'red');
        }
    },

    addComplianceStatus: function(frm) {
        const self = this;

        if (frm.doc.naming_series) {
            // Extract prefix from naming series
            const prefix = frm.doc.naming_series.replace('.####', '');

            frappe.call({
                method: 'portugal_compliance.utils.series_adapter.get_doctype_statistics',
                args: { doctype: frm.doctype },
                callback: function(r) {
                    if (r.message && r.message.is_portuguese) {
                        const status = r.message.series_communicated ? 'Comunicada' : 'Não Comunicada';
                        const indicator = r.message.series_communicated ? 'green' : 'orange';
                        frm.dashboard.add_indicator(__('📊 Série: {0}', [status]), indicator);
                    }
                }
            });
        }
    },

    addQuickActions: function(frm) {
        const self = this;

        // Generate ATCUD button
        if (frm.doc.docstatus === 1 && !frm.doc.atcud_code) {
            frm.add_custom_button(__('Generate ATCUD'), function() {
                self.generateATCUD(frm);
            }, __('🇵🇹 Portugal Compliance'));
        }

        // Validate ATCUD button
        if (frm.doc.docstatus === 1 && frm.doc.atcud_code) {
            frm.add_custom_button(__('Validate ATCUD'), function() {
                self.validateATCUD(frm.doc.atcud_code);
            }, __('🇵🇹 Portugal Compliance'));
        }

        // Show QR Code button
        if (frm.doc.docstatus === 1 && frm.doc.atcud_code) {
            frm.add_custom_button(__('Show QR Code'), function() {
                self.showQRCode(frm);
            }, __('🇵🇹 Portugal Compliance'));
        }

        // Export SAF-T button (for invoices)
        if (frm.doctype === 'Sales Invoice' && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Export SAF-T'), function() {
                self.exportSAFT(frm);
            }, __('🇵🇹 Portugal Compliance'));
        }
    },

    addPortugalStyling: function(frm) {
        // Add Portuguese flag indicator if applicable
        if (frm.doc.company) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Company',
                    filters: { name: frm.doc.company },
                    fieldname: ['country', 'portugal_compliance_enabled']
                },
                callback: function(r) {
                    if (r.message && r.message.country === 'Portugal' && r.message.portugal_compliance_enabled) {
                        frm.dashboard.add_indicator(__('🇵🇹 Portugal Compliance Active'), 'blue');
                    }
                }
            });
        }
    },

    // ========== VALIDAÇÕES ==========

    validateBeforeSave: function(frm) {
        const self = this;

        // Check if company has Portugal compliance enabled
        if (frm.doc.company) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Company',
                    filters: { name: frm.doc.company },
                    fieldname: ['portugal_compliance_enabled', 'country']
                },
                callback: function(r) {
                    if (r.message && r.message.country === 'Portugal' && r.message.portugal_compliance_enabled) {
                        self.validatePortugueseDocument(frm);
                    }
                }
            });
        }
    },

    validatePortugueseDocument: function(frm) {
        // Validate naming series is Portuguese
        if (!frm.doc.naming_series) {
            frappe.validated = false;
            frappe.msgprint({
                title: __('Naming Series Required'),
                message: __('Please select a Portuguese naming series for this document'),
                indicator: 'red'
            });
            return;
        }

        // Extract and validate prefix
        const prefix = frm.doc.naming_series.replace('.####', '');
        if (!this.validateSeriesFormat(prefix)) {
            frappe.validated = false;
            frappe.msgprint({
                title: __('Invalid Series Format'),
                message: __('Series format should be XX-YYYY-COMPANY'),
                indicator: 'red'
            });
        }
    },

    validateNIF: function(nif, callback) {
        if (!nif) {
            if (callback) callback(false);
            return false;
        }

        // Remove spaces and non-digits
        nif = nif.replace(/\D/g, '');

        // Check length
        if (nif.length !== 9) {
            if (callback) callback(false);
            return false;
        }

        // Check if starts with valid digit
        const first_digit = parseInt(nif[0]);
        const valid_first_digits = [1, 2, 3, 5, 6, 7, 8, 9];

        if (!valid_first_digits.includes(first_digit)) {
            if (callback) callback(false);
            return false;
        }

        // Calculate check digit
        let sum = 0;
        for (let i = 0; i < 8; i++) {
            sum += parseInt(nif[i]) * (9 - i);
        }

        const remainder = sum % 11;
        const check_digit = remainder < 2 ? 0 : 11 - remainder;

        const is_valid = check_digit === parseInt(nif[8]);

        if (callback) callback(is_valid);
        return is_valid;
    },

    validateATCUD: function(atcud, callback) {
        if (!atcud) {
            if (callback) callback(false);
            return false;
        }

        const is_valid = this.config.atcud_pattern.test(atcud);

        if (callback) {
            callback(is_valid);
        } else {
            if (is_valid) {
                frappe.show_alert({
                    message: __('✅ ATCUD format is valid'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Invalid ATCUD'),
                    message: __('ATCUD format is invalid'),
                    indicator: 'red'
                });
            }
        }

        return is_valid;
    },

    validateSeriesFormat: function(series, callback) {
        const is_valid = this.config.series_pattern.test(series);

        if (callback) callback(is_valid);
        return is_valid;
    },

    // ========== FEEDBACK VISUAL ==========

    showNIFValidationResult: function(frm, is_valid) {
        const field = frm.get_field('tax_id');
        if (field) {
            if (is_valid) {
                field.$wrapper.removeClass('has-error').addClass('has-success');
                frm.set_df_property('tax_id', 'description', '✅ NIF válido');
            } else {
                field.$wrapper.removeClass('has-success').addClass('has-error');
                frm.set_df_property('tax_id', 'description', '❌ NIF inválido');
            }
            frm.refresh_field('tax_id');
        }
    },

    showATCUDValidationResult: function(frm, is_valid) {
        const field = frm.get_field('atcud_code');
        if (field) {
            if (is_valid) {
                field.$wrapper.removeClass('has-error').addClass('has-success');
                frm.set_df_property('atcud_code', 'description', '✅ ATCUD válido');
            } else {
                field.$wrapper.removeClass('has-success').addClass('has-error');
                frm.set_df_property('atcud_code', 'description', '❌ ATCUD inválido');
            }
            frm.refresh_field('atcud_code');
        }
    },

    // ========== AÇÕES RÁPIDAS ==========

    generateATCUD: function(frm) {
        frappe.call({
            method: 'portugal_compliance.utils.document_hooks.generate_manual_atcud',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Generating ATCUD...'),
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('✅ ATCUD generated successfully: {0}', [r.message.atcud_code]),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('ATCUD Generation Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    showQRCode: function(frm) {
        frappe.call({
            method: 'portugal_compliance.utils.jinja_methods.get_qr_code_data',
            args: { doc: frm.doc },
            callback: function(r) {
                if (r.message) {
                    const qr_dialog = new frappe.ui.Dialog({
                        title: __('QR Code - {0}', [frm.doc.name]),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: `
                                    <div style="text-align: center; padding: 20px;">
                                        <div id="qr-code-container"></div>
                                        <p style="margin-top: 15px; font-family: monospace; font-size: 12px; word-break: break-all;">
                                            ${r.message}
                                        </p>
                                    </div>
                                `
                            }
                        ]
                    });

                    qr_dialog.show();

                    // Generate QR Code using qrcode.js
                    setTimeout(() => {
                        if (typeof QRCode !== 'undefined') {
                            new QRCode(document.getElementById("qr-code-container"), {
                                text: r.message,
                                width: 256,
                                height: 256
                            });
                        }
                    }, 100);
                }
            }
        });
    },

    exportSAFT: function(frm) {
        frappe.call({
            method: 'portugal_compliance.utils.saft_export.export_document_saft',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Exporting SAF-T...'),
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('✅ SAF-T exported successfully'),
                        indicator: 'green'
                    });

                    // Download file
                    if (r.message.file_url) {
                        window.open(r.message.file_url, '_blank');
                    }
                } else {
                    frappe.msgprint({
                        title: __('SAF-T Export Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    // ========== EVENTOS ESPECÍFICOS ==========

    onNamingSeriesChange: function(frm) {
        if (frm.doc.naming_series) {
            const prefix = frm.doc.naming_series.replace('.####', '');

            // Validate prefix format
            if (this.validateSeriesFormat(prefix)) {
                frm.dashboard.add_indicator(__('✅ Portuguese Series'), 'green');
            } else {
                frm.dashboard.add_indicator(__('⚠️ Non-Portuguese Series'), 'orange');
            }
        }
    },

    // ========== UTILITÁRIOS ==========

    formatCurrency: function(amount) {
        return new Intl.NumberFormat('pt-PT', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    },

    formatDate: function(date) {
        return new Intl.DateTimeFormat('pt-PT').format(new Date(date));
    },

    copyToClipboard: function(text) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text);
            frappe.show_alert(__('Copied to clipboard'), 'green');
        } else {
            // Fallback for older browsers
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
            frappe.show_alert(__('Copied to clipboard'), 'green');
        }
    },

    // ========== MÓDULO COMPANY ==========

    company: {
        init: function() {
            console.log('🏢 Initializing Company module');
            this.setupCompanyEvents();
        },

        setupCompanyEvents: function() {
            const self = this;

            // Company form events
            frappe.ui.form.on('Company', {
                refresh: function(frm) {
                    self.setup_buttons(frm);
                    self.setup_indicators(frm);
                    self.update_visual_feedback(frm);
                },

                country: function(frm) {
                    self.on_country_change(frm);
                },

                portugal_compliance_enabled: function(frm) {
                    self.on_compliance_toggle(frm);
                },

                before_save: function(frm) {
                    self.before_save_validations(frm);
                }
            });
        },

		enhance_form: function(frm) {
			try {
				console.log('🔧 Iniciando enhance_form para:', frm.doctype);

				// ✅ VERIFICAR SE FUNÇÕES EXISTEM ANTES DE CHAMAR
				if (typeof this.setup_conditional_fields === 'function') {
					this.setup_conditional_fields(frm);
				} else {
					console.warn('setup_conditional_fields não está definida');
				}

				// ✅ AGUARDAR FORMULÁRIO ESTAR PRONTO PARA VALIDAÇÕES
				setTimeout(() => {
					if (typeof this.setup_realtime_validations === 'function') {
						this.setup_realtime_validations(frm);
					} else {
						console.warn('setup_realtime_validations não está definida');
					}
				}, 500);

				if (typeof this.update_visual_feedback === 'function') {
					this.update_visual_feedback(frm);
				} else {
					console.warn('update_visual_feedback não está definida');
				}

				console.log('✅ enhance_form concluído');

			} catch (error) {
				console.error('❌ Erro em enhance_form:', error);
				frappe.show_alert({
					message: __('Erro ao melhorar formulário: {0}', [error.message]),
					indicator: 'red'
				});
			}
		},


		setup_buttons: function(frm) {
			// ✅ SEMPRE LIMPAR BOTÕES PRIMEIRO
			frm.clear_custom_buttons();

			// ✅ VERIFICAR SE DOCUMENTO ESTÁ SALVO
			const is_saved = !frm.doc.__islocal;

			// ✅ BOTÕES SEMPRE VISÍVEIS PARA EMPRESAS PORTUGUESAS COM COMPLIANCE
			if (frm.doc.country === 'Portugal' && frm.doc.portugal_compliance_enabled && is_saved) {

				// Configurar Credenciais AT
				frm.add_custom_button(__('⚙️ Configurar Credenciais AT'), function() {
					portugal_compliance.company.configure_at_credentials(frm);
				}, __('🇵🇹 Portugal Compliance'));

				// Criar Séries (sempre disponível)
				frm.add_custom_button(__('📋 Criar Séries Portuguesas'), function() {
					portugal_compliance.company.create_portugal_series_dialog(frm);
				}, __('🇵🇹 Portugal Compliance'));

				// Comunicar Séries (sempre disponível)
				frm.add_custom_button(__('📡 Comunicar Séries à AT'), function() {
					portugal_compliance.company.communicate_all_series(frm);
				}, __('🇵🇹 Portugal Compliance'));

				// Sincronizar Naming Series
				frm.add_custom_button(__('🔄 Sincronizar Naming Series'), function() {
					portugal_compliance.company.sync_all_naming_series(frm);
				}, __('🇵🇹 Portugal Compliance'));

				// Ver Séries Configuradas
				frm.add_custom_button(__('👁️ Ver Séries'), function() {
					frappe.set_route('List', 'Portugal Series Configuration', {
						'company': frm.doc.name
					});
				}, __('🇵🇹 Portugal Compliance'));

				// Diagnóstico (apenas para System Manager)
				if (frappe.user.has_role(['System Manager'])) {
					frm.add_custom_button(__('🔍 Diagnóstico'), function() {
						portugal_compliance.company.run_compliance_diagnostics(frm);
					}, __('🇵🇹 Portugal Compliance'));
				}

				// Desativar Compliance
				frm.add_custom_button(__('❌ Desativar Compliance'), function() {
					portugal_compliance.company.deactivate_portugal_compliance(frm);
				}, __('🇵🇹 Portugal Compliance'));
			}

			// ✅ BOTÃO PARA ATIVAR COMPLIANCE (se não estiver ativo)
			else if (frm.doc.country === 'Portugal' && !frm.doc.portugal_compliance_enabled && is_saved) {
				frm.add_custom_button(__('🇵🇹 Ativar Portugal Compliance'), function() {
					portugal_compliance.company.activate_portugal_compliance(frm);
				}, __('🇵🇹 Portugal Compliance'));
			}
		},


        setup_indicators: function(frm) {
            frm.dashboard.clear_headline();

            // Country indicator
            if (frm.doc.country) {
                const country_icon = frm.doc.country === 'Portugal' ? '🇵🇹' : '🌍';
                frm.dashboard.add_indicator(__(`${country_icon} País: {0}`, [frm.doc.country]),
                    frm.doc.country === 'Portugal' ? 'green' : 'blue');
            }

            // Compliance indicator
            if (frm.doc.country === 'Portugal') {
                if (frm.doc.portugal_compliance_enabled) {
                    frm.dashboard.add_indicator(__('✅ Portugal Compliance: Ativo'), 'green');
                    this.check_series_count(frm);
                } else {
                    frm.dashboard.add_indicator(__('❌ Portugal Compliance: Inativo'), 'red');
                }
            }

            // NIF indicator
            if (frm.doc.tax_id) {
                const nif_valid = portugal_compliance.validateNIF(frm.doc.tax_id);
                frm.dashboard.add_indicator(__(`🆔 NIF: ${nif_valid ? 'Válido' : 'Inválido'}`),
                    nif_valid ? 'green' : 'orange');
            }

            // AT Certificate indicator
            if (frm.doc.at_certificate_number) {
                frm.dashboard.add_indicator(__('📜 Certificado AT: Configurado'), 'blue');
            }
        },

        setup_conditional_fields: function(frm) {
            if (frm.doc.country === 'Portugal') {
                this.show_portugal_fields(frm);
            } else {
                this.hide_portugal_fields(frm);
            }

            if (frm.doc.portugal_compliance_enabled) {
                this.show_compliance_fields(frm);
            } else {
                this.hide_compliance_fields(frm);
            }
        },

		setup_realtime_validations: function(frm) {
			// ✅ USAR EVENTOS NATIVOS DO FRAPPE
			if (frm.fields_dict.tax_id) {
				frm.fields_dict.tax_id.df.onchange = function() {
					if (frm.doc.tax_id && frm.doc.country === 'Portugal') {
						portugal_compliance.validate_nif_realtime(frm);
					}
				};
			}

			if (frm.fields_dict.at_certificate_number) {
				frm.fields_dict.at_certificate_number.df.onchange = function() {
					if (frm.doc.at_certificate_number) {
						portugal_compliance.validate_certificate_realtime(frm);
					}
				};
			}
		},

        on_country_change: function(frm) {
            console.log('🌍 País alterado:', frm.doc.country);

            if (frm.doc.country !== 'Portugal' && frm.doc.portugal_compliance_enabled) {
                frappe.confirm(
                    __('País alterado para {0}. Desativar Portugal Compliance?', [frm.doc.country]),
                    function() {
                        frm.set_value('portugal_compliance_enabled', 0);
                        frm.set_value('at_certificate_number', '');
                    }
                );
            }

            this.setup_conditional_fields(frm);
            this.update_visual_feedback(frm);
            frm.refresh();
        },

        on_compliance_toggle: function(frm) {
            console.log('🇵🇹 Portugal Compliance alterado:', frm.doc.portugal_compliance_enabled);

            if (frm.doc.portugal_compliance_enabled) {
                this.on_compliance_activated(frm);
            } else {
                this.on_compliance_deactivated(frm);
            }

            this.setup_conditional_fields(frm);
            this.update_visual_feedback(frm);
            frm.refresh();
        },

        on_compliance_activated: function(frm) {
            console.log('✅ Portugal Compliance ativado');

            this.show_compliance_fields(frm);

            if (frm.doc.country !== 'Portugal') {
                frappe.msgprint({
                    title: __('Aviso'),
                    message: __('Portugal Compliance deve ser usado apenas para empresas portuguesas.'),
                    indicator: 'orange'
                });
            }

            if (!frm.doc.__islocal) {
                setTimeout(() => {
                    this.suggest_series_creation(frm);
                }, 1000);
            }
        },

        on_compliance_deactivated: function(frm) {
            console.log('❌ Portugal Compliance desativado');
            this.hide_compliance_fields(frm);

            if (!frm.doc.__islocal) {
                frappe.msgprint({
                    title: __('Compliance Desativado'),
                    message: __('Séries portuguesas serão desativadas e naming series restauradas.'),
                    indicator: 'orange'
                });
            }
        },

        activate_portugal_compliance: function(frm) {
            if (frm.doc.country !== 'Portugal') {
                frappe.msgprint({
                    title: __('Erro'),
                    message: __('Portugal Compliance só pode ser ativado para empresas portuguesas.'),
                    indicator: 'red'
                });
                return;
            }

            frappe.confirm(
                __('Ativar Portugal Compliance para {0}?<br><br>' +
                   '<strong>Isto irá:</strong><br>' +
                   '• Criar séries portuguesas automaticamente<br>' +
                   '• Substituir naming series por séries portuguesas<br>' +
                   '• Ativar validações de compliance<br>' +
                   '• Configurar campos obrigatórios<br><br>' +
                   'Continuar?', [frm.doc.name]),
                function() {
                    frm.set_value('portugal_compliance_enabled', 1);
                    frm.save().then(() => {
                        portugal_compliance.company.create_initial_series(frm);
                    });
                }
            );
        },

        deactivate_portugal_compliance: function(frm) {
            frappe.confirm(
                __('Desativar Portugal Compliance para {0}?<br><br>' +
                   '<strong>⚠️ Atenção:</strong><br>' +
                   '• Séries portuguesas serão desativadas<br>' +
                   '• Naming series serão restauradas para padrão<br>' +
                   '• Documentos existentes não serão afetados<br>' +
                   '• Esta ação pode ser revertida<br><br>' +
                   'Continuar?', [frm.doc.name]),
                function() {
                    frm.set_value('portugal_compliance_enabled', 0);
                    frm.set_value('at_certificate_number', '');
                    frm.save().then(() => {
                        frappe.show_alert('Portugal Compliance desativado', 'orange');
                    });
                }
            );
        },

		create_initial_series: function(frm) {
			const progress_dialog = this.show_series_creation_progress();

			frappe.call({
				// ✅ CORRIGIDO: Usar método whitelisted que funciona
				method: 'portugal_compliance.api.company_api.create_company_series',
				args: {
					// ✅ CORRIGIDO: Argumentos corretos
					company: frm.doc.name
				},
				freeze: true,
				freeze_message: __('Criando séries portuguesas...'),
				callback: function(r) {
					progress_dialog.hide();

					if (r.message && r.message.success) {
						// ✅ MOSTRAR RESULTADO DE SUCESSO
						frappe.msgprint({
							title: __('✅ Séries Criadas'),
							message: __('<div class="alert alert-success">' +
									   '<strong>Séries criadas com sucesso!</strong><br><br>' +
									   '• Total criadas: {0}<br>' +
									   '• Empresa: {1}<br><br>' +
									   '<em>As séries estão prontas para uso.</em>' +
									   '</div>', [r.message.created_count, frm.doc.name]),
							indicator: 'green'
						});

						// ✅ RECARREGAR FORMULÁRIO
						frm.refresh();

						// ✅ TRIGGER EVENTO PERSONALIZADO
						if (portugal_compliance.company && typeof portugal_compliance.company.show_series_creation_results === 'function') {
							portugal_compliance.company.show_series_creation_results(frm, r.message);
						}
					} else {
						const error_msg = r.message ? r.message.error : __('Erro ao criar séries');
						console.error('Erro na criação de séries:', r.message);

						frappe.msgprint({
							title: __('❌ Erro na Criação'),
							message: __('<div class="alert alert-danger">' +
									   '<strong>Erro:</strong> {0}<br><br>' +
									   '<em>Verifique se a empresa é portuguesa e tem compliance ativado.</em>' +
									   '</div>', [error_msg]),
							indicator: 'red'
						});
					}
				},
				error: function(xhr, status, error) {
					progress_dialog.hide();
					console.error('Erro de comunicação:', {xhr, status, error});

					let error_details = '';
					if (xhr.responseJSON && xhr.responseJSON.exception) {
						error_details = `<br><br><strong>Detalhes:</strong><br><code>${xhr.responseJSON.exception}</code>`;
					}

					frappe.msgprint({
						title: __('❌ Erro de Comunicação'),
						message: __('<div class="alert alert-danger">' +
								   '<strong>Erro na comunicação com o servidor:</strong><br>' +
								   '{0}{1}' +
								   '</div>', [error || 'Erro desconhecido', error_details]),
						indicator: 'red'
					});
				}
			});
		},

        create_portugal_series_dialog: function(frm) {
            const dialog = new frappe.ui.Dialog({
                title: __('Criar Séries Portuguesas'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div style="padding: 15px;">
                                <h5>📋 Séries que serão criadas:</h5>
                                <ul>
                                    <li><strong>FT-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Fatura</li>
                                    <li><strong>FS-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Fatura Simplificada</li>
                                    <li><strong>FR-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Fatura Recibo</li>
                                    <li><strong>NC-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Nota de Crédito</li>
                                    <li><strong>ND-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Nota de Débito</li>
                                    <li><strong>FC-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Fatura de Compra</li>
                                    <li><strong>RC-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Recibo</li>
                                    <li><strong>GT-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Guia de Transporte</li>
                                    <li><strong>GR-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Guia de Receção</li>
                                    <li><strong>JE-${new Date().getFullYear()}-${frm.doc.abbr}</strong> - Lançamento Contabilístico</li>
                                </ul>
                                <p><em>As séries serão criadas automaticamente e as naming series dos DocTypes serão atualizadas.</em></p>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Criar Séries'),
                primary_action: function() {
                    dialog.hide();
                    portugal_compliance.company.create_initial_series(frm);
                },
                secondary_action_label: __('Cancelar')
            });
            dialog.show();
        },

		communicate_all_series: function(frm) {
			// ✅ RECARREGAR DOCUMENTO PARA GARANTIR DADOS ATUAIS
			frm.reload_doc().then(() => {
				// ✅ VERIFICAR CREDENCIAIS APÓS RELOAD
				console.log('🔍 Verificando credenciais:', {
					username: frm.doc.at_username,
					has_password: !!frm.doc.at_password,
					environment: frm.doc.at_environment,
					company: frm.doc.name
				});

				// ✅ VALIDAÇÃO ROBUSTA DE CREDENCIAIS
				if (!frm.doc.at_username || !frm.doc.at_password) {
					frappe.msgprint({
						title: __('Credenciais AT Em Falta'),
						message: __('Configure as credenciais AT antes de comunicar séries.<br><br>' +
								   '<strong>Estado atual:</strong><br>' +
								   '• Utilizador: {0}<br>' +
								   '• Password: {1}<br>' +
								   '• Ambiente: {2}<br><br>' +
								   '<em>Use o botão "⚙️ Configurar Credenciais AT" para definir as credenciais.</em>', [
							frm.doc.at_username || '❌ Não definido',
							frm.doc.at_password ? '✅ Definida' : '❌ Não definida',
							frm.doc.at_environment || 'test'
						]),
						indicator: 'orange',
						primary_action: {
							label: __('Configurar Agora'),
							action: function() {
								portugal_compliance.company.configure_at_credentials(frm);
							}
						}
					});
					return;
				}

				// ✅ CONFIRMAÇÃO COM INFORMAÇÕES DETALHADAS
				frappe.confirm(
					__('Comunicar todas as séries não comunicadas de <strong>{0}</strong> à AT?<br><br>' +
					   '<div class="alert alert-info" style="margin: 10px 0;">' +
					   '<strong>📋 Configuração:</strong><br>' +
					   '• Utilizador: <code>{1}</code><br>' +
					   '• Ambiente: <code>{2}</code><br>' +
					   '• Empresa: <code>{3}</code>' +
					   '</div>' +
					   '<em>Esta operação irá comunicar apenas as séries que ainda não foram comunicadas.</em>',
					   [frm.doc.name, frm.doc.at_username, frm.doc.at_environment || 'test', frm.doc.name]),
					function() {
						// ✅ BUSCAR SÉRIES NÃO COMUNICADAS PRIMEIRO
						frappe.call({
							method: 'frappe.client.get_list',
							args: {
								'doctype': 'Portugal Series Configuration',
								'filters': {
									'company': frm.doc.name,
									'is_active': 1,
									'is_communicated': 0
								},
								'fields': ['name', 'prefix', 'document_type', 'series_name']
							},
							freeze: false,
							callback: function(r) {
								if (r.message && r.message.length > 0) {
									console.log('✅ Séries encontradas para comunicar:', r.message);

									// ✅ EXTRAIR NOMES DAS SÉRIES
									const series_names = r.message.map(series => series.name);
									const series_info = r.message;

									console.log('📋 Séries a comunicar:', series_names);

									// ✅ MOSTRAR CONFIRMAÇÃO FINAL COM LISTA DE SÉRIES
									let series_list = '<ul>';
									series_info.forEach(series => {
										series_list += `<li><strong>${series.prefix}</strong> - ${series.series_name || series.document_type}</li>`;
									});
									series_list += '</ul>';

									frappe.confirm(
										__('Confirmar comunicação de <strong>{0} séries</strong>?<br><br>' +
										   '<div class="alert alert-warning">' +
										   '<strong>📋 Séries a comunicar:</strong>' +
										   '{1}' +
										   '</div>' +
										   '<em>⚠️ Esta operação não pode ser desfeita.</em>',
										   [series_names.length, series_list]),
										function() {
											// ✅ MOSTRAR PROGRESSO
											const progress_dialog = portugal_compliance.company.show_communication_progress();

											// ✅ CORRIGIDO: USAR MÉTODO WHITELISTED ALTERNATIVO
											frappe.call({
												method: 'portugal_compliance.api.company_api.save_company_settings',
												args: {
													company_settings: {
														company: frm.doc.name,
														action: 'communicate_series',
														series_names: series_names,
														username: frm.doc.at_username,
														password: frm.doc.at_password,
														environment: frm.doc.at_environment || 'test'
													}
												},
												freeze: true,
												freeze_message: __('Comunicando {0} séries à AT...', [series_names.length]),
												callback: function(r) {
													progress_dialog.hide();
													console.log('📡 Resultado comunicação:', r.message);

													if (r.message && r.message.success) {
														// ✅ SUCESSO - MOSTRAR RESULTADOS DETALHADOS
														frappe.msgprint({
															title: __('✅ Comunicação Concluída'),
															message: __('<div class="alert alert-success">' +
																	   '<strong>Séries comunicadas com sucesso!</strong><br><br>' +
																	   '• Total processadas: {0}<br>' +
																	   '• Sucessos: {1}<br>' +
																	   '• Falhas: {2}<br><br>' +
																	   '<em>As séries foram marcadas como comunicadas.</em>' +
																	   '</div>', [
																series_names.length,
																r.message.successful || series_names.length,
																r.message.failed || 0
															]),
															indicator: 'green'
														});

														// ✅ RECARREGAR FORMULÁRIO PARA ATUALIZAR INDICADORES
														frm.reload_doc().then(() => {
															if (portugal_compliance.company.setup_buttons) {
																portugal_compliance.company.setup_buttons(frm);
															}
															if (portugal_compliance.company.setup_indicators) {
																portugal_compliance.company.setup_indicators(frm);
															}
														});

														// ✅ NOTIFICAÇÃO DE SUCESSO
														frappe.show_alert({
															message: __('✅ Comunicação concluída: {0} sucessos, {1} falhas',
																	   [r.message.successful || series_names.length, r.message.failed || 0]),
															indicator: 'green'
														});
													} else {
														// ✅ ERRO - MOSTRAR DETALHES
														const error_msg = r.message ? r.message.error : __('Erro na comunicação');
														console.error('❌ Erro na comunicação:', r.message);

														frappe.msgprint({
															title: __('❌ Erro na Comunicação'),
															message: __('<div class="alert alert-danger">' +
																	   '<strong>Erro:</strong> {0}<br><br>' +
																	   '<em>Verifique as credenciais AT e tente novamente.</em>' +
																	   '</div>', [error_msg]),
															indicator: 'red',
															primary_action: {
																label: __('Verificar Credenciais'),
																action: function() {
																	portugal_compliance.company.configure_at_credentials(frm);
																}
															}
														});
													}
												},
												error: function(xhr, status, error) {
													progress_dialog.hide();
													console.error('❌ Erro HTTP:', {xhr, status, error});

													let error_details = '';
													if (xhr.responseJSON && xhr.responseJSON.exception) {
														error_details = `<br><br><strong>Detalhes técnicos:</strong><br><code>${xhr.responseJSON.exception}</code>`;
													}

													frappe.msgprint({
														title: __('❌ Erro de Comunicação'),
														message: __('<div class="alert alert-danger">' +
																   '<strong>Erro na comunicação com o servidor:</strong><br>' +
																   '{0}{1}' +
																   '</div>', [error || 'Erro desconhecido', error_details]),
														indicator: 'red'
													});
												}
											});
										}
									);
								} else {
									// ✅ NENHUMA SÉRIE PARA COMUNICAR
									frappe.msgprint({
										title: __('✅ Nenhuma Série para Comunicar'),
										message: __('<div class="alert alert-success">' +
												   '<strong>Todas as séries já estão comunicadas!</strong><br><br>' +
												   'Não há séries não comunicadas para a empresa <strong>{0}</strong>.<br><br>' +
												   '<em>Pode ver o estado das séries clicando em "👁️ Ver Séries".</em>' +
												   '</div>', [frm.doc.name]),
										indicator: 'blue',
										primary_action: {
											label: __('Ver Séries'),
											action: function() {
												frappe.set_route('List', 'Portugal Series Configuration', {
													'company': frm.doc.name
												});
											}
										}
									});
								}
							},
							error: function(xhr, status, error) {
								console.error('❌ Erro ao buscar séries:', {xhr, status, error});
								frappe.msgprint({
									title: __('❌ Erro ao Buscar Séries'),
									message: __('<div class="alert alert-danger">' +
											   '<strong>Erro ao buscar séries da empresa:</strong><br>' +
											   '{0}<br><br>' +
											   '<em>Verifique se as séries foram criadas corretamente.</em>' +
											   '</div>', [error || 'Erro desconhecido']),
									indicator: 'red',
									primary_action: {
										label: __('Criar Séries'),
										action: function() {
											portugal_compliance.company.create_portugal_series_dialog(frm);
										}
									}
								});
							}
						});
					}
				);
			}).catch((error) => {
				// ✅ ERRO NO RELOAD DO DOCUMENTO
				console.error('❌ Erro ao recarregar documento:', error);
				frappe.msgprint({
					title: __('❌ Erro'),
					message: __('Erro ao recarregar dados da empresa. Tente novamente.'),
					indicator: 'red'
				});
			});
		},


        sync_all_naming_series: function(frm) {
            frappe.confirm(
                __('Sincronizar naming series de todas as séries portuguesas?'),
                function() {
                    frappe.call({
                        method: 'portugal_compliance.utils.series_adapter.sync_naming_series_for_company',
                        args: {
                            'company_abbr': frm.doc.abbr,
                            'force_update': true
                        },
                        freeze: true,
                        freeze_message: __('Sincronizando naming series...'),
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.msgprint({
                                    title: __('✅ Sincronização Concluída'),
                                    message: __('Naming series sincronizadas para {0} DocTypes', [r.message.successful_updates]),
                                    indicator: 'green'
                                });
                                frm.refresh();
                            } else {
                                frappe.msgprint({
                                    title: __('❌ Erro'),
                                    message: r.message ? r.message.error : __('Erro na sincronização'),
                                    indicator: 'red'
                                });
                            }
                        }
                    });
                }
            );
        },

        before_save_validations: function(frm) {
            // Validate NIF if provided
            if (frm.doc.tax_id && frm.doc.country === 'Portugal') {
                if (!portugal_compliance.validateNIF(frm.doc.tax_id)) {
                    frappe.msgprint({
                        title: __('NIF Inválido'),
                        message: __('O NIF fornecido não é válido segundo o algoritmo português.'),
                        indicator: 'orange'
                    });
                }
            }

            // Validate compliance only for Portugal
            if (frm.doc.portugal_compliance_enabled && frm.doc.country !== 'Portugal') {
                frappe.msgprint({
                    title: __('Erro de Configuração'),
                    message: __('Portugal Compliance só pode ser ativado para empresas portuguesas.'),
                    indicator: 'red'
                });
                frappe.validated = false;
            }
        },

        validate_nif_realtime: function(frm) {
            if (frm.doc.tax_id && frm.doc.country === 'Portugal') {
                const is_valid = portugal_compliance.validateNIF(frm.doc.tax_id);
                const nif_field = frm.get_field('tax_id');

                if (is_valid) {
                    nif_field.$wrapper.removeClass('has-error').addClass('has-success');
                    frm.set_df_property('tax_id', 'description', '✅ NIF válido');
                } else {
                    nif_field.$wrapper.removeClass('has-success').addClass('has-error');
                    frm.set_df_property('tax_id', 'description', '❌ NIF inválido');
                }

                frm.refresh_field('tax_id');
            }
        },

        validate_certificate_realtime: function(frm) {
            if (frm.doc.at_certificate_number) {
                const cert_field = frm.get_field('at_certificate_number');
                const is_valid = /^[0-9]{1,10}$/.test(frm.doc.at_certificate_number);

                if (is_valid) {
                    cert_field.$wrapper.removeClass('has-error').addClass('has-success');
                    frm.set_df_property('at_certificate_number', 'description', '✅ Formato válido');
                } else {
                    cert_field.$wrapper.removeClass('has-success').addClass('has-error');
                    frm.set_df_property('at_certificate_number', 'description', '❌ Deve conter apenas números');
                }

                frm.refresh_field('at_certificate_number');
            }
        },

        show_portugal_fields: function(frm) {
            if (frm.fields_dict.portugal_compliance_enabled) {
                frm.set_df_property('portugal_compliance_enabled', 'hidden', 0);
            }

            if (frm.fields_dict.tax_id) {
                frm.set_df_property('tax_id', 'reqd', 1);
                frm.set_df_property('tax_id', 'label', 'NIF');
                frm.set_df_property('tax_id', 'description', 'Número de Identificação Fiscal (obrigatório em Portugal)');
            }

            frm.refresh_fields();
        },

        hide_portugal_fields: function(frm) {
            if (frm.fields_dict.portugal_compliance_enabled) {
                frm.set_df_property('portugal_compliance_enabled', 'hidden', 1);
            }

            if (frm.fields_dict.at_certificate_number) {
                frm.set_df_property('at_certificate_number', 'hidden', 1);
            }

            if (frm.fields_dict.tax_id) {
                frm.set_df_property('tax_id', 'reqd', 0);
                frm.set_df_property('tax_id', 'label', 'Tax ID');
                frm.set_df_property('tax_id', 'description', '');
            }

            frm.refresh_fields();
        },

        show_compliance_fields: function(frm) {
            if (frm.fields_dict.at_certificate_number) {
                frm.set_df_property('at_certificate_number', 'hidden', 0);
                frm.set_df_property('at_certificate_number', 'description',
                    'Número do certificado de software emitido pela AT (opcional)');
            }

            frm.refresh_fields();
        },

        hide_compliance_fields: function(frm) {
            if (frm.fields_dict.at_certificate_number) {
                frm.set_df_property('at_certificate_number', 'hidden', 1);
            }

            frm.refresh_fields();
        },

        update_visual_feedback: function(frm) {
            // Implementation for visual feedback
            const status = this.get_compliance_status(frm);
            // Update visual indicators based on status
        },

        get_compliance_status: function(frm) {
            const status = {
                level: 'none',
                title: 'Não Configurado',
                message: 'Configure a empresa para Portugal',
                progress: 0
            };

            if (frm.doc.country !== 'Portugal') {
                return status;
            }

            status.progress = 25;

            if (!frm.doc.tax_id) {
                status.level = 'warning';
                status.title = 'NIF Em Falta';
                status.message = 'NIF é obrigatório para empresas portuguesas';
                return status;
            }

            if (!portugal_compliance.validateNIF(frm.doc.tax_id)) {
                status.level = 'warning';
                status.title = 'NIF Inválido';
                status.message = 'NIF fornecido não é válido';
                return status;
            }

            status.progress = 50;

            if (!frm.doc.portugal_compliance_enabled) {
                status.level = 'info';
                status.title = 'Compliance Inativo';
                status.message = 'Ative Portugal Compliance para usar séries portuguesas';
                return status;
            }

            status.progress = 75;

            if (!frm.doc.at_certificate_number) {
                status.level = 'warning';
                status.title = 'Certificado AT Recomendado';
                status.message = 'Configure certificado AT para compliance completo';
                status.progress = 90;
                return status;
            }

            status.level = 'success';
            status.title = 'Compliance Completo';
            status.message = 'Empresa configurada para compliance português total';
            status.progress = 100;

            return status;
        },

        check_series_count: function(frm) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    'doctype': 'Portugal Series Configuration',
                    'filters': {'company': frm.doc.name, 'is_active': 1},
                    'fields': ['name', 'is_communicated']
                },
                callback: function(r) {
                    if (r.message) {
                        const total_series = r.message.length;
                        const communicated_series = r.message.filter(s => s.is_communicated).length;

                        frm.dashboard.add_indicator(
                            __('📊 Séries: {0} total, {1} comunicadas', [total_series, communicated_series]),
                            total_series > 0 ? 'blue' : 'orange'
                        );
                    }
                }
            });
        },

        suggest_series_creation: function(frm) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    'doctype': 'Portugal Series Configuration',
                    'filters': {'company': frm.doc.name},
                    'limit': 1
                },
                callback: function(r) {
                    if (!r.message || r.message.length === 0) {
                        frappe.msgprint({
                            title: __('Criar Séries Portuguesas'),
                            message: __('Portugal Compliance foi ativado. Deseja criar séries portuguesas automaticamente?'),
                            indicator: 'blue',
                            primary_action: {
                                label: __('Criar Séries'),
                                action: function() {
                                    portugal_compliance.company.create_initial_series(frm);
                                }
                            }
                        });
                    }
                }
            });
        },

        run_compliance_diagnostics: function(frm) {
            const diagnostics = {
                company: frm.doc.name,
                country: frm.doc.country,
                tax_id: frm.doc.tax_id,
                nif_valid: portugal_compliance.validateNIF(frm.doc.tax_id),
                compliance_enabled: frm.doc.portugal_compliance_enabled,
                certificate: frm.doc.at_certificate_number
            };

            const dialog = new frappe.ui.Dialog({
                title: __('Diagnóstico de Compliance'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: this.build_diagnostics_html(diagnostics)
                    }
                ],
                primary_action_label: __('Fechar'),
                primary_action: function() {
                    dialog.hide();
                }
            });
            dialog.show();
        },

        build_diagnostics_html: function(diagnostics) {
            let html = '<div style="padding: 15px;">';
            html += '<h4>🔍 Diagnóstico de Compliance</h4>';
            html += '<table class="table table-bordered">';
            html += '<tr><th>Item</th><th>Valor</th><th>Status</th></tr>';

            const checks = [
                ['Empresa', diagnostics.company, diagnostics.company ? '✅' : '❌'],
                ['País', diagnostics.country, diagnostics.country === 'Portugal' ? '✅' : '❌'],
                ['NIF', diagnostics.tax_id || 'Não definido', diagnostics.tax_id ? (diagnostics.nif_valid ? '✅' : '❌') : '❌'],
                ['Compliance Ativo', diagnostics.compliance_enabled ? 'Sim' : 'Não', diagnostics.compliance_enabled ? '✅' : '❌'],
                ['Certificado AT', diagnostics.certificate || 'Não definido', diagnostics.certificate ? '✅' : '⚪']
            ];

            checks.forEach(check => {
                html += `<tr><td>${check[0]}</td><td>${check[1]}</td><td>${check[2]}</td></tr>`;
            });

            html += '</table>';
            html += '</div>';

            return html;
        },

        show_series_creation_progress: function() {
            const dialog = new frappe.ui.Dialog({
                title: __('Criando Séries'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div style="text-align: center; padding: 20px;">
                                <div class="progress">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                                         style="width: 100%"></div>
                                </div>
                                <p style="margin-top: 15px;">
                                    <i class="fa fa-cog fa-spin"></i>
                                    Criando séries portuguesas...
                                </p>
                            </div>
                        `
                    }
                ]
            });
            dialog.show();
            return dialog;
        },

        show_communication_progress: function() {
            const dialog = new frappe.ui.Dialog({
                title: __('Comunicando Séries'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div style="text-align: center; padding: 20px;">
                                <div class="progress">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                                         style="width: 100%"></div>
                                </div>
                                <p style="margin-top: 15px;">
                                    <i class="fa fa-wifi fa-spin"></i>
                                    Comunicando séries à AT...
                                </p>
                            </div>
                        `
                    }
                ]
            });
            dialog.show();
            return dialog;
        },

		show_series_creation_results: function(frm, results) {
			let html = `
				<div style="padding: 20px;">
					<div class="alert alert-success" style="margin-bottom: 20px;">
						<h4><i class="fa fa-check-circle"></i> ✅ Séries Criadas com Sucesso!</h4>
					</div>

					<div class="row">
						<div class="col-md-4">
							<div class="alert alert-success">
								<strong>✅ Criadas: ${results.created || 0}</strong>
							</div>
						</div>
						<div class="col-md-4">
							<div class="alert alert-info">
								<strong>⚠️ Já Existiam: ${results.skipped || 0}</strong>
							</div>
						</div>
						<div class="col-md-4">
							<div class="alert alert-danger">
								<strong>❌ Erros: ${results.errors || 0}</strong>
							</div>
						</div>
					</div>
			`;

			if (results.created_series && results.created_series.length > 0) {
				html += '<div class="alert alert-info"><h5>📋 Séries Criadas:</h5><ul>';
				results.created_series.forEach(series => {
					html += `<li><strong>${series}</strong> - Ativa e pronta para uso</li>`;
				});
				html += '</ul></div>';
			}

			html += `
				<div class="alert alert-warning">
					<h5><i class="fa fa-exclamation-triangle"></i> Próximos Passos:</h5>
					<ol>
						<li><strong>Salve a empresa</strong> para ativar os botões de comunicação</li>
						<li><strong>Configure credenciais AT</strong> nas configurações</li>
						<li><strong>Comunique as séries</strong> à Autoridade Tributária</li>
						<li><strong>Teste a criação</strong> de documentos</li>
					</ol>
				</div>
				<p><em>As naming series dos DocTypes foram atualizadas automaticamente.</em></p>
			</div>`;

			// ✅ MODAL PERSISTENTE - NÃO DESAPARECE AUTOMATICAMENTE
			const dialog = new frappe.ui.Dialog({
				title: __('🇵🇹 Séries Portuguesas Criadas'),
				fields: [
					{
						fieldtype: 'HTML',
						options: html
					}
				],
				primary_action_label: __('Entendi - Continuar'),
				primary_action: function() {
					dialog.hide();
					// Salvar automaticamente após confirmação
					frm.save();
				},
				secondary_action_label: __('Ver Séries Criadas'),
				secondary_action: function() {
					frappe.set_route('List', 'Portugal Series Configuration', {
						'company': frm.doc.name
					});
				}
			});

			dialog.show();

			// ✅ GARANTIR QUE MODAL NÃO DESAPARECE
			dialog.$wrapper.find('.modal').off('click.dismiss.bs.modal');
		},


        show_communication_results: function(results) {
            let html = `
                <div style="padding: 15px;">
                    <h4>📊 Resultados da Comunicação</h4>
                    <div class="alert alert-success">
                        <strong>✅ Sucesso: ${results.successful || 0}</strong>
                    </div>
                    <div class="alert alert-danger">
                        <strong>❌ Falhas: ${results.failed || 0}</strong>
                    </div>
            `;

            if (results.results && results.results.length > 0) {
                html += '<h5>📋 Detalhes:</h5><table class="table table-striped"><thead><tr><th>Série</th><th>Status</th><th>ATCUD/Erro</th></tr></thead><tbody>';

                results.results.forEach(result => {
                    const status_icon = result.success ? '✅' : '❌';
                    const detail = result.success ? result.atcud : result.message;

                    html += `<tr><td><strong>${result.series}</strong></td><td>${status_icon}</td><td><code>${detail}</code></td></tr>`;
                });

                html += '</tbody></table>';
            }

            html += '</div>';

            frappe.msgprint({
                title: __('Comunicação Concluída'),
                message: html,
                indicator: 'blue'
            });
        },
		configure_at_credentials: function(frm) {
			// ✅ PRÉ-CARREGAR VALORES EXISTENTES
			const current_values = {
				username: frm.doc.at_username || '',
				password: frm.doc.at_password || '',
				environment: frm.doc.at_environment || 'test',
				certificate_number: frm.doc.at_certificate_number || ''
			};

			const dialog = new frappe.ui.Dialog({
				title: __('⚙️ Configurar Credenciais AT'),
				fields: [
					{
						fieldtype: 'Section Break',
						label: __('Credenciais da Autoridade Tributária')
					},
					{
						fieldtype: 'Data',
						fieldname: 'username',
						label: __('Utilizador AT'),
						reqd: 1,
						default: current_values.username,
						description: __('NIF/Utilizador para acesso aos webservices da AT')
					},
					{
						fieldtype: 'Password',
						fieldname: 'password',
						label: __('Palavra-passe AT'),
						reqd: 1,
						default: current_values.password,
						description: __('Palavra-passe para acesso aos webservices da AT')
					},
					{
						fieldtype: 'Select',
						fieldname: 'environment',
						label: __('Ambiente'),
						options: 'test\nproduction',
						default: current_values.environment,
						reqd: 1,
						description: __('Ambiente de teste ou produção')
					},
					{
						fieldtype: 'Section Break',
						label: __('Certificado AT (Opcional)')
					},
					{
						fieldtype: 'Data',
						fieldname: 'certificate_number',
						label: __('Número do Certificado'),
						default: current_values.certificate_number,
						description: __('Número do certificado de software emitido pela AT')
					},
					{
						fieldtype: 'Section Break'
					},
					{
						fieldtype: 'HTML',
						options: `
							<div class="alert alert-info">
								<h5><i class="fa fa-info-circle"></i> Informação Importante:</h5>
								<ul>
									<li><strong>Ambiente Teste:</strong> Use para testes e desenvolvimento</li>
									<li><strong>Ambiente Produção:</strong> Use apenas para documentos reais</li>
									<li><strong>Credenciais:</strong> Obtidas no Portal das Finanças</li>
									<li><strong>Certificado:</strong> Opcional, mas recomendado para produção</li>
								</ul>
							</div>
						`
					}
				],
				primary_action_label: __('💾 Guardar Credenciais'),
				primary_action: function(values) {
					// ✅ VALIDAR CAMPOS OBRIGATÓRIOS
					if (!values.username || !values.password) {
						frappe.msgprint({
							title: __('Campos Obrigatórios'),
							message: __('Utilizador e palavra-passe são obrigatórios'),
							indicator: 'red'
						});
						return;
					}

					// ✅ GUARDAR CREDENCIAIS DIRETAMENTE NO DOCUMENTO
					frm.set_value('at_username', values.username);
					frm.set_value('at_password', values.password);
					frm.set_value('at_environment', values.environment);
					frm.set_value('at_certificate_number', values.certificate_number || '');

					// ✅ SALVAR O DOCUMENTO
					frm.save().then(() => {
						dialog.hide();
						frappe.show_alert({
							message: __('✅ Credenciais AT guardadas com sucesso'),
							indicator: 'green'
						});

						// ✅ ATUALIZAR BOTÕES
						portugal_compliance.company.setup_buttons(frm);

						console.log('✅ Credenciais guardadas:', {
							username: values.username,
							environment: values.environment,
							has_password: !!values.password
						});
					}).catch((error) => {
						frappe.msgprint({
							title: __('Erro ao Guardar'),
							message: __('Erro ao guardar credenciais: {0}', [error.message || error]),
							indicator: 'red'
						});
					});
				},
				secondary_action_label: __('🧪 Testar Conexão'),
				secondary_action: function(values) {
					if (!values.environment) {
						frappe.msgprint({
							title: __('Ambiente Obrigatório'),
							message: __('Selecione o ambiente para testar'),
							indicator: 'orange'
						});
						return;
					}

					frappe.call({
						method: 'portugal_compliance.utils.at_webservice.test_connection',
						args: {
							environment: values.environment
						},
						callback: function(r) {
							if (r.message && r.message.connected) {
								frappe.show_alert({
									message: __('✅ Conexão AT bem-sucedida'),
									indicator: 'green'
								});
							} else {
								frappe.show_alert({
									message: __('❌ Falha na conexão AT: {0}', [r.message?.error || 'Erro desconhecido']),
									indicator: 'red'
								});
							}
						},
						error: function() {
							frappe.show_alert({
								message: __('❌ Erro na comunicação com o servidor'),
								indicator: 'red'
							});
						}
					});
				}
			});

			dialog.show();
	},


    },

    // ========== UTILITÁRIOS GERAIS ==========

    utils: {
        isPortugueseCompany: function(company, callback) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Company',
                    filters: { name: company },
                    fieldname: ['country', 'portugal_compliance_enabled']
                },
                callback: function(r) {
                    const is_portuguese = r.message &&
                        r.message.country === 'Portugal' &&
                        r.message.portugal_compliance_enabled;

                    if (callback) callback(is_portuguese);
                }
            });
        },

        getFiscalYear: function(date, company, callback) {
            frappe.call({
                method: 'erpnext.accounts.utils.get_fiscal_year',
                args: {
                    date: date,
                    company: company
                },
                callback: function(r) {
                    if (callback) callback(r.message);
                }
            });
        }
    }
};

// ========== CSS STYLES ==========

$('<style>')
    .prop('type', 'text/css')
    .html(`
        .has-success .control-input input,
        .has-success .control-input select {
            border-color: #28a745 !important;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
        }

        .has-error .control-input input,
        .has-error .control-input select {
            border-color: #dc3545 !important;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
        }

        .compliance-status-card {
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .progress {
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }

        .card {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
        }

        .portugal-compliance-indicator {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
    `)
    .appendTo('head');

// ========== INICIALIZAÇÃO ==========

// Initialize when document is ready
$(document).ready(function() {
    portugal_compliance.init();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = portugal_compliance;
}

console.log('🇵🇹 Portugal Compliance Module v2.0.0 carregado com sucesso - Versão Unificada!');

