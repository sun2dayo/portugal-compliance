// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Journal Entry JS - Portugal Compliance VERSÃO NATIVA COMPLETA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ Auto-seleção de séries portuguesas comunicadas (JE/LC)
 * ✅ Geração automática de ATCUD para lançamentos contabilísticos
 * ✅ Validação de compliance português para lançamentos
 * ✅ Interface otimizada para lançamentos contabilísticos portugueses
 */

frappe.ui.form.on('Journal Entry', {
    // ========== SETUP INICIAL DO FORMULÁRIO ==========
    setup: function(frm) {
        // ✅ CONFIGURAR FILTROS PORTUGUESES
        setup_portugal_filters(frm);

        // ✅ CONFIGURAR CAMPOS PERSONALIZADOS
        setup_custom_fields(frm);

        // ✅ CONFIGURAR VALIDADORES
        setup_validators(frm);

        // ✅ CONFIGURAR EVENTOS PERSONALIZADOS
        setup_custom_events(frm);
    },

    // ========== REFRESH DO FORMULÁRIO ==========
    refresh: function(frm) {
        // ✅ VERIFICAR SE É EMPRESA PORTUGUESA
        if (is_portuguese_company(frm)) {
            // ✅ CONFIGURAR INTERFACE PORTUGUESA
            setup_portuguese_interface(frm);

            // ✅ MOSTRAR STATUS DE COMPLIANCE
            show_compliance_status(frm);

            // ✅ ADICIONAR BOTÕES PERSONALIZADOS
            add_custom_buttons(frm);

            // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
            setup_mandatory_fields(frm);
        }

        // ✅ ATUALIZAR DISPLAY DE ATCUD
        update_atcud_display(frm);

        // ✅ CONFIGURAR PRINT FORMATS
        setup_print_formats(frm);

        // ✅ CONFIGURAR VALIDAÇÕES CONTABILÍSTICAS
        setup_accounting_validations(frm);
    },

    // ========== EVENTOS DE EMPRESA ==========
    company: function(frm) {
        if (frm.doc.company) {
            // ✅ VERIFICAR COMPLIANCE PORTUGUÊS
            check_portugal_compliance(frm);

            // ✅ CONFIGURAR NAMING SERIES AUTOMÁTICA
            setup_automatic_naming_series(frm);

            // ✅ CARREGAR CONFIGURAÇÕES DA EMPRESA
            load_company_settings(frm);
        }
    },

    // ========== EVENTOS DE NAMING SERIES ==========
    naming_series: function(frm) {
        if (frm.doc.naming_series) {
            // ✅ VALIDAR SÉRIE PORTUGUESA
            validate_portuguese_series(frm);

            // ✅ VERIFICAR STATUS DE COMUNICAÇÃO
            check_series_communication_status(frm);

            // ✅ MOSTRAR INFORMAÇÕES DA SÉRIE
            show_series_info(frm);
        }
    },

    // ========== EVENTOS DE VOUCHER TYPE ==========
    voucher_type: function(frm) {
        if (frm.doc.voucher_type) {
            // ✅ CONFIGURAR CAMPOS BASEADO NO TIPO
            configure_fields_by_voucher_type(frm);

            // ✅ VALIDAR TIPO PARA COMPLIANCE
            validate_voucher_type(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_journal_entry(frm);
        }
    },

    // ========== EVENTOS BEFORE_SAVE ==========
    before_save: function(frm) {
        // ✅ PREPARAR DADOS PARA COMPLIANCE
        if (is_portuguese_company(frm)) {
            prepare_portugal_compliance_data(frm);
        }
    },

    // ========== EVENTOS AFTER_SAVE ==========
    after_save: function(frm) {
        // ✅ ATUALIZAR DISPLAY APÓS SAVE
        if (frm.doc.atcud_code) {
            update_atcud_display(frm);
            show_atcud_success_message(frm);
        }
    },

    // ========== EVENTOS BEFORE_SUBMIT ==========
    before_submit: function(frm) {
        // ✅ VALIDAÇÕES CRÍTICAS ANTES DA SUBMISSÃO
        if (is_portuguese_company(frm)) {
            return validate_before_submit_portuguese(frm);
        }
    },

    // ========== EVENTOS ON_SUBMIT ==========
    on_submit: function(frm) {
        // ✅ AÇÕES PÓS-SUBMISSÃO
        if (is_portuguese_company(frm)) {
            handle_portuguese_submission(frm);
        }
    }
});

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_portugal_filters(frm) {
    /**
     * Configurar filtros específicos para Portugal
     */

    // ✅ FILTRO PARA EMPRESAS PORTUGUESAS
    frm.set_query("company", function() {
        return {
            filters: {
                "country": "Portugal",
                "portugal_compliance_enabled": 1
            }
        };
    });

    // ✅ FILTRO PARA CONTAS DA EMPRESA
    frm.set_query("account", "accounts", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "is_group": 0
            }
        };
    });

    // ✅ FILTRO PARA COST CENTERS
    frm.set_query("cost_center", "accounts", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "is_group": 0
            }
        };
    });
}

