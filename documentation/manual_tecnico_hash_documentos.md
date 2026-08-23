# Manual Técnico: Hashing e Assinatura Digital de Documentos

> A integridade do ficheiro SAF-T e do ATCUD depende matematicamente da correção da hash.
> Uma diferença de 1 segundo na data-sistema, ou 1 espaço a mais na referência, produz uma
> assinatura diferente — sem invalidar a submissão, mas sem coincidir com o que um verificador
> externo recalcularia a partir dos mesmos dados.

---

## 1. Algoritmo

Imposto pela Portaria n.º 363/2010: **RSA-SHA1**, padding **PKCS#1 v1.5**.

```python
signature_bytes = private_key.sign(data_to_sign.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1())
signature_hash = base64.b64encode(signature_bytes).decode("ascii")
```

Chave privada RSA, formato PEM, tamanho determinado pela chave efetivamente configurada em
`Portugal Auth Settings.invoice_signing_key_path` (o módulo não impõe nem valida um tamanho
mínimo/máximo de chave — é uma responsabilidade de provisionamento, não de runtime).

---

## 2. Regras de Encadeamento (Chaining)

Cada documento assina uma string que inclui a hash Base64 do documento **anterior da mesma
série**.

* Primeiro documento da série → `HashAnterior = ""` (vazio).
* Segundo documento em diante → `HashAnterior` = `signature_hash` do documento imediatamente
  anterior, **na mesma série**.
* **Nunca** misturar séries — a hash anterior de um `RG2026N/2` tem de vir de `RG2026N/1`,
  nunca de outra série, mesmo que cronologicamente mais recente.

### 2.1. Concorrência — `SELECT ... FOR UPDATE`

```python
def _lock_series_for_signing(series_configuration):
    frappe.db.sql(
        "SELECT name FROM `tabPortugal Series Configuration` WHERE name = %s FOR UPDATE",
        series_configuration,
    )
```

Adquirido **antes** de ler a hash anterior, dentro de `get_previous_signature_hash()`. Sem
isto: dois documentos da mesma série submetidos quase em simultâneo correm em transações
separadas (o padrão de pedidos HTTP do Frappe/gunicorn); o segundo pode ler a "última hash"
antes do primeiro ter feito `COMMIT`, e ambos ficariam com a mesma `HashAnterior` — quebrando
a sequencialidade exigida por lei. O lock é libertado apenas no `COMMIT` da transação
completa (não logo após a leitura), cobrindo também a escrita do `ATCUD Log` em
`after_insert` do primeiro pedido.

> A alocação do **número de sequência** em si (`doc.name`) já é segura pelo contador atómico
> nativo do Frappe — o lock aqui protege especificamente a leitura da hash anterior, um
> problema distinto e adicional.

---

## 3. Composição da String de Dados (`data_to_sign`)

Formato fixo: `"DataDoc;DataSistema;Referencia;Total;HashAnterior"`. Os campos exatos por
tipo de documento vêm de `DOCUMENT_SIGNING_SPEC`
([utils/signature.py](portugal_compliance/utils/signature.py)):

```python
DOCUMENT_SIGNING_SPEC = {
    "Sales Invoice":    {"doc_code": "FT", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": "grand_total", "total_absolute": True},
    "Purchase Invoice": {"doc_code": "FC", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": "grand_total", "total_absolute": True},
    "POS Invoice":      {"doc_code": "FS", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": "grand_total", "total_absolute": True},
    "Payment Entry":    {"doc_code": "RC", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": "paid_amount", "total_absolute": True},
    "Delivery Note":    {"doc_code": "GT", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": None, "total_absolute": False},   # guias: Total fixo "0.00"
    "Purchase Receipt": {"doc_code": "GR", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": None, "total_absolute": False},
    "Stock Entry":      {"doc_code": "GM", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": None, "total_absolute": False},
    "Journal Entry":    {"doc_code": "LC", "date_field": "posting_date", "system_date_field": "creation",
                          "total_field": "total_debit", "total_absolute": True},
}
```

