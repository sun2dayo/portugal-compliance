// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Portugal Compliance Sales Invoice JavaScript - VERSÃO CERTIFICADA OTIMIZADA
 * Nova abordagem: usa apenas naming_series nativo, auto-seleção inteligente, validação otimizada
 * Compliance inviolável com séries portuguesas comunicadas - SEM CONFLITOS
 */

frappe.ui.form.on('Sales Invoice', {
    // ========== EVENTOS PRINCIPAIS OTIMIZADOS ==========

    onload: function(frm) {
        portugal_compliance_sales_invoice.setup_form(frm);
    },

    refresh: function(frm) {
        // ✅ ORDEM OTIMIZADA: Setup primeiro, depois verificações
        portugal_compliance_sales_invoice.setup_buttons(frm);
        portugal_compliance_sales_invoice.setup_fields(frm);

        // ✅ VERIFICAÇÃO INTELIGENTE: Só se necessário
        if (portugal_compliance_sales_invoice.should_check_compliance(frm)) {
            portugal_compliance_sales_invoice.check_portugal_compliance(frm);
        }

        // ✅ AUTO-SELEÇÃO INTELIGENTE: Só uma vez e com delay
        if (portugal_compliance_sales_invoice.should_auto_select_series(frm)) {
            portugal_compliance_sales_invoice.schedule_auto_select_naming_series(frm);
        }

        // ✅ FEEDBACK VISUAL: Sempre no final
        portugal_compliance_sales_invoice.update_compliance_visual_feedback(frm);
    },

    company: function(frm) {
        portugal_compliance_sales_invoice.on_company_change(frm);
    },

    before_save: function(frm) {
        portugal_compliance_sales_invoice.before_save_validations(frm);
    },

    validate: function(frm) {
        portugal_compliance_sales_invoice.validate_portugal_fields(frm);
    },

    // ========== EVENTOS DE CAMPOS ESPECÍFICOS OTIMIZADOS ==========

    customer: function(frm) {
        portugal_compliance_sales_invoice.on_customer_change(frm);
    },

    naming_series: function(frm) {
        portugal_compliance_sales_invoice.on_naming_series_change(frm);
    },

    // ✅ NOVO: Evento para setup inicial otimizado
    setup: function(frm) {
        if (portugal_compliance_sales_invoice.is_portuguese_company(frm)) {
            portugal_compliance_sales_invoice.setup_naming_series_filter(frm);
        }
    }
});

// ========== CLASSE PRINCIPAL PORTUGAL COMPLIANCE OTIMIZADA ==========

