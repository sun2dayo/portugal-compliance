# Manual de Utilizador: Portugal Compliance

Guia passo-a-passo para configurar a **NovaDX** (ou qualquer empresa portuguesa) no ERPNext
com o módulo `portugal_compliance`, desde o registo da empresa até à primeira exportação
SAF-T. Este manual fala de cliques, campos e ecrãs — não de código. Para a arquitetura
técnica por trás de cada passo, consulte os 12 manuais técnicos nesta mesma pasta.

> **Nota de transparência:** este manual foi escrito a partir de uma simulação real e
> completa, executada de ponta a ponta contra o webservice de testes da Autoridade
> Tributária, num ambiente limpo (`demo.erpnext.pt`, empresa NovaDX, NIF 518747832). Todos os
> valores concretos que aparecem abaixo — ATCUDs, números de documento, séries — são reais,
> gerados nessa simulação, não inventados para efeitos de exemplo. Por limitação técnica da
> ferramenta de navegação usada nesta sessão, não foi possível gravar capturas de ecrã em
> ficheiro para embeber aqui; cada passo descreve com exatidão o que aparece no ecrã (título,
> posição dos campos, texto dos botões, mensagens do sistema) para que possa ser seguido sem
> ambiguidade. Se preferir uma versão ilustrada, os mesmos passos podem ser repetidos com o
> separador **Claude in Chrome** ligado para capturar imagens reais.

---

## 1. Antes de começar

Precisa de:

- Acesso de **Administrador** (ou uma conta com o perfil System Manager) ao ERPNext.
- O **NIF** da empresa e, se já os tiver, os ficheiros de **certificado de assinatura** (chave
  privada RSA em PEM) e de **certificado mTLS** para comunicar com a AT. Em ambiente de
  testes, a Autoridade Tributária disponibiliza um certificado de sandbox próprio para isto;
  fale com o seu contabilista ou com a equipa técnica se não os tiver.
- As **credenciais do webservice da AT** (utilizador no formato `NIF/subutilizador`, ex.
  `518747832/1`, e a respetiva password) — são diferentes do login do Portal das Finanças.

Todo o processo abaixo demora entre 15 a 30 minutos numa empresa nova.

---

## 2. Passo 1 — Criar a Empresa

1. No menu lateral, abra **Organization › Company** e clique em **+ Add Company** (ou aceda
   diretamente ao assistente de configuração inicial do ERPNext, que pede os mesmos dados na
   primeira utilização do sistema).
2. Preencha:
   - **Company Name**: o nome da sua empresa (ex. `NovaDX`).
   - **Company Abbreviation**: uma sigla curta usada como sufixo em contas contabilísticas e
     séries (ex. `NDX`). Depois de gravada, esta sigla não pode ser alterada.
   - **Chart of Accounts**: selecione **Portugal - Plano de Contas SNC**. Isto cria
     automaticamente todas as contas do Sistema de Normalização Contabilística, incluindo as
     subcontas de IVA (2433x) que os documentos fiscais portugueses precisam.
   - **Country**: `Portugal`.
   - **Default Currency**: `EUR`.
3. Grave. A empresa fica criada com o plano de contas português já estruturado — não precisa
   de criar manualmente nenhuma conta de IVA.
4. Abra a ficha da empresa novamente e preencha o campo **NIF** (Número de Identificação
   Fiscal), no formato `518747832`. Este campo é obrigatório em Portugal e é validado pelo
   sistema.
5. Ainda na ficha da empresa, expanda a secção **Address & Contact** e registe a morada da
   sede (Address Line 1, City/Town, Postal Code, Country). **Este passo não é opcional**: a
   exportação SAF-T falha a validação do ficheiro se a empresa não tiver morada completa — o
   sistema recusa gerar um ficheiro que a AT rejeitaria à entrada.

---

## 3. Passo 2 — Configurar as Credenciais da AT (Portugal Auth Settings)

Esta é a página central onde vive tudo o que o sistema precisa para falar com a Autoridade
Tributária: credenciais, certificados e o modo sandbox/produção.