function setup_custom_fields(frm) {
    /**
     * Configurar campos personalizados para compliance português
     */

    // ✅ CONFIGURAR CAMPO ATCUD
    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.read_only = 1;
        frm.fields_dict.atcud_code.df.bold = 1;
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para lançamentos contabilísticos";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para lançamentos (JE-YYYY-EMPRESA.#### ou LC-YYYY-EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPOS CONTABILÍSTICOS
    if (frm.fields_dict.voucher_type) {
        frm.fields_dict.voucher_type.df.description = "Tipo de lançamento conforme legislação portuguesa";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE BALANCEAMENTO
    frm.add_custom_validator = function(field_name, validator_fn) {
        frm.fields_dict[field_name] && frm.fields_dict[field_name].$input.on('blur', validator_fn);
    };
}

function setup_custom_events(frm) {
    /**
     * Configurar eventos personalizados
     */

    // ✅ EVENTO PERSONALIZADO PARA ATCUD
    $(frm.wrapper).on('atcud_generated', function(e, data) {
        if (data.document === frm.doc.name) {
            frm.reload_doc();
            frappe.show_alert({
                message: `ATCUD gerado: ${data.atcud}`,
                indicator: 'green'
            });
        }
    });

    // ✅ EVENTO PARA VALIDAÇÃO DE BALANCEAMENTO
    $(frm.wrapper).on('accounts_updated', function() {
        validate_journal_balance(frm);
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_portuguese_interface(frm) {
    /**
     * Configurar interface específica para Portugal
     */

    // ✅ ADICIONAR INDICADOR DE COMPLIANCE
    if (!frm.doc.__islocal) {
        let compliance_status = get_compliance_status(frm);

        frm.dashboard.add_indicator(
            __('Portugal Compliance: {0}', [compliance_status.label]),
            compliance_status.color
        );
    }

    // ✅ CONFIGURAR TÍTULO DINÂMICO
    if (frm.doc.atcud_code) {
        frm.set_title_field('name');
        frm.set_subtitle_field('atcud_code');
    }

    // ✅ CONFIGURAR LAYOUT PORTUGUÊS
    setup_portuguese_layout(frm);
}

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para lançamentos portugueses
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }

    // ✅ ADICIONAR SEÇÃO DE COMPLIANCE
    if (!frm.doc.__islocal && frm.doc.atcud_code) {
        add_compliance_section(frm);
    }

    // ✅ ADICIONAR SEÇÃO CONTABILÍSTICA
    add_accounting_section(frm);
}

function add_compliance_section(frm) {
    /**
     * Adicionar seção de informações de compliance
     */

    let balance_info = calculate_journal_balance(frm);

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações de Compliance Português - Lançamento Contabilístico
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>ATCUD:</strong> ${frm.doc.atcud_code || 'Não gerado'}<br>
                    <strong>Série:</strong> ${frm.doc.naming_series || 'Não definida'}<br>
                    <strong>Tipo:</strong> ${frm.doc.voucher_type || 'Não definido'}
                </div>
                <div class="col-md-6">
                    <strong>Status:</strong> <span class="indicator ${get_compliance_status(frm).color}">${get_compliance_status(frm).label}</span><br>
                    <strong>Total Débito:</strong> €${balance_info.total_debit.toFixed(2)}<br>
                    <strong>Total Crédito:</strong> €${balance_info.total_credit.toFixed(2)}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-12">
                    <strong>Balanceamento:</strong>
                    <span class="indicator ${balance_info.is_balanced ? 'green' : 'red'}">
                        ${balance_info.is_balanced ? 'Balanceado' : `Diferença: €${balance_info.difference.toFixed(2)}`}
                    </span>
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.compliance_section_added) {
        $(frm.fields_dict.naming_series.wrapper).after(compliance_html);
        frm.compliance_section_added = true;
    }
}

function add_accounting_section(frm) {
    /**
     * Adicionar seção específica contabilística
     */

    if (frm.doc.__islocal) return;

    let accounting_html = `
        <div class="accounting-info" style="
            background: #e1f5fe;
            border: 1px solid #0288d1;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #01579b;">
                📊 Informações Contabilísticas
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Tipo Lançamento:</strong> ${frm.doc.voucher_type || 'Não definido'}<br>
                    <strong>Data Lançamento:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}<br>
                    <strong>Nº Contas:</strong> ${frm.doc.accounts ? frm.doc.accounts.length : 0}
                </div>
                <div class="col-md-6">
                    <strong>Referência:</strong> ${frm.doc.cheque_no || frm.doc.reference_no || 'Não definida'}<br>
                    <strong>Data Referência:</strong> ${frm.doc.cheque_date ? frappe.datetime.str_to_user(frm.doc.cheque_date) : 'Não definida'}<br>
                    <strong>Observações:</strong> ${frm.doc.user_remark || 'Nenhuma'}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.accounting_section_added) {
        $(frm.fields_dict.voucher_type.wrapper).after(accounting_html);
        frm.accounting_section_added = true;
    }
}

function show_compliance_status(frm) {
    /**
     * Mostrar status de compliance no formulário
     */

    if (frm.doc.__islocal) return;

    let status = get_compliance_status(frm);

    // ✅ MOSTRAR INDICADOR NO DASHBOARD
    frm.dashboard.clear_headline();
    frm.dashboard.set_headline(
        `<span class="indicator ${status.color}">${status.label}</span> ${status.description}`
    );
}

function get_compliance_status(frm) {
    /**
     * Obter status de compliance do documento
     */

    if (!frm.doc.naming_series) {
        return {
            label: 'Não Configurado',
            color: 'red',
            description: 'Série portuguesa não definida'
        };
    }

    if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        return {
            label: 'Não Conforme',
            color: 'red',
            description: 'Série não é portuguesa'
        };
    }

    if (!frm.doc.atcud_code) {
        return {
            label: 'Pendente',
            color: 'orange',
            description: 'ATCUD será gerado automaticamente'
        };
    }

    // ✅ VERIFICAR BALANCEAMENTO
    let balance_info = calculate_journal_balance(frm);
    if (!balance_info.is_balanced) {
        return {
            label: 'Não Balanceado',
            color: 'red',
            description: 'Lançamento não está balanceado'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Lançamento conforme legislação portuguesa'
    };
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para compliance português
     */

    if (frm.doc.__islocal) return;

    // ✅ BOTÃO PARA GERAR ATCUD MANUALMENTE
    if (!frm.doc.atcud_code && frm.doc.naming_series) {
        frm.add_custom_button(__('Gerar ATCUD'), function() {
            generate_atcud_manually(frm);
        }, __('Portugal Compliance'));
    }

    // ✅ BOTÃO PARA VERIFICAR SÉRIE
    if (frm.doc.naming_series) {
        frm.add_custom_button(__('Verificar Série'), function() {
            check_series_status(frm);
        }, __('Portugal Compliance'));
    }

    // ✅ BOTÃO PARA VALIDAR BALANCEAMENTO
    if (frm.doc.accounts && frm.doc.accounts.length > 0) {
        frm.add_custom_button(__('Validar Balanceamento'), function() {
            validate_and_show_balance(frm);
        }, __('Contabilidade'));
    }

    // ✅ BOTÃO PARA ANALISAR LANÇAMENTO
    if (frm.doc.accounts && frm.doc.accounts.length > 0) {
        frm.add_custom_button(__('Analisar Lançamento'), function() {
            analyze_journal_entry(frm);
        }, __('Contabilidade'));
    }

    // ✅ BOTÃO PARA IMPRIMIR LANÇAMENTO PORTUGUÊS
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Lançamento PT'), function() {
            print_portuguese_journal_entry(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VERIFICAR CONTAS
    if (frm.doc.accounts && frm.doc.accounts.length > 0) {
        frm.add_custom_button(__('Verificar Contas'), function() {
            validate_all_accounts(frm);
        }, __('Validações'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * Configurar naming series automática para empresa portuguesa
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA LANÇAMENTOS
    frappe.call({
        method: 'portugal_compliance.api.get_available_portugal_series_certified',
        args: {
            doctype: 'Journal Entry',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS JE/LC (Journal Entry/Lançamento Contabilístico)
                let je_series = r.message.series.filter(s =>
                    s.prefix.startsWith('JE-') || s.prefix.startsWith('LC-')
                );
                let communicated_series = je_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : je_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE JE/LC
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série JE/LC comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série JE/LC não comunicada selecionada. Comunique à AT antes de submeter.'),
                            indicator: 'orange'
                        });
                    }
                }
            }
        }
    });
}

function validate_portuguese_series(frm) {
    /**
     * Validar se naming series é portuguesa
     */

    if (!frm.doc.naming_series) return;

    if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        frappe.msgprint({
            title: __('Série Inválida'),
            message: __('Para compliance português, use séries no formato JE-YYYY-EMPRESA.#### ou LC-YYYY-EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE LANÇAMENTO
    let prefix = frm.doc.naming_series.split('-')[0];
    if (!['JE', 'LC'].includes(prefix)) {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para Journal Entry, use séries JE (Journal Entry) ou LC (Lançamento Contabilístico)'),
            indicator: 'orange'
        });
    }
}

function check_series_communication_status(frm) {
    /**
     * Verificar status de comunicação da série
     */

    if (!frm.doc.naming_series) return;

    let prefix = frm.doc.naming_series.replace('.####', '');

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {
                prefix: prefix,
                company: frm.doc.company
            },
            fieldname: ['is_communicated', 'validation_code', 'communication_date']
        },
        callback: function(r) {
            if (r.message) {
                show_series_communication_info(frm, r.message);
            }
        }
    });
}

function show_series_communication_info(frm, series_info) {
    /**
     * Mostrar informações de comunicação da série
     */

    let message = '';
    let indicator = '';

    if (series_info.is_communicated) {
        message = __('Série JE/LC comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série JE/LC não comunicada à AT. Comunique antes de submeter lançamentos.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_journal_entry(frm) {
    /**
     * Validações específicas para lançamentos portugueses
     */

    let errors = [];

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato JE-YYYY-EMPRESA.#### ou LC-YYYY-EMPRESA.####)'));
    }

    // ✅ VALIDAR TIPO DE LANÇAMENTO
    if (!frm.doc.voucher_type) {
        errors.push(__('Tipo de lançamento é obrigatório'));
    }

    // ✅ VALIDAR CONTAS
    if (!frm.doc.accounts || frm.doc.accounts.length === 0) {
        errors.push(__('Pelo menos duas contas são obrigatórias'));
    } else if (frm.doc.accounts.length < 2) {
        errors.push(__('Lançamento deve ter pelo menos duas contas'));
    }

    // ✅ VALIDAR BALANCEAMENTO
    let balance_info = calculate_journal_balance(frm);
    if (!balance_info.is_balanced) {
        errors.push(__('Lançamento deve estar balanceado (débito = crédito)'));
    }

    // ✅ VALIDAR CONTAS DA EMPRESA
    if (frm.doc.accounts) {
        let accounts_errors = validate_accounts_company(frm);
        errors = errors.concat(accounts_errors);
    }

    // ✅ MOSTRAR ERROS
    if (errors.length > 0) {
        frappe.msgprint({
            title: __('Validação Portugal Compliance'),
            message: errors.join('<br>'),
            indicator: 'red'
        });
        frappe.validated = false;
    }
}

function validate_accounts_company(frm) {
    /**
     * Validar se todas as contas pertencem à empresa
     */

    let errors = [];

    if (frm.doc.accounts) {
        frm.doc.accounts.forEach(function(account_row, index) {
            if (!account_row.account) {
                errors.push(__('Linha {0}: Conta é obrigatória', [index + 1]));
            }

            if (!account_row.debit && !account_row.credit) {
                errors.push(__('Linha {0}: Valor débito ou crédito é obrigatório', [index + 1]));
            }

            if (account_row.debit && account_row.credit) {
                errors.push(__('Linha {0}: Não pode ter débito e crédito simultaneamente', [index + 1]));
            }
        });
    }

    return errors;
}

function calculate_journal_balance(frm) {
    /**
     * Calcular balanceamento do lançamento
     */

    let total_debit = 0;
    let total_credit = 0;

    if (frm.doc.accounts) {
        frm.doc.accounts.forEach(function(account_row) {
            total_debit += (account_row.debit || 0);
            total_credit += (account_row.credit || 0);
        });
    }

    let difference = Math.abs(total_debit - total_credit);
    let is_balanced = difference < 0.01; // Tolerância de 1 cêntimo

    return {
        total_debit: total_debit,
        total_credit: total_credit,
        difference: difference,
        is_balanced: is_balanced
    };
}

function validate_journal_balance(frm) {
    /**
     * Validar balanceamento do lançamento
     */

    let balance_info = calculate_journal_balance(frm);

    if (!balance_info.is_balanced) {
        frappe.show_alert({
            message: __('Lançamento não balanceado. Diferença: €{0}', [balance_info.difference.toFixed(2)]),
            indicator: 'red'
        });
    } else {
        frappe.show_alert({
            message: __('Lançamento balanceado corretamente'),
            indicator: 'green'
        });
    }

    // ✅ ATUALIZAR SEÇÃO DE COMPLIANCE SE EXISTIR
    if (frm.compliance_section_added) {
        $('.portugal-compliance-info').remove();
        frm.compliance_section_added = false;
        add_compliance_section(frm);
    }
}

function validate_voucher_type(frm) {
    /**
     * Validar tipo de lançamento para compliance
     */

    if (!frm.doc.voucher_type) return;

    // ✅ TIPOS PERMITIDOS PARA PORTUGAL
    let allowed_types = [
        'Journal Entry',
        'Bank Entry',
        'Cash Entry',
        'Credit Card Entry',
        'Debit Note',
        'Credit Note',
        'Contra Entry',
        'Excise Entry',
        'Write Off Entry',
        'Opening Entry',
        'Depreciation Entry',
        'Exchange Rate Revaluation'
    ];

    if (!allowed_types.includes(frm.doc.voucher_type)) {
        frappe.msgprint({
            title: __('Tipo Não Suportado'),
            message: __('Tipo de lançamento não suportado para compliance português'),
            indicator: 'orange'
        });
    }
}

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão
     */

    return new Promise((resolve, reject) => {
        let validations = [];

        // ✅ VALIDAR ATCUD OBRIGATÓRIO
        if (!frm.doc.atcud_code) {
            validations.push(__('ATCUD é obrigatório para lançamentos contabilísticos portugueses'));
        }

        // ✅ VALIDAR SÉRIE COMUNICADA
        if (frm.doc.naming_series) {
            let prefix = frm.doc.naming_series.replace('.####', '');

            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Portugal Series Configuration',
                    filters: {prefix: prefix, company: frm.doc.company},
                    fieldname: 'is_communicated'
                },
                callback: function(r) {
                    if (r.message && !r.message.is_communicated) {
                        validations.push(__('Série JE/LC deve estar comunicada à AT antes da submissão'));
                    }

                    // ✅ VALIDAR BALANCEAMENTO FINAL
                    let balance_info = calculate_journal_balance(frm);
                    if (!balance_info.is_balanced) {
                        validations.push(__('Lançamento deve estar balanceado antes da submissão'));
                    }

                    if (validations.length > 0) {
                        frappe.msgprint({
                            title: __('Validação Crítica'),
                            message: validations.join('<br>'),
                            indicator: 'red'
                        });
                        reject();
                    } else {
                        resolve();
                    }
                }
            });
        } else {
            if (validations.length > 0) {
                frappe.msgprint({
                    title: __('Validação Crítica'),
                    message: validations.join('<br>'),
                    indicator: 'red'
                });
                reject();
            } else {
                resolve();
            }
        }
    });
}

// ========== FUNÇÕES CONTABILÍSTICAS ==========

function setup_accounting_validations(frm) {
    /**
     * Configurar validações específicas contabilísticas
     */

    // ✅ VALIDAR VALORES DOS LANÇAMENTOS
    if (frm.fields_dict.accounts && frm.fields_dict.accounts.grid) {
        frm.fields_dict.accounts.grid.get_field('debit').df.onchange = function() {
            validate_journal_balance(frm);
        };

        frm.fields_dict.accounts.grid.get_field('credit').df.onchange = function() {
            validate_journal_balance(frm);
        };
    }
}

function configure_fields_by_voucher_type(frm) {
    /**
     * Configurar campos baseado no tipo de lançamento
     */

    let type = frm.doc.voucher_type;

    switch(type) {
        case 'Bank Entry':
            frm.toggle_reqd('cheque_no', true);
            frm.toggle_reqd('cheque_date', true);
            frappe.show_alert({
                message: __('Preencha número e data do cheque/transferência'),
                indicator: 'blue'
            });
            break;

        case 'Cash Entry':
            frm.toggle_reqd('cheque_no', false);
            frm.toggle_reqd('cheque_date', false);
            break;

        case 'Credit Card Entry':
            frm.toggle_reqd('reference_no', true);
            break;

        default:
            frm.toggle_reqd('cheque_no', false);
            frm.toggle_reqd('cheque_date', false);
            frm.toggle_reqd('reference_no', false);
    }
}

// ========== FUNÇÕES DE AÇÕES ==========

function generate_atcud_manually(frm) {
    /**
     * Gerar ATCUD manualmente
     */

    frappe.call({
        method: 'portugal_compliance.utils.document_hooks.generate_manual_atcud_certified',
        args: {
            doctype: frm.doc.doctype,
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('ATCUD gerado: {0}', [r.message.atcud_code]),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao gerar ATCUD'),
                    indicator: 'red'
                });
            }
        }
    });
}

function check_series_status(frm) {
    /**
     * Verificar status da série
     */

    if (!frm.doc.naming_series) {
        frappe.msgprint(__('Naming series não definida'));
        return;
    }

    let prefix = frm.doc.naming_series.replace('.####', '');

    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {prefix: prefix, company: frm.doc.company}
        },
        callback: function(r) {
            if (r.message) {
                show_series_status_dialog(frm, r.message);
            } else {
                frappe.msgprint(__('Série não encontrada na configuração'));
            }
        }
    });
}

function show_series_status_dialog(frm, series_data) {
    /**
     * Mostrar dialog com status da série
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Status da Série JE/LC'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'series_info'
            }
        ]
    });

    let html = `
        <div class="series-status-info">
            <h5>${series_data.series_name}</h5>
            <table class="table table-bordered">
                <tr><td><strong>Prefixo:</strong></td><td>${series_data.prefix}</td></tr>
                <tr><td><strong>Tipo:</strong></td><td>Lançamento Contabilístico</td></tr>
                <tr><td><strong>Empresa:</strong></td><td>${series_data.company}</td></tr>
                <tr><td><strong>Ativa:</strong></td><td>${series_data.is_active ? 'Sim' : 'Não'}</td></tr>
                <tr><td><strong>Comunicada:</strong></td><td>${series_data.is_communicated ? 'Sim' : 'Não'}</td></tr>
                <tr><td><strong>Código AT:</strong></td><td>${series_data.validation_code || 'Não disponível'}</td></tr>
                <tr><td><strong>Sequência Atual:</strong></td><td>${series_data.current_sequence}</td></tr>
                <tr><td><strong>Total Emitidos:</strong></td><td>${series_data.total_documents_issued}</td></tr>
            </table>
        </div>
    `;

    dialog.fields_dict.series_info.$wrapper.html(html);
    dialog.show();
}

function validate_and_show_balance(frm) {
    /**
     * Validar e mostrar balanceamento
     */

    let balance_info = calculate_journal_balance(frm);

    frappe.msgprint({
        title: __('Informações de Balanceamento'),
        message: `
            <table class="table table-bordered">
                <tr><td><strong>Total Débito:</strong></td><td>€${balance_info.total_debit.toFixed(2)}</td></tr>
                <tr><td><strong>Total Crédito:</strong></td><td>€${balance_info.total_credit.toFixed(2)}</td></tr>
                <tr><td><strong>Diferença:</strong></td><td style="color: ${balance_info.is_balanced ? 'green' : 'red'}">€${balance_info.difference.toFixed(2)}</td></tr>
                <tr><td><strong>Status:</strong></td><td style="color: ${balance_info.is_balanced ? 'green' : 'red'}"><strong>${balance_info.is_balanced ? 'Balanceado' : 'Não Balanceado'}</strong></td></tr>
                <tr><td><strong>Nº Contas:</strong></td><td>${frm.doc.accounts ? frm.doc.accounts.length : 0}</td></tr>
            </table>
        `,
        indicator: balance_info.is_balanced ? 'green' : 'red'
    });
}

function analyze_journal_entry(frm) {
    /**
     * Analisar lançamento contabilístico
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise do Lançamento'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_info'
            }
        ]
    });

    let balance_info = calculate_journal_balance(frm);

    let html = `
        <div class="journal-analysis">
            <h5>Análise do Lançamento: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Tipo:</strong></td><td>${frm.doc.voucher_type || 'Não definido'}</td></tr>
                        <tr><td><strong>Data:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.posting_date)}</td></tr>
                        <tr><td><strong>Empresa:</strong></td><td>${frm.doc.company}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Balanceamento</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Débito:</strong></td><td>€${balance_info.total_debit.toFixed(2)}</td></tr>
                        <tr><td><strong>Total Crédito:</strong></td><td>€${balance_info.total_credit.toFixed(2)}</td></tr>
                        <tr><td><strong>Diferença:</strong></td><td style="color: ${balance_info.is_balanced ? 'green' : 'red'}">€${balance_info.difference.toFixed(2)}</td></tr>
                        <tr><td><strong>Status:</strong></td><td style="color: ${balance_info.is_balanced ? 'green' : 'red'}"><strong>${balance_info.is_balanced ? 'Balanceado' : 'Não Balanceado'}</strong></td></tr>
                    </table>
                </div>
            </div>

            <h6>Detalhes das Contas</h6>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Conta</th>
                        <th>Débito</th>
                        <th>Crédito</th>
                        <th>Centro de Custo</th>
                        <th>Observações</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.accounts) {
        frm.doc.accounts.forEach(function(account_row) {
            html += `
                <tr>
                    <td>${account_row.account || '-'}</td>
                    <td>€${(account_row.debit || 0).toFixed(2)}</td>
                    <td>€${(account_row.credit || 0).toFixed(2)}</td>
                    <td>${account_row.cost_center || '-'}</td>
                    <td>${account_row.user_remark || '-'}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.analysis_info.$wrapper.html(html);
    dialog.show();
}

function validate_all_accounts(frm) {
    /**
     * Validar todas as contas do lançamento
     */

    if (!frm.doc.accounts || frm.doc.accounts.length === 0) {
        frappe.msgprint(__('Nenhuma conta para validar'));
        return;
    }

    let accounts_to_check = frm.doc.accounts.filter(account => account.account);

    if (accounts_to_check.length === 0) {
        frappe.msgprint(__('Nenhuma conta válida para verificar'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Validação de Contas'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'accounts_info'
            }
        ]
    });

    let html = `
        <div class="accounts-validation-info">
            <h6>Validação de Contas do Lançamento</h6>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Conta</th>
                        <th>Empresa</th>
                        <th>Tipo</th>
                        <th>Status</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody id="accounts-table-body">
                    <tr><td colspan="5">Carregando...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.accounts_info.$wrapper.html(html);
    dialog.show();

    // Carregar dados das contas
    let checks_completed = 0;
    let accounts_data = [];

    accounts_to_check.forEach(function(account_row) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Account',
                filters: {name: account_row.account},
                fieldname: ['company', 'account_type', 'disabled', 'is_group']
            },
            callback: function(r) {
                checks_completed++;

                let status = 'Válida';
                let status_color = 'green';
                let company_match = true;

                if (r.message) {
                    if (r.message.company !== frm.doc.company) {
                        status = 'Empresa Diferente';
                        status_color = 'red';
                        company_match = false;
                    } else if (r.message.disabled) {
                        status = 'Desativada';
                        status_color = 'red';
                    } else if (r.message.is_group) {
                        status = 'É Grupo';
                        status_color = 'orange';
                    }
                } else {
                    status = 'Não Encontrada';
                    status_color = 'red';
                }

                let value = (account_row.debit || 0) + (account_row.credit || 0);

                accounts_data.push({
                    account: account_row.account,
                    company: r.message ? r.message.company : 'N/A',
                    account_type: r.message ? r.message.account_type : 'N/A',
                    status: status,
                    status_color: status_color,
                    value: value
                });

                if (checks_completed === accounts_to_check.length) {
                    // Atualizar tabela
                    let table_html = '';
                    accounts_data.forEach(function(data) {
                        table_html += `
                            <tr>
                                <td>${data.account}</td>
                                <td>${data.company}</td>
                                <td>${data.account_type}</td>
                                <td style="color: ${data.status_color}"><strong>${data.status}</strong></td>
                                <td>€${data.value.toFixed(2)}</td>
                            </tr>
                        `;
                    });

                    dialog.fields_dict.accounts_info.$wrapper.find('#accounts-table-body').html(table_html);
                }
            }
        });
    });
}

