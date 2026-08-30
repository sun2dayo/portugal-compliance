# Dívida Técnica e Backlog de Evolução — Portugal Compliance

**Versão:** 1.2.0 (+ Parte 3 aberta para V1.3.0)
**Estado:** ✅ Backlog V1.2.0 (Parte 1 e Parte 2) resolvido e validado ao vivo, fechado em
2026-08-29 — ver histórico de fecho abaixo. **Parte 3, aberta em 2026-08-30, tem 1 item
pendente** (ver secção própria): não bloqueia nem impacta o módulo em produção, mas tem
impacto potencial na contabilização nativa do inquilino.

---

## Parte 1 — Tarefas Agendadas (weekly/monthly/yearly) — ✅ RESOLVIDO

**Origem:** smoke test isolado de `weekly.execute()`, `monthly.execute()` e
`yearly.execute()` em demo.erpnext.pt/NovaDX, 2026-08-25, durante a preparação do
Hotfix v1.1.2 — 34 erros pré-existentes catalogados por categoria, com
ficheiro:linha.

**Resolução (2026-08-29)**: todas as 11 categorias corrigidas em `weekly.py`,
`monthly.py` e `yearly.py` — colunas fantasma (`communication_status` → `is_communicated`;
`title`/`error_message` em Error Log/Portugal Series Configuration → `method`/removido),
JOIN `al.series_name` → `al.series_used`, `Portugal Auth Settings` (Single) deixou de ser
tratado como doctype com tabela própria, chamadas a funções e a um DocType
(`Portugal Compliance Audit`) inexistentes removidas. Validado ao vivo: os 3 scripts,
corridos em sequência a partir de uma baseline limpa do Error Log, terminam com **zero
novas entradas** (antes: 34 erros confirmados por execução isolada).

**Achados adicionais durante a correção, fora do catálogo original de 34 erros** (a
correção de uma camada revelou uma segunda, mascarada pelo `try/except` da primeira —
sem estes, o Error Log não teria ficado 100% limpo):

- **~10 funções nunca definidas adicionais** em `yearly.py` (`generate_compliance_overview`,
  `calculate_annual_operational_metrics`, `calculate_annual_financial_impact`,
  `assess_annual_regulatory_compliance`, `conduct_annual_risk_review`,
  `evaluate_technology_performance`, `assess_stakeholder_impact`,
  `perform_annual_benchmarking`, `generate_strategic_recommendations`,
  `create_next_year_plan`, `measure_operational_excellence`, `review_strategic_initiatives`,
  `identify_challenges_overcome`, `create_future_outlook`) — mascaradas porque eram
  chamadas dentro do mesmo dict literal que as 2 funções já catalogadas; Python para de
  avaliar o dict no primeiro `NameError`, escondendo as seguintes. Removidas as chaves
  correspondentes (nenhum código consome essas chaves a jusante).
- **`Portugal Weekly Report`**: segundo DocType inexistente (mesmo padrão de
  `Portugal Compliance Audit`), em `weekly.py::store_weekly_report`. Removido — o cache
  de 30 dias já era o mecanismo real de persistência.
- **`Portugal Auth Settings` mal tratado em `yearly.py::audit_system_security`**: contava
  registos por um campo `"password"` que nunca existiu (o real é `at_password`, Password
  fieldtype cifrado), e tratava o Single como se tivesse múltiplos registos. Reescrito para
  ler a configuração real via `get_password()`.
- **`SAFTGenerator.generate_saft()` chamado com `start_date=`/`end_date=`** em
  `yearly.py::generate_company_annual_saft` (assinatura real usa `from_date`/`to_date`) —
  e o `SAF-T Export Log` subsequente usava campos inexistentes (`period_start`,
  `period_end`, `year`, `export_date`) e `export_type="Annual"`, não uma opção válida do
  Select. Corrigido para os campos reais (`from_date`/`to_date`/`fiscal_year`/`"Full"`).
