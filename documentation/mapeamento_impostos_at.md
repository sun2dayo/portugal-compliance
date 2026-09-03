# Mapeamento de Impostos AT (SAF-T PT)

> **Estado:** espelho do código em produção em 2026-09-03.
> **Âmbito:** este documento explica **o mecanismo** — como qualquer imposto configurado no módulo `portugal_compliance` se traduz para a estrutura do SAF-T PT (Portaria n.º 302/2016) e para o QR Code de fatura (Portaria n.º 195/2020). É um documento **técnico e genérico**, válido para qualquer instalação.
>
> Não confundir com [`tax_mapping_template.md`](tax_mapping_template.md), que é o **modelo de declaração por instalação** (checklist a preencher com os valores concretos de uma empresa específica antes de submeter à certificação). Os dois documentos complementam-se: este explica o motor; o outro é o formulário que se preenche com o resultado desse motor numa instalação real.
>
> **Regra de ouro seguida na elaboração:** nenhuma tabela, código ou nome de função abaixo foi inventado — todos foram confirmados por leitura direta do código-fonte listado em cada secção. Onde o código tem um comentário explicando uma decisão de desenho, esse comentário foi preservado em português próprio (não citação literal) para dar o contexto correto.

---

## 1. Mecanismo de Tradução (Arquitetura)

O mapeamento assenta inteiramente na **conta contabilística (`Account`)**, nunca na percentagem da taxa em si. A percentagem é apenas um dado de referência humano — o código AT, a região fiscal e o tipo de imposto vivem sempre na conta, e todo o resto do sistema (Item Tax Template, linha de documento, QR Code, SAF-T) resolve **através** dela.

### 1.1. Onde a taxonomia AT é gravada

`portugal_compliance/setup/tax_setup.py` acrescenta 5 Custom Fields à doctype `Account`:

| Campo | Tipo | Opções | Objetivo |
|---|---|---|---|
| `at_tax_type` | Select | `IVA` / `IS` | Distingue uma conta de IVA de uma conta de Imposto do Selo (ver secção 4) |
| `at_tax_region` | Select | `PT` / `PT-AC` / `PT-MA` | Praça fiscal AT da conta (`TaxCountryRegion` no SAF-T) |
| `at_tax_code` | Select | `NOR` / `INT` / `RED` / `ISE` | Código de taxa AT (`TaxCode` no SAF-T), só visível quando `at_tax_type == "IVA"` |
| `at_stamp_duty_verba` | Data (texto livre) | — | Verba da Tabela Geral do Imposto do Selo, só visível quando `at_tax_type == "IS"` |
| `at_withholding_tax_type` | Select | `IRS` / `IRC` / `IS` | Tipo de retenção na fonte, para contas usadas em retenção (independente de `at_tax_type`) |

Estas contas nunca são as contas genéricas do plano de contas nativo do ERPNext — o módulo cria sub-contas SNC dedicadas por região e por taxa (`_get_or_create_snc_tax_account` em `tax_setup.py`), sob os grupos-pai:

- `2433` — Continente (`PT`)
- `2434` — Madeira (`PT-MA`)
- `2435` — Açores (`PT-AC`)

### 1.2. Da conta ao template fiscal

`setup_tax_templates_for_company(company, region)` (chamada pela ativação zero-touch e por `create_regional_tax_setup_for_company`, que a repete para as 3 regiões) cria, por cada taxa de `AT_TAX_TAXONOMY[region]` (ver secção 2):

1. A conta SNC da taxa (se ainda não existir), já com `at_tax_type`/`at_tax_region`/`at_tax_code` preenchidos;
2. Um **Sales Taxes and Charges Template** (`title = "IVA {taxa}% {rótulo}{sufixo região} - {empresa}"`), com uma única linha `On Net Total` ligada a essa conta — é este que aparece no cabeçalho de fatura/documento;
3. Um **Item Tax Template** com o mesmo título e a mesma conta em `tax_type` — é este que se liga a um artigo específico quando uma linha precisa de uma taxa diferente da do cabeçalho.

Tudo isto é idempotente (verificado por `title`+`company`, nunca pela chave primária, porque o `autoname()` nativo destas doctypes acrescenta sempre o `abbr` da empresa ao nome).

### 1.3. Do template à linha do documento — resolução em tempo real

`portugal_compliance/utils/tax_breakdown.py` é o módulo único de resolução, partilhado entre a validação de motivo de isenção (`document_hooks.py`), o QR Code (`jinja_methods.py`) e o SAF-T (`saft_generator.py`) — para os três nunca poderem divergir sobre "qual é o código AT desta linha":

