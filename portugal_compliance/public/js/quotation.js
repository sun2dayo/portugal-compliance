// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Quotation JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (OR2025NDX em vez de OR-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (OR)
 * ✅ Geração automática de ATCUD para orçamentos
 * ✅ Validação de compliance português para orçamentos
 * ✅ Interface otimizada para orçamentos portugueses
 */

frappe.ui.form.on('Quotation', {
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

            // show_compliance_status removida (2026-08-30, mesmo
            // achado do utilizador ja corrigido em stock_entry.js -
            // ver esse ficheiro para o historico completo). Nota
            // 2026-09-04: a razao original dada aqui ("Quotation nao
            // esta em document_hooks.py::supported_doctypes") ficou
            // desatualizada pela Fase 1 - Quotation E' um doctype de
            // compliance completo desde entao (ATCUD/serie/assinatura/
            // comunicacao AT reais). A remocao em si mantem-se (nao
            // reintroduzida), so a justificacao estava errada.

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
        setup_quotation_validations(frm);
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
            // validate_portuguese_series removida (2026-08-30) - ver
            // nota em stock_entry.js.

            // ✅ VERIFICAR STATUS DE COMUNICAÇÃO
            check_series_communication_status(frm);

            // ✅ MOSTRAR INFORMAÇÕES DA SÉRIE
            show_series_info(frm);
        }
    },

    // ========== EVENTOS DE CUSTOMER ==========
    customer: function(frm) {
        if (frm.doc.customer) {
            // ✅ VALIDAR NIF DO CLIENTE
            validate_customer_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_customer_tax_info(frm);
        }
    },

    // ========== EVENTOS DE VALIDADE ==========
    valid_till: function(frm) {
        if (frm.doc.valid_till) {
            // ✅ VALIDAR PRAZO DE VALIDADE
            validate_quotation_validity(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_quotation(frm);
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
    frm.set_query("customer", function() {
        return {
            filters: {
                "disabled": 0
            }
        };
    });

    // ✅ FILTRO PARA TEMPLATES DE IMPOSTOS PORTUGUESES
    frm.set_query("taxes_and_charges", function() {
        return {
            filters: {
                "company": frm.doc.company
            }
        };
    });

    // ✅ FILTRO PARA ITENS ATIVOS
    frm.set_query("item_code", "items", function() {
        return {
            filters: {
                "disabled": 0,
                "is_sales_item": 1
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para orçamentos";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para orçamentos (OR2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPO VALIDADE
    if (frm.fields_dict.valid_till) {
        frm.fields_dict.valid_till.df.description = "Data de validade obrigatória para orçamentos portugueses";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE VALIDADE
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

    // ✅ EVENTO PARA VALIDADE EXPIRADA
    $(frm.wrapper).on('quotation_expired', function(e, data) {
        frappe.msgprint({
            title: __('Orçamento Expirado'),
            message: data.message,
            indicator: 'orange'
        });
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_portuguese_interface(frm) {
    /**
     * Configurar interface específica para Portugal
     */

    // ✅ CONFIGURAR LAYOUT PORTUGUÊS
    setup_portuguese_layout(frm);
}

// add_compliance_section, add_quotation_section,
// show_compliance_status e get_compliance_status removidas
// (2026-08-30, mesmo achado do utilizador ja corrigido em
// stock_entry.js - ver esse ficheiro para o historico completo). Nota
// 2026-09-04: a razao original dada aqui ("Quotation nao esta em
// document_hooks.py::supported_doctypes") ficou desatualizada pela
// Fase 1 - Quotation E' um doctype de compliance completo desde
// entao. A remocao em si mantem-se, so a justificacao estava errada.

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para orçamentos portugueses
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }
}

function get_validity_status(frm) {
    /**
     * Obter status de validade do orçamento
     */

    if (!frm.doc.valid_till) {
        return {
            label: 'Não Definida',
            color: 'orange',
            expired: false
        };
    }

    let valid_till = frappe.datetime.str_to_obj(frm.doc.valid_till);
    let today = new Date();

    if (valid_till < today) {
        return {
            label: 'Expirado',
            color: 'red',
            expired: true
        };
    }

    // Verificar se expira em breve (próximos 7 dias)
    let days_left = Math.ceil((valid_till - today) / (1000 * 60 * 60 * 24));

    if (days_left <= 7) {
        return {
            label: `Expira em ${days_left} dias`,
            color: 'orange',
            expired: false
        };
    }

    return {
        label: `Válido (${days_left} dias)`,
        color: 'green',
        expired: false
    };
}

function get_validity_days(frm) {
    /**
     * Obter número de dias de validade
     */

    if (!frm.doc.valid_till || !frm.doc.transaction_date) {
        return 'Não calculado';
    }

    let start_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);
    let end_date = frappe.datetime.str_to_obj(frm.doc.valid_till);
    let days = Math.ceil((end_date - start_date) / (1000 * 60 * 60 * 24));

    return days > 0 ? `${days} dias` : 'Inválido';
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para compliance português
     */

    if (frm.doc.__islocal) return;

    // ✅ BOTÃO PARA IMPRIMIR ORÇAMENTO PORTUGUÊS
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Orçamento PT'), function() {
            print_portuguese_quotation(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF CLIENTE
    if (frm.doc.customer) {
        frm.add_custom_button(__('Validar NIF Cliente'), function() {
            validate_customer_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA ANALISAR ORÇAMENTO
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Orçamento'), function() {
            analyze_quotation(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA RENOVAR VALIDADE
    if (frm.doc.docstatus === 1 && get_validity_status(frm).expired) {
        frm.add_custom_button(__('Renovar Validade'), function() {
            renew_quotation_validity(frm);
        }, __('Ações'));
    }

    // ✅ BOTÃO PARA CRIAR SALES ORDER
    if (frm.doc.docstatus === 1 && frm.doc.status !== 'Ordered') {
        frm.add_custom_button(__('Criar Sales Order'), function() {
            create_sales_order_from_quotation(frm);
        }, __('Conversões'));
    }

    // ✅ BOTÃO PARA DUPLICAR ORÇAMENTO
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Duplicar Orçamento'), function() {
            duplicate_quotation(frm);
        }, __('Ações'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA ORÇAMENTOS (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.api.series_api.get_available_portugal_series_certified',
        args: {
            doctype: 'Quotation',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS OR (formato SEM HÍFENS: OR2025NDX)
                let or_series = r.message.series.filter(s => s.prefix.startsWith('OR'));
                let communicated_series = or_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : or_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE OR
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série OR comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série OR não comunicada selecionada. Comunique à AT antes de submeter.'),
                            indicator: 'orange'
                        });
                    }
                }
            }
        }
    });
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
        message = __('Série OR comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série OR não comunicada à AT. Comunique antes de submeter orçamentos.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_quotation(frm) {
    /**
     * Validações específicas para orçamentos portugueses
     */

    let errors = [];

    // ✅ VALIDAR CLIENTE
    // 2026-08-30: era frm.doc.customer, mas Quotation nao tem esse
    // campo - o cliente fica em party_name (quotation_to='Customer').
    // frm.doc.customer era sempre undefined, logo este erro disparava
    // SEMPRE e bloqueava o Salvar de qualquer orcamento, mesmo com
    // cliente preenchido (confirmado ao vivo).
    if (!frm.doc.party_name) {
        errors.push(__('Cliente é obrigatório'));
    }

    // ✅ VALIDAR VALIDADE
    if (!frm.doc.valid_till) {
        errors.push(__('Data de validade é obrigatória para orçamentos portugueses'));
    } else {
        let validity_errors = validate_quotation_validity_rules(frm);
        errors = errors.concat(validity_errors);
    }

    // ✅ VALIDAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        errors.push(__('Pelo menos um item é obrigatório'));
    }

    // ✅ VALIDAR IMPOSTOS PORTUGUESES
    let tax_errors = validate_portuguese_taxes_structure(frm);
    errors = errors.concat(tax_errors);

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

function validate_quotation_validity(frm) {
    /**
     * Validar validade do orçamento
     */

    if (!frm.doc.valid_till) return;

    let valid_till = frappe.datetime.str_to_obj(frm.doc.valid_till);
    let today = new Date();

    if (valid_till <= today) {
        frappe.show_alert({
            message: __('Data de validade deve ser futura'),
            indicator: 'red'
        });
    } else {
        let days = Math.ceil((valid_till - today) / (1000 * 60 * 60 * 24));
        frappe.show_alert({
            message: __('Orçamento válido por {0} dias', [days]),
            indicator: 'green'
        });
    }
}

function validate_quotation_validity_rules(frm) {
    /**
     * Validar regras de validade do orçamento
     */

    let errors = [];

    if (!frm.doc.valid_till) {
        errors.push(__('Data de validade é obrigatória'));
        return errors;
    }

    let valid_till = frappe.datetime.str_to_obj(frm.doc.valid_till);
    let transaction_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);

    // ✅ VERIFICAR SE DATA É FUTURA
    if (valid_till <= transaction_date) {
        errors.push(__('Data de validade deve ser posterior à data do orçamento'));
    }

    // ✅ VERIFICAR PRAZO MÁXIMO (1 ano)
    let max_date = new Date(transaction_date);
    max_date.setFullYear(max_date.getFullYear() + 1);

    if (valid_till > max_date) {
        errors.push(__('Validade não pode exceder 1 ano'));
    }

    // ✅ VERIFICAR PRAZO MÍNIMO (1 dia)
    let min_date = new Date(transaction_date);
    min_date.setDate(min_date.getDate() + 1);

    if (valid_till < min_date) {
        errors.push(__('Validade deve ser de pelo menos 1 dia'));
    }

    return errors;
}

function validate_portuguese_taxes_structure(frm) {
    /**
     * Validar estrutura de impostos portugueses
     */

    let errors = [];

    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        errors.push(__('Configure impostos portugueses (IVA)'));
        return errors;
    }

    // ✅ VERIFICAR SE TEM IVA
    let has_iva = false;
    let iva_rates = [];

    frm.doc.taxes.forEach(function(tax) {
        // Em faturas multi-taxa (Item Tax Template diferente por linha),
        // o ERPNext gera as linhas de taxes dinamicamente e NUNCA
        // preenche description - so account_head (2026-08-30, confirmado
        // ao vivo: {account_head: "24331 - IVA Liquidado 23% Normal - ZB",
        // description: undefined}). Sem este fallback, has_iva ficava
        // sempre false neste modo e bloqueava documentos com IVA genuino
        // e corretamente calculado.
        let description = (tax.description || tax.account_head || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            has_iva = true;
            iva_rates.push(tax.rate);
        }
    });

    if (!has_iva) {
        errors.push(__('Orçamento deve ter IVA configurado'));
    }

    // ✅ VALIDAR TAXAS DE IVA PORTUGUESAS
    let valid_rates = [0, 6, 13, 23]; // Taxas válidas em Portugal
    iva_rates.forEach(function(rate) {
        if (!valid_rates.includes(rate)) {
            errors.push(__('Taxa de IVA {0}% não é válida em Portugal', [rate]));
        }
    });

    return errors;
}

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão
     */

    return new Promise((resolve, reject) => {
        let validations = [];

        // ✅ VALIDAR VALIDADE OBRIGATÓRIA
        if (!frm.doc.valid_till) {
            validations.push(__('Data de validade é obrigatória'));
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
    });
}

// ========== FUNÇÕES ESPECÍFICAS DE ORÇAMENTO ==========

function setup_quotation_validations(frm) {
    /**
     * Configurar validações específicas de orçamento
     */

    // ✅ VALIDAR VALIDADE QUANDO MUDA
    if (frm.fields_dict.valid_till) {
        frm.fields_dict.valid_till.$input.on('change', function() {
            validate_quotation_validity(frm);
        });
    }

    // ✅ VALIDAR IMPOSTOS QUANDO MUDAM
    if (frm.fields_dict.taxes && frm.fields_dict.taxes.grid) {
        // Guarda adicional em .df (2026-08-24): get_field() pode devolver
        // um wrapper cujo .df ainda nao esta preenchido se o grid ainda
        // nao renderizou por completo neste refresh - sem isto, atribuir
        // .onchange rebentava com "Cannot set properties of undefined".
        var rate_field = frm.fields_dict.taxes.grid.get_field('rate');
        if (rate_field && rate_field.df) {
            rate_field.df.onchange = function() {
                validate_portuguese_taxes(frm);
            };
        }
    }
}

function validate_portuguese_taxes(frm) {
    /**
     * Validar impostos portugueses
     */

    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        frappe.show_alert({
            message: __('Configure impostos portugueses (IVA)'),
            indicator: 'orange'
        });
        return;
    }

    let iva_found = false;
    let invalid_rates = [];

    frm.doc.taxes.forEach(function(tax) {
        let description = (tax.description || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            iva_found = true;

            // Verificar se taxa é válida em Portugal
            let valid_rates = [0, 6, 13, 23];
            if (!valid_rates.includes(tax.rate)) {
                invalid_rates.push(tax.rate);
            }
        }
    });

    if (!iva_found) {
        frappe.show_alert({
            message: __('Adicione IVA português ao orçamento'),
            indicator: 'orange'
        });
    } else if (invalid_rates.length > 0) {
        frappe.show_alert({
            message: __('Taxas de IVA inválidas: {0}%', [invalid_rates.join(', ')]),
            indicator: 'red'
        });
    } else {
        frappe.show_alert({
            message: __('Impostos portugueses válidos'),
            indicator: 'green'
        });
    }
}

function calculate_tax_breakdown(frm) {
    /**
     * Calcular breakdown de impostos
     */

    let total_tax = 0;
    let iva_breakdown = {};

    if (frm.doc.taxes) {
        frm.doc.taxes.forEach(function(tax) {
            total_tax += (tax.tax_amount || 0);

            let description = (tax.description || '').toUpperCase();
            if (description.includes('IVA') || description.includes('VAT')) {
                let rate = tax.rate || 0;
                if (!iva_breakdown[rate]) {
                    iva_breakdown[rate] = 0;
                }
                iva_breakdown[rate] += (tax.tax_amount || 0);
            }
        });
    }

    return {
        total_tax: total_tax,
        iva_breakdown: iva_breakdown
    };
}

function validate_customer_nif(frm) {
    /**
     * ✅ CORRIGIDO: Validar NIF do cliente usando jinja_methods.py
     */

    if (!frm.doc.customer) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: 'tax_id'
        },
        callback: function(r) {
            if (r.message && r.message.tax_id) {
                validate_nif_format(frm, r.message.tax_id, 'Cliente');
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
                if (r.message) {
                    frappe.show_alert({
                        message: __('NIF {0} válido: {1}', [entity_type, nif]),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('NIF {0} inválido: {1}', [entity_type, nif]),
                        indicator: 'red'
                    });
                }
            }
        }
    });
}

// ========== FUNÇÕES DE AÇÕES ==========

function print_portuguese_quotation(frm) {
    /**
     * Imprimir orçamento com formato português
     */

    // Sem format explicito - deixa o Frappe escolher o print format por
    // defeito (nao existe ainda nenhum print format dedicado para este doctype).
    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function analyze_quotation(frm) {
    /**
     * Analisar orçamento completo
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise do Orçamento'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_info'
            }
        ]
    });

    let tax_info = calculate_tax_breakdown(frm);
    let customer_nif = get_customer_nif(frm);
    let validity_status = get_validity_status(frm);

    let html = `
        <div class="quotation-analysis">
            <h5>Análise do Orçamento: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Cliente:</strong></td><td>${frm.doc.customer_name}</td></tr>
                        <tr><td><strong>NIF Cliente:</strong></td><td>${customer_nif || 'Não definido'}</td></tr>
                        <tr><td><strong>Data Criação:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.transaction_date)}</td></tr>
                        <tr><td><strong>Válido Até:</strong></td><td>${frm.doc.valid_till ? frappe.datetime.str_to_user(frm.doc.valid_till) : 'Não definida'}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Valores</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Total s/ IVA:</strong></td><td>€${(frm.doc.net_total || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>Total IVA:</strong></td><td>€${tax_info.total_tax.toFixed(2)}</td></tr>
                        <tr><td><strong>Total c/ IVA:</strong></td><td>€${(frm.doc.grand_total || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>Nº Itens:</strong></td><td>${frm.doc.items ? frm.doc.items.length : 0}</td></tr>
                        <tr><td><strong>Status Validade:</strong></td><td style="color: ${validity_status.color === 'green' ? 'green' : validity_status.color === 'orange' ? 'orange' : 'red'}">${validity_status.label}</td></tr>
                    </table>
                </div>
            </div>

            <h6>Breakdown IVA</h6>
            <table class="table table-striped">
                <thead>
                    <tr><th>Taxa</th><th>Valor</th><th>Status</th></tr>
                </thead>
                <tbody>
    `;

    Object.keys(tax_info.iva_breakdown).forEach(function(rate) {
        let valid_rates = [0, 6, 13, 23];
        let is_valid = valid_rates.includes(parseFloat(rate));
        html += `
            <tr>
                <td>IVA ${rate}%</td>
                <td>€${tax_info.iva_breakdown[rate].toFixed(2)}</td>
                <td style="color: ${is_valid ? 'green' : 'red'}">${is_valid ? 'Válida' : 'Inválida'}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.analysis_info.$wrapper.html(html);
    dialog.show();
}

function renew_quotation_validity(frm) {
    /**
     * Renovar validade do orçamento
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Renovar Validade do Orçamento'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'new_valid_till',
                label: __('Nova Data de Validade'),
                reqd: 1,
                default: frappe.datetime.add_days(frappe.datetime.nowdate(), 30)
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'renewal_reason',
                label: __('Motivo da Renovação'),
                reqd: 1
            }
        ],
        primary_action_label: __('Renovar'),
        primary_action: function(values) {
            frappe.call({
                method: 'portugal_compliance.api.renew_quotation_validity',
                args: {
                    quotation: frm.doc.name,
                    new_valid_till: values.new_valid_till,
                    reason: values.renewal_reason
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Validade renovada até {0}', [frappe.datetime.str_to_user(values.new_valid_till)]),
                            indicator: 'green'
                        });
                        dialog.hide();
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao renovar validade'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });

    dialog.show();
}

function create_sales_order_from_quotation(frm) {
    /**
     * Criar Sales Order a partir do orçamento
     */

    frappe.model.open_mapped_doc({
        method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
        frm: frm
    });
}

function duplicate_quotation(frm) {
    /**
     * Duplicar orçamento
     */

    frappe.confirm(
        __('Duplicar este orçamento? Será criado um novo orçamento com os mesmos dados.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.api.duplicate_quotation',
                args: {
                    quotation: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Orçamento duplicado: {0}', [r.message.new_quotation]),
                            indicator: 'green'
                        });

                        frappe.set_route("Form", "Quotation", r.message.new_quotation);
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao duplicar'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
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

function get_customer_nif(frm) {
    /**
     * Obter NIF do cliente
     */

    if (frm._customer_nif !== undefined) {
        return frm._customer_nif;
    }

    if (!frm.doc.customer) return null;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: 'tax_id'
        },
        async: false,
        callback: function(r) {
            frm._customer_nif = r.message ? r.message.tax_id : null;
        }
    });

    return frm._customer_nif;
}

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ CALCULAR BREAKDOWN DE IMPOSTOS
    let tax_info = calculate_tax_breakdown(frm);
    if (tax_info.total_tax > 0) {
        frm.doc.total_taxes_and_charges = tax_info.total_tax;
    }

    // ✅ DEFINIR VALIDADE PADRÃO SE NÃO DEFINIDA
    if (!frm.doc.valid_till && frm.doc.transaction_date) {
        let default_validity = frappe.datetime.add_days(frm.doc.transaction_date, 30);
        frm.doc.valid_till = default_validity;
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
                if (!frm.doc.currency && r.message.default_currency) {
                    frm.set_value('currency', r.message.default_currency);
                }
            }
        }
    });
}

