# Manual Técnico: Estrutura de Ficheiros e Arquitetura

**Versão:** 1.1.0

> Inventário técnico completo do módulo `portugal_compliance` (Frappe/ERPNext). Útil para
> programadores que precisem de manter, estender ou auditar a solução. Cada entrada foi
> confirmada por leitura direta do código, não por convenção assumida.

---

## 1. Visão Geral da Estrutura

```
portugal_compliance/
├── portugal_compliance/
│   ├── doctype/                # DocTypes do módulo (schema JSON + controller .py/.js)
│   ├── page/                   # Páginas customizadas (Dashboard AT)
│   ├── dashboard_chart/        # Gráficos nativos do Frappe (se existentes)
│   └── report/                 # Relatórios nativos do Frappe
├── utils/                      # Lógica de negócio - o "motor" do módulo
├── api/                        # Endpoints whitelisted (superfície pública para UI/integrações)
├── dashboards/                 # Lógica do Dashboard AT (Page customizada)
├── setup/                      # Provisionamento (taxonomia fiscal, contas SNC)
├── overrides/                  # Overrides pontuais de comportamento nativo do ERPNext
├── regional/                   # Configuração regional nativa do Frappe (`erpnext.regional`)
├── tasks/                      # Tarefas agendadas (all/hourly/daily/weekly/monthly/yearly)
├── templates/
│   ├── saft_t/                 # Templates Jinja2 do XML SAF-T
│   └── print_formats/          # ⚠️ Órfãos — ver secção 5
├── patches/                    # Patches de migração de schema (bench migrate)
├── migrations/                 # Scripts de migração de dados pontuais
├── public/js/                  # JavaScript client-side (Form Scripts)
├── fixtures/                   # Dados exportados via `bench export-fixtures`
├── wsdl/                       # Contratos SOAP oficiais da AT (bundled)
├── xsd/                        # Schema oficial do SAF-T (bundled)
├── exceptions/                 # Classes de exceção customizadas
├── hooks.py                    # Fonte de verdade: doc_events, scheduler_events, fixtures
└── config/                     # Configuração de módulo do Frappe Desk
```

---

## 2. Inventário Detalhado

### 2.1. `utils/` — Lógica de Negócio

| Ficheiro | Responsabilidade |
| :--- | :--- |
| `document_hooks.py` | **Crítico.** Todos os hooks de ciclo de vida de documento: bloqueio de eliminação/edição, geração de ATCUD, validação de compliance, registo de impressão. `FISCAL_IMMUTABLE_DOCTYPES` está aqui. |
| `signature.py` | Motor de assinatura RSA-SHA1: `sign_document()`, `verify_signature_chain()`, `export_signing_public_key()`, `DOCUMENT_SIGNING_SPEC`. |
| `atcud_generator.py` | `ATCUDGenerator` — orquestra sequência + assinatura + persistência em `ATCUD Log`. Contém também um segundo gerador de QR Code interno (ver Nota Metodológica, secção 5). |
| `tax_breakdown.py` | Resolução partilhada de código de taxa (NOR/INT/RED/ISE) e praça fiscal (PT/PT-AC/PT-MA) por linha — fonte única usada pelo QR Code, SAF-T e validação de isenção. |
| `jinja_methods.py` | Funções expostas aos templates Jinja/Print Formats: `get_qr_code_data()`, `get_atcud_code()`, `get_customer_nif()`, `get_document_at_code()`, etc. |
| `at_webservice.py` | Cliente SOAP do webservice de Séries (`registarSerie`, `consultarSeries`, `finalizarSerie`, `anularSerie`) + funções de baixo nível partilhadas (mTLS, WS-Security). |
| `at_invoice_webservice.py` | Cliente SOAP de Faturas em tempo real (`RegisterInvoice`, `ChangeInvoiceStatus`). |
| `at_transport_webservice.py` | Cliente SOAP de Documentos de Transporte (`envioDocumentoTransporte`). |
| `saft_generator.py` | `SAFTGenerator` — coleta de dados, render Jinja, hash do ficheiro, contagem de registos. |
| `series_adapter.py`, `series_manager.py`, `naming_series_customizer.py`, `compliance_hooks.py` | ⚠️ **Código morto** — não referenciados em `hooks.py` (ver secção 5). |

### 2.2. `portugal_compliance/doctype/` — DocTypes do Módulo