function print_portuguese_journal_entry(frm) {
    /**
     * Imprimir lançamento com formato português
     */

    frappe.route_options = {
        "format": "Lançamento Contabilístico Portugal"
    };

    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

// ========== FUNÇÕES AUXILIARES ==========

function is_portuguese_company(frm) {
    /**
     * Verificar se empresa é portuguesa com compliance ativo
     */

    if (!frm.doc.company) return false;

    // ✅ CACHE SIMPLES
    if (frm._is_portuguese_company !== undefined) {
        return frm._is_portuguese_company;
    }

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: {name: frm.doc.company},
            fieldname: ['country', 'portugal_compliance_enabled']
        },
        async: false,
        callback: function(r) {
            if (r.message) {
                frm._is_portuguese_company = (
                    r.message.country === 'Portugal' &&
                    r.message.portugal_compliance_enabled
                );
            } else {
                frm._is_portuguese_company = false;
            }
        }
    });

    return frm._is_portuguese_company || false;
}

function is_portuguese_naming_series(naming_series) {
    /**
     * Verificar se naming series é portuguesa
     */

    if (!naming_series) return false;

    // ✅ PADRÃO: XX-YYYY-COMPANY.####
    const pattern = /^[A-Z]{2,4}-\d{4}-[A-Z0-9]{2,4}\.####$/;
    return pattern.test(naming_series);
}

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ DEFINIR CAMPOS DE COMPLIANCE
    if (!frm.doc.portugal_compliance_status && frm.doc.naming_series) {
        if (is_portuguese_naming_series(frm.doc.naming_series)) {
            frm.doc.portugal_compliance_status = 'Pending';
        } else {
            frm.doc.portugal_compliance_status = 'Non-Compliant';
        }
    }

    // ✅ CALCULAR TOTAIS
    let balance_info = calculate_journal_balance(frm);
    if (balance_info.total_debit > 0) {
        frm.doc.total_debit = balance_info.total_debit;
        frm.doc.total_credit = balance_info.total_credit;
    }
}

