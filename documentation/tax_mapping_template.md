# Tabela de Mapeamento de Impostos (Declaração)

**Empresa:** [Nome da Empresa]
**Software:** ERPNext / Frappe — Módulo `portugal_compliance`
**Data:** [Data]

Esta tabela identifica a correspondência entre as contas de imposto configuradas no ERP e a
taxonomia SAF-T (PT) (Portaria n.º 321-A/2007, Despacho n.º 8632/2014). Ao contrário de uma
tabela de mapeamento independente e editável livremente, os três campos **Código SAF-T**,
**Região** e **Motivo de Isenção** vêm de um Custom Field dedicado em cada `Account` do
ERPNext (`at_tax_code`, `at_tax_region`, `at_exemption_reason`) — esta declaração é um
**relatório** do estado real dessa configuração, gerado a partir das contas efetivamente
criadas, não um ficheiro de configuração paralelo a manter sincronizado à mão.

---

## 1. Taxas Padrão por Região (`AT_TAX_TAXONOMY`)

Provisionadas automaticamente por
[setup/tax_setup.py](portugal_compliance/setup/tax_setup.py) — só **Continente** é criado
por omissão na ativação do compliance português numa empresa; Madeira e Açores ficam
disponíveis a pedido, via `create_regional_tax_setup_for_company()`.

| ID Interno (conta SNC) | Descrição | Taxa (%) | Código SAF-T | Tipo Imposto | Região | Motivo Isenção |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `2433.1 - IVA Normal` | IVA Normal (Continente) | **23.00** | **NOR** | IVA | PT | — |
| `2433.2 - IVA Intermédia` | IVA Intermédia (Continente) | **13.00** | **INT** | IVA | PT | — |
| `2433.3 - IVA Reduzida` | IVA Reduzida (Continente) | **6.00** | **RED** | IVA | PT | — |
| `2433.4 - IVA Isenta` | IVA Isenta (Continente) | **0.00** | **ISE** | IVA | PT | *(ver secção 3 — obrigatório por linha)* |
| `2434.1 - IVA Normal Madeira` | IVA Normal (Madeira) | **22.00** | **NOR** | IVA | PT-MA | — |
| `2434.2 - IVA Intermédia Madeira` | IVA Intermédia (Madeira) | **12.00** | **INT** | IVA | PT-MA | — |
| `2434.3 - IVA Reduzida Madeira` | IVA Reduzida (Madeira) | **5.00** | **RED** | IVA | PT-MA | — |
| `2434.4 - IVA Isenta Madeira` | IVA Isenta (Madeira) | **0.00** | **ISE** | IVA | PT-MA | *(ver secção 3)* |
| `2435.1 - IVA Normal Açores` | IVA Normal (Açores) | **16.00** | **NOR** | IVA | PT-AC | — |
| `2435.2 - IVA Intermédia Açores` | IVA Intermédia (Açores) | **9.00** | **INT** | IVA | PT-AC | — |
| `2435.3 - IVA Reduzida Açores` | IVA Reduzida (Açores) | **4.00** | **RED** | IVA | PT-AC | — |
| `2435.4 - IVA Isenta Açores` | IVA Isenta (Açores) | **0.00** | **ISE** | IVA | PT-AC | *(ver secção 3)* |

> **Prefixo da conta SNC por região** (`REGION_ACCOUNT_PREFIX`): Continente = `2433`,
> Madeira = `2434`, Açores = `2435` — blocos separados deliberadamente para nunca colidirem,
> em vez de reutilizar a conta genérica "Duties and Taxes" nativa do ERPNext.

> **[Preencher para a instalação real]**: confirmar via `bench execute` ou pela UI
> (Contabilidade → Plano de Contas → filtrar por "IVA") quais destas contas foram
> efetivamente criadas nesta empresa, e substituir/completar as taxas se a legislação em
> vigor no momento da instalação diferir das constantes acima (ex: taxas reduzidas
> transitórias, atualizações legais posteriores a 2026).

