[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundleDir,
    [string]$ExpectedDir
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$bundle = (Resolve-Path -LiteralPath $BundleDir).Path
if (-not $ExpectedDir) { $ExpectedDir = Join-Path $projectRoot 'packaging' }
$expected = (Resolve-Path -LiteralPath $ExpectedDir).Path

$metadataNames = @(
    'runtime-bundle.json',
    'runtime-manifest.json',
    'runtime-lock.json',
    'python-requirements.lock.txt'
)

foreach ($name in $metadataNames) {
    $expectedPath = Join-Path $expected $name
    $actualPath = Join-Path $bundle $name
    if (-not (Test-Path -LiteralPath $expectedPath -PathType Leaf)) { throw "Expected runtime metadata is missing: $expectedPath" }
    if (-not (Test-Path -LiteralPath $actualPath -PathType Leaf)) { throw "Downloaded runtime metadata is missing: $actualPath" }
    $expectedHash = (Get-FileHash -LiteralPath $expectedPath -Algorithm SHA256).Hash
    $actualHash = (Get-FileHash -LiteralPath $actualPath -Algorithm SHA256).Hash
    if ($expectedHash -ne $actualHash) { throw "Runtime metadata does not match the repository lock: $name" }
}

$bundleManifest = Get-Content -LiteralPath (Join-Path $expected 'runtime-bundle.json') -Encoding UTF8 | ConvertFrom-Json
$archiveRecords = @($bundleManifest.components | ForEach-Object { $_.parts } | ForEach-Object { $_ })
$allowedNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in $metadataNames) { $null = $allowedNames.Add($name) }
$null = $allowedNames.Add('SHA256SUMS.txt')
foreach ($record in $archiveRecords) { $null = $allowedNames.Add([string]$record.name) }

$actualFiles = @(Get-ChildItem -LiteralPath $bundle -File)
$unexpected = @($actualFiles | Where-Object { -not $allowedNames.Contains($_.Name) })
if ($unexpected.Count -gt 0) { throw "Runtime bundle contains unexpected files: $($unexpected.Name -join ', ')" }
$missing = @($allowedNames | Where-Object { -not (Test-Path -LiteralPath (Join-Path $bundle $_) -PathType Leaf) })
if ($missing.Count -gt 0) { throw "Runtime bundle is incomplete: $($missing -join ', ')" }

foreach ($record in $archiveRecords) {
    $archivePath = Join-Path $bundle ([string]$record.name)
    $item = Get-Item -LiteralPath $archivePath
    if ($item.Length -ne [int64]$record.bytes) { throw "Runtime archive size mismatch: $($record.name)" }
    $hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne [string]$record.sha256) { throw "Runtime archive hash mismatch: $($record.name)" }
}

$checksumPath = Join-Path $bundle 'SHA256SUMS.txt'
$checksumRecords = @{}
foreach ($line in Get-Content -LiteralPath $checksumPath -Encoding UTF8) {
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid SHA256SUMS.txt line: $line" }
    $checksumRecords[$Matches[2]] = $Matches[1].ToLowerInvariant()
}
foreach ($file in $actualFiles | Where-Object Name -ne 'SHA256SUMS.txt') {
    if (-not $checksumRecords.ContainsKey($file.Name)) { throw "SHA256SUMS.txt is missing: $($file.Name)" }
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $checksumRecords[$file.Name]) { throw "SHA256SUMS.txt mismatch: $($file.Name)" }
}
if ($checksumRecords.Count -ne ($actualFiles.Count - 1)) { throw 'SHA256SUMS.txt contains unexpected entries.' }

Write-Host "Runtime bundle verification passed: $bundle"
