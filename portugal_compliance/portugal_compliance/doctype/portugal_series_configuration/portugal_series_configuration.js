// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Portugal Series Configuration DocType JS - VERSÃO NATIVA CORRIGIDA
 * Configuração de séries portuguesas para compliance
 * ✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Suporte completo para TODOS os doctypes portugueses
 * ✅ Validação automática de prefixos e naming series
 * ✅ Interface otimizada para configuração de séries
 */

frappe.ui.form.on('Portugal Series Configuration', {
    // ========== SETUP INICIAL DO FORMULÁRIO ==========
    setup: function(frm) {
        // ✅ CONFIGURAR FILTROS ESPECÍFICOS
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
        // ✅ CONFIGURAR INTERFACE ESPECÍFICA
        setup_series_interface(frm);

        // ✅ MOSTRAR STATUS DA SÉRIE
        show_series_status(frm);

        // ✅ ADICIONAR BOTÕES PERSONALIZADOS
        add_custom_buttons(frm);

        // ✅ CONFIGURAR VALIDAÇÕES ESPECÍFICAS
        setup_series_validations(frm);
    },

    // ========== EVENTOS DE CAMPOS ==========
    document_type: function(frm) {
        if (frm.doc.document_type) {
            // ✅ CONFIGURAR PREFIXO AUTOMÁTICO
            setup_automatic_prefix(frm);

            // ✅ MOSTRAR INFORMAÇÕES DO DOCUMENTO
            show_document_type_info(frm);

            // ✅ VALIDAR TIPO DE DOCUMENTO
            validate_document_type(frm);
        }
    },

    prefix: function(frm) {
        if (frm.doc.prefix) {
            // ✅ VALIDAR FORMATO DO PREFIXO (SEM HÍFENS)
            validate_prefix_format(frm);

            // ✅ GERAR NAMING SERIES AUTOMATICAMENTE
            generate_naming_series(frm);

            // ✅ VERIFICAR DUPLICATAS
            check_prefix_duplicates(frm);
        }
    },

    company: function(frm) {
        if (frm.doc.company) {
            // ✅ VALIDAR EMPRESA PORTUGUESA
            validate_portuguese_company(frm);

            // ✅ CARREGAR CONFIGURAÇÕES DA EMPRESA
            load_company_settings(frm);
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PARA SÉRIES PORTUGUESAS
        validate_series_configuration(frm);
    },

    // ========== EVENTOS BEFORE_SAVE ==========
    before_save: function(frm) {
        // ✅ PREPARAR DADOS ANTES DO SAVE
        prepare_series_data(frm);
    },

    // ========== EVENTOS AFTER_SAVE ==========
    after_save: function(frm) {
        // ✅ AÇÕES APÓS SAVE
        handle_series_save(frm);
    }
});

// ========== CONFIGURAÇÃO DE TIPOS DE DOCUMENTO ==========

const PORTUGAL_DOCUMENT_TYPES = {
    // ✅ DOCUMENTOS DE VENDA
    'Sales Invoice': {
        code: 'FT',
        name: 'Fatura',
        description: 'Fatura de venda para clientes',
        communication_required: true,
        atcud_required: true
    },
    'POS Invoice': {
        code: 'FS',
        name: 'Fatura Simplificada',
        description: 'Fatura simplificada para POS/Retail',
        communication_required: true,
        atcud_required: true,
        nif_limit: 1000
    },
    'Sales Order': {
        code: 'FO',
        name: 'Fatura-Orçamento',
        description: 'Ordem de venda/Fatura-Orçamento',
        communication_required: true,
        atcud_required: true
    },
    'Quotation': {
        code: 'OR',
        name: 'Orçamento',
        description: 'Orçamento para clientes',
        communication_required: true,
        atcud_required: true
    },
    'Delivery Note': {
        code: 'GR',
        name: 'Guia de Remessa',
        description: 'Guia de remessa para entregas',
        communication_required: true,
        atcud_required: true
    },

    // ✅ DOCUMENTOS DE COMPRA
    'Purchase Invoice': {
        code: 'FC',
        name: 'Fatura de Compra',
        description: 'Fatura de compra de fornecedores',
        communication_required: true,
        atcud_required: true
    },
    'Purchase Order': {
        code: 'OC',
        name: 'Ordem de Compra',
        description: 'Ordem de compra para fornecedores',
        communication_required: true,
        atcud_required: true
    },
    'Purchase Receipt': {
        code: 'GR',
        name: 'Guia de Receção',
        description: 'Guia de receção de mercadorias',
        communication_required: true,
        atcud_required: true
    },

    // ✅ DOCUMENTOS DE STOCK
    'Stock Entry': {
        code: 'GM',
        name: 'Guia de Movimentação',
        description: 'Guia de movimentação de stock',
        communication_required: true,
        atcud_required: true
    },

    // ✅ DOCUMENTOS FINANCEIROS
    'Payment Entry': {
        code: 'RC',
        name: 'Recibo',
        description: 'Recibo de pagamento/recebimento',
        communication_required: true,
        atcud_required: true
    }
};

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

    // ✅ FILTRO PARA TIPOS DE DOCUMENTO SUPORTADOS
    frm.set_query("document_type", function() {
        return {
            filters: {
                "name": ["in", Object.keys(PORTUGAL_DOCUMENT_TYPES)]
            }
        };
    });
}

