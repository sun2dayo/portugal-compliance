# Dívida Técnica — Tarefas Agendadas (weekly/monthly/yearly)

**Versão:** 1.1.2
**Origem:** smoke test isolado de `weekly.execute()`, `monthly.execute()` e `yearly.execute()` em demo.erpnext.pt/NovaDX, 2026-08-25, durante a preparação do Hotfix v1.1.2.
**Estado:** nenhum destes itens foi corrigido — mapeados aqui exatamente como descobertos, para o V1.2.0.

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
