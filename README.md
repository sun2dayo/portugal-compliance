# 🇵🇹 Portugal Compliance para ERPNext

**Versão:** 1.1.0 | **Estado:** Production-Ready & Certificação AT

O **Portugal Compliance** é o motor fiscal definitivo para transformar o ERPNext numa máquina de faturação 100% alinhada com as exigências da Autoridade Tributária Portuguesa. Desenhado para infraestruturas *Enterprise*, este módulo elimina a complexidade técnica e garante total conformidade legal (Portarias n.º 363/2010 e n.º 195/2020) sem comprometer a fluidez e a usabilidade do Frappe.

##  Porquê escolher este módulo?

Ao contrário de adaptações superficiais, esta App atua profundamente no *core* do ERPNext, protegendo a sua empresa com mecanismos de segurança criptográfica, concorrência de base de dados e comunicação assíncrona.

###  Arquitetura de Segurança & Compliance
*   **ATCUD Imutável:** Geração 100% automatizada no momento da submissão. Sem margem para erros humanos ou "rascunhos zombies".
*   **Assinatura RSA-SHA1 Robusta:** Encadeamento criptográfico de ponta a ponta com bloqueios pessimistas (`SELECT ... FOR UPDATE`) na base de dados, garantindo zero colisões ou quebras de *hash* em cenários de alta concorrência.
*   **Garantia de Inviolabilidade:** Uma vez submetidos, os documentos fiscais (Faturas, Recibos, Guias) têm as suas permissões de edição e eliminação revogadas a nível de *backend*.
*   **Trilha de Auditoria Selada:** Todos os *Logs* (ATCUD, Comunicações, Impressões) são escritos estritamente pelo sistema e nativamente bloqueados para edição ou criação manual por qualquer utilizador, protegendo a empresa em caso de inspeção.

###  Comunicação AT em Tempo Real (Webservices)
Autenticação rigorosa (mTLS + WS-Security) para comunicação direta com a Autoridade Tributária, executada em filas de *background* para não congelar o ecrã do utilizador:
*   Registo e Gestão de Séries (`SeriesWSService`).
*   Faturação e Faturação Simplificada (`RegisterInvoice`).
*   Documentos de Transporte / Guias (`envioDocumentoTransporte`).
*   Sistema Inteligente de *Retry* com backoff exponencial automático para tolerância a falhas de rede.

###  Exportação SAF-T (PT) 1.04_01
*   Geração nativa de ficheiros XML (Header, MasterFiles, SourceDocuments) validados estritamente contra o XSD 1.1 oficial. 
*   Suporte a regimes de IVA de Caixa e gestão automática de NIF de Consumidor Final (`999999990`) para retalho.

###  QR Code e Formatos Legais
*   Geração de QR Code (Base64) mapeado com precisão milimétrica.
*   *Print Formats* dedicados em A4 e rolo térmico de 80mm para Faturas, Faturas Simplificadas, Notas de Crédito, Recibos e Guias de Transporte.

---

##  Instalação

O módulo instala-se nativamente no seu ambiente Frappe:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/sun2dayo/portugal-compliance.git --branch main
bench install-app portugal_compliance
```

Após a instalação, centralize toda a gestão de chaves privadas e certificados no DocType seguro **Portugal Auth Settings** e ative o compliance com um clique na ficha da sua Empresa.

---

##  Diagnóstico de Emergência para DevOps

Disponibilizamos comandos CLI para as equipas de sistemas diagnosticarem falhas na Autoridade Tributária sem precisarem de tocar na interface de utilizador:

```bash
# Testa a sessão mTLS com o webservice de séries da AT:
bench --site <site> execute portugal_compliance.utils.diagnostics.test_at_connection

# Verifica matematicamente a validade do par (Chave Privada mTLS + Certificado AT)
# para isolar rapidamente falhas de handshake:
bench --site <site> execute portugal_compliance.utils.diagnostics.verify_key_pair
```

---

## 🤝 Contribuição e Qualidade de Código
Este projeto utiliza `pre-commit` para garantir a excelência técnica (ruff, eslint, prettier). Para contribuir:
```bash
cd apps/portugal_compliance
pre-commit install
```

**Licença:** GPL-3.0
