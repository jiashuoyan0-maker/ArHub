[CmdletBinding()]
param(
    [string]$RuntimeDir = (Join-Path $env:LOCALAPPDATA 'Programs\ArHub\runtime'),
    [ValidateSet('pfx', 'azure')]
    [string]$SigningProvider = $(if ($env:ARHUB_SIGNING_PROVIDER) { $env:ARHUB_SIGNING_PROVIDER } else { 'pfx' }),
    [switch]$AllowUnsigned,
    [switch]$SkipTests,
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = (Resolve-Path -LiteralPath $RuntimeDir).Path

Push-Location $projectRoot
try {
    & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime -EnforceLock
    $env:ARHUB_RUNTIME_DIR = $runtime
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONUTF8 = '1'
    $env:PATH = (Join-Path $runtime 'python') + ';' + (Join-Path $runtime 'python\Scripts') + ';' + $env:PATH

    if (-not $SkipTests) {
        & npm ci --ignore-scripts=false
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
        & npm test
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
        & npm run audit:open-source
        if ($LASTEXITCODE -ne 0) { throw 'Open-source audit failed.' }
    }

    $env:ARHUB_SIGNING_PROVIDER = $SigningProvider
    if ($AllowUnsigned) {
        $env:ARHUB_REQUIRE_SIGNING = '0'
        $env:ARHUB_ARTIFACT_SUFFIX = '-unsigned'
        Remove-Item Env:ARHUB_PUBLISHER_NAME -ErrorAction SilentlyContinue
        Remove-Item Env:CSC_LINK -ErrorAction SilentlyContinue
        Remove-Item Env:CSC_KEY_PASSWORD -ErrorAction SilentlyContinue
    } else {
        $env:ARHUB_REQUIRE_SIGNING = '1'
        $env:ARHUB_ARTIFACT_SUFFIX = ''
        & (Join-Path $PSScriptRoot 'signing-preflight.ps1') -Provider $SigningProvider
    }

    $builder = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
    if (-not (Test-Path -LiteralPath $builder -PathType Leaf)) { throw "electron-builder is missing: $builder" }
    $arguments = @('--win', 'nsis', '--x64', '--config', 'electron-builder.config.cjs')
    if ($Publish) { $arguments += @('--publish', 'always') }
    & $builder @arguments
    if ($LASTEXITCODE -ne 0) { throw "electron-builder failed with exit code $LASTEXITCODE" }

    $packagedRuntime = Join-Path $projectRoot 'release\win-unpacked\runtime'
    & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $packagedRuntime -EnforceLock -SkipPythonDependencyCheck

    & (Join-Path $PSScriptRoot 'generate-sbom.ps1') -RuntimeDir $runtime
    & (Join-Path $PSScriptRoot 'create-checksums.ps1')
    if ($AllowUnsigned) {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -AllowUnsigned
    } else {
        & (Join-Path $PSScriptRoot 'verify-release.ps1')
    }
} finally {
    if ($env:ARHUB_EPHEMERAL_CERTIFICATE_PATH) {
        Remove-Item -LiteralPath $env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -Force -ErrorAction SilentlyContinue
        Remove-Item Env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -ErrorAction SilentlyContinue
    }
    Pop-Location
}