function load_customer_tax_info(frm) {
    /**
     * Carregar informações fiscais do cliente
     */

    if (!frm.doc.customer) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: ['tax_id', 'tax_category']
        },
        callback: function(r) {
            if (r.message) {
                frm._customer_tax_info = r.message;
                frm._customer_nif = r.message.tax_id;

                // ✅ MOSTRAR NIF SE DISPONÍVEL
                if (r.message.tax_id) {
                    frm.dashboard.add_indicator(
                        __('NIF Cliente: {0}', [r.message.tax_id]),
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

    // ✅ CAMPOS OBRIGATÓRIOS PARA ORÇAMENTOS PORTUGUESES
    frm.toggle_reqd('customer', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('transaction_date', true);
    frm.toggle_reqd('valid_till', true);
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
        message: __('Orçamento português submetido com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR TOTAL E VALIDADE
    frm.dashboard.add_indicator(__('Total: €{0}', [(frm.doc.grand_total || 0).toFixed(2)]), 'blue');

    if (frm.doc.valid_till) {
        let validity_status = get_validity_status(frm);
        frm.dashboard.add_indicator(validity_status.label, validity_status.color);
    }
}

function validate_customer_nif_manual(frm) {
    /**
     * Validar NIF do cliente manualmente
     */

    if (!frm.doc.customer) {
        frappe.msgprint(__('Selecione um cliente primeiro'));
        return;
    }

    validate_customer_nif(frm);
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

// ========== EVENTOS DE ITEMS ==========

frappe.ui.form.on('Quotation Item', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR IMPOSTOS QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            validate_portuguese_taxes(frm);
        }, 100);
    },

    rate: function(frm, cdt, cdn) {
        // ✅ RECALCULAR IMPOSTOS QUANDO PREÇO MUDA
        setTimeout(() => {
            validate_portuguese_taxes(frm);
        }, 100);
    }
});

// ========== EVENTOS DE TAXES ==========

frappe.ui.form.on('Sales Taxes and Charges', {
    rate: function(frm, cdt, cdn) {
        // ✅ VALIDAR TAXA DE IVA QUANDO MUDA
        let tax_row = locals[cdt][cdn];
        if (tax_row.rate) {
            let valid_rates = [0, 6, 13, 23];
            if (!valid_rates.includes(tax_row.rate)) {
                frappe.show_alert({
                    message: __('Taxa {0}% pode não ser válida em Portugal', [tax_row.rate]),
                    indicator: 'orange'
                });
            }
        }

        setTimeout(() => {
            validate_portuguese_taxes(frm);
        }, 100);
    },

    tax_amount: function(frm, cdt, cdn) {
        // (recálculo de totais é nativo do ERPNext)
    }
});

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Quotation', {
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
            "Série portuguesa para orçamentos. Formato: OR2025EMPRESA.#### (OR=Orçamento)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para orçamentos.";
    }

    if (frm.fields_dict.valid_till) {
        frm.fields_dict.valid_till.df.description =
            "Data de validade obrigatória para orçamentos portugueses (máximo 1 ano)";
    }

    if (frm.fields_dict.taxes_and_charges) {
        frm.fields_dict.taxes_and_charges.df.description =
            "Template de impostos portugueses (IVA 0%, 6%, 13%, 23%)";
    }

    if (frm.fields_dict.customer) {
        frm.fields_dict.customer.df.description =
            "Cliente português (verificar NIF para compliance)";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado para Portugal Compliance
     */

    // ✅ CTRL+V para validar validade
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+v',
        action: () => {
            if (frm.doc.valid_till) {
                validate_quotation_validity(frm);
            }
        },
        description: __('Validar Validade'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_quotation(frm);
            }
        },
        description: __('Imprimir Orçamento Português'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar orçamento
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.docstatus === 1) {
                analyze_quotation(frm);
            }
        },
        description: __('Analisar Orçamento'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+R para renovar validade
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+r',
        action: () => {
            if (frm.doc.docstatus === 1 && get_validity_status(frm).expired) {
                renew_quotation_validity(frm);
            }
        },
        description: __('Renovar Validade'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+S para criar sales order
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+s',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.status !== 'Ordered') {
                create_sales_order_from_quotation(frm);
            }
        },
        description: __('Criar Sales Order'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_quotation_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para orçamento
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

    // ✅ VERIFICAR VALIDADE
    if (!frm.doc.valid_till) {
        compliance_issues.push({
            type: 'error',
            message: 'Data de validade é obrigatória'
        });
    } else {
        let validity_status = get_validity_status(frm);
        if (validity_status.expired) {
            compliance_issues.push({
                type: 'error',
                message: 'Orçamento expirado'
            });
        }
    }

    // ✅ VERIFICAR DADOS DO CLIENTE
    let customer_nif = get_customer_nif(frm);
    if (!customer_nif) {
        compliance_issues.push({
            type: 'warning',
            message: 'NIF do cliente não definido'
        });
    }

    // ✅ VERIFICAR IMPOSTOS
    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        compliance_issues.push({
            type: 'warning',
            message: 'Impostos portugueses não configurados'
        });
    }

    return compliance_issues;
}

