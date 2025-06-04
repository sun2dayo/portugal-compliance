// portugal_compliance/portugal_compliance/doctype/portugal_document_series/portugal_document_series.js

frappe.ui.form.on('Portugal Document Series', {
    refresh: function(frm) {
        // Adicionar botões customizados
        add_custom_buttons(frm);

        // Adicionar indicadores de status
        add_status_indicators(frm);

        // Configurar campos baseado no status
        configure_fields_based_on_status(frm);

        // Auto-refresh para séries em comunicação
        if (frm.doc.communication_status === 'Retrying') {
            setTimeout(() => {
                frm.reload_doc();
            }, 10000);
        }
    },

    onload: function(frm) {
        // Configurar filtros para campos Link
        setup_field_filters(frm);

        // Configurar validações em tempo real
        setup_real_time_validations(frm);
    },

    prefix: function(frm) {
        // Validar formato em tempo real
        if (frm.doc.prefix) {
            validate_prefix_format(frm);
        }

        // Auto-gerar series_name se não definido
        if (!frm.doc.series_name) {
            auto_generate_series_name(frm);
        }
    },

    document_type: function(frm) {
        // Sugerir prefixo baseado no tipo de documento
        if (frm.doc.document_type && !frm.doc.prefix) {
            suggest_prefix(frm);
        }

        // Validar prefixo existente
        if (frm.doc.prefix) {
            validate_prefix_for_document_type(frm);
        }

        // Auto-gerar series_name
        auto_generate_series_name(frm);
    },

    company: function(frm) {
        // Verificar se empresa tem compliance português ativado
        if (frm.doc.company) {
            check_company_compliance(frm);
        }

        // Sugerir prefixo se ainda não definido
        if (frm.doc.document_type && !frm.doc.prefix) {
            suggest_prefix(frm);
        }

        // Filtrar configurações de série por empresa
        if (frm.doc.company) {
            frm.set_query('series_configuration', function() {
                return {
                    filters: {
                        'company': frm.doc.company,
                        'is_communicated': 1
                    }
                };
            });
        }
    },

    current_number: function(frm) {
        // Validar número de sequência
        if (frm.doc.current_number) {
            validate_sequence_number(frm);
        }
    },

    series_name: function(frm) {
        // Validar unicidade do nome da série
        if (frm.doc.series_name) {
            validate_series_name_uniqueness(frm);
        }
    },

    series_configuration: function(frm) {
        // Sincronizar dados da configuração selecionada
        if (frm.doc.series_configuration) {
            sync_configuration_data(frm);
        }
    }
});

function add_custom_buttons(frm) {
    // Limpar botões existentes
    frm.clear_custom_buttons();

    if (!frm.doc.__islocal) {

        // ========== BOTÕES DE CONFIGURAÇÃO ==========
        // Botão para criar configuração AT (se não existir)
        if (!frm.doc.series_configuration) {
            frm.add_custom_button(__('Criar Configuração AT'), function() {
                create_series_configuration(frm);
            }, __('Configuração'));
        }

        // Botão para sincronizar com configuração
        if (frm.doc.series_configuration) {
            frm.add_custom_button(__('Sincronizar Configuração'), function() {
                sync_configuration_data(frm);
            }, __('Configuração'));
        }

        // ========== BOTÕES DE ATCUD ==========
        // Botão para gerar ATCUD para documento
        if (frm.doc.validation_code) {
            frm.add_custom_button(__('Gerar ATCUD Documento'), function() {
                generate_atcud_dialog(frm);
            }, __('ATCUD'));

            frm.add_custom_button(__('Próximo Número ATCUD'), function() {
                get_next_atcud(frm);
            }, __('ATCUD'));
        }

        // ========== BOTÕES DE RELATÓRIOS ==========
        // Botão para ver estatísticas
        frm.add_custom_button(__('Ver Estatísticas'), function() {
            show_usage_statistics(frm);
        }, __('Relatórios'));

        // Botão para ver documentos relacionados
        if (frm.doc.total_documents_issued > 0) {
            frm.add_custom_button(__('Ver Documentos'), function() {
                view_related_documents(frm);
            }, __('Relatórios'));
        }

        // ========== BOTÕES DE AÇÕES ==========
        // Botão para reiniciar sequência (apenas para System Manager)
        if (frappe.user.has_role('System Manager')) {
            frm.add_custom_button(__('Reiniciar Sequência'), function() {
                reset_sequence_dialog(frm);
            }, __('Ações'));
        }

        // Botão para duplicar série
        frm.add_custom_button(__('Duplicar Série'), function() {
            duplicate_series(frm);
        }, __('Ações'));

        // Botão para atualizar estatísticas
        frm.add_custom_button(__('Atualizar Estatísticas'), function() {
            update_statistics(frm);
        }, __('Ações'));
    }
}

