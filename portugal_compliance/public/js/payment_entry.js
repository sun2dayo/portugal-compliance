// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Payment Entry JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (RC2025NDX em vez de RC-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (RC/RB)
 * ✅ Geração automática de ATCUD para recibos
 * ✅ Validação de compliance português para pagamentos
 * ✅ Interface otimizada para recibos portugueses
 */

frappe.ui.form.on('Payment Entry', {
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

        // ✅ CONFIGURAR VALIDAÇÕES ESPECÍFICAS
        setup_payment_validations(frm);
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

    // ========== EVENTOS DE PARTY ==========
    party: function(frm) {
        if (frm.doc.party) {
            // ✅ VALIDAR NIF DA ENTIDADE
            validate_party_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_party_tax_info(frm);
        }
    },

    // ========== EVENTOS DE PAYMENT TYPE ==========
    payment_type: function(frm) {
        if (frm.doc.payment_type) {
            // ✅ CONFIGURAR CAMPOS BASEADO NO TIPO
            configure_fields_by_payment_type(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_payment_entry(frm);
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

    // ✅ FILTRO PARA CLIENTES PORTUGUESES
    frm.set_query("party", function() {
        if (frm.doc.party_type === "Customer") {
            return {
                filters: {
                    "disabled": 0
                }
            };
        } else if (frm.doc.party_type === "Supplier") {
            return {
                filters: {
                    "disabled": 0
                }
            };
        }
    });

    // ✅ FILTRO PARA CONTAS BANCÁRIAS PORTUGUESAS
    frm.set_query("paid_from", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "account_type": ["in", ["Bank", "Cash"]]
            }
        };
    });

    frm.set_query("paid_to", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "account_type": ["in", ["Bank", "Cash"]]
            }
        };
    });
}