function setup_custom_fields(frm) {
    /**
     * Configurar campos personalizados para compliance português
     */

    // ✅ CONFIGURAR CAMPO PREFIX (SEM HÍFENS)
    if (frm.fields_dict.prefix) {
        frm.fields_dict.prefix.df.description = "Prefixo da série portuguesa (formato: XXYYYY + EMPRESA, ex: FT2025NDX)";
        frm.fields_dict.prefix.df.uppercase = true;
        frm.fields_dict.prefix.df.reqd = 1;
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.read_only = 1;
        frm.fields_dict.naming_series.df.description = "Série gerada automaticamente (formato: PREFIX.####)";
        frm.fields_dict.naming_series.df.bold = 1;
    }

    // ✅ CONFIGURAR CAMPO VALIDATION CODE
    if (frm.fields_dict.validation_code) {
        frm.fields_dict.validation_code.df.description = "Código de validação obtido da AT após comunicação";
        frm.fields_dict.validation_code.df.read_only = 1;
    }

    // ✅ CONFIGURAR CAMPO IS_COMMUNICATED
    if (frm.fields_dict.is_communicated) {
        frm.fields_dict.is_communicated.df.description = "Indica se a série foi comunicada à Autoridade Tributária";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE PREFIXO EM TEMPO REAL
    frm.add_custom_validator = function(field_name, validator_fn) {
        frm.fields_dict[field_name] && frm.fields_dict[field_name].$input.on('blur', validator_fn);
    };
}

function setup_custom_events(frm) {
    /**
     * Configurar eventos personalizados
     */

    // ✅ EVENTO PARA COMUNICAÇÃO COM AT
    $(frm.wrapper).on('series_communicated', function(e, data) {
        if (data.series === frm.doc.name) {
            frm.reload_doc();
            frappe.show_alert({
                message: `Série comunicada com sucesso: ${data.validation_code}`,
                indicator: 'green'
            });
        }
    });

    // ✅ EVENTO PARA ATUALIZAÇÃO DE SEQUÊNCIA
    $(frm.wrapper).on('sequence_updated', function(e, data) {
        if (data.series === frm.doc.name) {
            frm.set_value('current_sequence', data.new_sequence);
        }
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_series_interface(frm) {
    /**
     * Configurar interface específica para séries
     */

    // ✅ ADICIONAR INDICADORES DE STATUS
    if (!frm.doc.__islocal) {
        let status = get_series_status(frm);

        frm.dashboard.add_indicator(
            __('Status: {0}', [status.label]),
            status.color
        );

        if (frm.doc.is_communicated) {
            frm.dashboard.add_indicator(
                __('Comunicada à AT'),
                'green'
            );
        }

        if (frm.doc.total_documents_issued > 0) {
            frm.dashboard.add_indicator(
                __('Documentos: {0}', [frm.doc.total_documents_issued]),
                'blue'
            );
        }
    }

    // ✅ CONFIGURAR LAYOUT ESPECÍFICO
    setup_series_layout(frm);
}

function setup_series_layout(frm) {
    /**
     * Configurar layout específico para séries
     */

    // ✅ ADICIONAR SEÇÃO DE INFORMAÇÕES
    if (!frm.doc.__islocal) {
        add_series_info_section(frm);
    }

    // ✅ ADICIONAR SEÇÃO DE DOCUMENTO
    if (frm.doc.document_type) {
        add_document_type_section(frm);
    }
}

function add_series_info_section(frm) {
    /**
     * Adicionar seção de informações da série
     */

    let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type] || {};
    let status = get_series_status(frm);

    let info_html = `
        <div class="series-info-section" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Informações da Série Portuguesa
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Prefixo:</strong> ${frm.doc.prefix || 'Não definido'}<br>
                    <strong>Naming Series:</strong> ${frm.doc.naming_series || 'Não gerada'}<br>
                    <strong>Tipo Documento:</strong> ${doc_info.name || frm.doc.document_type}
                </div>
                <div class="col-md-6">
                    <strong>Status:</strong> <span class="indicator ${status.color}">${status.label}</span><br>
                    <strong>Sequência Atual:</strong> ${frm.doc.current_sequence || 0}<br>
                    <strong>Total Emitidos:</strong> ${frm.doc.total_documents_issued || 0}
                </div>
            </div>
            ${frm.doc.is_communicated ?
                `<div class="mt-2"><small class="text-success">✅ Série comunicada à AT em ${frappe.datetime.str_to_user(frm.doc.communication_date)}</small></div>` :
                '<div class="mt-2"><small class="text-warning">⚠️ Série não comunicada à AT</small></div>'
            }
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.series_info_added) {
        $(frm.fields_dict.naming_series.wrapper).after(info_html);
        frm.series_info_added = true;
    }
}

function add_document_type_section(frm) {
    /**
     * Adicionar seção de informações do tipo de documento
     */

    let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type];
    if (!doc_info) return;

    let doc_html = `
        <div class="document-type-section" style="
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #e65100;">
                📄 Informações do Tipo de Documento
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>Código:</strong> ${doc_info.code}<br>
                    <strong>Nome:</strong> ${doc_info.name}<br>
                    <strong>Comunicação:</strong> ${doc_info.communication_required ? 'Obrigatória' : 'Opcional'}
                </div>
                <div class="col-md-6">
                    <strong>ATCUD:</strong> ${doc_info.atcud_required ? 'Obrigatório' : 'Opcional'}<br>
                    <strong>Descrição:</strong> ${doc_info.description}<br>
                    ${doc_info.nif_limit ? `<strong>Limite s/ NIF:</strong> €${doc_info.nif_limit}` : ''}
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.document_type_added) {
        $(frm.fields_dict.document_type.wrapper).after(doc_html);
        frm.document_type_added = true;
    }
}

function show_series_status(frm) {
    /**
     * Mostrar status da série no formulário
     */

    if (frm.doc.__islocal) return;

    let status = get_series_status(frm);

    // ✅ MOSTRAR NO DASHBOARD
    frm.dashboard.clear_headline();
    frm.dashboard.set_headline(
        `<span class="indicator ${status.color}">${status.label}</span> ${status.description}`
    );
}

function get_series_status(frm) {
    /**
     * Obter status da série
     */

    if (!frm.doc.prefix) {
        return {
            label: 'Não Configurada',
            color: 'red',
            description: 'Prefixo não definido'
        };
    }

    if (!frm.doc.naming_series) {
        return {
            label: 'Incompleta',
            color: 'orange',
            description: 'Naming series não gerada'
        };
    }

    if (!frm.doc.is_active) {
        return {
            label: 'Inativa',
            color: 'gray',
            description: 'Série desativada'
        };
    }

    if (!frm.doc.is_communicated) {
        return {
            label: 'Não Comunicada',
            color: 'orange',
            description: 'Série não comunicada à AT'
        };
    }

    return {
        label: 'Ativa',
        color: 'green',
        description: 'Série ativa e comunicada'
    };
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * Adicionar botões personalizados para séries
     */

    if (frm.doc.__islocal) return;

    // ✅ BOTÃO PARA COMUNICAR À AT
    if (!frm.doc.is_communicated && frm.doc.naming_series) {
        frm.add_custom_button(__('Comunicar à AT'), function() {
            communicate_series_to_at(frm);
        }, __('Portugal Compliance'));
    }

    // ✅ BOTÃO PARA TESTAR SÉRIE
    if (frm.doc.naming_series) {
        frm.add_custom_button(__('Testar Série'), function() {
            test_series_generation(frm);
        }, __('Testes'));
    }

    // ✅ BOTÃO PARA VER DOCUMENTOS
    if (frm.doc.total_documents_issued > 0) {
        frm.add_custom_button(__('Ver Documentos'), function() {
            view_series_documents(frm);
        }, __('Relatórios'));
    }

    // ✅ BOTÃO PARA DUPLICAR SÉRIE
    frm.add_custom_button(__('Duplicar Série'), function() {
        duplicate_series(frm);
    }, __('Ações'));

    // ✅ BOTÃO PARA GERAR RELATÓRIO
    frm.add_custom_button(__('Relatório Completo'), function() {
        generate_series_report(frm);
    }, __('Relatórios'));

    // ✅ BOTÃO PARA VERIFICAR STATUS AT
    if (frm.doc.is_communicated) {
        frm.add_custom_button(__('Verificar Status AT'), function() {
            check_at_status(frm);
        }, __('Portugal Compliance'));
    }
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_series_configuration(frm) {
    /**
     * Validar configuração completa da série
     */

    let errors = [];

    // ✅ VALIDAR EMPRESA
    if (!frm.doc.company) {
        errors.push(__('Empresa é obrigatória'));
    }

    // ✅ VALIDAR TIPO DE DOCUMENTO
    if (!frm.doc.document_type) {
        errors.push(__('Tipo de documento é obrigatório'));
    } else if (!PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type]) {
        errors.push(__('Tipo de documento não suportado para Portugal'));
    }

    // ✅ VALIDAR PREFIXO
    if (!frm.doc.prefix) {
        errors.push(__('Prefixo é obrigatório'));
    } else if (!validate_prefix_format_check(frm.doc.prefix)) {
        errors.push(__('Formato de prefixo inválido (use: XXYYYY + EMPRESA)'));
    }

    // ✅ VALIDAR NAMING SERIES
    if (!frm.doc.naming_series) {
        errors.push(__('Naming series deve ser gerada'));
    }

    // ✅ MOSTRAR ERROS
    if (errors.length > 0) {
        frappe.msgprint({
            title: __('Validação da Série'),
            message: errors.join('<br>'),
            indicator: 'red'
        });
        frappe.validated = false;
    }
}

function validate_prefix_format(frm) {
    /**
     * ✅ CORRIGIDO: Validar formato do prefixo (SEM HÍFENS)
     */

    if (!frm.doc.prefix) return;

    let isValid = validate_prefix_format_check(frm.doc.prefix);

    if (!isValid) {
        frappe.show_alert({
            message: __('Formato inválido. Use: XXYYYY + EMPRESA (ex: FT2025NDX)'),
            indicator: 'red'
        });
        frm.set_value('prefix', '');
    } else {
        frappe.show_alert({
            message: __('Formato de prefixo válido'),
            indicator: 'green'
        });
    }
}

function validate_prefix_format_check(prefix) {
    /**
     * ✅ CORRIGIDO: Verificar formato do prefixo (SEM HÍFENS)
     */

    if (!prefix) return false;

    // ✅ PADRÃO: XXYYYY + EMPRESA (ex: FT2025NDX)
    const pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$/;
    return pattern.test(prefix);
}

function validate_document_type(frm) {
    /**
     * Validar tipo de documento
     */

    if (!frm.doc.document_type) return;

    if (!PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type]) {
        frappe.msgprint({
            title: __('Tipo de Documento Inválido'),
            message: __('Este tipo de documento não é suportado para compliance português'),
            indicator: 'red'
        });
        frm.set_value('document_type', '');
    }
}

function validate_portuguese_company(frm) {
    /**
     * Validar se empresa é portuguesa
     */

    if (!frm.doc.company) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: {name: frm.doc.company},
            fieldname: ['country', 'portugal_compliance_enabled']
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.country !== 'Portugal') {
                    frappe.msgprint({
                        title: __('Empresa Inválida'),
                        message: __('Apenas empresas portuguesas podem ter séries de compliance'),
                        indicator: 'red'
                    });
                    frm.set_value('company', '');
                }

                if (!r.message.portugal_compliance_enabled) {
                    frappe.msgprint({
                        title: __('Compliance Desativado'),
                        message: __('Ative o Portugal Compliance na empresa primeiro'),
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

function check_prefix_duplicates(frm) {
    /**
     * Verificar duplicatas de prefixo
     */

    if (!frm.doc.prefix || !frm.doc.company) return;

    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {
                prefix: frm.doc.prefix,
                company: frm.doc.company,
                name: ['!=', frm.doc.name || '']
            }
        },
        callback: function(r) {
            if (r.message > 0) {
                frappe.show_alert({
                    message: __('Prefixo já existe para esta empresa'),
                    indicator: 'red'
                });
            }
        }
    });
}

// ========== FUNÇÕES DE GERAÇÃO ==========

function setup_automatic_prefix(frm) {
    /**
     * ✅ CORRIGIDO: Configurar prefixo automático (SEM HÍFENS)
     */

    if (!frm.doc.document_type || frm.doc.prefix) return;

    let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type];
    if (!doc_info) return;

    // ✅ GERAR PREFIXO SUGERIDO (SEM HÍFENS)
    let currentYear = new Date().getFullYear();
    let companyCode = frm.doc.company ? frm.doc.company.substring(0, 3).toUpperCase() : 'NDX';
    let suggestedPrefix = `${doc_info.code}${currentYear}${companyCode}`;

    frappe.msgprint({
        title: __('Prefixo Sugerido'),
        message: __('Prefixo sugerido para {0}: <strong>{1}</strong>', [doc_info.name, suggestedPrefix]),
        primary_action: {
            label: __('Usar Sugerido'),
            action: function() {
                frm.set_value('prefix', suggestedPrefix);
            }
        }
    });
}