- `get_account_at_info(account_names)` — uma query só, devolve `{conta: {code, region, tax_type, verba}}`. Conta sem `at_tax_region` preenchido (anterior a 2026-08-24) assume `PT`; sem `at_tax_type` assume `IVA`.
- `get_item_tax_template_info(template_names, account_info_cache)` — resolve o código/região de um Item Tax Template através da sua própria linha (`Item Tax Template Detail.tax_type`, que é o **nome da conta**), reaproveitando o cache de contas já carregado.
- `get_line_at_tax_info(doc)` — para cada linha de `doc.items`, a ordem de resolução é:
  1. Código/região do **Item Tax Template do próprio artigo**, se existir e resolver um código válido (`NOR`/`INT`/`RED`/`ISE`);
  2. Senão, código/região da **primeira linha de `doc.taxes`** (o template de cabeçalho) que resolva um código válido — o mesmo caminho de recurso é usado tanto para "artigo sem template" como para "template sem código resolvível", propositadamente sem dois caminhos distintos;
  3. Senão, o valor fixo `{"code": "NOR", "region": "PT"}`.
- `get_line_at_tax_codes(doc)` — atalho de `get_line_at_tax_info()` só com o código, usado pela validação de isenção.
- `get_tax_breakdown_by_at_code(doc)` — discrimina base tributável (de `item.net_amount`, nunca de `tax_amount`/taxa, para não acumular erro de arredondamento) e imposto liquidado (de `doc.taxes`, a fonte oficial) por código AT **e** por região, para os campos I1-I8/J1-J8/K1-K8 do QR Code e para a `TaxTable` do SAF-T. Inclui uma reconciliação: se a soma discriminada não bater com `total_taxes_and_charges` do documento (±0,01), fica registado em Error Log — não bloqueia a submissão, mas sinaliza um mapeamento incompleto para investigação.

### 1.4. Da linha ao XML do SAF-T

`saft_generator.py` usa exatamente as mesmas funções de `tax_breakdown.py` (via os fechos internos `_line_region`/`_line_tax_code`/`_line_tax_type`, definidos em `get_sales_invoices_data()`) para preencher, por linha (`templates/saft_t/source_documents.xml`):

```xml
<Tax>
    <TaxType>{{ item.tax_type or 'IVA' }}</TaxType>
    <TaxCountryRegion>{{ item.tax_region or 'PT' }}</TaxCountryRegion>
    <TaxCode>{{ item.tax_code }}</TaxCode>
    <TaxPercentage>{{ '%.2f'|format(item.tax_percentage or 0) }}</TaxPercentage>
</Tax>
```

`_line_tax_code()` só cai numa classificação por **faixa de percentagem** (`_get_line_tax_code`: ≤0% → `ISE`, <10% → `RED`, <20% → `INT`, restante → `NOR`) quando não existe conta/template AT associável de todo — ou seja, para contas legadas anteriores ao campo `at_tax_region` (2026-08-24). Esta classificação por faixa foi identificada como uma fonte real de erro: a taxa Normal dos Açores (16%) cairia na faixa "Intermédia" (<20%) do Continente se dependesse só da percentagem — por isso é sempre o último recurso, nunca o caminho principal.

A `TaxTable` do ficheiro mestre (`master_files.xml`, alimentada por `get_tax_table_data()`) segue a mesma lógica: código real da conta quando disponível, faixa de percentagem só como reserva para contas legadas.

---

## 2. Tabela de Códigos de Imposto (TaxCode)

Fonte: `AT_TAX_TAXONOMY` em `portugal_compliance/setup/tax_setup.py`. É esta tabela, e só esta, que gera as contas SNC e os templates fiscais de cada empresa portuguesa — nada é gerado fora dela.

| Nome no ERPNext (título do template) | TaxType (AT) | Região (AT) | TaxCode (AT) | Taxa (%) |
|---|---|---|---|---|
| IVA 23% Normal - `{empresa}` | IVA | PT | NOR | 23 |
| IVA 13% Intermédia - `{empresa}` | IVA | PT | INT | 13 |
| IVA 6% Reduzida - `{empresa}` | IVA | PT | RED | 6 |
| IVA 0% Isenta - `{empresa}` | IVA | PT | ISE | 0 |
| IVA 22% Normal PT-MA - `{empresa}` | IVA | PT-MA | NOR | 22 |
| IVA 12% Intermédia PT-MA - `{empresa}` | IVA | PT-MA | INT | 12 |
| IVA 5% Reduzida PT-MA - `{empresa}` | IVA | PT-MA | RED | 5 |
| IVA 0% Isenta PT-MA - `{empresa}` | IVA | PT-MA | ISE | 0 |
| IVA 16% Normal PT-AC - `{empresa}` | IVA | PT-AC | NOR | 16 |
| IVA 9% Intermédia PT-AC - `{empresa}` | IVA | PT-AC | INT | 9 |
| IVA 4% Reduzida PT-AC - `{empresa}` | IVA | PT-AC | RED | 4 |
| IVA 0% Isenta PT-AC - `{empresa}` | IVA | PT-AC | ISE | 0 |