function setup_custom_fields(frm) {
    /**
     * Configurar campos personalizados para compliance português
     */

    // ✅ CONFIGURAR CAMPO ATCUD (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.read_only = 1;
        frm.fields_dict.atcud_code.df.bold = 1;
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para recibos";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para recibos (RC2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPO QR CODE
    if (frm.fields_dict.qr_code) {
        frm.fields_dict.qr_code.df.read_only = 1;
        frm.fields_dict.qr_code.df.description = "QR Code conforme legislação portuguesa";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE NIF
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

    // ✅ EVENTO PARA VALIDAÇÃO DE PAGAMENTO
    $(frm.wrapper).on('payment_validated', function(e, data) {
        frappe.show_alert({
            message: data.message,
            indicator: data.valid ? 'green' : 'red'
        });
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


    // ✅ CONFIGURAR LAYOUT PORTUGUÊS
    setup_portuguese_layout(frm);
}

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para recibos portugueses
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }

    // ✅ ADICIONAR SEÇÃO DE PAGAMENTO
    add_payment_section(frm);
}

// add_compliance_section removida (2026-08-30): o cartão "Informações
// de Compliance Português" duplicava campos já nativamente visíveis no
// formulário (ATCUD, Série, Entidade/party_name, Tipo/payment_type,
// Valor/paid_amount, Modo/mode_of_payment, Data/posting_date) - ao
// contrário de Sales Invoice/POS Invoice, o Payment Entry nunca
// mostrava um NIF aqui (Party pode ser Customer, Supplier, etc., não
// é sempre um "Cliente"), por isso não há um badge equivalente a
// manter.

function add_payment_section(frm) {
    /**
     * Adicionar seção específica de pagamento
     */

    if (frm.doc.__islocal) return;

    let payment_html = `
        <div class="payment-info" style="
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #2e7d32;">
                💰 Informações do Pagamento
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>De:</strong> ${frm.doc.paid_from || 'Não definida'}<br>
                    <strong>Para:</strong> ${frm.doc.paid_to || 'Não definida'}<br>
                    <strong>Referência:</strong> ${frm.doc.reference_no || 'Não definida'}
                </div>
                <div class="col-md-6">
                    <strong>Data Ref:</strong> ${frm.doc.reference_date ? frappe.datetime.str_to_user(frm.doc.reference_date) : 'Não definida'}<br>
                    <strong>Status:</strong> ${frm.doc.status || 'Draft'}<br>
                    <strong>Observações:</strong> ${frm.doc.remarks ? 'Definidas' : 'Não definidas'}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.payment_section_added) {
        $(frm.fields_dict.party.wrapper).after(payment_html);
        frm.payment_section_added = true;
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

    // ✅ VERIFICAR DADOS OBRIGATÓRIOS
    if (!frm.doc.party || !frm.doc.paid_amount || !frm.doc.mode_of_payment) {
        return {
            label: 'Dados Incompletos',
            color: 'orange',
            description: 'Complete os dados obrigatórios'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Recibo conforme legislação portuguesa'
    };
}

function get_payment_type_display(payment_type) {
    /**
     * Obter display do tipo de pagamento
     */

    const types = {
        'Receive': 'Recebimento',
        'Pay': 'Pagamento',
        'Internal Transfer': 'Transferência Interna'
    };

    return types[payment_type] || payment_type || 'Não definido';
}

function get_payment_summary(frm) {
    /**
     * Obter resumo do pagamento
     */

    return {
        total_amount: frm.doc.paid_amount || 0,
        currency: frm.doc.paid_from_account_currency || 'EUR',
        exchange_rate: frm.doc.source_exchange_rate || 1,
        party_type: frm.doc.party_type || '',
        party_name: frm.doc.party_name || ''
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

    // ✅ BOTÃO PARA IMPRIMIR RECIBO PORTUGUÊS
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Recibo PT'), function() {
            print_portuguese_receipt(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF
    if (frm.doc.party) {
        frm.add_custom_button(__('Validar NIF'), function() {
            validate_party_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA ANALISAR PAGAMENTO
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Pagamento'), function() {
            analyze_payment_entry(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA GERAR QR CODE
    if (frm.doc.docstatus === 1 && frm.doc.atcud_code) {
        frm.add_custom_button(__('Gerar QR Code'), function() {
            generate_qr_code_for_payment(frm);
        }, __('Portugal Compliance'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA RECIBOS (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
        args: {
            doctype: 'Payment Entry',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS RG/RC/RB (formato SEM HÍFENS: RG2025NDX)
                // RG ("Outros recibos emitidos") é o código por omissão para
                // Payment Entry - RC é só para regime de IVA de Caixa (ver
                // Portugal Auth Settings.cash_vat_scheme), auditoria de
                // certificação 2026-08-24.
                let rc_series = r.message.series.filter(s => s.prefix.startsWith('RG') || s.prefix.startsWith('RC') || s.prefix.startsWith('RB'));
                let communicated_series = rc_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : rc_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE RG/RC/RB
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série de recibo comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série de recibo não comunicada selecionada. Comunique à AT antes de submeter.'),
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
     * ✅ CORRIGIDO: Validar se naming series é portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.naming_series) return;

    if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        frappe.msgprint({
            title: __('Série Inválida'),
            message: __('Para compliance português, use séries no formato RC2025EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE RECIBO (formato SEM HÍFENS)
    let prefix = frm.doc.naming_series.replace('.####', '');
    let doc_code = prefix.substring(0, 2); // Primeiros 2 caracteres: RG, RC ou RB

    if (!['RG', 'RC', 'RB'].includes(doc_code)) {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para Payment Entry, use séries RG (Outros Recibos), RC (regime de IVA de Caixa) ou RB (Recibo Bancário)'),
            indicator: 'orange'
        });
    }
}

function check_series_communication_status(frm) {
    /**
     * ✅ CORRIGIDO: Verificar status de comunicação da série (formato SEM HÍFENS)
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
        message = __('Série RC comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série RC não comunicada à AT. Comunique antes de submeter recibos.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_payment_entry(frm) {
    /**
     * Validações específicas para recibos portugueses
     */

    let errors = [];

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato RC2025EMPRESA.####)'));
    }

    // ✅ VALIDAR PARTY
    if (!frm.doc.party) {
        errors.push(__('Entidade é obrigatória'));
    }

    // ✅ VALIDAR VALOR
    if (!frm.doc.paid_amount || frm.doc.paid_amount <= 0) {
        errors.push(__('Valor pago deve ser maior que zero'));
    }

    // ✅ VALIDAR MODO DE PAGAMENTO
    if (!frm.doc.mode_of_payment) {
        errors.push(__('Modo de pagamento é obrigatório'));
    }

    // ✅ VALIDAR CONTAS
    if (frm.doc.payment_type === 'Receive' && !frm.doc.paid_to) {
        errors.push(__('Conta de destino é obrigatória para recebimentos'));
    }

    if (frm.doc.payment_type === 'Pay' && !frm.doc.paid_from) {
        errors.push(__('Conta de origem é obrigatória para pagamentos'));
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

function validate_party_nif(frm) {
    /**
     * ✅ CORRIGIDO: Validar NIF da party usando jinja_methods.py
     */

    if (!frm.doc.party || !frm.doc.party_type) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: frm.doc.party_type,
            filters: {name: frm.doc.party},
            fieldname: 'tax_id'
        },
        callback: function(r) {
            if (r.message && r.message.tax_id) {
                validate_nif_format(frm, r.message.tax_id, frm.doc.party_type);
            }
        }
    });
}

function validate_nif_format(frm, nif, entity_type) {
    /**
     * ✅ CORRIGIDO: Validar formato do NIF português usando jinja_methods.py
     */

    if (!nif) return;

    frappe.call({
        method: 'portugal_compliance.utils.jinja_methods.validate_portuguese_nif',
        args: {nif: nif},
        callback: function(r) {
            if (r.message !== undefined) {
                $(frm.wrapper).trigger('payment_validated', {
                    valid: r.message,
                    message: r.message ?
                        __('NIF {0} válido: {1}', [entity_type, nif]) :
                        __('NIF {0} inválido: {1}', [entity_type, nif])
                });
            }
        }
    });
}

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão
     */

    return new Promise((resolve, reject) => {
        let validations = [];

        // Nota (2026-08-24): removida a validacao "ATCUD obrigatorio"
        // que existia aqui - o ATCUD so passou a ser gerado no proprio
        // submit (servidor, generate_atcud_on_submit), nunca antes.
        // Manter este bloqueio bloquearia SEMPRE a submissao, porque
        // frm.doc.atcud_code nunca esta preenchido neste ponto
        // (before_submit corre no cliente, antes do pedido chegar ao
        // servidor). Ver document_hooks.py para a validacao real, que
        // agora corre do lado do servidor depois desta.

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
                        validations.push(__('Série RC deve estar comunicada à AT antes da submissão'));
                    }

                    // ✅ VALIDAR VALOR MÍNIMO
                    if (frm.doc.paid_amount && frm.doc.paid_amount > 1000 && !get_party_nif(frm)) {
                        validations.push(__('NIF obrigatório para pagamentos acima de €1000'));
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

// ========== FUNÇÕES ESPECÍFICAS DE PAGAMENTO ==========

function setup_payment_validations(frm) {
    /**
     * Configurar validações específicas de pagamento
     */

    // ✅ VALIDAR VALOR QUANDO MUDA
    if (frm.fields_dict.paid_amount) {
        frm.fields_dict.paid_amount.$input.on('change', function() {
            validate_payment_amount(frm);
        });
    }

    // ✅ VALIDAR MODO DE PAGAMENTO
    if (frm.fields_dict.mode_of_payment) {
        frm.fields_dict.mode_of_payment.$input.on('change', function() {
            configure_payment_mode_fields(frm);
        });
    }
}

function validate_payment_amount(frm) {
    /**
     * Validar valor do pagamento
     */

    if (!frm.doc.paid_amount) return;

    if (frm.doc.paid_amount <= 0) {
        frappe.show_alert({
            message: __('Valor deve ser maior que zero'),
            indicator: 'red'
        });
    } else if (frm.doc.paid_amount > 1000) {
        frappe.show_alert({
            message: __('Valor acima de €1000 - NIF obrigatório'),
            indicator: 'orange'
        });
    } else {
        frappe.show_alert({
            message: __('Valor válido: €{0}', [frm.doc.paid_amount.toFixed(2)]),
            indicator: 'green'
        });
    }
}

function configure_fields_by_payment_type(frm) {
    /**
     * Configurar campos baseado no tipo de pagamento
     */

    if (frm.doc.payment_type === 'Receive') {
        // ✅ CONFIGURAR PARA RECEBIMENTO
        frm.set_df_property('paid_to', 'reqd', 1);
        frm.set_df_property('paid_from', 'reqd', 0);
    } else if (frm.doc.payment_type === 'Pay') {
        // ✅ CONFIGURAR PARA PAGAMENTO
        frm.set_df_property('paid_from', 'reqd', 1);
        frm.set_df_property('paid_to', 'reqd', 0);
    } else if (frm.doc.payment_type === 'Internal Transfer') {
        // ✅ CONFIGURAR PARA TRANSFERÊNCIA
        frm.set_df_property('paid_from', 'reqd', 1);
        frm.set_df_property('paid_to', 'reqd', 1);
    }
}

function configure_payment_mode_fields(frm) {
    /**
     * Configurar campos baseado no modo de pagamento
     */

    if (!frm.doc.mode_of_payment) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Mode of Payment',
            filters: {name: frm.doc.mode_of_payment},
            fieldname: ['type', 'enabled']
        },
        callback: function(r) {
            if (r.message) {
                let mode_type = r.message.type;

                if (mode_type === 'Bank') {
                    // ✅ CONFIGURAR PARA BANCÁRIO
                    frm.set_df_property('reference_no', 'reqd', 1);
                    frm.set_df_property('reference_date', 'reqd', 1);
                } else if (mode_type === 'Cash') {
                    // ✅ CONFIGURAR PARA DINHEIRO
                    frm.set_df_property('reference_no', 'reqd', 0);
                    frm.set_df_property('reference_date', 'reqd', 0);
                }
            }
        }
    });
}

// ========== FUNÇÕES DE AÇÕES ==========

function generate_atcud_manually(frm) {
    /**
     * ✅ CORRIGIDO: Gerar ATCUD manualmente usando API correta
     */

    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.generate_manual_atcud_certified',
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
        title: __('Status da Série RC'),
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
                <tr><td><strong>Tipo:</strong></td><td>Recibo</td></tr>
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

function print_portuguese_receipt(frm) {
    /**
     * Imprimir recibo com formato português
     */

    // Sem format explicito - deixa o Frappe escolher o print format por
    // defeito (nao existe ainda nenhum print format dedicado para este doctype).
    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function analyze_payment_entry(frm) {
    /**
     * Analisar pagamento completo
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise do Pagamento'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_info'
            }
        ]
    });

    let party_nif = get_party_nif(frm);
    let payment_summary = get_payment_summary(frm);

    let html = `
        <div class="payment-analysis">
            <h5>Análise do Pagamento: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Entidade:</strong></td><td>${frm.doc.party_name}</td></tr>
                        <tr><td><strong>Tipo:</strong></td><td>${frm.doc.party_type}</td></tr>
                        <tr><td><strong>NIF:</strong></td><td>${party_nif || 'Não definido'}</td></tr>
                        <tr><td><strong>Data:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.posting_date)}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Detalhes do Pagamento</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Tipo:</strong></td><td>${get_payment_type_display(frm.doc.payment_type)}</td></tr>
                        <tr><td><strong>Valor:</strong></td><td>€${(frm.doc.paid_amount || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>Modo:</strong></td><td>${frm.doc.mode_of_payment || 'N/A'}</td></tr>
                        <tr><td><strong>Referência:</strong></td><td>${frm.doc.reference_no || 'N/A'}</td></tr>
                        <tr><td><strong>Status:</strong></td><td>${frm.doc.status}</td></tr>
                    </table>
                </div>
            </div>

            <h6>Contas Envolvidas</h6>
            <table class="table table-striped">
                <thead>
                    <tr><th>Tipo</th><th>Conta</th><th>Valor</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Origem</td>
                        <td>${frm.doc.paid_from || 'N/A'}</td>
                        <td>€${(frm.doc.paid_amount || 0).toFixed(2)}</td>
                    </tr>
                    <tr>
                        <td>Destino</td>
                        <td>${frm.doc.paid_to || 'N/A'}</td>
                        <td>€${(frm.doc.received_amount || frm.doc.paid_amount || 0).toFixed(2)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.analysis_info.$wrapper.html(html);
    dialog.show();
}

function generate_qr_code_for_payment(frm) {
    /**
     * ✅ NOVA: Gerar QR Code para o recibo
     */

    frappe.call({
        method: 'portugal_compliance.utils.jinja_methods.get_qr_code_data',
        args: {doctype: frm.doc.doctype, docname: frm.doc.name},
        callback: function(r) {
            if (r.message) {
                show_qr_code_dialog(frm, r.message);
            } else {
                frappe.msgprint(__('Erro ao gerar QR Code'));
            }
        }
    });
}

function show_qr_code_dialog(frm, qr_data) {
    /**
     * ✅ NOVA: Mostrar dialog com QR Code
     */

    let dialog = new frappe.ui.Dialog({
        title: __('QR Code do Recibo'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'qr_code_display'
            }
        ]
    });

    // ✅ GERAR QR CODE USANDO BIBLIOTECA
    let qr_image = frappe.utils.generate_qr_code(qr_data);

    let html = `
        <div class="qr-code-display text-center">
            <h6>QR Code para Recibo: ${frm.doc.name}</h6>
            <div class="qr-code-image">
                ${qr_image}
            </div>
            <p class="mt-3"><strong>Dados:</strong></p>
            <textarea class="form-control" rows="4" readonly>${qr_data}</textarea>
            <p class="mt-2"><small>Conforme legislação portuguesa - Portaria 195/2020</small></p>
        </div>
    `;

    dialog.fields_dict.qr_code_display.$wrapper.html(html);
    dialog.show();
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
     * ✅ CORRIGIDO: Verificar se naming series é portuguesa (formato SEM HÍFENS)
     */

    if (!naming_series) return false;

    // ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
    const pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{1,4}\.####$/;
    return pattern.test(naming_series);
}

function get_party_nif(frm) {
    /**
     * Obter NIF da party
     */

    if (frm._party_nif !== undefined) {
        return frm._party_nif;
    }

    if (!frm.doc.party || !frm.doc.party_type) return null;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: frm.doc.party_type,
            filters: {name: frm.doc.party},
            fieldname: 'tax_id'
        },
        async: false,
        callback: function(r) {
            frm._party_nif = r.message ? r.message.tax_id : null;
        }
    });

    return frm._party_nif;
}

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ DEFINIR MOEDA PADRÃO
    if (!frm.doc.paid_from_account_currency && frm.doc.company) {
        frm.doc.paid_from_account_currency = 'EUR';
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
            fieldname: ['portugal_compliance_enabled', 'default_currency']
        },
        callback: function(r) {
            if (r.message) {
                frm._company_settings = r.message;

                // Definir moeda padrão se não definida
                if (!frm.doc.paid_from_account_currency && r.message.default_currency) {
                    frm.set_value('paid_from_account_currency', r.message.default_currency);
                }
            }
        }
    });
}

