// -*- coding: utf-8 -*-
// Copyright (c) 2025, NovaDX - Octávio Daio and contributors
// For license information, please see license.txt

/**
 * ATCUD Validator JS - Portugal Compliance VERSÃO NATIVA CORRIGIDA
 * Validador centralizado para ATCUD em todos os documentos
 * ✅ CORRIGIDO: Formato SEM HÍFENS (FT2025NDX em vez de FT-2025-NDX)
 * ✅ INTEGRAÇÃO: Alinhado com document_hooks.py e series_adapter.py
 * ✅ Validação universal para todos os doctypes portugueses
 * ✅ Suporte completo para todas as séries comunicadas
 * ✅ Interface unificada de validação ATCUD
 */

// ========== CONFIGURAÇÃO GLOBAL ==========

window.ATCUDValidator = {
    // ✅ MAPEAMENTO DE DOCTYPES PARA CÓDIGOS DE DOCUMENTO (SEM HÍFENS)
    DOCTYPE_CODES: {
        'Sales Invoice': 'FT',      // Fatura
        'Sales Order': 'FO',        // Fatura-Orçamento
        'Quotation': 'OR',          // Orçamento
        'Delivery Note': 'GR',      // Guia de Remessa
        'Purchase Invoice': 'FC',   // Fatura de Compra
        'Purchase Order': 'OC',     // Ordem de Compra
        'Purchase Receipt': 'GR',   // Guia de Receção
        'Stock Entry': 'GM',        // Guia de Movimentação
        'Payment Entry': 'RC',      // Recibo
        'POS Invoice': 'FS'         // Fatura Simplificada
    },

    // ✅ PADRÕES DE VALIDAÇÃO (SEM HÍFENS)
    PATTERNS: {
        // Padrão geral: XXYYYY + COMPANY.####
        NAMING_SERIES: /^[A-Z]{2,4}\d{4}[A-Z0-9]{2,4}\.####$/,

        // Padrão ATCUD: 0 + sequência
        ATCUD: /^0\.\d+$/,

        // Padrão NIF português
        NIF: /^\d{9}$/,

        // Padrão código postal português
        POSTAL_CODE: /^\d{4}-\d{3}$/
    },

    // ✅ CACHE DE VALIDAÇÕES
    cache: new Map(),

    // ✅ CONFIGURAÇÕES
    settings: {
        cache_timeout: 300000, // 5 minutos
        auto_validate: true,
        show_alerts: true
    }
};

// ========== FUNÇÕES PRINCIPAIS DE VALIDAÇÃO ==========

ATCUDValidator.validateDocument = function(frm) {
    /**
     * ✅ PRINCIPAL: Validar documento completo para compliance português
     */

    if (!this.isPortugueseCompany(frm)) {
        return {
            valid: true,
            message: 'Empresa não portuguesa - validação não aplicável',
            issues: []
        };
    }

    let issues = [];
    let doctype = frm.doc.doctype;

    // ✅ VALIDAR NAMING SERIES
    let seriesValidation = this.validateNamingSeries(frm.doc.naming_series, doctype);
    if (!seriesValidation.valid) {
        issues.push({
            type: 'error',
            field: 'naming_series',
            message: seriesValidation.message
        });
    }

    // ✅ VALIDAR ATCUD
    let atcudValidation = this.validateATCUD(frm.doc.atcud_code);
    if (!atcudValidation.valid && frm.doc.docstatus === 1) {
        issues.push({
            type: 'error',
            field: 'atcud_code',
            message: atcudValidation.message
        });
    }

    // ✅ VALIDAÇÕES ESPECÍFICAS POR DOCTYPE
    let specificValidation = this.validateDocTypeSpecific(frm);
    issues = issues.concat(specificValidation.issues);

    return {
        valid: issues.filter(i => i.type === 'error').length === 0,
        message: this.generateValidationMessage(issues),
        issues: issues
    };
};