1. Aceda a **Portugal Compliance › Portugal Auth Settings** (é um documento único — não se
   cria um novo, edita-se sempre o mesmo).
2. No topo, um indicador **Stats** mostra o estado atual: antes de configurar nada, verá
   pontos vermelhos como **Certificate Missing** e **Sandbox Mode**.
3. Preencha a secção principal:
   - **SSL Certificate Path**: caminho no servidor para o certificado `.pfx` da AT (se
     aplicável ao seu cenário de autenticação).
   - **Certificate Password**: password desse certificado.
   - **AT Webservice URL**: o endereço do webservice de séries da AT. Em testes, é
     `https://servicos.portaldasfinancas.gov.pt:722/SeriesWSService` — repare na porta `722`,
     que é especificamente a porta de **testes**; a porta de produção é diferente (`422`) e o
     sistema nunca as mistura automaticamente.
   - **Sandbox Mode**: mantenha marcado enquanto estiver a testar. Isto garante que todas as
     comunicações com a AT vão para o ambiente de sandbox, não para produção.
4. Na secção **Chave de Assinatura de Documentos (RSA-SHA1)**:
   - **Caminho da Chave Privada (PEM)**: caminho da chave privada RSA usada para assinar
     digitalmente cada documento emitido. É distinta do certificado do webservice.
   - **Password da Chave Privada**: se a chave estiver protegida por password.
   - **Versão da Chave**: um identificador texto livre (ex. `TESTE-1`) usado para auditoria —
     permite saber, em cada documento assinado, com que versão da chave foi assinado, o que é
     essencial se algum dia rodar a chave.
5. Na secção **Credenciais do Webservice da AT (WS-Security)**:
   - **Utilizador AT (webservice)**: no formato `NIF/subutilizador` (ex. `518747832/1`).
   - **Password AT**: a password correspondente.
   - **Certificado Cliente mTLS (PEM)** e respetiva chave privada: os ficheiros usados para
     autenticação mútua TLS nas chamadas SOAP à AT.
   - **Certificado Público da AT**: o certificado público da própria AT, usado para cifrar
     partes da comunicação (WS-Security).
6. Grave. Se todos os campos obrigatórios estiverem corretos, os indicadores no topo mudam
   para verde.

> Nas empresas onde já existe outra instalação a funcionar (por exemplo, um ambiente de
> desenvolvimento já validado), os mesmos ficheiros de certificado e as mesmas credenciais
> podem ser reutilizados sem alteração — não são específicos de um único site, apenas da
> empresa e do ambiente (teste/produção) a que pertencem.

---

## 4. Passo 3 — Ativar o Portugal Compliance na Empresa

1. Volte a **Organization › Company** e abra a ficha da sua empresa.
2. Marque a checkbox **Portugal Compliance Enabled** (por baixo do campo Country).
3. Clique em **Save**.
4. Ao gravar, o sistema mostra automaticamente uma caixa de diálogo **"Compliance Português
   Ativado!"** a confirmar, em poucos segundos:
   - **4 séries criadas** — as quatro séries fiscais base (Fatura, Fatura Simplificada,
     Recibo, Guia de Remessa) ficam criadas automaticamente, já com o prefixo correto no
     formato `TIPO+ANO+SIGLA` (ex. `FT2026NDX`).
   - **4 Property Setters configurados** — os campos de série (naming series) dos documentos
     de venda passam a mostrar só as séries portuguesas válidas, evitando escolhas incorretas.
   - **Custom fields criados** — os campos fiscais adicionais (ATCUD, referências de isenção,
     etc.) ficam disponíveis nos formulários.
   - **"Comunicação Automática Disponível"** — se as credenciais em Portugal Auth Settings já
     estiverem corretas (como configurado no Passo 2), o sistema informa que pode comunicar as
     séries à AT imediatamente, sem passos adicionais de configuração.
   - Uma nota **"Importante"** lembra: comunique as séries à AT antes de emitir documentos —
     um documento emitido com uma série ainda não comunicada não tem validade fiscal.