function load_party_tax_info(frm) {
    /**
     * Carregar informações fiscais da party
     */

    if (!frm.doc.party || !frm.doc.party_type) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: frm.doc.party_type,
            filters: {name: frm.doc.party},
            fieldname: ['tax_id', 'tax_category']
        },
        callback: function(r) {
            if (r.message) {
                frm._party_tax_info = r.message;
                frm._party_nif = r.message.tax_id;

                // ✅ MOSTRAR NIF SE DISPONÍVEL
                if (r.message.tax_id) {
                    frm.dashboard.add_indicator(
                        __('NIF {0}: {1}', [frm.doc.party_type, r.message.tax_id]),
                        'blue'
                    );
                }
            }
        }
    });
}

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA RECIBOS PORTUGUESES
    frm.toggle_reqd('party', true);
    frm.toggle_reqd('paid_amount', true);
    frm.toggle_reqd('mode_of_payment', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('posting_date', true);
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
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
        message: __('Recibo português submetido com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR VALOR E TIPO
    frm.dashboard.add_indicator(__('Valor: €{0}', [(frm.doc.paid_amount || 0).toFixed(2)]), 'blue');
    frm.dashboard.add_indicator(get_payment_type_display(frm.doc.payment_type), 'blue');
}

function validate_party_nif_manual(frm) {
    /**
     * Validar NIF da party manualmente
     */

    if (!frm.doc.party) {
        frappe.msgprint(__('Selecione uma entidade primeiro'));
        return;
    }

    validate_party_nif(frm);
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

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Payment Entry', {
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
     * ✅ CORRIGIDO: Configurar tooltips específicos para Portugal (formato SEM HÍFENS)
     */

    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description =
            "Série portuguesa para recibos. Formato: RC2025EMPRESA.#### (RC=Recibo, RB=Recibo Bancário)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para recibos.";
    }

    if (frm.fields_dict.paid_amount) {
        frm.fields_dict.paid_amount.df.description =
            "Valor do pagamento (NIF obrigatório acima de €1000)";
    }

    if (frm.fields_dict.mode_of_payment) {
        frm.fields_dict.mode_of_payment.df.description =
            "Modo de pagamento conforme legislação portuguesa";
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

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_receipt(frm);
            }
        },
        description: __('Imprimir Recibo Português'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+Q para gerar QR Code
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+q',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.atcud_code) {
                generate_qr_code_for_payment(frm);
            }
        },
        description: __('Gerar QR Code'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar pagamento
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.docstatus === 1) {
                analyze_payment_entry(frm);
            }
        },
        description: __('Analisar Pagamento'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('Payment Entry', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_company(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form payment-entry-pt');

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

    // ✅ OBSERVAR MUDANÇAS NA PARTY
    frm.fields_dict.party && frm.fields_dict.party.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.party) {
                validate_party_nif(frm);
                load_party_tax_info(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO VALOR
    frm.fields_dict.paid_amount && frm.fields_dict.paid_amount.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.paid_amount) {
                validate_payment_amount(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO TIPO DE PAGAMENTO
    frm.fields_dict.payment_type && frm.fields_dict.payment_type.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.payment_type) {
                configure_fields_by_payment_type(frm);

                // Atualizar seção de pagamento
                if (frm.payment_section_added) {
                    $('.payment-info').remove();
                    frm.payment_section_added = false;
                    add_payment_section(frm);
                }
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO MODO DE PAGAMENTO
    frm.fields_dict.mode_of_payment && frm.fields_dict.mode_of_payment.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.mode_of_payment) {
                configure_payment_mode_fields(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NA REFERÊNCIA
    frm.fields_dict.reference_no && frm.fields_dict.reference_no.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.reference_no && frm.payment_section_added) {
                // Atualizar seção de pagamento
                $('.payment-info').remove();
                frm.payment_section_added = false;
                add_payment_section(frm);
            }
        }, 100);
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_payment_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para pagamento
     */

    let compliance_issues = [];

    // ✅ VERIFICAR SÉRIE PORTUGUESA
    if (!frm.doc.naming_series || !is_portuguese_naming_series(frm.doc.naming_series)) {
        compliance_issues.push({
            type: 'error',
            message: 'Série portuguesa não configurada'
        });
    }

    // ✅ VERIFICAR ATCUD
    if (!frm.doc.atcud_code) {
        compliance_issues.push({
            type: 'warning',
            message: 'ATCUD será gerado automaticamente'
        });
    }

    // ✅ VERIFICAR DADOS OBRIGATÓRIOS
    if (!frm.doc.party) {
        compliance_issues.push({
            type: 'error',
            message: 'Entidade é obrigatória'
        });
    }

    if (!frm.doc.paid_amount || frm.doc.paid_amount <= 0) {
        compliance_issues.push({
            type: 'error',
            message: 'Valor deve ser maior que zero'
        });
    }

    if (!frm.doc.mode_of_payment) {
        compliance_issues.push({
            type: 'error',
            message: 'Modo de pagamento é obrigatório'
        });
    }

    // ✅ VERIFICAR NIF PARA VALORES ALTOS
    if (frm.doc.paid_amount > 1000 && !get_party_nif(frm)) {
        compliance_issues.push({
            type: 'warning',
            message: 'NIF obrigatório para valores acima de €1000'
        });
    }

    // ✅ VERIFICAR CONTAS
    if (frm.doc.payment_type === 'Receive' && !frm.doc.paid_to) {
        compliance_issues.push({
            type: 'error',
            message: 'Conta de destino obrigatória para recebimentos'
        });
    }

    if (frm.doc.payment_type === 'Pay' && !frm.doc.paid_from) {
        compliance_issues.push({
            type: 'error',
            message: 'Conta de origem obrigatória para pagamentos'
        });
    }

    return compliance_issues;
}

function show_compliance_report(frm) {
    /**
     * ✅ NOVA: Mostrar relatório completo de compliance
     */

    let issues = validate_payment_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Recibo</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6 style="color: red;">Erros (${errors.length})</h6>
                    <ul>
    `;

    if (errors.length === 0) {
        html += '<li style="color: green;">Nenhum erro encontrado</li>';
    } else {
        errors.forEach(error => {
            html += `<li style="color: red;">${error.message}</li>`;
        });
    }

    html += `
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6 style="color: orange;">Avisos (${warnings.length})</h6>
                    <ul>
    `;

    if (warnings.length === 0) {
        html += '<li style="color: green;">Nenhum aviso</li>';
    } else {
        warnings.forEach(warning => {
            html += `<li style="color: orange;">${warning.message}</li>`;
        });
    }

    html += `
                    </ul>
                </div>
            </div>

            <div class="mt-3">
                <h6>Status Geral</h6>
                <p style="color: ${errors.length === 0 ? 'green' : 'red'}; font-weight: bold;">
                    ${errors.length === 0 ? '✅ Conforme com legislação portuguesa' : '❌ Não conforme - corrija os erros'}
                </p>
            </div>
        </div>
    `;

    frappe.msgprint({
        title: __('Relatório de Compliance'),
        message: html,
        indicator: errors.length === 0 ? 'green' : 'red'
    });
}

// ========== FUNÇÕES DE RELATÓRIOS ==========

function generate_payment_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo do pagamento
     */

    let party_nif = get_party_nif(frm);
    let payment_summary = get_payment_summary(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo do Pagamento'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'report_content'
            }
        ],
        primary_action_label: __('Exportar PDF'),
        primary_action: function() {
            // ✅ FUNCIONALIDADE DE EXPORTAÇÃO PDF
            window.print();
        }
    });

    let html = `
        <div class="payment-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Pagamento</h3>
                <p><strong>Recibo:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}</p>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <h5>Dados da Empresa</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Empresa:</strong></td><td>${frm.doc.company}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                        <tr><td><strong>Série:</strong></td><td>${frm.doc.naming_series || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Dados da Entidade</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Nome:</strong></td><td>${frm.doc.party_name}</td></tr>
                        <tr><td><strong>Tipo:</strong></td><td>${frm.doc.party_type}</td></tr>
                        <tr><td><strong>NIF:</strong></td><td>${party_nif || 'N/A'}</td></tr>
                    </table>
                </div>
            </div>

            <h5>Detalhes do Pagamento</h5>
            <table class="table table-bordered">
                <tr><td><strong>Tipo:</strong></td><td>${get_payment_type_display(frm.doc.payment_type)}</td></tr>
                <tr><td><strong>Valor:</strong></td><td style="text-align: right;">€${(frm.doc.paid_amount || 0).toFixed(2)}</td></tr>
                <tr><td><strong>Modo:</strong></td><td>${frm.doc.mode_of_payment || 'N/A'}</td></tr>
                <tr><td><strong>Referência:</strong></td><td>${frm.doc.reference_no || 'N/A'}</td></tr>
                <tr><td><strong>Data Referência:</strong></td><td>${frm.doc.reference_date ? frappe.datetime.str_to_user(frm.doc.reference_date) : 'N/A'}</td></tr>
            </table>

            <h5>Contas Envolvidas</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Tipo</th><th>Conta</th><th>Valor</th><th>Moeda</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Origem</td>
                        <td>${frm.doc.paid_from || 'N/A'}</td>
                        <td style="text-align: right;">€${(frm.doc.paid_amount || 0).toFixed(2)}</td>
                        <td>${frm.doc.paid_from_account_currency || 'EUR'}</td>
                    </tr>
                    <tr>
                        <td>Destino</td>
                        <td>${frm.doc.paid_to || 'N/A'}</td>
                        <td style="text-align: right;">€${(frm.doc.received_amount || frm.doc.paid_amount || 0).toFixed(2)}</td>
                        <td>${frm.doc.paid_to_account_currency || 'EUR'}</td>
                    </tr>
                </tbody>
            </table>

            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <p><strong>Relatório gerado em:</strong> ${frappe.datetime.now_datetime()}</p>
                <p><strong>Portugal Compliance:</strong> Conforme Portaria 195/2020</p>
                <p><strong>Status do Pagamento:</strong> ${frm.doc.status}</p>
                <p><strong>Observações:</strong> ${frm.doc.remarks || 'Nenhuma'}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== FUNÇÕES DE INTEGRAÇÃO BANCÁRIA ==========

function validate_bank_details(frm) {
    /**
     * ✅ NOVA: Validar detalhes bancários para pagamentos
     */

    if (!frm.doc.mode_of_payment) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Mode of Payment',
            filters: {name: frm.doc.mode_of_payment},
            fieldname: ['type', 'enabled']
        },
        callback: function(r) {
            if (r.message && r.message.type === 'Bank') {
                // ✅ VALIDAR REFERÊNCIA BANCÁRIA
                if (!frm.doc.reference_no) {
                    frappe.show_alert({
                        message: __('Referência bancária obrigatória para este modo de pagamento'),
                        indicator: 'orange'
                    });
                }

                // ✅ VALIDAR DATA DE REFERÊNCIA
                if (!frm.doc.reference_date) {
                    frappe.show_alert({
                        message: __('Data de referência obrigatória para pagamentos bancários'),
                        indicator: 'orange'
                    });
                }

                // ✅ VALIDAR FORMATO IBAN SE APLICÁVEL
                if (frm.doc.reference_no && frm.doc.reference_no.length > 20) {
                    validate_iban_format(frm.doc.reference_no);
                }
            }
        }
    });
}

