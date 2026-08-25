# Declaração de Conformidade — `portugal_compliance`

**Versão:** 1.1.0

**Software:** portugal_compliance (módulo Frappe/ERPNext)
**Produtor:** NovaDX — Octávio Daio
**Empresa de referência para os testes:** NovaDX (NIF 518747832) — ambiente demo.erpnext.pt
**Branch:** `main`/`develop` · commit `e29edc8` · revalidado 2026-08-25
**Ambiente de testes:** sandbox da AT (`https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService`)

Este documento declara a conformidade do módulo com os diplomas legais abaixo, com base
numa auditoria de código linha a linha e em testes reais contra o webservice da AT (não
simulados). Auditoria original realizada entre 2026-08-17 e 2026-08-23; revalidada em
2026-08-25 com um teste end-to-end completo contra uma instalação nova (demo.erpnext.pt,
empresa NovaDX): ativação de compliance, comunicação das 5 séries à AT, emissão de uma
Fatura e de uma Nota de Crédito, verificação da cadeia de assinaturas e confirmação de
paridade QR Code/Log. Cada alínea remete para o ficheiro e, sempre que aplicável, para o
resultado do teste real que a validou. Limitações conhecidas estão declaradas explicitamente
na secção 5 — este documento não omite gaps por omissão.

## Âmbito declarado

`TaxAccountingBasis = "F"` (Faturação) — o módulo cobre a emissão e comunicação de
documentos fiscais (faturas, guias, recibos), não contabilidade integrada. Os elementos
`GeneralLedgerAccounts`/`GeneralLedgerEntries` do SAF-T (PT) são omitidos deliberadamente:
têm `minOccurs="0"` no XSD oficial e só são exigidos sob bases `C`/`I`.

Documentos abrangidos (`FISCAL_IMMUTABLE_DOCTYPES`,
[document_hooks.py](portugal_compliance/utils/document_hooks.py)): Sales Invoice (FT/NC),
POS Invoice (FS), Payment Entry (RG, ou RC sob regime de IVA de Caixa), Delivery Note (GT).
Purchase Invoice, Stock Entry e Journal Entry foram deliberadamente excluídos do âmbito
fiscal (documentos recebidos de terceiros ou uso interno — a responsabilidade de
ATCUD/assinatura é de quem emite, não de quem recebe).

---

## 1. Portaria n.º 363/2010 — Inviolabilidade e Assinatura Digital

**Bloqueio físico de eliminação e alteração**
[document_hooks.py:1389-1459](portugal_compliance/utils/document_hooks.py) —
`block_fiscal_document_deletion` (hook `on_trash`) impede apagar qualquer documento com
ATCUD gerado, ou já anulado (docstatus=2). `enforce_fiscal_field_lock` (hook `before_save`)
impede alterar campos fiscais (cliente, total, data, série) depois do ATCUD ter sido
gerado. `track_changes` é forçado por Property Setter em cada `after_migrate`
(`force_track_changes_property_setters`), não depende de configuração manual.

**Assinatura digital RSA-SHA1**
[signature.py](portugal_compliance/utils/signature.py) — `sign_document()` assina
`"DataDoc;DataSistema;Referencia;Total;HashAnterior"` com PKCS#1 v1.5 / SHA-1, chave privada
RSA gerida separadamente em Portugal Auth Settings (distinta da chave mTLS do webservice).

**Encadeamento de hash**
`get_previous_signature_hash()` adquire `SELECT ... FOR UPDATE` na linha da série
([signature.py:235](portugal_compliance/utils/signature.py:235)) antes de ler a hash
anterior, serializando documentos concorrentes da mesma série e fechando a janela de corrida
entre pedidos Frappe em transações separadas.

