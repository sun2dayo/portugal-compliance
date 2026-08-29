# Dívida Técnica e Backlog de Evolução — Portugal Compliance

**Versão:** 1.1.2
**Origem:** smoke test isolado de `weekly.execute()`, `monthly.execute()` e `yearly.execute()` em demo.erpnext.pt/NovaDX, 2026-08-25, durante a preparação do Hotfix v1.1.2.
**Estado:** a Parte 1 (34 erros de tarefas agendadas) continua totalmente por
corrigir. A Parte 2 teve 4 itens corrigidos em 2026-08-29 (3x Alta + 1x Média
de Impostos e SAF-T/Sistema, ver checkboxes abaixo e commit `8fe8a30` em
`develop`) — os restantes continuam mapeados aqui exatamente como
descobertos, para o V1.2.0.

## Parte 1 — Tarefas Agendadas (weekly/monthly/yearly)

## Contexto

O Hotfix v1.1.2 corrigiu apenas dois bugs pontuais, cirúrgicos e já confirmados
(`current_number` → `current_sequence` em `tasks/hourly.py`, e o padrão
`frappe.cache.set/get()` → `frappe.cache().set_value/get_value()` nos 4
ficheiros de tarefas agendadas). Ao validar esse hotfix com um smoke test
isolado a `weekly.execute()`, `monthly.execute()` e `yearly.execute()`,
surgiram **34 erros pré-existentes, sem qualquer relação com o hotfix**
(nenhum menciona `expires_in_sec` ou `current_number` — essa parte está
genuinamente limpa). São bugs antigos destes 3 scripts, nunca antes
exercitados em produção. Ficam documentados aqui, por categoria, com
ficheiro:linha, para não se perderem antes do V1.2.0.

---

## 1. Coluna fantasma `communication_status` (13 ocorrências)

`Portugal Series Configuration` não tem este campo — os reais são
`is_communicated`, `communication_date`, `validation_code`,
`communication_attempts`, `last_communication_attempt` (já corrigido no
padrão certo em `tasks/hourly.py` no Hotfix v1.1.1).

- `weekly.py:165` — escrita (`frappe.db.set_value`)
- `weekly.py:217` — leitura, `SELECT communication_status`
- `weekly.py:226`, `weekly.py:227` — acesso a `comm.communication_status` sobre o resultado da query acima (falha em cascata)
- `weekly.py:498` — `WHERE ... AND communication_status = 'Success'` (SQL raw)
- `weekly.py:679` — escrita
- `monthly.py:267`, `monthly.py:712`, `monthly.py:734`, `monthly.py:738` — escrita/filtro
- `yearly.py:214`, `yearly.py:363`, `yearly.py:908` — escrita/filtro

## 2. Coluna fantasma `title` em `Error Log` (6 ocorrências)

`Error Log` não tem campo `title` nesta versão do Frappe (16.x) — o campo
identificador é `method`.

- `weekly.py:260` — `SELECT title, COUNT(*) as count`
- `weekly.py:522` — idem
- `weekly.py:1030`, `weekly.py:1034` — `SELECT title, error, ... GROUP BY title, error`
- `monthly.py:431` — filtro `{"title": ["like", "%critical%"]}`
- `yearly.py:195`, `yearly.py:1102` — mesmo filtro

## 3. Coluna fantasma `error_message` (2 ocorrências)

- `weekly.py:1062` — pedida no `fields=[...]` de uma query a `Portugal Series Configuration` (mesmo campo inexistente já removido de `hourly.py` no Hotfix v1.1.1)
- `yearly.py:727` — `error_message = NULL` num `UPDATE` raw SQL

## 4. Coluna fantasma `certificate_expiry_date`

- `monthly.py:589` — filtro sobre `Portugal Auth Settings`. O mesmo bug já
  foi corrigido especificamente em `dashboards/company.py` (ver comentário
  nesse ficheiro, 2026-08-24) — falta replicar a correção aqui.

## 5. JOIN quebrado — `al.series_name`

`ATCUD Log` não tem campo `series_name` — o real é `series_used`.

- `weekly.py:1168` e `weekly.py:1182` — `LEFT JOIN \`tabATCUD Log\` al ON al.series_name = psc.series_name`

## 6. `Portugal Auth Settings` tratado como doctype com tabela própria

`Portugal Auth Settings` é um **Single** doctype — os seus dados vivem em
`tabSingles`, não numa tabela `tabPortugal Auth Settings` dedicada.
`frappe.db.get_all("Portugal Auth Settings", ...)` gera SQL contra uma
tabela que não existe.