5. Feche a caixa de diálogo. Na própria ficha da empresa, uma caixa **"Séries Portuguesas
   Configuradas"** mostra a tabela com as 4 séries, o respetivo tipo de documento e o estado
   (Ativa/Inativa, Comunicada Sim/Não).

---

## 5. Passo 4 — Comunicar as Séries à AT

Uma série só pode ser usada para emitir documentos com valor fiscal depois de comunicada à
Autoridade Tributária — é a AT que atribui o **código de validação** que, mais tarde, entra no
cálculo de cada ATCUD (Código Único de Documento).

1. Na ficha da empresa, no menu superior, clique em **Comunicação AT** (ao lado do menu
   **Portugal Compliance**).
2. Escolha **Comunicar Séries**.
3. O sistema mostra uma confirmação: *"Comunicar todas as séries não comunicadas à AT?"*, com
   dois avisos importantes:
   - Certifique-se de que as credenciais AT estão configuradas (Passo 2).
   - **Esta operação não pode ser desfeita** — cada série comunicada fica registada na AT de
     forma permanente.
4. Confirme com **Yes**. A chamada real ao webservice da AT demora poucos segundos. No fim,
   aparece a mensagem **"Comunicação Iniciada — Processo de comunicação iniciado. Verifique os
   logs para detalhes."**
5. Volte a abrir a ficha da empresa (ou atualize a página). A caixa de estado
   **"Portugal Compliance - Status"** deve agora mostrar **Séries Comunicadas: 4** e cada série
   na tabela passa a **Comunicada: Sim**.
6. Se quiser confirmar o detalhe técnico de cada série (código de validação devolvido pela AT,
   ambiente usado, data de comunicação), consulte **Portugal Compliance › Portugal Series
   Configuration** e abra qualquer uma das quatro séries.

Na simulação real que serviu de base a este manual, as quatro séries ficaram assim depois de
comunicadas:

| Prefixo | Tipo de Documento | Estado |
| :--- | :--- | :--- |
| `FT2026NDX` | Fatura (Sales Invoice) | Ativa · Comunicada |
| `FS2026NDX` | Fatura Simplificada (POS Invoice) | Ativa · Comunicada |
| `RG2026NDX` | Recibo (Payment Entry) | Ativa · Comunicada |
| `GR2026NDX` | Guia de Remessa (Delivery Note) | Ativa · Comunicada |

---

## 6. Passo 5 — Emitir os Primeiros Documentos

Com as séries comunicadas, já pode emitir documentos com valor fiscal. Cada um dos quatro
tipos gera automaticamente um **ATCUD** (Código Único de Documento) e um **QR Code**, ambos
obrigatórios por lei em qualquer fatura, recibo ou guia emitidos em Portugal — não precisa de
configurar nada adicional para isto acontecer.

### 6.1. Antes de emitir: criar um Artigo e um Cliente

Se ainda não tiver itens/clientes de teste:

- **Stock › Item › + Add Item**: preencha Item Code, Item Name, Item Group. Se for um serviço
  (não um produto físico com stock), desmarque **Maintain Stock**.
- **Selling › Customer › + Add Customer**: preencha o nome do cliente.

### 6.2. Fatura (Sales Invoice)

1. Abra **Selling › Sales Invoice › + Add Sales Invoice**.
2. A **Company** e a **Série** (`FT2026NDX.####`) já vêm pré-selecionadas — o sistema sabe,
   pela empresa ativa, qual a série correta a usar.
3. Escolha o **Customer**, adicione uma linha de item (Item, Quantidade, Preço).
4. Em **Sales Taxes and Charges Template**, escolha a taxa de IVA aplicável. O sistema já cria
   automaticamente os quatro templates corretos para Portugal continental:
   - `IVA 23% Normal`
   - `IVA 13% Intermédia`
   - `IVA 6% Reduzida`
   - `IVA 0% Isenta`