**Verificação da cadeia (auditoria a posteriori)**
`verify_signature_chain()` ([signature.py](portugal_compliance/utils/signature.py)),
whitelisted, percorre o `ATCUD Log` por série e confirma (a) continuidade da cadeia e (b)
validade criptográfica de cada assinatura contra a chave pública derivada.
**Teste real (2026-08-25, demo.erpnext.pt/NovaDX):** `verify_signature_chain(company="NovaDX")`
executado após emitir `FT2026NDX0005` e a Nota de Crédito `NC2026NDX0001` contra ela — 0
cadeias quebradas, 0 assinaturas inválidas, 2/2 documentos verificados, cada um na sua série
(cadeias independentes por série, como desenhado).

**Chave pública**
`export_signing_public_key()` ([signature.py](portugal_compliance/utils/signature.py))
deriva e exporta em PEM a chave pública correspondente à privada já protegida em Portugal
Auth Settings.

---

## 2. Portaria n.º 195/2020 — ATCUD, Séries e QR Code

**Comunicação de séries à AT**
[at_webservice.py](portugal_compliance/utils/at_webservice.py) implementa `registarSerie`,
`consultarSeries`, `finalizarSerie` e `anularSerie` contra o webservice real.
**Teste real (2026-08-25, demo.erpnext.pt/NovaDX):** `registarSerie` executado para as 5
séries da empresa (FT, NC, GR, RG, FS) — todas devolvidas pela AT com `estado="A"` e
`codValidacaoSerie` real, tanto por comunicação individual (botão "Comunicar à AT" na série)
como em lote (botão "Comunicar Séries" na Company → `communicate_all_company_series`).
`finalizarSerie` e `anularSerie` cobertos pela auditoria original (2026-08-23): código 2004 e
2003 respetivamente, motivo "ER" conforme o único código documentado no Manual de Integração
de Software da AT.

**ATCUD nos documentos**
Campo `atcud_code`, gerado uma vez por documento (`generate_atcud_before_save`), nunca
regenerado, persistido em `ATCUD Log` com sequência, hash e validation_code.

**QR Code — campos A-Q**
[jinja_methods.py](portugal_compliance/utils/jinja_methods.py) `get_qr_code_data()`.
Estrutura verificada campo a campo contra a Especificação Técnica — Código QR (Portaria
195/2020, v1.1, Outubro 2020): `C` = país do adquirente (não o emitente), `D` = código real
do documento extraído da série (FT/NC/FS/RG — não um mapeamento estático por DocType, que
não distingue uma Nota de Crédito de uma Fatura normal), `G` = "CÓDIGO SÉRIE/SEQUÊNCIA",
`I1` = código da praça fiscal (não um valor monetário), `I2`-`I8` = base/imposto por taxa na
ordem isenta/reduzida/intermédia/normal, `J`/`K` = 2ª/3ª praça fiscal quando há dados reais
de Açores/Madeira (`Account.at_tax_region`).
**Teste real (2026-08-25, demo.erpnext.pt/NovaDX):** `FT2026NDX0005` →
`D:FT...I1:PT...I7:100.00*I8:23.00`; `NC2026NDX0001` (nota de crédito contra a fatura
anterior) → `D:NC...G:NC NC2026NDX/1` (confirma que a Nota de Crédito não herda o código da
Fatura de origem). `ATCUD Log.qr_code_string` confirmado **byte-a-byte idêntico** ao
`qr_code` gravado no documento e usado na impressão/comunicação — fonte única de verdade,
sem gerador duplicado (o antigo `_build_qr_data_optimized()` foi eliminado no commit
`e29edc8`, ver secção 5 da versão anterior deste documento).

**QR Code na impressão (térmica e A4)**
Ambos os Print Formats reais (`Fatura Simplificada PT` — térmico, `Factura PT` — A4) chamam
`get_qr_code_data(doc=doc)` diretamente. PDF real gerado e verificado nesta auditoria.

**Número de certificado no rodapé**
`{{ frappe.db.get_single_value("Portugal Auth Settings", "software_certificate_number") or "0" }}/AT`,
com aviso adicional "AMBIENTE DE TESTES" quando `sandbox_mode` está ativo — nunca imprime um
número inventado.

---

