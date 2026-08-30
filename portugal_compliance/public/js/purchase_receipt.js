// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Purchase Receipt JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (GR2025NDX em vez de GR-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (GR)
 * ✅ Geração automática de ATCUD para guias de receção
 * ✅ Validação de compliance português para receção
 * ✅ Interface otimizada para guias de receção portuguesas
 */

frappe.ui.form.on('Purchase Receipt', {
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

            // show_compliance_status removida (2026-08-30) - ver nota
            // em stock_entry.js.

            // ✅ ADICIONAR BOTÕES PERSONALIZADOS
            add_custom_buttons(frm);

            // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
            setup_mandatory_fields(frm);
        }

        // ✅ ATUALIZAR DISPLAY DE ATCUD
        update_atcud_display(frm);

        // ✅ CONFIGURAR PRINT FORMATS
        setup_print_formats(frm);

        // ✅ CONFIGURAR VALIDAÇÕES DE RECEÇÃO
        setup_receipt_validations(frm);
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
            // nota em validate_portuguese_purchase_receipt/stock_entry.js.

            // ✅ VERIFICAR STATUS DE COMUNICAÇÃO
            check_series_communication_status(frm);

            // ✅ MOSTRAR INFORMAÇÕES DA SÉRIE
            show_series_info(frm);
        }
    },

    // ========== EVENTOS DE SUPPLIER ==========
    supplier: function(frm) {
        if (frm.doc.supplier) {
            // ✅ VALIDAR NIF DO FORNECEDOR
            validate_supplier_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_supplier_tax_info(frm);

            // ✅ CARREGAR ENDEREÇO DE FORNECEDOR
            load_supplier_address_info(frm);
        }
    },

    // ========== EVENTOS DE ENDEREÇOS ==========
    supplier_address: function(frm) {
        if (frm.doc.supplier_address) {
            validate_supplier_address(frm);
        }
    },

    shipping_address: function(frm) {
        if (frm.doc.shipping_address) {
            validate_shipping_address(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_purchase_receipt(frm);
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

    // ✅ FILTRO PARA FORNECEDORES PORTUGUESES
    frm.set_query("supplier", function() {
        return {
            filters: {
                "disabled": 0
            }
        };
    });

    // ✅ FILTRO PARA ARMAZÉNS DA EMPRESA
    frm.set_query("set_warehouse", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "disabled": 0,
                "is_group": 0
            }
        };
    });

    // ✅ FILTRO PARA PURCHASE ORDER
    frm.set_query("purchase_order", function() {
        return {
            filters: {
                "supplier": frm.doc.supplier,
                "company": frm.doc.company,
                "docstatus": 1
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para guias de receção";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para guias de receção (GR2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPOS DE RECEÇÃO
    if (frm.fields_dict.lr_no) {
        frm.fields_dict.lr_no.df.label = "Nº Guia de Receção";
        frm.fields_dict.lr_no.df.description = "Número da guia de receção conforme legislação portuguesa";
    }

    // ✅ CONFIGURAR CAMPO BILL NO
    if (frm.fields_dict.bill_no) {
        frm.fields_dict.bill_no.df.description = "Número da fatura do fornecedor (referência externa)";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE QUANTIDADE TOTAL
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

    // ✅ EVENTO PARA CÁLCULO DE TOTAIS
    $(frm.wrapper).on('items_updated', function() {
        calculate_receipt_totals(frm);
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

// add_compliance_section, add_receipt_section, show_compliance_status
// e get_compliance_status removidas (2026-08-30, mesmo achado do
// utilizador ja corrigido em stock_entry.js - ver esse ficheiro para
// o historico completo). Purchase Receipt nunca esteve em
// document_hooks.py::supported_doctypes - os cartoes/banner/indicador
// que geravam assumiam, incorretamente, que este doctype tem
// serie/ATCUD proprios.

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para guias de receção portuguesas
     */

    // ✅ REORGANIZAR CAMPOS PARA COMPLIANCE
    if (frm.fields_dict.atcud_code && frm.fields_dict.naming_series) {
        // Mover ATCUD para próximo da naming series
        frm.fields_dict.atcud_code.df.insert_after = 'naming_series';
        frm.refresh_field('atcud_code');
    }
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para compliance português
     */

    if (frm.doc.__islocal) return;

    // Botões "Gerar ATCUD"/"Verificar Série" removidos (2026-08-30) -
    // ver nota acima/em stock_entry.js.

    // ✅ BOTÃO PARA VALIDAR ENDEREÇOS
    if (frm.doc.supplier) {
        frm.add_custom_button(__('Validar Endereços'), function() {
            validate_all_addresses(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA CALCULAR TOTAIS
    if (frm.doc.items && frm.doc.items.length > 0) {
        frm.add_custom_button(__('Calcular Totais'), function() {
            calculate_and_show_totals(frm);
        }, __('Receção'));
    }

    // ✅ BOTÃO PARA IMPRIMIR GUIA PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Guia GR'), function() {
            print_portuguese_purchase_receipt(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF FORNECEDOR
    if (frm.doc.supplier) {
        frm.add_custom_button(__('Validar NIF Fornecedor'), function() {
            validate_supplier_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA COMPARAR COM PO
    if (frm.doc.purchase_order) {
        frm.add_custom_button(__('Comparar com PO'), function() {
            compare_with_purchase_order(frm);
        }, __('Receção'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA GUIAS DE RECEÇÃO (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.api.series_api.get_available_portugal_series_certified',
        args: {
            doctype: 'Purchase Receipt',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS GR (formato SEM HÍFENS: GR2025NDX)
                let gr_series = r.message.series.filter(s => s.prefix.startsWith('GR'));
                let communicated_series = gr_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : gr_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE GR
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série GR comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série GR não comunicada selecionada. Comunique à AT antes de submeter.'),
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
        message = __('Série GR comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série GR não comunicada à AT. Comunique antes de submeter guias.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_purchase_receipt(frm) {
    /**
     * Validações específicas para guias de receção portuguesas
     */

    let errors = [];

    // Exigencia de naming_series removida (2026-08-30, mesmo achado do
    // utilizador ja corrigido em stock_entry.js - ver esse ficheiro
    // para o historico completo): Purchase Receipt nunca esteve em
    // document_hooks.py::supported_doctypes (documento de rececao de
    // compra, nao emitido a terceiros - Portaria 195/2020 nao se
    // aplica), confirmado "ja era codigo morto" no proprio commit de
    // 2026-08-22 que o excluiu. Esta validacao client-side exigia na
    // mesma um formato de serie que a app nunca chegou a provisionar
    // de verdade para este doctype.

    // ✅ VALIDAR FORNECEDOR
    if (!frm.doc.supplier) {
        errors.push(__('Fornecedor é obrigatório'));
    }

    // ✅ VALIDAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        errors.push(__('Pelo menos um item é obrigatório'));
    }

    // ✅ VALIDAR ARMAZÉM
    if (!frm.doc.set_warehouse) {
        // Verificar se todos os itens têm armazém definido
        let items_without_warehouse = frm.doc.items.filter(item => !item.warehouse);
        if (items_without_warehouse.length > 0) {
            errors.push(__('Defina armazém para todos os itens ou use armazém padrão'));
        }
    }

    // ✅ VALIDAR QUANTIDADES
    let items_with_zero_qty = frm.doc.items.filter(item => !item.qty || item.qty <= 0);
    if (items_with_zero_qty.length > 0) {
        errors.push(__('Todos os itens devem ter quantidade maior que zero'));
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

function validate_supplier_nif(frm) {
    /**
     * ✅ CORRIGIDO: Validar NIF do fornecedor usando jinja_methods.py
     */

    if (!frm.doc.supplier) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Supplier',
            filters: {name: frm.doc.supplier},
            fieldname: 'tax_id'
        },
        callback: function(r) {
            if (r.message && r.message.tax_id) {
                validate_nif_format(frm, r.message.tax_id, 'Fornecedor');
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

function validate_supplier_address(frm) {
    /**
     * Validar endereço do fornecedor
     */

    if (!frm.doc.supplier_address) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.supplier_address},
            fieldname: ['address_line1', 'city', 'pincode', 'country']
        },
        callback: function(r) {
            if (r.message) {
                let address = r.message;
                let errors = [];

                if (!address.address_line1) errors.push('Morada');
                if (!address.city) errors.push('Cidade');
                if (!address.pincode) errors.push('Código Postal');

                if (errors.length > 0) {
                    frappe.show_alert({
                        message: __('Endereço fornecedor incompleto: falta {0}', [errors.join(', ')]),
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Endereço fornecedor válido'),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

function validate_shipping_address(frm) {
    /**
     * Validar endereço de entrega
     */

    if (!frm.doc.shipping_address) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.shipping_address},
            fieldname: ['address_line1', 'city', 'pincode', 'country']
        },
        callback: function(r) {
            if (r.message) {
                let address = r.message;
                let errors = [];

                if (!address.address_line1) errors.push('Morada');
                if (!address.city) errors.push('Cidade');
                if (!address.pincode) errors.push('Código Postal');

                if (errors.length > 0) {
                    frappe.show_alert({
                        message: __('Endereço entrega incompleto: falta {0}', [errors.join(', ')]),
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Endereço entrega válido'),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão.
     *
     * Exigencia de ATCUD/serie comunicada removida (2026-08-30) - ver
     * validate_portuguese_purchase_receipt (mesmo ficheiro) para o
     * historico completo. Purchase Receipt nunca gera ATCUD nem
     * comunica serie (nunca esteve em document_hooks.py::
     * supported_doctypes). Validacao de armazens (generica,
     * nao-fiscal) mantida tal como estava.
     */
    return new Promise((resolve, reject) => {
        let validations = [];

        // ✅ VALIDAR ARMAZÉNS
        let items_without_warehouse = frm.doc.items.filter(item => !item.warehouse);
        if (!frm.doc.set_warehouse && items_without_warehouse.length > 0) {
            validations.push(__('Todos os itens devem ter armazém definido'));
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

// ========== FUNÇÕES DE RECEÇÃO ==========

function setup_receipt_validations(frm) {
    /**
     * Configurar validações específicas de receção
     */

    // ✅ VALIDAR QUANTIDADE DOS ITENS
    if (frm.fields_dict.items && frm.fields_dict.items.grid) {
        // Guarda adicional em .df (2026-08-24): get_field() pode devolver
        // um wrapper cujo .df ainda nao esta preenchido se o grid ainda
        // nao renderizou por completo neste refresh - sem isto, atribuir
        // .onchange rebentava com "Cannot set properties of undefined".
        var qty_field = frm.fields_dict.items.grid.get_field('qty');
        if (qty_field && qty_field.df) {
            qty_field.df.onchange = function() {
                calculate_receipt_totals(frm);
            };
        }

        // ✅ VALIDAR RATE
        var rate_field = frm.fields_dict.items.grid.get_field('rate');
        if (rate_field && rate_field.df) {
            rate_field.df.onchange = function() {
                calculate_receipt_totals(frm);
            };
        }
    }
}

function calculate_receipt_totals(frm) {
    /**
     * Calcular totais da guia de receção
     */

    let total_qty = 0;
    let total_amount = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let qty = item.qty || 0;
            let rate = item.rate || 0;
            total_qty += qty;
            total_amount += (qty * rate);
        });
    }

    return {
        total_qty: total_qty,
        total_amount: total_amount
    };
}

function calculate_total_qty(frm) {
    /**
     * Calcular quantidade total da guia
     */

    let total_qty = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            total_qty += (item.qty || 0);
        });
    }

    return total_qty;
}

function calculate_and_show_totals(frm) {
    /**
     * Calcular e mostrar totais
     */

    let totals = calculate_receipt_totals(frm);

    frappe.msgprint({
        title: __('Informações de Receção'),
        message: `
            <table class="table table-bordered">
                <tr><td><strong>Quantidade Total:</strong></td><td>${totals.total_qty}</td></tr>
                <tr><td><strong>Valor Total Itens:</strong></td><td>€${totals.total_amount.toFixed(2)}</td></tr>
                <tr><td><strong>Grand Total:</strong></td><td>€${(frm.doc.grand_total || 0).toFixed(2)}</td></tr>
                <tr><td><strong>Nº Itens:</strong></td><td>${frm.doc.items ? frm.doc.items.length : 0}</td></tr>
            </table>
        `,
        indicator: 'blue'
    });
}

// ========== FUNÇÕES DE AÇÕES ==========


function validate_all_addresses(frm) {
    /**
     * Validar todos os endereços
     */

    let addresses_to_check = [];

    if (frm.doc.supplier_address) {
        addresses_to_check.push({name: frm.doc.supplier_address, type: 'Fornecedor'});
    }

    if (frm.doc.shipping_address) {
        addresses_to_check.push({name: frm.doc.shipping_address, type: 'Entrega'});
    }

    if (addresses_to_check.length === 0) {
        frappe.msgprint(__('Nenhum endereço para validar'));
        return;
    }

    addresses_to_check.forEach(function(addr) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Address',
                filters: {name: addr.name},
                fieldname: ['address_line1', 'city', 'pincode', 'country']
            },
            callback: function(r) {
                if (r.message) {
                    let address = r.message;
                    let errors = [];

                    if (!address.address_line1) errors.push('Morada');
                    if (!address.city) errors.push('Cidade');
                    if (!address.pincode) errors.push('Código Postal');

                    if (errors.length > 0) {
                        frappe.show_alert({
                            message: __('Endereço {0} incompleto: {1}', [addr.type, errors.join(', ')]),
                            indicator: 'orange'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Endereço {0} válido', [addr.type]),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    });
}

function print_portuguese_purchase_receipt(frm) {
    /**
     * Imprimir guia com formato português
     */

    // Sem format explicito - deixa o Frappe escolher o print format por
    // defeito (nao existe ainda nenhum print format dedicado para este doctype).
    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function compare_with_purchase_order(frm) {
    /**
     * Comparar com Purchase Order
     */

    if (!frm.doc.purchase_order) {
        frappe.msgprint(__('Nenhuma Purchase Order associada'));
        return;
    }

    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Purchase Order',
            name: frm.doc.purchase_order
        },
        callback: function(r) {
            if (r.message) {
                show_po_comparison_dialog(frm, r.message);
            }
        }
    });
}

function show_po_comparison_dialog(frm, po_doc) {
    /**
     * Mostrar dialog de comparação com PO
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Comparação com Purchase Order'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'comparison_info'
            }
        ]
    });

    let pr_total = frm.doc.grand_total || 0;
    let po_total = po_doc.grand_total || 0;
    let difference = pr_total - po_total;

    let html = `
        <div class="po-comparison-info">
            <h5>Purchase Order: ${po_doc.name}</h5>
            <table class="table table-bordered">
                <tr><td><strong>PO Total:</strong></td><td>€${po_total.toFixed(2)}</td></tr>
                <tr><td><strong>PR Total:</strong></td><td>€${pr_total.toFixed(2)}</td></tr>
                <tr><td><strong>Diferença:</strong></td><td style="color: ${difference >= 0 ? 'green' : 'red'}">€${difference.toFixed(2)}</td></tr>
                <tr><td><strong>Status PO:</strong></td><td>${po_doc.status}</td></tr>
                <tr><td><strong>Data PO:</strong></td><td>${frappe.datetime.str_to_user(po_doc.transaction_date)}</td></tr>
            </table>

            <h6>Itens:</h6>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qtd PO</th>
                        <th>Qtd PR</th>
                        <th>Diferença</th>
                    </tr>
                </thead>
                <tbody>
    `;

    // Comparar itens
    if (po_doc.items && frm.doc.items) {
        po_doc.items.forEach(function(po_item) {
            let pr_item = frm.doc.items.find(item => item.item_code === po_item.item_code);
            let pr_qty = pr_item ? pr_item.qty : 0;
            let qty_diff = pr_qty - po_item.qty;

            html += `
                <tr>
                    <td>${po_item.item_name}</td>
                    <td>${po_item.qty}</td>
                    <td>${pr_qty}</td>
                    <td style="color: ${qty_diff >= 0 ? 'green' : 'red'}">${qty_diff}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.comparison_info.$wrapper.html(html);
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

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ CALCULAR TOTAIS
    let totals = calculate_receipt_totals(frm);
    if (totals.total_qty > 0) {
        frm.doc.total_qty = totals.total_qty;
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
            fieldname: ['portugal_compliance_enabled']
        },
        callback: function(r) {
            if (r.message) {
                frm._company_settings = r.message;
            }
        }
    });
}

function load_supplier_tax_info(frm) {
    /**
     * Carregar informações fiscais do fornecedor
     */

    if (!frm.doc.supplier) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Supplier',
            filters: {name: frm.doc.supplier},
            fieldname: ['tax_id', 'tax_category']
        },
        callback: function(r) {
            if (r.message) {
                frm._supplier_tax_info = r.message;

                // ✅ MOSTRAR NIF SE DISPONÍVEL
                if (r.message.tax_id) {
                    frm.dashboard.add_indicator(
                        __('NIF Fornecedor: {0}', [r.message.tax_id]),
                        'blue'
                    );
                }
            }
        }
    });
}

function load_supplier_address_info(frm) {
    /**
     * Carregar informações do endereço do fornecedor
     */

    if (!frm.doc.supplier_address) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.supplier_address},
            fieldname: ['city', 'country', 'pincode']
        },
        callback: function(r) {
            if (r.message) {
                frm._supplier_address_info = r.message;
            }
        }
    });
}

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA GUIAS DE RECEÇÃO PORTUGUESAS
    frm.toggle_reqd('supplier', true);
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
        message: __('Guia de receção portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR INFORMAÇÕES DE RECEÇÃO
    let total_qty = calculate_total_qty(frm);
    if (total_qty > 0) {
        frm.dashboard.add_indicator(__('Qtd Total: {0}', [total_qty]), 'blue');
    }
}

function validate_supplier_nif_manual(frm) {
    /**
     * Validar NIF do fornecedor manualmente
     */

    if (!frm.doc.supplier) {
        frappe.msgprint(__('Selecione um fornecedor primeiro'));
        return;
    }

    validate_supplier_nif(frm);
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

frappe.ui.form.on('Purchase Receipt Item', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR TOTAIS QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            calculate_receipt_totals(frm);
        }, 100);
    },

    rate: function(frm, cdt, cdn) {
        // ✅ RECALCULAR TOTAIS QUANDO RATE MUDA
        setTimeout(() => {
            calculate_receipt_totals(frm);
        }, 100);
    },

    warehouse: function(frm, cdt, cdn) {
        // ✅ VALIDAR ARMAZÉM QUANDO MUDA
        let item = locals[cdt][cdn];
        if (item.warehouse) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Warehouse',
                    filters: {name: item.warehouse},
                    fieldname: ['company', 'disabled']
                },
                callback: function(r) {
                    if (r.message) {
                        if (r.message.company !== frm.doc.company) {
                            frappe.show_alert({
                                message: __('Armazém não pertence à empresa selecionada'),
                                indicator: 'red'
                            });
                        }
                        if (r.message.disabled) {
                            frappe.show_alert({
                                message: __('Armazém está desativado'),
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

frappe.ui.form.on('Purchase Receipt', {
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
            "Série portuguesa para guias de receção. Formato: GR2025EMPRESA.#### (GR=Guia de Receção)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para guias.";
    }

    if (frm.fields_dict.bill_no) {
        frm.fields_dict.bill_no.df.description =
            "Número da fatura do fornecedor (referência obrigatória para receção)";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado para Portugal Compliance
     */

    // Atalho Ctrl+G ("Gerar ATCUD") removido junto com o botão e a
    // função - ver nota em add_custom_buttons.

    // ✅ CTRL+T para calcular totais
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+t',
        action: () => {
            if (frm.doc.items && frm.doc.items.length > 0) {
                calculate_and_show_totals(frm);
            }
        },
        description: __('Calcular Totais'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_purchase_receipt(frm);
            }
        },
        description: __('Imprimir Guia Portuguesa'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+O para comparar com PO
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+o',
        action: () => {
            if (frm.doc.purchase_order) {
                compare_with_purchase_order(frm);
            }
        },
        description: __('Comparar com Purchase Order'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_purchase_receipt_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para guia de receção
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

    // ✅ VERIFICAR DADOS DO FORNECEDOR
    if (!frm.doc.supplier) {
        compliance_issues.push({
            type: 'error',
            message: 'Fornecedor é obrigatório'
        });
    }

    // ✅ VERIFICAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        compliance_issues.push({
            type: 'error',
            message: 'Pelo menos um item é obrigatório'
        });
    }

    // ✅ VERIFICAR ARMAZÉNS
    if (!frm.doc.set_warehouse) {
        let items_without_warehouse = frm.doc.items.filter(item => !item.warehouse);
        if (items_without_warehouse.length > 0) {
            compliance_issues.push({
                type: 'error',
                message: 'Defina armazém para todos os itens ou use armazém padrão'
            });
        }
    }

    // ✅ VERIFICAR QUANTIDADES
    if (frm.doc.items) {
        let items_with_zero_qty = frm.doc.items.filter(item => !item.qty || item.qty <= 0);
        if (items_with_zero_qty.length > 0) {
            compliance_issues.push({
                type: 'error',
                message: 'Todos os itens devem ter quantidade maior que zero'
            });
        }
    }

    return compliance_issues;
}

function show_compliance_report(frm) {
    /**
     * ✅ NOVA: Mostrar relatório completo de compliance
     */

    let issues = validate_purchase_receipt_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Guia de Receção</h5>

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

function generate_receipt_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo da receção
     */

    let totals = calculate_receipt_totals(frm);
    let supplier_nif = frm._supplier_tax_info ? frm._supplier_tax_info.tax_id : null;

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo da Receção'),
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
        <div class="receipt-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Receção</h3>
                <p><strong>Guia:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}</p>
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
                    <h5>Dados do Fornecedor</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Nome:</strong></td><td>${frm.doc.supplier_name}</td></tr>
                        <tr><td><strong>NIF:</strong></td><td>${supplier_nif || 'N/A'}</td></tr>
                        <tr><td><strong>Fatura Nº:</strong></td><td>${frm.doc.bill_no || 'N/A'}</td></tr>
                        <tr><td><strong>Data Fatura:</strong></td><td>${frm.doc.bill_date ? frappe.datetime.str_to_user(frm.doc.bill_date) : 'N/A'}</td></tr>
                    </table>
                </div>
            </div>

            <h5>Resumo da Receção</h5>
            <table class="table table-bordered">
                <tr><td><strong>Quantidade Total:</strong></td><td>${totals.total_qty}</td></tr>
                <tr><td><strong>Valor Total Itens:</strong></td><td>€${totals.total_amount.toFixed(2)}</td></tr>
                <tr style="font-weight: bold; background-color: #f8f9fa;"><td><strong>Grand Total:</strong></td><td>€${(frm.doc.grand_total || 0).toFixed(2)}</td></tr>
            </table>

            <h5>Itens Recebidos (${frm.doc.items ? frm.doc.items.length : 0})</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Item</th><th>Qtd</th><th>Rate</th><th>Valor</th><th>Armazém</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            html += `
                <tr>
                    <td>${item.item_name || item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td>€${(item.rate || 0).toFixed(2)}</td>
                    <td>€${(item.amount || 0).toFixed(2)}</td>
                    <td>${item.warehouse || frm.doc.set_warehouse || '-'}</td>
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
                <p><strong>Purchase Order:</strong> ${frm.doc.purchase_order || 'Não associada'}</p>
                <p><strong>Observações:</strong> ${frm.doc.remarks || 'Nenhuma'}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== FUNÇÕES DE AUDITORIA ==========

function create_receipt_audit_log(frm) {
    /**
     * ✅ NOVA: Criar log de auditoria para receção
     */

    if (!frm.doc.docstatus === 1) return;

    let totals = calculate_receipt_totals(frm);
    let supplier_nif = frm._supplier_tax_info ? frm._supplier_tax_info.tax_id : null;

    let audit_data = {
        document_type: frm.doc.doctype,
        document_name: frm.doc.name,
        atcud_code: frm.doc.atcud_code,
        supplier: frm.doc.supplier,
        supplier_name: frm.doc.supplier_name,
        supplier_nif: supplier_nif,
        total_qty: totals.total_qty,
        total_amount: frm.doc.grand_total,
        posting_date: frm.doc.posting_date,
        purchase_order: frm.doc.purchase_order,
        set_warehouse: frm.doc.set_warehouse,
        bill_no: frm.doc.bill_no,
        created_by: frappe.session.user,
        created_at: frappe.datetime.now_datetime()
    };

    frappe.call({
        method: 'portugal_compliance.api.create_receipt_audit_log',
        args: {
            audit_data: audit_data
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                console.log('Receipt audit log created:', frm.doc.name);
            }
        }
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Purchase Receipt JS loaded - Version 2.0.0');
