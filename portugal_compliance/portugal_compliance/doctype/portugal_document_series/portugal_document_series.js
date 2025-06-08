// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

frappe.ui.form.on('Portugal Document Series', {

    // ========== EVENTOS PRINCIPAIS ==========

    refresh: function(frm) {
        /**
         * ✅ ADAPTADO: Refresh alinhado com nova abordagem
         */
        setup_custom_buttons(frm);
        setup_field_visibility(frm);
        setup_field_dependencies(frm);
        setup_real_time_validation(frm);
        setup_series_sync_indicator(frm);

        // Mostrar informações de sincronização
        if (frm.doc.series_configuration) {
            frm.add_custom_button(__('Ver Portugal Series Configuration'), function() {
                frappe.set_route('Form', 'Portugal Series Configuration', frm.doc.series_configuration);
            }, __('Sincronização'));
        }
    },

    onload: function(frm) {
        /**
         * ✅ ADAPTADO: Configurações iniciais alinhadas
         */
        setup_field_filters(frm);
        setup_default_values(frm);
        load_company_settings(frm);

        // Verificar se empresa tem compliance ativo
        if (frm.doc.company) {
            check_company_compliance(frm);
        }
    },

    before_save: function(frm) {
        /**
         * ✅ NOVO: Validações antes de salvar
         */
        return validate_before_save(frm);
    },

    after_save: function(frm) {
        /**
         * ✅ NOVO: Ações após salvar
         */
        sync_with_portugal_series_configuration(frm);
        refresh_naming_series_options(frm);
    },

    // ========== EVENTOS DE CAMPOS ==========

    company: function(frm) {
        /**
         * ✅ ADAPTADO: Validação de empresa portuguesa
         */
        if (frm.doc.company) {
            check_company_compliance(frm);
            update_prefix_suggestion(frm);
            load_existing_series(frm);
        }
    },

    document_type: function(frm) {
        /**
         * ✅ ADAPTADO: Usar mapeamento da nova abordagem
         */
        if (frm.doc.document_type) {
            suggest_prefix_for_document_type(frm);
            validate_document_type_compatibility(frm);
            update_field_requirements(frm);
        }
    },

    prefix: function(frm) {
        /**
         * ✅ ADAPTADO: Validação de prefixo em tempo real
         */
        if (frm.doc.prefix) {
            validate_prefix_format_realtime(frm);
            check_prefix_availability(frm);
            update_naming_series_preview(frm);
        }
    },

    validation_code: function(frm) {
        /**
         * ✅ NOVO: Sincronizar código de validação
         */
        if (frm.doc.validation_code) {
            frm.set_value('is_communicated', 1);
            sync_validation_code_with_config(frm);
        }
    },

    current_number: function(frm) {
        /**
         * ✅ NOVO: Validar número atual
         */
        validate_sequence_number(frm);
    }
});

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

function setup_custom_buttons(frm) {
    /**
     * ✅ ADAPTADO: Botões alinhados com nova abordagem
     */
    if (!frm.doc.__islocal) {

        // Grupo: Gestão de Séries
        frm.add_custom_button(__('Gerar ATCUD'), function() {
            generate_atcud_for_document(frm);
        }, __('Gestão'));

        frm.add_custom_button(__('Reiniciar Sequência'), function() {
            reset_series_sequence(frm);
        }, __('Gestão'));

        frm.add_custom_button(__('Ver Estatísticas'), function() {
            show_series_statistics(frm);
        }, __('Gestão'));

        // Grupo: Sincronização (NOVO)
        frm.add_custom_button(__('Sincronizar com Config'), function() {
            sync_with_portugal_series_configuration(frm);
        }, __('Sincronização'));

        frm.add_custom_button(__('Criar Portugal Series Config'), function() {
            create_portugal_series_configuration(frm);
        }, __('Sincronização'));

        // Grupo: Comunicação AT
        if (frm.doc.validation_code) {
            frm.add_custom_button(__('Testar Comunicação AT'), function() {
                test_at_communication(frm);
            }, __('Comunicação AT'));
        } else {
            frm.add_custom_button(__('Comunicar à AT'), function() {
                communicate_series_to_at(frm);
            }, __('Comunicação AT'));
        }

        // Grupo: Documentos
        frm.add_custom_button(__('Ver Documentos'), function() {
            view_documents_using_series(frm);
        }, __('Documentos'));
    }
}

