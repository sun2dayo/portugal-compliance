# Manual Técnico: Comunicação de Documentos em Tempo Real (AT)

Este documento descreve o canal alternativo, em tempo real, de comunicação de documentos
fiscais à Autoridade Tributária — distinto e complementar ao SAF-T mensal (ver
[manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md)). Cobre dois
webservices SOAP distintos: **Faturação** (`fatcorews`) e **Documentos de Transporte**
(`sgdtws`), ambos autenticados por mTLS + WS-Security.

Por omissão, uma instalação nova do módulo permanece em modo **Offline** (comunicação apenas
via SAF-T mensal) — o canal de tempo real é opt-in, ativado explicitamente em `Portugal Auth
Settings`, para que instalações existentes não sofram chamadas de rede novas sem
configuração deliberada.

---

## 1. Visão Geral dos Dois Webservices

| | Faturação | Documentos de Transporte |
| :--- | :--- | :--- |
| **Serviço AT** | `fatcorews` | `sgdtws` |
| **Método SOAP** | `RegisterInvoice` / `ChangeInvoiceStatus` | `envioDocumentoTransporte` |
| **WSDL local** | [wsdl/faturas.wsdl](portugal_compliance/wsdl/faturas.wsdl) | [wsdl/documentosTransporte.wsdl](portugal_compliance/wsdl/documentosTransporte.wsdl) |
| **Porta (testes)** | 723 | **701** |
| **Porta (produção)** | 443 (implícita, sem porta) | **401** — não 701; confirmado na secção 6.6 do Manual de Integração oficial da AT. Produção e testes usam portas **diferentes**, ao contrário do webservice de séries. |
| **DocTypes cobertos** | Sales Invoice, POS Invoice | Delivery Note |
| **Módulo Python** | [utils/at_invoice_webservice.py](portugal_compliance/utils/at_invoice_webservice.py) | [utils/at_transport_webservice.py](portugal_compliance/utils/at_transport_webservice.py) |
| **Ativado por** | `Portugal Auth Settings.invoice_communication_method = "Tempo Real (Webservice)"` | `Portugal Auth Settings.transport_communication_method = "Tempo Real (Webservice)"` |

Ambos os módulos reutilizam, sem duplicar, as mesmas funções de baixo nível de
`at_webservice.py` (`_build_mtls_session`, `_build_wsse_security_header`) já validadas pelo
webservice de séries — a autenticação é idêntica nos três canais.

---

## 2. Autenticação: mTLS + WS-Security

Todos os webservices da AT usados por este módulo exigem **dupla autenticação**:

1. **mTLS (Mutual TLS)** — o cliente apresenta um certificado próprio ao servidor da AT
   durante o handshake TLS. Construído em `_build_mtls_session(cert_path, key_path)`
   (`at_webservice.py`), que devolve uma `requests.Session` com `cert=(cert_path, key_path)` —
   os campos `mtls_certificate_path`/`mtls_private_key_path` de `Portugal Auth Settings`.
2. **Cabeçalho WS-Security proprietário** — dentro do envelope SOAP, um cabeçalho
   `<Security>` com nonce, timestamp e a password cifrada com AES-128 e a chave pública da AT
   (`at_public_certificate_path`). Construído em `_build_wsse_security_header(at_username,
   at_password, at_public_cert_path)`.

> **Nonce e timestamp são de uso único** — o cabeçalho WS-Security tem de ser reconstruído a
> cada chamada SOAP, nunca reutilizado entre pedidos. Todos os clientes deste módulo chamam
> `get_*_webservice_client()` (uma função por webservice: séries, faturas, transporte) no
> início de cada operação, nunca guardando o cabeçalho em cache.