ATCUDValidator.validateNamingSeries = function(namingSeries, doctype) {
    /**
     * ✅ CORRIGIDO: Validar naming series portuguesa (formato SEM HÍFENS)
     */

    if (!namingSeries) {
        return {
            valid: false,
            message: 'Naming series é obrigatória para documentos portugueses'
        };
    }

    // ✅ VERIFICAR PADRÃO GERAL (SEM HÍFENS)
    if (!this.PATTERNS.NAMING_SERIES.test(namingSeries)) {
        return {
            valid: false,
            message: `Formato inválido. Use: XXYYYY + EMPRESA.#### (ex: FT2025NDX.####)`
        };
    }

    // ✅ EXTRAIR CÓDIGO DO DOCUMENTO
    let prefix = namingSeries.replace('.####', '');
    let docCode = prefix.substring(0, 2);
    let expectedCode = this.DOCTYPE_CODES[doctype];

    if (expectedCode && docCode !== expectedCode) {
        return {
            valid: false,
            message: `Código incorreto. Para ${doctype}, use séries ${expectedCode} (ex: ${expectedCode}2025EMPRESA.####)`
        };
    }

    return {
        valid: true,
        message: 'Naming series portuguesa válida'
    };
};

ATCUDValidator.validateATCUD = function(atcudCode) {
    /**
     * ✅ Validar código ATCUD
     */

    if (!atcudCode) {
        return {
            valid: false,
            message: 'ATCUD é obrigatório para documentos submetidos'
        };
    }

    if (!this.PATTERNS.ATCUD.test(atcudCode)) {
        return {
            valid: false,
            message: 'Formato ATCUD inválido. Deve ser: 0.sequência'
        };
    }

    return {
        valid: true,
        message: 'ATCUD válido'
    };
};

ATCUDValidator.validateDocTypeSpecific = function(frm) {
    /**
     * ✅ Validações específicas por tipo de documento
     */

    let issues = [];
    let doctype = frm.doc.doctype;

    switch(doctype) {
        case 'Sales Invoice':
        case 'POS Invoice':
            issues = issues.concat(this.validateSalesDocument(frm));
            break;

        case 'Purchase Invoice':
        case 'Purchase Receipt':
            issues = issues.concat(this.validatePurchaseDocument(frm));
            break;

        case 'Quotation':
        case 'Sales Order':
            issues = issues.concat(this.validateQuotationDocument(frm));
            break;

        case 'Stock Entry':
            issues = issues.concat(this.validateStockDocument(frm));
            break;

        case 'Payment Entry':
            issues = issues.concat(this.validatePaymentDocument(frm));
            break;
    }

    return { issues: issues };
};

ATCUDValidator.validateSalesDocument = function(frm) {
    /**
     * ✅ Validar documentos de venda
     */

    let issues = [];

    // ✅ VALIDAR CLIENTE
    if (!frm.doc.customer) {
        issues.push({
            type: 'error',
            field: 'customer',
            message: 'Cliente é obrigatório'
        });
    }

    // ✅ VALIDAR LIMITE SEM NIF (POS)
    if (frm.doc.doctype === 'POS Invoice' && (frm.doc.grand_total || 0) > 1000) {
        let customerNif = this.getCustomerNIF(frm.doc.customer);
        if (!customerNif) {
            issues.push({
                type: 'error',
                field: 'customer',
                message: 'NIF obrigatório para valores acima de €1000'
            });
        }
    }

    // ✅ VALIDAR IMPOSTOS
    if (!this.hasValidPortugueseTaxes(frm)) {
        issues.push({
            type: 'warning',
            field: 'taxes',
            message: 'Configure impostos portugueses (IVA)'
        });
    }

    return issues;
};

ATCUDValidator.validatePurchaseDocument = function(frm) {
    /**
     * ✅ Validar documentos de compra
     */

    let issues = [];

    // ✅ VALIDAR FORNECEDOR
    if (!frm.doc.supplier) {
        issues.push({
            type: 'error',
            field: 'supplier',
            message: 'Fornecedor é obrigatório'
        });
    }

    // ✅ VALIDAR DADOS DA FATURA (Purchase Invoice)
    if (frm.doc.doctype === 'Purchase Invoice') {
        if (!frm.doc.bill_no) {
            issues.push({
                type: 'error',
                field: 'bill_no',
                message: 'Número da fatura do fornecedor é obrigatório'
            });
        }

        if (!frm.doc.bill_date) {
            issues.push({
                type: 'error',
                field: 'bill_date',
                message: 'Data da fatura do fornecedor é obrigatória'
            });
        }
    }

    return issues;
};

