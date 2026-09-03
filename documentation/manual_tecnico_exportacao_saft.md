# Manual Técnico: Exportação SAF-T (PT) v1.04_01

**Versão:** 1.1.0

O ficheiro SAF-T (Standard Audit File for Tax Purposes) é o documento XML normalizado que
consolida toda a informação fiscal de um período (mensal ou anual), exigido pela Portaria
n.º 302/2016 e pelo Despacho n.º 8632/2014. Este manual descreve o processo técnico completo
de geração, validação e exportação no módulo `portugal_compliance`.

---

## 1. Interface e Modelo de Dados

**DocType**: `SAF-T Export Log` — um registo por exportação, campos: `company`, `from_date`,
`to_date`, `export_type`, `status` (Pending → In Progress → Completed | Failed),
`xml_validation_status` (Not Validated | Valid | Invalid | Validation Error),
`xsd_validation_errors`, `file_path`, `file_size`, `file_hash`, `total_records`.

**API**: [api/saft_api.py](portugal_compliance/api/saft_api.py) —
`generate_saft_export(company, from_date, to_date, export_type)` cria o log e despacha
`generate_saft_background` para a fila de background; `download_saft_file(export_log_name)`
serve o ficheiro, **recusando qualquer export cujo `status` não seja `"Completed"`**.

---

## 2. Âmbito: `TaxAccountingBasis = "F"`

O módulo declara-se, no cabeçalho SAF-T, como software de **Faturação** (`F`), não de
Contabilidade Integrada (`C`) nem Integrado (`I`):

```xml
<!-- header.xml -->
<TaxAccountingBasis>{{ tax_accounting_basis }}</TaxAccountingBasis>
```

Consequência direta, documentada em
[master_files.xml](portugal_compliance/templates/saft_t/master_files.xml):

```xml
<!-- GeneralLedgerAccounts fica de fora: só é exigido quando TaxAccountingBasis inclui -->
<!-- contabilidade (C/I) - aqui TaxAccountingBasis="F" (faturação). -->
```

Isto **não** é uma limitação de implementação — confirmado contra o XSD oficial
([xsd/saftpt1.04_01.xsd](portugal_compliance/xsd/saftpt1.04_01.xsd)): tanto
`GeneralLedgerAccounts` como `GeneralLedgerEntries` têm `minOccurs="0"` na definição do
elemento raiz `AuditFile`. Tentar preencher estas secções sob base `F` obrigaria a NovaDX a
pedir uma certificação de Sistema Integrado/Contabilidade, fora do âmbito atual do módulo.

---

## 3. Processo de Geração

### 3.1. Classe `SAFTGenerator`

[utils/saft_generator.py](portugal_compliance/utils/saft_generator.py),
`generate_saft(company, from_date, to_date, export_type="full")` — aceita qualquer intervalo
de datas (cobre exportação mensal ou anual sem distinção de código).

`prepare_context()` recolhe, com queries em lote (nunca N+1 por documento):

| Secção | Método | Conteúdo |
| :--- | :--- | :--- |
| Header | inline em `prepare_context` | NIF, nome, ano fiscal, `TaxAccountingBasis`, número de certificado |
| Customers | `get_customers_data` | Terceiros com movimentos no período |
| Suppliers | `get_suppliers_data` | Só para masterdata (ver secção 2) — nunca como SourceDocument |
| Products | `get_products_data` | Artigos movimentados |
| TaxTable | `get_tax_table_data` | Taxas de IVA + praça fiscal (`Account.at_tax_region`) |
| Sales Invoices | `get_sales_invoices_data` | Sales Invoice **e** POS Invoice — mesma estrutura de colunas |
| Payments | `get_payments_data` | Payment Entry, com linhas de referência a documentos de origem |

### 3.2. Render e Escrita

`render_template(context)` usa Jinja2 (`Environment(loader=FileSystemLoader(...),
autoescape=False, trim_blocks=True, lstrip_blocks=True)`) sobre 4 templates compostos em
[templates/saft_t/main.xml](portugal_compliance/templates/saft_t/main.xml):

