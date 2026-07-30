[CmdletBinding()]
param(
    [string]$ReleaseDir
)

$ErrorActionPreference = 'Stop'
if (-not $ReleaseDir) { $ReleaseDir = Join-Path $PSScriptRoot '..\release' }
$release = (Resolve-Path -LiteralPath $ReleaseDir).Path
$files = @(Get-ChildItem -LiteralPath $release -File | Where-Object {
    $_.Name -like 'ArHub-Setup-*.exe' -or
    $_.Name -like '*.blockmap' -or
    $_.Name -eq 'latest.yml' -or
    $_.Name -like 'sbom-*.cdx.json' -or
    $_.Name -eq 'installer-smoke-report.json'
} | Sort-Object Name)
if ($files.Count -eq 0) { throw "No release files found in $release" }
$lines = @($files | ForEach-Object {
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($_.Name)"
})
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines((Join-Path $release 'SHA256SUMS.txt'), $lines, $utf8)
Write-Host "SHA256SUMS.txt contains $($lines.Count) entries."