`{empresa}` é substituído pelo nome real da empresa no título do Sales Taxes and Charges Template / Item Tax Template (ex.: `"IVA 23% Normal - NovaDX"`). Estas 12 combinações são criadas para **todas** as empresas portuguesas com compliance ativo — as 3 regiões são sempre provisionadas, independentemente de a empresa operar de facto nas ilhas (é a existência de dados reais nessa região num documento, não a mera existência do template, que faz o QR Code/SAF-T reportarem J/K além de I — ver secção 1.3).

---

## 3. Gestão de Isenções (IVA a 0%)

### 3.1. Motivos de isenção oficiais carregados

`portugal_compliance/fixtures/at_tax_exemption.json` carrega, como registos da doctype `AT Tax Exemption`, os 8 motivos abaixo (Portaria n.º 302/2016):

| Código | Descrição |
|---|---|
| M01 | Isento Artigo 14.º do RITI |
| M02 | Isento Artigo 6.º do Decreto-Lei n.º 198/90, de 19 de Junho |
| M04 | Isento Artigo 13.º do CIVA |
| M05 | Isento Artigo 14.º do CIVA |
| M07 | Isento Artigo 9.º do CIVA |
| M10 | Isento Artigo 53.º do CIVA |
| M11 | Regime de renúncia à isenção (Artigo 12.º do CIVA) |
| M99 | Não sujeito ou não tributado / autoliquidação |

### 3.2. Onde o motivo é registado — ao nível da linha, nunca do documento

O campo `at_exemption_reason` (`Link` para `AT Tax Exemption`, `depends_on`/obrigatoriedade tratada por código, não pelo motor de validação nativo) existe em **três** doctypes de linha, por dois mecanismos diferentes:

| Doctype da linha | Mecanismo de registo |
|---|---|
| `Sales Invoice Item` | `EXEMPTION_REASON_FIELD` em `tax_setup.py::create_at_tax_custom_fields()` |
| `Delivery Note Item` | idem |
| `POS Invoice Item` | `fixtures/custom_field.json` (registo direto, desde sempre — nunca dependeu de `tax_setup.py`) |

Ser um campo `Link` (e não texto livre) garante por si só que só é possível preencher um dos 8 códigos oficiais acima — a integridade referencial é imposta pelo próprio motor do Frappe, sem validação adicional necessária para esse aspeto.

O motivo é sempre **por linha**, nunca por documento: um documento pode legitimamente ter linhas tributadas e linhas isentas em simultâneo, cada uma com o seu próprio motivo (ou nenhum, se tributada).

### 3.3. Validação — aviso brando vs. bloqueio rígido

`document_hooks.py` define duas funções, ambas usando `get_line_at_tax_codes()` de `tax_breakdown.py` como única fonte de verdade sobre "esta linha é isenta?", aplicadas às doctypes `Sales Invoice`, `POS Invoice` e `Delivery Note`:

- **`_validate_tax_exemption_soft`** (hook `validate`, corre em todo o `save`, incluindo rascunhos): usa `frappe.msgprint(..., indicator="orange", alert=True)` — **nunca bloqueia**. Avisa em dois casos: linha a 0% sem motivo preenchido, ou linha com IVA > 0% mas com motivo preenchido por engano.
- **`_validate_tax_exemption_hard`** (hook `before_submit`): usa `frappe.throw(...)` — **bloqueia a submissão** nos mesmos dois casos. Um documento fiscal submetido é imutável e legalmente vinculativo, por isso só aqui a exigência é rígida.

> **Nota histórica:** `POS Invoice` só foi acrescentado a esta tupla em 2026-08-30. O campo `at_exemption_reason` já existia em `POS Invoice Item` desde sempre (fixture) e a interface já deixava preenchê-lo — mas nem a validação branda nem a rígida verificavam de facto este doctype antes dessa correção, apesar de o hook `before_submit` já estar ligado para `POS Invoice` exatamente como para `Sales Invoice`. Era um documento fiscal a passar sem a mesma exigência que uma fatura normal.

