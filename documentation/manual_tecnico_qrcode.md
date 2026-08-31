# Manual Técnico: Código QR (Portaria n.º 195/2020)

**Versão:** 1.1.0

Este manual detalha a implementação do código de barras bidimensional (QR Code) legalmente
obrigatório em documentos fiscais portugueses, conforme a Especificação Técnica — Código QR
(Portaria n.º 195/2020, v1.1, Outubro 2020). Cobre a construção da string, o mapeamento exato
campo a campo, o tratamento de múltiplas praças fiscais, e a injeção nos Print Formats
térmico e A4.

---

## 1. Natureza do Conteúdo

O QR Code **não** é um link — é uma string de texto estruturada, formato `Campo:Valor`,
concatenada com `*`:

```
A:518747832*B:500000000*C:PT*D:FT*E:N*F:20260822*G:FT FT2026N/19*H:AAJFJD3KRX-0019*
I1:PT*I2:0.00*I3:0.00*I4:0.00*I5:0.00*I6:0.00*I7:200.00*I8:46.00*
N:246.00*O:246.00*P:0*Q:pSUo*R:FT2026N
```

*(exemplo real, capturado de `FT2026N0019`, novadx)*

---

## 2. Função Geradora: `get_qr_code_data()`

[utils/jinja_methods.py](portugal_compliance/utils/jinja_methods.py). Assinatura:

```python
def get_qr_code_data(doctype=None, docname=None, doc=None):
```

Aceita um `doc` já carregado (uso interno, print formats) **ou** `doctype`+`docname` (uso via
API), caso em que busca sempre o documento autoritativo do servidor e verifica permissão —
nunca confia num `doc` vindo do cliente:

```python
if doctype and docname:
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Sem permissão para gerar o QR Code deste documento"), frappe.PermissionError)
    doc = frappe.get_doc(doctype, docname)
```

Isto fecha a mesma classe de vulnerabilidade IDOR já corrigida em `regenerate_atcud` — um QR
Code contém NIF e totais, é um artefacto legal, e nunca deve ser gerado a partir de dados
fornecidos pelo cliente sem revalidação server-side.

A string final é construída filtrando campos vazios (respeitando a regra da especificação de
nunca criar um campo opcional sem informação):

```python
qr_string = "*".join([f"{key}:{value}" for key, value in qr_data.items() if value])
```

> **Ordem importa.** `qr_data` é um dicionário Python — a partir da versão 3.7 preserva ordem
> de inserção. Os campos são inseridos na ordem exata A→R exigida pela especificação; alterar
> a ordem de inserção no código altera a ordem no QR Code final.

---

## 3. Mapeamento de Campos A–R

| Campo | Conteúdo | Origem no código | Obrig. |
| :--- | :--- | :--- | :--- |
| `A` | NIF do emitente | `get_company_nif(doc.company)` | + |
| `B` | NIF do adquirente | `get_customer_nif(doc)` ou `get_supplier_nif(doc)`; `999999990` para Consumidor Final | + |
| `C` | **País** do adquirente (não o emitente) | `get_customer_country(doc)` — ver secção 3.1 | + |
| `D` | Código real do documento | `get_document_at_code(doc)` — ver secção 3.2 | + |
| `E` | Estado (`N`=Normal, `A`=Anulado) | Fixo `"N"` (o QR só é gerado para documentos ativos) | + |
| `F` | Data, `YYYYMMDD` | `doc.posting_date` | + |
| `G` | Identificação única | `get_document_ref_no(doc)` — ver secção 3.3 | + |
| `H` | ATCUD | `get_atcud_code(doc)` | + |
| `I1`/`J1`/`K1` | Código da praça fiscal (`PT`/`PT-AC`/`PT-MA`) | Ver secção 4 | + (I1), ++ (J/K) |
| `I2`-`I8` etc. | Base/imposto por taxa, na praça correspondente | Ver secção 4 | ++ |
| `N` | Total de impostos | `document_total` | + |
| `O` | Total do documento | `document_total` (Payment Entry usa `paid_amount`, não `grand_total`) | + |
| `P` | Retenção na fonte | Fixo `"0"` | ++ |
| `Q` | 4 caracteres de controlo da assinatura | `get_signature_hash_control(doc)` | + |
| `R` | Identificador da série | `get_series_prefix(doc)` | ++ |