O cliente SOAP em si é construído com [zeep](https://docs.python-zeep.org/), não `SoapClient`
nativo:

```python
session = _build_mtls_session(cert_path, key_path)
transport = Transport(session=session, timeout=60)
client = zeep.Client(wsdl=wsdl_path, transport=transport)
binding_name = list(client.wsdl.bindings.keys())[0]
service = client.create_service(binding_name, endpoint)
header = _build_wsse_security_header(at_username, at_password, at_public_cert_path)
# uso: service.RegisterInvoice(_soapheaders=[header], **payload)
```

---

## 3. Comunicação de Faturas (`RegisterInvoice`)

### 3.1. Gatilho

Hook `on_submit` de Sales Invoice e POS Invoice:
[document_hooks.py](portugal_compliance/hooks.py) → `at_invoice_webservice.enqueue_invoice_communication`.

```python
def enqueue_invoice_communication(doc, method=None):
    method_setting = frappe.db.get_single_value("Portugal Auth Settings", "invoice_communication_method")
    if method_setting != "Tempo Real (Webservice)":
        return
    frappe.enqueue(
        "portugal_compliance.utils.at_invoice_webservice.register_invoice",
        queue="short", timeout=120,
        document_type=doc.doctype, document_name=doc.name,
    )
```

A chamada SOAP nunca corre de forma síncrona dentro do pedido HTTP que submete o documento —
é sempre despachada para a fila `short` do Frappe (`frappe.enqueue`), para que uma AT lenta ou
indisponível nunca bloqueie a submissão do documento no ERPNext.

### 3.2. Construção do Payload — Reutilização do SAF-T

`build_invoice_payload()` **não recalcula** taxa, isenção, tipo de documento ou totais — chama
diretamente `SAFTGenerator.get_sales_invoices_data()` (o mesmo motor usado na exportação
mensal, ver [manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md)) e
filtra o resultado ao documento em questão:

```python
generator = SAFTGenerator()
invoices = generator.get_sales_invoices_data(doc.company, doc.posting_date, doc.posting_date, doctype=document_type)
invoice = next((i for i in invoices if i.name == document_name), None)
```

Isto garante que os dados enviados em tempo real e os dados reportados no SAF-T mensal nunca
divergem — uma única fonte de verdade para "qual é o tipo de documento, a taxa e o total
desta fatura", em vez de duas implementações independentes que podiam derivar.

Campos do payload com origem não trivial:

| Campo do WSDL | Origem | Nota |
| :--- | :--- | :--- |
| `InvoiceType` | `invoice.invoice_type`, calculado por `SAFTGenerator` a partir de `Portugal Series Configuration.document_code` da série realmente usada | **Não** um literal fixo "FT" — uma Nota de Crédito emitida na série NC tem de ser reportada como tal, nunca como Fatura. |
| `HashCharacters` | `ATCUD Log.signature_hash_control` | Só os 4 caracteres de controlo (posições 1/11/21/31 da assinatura Base64) — **não** a hash completa. Confundir este campo com o `<Hash>` completo do SAF-T foi um erro real só detetado ao ler a estrutura exata do WSDL. |
| `SelfBillingIndicator` | `Customer.at_is_self_billing` | Campo real do Customer, não um literal fixo. |
| `CashVATSchemeIndicator` | Fixo `0` neste payload | O indicador de regime de Caixa aplica-se à comunicação de **faturas**; o campo equivalente para **recibos** é `PaymentType` (RC/RG) no SAF-T — ver `manual_tecnico_exportacao_saft.md`, secção 5. |

### 3.3. Códigos de Resposta

```python
SUCCESS_CODES = {"0", "0000"}
DUPLICATE_CODES = {"-3", "-10"}
```

Um documento "duplicado" (já registado anteriormente) é tratado como **sucesso idempotente**,
não como falha — reenviar uma fatura já comunicada não deve gerar retries infinitos nem
alarmes. Note-se que o código real devolvido pela sandbox da AT num teste ao vivo
(2026-08-21) foi **`-10`** ("O documento já foi registado pelo emitente"), não o `-3`
documentado no cliente de referência — ambos são tratados, já que a AT pode devolver qualquer
um consoante o tipo de duplicação detetada.

### 3.4. Anulação — `ChangeInvoiceStatus`

Hook `on_cancel` → `enqueue_invoice_cancellation`. Só despacha `ChangeInvoiceStatus` se o
documento tiver mesmo um registo de **sucesso prévio** em `Portugal Invoice Communication
Log` — um documento comunicado apenas via SAF-T mensal (modo Offline) nunca foi registado
individualmente na AT por este canal, pelo que não há nada a mudar de estado; a sua anulação
chega à AT no próximo SAF-T (`InvoiceStatus="A"`, valores a `0.00`).

---

## 4. Comunicação de Transporte (`envioDocumentoTransporte`)

### 4.1. Especificidades face às Faturas

* **Portas assimétricas testes/produção** (701/401) — ao contrário do webservice de
  faturação, que usa 723/443. Um erro comum de configuração é assumir que a porta de
  produção é a mesma dos testes.
* **`MovementType`** tem de corresponder ao `document_code` real da série usada (`GR` neste
  sistema), extraído de `Portugal Series Configuration` via `_document_code_for()` — o mesmo
  padrão estrutural (não um literal fixo) já usado para `InvoiceType`.
* **`CustomerTaxID`/`SupplierTaxID`** são um `xsd:choice` — o payload nunca envia os dois.
* **`AddressStructurePT`** usa o campo `Addressdetail` (d minúsculo) — grafia confirmada no
  XSD real e no XML de um pedido bem-sucedido do módulo de referência, distinta da grafia
  usada na prosa do próprio manual oficial da AT.
* **`MovementEndTime`** é opcional e fica de fora — não existe no Delivery Note um campo
  fiável de "hora de fim de transporte"; inventar um valor seria pior do que omitir (mesmo
  critério do campo `WithholdingTaxType` no SAF-T).
* **Aceite mesmo sem ATCUD** (a AT devolve um aviso, não um erro), mas como a série GR já está
  comunicada e a gerar ATCUD real, é sempre enviado quando existe.

### 4.2. Códigos de Resposta

```python
SUCCESS_CODES = {"0"}
ALERT_CODES = {"-100"}  # "data de início inferior à atual" - aviso, não erro
```

`-100` é tratado como sucesso: a AT está apenas a informar que a data de início do transporte
já passou (comunicação tardia), não a rejeitar o documento.

---

## 5. Mecanismo de Retry com Backoff Exponencial

Ambos os canais partilham o mesmo padrão de resiliência, implementado independentemente em
cada módulo (`_write_log`, com a mesma lógica em `at_invoice_webservice.py` e
`at_transport_webservice.py`):

```python
if bump_retry:
    log.retry_count = (log.retry_count or 0) + 1
    if log.retry_count < 8:
        delay_minutes = min(2 ** log.retry_count, 240)
        log.next_retry_date = frappe.utils.add_to_date(frappe.utils.now(), minutes=delay_minutes)
    else:
        log.next_retry_date = None  # esgotadas as tentativas automáticas
```

| Tentativa | Atraso (minutos) | Atraso efetivo |
| :--- | :--- | :--- |
| 1 | 2¹ = 2 | 2 min |
| 2 | 2² = 4 | 4 min |
| 3 | 2³ = 8 | 8 min |
| 4 | 2⁴ = 16 | 16 min |
| 5 | 2⁵ = 32 | 32 min |
| 6 | 2⁶ = 64 | 1h04 |
| 7 | 2⁷ = 128 | 2h08 |
| 8 | min(2⁸, 240) = **240** | 4h (tempo máximo, retries param depois desta) |

Após a 8.ª tentativa falhada, `next_retry_date` fica `None` — o documento deixa de ser
reprocessado automaticamente e requer intervenção manual (reenvio explícito ou investigação
do erro registado em `at_response_message`).

### 5.1. O Processador Agendado

A tarefa horária [tasks/hourly.py](portugal_compliance/tasks/hourly.py),
`retry_invoice_communications()`, varre `Portugal Invoice Communication Log` por registos
prontos a reprocessar:

```python
pending = frappe.db.get_all(
    "Portugal Invoice Communication Log",
    filters={"status": ["in", ["Retrying", "Pending"]], "next_retry_date": ["<=", now()]},
    fields=["name", "document_type", "document_name"],
)
for log in pending:
    if log.document_type == "Delivery Note":
        register_transport_document(log.document_type, log.document_name, log_name=log.name)
    else:
        register_invoice(log.document_type, log.document_name, log_name=log.name)
```

O mesmo doctype de log (`Portugal Invoice Communication Log`, com o campo genérico
`document_type`) serve os dois canais — o nome do doctype ficou "Invoice" por ter sido o
primeiro fluxo implementado, mas a tarefa despacha corretamente para
`register_transport_document` ou `register_invoice` consoante o tipo real do documento.

Registado em `hooks.py`:

```python
scheduler_events = {
    "hourly": ["portugal_compliance.tasks.hourly.execute"],
    ...
}
```

---

## 6. Estrutura de Ficheiros

| Ficheiro | Função |
| :--- | :--- |
| [utils/at_webservice.py](portugal_compliance/utils/at_webservice.py) | Funções de baixo nível partilhadas (`_build_mtls_session`, `_build_wsse_security_header`) + webservice de séries. |
| [utils/at_invoice_webservice.py](portugal_compliance/utils/at_invoice_webservice.py) | `RegisterInvoice`, `ChangeInvoiceStatus`, retry, tabela de mensagens de erro. |
| [utils/at_transport_webservice.py](portugal_compliance/utils/at_transport_webservice.py) | `envioDocumentoTransporte`, retry, tabela de mensagens de erro. |
| [wsdl/faturas.wsdl](portugal_compliance/wsdl/faturas.wsdl) | Contrato SOAP oficial do serviço `fatcorews`. |
| [wsdl/documentosTransporte.wsdl](portugal_compliance/wsdl/documentosTransporte.wsdl) | Contrato SOAP oficial do serviço `sgdtws`. |
| [tasks/hourly.py](portugal_compliance/tasks/hourly.py) | `retry_invoice_communications()` — processador agendado do backoff. |

---

## 7. Resolução de Problemas

| Sintoma | Causa provável | Diagnóstico / Solução |
| :--- | :--- | :--- |
| Documento nunca é comunicado, sem erro visível | `invoice_communication_method`/`transport_communication_method` ainda em "Offline" | Verificar `Portugal Auth Settings` — o módulo está em modo Offline por omissão. |
| `InvoiceWebserviceError: Certificado mTLS não configurado` | Campos `mtls_certificate_path`/`mtls_private_key_path` vazios | Preencher em `Portugal Auth Settings`; usar `test_connection()` (whitelisted) para validar sem submeter um documento real. |
| Falha de ligação à porta 701 em produção | Confundir a porta de testes (701) com a de produção (401) para o serviço de transporte | As portas são assimétricas neste webservice — não presumir simetria com o de faturação (723/443). |
| Retries param ao fim de ~4h sem sucesso | 8 tentativas esgotadas, backoff atingiu o teto | `next_retry_date` fica `None` — reenviar manualmente via `register_invoice`/`register_transport_document`, ou investigar `at_response_message` no log. |
| Fatura marcada "Failed" mas a AT já a tem registada | Código de duplicado não reconhecido | Confirmar que o código devolvido está em `DUPLICATE_CODES` (`-3`, `-10`) — a AT pode devolver qualquer um dos dois. |
| `HashCharacters` no payload não bate com o QR Code impresso | Campo confundido com o `<Hash>` completo do SAF-T | `HashCharacters` são só os 4 caracteres de controlo (`ATCUD Log.signature_hash_control`), o mesmo valor do campo `Q` do QR Code — nunca a assinatura completa. |

---

**Nota Final**: este manual cobre exclusivamente o canal de comunicação em tempo real
(Séries, Faturas, Transporte via webservice SOAP). Para o processo de exportação e submissão
mensal do ficheiro SAF-T, ver
[manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md). Os dois canais são
independentes e complementares — uma instalação pode legalmente operar só com SAF-T mensal
(modo Offline, omissão), só com comunicação em tempo real, ou com ambos.