```xml
<AuditFile xmlns="urn:OECD:StandardAuditFile-Tax:PT_1.04_01">
    {% include "header.xml" %}
    {% include "master_files.xml" %}
    {% include "source_documents.xml" %}
</AuditFile>
```

`save_saft_file()` grava em `sites/<site>/private/files/saft_exports/`; `generate_file_hash()`
calcula SHA-256 do conteúdo, guardado em `SAF-T Export Log.file_hash` para deteção de
alteração posterior ao ficheiro em disco.

---

## 4. Validação Rigorosa: XSD 1.1

### 4.1. A armadilha da versão do schema

[xsd/saftpt1.04_01.xsd](portugal_compliance/xsd/saftpt1.04_01.xsd) declara na raiz:

```xml
<xs:schema ... vc:minVersion="1.1" ...>
```

Isto assinala **XML Schema 1.1**, não 1.0. Um validador construído com
`xmlschema.XMLSchema` (que implementa apenas XSD 1.0) trata este atributo de acordo com a
regra de conformidade de versão do próprio padrão XSD — e o sintoma é silencioso e enganador:
o próprio elemento raiz `AuditFile` deixa de ser reconhecido ("`{...}AuditFile` não é um
elemento do schema"), mascarando **todos** os erros reais de conteúdo por trás de um
falso-negativo genérico.

**Implementação correta**, em
[saf_t_export_log.py](portugal_compliance/portugal_compliance/doctype/saf_t_export_log/saf_t_export_log.py),
`validate_xml_content()`:

```python
import xmlschema
xsd_path = frappe.get_app_path("portugal_compliance", "xsd", "saftpt1.04_01.xsd")
schema = xmlschema.XMLSchema11(xsd_path)  # não XMLSchema (1.0)
errors = list(schema.iter_errors(xml_content))
```

`iter_errors` (não `is_valid`) devolve **todos** os erros encontrados, não só o primeiro —
essencial para diagnóstico: um SAF-T com centenas de faturas pode repetir o mesmo erro
estrutural centenas de vezes; a lista é limitada às primeiras 50 ocorrências / 5000
caracteres, com contagem do total, para que o resultado permaneça legível.

### 4.2. Gatilho no fluxo real de geração

`generate_saft_background()` chama `validate_xml_content()` **antes** de marcar o export como
`"Completed"`:

```python
is_valid = export_log.validate_xml_content(saft_xml)
if not is_valid:
    export_log.status = "Failed"
    export_log.save()
    return
export_log.status = "Completed"
```

`download_saft_file` (secção 1) recusa qualquer export que não esteja `"Completed"` — um
ficheiro inválido **nunca chega a estar disponível para download**, muito menos para
submissão à AT.

### 4.3. Defeitos reais encontrados por esta validação

A introdução da validação XSD 1.1 real (antes disso, o módulo tinha uma verificação manual
superficial com `xml.etree.ElementTree`, que nunca era sequer chamada pelo fluxo de geração)
encontrou dois defeitos pré-existentes:

1. **`PaymentRefNo`** usava o nome bruto do documento (`"RC2026N0001"`), não batendo com o
   padrão exigido `[^ ]+ [^/^ ]+/[0-9]+`. Corrigido para reutilizar o mesmo formato "CÓDIGO
   SÉRIE/SEQUÊNCIA" já usado em `InvoiceNo`.
2. **`Payment/Line/Tax`** com `TaxPercentage=0.00` sem `TaxExemptionReason`/`TaxExemptionCode`
   viola uma asserção `xs:assert` do XSD (`PaymentTax` exige isenção explícita quando a taxa é
   zero). Corrigido adicionando `TaxExemptionReason`/`TaxExemptionCode` como **irmãos** de
   `Tax` dentro de `Line` (não filhos de `Tax` — o tipo `PaymentTax` nem sequer os permite),
   com o código `M99` ("Não sujeito ou não tributado / autoliquidação").

Ambos passaram despercebidos indefinidamente precisamente porque nada validava o ficheiro
gerado contra o schema real.

---

## 5. Regime de IVA de Caixa: `RC` vs `RG`

### 5.1. A definição oficial

O tipo `SAFTPTPaymentType` do XSD documenta, na sua própria anotação:

> RC para Recibo emitido no âmbito do regime de IVA de Caixa (incluindo os relativos a
> adiantamentos desse regime), RG para Outros recibos emitidos

Isto **não tem qualquer relação com o sentido do pagamento** (Receber/Pagar) — uma
confusão real, corrigida nesta base de código: uma versão anterior gerava
`PaymentType="RC"` para qualquer Payment Entry do tipo "Receive", independentemente de a
empresa estar ou não no regime de Caixa.

### 5.2. Implementação correta

Campo `cash_vat_scheme` (Check) em `Portugal Auth Settings`:

```python
cash_vat_scheme = cint(frappe.db.get_single_value("Portugal Auth Settings", "cash_vat_scheme"))
saft_payment_type = "RC" if cash_vat_scheme else "RG"
```

```xml
<PaymentType>{{ payment.saft_payment_type }}</PaymentType>
```

`PaymentRefNo` (o número do documento) é um campo **separado**, com origem independente — o
código real da série (`Portugal Series Configuration.document_code`), estruturalmente
idêntico ao usado para `InvoiceType` de Sales Invoice/Nota de Crédito:

```python
def _payment_doc_code(naming_series):
    code = frappe.db.get_value("Portugal Series Configuration", {"naming_series": naming_series}, "document_code")
    return code or "RC"
```

> **Consistência com o Webservice de Séries.** A AT cruza o `tipoDoc` comunicado no registo
> da série (webservice `registarSerie`, ver
> [manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md)) com o `PaymentType`
> reportado no SAF-T mensal. O `document_code` por omissão de uma nova série de Payment Entry
> é **`RG`**, não `RC` — só é `RC` se a empresa estiver genuinamente enquadrada no regime de
> Caixa junto da AT.

### 5.3. Não implementado, e porquê

Um dropdown global "Regime de IVA" (Normal/Isenção Artigo 53º/Caixa), à semelhança de
sistemas como InvoiceXpress ou Odoo, **não foi implementado**. Auditado o módulo
`l10n_pt_certification` (OCA/l10n-portugal, branch 18.0) — o par mais próximo
arquiteturalmente (assinatura própria, ATCUD, QR, series mapping) — não existe lá nenhum
campo desse tipo: a isenção é tratada por registo de imposto individual
(`AT Tax Exemption`/`at_exemption_reason`), o mesmo padrão já usado aqui. Forçar
automaticamente um código de isenção a nível de empresa arriscaria aplicá-lo a transações que
não são efetivamente isentas.

---

## 6. Moeda Base (EUR) e Descontos Globais (2026-08-31)

`get_sales_invoices_data()` foi auditada e corrigida em dois pontos, ambos ligados a como o
ERPNext calcula e guarda valores por linha e por documento — não a erros de fórmula do
próprio módulo.

### 6.1. Moeda de Transação vs. Moeda Base

O ERPNext guarda cada valor monetário duas vezes: uma vez na **moeda de transação** do
documento (`net_total`, `grand_total`, `rate`, `amount` — o que aparece no ecrã se a fatura
for emitida em USD, por exemplo) e outra vez já convertida para a **moeda base da empresa**
(`base_net_total`, `base_grand_total`, `base_rate`, `base_net_amount`), aplicando
`conversion_rate` internamente. O SAF-T (PT) exige valores em EUR — a moeda base de qualquer
empresa portuguesa — independentemente da moeda em que uma fatura específica foi emitida.

**Defeito corrigido**: a versão anterior selecionava e usava os campos de moeda de
**transação** (`si.net_total`, `si.total_taxes_and_charges`, `si.grand_total`, `sii.rate`,
`sii.amount`) diretamente no XML, com `si.conversion_rate` selecionado mas nunca de facto
utilizado (código morto, removido). Numa fatura em EUR isto não tinha efeito visível — moeda
de transação e moeda base coincidem — mas uma fatura em USD ou qualquer outra moeda
estrangeira reportava ao SAF-T os valores errados, sem qualquer conversão à taxa de câmbio.
Confirmado ao vivo com uma fatura de teste em USD e uma taxa de câmbio real
(`Currency Exchange`, USD→EUR): antes da correção, os totais no XML batiam com o valor em
dólares, não em euros. Corrigido trocando todos os campos usados (linha e cabeçalho) para os
equivalentes `base_*`:

```python
# get_sales_invoices_data - SELECT corrigido
si.base_net_total, si.base_total_taxes_and_charges, si.base_grand_total,
sii.base_rate, sii.base_net_amount
```

### 6.2. Desconto Global (`additional_discount_amount`)

**Defeito corrigido**: a construção da linha usava `Item.amount`/`base_amount` — campo que só
reflete o desconto **de linha** (`discount_percentage`/`discount_amount` preenchidos
diretamente no item). Confirmado por leitura de
`erpnext/controllers/taxes_and_totals.py::apply_discount_amount()`: quando a fatura tem um
desconto **global** (`additional_discount_amount`, aplicado ao cabeçalho, ex. "10% de desconto
em toda a fatura"), o ERPNext distribui-o proporcionalmente por cada linha, mas grava o
resultado apenas em `Item.net_amount`/`base_net_amount` — nunca em `amount`/`base_amount`, que
permanecem com o valor pré-desconto-global. O total do cabeçalho (`grand_total`) já refletia
corretamente o desconto; era só a discriminação por linha do SAF-T que o ignorava, produzindo
um ficheiro onde a soma das linhas não batia com o total do documento sempre que um desconto
global era usado. Corrigido usando `net_amount`/`base_net_amount` (e `base_rate`) em vez de
`amount`/`base_amount` na construção de cada linha de `SourceDocuments`.

> Para uma fatura normal em EUR sem desconto global (o caso comum), `base_*` e `net_amount`
> coincidem exatamente com os valores usados antes da correção — sem regressão. O impacto real
> é limitado às faturas em moeda estrangeira e/ou com desconto global aplicado, mas nesses
> casos era um erro fiscal genuíno, não cosmético.

---

## 7. Documentos Anulados

Uma fatura anulada (`docstatus=2`) **não desaparece** do SAF-T — a lei exige o registo da
anulação, não a sua omissão:

```python
# get_sales_invoices_data - query SQL
WHERE si.docstatus IN (1, 2)  # inclui anuladas
```

```python
is_cancelled = row.docstatus == 2
invoice["tax_payable"] = 0.0 if is_cancelled else abs(flt(row.base_total_taxes_and_charges))
invoice["net_total_abs"] = 0.0 if is_cancelled else abs(flt(row.base_net_total))
invoice["gross_total_abs"] = 0.0 if is_cancelled else abs(flt(row.base_grand_total))
```

```xml
<!-- source_documents.xml -->
<InvoiceStatus>{{ 'N' if invoice.docstatus == 1 else 'A' if invoice.docstatus == 2 else 'T' }}</InvoiceStatus>
```

O ATCUD e a hash de assinatura reportados permanecem os **originais** (nunca recalculados nem
apagados — ver inviolabilidade em `document_hooks.py`) — prova de que o documento foi
efetivamente assinado antes de ser anulado, sem que a AT liquide imposto sobre um documento
sem efeito fiscal.

---

## 8. Praça Fiscal (Continente/Açores/Madeira)

`TaxCountryRegion` — tanto na `TaxTable` mestra como por linha de `SourceDocuments` — é
extraído estruturalmente de `Account.at_tax_region`, nunca adivinhado a partir da
percentagem de imposto (duas praças fiscais podem partilhar a mesma taxa hoje, ou convergir
no futuro). Ver detalhe completo em
[manual_tecnico_qrcode.md](manual_tecnico_qrcode.md), secção 4 — a mesma resolução de
`tax_breakdown.py` alimenta o QR Code e o SAF-T a partir de uma única fonte.

**Limitação conhecida**: `Payment/Line/Tax/TaxCountryRegion` (não a `TaxTable` mestra, já
corrigida) mantém-se fixo em `"PT"` — o bloco de imposto de um recibo é sempre a isenção fixa
`M99` (sem taxa própria, herda o imposto já liquidado na fatura de origem referenciada em
`SourceDocumentID`), pelo que herdar a região do documento de origem é uma alteração a
implementar à parte.

---

## 9. Retenção na Fonte

`_withholding_tax_rows(invoice_name)` mapeia linhas de `Sales Taxes and Charges` marcadas com
`is_tax_withholding_account=1` (campo nativo do ERPNext, populado quando uma *Tax Withholding
Category* é aplicada):

```sql
SELECT description, base_tax_amount FROM `tabSales Taxes and Charges`
WHERE parent = %s AND is_tax_withholding_account = 1
```

> Corrigido de `tax_amount` para `base_tax_amount` na mesma auditoria da secção 6 — mesma
> razão: `tax_amount` é a moeda de transação, `base_tax_amount` é a moeda base (EUR) exigida
> pelo SAF-T.

`WithholdingTaxType` (IRS/IRC/IS) — campo opcional no XSD — é deliberadamente omitido: não
tem correspondência fiável no modelo de dados do ERPNext, e inventar um valor seria pior do
que não o reportar.

---

## 10. Geração Automática Mensal e Envio por Email (2026-09-03)

Não existe nenhum webservice da AT para upload do ficheiro SAF-T — confirmado por auditoria
direta aos manuais oficiais de integração da AT (não assumido). O único webservice de
faturação (perfil WFA, `RegisterInvoice`/`fatcorews`, ver
[manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md))
comunica documentos um a um — quando esse canal está em Tempo Real
(`Portugal Auth Settings.invoice_communication_method`), a obrigação de comunicar o SAF-T
mensal à AT deixa de existir na prática. O ficheiro gerado aqui serve sempre para arquivo e
para download/envio ao contabilista — **nunca** para submissão automática à AT, que não
existe como webservice. `saf_t_export_log.py::submit_to_at()` reflete isto: lança sempre
`NotImplementedError`, documentado no próprio docstring.

### 10.1. Configuração — `Portugal Auth Settings`

Secção "Comunicação SAF-T Mensal":

| Campo | Tipo | Omissão | Descrição |
| :--- | :--- | :--- | :--- |
| `saft_communication_method` | Select | `Manual` | `Manual` (fica disponível para download em `SAF-T Export Log`) ou `Email (Contabilista)` (também enviado por email). Nunca uma terceira opção de webservice — ver acima. |
| `saft_send_day` | Select (1–28) | `5` | Dia do mês em que o SAF-T do mês anterior é gerado automaticamente — o prazo legal (Portaria 302/2016). |
| `saft_recipient_email` | Data (Email) | — | Só relevante quando `saft_communication_method = "Email (Contabilista)"`. |

### 10.2. Geração — `utils/saft_scheduler.py`

`ensure_monthly_saft_generated()`, registada em `scheduler_events["daily"]` (hooks.py). Só
atua no dia configurado em `saft_send_day`; gera o SAF-T do **mês anterior** para cada empresa
portuguesa com compliance ativo. Idempotente: não cria um segundo log se já existir um para a
mesma empresa/período (`Pending`, `In Progress` ou `Completed`) — seguro correr todos os dias,
e seguro voltar a correr no mesmo dia.

Não duplica lógica de geração: cria apenas o registo `SAF-T Export Log`
(`export_type="Invoicing"`, `export_reason="Monthly Submission"`), reutilizando o fluxo real já
existente e validado (`after_insert` → `saft_generator.generate_saft_background`, secção 3
acima) — o mesmo caminho que um utilizador percorre manualmente pela UI.

> **Armadilha já apanhada uma vez**: `bench migrate` corre a sincronização de fixtures
> *antes* de `after_migrate`. Se um `Print Format` ou `Custom Field` fixture-tracked
> (`module="Portugal Compliance"`) for editado na DB sem correr `bench export-fixtures`
> logo a seguir, a próxima migração reverte-o silenciosamente para o estado antigo — mesmo
> que um marcador de "já está correto" continue presente. Não é específico do SAF-T, mas
> foi descoberto a testar esta funcionalidade: qualquer alteração deste tipo tem de ser
> seguida de `bench export-fixtures` **antes** do próximo `bench migrate`, nunca depois.

### 10.3. Envio por Email — `_send_saft_export_email()`

Chamada em `saft_generator.py::generate_saft_background()`, imediatamente a seguir a
`status="Completed"`. Só dispara quando **ambas** as condições se verificam:

1. `export_log.export_reason == "Monthly Submission"` — a única razão usada pela geração
   automática mensal; um export ad-hoc (`Audit Request`, `System Test`, regeneração manual de
   um período qualquer) nunca vai parar à caixa de correio do contabilista sem essa intenção
   explícita.
2. `Portugal Auth Settings.saft_communication_method == "Email (Contabilista)"`.

Assunto: `SAF-T (Faturação) - {Empresa} - {Mês}/{Ano}` (reutiliza
`get_month_name_portuguese()` de `jinja_methods.py`, mesma convenção dos Print Formats). Corpo
HTML simples, cita o número de certificado real (nunca hardcoded). Anexa o XML gerado
diretamente da memória (`saft_xml`), sem reler do disco.

**Resiliência (best-effort, por desenho)**: todo o passo de email está dentro do seu próprio
`try/except`, isolado do fluxo principal — uma falha (SMTP não configurado, servidor da
empresa em baixo, etc.) fica só registada no Error Log, nunca reverte nem marca como `Failed`
um SAF-T já gerado e validado com sucesso. O ficheiro fica sempre disponível para download
manual. Verificado ao vivo: sem nenhuma Conta de Email de saída configurada, a geração
completa normalmente e o envio falha exatamente como esperado
(`frappe.exceptions.OutgoingEmailError`), sem afetar o export. Com uma conta real configurada,
o email é injetado corretamente na fila (`Email Queue`) do Frappe.

---

## 11. Estrutura de Ficheiros

| Ficheiro | Função |
| :--- | :--- |
| [utils/saft_generator.py](portugal_compliance/utils/saft_generator.py) | Classe `SAFTGenerator` — coleta de dados, render, hash, contagem de registos; `generate_saft_background()` (job) e `_send_saft_export_email()` (secção 10.3). |
| [utils/saft_scheduler.py](portugal_compliance/utils/saft_scheduler.py) | `ensure_monthly_saft_generated()` — geração automática mensal, secção 10.2. |
| [doctype/saf_t_export_log/saf_t_export_log.py](portugal_compliance/portugal_compliance/doctype/saf_t_export_log/saf_t_export_log.py) | `validate_xml_content()` — validação XSD 1.1 real; `submit_to_at()` — sempre `NotImplementedError` (secção 10). |
| [templates/saft_t/main.xml](portugal_compliance/templates/saft_t/main.xml) | Composição dos 3 blocos (Header/MasterFiles/SourceDocuments). |
| [templates/saft_t/header.xml](portugal_compliance/templates/saft_t/header.xml) | Cabeçalho: empresa, `TaxAccountingBasis`, ano fiscal. |
| [templates/saft_t/master_files.xml](portugal_compliance/templates/saft_t/master_files.xml) | Customers, Suppliers, Products, TaxTable. |
| [templates/saft_t/source_documents.xml](portugal_compliance/templates/saft_t/source_documents.xml) | SalesInvoices, Payments. |
| [xsd/saftpt1.04_01.xsd](portugal_compliance/xsd/saftpt1.04_01.xsd) | Schema oficial da AT, bundled. |
| [api/saft_api.py](portugal_compliance/api/saft_api.py) | Endpoints whitelisted: gerar, listar, descarregar. |

---

## 12. Resolução de Problemas

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| `status="Failed"`, `xml_validation_status="Invalid"` | O XML gerado viola o schema real | Ler `xsd_validation_errors` — cada linha traz `[caminho XPath] motivo`. |
| Validação parece sempre passar mesmo com XML claramente errado | `xmlschema.XMLSchema` (1.0) usado em vez de `XMLSchema11` | O schema da AT exige 1.1 (`vc:minVersion="1.1"`) — sob 1.0 o root nem é reconhecido, mascarando tudo. |
| `PaymentType` reporta "RC" numa empresa que não está no regime de Caixa | `cash_vat_scheme` desligado (omissão) mas o código antigo usava Receive/Pay | Confirmar `Portugal Auth Settings.cash_vat_scheme`; código atual já não depende do sentido do pagamento. |
| `download_saft_file` devolve `{"status": "error", "message": "Export not completed"}` | Export com `status` diferente de `"Completed"` (ainda `In Progress` ou `Failed`) | Verificar `SAF-T Export Log` — um export inválido nunca fica disponível para download por desenho. |
| `GeneralLedgerEntries` ausente do ficheiro | Não é um erro — `TaxAccountingBasis="F"` | Só exigido sob base `C`/`I` (contabilidade integrada), fora do âmbito atual do módulo. |
| Faturas de fornecedor aparecem na tabela de Suppliers mas não em SourceDocuments | Comportamento correto — Purchase Invoice só popula masterdata | Ver Pilar 5 em [manual_funcionalidades_compliance.md](manual_funcionalidades_compliance.md). |
| Soma das linhas de uma fatura não bate com o total do documento no SAF-T | Desconto global (`additional_discount_amount`) só refletido em `net_amount`/`base_net_amount`, não em `amount`/`base_amount` | Corrigido nesta versão — ver secção 6.2. Confirmar que a instalação já tem a correção (`get_sales_invoices_data` a usar `base_net_amount`). |
| Totais do SAF-T não batem com os valores mostrados no documento em moeda estrangeira | Query usava campos de moeda de transação em vez de `base_*` (moeda base/EUR) | Corrigido nesta versão — ver secção 6.1. O SAF-T exige sempre EUR, independentemente da moeda de emissão da fatura. |
| SAF-T mensal não é gerado automaticamente no dia esperado | `saft_send_day` não é o dia de hoje, ou nenhuma empresa portuguesa tem compliance ativo | `ensure_monthly_saft_generated()` só atua no dia configurado — verificar `Portugal Auth Settings.saft_send_day`. |
| Email ao contabilista nunca chega, sem erro visível | `saft_communication_method` não está em "Email (Contabilista)", ou o export não tem `export_reason="Monthly Submission"` | Verificar as duas condições na secção 10.3 — um export manual/ad-hoc nunca envia email por desenho, não é um bug. |
| Email falha com `OutgoingEmailError` | Sem Conta de Email de saída (`enable_outgoing=1`) configurada no site | Configurar em Definições > Contas de Email. A geração do SAF-T não é afetada — o ficheiro continua disponível para download manual. |

---

**Nota Legal**: o ficheiro SAF-T (PT) referente a um mês deve ser submetido até ao dia 5 do
mês seguinte à emissão dos documentos, salvo prazo diferente comunicado pela AT. Este módulo
gera, valida e (opcionalmente, secção 10.3) envia o ficheiro por email ao contabilista — a
submissão em si é sempre manual, por upload no Portal das Finanças (`e-fatura`). Não existe
nenhum webservice da AT para automatizar este último passo (secção 10) — `submit_to_at()`
lança sempre `NotImplementedError`, por desenho, não por lacuna a preencher.