function validate_iban_format(iban) {
    /**
     * ✅ NOVA: Validar formato IBAN português
     */

    if (!iban) return;

    // ✅ IBAN PORTUGUÊS: PT50 + 21 dígitos
    const iban_pattern = /^PT\d{23}$/;

    if (iban.startsWith('PT') && !iban_pattern.test(iban.replace(/\s/g, ''))) {
        frappe.show_alert({
            message: __('Formato IBAN português inválido'),
            indicator: 'red'
        });
    } else if (iban.startsWith('PT')) {
        frappe.show_alert({
            message: __('IBAN português válido'),
            indicator: 'green'
        });
    }
}

// ========== FUNÇÕES DE AUDITORIA ==========

function create_payment_audit_log(frm) {
    /**
     * ✅ NOVA: Criar log de auditoria para o pagamento
     */

    if (!frm.doc.docstatus === 1) return;

    let audit_data = {
        document_type: frm.doc.doctype,
        document_name: frm.doc.name,
        atcud_code: frm.doc.atcud_code,
        party_type: frm.doc.party_type,
        party: frm.doc.party,
        amount: frm.doc.paid_amount,
        currency: frm.doc.paid_from_account_currency,
        mode_of_payment: frm.doc.mode_of_payment,
        reference_no: frm.doc.reference_no,
        posting_date: frm.doc.posting_date,
        compliance_status: get_compliance_status(frm).label,
        created_by: frappe.session.user,
        created_at: frappe.datetime.now_datetime()
    };

    frappe.call({
        method: 'portugal_compliance.api.create_audit_log',
        args: {
            audit_data: audit_data
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                console.log('Audit log created for payment:', frm.doc.name);
            }
        }
    });
}

