// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * POS Invoice JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (FS2025NDX em vez de FS-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (FS)
 * ✅ Geração automática de ATCUD para faturas POS
 * ✅ Validação de compliance português para retail
 * ✅ Interface otimizada para POS portuguesas com QR Code
 */

frappe.ui.form.on('POS Invoice', {
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

        // ✅ CONFIGURAR VALIDAÇÕES FISCAIS POS
        setup_pos_fiscal_validations(frm);
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

    // ========== EVENTOS DE CUSTOMER ==========
    customer: function(frm) {
        if (frm.doc.customer) {
            // ✅ VALIDAR NIF DO CLIENTE
            validate_customer_nif(frm);

            // ✅ CARREGAR DADOS FISCAIS
            load_customer_tax_info(frm);

            // ✅ VERIFICAR LIMITE SEM NIF
            check_pos_nif_limit(frm);
        }
    },

    // ========== EVENTOS DE TOTAL ==========
    grand_total: function(frm) {
        if (frm.doc.grand_total) {
            // ✅ VERIFICAR LIMITE FATURA SIMPLIFICADA
            check_simplified_invoice_limit(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_pos_invoice(frm);
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para faturas POS";
    }

    // ✅ CONFIGURAR CAMPO QR CODE
    if (frm.fields_dict.qr_code) {
        frm.fields_dict.qr_code.df.read_only = 1;
        frm.fields_dict.qr_code.df.description = "QR Code obrigatório para faturas POS portuguesas";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para POS (FS2025EMPRESA.#### - Fatura Simplificada)";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE LIMITE POS
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

    // ✅ EVENTO PARA VERIFICAÇÃO DE LIMITE
    $(frm.wrapper).on('limit_exceeded', function(e, data) {
        frappe.msgprint({
            title: __('Limite Excedido'),
            message: data.message,
            indicator: 'red'
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
     * Configurar layout específico para POS portuguesas
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

    // ✅ ADICIONAR SEÇÃO POS
    add_pos_section(frm);
}

function add_compliance_section(frm) {
    /**
     * Adicionar seção de informações de compliance
     */

    let tax_info = calculate_tax_breakdown(frm);
    let nif_required = check_nif_required(frm);

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações de Compliance Português - Fatura POS
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>ATCUD:</strong> ${frm.doc.atcud_code || 'Não gerado'}<br>
                    <strong>Série:</strong> ${frm.doc.naming_series || 'Não definida'}<br>
                    <strong>Cliente:</strong> ${frm.doc.customer_name || 'Consumidor Final'}
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
                    ${nif_required ? '<span class="ml-3 text-warning"><strong>⚠️ NIF Obrigatório</strong></span>' : ''}
                    ${frm.doc.qr_code ? '<span class="ml-3"><strong>QR Code:</strong> <span class="indicator green">Gerado</span></span>' : ''}
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

function add_pos_section(frm) {
    /**
     * Adicionar seção específica POS
     */

    if (frm.doc.__islocal) return;

    let pos_html = `
        <div class="pos-info" style="
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #2e7d32;">
                🛒 Informações POS - Retail
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Tipo Documento:</strong> Fatura Simplificada<br>
                    <strong>Data Venda:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}<br>
                    <strong>POS Profile:</strong> ${frm.doc.pos_profile || 'Não definido'}
                </div>
                <div class="col-md-6">
                    <strong>Limite s/ NIF:</strong> €1000 (${(frm.doc.grand_total || 0) <= 1000 ? 'OK' : 'EXCEDIDO'})<br>
                    <strong>Modo Pagamento:</strong> ${get_payment_modes(frm)}<br>
                    <strong>QR Code:</strong> ${frm.doc.qr_code ? 'Gerado' : 'Pendente'}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.pos_section_added) {
        $(frm.fields_dict.customer.wrapper).after(pos_html);
        frm.pos_section_added = true;
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

    // ✅ VERIFICAR LIMITE SEM NIF
    if (check_nif_required(frm) && !get_customer_nif(frm)) {
        return {
            label: 'NIF Obrigatório',
            color: 'red',
            description: 'Valor acima de €1000 requer NIF do cliente'
        };
    }

    // ✅ VERIFICAR QR CODE
    if (!frm.doc.qr_code) {
        return {
            label: 'QR Code Pendente',
            color: 'orange',
            description: 'QR Code será gerado automaticamente'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Fatura POS conforme legislação portuguesa'
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

    // ✅ BOTÃO PARA GERAR QR CODE
    if (frm.doc.atcud_code && !frm.doc.qr_code) {
        frm.add_custom_button(__('Gerar QR Code'), function() {
            generate_qr_code_manually(frm);
        }, __('Portugal Compliance'));
    }

    // ✅ BOTÃO PARA VERIFICAR SÉRIE
    if (frm.doc.naming_series) {
        frm.add_custom_button(__('Verificar Série'), function() {
            check_series_status(frm);
        }, __('Portugal Compliance'));
    }

    // ✅ BOTÃO PARA IMPRIMIR TÉRMICA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Térmica'), function() {
            print_thermal_receipt(frm);
        }, __('POS'));
    }

    // ✅ BOTÃO PARA REIMPRIMIR
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Reimprimir'), function() {
            reprint_pos_invoice(frm);
        }, __('POS'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF CLIENTE
    if (frm.doc.customer && frm.doc.customer !== 'Consumidor Final') {
        frm.add_custom_button(__('Validar NIF Cliente'), function() {
            validate_customer_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA CONVERTER EM FATURA
    if (frm.doc.docstatus === 1 && frm.doc.grand_total > 1000) {
        frm.add_custom_button(__('Converter em Fatura'), function() {
            convert_to_sales_invoice(frm);
        }, __('Conversões'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA POS (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
        args: {
            doctype: 'POS Invoice',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS FS (formato SEM HÍFENS: FS2025NDX)
                let fs_series = r.message.series.filter(s => s.prefix.startsWith('FS'));
                let communicated_series = fs_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : fs_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE FS
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série FS comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série FS não comunicada selecionada. Comunique à AT antes de usar POS.'),
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
            message: __('Para compliance português, use séries no formato FS2025EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE FATURA SIMPLIFICADA (formato SEM HÍFENS)
    let prefix = frm.doc.naming_series.replace('.####', '');
    let doc_code = prefix.substring(0, 2); // Primeiros 2 caracteres: FS

    if (doc_code !== 'FS') {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para POS Invoice, use séries FS (Fatura Simplificada)'),
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
        message = __('Série FS comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série FS não comunicada à AT. Comunique antes de usar POS.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO POS ==========

function validate_portuguese_pos_invoice(frm) {
    /**
     * Validações específicas para POS portuguesas
     */

    let errors = [];

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato FS2025EMPRESA.####)'));
    }

    // ✅ VALIDAR LIMITE SEM NIF
    if (check_nif_required(frm) && !get_customer_nif(frm)) {
        errors.push(__('Valor acima de €1000 requer NIF do cliente'));
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

function check_simplified_invoice_limit(frm) {
    /**
     * Verificar limite de fatura simplificada
     */

    let total = frm.doc.grand_total || 0;
    let customer_nif = get_customer_nif(frm);

    if (total > 1000 && !customer_nif) {
        frappe.msgprint({
            title: __('Limite Excedido'),
            message: __('Faturas POS acima de €1000 requerem NIF do cliente. Total atual: €{0}', [total.toFixed(2)]),
            indicator: 'red',
            primary_action: {
                label: __('Definir Cliente'),
                action: function() {
                    frm.set_focus('customer');
                }
            }
        });

        $(frm.wrapper).trigger('limit_exceeded', {
            message: __('Limite de €1000 excedido sem NIF')
        });
    } else if (total > 1000 && customer_nif) {
        frappe.show_alert({
            message: __('Valor acima de €1000 com NIF válido'),
            indicator: 'green'
        });
    }
}

function check_pos_nif_limit(frm) {
    /**
     * Verificar limite NIF para POS
     */

    if (frm.doc.grand_total > 1000) {
        check_simplified_invoice_limit(frm);
    }
}

function check_nif_required(frm) {
    /**
     * Verificar se NIF é obrigatório
     */

    return (frm.doc.grand_total || 0) > 1000;
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
        errors.push(__('Fatura POS deve ter IVA configurado'));
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
            validations.push(__('ATCUD é obrigatório para faturas POS portuguesas'));
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
                        validations.push(__('Série FS deve estar comunicada à AT antes da submissão'));
                    }

                    // ✅ VALIDAR LIMITE SEM NIF
                    if (check_nif_required(frm) && !get_customer_nif(frm)) {
                        validations.push(__('Valor acima de €1000 requer NIF do cliente'));
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

function setup_pos_fiscal_validations(frm) {
    /**
     * Configurar validações específicas fiscais POS
     */

    // ✅ VALIDAR IMPOSTOS QUANDO MUDAM
    if (frm.fields_dict.taxes && frm.fields_dict.taxes.grid) {
        frm.fields_dict.taxes.grid.get_field('rate').df.onchange = function() {
            validate_portuguese_taxes(frm);
        };
    }

    // ✅ VALIDAR TOTAL QUANDO MUDA
    if (frm.fields_dict.grand_total) {
        frm.fields_dict.grand_total.$input.on('change', function() {
            check_simplified_invoice_limit(frm);
        });
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
            message: __('Adicione IVA português à fatura POS'),
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

    if (!frm.doc.customer || frm.doc.customer === 'Consumidor Final') return;

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

function generate_qr_code_manually(frm) {
    /**
     * ✅ CORRIGIDO: Gerar QR Code manualmente usando API correta
     */

    if (!frm.doc.atcud_code) {
        frappe.msgprint(__('ATCUD é necessário para gerar QR Code'));
        return;
    }

    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.generate_qr_code_for_document',
        args: {
            doctype: frm.doc.doctype,
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('QR Code gerado com sucesso'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao gerar QR Code'),
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
        title: __('Status da Série FS'),
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
                <tr><td><strong>Tipo:</strong></td><td>Fatura Simplificada (POS)</td></tr>
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

function print_thermal_receipt(frm) {
    /**
     * Imprimir recibo térmico
     */

    frappe.call({
        method: 'portugal_compliance.pos.print_thermal_receipt',
        args: {
            pos_invoice: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Recibo térmico enviado para impressora'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao imprimir'),
                    indicator: 'red'
                });
            }
        }
    });
}

function reprint_pos_invoice(frm) {
    /**
     * Reimprimir fatura POS
     */

    frappe.route_options = {
        "format": "Fatura Simplificada Portugal"
    };

    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function convert_to_sales_invoice(frm) {
    /**
     * Converter POS Invoice em Sales Invoice
     */

    frappe.confirm(
        __('Converter esta fatura POS em fatura normal? Isso criará uma nova Sales Invoice.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.pos.convert_pos_to_sales_invoice',
                args: {
                    pos_invoice: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Sales Invoice criada: {0}', [r.message.sales_invoice]),
                            indicator: 'green'
                        });

                        frappe.set_route("Form", "Sales Invoice", r.message.sales_invoice);
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro na conversão'),
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

function get_customer_nif(frm) {
    /**
     * Obter NIF do cliente
     */

    if (frm._customer_nif !== undefined) {
        return frm._customer_nif;
    }

    if (!frm.doc.customer || frm.doc.customer === 'Consumidor Final') return null;

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

function get_payment_modes(frm) {
    /**
     * Obter modos de pagamento
     */

    if (!frm.doc.payments || frm.doc.payments.length === 0) {
        return 'Não definido';
    }

    let modes = frm.doc.payments.map(p => p.mode_of_payment).join(', ');
    return modes || 'Não definido';
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

    // ✅ DEFINIR CLIENTE PADRÃO SE NECESSÁRIO
    if (!frm.doc.customer && (frm.doc.grand_total || 0) <= 1000) {
        frm.doc.customer = 'Consumidor Final';
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

function load_customer_tax_info(frm) {
    /**
     * Carregar informações fiscais do cliente
     */

    if (!frm.doc.customer || frm.doc.customer === 'Consumidor Final') return;

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

    // ✅ CAMPOS OBRIGATÓRIOS PARA POS PORTUGUESAS
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('posting_date', true);

    // ✅ CLIENTE OBRIGATÓRIO SE VALOR > €1000
    if (check_nif_required(frm)) {
        frm.toggle_reqd('customer', true);
    }
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
    frm.meta.default_print_format = "Fatura Simplificada Portugal";
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
        message: __('Fatura POS portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR TOTAL
    frm.dashboard.add_indicator(__('Total: €{0}', [(frm.doc.grand_total || 0).toFixed(2)]), 'blue');

    // ✅ SUGERIR IMPRESSÃO TÉRMICA
    if (frm.doc.docstatus === 1) {
        frappe.msgprint({
            title: __('Fatura Submetida'),
            message: __('Deseja imprimir o recibo térmico agora?'),
            primary_action: {
                label: __('Imprimir'),
                action: function() {
                    print_thermal_receipt(frm);
                }
            }
        });
    }
}

function validate_customer_nif_manual(frm) {
    /**
     * Validar NIF do cliente manualmente
     */

    if (!frm.doc.customer || frm.doc.customer === 'Consumidor Final') {
        frappe.msgprint(__('Selecione um cliente com NIF primeiro'));
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

frappe.ui.form.on('POS Invoice Item', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR IMPOSTOS QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            validate_portuguese_taxes(frm);
            check_simplified_invoice_limit(frm);
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
            check_simplified_invoice_limit(frm);
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    }
});

// ========== EVENTOS DE PAYMENTS ==========

frappe.ui.form.on('POS Invoice Payment', {
    amount: function(frm, cdt, cdn) {
        // ✅ RECALCULAR QUANDO PAGAMENTO MUDA
        setTimeout(() => {
            if (frm.pos_section_added) {
                // Atualizar seção POS
                $('.pos-info').remove();
                frm.pos_section_added = false;
                add_pos_section(frm);
            }
        }, 100);
    }
});

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('POS Invoice', {
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
            "Série portuguesa para POS. Formato: FS2025EMPRESA.#### (FS=Fatura Simplificada)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para POS.";
    }

    if (frm.fields_dict.qr_code) {
        frm.fields_dict.qr_code.df.description =
            "QR Code obrigatório para faturas POS portuguesas";
    }

    if (frm.fields_dict.customer) {
        frm.fields_dict.customer.df.description =
            "Cliente obrigatório para valores acima de €1000. Use 'Consumidor Final' para valores menores.";
    }

    if (frm.fields_dict.grand_total) {
        frm.fields_dict.grand_total.df.description =
            "Limite €1000 sem NIF do cliente para faturas simplificadas";
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

    // ✅ CTRL+Q para gerar QR Code
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+q',
        action: () => {
            if (frm.doc.atcud_code && !frm.doc.qr_code) {
                generate_qr_code_manually(frm);
            }
        },
        description: __('Gerar QR Code'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir térmica
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_thermal_receipt(frm);
            }
        },
        description: __('Imprimir Térmica'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+R para reimprimir
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+r',
        action: () => {
            if (frm.doc.docstatus === 1) {
                reprint_pos_invoice(frm);
            }
        },
        description: __('Reimprimir Fatura'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+C para converter
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+c',
        action: () => {
            if (frm.doc.docstatus === 1 && frm.doc.grand_total > 1000) {
                convert_to_sales_invoice(frm);
            }
        },
        description: __('Converter em Fatura'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('POS Invoice', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_company(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form pos-invoice-pt');

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

    // ✅ OBSERVAR MUDANÇAS NO CLIENTE
    frm.fields_dict.customer && frm.fields_dict.customer.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.customer) {
                validate_customer_nif(frm);
                load_customer_tax_info(frm);
                check_pos_nif_limit(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO TOTAL
    frm.fields_dict.grand_total && frm.fields_dict.grand_total.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.grand_total) {
                check_simplified_invoice_limit(frm);

                // Atualizar seções visuais
                if (frm.compliance_section_added) {
                    $('.portugal-compliance-info').remove();
                    frm.compliance_section_added = false;
                    add_compliance_section(frm);
                }

                if (frm.pos_section_added) {
                    $('.pos-info').remove();
                    frm.pos_section_added = false;
                    add_pos_section(frm);
                }
            }
        }, 100);
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_pos_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para POS
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

    // ✅ VERIFICAR QR CODE
    if (!frm.doc.qr_code) {
        compliance_issues.push({
            type: 'warning',
            message: 'QR Code será gerado automaticamente'
        });
    }

    // ✅ VERIFICAR LIMITE SEM NIF
    if (check_nif_required(frm) && !get_customer_nif(frm)) {
        compliance_issues.push({
            type: 'error',
            message: 'Valor acima de €1000 requer NIF do cliente'
        });
    }

    // ✅ VERIFICAR IMPOSTOS
    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        compliance_issues.push({
            type: 'warning',
            message: 'Impostos portugueses não configurados'
        });
    }

    // ✅ VERIFICAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        compliance_issues.push({
            type: 'error',
            message: 'Pelo menos um item é obrigatório'
        });
    }

    return compliance_issues;
}

function show_compliance_report(frm) {
    /**
     * ✅ NOVA: Mostrar relatório completo de compliance
     */

    let issues = validate_pos_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Fatura POS</h5>

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

function generate_pos_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo da POS
     */

    let tax_info = calculate_tax_breakdown(frm);
    let customer_nif = get_customer_nif(frm);
    let payment_modes = get_payment_modes(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo POS'),
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
        <div class="pos-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório POS - Fatura Simplificada</h3>
                <p><strong>Fatura:</strong> ${frm.doc.name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}</p>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <h5>Dados da Empresa</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Empresa:</strong></td><td>${frm.doc.company}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                        <tr><td><strong>Série:</strong></td><td>${frm.doc.naming_series || 'N/A'}</td></tr>
                        <tr><td><strong>QR Code:</strong></td><td>${frm.doc.qr_code ? 'Gerado' : 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Dados do Cliente</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Nome:</strong></td><td>${frm.doc.customer_name || 'Consumidor Final'}</td></tr>
                        <tr><td><strong>NIF:</strong></td><td>${customer_nif || 'N/A'}</td></tr>
                        <tr><td><strong>Limite €1000:</strong></td><td style="color: ${(frm.doc.grand_total || 0) <= 1000 ? 'green' : 'red'}">${(frm.doc.grand_total || 0) <= 1000 ? 'OK' : 'EXCEDIDO'}</td></tr>
                        <tr><td><strong>Tipo Fatura:</strong></td><td>Simplificada (POS)</td></tr>
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

            <h5>Pagamentos</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Modo</th><th style="text-align: right;">Valor</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.payments) {
        frm.doc.payments.forEach(function(payment) {
            html += `
                <tr>
                    <td>${payment.mode_of_payment}</td>
                    <td style="text-align: right;">€${(payment.amount || 0).toFixed(2)}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>

            <h5>Itens da Fatura (${frm.doc.items ? frm.doc.items.length : 0})</h5>
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
                <p><strong>Tipo Documento:</strong> Fatura Simplificada (POS)</p>
                <p><strong>Modos de Pagamento:</strong> ${payment_modes}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== FUNÇÕES DE AUDITORIA POS ==========

function create_pos_audit_log(frm) {
    /**
     * ✅ NOVA: Criar log de auditoria para POS
     */

    if (!frm.doc.docstatus === 1) return;

    let audit_data = {
        document_type: frm.doc.doctype,
        document_name: frm.doc.name,
        atcud_code: frm.doc.atcud_code,
        qr_code: frm.doc.qr_code ? 'Generated' : 'Not Generated',
        customer: frm.doc.customer,
        customer_nif: get_customer_nif(frm),
        total_amount: frm.doc.grand_total,
        currency: frm.doc.currency,
        posting_date: frm.doc.posting_date,
        pos_profile: frm.doc.pos_profile,
        payment_modes: get_payment_modes(frm),
        nif_required: check_nif_required(frm),
        compliance_status: get_compliance_status(frm).label,
        created_by: frappe.session.user,
        created_at: frappe.datetime.now_datetime()
    };

    frappe.call({
        method: 'portugal_compliance.api.create_pos_audit_log',
        args: {
            audit_data: audit_data
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                console.log('POS audit log created:', frm.doc.name);
            }
        }
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance POS Invoice JS loaded - Version 2.0.0');