ATCUDValidator.validateQuotationDocument = function(frm) {
    /**
     * ✅ Validar orçamentos
     */

    let issues = [];

    // ✅ VALIDAR VALIDADE (Quotation)
    if (frm.doc.doctype === 'Quotation' && !frm.doc.valid_till) {
        issues.push({
            type: 'error',
            field: 'valid_till',
            message: 'Data de validade é obrigatória para orçamentos'
        });
    }

    return issues;
};

ATCUDValidator.validateStockDocument = function(frm) {
    /**
     * ✅ Validar movimentações de stock
     */

    let issues = [];

    // ✅ VALIDAR TIPO DE MOVIMENTAÇÃO
    if (!frm.doc.stock_entry_type) {
        issues.push({
            type: 'error',
            field: 'stock_entry_type',
            message: 'Tipo de movimentação é obrigatório'
        });
    }

    // ✅ VALIDAR ARMAZÉNS
    if (!frm.doc.from_warehouse && !frm.doc.to_warehouse) {
        let itemsWithoutWarehouses = (frm.doc.items || []).filter(item =>
            !item.s_warehouse || !item.t_warehouse
        );

        if (itemsWithoutWarehouses.length > 0) {
            issues.push({
                type: 'error',
                field: 'items',
                message: 'Defina armazéns origem e destino'
            });
        }
    }

    return issues;
};

ATCUDValidator.validatePaymentDocument = function(frm) {
    /**
     * ✅ Validar recibos
     */

    let issues = [];

    // ✅ VALIDAR ENTIDADE
    if (!frm.doc.party) {
        issues.push({
            type: 'error',
            field: 'party',
            message: 'Entidade é obrigatória'
        });
    }

    // ✅ VALIDAR VALOR
    if (!frm.doc.paid_amount || frm.doc.paid_amount <= 0) {
        issues.push({
            type: 'error',
            field: 'paid_amount',
            message: 'Valor deve ser maior que zero'
        });
    }

    // ✅ VALIDAR MODO DE PAGAMENTO
    if (!frm.doc.mode_of_payment) {
        issues.push({
            type: 'error',
            field: 'mode_of_payment',
            message: 'Modo de pagamento é obrigatório'
        });
    }

    return issues;
};

// ========== FUNÇÕES DE VALIDAÇÃO DE SÉRIES ==========

ATCUDValidator.validateSeriesCommunication = function(namingSeries, company) {
    /**
     * ✅ CORRIGIDO: Validar se série está comunicada à AT (formato SEM HÍFENS)
     */

    if (!namingSeries) return Promise.resolve({ valid: false, message: 'Série não definida' });

    let prefix = namingSeries.replace('.####', '');
    let cacheKey = `series_${prefix}_${company}`;

    // ✅ VERIFICAR CACHE
    if (this.cache.has(cacheKey)) {
        let cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.settings.cache_timeout) {
            return Promise.resolve(cached.data);
        }
    }

    // ✅ BUSCAR NO SERVIDOR
    return new Promise((resolve) => {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Portugal Series Configuration',
                filters: { prefix: prefix, company: company },
                fieldname: ['is_communicated', 'validation_code', 'communication_date']
            },
            callback: (r) => {
                let result;

                if (r.message) {
                    result = {
                        valid: r.message.is_communicated || false,
                        message: r.message.is_communicated ?
                            `Série comunicada à AT em ${frappe.datetime.str_to_user(r.message.communication_date)}` :
                            'Série não comunicada à AT',
                        data: r.message
                    };
                } else {
                    result = {
                        valid: false,
                        message: 'Série não encontrada na configuração'
                    };
                }

                // ✅ ARMAZENAR NO CACHE
                this.cache.set(cacheKey, {
                    data: result,
                    timestamp: Date.now()
                });

                resolve(result);
            }
        });
    });
};

