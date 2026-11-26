param(
    [Parameter(Mandatory)]
    [ValidateSet('limpa', 'atualizacao')]
    [string]$Cenario
)

$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Use um runner Windows descartável.'
}

$api = 'http://127.0.0.1:8000'
$destino = Join-Path $env:RUNNER_TEMP 'lead-scraper-validacao'
if ((Test-Path (Join-Path $env:APPDATA 'com.leadscraper.app')) -or (Test-Path $destino)) {
    throw 'O cenário exige uma instalação e um perfil sem dados anteriores.'
}

function Instalar-Programa([string]$Instalador) {
    $instalacao = Start-Process -FilePath $Instalador -ArgumentList @('/S', "/D=$destino") -WindowStyle Hidden -PassThru -Wait
    if ($instalacao.ExitCode -ne 0) { throw "Instalador retornou $($instalacao.ExitCode)." }
    $executavel = Get-ChildItem -LiteralPath $destino -File |
        Where-Object { $_.Name -match '^lead[ .-]scraper\.exe$' } |
        Select-Object -First 1
    if (-not $executavel) { throw 'Executável do Lead Scraper não encontrado.' }
    return $executavel.FullName
}

function Aguardar-Backend($Processo, [string]$Versao = '') {
    for ($tentativa = 0; $tentativa -lt 45; $tentativa++) {
        if ($Processo.HasExited) { throw 'O aplicativo encerrou durante a inicialização.' }
        try {
            $saude = Invoke-RestMethod "$api/health" -TimeoutSec 2
            if ($saude.db_ready -and (!$Versao -or $saude.desktopVersion -eq $Versao)) { return }
        } catch {
        }
        Start-Sleep -Seconds 1
    }
    Get-ChildItem -Path (Join-Path $env:APPDATA 'com.leadscraper.app') -Filter '*.log' |
        ForEach-Object { Write-Host $_.Name; Get-Content -LiteralPath $_.FullName -Tail 80 }
    throw 'O sidecar não confirmou a disponibilidade do banco.'
}

function Encerrar-Programa($Processo) {
    if ($Processo.HasExited) { return }
    if ($Processo.CloseMainWindow() -and $Processo.WaitForExit(10000)) { return }
    # encerra somente a árvore do aplicativo de teste
    & taskkill.exe /PID $Processo.Id /T /F | Out-Null
    if (-not $Processo.WaitForExit(10000)) { throw 'O aplicativo de teste não encerrou.' }
}

$candidato = Get-ChildItem -Path 'candidato/nsis/*-setup.exe' -File | Select-Object -First 1
if (-not $candidato -or -not (Test-Path -LiteralPath "$($candidato.FullName).sig")) {
    throw 'Instalador NSIS assinado não encontrado.'
}

if ($Cenario -eq 'atualizacao') {
    $antigo = Join-Path $env:RUNNER_TEMP 'Lead.Scraper_0.5.0_x64-setup.exe'
    $release = 'https://github.com/eduardocicutti/leadscraper/releases/download/v0.5.0'
    Invoke-WebRequest "$release/Lead.Scraper_0.5.0_x64-setup.exe" -OutFile $antigo
    $hashes = (Invoke-WebRequest "$release/SHA256SUMS.txt").Content
    if ($hashes -is [byte[]]) { $hashes = [Text.Encoding]::UTF8.GetString($hashes) }
    $hash = (Get-FileHash -LiteralPath $antigo -Algorithm SHA256).Hash
    if ($hashes -notmatch "(?im)^$hash\s+.*setup\.exe\s*$") {
        throw 'O checksum do instalador anterior não confere.'
    }
    $processo = Start-Process -FilePath (Instalar-Programa $antigo) -WindowStyle Hidden -PassThru
    try {
        Aguardar-Backend $processo
        $exemplo = @{ nome = 'Lead de atualizacao QA'; cidade = 'Campinas'; estado = 'SP'; telefone = '(19) 99000-1234' }
        $corpo = @{ leads = @($exemplo) } | ConvertTo-Json -Depth 4
        Invoke-RestMethod "$api/selected-leads" -Method Post -ContentType 'application/json' -Body $corpo | Out-Null
    } finally {
        Encerrar-Programa $processo
    }
}

$processo = Start-Process -FilePath (Instalar-Programa $candidato.FullName) -WindowStyle Hidden -PassThru
try {
    Aguardar-Backend $processo '0.6.0'
    $municipios = Invoke-RestMethod "$api/api/v1/localidades/municipios?uf=SP&busca=campinas"
    if ($municipios.itens[0].codigo -ne 3509502) { throw 'Catálogo empacotado inválido.' }
    $empresas = Invoke-RestMethod "$api/api/v1/crm/empresas"
    if ($empresas.total -ne 0) { throw 'O CRM de teste deveria começar sem empresas.' }
    $leads = Invoke-RestMethod "$api/selected-leads"
    if ($Cenario -eq 'atualizacao') {
        if ($leads.Count -ne 1 -or $leads[0].nome -ne 'Lead de atualizacao QA') {
            throw 'A atualização não preservou o lead da versão anterior.'
        }
        $id = $leads[0].id
        $vinculo = Invoke-RestMethod "$api/api/v1/crm/selecionados/$id/converter" -Method Post -Body '{}' -ContentType 'application/json'
        if (-not $vinculo.empresaId) { throw 'O lead migrado não pôde ser convertido.' }
    } elseif ($leads.Count -ne 0) {
        throw 'A instalação limpa deveria começar sem leads.'
    }
    Write-Host "Instalação $Cenario validada."
} finally {
    Encerrar-Programa $processo
}
