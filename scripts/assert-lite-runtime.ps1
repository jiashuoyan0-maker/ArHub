[CmdletBinding()]
param(
    [string]$RuntimeDir,
    [string]$ManifestPath,
    [string]$LockPath,
    [string]$PythonLockPath,
    [switch]$AllowOptionalComponents,
    [switch]$EnforceLock
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'runtime-paths.ps1')
$RuntimeDir = Resolve-ArHubRuntimeDir -RuntimeDir $RuntimeDir -ProjectRoot $projectRoot
if (-not $ManifestPath) { $ManifestPath = Join-Path $projectRoot 'packaging\runtime-manifest.json' }
if (-not $LockPath) { $LockPath = Join-Path $projectRoot 'packaging\runtime-lock.json' }
if (-not $PythonLockPath) { $PythonLockPath = Join-Path $projectRoot 'packaging\python-requirements.lock.txt' }

$runtime = [System.IO.Path]::GetFullPath($RuntimeDir)
if (-not (Test-Path -LiteralPath $runtime -PathType Container)) {
    throw "Lite runtime directory does not exist: $runtime"
}

$python = Join-Path $runtime 'python\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Lite runtime is missing Python: $python"
}

$excludedComponents = @('node', 'git', 'pandoc', 'draw.io', 'texlive')
if (-not $AllowOptionalComponents) {
    foreach ($component in $excludedComponents) {
        if (Test-Path -LiteralPath (Join-Path $runtime $component)) {
            throw "Lite runtime unexpectedly contains optional component: $component"
        }
    }
}

$probe = @'
import importlib
import importlib.metadata
modules = [
    'fastapi', 'uvicorn', 'aiosqlite', 'httpx', 'websockets', 'pydantic',
    'multipart', 'docx', 'openpyxl', 'PIL', 'cryptography'
]
for name in modules:
    importlib.import_module(name)
print('lite-runtime-core-ok')
print('cryptography=' + importlib.metadata.version('cryptography'))
'@
$output = (& $python -B -X utf8 -c $probe 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $output -notmatch 'lite-runtime-core-ok') {
    throw "Lite Python runtime dependency probe failed: $output"
}

$pipCheck = (& $python -B -X utf8 -m pip check 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Lite Python runtime dependency check failed: $pipCheck"
}

if ($EnforceLock) {
    foreach ($requiredPath in @($ManifestPath, $LockPath, $PythonLockPath)) {
        if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            throw "Lite runtime lock input is missing: $requiredPath"
        }
    }

    $manifest = Get-Content -LiteralPath $ManifestPath -Encoding UTF8 | ConvertFrom-Json
    $lock = Get-Content -LiteralPath $LockPath -Encoding UTF8 | ConvertFrom-Json
    if ($lock.runtimeVersion -ne $manifest.runtimeVersion) {
        throw 'Runtime lock version does not match the manifest.'
    }
    $manifestHash = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $requirementsHash = (Get-FileHash -LiteralPath $PythonLockPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($lock.manifestSha256 -ne $manifestHash) { throw 'Runtime manifest hash does not match the lock.' }
    if ($lock.pythonRequirementsSha256 -ne $requirementsHash) { throw 'Python requirements hash does not match the lock.' }

    $expectedPackages = @(Get-Content -LiteralPath $PythonLockPath -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') })
    $expectedSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $expectedPackages) { $null = $expectedSet.Add([string]$entry) }
    $actualPackages = @(& $python -B -X utf8 -m pip freeze --all)
    $unexpectedPackages = @($actualPackages | Where-Object { -not $expectedSet.Contains([string]$_) })
    if ($unexpectedPackages.Count -gt 0) {
        throw "Lite runtime contains packages outside the lock:`n$($unexpectedPackages -join "`n")"
    }

    $expectedCryptography = @($expectedPackages | Where-Object { $_ -match '^cryptography==' })
    if ($expectedCryptography.Count -ne 1) { throw 'The Python lock must contain exactly one cryptography version.' }
    $actualCryptography = if ($output -match '(?m)^cryptography=(.+)$') { $Matches[1].Trim() } else { '' }
    if ($expectedCryptography[0] -ne "cryptography==$actualCryptography") {
        throw "cryptography version mismatch: $actualCryptography"
    }

    foreach ($probeProperty in $lock.probes.PSObject.Properties) {
        if (-not $probeProperty.Name.StartsWith('python/')) { continue }
        $probePath = Join-Path $runtime ($probeProperty.Name -replace '/', '\')
        if (-not (Test-Path -LiteralPath $probePath -PathType Leaf)) {
            throw "Locked Lite runtime probe is missing: $($probeProperty.Name)"
        }
        $probeItem = Get-Item -LiteralPath $probePath
        if ($probeItem.Length -ne [int64]$probeProperty.Value.bytes) {
            throw "Locked Lite runtime probe size changed: $($probeProperty.Name)"
        }
        $probeHash = (Get-FileHash -LiteralPath $probePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($probeHash -ne $probeProperty.Value.sha256) {
            throw "Locked Lite runtime probe hash changed: $($probeProperty.Name)"
        }
    }
}

[pscustomobject]@{
    RuntimeDir = $runtime
    Profile = 'lite'
    LockEnforced = [bool]$EnforceLock
    Status = 'Valid'
} | Format-List
