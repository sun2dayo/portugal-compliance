// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Company JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ AUTO-SETUP: Configuração automática de séries portuguesas
 * ✅ CORRIGIDO: APIs whitelisted e tratamento de erros
 * ✅ CORRIGIDO: Todas as chamadas de API e tratamento de erros
 */

// ✅ VERIFICAÇÃO DE DEPENDÊNCIAS ANTES DE DEFINIR EVENTOS
if (typeof frappe === 'undefined' || !frappe.ui || !frappe.ui.form) {
    console.error('Frappe UI não está disponível para Company events');
} else {
    frappe.ui.form.on('Company', {

        // ========== SETUP INICIAL DO FORMULÁRIO ==========
        setup: function(frm) {
            try {
                console.log('🏢 Company setup iniciado para:', frm.doc.name || 'Nova empresa');

                // ✅ VERIFICAR SE FUNÇÕES EXISTEM ANTES DE CHAMAR
                if (typeof setup_portugal_filters === 'function') {
                    setup_portugal_filters(frm);
                } else {
                    console.warn('setup_portugal_filters não está definida');
                }

                if (typeof setup_custom_fields === 'function') {
                    setup_custom_fields(frm);
                } else {
                    console.warn('setup_custom_fields não está definida');
                }

                if (typeof setup_validators === 'function') {
                    setup_validators(frm);
                } else {
                    console.warn('setup_validators não está definida');
                }

                if (typeof setup_custom_events === 'function') {
                    setup_custom_events(frm);
                } else {
                    console.warn('setup_custom_events não está definida');
                }

                console.log('✅ Company setup concluído');
            } catch (error) {
                console.error('❌ Erro no setup da Company:', error);
                frappe.msgprint({
                    title: __('Erro de Inicialização'),
                    message: __('Erro ao configurar formulário da empresa: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== REFRESH DO FORMULÁRIO ==========
        refresh: function(frm) {
            try {
                console.log('🔄 Company refresh para:', frm.doc.name || 'Nova empresa');

                // ✅ VERIFICAR SE É EMPRESA PORTUGUESA COM VALIDAÇÃO SEGURA
                if (typeof is_portuguese_company_setup === 'function' && is_portuguese_company_setup(frm)) {
                    console.log('🇵🇹 Empresa portuguesa detectada');

                    // ✅ CONFIGURAR INTERFACE PORTUGUESA
                    if (typeof setup_portuguese_interface === 'function') {
                        setup_portuguese_interface(frm);
                    }

                    // ✅ MOSTRAR STATUS DE COMPLIANCE
                    if (typeof show_compliance_status === 'function') {
                        show_compliance_status(frm);
                    }

                    // ✅ ADICIONAR BOTÕES PERSONALIZADOS
                    if (typeof add_custom_buttons === 'function') {
                        add_custom_buttons(frm);
                    }
                } else {
                    console.log('🌍 Empresa não portuguesa ou função não disponível');
                }

                // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
                if (typeof setup_mandatory_fields === 'function') {
                    setup_mandatory_fields(frm);
                }

                // ✅ CONFIGURAR VALIDAÇÕES ESPECÍFICAS
                if (typeof setup_company_validations === 'function') {
                    setup_company_validations(frm);
                }

                console.log('✅ Company refresh concluído');
            } catch (error) {
                console.error('❌ Erro no refresh da Company:', error);
                // Não mostrar msgprint no refresh para evitar spam
            }
        },

        // ========== EVENTOS DE PAÍS ==========
        country: function(frm) {
            try {
                console.log('🌍 País alterado para:', frm.doc.country);

                if (frm.doc.country === 'Portugal') {
                    console.log('🇵🇹 Configurando para Portugal');

                    // ✅ MOSTRAR OPÇÃO DE COMPLIANCE PORTUGUÊS
                    if (typeof show_portugal_compliance_option === 'function') {
                        show_portugal_compliance_option(frm);
                    }

                    // ✅ CONFIGURAR CAMPOS PORTUGUESES
                    if (typeof setup_portugal_fields === 'function') {
                        setup_portugal_fields(frm);
                    }

                    // ✅ VALIDAR NIF SE EXISTIR
                    if (frm.doc.tax_id && typeof validate_portuguese_nif === 'function') {
                        validate_portuguese_nif(frm, frm.doc.tax_id);
                    }
                } else {
                    console.log('🌍 País não português, ocultando campos');

                    // ✅ OCULTAR CAMPOS PORTUGUESES
                    if (typeof hide_portugal_fields === 'function') {
                        hide_portugal_fields(frm);
                    }
                }
            } catch (error) {
                console.error('❌ Erro ao processar mudança de país:', error);
                frappe.show_alert({
                    message: __('Erro ao configurar país: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== EVENTOS DE COMPLIANCE PORTUGUÊS ==========
        portugal_compliance_enabled: function(frm) {
            try {
                console.log('🇵🇹 Portugal Compliance alterado para:', frm.doc.portugal_compliance_enabled);

                if (frm.doc.portugal_compliance_enabled) {
                    console.log('✅ Ativando Portugal Compliance');

                    // ✅ ATIVAR COMPLIANCE PORTUGUÊS
                    if (typeof enable_portugal_compliance === 'function') {
                        enable_portugal_compliance(frm);
                    } else {
                        console.warn('enable_portugal_compliance não está definida');
                        frappe.show_alert({
                            message: __('Portugal Compliance ativado! Salve para configurar séries.'),
                            indicator: 'green'
                        });
                        frm._portugal_compliance_activated = true;
                    }
                } else {
                    console.log('❌ Desativando Portugal Compliance');

                    // ✅ DESATIVAR COMPLIANCE PORTUGUÊS
                    if (typeof disable_portugal_compliance === 'function') {
                        disable_portugal_compliance(frm);
                    } else {
                        console.warn('disable_portugal_compliance não está definida');
                        frappe.show_alert({
                            message: __('Portugal Compliance desativado'),
                            indicator: 'orange'
                        });
                    }
                }
            } catch (error) {
                console.error('❌ Erro ao alterar Portugal Compliance:', error);
                frappe.msgprint({
                    title: __('Erro'),
                    message: __('Erro ao alterar Portugal Compliance: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== EVENTOS DE NIF ==========
        tax_id: function(frm) {
            try {
                if (frm.doc.country === 'Portugal' && frm.doc.tax_id) {
                    console.log('🆔 Validando NIF:', frm.doc.tax_id);

                    if (typeof validate_portuguese_nif === 'function') {
                        validate_portuguese_nif(frm, frm.doc.tax_id);
                    } else {
                        console.warn('validate_portuguese_nif não está definida');
                        // Validação básica local
                        const nif_clean = frm.doc.tax_id.replace(/[^\d]/g, '');
                        if (nif_clean.length === 9) {
                            frappe.show_alert({
                                message: __('NIF tem formato válido: {0}', [frm.doc.tax_id]),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __('NIF deve ter 9 dígitos: {0}', [frm.doc.tax_id]),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            } catch (error) {
                console.error('❌ Erro ao validar NIF:', error);
                frappe.show_alert({
                    message: __('Erro na validação do NIF: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== EVENTOS DE ABREVIATURA ==========
        abbr: function(frm) {
            try {
                if (frm.doc.abbr) {
                    console.log('🏷️ Validando abreviatura:', frm.doc.abbr);

                    if (typeof validate_company_abbreviation === 'function') {
                        validate_company_abbreviation(frm);
                    } else {
                        console.warn('validate_company_abbreviation não está definida');
                        // Validação básica local
                        const pattern = /^[A-Z0-9]{1,4}$/;
                        if (pattern.test(frm.doc.abbr)) {
                            frappe.show_alert({
                                message: __('Abreviatura válida: {0}', [frm.doc.abbr]),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __('Abreviatura deve ter 1-4 caracteres maiúsculos: {0}', [frm.doc.abbr]),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            } catch (error) {
                console.error('❌ Erro ao validar abreviatura:', error);
                frappe.show_alert({
                    message: __('Erro na validação da abreviatura: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== EVENTOS DE VALIDAÇÃO ==========
        validate: function(frm) {
            try {
                // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
                if (frm.doc.country === 'Portugal') {
                    console.log('🔍 Validando empresa portuguesa');

                    if (typeof validate_portuguese_company === 'function') {
                        validate_portuguese_company(frm);
                    } else {
                        console.warn('validate_portuguese_company não está definida');
                        // Validações básicas locais
                        let errors = [];

                        if (frm.doc.portugal_compliance_enabled) {
                            if (!frm.doc.tax_id) {
                                errors.push(__('NIF é obrigatório para empresas portuguesas'));
                            }
                            if (!frm.doc.abbr) {
                                errors.push(__('Abreviatura é obrigatória'));
                            }
                        }

                        if (errors.length > 0) {
                            frappe.msgprint({
                                title: __('Validação Portugal'),
                                message: errors.join('<br>'),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            } catch (error) {
                console.error('❌ Erro na validação:', error);
                frappe.msgprint({
                    title: __('Erro de Validação'),
                    message: __('Erro durante validação: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        },

        // ========== EVENTOS BEFORE_SAVE ==========
        before_save: function(frm) {
            try {
                // ✅ PREPARAR DADOS PARA COMPLIANCE
                if (frm.doc.country === 'Portugal' && frm.doc.portugal_compliance_enabled) {
                    console.log('💾 Preparando dados para compliance antes do save');

                    if (typeof prepare_portugal_compliance_data === 'function') {
                        prepare_portugal_compliance_data(frm);
                    } else {
                        console.warn('prepare_portugal_compliance_data não está definida');
                        // Preparação básica local
                        if (!frm.doc.default_currency) {
                            frm.doc.default_currency = 'EUR';
                            console.log('💰 Moeda padrão definida como EUR');
                        }
                    }
                }
            } catch (error) {
                console.error('❌ Erro no before_save:', error);
                frappe.msgprint({
                    title: __('Erro antes de Salvar'),
                    message: __('Erro ao preparar dados: {0}', [error.message]),
                    indicator: 'red'
                });
                frappe.validated = false;
            }
        },

        // ========== EVENTO AFTER_SAVE - CRIAR SÉRIES AUTOMATICAMENTE ==========
        after_save: function(frm) {
            try {
                // ✅ CRIAR SÉRIES AUTOMATICAMENTE APÓS ATIVAR COMPLIANCE
                if (frm.doc.country === 'Portugal' &&
                    frm.doc.portugal_compliance_enabled &&
                    frm._portugal_compliance_activated) {

                    console.log('🏭 Criando séries automaticamente após save');

                    // Reset flag
                    frm._portugal_compliance_activated = false;

                    // Criar séries automaticamente com delay
                    setTimeout(function() {
                        if (typeof create_portugal_series_automatic === 'function') {
                            create_portugal_series_automatic(frm);
                        } else {
                            console.warn('create_portugal_series_automatic não está definida');

                            // Fallback: mostrar opção manual
                            frappe.msgprint({
                                title: __('Portugal Compliance Ativado'),
                                message: __('Portugal Compliance foi ativado com sucesso!<br><br>Use o botão "Configurar Séries" para criar as séries portuguesas.'),
                                indicator: 'green',
                                primary_action: {
                                    label: __('Configurar Séries'),
                                    action: function() {
                                        if (typeof setup_portugal_series_manual === 'function') {
                                            setup_portugal_series_manual(frm);
                                        } else {
                                            frappe.show_alert({
                                                message: __('Função de criação de séries não disponível'),
                                                indicator: 'orange'
                                            });
                                        }
                                    }
                                }
                            });
                        }
                    }, 1000);
                }
            } catch (error) {
                console.error('❌ Erro no after_save:', error);
                frappe.msgprint({
                    title: __('Erro após Salvar'),
                    message: __('Erro ao processar após salvar: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        }
    });

    console.log('✅ Company form events registrados com sucesso');
}


// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_portugal_filters(frm) {
    /**
     * Configurar filtros específicos para Portugal
     */

    // ✅ FILTRO PARA MOEDA PADRÃO (EUR para Portugal)
    frm.set_query("default_currency", function() {
        if (frm.doc.country === 'Portugal') {
            return {
                filters: {
                    "name": "EUR"
                }
            };
        }
        return {};
    });
}

function setup_custom_fields(frm) {
    /**
     * Configurar campos personalizados para compliance português
     */

    // ✅ CONFIGURAR CAMPO PORTUGAL COMPLIANCE
    if (frm.fields_dict.portugal_compliance_enabled) {
        frm.fields_dict.portugal_compliance_enabled.df.description =
            "Ativar compliance com legislação portuguesa (ATCUD, SAF-T, QR Code)";
    }

    // ✅ CONFIGURAR CAMPO NIF
    if (frm.fields_dict.tax_id) {
        frm.fields_dict.tax_id.df.description =
            "NIF (Número de Identificação Fiscal) - 9 dígitos para empresas portuguesas";
    }

    // ✅ CONFIGURAR CAMPO ABREVIATURA
    if (frm.fields_dict.abbr) {
        frm.fields_dict.abbr.df.description =
            "Abreviatura da empresa (1-4 caracteres) - usada nas séries portuguesas";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE NIF
    frm.add_custom_validator = function(field_name, validator_fn) {
        if (frm.fields_dict[field_name] && frm.fields_dict[field_name].$input) {
            frm.fields_dict[field_name].$input.on('blur', validator_fn);
        }
    };
}

function setup_custom_events(frm) {
    /**
     * Configurar eventos personalizados
     */

    // ✅ EVENTO PERSONALIZADO PARA COMPLIANCE ATIVADO
    $(frm.wrapper).on('portugal_compliance_activated', function(e, data) {
        frappe.show_alert({
            message: `Portugal Compliance ativado: ${data.series_created} séries criadas`,
            indicator: 'green'
        });
    });

    // ✅ EVENTO PARA SÉRIES CRIADAS
    $(frm.wrapper).on('series_created', function(e, data) {
        frappe.msgprint({
            title: __('Séries Portuguesas Criadas'),
            message: data.message,
            indicator: 'green'
        });
    });
}

// ========== FUNÇÕES DE INTERFACE ==========

function setup_portuguese_interface(frm) {
    /**
     * Configurar interface específica para Portugal
     */

    // ✅ ADICIONAR INDICADOR DE COMPLIANCE
    if (frm.doc.portugal_compliance_enabled) {
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
     * Configurar layout específico para empresas portuguesas
     */

    // ✅ ADICIONAR SEÇÃO DE COMPLIANCE
    if (frm.doc.portugal_compliance_enabled) {
        add_compliance_section(frm);
    }

    // ✅ ADICIONAR SEÇÃO DE SÉRIES
    if (frm.doc.portugal_compliance_enabled && !frm.doc.__islocal) {
        add_series_section(frm);
    }
}

function add_compliance_section(frm) {
    /**
     * ✅ CORRIGIDO: Adicionar seção de informações de compliance
     */

    let series_count = 0;
    let communicated_series = 0;

    // ✅ BUSCAR ESTATÍSTICAS DE SÉRIES (APENAS SE NÃO FOR NOVO DOCUMENTO)
    if (!frm.doc.__islocal && frm.doc.name) {
        frappe.call({
            method: 'portugal_compliance.api.company_api.get_company_compliance_status',
            args: {
                company: frm.doc.name
            },
            freeze: false,
            callback: function(r) {
                if (r.message && r.message.success) {
                    series_count = r.message.series_count || 0;
                    communicated_series = r.message.communicated_series || 0;
                    update_compliance_section_data(frm, series_count, communicated_series);
                } else {
                    console.warn('Erro ao obter status de compliance:', r.message);
                    update_compliance_section_data(frm, 0, 0);
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro na chamada API:', error);
                update_compliance_section_data(frm, 0, 0);
            }
        });
    }

    let compliance_html = `
        <div class="portugal-compliance-info" style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #495057;">
                🇵🇹 Portugal Compliance - Status
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <strong>NIF:</strong> ${frm.doc.tax_id || 'Não definido'}<br>
                    <strong>Moeda:</strong> ${frm.doc.default_currency || 'Não definida'}<br>
                    <strong>Abreviatura:</strong> ${frm.doc.abbr || 'Não definida'}
                </div>
                <div class="col-md-6">
                    <strong>Séries Criadas:</strong> <span id="series-count">${series_count}</span><br>
                    <strong>Séries Comunicadas:</strong> <span id="communicated-count">${communicated_series}</span><br>
                    <strong>Status:</strong> <span class="indicator ${get_compliance_status(frm).color}">${get_compliance_status(frm).label}</span>
                </div>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO (VERIFICAR SE JÁ FOI ADICIONADO)
    if (!frm.compliance_section_added && frm.fields_dict.portugal_compliance_enabled) {
        $(frm.fields_dict.portugal_compliance_enabled.wrapper).after(compliance_html);
        frm.compliance_section_added = true;
    }
}

function update_compliance_section_data(frm, series_count, communicated_series) {
    /**
     * Atualizar dados da seção de compliance
     */
    $('#series-count').text(series_count);
    $('#communicated-count').text(communicated_series);
}

function add_series_section(frm) {
    /**
     * Adicionar seção de séries portuguesas
     */

    if (frm.doc.__islocal) return;

    let series_html = `
        <div class="portugal-series-info" style="
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        ">
            <h6 style="margin-bottom: 10px; color: #e65100;">
                📋 Séries Portuguesas Configuradas
            </h6>
            <div id="series-list">
                <p>Carregando séries...</p>
            </div>
        </div>
    `;

    // ✅ ADICIONAR HTML AO FORMULÁRIO
    if (!frm.series_section_added && frm.fields_dict.abbr) {
        $(frm.fields_dict.abbr.wrapper).after(series_html);
        frm.series_section_added = true;

        // ✅ CARREGAR SÉRIES
        load_company_series(frm);
    }
}

function load_company_series(frm) {
    /**
     * Carregar séries da empresa
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {
                company: frm.doc.name
            },
            fields: ['prefix', 'document_type', 'is_active', 'is_communicated', 'series_name'],
            order_by: 'document_type, prefix'
        },
        freeze: false,
        callback: function(r) {
            if (r.message) {
                display_company_series(frm, r.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro ao carregar séries:', error);
            $('#series-list').html('<p>Erro ao carregar séries.</p>');
        }
    });
}

// Tipos de documento que a lei portuguesa (Portaria 195/2020) exige
// comunicar à AT (ATCUD/série comunicada) - documentos emitidos a
// clientes. Todos os outros (lançamentos contábeis, faturas de
// compra, movimentos de stock internos, etc.) nunca têm série
// comunicada à AT por definição - mostrar "Não" para esses é um falso
// alarme, não um problema de configuração real.
const AT_CLIENT_FACING_DOCTYPES = ['Sales Invoice', 'POS Invoice', 'Payment Entry', 'Delivery Note'];

function display_company_series(frm, series_list) {
    /**
     * Exibir séries da empresa
     */

    if (!series_list || series_list.length === 0) {
        $('#series-list').html('<p>Nenhuma série configurada. Use o botão "Configurar Séries" para criar.</p>');
        return;
    }

    let html = '<table class="table table-sm table-bordered">';
    html += '<thead><tr><th>Prefixo</th><th>Tipo</th><th>Status</th><th>Comunicada</th></tr></thead><tbody>';

    series_list.forEach(function(series) {
        let status = series.is_active ? '✅ Ativa' : '❌ Inativa';
        let communicated;
        if (AT_CLIENT_FACING_DOCTYPES.includes(series.document_type)) {
            communicated = series.is_communicated ? '✅ Sim' : '⚠️ Não';
        } else {
            communicated = '<span style="color:#888;">N/A - Uso Interno</span>';
        }

        html += `<tr>
            <td><strong>${series.prefix}</strong></td>
            <td>${get_document_type_display(series.document_type)}</td>
            <td>${status}</td>
            <td>${communicated}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    $('#series-list').html(html);
}

function get_document_type_display(doctype) {
    /**
     * Obter display do tipo de documento
     */
    const displays = {
        'Sales Invoice': 'Fatura Venda',
        'Purchase Invoice': 'Fatura Compra',
        'POS Invoice': 'Fatura POS',
        'Payment Entry': 'Recibo',
        'Delivery Note': 'Guia Transporte',
        'Purchase Receipt': 'Guia Receção',
        'Stock Entry': 'Movimento Stock',
        'Quotation': 'Orçamento',
        'Sales Order': 'Encomenda Cliente',
        'Purchase Order': 'Encomenda Fornecedor',
        'Journal Entry': 'Lançamento Contábil',
        'Material Request': 'Requisição Material'
    };

    return displays[doctype] || doctype;
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
     * Obter status de compliance da empresa
     */

    if (!frm.doc.country || frm.doc.country !== 'Portugal') {
        return {
            label: 'Não Aplicável',
            color: 'grey',
            description: 'Empresa não é portuguesa'
        };
    }

    if (!frm.doc.portugal_compliance_enabled) {
        return {
            label: 'Inativo',
            color: 'red',
            description: 'Portugal Compliance não ativado'
        };
    }

    if (!frm.doc.tax_id) {
        return {
            label: 'Incompleto',
            color: 'orange',
            description: 'NIF não definido'
        };
    }

    if (!validate_nif_format(frm.doc.tax_id)) {
        return {
            label: 'NIF Inválido',
            color: 'red',
            description: 'NIF não tem formato válido'
        };
    }

    return {
        label: 'Ativo',
        color: 'green',
        description: 'Portugal Compliance configurado corretamente'
    };
}

// ========== FUNÇÕES DE BOTÕES PERSONALIZADOS ==========

function add_custom_buttons(frm) {
    /**
     * ✅ CORRIGIDO: Botões completos com métodos whitelisted
     */

    if (frm.doc.__islocal || !frm.doc.portugal_compliance_enabled) return;

    // ✅ GRUPO: Portugal Compliance (RESTAURADOS)
    frm.add_custom_button(__('Configurar Séries'), function() {
        setup_portugal_series_manual(frm);
    }, __('Portugal Compliance'));

    frm.add_custom_button(__('Verificar Compliance'), function() {
        check_compliance_status(frm);
    }, __('Portugal Compliance'));

    frm.add_custom_button(__('Estatísticas'), function() {
        show_series_statistics(frm);
    }, __('Portugal Compliance'));

    // ✅ RESTAURADO: Configurações Avançadas
    frm.add_custom_button(__('Configurações Avançadas'), function() {
        show_advanced_settings(frm);
    }, __('Portugal Compliance'));

    // ✅ GRUPO: Comunicação AT (CORRIGIDO)
    frm.add_custom_button(__('Comunicar Séries'), function() {
        communicate_all_series_to_at_fixed(frm);
    }, __('Comunicação AT'));

    frm.add_custom_button(__('Verificar Séries Comunicadas'), function() {
        check_communicated_series_fixed(frm);
    }, __('Comunicação AT'));

    // Botões "Configurar Credenciais AT" e "Testar Conexão AT" removidos
    // (2026-08-23): geriam Company.at_username/at_password/at_environment,
    // campos legados eliminados - Portugal Auth Settings é agora a única
    // fonte de verdade, com o seu próprio ecrã de configuração e o botão
    // nativo "Testar Ligação" (portugal_auth_settings.js).

    // ✅ GRUPO: Relatórios
    frm.add_custom_button(__('Ver Séries'), function() {
        view_series_list(frm);
    }, __('Relatórios'));

    frm.add_custom_button(__('Exportar Configuração'), function() {
        export_compliance_config(frm);
    }, __('Relatórios'));
}

// ========== FUNÇÕES CORRIGIDAS ==========

function communicate_all_series_to_at_fixed(frm) {
    /**
     * ✅ CORRIGIDO: Usar método whitelisted existente
     */

    frappe.confirm(
        __('Comunicar todas as séries não comunicadas à AT?<br><br>' +
           '<strong>⚠️ Importante:</strong><br>' +
           '• Certifique-se que as credenciais AT estão configuradas<br>' +
           '• Esta operação não pode ser desfeita'),
        function() {
            // ✅ USAR MÉTODO WHITELISTED EXISTENTE
            // Credenciais deixaram de ser enviadas no payload (2026-08-23) -
            // communicate_series_safe já lê Portugal Auth Settings
            // diretamente no servidor.
            frappe.call({
                method: 'portugal_compliance.api.company_api.save_company_settings',
                args: {
                    company_settings: {
                        company: frm.doc.name,
                        action: 'communicate_all_series'
                    }
                },
                freeze: true,
                freeze_message: __('Comunicando séries à AT...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('✅ Comunicação Iniciada'),
                            message: __('Processo de comunicação iniciado. Verifique os logs para detalhes.'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('❌ Erro na Comunicação'),
                            message: r.message ? r.message.error : __('Erro desconhecido'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(xhr, status, error) {
                    frappe.msgprint({
                        title: __('❌ Erro de Conexão'),
                        message: __('Erro ao comunicar: {0}', [error]),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function check_communicated_series_fixed(frm) {
    /**
     * ✅ CORRIGIDO: Verificar séries usando método whitelisted
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {
                company: frm.doc.name
            },
            fields: ['prefix', 'document_type', 'is_communicated', 'communication_date'],
            order_by: 'is_communicated desc, document_type'
        },
        callback: function(r) {
            if (r.message) {
                show_series_communication_status_fixed(frm, r.message);
            }
        },
        error: function(xhr, status, error) {
            frappe.msgprint({
                title: __('❌ Erro'),
                message: __('Erro ao carregar séries: {0}', [error]),
                indicator: 'red'
            });
        }
    });
}

// configure_at_credentials_fixed e test_at_connection_fixed removidas
// (2026-08-23): geriam Company.at_username/at_password/at_environment/
// at_certificate_number, campos legados eliminados - ver nota junto
// aos botões "Configurar Credenciais AT"/"Testar Conexão AT" removidos
// em add_custom_buttons, acima.

function show_series_communication_status_fixed(frm, series_data) {
    /**
     * ✅ CORRIGIDO: Mostrar status das séries
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Status de Comunicação das Séries'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'series_status'
            }
        ]
    });

    let communicated = series_data.filter(s => s.is_communicated).length;
    let total = series_data.length;

    let html = `
        <div class="series-communication-status">
            <h5>📊 Resumo: ${communicated}/${total} séries comunicadas</h5>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Prefixo</th>
                        <th>Tipo</th>
                        <th>Status</th>
                        <th>Data Comunicação</th>
                    </tr>
                </thead>
                <tbody>
    `;

    series_data.forEach(function(series) {
        let status = series.is_communicated ?
            '<span class="indicator green">✅ Comunicada</span>' :
            '<span class="indicator red">❌ Não Comunicada</span>';

        let date = series.communication_date ?
            frappe.datetime.str_to_user(series.communication_date) :
            '-';

        html += `
            <tr>
                <td><strong>${series.prefix}</strong></td>
                <td>${series.document_type}</td>
                <td>${status}</td>
                <td>${date}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';

    dialog.fields_dict.series_status.$wrapper.html(html);
    dialog.show();
}

function view_series_list(frm) {
    /**
     * ✅ NOVO: Ver lista de séries
     */
    frappe.set_route('List', 'Portugal Series Configuration', {
        'company': frm.doc.name
    });
}

function export_compliance_config(frm) {
    /**
     * ✅ NOVO: Exportar configuração
     */
    frappe.call({
        method: 'portugal_compliance.api.company_api.get_company_compliance_status',
        args: {
            company: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: __('Configuração de Compliance'),
                    message: `<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
                    indicator: 'blue'
                });
            }
        }
    });
}


// communicate_all_series_to_at / check_communicated_series /
// configure_at_credentials / test_at_connection / show_series_
// communication_status removidas (2026-08-23): código morto, nunca
// chamado por nenhum add_custom_button (as versões "_fixed" acima são
// as reais) - chamavam inclusive um módulo
// portugal_compliance.api.at_communication que nunca existiu neste
// repositório. As duas primeiras também dependiam de
// Company.at_username/at_password/at_environment, campos legados
// entretanto eliminados.

function generate_compliance_report(frm) {
    /**
     * ✅ NOVO: Gerar relatório de compliance
     */

    frappe.set_route('query-report', 'Portugal Compliance Report', {
        company: frm.doc.name
    });
}

function export_saft_report(frm) {
    /**
     * ✅ NOVO: Exportar relatório SAF-T
     */

    frappe.call({
        method: 'portugal_compliance.api.saft_export.generate_saft',
        args: {
            company: frm.doc.name,
            from_date: frappe.datetime.year_start(),
            to_date: frappe.datetime.year_end()
        },
        freeze: true,
        freeze_message: __('Gerando SAF-T...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                // Download do arquivo
                window.open(r.message.file_url);
            }
        }
    });
}

// ========== FUNÇÕES DE CRIAÇÃO DE SÉRIES ==========

function create_portugal_series_automatic(frm) {
    /**
     * ✅ NOVA: Criar séries automaticamente após ativar compliance
     */

    frappe.confirm(
        __('Deseja criar séries portuguesas automaticamente?<br><br>Isso irá criar séries para todos os tipos de documentos conforme legislação portuguesa.'),
        function() {
            // Usuário confirmou
            frappe.call({
                method: 'portugal_compliance.api.company_api.create_company_series',
                args: {
                    company: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Criando séries portuguesas...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('✅ {0} séries criadas automaticamente!', [r.message.created_count]),
                            indicator: 'green'
                        });

                        // Trigger evento personalizado
                        $(frm.wrapper).trigger('portugal_compliance_activated', {
                            series_created: r.message.created_count
                        });

                        // Recarregar formulário
                        setTimeout(function() {
                            frm.reload_doc();
                        }, 2000);

                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao criar séries automaticamente'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Erro na criação automática:', error);
                    frappe.msgprint({
                        title: __('Erro de Comunicação'),
                        message: __('Erro ao comunicar com servidor: {0}', [error]),
                        indicator: 'red'
                    });
                }
            });
        },
        function() {
            // Usuário cancelou
            frappe.show_alert({
                message: __('Criação de séries cancelada. Use o botão "Configurar Séries" quando necessário.'),
                indicator: 'orange'
            });
        }
    );
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_company(frm) {
    /**
     * Validações específicas para empresas portuguesas
     */

    let errors = [];

    // ✅ VALIDAR NIF OBRIGATÓRIO
    if (!frm.doc.tax_id) {
        errors.push(__('NIF é obrigatório para empresas portuguesas'));
    } else if (!validate_nif_format(frm.doc.tax_id)) {
        errors.push(__('NIF deve ter formato válido (9 dígitos)'));
    }

    // ✅ VALIDAR MOEDA
    if (frm.doc.default_currency && frm.doc.default_currency !== 'EUR') {
        frappe.msgprint({
            message: __('Recomenda-se usar EUR como moeda padrão para empresas portuguesas'),
            indicator: 'orange'
        });
    }

    // ✅ VALIDAR ABREVIATURA
    if (!frm.doc.abbr) {
        errors.push(__('Abreviatura é obrigatória'));
    } else if (!validate_abbreviation_format(frm.doc.abbr)) {
        errors.push(__('Abreviatura deve ter 1-4 caracteres alfanuméricos'));
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

function validate_portuguese_nif(frm, nif) {
    /**
     * ✅ CORRIGIDO: Validar NIF português usando API whitelisted
     */

    if (!nif) return;

    frappe.call({
        method: 'portugal_compliance.utils.jinja_methods.validate_portuguese_nif',
        args: {nif: nif},
        freeze: false,
        callback: function(r) {
            if (r.message !== undefined) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('NIF válido: {0}', [nif]),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('NIF inválido: {0}', [nif]),
                        indicator: 'red'
                    });
                }
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro na validação de NIF:', error);
        }
    });
}

function validate_nif_format(nif) {
    /**
     * Validar formato básico do NIF
     */
    if (!nif) return false;

    const nif_clean = nif.replace(/[^\d]/g, '');
    return nif_clean.length === 9 && /^\d{9}$/.test(nif_clean);
}

function validate_company_abbreviation(frm) {
    /**
     * Validar abreviatura da empresa
     */

    if (!frm.doc.abbr) return;

    if (!validate_abbreviation_format(frm.doc.abbr)) {
        frappe.show_alert({
            message: __('Abreviatura deve ter 1-4 caracteres alfanuméricos maiúsculos'),
            indicator: 'orange'
        });
    } else {
        frappe.show_alert({
            message: __('Abreviatura válida para séries portuguesas'),
            indicator: 'green'
        });
    }
}

function validate_abbreviation_format(abbr) {
    /**
     * Validar formato da abreviatura
     */
    if (!abbr) return false;

    // ✅ FORMATO: 1-4 caracteres alfanuméricos maiúsculos (abbr nativo do ERPNext pode ter só 1)
    const pattern = /^[A-Z0-9]{1,4}$/;
    return pattern.test(abbr);
}

// ========== FUNÇÕES DE COMPLIANCE ==========

function show_portugal_compliance_option(frm) {
    /**
     * Mostrar opção de compliance português
     */

    if (!frm.doc.portugal_compliance_enabled) {
        frappe.msgprint({
            title: __('Portugal Compliance'),
            message: __('Esta empresa está configurada para Portugal. Deseja ativar o Portugal Compliance?<br><br>Isso irá:<br>• Criar séries portuguesas automaticamente<br>• Ativar geração de ATCUD<br>• Configurar compliance com legislação portuguesa'),
            primary_action: {
                label: __('Ativar Portugal Compliance'),
                action: function() {
                    frm.set_value('portugal_compliance_enabled', 1);
                }
            }
        });
    }
}

function setup_portugal_fields(frm) {
    /**
     * Configurar campos específicos para Portugal
     */

    // ✅ DEFINIR MOEDA PADRÃO
    if (!frm.doc.default_currency) {
        frm.set_value('default_currency', 'EUR');
    }

    // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
    frm.toggle_reqd('tax_id', true);
    frm.toggle_reqd('abbr', true);
}

function hide_portugal_fields(frm) {
    /**
     * Ocultar campos específicos para Portugal
     */

    // ✅ DESATIVAR COMPLIANCE SE PAÍS MUDOU
    if (frm.doc.portugal_compliance_enabled) {
        frm.set_value('portugal_compliance_enabled', 0);
    }

    // ✅ REMOVER OBRIGATORIEDADE
    frm.toggle_reqd('tax_id', false);
}

function enable_portugal_compliance(frm) {
    /**
     * Ativar compliance português
     */

    if (frm.doc.country !== 'Portugal') {
        frappe.msgprint({
            message: __('Portugal Compliance só pode ser ativado para empresas portuguesas'),
            indicator: 'red'
        });
        frm.set_value('portugal_compliance_enabled', 0);
        return;
    }

    // ✅ MOSTRAR MENSAGEM DE ATIVAÇÃO
    frappe.show_alert({
        message: __('Portugal Compliance ativado! Salve a empresa para configurar séries automaticamente.'),
        indicator: 'green'
    });

    // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
    setup_portugal_fields(frm);

    // ✅ MARCAR PARA SETUP APÓS SAVE
    frm._portugal_compliance_activated = true;
}

function disable_portugal_compliance(frm) {
    /**
     * Desativar compliance português
     */

    frappe.confirm(
        __('Tem certeza que deseja desativar o Portugal Compliance?<br><br>Isso irá:<br>• Manter as séries existentes mas inativas<br>• Desativar geração automática de ATCUD<br>• Remover validações portuguesas'),
        function() {
            frappe.show_alert({
                message: __('Portugal Compliance desativado'),
                indicator: 'orange'
            });
        },
        function() {
            frm.set_value('portugal_compliance_enabled', 1);
        }
    );
}

function prepare_portugal_compliance_data(frm) {
    /**
     * Preparar dados para compliance antes do save
     */

    // ✅ VALIDAR DADOS OBRIGATÓRIOS
    if (!frm.doc.tax_id) {
        frappe.throw(__('NIF é obrigatório para ativar Portugal Compliance'));
    }

    if (!frm.doc.abbr) {
        frappe.throw(__('Abreviatura é obrigatória para ativar Portugal Compliance'));
    }

    // ✅ DEFINIR MOEDA PADRÃO
    if (!frm.doc.default_currency) {
        frm.doc.default_currency = 'EUR';
    }
}

// ========== FUNÇÕES DE AÇÕES ==========

function setup_portugal_series_manual(frm) {
    /**
     * ✅ CORRIGIDO: Configurar séries portuguesas usando API whitelisted
     */

    frappe.confirm(
        __('Configurar séries portuguesas para esta empresa?<br><br>Isso irá criar séries para todos os tipos de documentos conforme legislação portuguesa.'),
        function() {
            frappe.call({
                method: 'portugal_compliance.api.company_api.create_company_series',
                args: {
                    company: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Criando séries portuguesas...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Séries configuradas com sucesso! Criadas: {0}', [r.message.created_count]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Erro'),
                            message: r.message ? r.message.error : __('Erro ao configurar séries'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Erro na configuração manual:', error);
                    frappe.msgprint({
                        title: __('Erro de Comunicação'),
                        message: __('Erro ao comunicar com servidor: {0}', [error]),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function check_compliance_status(frm) {
    /**
     * ✅ CORRIGIDO: Verificar status de compliance usando API whitelisted
     */

    frappe.call({
        method: 'portugal_compliance.api.company_api.get_company_compliance_status',
        args: {
            company: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Verificando compliance...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                show_compliance_dialog(frm, r.message);
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao verificar compliance'),
                    indicator: 'red'
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro na verificação:', error);
            frappe.msgprint({
                title: __('Erro de Comunicação'),
                message: __('Erro ao comunicar com servidor: {0}', [error]),
                indicator: 'red'
            });
        }
    });
}

function show_compliance_dialog(frm, compliance_data) {
    /**
     * Mostrar dialog com status de compliance
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Status Portugal Compliance'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'compliance_info'
            }
        ]
    });

    let html = `
        <div class="compliance-status">
            <h5>Empresa: ${frm.doc.company_name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>NIF:</strong></td><td>${frm.doc.tax_id || 'Não definido'}</td></tr>
                        <tr><td><strong>País:</strong></td><td>${frm.doc.country}</td></tr>
                        <tr><td><strong>Moeda:</strong></td><td>${frm.doc.default_currency}</td></tr>
                        <tr><td><strong>Abreviatura:</strong></td><td>${frm.doc.abbr}</td></tr>
                        <tr><td><strong>Compliance:</strong></td><td>${compliance_data.compliance_enabled ? 'Ativo' : 'Inativo'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Estatísticas de Séries</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Séries:</strong></td><td>${compliance_data.series_count}</td></tr>
                        <tr><td><strong>Séries Comunicadas:</strong></td><td>${compliance_data.communicated_series}</td></tr>
                        <tr><td><strong>Status:</strong></td><td>${compliance_data.can_enable_compliance ? '✅ Conforme' : '⚠️ Pendente'}</td></tr>
                    </table>
                </div>
            </div>
        </div>
    `;

    dialog.fields_dict.compliance_info.$wrapper.html(html);
    dialog.show();
}

function show_series_statistics(frm) {
    /**
     * Mostrar estatísticas detalhadas das séries
     */

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Portugal Series Configuration',
            filters: {
                company: frm.doc.name
            },
            fields: ['document_type', 'prefix', 'is_active', 'is_communicated', 'total_documents_issued'],
            order_by: 'document_type'
        },
        freeze: true,
        freeze_message: __('Carregando estatísticas...'),
        callback: function(r) {
            if (r.message) {
                show_statistics_dialog(frm, r.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro ao carregar estatísticas:', error);
            frappe.msgprint({
                title: __('Erro'),
                message: __('Erro ao carregar estatísticas: {0}', [error]),
                indicator: 'red'
            });
        }
    });
}

function show_statistics_dialog(frm, series_data) {
    /**
     * Mostrar dialog com estatísticas detalhadas
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Estatísticas Detalhadas'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'statistics_info'
            }
        ]
    });

    let total_series = series_data.length;
    let active_series = series_data.filter(s => s.is_active).length;
    let communicated_series = series_data.filter(s => s.is_communicated).length;
    let total_documents = series_data.reduce((sum, s) => sum + (s.total_documents_issued || 0), 0);

    let html = `
        <div class="statistics-info">
            <h5>Estatísticas da Empresa</h5>
            <div class="row">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h6>Total Séries</h6>
                            <h3>${total_series}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h6>Séries Ativas</h6>
                            <h3>${active_series}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h6>Comunicadas</h6>
                            <h3>${communicated_series}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h6>Documentos</h6>
                            <h3>${total_documents}</h3>
                        </div>
                    </div>
                </div>
            </div>

            <h6 class="mt-4">Detalhes por Série</h6>
            <table class="table table-striped">
                <thead>
                    <tr><th>Prefixo</th><th>Tipo</th><th>Status</th><th>Comunicada</th><th>Documentos</th></tr>
                </thead>
                <tbody>
    `;

    series_data.forEach(function(series) {
        let status = series.is_active ? '✅ Ativa' : '❌ Inativa';
        let communicated = series.is_communicated ? '✅ Sim' : '⚠️ Não';

        html += `
            <tr>
                <td><strong>${series.prefix}</strong></td>
                <td>${get_document_type_display(series.document_type)}</td>
                <td>${status}</td>
                <td>${communicated}</td>
                <td>${series.total_documents_issued || 0}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.statistics_info.$wrapper.html(html);
    dialog.show();
}

function show_advanced_settings(frm) {
    /**
     * Mostrar configurações avançadas
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Configurações Avançadas Portugal Compliance'),
        fields: [
            {
                fieldtype: 'Section Break',
                label: __('Configurações de Séries')
            },
            {
                fieldtype: 'Check',
                fieldname: 'auto_create_series',
                label: __('Criar séries automaticamente'),
                default: 1,
                description: __('Criar séries portuguesas automaticamente ao ativar compliance')
            },
            {
                fieldtype: 'Check',
                fieldname: 'auto_generate_atcud',
                label: __('Gerar ATCUD automaticamente'),
                default: 1,
                description: __('Gerar ATCUD automaticamente para documentos')
            },
            {
                fieldtype: 'Section Break',
                label: __('Validações')
            },
            {
                fieldtype: 'Check',
                fieldname: 'validate_nif',
                label: __('Validar NIF'),
                default: 1,
                description: __('Validar formato de NIF português')
            },
            {
                fieldtype: 'Check',
                fieldname: 'require_customer_nif',
                label: __('Exigir NIF do cliente'),
                default: 0,
                description: __('Tornar NIF obrigatório para clientes')
            }
        ],
        primary_action_label: __('Salvar Configurações'),
        primary_action: function(values) {
            save_advanced_settings(frm, values);
            dialog.hide();
        }
    });

    dialog.show();
}

function save_advanced_settings(frm, settings) {
    /**
     * ✅ CORRIGIDO: Salvar configurações avançadas usando API whitelisted
     */

    frappe.call({
        method: 'portugal_compliance.api.company_api.save_company_settings',
        args: {
            company_settings: {
                company: frm.doc.name,
                ...settings
            }
        },
        freeze: true,
        freeze_message: __('Salvando configurações...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Configurações salvas com sucesso'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao salvar configurações'),
                    indicator: 'red'
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro ao salvar configurações:', error);
            frappe.msgprint({
                title: __('Erro de Comunicação'),
                message: __('Erro ao comunicar com servidor: {0}', [error]),
                indicator: 'red'
            });
        }
    });
}

// ========== FUNÇÕES AUXILIARES ==========

function is_portuguese_company_setup(frm) {
    /**
     * Verificar se empresa é portuguesa
     */
    return frm.doc.country === 'Portugal';
}

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios
     */

    if (frm.doc.country === 'Portugal' && frm.doc.portugal_compliance_enabled) {
        frm.toggle_reqd('tax_id', true);
        frm.toggle_reqd('abbr', true);
        frm.toggle_reqd('default_currency', true);
    }
}

function setup_company_validations(frm) {
    /**
     * ✅ CORRIGIDO: Configurar validações específicas da empresa
     */

    // ✅ VALIDAÇÃO DE NIF
    // Guarda adicional em .df (2026-08-24): field wrapper pode existir
    // sem .df ainda preenchido nalguns refreshes - sem isto, atribuir
    // .onchange rebentava com "Cannot set properties of undefined".
    if (frm.fields_dict.tax_id && frm.fields_dict.tax_id.df) {
        frm.fields_dict.tax_id.df.onchange = function() {
            if (frm.doc.country === 'Portugal' && frm.doc.tax_id) {
                validate_portuguese_nif(frm, frm.doc.tax_id);
            }
        };
    }

    // ✅ VALIDAÇÃO DE ABREVIATURA
    if (frm.fields_dict.abbr && frm.fields_dict.abbr.df) {
        frm.fields_dict.abbr.df.onchange = function() {
            if (frm.doc.abbr) {
                validate_company_abbreviation(frm);
            }
        };
    }
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Company JS loaded - Version 2.0.0 - FULLY CORRECTED - All APIs Fixed');
