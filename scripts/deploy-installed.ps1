[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'Programs\ArHub'),
    [switch]$StopRunning
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installDirResolved = (Resolve-Path -LiteralPath $InstallDir).Path
$appDir = Join-Path $installDirResolved 'resources\app'
$exePath = Join-Path $installDirResolved 'ArHub.exe'

if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
    throw "Expected installed executable was not found: $exePath"
}
if (-not (Test-Path -LiteralPath $appDir -PathType Container)) {
    throw "Expected resources\app directory was not found: $appDir"
}

$running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    try { $_.Path -eq $exePath } catch { $false }
})
if ($running.Count -gt 0 -and -not $StopRunning) {
    throw 'ArHub is running. Close it or pass -StopRunning before deployment.'
}
foreach ($process in $running) {
    $null = $process.CloseMainWindow()
    if (-not $process.WaitForExit(5000)) {
        Stop-Process -Id $process.Id -Force
    }
}

$relativeFiles = @(
    'icon.ico'
    'main.js'
    'package.json'
    'updater.js'
    'updater-config.json'
    'extension.schema.json'
    'extensions\core\manifest.json'
    'extensions\diagram\manifest.json'
    'extensions\web\manifest.json'
    'backend\config.py'
    'backend\extension_registry.py'
    'backend\main.py'
    'backend\provider_urls.py'
    'backend\routers\artifacts.py'
    'backend\routers\extensions.py'
    'dist\favicon.svg'
    'dist\index.html'
    'dist\logo.svg'
    'dist\splash.html'
    'dist\assets\index-BabYh3e1.js'
    'dist\assets\apple-ui-20260727.css'
    'dist\assets\arhub-icons.js'
    'dist\assets\arhub-codex-shell.css'
    'dist\assets\arhub-codex-desktop.css'
    'dist\assets\arhub-editor-studio.css'
    'dist\assets\arhub-studio-shell.css'
    'dist\assets\arhub-glass.css'
    'dist\assets\arhub-codex-shell.js'
    'dist\assets\arhub-codex-desktop.js'
    'dist\assets\arhub-editor-studio.js'
    'dist\assets\arhub-studio-shell.js'
    'dist\assets\arhub-workspace.css'
    'dist\assets\arhub-workspace.js'
)

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $installDirResolved ".arhub-backups\$timestamp"
$deployed = New-Object System.Collections.Generic.List[string]

foreach ($relativePath in $relativeFiles) {
    $source = Join-Path $sourceRoot $relativePath
    $destination = Join-Path $appDir $relativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Deployment source is missing: $source"
    }

    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        $backup = Join-Path $backupRoot $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $destination -Destination $backup -Force
    }

    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    $deployed.Add($relativePath)
}

$manifest = [ordered]@{
    deployed_at = (Get-Date).ToString('o')
    source_root = $sourceRoot
    install_dir = $installDirResolved
    backup_dir = $backupRoot
    files = $deployed
}
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backupRoot 'deployment.json') -Encoding UTF8

Write-Host "Deployed $($deployed.Count) files to $appDir"
Write-Host "Backup: $backupRoot"