function load_company_settings(frm) {
    /**
     * Carregar configurações da empresa
     */

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: {name: frm.doc.company},
            fieldname: ['at_environment', 'portugal_compliance_enabled']
        },
        callback: function(r) {
            if (r.message) {
                frm._company_settings = r.message;
            }
        }
    });
}

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA LANÇAMENTOS PORTUGUESES
    frm.toggle_reqd('voucher_type', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('posting_date', true);
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
    frm.meta.default_print_format = "Lançamento Contabilístico Portugal";
}

function update_atcud_display(frm) {
    /**
     * Atualizar display do ATCUD
     */

    if (frm.doc.atcud_code) {
        // ✅ DESTACAR ATCUD NO FORMULÁRIO
        if (frm.fields_dict.atcud_code) {
            frm.fields_dict.atcud_code.$wrapper.find('.control-value').css({
                'font-weight': 'bold',
                'color': '#2e7d32',
                'font-size': '14px'
            });
        }
    }
}

function show_atcud_success_message(frm) {
    /**
     * Mostrar mensagem de sucesso do ATCUD
     */

    if (frm.doc.atcud_code) {
        frappe.show_alert({
            message: __('ATCUD gerado automaticamente: {0}', [frm.doc.atcud_code]),
            indicator: 'green'
        });
    }
}

