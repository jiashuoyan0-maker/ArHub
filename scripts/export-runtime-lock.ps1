[CmdletBinding()]
param(
    [string]$RuntimeDir = (Join-Path $env:LOCALAPPDATA 'Programs\ArHub\runtime'),
    [string]$ManifestPath,
    [string]$LockPath,
    [string]$PythonLockPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $ManifestPath) { $ManifestPath = Join-Path $PSScriptRoot '..\packaging\runtime-manifest.json' }
if (-not $LockPath) { $LockPath = Join-Path $PSScriptRoot '..\packaging\runtime-lock.json' }
if (-not $PythonLockPath) { $PythonLockPath = Join-Path $PSScriptRoot '..\packaging\python-requirements.lock.txt' }

$runtime = (Resolve-Path -LiteralPath $RuntimeDir).Path
$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifest = Get-Content -LiteralPath $manifestFile -Encoding UTF8 | ConvertFrom-Json

& (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime -ManifestPath $manifestFile -SkipPythonDependencyCheck

$pythonExe = Join-Path $runtime 'python\python.exe'
$pythonPackages = @(& $pythonExe -X utf8 -m pip freeze --all | Sort-Object)
$utf8 = New-Object System.Text.UTF8Encoding($false)
$pythonLockFullPath = [System.IO.Path]::GetFullPath($PythonLockPath)
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($pythonLockFullPath)) | Out-Null
[System.IO.File]::WriteAllLines($pythonLockFullPath, $pythonPackages, $utf8)

$components = [ordered]@{}
foreach ($component in $manifest.components) {
    $files = @(Get-ChildItem -LiteralPath (Join-Path $runtime $component.name) -File -Recurse -Force)
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    $components[$component.name] = [ordered]@{ files = $files.Count; bytes = [int64]$bytes }
}

$probes = [ordered]@{}
foreach ($component in $manifest.components) {
    foreach ($required in $component.requiredFiles) {
        $relative = [string]$required.path
        $file = Join-Path $runtime ($relative -replace '/', '\')
        $probes[$relative] = [ordered]@{
            bytes = (Get-Item -LiteralPath $file).Length
            sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
}

$lock = [ordered]@{
    schemaVersion = 1
    runtimeVersion = $manifest.runtimeVersion
    architecture = $manifest.architecture
    manifestSha256 = (Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash.ToLowerInvariant()
    pythonRequirementsSha256 = (Get-FileHash -LiteralPath $pythonLockFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    components = $components
    probes = $probes
}
$lockJson = $lock | ConvertTo-Json -Depth 8
$lockFullPath = [System.IO.Path]::GetFullPath($LockPath)
[System.IO.File]::WriteAllText($lockFullPath, $lockJson + "`n", $utf8)

Write-Host "Runtime lock: $lockFullPath"
Write-Host "Python lock:  $pythonLockFullPath"
