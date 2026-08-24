# Manual Técnico: Séries Documentais, ATCUD e Assinatura Digital

**Versão:** 1.1.0

Este manual descreve o ciclo de vida completo de uma série documental — registo na AT,
assinatura criptográfica de cada documento, encadeamento de hash, geração do ATCUD, e as
operações de fecho (finalização e anulação). Complementa
[manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md)
(webservices) e [manual_tecnico_qrcode.md](manual_tecnico_qrcode.md) (impressão).

---

## 1. Visão Geral do Ciclo de Vida

```
registarSerie (AT) ──► Ativa ──┬──► finalizarSerie (AT) ──► Finalizada
                                └──► anularSerie (AT) ──────► Anulada
```

1. **Registo**: uma série é comunicada à AT (`registarSerie`), que devolve um **código de
   validação**, partilhado por todos os documentos dessa série.
2. **Emissão**: cada documento, ao ser submetido, é assinado com RSA-SHA1 e recebe um ATCUD =
   `código_de_validação-sequência`.
3. **Fecho**: a série pode ser formalmente **finalizada** (`finalizarSerie` — fim de uso
   legítimo, histórico preservado) ou **anulada** (`anularSerie` — desfaz um registo por
   erro, só possível no mesmo dia/dia seguinte e sem documentos emitidos).

**DocType**: `Portugal Series Configuration` — um registo por (empresa, DocType, prefixo):
`document_code`, `naming_series`, `prefix`, `current_sequence`, `is_active`,
`is_communicated`, `validation_code`, `communication_date`, `total_documents_issued`.

---

## 2. Fase 1 — Registo da Série (`registarSerie`)

### 2.1. Payload e Mapeamento de Classes

[utils/at_webservice.py](portugal_compliance/utils/at_webservice.py),
`ATWebserviceClient.register_naming_series()`. A AT valida rigorosamente a correspondência
entre `tipoDoc` (2-4 letras) e `classeDoc` (2 letras) — `_map_doc_code_to_class()`:

```python
DOC_CODE_TO_CLASS = {
    "FT": "SI", "FS": "SI", "FR": "SI", "NC": "SI", "ND": "SI",  # Sales Invoices
    "GT": "MG", "GR": "MG", "GD": "MG", "GC": "MG", "GM": "MG",  # Movement of Goods
    "RC": "PY", "RB": "PY", "RG": "PY",                          # Payments
}
```