function setup_field_visibility(frm) {
    /**
     * ✅ ADAPTADO: Visibilidade baseada no estado
     */

    // Campos de comunicação AT
    frm.toggle_display('validation_code', frm.doc.is_communicated);
    frm.toggle_display('communication_date', frm.doc.is_communicated);
    frm.toggle_display('at_response', frm.doc.is_communicated);

    // Campos de sincronização (NOVO)
    frm.toggle_display('series_configuration', frm.doc.series_configuration);

    // Campos de estatísticas
    frm.toggle_display('total_documents_issued', !frm.doc.__islocal);
    frm.toggle_display('usage_trend', !frm.doc.__islocal);
    frm.toggle_display('average_monthly_usage', !frm.doc.__islocal);
}

function setup_field_dependencies(frm) {
    /**
     * ✅ ADAPTADO: Dependências alinhadas
     */

    // Prefixo obrigatório se documento e empresa definidos
    frm.toggle_reqd('prefix', frm.doc.document_type && frm.doc.company);

    // Série obrigatória se prefixo definido
    frm.toggle_reqd('series_name', frm.doc.prefix);

    // Validação de campos de comunicação
    if (frm.doc.is_communicated) {
        frm.toggle_reqd('validation_code', true);
        frm.toggle_reqd('communication_date', true);
    }
}

function setup_real_time_validation(frm) {
    /**
     * ✅ NOVO: Validações em tempo real
     */

    // Validar prefixo enquanto digita
    if (frm.doc.prefix) {
        setTimeout(() => {
            validate_prefix_format_realtime(frm);
        }, 500);
    }

    // Atualizar preview da naming series
    if (frm.doc.prefix) {
        update_naming_series_preview(frm);
    }
}

function setup_series_sync_indicator(frm) {
    /**
     * ✅ NOVO: Indicador de sincronização
     */
    if (frm.doc.series_configuration) {
        frm.dashboard.add_indicator(__('Sincronizado com Portugal Series Config'), 'green');
    } else if (!frm.doc.__islocal) {
        frm.dashboard.add_indicator(__('Não sincronizado'), 'orange');
    }
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_before_save(frm) {
    /**
     * ✅ NOVO: Validações antes de salvar
     */
    return new Promise((resolve, reject) => {

        // Validar formato do prefixo
        if (!validate_prefix_format_sync(frm.doc.prefix)) {
            frappe.msgprint({
                title: __('Erro de Validação'),
                message: __('Formato do prefixo inválido. Use: XXYYYY+EMPRESA (ex: FT2025DSY) ou XX-YYYY-EMPRESA (ex: FT-2025-DSY)'),
                indicator: 'red'
            });
            reject();
            return;
        }

        // Validar compatibilidade com document type
        validate_document_type_prefix_compatibility(frm).then(() => {
            resolve();
        }).catch(() => {
            reject();
        });
    });
}

function validate_prefix_format_realtime(frm) {
    /**
     * ✅ ADAPTADO: Validação de prefixo em tempo real
     */
    if (!frm.doc.prefix) return;

    // Padrões aceitos (novo e antigo)
    const new_pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$/;  // FT2025DSY
    const old_pattern = /^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$/;    // FT-2025-DSY

    const is_valid = new_pattern.test(frm.doc.prefix) || old_pattern.test(frm.doc.prefix);

    if (is_valid) {
        frm.set_df_property('prefix', 'description',
            '<span style="color: green;">✅ Formato válido</span>');
    } else {
        frm.set_df_property('prefix', 'description',
            '<span style="color: red;">❌ Formato inválido. Use: FT2025DSY ou FT-2025-DSY</span>');
    }
}

function validate_prefix_format_sync(prefix) {
    /**
     * ✅ ADAPTADO: Validação síncrona de prefixo
     */
    if (!prefix) return false;

    const new_pattern = /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}$/;
    const old_pattern = /^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$/;

    return new_pattern.test(prefix) || old_pattern.test(prefix);
}