---

## 1bis. Imposto do Selo (IS) — Configuração Manual por Inquilino

Ao contrário da tabela da secção 1 (IVA, gerada automaticamente na ativação), **não existe
nenhuma verba de Imposto do Selo pré-configurada** — as verbas da TGIS aplicáveis dependem do
tipo de negócio de cada empresa, e não faria sentido assumir um código fiscal por omissão numa
instalação multi-inquilino (SaaS). Mecanismo pronto desde 2026-08-29 (`Account.at_tax_type` +
`Account.at_stamp_duty_verba`, ver [setup/tax_setup.py](portugal_compliance/setup/tax_setup.py))
— configuração fica a cargo de cada empresa/inquilino, documentado passo a passo em
[user_manual.md](user_manual.md), secção 4.2.

| Campo (`Account`) | Tipo | Preenchimento |
| :--- | :--- | :--- |
| `at_tax_type` | Select (`IVA`/`IS`) | `IS` para contas de Imposto do Selo |
| `at_stamp_duty_verba` | Texto livre | Verba TGIS real (ex: `"1.1"`, `"17.3.1"`) — sem valor por omissão |

**[Preencher para a instalação real]**: listar aqui as contas de IS efetivamente criadas
nesta empresa e a verba TGIS de cada uma, à medida que forem configuradas — mesmo princípio da
tabela da secção 1 (declaração do estado real, não um ficheiro de configuração paralelo).

| Conta | Verba TGIS | Descrição |
| :--- | :--- | :--- |
| *(nenhuma conta de IS configurada nesta instalação até à data)* | — | — |

> Sem verba configurada (`at_stamp_duty_verba` vazio), o SAF-T usa `"OUT"` (Outro) como código
> de reserva em vez de inventar uma verba — ver `saft_generator.py::_line_tax_code`.

---

## 2. Regime de IVA de Caixa

| Campo | Valor |
| :--- | :--- |
| **`Portugal Auth Settings.cash_vat_scheme`** | [ ] Ativo / [ ] Inativo *(preencher)* |
| **Impacto no SAF-T** | Determina `PaymentType` (`RC` se ativo, `RG` se inativo) em todos os recibos comunicados — ver [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md), secção 5 |
| **Impacto no código da série de Payment Entry** | `document_code` da série (`Portugal Series Configuration`) — confirmar se está alinhado com o valor acima; a AT cruza o `tipoDoc` do registo da série com o `PaymentType` do SAF-T mensal |

> Este campo é uma declaração factual sobre o enquadramento fiscal real da empresa junto da
> AT — nunca deve ser ativado apenas para "corresponder" a uma série já registada. Se a
> empresa não estiver genuinamente no regime de Caixa, o valor correto é **Inativo**
> (`RG`), independentemente do que uma série comunicada anteriormente possa já refletir.

---

## 3. Motivos de Isenção de IVA (`AT Tax Exemption`)

Taxonomia carregada como fixture — os códigos abaixo são os efetivamente disponíveis nesta
instalação (`AT Tax Exemption.code`), não um subconjunto arbitrário:

| Código | Descrição |
| :--- | :--- |
| **M01** | Isento Artigo 14.º do RITI |
| **M02** | Isento Artigo 6.º do Decreto-Lei n.º 198/90, de 19 de Junho |
| **M04** | Isento Artigo 13.º do CIVA |
| **M05** | Isento Artigo 14.º do CIVA (tipicamente exportações) |
| **M07** | Isento Artigo 9.º do CIVA |
| **M10** | Isento Artigo 53.º do CIVA (Regime de Isenção — pequenos retalhistas/pequenas empresas) |
| **M11** | Regime de renúncia à isenção (Artigo 12.º do CIVA) |
| **M99** | Não sujeito ou não tributado / autoliquidação — também usado internamente para o bloco `Tax` de recibos (Payment Entry), que nunca tem taxa própria |

