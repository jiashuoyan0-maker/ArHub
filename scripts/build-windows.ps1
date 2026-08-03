[CmdletBinding()]
param(
    [string]$RuntimeDir,
    [ValidateSet('full', 'lite')]
    [string]$RuntimeProfile = $(if ($env:ARHUB_RUNTIME_PROFILE) { $env:ARHUB_RUNTIME_PROFILE } else { 'full' }),
    [ValidateSet('pfx', 'azure')]
    [string]$SigningProvider = $(if ($env:ARHUB_SIGNING_PROVIDER) { $env:ARHUB_SIGNING_PROVIDER } else { 'pfx' }),
    [switch]$AllowUnsigned,
    [switch]$UnsignedRelease,
    [switch]$AllowRuntimeDrift,
    [switch]$SkipTests,
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'runtime-paths.ps1')
$runtime = Resolve-ArHubRuntimeDir -RuntimeDir $RuntimeDir -ProjectRoot $projectRoot
if ($AllowUnsigned -and $UnsignedRelease) {
    throw 'AllowUnsigned and UnsignedRelease are mutually exclusive.'
}
if ($AllowRuntimeDrift -and (-not $AllowUnsigned -or $Publish)) {
    throw 'AllowRuntimeDrift is limited to non-published -AllowUnsigned candidate builds.'
}

Push-Location $projectRoot
try {
    if ($AllowRuntimeDrift) {
        & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime
    } else {
        & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime -EnforceLock
    }
    $env:ARHUB_RUNTIME_DIR = $runtime
    $env:ARHUB_RUNTIME_PROFILE = $RuntimeProfile
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

    if ($AllowUnsigned -or $UnsignedRelease) {
        $env:ARHUB_SIGNING_PROVIDER = 'none'
        $env:ARHUB_REQUIRE_SIGNING = '0'
        $env:ARHUB_ARTIFACT_SUFFIX = if ($UnsignedRelease) { '' } else { '-unsigned' }
        Remove-Item Env:ARHUB_PUBLISHER_NAME -ErrorAction SilentlyContinue
        Remove-Item Env:CSC_LINK -ErrorAction SilentlyContinue
        Remove-Item Env:CSC_KEY_PASSWORD -ErrorAction SilentlyContinue
        Remove-Item Env:WINDOWS_CERTIFICATE_BASE64 -ErrorAction SilentlyContinue
        Remove-Item Env:WINDOWS_CERTIFICATE_PASSWORD -ErrorAction SilentlyContinue
    } else {
        $env:ARHUB_SIGNING_PROVIDER = $SigningProvider
        $env:ARHUB_REQUIRE_SIGNING = '1'
        $env:ARHUB_ARTIFACT_SUFFIX = ''
        & (Join-Path $PSScriptRoot 'signing-preflight.ps1') -Provider $SigningProvider
    }

    $builder = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
    if (-not (Test-Path -LiteralPath $builder -PathType Leaf)) { throw "electron-builder is missing: $builder" }
    $arguments = @('--win', 'nsis', '--x64', '--config', 'electron-builder.config.cjs')
    $arguments += if ($Publish) { @('--publish', 'always') } else { @('--publish', 'never') }
    & $builder @arguments
    if ($LASTEXITCODE -ne 0) { throw "electron-builder failed with exit code $LASTEXITCODE" }

    $packagedRuntime = Join-Path $projectRoot 'release\win-unpacked\runtime'
    if ($RuntimeProfile -eq 'lite') {
        & (Join-Path $PSScriptRoot 'assert-lite-runtime.ps1') -RuntimeDir $packagedRuntime
    } else {
        & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $packagedRuntime -EnforceLock -SkipPythonDependencyCheck
    }

    & (Join-Path $PSScriptRoot 'generate-sbom.ps1') -RuntimeDir $packagedRuntime
    & (Join-Path $PSScriptRoot 'create-checksums.ps1')
    if ($UnsignedRelease) {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -RequireUnsigned -RuntimeProfile $RuntimeProfile
    } elseif ($AllowUnsigned) {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -AllowUnsigned -RuntimeProfile $RuntimeProfile
    } else {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -RuntimeProfile $RuntimeProfile
    }
} finally {
    if ($env:ARHUB_EPHEMERAL_CERTIFICATE_PATH) {
        Remove-Item -LiteralPath $env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -Force -ErrorAction SilentlyContinue
        Remove-Item Env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -ErrorAction SilentlyContinue
    }
    Pop-Location
}