5. Grave (**Save**) e depois **Submit** (o botão de submissão definitiva, que confirma:
   *"Permanently Submit FT2026NDX0001?"*).
6. Ao submeter, o documento fica **imediatamente assinado e com ATCUD atribuído** — não há um
   passo manual separado. Na barra lateral do documento, uma caixa
   **"Informações de Compliance Português - Fatura de Venda"** mostra:
   - **ATCUD**: código único (ex. `AAJFJ93MZ2-0001`), com o estado **Conforme** a verde.
   - **Total s/ IVA** e **Total c/ IVA** do documento.
   - O **QR Code** propriamente dito, já pronto para impressão.
7. Para ver a fatura como o cliente a receberia, use **Imprimir › Imprimir Fatura PT** (o
   formato de impressão dedicado do módulo). O documento impresso mostra o cabeçalho da
   empresa, o número da fatura, o ATCUD, o QR Code, a tabela de artigos com IVA discriminado
   por taxa, e o rodapé legal obrigatório: *"Código Único de Documento (ATCUD), gerado
   automaticamente conforme Portaria n.º 195/2020."* — e, em ambiente de testes, a indicação
   **"Processado por programa informático certificado n.º 0/AT — AMBIENTE DE TESTES, sem
   valor fiscal."**, que desaparece automaticamente assim que o Sandbox Mode é desligado.

### 6.3. Recibo (Payment Entry)

1. Abra **Payments › Payment Entry › + Add Payment Entry**.
2. A **Série** já aparece pré-selecionada como `RG2026NDX.####` (Recibo), com a ajuda de
   contexto *"Série portuguesa para recibos. Formato: RC2025EMPRESA.#### (RC=Recibo,
   RB=Recibo Bancário)"*.
3. Escolha **Payment Type: Receive**, o **Party** (cliente), o **Mode of Payment** (ex. Cash) e
   o **Paid Amount**. Repare no aviso *"Valor do pagamento (NIF obrigatório acima de €1000)"*
   — a lei portuguesa exige a identificação fiscal do cliente acima desse valor, e o sistema
   lembra disto no próprio campo.
4. Se quiser associar o recibo a uma fatura específica, clique em **Get Outstanding Invoices**
   na secção **Reference** para trazer automaticamente as faturas em aberto desse cliente.
5. Grave o rascunho normalmente — pode corrigir qualquer campo à vontade nesta fase, incluindo
   depois de gravar uma primeira vez; um recibo em rascunho ainda **não** tem ATCUD nem
   assinatura, exatamente por ainda não ser definitivo. Só depois, ao clicar **Submit**, é que
   o recibo fica assinado e com ATCUD atribuído — tal como a fatura (secção 6.2), este é o
   único momento em que a assinatura é gerada.
6. A partir da submissão, o documento é imutável: o sistema **bloqueia qualquer alteração
   posterior a campos fiscais** (como a data ou o valor). Se precisar de corrigir um recibo já
   submetido, a mensagem do sistema é clara: *"Anule o documento e emita um novo em vez de
   corrigir os valores diretamente"* — este é o princípio de inviolabilidade fiscal exigido
   pela Portaria 195/2020, aplicado a partir do momento em que o documento se torna
   definitivo, nunca antes.

### 6.4. Fatura Simplificada (POS Invoice)

Este documento é o usado em ponto de venda, tipicamente para clientes finais sem NIF definido
ou para valores mais baixos do dia-a-dia.

1. Antes da primeira venda, é preciso configurar um **POS Profile**
   (**Selling › POS › POS Profile › + Add**): dê-lhe um nome, escolha o **Warehouse**, defina
   uma **Conta de Write Off** e o respetivo **Cost Center**, e em **Payment Methods** adicione
   pelo menos um método (ex. Cash) marcado como **Default**. Em **Applicable for Users**,
   adicione os utilizadores autorizados a vender neste perfil.
