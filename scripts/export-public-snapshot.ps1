[CmdletBinding()]
param(
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Destination) {
    $Destination = Join-Path (Split-Path -Parent $sourceRoot) 'ArHub-open-source'
}
$destinationFull = [System.IO.Path]::GetFullPath($Destination)

if ($destinationFull -eq $sourceRoot) {
    throw 'Destination must be different from the recovery repository.'
}
if (Test-Path -LiteralPath $destinationFull) {
    throw "Destination already exists; refusing to overwrite it: $destinationFull"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sourceRoot 'scripts\open-source-audit.ps1')
if ($LASTEXITCODE -ne 0) {
    throw 'Source open-source audit failed.'
}

Push-Location $sourceRoot
try {
    $files = @(& git ls-files)
    $files += @(& git ls-files --others --exclude-standard)
    $files = @($files | Sort-Object -Unique | Where-Object {
        Test-Path -LiteralPath $_ -PathType Leaf
    })
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Path $destinationFull | Out-Null
foreach ($relativePath in $files) {
    $source = Join-Path $sourceRoot $relativePath
    $destination = Join-Path $destinationFull $relativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
}

& git -C $destinationFull init -b main | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to initialize the clean public repository.'
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $destinationFull 'scripts\open-source-audit.ps1')
if ($LASTEXITCODE -ne 0) {
    throw 'Exported snapshot audit failed.'
}

Write-Host "Exported $($files.Count) files to $destinationFull"
Write-Host 'The clean repository has no commits and no remote.'
