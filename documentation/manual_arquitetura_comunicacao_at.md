# Manual: Arquitetura Lógica de Comunicação e Certificação

Este documento apresenta a arquitetura lógica do módulo `portugal_compliance`, ilustrando o
fluxo de dados, a gestão de chaves e o ciclo de vida da comunicação com a Autoridade
Tributária (AT) — em diagramas Mermaid, fiéis ao mecanismo real de `hooks.py` do Frappe (não
a triggers de eventos genéricos nem a um middleware externo).

---

## 1. Visão Geral do Ecossistema

O módulo não é um plugin que intercepta chamadas externas — funde-se na árvore de execução
do próprio Frappe através de `doc_events` declarados em `hooks.py`. Cada submissão de
documento fiscal atravessa esta cadeia dentro da mesma transação de base de dados.

```mermaid
graph TD
    subgraph Core ["ERPNext / Frappe Core"]
        Invoice["Sales Invoice / POS Invoice /<br/>Payment Entry / Delivery Note"]
        DB[("MariaDB")]
    end

    subgraph Module ["portugal_compliance"]
        Hooks["document_hooks.py<br/>(before_save / validate / after_insert)"]
        Signer["🔑 signature.py<br/>sign_document()"]
        ATCUDGen["atcud_generator.py<br/>ATCUDGenerator"]
        TaxBreak["tax_breakdown.py<br/>(código + praça fiscal)"]
        WS["📡 at_webservice.py /<br/>at_invoice_webservice.py /<br/>at_transport_webservice.py"]
        SAFT["saft_generator.py<br/>SAFTGenerator"]
        Logs[("ATCUD Log /<br/>Portugal *Log")]
    end

    subgraph SecureConfig ["Portugal Auth Settings (Single)"]
        KeySign["🔑 invoice_signing_key_path<br/>(assinatura RSA-SHA1)"]
        KeyMTLS["🔐 mtls_certificate_path /<br/>mtls_private_key_path<br/>(mTLS webservice)"]
    end

    subgraph AT ["Autoridade Tributária"]
        WSSeries["SeriesWSService"]
        WSInv["fatcorews"]
        WSTransp["sgdtws"]
    end

    Invoice -->|"before_save / validate"| Hooks
    Hooks -->|"1. Assinar"| Signer
    Signer -->|"Lê chave"| KeySign
    Signer -->|"2. Consulta região/código"| TaxBreak
    Signer -->|"3. hash + hash_control"| ATCUDGen
    ATCUDGen -->|"4. Persiste"| Logs
    Hooks -->|"5. Grava atcud_code/qr_code"| DB

    Hooks -->|"on_submit (se Tempo Real)"| WS
    WS -->|"mTLS"| KeyMTLS
    WS -->|"SOAP"| WSSeries
    WS -->|"SOAP"| WSInv
    WS -->|"SOAP"| WSTransp

    SAFT -->|"lê"| DB
    SAFT -->|"reutiliza"| TaxBreak
```

---

## 2. Ciclo de Vida do Documento (Sequence Diagram)

Do registo da série até à emissão e impressão de uma fatura, com os nomes reais das funções
envolvidas.

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👤 Admin
    participant Frappe as 🏢 Frappe/ERPNext
    participant Hooks as 🛡️ document_hooks.py
    participant Sig as 🔑 signature.py
    participant AT as 🏛️ AT (SeriesWSService)

    note over Admin, AT: FASE 1 — Registo de Série (uma vez, antes do 1º documento)
    Admin->>Frappe: Criar Portugal Series Configuration (prefix="FT2026N")
    Frappe->>AT: SOAP registarSerie(serie, tipoDoc="FT", classeDoc="SI")
    AT-->>Frappe: codResultOper=2001, codValidacaoSerie="AAJFJ..."
    Frappe->>Frappe: db.set_value(is_communicated=1, validation_code=...)

    note over Admin, AT: FASE 2 — Emissão de Fatura (runtime, dentro do mesmo pedido)
    Admin->>Frappe: Submeter Sales Invoice
    Frappe->>Hooks: before_save: enforce_fiscal_field_lock, generate_atcud_before_save
    activate Hooks
    Hooks->>Sig: sign_document(doc, series_prefix, sequence_number)
    activate Sig
    Sig->>Sig: SELECT ... FOR UPDATE (lock da série)
    Sig->>Sig: get_previous_signature_hash (mesma série)
    Sig->>Sig: build_data_to_sign() -> RSA-SHA1 -> Base64
    Sig-->>Hooks: signature_hash, hash_control, atcud_code
    deactivate Sig
    Hooks->>Frappe: doc.atcud_code = "AAJFJ...-19"
    deactivate Hooks
    Frappe->>Hooks: after_insert: generate_atcud_after_insert, generate_and_attach_qr_code
    Hooks->>Frappe: ATCUD Log.insert() e doc.db_set(qr_code, qr_code_image)
    Frappe->>Hooks: validate: _validate_series_not_inactive (bloqueia se série Finalizada/Anulada)
    Frappe->>Frappe: COMMIT

    note over Admin, AT: FASE 3 — Comunicação em Tempo Real (opcional, assíncrona)
    Frappe->>Hooks: on_submit: enqueue_invoice_communication
    Hooks->>Frappe: frappe.enqueue(register_invoice, queue="short")
    note right of Frappe: Fora da transação do pedido HTTP -<br/>uma AT lenta nunca bloqueia a submissão
    Frappe-->>AT: SOAP RegisterInvoice (background job)
    AT-->>Frappe: CodigoResposta=0/0000 (sucesso) ou -3/-10 (duplicado, idempotente)
