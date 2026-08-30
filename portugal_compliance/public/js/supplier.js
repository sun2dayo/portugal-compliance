// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Supplier JS - Portugal Compliance VERSÃO NATIVA COMPLETA
 * Integração completa com validação de NIF e compliance português
 * ✅ Validação automática de NIF português
 * ✅ Configuração automática de impostos
 * ✅ Validação de endereços portugueses
 * ✅ Interface otimizada para fornecedores portugueses
 */

frappe.ui.form.on('Supplier', {
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
        // ✅ VERIFICAR SE É FORNECEDOR PORTUGUÊS
        if (is_portuguese_supplier(frm)) {
            // ✅ CONFIGURAR INTERFACE PORTUGUESA
            setup_portuguese_interface(frm);

            // ✅ MOSTRAR STATUS DE COMPLIANCE
            show_compliance_status(frm);

            // ✅ ADICIONAR BOTÕES PERSONALIZADOS
            add_custom_buttons(frm);
        }

        // ✅ CONFIGURAR VALIDAÇÕES ESPECÍFICAS
        setup_supplier_validations(frm);
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

    // ========== EVENTOS DE PAÍS ==========
    country: function(frm) {
        if (frm.doc.country === 'Portugal') {
            // ✅ CONFIGURAR FORNECEDOR PORTUGUÊS
            setup_portuguese_supplier(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_supplier(frm)) {
            validate_portuguese_supplier(frm);
        }
    },

    // ========== EVENTOS BEFORE_SAVE ==========
    before_save: function(frm) {
        // ✅ PREPARAR DADOS PARA COMPLIANCE
        if (is_portuguese_supplier(frm)) {
            prepare_portugal_compliance_data(frm);
        }
    },

    // ========== EVENTOS AFTER_SAVE ==========
    after_save: function(frm) {
        // ✅ AÇÕES PÓS-SAVE
        if (is_portuguese_supplier(frm)) {
            handle_portuguese_supplier_save(frm);
        }
    }
});

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_portugal_filters(frm) {
    /**
     * Configurar filtros específicos para Portugal
     */

    // ✅ FILTRO PARA PAÍSES
    frm.set_query("country", function() {
        return {
            filters: {
                "name": ["in", ["Portugal", "Spain", "France", "Germany", "Italy", "United Kingdom"]]
            }
        };
    });

    // ✅ FILTRO PARA GRUPOS DE FORNECEDORES
    frm.set_query("supplier_group", function() {
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
            "NIF do fornecedor (obrigatório para fornecedores portugueses)";
    }

    // ✅ CONFIGURAR CAMPO CATEGORIA FISCAL
    if (frm.fields_dict.tax_category) {
        frm.fields_dict.tax_category.df.description =
            "Categoria fiscal para aplicação automática de impostos portugueses";
    }

    // ✅ CONFIGURAR CAMPO PAÍS
    if (frm.fields_dict.country) {
        frm.fields_dict.country.df.description =
            "País do fornecedor (Portugal para compliance português)";
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
     * Configurar layout específico para fornecedores portugueses
     */

    // ✅ ADICIONAR SEÇÃO DE COMPLIANCE
    if (frm.doc.tax_id || frm.doc.country === 'Portugal') {
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
                🇵🇹 Informações de Compliance Português - Fornecedor
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>NIF:</strong> ${frm.doc.tax_id || 'Não definido'}<br>
                    <strong>Status NIF:</strong> <span class="indicator ${nif_status.color}">${nif_status.label}</span><br>
                    <strong>País:</strong> ${frm.doc.country || 'Não definido'}
                </div>
                <div class="col-md-6">
                    <strong>Categoria Fiscal:</strong> ${frm.doc.tax_category || 'Padrão'}<br>
                    <strong>Endereços:</strong> ${address_count}<br>
                    <strong>Tipo Fornecedor:</strong> ${frm.doc.supplier_type || 'Company'}
                </div>
            </div>
            ${nif_status.valid ?
                '<div class="mt-2"><small class="text-success">✅ Fornecedor configurado para compliance português</small></div>' :
                '<div class="mt-2"><small class="text-warning">⚠️ Configure NIF válido para compliance completo</small></div>'
            }
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.compliance_section_added) {
        $(frm.fields_dict.country.wrapper).after(compliance_html);
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
     * Obter status de compliance do fornecedor
     */

    if (frm.doc.country !== 'Portugal') {
        return {
            label: 'Não Aplicável',
            color: 'gray',
            description: 'Fornecedor não português'
        };
    }

    if (!frm.doc.tax_id) {
        return {
            label: 'Incompleto',
            color: 'orange',
            description: 'NIF não definido (obrigatório para fornecedores portugueses)'
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
        description: 'Fornecedor configurado para compliance português'
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
                'link_doctype': 'Supplier',
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
        check_supplier_addresses(frm);
    }, __('Validações'));

    // ✅ BOTÃO PARA CONFIGURAR IMPOSTOS
    if (frm.doc.country === 'Portugal') {
        frm.add_custom_button(__('Configurar Impostos PT'), function() {
            setup_supplier_portuguese_taxes(frm);
        }, __('Configuração'));
    }

    // ✅ BOTÃO PARA VER FATURAS DE COMPRA
    if (frm.doc.name) {
        frm.add_custom_button(__('Ver Faturas Compra'), function() {
            view_supplier_invoices(frm);
        }, __('Relatórios'));
    }

    // ✅ BOTÃO PARA ANÁLISE FISCAL
    if (frm.doc.tax_id && frm.doc.country === 'Portugal') {
        frm.add_custom_button(__('Análise Fiscal'), function() {
            analyze_supplier_fiscal_data(frm);
        }, __('Análise'));
    }

    // ✅ BOTÃO PARA VERIFICAR CERTIFICAÇÕES
    if (frm.doc.country === 'Portugal') {
        frm.add_custom_button(__('Verificar Certificações'), function() {
            check_supplier_certifications(frm);
        }, __('Validações'));
    }
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_supplier(frm) {
    /**
     * Validações específicas para fornecedores portugueses
     */

    let errors = [];

    // ✅ VALIDAR NIF OBRIGATÓRIO PARA PORTUGAL
    if (frm.doc.country === 'Portugal') {
        if (!frm.doc.tax_id) {
            errors.push(__('NIF é obrigatório para fornecedores portugueses'));
        } else if (!validate_portuguese_nif_format(frm.doc.tax_id)) {
            errors.push(__('Formato de NIF inválido'));
        }
    }

    // ✅ VALIDAR CATEGORIA FISCAL
    if (frm.doc.country === 'Portugal' && !frm.doc.tax_category) {
        frappe.show_alert({
            message: __('Categoria fiscal recomendada para fornecedores portugueses'),
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
     * Validar formato do NIF português (validação local básica)
     */

    if (!nif) return false;

    // ✅ LIMPAR E NORMALIZAR
    nif = nif.toString().replace(/[^0-9]/g, '');

    // ✅ VERIFICAR SE TEM 9 DÍGITOS
    if (nif.length !== 9) return false;

    // ✅ VERIFICAR PRIMEIRO DÍGITO VÁLIDO
    if (!['1', '2', '3', '5', '6', '7', '8', '9'].includes(nif[0])) return false;

    // ✅ ALGORITMO DE VALIDAÇÃO
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
        frappe.msgprint(__('Defina o NIF do fornecedor primeiro'));
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
        if (!frm.doc.country || frm.doc.country !== 'Portugal') {
            frappe.msgprint({
                title: __('NIF Português Detectado'),
                message: __('Este NIF parece ser português. Deseja definir o país como Portugal?'),
                primary_action: {
                    label: __('Sim, Definir Portugal'),
                    action: function() {
                        frm.set_value('country', 'Portugal');
                        setup_portuguese_supplier(frm);
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

function setup_portuguese_supplier(frm) {
    /**
     * Configurar fornecedor português automaticamente
     */

    // ✅ SUGERIR CATEGORIA FISCAL
    if (!frm.doc.tax_category) {
        suggest_tax_category(frm);
    }

    // ✅ TORNAR NIF OBRIGATÓRIO
    frm.toggle_reqd('tax_id', true);

    // ✅ MOSTRAR INFORMAÇÕES
    frappe.show_alert({
        message: __('Fornecedor configurado para Portugal. Verifique NIF e categoria fiscal.'),
        indicator: 'blue'
    });
}

function suggest_tax_category(frm) {
    /**
     * Sugerir categoria fiscal baseada no tipo de fornecedor
     */

    let suggested_category = '';

    switch(frm.doc.supplier_type) {
        case 'Individual':
            suggested_category = 'Portugal - Individual';
            break;
        case 'Company':
            suggested_category = 'Portugal - Empresa';
            break;
        default:
            suggested_category = 'Portugal - Fornecedor';
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

function setup_supplier_portuguese_taxes(frm) {
    /**
     * Configurar impostos portugueses para fornecedor
     */

    frappe.call({
        method: 'portugal_compliance.regional.portugal.setup_supplier_tax_category',
        args: {
            supplier: frm.doc.name,
            supplier_type: frm.doc.supplier_type
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

function check_supplier_addresses(frm) {
    /**
     * Verificar endereços do fornecedor
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Address',
            filters: {
                'link_doctype': 'Supplier',
                'link_name': frm.doc.name
            },
            fields: ['name', 'address_title', 'address_line1', 'city', 'pincode', 'country']
        },
        callback: function(r) {
            if (r.message) {
                show_addresses_dialog(frm, r.message);
            } else {
                frappe.msgprint(__('Nenhum endereço encontrado para este fornecedor'));
            }
        }
    });
}

function show_addresses_dialog(frm, addresses) {
    /**
     * Mostrar dialog com endereços do fornecedor
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Endereços do Fornecedor'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'addresses_info'
            }
        ]
    });

    let html = `
        <div class="supplier-addresses">
            <h5>Endereços: ${frm.doc.supplier_name}</h5>

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

function view_supplier_invoices(frm) {
    /**
     * Ver faturas de compra do fornecedor
     */

    frappe.route_options = {
        "supplier": frm.doc.name
    };

    frappe.set_route("List", "Purchase Invoice");
}

function analyze_supplier_fiscal_data(frm) {
    /**
     * Analisar dados fiscais do fornecedor
     */

    frappe.call({
        method: 'portugal_compliance.api.get_supplier_fiscal_analysis',
        args: {
            supplier: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_fiscal_analysis_dialog(frm, r.message);
            }
        }
    });
}

function show_fiscal_analysis_dialog(frm, fiscal_data) {
    /**
     * Mostrar dialog com análise fiscal
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise Fiscal do Fornecedor'),
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
            <h5>Análise Fiscal: ${frm.doc.supplier_name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>NIF:</strong></td><td>${frm.doc.tax_id || 'Não definido'}</td></tr>
                        <tr><td><strong>País:</strong></td><td>${frm.doc.country || 'Não definido'}</td></tr>
                        <tr><td><strong>Categoria Fiscal:</strong></td><td>${frm.doc.tax_category || 'Padrão'}</td></tr>
                        <tr><td><strong>Tipo Fornecedor:</strong></td><td>${frm.doc.supplier_type || 'Company'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Estatísticas Fiscais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Faturas:</strong></td><td>${fiscal_data.total_invoices || 0}</td></tr>
                        <tr><td><strong>Valor Total:</strong></td><td>€${(fiscal_data.total_amount || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>IVA Total:</strong></td><td>€${(fiscal_data.total_tax || 0).toFixed(2)}</td></tr>
                        <tr><td><strong>Última Fatura:</strong></td><td>${fiscal_data.last_invoice_date || 'Nunca'}</td></tr>
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
                    Análise baseada em faturas de compra submetidas<br>
                    Dados atualizados até: ${frappe.datetime.now_datetime()}
                </small>
            </div>
        </div>
    `;

    dialog.fields_dict.fiscal_analysis.$wrapper.html(html);
    dialog.show();
}

function check_supplier_certifications(frm) {
    /**
     * Verificar certificações do fornecedor
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Verificação de Certificações'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'certifications_info'
            }
        ]
    });

    let html = `
        <div class="supplier-certifications">
            <h5>Verificação de Certificações: ${frm.doc.supplier_name}</h5>

            <div class="alert alert-info">
                <strong>Verificações Recomendadas para Fornecedores Portugueses:</strong>
            </div>

            <table class="table table-striped">
                <thead>
                    <tr><th>Certificação</th><th>Status</th><th>Observações</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>NIF Válido</td>
                        <td><span class="indicator ${get_nif_status(frm).color}">${get_nif_status(frm).label}</span></td>
                        <td>Verificação automática do algoritmo de NIF</td>
                    </tr>
                    <tr>
                        <td>Endereço Completo</td>
                        <td><span class="indicator ${get_address_count(frm) > 0 ? 'green' : 'orange'}">${get_address_count(frm) > 0 ? 'Configurado' : 'Pendente'}</span></td>
                        <td>Pelo menos um endereço completo</td>
                    </tr>
                    <tr>
                        <td>Categoria Fiscal</td>
                        <td><span class="indicator ${frm.doc.tax_category ? 'green' : 'orange'}">${frm.doc.tax_category ? 'Configurada' : 'Pendente'}</span></td>
                        <td>Categoria fiscal para impostos portugueses</td>
                    </tr>
                    <tr>
                        <td>Dados Bancários</td>
                        <td><span class="indicator orange">Manual</span></td>
                        <td>Verificar IBAN e dados bancários manualmente</td>
                    </tr>
                    <tr>
                        <td>Certificado ISO</td>
                        <td><span class="indicator orange">Manual</span></td>
                        <td>Verificar certificações de qualidade</td>
                    </tr>
                </tbody>
            </table>

            <div class="mt-3">
                <small class="text-muted">
                    Esta verificação é automática para alguns itens.<br>
                    Certificações manuais devem ser verificadas externamente.
                </small>
            </div>
        </div>
    `;

    dialog.fields_dict.certifications_info.$wrapper.html(html);
    dialog.show();
}

// ========== FUNÇÕES AUXILIARES ==========

function is_portuguese_supplier(frm) {
    /**
     * Verificar se fornecedor é português
     */

    return frm.doc.country === 'Portugal' ||
           (frm.doc.tax_id && validate_portuguese_nif_format(frm.doc.tax_id));
}

function setup_supplier_validations(frm) {
    /**
     * Configurar validações específicas do fornecedor
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
    if (frm.doc.country === 'Portugal' && !frm.doc.tax_category) {
        let default_category = frm.doc.supplier_type === 'Individual' ?
            'Portugal - Individual' : 'Portugal - Fornecedor';

        frm.doc.tax_category = default_category;
    }
}

function handle_portuguese_supplier_save(frm) {
    /**
     * Ações após salvar fornecedor português
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
            message: __('Fornecedor português salvo com NIF válido'),
            indicator: 'green'
        });
    }
}

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Supplier', {
    onload: function(frm) {
        // ✅ CONFIGURAÇÃO INICIAL QUANDO FORMULÁRIO CARREGA
        if (is_portuguese_supplier(frm)) {
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
            "NIF do fornecedor português. Formato: 9 dígitos. Obrigatório para fornecedores portugueses";
    }

    if (frm.fields_dict.country) {
        frm.fields_dict.country.df.description =
            "País do fornecedor. Defina 'Portugal' para ativar compliance português";
    }

    if (frm.fields_dict.tax_category) {
        frm.fields_dict.tax_category.df.description =
            "Categoria fiscal para aplicação automática de impostos portugueses (IVA)";
    }

    if (frm.fields_dict.supplier_type) {
        frm.fields_dict.supplier_type.df.description =
            "Tipo de fornecedor: Individual (pessoa física) ou Company (pessoa jurídica)";
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
            check_supplier_addresses(frm);
        },
        description: __('Verificar Endereços'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+F para análise fiscal
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+f',
        action: () => {
            if (frm.doc.tax_id && frm.doc.country === 'Portugal') {
                analyze_supplier_fiscal_data(frm);
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
                view_supplier_invoices(frm);
            }
        },
        description: __('Ver Faturas do Fornecedor'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+C para verificar certificações
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+c',
        action: () => {
            if (frm.doc.country === 'Portugal') {
                check_supplier_certifications(frm);
            }
        },
        description: __('Verificar Certificações'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Supplier JS loaded - Version 2.0.0');
