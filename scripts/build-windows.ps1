[CmdletBinding()]
param(
    [string]$RuntimeDir,
    [ValidateSet('full', 'lite', 'app-only')]
    [string]$RuntimeProfile = $(if ($env:ARHUB_RUNTIME_PROFILE) { $env:ARHUB_RUNTIME_PROFILE } else { 'lite' }),
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
$isAppOnly = $RuntimeProfile -eq 'app-only'
$runtime = if ($isAppOnly) { $null } else { Resolve-ArHubRuntimeDir -RuntimeDir $RuntimeDir -ProjectRoot $projectRoot }
if ($AllowUnsigned -and $UnsignedRelease) {
    throw 'AllowUnsigned and UnsignedRelease are mutually exclusive.'
}
if ($AllowRuntimeDrift -and (-not $AllowUnsigned -or $Publish)) {
    throw 'AllowRuntimeDrift is limited to non-published -AllowUnsigned candidate builds.'
}
if ($isAppOnly -and $AllowRuntimeDrift) {
    throw 'AllowRuntimeDrift cannot be used for an app-only package because no runtime is bundled.'
}

Push-Location $projectRoot
try {
    $originalPath = $env:PATH
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'scripts\verify-capabilities.cjs') -PathType Leaf)) {
        throw 'Capability verification script is missing.'
    }
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCommand) { throw 'Node.js is required for capability verification and packaging.' }
    & $nodeCommand.Source scripts/verify-capabilities.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Capability verification failed.' }

    if (-not $isAppOnly) {
        if ($RuntimeProfile -eq 'lite') {
            $liteValidation = @('-RuntimeDir', $runtime, '-AllowOptionalComponents')
            if (-not $AllowRuntimeDrift) { $liteValidation += '-EnforceLock' }
            & (Join-Path $PSScriptRoot 'assert-lite-runtime.ps1') @liteValidation
        } elseif ($AllowRuntimeDrift) {
            & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime
        } else {
            & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime -EnforceLock
        }
        $env:ARHUB_RUNTIME_DIR = $runtime
        $env:PATH = (Join-Path $runtime 'python') + ';' + (Join-Path $runtime 'python\Scripts') + ';' + $env:PATH
    } else {
        Remove-Item Env:ARHUB_RUNTIME_DIR -ErrorAction SilentlyContinue
    }
    $env:ARHUB_RUNTIME_PROFILE = $RuntimeProfile
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONUTF8 = '1'

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

    $unpacked = Join-Path $projectRoot 'release\win-unpacked'
    $packagedRuntime = Join-Path $unpacked 'runtime'
    if ($isAppOnly) {
        if (Test-Path -LiteralPath $packagedRuntime) {
            throw "App-only package unexpectedly contains a runtime directory: $packagedRuntime"
        }

        $requiredAppOnlyLayout = @(
            'ArHub.exe',
            'resources\app\main.js',
            'resources\app\runtime-store.js',
            'resources\app\update-health.js',
            'resources\app\backend\main.py',
            'resources\app\dist\index.html',
            'resources\app\packaging\runtime-bundle.json',
            'resources\app\packaging\runtime-lock.json',
            'resources\app\packaging\runtime-manifest.json'
        )
        foreach ($relativePath in $requiredAppOnlyLayout) {
            if (-not (Test-Path -LiteralPath (Join-Path $unpacked $relativePath) -PathType Leaf)) {
                throw "App-only packaged layout is missing: $relativePath"
            }
        }

        $packagedMetadata = Get-Content -LiteralPath (Join-Path $unpacked 'resources\app\package.json') -Encoding utf8 | ConvertFrom-Json
        if ($packagedMetadata.arhubPackageProfile -ne 'app-only' -or $packagedMetadata.arhubRuntimeProfile -ne 'external') {
            throw 'App-only package metadata does not identify the app-only profile.'
        }
        if (-not $packagedMetadata.arhubRuntimeCompatibility.requiresExternalRuntime) {
            throw 'App-only package metadata must require an external runtime.'
        }
        $expectedRuntimeVersion = [string](Get-Content -LiteralPath (Join-Path $projectRoot 'packaging\runtime-manifest.json') -Encoding utf8 | ConvertFrom-Json).runtimeVersion
        if ($packagedMetadata.arhubRuntimeVersion -ne $expectedRuntimeVersion -or
            $packagedMetadata.arhubRuntimeCompatibility.runtimeVersion -ne $expectedRuntimeVersion) {
            throw "App-only package metadata does not require the locked runtime version $expectedRuntimeVersion."
        }
        $compatibleProfiles = @($packagedMetadata.arhubRuntimeCompatibility.profiles)
        if ($compatibleProfiles.Count -ne 2 -or 'full' -notin $compatibleProfiles -or 'lite' -notin $compatibleProfiles) {
            throw 'App-only package metadata must declare compatibility with both Full and Lite runtimes.'
        }

        $installers = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'release') -File -Filter 'ArHub-Setup-*-app-only-x64*.exe')
        if ($installers.Count -ne 1) { throw "Expected exactly one app-only installer, found $($installers.Count)." }
        $latest = Join-Path $projectRoot 'release\latest.yml'
        if (-not (Test-Path -LiteralPath $latest -PathType Leaf)) { throw 'latest.yml is missing.' }
        $latestYaml = Get-Content -LiteralPath $latest -Encoding utf8 | Out-String
        if ($latestYaml -notmatch '(?m)^sha512:\s*\S+' -or $latestYaml -notmatch [regex]::Escape($installers[0].Name)) {
            throw 'latest.yml does not contain a hash and reference the app-only installer.'
        }

        $signatureTargets = @(
            Get-Item -LiteralPath (Join-Path $unpacked 'ArHub.exe')
            $installers[0]
        )
        foreach ($target in $signatureTargets) {
            $signature = Get-AuthenticodeSignature -LiteralPath $target.FullName
            if ($UnsignedRelease -and $signature.Status -ne 'NotSigned') {
                throw "Official unsigned app-only target must be NotSigned: $($target.Name) ($($signature.Status))"
            }
            if ($AllowUnsigned -and $signature.Status -notin @('Valid', 'NotSigned')) {
                throw "Unexpected signature status for app-only target $($target.Name): $($signature.Status)"
            }
            if (-not $UnsignedRelease -and -not $AllowUnsigned -and $signature.Status -ne 'Valid') {
                throw "Invalid Authenticode signature for app-only target $($target.Name): $($signature.Status)"
            }
        }
        if (Test-Path -LiteralPath (Join-Path $unpacked 'resources\app.asar')) {
            throw 'app.asar exists, but ArHub requires unpacked backend source.'
        }

        $nodeSbom = (& npm sbom --omit=dev --sbom-format cyclonedx 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0) { throw "npm SBOM generation failed: $nodeSbom" }
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText((Join-Path $projectRoot 'release\sbom-node.cdx.json'), $nodeSbom.Trim() + "`n", $utf8)
    } elseif ($RuntimeProfile -eq 'lite') {
        $packagedLiteValidation = @('-RuntimeDir', $packagedRuntime)
        if (-not $AllowRuntimeDrift) { $packagedLiteValidation += '-EnforceLock' }
        & (Join-Path $PSScriptRoot 'assert-lite-runtime.ps1') @packagedLiteValidation
        & (Join-Path $PSScriptRoot 'generate-sbom.ps1') -RuntimeDir $packagedRuntime
    } else {
        & (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $packagedRuntime -EnforceLock -SkipPythonDependencyCheck
        & (Join-Path $PSScriptRoot 'generate-sbom.ps1') -RuntimeDir $packagedRuntime
    }

    & (Join-Path $PSScriptRoot 'create-checksums.ps1')
    if ($isAppOnly) {
        Write-Host 'App-only package verification passed.'
    } elseif ($UnsignedRelease) {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -RequireUnsigned -RuntimeProfile $RuntimeProfile
    } elseif ($AllowUnsigned) {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -AllowUnsigned -RuntimeProfile $RuntimeProfile
    } else {
        & (Join-Path $PSScriptRoot 'verify-release.ps1') -RuntimeProfile $RuntimeProfile
    }
} finally {
    if (Test-Path variable:originalPath) { $env:PATH = $originalPath }
    if ($env:ARHUB_EPHEMERAL_CERTIFICATE_PATH) {
        Remove-Item -LiteralPath $env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -Force -ErrorAction SilentlyContinue
        Remove-Item Env:ARHUB_EPHEMERAL_CERTIFICATE_PATH -ErrorAction SilentlyContinue
    }
    Pop-Location
}