function add_status_indicators(frm) {
    // Limpar indicadores existentes
    frm.dashboard.clear_headline();

    // Indicador de configuração AT
    if (frm.doc.series_configuration) {
        frm.dashboard.add_indicator(__('Configuração AT: Ligada'), 'green');
    } else {
        frm.dashboard.add_indicator(__('Configuração AT: Não Ligada'), 'orange');
    }

    // Indicador de ATCUD
    if (frm.doc.validation_code) {
        frm.dashboard.add_indicator(__('ATCUD: {0}', [frm.doc.validation_code]), 'blue');
    } else {
        frm.dashboard.add_indicator(__('ATCUD: Não Disponível'), 'red');
    }

    // Indicador de comunicação
    if (frm.doc.is_communicated) {
        frm.dashboard.add_indicator(__('Comunicada à AT'), 'green');
    } else {
        frm.dashboard.add_indicator(__('Não Comunicada'), 'red');
    }

    // Indicador de ambiente
    if (frm.doc.at_environment) {
        const env_color = frm.doc.at_environment === 'production' ? 'green' : 'blue';
        frm.dashboard.add_indicator(__('Ambiente: {0}', [frm.doc.at_environment.toUpperCase()]), env_color);
    }

    // Indicador de uso
    if (frm.doc.total_documents_issued > 0) {
        frm.dashboard.add_indicator(__('Documentos Emitidos: {0}', [frm.doc.total_documents_issued]), 'blue');
    }

    // Indicador de sequência atual
    if (frm.doc.current_number > 1) {
        frm.dashboard.add_indicator(__('Próximo Número: {0}', [frm.doc.current_number]), 'blue');
    }

    // Indicador de tendência de uso
    if (frm.doc.usage_trend) {
        const trend_colors = {
            'Increasing': 'green',
            'Stable': 'blue',
            'Decreasing': 'orange',
            'New': 'grey',
            'Seasonal': 'purple'
        };
        const color = trend_colors[frm.doc.usage_trend] || 'grey';
        frm.dashboard.add_indicator(__('Tendência: {0}', [frm.doc.usage_trend]), color);
    }
}

function configure_fields_based_on_status(frm) {
    // Configurar campos baseado no status de comunicação
    if (frm.doc.is_communicated) {
        // Tornar campos críticos somente leitura após comunicação
        frm.set_df_property('prefix', 'read_only', 1);
        frm.set_df_property('document_type', 'read_only', 1);
        frm.set_df_property('company', 'read_only', 1);
        frm.set_df_property('series_configuration', 'read_only', 1);
    } else {
        frm.set_df_property('prefix', 'read_only', 0);
        frm.set_df_property('document_type', 'read_only', 0);
        frm.set_df_property('company', 'read_only', 0);
        frm.set_df_property('series_configuration', 'read_only', 0);
    }

    // Mostrar/ocultar campos baseado no status
    frm.toggle_display('validation_code', frm.doc.validation_code);
    frm.toggle_display('communication_date', frm.doc.communication_date);
    frm.toggle_display('at_environment', frm.doc.at_environment);
    frm.toggle_display('error_message', frm.doc.communication_status === 'Failed');
    frm.toggle_display('communication_attempts', frm.doc.communication_attempts > 0);
}

function setup_field_filters(frm) {
    // Filtro para empresa (apenas empresas portuguesas)
    frm.set_query('company', function() {
        return {
            filters: {
                'country': 'Portugal'
            }
        };
    });

    // Filtro para ano fiscal
    frm.set_query('fiscal_year', function() {
        return {
            filters: {
                'company': frm.doc.company
            }
        };
    });

    // Filtro para configuração de série (apenas comunicadas)
    frm.set_query('series_configuration', function() {
        return {
            filters: {
                'company': frm.doc.company,
                'is_communicated': 1,
                'document_type': frm.doc.document_type
            }
        };
    });
}