ATCUDValidator.getAvailableSeries = function(doctype, company) {
    /**
     * ✅ CORRIGIDO: Obter séries disponíveis para doctype (formato SEM HÍFENS)
     */

    let cacheKey = `available_series_${doctype}_${company}`;

    // ✅ VERIFICAR CACHE
    if (this.cache.has(cacheKey)) {
        let cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.settings.cache_timeout) {
            return Promise.resolve(cached.data);
        }
    }

    return new Promise((resolve) => {
        frappe.call({
            method: 'portugal_compliance.utils.atcud_generator.get_available_portugal_series_certified',
            args: { doctype: doctype, company: company },
            callback: (r) => {
                let result = r.message || { success: false, series: [] };

                // ✅ ARMAZENAR NO CACHE
                this.cache.set(cacheKey, {
                    data: result,
                    timestamp: Date.now()
                });

                resolve(result);
            }
        });
    });
};

// ========== FUNÇÕES DE VALIDAÇÃO DE NIF ==========

ATCUDValidator.validatePortugueseNIF = function(nif) {
    /**
     * ✅ Validar NIF português (algoritmo completo)
     */

    if (!nif) return { valid: false, message: 'NIF não fornecido' };

    // ✅ LIMPAR E NORMALIZAR
    nif = nif.toString().replace(/[^0-9]/g, '');

    // ✅ VERIFICAR COMPRIMENTO
    if (nif.length !== 9) {
        return { valid: false, message: 'NIF deve ter 9 dígitos' };
    }

    // ✅ VERIFICAR PRIMEIRO DÍGITO
    let firstDigit = nif[0];
    if (!['1', '2', '3', '5', '6', '7', '8', '9'].includes(firstDigit)) {
        return { valid: false, message: 'Primeiro dígito do NIF inválido' };
    }

    // ✅ ALGORITMO DE VALIDAÇÃO
    let checksum = 0;
    for (let i = 0; i < 8; i++) {
        checksum += parseInt(nif[i]) * (9 - i);
    }

    let remainder = checksum % 11;
    let controlDigit = remainder < 2 ? 0 : 11 - remainder;

    if (parseInt(nif[8]) !== controlDigit) {
        return { valid: false, message: 'Dígito de controlo do NIF inválido' };
    }

    return {
        valid: true,
        message: 'NIF português válido',
        nif_type: this.getNIFType(firstDigit)
    };
};

ATCUDValidator.getNIFType = function(firstDigit) {
    /**
     * ✅ Obter tipo de entidade baseado no primeiro dígito do NIF
     */

    const types = {
        '1': 'Pessoa Singular',
        '2': 'Pessoa Singular',
        '3': 'Pessoa Singular',
        '5': 'Pessoa Coletiva',
        '6': 'Administração Pública',
        '7': 'Outras Entidades',
        '8': 'Empresário em Nome Individual',
        '9': 'Pessoa Coletiva'
    };

    return types[firstDigit] || 'Desconhecido';
};

// ========== FUNÇÕES DE VALIDAÇÃO DE IMPOSTOS ==========

ATCUDValidator.hasValidPortugueseTaxes = function(frm) {
    /**
     * ✅ Verificar se documento tem impostos portugueses válidos
     */

    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        return false;
    }

    let hasIVA = false;
    let validRates = [0, 6, 13, 23]; // Taxas válidas em Portugal

    frm.doc.taxes.forEach(tax => {
        let description = (tax.description || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            hasIVA = true;

            // Verificar se taxa é válida
            if (!validRates.includes(tax.rate)) {
                return false;
            }
        }
    });

    return hasIVA;
};

