[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundleDir,
    [string]$DestinationDir
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$bundleRoot = (Resolve-Path -LiteralPath $BundleDir).Path
$bundlePath = Join-Path $bundleRoot 'runtime-bundle.json'
if (-not (Test-Path -LiteralPath $bundlePath -PathType Leaf)) { throw "runtime-bundle.json is missing: $bundlePath" }
$bundle = Get-Content -LiteralPath $bundlePath -Encoding UTF8 | ConvertFrom-Json

if (-not $DestinationDir) {
    $DestinationDir = Join-Path $projectRoot ".runtime\restored\$($bundle.runtimeVersion)"
}
$destination = [System.IO.Path]::GetFullPath($DestinationDir)
if (Test-Path -LiteralPath $destination) {
    $existing = @(Get-ChildItem -LiteralPath $destination -Force)
    if ($existing.Count -gt 0) { throw "Runtime restore destination is not empty: $destination" }
} else {
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
}

$sevenZip = Join-Path $projectRoot 'node_modules\7zip-bin\win\x64\7za.exe'
if (-not (Test-Path -LiteralPath $sevenZip -PathType Leaf)) { throw '7za.exe was not found. Run npm ci first.' }

foreach ($component in $bundle.components) {
    foreach ($part in $component.parts) {
        $partPath = Join-Path $bundleRoot $part.name
        if (-not (Test-Path -LiteralPath $partPath -PathType Leaf)) { throw "Runtime archive part is missing: $($part.name)" }
        $item = Get-Item -LiteralPath $partPath
        if ($item.Length -ne [int64]$part.bytes) { throw "Runtime archive size mismatch: $($part.name)" }
        $hash = (Get-FileHash -LiteralPath $partPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $part.sha256) { throw "Runtime archive hash mismatch: $($part.name)" }
    }
    $firstPart = Join-Path $bundleRoot $component.extractFrom
    Write-Host "Restoring runtime component: $($component.name)"
    & $sevenZip x -y "-o$destination" $firstPart
    if ($LASTEXITCODE -ne 0) { throw "7-Zip extraction failed for $($component.name)" }
}

& (Join-Path $PSScriptRoot 'assert-runtime.ps1') `
    -RuntimeDir $destination `
    -ManifestPath (Join-Path $bundleRoot 'runtime-manifest.json') `
    -LockPath (Join-Path $bundleRoot 'runtime-lock.json') `
    -PythonLockPath (Join-Path $bundleRoot 'python-requirements.lock.txt') `
    -EnforceLock

Write-Host "Runtime restored and verified: $destination"
