# Release e assinatura

## Instalador recomendado

Para o comercial, publique o instalador NSIS:

```text
Lead Scraper_*_x64-setup.exe
```

Evite enviar o instalador por WhatsApp ou zip manual. Publique no GitHub Releases e envie o link do release.

## Atualizacao automatica

O app usa o updater oficial do Tauri apontando para:

```text
https://github.com/eduardocicutti/leadscraper/releases/latest/download/latest.json
```

O workflow `.github/workflows/release.yml` gera e publica o `latest.json` quando uma tag `v*` e enviada ao GitHub.

Configure estes secrets no GitHub antes do proximo release:

```text
TAURI_SIGNING_PRIVATE_KEY
TAURI_SIGNING_PRIVATE_KEY_PASSWORD
```

No computador local, a chave privada gerada esta em:

```text
updater-private.key
```

Copie o conteudo desse arquivo para o secret `TAURI_SIGNING_PRIVATE_KEY`. A chave foi gerada sem senha, entao `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` pode ficar vazio ou nao ser criado.

Importante: nao perca `updater-private.key`. Sem ela, usuarios que instalaram uma versao com updater assinado por essa chave nao conseguirao atualizar automaticamente para novas versoes.

## Assinatura de codigo Windows

O updater assina os pacotes para o Tauri validar atualizacoes. Isso e diferente da assinatura Authenticode do Windows, que reduz alertas de SmartScreen.

Para assinar o instalador como fornecedor confiavel, compre um certificado Code Signing OV ou EV e configure o signing do Windows no workflow. Enquanto isso nao existir, o app pode continuar funcionando, mas o Windows pode exibir avisos para alguns usuarios.

Secrets normalmente usados para Authenticode:

```text
WINDOWS_CERTIFICATE
WINDOWS_CERTIFICATE_PASSWORD
```

Depois de comprar o certificado, adicione um `signCommand` no `src-tauri/tauri.conf.json` ou um passo com `signtool.exe` no workflow.