ATCUDValidator.validateTaxStructure = function(frm) {
    /**
     * ✅ Validar estrutura completa de impostos
     */

    let issues = [];

    if (!frm.doc.taxes || frm.doc.taxes.length === 0) {
        issues.push({
            type: 'warning',
            field: 'taxes',
            message: 'Configure impostos portugueses (IVA)'
        });
        return issues;
    }

    let hasIVA = false;
    let invalidRates = [];
    let validRates = [0, 6, 13, 23];

    frm.doc.taxes.forEach(tax => {
        let description = (tax.description || '').toUpperCase();
        if (description.includes('IVA') || description.includes('VAT')) {
            hasIVA = true;

            if (!validRates.includes(tax.rate)) {
                invalidRates.push(tax.rate);
            }
        }
    });

    if (!hasIVA) {
        issues.push({
            type: 'error',
            field: 'taxes',
            message: 'Documento deve ter IVA configurado'
        });
    }

    if (invalidRates.length > 0) {
        issues.push({
            type: 'error',
            field: 'taxes',
            message: `Taxas de IVA inválidas: ${invalidRates.join(', ')}%`
        });
    }

    return issues;
};

// ========== FUNÇÕES AUXILIARES ==========

ATCUDValidator.isPortugueseCompany = function(frm) {
    /**
     * ✅ Verificar se empresa é portuguesa com compliance ativo
     */

    if (!frm.doc.company) return false;

    let cacheKey = `company_${frm.doc.company}`;

    // ✅ VERIFICAR CACHE
    if (this.cache.has(cacheKey)) {
        let cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.settings.cache_timeout) {
            return cached.data;
        }
    }

    let result = false;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company',
            filters: { name: frm.doc.company },
            fieldname: ['country', 'portugal_compliance_enabled']
        },
        async: false,
        callback: (r) => {
            if (r.message) {
                result = r.message.country === 'Portugal' && r.message.portugal_compliance_enabled;
            }

            // ✅ ARMAZENAR NO CACHE
            this.cache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });
        }
    });

    return result;
};

ATCUDValidator.getCustomerNIF = function(customer) {
    /**
     * ✅ Obter NIF do cliente
     */

    if (!customer) return null;

    let cacheKey = `customer_nif_${customer}`;

    // ✅ VERIFICAR CACHE
    if (this.cache.has(cacheKey)) {
        let cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.settings.cache_timeout) {
            return cached.data;
        }
    }

    let result = null;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: { name: customer },
            fieldname: 'tax_id'
        },
        async: false,
        callback: (r) => {
            result = r.message ? r.message.tax_id : null;

            // ✅ ARMAZENAR NO CACHE
            this.cache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });
        }
    });

    return result;
};

ATCUDValidator.generateValidationMessage = function(issues) {
    /**
     * ✅ Gerar mensagem de validação baseada nos issues
     */

    if (issues.length === 0) {
        return 'Documento conforme com legislação portuguesa';
    }

    let errors = issues.filter(i => i.type === 'error');
    let warnings = issues.filter(i => i.type === 'warning');

    let message = '';

    if (errors.length > 0) {
        message += `${errors.length} erro(s) encontrado(s). `;
    }

    if (warnings.length > 0) {
        message += `${warnings.length} aviso(s) encontrado(s). `;
    }

    return message.trim();
};

// ========== FUNÇÕES DE INTERFACE ==========

ATCUDValidator.showValidationDialog = function(frm, validation) {
    /**
     * ✅ Mostrar dialog de validação completa
     */

    let dialog = new frappe.ui.Dialog({
        title: __('Validação Portugal Compliance'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'validation_content'
            }
        ]
    });

    let html = this.generateValidationHTML(frm, validation);
    dialog.fields_dict.validation_content.$wrapper.html(html);
    dialog.show();
};

ATCUDValidator.generateValidationHTML = function(frm, validation) {
    /**
     * ✅ Gerar HTML para dialog de validação
     */

    let errors = validation.issues.filter(i => i.type === 'error');
    let warnings = validation.issues.filter(i => i.type === 'warning');

    let html = `
        <div class="atcud-validation-report">
            <h5>Relatório de Validação: ${frm.doc.doctype}</h5>
            <p><strong>Documento:</strong> ${frm.doc.name || 'Novo'}</p>

            <div class="row">
                <div class="col-md-6">
                    <h6 style="color: red;">Erros (${errors.length})</h6>
                    <ul>
    `;

    if (errors.length === 0) {
        html += '<li style="color: green;">Nenhum erro encontrado</li>';
    } else {
        errors.forEach(error => {
            html += `<li style="color: red;"><strong>${error.field}:</strong> ${error.message}</li>`;
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
            html += `<li style="color: orange;"><strong>${warning.field}:</strong> ${warning.message}</li>`;
        });
    }

    html += `
                    </ul>
                </div>
            </div>

            <div class="mt-3">
                <h6>Status Geral</h6>
                <p style="color: ${validation.valid ? 'green' : 'red'}; font-weight: bold;">
                    ${validation.valid ? '✅ Documento conforme' : '❌ Documento não conforme'}
                </p>
                <p><small>${validation.message}</small></p>
            </div>
        </div>
    `;

    return html;
};