function handle_portuguese_submission(frm) {
    /**
     * Ações após submissão de documento português
     */

    // ✅ MOSTRAR MENSAGEM DE SUCESSO
    frappe.show_alert({
        message: __('Lançamento contabilístico português submetido com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR INFORMAÇÕES DE BALANCEAMENTO
    let balance_info = calculate_journal_balance(frm);
    frm.dashboard.add_indicator(__('Total: €{0}', [balance_info.total_debit.toFixed(2)]), 'blue');
}

function check_portugal_compliance(frm) {
    /**
     * Verificar compliance português da empresa
     */

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: {name: frm.doc.company},
            fieldname: ['country', 'portugal_compliance_enabled']
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.country === 'Portugal' && !r.message.portugal_compliance_enabled) {
                    frappe.msgprint({
                        title: __('Portugal Compliance'),
                        message: __('Ative o Portugal Compliance na empresa para usar funcionalidades portuguesas'),
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

function show_series_info(frm) {
    /**
     * Mostrar informações da série selecionada
     */

    if (!frm.doc.naming_series) return;

    let prefix = frm.doc.naming_series.replace('.####', '');

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {prefix: prefix, company: frm.doc.company},
            fieldname: ['series_name', 'is_communicated', 'current_sequence']
        },
        callback: function(r) {
            if (r.message) {
                let status = r.message.is_communicated ? 'Comunicada' : 'Não Comunicada';
                let color = r.message.is_communicated ? 'green' : 'orange';

                frm.dashboard.add_indicator(
                    __('Série: {0} ({1})', [r.message.series_name, status]),
                    color
                );
            }
        }
    });
}

// ========== EVENTOS DE ACCOUNTS ==========

frappe.ui.form.on('Journal Entry Account', {
    debit: function(frm, cdt, cdn) {
        // ✅ VALIDAR BALANCEAMENTO QUANDO DÉBITO MUDA
        setTimeout(() => {
            validate_journal_balance(frm);
        }, 100);
    },

    credit: function(frm, cdt, cdn) {
        // ✅ VALIDAR BALANCEAMENTO QUANDO CRÉDITO MUDA
        setTimeout(() => {
            validate_journal_balance(frm);
        }, 100);
    },

    account: function(frm, cdt, cdn) {
        // ✅ VALIDAR CONTA QUANDO MUDA
        let account_row = locals[cdt][cdn];
        if (account_row.account) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Account',
                    filters: {name: account_row.account},
                    fieldname: ['company', 'disabled', 'is_group']
                },
                callback: function(r) {
                    if (r.message) {
                        if (r.message.company !== frm.doc.company) {
                            frappe.show_alert({
                                message: __('Conta não pertence à empresa selecionada'),
                                indicator: 'red'
                            });
                        }
                        if (r.message.disabled) {
                            frappe.show_alert({
                                message: __('Conta está desativada'),
                                indicator: 'orange'
                            });
                        }
                        if (r.message.is_group) {
                            frappe.show_alert({
                                message: __('Não pode usar conta de grupo'),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            });
        }
    }
});

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Journal Entry', {
    onload: function(frm) {
        // ✅ CONFIGURAÇÃO INICIAL QUANDO FORMULÁRIO CARREGA
        if (is_portuguese_company(frm)) {
            // ✅ CONFIGURAR TOOLTIPS PORTUGUESES
            setup_portuguese_tooltips(frm);

            // ✅ CONFIGURAR ATALHOS DE TECLADO
            setup_keyboard_shortcuts(frm);
        }
    }
});

function setup_portuguese_tooltips(frm) {
    /**
     * Configurar tooltips específicos para Portugal
     */

    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description =
            "Série portuguesa para lançamentos. Formato: JE-YYYY-EMPRESA.#### (Journal Entry) ou LC-YYYY-EMPRESA.#### (Lançamento Contabilístico)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para lançamentos.";
    }

    if (frm.fields_dict.voucher_type) {
        frm.fields_dict.voucher_type.df.description =
            "Tipo de lançamento contabilístico conforme legislação portuguesa";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado para Portugal Compliance
     */

    // ✅ CTRL+G para gerar ATCUD
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+g',
        action: () => {
            if (!frm.doc.atcud_code && frm.doc.naming_series) {
                generate_atcud_manually(frm);
            }
        },
        description: __('Gerar ATCUD'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+B para validar balanceamento
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+b',
        action: () => {
            if (frm.doc.accounts && frm.doc.accounts.length > 0) {
                validate_and_show_balance(frm);
            }
        },
        description: __('Validar Balanceamento'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar lançamento
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.accounts && frm.doc.accounts.length > 0) {
                analyze_journal_entry(frm);
            }
        },
        description: __('Analisar Lançamento'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_journal_entry(frm);
            }
        },
        description: __('Imprimir Lançamento Português'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('Journal Entry', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_company(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form journal-entry-pt');

            // ✅ CONFIGURAR OBSERVADORES DE MUDANÇA
            setup_change_observers(frm);
        }
    }
});

function setup_change_observers(frm) {
    /**
     * Configurar observadores de mudança para campos críticos
     */

    // ✅ OBSERVAR MUDANÇAS NA NAMING SERIES
    frm.fields_dict.naming_series && frm.fields_dict.naming_series.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.naming_series) {
                validate_portuguese_series(frm);
                check_series_communication_status(frm);
                show_series_info(frm);
            }
        }, 100);
    });

	// ✅ OBSERVAR MUDANÇAS NO TIPO DE LANÇAMENTO
	frm.fields_dict.voucher_type && frm.fields_dict.voucher_type.$input.on('change', function() {
		setTimeout(() => {
			if (frm.doc.voucher_type) {
				configure_fields_by_voucher_type(frm);
				validate_voucher_type(frm);
			}
		}, 100);
	});
	}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Journal Entry JS loaded - Version 2.0.0');

