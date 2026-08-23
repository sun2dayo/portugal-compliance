# Manual de Funcionalidades e Arquitetura: Portugal Compliance

Este manual documenta exaustivamente a arquitetura, as funcionalidades e o modelo de dados
do módulo **`portugal_compliance`** para Frappe/ERPNext. A análise baseia-se na revisão
código-a-código do módulo e em testes reais contra o webservice da Autoridade Tributária
(AT), não em intenção de código nem em documentação de terceiros.

Ao contrário de uma integração como plugin externo (o modelo típico noutras plataformas),
este módulo funde-se na própria árvore de execução do Frappe através do seu sistema nativo
de **hooks declarativos** (`hooks.py`) — não existe injeção de JavaScript para esconder
botões, nem cópia de ficheiros para pastas "core": o bloqueio, a assinatura e a comunicação
correm no mesmo ciclo de vida do documento, ao nível do servidor.

---

## 1. Arquitetura de Alto Nível

### 1.1. O mecanismo de `doc_events`

O Frappe expõe, por cada DocType, uma cadeia de eventos do ciclo de vida do documento
(`before_insert`, `before_save`, `validate`, `before_submit`, `after_insert`, `on_submit`,
`on_cancel`, `on_trash`, `before_print`). O módulo regista funções Python para estes eventos
declarativamente em [hooks.py](portugal_compliance/hooks.py), no dicionário `doc_events`, um
por DocType fiscal:

```python
doc_events = {
    "Sales Invoice": {
        "before_insert": "portugal_compliance.utils.document_hooks.reset_fiscal_fields_on_return_clone",
        "before_save": [
            "portugal_compliance.utils.document_hooks.enforce_fiscal_field_lock",
            "portugal_compliance.utils.document_hooks.generate_atcud_before_save"
        ],
        "validate": "portugal_compliance.utils.document_hooks.validate_portugal_compliance",
        "before_submit": "portugal_compliance.utils.document_hooks.before_submit_document",
        "before_print": "portugal_compliance.utils.document_hooks.log_document_print",
        "after_insert": [
            "portugal_compliance.utils.document_hooks.generate_atcud_after_insert",
            "portugal_compliance.utils.document_hooks.generate_and_attach_qr_code"
        ],
        "on_submit": "portugal_compliance.utils.at_invoice_webservice.enqueue_invoice_communication",
        "on_trash": "portugal_compliance.utils.document_hooks.block_fiscal_document_deletion",
        "on_cancel": [
            "portugal_compliance.utils.document_hooks.log_document_cancellation",
            "portugal_compliance.utils.at_invoice_webservice.enqueue_invoice_cancellation"
        ]
    },
    # POS Invoice, Payment Entry, Delivery Note: estrutura equivalente
}
```

Esta tabela é a fonte de verdade de tudo o que o módulo faz a um documento fiscal. Qualquer
comportamento não wired aqui **não corre em produção**, independentemente de existir código
Python correspondente algures no repositório — um princípio que se revelou crítico durante
esta auditoria (ver secção 6, "Código Morto").

### 1.2. Camadas do módulo

| Camada | Responsabilidade | Módulos principais |
| :--- | :--- | :--- |
| **Hooks de documento** | Intercetar o ciclo de vida (bloqueio, geração de ATCUD, impressão) | `utils/document_hooks.py` |
| **Motor de assinatura** | RSA-SHA1, encadeamento de hash, verificação | `utils/signature.py` |
| **Gerador de ATCUD/QR** | Sequência, código único, string do QR Code | `utils/atcud_generator.py`, `utils/jinja_methods.py` |
| **Cliente de webservices AT** | Séries, Faturas, Transporte (SOAP + mTLS) | `utils/at_webservice.py`, `utils/at_invoice_webservice.py`, `utils/at_transport_webservice.py` |
| **Gerador SAF-T** | XML mensal/anual + validação XSD | `utils/saft_generator.py` |
| **Discriminação fiscal partilhada** | Categoria de taxa (NOR/INT/RED/ISE) e praça fiscal (PT/PT-AC/PT-MA), reutilizada pelo QR Code, SAF-T e validação de isenção | `utils/tax_breakdown.py` |
| **Tarefas agendadas** | Retries com backoff, relatórios de compliance | `tasks/hourly.py`, `tasks/daily.py`, `tasks/weekly.py`, `tasks/yearly.py` |