```

---

## 3. Arquitetura "Dual Key" (Segurança)

A separação entre a identidade "Fiscal" (assinatura de documentos) e a identidade "Técnica"
(autenticação de rede) é deliberada e explícita no schema de `Portugal Auth Settings` — não
duas pastas de ficheiros por convenção, mas dois grupos de campos distintos na mesma
configuração.

```mermaid
classDiagram
    class ChaveAssinatura {
        <<Portugal Auth Settings>>
        +invoice_signing_key_path: Password
        +invoice_signing_key_password: Password
        +invoice_signing_key_version: Data
        +Algoritmo: RSA-SHA1, PKCS1 v1.5
        +Uso: assinatura de documentos
        +Continuidade: crítica, ver nota abaixo
    }

    class ChaveComunicacao {
        <<Portugal Auth Settings>>
        +mtls_certificate_path: Data
        +mtls_private_key_path: Data
        +at_public_certificate_path: Data
        +Uso: mTLS e WS-Security
        +Renovacao: conforme validade do certificado
    }

    class Documento {
        +atcud_code
        +qr_code
    }

    Documento ..> ChaveAssinatura : Assinado com signature.py
    Documento ..> ChaveComunicacao : Comunicado via webservice
```

> **Continuidade da chave de assinatura**: `sign_document()` usa `invoice_signing_key_path`
> para calcular o hash RSA-SHA1 de cada documento. Trocar esta chave **não invalida**
> documentos já assinados, mas **rompe o encadeamento** para o próximo documento da série —
> `previous_signature_hash` deixa de poder ser recalculado a partir da chave antiga, pelo que
> a rotação de chave tem de ser feita com o mesmo cuidado de uma finalização de série.
>
> **Renovação da chave de comunicação**: os certificados mTLS/AT (`mtls_certificate_path`,
> `mtls_private_key_path`, `at_public_certificate_path`) devem ser renovados conforme a
> validade emitida pela entidade certificadora — ao contrário da chave de assinatura, a sua
> renovação não tem qualquer efeito sobre documentos já emitidos, porque não participa no
> cálculo do hash fiscal.

> **Nota de fidelidade ao código**: ao contrário de convenções de pastas fixas
> (`saft/production/`, `webservice/production/`), este módulo **não impõe** uma estrutura de
> diretórios para os ficheiros de chave/certificado — cada caminho é um campo de texto livre
> em `Portugal Auth Settings`, resolvido em runtime. A responsabilidade de organizar os
> ficheiros no sistema de ficheiros do servidor (permissões, localização fora da webroot) é
> do administrador de sistema. Ver
> [manual_tecnico_devops_certificados.md](manual_tecnico_devops_certificados.md) para uma
> convenção recomendada.

---

## 4. Estrutura de Módulos e Dependências

```mermaid
classDiagram
    class document_hooks {
        +generate_atcud_before_save(doc)
        +generate_atcud_after_insert(doc)
        +validate_portugal_compliance(doc)
        +enforce_fiscal_field_lock(doc)
        +block_fiscal_document_deletion(doc)
        +log_document_print(doc)
        -_validate_series_not_inactive(doc)
    }

    class ATCUDGenerator {
        +generate_atcud_for_document(doc)
        +persist_pending_atcud_log(doc)
        -_build_qr_data_optimized(doc)
        -_get_next_sequence_thread_safe(doc)
    }

    class signature {
        +sign_document(doc, series_prefix, sequence_number)
        +verify_signature_chain(company)
        +export_signing_public_key()
        -build_data_to_sign(doc, spec, ...)
        -_lock_series_for_signing(series)
    }

    class tax_breakdown {
        +get_tax_breakdown_by_at_code(doc)
        +get_line_at_tax_info(doc)
        +get_account_at_info(account_names)
    }

    class ATWebserviceClient {
        +register_naming_series(naming_series, company)
        +consultar_serie(series_config_name)
        +finalizar_serie(series_config_name, ...)
        +anular_serie(series_config_name, ...)
    }

    class SAFTGenerator {
        +generate_saft(company, from_date, to_date)
        +get_sales_invoices_data(company, ...)
        +get_tax_table_data(company)
    }

    document_hooks --> ATCUDGenerator : delega geração de ATCUD
    ATCUDGenerator --> signature : usa para assinar
    signature --> tax_breakdown : resolve região/código (indireto, via QR)
    document_hooks --> ATWebserviceClient : ativa/anula/finaliza séries
    SAFTGenerator --> tax_breakdown : mesma fonte de código/região
    SAFTGenerator ..> signature : lê ATCUD Log (assinatura já gerada)
