// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Sales Order JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (EC2025NDX em vez de EN-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (EC)
 * ✅ Geração automática de ATCUD para encomendas
 * ✅ Validação de compliance português para encomendas
 * ✅ Interface otimizada para encomendas portuguesas
 */

frappe.ui.form.on('Sales Order', {
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
            // 2026-09-04: a razao original dada aqui ("Sales Order nao
            // esta em document_hooks.py::supported_doctypes") ficou
            // desatualizada pela Fase 1 - Sales Order E' um doctype de
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
        setup_sales_order_validations(frm);
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

    // ========== EVENTOS DE DELIVERY DATE ==========
    delivery_date: function(frm) {
        if (frm.doc.delivery_date) {
            // ✅ VALIDAR PRAZO DE ENTREGA
            validate_delivery_date(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_sales_order(frm);
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para encomendas";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para encomendas (EC2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPO DELIVERY DATE
    if (frm.fields_dict.delivery_date) {
        frm.fields_dict.delivery_date.df.description = "Data de entrega obrigatória para encomendas portuguesas";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE PRAZO DE ENTREGA
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

    // ✅ EVENTO PARA PRAZO DE ENTREGA
    $(frm.wrapper).on('delivery_date_warning', function(e, data) {
        frappe.msgprint({
            title: __('Prazo de Entrega'),
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

// add_compliance_section, add_sales_order_section,
// show_compliance_status e get_compliance_status removidas
// (2026-08-30, mesmo achado do utilizador ja corrigido em
// stock_entry.js - ver esse ficheiro para o historico completo). Nota
// 2026-09-04: a razao original dada aqui ("Sales Order nao esta em
// document_hooks.py::supported_doctypes") ficou desatualizada pela
// Fase 1 - Sales Order E' um doctype de compliance completo desde
// entao. A remocao em si mantem-se, so a justificacao estava errada.

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para encomendas portuguesas
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }
}

function get_delivery_status(frm) {
    /**
     * Obter status de entrega da encomenda
     */

    if (!frm.doc.delivery_date) {
        return {
            label: 'Não Definida',
            color: 'orange',
            overdue: false
        };
    }

    let delivery_date = frappe.datetime.str_to_obj(frm.doc.delivery_date);
    let today = new Date();

    if (delivery_date < today) {
        return {
            label: 'Atrasada',
            color: 'red',
            overdue: true
        };
    }

    // Verificar se entrega é em breve (próximos 7 dias)
    let days_left = Math.ceil((delivery_date - today) / (1000 * 60 * 60 * 24));

    if (days_left <= 7) {
        return {
            label: `Entrega em ${days_left} dias`,
            color: 'orange',
            overdue: false
        };
    }

    return {
        label: `Entrega em ${days_left} dias`,
        color: 'green',
        overdue: false
    };
}

function get_delivery_days(frm) {
    /**
     * Obter número de dias para entrega
     */

    if (!frm.doc.delivery_date || !frm.doc.transaction_date) {
        return 'Não calculado';
    }

    let start_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);
    let end_date = frappe.datetime.str_to_obj(frm.doc.delivery_date);
    let days = Math.ceil((end_date - start_date) / (1000 * 60 * 60 * 24));

    return days > 0 ? `${days} dias` : 'Inválido';
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para compliance português
     */

    if (frm.doc.__islocal) return;

    // ✅ BOTÃO PARA IMPRIMIR ENCOMENDA PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Encomenda PT'), function() {
            print_portuguese_sales_order(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF CLIENTE
    if (frm.doc.customer) {
        frm.add_custom_button(__('Validar NIF Cliente'), function() {
            validate_customer_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA ANALISAR ENCOMENDA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Encomenda'), function() {
            analyze_sales_order(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA ATUALIZAR PRAZO
    if (frm.doc.docstatus === 1 && get_delivery_status(frm).overdue) {
        frm.add_custom_button(__('Atualizar Prazo'), function() {
            update_delivery_date(frm);
        }, __('Ações'));
    }

    // ✅ BOTÃO PARA CRIAR DELIVERY NOTE
    if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
        frm.add_custom_button(__('Criar Guia Remessa'), function() {
            create_delivery_note_from_sales_order(frm);
        }, __('Conversões'));
    }

    // ✅ BOTÃO PARA CRIAR SALES INVOICE
    if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
        frm.add_custom_button(__('Criar Fatura'), function() {
            create_sales_invoice_from_sales_order(frm);
        }, __('Conversões'));
    }

    // ✅ BOTÃO PARA DUPLICAR ENCOMENDA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Duplicar Encomenda'), function() {
            duplicate_sales_order(frm);
        }, __('Ações'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA ENCOMENDAS (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.api.series_api.get_available_portugal_series_certified',
        args: {
            doctype: 'Sales Order',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS EC (formato SEM HÍFENS: EC2025NDX)
                let ec_series = r.message.series.filter(s => s.prefix.startsWith('EC'));
                let communicated_series = ec_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : ec_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE EC
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série EC comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série EC não comunicada selecionada. Comunique à AT antes de submeter.'),
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
        message = __('Série EC comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série EC não comunicada à AT. Comunique antes de submeter encomendas.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_sales_order(frm) {
    /**
     * Validações específicas para encomendas portuguesas
     */

    let errors = [];

    // ✅ VALIDAR CLIENTE
    if (!frm.doc.customer) {
        errors.push(__('Cliente é obrigatório'));
    }

    // ✅ VALIDAR DATA DE ENTREGA
    if (!frm.doc.delivery_date) {
        errors.push(__('Data de entrega é obrigatória para encomendas portuguesas'));
    } else {
        let delivery_errors = validate_delivery_date_rules(frm);
        errors = errors.concat(delivery_errors);
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

function validate_delivery_date(frm) {
    /**
     * Validar data de entrega
     */

    if (!frm.doc.delivery_date) return;

    let delivery_date = frappe.datetime.str_to_obj(frm.doc.delivery_date);
    let transaction_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);

    if (delivery_date <= transaction_date) {
        frappe.show_alert({
            message: __('Data de entrega deve ser posterior à data da encomenda'),
            indicator: 'red'
        });
    } else {
        let days = Math.ceil((delivery_date - transaction_date) / (1000 * 60 * 60 * 24));
        frappe.show_alert({
            message: __('Prazo de entrega: {0} dias', [days]),
            indicator: 'green'
        });
    }
}

function validate_delivery_date_rules(frm) {
    /**
     * Validar regras de data de entrega
     */

    let errors = [];

    if (!frm.doc.delivery_date) {
        errors.push(__('Data de entrega é obrigatória'));
        return errors;
    }

    let delivery_date = frappe.datetime.str_to_obj(frm.doc.delivery_date);
    let transaction_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);

    // ✅ VERIFICAR SE DATA É FUTURA
    if (delivery_date <= transaction_date) {
        errors.push(__('Data de entrega deve ser posterior à data da encomenda'));
    }

    // ✅ VERIFICAR PRAZO MÁXIMO (1 ano)
    let max_date = new Date(transaction_date);
    max_date.setFullYear(max_date.getFullYear() + 1);

    if (delivery_date > max_date) {
        errors.push(__('Prazo de entrega não pode exceder 1 ano'));
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
        errors.push(__('Encomenda deve ter IVA configurado'));
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

        // ✅ VALIDAR DATA DE ENTREGA OBRIGATÓRIA
        if (!frm.doc.delivery_date) {
            validations.push(__('Data de entrega é obrigatória'));
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

// ========== FUNÇÕES ESPECÍFICAS DE ENCOMENDA ==========

function setup_sales_order_validations(frm) {
    /**
     * Configurar validações específicas de encomenda
     */

    // ✅ VALIDAR DATA DE ENTREGA QUANDO MUDA
    if (frm.fields_dict.delivery_date) {
        frm.fields_dict.delivery_date.$input.on('change', function() {
            validate_delivery_date(frm);
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
            message: __('Adicione IVA português à encomenda'),
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

function print_portuguese_sales_order(frm) {
    /**
     * Imprimir encomenda com formato português
     */

    // Sem format explicito - deixa o Frappe escolher o print format por
    // defeito (nao existe ainda nenhum print format dedicado para este doctype).
    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function analyze_sales_order(frm) {
    /**
     * Analisar encomenda completa
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise da Encomenda'),
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
    let delivery_status = get_delivery_status(frm);

    let html = `
        <div class="sales-order-analysis">
            <h5>Análise da Encomenda: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Cliente:</strong></td><td>${frm.doc.customer_name}</td></tr>
                        <tr><td><strong>NIF Cliente:</strong></td><td>${customer_nif || 'Não definido'}</td></tr>
                        <tr><td><strong>Data Encomenda:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.transaction_date)}</td></tr>
                        <tr><td><strong>Data Entrega:</strong></td><td>${frm.doc.delivery_date ? frappe.datetime.str_to_user(frm.doc.delivery_date) : 'Não definida'}</td></tr>
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
                        <tr><td><strong>Status Entrega:</strong></td><td style="color: ${delivery_status.color === 'green' ? 'green' : delivery_status.color === 'orange' ? 'orange' : 'red'}">${delivery_status.label}</td></tr>
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

function update_delivery_date(frm) {
    /**
     * Atualizar data de entrega - só em rascunho (docstatus=0).
     * Correção 2026-09-04 (princípio de inalterabilidade da AT): uma
     * encomenda submetida tem ATCUD/assinatura já gerados e não pode
     * ser alterada in-place - o backend já recusa isto de forma
     * definitiva, esta verificação aqui só evita abrir o diálogo
     * inteiro para o utilizador só descobrir o erro no fim.
     */
    if (frm.doc.docstatus !== 0) {
        frappe.msgprint({
            title: __('Documento Imutável'),
            message: __('Documentos fiscais submetidos não podem ser alterados. Utilize a função Duplicar para gerar um novo documento.'),
            indicator: 'orange'
        });
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Atualizar Data de Entrega'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'new_delivery_date',
                label: __('Nova Data de Entrega'),
                reqd: 1,
                default: frappe.datetime.add_days(frappe.datetime.nowdate(), 7)
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'update_reason',
                label: __('Motivo da Alteração'),
                reqd: 1
            }
        ],
        primary_action_label: __('Atualizar'),
        primary_action: function(values) {
            frappe.call({
                method: 'portugal_compliance.api.document_actions_api.update_sales_order_delivery_date',
                args: {
                    sales_order: frm.doc.name,
                    new_delivery_date: values.new_delivery_date,
                    reason: values.update_reason
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Data de entrega atualizada para {0}', [frappe.datetime.str_to_user(values.new_delivery_date)]),
                            indicator: 'green'
                        });
                        dialog.hide();
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao atualizar data'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });

    dialog.show();
}

function create_delivery_note_from_sales_order(frm) {
    /**
     * Criar Delivery Note a partir da encomenda
     */

    frappe.model.open_mapped_doc({
        method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
        frm: frm
    });
}

function create_sales_invoice_from_sales_order(frm) {
    /**
     * Criar Sales Invoice a partir da encomenda
     */

    frappe.model.open_mapped_doc({
        method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
        frm: frm
    });
}

function duplicate_sales_order(frm) {
    /**
     * Duplicar encomenda
     */

    frappe.confirm(
        __('Duplicar esta encomenda? Será criada uma nova encomenda com os mesmos dados.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.api.document_actions_api.duplicate_sales_order',
                args: {
                    sales_order: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Encomenda duplicada: {0}', [r.message.new_sales_order]),
                            indicator: 'green'
                        });

                        frappe.set_route("Form", "Sales Order", r.message.new_sales_order);
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

    // ✅ DEFINIR DATA DE ENTREGA PADRÃO SE NÃO DEFINIDA
    if (!frm.doc.delivery_date && frm.doc.transaction_date) {
        let default_delivery = frappe.datetime.add_days(frm.doc.transaction_date, 7);
        frm.doc.delivery_date = default_delivery;
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

    // ✅ CAMPOS OBRIGATÓRIOS PARA ENCOMENDAS PORTUGUESAS
    frm.toggle_reqd('customer', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('transaction_date', true);
    frm.toggle_reqd('delivery_date', true);
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
        message: __('Encomenda portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR TOTAL E ENTREGA
    frm.dashboard.add_indicator(__('Total: €{0}', [(frm.doc.grand_total || 0).toFixed(2)]), 'blue');

    if (frm.doc.delivery_date) {
        let delivery_status = get_delivery_status(frm);
        frm.dashboard.add_indicator(delivery_status.label, delivery_status.color);
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

frappe.ui.form.on('Sales Order Item', {
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
    },

    delivery_date: function(frm, cdt, cdn) {
        // ✅ VALIDAR DATA DE ENTREGA DO ITEM
        let item = locals[cdt][cdn];
        if (item.delivery_date) {
            let item_delivery = frappe.datetime.str_to_obj(item.delivery_date);
            let order_delivery = frappe.datetime.str_to_obj(frm.doc.delivery_date);

            if (item_delivery > order_delivery) {
                frappe.show_alert({
                    message: __('Data de entrega do item não pode ser posterior à data da encomenda'),
                    indicator: 'orange'
                });
            }
        }
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

frappe.ui.form.on('Sales Order', {
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
            "Série portuguesa para encomendas. Formato: EC2025EMPRESA.#### (EC=Encomenda Cliente)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para encomendas.";
    }

    if (frm.fields_dict.delivery_date) {
        frm.fields_dict.delivery_date.df.description =
            "Data de entrega obrigatória para encomendas portuguesas";
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

    // ✅ CTRL+D para validar data de entrega
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+d',
        action: () => {
            if (frm.doc.delivery_date) {
                validate_delivery_date(frm);
            }
        },
        description: __('Validar Data de Entrega'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_sales_order(frm);
            }
        },
        description: __('Imprimir Encomenda Portuguesa'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar encomenda
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.docstatus === 1) {
                analyze_sales_order(frm);
            }
        },
        description: __('Analisar Encomenda'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+U para atualizar prazo
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+u',
        action: () => {
            if (frm.doc.docstatus === 1 && get_delivery_status(frm).overdue) {
                update_delivery_date(frm);
            }
        },
        description: __('Atualizar Prazo de Entrega'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+I para criar fatura
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+i',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
                create_sales_invoice_from_sales_order(frm);
            }
        },
        description: __('Criar Fatura'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+N para criar guia de remessa
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+n',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
                create_delivery_note_from_sales_order(frm);
            }
        },
        description: __('Criar Guia de Remessa'),
        ignore_inputs: true,
        page: frm.page
    });
}

// validate_sales_order_compliance / show_compliance_report removidas
// (2026-08-30): codigo morto (sem nenhum caller) que gerava o mesmo
// relatorio "Série portuguesa não configurada / Não conforme" que ja
// removemos de outros doctypes fora do ambito fiscal - ver stock_entry.js.

// ========== FUNÇÕES DE RELATÓRIOS ==========

function generate_sales_order_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo da encomenda
     */

    let tax_info = calculate_tax_breakdown(frm);
    let customer_nif = get_customer_nif(frm);
    let delivery_status = get_delivery_status(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo da Encomenda'),
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
        <div class="sales-order-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Encomenda</h3>
                <p><strong>Encomenda:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.transaction_date)}</p>
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
                        <tr><td><strong>Data Entrega:</strong></td><td>${frm.doc.delivery_date ? frappe.datetime.str_to_user(frm.doc.delivery_date) : 'N/A'}</td></tr>
                        <tr><td><strong>Status Entrega:</strong></td><td style="color: ${delivery_status.color === 'green' ? 'green' : delivery_status.color === 'orange' ? 'orange' : 'red'}">${delivery_status.label}</td></tr>
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

            <h5>Itens da Encomenda (${frm.doc.items ? frm.doc.items.length : 0})</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Item</th><th>Qtd</th><th style="text-align: right;">Preço Unit.</th><th style="text-align: right;">Total</th><th>Entrega</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let item_delivery = item.delivery_date ? frappe.datetime.str_to_user(item.delivery_date) : 'Conforme encomenda';
            html += `
                <tr>
                    <td>${item.item_name || item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td style="text-align: right;">€${(item.rate || 0).toFixed(2)}</td>
                    <td style="text-align: right;">€${(item.amount || 0).toFixed(2)}</td>
                    <td>${item_delivery}</td>
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
                <p><strong>Status da Encomenda:</strong> ${frm.doc.status}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Sales Order JS loaded - Version 2.0.0');
