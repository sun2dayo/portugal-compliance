# Manual Técnico para DevOps: Certificados, Chaves e Segredos

**Versão:** 1.1.0

Referência definitiva para a gestão de identidade digital e criptografia no módulo
`portugal_compliance`. Destina-se a DevOps e Administradores de Sistema — não a
programadores da lógica fiscal (ver
[manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md) para essa camada).

---

## 1. Arquitetura de Chave Dupla

O sistema usa dois pares de chave/certificado, com responsabilidades e ciclos de vida
completamente distintos:

| | Chave de Assinatura | Chave/Certificado mTLS |
| :--- | :--- | :--- |
| **Função** | Assinar RSA-SHA1 cada documento fiscal (`sign_document`) | Autenticar o servidor Frappe junto da AT (handshake TLS) |
| **Campo em Portugal Auth Settings** | `invoice_signing_key_path` / `invoice_signing_key_password` | `mtls_certificate_path` / `mtls_private_key_path` |
| **Requisito crítico** | **Continuidade.** Trocar a chave rompe o encadeamento de hash para o próximo documento da série (`previous_signature_hash` deixa de poder ser reverificado com a chave nova contra assinaturas antigas). | **Validade corrente.** Certificados expiram; renovação periódica é normal e esperada. |
| **Impacto de perda/comprometimento** | Grave — implica registar séries novas (ver secção 4) | Moderado — gerar novo par, atualizar campos, sem impacto nos documentos já assinados |
| **Terceira chave**: `at_public_certificate_path` — o certificado **público da AT**, usado para cifrar o bloco de credenciais WS-Security (AES-128 + RSA); não é uma chave própria da empresa, é distribuído pela AT (ver secção 3). |

> **A separação é deliberada.** Usar a mesma chave para assinatura e para mTLS foi um erro
> real identificado no módulo de referência (Dolibarr) numa versão anterior — não repetido
> aqui. Os dois campos são independentes em `Portugal Auth Settings`: renovar o certificado
> de rede nunca requer tocar na chave de assinatura, e vice-versa.

---

## 2. Localização dos Ficheiros — Sem Convenção Imposta

Ao contrário de um módulo com estrutura de pastas fixa
(`documents/certificates/<módulo>/{saft,webservice}/{production,test}/`), o
`portugal_compliance` **não impõe** onde os ficheiros de chave/certificado residem no
sistema de ficheiros do servidor. Cada caminho é um campo de texto livre em
`Portugal Auth Settings`, lido em runtime:

```python
settings = frappe.get_single("Portugal Auth Settings")
key_path = settings.get("invoice_signing_key_path")
with open(key_path, "rb") as key_file:
    key_bytes = key_file.read()
```

Isto dá flexibilidade, mas transfere para o administrador de sistema a responsabilidade de
garantir localização segura e permissões corretas. **Convenção recomendada** (não imposta
pelo código, mas alinhada com a prática do módulo de referência):

```text
/home/frappe/certs/portugal_compliance/
├── signing/
│   ├── production/private_key.pem       (chave de assinatura RSA — produção)
│   └── test/private_key.pem             (chave de assinatura RSA — sandbox)
└── webservice/
    ├── production/
    │   ├── client_cert.pem              (certificado mTLS — produção)
    │   ├── client_key.pem               (chave privada mTLS — produção)
    │   └── at_public_cert.cer           (certificado público da AT)
    └── test/
        └── ...
```

Fora da `webroot` pública do site Frappe (`sites/<site>/public/`), com permissões `0600`
(leitura/escrita apenas pelo utilizador que corre os workers do Frappe).

---

## 3. Segurança de Rede: mTLS + WS-Security

Dois níveis de autenticação, independentes, em toda chamada SOAP à AT:

### 3.1. Nível de Rede — mTLS

```python
def _build_mtls_session(cert_path, key_path):
    session = requests.Session()
    session.cert = (cert_path, key_path)
    return session
```

1. **Server Hello**: a AT apresenta o seu certificado; o cliente Python (via `requests`/
   `zeep.transports.Transport`) valida a cadeia normalmente (HTTPS padrão).
2. **Client Hello (mTLS)**: a AT exige o certificado do cliente — a `requests.Session` com
   `cert=(cert_path, key_path)` apresenta-o automaticamente durante o handshake.
3. **Verificação**: a AT confirma que o certificado é válido, não revogado, emitido por uma
   entidade certificadora reconhecida, e que a chave privada apresentada corresponde
   matematicamente ao certificado.
   * **Erro comum**: falha de handshake / "Could not connect to host" quando a chave e o
     certificado não formam um par válido (par trocado, ou certificado renovado sem
     atualizar a chave correspondente).

### 3.2. Nível Aplicacional — WS-Security Proprietário

```python
def _build_wsse_security_header(at_username, at_password, at_public_cert_path):
    # nonce + timestamp (uso único) + password cifrada com a chave pública da AT (AES-128 + RSA)
    ...
```