function setup_real_time_validations(frm) {
    // Validação em tempo real do prefixo
    if (frm.fields_dict.prefix && frm.fields_dict.prefix.$input) {
        frm.fields_dict.prefix.$input.on('input', function() {
            const value = $(this).val();
            if (value) {
                validate_prefix_format_realtime(frm, value);
            }
        });
    }

    // Validação em tempo real do nome da série
    if (frm.fields_dict.series_name && frm.fields_dict.series_name.$input) {
        frm.fields_dict.series_name.$input.on('input', function() {
            const value = $(this).val();
            if (value) {
                validate_series_name_realtime(frm, value);
            }
        });
    }
}

// ========== FUNÇÕES DE CONFIGURAÇÃO AT ==========

function create_series_configuration(frm) {
    if (!frm.doc.prefix || !frm.doc.document_type || !frm.doc.company) {
        frappe.msgprint(__('Preencha Prefixo, Tipo de Documento e Empresa primeiro'));
        return;
    }

    frappe.prompt([
        {
            label: __('Nome da Configuração'),
            fieldname: 'config_name',
            fieldtype: 'Data',
            reqd: 1,
            default: `${frm.doc.prefix}-CONFIG`,
            description: __('Nome para a configuração AT')
        },
        {
            label: __('Username AT'),
            fieldname: 'at_username',
            fieldtype: 'Data',
            reqd: 1,
            description: __('Username AT no formato NIF/Utilizador')
        },
        {
            label: __('Password AT'),
            fieldname: 'at_password',
            fieldtype: 'Password',
            reqd: 1,
            description: __('Password do utilizador AT')
        },
        {
            label: __('Ambiente'),
            fieldname: 'at_environment',
            fieldtype: 'Select',
            options: 'test\nproduction',
            default: 'test',
            reqd: 1,
            description: __('Ambiente AT para comunicação')
        }
    ], function(values) {
        frappe.call({
            method: 'frappe.client.insert',
            args: {
                doc: {
                    doctype: 'Portugal Series Configuration',
                    series_name: values.config_name,
                    prefix: frm.doc.prefix,
                    document_type: frm.doc.document_type,
                    company: frm.doc.company,
                    current_sequence: frm.doc.current_number || 1,
                    enable_at_communication: 1,
                    at_environment: values.at_environment,
                    at_username: values.at_username,
                    at_password: values.at_password,
                    is_active: 1
                }
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Configuração AT criada com sucesso!'));
                    frm.set_value('series_configuration', r.message.name);
                    frm.save();
                }
            }
        });
    }, __('Criar Configuração AT'));
}

function sync_configuration_data(frm) {
    if (!frm.doc.series_configuration) {
        frappe.msgprint(__('Nenhuma configuração AT selecionada'));
        return;
    }

    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Portugal Series Configuration',
            name: frm.doc.series_configuration
        },
        callback: function(r) {
            if (r.message) {
                const config = r.message;

                if (!config.is_communicated) {
                    frappe.msgprint({
                        title: __('Configuração Não Comunicada'),
                        message: __('A configuração selecionada ainda não foi comunicada à AT'),
                        indicator: 'orange'
                    });
                    return;
                }

                // Sincronizar dados
                frm.set_value('validation_code', config.validation_code);
                frm.set_value('at_environment', config.at_environment);
                frm.set_value('communication_date', config.communication_date);
                frm.set_value('is_communicated', config.is_communicated);
                frm.set_value('communication_status', config.communication_status);

                frappe.show_alert({
                    message: __('Dados sincronizados com sucesso!'),
                    indicator: 'green'
                });

                frm.refresh();
            }
        }
    });
}

// ========== FUNÇÕES DE ATCUD ==========