- `weekly.py:984` — `Error getting configuration changes: Table '...tabPortugal Auth Settings' doesn't exist`

## 7. Funções nunca definidas (`NameError`)

- `yearly.py:83` — chama `generate_compliance_overview(year_start, year_end)`, nunca definida/importada neste módulo
- `yearly.py:125` — chama `measure_operational_excellence(start_date, end_date)`, idem

## 8. Assinatura incompatível — `SAFTGenerator.generate_saft()`

- `yearly.py:576-578` — chama `saft_generator.generate_saft(..., start_date=start_date, ...)`, mas o método real não aceita `start_date` como kwarg (assinatura real usa `from_date`/`to_date`, ver `utils/saft_generator.py` e `CERTIFICATION.md` secção 3).

## 9. DocType apagada ainda referenciada

- `yearly.py:1167` — `frappe.get_doc({"doctype": "Portugal Compliance Audit", ...})`. Esta DocType não existe no app atual (erro: "the DocType you're trying to open might be deleted") — provavelmente um resquício de uma versão anterior da app.

## 10. `KeyError` em cascata (efeito, não causa raiz)

`weekly.py:420` e `weekly.py:1462-1464` acedem a
`report_data['series_statistics']['series_communicated']` e
`summary['key_metrics']`, chaves que nunca chegam a existir porque o passo
que as preencheria (`get_weekly_series_stats`, item 1 acima) já falhou antes.
Corrigir o item 1 deve eliminar estes dois automaticamente — não são bugs
independentes.

## 11. Erro de formatação de string

- `weekly.py`, função `get_weekly_error_stats` (~linha 243-264) — "not enough
  arguments for format string". A query em `weekly.py:264` usa
  `LIKE '%portugal_compliance%'` dentro de uma string que também é composta
  com o operador `%` do Python em vez de passar os parâmetros a
  `frappe.db.sql(query, params)` — o `%` literal do `LIKE` está a ser
  interpretado como um placeholder de formatação.

---

## Resumo por script

| Script | Erros | Categorias envolvidas |
|---|---|---|
| `weekly.py` | 14 | 1, 2, 3, 5, 6, 10, 11 |
| `monthly.py` | 9 | 1, 2, 4 |
| `yearly.py` | 11 | 1, 2, 3, 7, 8, 9 |

**Total: 34 erros**, todos confirmados ao vivo (não simulados) contra
demo.erpnext.pt/NovaDX em 2026-08-25, com o Error Log de cada execução
isolada como evidência.

---

## Parte 2 — Backlog de Evolução (V1.2.0)

**Origem:** lista de TODO trazida pelo utilizador em 2026-08-26, validada item a
item contra o código atual em `develop` antes de ser aceite aqui, e reorganizada
em 2026-08-26 por assunto e prioridade a pedido do utilizador. 3 itens da lista
original já estavam implementados (ver "Já resolvido" no fim) e 1 item (limpeza
de código morto) foi corrigido: um dos 4 ficheiros apontados como "morto" está
na verdade em uso ativo. O item "Faturação por Terceiros" foi removido do
backlog (sem caso de uso concreto que o justifique).

Organização: agrupado por assunto; dentro de cada assunto, ordenado por
prioridade (Alta → Média → Baixa), com a prioridade de cada item marcada
explicitamente.

### Impostos e SAF-T

- [x] **[Prioridade Alta] Suporte a Imposto do Selo (IS) — parcial (mecanismo pronto, sem verba real)**
  Corrigido em `8fe8a30` (2026-08-29): `TaxType` dinâmico em
  `source_documents.xml`, deteção via `Account.at_tax_type`/`at_tax_code`,
  novo campo `at_stamp_duty_verba` em `setup/tax_setup.py`. **Não** foi
  criada nenhuma tabela de verbas/taxas da TGIS — não havia dados reais do
  negócio disponíveis e um código fiscal fabricado seria pior do que
  nenhum. Falta: criar a(s) conta(s) de Imposto do Selo reais
  (`at_tax_type="IS"` + `at_stamp_duty_verba` com a verba aplicável) e
  validar um documento real de IS contra o XSD antes de considerar
  fechado por completo.

- [x] **[Prioridade Alta] Granularidade de Impostos nos Recibos (Payment Entry) — taxa e base reais**
  Corrigido em `8fe8a30` (2026-08-29): `utils/saft_generator.py` calcula
  agora os grupos reais de imposto (região+código+base) da fatura
  referenciada por cada `Payment Entry Reference`, com split proporcional
  do `allocated_amount` quando a fatura tem taxas mistas — cada grupo vira
  uma `<Line>` própria em `source_documents.xml`. `TaxExemptionReason`/
  `TaxExemptionCode` = M99 passou a só aparecer quando o grupo é isento
  (`ISE`), não como valor universal. Validado ao vivo: XML real gerado
  para `novadx` com recibos a 23% (`FT2026N0012`/`0013`) mostra
  `TaxPercentage=23.00` sem exemption, e passa a validação XSD completa.