- **`saf_t_export_log.py::set_system_info()`**: `frappe.get_request_header("User-Agent")`
  levanta `RuntimeError("object is not bound")` fora de um pedido HTTP real — ou seja,
  **sempre** que um SAF-T é gerado pelo scheduler (não só em testes via `bench execute`).
  Bloqueava toda a geração anual de SAF-T em produção. Protegido com try/except.
- Um bug próprio introduzido a meio da correção (`get_configuration_changes` em
  `weekly.py` comparava `str` com `datetime` sem `get_datetime()`) foi apanhado pelo
  próprio smoke test e corrigido antes do fecho.

---

## Parte 2 — Backlog de Evolução (V1.2.0) — ✅ RESOLVIDO

### Impostos e SAF-T

- ✅ **Suporte a Imposto do Selo (IS)** — mecanismo implementado em 2026-08-29
  (`Account.at_tax_type`/`at_stamp_duty_verba`, `TaxType` dinâmico no SAF-T). Sem
  verba/taxa da TGIS fabricada — não faz sentido um valor por omissão numa instalação
  multi-inquilino (SaaS), e um código fiscal errado é pior do que nenhum. Processo de
  configuração documentado em [documentation/user_manual.md](documentation/user_manual.md)
  secção 4.2 e [documentation/tax_mapping_template.md](documentation/tax_mapping_template.md)
  secção 1bis — cada empresa/inquilino configura a sua própria verba, sem intervenção de
  código. Considerado **100% Feito** nestes termos (mecanismo + documentação); a
  configuração de uma verba real fica ao cuidado de cada inquilino quando aplicável ao
  seu negócio.
- ✅ **Granularidade de Impostos nos Recibos (Payment Entry)** — taxa/código/região reais
  da fatura de origem, validado ao vivo contra o XSD oficial (2026-08-29).
- ✅ **Herdar Região Fiscal nos Recibos** — mesma correção acima.
- ✅ **Mapeamento de Retenção na Fonte (`WithholdingTaxType`)** — campo
  `Account.at_withholding_tax_type` (IRS/IRC/IS) implementado 2026-08-29,
  `_withholding_tax_rows()` e `source_documents.xml` atualizados para o popular
  dinamicamente quando configurado. Validado contra o XSD (sem regressão nas faturas
  sem retenção).

### Sistema e Manutenção

- ✅ **Proteção de Cálculo de Métricas** (`update_cache_if_needed`) — corrigido e
  testado ao vivo com o cenário exato do bug (valor `bytes` corrompido no cache).

### Limpeza e Refatoração

- ✅ **Limpeza de Código Morto** — `git rm` de `utils/series_manager.py`,
  `utils/compliance_hooks.py`, `utils/series_validator.py` (2026-08-29), confirmado sem
  nenhuma referência restante (Python **e** JSON — onboarding/workspace/fixtures) antes
  da remoção. `bench migrate` limpo depois da remoção.
  - ⚠️ **Correção à lista original**: `utils/naming_series_customizer.py`, dado como
    "confirmado morto" na versão anterior deste backlog, **não está morto** — é chamado
    dinamicamente por `onboarding/portugal_setup.json` (step 3, `server_action` de
    validação), uma referência que só aparece em JSON, não em `import` Python, e por
    isso escapou à verificação anterior (grep só a `.py`). Confirmado vivo com
    `frappe.get_attr()` ao vivo antes de decidir não o remover. Fica como aviso: futuras
    limpezas de código morto neste módulo devem também grep a `.json` (onboarding/
    workspace/fixtures), não só a `.py`.
  - `utils/series_adapter.py` continua fora desta limpeza (uso real confirmado
    anteriormente, ver nota da versão anterior deste ficheiro no histórico do git).