2. Verifique em **Setup › POS Settings** que o campo **Invoice Type Created via POS Screen**
   está definido como **POS Invoice** — só assim o sistema usa a série `FS2026NDX`
   dedicada à Fatura Simplificada; se estiver como "Sales Invoice", as vendas de balcão
   entram na série de Fatura normal.
3. Abra um turno de caixa: **POS › POS Opening Entry › + Add**, escolha o **POS Profile**
   criado, confirme o **Cashier** e o saldo de abertura, e submeta.
4. Agora pode criar a venda: **POS › POS Invoice › + Add**. O **POS Profile** e a **Série**
   (`FS2026NDX.####`) já vêm preenchidos automaticamente. Escolha o cliente (ou use
   "Consumidor Final", desde que já exista como registo de Cliente), adicione os artigos e o
   template de IVA.
5. No separador **Payments**, o valor a pagar é automaticamente distribuído pelo método de
   pagamento default do perfil (ex. Cash).
6. Grave e submeta. O sistema pergunta de imediato: *"Fatura Submetida — Deseja imprimir o
   recibo térmico agora?"* — o fluxo pensado para um balcão de loja, sem passos extra.
7. No fim do dia, feche o turno em **POS › POS Closing Entry**, associando-o à respetiva
   Opening Entry, para reconciliar os valores movimentados.

### 6.5. Guia de Remessa / Transporte (Delivery Note)

Documento de transporte de mercadorias — tem regras adicionais exigidas pela AT que os outros
três documentos não têm.

1. Abra **Stock › Delivery Note › + Add Delivery Note**. A **Série** já vem pré-selecionada
   como `GR2026NDX.####`.
2. Escolha o **Customer** e adicione a linha de artigo.
3. Abra a linha do artigo (ícone de lápis) e expanda **Item Weight Details**: preencha
   **Weight Per Unit** e **Weight UOM** (ex. `Kg`). A AT exige o peso transportado em
   documentos de transporte — sem isto, o sistema recusa gravar o documento com uma mensagem
   clara: *"Configure o peso dos itens para compliance de transporte."*
4. No separador **Address & Contact**, preencha o campo **Shipping Address** com a morada de
   entrega. Também aqui, o sistema impõe a regra: *"Endereço de entrega é obrigatório para
   guias de transporte portuguesas."* Se a morada ainda não existir, crie-a em **+ Create a new
   Address** — e lembre-se de a associar ao Cliente correto na tabela **Links** da própria
   morada, ou o sistema recusa aceitá-la como morada de entrega desse cliente.
5. Grave e submeta. Tal como os outros documentos, fica com ATCUD e QR Code próprios. Repare
   que, no QR Code, o campo de tipo de documento mostra corretamente **`GR`** — o código real
   da série usada — coerente com o prefixo `GR2026NDX` visível no número do documento.

---

## 7. Passo 6 — Gerar a Exportação SAF-T

O ficheiro SAF-T (Standard Audit File for Tax) é o relatório mensal/anual que resume todas as
transações fiscais da empresa, no formato XML exigido pela AT — é o que se entrega numa
inspeção ou, nalguns regimes, mensalmente por obrigação legal.

1. Aceda a **Portugal Compliance › SAF-T Export Log › + Add SAF-T Export Log**.
2. Preencha:
   - **Company**: a sua empresa.
   - **Export Type**: `Full` para uma exportação completa.
   - **From Date** / **To Date**: o período a exportar (ex. o mês corrente).
3. Grave. A geração do ficheiro acontece automaticamente ao gravar — não há um botão "gerar"
   separado. Em segundos, o registo atualiza-se com:
   - **Status**: `Completed` (ou `Failed`, se algo faltar — ver nota abaixo).
   - **File Name**, **File Hash (SHA256)**, **File Path** e **File Size** do XML gerado.
   - **XML Validation Status**: `Valid` se o ficheiro cumprir integralmente o esquema XSD
     oficial da AT, ou `Invalid` com a lista exata dos erros encontrados.
   - Estatísticas de conteúdo: número de faturas, recibos, guias e outros registos incluídos.