function generate_atcud_dialog(frm) {
    if (!frm.doc.validation_code) {
        frappe.msgprint(__('Série não tem código de validação AT'));
        return;
    }

    frappe.prompt([
        {
            label: __('Número do Documento'),
            fieldname: 'document_number',
            fieldtype: 'Int',
            reqd: 1,
            default: frm.doc.current_number,
            description: __('Digite o número sequencial do documento')
        }
    ], function(values) {
        frappe.call({
            method: 'generate_atcud_for_document',
            doc: frm.doc,
            args: {
                document_sequence: values.document_number
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const result = r.message;

                    const dialog = new frappe.ui.Dialog({
                        title: __('ATCUD Gerado'),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: `
                                    <div class="alert alert-success">
                                        <h5>✅ ATCUD Gerado com Sucesso!</h5>
                                        <hr>
                                        <p><strong>Código ATCUD:</strong> <code>${result.atcud_code}</code></p>
                                        <p><strong>Para Exibição:</strong> <code>${result.atcud_display}</code></p>
                                        <p><strong>Código de Validação:</strong> <code>${result.validation_code}</code></p>
                                        <p><strong>Número Sequencial:</strong> <code>${result.sequence_number}</code></p>
                                        <p><strong>Série:</strong> <code>${result.series_name}</code></p>
                                        <hr>
                                        <small class="text-muted">
                                            Use o "Código ATCUD" no campo do documento<br>
                                            Use "Para Exibição" na impressão/relatórios
                                        </small>
                                    </div>
                                `
                            }
                        ],
                        primary_action_label: __('Copiar ATCUD'),
                        primary_action: function() {
                            navigator.clipboard.writeText(result.atcud_code);
                            frappe.show_alert(__('ATCUD copiado para clipboard!'));
                            dialog.hide();
                        }
                    });

                    dialog.show();
                }
            }
        });
    }, __('Gerar ATCUD'));
}

function get_next_atcud(frm) {
    if (!frm.doc.validation_code) {
        frappe.msgprint(__('Série não tem código de validação AT'));
        return;
    }

    frappe.call({
        method: 'generate_atcud_for_document',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                const result = r.message;

                frappe.msgprint({
                    title: __('Próximo ATCUD'),
                    message: `
                        <p><strong>Próximo ATCUD:</strong> <code>${result.atcud_code}</code></p>
                        <p><strong>Número:</strong> ${result.sequence_number}</p>
                        <p><small>Este será o ATCUD do próximo documento criado</small></p>
                    `,
                    indicator: 'blue'
                });
            }
        }
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO (mantidas do código original) ==========

function validate_prefix_format(frm) {
    if (!frm.doc.prefix) return;

    const pattern = /^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$/;

    if (!pattern.test(frm.doc.prefix)) {
        frappe.msgprint({
            title: __('Formato Inválido'),
            message: __('Prefixo deve seguir o formato: XX-YYYY-EMPRESA (ex: FT-2025-COMP)'),
            indicator: 'red'
        });
        frm.set_value('prefix', '');
    }
}

function validate_prefix_format_realtime(frm, value) {
    const pattern = /^[A-Z]{2,4}-\d{4}-[A-Z0-9]+$/;
    const $input = frm.fields_dict.prefix.$input;

    if (pattern.test(value)) {
        $input.removeClass('invalid-input').addClass('valid-input');
    } else {
        $input.removeClass('valid-input').addClass('invalid-input');
    }
}

function validate_series_name_realtime(frm, value) {
    const $input = frm.fields_dict.series_name.$input;

    if (value && value.length >= 3) {
        $input.removeClass('invalid-input').addClass('valid-input');
    } else {
        $input.removeClass('valid-input').addClass('invalid-input');
    }
}

function auto_generate_series_name(frm) {
    if (frm.doc.prefix && frm.doc.document_type && !frm.doc.series_name) {
        const series_name = `${frm.doc.prefix}-${frm.doc.document_type.replace(' ', '')}`;
        frm.set_value('series_name', series_name);
    }
}

function suggest_prefix(frm) {
    if (!frm.doc.document_type || !frm.doc.company) return;

    // Obter abreviação da empresa
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: { name: frm.doc.company },
            fieldname: 'abbr'
        },
        callback: function(r) {
            if (r.message && r.message.abbr) {
                const year = new Date().getFullYear();
                const prefix = get_default_prefix(frm.doc.document_type);
                const company_abbr = r.message.abbr.toUpperCase();

                const suggested_prefix = `${prefix}-${year}-${company_abbr}`;

                if (!frm.doc.prefix) {
                    frm.set_value('prefix', suggested_prefix);
                }
            }
        }
    });
}