```

---

## 5. Comunicação em Tempo Real — Estados

```mermaid
stateDiagram-v2
    [*] --> Rascunho
    Rascunho --> Submetido : Submeter documento

    state Submetido {
        [*] --> AssinarRSA
        AssinarRSA --> GerarATCUD
        GerarATCUD --> PersistirLog : ATCUD Log
        PersistirLog --> [*]
    }

    Submetido --> Enfileirado : on_submit (se "Tempo Real" ativo)

    state Enfileirado {
        [*] --> ConstruirPayload : reutiliza SAFTGenerator
        ConstruirPayload --> EnviarSOAP
        EnviarSOAP --> Sucesso : código 0/0000/-3/-10
        EnviarSOAP --> Retrying : outro código, ou falha de rede

        Retrying --> EnviarSOAP : next_retry_date atingida\n(backoff 2^n, teto 240min)
        Retrying --> Esgotado : 8 tentativas falhadas
    }

    Sucesso --> [*]
    Esgotado --> [*] : requer reenvio manual

    Submetido --> Anulado : on_cancel
    Anulado --> ComunicarAnulacao : só se houve Sucesso prévio\n(ChangeInvoiceStatus)
```

---

## 6. Diferenças Face ao Modelo de Referência (Dolibarr)

| Aspeto | Módulo de Referência (Dolibarr) | `portugal_compliance` (Frappe) |
| :--- | :--- | :--- |
| Mecanismo de interceção | Triggers de evento (`BILL_VALIDATE`, `SHIPPING_VALIDATE`) + injeção de JS para esconder botões | `doc_events` declarativos em `hooks.py`, bloqueio ao nível do servidor (`frappe.throw`), sem dependência de JavaScript |
| Armazenamento de dados fiscais | Tabelas dedicadas (`llx_compliance_portugal_data`, `_series`) | DocTypes nativos do Frappe (`ATCUD Log`, `Portugal Series Configuration`), com toda a infraestrutura de permissões/auditoria do framework incluída |
| Modelos PDF | Cópia de ficheiros `.php` para a árvore `core/` do Dolibarr na ativação do módulo | Registos `Print Format` nativos, versionados como fixture (`fixtures/print_format.json`) |
| Validação SAF-T | XSD 1.0 implícito (biblioteca PHP padrão) | XSD 1.1 explícito (`xmlschema.XMLSchema11`) — necessário porque o schema real da AT declara `vc:minVersion="1.1"` |
| Retry de comunicação | Não documentado no material de referência | Backoff exponencial explícito (`2^n` min, teto 240 min), processado por tarefa agendada horária |

---

**Ver também**: [manual_funcionalidades_compliance.md](manual_funcionalidades_compliance.md)
(visão funcional), [manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md) (detalhe
de implementação da assinatura e séries),
[manual_tecnico_comunicacao_documentos_at.md](manual_tecnico_comunicacao_documentos_at.md)
(detalhe dos webservices).
