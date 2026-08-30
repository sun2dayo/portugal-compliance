// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Sales Invoice JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (FT2025DSY em vez de FT-2025-DSY)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e at_webservice.py
 * ✅ CORREÇÃO: Campo Customer obrigatório e query funcionando
 * ✅ Auto-seleção de séries portuguesas comunicadas (FT)
 * ✅ Geração automática de ATCUD para faturas de venda
 * ✅ Validação de compliance português para vendas
 * ✅ Interface otimizada para faturas de venda portuguesas
 */

frappe.ui.form.on('Sales Invoice', {
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

        // ✅ CONFIGURAR VALIDAÇÕES FISCAIS
        setup_fiscal_validations(frm);
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

            // ✅ RECONFIGURAR CUSTOMER COMO OBRIGATÓRIO
            if (is_portuguese_company(frm)) {
                frm.toggle_reqd('customer', true);
            }
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

    // ========== EVENTOS DE CUSTOMER ==========
    customer: function(frm) {
        if (frm.doc.customer) {
            // ✅ VALIDAR NIF DO CLIENTE
            validate_customer_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_customer_tax_info(frm);

            // ✅ CONFIGURAR IMPOSTOS AUTOMÁTICOS
            setup_automatic_taxes(frm);

            // ✅ VALIDAR SELEÇÃO DO CUSTOMER
            validate_customer_selection(frm);
        }
        // ✅ ATUALIZAR BADGE DE NIF - limpa a cache (get_customer_nif
        // nunca a invalidava sozinha, ficava presa ao cliente anterior)
        frm._customer_nif = undefined;
        add_customer_nif_badge(frm);
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_sales_invoice(frm);
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
     * ✅ CORRIGIDO: Configurar filtros específicos para Portugal
     * Baseado na sua experiência com programação.teste_no_console[3]
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

    // ✅ FILTRO PARA CLIENTES ATIVOS COM QUERY CORRETA
    frm.set_query("customer", function() {
        return {
            query: "portugal_compliance.queries.customer.customer_query",
            filters: {
                disabled: 0,
                company: frm.doc.company
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para faturas de venda";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para faturas de venda (FT2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPO CUSTOMER COMO OBRIGATÓRIO
    if (frm.fields_dict.customer) {
        frm.fields_dict.customer.df.description = "Cliente obrigatório para empresas portuguesas";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE TOTAIS
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

    // ✅ EVENTO PARA CÁLCULO DE IMPOSTOS
    $(frm.wrapper).on('taxes_updated', function() {
        validate_portuguese_taxes(frm);
    });
}

function setup_customer_validations(frm) {
    /**
     * ✅ NOVA: Configurar validações específicas do customer
     * Baseado na sua experiência com programação.js[5]
     */

    // ✅ VALIDAÇÃO QUANDO CUSTOMER MUDA
    if (frm.fields_dict.customer) {
        frm.fields_dict.customer.$input.on('change', function() {
            setTimeout(() => {
                if (frm.doc.customer) {
                    validate_customer_selection(frm);
                }
            }, 100);
        });
    }
}

function validate_customer_selection(frm) {
    /**
     * ✅ NOVA: Validar seleção do customer
     */

    if (!frm.doc.customer) {
        frappe.show_alert({
            message: __('Cliente é obrigatório para empresas portuguesas'),
            indicator: 'red'
        });
        return;
    }

    // ✅ VERIFICAR SE CUSTOMER EXISTE E ESTÁ ATIVO
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: ['disabled', 'customer_name', 'tax_id']
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.disabled) {
                    frappe.msgprint({
                        title: __('Cliente Inativo'),
                        message: __('Cliente {0} está inativo', [frm.doc.customer]),
                        indicator: 'red'
                    });
                    frm.set_value('customer', '');
                } else {
                    frappe.show_alert({
                        message: __('Cliente válido: {0}', [r.message.customer_name]),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_portuguese_interface(frm) {
    /**
     * ✅ CORRIGIDO: Configurar interface específica para Portugal
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
     * Configurar layout específico para faturas de venda portuguesas
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }

    // ✅ NIF do cliente - pequeno badge junto ao campo Customer
    // (2026-08-30): substitui os antigos cartões "Informações de
    // Compliance Português" e "Informações Fiscais" (removidos) - quase
    // todos os seus campos (ATCUD, Série, Cliente, datas, totais) já
    // eram nativamente visíveis no formulário; o NIF do cliente era a
    // única informação real que não estava visível em mais lado nenhum.
    add_customer_nif_badge(frm);
}

function add_customer_nif_badge(frm) {
    /**
     * Pequeno badge com o NIF do cliente, junto ao campo Customer.
     */
    $(frm.fields_dict.customer.wrapper).find('.customer-nif-badge').remove();
    if (frm.doc.__islocal || !frm.doc.customer) return;

    let nif = get_customer_nif(frm);
    let badge_html = `<div class="customer-nif-badge text-muted small" style="margin-top: 4px;">
        <strong>NIF:</strong> ${nif || 'Não definido'}
    </div>`;
    $(frm.fields_dict.customer.wrapper).append(badge_html);
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

    if (!frm.doc.customer) {
        return {
            label: 'Cliente Obrigatório',
            color: 'red',
            description: 'Cliente é obrigatório para empresas portuguesas'
        };
    }

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

    // ✅ VERIFICAR IMPOSTOS
    if (!has_valid_portuguese_taxes(frm)) {
        return {
            label: 'Impostos Inválidos',
            color: 'orange',
            description: 'Verifique configuração de impostos portugueses'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Fatura de venda conforme legislação portuguesa'
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

    // ✅ BOTÃO PARA VALIDAR IMPOSTOS
    if (frm.doc.taxes && frm.doc.taxes.length > 0) {
        frm.add_custom_button(__('Validar Impostos PT'), function() {
            validate_and_show_taxes(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA IMPRIMIR FATURA PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Fatura PT'), function() {
            print_portuguese_sales_invoice(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF CLIENTE
    if (frm.doc.customer) {
        frm.add_custom_button(__('Validar NIF Cliente'), function() {
            validate_customer_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA ANALISAR FATURA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Fatura'), function() {
            analyze_sales_invoice(frm);
        }, __('Análise'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA FATURAS DE VENDA (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.api.series_api.get_available_portugal_series_certified',
        args: {
            doctype: 'Sales Invoice',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS FT (formato SEM HÍFENS: FT2025DSY)
                let ft_series = r.message.series.filter(s => s.prefix.startsWith('FT'));
                let communicated_series = ft_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : ft_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE FT
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série FT comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série FT não comunicada selecionada. Comunique à AT antes de submeter.'),
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
            message: __('Para compliance português, use séries no formato FT2025EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE FATURA DE VENDA (formato SEM HÍFENS)
    let prefix = frm.doc.naming_series.replace('.####', '');
    let doc_code = prefix.substring(0, 2); // Primeiros 2 caracteres: FT

    if (!['FT', 'FS', 'FR', 'NC', 'ND'].includes(doc_code)) {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para Sales Invoice, use séries FT (Fatura), FS (Fatura Simplificada), NC (Nota Crédito), ND (Nota Débito)'),
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
        message = __('Série FT comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série FT não comunicada à AT. Comunique antes de submeter faturas.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_sales_invoice(frm) {
    /**
     * Validações específicas para faturas de venda portuguesas
     */

    let errors = [];

    // ✅ VALIDAR CUSTOMER OBRIGATÓRIO
    if (!frm.doc.customer) {
        errors.push(__('Cliente é obrigatório para empresas portuguesas'));
    }

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato FT2025EMPRESA.####)'));
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
        // sempre false neste modo e bloqueava faturas com IVA genuino e
        // corretamente calculado.
        let description = (tax.description || tax.account_head || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            has_iva = true;
            iva_rates.push(tax.rate);
        }
    });

    if (!has_iva) {
        errors.push(__('Fatura deve ter IVA configurado'));
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

function validate_customer_nif(frm) {
    /**
     * ✅ CORRIGIDO: Validar NIF do cliente
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
     * ✅ CORRIGIDO: Validar formato do NIF português
     */

    if (!nif) return;

    frappe.call({
        // 2026-08-30: era document_hooks.validate_portuguese_nif, que
        // nunca existiu (nem como método de classe nem como função de
        // módulo) - erro "has no attribute" em toda a consola sempre
        // que o NIF do cliente mudava. A função real e whitelisted é
        // jinja_methods.validate_portuguese_nif(nif), já usada
        // corretamente com esta mesma assinatura em customer.js,
        // supplier.js, company.js e em todos os outros doctype_js
        // (purchase_invoice, pos_invoice, delivery_note, quotation,
        // sales_order, purchase_order, purchase_receipt,
        // payment_entry) - só este ficheiro tinha o caminho errado.
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

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão
     */

    return new Promise((resolve, reject) => {
        let validations = [];

        // ✅ VALIDAR CUSTOMER OBRIGATÓRIO
        if (!frm.doc.customer) {
            validations.push(__('Cliente é obrigatório para faturas de venda portuguesas'));
        }

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
                        validations.push(__('Série FT deve estar comunicada à AT antes da submissão'));
                    }

                    // ✅ VALIDAR IMPOSTOS OBRIGATÓRIOS
                    if (!has_valid_portuguese_taxes(frm)) {
                        validations.push(__('Configure impostos portugueses válidos'));
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

// ========== FUNÇÕES FISCAIS ==========

function setup_fiscal_validations(frm) {
    /**
     * Configurar validações específicas fiscais
     */

    // ✅ VALIDAR IMPOSTOS QUANDO MUDAM
    if (frm.fields_dict.taxes && frm.fields_dict.taxes.grid) {
        // Guarda adicional em .df (2026-08-24): get_field() pode devolver
        // um wrapper cujo .df ainda nao esta preenchido se o grid ainda
        // nao renderizou por completo neste refresh - sem isto, atribuir
        // .onchange rebentava com "Cannot set properties of undefined"
        // (apanhado ao vivo, console sujo em todos os forms fiscais).
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
            message: __('Adicione IVA português à fatura'),
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

function has_valid_portuguese_taxes(frm) {
    /**
     * Verificar se tem impostos portugueses válidos
     */

    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        return false;
    }

    let has_iva = false;
    let valid_rates = [0, 6, 13, 23];

    frm.doc.taxes.forEach(function(tax) {
        let description = (tax.description || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            has_iva = true;
            if (!valid_rates.includes(tax.rate)) {
                return false;
            }
        }
    });

    return has_iva;
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

function setup_automatic_taxes(frm) {
    /**
     * Configurar impostos automáticos baseado no cliente
     */

    if (!frm.doc.customer) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: ['tax_category', 'tax_id']
        },
        callback: function(r) {
            if (r.message && r.message.tax_category) {
                // Sugerir template de impostos baseado na categoria
                suggest_tax_template(frm, r.message.tax_category);
            }
        }
    });
}

function suggest_tax_template(frm, tax_category) {
    /**
     * Sugerir template de impostos
     */

    if (frm.doc.taxes_and_charges) return; // Já tem template

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Sales Taxes and Charges Template',
            filters: {
                company: frm.doc.company,
                disabled: 0
            },
            fields: ['name', 'title'],
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frappe.show_alert({
                    message: __('Template de impostos sugerido: {0}', [r.message[0].title]),
                    indicator: 'blue'
                });
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
        title: __('Status da Série FT'),
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
                <tr><td><strong>Tipo:</strong></td><td>Fatura de Venda</td></tr>
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

function validate_and_show_taxes(frm) {
    /**
     * Validar e mostrar impostos
     */

    let tax_info = calculate_tax_breakdown(frm);

    let html = `
        <table class="table table-bordered">
            <tr><td><strong>Total sem IVA:</strong></td><td>€${(frm.doc.net_total || 0).toFixed(2)}</td></tr>
            <tr><td><strong>Total IVA:</strong></td><td>€${tax_info.total_tax.toFixed(2)}</td></tr>
            <tr><td><strong>Total com IVA:</strong></td><td>€${(frm.doc.grand_total || 0).toFixed(2)}</td></tr>
        </table>
        <h6>Breakdown IVA:</h6>
        <table class="table table-striped">
    `;

    Object.keys(tax_info.iva_breakdown).forEach(function(rate) {
        html += `
            <tr>
                <td>IVA ${rate}%</td>
                <td>€${tax_info.iva_breakdown[rate].toFixed(2)}</td>
            </tr>
        `;
    });

    html += '</table>';

    frappe.msgprint({
        title: __('Análise de Impostos Portugueses'),
        message: html,
        indicator: 'blue'
    });
}

function analyze_sales_invoice(frm) {
    /**
     * Analisar fatura de venda completa
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise da Fatura de Venda'),
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

    let html = `
        <div class="invoice-analysis">
            <h5>Análise da Fatura: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Tipo:</strong></td><td>Fatura de Venda</td></tr>
                        <tr><td><strong>Data:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.posting_date)}</td></tr>
                        <tr><td><strong>Cliente:</strong></td><td>${frm.doc.customer_name}</td></tr>
                        <tr><td><strong>NIF Cliente:</strong></td><td>${customer_nif || 'Não definido'}</td></tr>
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
                        <tr><td><strong>Vencimento:</strong></td><td>${frm.doc.due_date ? frappe.datetime.str_to_user(frm.doc.due_date) : 'N/A'}</td></tr>
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

function print_portuguese_sales_invoice(frm) {
    /**
     * Imprimir fatura com formato português
     */

    frappe.route_options = {
        "format": "Factura PT"
    };

    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

// ========== FUNÇÕES AUXILIARES ==========

function is_portuguese_company(frm) {
    /**
     * ✅ CORRIGIDO: Verificar se empresa é portuguesa com compliance ativo
     * Baseado na sua experiência com programação.autenticação[4]
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
     * ✅ CORRIGIDO: Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA FATURAS DE VENDA PORTUGUESAS
    frm.toggle_reqd('customer', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('posting_date', true);
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
    frm.meta.default_print_format = "Factura PT";
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
        message: __('Fatura de venda portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR TOTAL
    frm.dashboard.add_indicator(__('Total: €{0}', [(frm.doc.grand_total || 0).toFixed(2)]), 'blue');
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

// ========== LIMPEZA DE CAMPOS FISCAIS HERDADOS (NOTA DE CRÉDITO) ==========

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        // ✅ REFORÇO CLIENT-SIDE (defesa em profundidade): atcud_code/
        // qr_code_image já têm no_copy=1 (2026-08-30), o que impede
        // frappe.model.mapper (usado por make_return_doc, o botão
        // "Return / Credit Note") de copiar estes campos da fatura
        // original para o rascunho novo. Mas no_copy só protege esse
        // caminho especifico - este handler e uma rede de segurança
        // adicional, para o utilizador nunca ver, nem por um instante,
        // um ATCUD/QR Code herdado da fatura original numa Nota de
        // Crédito nova.
        clear_inherited_fiscal_fields_on_return(frm);
    }
});

function clear_inherited_fiscal_fields_on_return(frm) {
    if (frm.is_new() && frm.doc.is_return) {
        ['atcud_code', 'qr_code', 'qr_code_image'].forEach(function(fieldname) {
            if (frm.doc[fieldname]) {
                frm.set_value(fieldname, '');
            }
        });
    }
}

// ========== EVENTOS DE ITEMS ==========

frappe.ui.form.on('Sales Invoice Item', {
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
    }
});

// ========== CONTINUAÇÃO DO ARQUIVO PURCHASE_INVOICE.JS ==========

// ========== FUNÇÕES DE EXPORTAÇÃO E RELATÓRIOS (CONTINUAÇÃO) ==========

function export_purchase_data_excel(frm) {
    /**
     * ✅ NOVA: Exportar dados da fatura para Excel
     */

    if (!frm.doc.docstatus === 1) {
        frappe.msgprint(__('Fatura deve estar submetida para exportar'));
        return;
    }

    let tax_info = calculate_tax_breakdown(frm);
    let supplier_nif = get_supplier_nif(frm);

    // ✅ PREPARAR DADOS PARA EXCEL
    let excel_data = [
        ['Relatório de Fatura de Compra'],
        [''],
        ['Dados Gerais'],
        ['Fatura', frm.doc.name],
        ['Data', frappe.datetime.str_to_user(frm.doc.posting_date)],
        ['ATCUD', frm.doc.atcud_code || 'N/A'],
        ['Série', frm.doc.naming_series || 'N/A'],
        [''],
        ['Fornecedor'],
        ['Nome', frm.doc.supplier_name],
        ['NIF', supplier_nif || 'N/A'],
        ['Fatura Nº', frm.doc.bill_no || 'N/A'],
        ['Data Fatura', frm.doc.bill_date ? frappe.datetime.str_to_user(frm.doc.bill_date) : 'N/A'],
        [''],
        ['Valores'],
        ['Total sem IVA', (frm.doc.net_total || 0).toFixed(2)],
        ['Total IVA', tax_info.total_tax.toFixed(2)],
        ['Total com IVA', (frm.doc.grand_total || 0).toFixed(2)],
        [''],
        ['Breakdown IVA'],
        ['Taxa', 'Valor IVA']
    ];

    // ✅ ADICIONAR BREAKDOWN IVA
    Object.keys(tax_info.iva_breakdown).forEach(function(rate) {
        excel_data.push([`IVA ${rate}%`, tax_info.iva_breakdown[rate].toFixed(2)]);
    });

    excel_data.push(['']);
    excel_data.push(['Itens']);
    excel_data.push(['Item', 'Quantidade', 'Preço Unitário', 'Total']);

    // ✅ ADICIONAR ITENS
    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            excel_data.push([
                item.item_name || item.item_code,
                item.qty || 0,
                (item.rate || 0).toFixed(2),
                (item.amount || 0).toFixed(2)
            ]);
        });
    }

    // ✅ CONVERTER PARA CSV
    let csv_content = excel_data.map(row => row.join(',')).join('\n');

    // ✅ DOWNLOAD
    let blob = new Blob([csv_content], { type: 'text/csv' });
    let url = URL.createObjectURL(blob);
    let link = document.createElement('a');
    link.href = url;
    link.download = `fatura_compra_${frm.doc.name}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    frappe.show_alert({
        message: __('Dados exportados para Excel: fatura_compra_{0}.csv', [frm.doc.name]),
        indicator: 'green'
    });
}

// ========== FUNÇÕES DE INTEGRAÇÃO COM CONTABILIDADE ==========

function generate_accounting_entries_preview(frm) {
    /**
     * ✅ NOVA: Gerar preview dos lançamentos contabilísticos
     */

    if (!frm.doc.docstatus === 1) {
        frappe.msgprint(__('Fatura deve estar submetida'));
        return;
    }

    let tax_info = calculate_tax_breakdown(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Preview Lançamentos Contabilísticos'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'accounting_preview'
            }
        ]
    });

    let html = `
        <div class="accounting-preview">
            <h5>Lançamentos Contabilísticos - ${frm.doc.name}</h5>

            <table class="table table-bordered">
                <thead>
                    <tr><th>Conta</th><th>Descrição</th><th>Débito</th><th>Crédito</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Compras</td>
                        <td>Fatura de compra ${frm.doc.name}</td>
                        <td>€${(frm.doc.net_total || 0).toFixed(2)}</td>
                        <td>-</td>
                    </tr>
    `;

    // ✅ ADICIONAR LANÇAMENTOS DE IVA
    Object.keys(tax_info.iva_breakdown).forEach(function(rate) {
        if (parseFloat(rate) > 0) {
            html += `
                <tr>
                    <td>IVA Dedutível ${rate}%</td>
                    <td>IVA da fatura ${frm.doc.name}</td>
                    <td>€${tax_info.iva_breakdown[rate].toFixed(2)}</td>
                    <td>-</td>
                </tr>
            `;
        }
    });

    html += `
                    <tr style="font-weight: bold;">
                        <td>Fornecedores</td>
                        <td>A pagar - ${frm.doc.supplier_name}</td>
                        <td>-</td>
                        <td>€${(frm.doc.grand_total || 0).toFixed(2)}</td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr style="font-weight: bold; background-color: #f8f9fa;">
                        <td colspan="2">TOTAIS</td>
                        <td>€${(frm.doc.grand_total || 0).toFixed(2)}</td>
                        <td>€${(frm.doc.grand_total || 0).toFixed(2)}</td>
                    </tr>
                </tfoot>
            </table>

            <div class="mt-3">
                <small class="text-muted">
                    <strong>Nota:</strong> Este é um preview indicativo. Os lançamentos reais podem variar conforme o plano de contas.
                </small>
            </div>
        </div>
    `;

    dialog.fields_dict.accounting_preview.$wrapper.html(html);
    dialog.show();
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA (CONTINUAÇÃO) ==========

function validate_purchase_invoice_against_po(frm) {
    /**
     * ✅ NOVA: Validar fatura contra ordem de compra
     */

    if (!frm.doc.items || frm.doc.items.length === 0) {
        return;
    }

    // ✅ VERIFICAR SE HÁ PURCHASE ORDERS REFERENCIADAS
    let po_references = [];
    frm.doc.items.forEach(function(item) {
        if (item.purchase_order && !po_references.includes(item.purchase_order)) {
            po_references.push(item.purchase_order);
        }
    });

    if (po_references.length === 0) {
        frappe.show_alert({
            message: __('Nenhuma ordem de compra referenciada'),
            indicator: 'orange'
        });
        return;
    }

    // ✅ VALIDAR CONTRA CADA PO
    po_references.forEach(function(po_name) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Purchase Order',
                name: po_name
            },
            callback: function(r) {
                if (r.message) {
                    validate_po_compliance(frm, r.message);
                }
            }
        });
    });
}

function validate_po_compliance(frm, po_doc) {
    /**
     * ✅ NOVA: Validar compliance com ordem de compra
     */

    let issues = [];

    // ✅ VERIFICAR FORNECEDOR
    if (frm.doc.supplier !== po_doc.supplier) {
        issues.push(`Fornecedor diferente da PO ${po_doc.name}`);
    }

    // ✅ VERIFICAR VALORES
    let po_total = po_doc.grand_total || 0;
    let invoice_total = frm.doc.grand_total || 0;
    let variance = Math.abs(po_total - invoice_total);
    let variance_percent = (variance / po_total) * 100;

    if (variance_percent > 5) { // Tolerância de 5%
        issues.push(`Variação de valor significativa com PO ${po_doc.name}: ${variance_percent.toFixed(1)}%`);
    }

    // ✅ MOSTRAR ISSUES SE HOUVER
    if (issues.length > 0) {
        frappe.msgprint({
            title: __('Validação contra Ordem de Compra'),
            message: issues.join('<br>'),
            indicator: 'orange'
        });
    } else {
        frappe.show_alert({
            message: __('Fatura conforme com PO {0}', [po_doc.name]),
            indicator: 'green'
        });
    }
}

// ========== FUNÇÕES DE WORKFLOW ==========

function setup_purchase_workflow(frm) {
    /**
     * ✅ NOVA: Configurar workflow específico para compras portuguesas
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ ADICIONAR ESTADOS DE WORKFLOW
    if (frm.doc.docstatus === 0) {
        frm.add_custom_button(__('Validar Compliance'), function() {
            show_compliance_report(frm);
        }, __('Workflow'));
    }

    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Gerar Lançamentos'), function() {
            generate_accounting_entries_preview(frm);
        }, __('Workflow'));

        frm.add_custom_button(__('Exportar SAF-T'), function() {
            export_saft_data(frm);
        }, __('Workflow'));

        frm.add_custom_button(__('Relatório Completo'), function() {
            generate_purchase_summary_report(frm);
        }, __('Workflow'));
    }
}

// ========== FUNÇÕES DE NOTIFICAÇÕES ==========

function setup_purchase_notifications(frm) {
    /**
     * ✅ NOVA: Configurar notificações específicas
     */

    // ✅ NOTIFICAÇÃO DE VENCIMENTO
    if (frm.doc.due_date && frm.doc.docstatus === 1) {
        let due_date = frappe.datetime.str_to_obj(frm.doc.due_date);
        let today = new Date();
        let days_to_due = Math.ceil((due_date - today) / (1000 * 60 * 60 * 24));

        if (days_to_due <= 7 && days_to_due > 0) {
            frm.dashboard.add_indicator(
                __('Vence em {0} dias', [days_to_due]),
                'orange'
            );
        } else if (days_to_due <= 0) {
            frm.dashboard.add_indicator(
                __('Vencida há {0} dias', [Math.abs(days_to_due)]),
                'red'
            );
        }
    }

    // ✅ NOTIFICAÇÃO DE SÉRIE NÃO COMUNICADA
    if (frm.doc.naming_series && !frm.doc.__islocal) {
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
                    frm.dashboard.add_indicator(
                        __('Série FC não comunicada à AT'),
                        'red'
                    );
                }
            }
        });
    }
}

// ========== FUNÇÕES DE PERFORMANCE ==========

function optimize_form_performance(frm) {
    /**
     * ✅ NOVA: Otimizar performance do formulário
     */

    // ✅ CACHE PARA DADOS DO FORNECEDOR
    if (!frm._supplier_cache) {
        frm._supplier_cache = {};
    }

    // ✅ LAZY LOADING PARA SEÇÕES PESADAS
    if (!frm.doc.__islocal && !frm._heavy_sections_loaded) {
        setTimeout(() => {
            setup_purchase_workflow(frm);
            setup_purchase_notifications(frm);
            frm._heavy_sections_loaded = true;
        }, 500);
    }
}

// ========== EVENTOS DE CLEANUP E FINALIZAÇÃO ==========

frappe.ui.form.on('Purchase Invoice', {
    before_unload: function(frm) {
        // ✅ CLEANUP ANTES DE SAIR DO FORMULÁRIO
        if (frm._change_observers) {
            frm._change_observers.forEach(observer => {
                if (observer.disconnect) observer.disconnect();
            });
        }

        // ✅ LIMPAR TIMERS
        if (frm._notification_timer) {
            clearTimeout(frm._notification_timer);
        }

        // ✅ LIMPAR CACHE
        delete frm._supplier_cache;
        delete frm._company_settings;
        delete frm._is_portuguese_company;
    }
});

// ========== FUNÇÕES DE INTEGRAÇÃO COM OUTROS MÓDULOS ==========

function integrate_with_asset_management(frm) {
    /**
     * ✅ NOVA: Integração com gestão de ativos
     */

    if (!frm.doc.items) return;

    let asset_items = frm.doc.items.filter(item =>
        item.item_code && item.item_code.toLowerCase().includes('ativo')
    );

    if (asset_items.length > 0) {
        frm.add_custom_button(__('Criar Ativos'), function() {
            create_assets_from_invoice(frm, asset_items);
        }, __('Gestão de Ativos'));
    }
}

function create_assets_from_invoice(frm, asset_items) {
    /**
     * ✅ NOVA: Criar ativos a partir da fatura
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Criar Ativos'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'asset_info',
                options: `<p>Foram identificados ${asset_items.length} itens que podem ser ativos.</p>`
            },
            {
                fieldtype: 'Check',
                fieldname: 'create_assets',
                label: __('Criar ativos automaticamente'),
                default: 1
            }
        ],
        primary_action_label: __('Criar'),
        primary_action: function() {
            if (dialog.get_value('create_assets')) {
                asset_items.forEach(item => {
                    frappe.call({
                        method: 'erpnext.assets.doctype.asset.asset.make_asset_from_purchase_invoice',
                        args: {
                            purchase_invoice: frm.doc.name,
                            item_code: item.item_code
                        },
                        callback: function(r) {
                            if (r.message) {
                                frappe.show_alert({
                                    message: __('Ativo criado: {0}', [r.message]),
                                    indicator: 'green'
                                });
                            }
                        }
                    });
                });
            }
            dialog.hide();
        }
    });

    dialog.show();
}

// ========== FUNÇÕES DE AUDITORIA ==========

function setup_audit_trail(frm) {
    /**
     * ✅ NOVA: Configurar trilha de auditoria
     */

    if (!frm.doc.docstatus === 1) return;

    frm.add_custom_button(__('Trilha de Auditoria'), function() {
        show_audit_trail(frm);
    }, __('Auditoria'));
}

function show_audit_trail(frm) {
    /**
     * ✅ NOVA: Mostrar trilha de auditoria
     */

    frappe.call({
        method: 'frappe.desk.form.load.get_docinfo',
        args: {
            doctype: frm.doc.doctype,
            name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                display_audit_info(frm, r.message);
            }
        }
    });
}

function display_audit_info(frm, docinfo) {
    /**
     * ✅ NOVA: Exibir informações de auditoria
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Trilha de Auditoria - {0}', [frm.doc.name]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'audit_content'
            }
        ]
    });

    let html = `
        <div class="audit-trail">
            <h5>Histórico de Alterações</h5>

            <table class="table table-striped">
                <thead>
                    <tr><th>Data/Hora</th><th>Usuário</th><th>Ação</th><th>Detalhes</th></tr>
                </thead>
                <tbody>
    `;

    // ✅ ADICIONAR VERSÕES
    if (docinfo.versions) {
        docinfo.versions.forEach(version => {
            html += `
                <tr>
                    <td>${frappe.datetime.str_to_user(version.creation)}</td>
                    <td>${version.owner}</td>
                    <td>Alteração</td>
                    <td>Versão ${version.name}</td>
                </tr>
            `;
        });
    }

    // ✅ ADICIONAR COMENTÁRIOS
    if (docinfo.comments) {
        docinfo.comments.forEach(comment => {
            html += `
                <tr>
                    <td>${frappe.datetime.str_to_user(comment.creation)}</td>
                    <td>${comment.owner}</td>
                    <td>Comentário</td>
                    <td>${comment.content}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.audit_content.$wrapper.html(html);
    dialog.show();
}

// ========== INICIALIZAÇÃO FINAL ==========

$(document).ready(function() {
    // ✅ CONFIGURAÇÕES GLOBAIS PARA PURCHASE INVOICE
    if (window.location.pathname.includes('Purchase Invoice')) {
        // ✅ ADICIONAR ESTILOS CSS ESPECÍFICOS
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .portugal-compliance-form .control-label {
                    font-weight: 600;
                }
                .portugal-compliance-info {
                    animation: fadeIn 0.3s ease-in;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .purchase-invoice-pt .form-section {
                    border-left: 3px solid #ff9800;
                }
            `)
            .appendTo('head');
    }
});

// ========== CONSOLE LOG FINAL ==========
console.log('Portugal Compliance Purchase Invoice JS - COMPLETE VERSION 2.0.0 - All Functions Loaded');
console.log('Features: ATCUD Generation, Tax Validation, Compliance Checking, Reporting, SAF-T Export');
console.log('Format: ERPNext Native (WITHOUT HYPHENS) - FC2025EMPRESA.####');