| DocType | Tipo | Ficheiros relevantes |
| :--- | :--- | :--- |
| `portugal_auth_settings` | Single | `.json` (schema), `.py` (controller vazio/mínimo) |
| `portugal_series_configuration` | Documento | `.json`, `.py` (validação de prefixo, `get_document_prefix`), `.js` (UI: botões Comunicar/Finalizar/Anular, dashboard de status) |
| `atcud_log` | Documento (log) | `.json`, `.py` (`persist_pending_atcud_log`, retry de gravação) |
| `saf_t_export_log` | Documento (log) | `.json`, `.py` (`validate_xml_content`, `submit_to_at`) |
| `portugal_invoice_communication_log` | Documento (log) | `.json` |
| `portugal_document_print_log` | Documento (log) | `.json` |
| `at_tax_exemption` | Documento (referência) | `.json` — carregado como fixture, taxonomia M01-M99 |

Ver [manual_tecnico_schema_dados.md](manual_tecnico_schema_dados.md) para o schema completo
campo a campo de cada um.

### 2.3. `api/` — Endpoints Whitelisted

| Ficheiro | Superfície |
| :--- | :--- |
| `atcud_api.py` | `regenerate_atcud`, `bulk_generate_atcud`, `validate_atcud`, estatísticas de ATCUD. Allowlist de doctypes suportados alinhada com `FISCAL_IMMUTABLE_DOCTYPES`. |
| `series_api.py` | `get_available_document_types`, `test_series_generation`, estatísticas de séries. |
| `company_api.py` | Ativação de compliance português numa empresa; séries de devolução (`RETURN_DOCUMENT_SERIES`). |
| `saft_api.py` | `generate_saft_export`, `download_saft_file`, listagem de exports. |

### 2.4. `page/compliance_dashboard/` — Dashboard AT

Página customizada do Frappe Desk (não um Workspace nem um Dashboard Chart nativo).
`compliance_dashboard.js` renderiza os dados devolvidos por
[dashboards/company.py](portugal_compliance/dashboards/company.py) (`CompanyDashboard`) —
estatísticas, alertas de expiração de certificado, tabela "Séries por tipo de documento"
(agrupada por código AT, não por DocType do Frappe — ver
[manual_funcionalidades_compliance.md](manual_funcionalidades_compliance.md)).

### 2.5. `setup/` — Provisionamento

| Ficheiro | Função |
| :--- | :--- |
| `tax_setup.py` | `AT_TAX_TAXONOMY` (taxas por região), `REGION_ACCOUNT_PREFIX` (2433/2434/2435), criação de Custom Fields em `Account` (`at_tax_type`, `at_tax_region`, `at_tax_code`), criação de contas SNC e Item Tax Templates por empresa. |
| `setup_company_portugal_compliance.py` | Ativação do compliance português numa `Company` — orquestra o resto do provisionamento. |

### 2.6. `overrides/` e `regional/`

| Ficheiro | Função |
| :--- | :--- |
| `overrides/payment_entry.py` | Ajustes pontuais ao comportamento nativo de Payment Entry necessários para o fluxo fiscal (ex: conta de destino em recebimentos). |
| `regional/portugal.py` | Ponto de integração com o mecanismo nativo `erpnext.regional` do ERPNext (não confundir com a lógica fiscal própria do módulo, que vive em `utils/`). |

### 2.7. `tasks/` — Tarefas Agendadas

| Ficheiro | Registado em `hooks.py` como | Conteúdo |
| :--- | :--- | :--- |
| `all.py` | `scheduler_events["all"]` | Métricas diárias em cache, tarefas de alta frequência. |
| `hourly.py` | `scheduler_events["hourly"]` | `retry_invoice_communications()` — processador do backoff exponencial (ver [manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md)). |
| `daily.py` | `scheduler_events["daily"]` | `check_certificate_expiry` e afins. |
| `weekly.py` | `scheduler_events["weekly"]` | Relatórios semanais de compliance. |
| `monthly.py` | `scheduler_events["monthly"]` | Lembrete/preparação da exportação SAF-T mensal. |
| `yearly.py` | `scheduler_events["yearly"]` | Relatório executivo anual e score de compliance — **não** cria séries novas para o ano seguinte (gestão anual de séries continua manual, ver limitação em [CERTIFICATION.md](CERTIFICATION.md)). |

### 2.8. `templates/`, `wsdl/`, `xsd/`, `fixtures/`

