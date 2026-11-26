param([Parameter(Mandatory)][string]$Instalador)

$ErrorActionPreference = 'Stop'
$configuracao = Get-Content -LiteralPath 'src-tauri/tauri.conf.json' -Raw | ConvertFrom-Json
$configuracaoAnterior = git show v0.5.0:src-tauri/tauri.conf.json | ConvertFrom-Json
if ($configuracao.plugins.updater.pubkey -ne $configuracaoAnterior.plugins.updater.pubkey) {
    throw 'A chave de atualização mudou desde a v0.5.0.'
}
$programa = Resolve-Path 'build/minisign-0.12/minisign-win64/x86_64/minisign.exe'
$alvo = (Resolve-Path -LiteralPath $Instalador).Path
$chave = "$alvo.pub"
$assinatura = "$alvo.minisig"
$codificada = [IO.File]::ReadAllText("$alvo.sig").Trim()
[IO.File]::WriteAllBytes($chave, [Convert]::FromBase64String($configuracao.plugins.updater.pubkey))
[IO.File]::WriteAllBytes($assinatura, [Convert]::FromBase64String($codificada))
& $programa -Vm $alvo -p $chave -x $assinatura
if ($LASTEXITCODE) { throw 'A assinatura do instalador não é compatível com a chave do updater.' }
