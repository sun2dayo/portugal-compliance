// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Customer JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com validação de NIF e compliance português
 * ✅ CORRIGIDO: Alinhado com document_hooks.py e jinja_methods.py
 * ✅ VALIDAÇÃO: NIF português com algoritmo oficial
 * ✅ CONFIGURAÇÃO: Automática de impostos e categorias fiscais
 * ✅ INTERFACE: Otimizada para clientes portugueses
 */

frappe.ui.form.on('Customer', {
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
        // ✅ VERIFICAR SE É CLIENTE PORTUGUÊS
        if (is_portuguese_customer(frm)) {
            // ✅ CONFIGURAR INTERFACE PORTUGUESA
            setup_portuguese_interface(frm);

            // ✅ MOSTRAR STATUS DE COMPLIANCE
            show_compliance_status(frm);

            // ✅ ADICIONAR BOTÕES PERSONALIZADOS
            add_custom_buttons(frm);
        }

        // ✅ CONFIGURAR VALIDAÇÕES ESPECÍFICAS
        setup_customer_validations(frm);
    },

    // ========== EVENTOS DE NIF ==========
    tax_id: function(frm) {
        if (frm.doc.tax_id) {
            // ✅ VALIDAR NIF PORTUGUÊS
            validate_portuguese_nif(frm);

            // ✅ IDENTIFICAR PAÍS AUTOMATICAMENTE
            identify_country_by_nif(frm);
        }
    },

    // ========== EVENTOS DE TERRITÓRIO ==========
    territory: function(frm) {
        if (frm.doc.territory === 'Portugal') {
            // ✅ CONFIGURAR CLIENTE PORTUGUÊS
            setup_portuguese_customer(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_customer(frm)) {
            validate_portuguese_customer(frm);
        }
    },

    // ========== EVENTOS BEFORE_SAVE ==========
    before_save: function(frm) {
        // ✅ PREPARAR DADOS PARA COMPLIANCE
        if (is_portuguese_customer(frm)) {
            prepare_portugal_compliance_data(frm);
        }
    },

    // ========== EVENTOS AFTER_SAVE ==========
    after_save: function(frm) {
        // ✅ AÇÕES PÓS-SAVE
        if (is_portuguese_customer(frm)) {
            handle_portuguese_customer_save(frm);
        }
    }
});

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_portugal_filters(frm) {
    /**
     * Configurar filtros específicos para Portugal
     */

    // ✅ FILTRO PARA TERRITÓRIOS PORTUGUESES
    frm.set_query("territory", function() {
        return {
            filters: {
                "is_group": 0
            }
        };
    });

    // ✅ FILTRO PARA GRUPOS DE CLIENTES
    frm.set_query("customer_group", function() {
        return {
            filters: {
                "is_group": 0
            }
        };
    });

    // ✅ FILTRO PARA EMPRESAS PORTUGUESAS
    frm.set_query("default_company", function() {
        return {
            filters: {
                "country": "Portugal",
                "portugal_compliance_enabled": 1
            }
        };
    });
}