function get_default_prefix(document_type) {
    const prefix_map = {
        'Sales Invoice': 'FT',
        'Purchase Invoice': 'FC',
        'Payment Entry': 'RC',
        'Delivery Note': 'GT',
        'Purchase Receipt': 'GR',
        'Journal Entry': 'JE',
        'Stock Entry': 'GT',
        // NOVOS DOCTYPES ADICIONADOS
        'Quotation': 'OR',
        'Sales Order': 'EC',
        'Purchase Order': 'EF',
        'Material Request': 'REQ'
    };
    return prefix_map[document_type] || 'FT';
}

function validate_prefix_for_document_type(frm) {
    if (!frm.doc.document_type || !frm.doc.prefix) return;

        const valid_prefixes = {
        'Sales Invoice': ['FT', 'FS', 'FR', 'NC', 'ND'],
        'Purchase Invoice': ['FC', 'FT'],
        'Payment Entry': ['RC', 'RB'],
        'Delivery Note': ['GT', 'GR'],
        'Purchase Receipt': ['GR', 'GT'],
        'Journal Entry': ['JE'],
        'Stock Entry': ['GT'],
        // NOVOS DOCTYPES ADICIONADOS
        'Quotation': ['OR', 'ORC'],
        'Sales Order': ['EC', 'ECO'],
        'Purchase Order': ['EF', 'EFO'],
        'Material Request': ['REQ', 'MR']
    };

    const prefix_code = frm.doc.prefix.split('-')[0];
    const document_prefixes = valid_prefixes[frm.doc.document_type] || [];

    if (document_prefixes.length > 0 && !document_prefixes.includes(prefix_code)) {
        frappe.msgprint({
            title: __('Prefixo Inválido'),
            message: __('Para {0}, prefixos válidos são: {1}', [
                frm.doc.document_type,
                document_prefixes.join(', ')
            ]),
            indicator: 'orange'
        });
    }
}

function check_company_compliance(frm) {
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: { name: frm.doc.company },
            fieldname: ['country', 'portugal_compliance_enabled']
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.country !== 'Portugal') {
                    frappe.msgprint({
                        title: __('Empresa Inválida'),
                        message: __('Empresa deve estar configurada para Portugal'),
                        indicator: 'red'
                    });
                }

                if (!r.message.portugal_compliance_enabled) {
                    frappe.msgprint({
                        title: __('Compliance Não Ativado'),
                        message: __('Compliance português não está ativado para esta empresa'),
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

function validate_sequence_number(frm) {
    if (frm.doc.current_number < 1) {
        frappe.msgprint({
            title: __('Sequência Inválida'),
            message: __('Número atual deve ser maior que 0'),
            indicator: 'red'
        });
        frm.set_value('current_number', 1);
    }

    if (frm.doc.current_number > 99999999) {
        frappe.msgprint({
            title: __('Sequência Muito Grande'),
            message: __('Número atual não pode exceder 99,999,999'),
            indicator: 'red'
        });
        frm.set_value('current_number', 99999999);
    }
}

function validate_series_name_uniqueness(frm) {
    if (!frm.doc.series_name || frm.doc.__islocal) return;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Portugal Document Series',
            filters: {
                'series_name': frm.doc.series_name,
                'name': ['!=', frm.doc.name]
            },
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                frappe.msgprint({
                    title: __('Nome de Série Duplicado'),
                    message: __('Nome da série já existe'),
                    indicator: 'red'
                });
                frm.set_value('series_name', '');
            }
        }
    });
}

// ========== FUNÇÕES DE RELATÓRIOS (mantidas do código original) ==========

function show_usage_statistics(frm) {
    frappe.call({
        method: 'get_usage_statistics',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                const stats = r.message;

                const dialog = new frappe.ui.Dialog({
                    title: __('Estatísticas de Uso'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            options: get_statistics_html_enhanced(stats)
                        }
                    ]
                });

                dialog.show();
            }
        }
    });
}