// ========== FUNÇÕES DE EXPORTAÇÃO ==========

function export_payment_data(frm) {
    /**
     * ✅ NOVA: Exportar dados do pagamento para SAF-T
     */

    if (!frm.doc.docstatus === 1) return;

    let saft_data = {
        // ✅ CABEÇALHO DO DOCUMENTO
        payment_no: frm.doc.name,
        atcud: frm.doc.atcud_code,
        payment_date: frm.doc.posting_date,
        payment_type: frm.doc.payment_type,

        // ✅ DADOS DA ENTIDADE
        party_type: frm.doc.party_type,
        party_id: frm.doc.party,
        party_name: frm.doc.party_name,
        party_nif: get_party_nif(frm),

        // ✅ DADOS FINANCEIROS
        amount: frm.doc.paid_amount,
        currency: frm.doc.paid_from_account_currency,
        exchange_rate: frm.doc.source_exchange_rate,

        // ✅ DADOS BANCÁRIOS
        mode_of_payment: frm.doc.mode_of_payment,
        reference_no: frm.doc.reference_no,
        reference_date: frm.doc.reference_date,

        // ✅ CONTAS
        paid_from: frm.doc.paid_from,
        paid_to: frm.doc.paid_to,

        // ✅ METADADOS
        created_by: frm.doc.owner,
        modified_by: frm.doc.modified_by,
        creation: frm.doc.creation,
        modified: frm.doc.modified
    };

    // ✅ CONVERTER PARA JSON FORMATADO
    let json_data = JSON.stringify(saft_data, null, 2);

    // ✅ CRIAR DOWNLOAD
    let blob = new Blob([json_data], { type: 'application/json' });
    let url = URL.createObjectURL(blob);
    let link = document.createElement('a');
    link.href = url;
    link.download = `payment_${frm.doc.name}.json`;
    link.click();
    URL.revokeObjectURL(url);

    frappe.show_alert({
        message: __('Dados do pagamento exportados: payment_{0}.json', [frm.doc.name]),
        indicator: 'green'
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Payment Entry JS loaded - Version 2.0.0');