> **Âmbito real vs. spec declarado.** Só `Sales Invoice`, `POS Invoice`, `Payment Entry` e
> `Delivery Note` estão em `FISCAL_IMMUTABLE_DOCTYPES` e têm `sign_document()` efetivamente
> chamado via `hooks.py`. As entradas `Purchase Invoice`, `Purchase Receipt`, `Stock Entry` e
> `Journal Entry` continuam na especificação (a função `get_signing_spec()` é genérica e
> funcionaria se chamada), mas **não são alcançadas** por nenhum `doc_events` — mantidas aqui
> por referência histórica/futura extensão, não por uso corrente.

### 3.1. Tabela por Tipo de Documento

| Campo | Sales Invoice / POS Invoice | Payment Entry | Delivery Note |
| :--- | :--- | :--- | :--- |
| **DataDoc** | `posting_date` → `YYYY-MM-DD` | `posting_date` → `YYYY-MM-DD` | `posting_date` → `YYYY-MM-DD` |
| **DataSistema** | `creation` → `YYYY-MM-DDTHH:MM:SS` | `creation` → `YYYY-MM-DDTHH:MM:SS` | `creation` → `YYYY-MM-DDTHH:MM:SS` |
| **Referencia** | `"FT SERIE/SEQ"` ou `"NC SERIE/SEQ"` (código real da série) | `"RC SERIE/SEQ"` (⚠️ ver Nota A) | `"GT SERIE/SEQ"` (⚠️ ver Nota B) |
| **Total** | `abs(grand_total)`, 2 casas decimais | `abs(paid_amount)`, 2 casas decimais | Fixo `"0.00"` |
| **HashAnterior** | Hash Base64 do documento anterior da mesma série | idem | idem |

> **Nota A — `doc_code` estático "RC" para Payment Entry.** `DOCUMENT_SIGNING_SPEC` não
> distingue RG (Outros recibos) de RC (Regime de IVA de Caixa) — usa sempre `"RC"` no campo
> `Referencia` da string assinada, independentemente do `document_code` real da série
> (`RG` por omissão desde a correção documentada em
> [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md), secção 5). O
> `series_prefix` passado a `sign_document()` **é** sempre o real (ex: `"RG2026N"`) — só o
> `doc_code` prefixado ao início da `Referencia` fica estático. Resultado: a `Referencia`
> embutida na assinatura de um recibo real neste sistema é `"RC RG2026N/1"` — o código e o
> prefixo da série não coincidem dentro do conteúdo assinado. Não invalida a assinatura (é só
> texto de entrada), mas é uma inconsistência real a corrigir.

> **Nota B — mesma classe de inconsistência em Delivery Note.** `doc_code` estático `"GT"`,
> enquanto o `document_code` real da série de Delivery Note comunicada neste sistema é
> `"GR"` (Guia de Remessa — ver `at_transport_webservice.py::_document_code_for`). A
> `Referencia` assinada de uma Guia real é `"GT GR2026N/1"` — mesmo padrão de defeito da Nota
> A, encontrado ao escrever este manual, ainda por corrigir.

### 3.2. Notas de Crédito

Notas de Crédito (`Sales Invoice` com `is_return=1`) seguem exatamente a mesma lógica das
Faturas — mesmo DocType, mesma tabela, mesma função de assinatura. O que muda é o `doc_code`
usado na `Referencia`, que **neste caso está correto** porque `build_data_to_sign()` recebe
`series_prefix` real e o chamador (`ATCUDGenerator`) já resolve o `doc_code` real via
`Portugal Series Configuration` antes de invocar `sign_document()` para Sales Invoice — a
inconsistência das Notas A/B acima é específica de Payment Entry/Delivery Note, não de Sales
Invoice/Nota de Crédito.

> **Total sempre absoluto/positivo.** Uma Nota de Crédito tem valores negativos no ERPNext
> (`grand_total < 0`); a assinatura usa sempre `abs()` — o sentido (crédito/estorno) é
> comunicado pelo `InvoiceType="NC"` e pelo `DebitAmount`/`CreditAmount` por linha no SAF-T,
> nunca por um total negativo dentro da string assinada.

