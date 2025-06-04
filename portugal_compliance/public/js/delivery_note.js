// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Delivery Note JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (GT2025NDX em vez de GT-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (GT)
 * ✅ Geração automática de ATCUD para guias de transporte
 * ✅ Validação de compliance português para transporte
 * ✅ Interface otimizada para guias de transporte portuguesas
 */

frappe.ui.form.on('Delivery Note', {
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

        // ✅ CONFIGURAR VALIDAÇÕES DE TRANSPORTE
        setup_transport_validations(frm);
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

            // ✅ CARREGAR ENDEREÇO DE ENTREGA
            load_delivery_address_info(frm);
        }
    },

    // ========== EVENTOS DE ENDEREÇOS ==========
    shipping_address_name: function(frm) {
        if (frm.doc.shipping_address_name) {
            validate_shipping_address(frm);
        }
    },

    customer_address: function(frm) {
        if (frm.doc.customer_address) {
            validate_customer_address(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_delivery_note(frm);
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

    // ✅ FILTRO PARA ARMAZÉNS DA EMPRESA
    frm.set_query("set_warehouse", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "disabled": 0
            }
        };
    });

    // ✅ FILTRO PARA TRANSPORTADORAS
    frm.set_query("transporter", function() {
        return {
            filters: {
                "supplier_group": "Transportadoras"
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para guias de transporte";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para guias de transporte (GT2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPOS DE TRANSPORTE
    if (frm.fields_dict.lr_no) {
        frm.fields_dict.lr_no.df.label = "Nº Guia de Transporte";
        frm.fields_dict.lr_no.df.description = "Número da guia de transporte conforme legislação portuguesa";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE PESO TOTAL
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

    // ✅ EVENTO PARA CÁLCULO DE PESO TOTAL
    $(frm.wrapper).on('items_updated', function() {
        calculate_total_weight(frm);
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
     * Configurar layout específico para guias de transporte portuguesas
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

    // ✅ ADICIONAR SEÇÃO DE TRANSPORTE
    add_transport_section(frm);
}

function add_compliance_section(frm) {
    /**
     * Adicionar seção de informações de compliance
     */

    let total_weight = calculate_total_weight(frm);
    let total_qty = calculate_total_qty(frm);

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações de Compliance Português - Guia de Transporte
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>ATCUD:</strong> ${frm.doc.atcud_code || 'Não gerado'}<br>
                    <strong>Série:</strong> ${frm.doc.naming_series || 'Não definida'}<br>
                    <strong>Cliente:</strong> ${frm.doc.customer_name || ''}
                </div>
                <div class="col-md-6">
                    <strong>Status:</strong> <span class="indicator ${get_compliance_status(frm).color}">${get_compliance_status(frm).label}</span><br>
                    <strong>Peso Total:</strong> ${total_weight} kg<br>
                    <strong>Qtd Total:</strong> ${total_qty}
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

function add_transport_section(frm) {
    /**
     * Adicionar seção específica de transporte
     */

    if (frm.doc.__islocal) return;

    let transport_html = `
        <div class="transport-info" style="
            background: #e3f2fd;
            border: 1px solid #90caf9;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #1565c0;">
                🚛 Informações de Transporte
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Transportadora:</strong> ${frm.doc.transporter_name || 'Não definida'}<br>
                    <strong>Nº Guia:</strong> ${frm.doc.lr_no || 'Não definido'}<br>
                    <strong>Data Expedição:</strong> ${frappe.datetime.str_to_user(frm.doc.posting_date)}
                </div>
                <div class="col-md-6">
                    <strong>Endereço Entrega:</strong> ${frm.doc.shipping_address || 'Não definido'}<br>
                    <strong>Contacto:</strong> ${frm.doc.contact_person || 'Não definido'}<br>
                    <strong>Observações:</strong> ${frm.doc.instructions || 'Nenhuma'}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.transport_section_added) {
        $(frm.fields_dict.customer.wrapper).after(transport_html);
        frm.transport_section_added = true;
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

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Guia conforme legislação portuguesa'
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

    // ✅ BOTÃO PARA VALIDAR ENDEREÇOS
    if (frm.doc.customer) {
        frm.add_custom_button(__('Validar Endereços'), function() {
            validate_all_addresses(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA CALCULAR PESO TOTAL
    if (frm.doc.items && frm.doc.items.length > 0) {
        frm.add_custom_button(__('Calcular Peso'), function() {
            calculate_and_show_weight(frm);
        }, __('Transporte'));
    }

    // ✅ BOTÃO PARA IMPRIMIR GUIA PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Guia PT'), function() {
            print_portuguese_delivery_note(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VALIDAR NIF CLIENTE
    if (frm.doc.customer) {
        frm.add_custom_button(__('Validar NIF Cliente'), function() {
            validate_customer_nif_manual(frm);
        }, __('Validações'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA GUIAS (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
        args: {
            doctype: 'Delivery Note',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS GT (formato SEM HÍFENS: GT2025NDX)
                let gt_series = r.message.series.filter(s => s.prefix.startsWith('GT'));
                let communicated_series = gt_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : gt_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE GT
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série GT comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série GT não comunicada selecionada. Comunique à AT antes de submeter.'),
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
            message: __('Para compliance português, use séries no formato GT2025EMPRESA.####'),
            indicator: 'red'
        });
        frm.set_value('naming_series', '');
        return;
    }

    // ✅ VERIFICAR SE É SÉRIE DE GUIA DE TRANSPORTE (formato SEM HÍFENS)
    let prefix = frm.doc.naming_series.replace('.####', '');
    let doc_code = prefix.substring(0, 2); // Primeiros 2 caracteres: GT

    if (doc_code !== 'GT') {
        frappe.msgprint({
            title: __('Série Incorreta'),
            message: __('Para Delivery Note, use séries GT (Guia de Transporte)'),
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
        message = __('Série GT comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série GT não comunicada à AT. Comunique antes de submeter guias.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_delivery_note(frm) {
    /**
     * Validações específicas para guias de transporte portuguesas
     */

    let errors = [];

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming Series é obrigatória para empresas portuguesas'));
    } else if (!is_portuguese_naming_series(frm.doc.naming_series)) {
        errors.push(__('Use naming series portuguesa (formato GT2025EMPRESA.####)'));
    }

    // ✅ VALIDAR CLIENTE
    if (!frm.doc.customer) {
        errors.push(__('Cliente é obrigatório'));
    }

    // ✅ VALIDAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        errors.push(__('Pelo menos um item é obrigatório'));
    }

    // ✅ VALIDAR ENDEREÇO DE ENTREGA
    if (!frm.doc.shipping_address_name) {
        errors.push(__('Endereço de entrega é obrigatório para guias de transporte'));
    }

    // ✅ VALIDAR PESO TOTAL (SE CONFIGURADO)
    let total_weight = calculate_total_weight(frm);
    if (total_weight === 0) {
        errors.push(__('Configure o peso dos itens para compliance de transporte'));
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
                validate_nif_format(frm, r.message.tax_id);
            }
        }
    });
}

function validate_nif_format(frm, nif) {
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
                        message: __('NIF cliente válido: {0}', [nif]),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('NIF cliente inválido: {0}', [nif]),
                        indicator: 'red'
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

    if (!frm.doc.shipping_address_name) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.shipping_address_name},
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
                        message: __('Endereço incompleto: falta {0}', [errors.join(', ')]),
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Endereço de entrega válido'),
                        indicator: 'green'
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

        // ✅ VALIDAR ATCUD OBRIGATÓRIO
        if (!frm.doc.atcud_code) {
            validations.push(__('ATCUD é obrigatório para guias de transporte portuguesas'));
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
                        validations.push(__('Série GT deve estar comunicada à AT antes da submissão'));
                    }

                    // ✅ VALIDAR ENDEREÇO OBRIGATÓRIO
                    if (!frm.doc.shipping_address_name) {
                        validations.push(__('Endereço de entrega é obrigatório'));
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

// ========== FUNÇÕES DE TRANSPORTE ==========

function setup_transport_validations(frm) {
    /**
     * Configurar validações específicas de transporte
     */

    // ✅ VALIDAR PESO DOS ITENS
    if (frm.fields_dict.items && frm.fields_dict.items.grid) {
        frm.fields_dict.items.grid.get_field('weight_per_unit').df.onchange = function() {
            calculate_total_weight(frm);
        };

        // ✅ VALIDAR QUANTIDADE
        frm.fields_dict.items.grid.get_field('qty').df.onchange = function() {
            calculate_total_weight(frm);
            calculate_total_qty(frm);
        };
    }
}

function calculate_total_weight(frm) {
    /**
     * Calcular peso total da guia
     */

    let total_weight = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let weight_per_unit = item.weight_per_unit || 0;
            let qty = item.qty || 0;
            total_weight += (weight_per_unit * qty);
        });
    }

    return total_weight;
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

function calculate_and_show_weight(frm) {
    /**
     * Calcular e mostrar peso total
     */

    let total_weight = calculate_total_weight(frm);
    let total_qty = calculate_total_qty(frm);

    frappe.msgprint({
        title: __('Informações de Transporte'),
        message: `
            <table class="table table-bordered">
                <tr><td><strong>Quantidade Total:</strong></td><td>${total_qty}</td></tr>
                <tr><td><strong>Peso Total:</strong></td><td>${total_weight} kg</td></tr>
                <tr><td><strong>Peso Médio/Item:</strong></td><td>${total_qty > 0 ? (total_weight / total_qty).toFixed(2) : 0} kg</td></tr>
            </table>
        `,
        indicator: 'blue'
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
        title: __('Status da Série GT'),
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
                <tr><td><strong>Tipo:</strong></td><td>Guia de Transporte</td></tr>
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

function validate_all_addresses(frm) {
    /**
     * Validar todos os endereços
     */

    let addresses_to_check = [];

    if (frm.doc.customer_address) {
        addresses_to_check.push({name: frm.doc.customer_address, type: 'Cliente'});
    }

    if (frm.doc.shipping_address_name) {
        addresses_to_check.push({name: frm.doc.shipping_address_name, type: 'Entrega'});
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

function print_portuguese_delivery_note(frm) {
    /**
     * Imprimir guia com formato português
     */

    frappe.route_options = {
        "format": "Guia de Transporte Portugal"
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
     * ✅ CORRIGIDO: Verificar se naming series é portuguesa (formato SEM HÍFENS)
     */

    if (!naming_series) return false;

    // ✅ PADRÃO PORTUGUÊS SEM HÍFENS: XXYYYY + COMPANY.####
    const pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$/;
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

    // ✅ CALCULAR PESO TOTAL
    let total_weight = calculate_total_weight(frm);
    if (total_weight > 0) {
        frm.doc.total_net_weight = total_weight;
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

function load_delivery_address_info(frm) {
    /**
     * Carregar informações do endereço de entrega
     */

    if (!frm.doc.shipping_address_name) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.shipping_address_name},
            fieldname: ['city', 'country', 'pincode']
        },
        callback: function(r) {
            if (r.message) {
                frm._delivery_address_info = r.message;
            }
        }
    });
}

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA GUIAS DE TRANSPORTE PORTUGUESAS
    frm.toggle_reqd('customer', true);
    frm.toggle_reqd('naming_series', true);
    frm.toggle_reqd('shipping_address_name', true);
    frm.toggle_reqd('posting_date', true);
}

function setup_print_formats(frm) {
    /**
     * Configurar print formats portugueses
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ DEFINIR PRINT FORMAT PADRÃO
    frm.meta.default_print_format = "Guia de Transporte Portugal";
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
        message: __('Guia de transporte portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR INFORMAÇÕES DE TRANSPORTE
    let total_weight = calculate_total_weight(frm);
    if (total_weight > 0) {
        frm.dashboard.add_indicator(__('Peso Total: {0} kg', [total_weight]), 'blue');
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

function validate_customer_address(frm) {
    /**
     * Validar endereço do cliente
     */

    if (!frm.doc.customer_address) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Address',
            filters: {name: frm.doc.customer_address},
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
                        message: __('Endereço cliente incompleto: falta {0}', [errors.join(', ')]),
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Endereço cliente válido'),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

// ========== EVENTOS DE ITEMS ==========

frappe.ui.form.on('Delivery Note Item', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR PESO QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            calculate_total_weight(frm);
            if (frm.compliance_section_added) {
                // Atualizar seção de compliance
                $('.portugal-compliance-info').remove();
                frm.compliance_section_added = false;
                add_compliance_section(frm);
            }
        }, 100);
    },

    weight_per_unit: function(frm, cdt, cdn) {
        // ✅ RECALCULAR PESO QUANDO PESO UNITÁRIO MUDA
        setTimeout(() => {
            calculate_total_weight(frm);
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

frappe.ui.form.on('Delivery Note', {
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
            "Série portuguesa para guias de transporte. Formato: GT2025EMPRESA.#### (GT=Guia de Transporte)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para guias.";
    }

    if (frm.fields_dict.shipping_address_name) {
        frm.fields_dict.shipping_address_name.df.description =
            "Endereço de entrega obrigatório para guias de transporte portuguesas";
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

    // ✅ CTRL+W para calcular peso
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+w',
        action: () => {
            if (frm.doc.items && frm.doc.items.length > 0) {
                calculate_and_show_weight(frm);
            }
        },
        description: __('Calcular Peso Total'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+P para imprimir formato português
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+p',
        action: () => {
            if (frm.doc.docstatus === 1) {
                print_portuguese_delivery_note(frm);
            }
        },
        description: __('Imprimir Guia Portuguesa'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('Delivery Note', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_company(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form delivery-note-pt');

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
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO ENDEREÇO DE ENTREGA
    frm.fields_dict.shipping_address_name && frm.fields_dict.shipping_address_name.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.shipping_address_name) {
                validate_shipping_address(frm);
                load_delivery_address_info(frm);
            }
        }, 100);
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Delivery Note JS loaded - Version 2.0.0');