## 3. Despacho n.º 8632/2014 — SAF-T (PT) v1.04_01

**Estrutura do ficheiro**
[xsd/saftpt1.04_01.xsd](portugal_compliance/xsd/saftpt1.04_01.xsd) incluído no repositório;
namespace `urn:OECD:StandardAuditFile-Tax:PT_1.04_01` confirmado em
[header.xml](portugal_compliance/templates/saft_t/header.xml). Header, MasterFiles e
SourceDocuments gerados e populados; GeneralLedgerEntries omitido por desenho (ver âmbito).

**Validação real contra o XSD**
[saf_t_export_log.py](portugal_compliance/portugal_compliance/doctype/saf_t_export_log/saf_t_export_log.py)
`validate_xml_content()` usa `xmlschema.XMLSchema11` (não `XMLSchema` 1.0 — o XSD da AT
declara `vc:minVersion="1.1"` na raiz; sob 1.0 o próprio elemento `AuditFile` deixa de ser
reconhecido, mascarando todos os erros de conteúdo) contra o schema oficial bundled.
`generate_saft_background()` chama esta validação antes de marcar o export como
`"Completed"` — um ficheiro inválido fica `"Failed"` com os erros reais do schema, e
`download_saft_file` (api/saft_api.py) recusa descarregar qualquer export que não esteja
`"Completed"`.
**Teste real:** SAF-T completo da novadx (2026-01-01 a 2026-12-31, 29 registos) —
`xml_validation_status="Valid"`, 0 erros. Esta validação encontrou e permitiu corrigir 2
defeitos reais pré-existentes (formato de `PaymentRefNo`, asserção `TaxExemptionReason` em
`Payment/Line/Tax`) que nenhuma verificação anterior tinha detetado.

**Documentos anulados**
`InvoiceStatus` = `'A'` para `docstatus=2`
([source_documents.xml:16](portugal_compliance/templates/saft_t/source_documents.xml:16));
`tax_payable`/`net_total`/`gross_total` forçados a `0.00`
([saft_generator.py:541-544](portugal_compliance/utils/saft_generator.py)); ATCUD e hash
originais mantidos como prova de que o documento foi assinado antes de anulado — sem
liquidação indevida de imposto.

**Geração parcial/total**
`generate_saft(company, from_date, to_date, export_type)` aceita qualquer intervalo de
datas — cobre exportação mensal ou anual.

**Praça fiscal (Continente/Açores/Madeira)**
`TaxCountryRegion` — tanto na `TaxTable` mestra
([master_files.xml](portugal_compliance/templates/saft_t/master_files.xml),
`get_tax_table_data`) como por linha de fatura em `SourceDocuments`
([source_documents.xml](portugal_compliance/templates/saft_t/source_documents.xml)) —
extraído estruturalmente de `Account.at_tax_region`, nunca adivinhado a partir da
percentagem de imposto.

**Regime de IVA de Caixa**
Campo `cash_vat_scheme` em Portugal Auth Settings determina `PaymentType` (`RC`/`RG`)
conforme a definição oficial do XSD (`SAFTPTPaymentType`) — não o sentido do pagamento
(Receber/Pagar), erro real encontrado e corrigido nesta auditoria.

**Retenção na fonte**
`_withholding_tax_rows()` mapeia linhas com `is_tax_withholding_account=1`; valor e
descrição mapeados, `WithholdingTaxType` (campo opcional no XSD) omitido por não ter
correspondência fiável no ERPNext.

---

## 4. Numeração Sequencial e Separação de Dados

**Sequencialidade e anti-reutilização**
Sequência extraída de `doc.name` (contador atómico nativo do Frappe), nunca de um contador
paralelo. Lock de série (secção 1) serializa a leitura da hash anterior entre documentos
concorrentes.