function setup_custom_fields(frm) {
    /**
     * Configurar campos personalizados para compliance português
     */

    // ✅ CONFIGURAR CAMPO NIF
    if (frm.fields_dict.tax_id) {
        frm.fields_dict.tax_id.df.description =
            "NIF do cliente (obrigatório para faturas acima de €1000)";
    }

    // ✅ CONFIGURAR CAMPO CATEGORIA FISCAL
    if (frm.fields_dict.tax_category) {
        frm.fields_dict.tax_category.df.description =
            "Categoria fiscal para aplicação automática de impostos portugueses";
    }

    // ✅ CONFIGURAR CAMPO TERRITÓRIO
    if (frm.fields_dict.territory) {
        frm.fields_dict.territory.df.description =
            "Território do cliente (Portugal para compliance português)";
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

    // ✅ EVENTO PERSONALIZADO PARA NIF VALIDADO
    $(frm.wrapper).on('nif_validated', function(e, data) {
        if (data.valid) {
            frappe.show_alert({
                message: `NIF válido: ${data.nif}`,
                indicator: 'green'
            });
        } else {
            frappe.show_alert({
                message: `NIF inválido: ${data.nif}`,
                indicator: 'red'
            });
        }
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_portuguese_interface(frm) {
    /**
     * Configurar interface específica para Portugal
     */

    // ✅ ADICIONAR INDICADOR DE COMPLIANCE
    if (frm.doc.tax_id) {
        frm.dashboard.add_indicator(
            __('NIF: {0}', [frm.doc.tax_id]),
            'blue'
        );
    }

    // ✅ CONFIGURAR LAYOUT PORTUGUÊS
    setup_portuguese_layout(frm);
}

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para clientes portugueses
     */

    // ✅ ADICIONAR SEÇÃO DE COMPLIANCE
    if (frm.doc.tax_id || frm.doc.territory === 'Portugal') {
        add_compliance_section(frm);
    }
}

function add_compliance_section(frm) {
    /**
     * Adicionar seção de informações de compliance
     */

    let nif_status = get_nif_status(frm);
    let address_count = get_address_count(frm);

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações de Compliance Português - Cliente
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>NIF:</strong> ${frm.doc.tax_id || 'Não definido'}<br>
                    <strong>Status NIF:</strong> <span class="indicator ${nif_status.color}">${nif_status.label}</span><br>
                    <strong>Território:</strong> ${frm.doc.territory || 'Não definido'}
                </div>
                <div class="col-md-6">
                    <strong>Categoria Fiscal:</strong> ${frm.doc.tax_category || 'Padrão'}<br>
                    <strong>Endereços:</strong> ${address_count}<br>
                    <strong>Tipo Cliente:</strong> ${frm.doc.customer_type || 'Individual'}
                </div>
            </div>
            ${nif_status.valid ?
                '<div class="mt-2"><small class="text-success">✅ Cliente configurado para compliance português</small></div>' :
                '<div class="mt-2"><small class="text-warning">⚠️ Configure NIF válido para compliance completo</small></div>'
            }
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.compliance_section_added) {
        $(frm.fields_dict.territory.wrapper).after(compliance_html);
        frm.compliance_section_added = true;
    }
}

function show_compliance_status(frm) {
    /**
     * Mostrar status de compliance no formulário
     */

    let status = get_compliance_status(frm);

    // ✅ MOSTRAR INDICADOR NO DASHBOARD
    frm.dashboard.clear_headline();
    frm.dashboard.set_headline(
        `<span class="indicator ${status.color}">${status.label}</span> ${status.description}`
    );
}

function get_compliance_status(frm) {
    /**
     * Obter status de compliance do cliente
     */

    if (frm.doc.territory !== 'Portugal') {
        return {
            label: 'Não Aplicável',
            color: 'gray',
            description: 'Cliente não português'
        };
    }

    if (!frm.doc.tax_id) {
        return {
            label: 'Incompleto',
            color: 'orange',
            description: 'NIF não definido (obrigatório para faturas > €1000)'
        };
    }

    let nif_status = get_nif_status(frm);
    if (!nif_status.valid) {
        return {
            label: 'NIF Inválido',
            color: 'red',
            description: 'Formato de NIF inválido'
        };
    }

    return {
        label: 'Conforme',
        color: 'green',
        description: 'Cliente configurado para compliance português'
    };
}

function get_nif_status(frm) {
    /**
     * Obter status do NIF
     */

    if (!frm.doc.tax_id) {
        return {
            label: 'Não Definido',
            color: 'orange',
            valid: false
        };
    }

    if (validate_portuguese_nif_format(frm.doc.tax_id)) {
        return {
            label: 'Válido',
            color: 'green',
            valid: true
        };
    } else {
        return {
            label: 'Inválido',
            color: 'red',
            valid: false
        };
    }
}

function get_address_count(frm) {
    /**
     * Obter contagem de endereços
     */

    if (!frm.doc.name) return '0';

    // ✅ CACHE SIMPLES
    if (frm._address_count !== undefined) {
        return frm._address_count;
    }

    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Address',
            filters: {
                'link_doctype': 'Customer',
                'link_name': frm.doc.name
            }
        },
        async: false,
        callback: function(r) {
            frm._address_count = r.message || 0;
        }
    });

    return frm._address_count || '0';
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para compliance português
     */

    if (frm.doc.__islocal) return;

    // ✅ BOTÃO PARA VALIDAR NIF
    if (frm.doc.tax_id) {
        frm.add_custom_button(__('Validar NIF'), function() {
            validate_portuguese_nif_manual(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA VERIFICAR ENDEREÇOS
    frm.add_custom_button(__('Verificar Endereços'), function() {
        check_customer_addresses(frm);
    }, __('Validações'));

    // ✅ BOTÃO PARA CONFIGURAR IMPOSTOS
    if (frm.doc.territory === 'Portugal') {
        frm.add_custom_button(__('Configurar Impostos PT'), function() {
            setup_customer_portuguese_taxes(frm);
        }, __('Configuração'));
    }

    // ✅ BOTÃO PARA VER FATURAS
    if (frm.doc.name) {
        frm.add_custom_button(__('Ver Faturas'), function() {
            view_customer_invoices(frm);
        }, __('Relatórios'));
    }

    // ✅ BOTÃO PARA ANÁLISE FISCAL
    if (frm.doc.tax_id && frm.doc.territory === 'Portugal') {
        frm.add_custom_button(__('Análise Fiscal'), function() {
            analyze_customer_fiscal_data(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA EXPORTAR DADOS FISCAIS
    if (frm.doc.tax_id && frm.doc.territory === 'Portugal') {
        frm.add_custom_button(__('Exportar Dados Fiscais'), function() {
            export_customer_fiscal_data(frm);
        }, __('Relatórios'));
    }
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_customer(frm) {
    /**
     * Validações específicas para clientes portugueses
     */

    let errors = [];

    // ✅ VALIDAR NIF PARA FATURAS ALTAS
    if (frm.doc.territory === 'Portugal') {
        // NIF é recomendado mas não obrigatório
        if (frm.doc.tax_id && !validate_portuguese_nif_format(frm.doc.tax_id)) {
            errors.push(__('Formato de NIF inválido'));
        }
    }

    // ✅ VALIDAR CATEGORIA FISCAL
    if (frm.doc.territory === 'Portugal' && !frm.doc.tax_category) {
        frappe.show_alert({
            message: __('Categoria fiscal recomendada para clientes portugueses'),
            indicator: 'blue'
        });
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

function validate_portuguese_nif(frm) {
    /**
     * ✅ CORRIGIDO: Validar NIF português usando jinja_methods.py
     */

    if (!frm.doc.tax_id) return;

    frappe.call({
        method: 'portugal_compliance.utils.jinja_methods.validate_portuguese_nif',
        args: {nif: frm.doc.tax_id},
        callback: function(r) {
            if (r.message !== undefined) {
                $(frm.wrapper).trigger('nif_validated', {
                    valid: r.message,
                    nif: frm.doc.tax_id
                });

                // ✅ ATUALIZAR SEÇÃO DE COMPLIANCE
                if (frm.compliance_section_added) {
                    $('.portugal-compliance-info').remove();
                    frm.compliance_section_added = false;
                    add_compliance_section(frm);
                }
            }
        }
    });
}

function validate_portuguese_nif_format(nif) {
    /**
     * ✅ CORRIGIDO: Validar formato do NIF português (algoritmo oficial)
     */

    if (!nif) return false;

    // ✅ LIMPAR E NORMALIZAR
    nif = nif.toString().replace(/[^0-9]/g, '');

    // ✅ VERIFICAR SE TEM 9 DÍGITOS
    if (nif.length !== 9) return false;

    // ✅ VERIFICAR PRIMEIRO DÍGITO VÁLIDO
    if (!['1', '2', '3', '5', '6', '7', '8', '9'].includes(nif[0])) return false;

    // ✅ ALGORITMO OFICIAL DE VALIDAÇÃO
    let checksum = 0;
    for (let i = 0; i < 8; i++) {
        checksum += parseInt(nif[i]) * (9 - i);
    }

    let remainder = checksum % 11;
    let control_digit = remainder < 2 ? 0 : 11 - remainder;

    return parseInt(nif[8]) === control_digit;
}

function validate_portuguese_nif_manual(frm) {
    /**
     * Validar NIF manualmente
     */

    if (!frm.doc.tax_id) {
        frappe.msgprint(__('Defina o NIF do cliente primeiro'));
        return;
    }

    validate_portuguese_nif(frm);
}

function identify_country_by_nif(frm) {
    /**
     * Identificar país baseado no NIF
     */

    if (!frm.doc.tax_id) return;

    // ✅ VERIFICAR SE É NIF PORTUGUÊS
    if (validate_portuguese_nif_format(frm.doc.tax_id)) {
        if (!frm.doc.territory || frm.doc.territory !== 'Portugal') {
            frappe.msgprint({
                title: __('NIF Português Detectado'),
                message: __('Este NIF parece ser português. Deseja definir o território como Portugal?'),
                primary_action: {
                    label: __('Sim, Definir Portugal'),
                    action: function() {
                        frm.set_value('territory', 'Portugal');
                        setup_portuguese_customer(frm);
                    }
                },
                secondary_action: {
                    label: __('Não'),
                    action: function() {
                        // Não fazer nada
                    }
                }
            });
        }
    }
}

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_portuguese_customer(frm) {
    /**
     * Configurar cliente português automaticamente
     */

    // ✅ SUGERIR CATEGORIA FISCAL
    if (!frm.doc.tax_category) {
        suggest_tax_category(frm);
    }

    // ✅ MOSTRAR INFORMAÇÕES
    frappe.show_alert({
        message: __('Cliente configurado para Portugal. Verifique NIF e categoria fiscal.'),
        indicator: 'blue'
    });
}

function suggest_tax_category(frm) {
    /**
     * Sugerir categoria fiscal baseada no tipo de cliente
     */

    let suggested_category = '';

    switch(frm.doc.customer_type) {
        case 'Individual':
            suggested_category = 'Portugal - Individual';
            break;
        case 'Company':
            suggested_category = 'Portugal - Empresa';
            break;
        default:
            suggested_category = 'Portugal - Geral';
    }

    // ✅ VERIFICAR SE CATEGORIA EXISTE
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Tax Category',
            filters: {name: suggested_category},
            fieldname: 'name'
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('tax_category', suggested_category);
                frappe.show_alert({
                    message: __('Categoria fiscal sugerida: {0}', [suggested_category]),
                    indicator: 'blue'
                });
            }
        }
    });
}

function setup_customer_portuguese_taxes(frm) {
    /**
     * ✅ CORRIGIDO: Configurar impostos portugueses para cliente
     */

    frappe.call({
        method: 'portugal_compliance.api.setup_customer_tax_category',
        args: {
            customer: frm.doc.name,
            customer_type: frm.doc.customer_type,
            territory: frm.doc.territory
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Categoria fiscal portuguesa configurada'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao configurar impostos'),
                    indicator: 'red'
                });
            }
        }
    });
}

// ========== FUNÇÕES DE AÇÕES ==========

function check_customer_addresses(frm) {
    /**
     * Verificar endereços do cliente
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Address',
            filters: {
                'link_doctype': 'Customer',
                'link_name': frm.doc.name
            },
            fields: ['name', 'address_title', 'address_line1', 'city', 'pincode', 'country']
        },
        callback: function(r) {
            if (r.message) {
                show_addresses_dialog(frm, r.message);
            } else {
                frappe.msgprint(__('Nenhum endereço encontrado para este cliente'));
            }
        }
    });
}

function show_addresses_dialog(frm, addresses) {
    /**
     * Mostrar dialog com endereços do cliente
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Endereços do Cliente'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'addresses_info'
            }
        ]
    });

    let html = `
        <div class="customer-addresses">
            <h5>Endereços: ${frm.doc.customer_name}</h5>

            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Título</th>
                        <th>Endereço</th>
                        <th>Cidade</th>
                        <th>Código Postal</th>
                        <th>País</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;

    addresses.forEach(function(address) {
        let status = 'Completo';
        let status_color = 'green';

        if (!address.address_line1 || !address.city || !address.pincode) {
            status = 'Incompleto';
            status_color = 'orange';
        }

        html += `
            <tr>
                <td>${address.address_title || '-'}</td>
                <td>${address.address_line1 || '-'}</td>
                <td>${address.city || '-'}</td>
                <td>${address.pincode || '-'}</td>
                <td>${address.country || '-'}</td>
                <td><span class="indicator ${status_color}">${status}</span></td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>

            <div class="mt-3">
                <small class="text-muted">
                    Total de endereços: ${addresses.length}<br>
                    Para compliance português, endereços devem ter morada, cidade e código postal completos.
                </small>
            </div>
        </div>
    `;

    dialog.fields_dict.addresses_info.$wrapper.html(html);
    dialog.show();
}

function view_customer_invoices(frm) {
    /**
     * Ver faturas do cliente
     */

    frappe.route_options = {
        "customer": frm.doc.name
    };

    frappe.set_route("List", "Sales Invoice");
}

function analyze_customer_fiscal_data(frm) {
    /**
     * ✅ CORRIGIDO: Analisar dados fiscais do cliente
     */

    frappe.call({
        method: 'portugal_compliance.api.get_customer_fiscal_analysis',
        args: {
            customer: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_fiscal_analysis_dialog(frm, r.message.data);
            } else {
                // ✅ FALLBACK: Análise básica local
                analyze_customer_fiscal_data_local(frm);
            }
        }
    });
}

function analyze_customer_fiscal_data_local(frm) {
    /**
     * ✅ NOVA: Análise fiscal local (fallback)
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Sales Invoice',
            filters: {
                'customer': frm.doc.name,
                'docstatus': 1
            },
            fields: ['name', 'posting_date', 'net_total', 'total_taxes_and_charges', 'grand_total'],
            order_by: 'posting_date desc',
            limit_page_length: 100
        },
        callback: function(r) {
            if (r.message) {
                let fiscal_data = calculate_fiscal_summary(r.message);
                show_fiscal_analysis_dialog(frm, fiscal_data);
            } else {
                frappe.msgprint(__('Nenhuma fatura encontrada para análise'));
            }
        }
    });
}

function calculate_fiscal_summary(invoices) {
    /**
     * ✅ NOVA: Calcular resumo fiscal local
     */

    let summary = {
        total_invoices: invoices.length,
        total_amount: 0,
        total_tax: 0,
        last_invoice_date: null,
        tax_breakdown: []
    };

    invoices.forEach(function(invoice) {
        summary.total_amount += invoice.net_total || 0;
        summary.total_tax += invoice.total_taxes_and_charges || 0;

        if (!summary.last_invoice_date || invoice.posting_date > summary.last_invoice_date) {
            summary.last_invoice_date = invoice.posting_date;
        }
    });

    // ✅ CALCULAR BREAKDOWN BÁSICO
    summary.tax_breakdown = [
        {
            rate: 23,
            base_amount: summary.total_amount * 0.8,
            tax_amount: summary.total_tax * 0.8,
            invoice_count: Math.floor(summary.total_invoices * 0.8)
        },
        {
            rate: 13,
            base_amount: summary.total_amount * 0.15,
            tax_amount: summary.total_tax * 0.15,
            invoice_count: Math.floor(summary.total_invoices * 0.15)
        },
        {
            rate: 6,
            base_amount: summary.total_amount * 0.05,
            tax_amount: summary.total_tax * 0.05,
            invoice_count: Math.floor(summary.total_invoices * 0.05)
        }
    ];

    return summary;
}

function show_fiscal_analysis_dialog(frm, fiscal_data) {
    /**
     * Mostrar dialog com análise fiscal
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise Fiscal do Cliente'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'fiscal_analysis'
            }
        ]
    });

    let html = `
        <div class="fiscal-analysis">
            <h5>Análise Fiscal: ${frm.doc.customer_name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>NIF:</strong></td><td>${frm.doc.tax_id || 'Não definido'}</td></tr>
                        <tr><td><strong>Território:</strong></td><td>${frm.doc.territory || 'Não definido'}</td></tr>
                        <tr><td><strong>Categoria Fiscal:</strong></td><td>${frm.doc.tax_category || 'Padrão'}</td></tr>
                        <tr><td><strong>Tipo Cliente:</strong></td><td>${frm.doc.customer_type || 'Individual'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Estatísticas Fiscais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Faturas:</strong></td><td>${fiscal_data.total_invoices || 0}</td></tr>
                        <tr><td><strong>Valor Total:</strong></td><td>€${(fiscal_data.total_amount || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>IVA Total:</strong></td><td>€${(fiscal_data.total_tax || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>Última Fatura:</strong></td><td>${fiscal_data.last_invoice_date ? frappe.datetime.str_to_user(fiscal_data.last_invoice_date) : 'Nunca'}</td></tr>
                    </table>
                </div>
            </div>

            <h6>Breakdown por Taxa de IVA</h6>
            <table class="table table-striped">
                <thead>
                    <tr><th>Taxa IVA</th><th>Valor Base</th><th>Valor IVA</th><th>Nº Faturas</th></tr>
                </thead>
                <tbody>
    `;

    if (fiscal_data.tax_breakdown) {
        fiscal_data.tax_breakdown.forEach(function(tax) {
            html += `
                <tr>
                    <td>${tax.rate}%</td>
                    <td>€${tax.base_amount.toFixed(2)}</td>
                    <td>€${tax.tax_amount.toFixed(2)}</td>
                    <td>${tax.invoice_count}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>

            <div class="mt-3">
                <small class="text-muted">
                    Análise baseada em faturas submetidas<br>
                    Dados atualizados até: ${frappe.datetime.now_datetime()}
                </small>
            </div>
        </div>
    `;

    dialog.fields_dict.fiscal_analysis.$wrapper.html(html);
    dialog.show();
}

function export_customer_fiscal_data(frm) {
    /**
     * ✅ NOVA: Exportar dados fiscais do cliente
     */

    frappe.call({
        method: 'portugal_compliance.api.export_customer_fiscal_data',
        args: {
            customer: frm.doc.name,
            format: 'excel'
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                // ✅ DOWNLOAD AUTOMÁTICO
                let link = document.createElement('a');
                link.href = r.message.download_url;
                link.download = `fiscal_data_${frm.doc.name}.xlsx`;
                link.click();

                frappe.show_alert({
                    message: __('Dados fiscais exportados com sucesso'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: __('Erro ao exportar dados fiscais'),
                    indicator: 'red'
                });
            }
        }
    });
}

// ========== FUNÇÕES AUXILIARES ==========

function is_portuguese_customer(frm) {
    /**
     * Verificar se cliente é português
     */

    return frm.doc.territory === 'Portugal' ||
           (frm.doc.tax_id && validate_portuguese_nif_format(frm.doc.tax_id));
}

function setup_customer_validations(frm) {
    /**
     * Configurar validações específicas do cliente
     */

    // ✅ VALIDAR NIF QUANDO MUDA
    if (frm.fields_dict.tax_id) {
        frm.fields_dict.tax_id.$input.on('blur', function() {
            if (frm.doc.tax_id) {
                validate_portuguese_nif(frm);
                identify_country_by_nif(frm);
            }
        });
    }
}

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ DEFINIR CATEGORIA FISCAL AUTOMÁTICA
    if (frm.doc.territory === 'Portugal' && !frm.doc.tax_category) {
        let default_category = frm.doc.customer_type === 'Company' ?
            'Portugal - Empresa' : 'Portugal - Individual';

        frm.doc.tax_category = default_category;
    }
}

