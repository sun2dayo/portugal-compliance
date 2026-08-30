// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * Stock Entry JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Integração completa com naming_series nativas e ATCUD automático
 * ✅ CORRIGIDO: Formato SEM HÍFENS (GM2025NDX em vez de GM-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Auto-seleção de séries portuguesas comunicadas (GM)
 * ✅ Geração automática de ATCUD para guias de movimentação
 * ✅ Validação de compliance português para movimentação de stock
 * ✅ Interface otimizada para guias de movimentação portuguesas
 */

frappe.ui.form.on('Stock Entry', {
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

            // show_compliance_status removida (2026-08-30, achado pelo
            // utilizador): mostrava um banner "Não Conforme - Série
            // não é portuguesa" para QUALQUER Stock Entry com serie
            // nativa - Stock Entry nao esta em document_hooks.py::
            // supported_doctypes desde 2026-08-22 (nao e documento
            // fiscal), por isso "nao conforme" era sempre falso e
            // enganoso, mesmo depois de destravar as validacoes de
            // serie/ATCUD nos commits anteriores (c8fbe3d, e0dc336).

            // ✅ ADICIONAR BOTÕES PERSONALIZADOS
            add_custom_buttons(frm);

            // ✅ CONFIGURAR CAMPOS OBRIGATÓRIOS
            setup_mandatory_fields(frm);
        }

        // ✅ ATUALIZAR DISPLAY DE ATCUD
        update_atcud_display(frm);

        // ✅ CONFIGURAR PRINT FORMATS
        setup_print_formats(frm);

        // ✅ CONFIGURAR VALIDAÇÕES DE STOCK
        setup_stock_validations(frm);
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
            // validate_portuguese_series removida (2026-08-30, achado
            // pelo utilizador): limpava (frm.set_value('naming_series',
            // '')) qualquer serie que nao seguisse o formato
            // GM2025EMPRESA.####, e avisava mesmo para prefixos != GM -
            // exatamente o mesmo bloqueio ja corrigido em validate:/
            // before_submit: (c8fbe3d, e0dc336), so que nesta funcao
            // ainda apagava o valor escolhido pelo utilizador. Stock
            // Entry nao e documento fiscal (ver notas anteriores).

            // ✅ VERIFICAR STATUS DE COMUNICAÇÃO
            check_series_communication_status(frm);

            // ✅ MOSTRAR INFORMAÇÕES DA SÉRIE
            show_series_info(frm);
        }
    },

    // ========== EVENTOS DE STOCK ENTRY TYPE ==========
    stock_entry_type: function(frm) {
        if (frm.doc.stock_entry_type) {
            // ✅ CONFIGURAR CAMPOS BASEADO NO TIPO
            configure_fields_by_type(frm);

            // ✅ VALIDAR TIPO PARA COMPLIANCE
            validate_stock_entry_type(frm);
        }
    },

    // ========== EVENTOS DE ARMAZÉNS ==========
    from_warehouse: function(frm) {
        if (frm.doc.from_warehouse) {
            validate_warehouse(frm, frm.doc.from_warehouse, 'origem');
        }
    },

    to_warehouse: function(frm) {
        if (frm.doc.to_warehouse) {
            validate_warehouse(frm, frm.doc.to_warehouse, 'destino');
        }
    },

    // ========== EVENTOS DE VALIDAÇÃO ==========
    validate: function(frm) {
        // ✅ VALIDAÇÕES ESPECÍFICAS PORTUGUESAS
        if (is_portuguese_company(frm)) {
            validate_portuguese_stock_entry(frm);
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

    // ✅ FILTRO PARA ARMAZÉNS DA EMPRESA
    frm.set_query("from_warehouse", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "disabled": 0,
                "is_group": 0
            }
        };
    });

    frm.set_query("to_warehouse", function() {
        return {
            filters: {
                "company": frm.doc.company,
                "disabled": 0,
                "is_group": 0
            }
        };
    });

    // ✅ FILTRO PARA ITENS ATIVOS
    frm.set_query("item_code", "items", function() {
        return {
            filters: {
                "disabled": 0,
                "is_stock_item": 1
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
        frm.fields_dict.atcud_code.df.description = "Código Único de Documento - Gerado automaticamente para guias de movimentação";
    }

    // ✅ CONFIGURAR CAMPO NAMING SERIES (CORRIGIDO: SEM HÍFENS)
    if (frm.fields_dict.naming_series) {
        frm.fields_dict.naming_series.df.description = "Série portuguesa para guias de movimentação (GM2025EMPRESA.####)";
    }

    // ✅ CONFIGURAR CAMPOS DE MOVIMENTAÇÃO
    if (frm.fields_dict.stock_entry_type) {
        frm.fields_dict.stock_entry_type.df.description = "Tipo de movimentação conforme legislação portuguesa";
    }
}

function setup_validators(frm) {
    /**
     * Configurar validadores personalizados
     */

    // ✅ VALIDADOR DE QUANTIDADES
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

    // ✅ EVENTO PARA CÁLCULO DE TOTAIS DE STOCK
    $(frm.wrapper).on('items_updated', function() {
        calculate_stock_totals(frm);
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

// add_compliance_section, add_stock_movement_section,
// show_compliance_status e get_compliance_status removidas
// (2026-08-30, achado pelo utilizador): os dois cartões HTML e o
// indicador/banner de dashboard que geravam ("Portugal Compliance:
// Não Conforme", "Não Conforme - Série não é portuguesa", os cartões
// "Informações de Compliance Português"/"Informações de Movimentação
// de Stock") assumiam todos que Stock Entry e um documento fiscal com
// serie/ATCUD proprios - nao e, desde 2026-08-22
// (document_hooks.py::supported_doctypes nao o inclui). Depois de
// destravar as validações de série/ATCUD (commits c8fbe3d, e0dc336),
// estes elementos ficaram ainda mais obviamente errados: mostravam
// "Não Conforme" (banner, indicador E cartão, em triplicado) por um
// requisito que a própria app já não impõe. add_compliance_section em
// particular nunca chegava sequer a renderizar na prática (guardada
// por frm.doc.atcud_code, que Stock Entry nunca preenche) - código
// morto desde sempre, não só desde esta correção.

function setup_portuguese_layout(frm) {
    /**
     * Configurar layout específico para guias de movimentação portuguesas
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

    // Botões "Gerar ATCUD"/"Verificar Série" (menu "Portugal
    // Compliance") removidos (2026-08-30, achado pelo utilizador: o
    // menu aparecia num Stock Entry ja submetido, ao lado do menu
    // gemeo "🇵🇹 Portugal Compliance" do ficheiro partilhado -
    // corrigido em portugal_compliance.js na mesma sessao). "Gerar
    // ATCUD" nao e so cosmetico - chamava generate_manual_atcud_
    // certified no servidor, arriscando gerar um ATCUD falso para um
    // documento que a lei nunca exige assinar (Stock Entry nao esta
    // em document_hooks.py::supported_doctypes desde 2026-08-22).
    // "Verificar Série" so mostraria "Série não encontrada" para
    // qualquer serie nativa.

    // ✅ BOTÃO PARA VALIDAR ARMAZÉNS
    if (frm.doc.from_warehouse || frm.doc.to_warehouse) {
        frm.add_custom_button(__('Validar Armazéns'), function() {
            validate_all_warehouses(frm);
        }, __('Validações'));
    }

    // ✅ BOTÃO PARA CALCULAR TOTAIS DE STOCK
    if (frm.doc.items && frm.doc.items.length > 0) {
        frm.add_custom_button(__('Calcular Totais'), function() {
            calculate_and_show_stock_totals(frm);
        }, __('Stock'));
    }

    // ✅ BOTÃO PARA IMPRIMIR GUIA PORTUGUESA
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Imprimir Guia GM'), function() {
            print_portuguese_stock_entry(frm);
        }, __('Imprimir'));
    }

    // ✅ BOTÃO PARA VERIFICAR STOCK DISPONÍVEL
    if (frm.doc.from_warehouse && frm.doc.items) {
        frm.add_custom_button(__('Verificar Stock'), function() {
            check_available_stock(frm);
        }, __('Stock'));
    }

    // ✅ BOTÃO PARA ANALISAR MOVIMENTAÇÃO
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Analisar Movimentação'), function() {
            analyze_stock_movement(frm);
        }, __('Stock'));
    }
}

// ========== FUNÇÕES DE NAMING SERIES ==========

function setup_automatic_naming_series(frm) {
    /**
     * ✅ CORRIGIDO: Configurar naming series automática para empresa portuguesa (formato SEM HÍFENS)
     */

    if (!frm.doc.company || frm.doc.naming_series) return;

    // ✅ BUSCAR SÉRIES PORTUGUESAS DISPONÍVEIS PARA GUIAS DE MOVIMENTAÇÃO (SEM HÍFENS)
    frappe.call({
        method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
        args: {
            doctype: 'Stock Entry',
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.success && r.message.series.length > 0) {
                // ✅ PRIORIZAR SÉRIES COMUNICADAS GM (formato SEM HÍFENS: GM2025NDX)
                let gm_series = r.message.series.filter(s => s.prefix.startsWith('GM'));
                let communicated_series = gm_series.filter(s => s.is_communicated);
                let series_to_use = communicated_series.length > 0 ? communicated_series : gm_series;

                if (series_to_use.length > 0) {
                    // ✅ AUTO-SELECIONAR PRIMEIRA SÉRIE GM
                    frm.set_value('naming_series', series_to_use[0].naming_series);

                    // ✅ MOSTRAR INFORMAÇÃO
                    if (communicated_series.length > 0) {
                        frappe.show_alert({
                            message: __('Série GM comunicada selecionada automaticamente'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Série GM não comunicada selecionada. Comunique à AT antes de submeter.'),
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
        message = __('Série GM comunicada à AT em {0}', [frappe.datetime.str_to_user(series_info.communication_date)]);
        indicator = 'green';
    } else {
        message = __('Série GM não comunicada à AT. Comunique antes de submeter guias.');
        indicator = 'orange';
    }

    frappe.show_alert({
        message: message,
        indicator: indicator
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO ==========

function validate_portuguese_stock_entry(frm) {
    /**
     * Validações específicas para guias de movimentação portuguesas
     */

    let errors = [];

    // Exigencia de naming_series "GM" removida (2026-08-30, achado pelo
    // utilizador): Stock Entry (movimentos internos, acertos, entradas
    // iniciais) nao e um documento emitido a terceiros nos termos da
    // Portaria 195/2020 - ja tinha sido excluido do ambito fiscal do
    // lado do servidor em 2026-08-22 (document_hooks.py:
    // supported_doctypes nao inclui Stock Entry; nunca teve serie
    // comunicada, nem devia). Esta validacao client-side ficou para
    // tras a bloquear (frappe.validated = false) o uso de series
    // nativas do ERPNext (ex: MAT-STE-.YYYY.-) em QUALQUER Stock Entry
    // de empresa portuguesa, contradizendo essa decisao ja tomada. Sem
    // suporte real do lado do servidor para emitir GM via Stock Entry
    // (nao esta em supported_doctypes, nao gera ATCUD, nao comunica
    // serie), um opt-in aqui seria uma funcionalidade a meio - se essa
    // emissao vier a ser suportada oficialmente, a validacao volta
    // junto com o resto do mecanismo (ATCUD, comunicacao de serie),
    // nao isolada aqui.

    // ✅ VALIDAR TIPO DE MOVIMENTAÇÃO
    if (!frm.doc.stock_entry_type) {
        errors.push(__('Tipo de movimentação é obrigatório'));
    }

    // ✅ VALIDAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        errors.push(__('Pelo menos um item é obrigatório'));
    }

    // ✅ VALIDAR ARMAZÉNS BASEADO NO TIPO
    if (frm.doc.stock_entry_type) {
        let warehouse_errors = validate_warehouses_by_type(frm);
        errors = errors.concat(warehouse_errors);
    }

    // ✅ VALIDAR QUANTIDADES
    if (frm.doc.items) {
        let items_with_zero_qty = frm.doc.items.filter(item => !item.qty || item.qty <= 0);
        if (items_with_zero_qty.length > 0) {
            errors.push(__('Todos os itens devem ter quantidade maior que zero'));
        }
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

function validate_warehouses_by_type(frm) {
    /**
     * Validar armazéns baseado no tipo de movimentação
     */

    let errors = [];
    let type = frm.doc.stock_entry_type;

    switch(type) {
        case 'Material Transfer':
            if (!frm.doc.from_warehouse && !frm.doc.to_warehouse) {
                // Verificar se todos os itens têm armazéns definidos
                let items_without_warehouses = frm.doc.items.filter(item =>
                    !item.s_warehouse || !item.t_warehouse
                );
                if (items_without_warehouses.length > 0) {
                    errors.push(__('Para transferência, defina armazéns origem e destino'));
                }
            }
            break;

        case 'Material Issue':
            if (!frm.doc.from_warehouse) {
                let items_without_source = frm.doc.items.filter(item => !item.s_warehouse);
                if (items_without_source.length > 0) {
                    errors.push(__('Para saída, defina armazém de origem'));
                }
            }
            break;

        case 'Material Receipt':
            if (!frm.doc.to_warehouse) {
                let items_without_target = frm.doc.items.filter(item => !item.t_warehouse);
                if (items_without_target.length > 0) {
                    errors.push(__('Para entrada, defina armazém de destino'));
                }
            }
            break;
    }

    return errors;
}

function validate_warehouse(frm, warehouse, type) {
    /**
     * Validar armazém específico
     */

    if (!warehouse) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Warehouse',
            filters: {name: warehouse},
            fieldname: ['company', 'disabled', 'is_group']
        },
        callback: function(r) {
            if (r.message) {
                let errors = [];

                if (r.message.company !== frm.doc.company) {
                    errors.push('não pertence à empresa');
                }
                if (r.message.disabled) {
                    errors.push('está desativado');
                }
                if (r.message.is_group) {
                    errors.push('é um grupo');
                }

                if (errors.length > 0) {
                    frappe.show_alert({
                        message: __('Armazém {0} {1}', [type, errors.join(', ')]),
                        indicator: 'red'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Armazém {0} válido', [type]),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

function validate_stock_entry_type(frm) {
    /**
     * Validar tipo de movimentação para compliance
     */

    if (!frm.doc.stock_entry_type) return;

    // ✅ TIPOS PERMITIDOS PARA PORTUGAL
    let allowed_types = [
        'Material Transfer',
        'Material Issue',
        'Material Receipt',
        'Manufacture',
        'Repack',
        'Send to Subcontractor'
    ];

    if (!allowed_types.includes(frm.doc.stock_entry_type)) {
        frappe.msgprint({
            title: __('Tipo Não Suportado'),
            message: __('Tipo de movimentação não suportado para compliance português'),
            indicator: 'orange'
        });
    }
}

function validate_before_submit_portuguese(frm) {
    /**
     * Validações críticas antes da submissão.
     *
     * Exigencia de ATCUD/serie comunicada removida daqui (2026-08-30,
     * mesmo achado do utilizador que ja tinha corrigido a validacao de
     * naming_series em validate: - ver comentario em
     * validate_portuguese_stock_entry). Stock Entry nao esta em
     * document_hooks.py::supported_doctypes desde 2026-08-22, nunca
     * gera ATCUD nem comunica serie - o check "ATCUD e obrigatorio"
     * exigia um campo que estruturalmente NUNCA existe neste ponto (o
     * ATCUD so e gerado no servidor, DEPOIS de submeter, em qualquer
     * doctype desta app - ver generate_atcud_on_submit), bloqueando a
     * submissao de TODO Stock Entry, sempre, sem excecao possivel.
     *
     * A verificacao de stock disponivel (para Material Issue/Transfer)
     * e generica/nao-fiscal - mantida tal como estava.
     */
    return new Promise((resolve) => {
        if (frm.doc.stock_entry_type === 'Material Issue' ||
            frm.doc.stock_entry_type === 'Material Transfer') {
            validate_stock_availability(frm).then(resolve);
        } else {
            resolve();
        }
    });
}

function validate_stock_availability(frm) {
    /**
     * Validar disponibilidade de stock
     */

    return new Promise((resolve) => {
        if (!frm.doc.items || frm.doc.items.length === 0) {
            resolve();
            return;
        }

        let items_to_check = frm.doc.items.filter(item =>
            item.s_warehouse && item.qty > 0
        );

        if (items_to_check.length === 0) {
            resolve();
            return;
        }

        // Verificar stock para cada item
        let checks_completed = 0;
        let stock_errors = [];

        items_to_check.forEach(function(item) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Bin',
                    filters: {
                        item_code: item.item_code,
                        warehouse: item.s_warehouse
                    },
                    fieldname: 'actual_qty'
                },
                callback: function(r) {
                    checks_completed++;

                    if (r.message) {
                        let available_qty = r.message.actual_qty || 0;
                        if (available_qty < item.qty) {
                            stock_errors.push(
                                __('Item {0}: disponível {1}, necessário {2}',
                                [item.item_code, available_qty, item.qty])
                            );
                        }
                    }

                    if (checks_completed === items_to_check.length) {
                        if (stock_errors.length > 0) {
                            frappe.msgprint({
                                title: __('Stock Insuficiente'),
                                message: stock_errors.join('<br>'),
                                indicator: 'red'
                            });
                        }
                        resolve();
                    }
                }
            });
        });
    });
}

// ========== FUNÇÕES DE STOCK ==========

function setup_stock_validations(frm) {
    /**
     * Configurar validações específicas de stock
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
                calculate_stock_totals(frm);
            };
        }

        // ✅ VALIDAR BASIC RATE
        var basic_rate_field = frm.fields_dict.items.grid.get_field('basic_rate');
        if (basic_rate_field && basic_rate_field.df) {
            basic_rate_field.df.onchange = function() {
                calculate_stock_totals(frm);
            };
        }
    }
}

function calculate_stock_totals(frm) {
    /**
     * Calcular totais da movimentação de stock
     */

    let total_qty = 0;
    let total_value = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let qty = item.qty || 0;
            let rate = item.basic_rate || 0;
            total_qty += qty;
            total_value += (qty * rate);
        });
    }

    return {
        total_qty: total_qty,
        total_value: total_value
    };
}

function calculate_total_qty(frm) {
    /**
     * Calcular quantidade total
     */

    let total_qty = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            total_qty += (item.qty || 0);
        });
    }

    return total_qty;
}

function calculate_total_value(frm) {
    /**
     * Calcular valor total
     */

    let total_value = 0;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let qty = item.qty || 0;
            let rate = item.basic_rate || 0;
            total_value += (qty * rate);
        });
    }

    return total_value;
}

function calculate_and_show_stock_totals(frm) {
    /**
     * Calcular e mostrar totais de stock
     */

    let totals = calculate_stock_totals(frm);

    frappe.msgprint({
        title: __('Informações de Movimentação'),
        message: `
            <table class="table table-bordered">
                <tr><td><strong>Quantidade Total:</strong></td><td>${totals.total_qty}</td></tr>
                <tr><td><strong>Valor Total:</strong></td><td>€${totals.total_value.toFixed(2)}</td></tr>
                <tr><td><strong>Nº Itens:</strong></td><td>${frm.doc.items ? frm.doc.items.length : 0}</td></tr>
                <tr><td><strong>Tipo Movimentação:</strong></td><td>${frm.doc.stock_entry_type || 'Não definido'}</td></tr>
            </table>
        `,
        indicator: 'blue'
    });
}

function configure_fields_by_type(frm) {
    /**
     * Configurar campos baseado no tipo de movimentação
     */

    let type = frm.doc.stock_entry_type;

    switch(type) {
        case 'Material Transfer':
            frm.toggle_reqd('from_warehouse', false);
            frm.toggle_reqd('to_warehouse', false);
            frappe.show_alert({
                message: __('Defina armazéns origem e destino nos itens'),
                indicator: 'blue'
            });
            break;

        case 'Material Issue':
            frm.toggle_reqd('from_warehouse', true);
            frm.toggle_reqd('to_warehouse', false);
            break;

        case 'Material Receipt':
            frm.toggle_reqd('from_warehouse', false);
            frm.toggle_reqd('to_warehouse', true);
            break;

        default:
            frm.toggle_reqd('from_warehouse', false);
            frm.toggle_reqd('to_warehouse', false);
    }
}

// ========== FUNÇÕES DE AÇÕES ==========

// generate_atcud_manually, check_series_status e
// show_series_status_dialog removidas (2026-08-30) - ver nota em
// add_custom_buttons. Stock Entry nao gera ATCUD nem tem serie fiscal
// desde 2026-08-22 (document_hooks.py::supported_doctypes).

function validate_all_warehouses(frm) {
    /**
     * Validar todos os armazéns
     */

    let warehouses_to_check = [];

    if (frm.doc.from_warehouse) {
        warehouses_to_check.push({name: frm.doc.from_warehouse, type: 'Origem'});
    }

    if (frm.doc.to_warehouse) {
        warehouses_to_check.push({name: frm.doc.to_warehouse, type: 'Destino'});
    }

    // Adicionar armazéns dos itens
    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            if (item.s_warehouse && !warehouses_to_check.find(w => w.name === item.s_warehouse)) {
                warehouses_to_check.push({name: item.s_warehouse, type: 'Item Origem'});
            }
            if (item.t_warehouse && !warehouses_to_check.find(w => w.name === item.t_warehouse)) {
                warehouses_to_check.push({name: item.t_warehouse, type: 'Item Destino'});
            }
        });
    }

    if (warehouses_to_check.length === 0) {
        frappe.msgprint(__('Nenhum armazém para validar'));
        return;
    }

    warehouses_to_check.forEach(function(wh) {
        validate_warehouse(frm, wh.name, wh.type);
    });
}

function check_available_stock(frm) {
    /**
     * Verificar stock disponível
     */

    if (!frm.doc.items || frm.doc.items.length === 0) {
        frappe.msgprint(__('Nenhum item para verificar'));
        return;
    }

    let items_to_check = frm.doc.items.filter(item =>
        item.s_warehouse && item.item_code
    );

    if (items_to_check.length === 0) {
        frappe.msgprint(__('Nenhum item com armazém origem para verificar'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Stock Disponível'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'stock_info'
            }
        ]
    });

    let html = `
        <div class="stock-availability-info">
            <h6>Verificação de Stock Disponível</h6>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Armazém</th>
                        <th>Necessário</th>
                        <th>Disponível</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="stock-table-body">
                    <tr><td colspan="5">Carregando...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.stock_info.$wrapper.html(html);
    dialog.show();

    // Carregar dados de stock
    let checks_completed = 0;
    let stock_data = [];

    items_to_check.forEach(function(item) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Bin',
                filters: {
                    item_code: item.item_code,
                    warehouse: item.s_warehouse
                },
                fieldname: 'actual_qty'
            },
            callback: function(r) {
                checks_completed++;

                let available_qty = r.message ? (r.message.actual_qty || 0) : 0;
                let status = available_qty >= item.qty ? 'Suficiente' : 'Insuficiente';
                let status_color = available_qty >= item.qty ? 'green' : 'red';

                stock_data.push({
                    item_code: item.item_code,
                    warehouse: item.s_warehouse,
                    required: item.qty,
                    available: available_qty,
                    status: status,
                    status_color: status_color
                });

                if (checks_completed === items_to_check.length) {
                    // Atualizar tabela
                    let table_html = '';
                    stock_data.forEach(function(data) {
                        table_html += `
                            <tr>
                                <td>${data.item_code}</td>
                                <td>${data.warehouse}</td>
                                <td>${data.required}</td>
                                <td>${data.available}</td>
                                <td style="color: ${data.status_color}"><strong>${data.status}</strong></td>
                            </tr>
                        `;
                    });

                    dialog.fields_dict.stock_info.$wrapper.find('#stock-table-body').html(table_html);
                }
            }
        });
    });
}

function print_portuguese_stock_entry(frm) {
    /**
     * Imprimir guia com formato português
     */

    // Sem format explicito - deixa o Frappe escolher o print format por
    // defeito (nao existe ainda nenhum print format dedicado para este doctype).
    frappe.set_route("print", frm.doc.doctype, frm.doc.name);
}

function analyze_stock_movement(frm) {
    /**
     * Analisar movimentação de stock
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Análise de Movimentação'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_info'
            }
        ]
    });

    let totals = calculate_stock_totals(frm);
    let movement_type = frm.doc.stock_entry_type || 'Não definido';

    let html = `
        <div class="movement-analysis">
            <h5>Análise da Movimentação: ${frm.doc.name}</h5>

            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Tipo:</strong></td><td>${movement_type}</td></tr>
                        <tr><td><strong>Data:</strong></td><td>${frappe.datetime.str_to_user(frm.doc.posting_date)}</td></tr>
                        <tr><td><strong>Empresa:</strong></td><td>${frm.doc.company}</td></tr>
                        <tr><td><strong>ATCUD:</strong></td><td>${frm.doc.atcud_code || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Totais</h6>
                    <table class="table table-bordered">
                        <tr><td><strong>Nº Itens:</strong></td><td>${frm.doc.items ? frm.doc.items.length : 0}</td></tr>
                        <tr><td><strong>Qtd Total:</strong></td><td>${totals.total_qty}</td></tr>
                        <tr><td><strong>Valor Total:</strong></td><td>€${totals.total_value.toFixed(2)}</td></tr>
                        <tr><td><strong>Valor Médio:</strong></td><td>€${totals.total_qty > 0 ? (totals.total_value / totals.total_qty).toFixed(2) : '0.00'}</td></tr>
                    </table>
                </div>
            </div>

            <h6>Detalhes dos Itens</h6>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qtd</th>
                        <th>Rate</th>
                        <th>Valor</th>
                        <th>Origem</th>
                        <th>Destino</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let value = (item.qty || 0) * (item.basic_rate || 0);
            html += `
                <tr>
                    <td>${item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td>€${(item.basic_rate || 0).toFixed(2)}</td>
                    <td>€${value.toFixed(2)}</td>
                    <td>${item.s_warehouse || frm.doc.from_warehouse || '-'}</td>
                    <td>${item.t_warehouse || frm.doc.to_warehouse || '-'}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
            </table>
        </div>
    `;

    dialog.fields_dict.analysis_info.$wrapper.html(html);
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
    let totals = calculate_stock_totals(frm);
    if (totals.total_qty > 0) {
        frm.doc.total_outgoing_value = totals.total_value;
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

function setup_mandatory_fields(frm) {
    /**
     * Configurar campos obrigatórios para compliance português
     */

    if (!is_portuguese_company(frm)) return;

    // ✅ CAMPOS OBRIGATÓRIOS PARA GUIAS DE MOVIMENTAÇÃO PORTUGUESAS
    frm.toggle_reqd('stock_entry_type', true);
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
        message: __('Guia de movimentação portuguesa submetida com sucesso'),
        indicator: 'green'
    });

    // ✅ ATUALIZAR STATUS DE COMPLIANCE
    if (frm.doc.atcud_code) {
        frm.dashboard.add_indicator(__('Conforme Legislação PT'), 'green');
    }

    // ✅ MOSTRAR INFORMAÇÕES DE MOVIMENTAÇÃO
    let total_qty = calculate_total_qty(frm);
    if (total_qty > 0) {
        frm.dashboard.add_indicator(__('Qtd Movimentada: {0}', [total_qty]), 'blue');
    }
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

frappe.ui.form.on('Stock Entry Detail', {
    qty: function(frm, cdt, cdn) {
        // ✅ RECALCULAR TOTAIS QUANDO QUANTIDADE MUDA
        setTimeout(() => {
            calculate_stock_totals(frm);
        }, 100);
    },

    basic_rate: function(frm, cdt, cdn) {
        // ✅ RECALCULAR TOTAIS QUANDO RATE MUDA
        setTimeout(() => {
            calculate_stock_totals(frm);
        }, 100);
    },

    s_warehouse: function(frm, cdt, cdn) {
        // ✅ VALIDAR ARMAZÉM ORIGEM
        let item = locals[cdt][cdn];
        if (item.s_warehouse) {
            validate_warehouse(frm, item.s_warehouse, 'origem do item');
        }
    },

    t_warehouse: function(frm, cdt, cdn) {
        // ✅ VALIDAR ARMAZÉM DESTINO
        let item = locals[cdt][cdn];
        if (item.t_warehouse) {
            validate_warehouse(frm, item.t_warehouse, 'destino do item');
        }
    }
});

// ========== INICIALIZAÇÃO ==========

frappe.ui.form.on('Stock Entry', {
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
            "Série portuguesa para guias de movimentação. Formato: GM2025EMPRESA.#### (GM=Guia de Movimentação)";
    }

    if (frm.fields_dict.atcud_code) {
        frm.fields_dict.atcud_code.df.description =
            "Código Único de Documento conforme Portaria 195/2020. Gerado automaticamente para guias de movimentação.";
    }

    if (frm.fields_dict.stock_entry_type) {
        frm.fields_dict.stock_entry_type.df.description =
            "Tipo de movimentação conforme legislação portuguesa";
    }

    if (frm.fields_dict.from_warehouse) {
        frm.fields_dict.from_warehouse.df.description =
            "Armazém de origem para movimentação de stock";
    }

    if (frm.fields_dict.to_warehouse) {
        frm.fields_dict.to_warehouse.df.description =
            "Armazém de destino para movimentação de stock";
    }
}

function setup_keyboard_shortcuts(frm) {
    /**
     * Configurar atalhos de teclado para Portugal Compliance
     */

    // Atalho Ctrl+G ("Gerar ATCUD") removido junto com o botão e a
    // função - ver nota em add_custom_buttons.

    // ✅ CTRL+S para verificar stock
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+s',
        action: () => {
            if (frm.doc.from_warehouse && frm.doc.items) {
                check_available_stock(frm);
            }
        },
        description: __('Verificar Stock'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+T para calcular totais
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+t',
        action: () => {
            if (frm.doc.items && frm.doc.items.length > 0) {
                calculate_and_show_stock_totals(frm);
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
                print_portuguese_stock_entry(frm);
            }
        },
        description: __('Imprimir Guia Portuguesa'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+A para analisar movimentação
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+shift+a',
        action: () => {
            if (frm.doc.docstatus === 1) {
                analyze_stock_movement(frm);
            }
        },
        description: __('Analisar Movimentação'),
        ignore_inputs: true,
        page: frm.page
    });

    // ✅ CTRL+W para validar armazéns
    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+w',
        action: () => {
            if (frm.doc.from_warehouse || frm.doc.to_warehouse) {
                validate_all_warehouses(frm);
            }
        },
        description: __('Validar Armazéns'),
        ignore_inputs: true,
        page: frm.page
    });
}

// ========== FUNÇÕES DE VALIDAÇÃO AVANÇADA ==========

function validate_stock_entry_compliance(frm) {
    /**
     * ✅ NOVA: Validação completa de compliance para movimentação de stock
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

    // ✅ VERIFICAR TIPO DE MOVIMENTAÇÃO
    if (!frm.doc.stock_entry_type) {
        compliance_issues.push({
            type: 'error',
            message: 'Tipo de movimentação é obrigatório'
        });
    }

    // ✅ VERIFICAR ITENS
    if (!frm.doc.items || frm.doc.items.length === 0) {
        compliance_issues.push({
            type: 'error',
            message: 'Pelo menos um item é obrigatório'
        });
    }

    // ✅ VERIFICAR ARMAZÉNS BASEADO NO TIPO
    if (frm.doc.stock_entry_type) {
        let warehouse_issues = validate_warehouses_compliance(frm);
        compliance_issues = compliance_issues.concat(warehouse_issues);
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

function validate_warehouses_compliance(frm) {
    /**
     * ✅ NOVA: Validar armazéns para compliance
     */

    let issues = [];
    let type = frm.doc.stock_entry_type;

    switch(type) {
        case 'Material Transfer':
            if (!frm.doc.from_warehouse && !frm.doc.to_warehouse) {
                // Verificar se todos os itens têm armazéns definidos
                let items_without_warehouses = frm.doc.items.filter(item =>
                    !item.s_warehouse || !item.t_warehouse
                );
                if (items_without_warehouses.length > 0) {
                    issues.push({
                        type: 'error',
                        message: 'Para transferência, defina armazéns origem e destino nos itens'
                    });
                }
            }
            break;

        case 'Material Issue':
            if (!frm.doc.from_warehouse) {
                let items_without_source = frm.doc.items.filter(item => !item.s_warehouse);
                if (items_without_source.length > 0) {
                    issues.push({
                        type: 'error',
                        message: 'Para saída, defina armazém de origem'
                    });
                }
            }
            break;

        case 'Material Receipt':
            if (!frm.doc.to_warehouse) {
                let items_without_target = frm.doc.items.filter(item => !item.t_warehouse);
                if (items_without_target.length > 0) {
                    issues.push({
                        type: 'error',
                        message: 'Para entrada, defina armazém de destino'
                    });
                }
            }
            break;
    }

    return issues;
}

function show_compliance_report(frm) {
    /**
     * ✅ NOVA: Mostrar relatório completo de compliance
     */

    let issues = validate_stock_entry_compliance(frm);
    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let html = `
        <div class="compliance-report">
            <h5>Relatório de Compliance - Guia de Movimentação</h5>

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

function generate_stock_movement_summary_report(frm) {
    /**
     * ✅ NOVA: Gerar relatório resumo da movimentação
     */

    let totals = calculate_stock_totals(frm);

    let dialog = new frappe.ui.Dialog({
        title: __('Relatório Resumo da Movimentação'),
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
        <div class="stock-movement-summary-report">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>Relatório de Movimentação de Stock</h3>
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
                    <h5>Dados da Movimentação</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Tipo:</strong></td><td>${frm.doc.stock_entry_type || 'N/A'}</td></tr>
                        <tr><td><strong>Armazém Origem:</strong></td><td>${frm.doc.from_warehouse || 'N/A'}</td></tr>
                        <tr><td><strong>Armazém Destino:</strong></td><td>${frm.doc.to_warehouse || 'N/A'}</td></tr>
                    </table>
                </div>
            </div>

            <h5>Resumo Quantitativo</h5>
            <table class="table table-bordered">
                <tr><td><strong>Nº Itens:</strong></td><td>${frm.doc.items ? frm.doc.items.length : 0}</td></tr>
                <tr><td><strong>Quantidade Total:</strong></td><td>${totals.total_qty}</td></tr>
                <tr style="font-weight: bold; background-color: #f8f9fa;"><td><strong>Valor Total:</strong></td><td>€${totals.total_value.toFixed(2)}</td></tr>
            </table>

            <h5>Itens Movimentados</h5>
            <table class="table table-striped">
                <thead>
                    <tr><th>Item</th><th>Qtd</th><th>Rate</th><th>Valor</th><th>Origem</th><th>Destino</th></tr>
                </thead>
                <tbody>
    `;

    if (frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            let value = (item.qty || 0) * (item.basic_rate || 0);
            html += `
                <tr>
                    <td>${item.item_code}</td>
                    <td>${item.qty || 0}</td>
                    <td>€${(item.basic_rate || 0).toFixed(2)}</td>
                    <td>€${value.toFixed(2)}</td>
                    <td>${item.s_warehouse || frm.doc.from_warehouse || '-'}</td>
                    <td>${item.t_warehouse || frm.doc.to_warehouse || '-'}</td>
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
                <p><strong>Tipo Documento:</strong> Guia de Movimentação (GM)</p>
                <p><strong>Observações:</strong> ${frm.doc.remarks || 'Nenhuma'}</p>
            </div>
        </div>
    `;

    dialog.fields_dict.report_content.$wrapper.html(html);
    dialog.show();
}

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('Portugal Compliance Stock Entry JS loaded - Version 2.0.0');