---

## 4. Hash Control (4 Caracteres)

```python
def _extract_hash_control(signature_b64):
    positions_1_indexed = (1, 11, 21, 31)
    return "".join(signature_b64[p - 1] for p in positions_1_indexed if p - 1 < len(signature_b64))
```

Os caracteres nas posições 1, 11, 21 e 31 (1-indexed) da assinatura Base64 completa — este
valor de 4 caracteres é o que aparece:

* No campo `Q` do QR Code (ver
  [manual_tecnico_qrcode.md](manual_tecnico_qrcode.md)).
* No campo `HashCharacters` do payload de `RegisterInvoice` (comunicação em tempo real, ver
  [manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md)).

**Nunca** é a hash completa — confundir os dois foi um erro real só detetado ao ler a
estrutura exata do WSDL de faturas.

---

## 5. Persistência: `ATCUD Log`

Um registo por documento fiscal assinado — nunca guardado na própria tabela do documento
(`tabSales Invoice` etc.), sempre no DocType dedicado, um-para-um:

| Campo | Conteúdo |
| :--- | :--- |
| `document_type` / `document_name` | Referência ao documento original |
| `series_used` | Link para `Portugal Series Configuration` |
| `sequence_number` | Sequência dentro da série |
| `atcud_code` | `validation_code-sequência` |
| `signature_hash` | Assinatura RSA-SHA1 completa, Base64 |
| `previous_signature_hash` | Hash do documento anterior da mesma série |
| `signature_hash_control` | Os 4 caracteres (secção 4) |
| `signing_key_version` | `Portugal Auth Settings.invoice_signing_key_version` no momento da assinatura — auditoria de rotação de chave |
| `qr_code_string` | ⚠️ Produzido por um gerador de QR Code **diferente** do usado na impressão real — ver [manual_tecnico_qrcode.md](manual_tecnico_qrcode.md), secção 5 |
| `generation_status` | `Success` / `Failed` / `Pending` / `Retrying` — só entradas `Success` participam na verificação de cadeia |

---

## 6. Verificação e Recuperação

### 6.1. Verificação a Posteriori — `verify_signature_chain()`

Ver detalhe completo em
[manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md), secção 4. Em resumo:
percorre `ATCUD Log` por série, confirma continuidade (`previous_signature_hash` bate com o
documento anterior) e valida criptograficamente cada assinatura contra a chave pública
derivada da chave privada atual.

### 6.2. Não Existe Ferramenta de Reparação Automática de Cadeia

Ao contrário do módulo de referência (que inclui um script "Series-Aware" de recálculo em
lote de hashes quebradas), este módulo **não** oferece uma ferramenta de reparação automática
da cadeia — e deliberadamente não deveria: se um documento fiscal já submetido tivesse a sua
hash recalculada retroativamente, isso invalidaria a prova de que a assinatura original
correspondia ao estado do documento no momento da emissão, contrariando o próprio propósito
da inviolabilidade (Pilar 1). Uma cadeia quebrada detetada por `verify_signature_chain()` é
um **achado de auditoria** a investigar (documento alterado fora do fluxo normal? backup
parcial restaurado? bug num commit específico?), não um estado a "corrigir" apagando a
evidência.

---

## 7. Estrutura de Ficheiros

| Ficheiro | Função |
| :--- | :--- |
| [utils/signature.py](portugal_compliance/utils/signature.py) | `DOCUMENT_SIGNING_SPEC`, `build_data_to_sign()`, `sign_document()`, `_lock_series_for_signing()`, `verify_signature_chain()`. |
| [utils/atcud_generator.py](portugal_compliance/utils/atcud_generator.py) | Orquestração — chama `sign_document()`, persiste `ATCUD Log`. |
| [doctype/atcud_log/atcud_log.py](portugal_compliance/portugal_compliance/doctype/atcud_log/atcud_log.py) | Controller do log — retry de persistência pendente (`persist_pending_atcud_log`). |