function generate_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Gerar naming series (SEM HÍFENS)
     */

    if (!frm.doc.prefix) return;

    // ✅ FORMATO: PREFIX.#### (ex: FT2025NDX.####)
    let namingSeries = `${frm.doc.prefix}.####`;
    frm.set_value('naming_series', namingSeries);

    frappe.show_alert({
        message: __('Naming series gerada: {0}', [namingSeries]),
        indicator: 'blue'
    });
}

function show_document_type_info(frm) {
    /**
     * Mostrar informações do tipo de documento
     */

    if (!frm.doc.document_type) return;

    let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type];
    if (!doc_info) return;

    frappe.show_alert({
        message: __('Documento: {0} (Código: {1})', [doc_info.name, doc_info.code]),
        indicator: 'blue'
    });

    // ✅ ATUALIZAR SEÇÃO DE DOCUMENTO
    if (frm.document_type_added) {
        $('.document-type-section').remove();
        frm.document_type_added = false;
        add_document_type_section(frm);
    }
}

// ========== FUNÇÕES DE AÇÕES ==========

function communicate_series_to_at(frm) {
    /**
     * Comunicar série à Autoridade Tributária
     */

    frappe.confirm(
        __('Comunicar série {0} à Autoridade Tributária?', [frm.doc.series_name]),
        function() {
            frappe.call({
                method: 'portugal_compliance.utils.at_communication.communicate_series',
                args: {
                    series_config: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Série comunicada com sucesso: {0}', [r.message.validation_code]),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Erro na Comunicação'),
                            message: r.message ? r.message.error : __('Erro ao comunicar série'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function test_series_generation(frm) {
    /**
     * Testar geração da série
     */

    frappe.call({
        method: 'portugal_compliance.utils.series_adapter.test_series_generation',
        args: {
            series_config: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_test_results_dialog(frm, r.message);
            }
        }
    });
}

function show_test_results_dialog(frm, test_results) {
    /**
     * Mostrar resultados do teste
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Resultados do Teste'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'test_results'
            }
        ]
    });

    let html = `
        <div class="test-results">
            <h5>Teste da Série: ${frm.doc.series_name}</h5>

            <table class="table table-bordered">
                <tr><td><strong>Prefixo:</strong></td><td>${frm.doc.prefix}</td></tr>
                <tr><td><strong>Naming Series:</strong></td><td>${frm.doc.naming_series}</td></tr>
                <tr><td><strong>Próximo Número:</strong></td><td>${test_results.next_number}</td></tr>
                <tr><td><strong>ATCUD Exemplo:</strong></td><td>${test_results.sample_atcud}</td></tr>
                <tr><td><strong>Status:</strong></td><td style="color: ${test_results.valid ? 'green' : 'red'}">${test_results.valid ? 'Válido' : 'Inválido'}</td></tr>
            </table>

            ${test_results.issues && test_results.issues.length > 0 ? `
                <h6>Problemas Encontrados:</h6>
                <ul>
                    ${test_results.issues.map(issue => `<li style="color: red;">${issue}</li>`).join('')}
                </ul>
            ` : '<p style="color: green;">✅ Nenhum problema encontrado</p>'}
        </div>
    `;

    dialog.fields_dict.test_results.$wrapper.html(html);
    dialog.show();
}

function view_series_documents(frm) {
    /**
     * Ver documentos da série
     */

    if (!frm.doc.document_type) return;

    // ✅ ABRIR LISTA DE DOCUMENTOS
    frappe.route_options = {
        "naming_series": frm.doc.naming_series
    };

    frappe.set_route("List", frm.doc.document_type);
}

function duplicate_series(frm) {
    /**
     * Duplicar série para outra empresa
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Duplicar Série'),
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'new_company',
                label: __('Nova Empresa'),
                options: 'Company',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            "country": "Portugal",
                            "portugal_compliance_enabled": 1
                        }
                    };
                }
            },
            {
                fieldtype: 'Data',
                fieldname: 'new_prefix',
                label: __('Novo Prefixo'),
                reqd: 1
            }
        ],
        primary_action_label: __('Duplicar'),
        primary_action: function(values) {
            frappe.call({
                method: 'portugal_compliance.api.duplicate_series_configuration',
                args: {
                    source_series: frm.doc.name,
                    new_company: values.new_company,
                    new_prefix: values.new_prefix
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Série duplicada: {0}', [r.message.new_series]),
                            indicator: 'green'
                        });
                        dialog.hide();
                        frappe.set_route("Form", "Portugal Series Configuration", r.message.new_series);
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao duplicar série'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });

    dialog.show();
}

function generate_series_report(frm) {
    /**
     * Gerar relatório completo da série
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório da Série'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'series_report'
            }
        ],
        primary_action_label: __('Exportar PDF'),
        primary_action: function() {
            window.print();
        }
    });

    let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type] || {};
    let status = get_series_status(frm);

    let html = `
        <div class="series-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Série Portuguesa</h3>
                <p><strong>Série:</strong> ${frm.doc.series_name} | <strong>Data:</strong> ${frappe.datetime.str_to_user(frappe.datetime.nowdate())}</p>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <h5>Informações Básicas</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Nome:</strong></td><td>${frm.doc.series_name}</td></tr>
                        <tr><td><strong>Empresa:</strong></td><td>${frm.doc.company}</td></tr>
                        <tr><td><strong>Tipo Documento:</strong></td><td>${doc_info.name || frm.doc.document_type}</td></tr>
                        <tr><td><strong>Código:</strong></td><td>${doc_info.code || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Configuração Técnica</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Prefixo:</strong></td><td>${frm.doc.prefix}</td></tr>
                        <tr><td><strong>Naming Series:</strong></td><td>${frm.doc.naming_series}</td></tr>
                        <tr><td><strong>Sequência Atual:</strong></td><td>${frm.doc.current_sequence}</td></tr>
                        <tr><td><strong>Status:</strong></td><td style="color: ${status.color}">${status.label}</td></tr>
                    </table>
                </div>
            </div>

            <h5>Status de Comunicação</h5>
            <table class="table table-bordered">
                <tr><td><strong>Comunicada:</strong></td><td>${frm.doc.is_communicated ? 'Sim' : 'Não'}</td></tr>
                <tr><td><strong>Data Comunicação:</strong></td><td>${frm.doc.communication_date ? frappe.datetime.str_to_user(frm.doc.communication_date) : 'N/A'}</td></tr>
                <tr><td><strong>Código Validação:</strong></td><td>${frm.doc.validation_code || 'N/A'}</td></tr>
                <tr><td><strong>Ambiente AT:</strong></td><td>${frm.doc.at_environment || 'Produção'}</td></tr>
            </table>

            <h5>Estatísticas de Uso</h5>
            <table class="table table-bordered">
                <tr><td><strong>Total Documentos:</strong></td><td>${frm.doc.total_documents_issued || 0}</td></tr>
                <tr><td><strong>Último Documento:</strong></td><td>${frm.doc.last_document_date ? frappe.datetime.str_to_user(frm.doc.last_document_date) : 'Nunca'}</td></tr>
                <tr><td><strong>Ativa:</strong></td><td>${frm.doc.is_active ? 'Sim' : 'Não'}</td></tr>
            </table>

            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <p><strong>Relatório gerado em:</strong> ${frappe.datetime.now_datetime()}</p>
                <p><strong>Portugal Compliance:</strong> Conforme Portaria 195/2020</p>
                <p><strong>Observações:</strong> ${frm.doc.notes || 'Nenhuma'}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.series_report.$wrapper.html(html);
    dialog.show();
}

function check_at_status(frm) {
    /**
     * Verificar status na AT
     */

    frappe.call({
        method: 'portugal_compliance.utils.at_communication.check_series_status',
        args: {
            series_config: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: __('Status na AT'),
                    message: `
                        <table class="table table-bordered">
                            <tr><td><strong>Status:</strong></td><td>${r.message.status}</td></tr>
                            <tr><td><strong>Última Verificação:</strong></td><td>${frappe.datetime.str_to_user(r.message.last_check)}</td></tr>
                            <tr><td><strong>Código Validação:</strong></td><td>${r.message.validation_code}</td></tr>
                        </table>
                    `,
                    indicator: r.message.valid ? 'green' : 'orange'
                });
            }
        }
    });
}

// ========== FUNÇÕES AUXILIARES ==========

function prepare_series_data(frm) {
    /**
     * Preparar dados antes do save
     */

    // ✅ GERAR NAMING SERIES SE NÃO EXISTE
    if (frm.doc.prefix && !frm.doc.naming_series) {
        frm.doc.naming_series = `${frm.doc.prefix}.####`;
    }

    // ✅ DEFINIR SEQUÊNCIA INICIAL
    if (!frm.doc.current_sequence) {
        frm.doc.current_sequence = 1;
    }

    // ✅ DEFINIR NOME DA SÉRIE
    if (!frm.doc.series_name && frm.doc.prefix) {
        let doc_info = PORTUGAL_DOCUMENT_TYPES[frm.doc.document_type];
        frm.doc.series_name = `${doc_info?.name || frm.doc.document_type} - ${frm.doc.prefix}`;
    }

    // ✅ DEFINIR ATIVA POR PADRÃO
    if (frm.doc.is_active === undefined) {
        frm.doc.is_active = 1;
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
            fieldname: ['at_environment', 'portugal_compliance_enabled', 'tax_id']
        },
        callback: function(r) {
            if (r.message) {
                frm._company_settings = r.message;

                // ✅ DEFINIR AMBIENTE AT
                if (!frm.doc.at_environment && r.message.at_environment) {
                    frm.set_value('at_environment', r.message.at_environment);
                }
            }
        }
    });
}

