# Portugal Compliance

Aplicação para ERPNext que implementa os requisitos fiscais portugueses, incluindo comunicação de séries à AT, ATCUD, assinatura digital e QRCode.

## Visão Geral

A aplicação `portugal_compliance` implementa os requisitos fiscais portugueses para o ERPNext, seguindo as especificações da Autoridade Tributária (AT). A aplicação segue um fluxo sequencial:

1. **Comunicação de Séries à AT via Webservice SOAP**
2. **Geração e Armazenamento do ATCUD**
3. **Assinatura Digital (incluindo ATCUD)**
4. **Geração do QRCode (incluindo ATCUD e caracteres da assinatura)**

## Instalação e Configuração

### Pré-requisitos

- ERPNext v14 ou superior
- Python 3.10 ou superior
- Certificado digital para comunicação com a AT
- Chave privada RSA para assinatura digital
- Chave pública da AT para cifra de credenciais
- Credenciais de acesso ao Portal das Finanças

### Instalação

```bash
# Navegar para o diretório bench
cd /path/to/bench

# Obter a aplicação do repositório
bench get-app https://github.com/seu-repositorio/portugal_compliance.git

# Instalar a aplicação no site
bench --site seu-site install-app portugal_compliance

# Instalar dependências
bench pip install -r apps/portugal_compliance/requirements.txt
```

### Configuração Inicial

Após a instalação, é necessário configurar:

1. **PT Compliance Settings**: Configurações globais da aplicação
   - Credenciais da AT
   - Caminhos para certificados e chaves
   - Informações do produtor do software

2. **PT Document Series**: Séries documentais a serem comunicadas à AT
   - Cada série deve ser configurada e comunicada antes de ser utilizada

## Documentação

Para documentação detalhada sobre a arquitetura, módulos, fluxo de trabalho, segurança e resolução de problemas, consulte o arquivo [DOCUMENTATION.md](DOCUMENTATION.md).

## Licença

Este projeto está licenciado sob a [GNU General Public License v3.0](LICENSE).

## Suporte e Contribuições

Para suporte ou contribuições, entre em contato:

- Email: app@novadx.eu
- GitHub: https://github.com/seu-repositorio/portugal_compliance