function get_statistics_html_enhanced(stats) {
    return `
        <div class="row">
            <div class="col-md-6">
                <h5>${__('Informações da Série')}</h5>
                <p><strong>${__('Nome')}:</strong> ${stats.series_name}</p>
                <p><strong>${__('Prefixo')}:</strong> ${stats.prefix}</p>
                <p><strong>${__('Tipo de Documento')}:</strong> ${stats.document_type}</p>
                <p><strong>${__('Número Atual')}:</strong> ${stats.current_number}</p>
                <p><strong>${__('ATCUD')}:</strong> ${stats.validation_code || 'Não disponível'}</p>
            </div>
            <div class="col-md-6">
                <h5>${__('Dados de Uso')}</h5>
                <p><strong>${__('Total de Documentos')}:</strong> ${stats.total_documents}</p>
                <p><strong>${__('Média Mensal')}:</strong> ${stats.average_monthly_usage}</p>
                <p><strong>${__('Projeção Anual')}:</strong> ${stats.projected_annual_usage}</p>
                <p><strong>${__('Tendência')}:</strong> ${stats.usage_trend}</p>
                <p><strong>${__('Comunicada')}:</strong> ${stats.validation_code ? __('Sim') : __('Não')}</p>
                <p><strong>${__('Números Disponíveis')}:</strong> ${stats.available_numbers}</p>
            </div>
        </div>
        ${stats.validation_code ? `
        <div class="row mt-3">
            <div class="col-md-12">
                <div class="alert alert-info">
                    <strong>💡 Próximo ATCUD:</strong> ${stats.validation_code}-${stats.current_number.toString().padStart(8, '0')}
                </div>
            </div>
        </div>
        ` : ''}
    `;
}

function view_related_documents(frm) {
    frappe.set_route('List', frm.doc.document_type, {
        'portugal_series': frm.doc.name
    });
}

function reset_sequence_dialog(frm) {
    frappe.prompt([
        {
            label: __('Novo Número Inicial'),
            fieldname: 'new_start',
            fieldtype: 'Int',
            reqd: 1,
            default: 1,
            description: __('Digite o novo número inicial para a sequência')
        }
    ], function(values) {
        frappe.confirm(
            __('Tem certeza que deseja reiniciar a sequência para {0}? Esta ação não pode ser desfeita.', [values.new_start]),
            function() {
                frappe.call({
                    method: 'reset_sequence',
                    doc: frm.doc,
                    args: {
                        new_start: values.new_start
                    },
                    callback: function(r) {
                        frm.reload_doc();
                    }
                });
            }
        );
    }, __('Reiniciar Sequência'));
}

function duplicate_series(frm) {
    frappe.prompt([
        {
            label: __('Novo Nome da Série'),
            fieldname: 'new_name',
            fieldtype: 'Data',
            reqd: 1,
            description: __('Digite o nome para a nova série')
        },
        {
            label: __('Novo Prefixo'),
            fieldname: 'new_prefix',
            fieldtype: 'Data',
            reqd: 1,
            description: __('Digite o prefixo para a nova série')
        }
    ], function(values) {
        frappe.call({
            method: 'frappe.client.copy_doc',
            args: {
                dt: frm.doc.doctype,
                dn: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    const new_doc = frappe.model.sync(r.message);
                    new_doc[0].series_name = values.new_name;
                    new_doc[0].prefix = values.new_prefix;
                    new_doc[0].is_communicated = 0;
                    new_doc[0].validation_code = '';
                    new_doc[0].communication_date = '';
                    new_doc[0].current_number = 1;
                    new_doc[0].series_configuration = '';

                    frappe.set_route('Form', frm.doc.doctype, new_doc[0].name);
                }
            }
        });
    }, __('Duplicar Série'));
}

function update_statistics(frm) {
    frappe.show_alert({
        message: __('Atualizando estatísticas...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'frappe.client.save',
        args: {
            doc: frm.doc
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Estatísticas atualizadas com sucesso'),
                    indicator: 'green'
                });
                frm.reload_doc();
            }
        }
    });
}

// CSS para validação em tempo real e melhorias visuais
$('<style>')
    .prop('type', 'text/css')
    .html(`
        .valid-input {
            border-color: #28a745 !important;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
        }

        .invalid-input {
            border-color: #dc3545 !important;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
        }

        .usage-statistics-card {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .atcud-section {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }

        .config-section {
            background-color: #f3e5f5;
            border-left: 4px solid #9c27b0;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
    `)
    .appendTo('head');