### 3.1. Campo `C` — País do Adquirente

```python
def get_customer_country(doc):
    address_name = getattr(doc, 'customer_address', None) or _dynamic_link_lookup(doc)
    if address_name:
        country_name = frappe.db.get_value("Address", address_name, "country")
        code = frappe.db.get_value("Country", country_name, "code")  # ex: "pt" -> "PT"
        if code:
            return code.upper()
    return "PT"  # default domestico, nao ha "adquirente desconhecido" para este campo
```

`Address.country` guarda o nome completo ("Portugal"), não o código ISO — daí o lookup extra
à tabela `Country`. **Defeito corrigido**: uma versão anterior preenchia este campo com o
**nome da empresa emitente**, não com o país do cliente — um campo obrigatório do QR Code
estava semanticamente errado em todas as faturas.

### 3.2. Campo `D` — Código Real do Documento

```python
def get_document_at_code(doc):
    prefix = get_series_prefix(doc)          # ex: "NC2026N"
    match = re.match(r"^([A-Z]{2,4})", prefix)
    if match:
        return match.group(1)                 # "NC"
    return get_document_type_code(doc.doctype)  # fallback estático
```

**Defeito corrigido**: a versão anterior usava `get_document_type_code(doc.doctype)` — um
mapeamento estático por DocType do Frappe, que devolve sempre `"FT"` para qualquer Sales
Invoice, **mesmo uma Nota de Crédito** (mesma DocType, série diferente). Confirmado ao vivo:
`NC2026N0001` imprimia `D:FT` — uma afirmação legal falsa sobre o tipo de documento. A
correção extrai o código real do prefixo da série efetivamente usada, a mesma convenção já
usada em `at_webservice.py` para separar série de ano/empresa.

### 3.3. Campo `G` — Identificação Única

```python
def get_document_ref_no(doc):
    doc_code = get_document_at_code(doc)
    prefix = get_series_prefix(doc)
    match = re.match(r"^(.*?)(\d+)$", doc.name)
    series_part, sequence_number = match.groups() if match else (doc.name, 0)
    return f"{doc_code} {prefix or series_part}/{int(sequence_number)}"
```

Formato exigido: `"CÓDIGO SÉRIE/SEQUÊNCIA"` (ex: `"FT FT2026N/19"`, `"NC NC2026N/1"`) —
idêntico ao exemplo oficial da especificação (`G:FT AB2019/0035`). **Defeito corrigido**: a
versão anterior usava `doc.name` diretamente (`"FT2026N0019"`), sem espaço nem barra — não
batia com o formato exigido.

### 3.4. Campo `B` — NIF do Adquirente e o Fallback para Consumidor Final (2026-08-24)

```python
customer_nif = get_customer_nif(doc) or get_supplier_nif(doc) or "999999990"
```

**Defeito corrigido**: `get_customer_nif(doc)`/`get_supplier_nif(doc)` devolvem `""` quando o
Cliente/Fornecedor não tem `tax_id` preenchido — cenário comum em vendas de retalho/POS a
consumidor final, onde pedir o NIF não é obrigatório. Antes desta correção, o campo `B` ficava
vazio nesses casos; a Especificação Técnica - Código QR (Portaria 195/2020) exige o NIF
genérico **"Consumidor Final" `999999990`**, nunca um campo vazio. O `or` só atua quando as
duas chamadas anteriores devolvem `""` — um NIF real (B2B) nunca é substituído, testado ao vivo
atribuindo temporariamente um NIF a um Customer e confirmando que o campo `B` refletia esse
valor sem interferência do *fallback*.