### 3.1. Validação Automática

O sistema **valida** (não força automaticamente) o preenchimento do motivo de isenção sempre
que uma linha tem taxa 0% — dois níveis, ambos em
[utils/document_hooks.py](portugal_compliance/utils/document_hooks.py):

* `_validate_tax_exemption_soft` (hook `validate`) — aviso brando (`msgprint`), não bloqueia,
  corre em todo o save incluindo rascunhos.
* `_validate_tax_exemption_hard` (hook `before_submit`) — bloqueio rígido, impede a submissão
  de um documento com uma linha isenta (0%) sem motivo de isenção preenchido, ou com um
  motivo preenchido numa linha que afinal não é 0%.

> **Por que não é forçado automaticamente a nível de empresa**: um dropdown global "Regime de
> Isenção" que forçasse `M10` em todas as faturas seria perigoso — se a empresa tiver
> qualquer transação genuinamente tributável (ex: excede o limiar do Artigo 53.º, ou tem
> atividade mista), um override automático produziria uma declaração fiscal errada. A
> validação é sempre por linha, nunca por empresa. Ver
> [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md), secção 5.3.

---

## 4. Resolução por Documento — Código vs. Percentagem vs. Região

Três perguntas distintas, resolvidas por três mecanismos (documentados em
[manual_tecnico_qrcode.md](manual_tecnico_qrcode.md), secção 4):

| Pergunta | Resolvido por | Fonte |
| :--- | :--- | :--- |
| Qual a **categoria de taxa** (NOR/INT/RED/ISE) desta linha? | `get_line_at_tax_codes()` | `Item Tax Template` da linha → `Account.at_tax_code`, com *fallback* para a primeira linha de impostos do cabeçalho |
| Qual a **praça fiscal** (PT/PT-AC/PT-MA) desta linha? | `get_line_at_tax_info()` | Mesma cadeia, lendo `Account.at_tax_region` em vez de `at_tax_code` |
| Qual o **motivo de isenção**, se a taxa for 0%? | `_validate_tax_exemption_*` | Campo `at_exemption_reason` da própria linha do documento (`Sales Invoice Item.at_exemption_reason`), nunca inferido automaticamente |

**Nunca** por percentagem numérica isolada — duas contas em regiões diferentes podem
partilhar a mesma taxa nominal (coincidência atual ou futura convergência legal), e só a
`Account` associada determina inequivocamente código e região.

---

## 5. Checklist de Validação Antes de Submeter à Certificação

- [ ] Confirmar que todas as contas de imposto realmente usadas têm `at_tax_code` e
      `at_tax_region` preenchidos (não deixados em branco por omissão).
- [ ] Confirmar `Portugal Auth Settings.cash_vat_scheme` alinhado com o enquadramento real da
      empresa junto da AT.
- [ ] Gerar um SAF-T de teste e confirmar, na `TaxTable`, que a `TaxCountryRegion` de cada
      taxa reportada corresponde à tabela da secção 1 (ver
      [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md), secção 4).
- [ ] Confirmar que nenhum documento com linha isenta foi submetido sem motivo de isenção
      preenchido — a validação `before_submit` deveria já impedir isto, mas vale confirmar em
      dados históricos migrados de outro sistema (onde os hooks deste módulo nunca correram).
- [ ] Se a empresa opera em mais do que uma praça fiscal, confirmar que existe pelo menos um
      documento de teste com linhas em cada região, e que o QR Code gerado popula
      corretamente os blocos `J`/`K` (ver
      [manual_tecnico_qrcode.md](manual_tecnico_qrcode.md), secção 4.1).

---

**Nota Técnica**: esta tabela não substitui a validação automática do sistema (secção 3.1) —
é uma declaração formal do estado de configuração, útil para auditoria externa (AT,
contabilista certificado, ou processo de certificação de software) sem necessidade de aceder
diretamente à base de dados.