Esta separação por responsabilidade é deliberada: `tax_breakdown.py`, por exemplo, existe
precisamente para que a resolução de "que taxa e que região fiscal se aplica a esta linha"
tenha **uma única fonte de verdade**, partilhada entre o QR Code impresso, o ficheiro SAF-T e
a validação de isenção de IVA — evitando que dois caminhos de código cheguem a respostas
diferentes para a mesma pergunta.

---

## 2. Os 5 Pilares de Certificação

O módulo foi auditado formalmente contra os cinco pilares que um inspetor da AT verificaria
numa inspeção de certificação de software. Ver [CERTIFICATION.md](CERTIFICATION.md) para a
declaração de conformidade completa, com evidência ficheiro:linha e resultados de testes
reais em sandbox.

### Pilar 1 — Segurança e Inviolabilidade (Portaria n.º 363/2010)

Um documento fiscal, uma vez assinado, não pode ser alterado nem eliminado por nenhuma via —
UI, API ou acesso direto à base de dados por um utilizador com privilégios elevados.

* `block_fiscal_document_deletion` (`on_trash`) impede eliminar qualquer documento com
  `atcud_code` preenchido, ou já anulado (`docstatus=2`).
* `enforce_fiscal_field_lock` (`before_save`) impede alterar campos fiscais (cliente, total,
  data, série) depois do ATCUD ter sido gerado — compara sempre com
  `doc.get_doc_before_save()`.
* `force_track_changes_property_setters` (`after_migrate`) garante, via Property Setter, que
  `track_changes` está sempre ativo nos DocTypes fiscais — não é uma preferência de UI que um
  utilizador possa desligar em Customize Form.
* `log_document_print` (`before_print`) regista cada impressão/reimpressão em **Portugal
  Document Print Log** — a pista de auditoria cobre emissão, anulação e impressão.

### Pilar 2 — Criptografia e ATCUD (Portaria n.º 195/2020)

* Assinatura RSA-SHA1 (PKCS#1 v1.5) por documento, chave privada dedicada (distinta da chave
  mTLS do webservice).
* Encadeamento de hash: cada assinatura inclui a hash Base64 do documento anterior da mesma
  série. Um `SELECT ... FOR UPDATE` na linha da série fecha a janela de corrida entre
  documentos concorrentes.
* `verify_signature_chain()` — ferramenta de verificação a posteriori, percorre o `ATCUD Log`
  por série e confirma continuidade da cadeia e validade criptográfica de cada assinatura.

Ver [manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md) para o detalhe completo.

### Pilar 3 — Layouts e QR Code (Portaria n.º 195/2020)

QR Code com os campos A-Q exatos da Especificação Técnica da AT, incluindo suporte a três
praças fiscais (Continente/Açores/Madeira), impresso tanto em Print Formats térmicos
(recibos/faturas simplificadas) como A4. Ver
[manual_tecnico_qrcode.md](manual_tecnico_qrcode.md).

### Pilar 4 — Interoperabilidade (SAF-T)

Ficheiro SAF-T (PT) v1.04_01, validado rigorosamente contra o XSD oficial (XML Schema 1.1),
com tratamento correto de documentos anulados (`InvoiceStatus="A"`, valores a `0.00`, ATCUD e
hash originais preservados) e do Regime de IVA de Caixa. Ver
[manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md).

### Pilar 5 — Separação de Dados

Documentos recebidos de terceiros (Purchase Invoice) ou de uso puramente interno (Stock
Entry, Journal Entry) nunca consomem ATCUD, nunca são assinados e nunca poluem o SAF-T como
documentos fiscais — ver secção 3 abaixo.

---

## 3. DocTypes Fiscais vs. Não Fiscais

### 3.1. `FISCAL_IMMUTABLE_DOCTYPES`

A constante autoritativa, definida em
[document_hooks.py](portugal_compliance/utils/document_hooks.py), determina quais os 4
DocTypes nativos do ERPNext que este módulo trata como documentos fiscais portugueses:

```python
FISCAL_IMMUTABLE_DOCTYPES = ["Sales Invoice", "Delivery Note", "Payment Entry", "POS Invoice"]
```

| DocType | Papel fiscal | Código(s) AT | Série comunicada |
| :--- | :--- | :--- | :--- |
| **Sales Invoice** | Fatura (FT) ou Nota de Crédito (NC), consoante a série realmente usada (`is_return=1` → NC) | FT, NC | Sim |
| **POS Invoice** | Fatura Simplificada | FS | Sim |
| **Payment Entry** | Recibo — RG ("Outros recibos emitidos") por omissão, ou RC ("Regime de IVA de Caixa") se `Portugal Auth Settings.cash_vat_scheme` estiver ativo | RG / RC | Sim |
| **Delivery Note** | Guia de Remessa | GR | Sim |

### 3.2. Doctypes deliberadamente excluídos

Purchase Invoice (faturas de compra recebidas de fornecedores), Stock Entry (movimentos de
stock internos) e Journal Entry (lançamentos contabilísticos) **não** aparecem em
`FISCAL_IMMUTABLE_DOCTYPES`, nem em nenhum `doc_events` de `hooks.py`. Esta é uma decisão
legal deliberada (Pilar 5), não uma omissão:

> ATCUD/assinatura RSA/séries aplicam-se por lei a documentos **emitidos** a clientes
> (Portaria 195/2020), nunca a faturas de compra **recebidas** de fornecedores — a
> responsabilidade fiscal desse documento é de quem o emitiu.
> — comentário em `document_hooks.py`, junto à remoção histórica de Purchase Invoice do
> âmbito fiscal (2026-08-22)

Esta exclusão propaga-se a todas as camadas do módulo:

* **Dashboard AT** (`dashboards/company.py`) — `FISCAL_SERIES_DOCTYPES` filtra estatísticas e
  a tabela "Séries por tipo de documento" aos 4 DocTypes fiscais, mesmo que existam registos
  antigos de `Portugal Series Configuration` para Purchase Invoice/Stock Entry/Journal Entry
  na base de dados (nunca apagados, apenas deixaram de gerar ATCUD).
* **APIs de estatística** (`atcud_api.py`, `series_api.py`) — allowlists de doctypes
  suportados alinhadas com o mesmo âmbito, incluindo o próprio endpoint de criação manual de
  ATCUD (`regenerate_atcud`), para que não seja possível gerar um ATCUD manualmente num
  doctype fora de âmbito através da API.
* **SAF-T** — `SAFTGenerator` só lê Purchase Invoice para popular a tabela mestra de
  Suppliers (exigida pelo schema como masterdata), nunca como `SourceDocument` fiscal.

### 3.3. Âmbito de contabilidade (`TaxAccountingBasis`)

O módulo declara-se explicitamente `TaxAccountingBasis = "F"` (Faturação) no cabeçalho do
SAF-T — cobre emissão e comunicação de documentos fiscais, não contabilidade integrada. Os
elementos `GeneralLedgerAccounts`/`GeneralLedgerEntries` são omitidos por desenho (têm
`minOccurs="0"` no XSD oficial sob esta base). Ver
[manual_tecnico_exportacao_saft.md](manual_tecnico_exportacao_saft.md), secção 2.

---

## 4. Modelo de Dados — DocTypes do Módulo