function setup_series_validations(frm) {
    /**
     * Configurar validações em tempo real
     */

    // ✅ VALIDAR PREFIXO QUANDO MUDA
    if (frm.fields_dict.prefix) {
        frm.fields_dict.prefix.$input.on('blur', function() {
            if (frm.doc.prefix) {
                validate_prefix_format(frm);
                check_prefix_duplicates(frm);
                generate_naming_series(frm);
            }
        });
    }

    // ✅ VALIDAR EMPRESA QUANDO MUDA
    if (frm.fields_dict.company) {
        frm.fields_dict.company.$input.on('change', function() {
            if (frm.doc.company) {
                validate_portuguese_company(frm);
                load_company_settings(frm);
            }
        });
    }
}

function handle_series_save(frm) {
    /**
     * Ações após salvar série
     */

    // ✅ ATUALIZAR SEÇÕES VISUAIS
    if (frm.series_info_added) {
        $('.series-info-section').remove();
        frm.series_info_added = false;
        add_series_info_section(frm);
    }

    // ✅ MOSTRAR MENSAGEM DE SUCESSO
    frappe.show_alert({
        message: __('Série {0} salva com sucesso', [frm.doc.series_name]),
        indicator: 'green'
    });
}

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Portugal Series Configuration', {
    onload: function(frm) {
        // ✅ CONFIGURAÇÃO INICIAL
        setup_tooltips(frm);
        setup_keyboard_shortcuts(frm);
    }
});

function setup_tooltips(frm) {
    /**
     * ✅ CORRIGIDO: Configurar tooltips (formato SEM HÍFENS)
     */

    if (frm.fields_dict.prefix) {
        frm.fields_dict.prefix.df.description =
            "Prefixo da série portuguesa. Formato: XXYYYY + EMPRESA (ex: FT2025NDX)";
    }

    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description =
            "Série gerada automaticamente no formato PREFIX.#### (ex: FT2025NDX.####)";
    }

    if (frm.fields_dict.document_type) {
        frm.fields_dict.document_type.df.description =
            "Tipo de documento português suportado pelo sistema";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado
     */

    // ✅ CTRL+T para testar série
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+t',
        action: () => {
            if (frm.doc.naming_series) {
                test_series_generation(frm);
            }
        },
        description: __('Testar Série'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+C para comunicar
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+c',
        action: () => {
            if (!frm.doc.is_communicated && frm.doc.naming_series) {
                communicate_series_to_at(frm);
            }
        },
        description: __('Comunicar à AT'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+R para relatório
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+r',
        action: () => {
            generate_series_report(frm);
        },
        description: __('Gerar Relatório'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Series Configuration DocType JS loaded - Version 2.0.0 - Fully Aligned');
