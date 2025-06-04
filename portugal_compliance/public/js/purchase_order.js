// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Purchase Order JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (OC2025NDX em vez de OC-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (OC)
 * ✅ Geração automática de ATCUD para ordens de compra
 * ✅ Validação de compliance português para compras
 * ✅ Interface otimizada para ordens de compra portuguesas
 */

frappe.ui.form.on('Purchase Order', {
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
        setup_purchase_order_validations(frm);
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

    // ========== EVENTOS DE SUPPLIER ==========
    supplier: function(frm) {
        if (frm.doc.supplier) {
            // ✅ VALIDAR NIF DO FORNECEDOR
            validate_supplier_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_supplier_tax_info(frm);
        }
    },

    // ========== EVENTOS DE SCHEDULE DATE ==========
    schedule_date: function(frm) {
        if (frm.doc.schedule_date) {
            // ✅ VALIDAR PRAZO DE ENTREGA
            validate_schedule_date(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_purchase_order(frm);
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
                "is_purchase_item": 1
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para ordens de compra";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para ordens de compra (OC2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPO SCHEDULE DATE
    if (frm.fields_dict.schedule_date) {
        frm.fields_dict.schedule_date.df.description = "Data de entrega esperada para ordem de compra";
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
    $(frm.wrapper).on('schedule_date_warning', function(e, data) {
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
     * Configurar layout específico para ordens de compra portuguesas
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

    // ✅ ADICIONAR SEÇÃO DE ORDEM DE COMPRA
    add_purchase_order_section(frm);
}

function add_compliance_section(frm) {
    /**
     * Adicionar seção de informações de compliance
     */

    let tax_info = calculate_tax_breakdown(frm);
    let schedule_status = get_schedule_status(frm);

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações de Compliance Português - Ordem de Compra
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>ATCUD:</strong> ${frm.doc.atcud_code || 'Não gerado'}<br>
                    <strong>Série:</strong> ${frm.doc.naming_series || 'Não definida'}<br>
                    <strong>Fornecedor:</strong> ${frm.doc.supplier_name || 'Não definido'}
                </div>
                <div class="col-md-6">
                    <strong>Status:</strong> <span class="indicator ${get_compliance_status(frm).color}">${get_compliance_status(frm).label}</span><br>
                    <strong>Total s/ IVA:</strong> €${(frm.doc.net_total || 0).toFixed(2)}<br>
                    <strong>Total IVA:</strong> €${tax_info.total_tax.toFixed(2)}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-12">
                    <strong>Total c/ IVA:</strong> €${(frm.doc.grand_total || 0).toFixed(2)}
                    <span class="ml-3"><strong>Entrega:</strong> <span class="indicator ${schedule_status.color}">${schedule_status.label}</span></span>
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

function add_purchase_order_section(frm) {
    /**
     * Adicionar seção específica de ordem de compra
     */

    if (frm.doc.__islocal) return;

    let purchase_order_html = `
        <div class="purchase-order-info" style="
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #e65100;">
                🛒 Informações da Ordem de Compra
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Data Ordem:</strong> ${frappe.datetime.str_to_user(frm.doc.transaction_date)}<br>
                    <strong>Data Entrega:</strong> ${frm.doc.schedule_date ? frappe.datetime.str_to_user(frm.doc.schedule_date) : 'Não definida'}<br>
                    <strong>Status:</strong> ${frm.doc.status || 'Draft'}
                </div>
                <div class="col-md-6">
                    <strong>Prazo Entrega:</strong> ${get_schedule_days(frm)}<br>
                    <strong>Tipo Ordem:</strong> ${frm.doc.order_type || 'Purchase'}<br>
                    <strong>Observações:</strong> ${frm.doc.terms ? 'Definidas' : 'Não definidas'}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.purchase_order_section_added) {
        $(frm.fields_dict.supplier.wrapper).after(purchase_order_html);
        frm.purchase_order_section_added = true;
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

    // ✅ VERIFICAR DATA DE ENTREGA
    if (!frm.doc.schedule_date) {
        return {
            label: 'Entrega Pendente',
            color: 'orange',
            description: 'Data de entrega recomendada'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Ordem de compra conforme legislação portuguesa'
    };
}

function get_schedule_status(frm) {
    /**
     * Obter status de entrega da ordem
     */

    if (!frm.doc.schedule_date) {
        return {
            label: 'Não Definida',
            color: 'orange',
            overdue: false
        };
    }

    let schedule_date = frappe.datetime.str_to_obj(frm.doc.schedule_date);
    let today = new Date();

    if (schedule_date < today) {
        return {
            label: 'Atrasada',
            color: 'red',
            overdue: true
        };
    }

    // Verificar se entrega é em breve (próximos 7 dias)
    let days_left = Math.ceil((schedule_date - today) / (1000 * 60 * 60 * 24));

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

function get_schedule_days(frm) {
    /**
     * Obter número de dias para entrega
     */

    if (!frm.doc.schedule_date || !frm.doc.transaction_date) {
        return 'Não calculado';
    }

    let start_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);
    let end_date = frappe.datetime.str_to_obj(frm.doc.schedule_date);
    let days = Math.ceil((end_date - start_date) / (1000 * 60 * 60 * 24));

    return days > 0 ? `${days} dias` : 'Inválido';
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

    // ✅ BOTÃO PARA IMPRIMIR ORDEM PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Ordem PT'), function() {
            print_portuguese_purchase_order(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF FORNECEDOR
    if (frm.doc.supplier) {
        frm.add_custom_button(__('Validar NIF Fornecedor'), function() {
            validate_supplier_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA ANALISAR ORDEM
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Ordem'), function() {
            analyze_purchase_order(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA ATUALIZAR PRAZO
    if (frm.doc.docstatus === 1 && get_schedule_status(frm).overdue) {
        frm.add_custom_button(__('Atualizar Prazo'), function() {
            update_schedule_date(frm);
        }, __('Ações'));
    }

    // ✅ BOTÃO PARA CRIAR PURCHASE RECEIPT
    if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
        frm.add_custom_button(__('Criar Recebimento'), function() {
            create_purchase_receipt_from_purchase_order(frm);
        }, __('Conversões'));
    }

    // ✅ BOTÃO PARA CRIAR PURCHASE INVOICE
    if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
        frm.add_custom_button(__('Criar Fatura Compra'), function() {
            create_purchase_invoice_from_purchase_order(frm);
        }, __('Conversões'));
    }

    // ✅ BOTÃO PARA DUPLICAR ORDEM
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Duplicar Ordem'), function() {
            duplicate_purchase_order(frm);
        }, __('Ações'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA ORDENS DE COMPRA (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
        args: {
            doctype: 'Purchase Order',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS OC (formato SEM HÍFENS: OC2025NDX)
                let oc_series = r.message.series.filter(s => s.prefix.startsWith('OC'));
                let communicated_series = oc_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : oc_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE OC
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série OC comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série OC não comunicada selecionada. Comunique à AT antes de submeter.'),
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
            message: __('Para compliance português, use séries no formato OC2025EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE ORDEM DE COMPRA (formato SEM HÍFENS)
    let prefix = frm.doc.naming_series.replace('.####', '');
    let doc_code = prefix.substring(0, 2); // Primeiros 2 caracteres: OC

    if (doc_code !== 'OC') {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para Purchase Order, use séries OC (Ordem de Compra)'),
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
        message = __('Série OC comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série OC não comunicada à AT. Comunique antes de submeter ordens.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_purchase_order(frm) {
    /**
     * Validações específicas para ordens de compra portuguesas
     */

    let errors = [];

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato OC2025EMPRESA.####)'));
    }

    // ✅ VALIDAR FORNECEDOR
    if (!frm.doc.supplier) {
        errors.push(__('Fornecedor é obrigatório'));
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

function validate_schedule_date(frm) {
    /**
     * Validar data de entrega
     */

    if (!frm.doc.schedule_date) return;

    let schedule_date = frappe.datetime.str_to_obj(frm.doc.schedule_date);
    let transaction_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);

    if (schedule_date <= transaction_date) {
        frappe.show_alert({
            message: __('Data de entrega deve ser posterior à data da ordem'),
            indicator: 'red'
        });
    } else {
        let days = Math.ceil((schedule_date - transaction_date) / (1000 * 60 * 60 * 24));
        frappe.show_alert({
            message: __('Prazo de entrega: {0} dias', [days]),
            indicator: 'green'
        });
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
        let description = (tax.description || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            has_iva = true;
            iva_rates.push(tax.rate);
        }
    });

    if (!has_iva) {
        errors.push(__('Ordem deve ter IVA configurado'));
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

        // ✅ VALIDAR ATCUD OBRIGATÓRIO
        if (!frm.doc.atcud_code) {
            validations.push(__('ATCUD é obrigatório para ordens de compra portuguesas'));
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
                        validations.push(__('Série OC deve estar comunicada à AT antes da submissão'));
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

// ========== FUNÇÕES ESPECÍFICAS DE ORDEM DE COMPRA ==========

function setup_purchase_order_validations(frm) {
    /**
     * Configurar validações específicas de ordem de compra
     */

    // ✅ VALIDAR DATA DE ENTREGA QUANDO MUDA
    if (frm.fields_dict.schedule_date) {
        frm.fields_dict.schedule_date.$input.on('change', function() {
            validate_schedule_date(frm);
        });
    }

    // ✅ VALIDAR IMPOSTOS QUANDO MUDAM
    if (frm.fields_dict.taxes && frm.fields_dict.taxes.grid) {
        frm.fields_dict.taxes.grid.get_field('rate').df.onchange = function() {
            validate_portuguese_taxes(frm);
        };
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
            message: __('Adicione IVA português à ordem'),
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
        title: __('Status da Série OC'),
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
                <tr><td><strong>Tipo:</strong></td><td>Ordem de Compra</td></tr>
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

function print_portuguese_purchase_order(frm) {
    /**
     * Imprimir ordem com formato português
     */

    frappe.route_options = {
        "format": "Ordem de Compra Portugal"
    };

    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function analyze_purchase_order(frm) {
    /**
     * Analisar ordem de compra completa
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise da Ordem de Compra'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_info'
            }
        ]
    });

    let tax_info = calculate_tax_breakdown(frm);
    let supplier_nif = get_supplier_nif(frm);
    let schedule_status = get_schedule_status(frm);

    let html = `
        <div class="purchase-order-analysis">
            <h5>Análise da Ordem de Compra: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Fornecedor:</strong></td><td>${frm.doc.supplier_name}</td></tr>
                        <tr><td><strong>NIF Fornecedor:</strong></td><td>${supplier_nif || 'Não definido'}</td></tr>
                        <tr><td><strong>Data Ordem:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.transaction_date)}</td></tr>
                        <tr><td><strong>Data Entrega:</strong></td><td>${frm.doc.schedule_date ? frappe.datetime.str_to_user(frm.doc.schedule_date) : 'Não definida'}</td></tr>
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
                        <tr><td><strong>Status Entrega:</strong></td><td style="color: ${schedule_status.color === 'green' ? 'green' : schedule_status.color === 'orange' ? 'orange' : 'red'}">${schedule_status.label}</td></tr>
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

function update_schedule_date(frm) {
    /**
     * Atualizar data de entrega
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Atualizar Data de Entrega'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'new_schedule_date',
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
                method: 'portugal_compliance.api.update_purchase_order_schedule_date',
                args: {
                    purchase_order: frm.doc.name,
                    new_schedule_date: values.new_schedule_date,
                    reason: values.update_reason
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Data de entrega atualizada para {0}', [frappe.datetime.str_to_user(values.new_schedule_date)]),
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

function create_purchase_receipt_from_purchase_order(frm) {
    /**
     * Criar Purchase Receipt a partir da ordem
     */

    frappe.model.open_mapped_doc({
        method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
        frm: frm
    });
}

function create_purchase_invoice_from_purchase_order(frm) {
    /**
     * Criar Purchase Invoice a partir da ordem
     */

    frappe.model.open_mapped_doc({
        method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
        frm: frm
    });
}

function duplicate_purchase_order(frm) {
    /**
     * Duplicar ordem de compra
     */

    frappe.confirm(
        __('Duplicar esta ordem de compra? Será criada uma nova ordem com os mesmos dados.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.api.duplicate_purchase_order',
                args: {
                    purchase_order: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Ordem duplicada: {0}', [r.message.new_purchase_order]),
                            indicator: 'green'
                        });

                        frappe.set_route("Form", "Purchase Order", r.message.new_purchase_order);
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
    const pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$/;
    return pattern.test(naming_series);
}

function get_supplier_nif(frm) {
    /**
     * Obter NIF do fornecedor
     */

    if (frm._supplier_nif !== undefined) {
        return frm._supplier_nif;
    }

    if (!frm.doc.supplier) return null;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Supplier',
            filters: {name: frm.doc.supplier},
            fieldname: 'tax_id'
        },
        async: false,
        callback: function(r) {
            frm._supplier_nif = r.message ? r.message.tax_id : null;
        }
    });

    return frm._supplier_nif;
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

    // ✅ CALCULAR BREAKDOWN DE IMPOSTOS
    let tax_info = calculate_tax_breakdown(frm);
    if (tax_info.total_tax > 0) {
        frm.doc.total_taxes_and_charges = tax_info.total_tax;
    }

    // ✅ DEFINIR DATA DE ENTREGA PADRÃO SE NÃO DEFINIDA
    if (!frm.doc.schedule_date && frm.doc.transaction_date) {
        let default_schedule = frappe.datetime.add_days(frm.doc.transaction_date, 14);
        frm.doc.schedule_date = default_schedule;
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
            fieldname: ['at_environment', 'portugal_compliance_enabled', 'default_currency']
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
                frm._supplier_nif = r.message.tax_id;

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

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA ORDENS DE COMPRA PORTUGUESAS
    frm.toggle_reqd('supplier', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('transaction_date', true);
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
    frm.meta.default_print_format = "Ordem de Compra Portugal";
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
        message: __('Ordem de compra portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR TOTAL E ENTREGA
    frm.dashboard.add_indicator(__('Total: €{0}', [(frm.doc.grand_total || 0).toFixed(2)]), 'blue');

    if (frm.doc.schedule_date) {
        let schedule_status = get_schedule_status(frm);
        frm.dashboard.add_indicator(schedule_status.label, schedule_status.color);
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

frappe.ui.form.on('Purchase Order Item', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR IMPOSTOS QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            validate_portuguese_taxes(frm);
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    },

    rate: function(frm, cdt, cdn) {
        // ✅ RECALCULAR IMPOSTOS QUANDO PREÇO MUDA
        setTimeout(() => {
            validate_portuguese_taxes(frm);
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    },

    schedule_date: function(frm, cdt, cdn) {
        // ✅ VALIDAR DATA DE ENTREGA DO ITEM
        let item = locals[cdt][cdn];
        if (item.schedule_date) {
            let item_schedule = frappe.datetime.str_to_obj(item.schedule_date);
            let order_schedule = frappe.datetime.str_to_obj(frm.doc.schedule_date);

            if (order_schedule && item_schedule > order_schedule) {
                frappe.show_alert({
                    message: __('Data de entrega do item não pode ser posterior à data da ordem'),
                    indicator: 'orange'
                });
            }
        }
    }
});

// ========== EVENTOS DE TAXES ==========

frappe.ui.form.on('Purchase Taxes and Charges', {
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
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    },

    tax_amount: function(frm, cdt, cdn) {
        // ✅ RECALCULAR TOTAIS QUANDO VALOR DE IMPOSTO MUDA
        setTimeout(() => {
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    }
});

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Purchase Order', {
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
            "Série portuguesa para ordens de compra. Formato: OC2025EMPRESA.#### (OC=Ordem de Compra)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para ordens de compra.";
    }

    if (frm.fields_dict.schedule_date) {
        frm.fields_dict.schedule_date.df.description =
            "Data de entrega esperada para ordem de compra portuguesa";
    }

    if (frm.fields_dict.taxes_and_charges) {
        frm.fields_dict.taxes_and_charges.df.description =
            "Template de impostos portugueses (IVA 0%, 6%, 13%, 23%)";
    }

    if (frm.fields_dict.supplier) {
        frm.fields_dict.supplier.df.description =
            "Fornecedor português (verificar NIF para compliance)";
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

    // ✅ CTRL+D para validar data de entrega
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+d',
        action: () => {
            if (frm.doc.schedule_date) {
                validate_schedule_date(frm);
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
                print_portuguese_purchase_order(frm);
            }
        },
        description: __('Imprimir Ordem Portuguesa'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar ordem
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.docstatus === 1) {
                analyze_purchase_order(frm);
            }
        },
        description: __('Analisar Ordem'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+U para atualizar prazo
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+u',
        action: () => {
            if (frm.doc.docstatus === 1 && get_schedule_status(frm).overdue) {
                update_schedule_date(frm);
            }
        },
        description: __('Atualizar Prazo de Entrega'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+R para criar recebimento
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+r',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
                create_purchase_receipt_from_purchase_order(frm);
            }
        },
        description: __('Criar Recebimento'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+I para criar fatura
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+i',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.status !== 'Completed') {
                create_purchase_invoice_from_purchase_order(frm);
            }
        },
        description: __('Criar Fatura de Compra'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('Purchase Order', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_company(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form purchase-order-pt');

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

    // ✅ OBSERVAR MUDANÇAS NO FORNECEDOR
    frm.fields_dict.supplier && frm.fields_dict.supplier.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.supplier) {
                validate_supplier_nif(frm);
                load_supplier_tax_info(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NA DATA DE ENTREGA
    frm.fields_dict.schedule_date && frm.fields_dict.schedule_date.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.schedule_date) {
                validate_schedule_date(frm);

                // Atualizar seções visuais
                if (frm.compliance_section_added) {
                    $('.portugal-compliance-info').remove();
                    frm.compliance_section_added = false;
                    add_compliance_section(frm);
                }

                if (frm.purchase_order_section_added) {
                    $('.purchase-order-info').remove();
                    frm.purchase_order_section_added = false;
                    add_purchase_order_section(frm);
                }
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO TEMPLATE DE IMPOSTOS
    frm.fields_dict.taxes_and_charges && frm.fields_dict.taxes_and_charges.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.taxes_and_charges) {
                frappe.show_alert({
                    message: __('Template de impostos aplicado: {0}', [frm.doc.taxes_and_charges]),
                    indicator: 'blue'
                });
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO STATUS
    frm.fields_dict.status && frm.fields_dict.status.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.status && frm.purchase_order_section_added) {
                // Atualizar seção de ordem
                $('.purchase-order-info').remove();
                frm.purchase_order_section_added = false;
                add_purchase_order_section(frm);
            }
        }, 100);
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_purchase_order_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para ordem de compra
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

    // ✅ VERIFICAR DATA DE ENTREGA
    if (!frm.doc.schedule_date) {
        compliance_issues.push({
            type: 'warning',
            message: 'Data de entrega recomendada'
        });
    } else {
        let schedule_status = get_schedule_status(frm);
        if (schedule_status.overdue) {
            compliance_issues.push({
                type: 'error',
                message: 'Data de entrega já passou'
            });
        }
    }

    // ✅ VERIFICAR DADOS DO FORNECEDOR
    let supplier_nif = get_supplier_nif(frm);
    if (!supplier_nif) {
        compliance_issues.push({
            type: 'warning',
            message: 'NIF do fornecedor não definido'
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

    let issues = validate_purchase_order_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Ordem de Compra</h5>

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

function generate_purchase_order_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo da ordem de compra
     */

    let tax_info = calculate_tax_breakdown(frm);
    let supplier_nif = get_supplier_nif(frm);
    let schedule_status = get_schedule_status(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo da Ordem de Compra'),
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
        <div class="purchase-order-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Ordem de Compra</h3>
                <p><strong>Ordem:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.transaction_date)}</p>
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
                        <tr><td><strong>Data Entrega:</strong></td><td>${frm.doc.schedule_date ? frappe.datetime.str_to_user(frm.doc.schedule_date) : 'N/A'}</td></tr>
                        <tr><td><strong>Status Entrega:</strong></td><td style="color: ${schedule_status.color === 'green' ? 'green' : schedule_status.color === 'orange' ? 'orange' : 'red'}">${schedule_status.label}</td></tr>
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

            <h5>Itens da Ordem (${frm.doc.items ? frm.doc.items.length : 0})</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Item</th><th>Qtd</th><th style="text-align: right;">Preço Unit.</th><th style="text-align: right;">Total</th><th>Entrega</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let item_schedule = item.schedule_date ? frappe.datetime.str_to_user(item.schedule_date) : 'Conforme ordem';
            html += `
                <tr>
                    <td>${item.item_name || item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td style="text-align: right;">€${(item.rate || 0).toFixed(2)}</td>
                    <td style="text-align: right;">€${(item.amount || 0).toFixed(2)}</td>
                    <td>${item_schedule}</td>
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
                <p><strong>Status da Ordem:</strong> ${frm.doc.status}</p>
                <p><strong>Prazo de Entrega:</strong> ${get_schedule_days(frm)}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Purchase Order JS loaded - Version 2.0.0');