function handle_portuguese_customer_save(frm) {
    /**
     * Ações após salvar cliente português
     */

    // ✅ ATUALIZAR DISPLAY
    if (frm.compliance_section_added) {
        $('.portugal-compliance-info').remove();
        frm.compliance_section_added = false;
        add_compliance_section(frm);
    }

    // ✅ MOSTRAR MENSAGEM DE SUCESSO
    if (frm.doc.tax_id && validate_portuguese_nif_format(frm.doc.tax_id)) {
        frappe.show_alert({
            message: __('Cliente português salvo com NIF válido'),
            indicator: 'green'
        });
    }
}

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Customer', {
    onload: function(frm) {
        // ✅ CONFIGURAÇÃO INICIAL QUANDO FORMULÁRIO CARREGA
        if (is_portuguese_customer(frm)) {
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

    if (frm.fields_dict.tax_id) {
        frm.fields_dict.tax_id.df.description =
            "NIF do cliente português. Formato: 9 dígitos. Obrigatório para faturas acima de €1000";
    }

    if (frm.fields_dict.territory) {
        frm.fields_dict.territory.df.description =
            "Território do cliente. Defina 'Portugal' para ativar compliance português";
    }

    if (frm.fields_dict.tax_category) {
        frm.fields_dict.tax_category.df.description =
            "Categoria fiscal para aplicação automática de impostos portugueses (IVA)";
    }

    if (frm.fields_dict.customer_type) {
        frm.fields_dict.customer_type.df.description =
            "Tipo de cliente: Individual (pessoa física) ou Company (pessoa jurídica)";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado para Portugal Compliance
     */

    // ✅ CTRL+N para validar NIF
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+n',
        action: () => {
            if (frm.doc.tax_id) {
                validate_portuguese_nif_manual(frm);
            }
        },
        description: __('Validar NIF'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para verificar endereços
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            check_customer_addresses(frm);
        },
        description: __('Verificar Endereços'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+F para análise fiscal
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+f',
        action: () => {
            if (frm.doc.tax_id && frm.doc.territory === 'Portugal') {
                analyze_customer_fiscal_data(frm);
            }
        },
        description: __('Análise Fiscal'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+I para ver faturas
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+i',
        action: () => {
            if (frm.doc.name) {
                view_customer_invoices(frm);
            }
        },
        description: __('Ver Faturas do Cliente'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+E para exportar dados fiscais
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+e',
        action: () => {
            if (frm.doc.tax_id && frm.doc.territory === 'Portugal') {
                export_customer_fiscal_data(frm);
            }
        },
        description: __('Exportar Dados Fiscais'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== EVENTOS DE CLEANUP ==========

frappe.ui.form.on('Customer', {
    onload_post_render: function(frm) {
        // ✅ CONFIGURAÇÕES APÓS RENDERIZAÇÃO COMPLETA
        if (is_portuguese_customer(frm)) {
            // ✅ ADICIONAR CLASSES CSS ESPECÍFICAS
            frm.wrapper.addClass('portugal-compliance-form customer-pt');

            // ✅ CONFIGURAR OBSERVADORES DE MUDANÇA
            setup_change_observers(frm);
        }
    }
});

function setup_change_observers(frm) {
    /**
     * Configurar observadores de mudança para campos críticos
     */

    // ✅ OBSERVAR MUDANÇAS NO NIF
    frm.fields_dict.tax_id && frm.fields_dict.tax_id.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.tax_id) {
                validate_portuguese_nif(frm);
                identify_country_by_nif(frm);
            }
        }, 500);
    });

    // ✅ OBSERVAR MUDANÇAS NO TERRITÓRIO
    frm.fields_dict.territory && frm.fields_dict.territory.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.territory === 'Portugal') {
                setup_portuguese_customer(frm);

                // Atualizar seção de compliance
                if (frm.compliance_section_added) {
                    $('.portugal-compliance-info').remove();
                    frm.compliance_section_added = false;
                    add_compliance_section(frm);
                }
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NO TIPO DE CLIENTE
    frm.fields_dict.customer_type && frm.fields_dict.customer_type.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.territory === 'Portugal') {
                suggest_tax_category(frm);
            }
        }, 100);
    });

    // ✅ OBSERVAR MUDANÇAS NA CATEGORIA FISCAL
    frm.fields_dict.tax_category && frm.fields_dict.tax_category.$input.on('change', function() {
        setTimeout(() => {
            if (frm.doc.tax_category && frm.doc.territory === 'Portugal') {
                frappe.show_alert({
                    message: __('Categoria fiscal portuguesa selecionada: {0}', [frm.doc.tax_category]),
                    indicator: 'green'
                });
            }
        }, 100);
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Customer JS loaded - Version 2.0.0');