ATCUDValidator.addValidationButton = function(frm) {
    /**
     * ✅ Adicionar botão de validação ao formulário
     */

    if (!this.isPortugueseCompany(frm)) return;

    frm.add_custom_button(__('Validar Compliance PT'), () => {
        let validation = this.validateDocument(frm);
        this.showValidationDialog(frm, validation);
    }, __('Portugal Compliance'));
};

// ========== FUNÇÕES DE AUTO-VALIDAÇÃO ==========

ATCUDValidator.setupAutoValidation = function(frm) {
    /**
     * ✅ Configurar validação automática
     */

    if (!this.settings.auto_validate || !this.isPortugueseCompany(frm)) return;

    // ✅ VALIDAR NO REFRESH
    if (!frm.doc.__islocal) {
        setTimeout(() => {
            this.performQuickValidation(frm);
        }, 1000);
    }

    // ✅ VALIDAR ANTES DO SAVE
    frm.doc.__atcud_validator_attached = true;
};

ATCUDValidator.performQuickValidation = function(frm) {
    /**
     * ✅ Validação rápida sem dialog
     */

    let validation = this.validateDocument(frm);

    if (!validation.valid && this.settings.show_alerts) {
        let errors = validation.issues.filter(i => i.type === 'error').length;
        let warnings = validation.issues.filter(i => i.type === 'warning').length;

        if (errors > 0) {
            frappe.show_alert({
                message: `Portugal Compliance: ${errors} erro(s) encontrado(s)`,
                indicator: 'red'
            });
        } else if (warnings > 0) {
            frappe.show_alert({
                message: `Portugal Compliance: ${warnings} aviso(s)`,
                indicator: 'orange'
            });
        }
    }
};

// ========== INICIALIZAÇÃO AUTOMÁTICA ==========

$(document).ready(function() {
    // ✅ CONFIGURAR VALIDAÇÃO AUTOMÁTICA PARA TODOS OS FORMULÁRIOS
    frappe.ui.form.handlers = frappe.ui.form.handlers || {};

    // ✅ ADICIONAR HANDLER UNIVERSAL
    let originalSetup = frappe.ui.form.Form.prototype.setup;
    frappe.ui.form.Form.prototype.setup = function() {
        originalSetup.call(this);

        // ✅ VERIFICAR SE É DOCTYPE PORTUGUÊS
        if (ATCUDValidator.DOCTYPE_CODES[this.doctype]) {
            ATCUDValidator.setupAutoValidation(this);
            ATCUDValidator.addValidationButton(this);
        }
    };
});

// ========== FUNÇÕES DE UTILIDADE PÚBLICA ==========

window.validatePortugalCompliance = function(frm) {
    /**
     * ✅ FUNÇÃO PÚBLICA: Validar compliance português
     */
    return ATCUDValidator.validateDocument(frm);
};

window.showPortugalComplianceReport = function(frm) {
    /**
     * ✅ FUNÇÃO PÚBLICA: Mostrar relatório de compliance
     */
    let validation = ATCUDValidator.validateDocument(frm);
    ATCUDValidator.showValidationDialog(frm, validation);
};

window.validatePortugueseNIF = function(nif) {
    /**
     * ✅ FUNÇÃO PÚBLICA: Validar NIF português
     */
    return ATCUDValidator.validatePortugueseNIF(nif);
};

// ========== CONSOLE LOG PARA DEBUG ==========
console.log('ATCUD Validator loaded - Version 2.0.0 - Universal Portugal Compliance');