### 3.4. Legenda impressa — namespace de correspondência garantida

`register_exemption_note(item, exemption_notes)` e `render_exemption_legend(exemption_notes)`, também em `tax_breakdown.py`, são a única fonte de verdade para a numeração `(1)`, `(2)`... impressa junto a cada linha isenta e na legenda ao fundo do documento:

- Um Print Format declara `{% set exemption_notes = namespace(codes=[]) %}` antes do ciclo de linhas;
- Por cada linha, `register_exemption_note(item, exemption_notes)` lê `item.at_exemption_reason`; se preenchido, acrescenta o código à lista (se ainda não lá estiver) e devolve `<sup>(n)</sup>` — `n` é sempre a posição do código na lista, garantindo que a mesma isenção usa sempre o mesmo número dentro do mesmo documento;
- `render_exemption_legend(exemption_notes)` gera o bloco final `"(n) M0x - <descrição>"` por código distinto, pela mesma ordem/numeração.

Por partilharem o mesmo `namespace` e a mesma função de leitura do campo, a legenda impressa nunca pode divergir do que foi de facto preenchido linha a linha — não há dois pontos de verdade separados para "o que a fatura mostra" e "o que foi validado".

### 3.5. Emissão no XML do SAF-T

Em `templates/saft_t/source_documents.xml`, `TaxExemptionReason`/`TaxExemptionCode` só são emitidos **dentro da `Line`**, como irmãos de `Tax` (não filhos), e só quando `item.tax_percentage == 0`:

```xml
{% if item.tax_percentage == 0 %}
<TaxExemptionReason>{{ item.tax_exemption_reason or 'Isento' }}</TaxExemptionReason>
<TaxExemptionCode>{{ item.tax_exemption_code or 'M99' }}</TaxExemptionCode>
{% endif %}
```

`item.tax_exemption_code`/`tax_exemption_reason` vêm diretamente de `row.at_exemption_reason` (código) e da `description` do respetivo `AT Tax Exemption` (texto) — geradas em `saft_generator.py::get_sales_invoices_data()`. O recurso a `'Isento'`/`'M99'` quando o campo está vazio é, na prática, inatingível para Faturas/Faturas Simplificadas/Guias de Remessa emitidas por este módulo, porque `_validate_tax_exemption_hard` já bloqueou a submissão de qualquer linha a 0% sem motivo — existe apenas como rede de segurança do gerador de SAF-T em si.

Para os **recibos/pagamentos** (secção `Payments` do SAF-T), quando a referência a uma fatura isenta o exige, o motivo é sempre o literal fixo `M99` — porque o imposto real, quando existe, já foi liquidado e reportado na fatura de origem (referenciada em `SourceDocumentID`), nunca no recibo.

---

## 4. Imposto do Selo (IS) e Outros

**Não existe, atualmente, nenhuma verba do Imposto do Selo pré-configurada** neste módulo — ao contrário do IVA (secção 2), onde as 12 combinações de taxa/região/código são criadas automaticamente, não há nenhuma "tabela de verbas TGIS" equivalente carregada por omissão. A razão é estrutural: a Tabela Geral do Imposto do Selo tem dezenas de verbas (juros, garantias, seguros, operações financeiras, etc.), cada uma aplicável a um tipo de operação muito específico do negócio de cada empresa — ao contrário das 4 taxas de IVA, que são universais.

O que **existe** é o mecanismo genérico já pronto para receber essa configuração, reutilizando exatamente o mesmo pipeline do IVA:

1. O administrador cria uma `Account` normal (`account_type = "Tax"`), tal como as contas SNC do IVA — não precisa de estar sob `2433`/`2434`/`2435`, essas são específicas de IVA;
2. Define `at_tax_type = "IS"` nessa conta — isto por si só faz `at_tax_code` (a classificação NOR/INT/RED/ISE, que não se aplica a Imposto do Selo) desaparecer do formulário e revela `at_stamp_duty_verba`;
3. Preenche `at_stamp_duty_verba` com a verba real aplicável (texto livre — ex.: `"1.1"`, `"17.3.1"`), conforme a Tabela Geral do Imposto do Selo;
4. Usa essa conta num Sales Taxes and Charges Template / Item Tax Template exatamente como faria para uma conta de IVA — não há nenhum código especial de "modo Imposto do Selo" a ativar em mais lado nenhum: `get_account_at_info()`, `get_line_at_tax_info()` e a extração do SAF-T já leem `at_tax_type`/`at_stamp_duty_verba` de qualquer conta, sem distinguir a origem.