function validate_document_type_prefix_compatibility(frm) {
    /**
     * ✅ ADAPTADO: Validar compatibilidade com nova abordagem
     */
    return new Promise((resolve, reject) => {
        if (!frm.doc.document_type || !frm.doc.prefix) {
            resolve();
            return;
        }

        // Buscar código válido da nova abordagem
        frappe.call({
            method: 'portugal_compliance.regional.portugal.get_document_type_info',
            args: {
                document_type: frm.doc.document_type
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const valid_code = r.message.code;

                    // Extrair código do prefixo
                    let prefix_code;
                    if (frm.doc.prefix.includes('-')) {
                        prefix_code = frm.doc.prefix.split('-')[0];
                    } else {
                        const match = frm.doc.prefix.match(/^[A-Z]{2,4}/);
                        prefix_code = match ? match[0] : '';
                    }

                    if (prefix_code === valid_code) {
                        resolve();
                    } else {
                        frappe.msgprint({
                            title: __('Incompatibilidade'),
                            message: __('Prefixo "{0}" inválido para "{1}". Use: {2}', [prefix_code, frm.doc.document_type, valid_code]),
                            indicator: 'red'
                        });
                        reject();
                    }
                } else {
                    resolve(); // Se não conseguir validar, permite continuar
                }
            }
        });
    });
}

function validate_sequence_number(frm) {
    /**
     * ✅ NOVO: Validar número de sequência
     */
    if (frm.doc.current_number) {
        if (frm.doc.current_number < 1) {
            frappe.msgprint(__('Número atual deve ser maior que 0'));
            frm.set_value('current_number', 1);
        } else if (frm.doc.current_number > 99999999) {
            frappe.msgprint(__('Número atual não pode exceder 99.999.999'));
            frm.set_value('current_number', 99999999);
        }
    }
}

// ========== FUNÇÕES DE SINCRONIZAÇÃO ==========

function sync_with_portugal_series_configuration(frm) {
    /**
     * ✅ NOVO: Sincronizar com Portugal Series Configuration
     */
    if (!frm.doc.name) return;

    frappe.call({
        method: 'portugal_compliance.doctype.portugal_document_series.portugal_document_series.sync_with_portugal_series_configuration',
        args: {
            series_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Sincronizando...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Sincronização concluída com sucesso'),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: __('Erro na Sincronização'),
                    message: r.message ? r.message.error : __('Erro desconhecido'),
                    indicator: 'red'
                });
            }
        }
    });
}

function create_portugal_series_configuration(frm) {
    /**
     * ✅ NOVO: Criar Portugal Series Configuration correspondente
     */
    if (!frm.doc.name) {
        frappe.msgprint(__('Salve a série primeiro'));
        return;
    }

    frappe.call({
        method: 'portugal_compliance.doctype.portugal_document_series.portugal_document_series.create_portugal_series_configuration',
        args: {
            series_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Criando configuração...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Portugal Series Configuration criada: {0}', [r.message.config_name]),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: __('Erro'),
                    message: r.message ? r.message.error : __('Erro ao criar configuração'),
                    indicator: 'red'
                });
            }
        }
    });
}

function sync_validation_code_with_config(frm) {
    /**
     * ✅ NOVO: Sincronizar código de validação
     */
    if (frm.doc.series_configuration && frm.doc.validation_code) {
        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: 'Portugal Series Configuration',
                name: frm.doc.series_configuration,
                fieldname: 'validation_code',
                value: frm.doc.validation_code
            },
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert(__('Código de validação sincronizado'));
                }
            }
        });
    }
}

// ========== FUNÇÕES DE SUGESTÃO E AUTOMAÇÃO ==========