- [x] **[Prioridade Alta] Herdar Região Fiscal nos Recibos (`Payment/Line/Tax/TaxCountryRegion`)**
  Corrigido junto com o item anterior (mesma função/template) em `8fe8a30`
  — `reference.tax_region` já vem do grupo de imposto real da fatura
  (`Account.at_tax_region`), substituindo o `PT` fixo. Ainda não exercitado
  ao vivo com uma fatura de Madeira/Açores (essas contas só passaram a
  existir hoje via a correção da Taxa de IVA Regional — ver nota no fim
  desta secção), mas a lógica é a mesma já validada para faturas.
  já usada para faturas em `_line_region`, `utils/saft_generator.py` linha
  ~291-300) e passar `reference.tax_region` para o template, substituindo o
  `PT` fixo por `{{ reference.tax_region or 'PT' }}`.

- [ ] **[Prioridade Média] Mapeamento de Retenção na Fonte (`WithholdingTaxType`)**
  Confirmado pendente — `utils/saft_generator.py` (comentário na função de
  `_withholding_tax_rows()`, ~linha 550-559) já mapeia valor e descrição mas
  omite deliberadamente `WithholdingTaxType` por falta de correspondência
  fiável no ERPNext.
  **Instruções de implementação:**
  1. Adicionar um campo `at_withholding_tax_type` (Select: IRS/IRC/IS) à
     configuração da conta de retenção (ou a um novo campo em `Portugal Auth
     Settings` se for por empresa, não por conta).
  2. Popular esse campo nas contas de retenção existentes.
  3. Em `_withholding_tax_rows()`, ler o novo campo e passar como
     `WithholdingTaxType` no dicionário retornado.
  4. Atualizar `templates/saft_t/source_documents.xml` (bloco
     `<WithholdingTax>`, ~linha 76-79) para emitir
     `<WithholdingTaxType>{{ wh.withholding_tax_type }}</WithholdingTaxType>`
     apenas quando o campo estiver preenchido (é opcional no XSD).

### Correções adicionais (fora deste backlog, encontradas em 2026-08-29)

Não estavam mapeadas aqui — descobertas durante a investigação/implementação
dos itens acima e corrigidas no mesmo commit `8fe8a30`.

- [x] **Taxa de IVA Regional nunca gerada para Madeira/Açores**
  `setup/tax_setup.py::_execute_compliance_setup` chamava
  `setup_tax_templates_for_company(company, region="PT")` com a região fixa
  em Continente — a própria taxonomia (`AT_TAX_TAXONOMY`) já tinha os dados
  completos das 3 regiões, e o ficheiro documentava
  `create_regional_tax_setup_for_company()` no topo, mas essa função nunca
  chegou a ser implementada (confirmado por grep a todo o repositório).
  Implementada e ligada à ativação automática + novo botão manual "Gerar
  Séries/Taxas Regionais". Validado ao vivo: 12 templates + 12 contas SNC
  (2433x/2434x/2435x) na `novadx`.
- [x] **Bug de idempotência em `setup_tax_templates_for_company`**
  A verificação `frappe.db.exists(doctype, template_title)` comparava o
  título contra a chave primária, mas `Sales Taxes and Charges Template`/
  `Item Tax Template` sobrescrevem `autoname()` para
  `name = título + " - " + abreviatura_empresa` — nunca batia certo. Ficou
  dormant por a função só correr uma vez (ativação); expôs-se como
  `IntegrityError` ao testar a via de reexecução acima. Corrigido para
  filtrar por `{title, company}`.
- [x] **`tax_code` do SAF-T ignorava a região (faturas e tabela mestra)**
  `_get_line_tax_code()` classificava NOR/INT/RED/ISE só por faixa de
  percentagem — a taxa Normal dos Açores (16%) caía na faixa "Intermédia"
  (<20%) do Continente. Ficou dormant por nunca terem existido contas dos
  Açores/Madeira; o item acima ativou-o. Corrigido em
  `utils/saft_generator.py` (`get_sales_invoices_data` e
  `get_tax_table_data`) para usar o código real da conta (`at_tax_code`,
  já correto por região) quando disponível.

### Sistema e Manutenção