A password **nunca viaja em claro** — é cifrada com a chave pública da AT
(`at_public_certificate_path`), combinada com um nonce e timestamp gerados a cada chamada.
Reconstruído em cada pedido SOAP — nunca reutilizado entre chamadas (nonce de uso único).

---

## 4. Procedimentos de Manutenção

### 4.1. Renovar o Certificado mTLS

1. Gerar novo par chave/certificado (ou CSR + resposta da entidade certificadora, conforme o
   processo da AT em vigor).
2. Atualizar `mtls_certificate_path` e `mtls_private_key_path` em `Portugal Auth Settings`
   para os novos ficheiros.
3. **Não tocar** em `invoice_signing_key_path` — são campos independentes.
4. Testar com `test_connection()` (whitelisted, disponível tanto para o webservice de séries
   como para o de faturas) antes de confiar em produção.

### 4.2. Perda ou Comprometimento da Chave de Assinatura

**Cenário crítico.** A chave de assinatura garante a continuidade da cadeia de hash de cada
série (ver [manual_tecnico_series_atcud.md](manual_tecnico_series_atcud.md), secção 3.4).
Se for perdida ou comprometida:

> **Impacto operacional (2026-08-31).** `invoice_signing_key_path` deixou de ser apenas um
> requisito para gerar uma assinatura válida — é agora um **bloqueio rígido de submissão**
> (`before_submit_document`, ver
> [manual_tecnico_hash_documentos.md](manual_tecnico_hash_documentos.md), secção 1.1). Isto
> muda o risco de uma rotação de chave: uma janela em que o campo fica temporariamente vazio
> ou aponta para um ficheiro ilegível já não degrada silenciosamente (documento sem
> assinatura, mas submetido) — **impede a submissão de qualquer Sales Invoice, POS Invoice,
> Payment Entry ou Delivery Note** até o caminho ser corrigido. Planear a rotação para não
> deixar essa janela aberta durante horário de faturação ativa.

1. Gerar uma nova chave privada RSA e atualizar `invoice_signing_key_path` /
   `invoice_signing_key_version` (incrementar a versão, para auditoria).
2. **Obrigatório**: qualquer série ainda ativa que dependa da continuidade de encadeamento
   com a chave antiga deve ser formalmente **finalizada** (`finalizarSerie`, nunca anulada —
   os documentos já emitidos são legítimos) e uma **nova série** registada na AT para uso a
   partir daqui.
3. `verify_signature_chain()` continua a verificar corretamente os documentos assinados com a
   chave antiga (a verificação deriva a chave pública correta a partir de qual chave privada
   está atualmente configurada — para reverificar documentos históricos após a rotação, é
   necessário manter acesso à chave privada antiga separadamente, ou à chave pública
   exportada previamente via `export_signing_public_key()`).

### 4.3. Certificado Público da AT Expirado ou Renovado

A AT renova o seu próprio certificado público raramente. Quando o fizer, o ficheiro em
`at_public_certificate_path` tem de ser substituído pelo novo, disponibilizado no Portal das
Finanças — sem isto, a cifragem do bloco WS-Security deixa de ser aceite pela AT (erros de
autenticação, não de assinatura de documentos).

---

## 5. Diagnóstico

| Ferramenta | Uso |
| :--- | :--- |
| `at_webservice.test_connection()` (whitelisted) | Testa configuração do webservice de séries — mTLS + credenciais presentes, sem submeter nada. |
| `at_invoice_webservice.test_connection()` (whitelisted) | Equivalente para o webservice de faturas. |
| `signature.verify_signing_key_configured()` (whitelisted) | Confirma que a chave de assinatura está configurada, sem expor o caminho a utilizadores sem permissão de leitura em `Portugal Auth Settings`. |
| Tentativa de submissão de um documento fiscal (Sales Invoice/POS Invoice/Payment Entry/Delivery Note) | Desde 2026-08-31, é também um diagnóstico prático: se `invoice_signing_key_path` estiver vazio ou o ficheiro for ilegível, a submissão falha de imediato com *"Emissão bloqueada: A Chave Privada de Assinatura Digital não está configurada..."* — confirma em produção, sem consultar o ficheiro diretamente no servidor. |
| `openssl x509 -in <cert> -text -noout` | Inspeção manual de validade/emissor de um certificado, fora do módulo. |
| `openssl rsa -in <key> -check` | Confirma que uma chave privada é matematicamente válida. |

---

## 6. Nota de Segurança e Permissões

`Portugal Auth Settings` é um Single DocType com `permissions` restrito a `System Manager`
(leitura/escrita/criação apenas — sem `delete`/`email`/`export`/`print`/`report`/`share`),
precisamente porque guarda caminhos para credenciais e chaves sensíveis. Confirmar que
qualquer novo campo adicionado a este DocType segue a mesma política de permissões — não
existe validação automática do Frappe que o garanta por si.

Os ficheiros de chave em si (fora do Frappe, no sistema de ficheiros do servidor) **devem**
ter permissões `0600`, geridas pelo administrador de sistema — o módulo não tenta aplicar
`chmod` automaticamente (ao contrário do módulo de referência, que o fazia via `setup.php`).