Esta tabela foi extraída do módulo de referência Dolibarr (`complianceportugal`), já validado
em produção — a AT rejeita com erro **4045** ("O valor indicado na Classe do Documento deve
corresponder a um valor predefinido") qualquer classe inventada.

### 2.2. Formato do Identificador de Série

Confirmado contra o Manual de Integração de Software oficial da AT: máximo 35 caracteres,
apenas `[A-Za-z0-9._-]`, nunca iniciado por "AT" (reservado para programas da própria AT), sem
separadores consecutivos nem nas extremidades. Neste sistema, o formato usado é
`PREFIXO+ANO+EMPRESA` sem hífenes (ex: `FT2026N`, `RG2026N`) — validado localmente antes de
sequer contactar a AT:

```python
pattern = r'^([A-Z]{2,4})(\d{4})([A-Z0-9]{1,4})\.####$'  # naming_series
valid_doc_codes = ["FT","FS","FR","NC","ND","FC","RC","RG","RB","GT","GR","GM","JE","LC","OR","EC","EF","MR"]
```

### 2.3. Códigos de Retorno Confirmados em Sandbox

| Código | Significado | Confirmado ao vivo |
| :--- | :--- | :--- |
| `2001` | Série registada com sucesso, código de validação atribuído | Sim |
| `4001` | Série já registada para este tipo de documento | — |
| `4045` | Classe do documento inválida | Sim (durante o desenvolvimento do mapeamento) |
| `4046` | Tipo de documento não corresponde à classe indicada | — |

### 2.4. Armazenamento

```python
frappe.db.set_value("Portugal Series Configuration", doc.name, {
    "is_communicated": 1,
    "validation_code": result.get("validation_code"),
    "communication_date": frappe.utils.now(),
})
```

> **O código de validação é único por série**, não por documento — todos os documentos
> emitidos sob a mesma série partilham o mesmo `validation_code`; o que os distingue é a
> sequência.

### 2.5. Imutabilidade Pós-Comunicação (2026-08-24)

Assim que `is_communicated` passa a `1`, os campos que identificam a série perante a AT ficam
imutáveis — alterá-los depois de comunicada desalinharia a geração local do ATCUD do que a AT
validou em `registarSerie`, corrompendo a cadeia de assinatura sem que a AT tivesse
conhecimento da mudança. Bloqueio em duas camadas:

- **Client-side** (`portugal_series_configuration.js::enforce_communicated_series_
  immutability`, chamado no `refresh`): marca `read_only` os campos `company`,
  `document_type`, `prefix`, `naming_series`, `validation_code`, `at_environment`,
  `is_communicated`, `communication_date` e `is_active` quando `is_communicated === 1`. Só UX —
  não é a autoridade real.
- **Server-side** (`document_hooks.py::_enforce_communicated_series_immutability`, chamada a
  partir de `validate_series_configuration`): compara os mesmos 9 campos contra o estado
  imediatamente anterior à gravação (`doc.get_doc_before_save()`) e bloqueia com
  `frappe.throw()` se algum mudou — mas só quando o valor *anterior* de `is_communicated` já
  era `1`. A própria transição de `0` para `1` (a comunicação em si, feita pelo `frappe.db.
  set_value()` acima) nunca é bloqueada, porque nesse momento o valor anterior ainda é `0`.

`is_active` está incluído deliberadamente: o estado de uma série comunicada só deve mudar
através de **Finalizar Série na AT** ou **Anular Série na AT** (secção 5) — ambos gravam com
`frappe.db.set_value()` direto, nunca passam por `validate()`, por isso não ficam bloqueados
por este mecanismo.

---

## 3. Fase 2 — Assinatura Digital e ATCUD (Emissão)

### 3.1. Especificação de Assinatura por Tipo de Documento

[utils/signature.py](portugal_compliance/utils/signature.py), `DOCUMENT_SIGNING_SPEC` — um
dicionário estático por DocType, definindo os campos que compõem a string a assinar:

```python
DOCUMENT_SIGNING_SPEC = {
    "Sales Invoice": {"doc_code": "FT", "date_field": "posting_date", "system_date_field": "creation",
                       "total_field": "grand_total", "total_absolute": True},
    "Payment Entry": {"doc_code": "RC", "date_field": "posting_date", "system_date_field": "creation",
                       "total_field": "paid_amount", "total_absolute": True},
    "Delivery Note": {"doc_code": "GT", "date_field": "posting_date", "system_date_field": "creation",
                       "total_field": None, "total_absolute": False},  # guias: Total fixo "0.00"
    # ...
}
```

### 3.2. Construção da String a Assinar

`build_data_to_sign()` produz exatamente:

```
"DataDoc;DataSistema;Referencia;Total;HashAnterior"
```

```python
data_doc = getdate(doc.posting_date).strftime("%Y-%m-%d")
data_sistema = get_datetime(doc.creation).strftime("%Y-%m-%dT%H:%M:%S")
referencia = f"{spec['doc_code']} {series_prefix}/{sequence_number}"
total = f"{abs(flt(doc.grand_total)):.2f}"  # ou "0.00" para guias
return f"{data_doc};{data_sistema};{referencia};{total};{previous_hash or ''}"
```

Esta é a especificação de referência extraída do módulo Dolibarr (`complianceportugal`), já
validada contra rejeições reais da AT — replicada integralmente, não reinventada.

### 3.3. Assinatura RSA-SHA1

```python
private_key = _load_private_key()  # Portugal Auth Settings.invoice_signing_key_path
signature_bytes = private_key.sign(data_to_sign.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1())
signature_hash = base64.b64encode(signature_bytes).decode("ascii")
```

Chave privada RSA, formato PEM, carregada de `invoice_signing_key_path` — **distinta** da
chave usada para mTLS no webservice (ver
[manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md),
secção 2).

### 3.4. Encadeamento de Hash e Concorrência

`get_previous_signature_hash(series_configuration, before_sequence_number)` lê a assinatura do
documento imediatamente anterior da **mesma série** — vazio se for o primeiro. Antes de ler,
adquire um lock pessimista:

```python
def _lock_series_for_signing(series_configuration):
    frappe.db.sql(
        "SELECT name FROM `tabPortugal Series Configuration` WHERE name = %s FOR UPDATE",
        series_configuration,
    )
```

**Porquê é necessário**: a alocação do próprio número de sequência (`doc.name`) já é segura,
via o contador atómico nativo do Frappe. O problema é especificamente a leitura da *hash
anterior*: assinatura e persistência do `ATCUD Log` correm ambas dentro do mesmo hook
`on_submit` (`generate_atcud_on_submit`, ver 3.7), mas isso não elimina a janela de corrida —
se dois documentos da mesma série forem submetidos quase em simultâneo, o segundo pedido pode
ler a "última hash" **antes** de o primeiro ter terminado o commit da sua própria transação
(pedidos Frappe correm em transações separadas, cada uma só visível às outras após commit), e
os dois ficariam com a mesma `HashAnterior` — quebrando a cadeia sequencial exigida pela
Portaria 363/2010.

Ao bloquear a linha da série logo no início da assinatura, e só a libertar no commit da
transação (fim do pedido), o segundo pedido fica bloqueado na leitura até o primeiro terminar
por completo — incluindo a escrita do seu próprio `ATCUD Log`, feita pela mesma chamada a
`generate_atcud_on_submit` que gerou a assinatura.

### 3.5. Hash Control (4 caracteres)

```python
def _extract_hash_control(signature_b64):
    # posições 1, 11, 21, 31 (1-indexed) da assinatura Base64
    positions_1_indexed = (1, 11, 21, 31)
    return "".join(signature_b64[p - 1] for p in positions_1_indexed if p - 1 < len(signature_b64))
```

Este valor de 4 caracteres é o campo `Q` do QR Code (ver
[manual_tecnico_qrcode.md](manual_tecnico_qrcode.md)) e o campo `HashCharacters` no payload
de comunicação em tempo real de faturas — **não** a hash completa.

### 3.6. Geração do ATCUD

```
ATCUD = validation_code + "-" + sequência
```

Exemplo real, confirmado em teste: `AAJFJD3KRX-0019`. A sequência é extraída de `doc.name`
(o contador nativo do Frappe), nunca de um contador paralelo — a sua largura acompanha a do
próprio nome do documento (`0019`, não forçada a 8 dígitos), tal como softwares certificados
de mercado (Cegid Vendus, InvoiceXpress).

### 3.7. Persistência: `ATCUD Log`

Hook `on_submit` de cada DocType fiscal
([document_hooks.py](portugal_compliance/utils/document_hooks.py),
`generate_atcud_on_submit`) delega em
`ATCUDGenerator.generate_atcud_for_document(doc)`
([utils/atcud_generator.py](portugal_compliance/utils/atcud_generator.py)) para calcular a
assinatura, seguido de `persist_pending_atcud_log(doc)` para gravar o registo — ambos dentro da
mesma chamada, já com o documento definitivamente submetido (`docstatus=1`):

> **Nota histórica (correção de 2026-08-24)**: antes desta data, o cálculo da assinatura
> (`generate_atcud_before_save`) e a persistência do `ATCUD Log` (`generate_atcud_after_insert`)
> estavam divididos entre `before_save` e `after_insert` — ou seja, corriam em **qualquer**
> gravação de rascunho, não só na submissão final. Um documento que falhasse depois uma
> validação de negócio (ex.: motivo de isenção de IVA em falta, só verificado de forma rígida em
> `before_submit`) ficava com um ATCUD/assinatura reais já gravados num rascunho que nunca
> chegava a ser legalmente vinculativo — e `enforce_fiscal_field_lock` bloqueava depois qualquer
> tentativa de corrigir o campo em falta, prendendo o rascunho ("rascunho zombie": nem editável
> nem submetível). A divisão em duas fases existia apenas por uma restrição técnica do Frappe
> (o `ATCUD Log` tem uma Dynamic Link para o documento, que só é válida depois de o `db_insert`
> acontecer — e este só corre depois de `before_save`); como `on_submit` já corre sobre um
> documento com registo na BD há muito estabelecido (inserido no momento do primeiro rascunho),
> essa restrição deixou de se aplicar, e as duas fases foram unificadas numa só chamada.

Grava um registo por documento:

| Campo | Conteúdo |
| :--- | :--- |
| `atcud_code` | `validation_code-sequência` |
| `signature_hash` | Assinatura RSA-SHA1 completa (Base64) |
| `previous_signature_hash` | Hash do documento anterior da mesma série |
| `signature_hash_control` | Os 4 caracteres do campo `Q` |
| `sequence_number`, `series_used` | Para reconstrução da cadeia |
| `generation_status` | `Success` / `Failed` — só entradas `Success` contam para verificação |

---

## 4. Verificação da Cadeia (Auditoria a Posteriori)

`verify_signature_chain(series_configuration=None, company=None)`, whitelisted, percorre o
`ATCUD Log` por série, em sequência, e para cada documento:

1. Confirma que `previous_signature_hash` bate exatamente com a `signature_hash` do
   documento anterior da mesma série (continuidade da cadeia).
2. Reconstrói `data_to_sign` a partir do documento **atual** — só é seguro fazê-lo porque a
   inviolabilidade fiscal (`enforce_fiscal_field_lock`) garante que os campos usados na
   assinatura não puderam mudar desde que foi gerada.
3. Verifica a assinatura RSA contra a chave pública (`private_key.public_key().verify(...)`,
   `padding.PKCS1v15()`, `hashes.SHA1()`), capturando `InvalidSignature`.

```python
result = verify_signature_chain(company="novadx")
# {"success": bool, "series_checked": int, "documents_checked": int,
#  "broken_chains": int, "invalid_signatures": int, "series": {...}}
```

Nunca lança exceção por uma entrada inválida — continua a verificar o resto da cadeia,
registando o erro por documento, para que um único problema não impeça a auditoria do
restante.

`export_signing_public_key()`, também whitelisted, deriva e exporta em PEM a chave pública
correspondente à privada — sem necessidade de um campo de armazenamento próprio (a chave
pública é sempre derivável da privada já protegida), evitando duas cópias da mesma informação
a poderem divergir.

---

## 5. Fase 3 — Fecho de Série: Finalizar vs. Anular

Duas operações distintas, frequentemente confundidas:

| | `finalizarSerie` | `anularSerie` |
| :--- | :--- | :--- |
| **Semântica legal** | Encerramento formal de uma série **realmente usada** | Desfaz um registo **por erro**, como se nunca tivesse existido |
| **Pré-condição AT** | Série "Ativa" | Série "Ativa" **e** comunicada no próprio dia ou dia seguinte |
| **Documentos emitidos** | Pode (e normalmente tem) documentos emitidos | Exige atestar `declaracaoNaoEmissao=true` — **nenhum** documento pode ter sido emitido |
| **Estado final** | `Finalizada` (F) — histórico preservado | `Anulada` (N) — como se nunca tivesse sido comunicada |
| **Código de sucesso confirmado** | `2004` | `2003` |
| **Reversível?** | Não | Não |

### 5.1. Implementação

```python
def finalizar_serie(self, series_config_name, seq_ultimo_doc_emitido=None, justificacao=None, ...):
    response = service.finalizarSerie(serie=..., classeDoc=..., tipoDoc=...,
                                       codValidacaoSerie=series_config.validation_code,
                                       seqUltimoDocEmitido=..., justificacao=..., _soapheaders=[wsse_header])
    is_success = cod_result == 2004
    if is_success:
        frappe.db.set_value("Portugal Series Configuration", series_config_name, "is_active", 0)
```

```python
def anular_serie(self, series_config_name, declaracao_nao_emissao, motivo="ER", ...):
    if not declaracao_nao_emissao:
        return {"success": False, "error": _("É obrigatório confirmar que não foram emitidos documentos...")}
    # Pré-validação local do prazo de 1 dia, antes de gastar uma chamada à AT:
    dias = (frappe.utils.now_datetime().date() - get_datetime(series_config.communication_date).date()).days
    if dias > 1:
        return {"success": False, "error": _("Só é possível anular uma série comunicada no próprio dia ou no dia imediatamente anterior...")}
    response = service.anularSerie(..., motivo=motivo, declaracaoNaoEmissao=True, _soapheaders=[wsse_header])
    is_success = cod_result == 2003
    if is_success:
        frappe.db.set_value("Portugal Series Configuration", series_config_name,
                             {"is_active": 0, "is_communicated": 0, "validation_code": None})
```

O campo `motivo` de `anularSerie` **não é texto livre** — o XSD (`SAFTPTPaymentType`-análogo
para motivos de anulação) restringe a um código fixo de 2 caracteres; **"ER"** ("Anulação por
erro de registo") é o único valor documentado no Manual de Integração de Software da AT para
esta operação, e o único aplicável ao cenário legítimo de anulação.

### 5.2. Bloqueio Físico de Reutilização

Uma série finalizada ou anulada não pode voltar a ser usada — dois mecanismos independentes:

1. **UX**: `_setup_automatic_property_setters()` reconstrói o Property Setter de opções do
   campo `naming_series` para **todos** os DocTypes fiscais (mesmo os que ficam com lista
   vazia), removendo a série inativa do dropdown de imediato após `finalizar_serie`/
   `anular_serie` chamarem `_refresh_naming_series_options(company)`.
2. **Bloqueio real**: `_validate_series_not_inactive()`
   ([document_hooks.py](portugal_compliance/utils/document_hooks.py)), hook `validate` nos 4
   DocTypes fiscais — bloqueia com `frappe.throw` qualquer documento novo (ainda sem ATCUD)
   cuja série tenha `is_active=0`, com a mensagem: *"A série X está Finalizada/Anulada.
   Comunique uma nova série à AT antes de faturar."* Esta é a rede de segurança que não
   depende do Property Setter já ter sido reconstruído nem do cache de meta do worker estar
   atualizado.

Um documento já assinado quando a série ainda estava ativa (ex: a ser cancelado depois de a
série ter sido finalizada mais tarde) nunca é bloqueado por esta verificação — o `validate`
só atua sobre documentos sem `atcud_code` ainda.

---

## 6. Estrutura de Ficheiros

| Ficheiro | Função |
| :--- | :--- |
| [utils/signature.py](portugal_compliance/utils/signature.py) | Especificação de assinatura, `sign_document()`, `verify_signature_chain()`, `export_signing_public_key()`. |
| [utils/atcud_generator.py](portugal_compliance/utils/atcud_generator.py) | `ATCUDGenerator` — orquestra assinatura + sequência + persistência em `ATCUD Log`. |
| [utils/at_webservice.py](portugal_compliance/utils/at_webservice.py) | `registarSerie`, `consultarSeries`, `finalizarSerie`, `anularSerie` — `ATWebserviceClient`. |
| [utils/document_hooks.py](portugal_compliance/utils/document_hooks.py) | Hooks `on_submit`/`validate`/`before_submit` que disparam a geração (só em `on_submit`) e bloqueiam séries inativas/documentos com validações pendentes. |
| [doctype/atcud_log/atcud_log.py](portugal_compliance/portugal_compliance/doctype/atcud_log/atcud_log.py) | Controller do log — retry de persistência pendente. |
| [wsdl/Comunicacao_Series.wsdl](portugal_compliance/wsdl/Comunicacao_Series.wsdl) | Contrato SOAP oficial (`registarSerie`, `consultarSeries`, `finalizarSerie`, `anularSerie`). |

---

## 7. Resolução de Problemas

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| `anularSerie` recusado localmente antes de contactar a AT | Série comunicada há mais de 1 dia | Regra legal, não um bug — usar `finalizarSerie` se a série já foi usada, ou registar uma série nova. |
| Erro AT `4051` ("motivo de anulação deve corresponder a um valor pré-definido") | `motivo` enviado como texto livre | O único código documentado é `"ER"` — não é um campo de texto. |
| `verify_signature_chain` reporta `signature_ok: False` num documento antigo | Documento criado antes de `sign_document()` existir (sem assinatura real gerada) | Gap histórico, não recuperável — documentar como limitação conhecida, não "corrigir" retroativamente uma assinatura que nunca existiu. |
| Naming series de uma série anulada continua no dropdown do documento | `_setup_automatic_property_setters` não corre para um DocType que caiu a zero séries ativas | Confirmar que a versão em produção reconstrói **todos** os DocTypes fiscais, não só os que ainda têm série ativa. |
| ATCUD ausente num documento submetido | Série correspondente `is_active=0`, ou não comunicada (`is_communicated=0`) | `_validate_series_not_inactive` já bloqueia a submissão neste caso — o documento nunca deveria ter chegado a `submit` sem ATCUD. |
| Duas faturas da mesma série com a mesma `previous_signature_hash` | Corrida entre pedidos concorrentes sem o lock de série | Confirmar que `_lock_series_for_signing` corre **antes** da leitura, nunca depois — ver secção 3.4. |