- ✅ **Renomear Log de Comunicação** — `Portugal Invoice Communication Log` →
  `Portugal AT Communication Log`, via `frappe.rename_doc("DocType", ...)` com
  `developer_mode` ativado em `dev.erpnext.pt` (necessário para o rename automático de
  pasta/ficheiros de um DocType não-custom). Tabela SQL, pasta do módulo, `.py`/`.js`/
  `.json`, classe Python (`PortugalATCommunicationLog`) e os 28 registos existentes
  migrados automaticamente pelo próprio mecanismo do Frappe. Referências textuais soltas
  (`tasks/hourly.py`, `utils/at_invoice_webservice.py`,
  `utils/at_transport_webservice.py`, fixtures/workspace) atualizadas manualmente à parte
  (o rename automático só cobre metadados estruturados, não strings livres no código).
  Validado ao vivo: `bench migrate` limpo, 28 registos intactos, `tasks/hourly.execute()`
  (caminho real que escreve neste DocType) sem novos erros.

### ✅ Já resolvido (herdado de versões anteriores deste ficheiro)

- ~~Refatoração do `TaxCountryRegion` nas linhas de fatura~~ — já implementado antes desta
  sprint.
- ~~Correção do Redis em `tasks/all.py`~~ — já corrigido, commits `a4c081d`/`8b05308`.
- ~~Remover segundo gerador de QR Code~~ — já eliminado, commit `e29edc8`.

---

## Parte 3 — Backlog V1.3.0 (aberto)

### 🔲 Onboarding: retificar Plano de Contas / Default Accounts da Company

**Origem:** reportado pelo utilizador principal, 2026-08-30, ao tentar corrigir
manualmente `Company.default_receivable_account` (estava configurada como "219 - Perdas
por imparidade acumuladas - ZB" em vez de uma conta de Clientes real) e descobrir que a
pesquisa do campo Link não devolve **nenhum** resultado para "211", apesar de a conta
existir no Plano de Contas. Investigado e confirmado não ser bug do `portugal_compliance`
nem do core do ERPNext — ver auditoria completa na conversa de 2026-08-30.

**Causa raiz confirmada (consultada diretamente na base de dados):** o Plano de Contas
desta empresa (NovaDX) tem pelo menos duas contas-grupo de topo com `root_type`
estruturalmente errado — e `root_type` no Frappe é herdado por toda a subárvore, não é
editável por conta individual:
- `2 - Contas a receber e a pagar` está classificada como `root_type=Liability`. A SNC
  agrupa Clientes (ativo) e Fornecedores (passivo) sob a mesma classe 2, mas o Frappe só
  permite um único `root_type` por ramo da árvore. Resultado: as 18 contas com
  `account_type=Receivable` desta empresa (211, 2111–2116, 212, 218, 219, etc.) são
  **todas** `Liability` — nenhuma passa no filtro nativo do campo *Default Receivable
  Account* (que exige `root_type=Asset`). É literalmente impossível selecionar qualquer
  conta de Clientes através da UI sem reestruturar a árvore primeiro.
- `3 - Inventários e activos biológicos` está classificada como `root_type=Expense`
  (devia ser Asset) — mesma família de problema; impacto ainda não investigado a fundo.

**Impacto atual:** nenhum no módulo `portugal_compliance` — SAF-T, ATCUD e faturação não
dependem do `root_type` de Clientes/Inventário. Impacta sim relatórios contabilísticos
nativos do ERPNext (ex: Balanço) que dependem de `root_type=Asset` para classificar
Clientes/Inventário corretamente como ativo.

**Proposta de resolução futura (não implementada — decisão de arquitetura pendente):** um
processo de onboarding que detete este tipo de má classificação na árvore de contas e
ofereça retificá-la automaticamente (separar Clientes de Fornecedores em ramos-raiz
distintos com `root_type` correto), preenchendo depois os campos Default
Receivable/Payable/Cash/Bank Account da Company com as contas corretas resultantes. Por
decidir: se corre na ativação do compliance (junto de `setup_default_tax_categories`,
`tax_setup.py`) ou como um passo dedicado à parte — é uma reestruturação de dados
contabilísticos existentes (mais sensível do que criar registos novos como Tax Category),
não um mecanismo puramente aditivo/idempotente, por isso precisa de mais cuidado de
desenho antes de implementar.