function show_compliance_report(frm) {
    /**
     * ✅ NOVA: Mostrar relatório completo de compliance
     */

    let issues = validate_quotation_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Orçamento</h5>

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

function generate_quotation_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo do orçamento
     */

    let tax_info = calculate_tax_breakdown(frm);
    let customer_nif = get_customer_nif(frm);
    let validity_status = get_validity_status(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo do Orçamento'),
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
        <div class="quotation-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Orçamento</h3>
                <p><strong>Orçamento:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.transaction_date)}</p>
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
                    <h5>Dados do Cliente</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Nome:</strong></td><td>${frm.doc.customer_name}</td></tr>
                        <tr><td><strong>NIF:</strong></td><td>${customer_nif || 'N/A'}</td></tr>
                        <tr><td><strong>Válido Até:</strong></td><td>${frm.doc.valid_till ? frappe.datetime.str_to_user(frm.doc.valid_till) : 'N/A'}</td></tr>
                        <tr><td><strong>Status Validade:</strong></td><td style="color: ${validity_status.color === 'green' ? 'green' : validity_status.color === 'orange' ? 'orange' : 'red'}">${validity_status.label}</td></tr>
                    </table>
                </div>
            </div>

            <h5>Resumo Financeiro</h5>
            <table class="table table-bordered">
                <tr><td><strong>Total sem IVA:</strong></td><td style="text-align: right;">€${(frm.doc.net_total || 0).toFixed(2)}</td></tr>
                <tr><td><strong>Total IVA:</strong></td><td style="text-align: right;">€${tax_info.total_tax.toFixed(2)}</td></tr>
                <tr style="font-weight: bold; background-color: #f8f9fa;"><td><strong>Total com IVA:</strong></td><td style="text-align: right;">€${(frm.doc.grand_total || 0).toFixed(2)}</td></tr>
            </table>

            <h5>Breakdown IVA</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Taxa IVA</th><th style="text-align: right;">Valor Base</th><th style="text-align: right;">Valor IVA</th></tr>
                </thead>
                <tbody>
    `;

    Object.keys(tax_info.iva_breakdown).forEach(function(rate) {
        // Calcular base aproximada (simplificado)
        let base_amount = tax_info.iva_breakdown[rate] / (parseFloat(rate) / 100);
        if (parseFloat(rate) === 0) base_amount = frm.doc.net_total || 0;

        html += `
            <tr>
                <td>IVA ${rate}%</td>
                <td style="text-align: right;">€${base_amount.toFixed(2)}</td>
                <td style="text-align: right;">€${tax_info.iva_breakdown[rate].toFixed(2)}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>

            <h5>Itens do Orçamento (${frm.doc.items ? frm.doc.items.length : 0})</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Item</th><th>Qtd</th><th style="text-align: right;">Preço Unit.</th><th style="text-align: right;">Total</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            html += `
                <tr>
                    <td>${item.item_name || item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td style="text-align: right;">€${(item.rate || 0).toFixed(2)}</td>
                    <td style="text-align: right;">€${(item.amount || 0).toFixed(2)}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>

            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <p><strong>Relatório gerado em:</strong> ${frappe.datetime.now_datetime()}</p>
                <p><strong>Portugal Compliance:</strong> Conforme Portaria 195/2020</p>
                <p><strong>Status do Orçamento:</strong> ${frm.doc.status}</p>
                <p><strong>Validade:</strong> ${get_validity_days(frm)}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Quotation JS loaded - Version 2.0.0');