Mesma convenção já aplicada, de forma independente, em dois outros pontos do módulo:
`CustomerTaxID` no SAF-T (`saft_generator.py`, via `{{ customer.tax_id or '999999990' }}` no
template `master_files.xml`) e `CustomerTaxID` no registo em tempo real à AT
(`at_invoice_webservice.py`/`at_transport_webservice.py`, via `doc.tax_id or "999999990"`).
Note-se que `999999990` passa validamente o algoritmo de módulo 11 por construção (dígitos
`9×8` somam um resto 0, dígito de controlo `0`) — não precisa de exceção no validador de NIF
(`Portugal Auth Settings` › **Validar NIF**, ver
[manual_tecnico_schema_dados.md](manual_tecnico_schema_dados.md)), que já o ignora
explicitamente por comparação direta da string, não por confiar nesse resultado do cálculo.

---

## 4. Praça Fiscal: Continente, Açores, Madeira

### 4.1. Estrutura I/J/K

A especificação prevê até **três** praças fiscais no mesmo QR Code — `I1`-`I8` para a
primeira, `J1`-`J8` para a segunda, `K1`-`K8` para a terceira, cada bloco com a mesma
estrutura interna:

```python
region_letters = [("I", "PT"), ("J", "PT-AC"), ("K", "PT-MA")]
for letter, region in region_letters:
    bucket = regions.get(region)
    if not bucket:
        continue
    qr_data[f"{letter}1"] = region
    qr_data[f"{letter}2"] = f"{bucket['ISE']['base']:.2f}"
    qr_data[f"{letter}3"] = f"{bucket['RED']['base']:.2f}"
    qr_data[f"{letter}4"] = f"{bucket['RED']['tax']:.2f}"
    qr_data[f"{letter}5"] = f"{bucket['INT']['base']:.2f}"
    qr_data[f"{letter}6"] = f"{bucket['INT']['tax']:.2f}"
    qr_data[f"{letter}7"] = f"{bucket['NOR']['base']:.2f}"
    qr_data[f"{letter}8"] = f"{bucket['NOR']['tax']:.2f}"
```

> **Ordem dentro do bloco**: isenta → reduzida → intermédia → normal (posições 2-8), **não**
> a ordem NOR/INT/RED/ISE usada internamente pelo motor de cálculo — uma inversão real
> encontrada nesta auditoria (o campo `I1` continha uma base tributável em vez do código da
> praça, e a atribuição base/imposto por taxa não batia com a ordem real do formulário da AT).

Só `I` (Continente) é sempre presente — o QR Code exige pelo menos um espaço fiscal. `J`/`K`
só aparecem quando há dados reais de Açores/Madeira no documento.

### 4.2. Fonte da Região: `tax_breakdown.py`

[utils/tax_breakdown.py](portugal_compliance/utils/tax_breakdown.py),
`get_tax_breakdown_by_at_code(doc)` — módulo **partilhado** entre o QR Code, a `TaxTable`
mestra do SAF-T e a validação de motivo de isenção, para que os três nunca dessincronizem
sobre "que taxa e que região se aplica a esta linha":

```python
def get_account_at_info(account_names):
    rows = frappe.get_all("Account", filters={"name": ["in", list(account_names)]},
                           fields=["name", "at_tax_code", "at_tax_region"])
    return {r.name: {"code": r.at_tax_code, "region": r.at_tax_region or "PT"} for r in rows}
```

A região é lida diretamente do campo `Account.at_tax_region` (populado na criação das contas
SNC regionais em `setup/tax_setup.py` — contas dedicadas para Continente/2433, Madeira/2434,
Açores/2435), **nunca adivinhada a partir da percentagem de imposto**: duas praças fiscais
podem partilhar a mesma taxa numérica hoje, ou convergir no futuro, sem que isso as torne a
mesma praça.

Resolução por linha, com o mesmo padrão de *fallback* usado para o código de taxa: código do
Item Tax Template do próprio artigo; se ausente, cai na primeira linha de `doc.taxes` que
resolva um código válido:

```python
def get_line_at_tax_info(doc):
    account_info = get_account_at_info({r.account_head for r in doc.taxes if r.account_head})
    header_fallback = next((account_info[r.account_head] for r in doc.taxes
                             if account_info.get(r.account_head, {}).get("code") in VALID_AT_CODES), None)
    template_info = get_item_tax_template_info(template_names, account_info)
    return {item.name: template_info.get(item.item_tax_template) or header_fallback or {"code": "NOR", "region": "PT"}
            for item in doc.items}
```

### 4.3. `TaxTable` do SAF-T — Mesma Fonte

```python
# get_tax_table_data() em saft_generator.py
SELECT DISTINCT at.rate, at.description, a.at_tax_region AS region
FROM `tabAccount` a INNER JOIN `tabSales Taxes and Charges` at ON at.account_head = a.name
WHERE a.company = %s AND a.account_type = 'Tax' AND a.is_group = 0
```

```xml
<TaxCountryRegion>{{ tax.region }}</TaxCountryRegion>
```

E, por linha de fatura em `SourceDocuments`, a mesma resolução estrutural
(`get_account_at_info`/`get_item_tax_template_info`, tornadas públicas precisamente para
serem partilhadas entre `tax_breakdown.py` e `saft_generator.py`) — nunca uma segunda lógica
paralela baseada em faixas de percentagem.

> **Limitação conhecida**: `Payment/Line/Tax/TaxCountryRegion` (recibos, distinto da linha de
> fatura) mantém-se fixo em `"PT"` — o bloco de imposto de um recibo é sempre a isenção fixa
> `M99` (sem taxa própria, herda o imposto já liquidado na fatura de origem), pelo que herdar
> a região do documento de origem referenciado é uma alteração a implementar à parte.

---

## 5. Persistência: `qr_code` / `qr_code_image`

A geração do QR Code persistido faz parte de `generate_atcud_on_submit` (hook `on_submit`,
[document_hooks.py](portugal_compliance/utils/document_hooks.py) — até 2026-08-24 era uma
função separada, `generate_and_attach_qr_code`, chamada em `after_insert`; foi absorvida na
mesma função que assina o documento, já que ambas só fazem sentido depois de o ATCUD existir,
e o ATCUD só existe a partir do submit). Chama `get_qr_code_data(doc=doc)` e
`generate_qr_code_image()` (biblioteca `qrcode`, PNG Base64) e grava ambos no próprio
documento:

```python
qr_string = get_qr_code_data(doc=doc)
doc.db_set("qr_code", qr_string, update_modified=False)
qr_image = generate_qr_code_image(qr_string, 280)
doc.db_set("qr_code_image", qr_image, update_modified=False)
```

Isto **não** substitui o cálculo em tempo de impressão — os Print Formats continuam a chamar
`get_qr_code_data(doc=doc)` diretamente (secção 6), sempre com os dados mais recentes. Os
campos persistidos servem o painel de estado da UI e qualquer inspeção/auditoria futura ao
documento sem necessidade de o reimprimir.

> **Nota de arquitetura — segundo gerador de QR Code.**
> [utils/atcud_generator.py](portugal_compliance/utils/atcud_generator.py) contém uma
> **segunda** implementação independente de construção do QR Code
> (`_build_qr_data_optimized()`, chamada de `generate_atcud_for_document()` em todo
> `before_save`/`after_insert`), com o mesmo defeito de mapeamento de campos já corrigido em
> `get_qr_code_data()`. O valor que produz só é escrito em `ATCUD Log.qr_code_string` (pista
> de auditoria interna) — não é lido pelo webservice da AT nem pelos Print Formats reais, que
> usam `get_qr_code_data()` diretamente. Sem impacto no que é comunicado à AT ou impresso;
> inconsistência da trilha de auditoria a corrigir num commit dedicado.

---

## 6. Injeção nos Print Formats

### 6.1. A4 (`Factura PT`)

```jinja
{% set qr_data = get_qr_code_data(doc=doc) %}
{% if qr_data %}
<table style="width: 32mm; ...">
  <tr><td style="width: 32mm; height: 32mm; ...">
    <!-- imagem gerada inline via generate_qr_code_image -->
  </td></tr>
</table>
{% endif %}
```