4. Pode descarregar o ficheiro gerado a partir do anexo **File** no topo do registo.

> **O que fazer se o estado for "Failed" com erros de XSD:** na prática, o erro mais comum
> numa empresa nova é a falta da morada da empresa (ver Passo 1, ponto 5) — o esquema oficial
> exige `AddressDetail`, `City` e `PostalCode` preenchidos na morada da empresa, e o sistema
> corretamente recusa produzir um ficheiro que a AT rejeitaria à entrada. Preencha a morada e
> crie um novo SAF-T Export Log; não há necessidade de repetir mais nenhum passo anterior.

---

## 8. Passo 7 — Consultar o Dashboard AT

O Dashboard AT dá uma visão consolidada, em tempo real, do estado de compliance da empresa —
útil para uma verificação rápida sem ter de abrir cada série ou documento individualmente.

1. Aceda a **Portugal Compliance › Dashboard AT**.
2. No topo, um indicador de estado geral (ex. **"Fully Compliant"**) resume, de forma visual,
   se a empresa está com tudo em ordem.
3. Um conjunto de indicadores numéricos mostra, entre outros:
   - **Séries Ativas** e **Séries Comunicadas** (ex. `4` e `4 / 4`).
   - **% Comunicação** — a percentagem de séries ativas já comunicadas à AT (deve estar em
     100%; qualquer valor abaixo disso indica séries pendentes que precisam de ser comunicadas
     antes de serem usadas).
   - **ATCUD Gerados (total)** e **ATCUD Este Mês** — contagem de documentos assinados.
4. Um gráfico de barras **"ATCUD gerados - últimos 6 meses"** mostra a evolução mensal da
   atividade de emissão.
5. A tabela **"Séries por tipo de documento"** discrimina, por tipo (Fatura, Fatura
   Simplificada, Guia de Remessa, Outros Recibos), quantas séries estão ativas e quantas
   comunicadas — permitindo identificar rapidamente se algum tipo de documento específico
   ainda não está pronto para uso.
6. Use o botão **Atualizar**, no canto superior direito, para recalcular os indicadores após
   emitir novos documentos.

---

## 9. Gestão e Manutenção de Séries

Os passos anteriores cobrem o arranque: comunicar, em bloco, todas as séries criadas
automaticamente quando a compliance é ativada. Mas a vida de uma empresa não pára aí — ao
longo do ano vai certamente precisar de criar uma série nova isoladamente (ex. uma segunda
série de Faturas para outro departamento), fechar formalmente uma série no final do ano
fiscal, ou corrigir um erro de configuração antes de a série ter sido usada. Estas três
operações fazem-se todas a partir da própria série, em
**Portugal Compliance › Portugal Series Configuration**, e não do comunicador em bloco da
Empresa usado no Passo 4.

Abra a série que quer gerir. Consoante o estado em que ela se encontra, verá botões
diferentes no topo do documento, agrupados sob o menu **Portugal Compliance**.

### 9.1. Comunicação Individual de uma Série

Se criar uma série nova a meio do ano — por exemplo, ao adicionar manualmente uma segunda
série de Faturas — **não precisa de voltar à Empresa e repetir a comunicação em bloco**. Essa
ação reenviaria também as séries que já estão comunicadas, o que não é necessário. Em vez
disso:

1. Abra a série recém-criada em **Portugal Series Configuration**.
2. Enquanto a série não estiver comunicada, o sistema mostra o botão
   **Comunicar à AT** (menu **Portugal Compliance**, no topo do documento).
3. Clique nele. O sistema pede confirmação: *"Comunicar série {nome da série} à Autoridade
   Tributária?"*.
4. Confirme. A chamada à AT é feita apenas para esta série — as restantes séries da empresa
   não são tocadas.
5. Em caso de sucesso, aparece uma notificação verde:
   *"Série comunicada com sucesso: {código de validação}"*, e o documento recarrega já com o
   estado **Comunicada: Sim** e o código de validação preenchido.