function suggest_prefix_for_document_type(frm) {
    /**
     * ✅ ADAPTADO: Sugerir prefixo baseado na nova abordagem
     */
    if (!frm.doc.document_type || !frm.doc.company) return;

    frappe.call({
        method: 'portugal_compliance.regional.portugal.get_document_type_info',
        args: {
            document_type: frm.doc.document_type
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const code = r.message.code;
                const year = new Date().getFullYear();

                // Obter abreviatura da empresa
                frappe.db.get_value('Company', frm.doc.company, 'abbr').then(result => {
                    if (result.message && result.message.abbr) {
                        const suggested_prefix = `${code}${year}${result.message.abbr}`;

                        if (!frm.doc.prefix) {
                            frm.set_value('prefix', suggested_prefix);
                            frappe.show_alert(__('Prefixo sugerido: {0}', [suggested_prefix]));
                        }
                    }
                });
            }
        }
    });
}

function update_prefix_suggestion(frm) {
    /**
     * ✅ ADAPTADO: Atualizar sugestão de prefixo
     */
    if (frm.doc.document_type && frm.doc.company && !frm.doc.prefix) {
        suggest_prefix_for_document_type(frm);
    }
}

function update_naming_series_preview(frm) {
    /**
     * ✅ NOVO: Mostrar preview da naming series
     */
    if (frm.doc.prefix) {
        const naming_series = `${frm.doc.prefix}.####`;
        frm.set_df_property('prefix', 'description',
            `<strong>Naming Series:</strong> ${naming_series}`);
    }
}

// ========== FUNÇÕES DE VERIFICAÇÃO ==========

function check_company_compliance(frm) {
    /**
     * ✅ ADAPTADO: Verificar compliance da empresa
     */
    if (!frm.doc.company) return;

    frappe.db.get_value('Company', frm.doc.company, ['country', 'portugal_compliance_enabled']).then(result => {
        if (result.message) {
            const company_data = result.message;

            if (company_data.country !== 'Portugal') {
                frm.dashboard.add_indicator(__('Empresa não é portuguesa'), 'red');
                frappe.msgprint({
                    title: __('Aviso'),
                    message: __('Esta empresa não está configurada para Portugal'),
                    indicator: 'orange'
                });
            } else if (!company_data.portugal_compliance_enabled) {
                frm.dashboard.add_indicator(__('Compliance não ativado'), 'orange');
                frappe.msgprint({
                    title: __('Aviso'),
                    message: __('Portugal Compliance não está ativado para esta empresa'),
                    indicator: 'orange'
                });
            } else {
                frm.dashboard.add_indicator(__('Empresa portuguesa com compliance'), 'green');
            }
        }
    });
}

function check_prefix_availability(frm) {
    /**
     * ✅ NOVO: Verificar disponibilidade do prefixo
     */
    if (!frm.doc.prefix || !frm.doc.company) return;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Portugal Document Series',
            filters: {
                prefix: frm.doc.prefix,
                company: frm.doc.company,
                name: ['!=', frm.doc.name || '']
            },
            fields: ['name', 'series_name']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frm.set_df_property('prefix', 'description',
                    `<span style="color: red;">❌ Prefixo já usado em: ${r.message[0].series_name}</span>`);
            }
        }
    });
}

// ========== FUNÇÕES DE AÇÃO ==========