| DocType | Tipo | Papel |
| :--- | :--- | :--- |
| **Portugal Auth Settings** | Single | Configuração central: credenciais mTLS/WS-Security da AT, chave privada de assinatura, número de certificado de software, modo sandbox/produção, método de comunicação (Offline/Tempo Real), regime de IVA de Caixa. |
| **Portugal Series Configuration** | Documento | Uma série documental por (empresa, DocType, prefixo). Guarda `document_code` (FT/NC/FS/RG/GR...), `naming_series`, `current_sequence`, `is_active`, `is_communicated`, `validation_code` (devolvido pela AT no registo). |
| **ATCUD Log** | Documento (log) | Um registo por documento fiscal assinado: `atcud_code`, `signature_hash`, `previous_signature_hash`, `sequence_number`, `series_used`, `generation_status`. A fonte de dados para `verify_signature_chain()`. |
| **SAF-T Export Log** | Documento (log) | Um registo por exportação SAF-T: período, tipo, `status` (Pending/In Progress/Completed/Failed), `xml_validation_status`, `xsd_validation_errors`, caminho e hash do ficheiro. |
| **Portugal Invoice Communication Log** | Documento (log) | Um registo por tentativa de comunicação em tempo real (faturas e guias de transporte, ver `document_type`): `status`, `at_response_code`, `retry_count`, `next_retry_date`. |
| **Portugal Document Print Log** | Documento (log) | Um registo por impressão/reimpressão de documento fiscal: `document_type`, `document_name`, `print_format`, `printed_by`, `print_datetime`, `atcud_code`. |
| **AT Tax Exemption** | Documento (referência) | Taxonomia oficial de códigos de isenção de IVA (M01-M99), carregada como fixture. |

Todos os logs (`ATCUD Log`, `SAF-T Export Log`, `Portugal Invoice Communication Log`,
`Portugal Document Print Log`) são apend-only na prática — nenhum hook do módulo os edita ou
apaga depois de escritos, formando em conjunto a pista de auditoria completa exigida pelo
Pilar 1.

---

## 5. Configuração Central: Portugal Auth Settings

Single DocType com `permissions` restrito a `System Manager` (leitura/escrita/criação, sem
delete/email/export/print/report/share — guarda credenciais e a chave privada de assinatura).

| Secção | Campos | Uso |
| :--- | :--- | :--- |
| **Certificado do webservice** | `ssl_certificate_path`, `certificate_password`, `at_webservice_url`, `sandbox_mode` | Ligação inicial ao webservice de séries. |
| **Chave de Assinatura (RSA-SHA1)** | `invoice_signing_key_path`, `invoice_signing_key_password`, `invoice_signing_key_version`, `software_certificate_number` | Assinatura de documentos — **distinta** da chave mTLS (ver Nota abaixo). |
| **Credenciais WS-Security** | `at_username`, `at_password`, `mtls_certificate_path`, `mtls_private_key_path`, `at_public_certificate_path` | Autenticação dupla (mTLS + WS-Security) exigida por todos os webservices da AT. |
| **Comunicação de Faturas** | `invoice_communication_method` (Offline/Tempo Real) | Determina se `enqueue_invoice_communication` efetivamente despacha uma chamada de rede. |
| **Comunicação de Transporte** | `transport_communication_method` (Tempo Real/Desativado) | Equivalente para Delivery Note. |
| **Regime de IVA de Caixa** | `cash_vat_scheme` | Determina `PaymentType` (RC/RG) nos recibos do SAF-T — não o sentido do pagamento. |

> **Nota — Arquitetura de Chave Dupla.** A chave usada para assinar documentos
> (`invoice_signing_key_path`) e a chave usada para autenticação mTLS no webservice
> (`mtls_private_key_path`) são deliberadamente **campos distintos**, geridos
> independentemente. Usar a mesma chave para os dois fins foi um erro identificado no módulo
> de referência (Dolibarr) numa versão anterior — não repetido aqui.

---

## 6. Nota Metodológica — Código Morto

Uma característica recorrente encontrada durante a auditoria deste módulo: várias
funcionalidades foram implementadas mais do que uma vez, em módulos paralelos
(`series_adapter.py`, `series_manager.py`, `naming_series_customizer.py`,
`compliance_hooks.py`), sem que a versão mais antiga tivesse sido removida quando a nova
substituiu o seu papel em `hooks.py`. Estes módulos **não estão referenciados em nenhum
`doc_events` nem `scheduler_events`** — código sintaticamente válido, mas nunca executado.

**Regra prática para qualquer intervenção futura no módulo**: antes de assumir que uma função
Python é "a" implementação de uma funcionalidade, confirmar que está de facto referenciada em
`hooks.py` (`doc_events`, `scheduler_events`, `override_doctype_class`) ou chamada a partir de
outro módulo que o esteja. `grep` ao nome da função em todo o repositório é o teste mais
rápido — se o único resultado for a própria definição, é código morto.