**Bloqueio de séries Finalizadas/Anuladas**
`_validate_series_not_inactive()` ([document_hooks.py](portugal_compliance/utils/document_hooks.py)),
hook `validate` nos 4 doctypes fiscais — bloqueia com `frappe.throw` qualquer documento novo
cuja série esteja `is_active=0`. `_setup_automatic_property_setters` reconstrói a lista de
opções do campo Naming Series para refletir isto na UI de imediato.
**Teste real:** tentativa de criar um Payment Entry na série `RC2026NX` (já anulada na AT)
bloqueada corretamente com a mensagem legal exigida.

**Separação Purchase Invoice / documentos internos**
`FISCAL_IMMUTABLE_DOCTYPES` e o dicionário `supported_doctypes` de `document_hooks.py` (a
fonte autoritativa dos `doc_events`) não incluem Purchase Invoice, Stock Entry nem Journal
Entry desde 2026-08-22. Dashboard AT, estatísticas e allowlists de APIs (`atcud_api.py`,
`series_api.py`) filtrados ao mesmo âmbito.

**Pista de auditoria de impressão**
`log_document_print()` (hook `before_print`) regista cada impressão/reimpressão em
`Portugal Document Print Log` — cobre tanto a pré-visualização como a geração de PDF.

---

## 5. Limitações conhecidas (declaradas, não corrigidas nesta sessão)

Secção reescrita em 2026-08-25 com base no código atual e num teste end-to-end real contra
a instalação de referência (demo.erpnext.pt/NovaDX). Os gaps da auditoria anterior já
resolvidos por código (ex.: segundo gerador de QR Code) não são repetidos aqui; os que eram
apenas dados históricos de uma instalação diferente (dev.erpnext.pt/novadx — `FT2026N0001`,
a referência estática pré-2026-08-24, a série `RC-2026-N-5b5cf7`) saíram do âmbito desta
declaração porque essa não é a instalação de referência dos testes atuais.

1. **Série de estorno (NC) não é criada automaticamente pela checkbox de compliance** —
   ativar "Portugal Compliance Enabled" na Company cria as 4 séries transacionais base
   (Fatura, Fatura Simplificada, Recibo, Guia de Remessa) mas não a série de Nota de Crédito:
   o caminho automático (`_create_dynamic_portugal_series_certified` → import quebrado →
   fallback) nunca chama `ensure_return_series_for_company()`. Confirmado ao vivo em
   2026-08-25: a NC só nasceu depois de clicar manualmente em "Gerar Séries Base" (que passa
   pelo caminho correto, `company_api.create_company_series`). Contornável (workaround
   documentado no [manual do utilizador](documentation/user_manual.md), secção 4), mas o
   caminho automático continua incompleto — corrigir a fonte do gap é trabalho de código à
   parte.
2. **`TaxCountryRegion` em `Payment/Line/Tax`** — mantido fixo em `"PT"` (o bloco é sempre a
   isenção fixa M99, sem taxa própria — o recibo herda o imposto já liquidado na fatura de
   origem). Herdar a região do documento de origem referenciado é uma alteração à parte.
   Backlog V1.2.0.
3. **Faturação por terceiros** (emissão em nome de outro sujeito passivo) — sem
   campo/suporte dedicado. Não confirmado se aplicável ao modelo de negócio da NovaDX.
   Backlog V1.2.0.

---

## 6. Referências legais

- Portaria n.º 363/2010, de 23 de junho — Inviolabilidade e assinatura digital
- Portaria n.º 195/2020, de 13 de agosto — Séries documentais, ATCUD e QR Code
- Decreto-Lei n.º 28/2019, de 15 de fevereiro — Faturação eletrónica
- Despacho n.º 8632/2014, de 3 de julho — Estrutura de dados SAF-T (PT) v1.04_01
- Portaria n.º 302/2016, de 2 de dezembro — Ficheiro SAF-T (PT)

*Documento gerado a partir de auditoria de código e testes reais em sandbox. Auditoria
original: 2026-08-17 a 2026-08-23 (dev.erpnext.pt/novadx). Revalidação end-to-end:
2026-08-25 (demo.erpnext.pt/NovaDX). Não substitui a validação formal pela Autoridade
Tributária no processo de certificação.*