var portugal_compliance_sales_invoice = {

    // ✅ CONTROLE DE ESTADO PARA EVITAR CONFLITOS
    _state: {
        auto_select_scheduled: false,
        compliance_checked: false,
        series_loading: false
    },

    // ========== CONFIGURAÇÃO INICIAL OTIMIZADA ==========

    setup_form: function(frm) {
        console.log('🇵🇹 Portugal Compliance: Configurando Sales Invoice - Versão Otimizada');

        // ✅ RESET DE ESTADO
        this.reset_state();

        // Configurar filtros personalizados
        this.setup_custom_filters(frm);

        // Configurar validações em tempo real (otimizadas)
        this.setup_realtime_validations(frm);

        // ✅ CONFIGURAR FEEDBACK VISUAL
        this.setup_visual_feedback_system(frm);
    },

    // ✅ NOVA FUNÇÃO: Reset de estado
    reset_state: function() {
        this._state = {
            auto_select_scheduled: false,
            compliance_checked: false,
            series_loading: false
        };
    },

    // ✅ NOVA FUNÇÃO: Verificar se deve auto-selecionar série
    should_auto_select_series: function(frm) {
        return (
            frm.doc.company &&
            !frm.doc.naming_series &&
            this.is_portuguese_company(frm) &&
            !this._state.auto_select_scheduled &&
            !this._state.series_loading
        );
    },

    // ✅ NOVA FUNÇÃO: Verificar se deve verificar compliance
    should_check_compliance: function(frm) {
        return (
            this.is_portuguese_company(frm) &&
            !this._state.compliance_checked
        );
    },

    // ✅ NOVA FUNÇÃO: Agendar auto-seleção (evita múltiplas chamadas)
    schedule_auto_select_naming_series: function(frm) {
        if (this._state.auto_select_scheduled) return;

        this._state.auto_select_scheduled = true;

        setTimeout(() => {
            if (!frm.doc.naming_series && this.is_portuguese_company(frm)) {
                this.auto_select_naming_series(frm);
            }
            this._state.auto_select_scheduled = false;
        }, 1000);
    },

    setup_buttons: function(frm) {
        // ✅ LIMPAR BOTÕES PRIMEIRO
        frm.clear_custom_buttons();

        if (!this.is_portuguese_company(frm)) return;

        // ✅ BOTÃO: GERAR ATCUD MANUAL
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Gerar ATCUD'), function() {
                portugal_compliance_sales_invoice.generate_atcud_manual(frm);
            }, __('Portugal Compliance'));
        }

        // ✅ BOTÃO: VALIDAR COMPLIANCE
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Validar Compliance'), function() {
                portugal_compliance_sales_invoice.validate_compliance_full(frm);
            }, __('Portugal Compliance'));
        }

        // ✅ BOTÃO: PREVIEW ATCUD
        if (frm.doc.naming_series && frm.doc.docstatus === 0 && this.is_portuguese_naming_series(frm)) {
            frm.add_custom_button(__('Preview ATCUD'), function() {
                portugal_compliance_sales_invoice.preview_atcud(frm);
            }, __('Portugal Compliance'));
        }

        // ✅ BOTÃO: CONFIGURAR SÉRIE
        if (frappe.user.has_role(['System Manager', 'Accounts Manager'])) {
            frm.add_custom_button(__('Configurar Séries'), function() {
                frappe.set_route('List', 'Portugal Series Configuration');
            }, __('Portugal Compliance'));
        }

        // ✅ BOTÃO: COMUNICAR SÉRIE
        if (frm.doc.naming_series && frm.doc.docstatus === 0 && this.is_portuguese_naming_series(frm)) {
            this.check_series_communication_status(frm);
        }

        // ✅ BOTÃO: DIAGNÓSTICO
        if (frappe.user.has_role(['System Manager'])) {
            frm.add_custom_button(__('Diagnóstico Compliance'), function() {
                portugal_compliance_sales_invoice.run_compliance_diagnostics(frm);
            }, __('Portugal Compliance'));
        }
    },

    setup_fields: function(frm) {
        if (!this.is_portuguese_company(frm)) return;

        // ✅ CONFIGURAR CAMPO ATCUD (READ-ONLY)
        if (frm.fields_dict.atcud_code) {
            frm.set_df_property('atcud_code', 'read_only', 1);
            frm.set_df_property('atcud_code', 'bold', 1);
            frm.set_df_property('atcud_code', 'description',
                '🇵🇹 ATCUD gerado automaticamente pela série portuguesa comunicada');
        }

        // ✅ CONFIGURAR CAMPO NAMING_SERIES
        if (frm.fields_dict.naming_series) {
            frm.set_df_property('naming_series', 'reqd', 1);
            frm.set_df_property('naming_series', 'bold', 1);
            frm.set_df_property('naming_series', 'description',
                '📋 Série portuguesa obrigatória - selecionada automaticamente');
        }

        // ✅ CONFIGURAR VALIDAÇÃO NIF
        if (frm.fields_dict.customer) {
            this.setup_customer_nif_validation(frm);
        }
    },

    setup_custom_filters: function(frm) {
        if (!this.is_portuguese_company(frm)) return;

        // ✅ FILTRO OTIMIZADO PARA NAMING SERIES
        frm.set_query('naming_series', function() {
            return {
                query: 'portugal_compliance.queries.series_queries.get_naming_series_for_doctype',
                filters: {
                    'doctype': 'Sales Invoice',
                    'company': frm.doc.company,
                    'communicated_only': 1
                }
            };
        });
    },

    setup_realtime_validations: function(frm) {
        // ✅ VALIDAÇÃO NIF OTIMIZADA (DEBOUNCED)
        if (frm.fields_dict.tax_id) {
            let nif_timeout;
            frm.fields_dict.tax_id.$input.on('input', function() {
                clearTimeout(nif_timeout);
                nif_timeout = setTimeout(() => {
                    portugal_compliance_sales_invoice.validate_nif_realtime(frm);
                }, 500);
            });
        }

        // ✅ VALIDAÇÃO DE VALORES OTIMIZADA
        ['grand_total', 'net_total'].forEach(function(field) {
            if (frm.fields_dict[field]) {
                let value_timeout;
                frm.fields_dict[field].$input.on('change', function() {
                    clearTimeout(value_timeout);
                    value_timeout = setTimeout(() => {
                        portugal_compliance_sales_invoice.update_compliance_status(frm);
                    }, 300);
                });
            }
        });
    },

    // ✅ CONFIGURAR SISTEMA DE FEEDBACK VISUAL OTIMIZADO
    setup_visual_feedback_system: function(frm) {
        if (frm.compliance_feedback_container) return; // Já existe

        frm.compliance_feedback_container = $(`
            <div class="compliance-feedback-container" style="margin: 15px 0;">
                <div class="compliance-status-card"></div>
            </div>
        `);

        frm.layout.wrapper.find('.form-layout').prepend(frm.compliance_feedback_container);
    },

    // ========== EVENTOS DE MUDANÇA OTIMIZADOS ==========

    on_company_change: function(frm) {
        console.log('🏢 Empresa alterada:', frm.doc.company);

        // ✅ RESET COMPLETO DE ESTADO
        this.reset_state();

        // Limpar campos relacionados
        if (frm.doc.naming_series) {
            frm.set_value('naming_series', '');
            frm.set_value('atcud_code', '');
        }

        // Limpar cache de empresa
        delete frm._is_portuguese_company;

        // ✅ CONFIGURAÇÃO CONDICIONAL
        if (this.is_portuguese_company(frm)) {
            this.setup_portugal_compliance_for_company(frm);
        } else {
            this.hide_portugal_fields(frm);
        }

        // Atualizar interface
        frm.refresh_field('naming_series');
        this.update_compliance_visual_feedback(frm);
    },

    on_naming_series_change: function(frm) {
        console.log('📋 Naming series alterada:', frm.doc.naming_series);

        if (this._state.series_loading) return; // Evitar loops

        if (frm.doc.naming_series && this.is_portuguese_naming_series(frm)) {
            this._state.series_loading = true;
            this.get_series_info_from_naming_series(frm);
        } else {
            frm.set_value('atcud_code', '');
            this.update_compliance_status(frm);
        }

        this.update_compliance_visual_feedback(frm);
    },

    // ✅ FUNÇÃO OTIMIZADA: Obter informações da série
    get_series_info_from_naming_series: function(frm) {
        if (!frm.doc.naming_series) {
            this._state.series_loading = false;
            return;
        }

        const prefix = frm.doc.naming_series.replace('.####', '');

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company,
                    'document_type': 'Sales Invoice'
                },
                'fieldname': ['name', 'validation_code', 'is_communicated', 'at_environment']
            },
            callback: function(r) {
                portugal_compliance_sales_invoice._state.series_loading = false;

                if (r.message) {
                    portugal_compliance_sales_invoice.on_series_loaded(frm, r.message);
                }
            },
            error: function() {
                portugal_compliance_sales_invoice._state.series_loading = false;
            }
        });
    },

    on_series_loaded: function(frm, series_data) {
        console.log('✅ Série carregada:', series_data);

        // ✅ GERAR ATCUD APENAS SE NECESSÁRIO
        if (series_data.validation_code && !frm.doc.atcud_code && frm.doc.name && frm.doc.name !== 'new') {
            this.generate_atcud_for_series(frm, series_data);
        }

        // Mostrar informações da série
        this.show_series_info(frm, series_data);

        // Atualizar status
        this.update_compliance_status(frm);
        this.update_compliance_visual_feedback(frm);
    },

    on_customer_change: function(frm) {
        if (!frm.doc.customer || !this.is_portuguese_company(frm)) return;

        // ✅ OBTER NIF DO CLIENTE (OTIMIZADO)
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Customer',
                'fieldname': 'tax_id',
                'filters': {'name': frm.doc.customer}
            },
            callback: function(r) {
                if (r.message && r.message.tax_id) {
                    frm.set_value('tax_id', r.message.tax_id);
                    portugal_compliance_sales_invoice.validate_nif_realtime(frm);
                }
            }
        });
    },

    // ========== GERAÇÃO DE ATCUD OTIMIZADA ==========

    generate_atcud_for_series: function(frm, series_data) {
        if (!series_data || !series_data.validation_code) {
            console.log('⚠️ Série não tem código de validação AT');
            return;
        }

        if (!frm.doc.name || frm.doc.name === 'new') {
            console.log('⚠️ Documento ainda não tem nome - ATCUD será gerado no save');
            return;
        }

        frappe.call({
            method: 'portugal_compliance.utils.document_hooks.generate_manual_atcud',
            args: {
                'doctype': 'Sales Invoice',
                'docname': frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frm.set_value('atcud_code', r.message.atcud_code);
                    portugal_compliance_sales_invoice.show_atcud_success(frm, r.message.atcud_code);
                } else {
                    console.log('❌ Erro ao gerar ATCUD:', r.message);
                }
            }
        });
    },

    generate_atcud_manual: function(frm) {
        if (!frm.doc.naming_series || !this.is_portuguese_naming_series(frm)) {
            frappe.msgprint({
                title: __('Erro'),
                message: __('Selecione uma naming series portuguesa comunicada primeiro.'),
                indicator: 'red'
            });
            return;
        }

        const prefix = frm.doc.naming_series.replace('.####', '');

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company
                },
                'fieldname': ['is_communicated', 'validation_code']
            },
            callback: function(r) {
                if (!r.message || !r.message.is_communicated) {
                    frappe.msgprint({
                        title: __('Série Não Comunicada'),
                        message: __('Esta série não foi comunicada à AT. Comunique primeiro.'),
                        indicator: 'orange'
                    });
                    return;
                }

                if (!r.message.validation_code) {
                    frappe.msgprint({
                        title: __('Código AT Em Falta'),
                        message: __('Esta série não tem código de validação AT.'),
                        indicator: 'red'
                    });
                    return;
                }

                // Gerar ATCUD
                frappe.call({
                    method: 'portugal_compliance.utils.document_hooks.generate_manual_atcud',
                    args: {
                        'doctype': 'Sales Invoice',
                        'docname': frm.doc.name || 'new'
                    },
                    callback: function(result) {
                        if (result.message && result.message.success) {
                            frm.set_value('atcud_code', result.message.atcud_code);
                            portugal_compliance_sales_invoice.show_atcud_success(frm, result.message.atcud_code);
                        } else {
                            frappe.msgprint({
                                title: __('Erro'),
                                message: result.message ? result.message.error : __('Erro ao gerar ATCUD'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        });
    },

    preview_atcud: function(frm) {
        if (!frm.doc.naming_series || !this.is_portuguese_naming_series(frm)) {
            frappe.msgprint({
                title: __('Erro'),
                message: __('Selecione uma naming series portuguesa primeiro.'),
                indicator: 'red'
            });
            return;
        }

        const prefix = frm.doc.naming_series.replace('.####', '');

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company
                },
                'fieldname': ['name', 'validation_code', 'is_communicated']
            },
            callback: function(r) {
                if (r.message && r.message.validation_code) {
                    portugal_compliance_sales_invoice.show_atcud_preview_dialog(frm, {
                        atcud_code: `${r.message.validation_code}-000001`,
                        validation_code: r.message.validation_code,
                        sequence_number: 1,
                        is_communicated: r.message.is_communicated
                    });
                } else {
                    frappe.msgprint({
                        title: __('Erro'),
                        message: __('Série não tem código de validação AT. Comunique a série primeiro.'),
                        indicator: 'orange'
                    });
                }
            }
        });
    },

    show_atcud_preview_dialog: function(frm, atcud_data) {
        const status_color = atcud_data.is_communicated ? 'green' : 'orange';
        const status_text = atcud_data.is_communicated ? 'Comunicada' : 'Não Comunicada';

        const dialog = new frappe.ui.Dialog({
            title: __('Preview ATCUD'),
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <div style="text-align: center; padding: 20px;">
                            <h4>🇵🇹 Código ATCUD Preview</h4>
                            <div style="font-size: 18px; font-weight: bold; color: #2e7d32; margin: 20px 0;">
                                ${atcud_data.atcud_code}
                            </div>
                            <p><strong>Formato:</strong> CODIGO-SEQUENCIA</p>
                            <p><strong>Código de Validação:</strong> ${atcud_data.validation_code}</p>
                            <p><strong>Sequência:</strong> ${atcud_data.sequence_number}</p>
                            <p><strong>Naming Series:</strong> ${frm.doc.naming_series}</p>
                            <p><strong>Status:</strong> <span style="color: ${status_color};">${status_text}</span></p>
                            <p><em>Este é apenas um preview. O ATCUD real será gerado ao salvar o documento.</em></p>
                        </div>
                    `
                }
            ],
            primary_action_label: __('Fechar'),
            primary_action: function() {
                dialog.hide();
            }
        });
        dialog.show();
    },

    // ========== VALIDAÇÕES OTIMIZADAS ==========

    before_save_validations: function(frm) {
        if (!this.is_portuguese_company(frm)) return;

        // ✅ VALIDAÇÃO NAMING SERIES
        if (!frm.doc.naming_series) {
            frappe.msgprint({
                title: __('Erro de Compliance'),
                message: __('Naming series portuguesa é obrigatória para empresas portuguesas.'),
                indicator: 'red'
            });
            frappe.validated = false;
            return;
        }

        // ✅ VALIDAÇÃO SÉRIE PORTUGUESA
        if (!this.is_portuguese_naming_series(frm)) {
            frappe.msgprint({
                title: __('Erro de Compliance'),
                message: __('Naming series selecionada não é uma série portuguesa válida.'),
                indicator: 'red'
            });
            frappe.validated = false;
            return;
        }

        // ✅ VALIDAÇÃO SÉRIE COMUNICADA (SÍNCRONA)
        this.validate_series_communicated_before_save(frm);

        // Validar NIF se fornecido
        if (frm.doc.tax_id) {
            this.validate_nif_before_save(frm);
        }
    },

    validate_series_communicated_before_save: function(frm) {
        if (!frm.doc.naming_series) return;

        const prefix = frm.doc.naming_series.replace('.####', '');

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company
                },
                'fieldname': 'is_communicated'
            },
            async: false,
            callback: function(r) {
                if (!r.message || !r.message.is_communicated) {
                    frappe.msgprint({
                        title: __('Série Não Comunicada'),
                        message: __('Só pode emitir documentos com séries comunicadas à AT.'),
                        indicator: 'red'
                    });
                    frappe.validated = false;
                }
            }
        });
    },

    validate_portugal_fields: function(frm) {
        if (!this.is_portuguese_company(frm)) return;

        const validations = [];

        // Validação naming series
        if (!frm.doc.naming_series) {
            validations.push('Naming series portuguesa é obrigatória');
        } else if (!this.is_portuguese_naming_series(frm)) {
            validations.push('Naming series selecionada não é portuguesa');
        }

        // Validação NIF
        if (frm.doc.tax_id && !this.validate_portuguese_nif(frm.doc.tax_id)) {
            validations.push('NIF do cliente inválido');
        }

        // Validação valores
        if (!frm.doc.grand_total || frm.doc.grand_total <= 0) {
            validations.push('Total da fatura deve ser maior que zero');
        }

        // Mostrar validações
        if (validations.length > 0) {
            this.show_validation_errors(frm, validations);
        }
    },

    validate_compliance_full: function(frm) {
        const compliance_status = this.get_compliance_status_certified(frm);
        this.show_compliance_report(frm, compliance_status);
    },

    validate_nif_realtime: function(frm) {
        if (!frm.doc.tax_id) return;

        const is_valid = this.validate_portuguese_nif(frm.doc.tax_id);

        if (is_valid) {
            frm.set_df_property('tax_id', 'description', '✅ NIF válido');
        } else {
            frm.set_df_property('tax_id', 'description', '❌ NIF inválido');
        }

        frm.refresh_field('tax_id');
    },

    validate_nif_before_save: function(frm) {
        if (!this.validate_portuguese_nif(frm.doc.tax_id)) {
            frappe.msgprint({
                title: __('NIF Inválido'),
                message: __('O NIF fornecido não é válido segundo o algoritmo português.'),
                indicator: 'orange'
            });
        }
    },

    // ========== UTILITÁRIOS OTIMIZADOS ==========

    is_portuguese_company: function(frm) {
        // ✅ CACHE OTIMIZADO
        if (frm._is_portuguese_company !== undefined) {
            return frm._is_portuguese_company;
        }

        if (!frm.doc.company) {
            frm._is_portuguese_company = false;
            return false;
        }

        // ✅ VERIFICAÇÃO ASSÍNCRONA OTIMIZADA
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Company',
                'fieldname': ['country', 'portugal_compliance_enabled'],
                'filters': {'name': frm.doc.company}
            },
            callback: function(r) {
                if (r.message) {
                    const is_portuguese = r.message.country === 'Portugal' && r.message.portugal_compliance_enabled;
                    frm._is_portuguese_company = is_portuguese;

                    if (is_portuguese && !portugal_compliance_sales_invoice._state.compliance_checked) {
                        portugal_compliance_sales_invoice.setup_portugal_compliance_for_company(frm);
                    }
                }
            }
        });

        return false;
    },

    is_portuguese_naming_series: function(frm) {
        if (!frm.doc.naming_series || !frm.doc.company) return false;

        const prefix = frm.doc.naming_series.replace('.####', '');
        const cache_key = `portuguese_series_${prefix}_${frm.doc.company}`;

        // ✅ CACHE OTIMIZADO
        const cached_result = frappe.cache.get(cache_key);
        if (cached_result !== undefined) {
            return cached_result;
        }

        // Verificação assíncrona
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company,
                    'document_type': 'Sales Invoice',
                    'is_active': 1
                },
                'fieldname': ['is_communicated', 'validation_code']
            },
            callback: function(r) {
                const is_portuguese = !!(r.message && r.message.is_communicated && r.message.validation_code);
                frappe.cache.set(cache_key, is_portuguese, 300);

                if (is_portuguese) {
                    portugal_compliance_sales_invoice.update_compliance_status(frm);
                    portugal_compliance_sales_invoice.update_compliance_visual_feedback(frm);
                }
            }
        });

        return false;
    },

    validate_portuguese_nif: function(nif) {
        if (!nif) return false;

        nif = nif.toString().replace(/[^0-9]/g, '');

        if (nif.length !== 9) return false;
        if (!'123456789'.includes(nif[0])) return false;

        let checksum = 0;
        for (let i = 0; i < 8; i++) {
            checksum += parseInt(nif[i]) * (9 - i);
        }

        const remainder = checksum % 11;
        const control_digit = remainder < 2 ? 0 : 11 - remainder;

        return parseInt(nif[8]) === control_digit;
    },

    setup_portugal_compliance_for_company: function(frm) {
        console.log('🇵🇹 Configurando compliance português para empresa');

        this.show_portugal_fields(frm);

        // ✅ AUTO-SELEÇÃO INTELIGENTE
        if (!frm.doc.naming_series && !this._state.auto_select_scheduled) {
            this.schedule_auto_select_naming_series(frm);
        }

        this.setup_portugal_validations(frm);
        this.update_compliance_visual_feedback(frm);

        this._state.compliance_checked = true;
    },

    // ✅ AUTO-SELEÇÃO OTIMIZADA
    auto_select_naming_series: function(frm) {
        if (this._state.series_loading) return;

        this._state.series_loading = true;

        frappe.call({
            method: 'portugal_compliance.queries.series_queries.get_naming_series_for_doctype',
            args: {
                'doctype': 'Sales Invoice',
                'company': frm.doc.company,
                'communicated_only': 1
            },
            callback: function(r) {
                portugal_compliance_sales_invoice._state.series_loading = false;

                if (r.message && r.message.success && r.message.naming_series.length > 0) {
                    const selected_series = r.message.naming_series[0];

                    frm.set_value('naming_series', selected_series.naming_series);

                    frappe.show_alert({
                        message: __('Naming series portuguesa comunicada selecionada: {0}', [selected_series.naming_series]),
                        indicator: 'green'
                    });

                    portugal_compliance_sales_invoice.update_compliance_visual_feedback(frm);
                } else {
                    frappe.msgprint({
                        title: __('Séries Não Comunicadas'),
                        message: __('Não há séries portuguesas comunicadas para Sales Invoice. Configure e comunique séries primeiro.'),
                        indicator: 'orange'
                    });
                }
            },
            error: function() {
                portugal_compliance_sales_invoice._state.series_loading = false;
            }
        });
    },

    show_portugal_fields: function(frm) {
        if (frm.fields_dict.atcud_code) {
            frm.set_df_property('atcud_code', 'hidden', 0);
        }

        if (frm.fields_dict.naming_series) {
            frm.set_df_property('naming_series', 'reqd', 1);
            frm.set_df_property('naming_series', 'bold', 1);
        }

        frm.refresh_fields();
    },

    hide_portugal_fields: function(frm) {
        if (frm.fields_dict.atcud_code) {
            frm.set_df_property('atcud_code', 'hidden', 1);
        }

        if (frm.fields_dict.naming_series) {
            frm.set_df_property('naming_series', 'reqd', 0);
            frm.set_df_property('naming_series', 'bold', 0);
        }

        frm.refresh_fields();
    },

    setup_customer_nif_validation: function(frm) {
        if (frm.fields_dict.tax_id) {
            frm.fields_dict.tax_id.$input.attr('placeholder', 'Ex: 123456789');
            frm.fields_dict.tax_id.$input.attr('maxlength', '9');
        }
    },

    setup_portugal_validations: function(frm) {
        frm.set_df_property('naming_series', 'reqd', 1);
        frm.set_df_property('naming_series', 'bold', 1);
        frm.set_df_property('atcud_code', 'bold', 1);
    },

    setup_naming_series_filter: function(frm) {
        frm.set_query('naming_series', function() {
            return {
                query: 'portugal_compliance.queries.series_queries.get_naming_series_for_doctype',
                filters: {
                    'doctype': 'Sales Invoice',
                    'company': frm.doc.company,
                    'communicated_only': 1
                }
            };
        });
    },

    // ========== FEEDBACK VISUAL OTIMIZADO ==========

    update_compliance_visual_feedback: function(frm) {
        if (!frm.compliance_feedback_container) {
            this.setup_visual_feedback_system(frm);
        }

        const status = this.get_compliance_status_certified(frm);
        const feedback_html = this.build_compliance_feedback_html(status);

        frm.compliance_feedback_container.find('.compliance-status-card').html(feedback_html);
    },

    get_compliance_status_certified: function(frm) {
        const status = {
            level: 'none',
            title: 'Não Configurado',
            message: 'Configure a fatura para compliance português',
            icon: '⚪',
            color: 'grey',
            progress: 0,
            steps: []
        };

        if (!this.is_portuguese_company(frm)) {
            status.steps.push('❌ Empresa não é portuguesa');
            return status;
        }

        status.steps.push('✅ Empresa portuguesa');
        status.progress = 20;

        if (!frm.doc.naming_series) {
            status.level = 'warning';
            status.title = 'Naming Series Em Falta';
            status.message = 'Selecione uma naming series portuguesa';
            status.icon = '⚠️';
            status.color = 'orange';
            status.steps.push('❌ Selecionar naming series');
            return status;
        }

        status.steps.push('✅ Naming series definida');
        status.progress = 40;

        if (!this.is_portuguese_naming_series(frm)) {
            status.level = 'warning';
            status.title = 'Série Não Comunicada';
            status.message = 'Naming series não é portuguesa ou não está comunicada';
            status.icon = '⚠️';
            status.color = 'orange';
            status.steps.push('❌ Série não comunicada à AT');
            return status;
        }

        status.steps.push('✅ Série portuguesa comunicada');
        status.progress = 70;

        if (!frm.doc.atcud_code) {
            status.level = 'info';
            status.title = 'ATCUD Pendente';
            status.message = 'ATCUD será gerado ao salvar';
            status.icon = '🔵';
            status.color = 'blue';
            status.steps.push('⏳ ATCUD será gerado');
            status.progress = 85;
            return status;
        }

        status.steps.push('✅ ATCUD gerado');
        status.level = 'success';
        status.title = 'Compliance Total';
        status.message = 'Fatura em compliance total com legislação portuguesa';
        status.icon = '✅';
        status.color = 'green';
        status.progress = 100;

        return status;
    },

    build_compliance_feedback_html: function(status) {
        const progress_color = status.color === 'green' ? 'success' :
                              status.color === 'orange' ? 'warning' :
                              status.color === 'blue' ? 'info' : 'secondary';

        return `
            <div class="card border-${status.color === 'green' ? 'success' : status.color === 'orange' ? 'warning' : 'info'}">
                <div class="card-header bg-${status.color === 'green' ? 'success' : status.color === 'orange' ? 'warning' : 'info'} text-white">
                    <h6 class="mb-0">
                        ${status.icon} Portugal Compliance: ${status.title}
                    </h6>
                </div>
                <div class="card-body">
                    <p class="mb-2">${status.message}</p>

                    <div class="progress mb-3" style="height: 8px;">
                        <div class="progress-bar bg-${progress_color}"
                             style="width: ${status.progress}%"></div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <h6>📋 Checklist:</h6>
                            <ul class="list-unstyled mb-0">
                                ${status.steps.map(step => `<li style="font-size: 12px;">${step}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>📊 Progresso:</h6>
                            <p class="mb-0" style="font-size: 12px;">
                                <strong>${status.progress}%</strong> completo
                            </p>
                            ${status.progress === 100 ?
                                '<p class="text-success mb-0" style="font-size: 12px;"><i class="fa fa-check"></i> Pronto para emissão!</p>' :
                                '<p class="text-muted mb-0" style="font-size: 12px;">Complete os passos em falta</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // ========== INTERFACE E FEEDBACK ==========

    show_atcud_success: function(frm, atcud_code) {
        frappe.show_alert({
            message: __('ATCUD gerado com sucesso: {0}', [atcud_code]),
            indicator: 'green'
        });

        this.update_compliance_status(frm);
        this.update_compliance_visual_feedback(frm);
    },

    show_series_info: function(frm, series_data) {
        if (series_data.is_communicated) {
            frm.dashboard.add_comment(
                __('✅ Série comunicada à AT - ATCUD será gerado automaticamente'),
                'green'
            );
        } else {
            frm.dashboard.add_comment(
                __('⚠️ Série não comunicada à AT - Configure comunicação primeiro'),
                'orange'
            );
        }
    },

    show_validation_errors: function(frm, validations) {
        const message = '<ul><li>' + validations.join('</li><li>') + '</li></ul>';

        frappe.msgprint({
            title: __('Erros de Validação'),
            message: message,
            indicator: 'red'
        });
    },

    show_compliance_report: function(frm, status) {
        const dialog = new frappe.ui.Dialog({
            title: __('Relatório de Compliance'),
            fields: [
                {
                    fieldtype: 'HTML',
                    options: this.build_compliance_report_html(status)
                }
            ],
            primary_action_label: __('Fechar'),
            primary_action: function() {
                dialog.hide();
            }
        });
        dialog.show();
    },

    build_compliance_report_html: function(status) {
        let html = '<div style="padding: 15px;">';

        const status_color = status.level === 'success' ? 'green' : status.level === 'warning' ? 'orange' : 'red';
        const status_icon = status.icon;

        html += `<h4 style="color: ${status_color};">${status_icon} Status: ${status.title}</h4>`;
        html += `<p>${status.message}</p>`;

        html += `<div class="progress mb-3"><div class="progress-bar" style="width: ${status.progress}%"></div></div>`;

        if (status.steps && status.steps.length > 0) {
            html += '<h5>📋 Checklist:</h5><ul>';
            status.steps.forEach(function(step) {
                html += `<li>${step}</li>`;
            });
            html += '</ul>';
        }

        if (status.level !== 'success') {
            html += '<h5>💡 Recomendações:</h5><ul>';
            if (!frm.doc.naming_series) {
                html += '<li>Selecione uma naming series portuguesa comunicada</li>';
            }
            if (!frm.doc.atcud_code) {
                html += '<li>ATCUD será gerado automaticamente ao salvar</li>';
            }
            html += '</ul>';
        }

        html += '</div>';
        return html;
    },

    update_compliance_status: function(frm) {
        let status = 'red';
        let message = 'Não Compliant';

        if (this.is_portuguese_naming_series(frm) && frm.doc.atcud_code) {
            status = 'green';
            message = 'Compliant';
        } else if (this.is_portuguese_naming_series(frm)) {
            status = 'orange';
            message = 'Parcialmente Compliant';
        }

        frm.dashboard.set_headline_alert(
            `<div style="color: ${status};">🇵🇹 Portugal Compliance: ${message}</div>`
        );
    },

    check_series_communication_status: function(frm) {
        if (!frm.doc.naming_series) return;

        const prefix = frm.doc.naming_series.replace('.####', '');

        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Portugal Series Configuration',
                'filters': {
                    'prefix': prefix,
                    'company': frm.doc.company
                },
                'fieldname': ['is_communicated', 'name']
            },
            callback: function(r) {
                if (r.message && !r.message.is_communicated) {
                    frm.add_custom_button(__('Comunicar Série à AT'), function() {
                        portugal_compliance_sales_invoice.communicate_series_to_at(frm, r.message.name);
                    }, __('Portugal Compliance'));
                }
            }
        });
    },

    communicate_series_to_at: function(frm, series_name) {
        frappe.call({
            method: 'portugal_compliance.doctype.portugal_series_configuration.portugal_series_configuration.register_series_at',
            args: {
                'series_name': series_name
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: __('Sucesso'),
                        message: __('Série comunicada à AT com sucesso! ATCUD: {0}', [r.message.validation_code]),
                        indicator: 'green'
                    });
                    frm.refresh();
                } else {
                    frappe.msgprint({
                        title: __('Erro'),
                        message: r.message ? r.message.error : __('Erro ao comunicar série'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    run_compliance_diagnostics: function(frm) {
        const diagnostics = {
            company: frm.doc.company,
            is_portuguese: this.is_portuguese_company(frm),
            naming_series: frm.doc.naming_series,
            is_portuguese_series: this.is_portuguese_naming_series(frm),
            atcud_code: frm.doc.atcud_code,
            tax_id: frm.doc.tax_id,
            nif_valid: this.validate_portuguese_nif(frm.doc.tax_id)
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
            ['É Portuguesa', diagnostics.is_portuguese ? 'Sim' : 'Não', diagnostics.is_portuguese ? '✅' : '❌'],
            ['Naming Series', diagnostics.naming_series || 'Não definida', diagnostics.naming_series ? '✅' : '❌'],
            ['Série Portuguesa', diagnostics.is_portuguese_series ? 'Sim' : 'Não', diagnostics.is_portuguese_series ? '✅' : '❌'],
            ['ATCUD', diagnostics.atcud_code || 'Não gerado', diagnostics.atcud_code ? '✅' : '⏳'],
            ['NIF Cliente', diagnostics.tax_id || 'Não fornecido', diagnostics.tax_id ? (diagnostics.nif_valid ? '✅' : '❌') : '⚪']
        ];

        checks.forEach(check => {
            html += `<tr><td>${check[0]}</td><td>${check[1]}</td><td>${check[2]}</td></tr>`;
        });

        html += '</table>';
        html += '</div>';

        return html;
    },

    check_portugal_compliance: function(frm) {
        if (this.is_portuguese_company(frm)) {
            this.update_compliance_visual_feedback(frm);
            this._state.compliance_checked = true;
        }
    }
};

// ========== FUNÇÕES AUXILIARES GLOBAIS OTIMIZADAS ==========

window.portugal_compliance_debug = function(frm) {
    console.log('🇵🇹 Portugal Compliance Debug Info:');
    console.log('Company:', frm.doc.company);
    console.log('Naming Series:', frm.doc.naming_series);
    console.log('ATCUD Code:', frm.doc.atcud_code);
    console.log('Is Portuguese Company:', portugal_compliance_sales_invoice.is_portuguese_company(frm));
    console.log('Is Portuguese Naming Series:', portugal_compliance_sales_invoice.is_portuguese_naming_series(frm));
    console.log('State:', portugal_compliance_sales_invoice._state);
};

window.reset_portugal_compliance = function(frm) {
    frm.set_value('naming_series', '');
    frm.set_value('atcud_code', '');
    portugal_compliance_sales_invoice.reset_state();
    portugal_compliance_sales_invoice.update_compliance_status(frm);
    portugal_compliance_sales_invoice.update_compliance_visual_feedback(frm);
    frappe.show_alert('Portugal Compliance reset', 'orange');
};

// ========== CSS OTIMIZADO ==========

$('<style>')
    .prop('type', 'text/css')
    .html(`
        .compliance-feedback-container {
            margin: 15px 0;
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
    `)
    .appendTo('head');

console.log('🇵🇹 Portugal Compliance Sales Invoice JS OTIMIZADO carregado com sucesso!');
