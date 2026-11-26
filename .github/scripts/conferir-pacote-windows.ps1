param([Parameter(Mandatory)][string]$Pasta)

$ErrorActionPreference = 'Stop'
$manifesto = Join-Path $Pasta 'SHA256SUMS.txt'
$linhas = Get-Content -LiteralPath $manifesto
foreach ($extensao in @('exe', 'msi')) {
    $arquivo = Get-ChildItem -LiteralPath $Pasta -Recurse -File |
        Where-Object { $_.Extension -eq ".$extensao" -and $_.Name -match '0\.6\.0_x64' } |
        Select-Object -First 1
    if (-not $arquivo) { throw "Instalador $extensao ausente." }
    $hash = (Get-FileHash -LiteralPath $arquivo.FullName -Algorithm SHA256).Hash
    $nomeEsperado = [regex]::Escape($arquivo.Name).Replace('\.', '[. ]')
    if (-not ($linhas -match "(?i)^$hash\s+$nomeEsperado$")) {
        # GitHub normaliza os espaços dos nomes ao publicar os arquivos.
        if (-not ($linhas -match "(?i)^$hash\s+.*0\.6\.0_x64.*\.$extensao$")) {
            throw "Checksum não confere para $($arquivo.Name)."
        }
    }
    & "$PSScriptRoot/conferir-assinatura-release.ps1" -Instalador $arquivo.FullName
    Write-Host "SHA-256 e assinatura conferidos para $($arquivo.Name)."
}