Chamado diretamente do template Jinja do Print Format — não depende do campo persistido
`qr_code_image`, gera sempre fresco no momento da impressão/PDF.

### 6.2. Térmico (`Fatura Simplificada PT`)

Mesma chamada `get_qr_code_data(doc=doc)`, layout dimensionado para largura de rolo térmico
(58mm/80mm) em vez de A4 — o mesmo motor gerador serve os dois formatos; a diferença é
exclusivamente de **layout** (dimensões, posição, tipografia), nunca de dados.

### 6.3. Rodapé Legal

Ambos os formatos incluem, junto ao QR Code, o número de certificado do software e o ATCUD:

```jinja
Processado por programa informático certificado n.º
{{ frappe.db.get_single_value("Portugal Auth Settings", "software_certificate_number") or "0" }}/AT
{% if frappe.db.get_single_value("Portugal Auth Settings", "sandbox_mode") %} — AMBIENTE DE TESTES, sem valor fiscal.{% endif %}
```

Lê sempre `Portugal Auth Settings` diretamente (nunca um valor hardcoded ou cacheado) — e
inclui um aviso adicional de "AMBIENTE DE TESTES" quando o módulo está em modo sandbox, para
que um PDF gerado em testes nunca seja confundível com um documento fiscal real.

---

## 7. Estrutura de Ficheiros

| Ficheiro | Função |
| :--- | :--- |
| [utils/jinja_methods.py](portugal_compliance/utils/jinja_methods.py) | `get_qr_code_data()`, `generate_qr_code_image()`, `get_customer_country()`, `get_document_at_code()`, `get_document_ref_no()`. |
| [utils/tax_breakdown.py](portugal_compliance/utils/tax_breakdown.py) | Discriminação por código de taxa e praça fiscal — fonte partilhada com o SAF-T. |
| [utils/document_hooks.py](portugal_compliance/utils/document_hooks.py) | `generate_atcud_on_submit` (hook `on_submit`) — persistência em `doc.qr_code`/`qr_code_image`, a seguir à assinatura. |
| [fixtures/print_format.json](portugal_compliance/fixtures/print_format.json) | Os Print Formats reais (`Factura PT`, `Fatura Simplificada PT`, `Fatura Simplificada PT (A4)`, `Recibo PT`, `Guia de Transporte PT`, `Guia de Transporte Valorizada PT`, `Talão POS PT`) — não os ficheiros em `templates/print_formats/*.html`, que não são referenciados por nenhum código (ver Nota Metodológica em [manual_funcionalidades_compliance.md](manual_funcionalidades_compliance.md)). |

---

## 8. Resolução de Problemas

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| Campo `C` mostra o nome da empresa em vez de um código de país | Código antigo lia `doc.company` | Corrigido — usa `get_customer_country(doc)`. |
| `D:FT` numa Nota de Crédito real | Mapeamento estático por DocType, não por série | Corrigido — usa `get_document_at_code(doc)`, extraído do prefixo da série real. |
| `I1` contém um valor monetário | Estrutura de campos desalinhada desde a origem | Corrigido — `I1`/`J1`/`K1` são sempre o código da praça (`"PT"` etc.), nunca um total. |
| QR Code não aparece no PDF | Print Format errado selecionado, ou `qr_data` vazio (documento sem ATCUD) | Confirmar Print Format ativo em `Portugal Auth Settings`/Property Setter `default_print_format`; confirmar que o documento tem `atcud_code`. |
| `ATCUD Log.qr_code_string` não bate com o QR impresso | Segundo gerador em `atcud_generator.py` (ver secção 5) | Sem impacto no impresso/comunicado — a inconsistência é só na pista de auditoria interna. |
| Valores a zero em `J`/`K` mesmo havendo vendas em Açores/Madeira | Conta de imposto usada na linha sem `at_tax_region` preenchido | Confirmar que a conta SNC regional (`setup/tax_setup.py`) foi criada e associada ao Item Tax Template correto. |