No SAF-T, `saft_generator.py::_line_tax_code()` trata este caso explicitamente:

```python
if info.get("tax_type") == "IS":
    # Imposto do Selo: o código é a verba da TGIS
    # (at_stamp_duty_verba, texto livre), nunca a
    # classificação NOR/INT/RED/ISE de IVA. "OUT" (Outro)
    # é o código de reserva do XSD quando a verba ainda
    # não foi configurada na conta.
    return info.get("verba") or "OUT"
```

Ou seja: **sem verba configurada, o TaxCode exportado é `"OUT"`** — um valor tecnicamente válido no XSD do SAF-T, mas que qualquer contabilista/inspetor identificará de imediato como "por configurar". Não há bloqueio de submissão associado a isto (ao contrário da isenção de IVA, secção 3.3) — é responsabilidade do administrador configurar a verba antes de uma conta de Imposto do Selo entrar em uso real.

### 4.1. Retenção na fonte (campo relacionado, não é Imposto do Selo em si)

`at_withholding_tax_type` (Select `IRS`/`IRC`/`IS`) é um campo independente de `at_tax_type`, para contas usadas em linhas de `Sales Taxes and Charges` com o campo nativo `is_tax_withholding_account=1`. Não há correspondência automática possível a partir da configuração nativa do ERPNext (Tax Withholding Category) — cada conta de retenção tem de ser marcada manualmente. `saft_generator.py::_withholding_tax_rows()` só popula `WithholdingTaxType` no XML quando este campo está preenchido (é opcional no XSD).

---

## 5. Regras de Validação

| Regra | Tipo | Hook | Doctypes | Efeito |
|---|---|---|---|---|
| Linha a 0% sem `at_exemption_reason` | Aviso | `validate` (`_validate_tax_exemption_soft`) | Sales Invoice, POS Invoice, Delivery Note | `msgprint` laranja, não bloqueia — corre em cada gravação, incl. rascunhos |
| Linha com IVA > 0% mas com `at_exemption_reason` preenchido | Aviso | `validate` (`_validate_tax_exemption_soft`) | idem | idem |
| Linha a 0% sem `at_exemption_reason` | Bloqueio | `before_submit` (`_validate_tax_exemption_hard`) | idem | `frappe.throw` — impede a submissão |
| Linha com IVA > 0% mas com `at_exemption_reason` preenchido | Bloqueio | `before_submit` (`_validate_tax_exemption_hard`) | idem | `frappe.throw` — impede a submissão |
| `at_exemption_reason` só pode ser um código oficial | Integridade referencial | Motor nativo do Frappe (campo `Link`) | Sales Invoice Item, POS Invoice Item, Delivery Note Item | Impossível gravar um código fora da tabela `AT Tax Exemption` |
| Soma discriminada por código+região ≠ `total_taxes_and_charges` | Deteção (não bloqueia) | Chamada interna de `get_tax_breakdown_by_at_code()` (QR Code / SAF-T) | Qualquer documento com discriminação AT | Registo em Error Log para investigação; o QR/SAF-T são gerados na mesma com o melhor mapeamento disponível |

A validação de isenção é deliberadamente **por linha**, nunca por documento ou por empresa: um único documento pode misturar linhas tributadas e isentas, cada uma com o seu próprio código de motivo — validar ao nível do cabeçalho do documento permitiria uma linha isenta sem motivo desde que outra linha do mesmo documento estivesse corretamente preenchida.

---

## Referências de código (para auditoria)

- `portugal_compliance/setup/tax_setup.py` — taxonomia, contas SNC, templates fiscais, Custom Fields
- `portugal_compliance/utils/tax_breakdown.py` — resolução por linha, discriminação QR/SAF-T, legenda de isenções
- `portugal_compliance/utils/document_hooks.py` — `_validate_tax_exemption_soft`/`_validate_tax_exemption_hard`
- `portugal_compliance/utils/saft_generator.py` — extração para XML (`_line_tax_code`, `_line_tax_type`, `_line_region`, `get_tax_table_data`)
- `portugal_compliance/templates/saft_t/source_documents.xml`, `master_files.xml` — emissão XML
- `portugal_compliance/fixtures/at_tax_exemption.json` — motivos de isenção oficiais
- `portugal_compliance/fixtures/custom_field.json` — `at_exemption_reason` em `POS Invoice Item`

Para a declaração de configuração fiscal de uma instalação concreta (valores reais de uma empresa, checklist de certificação), preencher [`tax_mapping_template.md`](tax_mapping_template.md) usando este documento como base técnica.