- [x] **[Prioridade Média] Proteção de Cálculo de Métricas (TypeError data - NoneType)**
  Corrigido em `8fe8a30` (2026-08-29): `tasks/all.py::update_cache_if_needed()`
  agora calcula `parsed_last_cache_update = get_datetime(last_cache_update)
  if last_cache_update else None` antes do `if`, protegendo contra o `None`
  devolvido por um parse falhado (valor `bytes` corrompido no cache), não só
  contra o valor original vazio. Testado ao vivo com o cenário exato do
  bug (valor `bytes` inválido forçado no cache) — sem novo erro no Error
  Log. O item opcional (migrar para `frappe.cache().get_value()`/
  `set_value()`) não foi feito — não é a causa do bug, fica em aberto se
  se quiser eliminar de vez a possibilidade de `bytes`.

### Limpeza e Refatoração

- [ ] **[Prioridade Baixa] Limpeza de Código Morto — corrigido face à lista original**
  Verificado com grep de importações reais (não comentários) em todo o
  repositório antes de validar esta tarefa:
  - `utils/series_manager.py` — **confirmado morto**, zero imports reais fora
    do próprio ficheiro. Seguro remover (`git rm`).
  - `utils/naming_series_customizer.py` — **confirmado morto**, mesma
    verificação. Seguro remover.
  - `utils/compliance_hooks.py` — **confirmado morto**, mesma verificação.
    Seguro remover.
  - `utils/series_validator.py` — **não estava na lista original, mas também
    está morto** (zero imports reais fora dele próprio) — candidato extra
    para a mesma limpeza.
  - `utils/series_adapter.py` — **⚠️ NÃO está morto**, ao contrário do
    proposto. Tem imports reais e ativos a partir de
    `portugal_compliance/doctype/portugal_series_configuration/portugal_series_configuration.py`
    (5 pontos: `update_doctype_naming_series`, `sync_all_company_naming_series`,
    `sync_all_doctypes`) e de `uninstall/before_uninstall.py`
    (`cleanup_naming_series_on_uninstall`). **Não remover** sem primeiro
    verificar se essas 6 funções são de facto chamadas em produção ou se são
    elas próprias código morto dentro de um ficheiro vivo — precisa de uma
    análise à parte, não uma remoção direta.
  **Instruções de implementação:** `git rm` dos 4 ficheiros confirmados
  mortos (`series_manager.py`, `naming_series_customizer.py`,
  `compliance_hooks.py`, `series_validator.py`), correr `bench migrate` e a
  suite de testes para confirmar que nada rebenta, só depois commitar.
  `series_adapter.py` fica de fora desta limpeza até à análise à parte.

- [ ] **[Prioridade Baixa] Renomear Log de Comunicação** (`Portugal Invoice
  Communication Log` → algo como `Portugal AT Communication Log`)
  Confirmado: `tasks/hourly.py:169-177` despacha para `register_invoice()`
  (faturas) ou `register_transport_document()` (Delivery Note) consoante
  `log.document_type` — o mesmo DocType serve ambos os fluxos, e o nome só
  reflete o primeiro. Renomear DocType em Frappe é uma operação nativa
  (`bench rename-doctype` ou o botão de rename na UI) que atualiza
  automaticamente todas as referências — baixo risco, mas requer testar a
  app depois (relatórios, dashboards e o próprio `tasks/hourly.py` referenciam
  o nome do DocType).

### ✅ Já resolvido (estava na lista original, não fica pendente)

- ~~Refatoração do `TaxCountryRegion` nas linhas de fatura~~ — **já implementado.**
  `templates/saft_t/source_documents.xml:65` usa
  `{{ item.tax_region or 'PT' }}`, populado por `_line_region()` em
  `utils/saft_generator.py` a partir de `Account.at_tax_region` — não há
  nenhuma lógica de "adivinhar pela percentagem". Confirmado por leitura
  direta do código atual em `develop`.
- ~~Correção do Redis em `tasks/all.py`~~ — **já corrigido**, commit `a4c081d`
  (2026-08-24) e reforçado no Hotfix v1.1.2 (`8b05308`) para os restantes
  ficheiros de tarefas agendadas. `tasks/all.py` já usa
  `frappe.cache().set_value(...)` em todos os pontos onde armazena
  dicts/listas.
- ~~Remover segundo gerador de QR Code (`_build_qr_data_optimized`)~~ — **já
  eliminado**, commit `e29edc8` (Fase 1 da certificação v1.1.0). A função não
  existe mais no código; as únicas ocorrências do nome são comentários a
  explicar a remoção.