Esta é a forma normal e recomendada de comunicar qualquer série que não tenha sido criada
pelo assistente automático da Empresa (Passo 3) — por exemplo, séries adicionais, séries de
um novo tipo de documento, ou séries de um novo ano fiscal.

### 9.2. Finalizar Série na AT

**Quando usar:** no final do ano fiscal, quando uma série deixa de ser usada por mudança de
sistema, ou sempre que decidir deliberadamente parar de emitir documentos numa série
específica. A AT não permite que uma série fique "em aberto" indefinidamente sem que a
empresa a feche formalmente quando deixa de a usar — é essa formalização que este botão faz.

Finalizar **não apaga nem invalida** nada: os documentos já emitidos nessa série continuam
válidos para sempre. Só impede a emissão de **novos** documentos nela.

1. Abra a série a fechar. O botão **Finalizar Série na AT** só aparece depois de a série já
   estar comunicada (com código de validação atribuído) — não faz sentido fechar na AT algo
   que a AT nem sequer conhece.
2. Clique em **Finalizar Série na AT**. Abre-se uma caixa de diálogo com o mesmo nome, que
   confirma: *"A série {nome} (código {código de validação}) vai ser fechada junto da AT."*
3. Preencha:
   - **Número do Último Documento Emitido**: campo numérico obrigatório, já vem preenchido
     por defeito com o último número realmente emitido nesta série. Confirme que está
     correto — é este valor que a AT regista como o ponto onde a série foi fechada.
   - **Justificação** (opcional): um texto livre curto, para o seu próprio registo interno.
4. Clique em **Finalizar Série**. O sistema mostra a resposta da AT (código e mensagem) numa
   caixa **"Resposta da AT"**.
5. A partir deste momento, a série deixa de estar disponível para emitir novos documentos —
   se tentar usá-la, o sistema bloqueia a criação, tal como bloquearia uma série nunca
   comunicada.

### 9.3. Anular Série na AT

**Quando usar — e quando nunca usar:** a Anulação é uma operação diferente da Finalização, e
a diferença é importante: **anular só deve ser usado para séries criadas por engano e nunca
utilizadas para emitir nenhum documento**. Ao contrário de Finalizar (que fecha uma série com
histórico legítimo), Anular desfaz o registo da série na AT como se ela nunca tivesse sido
comunicada — não é uma operação para "encerrar" uma série que já teve uso normal.

O sistema impõe duas condições rígidas, exigidas pela própria AT, e não deixa anular fora
delas:

- **Só é possível anular no próprio dia em que a série foi comunicada, ou no dia seguinte.**
  Passado esse prazo, a única opção para uma série mal configurada mas já em uso é
  Finalizá-la e criar uma nova série corrigida.
- **A série tem de ter zero documentos emitidos.** Se já emitiu sequer uma fatura, um recibo
  ou uma guia com essa série, não pode anulá-la — só finalizá-la.

Passos:

1. Abra a série a anular. Tal como o botão de Finalizar, **Anular Série na AT** só aparece em
   séries já comunicadas.
2. Clique em **Anular Série na AT**. A caixa de diálogo mostra um aviso explícito (fundo
   amarelo) a repetir as duas condições acima e a informar que o motivo reportado à AT será
   automaticamente **"ER — Anulação por erro de registo"** — o único motivo previsto pela AT
   para este cenário, pelo que não precisa de o escolher manualmente.
3. Marque a checkbox obrigatória **"Confirmo que não foram emitidos documentos com esta
   série"**. O sistema não deixa avançar sem esta confirmação explícita — não vem marcada por
   defeito.
4. Clique em **Anular Série**. O sistema mostra a resposta da AT (código e mensagem).
5. A série fica anulada, como se nunca tivesse existido do ponto de vista da AT — mas o
   registo em si permanece no ERPNext, para auditoria interna do que aconteceu e porquê.

### 9.4. Resumo: Finalizar vs. Anular