| Diretório | Conteúdo |
| :--- | :--- |
| `templates/saft_t/` | `main.xml`, `header.xml`, `master_files.xml`, `source_documents.xml` — os únicos templates realmente usados na geração do SAF-T. |
| `templates/print_formats/` | ⚠️ Ficheiros `.html` órfãos — ver secção 5. |
| `wsdl/` | `Comunicacao_Series.wsdl`, `faturas.wsdl`, `documentosTransporte.wsdl` — contratos oficiais da AT, bundled para não depender de acesso de rede a `info.portaldasfinancas.gov.pt` em runtime. |
| `xsd/` | `saftpt1.04_01.xsd` — schema oficial, usado por `xmlschema.XMLSchema11` (ver [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md)). |
| `fixtures/` | `custom_field.json`, `property_setter.json`, `print_format.json`, `at_tax_exemption.json`, `workspace.json`, `workspace_sidebar.json`, `desktop_icon.json` — regenerados via `bench export-fixtures --app portugal_compliance`, nunca editados à mão diretamente (risco de reformatação/perda de dados). |

---

## 3. Fluxo de Dados Principal

```
1. Rascunho     Utilizador grava Sales Invoice/POS Invoice/Payment Entry/Delivery Note
                enforce_fiscal_field_lock (before_save) — nada a bloquear ainda (sem ATCUD)
                Editável à vontade nesta fase - nenhuma assinatura foi gerada
                    │
2. Submissão    Utilizador clica Submit
                validate + before_submit_document: isenção de IVA (rígida), série comunicada
                Se qualquer validação falhar aqui, toda a transação sofre rollback -
                nenhum ATCUD chega a ser queimado (correção de arquitetura, 2026-08-24)
                    │
3. Assinatura   on_submit: generate_atcud_on_submit → ATCUDGenerator → signature.sign_document()
                RSA-SHA1 + SELECT FOR UPDATE na série + hash encadeada
                    │
4. Persistência (mesma chamada) ATCUD Log (signature_hash, atcud_code, ...)
                doc.db_set(atcud_code, qr_code, qr_code_image)
                    │
5. Comunicação  on_submit (a seguir, mesma lista de hooks) → enqueue_invoice_communication /
                enqueue_transport_communication
                (só se "Tempo Real" ativo; caso contrário aguarda o SAF-T mensal)
                    │
6. Impressão    before_print → log_document_print (Portugal Document Print Log)
                Print Format chama get_qr_code_data(doc=doc) diretamente
                    │
7. Exportação   SAF-T mensal/anual → SAFTGenerator → validação XMLSchema11 → download
```

---

## 4. Convenção de Nomenclatura de Séries

Formato usado neste sistema, sem hífenes: `PREFIXO+ANO+EMPRESA.####` (ex: `FT2026N.####`,
`RG2026N.####`). O nome do registo `Portugal Series Configuration` em si usa um formato
diferente, com hífenes, gerado automaticamente
(`{document_code}-{ano}-{company_code}-{hash}`, ex: `RG-2026-N-e434a0`) — **não confundir os
dois**: o campo `prefix`/`naming_series` é o que a AT recebe e o que aparece no `ATCUD`/QR
Code; o `name` do documento `Portugal Series Configuration` é apenas a chave interna do
Frappe.

---

## 5. Nota Metodológica — Código Morto e Inconsistências Detetadas

Esta auditoria confirmou, por leitura e teste direto, dois tipos de risco recorrentes nesta
base de código:

**A. Módulos nunca executados** — `series_adapter.py`, `series_manager.py`,
`naming_series_customizer.py`, `compliance_hooks.py`, e os ficheiros `.html` em
`templates/print_formats/` não são referenciados em `hooks.py` nem chamados por nenhum módulo
que o seja. Os Print Formats realmente servidos ao utilizador vivem em `fixtures/print_format.json`
(registos `Print Format` completos, incluindo o HTML), não nos ficheiros `.html` soltos.

**B. Implementações paralelas divergentes** — a mesma funcionalidade reimplementada em dois
sítios, sem que um substitua claramente o outro:

* `atcud_generator.py::_build_qr_data_optimized()` (chamada em todo `before_save`/
  `after_insert`) constrói uma segunda string de QR Code, independente de
  `jinja_methods.get_qr_code_data()` (usada pelos Print Formats reais) — só escreve em
  `ATCUD Log.qr_code_string`, sem impacto no que é impresso ou comunicado à AT, mas
  inconsistente como pista de auditoria.

**Regra prática**: antes de assumir que uma função é "a" implementação de uma
funcionalidade, confirmar com `grep` que está de facto referenciada em `hooks.py` ou chamada
a partir de um módulo que o esteja — e, para valores estáticos por DocType (como
`DOCUMENT_SIGNING_SPEC`, `get_document_type_code`), confirmar que continuam alinhados com o
`document_code` real das séries em produção, não apenas com o que fazia sentido quando o
mapeamento foi escrito.