function generate_atcud_for_document(frm) {
    /**
     * ✅ ADAPTADO: Gerar ATCUD usando nova abordagem
     */
    if (!frm.doc.validation_code) {
        frappe.msgprint(__('Série deve estar comunicada à AT primeiro'));
        return;
    }

    let sequence = prompt(__('Digite o número da sequência:'), frm.doc.current_number);
    if (!sequence) return;

    frappe.call({
        method: 'portugal_compliance.doctype.portugal_document_series.portugal_document_series.generate_atcud_for_document',
        args: {
            series_name: frm.doc.name,
            document_sequence: parseInt(sequence)
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('ATCUD Gerado'),
                    message: `
                        <strong>ATCUD:</strong> ${r.message.atcud_code}<br>
                        <strong>Sequência:</strong> ${r.message.sequence_number}<br>
                        <strong>Código Validação:</strong> ${r.message.validation_code}
                    `,
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

function reset_series_sequence(frm) {
    /**
     * ✅ ADAPTADO: Reiniciar sequência com sincronização
     */
    frappe.prompt({
        label: __('Novo número inicial'),
        fieldname: 'new_start',
        fieldtype: 'Int',
        default: 1,
        reqd: 1
    }, function(values) {
        frappe.call({
            method: 'portugal_compliance.doctype.portugal_document_series.portugal_document_series.reset_sequence',
            args: {
                series_name: frm.doc.name,
                new_start: values.new_start
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert(__('Sequência reiniciada com sucesso'));
                    frm.reload_doc();
                } else {
                    frappe.msgprint(__('Erro ao reiniciar sequência'));
                }
            }
        });
    }, __('Reiniciar Sequência'));
}

function show_series_statistics(frm) {
    /**
     * ✅ NOVO: Mostrar estatísticas da série
     */
    frappe.call({
        method: 'portugal_compliance.doctype.portugal_document_series.portugal_document_series.get_series_statistics',
        args: {
            series_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const stats = r.message.statistics;

                let message = `
                    <h4>Estatísticas da Série</h4>
                    <table class="table table-bordered">
                        <tr><td><strong>Total de Documentos:</strong></td><td>${stats.total_documents || 0}</td></tr>
                        <tr><td><strong>Uso Mensal Médio:</strong></td><td>${stats.monthly_average || 0}</td></tr>
                        <tr><td><strong>Último Documento:</strong></td><td>${stats.last_document || 'Nenhum'}</td></tr>
                        <tr><td><strong>Tendência:</strong></td><td>${stats.trend || 'Nova'}</td></tr>
                    </table>
                `;

                frappe.msgprint({
                    title: __('Estatísticas'),
                    message: message,
                    indicator: 'blue'
                });
            }
        }
    });
}

function communicate_series_to_at(frm) {
    /**
     * ✅ NOVO: Comunicar série à AT
     */
    frappe.confirm(__('Comunicar esta série à AT?'), function() {
        frappe.call({
            method: 'portugal_compliance.api.at_communication.communicate_series_to_at',
            args: {
                series_name: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Comunicando à AT...'),
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert(__('Série comunicada com sucesso'));
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Erro na Comunicação'),
                        message: r.message ? r.message.error : __('Erro desconhecido'),
                        indicator: 'red'
                    });
                }
            }
        });
    });
}

function test_at_communication(frm) {
    /**
     * ✅ NOVO: Testar comunicação AT
     */
    frappe.call({
        method: 'portugal_compliance.api.at_communication.test_series_communication',
        args: {
            series_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Testando comunicação...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Teste Bem-sucedido'),
                    message: __('Comunicação com AT funcionando corretamente'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Falha no Teste'),
                    message: r.message ? r.message.error : __('Erro na comunicação'),
                    indicator: 'red'
                });
            }
        }
    });
}

function view_documents_using_series(frm) {
    /**
     * ✅ ADAPTADO: Ver documentos que usam esta série
     */
    const naming_series = `${frm.doc.prefix}.####`;

    frappe.set_route('List', frm.doc.document_type, {
        'naming_series': naming_series,
        'company': frm.doc.company
    });
}

// ========== FUNÇÕES AUXILIARES ==========

function setup_field_filters(frm) {
    /**
     * ✅ ADAPTADO: Filtros de campos
     */

    // Filtrar apenas empresas portuguesas
    frm.set_query('company', function() {
        return {
            filters: {
                'country': 'Portugal'
            }
        };
    });

    // Filtrar document types válidos
    frm.set_query('document_type', function() {
        return {
            filters: {
                'name': ['in', [
                    'Sales Invoice', 'POS Invoice', 'Purchase Invoice', 'Payment Entry',
                    'Sales Order', 'Purchase Order', 'Quotation', 'Delivery Note',
                    'Purchase Receipt', 'Stock Entry', 'Journal Entry', 'Material Request'
                ]]
            }
        };
    });
}