| | **Finalizar Série** | **Anular Série** |
| :--- | :--- | :--- |
| **Quando** | Fim de ano fiscal, fim de vida da série, mudança de sistema | Só logo a seguir a uma comunicação feita por engano |
| **Prazo na AT** | Sem limite de tempo | Apenas no dia da comunicação ou no dia seguinte |
| **Documentos já emitidos** | Pode ter qualquer quantidade — ficam válidos | Tem de ter zero |
| **Efeito** | Fecha a série para novos documentos; histórico mantém-se válido | Desfaz o registo, como se a série nunca tivesse sido comunicada |
| **Motivo enviado à AT** | Justificação livre (opcional) | Fixo: "ER — Anulação por erro de registo" |

---

## 10. Comunicação em Tempo Real e Reenvio Manual

Além da exportação SAF-T mensal (Passo 6), a empresa pode optar por comunicar cada fatura
individualmente à AT no momento em que é submetida — o chamado modo **"Tempo Real
(Webservice)"**, configurável em **Portugal Auth Settings**, campo **Método de Comunicação de
Faturas**. Com este modo ativo, cada submissão de Fatura ou Fatura Simplificada dispara, em
segundo plano, uma chamada real à AT logo a seguir à assinatura do documento — sem atrasar a
submissão em si (a chamada corre de forma assíncrona).

### 10.1. Consultar o Estado das Comunicações

Cada tentativa de comunicação fica registada em **Portugal Compliance › Portugal Invoice
Communication Log** (também disponível como atalho no ecrã inicial do Workspace). Cada registo
mostra:

- **Status**: `Pending` (ainda por tentar), `Success` (a AT aceitou), `Failed` (a AT recusou ou
  a ligação falhou) ou `Retrying` (falhou, mas está agendada uma nova tentativa automática).
- **Código de Resposta** e **Mensagem**: a resposta literal devolvida pela AT.
- **Tentativas** e **Próxima Tentativa**: quantas vezes já se tentou, e quando é a próxima
  tentativa automática (o sistema usa um intervalo crescente entre tentativas, até um máximo de
  4 horas, durante até 8 tentativas).

### 10.2. Reenviar Manualmente uma Comunicação Falhada

Se uma comunicação ficar em `Failed` ou `Retrying` e não quiser esperar pela próxima tentativa
automática (por exemplo, depois de corrigir a causa do problema — uma credencial errada, uma
falha de rede temporária), pode forçar o reenvio imediato:

1. Abra o registo em **Portugal Invoice Communication Log**.
2. Clique no botão **Reenviar Agora (Retry)**, visível apenas quando o estado é `Failed` ou
   `Retrying`.
3. Confirme na caixa de diálogo, que mostra também a data da próxima tentativa automática que
   está a ser antecipada.
4. O sistema mostra de imediato se o reenvio teve sucesso ou não, e o registo atualiza-se com o
   novo estado e a resposta da AT.

Isto não cria um novo documento nem uma nova tentativa "extra" fora do histórico — é
exatamente a mesma operação que a tarefa automática horária executaria, apenas disparada por si
de imediato em vez de esperar pelo agendamento.

---

## 11. Resumo do fluxo completo

```
Criar Empresa (NIF + Morada)
        │
        ▼
Configurar Portugal Auth Settings (credenciais + certificados)
        │
        ▼
Ativar "Portugal Compliance Enabled" na Empresa
        │        (cria as 4 séries automaticamente)
        ▼
Comunicar Séries à AT
        │        (obrigatório antes de emitir)
        ▼
Emitir Documentos (Fatura, Recibo, Fatura Simplificada, Guia)
        │        (ATCUD + QR Code gerados automaticamente)
        ▼
Gerar Exportação SAF-T
        │
        ▼
Consultar Dashboard AT para verificação global
```

Cada seta representa uma dependência real imposta pelo próprio sistema — não é possível, por
exemplo, emitir uma fatura numa série não comunicada, nem exportar um SAF-T válido sem a
morada da empresa preenchida. O módulo foi desenhado para que seja difícil saltar um passo por
engano.
