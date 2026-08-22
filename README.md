## Portugal Compliance

App de conformidade fiscal portuguesa para o ERPNext/Frappe: ATCUD, assinatura RSA-SHA1, comunicação em tempo real com os webservices da AT, exportação SAF-T (PT) e os print formats legais correspondentes.

### O que está implementado

- **ATCUD** (Portaria n.º 195/2020) gerado automaticamente na submissão, com cadeia de hash e código de validação por série.
- **Assinatura RSA-SHA1** dos documentos fiscais, com controlo de concorrência (`SELECT ... FOR UPDATE`) na leitura da hash anterior.
- **Webservices da AT**, sobre o mesmo cliente certificado (mTLS + WS-Security):
  - Registo de séries (`SeriesWSService`)
  - Faturação em tempo real (`RegisterInvoice`) — Sales Invoice
  - Documentos de transporte (`envioDocumentoTransporte`) — Delivery Note
- **SAF-T (PT) 1.04\_01** — Header, MasterFiles, SourceDocuments (faturas e pagamentos), validado contra o XSD 1.1 oficial.
- **QR Code** (Base64, gerado no momento da impressão) e **Print Formats A4** com ATCUD, QR e assinatura visíveis:
  - `Factura PT` — Sales Invoice (Fatura / Fatura-Recibo / Nota de Crédito)
  - `Guia de Transporte PT` — Delivery Note
  - `Fatura Simplificada PT` (talão 80mm, omissão) e `Fatura Simplificada PT (A4)` — POS Invoice
  - `Recibo PT` — Payment Entry
- **Inviolabilidade** (Portaria n.º 363/2010): documentos fiscais assinados não podem ser eliminados nem ter campos fiscais alterados; anulação é sempre pela via legal (Cancelar / documento de estorno).
- **Finalizar / Anular Série** junto da AT (`finalizarSerie`/`anularSerie`), a partir de Portugal Series Configuration — fecho formal de série em fim de ano ou migração, e anulação de série mal configurada nunca usada.
- **Workspace nativo** "Portugal Compliance" no Desk, com atalhos para configuração, séries, logs e auditoria, e uma página **Dashboard AT** com estado de compliance, alertas (certificados a expirar, séries por comunicar), estatísticas e gráfico de ATCUD dos últimos 6 meses.

O motor fiscal (ATCUD, assinatura, inviolabilidade) aplica-se apenas a documentos **emitidos a terceiros** (Portaria 195/2020): `Sales Invoice`, `POS Invoice`, `Delivery Note` e `Payment Entry`. Documentos internos (Stock Entry, Journal Entry) e de compra (Purchase Invoice, Purchase Receipt) não são assinados nem comunicados à AT.

### Configuração

Toda a configuração de compliance (credenciais AT, certificados mTLS, chave de assinatura, ambiente sandbox/produção, número de certificado de software) vive em **Portugal Auth Settings** — fonte única de verdade, independente da Company. Na Company, ativa-se apenas o toggle `Portugal Compliance Enabled`.

### Instalação

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app portugal_compliance
```

Depois de instalar, configura as credenciais e certificados AT em **Portugal Auth Settings** e ativa `Portugal Compliance Enabled` na(s) Company(ies) portuguesa(s).

### Diagnóstico de emergência

Dois comandos para correr sem programador disponível quando a comunicação com a AT começa a falhar, sem precisar de UI:

```bash
# Testa se a configuração atual (mTLS + credenciais) chega para abrir
# sessão com o webservice de séries da AT.
bench --site <site> execute portugal_compliance.utils.diagnostics.test_at_connection

# Verifica matematicamente se a chave privada mTLS e o certificado
# público (Portugal Auth Settings) formam um par válido - isola em
# segundos a causa mais comum de "Could not connect to host" (chave e
# certificado desemparelhados, ex: um dos dois foi renovado sem o
# outro), sem precisar de rede real até à AT.
bench --site <site> execute portugal_compliance.utils.diagnostics.verify_key_pair
```

Ambos imprimem um resumo legível e devolvem um dicionário (útil para scripting). Ver `portugal_compliance/utils/diagnostics.py` para o código.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/portugal_compliance
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

gpl-3.0