function setup_default_values(frm) {
    /**
     * ✅ NOVO: Valores padrão
     */
    if (frm.doc.__islocal) {
        if (!frm.doc.current_number) {
            frm.set_value('current_number', 1);
        }

        if (!frm.doc.is_active) {
            frm.set_value('is_active', 1);
        }
    }
}

function load_company_settings(frm) {
    /**
     * ✅ NOVO: Carregar configurações da empresa
     */
    if (frm.doc.company) {
        frappe.db.get_value('Company', frm.doc.company, [
            'portugal_compliance_enabled', 'at_environment', 'at_username'
        ]).then(result => {
            if (result.message) {
                const company_data = result.message;

                // Definir ambiente padrão baseado na empresa
                if (company_data.at_environment && !frm.doc.at_environment) {
                    frm.set_value('at_environment', company_data.at_environment);
                }
            }
        });
    }
}

function load_existing_series(frm) {
    /**
     * ✅ NOVO: Carregar séries existentes para referência
     */
    if (frm.doc.company) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Portugal Document Series',
                filters: {
                    company: frm.doc.company
                },
                fields: ['prefix', 'document_type', 'series_name'],
                limit: 10
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    console.log('Séries existentes:', r.message);
                }
            }
        });
    }
}

function validate_document_type_compatibility(frm) {
    /**
     * ✅ NOVO: Validar compatibilidade do tipo de documento
     */
    if (frm.doc.document_type) {
        // Verificar se tipo de documento é suportado pela nova abordagem
        const supported_types = [
            'Sales Invoice', 'POS Invoice', 'Purchase Invoice', 'Payment Entry',
            'Sales Order', 'Purchase Order', 'Quotation', 'Delivery Note',
            'Purchase Receipt', 'Stock Entry', 'Journal Entry', 'Material Request'
        ];

        if (!supported_types.includes(frm.doc.document_type)) {
            frappe.msgprint({
                title: __('Tipo de Documento'),
                message: __('Este tipo de documento pode não ser totalmente suportado pela nova abordagem'),
                indicator: 'orange'
            });
        }
    }
}

function update_field_requirements(frm) {
    /**
     * ✅ NOVO: Atualizar requisitos de campos baseado no tipo
     */
    if (frm.doc.document_type) {
        // Documentos fiscais requerem validação AT
        const fiscal_documents = ['Sales Invoice', 'POS Invoice', 'Purchase Invoice', 'Payment Entry'];

        if (fiscal_documents.includes(frm.doc.document_type)) {
            frm.set_df_property('validation_code', 'description',
                '<span style="color: orange;">⚠️ Documento fiscal - requer comunicação à AT</span>');
        }
    }
}

function refresh_naming_series_options(frm) {
    /**
     * ✅ NOVO: Atualizar opções de naming series
     */
    if (frm.doc.prefix && frm.doc.document_type) {
        // Trigger refresh das opções de naming series no DocType
        frappe.call({
            method: 'portugal_compliance.utils.naming_series.refresh_naming_series_options',
            args: {
                document_type: frm.doc.document_type,
                company: frm.doc.company
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    console.log('Naming series options refreshed');
                }
            }
        });
    }
}

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Portugal Document Series', {
    setup: function(frm) {
        /**
         * ✅ NOVO: Configuração inicial do formulário
         */

        // Configurar formatters personalizados
        frm.set_indicator_formatter('validation_code', function(doc) {
            if (doc.validation_code) {
                return { indicator: 'green', title: __('Comunicada à AT') };
            } else {
                return { indicator: 'orange', title: __('Não comunicada') };
            }
        });

        // Configurar help text dinâmico
        frm.set_df_property('prefix', 'description',
            __('Formato: XXYYYY+EMPRESA (ex: FT2025DSY) ou XX-YYYY-EMPRESA (ex: FT-2025-DSY)'));
    }
});

// ========== LOG DE INICIALIZAÇÃO ==========
console.log('Portugal Document Series JS loaded - Version 2.0.0 - Aligned with new approach');
