[CmdletBinding()]
param(
    [string]$RuntimeDir,
    [string]$ManifestPath,
    [string]$LockPath,
    [string]$PythonLockPath,
    [switch]$EnforceLock,
    [switch]$SkipPythonDependencyCheck
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'runtime-paths.ps1')
$RuntimeDir = Resolve-ArHubRuntimeDir -RuntimeDir $RuntimeDir -ProjectRoot $projectRoot

if (-not $ManifestPath) { $ManifestPath = Join-Path $PSScriptRoot '..\packaging\runtime-manifest.json' }
if (-not $LockPath) { $LockPath = Join-Path $PSScriptRoot '..\packaging\runtime-lock.json' }
if (-not $PythonLockPath) { $PythonLockPath = Join-Path $PSScriptRoot '..\packaging\python-requirements.lock.txt' }

function Get-DirectoryStats {
    param([Parameter(Mandatory = $true)][string]$Path)
    $files = @(Get-ChildItem -LiteralPath $Path -File -Recurse -Force -ErrorAction Stop)
    $size = ($files | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $size) { $size = 0 }
    [pscustomobject]@{ Files = $files.Count; Bytes = [int64]$size }
}

function Add-Issue {
    param([string]$Message)
    $script:issues.Add($Message)
}

if (-not (Test-Path -LiteralPath $RuntimeDir -PathType Container)) {
    throw "Runtime directory does not exist: $RuntimeDir"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Runtime manifest does not exist: $ManifestPath"
}

$runtime = (Resolve-Path -LiteralPath $RuntimeDir).Path
$manifest = Get-Content -LiteralPath $ManifestPath -Encoding UTF8 | ConvertFrom-Json
$issues = New-Object System.Collections.Generic.List[string]
$componentStats = [ordered]@{}
$totalBytes = [int64]0

foreach ($component in $manifest.components) {
    $componentDir = Join-Path $runtime $component.name
    if (-not (Test-Path -LiteralPath $componentDir -PathType Container)) {
        Add-Issue "Missing component directory: $($component.name)"
        continue
    }

    $stats = Get-DirectoryStats -Path $componentDir
    $componentStats[$component.name] = $stats
    $totalBytes += $stats.Bytes
    if ($stats.Bytes -lt [int64]$component.minimumBytes) {
        Add-Issue "$($component.name) is too small: $($stats.Bytes) bytes"
    }
    if ($stats.Files -lt [int]$component.minimumFiles) {
        Add-Issue "$($component.name) has too few files: $($stats.Files)"
    }

    foreach ($required in $component.requiredFiles) {
        $relative = $required.path -replace '/', '\'
        $file = Join-Path $runtime $relative
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            Add-Issue "Missing required runtime file: $($required.path)"
            continue
        }
        $item = Get-Item -LiteralPath $file
        if ($required.PSObject.Properties.Name -contains 'minimumBytes' -and $item.Length -lt [int64]$required.minimumBytes) {
            Add-Issue "$($required.path) is too small: $($item.Length) bytes"
        }
        if ($required.PSObject.Properties.Name -contains 'fileVersion' -and $item.VersionInfo.FileVersion -ne $required.fileVersion) {
            Add-Issue "$($required.path) version mismatch: $($item.VersionInfo.FileVersion)"
        }
        if ($required.PSObject.Properties.Name -contains 'signature') {
            $signature = Get-AuthenticodeSignature -LiteralPath $file
            if ($required.signature -eq 'valid' -and $signature.Status -ne 'Valid') {
                Add-Issue "$($required.path) does not have a valid vendor signature: $($signature.Status)"
            }
            if ($required.signature -eq 'valid-or-unsigned' -and $signature.Status -notin @('Valid', 'NotSigned')) {
                Add-Issue "$($required.path) has an invalid signature state: $($signature.Status)"
            }
            if ($required.PSObject.Properties.Name -contains 'publisherContains' -and $signature.Status -eq 'Valid') {
                if (-not $signature.SignerCertificate.Subject.Contains([string]$required.publisherContains)) {
                    Add-Issue "$($required.path) publisher mismatch: $($signature.SignerCertificate.Subject)"
                }
            }
        }
    }

    if ($component.PSObject.Properties.Name -contains 'versionProbe') {
        $probe = $component.versionProbe
        $probeExe = Join-Path $runtime ($probe.path -replace '/', '\')
        if (Test-Path -LiteralPath $probeExe -PathType Leaf) {
            $previousErrorAction = $ErrorActionPreference
            try {
                $ErrorActionPreference = 'Continue'
                $probeOutput = (& $probeExe @($probe.arguments) 2>&1 | Out-String).Trim()
            } finally {
                $ErrorActionPreference = $previousErrorAction
            }
            if ($probeOutput -notmatch $probe.pattern) {
                Add-Issue "$($component.name) version probe did not match '$($probe.pattern)': $probeOutput"
            }
        }
    }

    if ($component.PSObject.Properties.Name -contains 'packages') {
        foreach ($packageProperty in $component.packages.PSObject.Properties) {
            $packagePath = Join-Path $componentDir ("node_modules\{0}\package.json" -f ($packageProperty.Name -replace '/', '\'))
            if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
                Add-Issue "Missing Node runtime package: $($packageProperty.Name)"
                continue
            }
            $packageJson = Get-Content -LiteralPath $packagePath -Encoding UTF8 | ConvertFrom-Json
            if ($packageJson.version -ne $packageProperty.Value) {
                Add-Issue "Node runtime package $($packageProperty.Name) is $($packageJson.version), expected $($packageProperty.Value)"
            }
        }
    }
}

if ($totalBytes -lt [int64]$manifest.minimumTotalBytes) {
    Add-Issue "Runtime total is too small: $totalBytes bytes"
}

$forbidden = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in $manifest.forbiddenFileNames) { $null = $forbidden.Add([string]$name) }
foreach ($file in Get-ChildItem -LiteralPath $runtime -File -Recurse -Force -ErrorAction Stop) {
    if ($forbidden.Contains($file.Name)) {
        Add-Issue "Forbidden credential-like file in runtime: $($file.FullName.Substring($runtime.Length + 1))"
    }
}
if ($manifest.PSObject.Properties.Name -contains 'forbiddenPaths') {
    foreach ($relativePath in $manifest.forbiddenPaths) {
        $normalized = ([string]$relativePath) -replace '/', '\'
        $forbiddenPath = [System.IO.Path]::GetFullPath((Join-Path $runtime $normalized))
        $runtimePrefix = $runtime.TrimEnd('\') + '\'
        if (-not $forbiddenPath.StartsWith($runtimePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            Add-Issue "Forbidden runtime path escapes the runtime root: $relativePath"
        } elseif (Test-Path -LiteralPath $forbiddenPath) {
            Add-Issue "Architecture-incompatible file is present: $relativePath"
        }
    }
}

$pythonExe = Join-Path $runtime 'python\python.exe'
if (-not $SkipPythonDependencyCheck -and (Test-Path -LiteralPath $pythonExe)) {
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $pipCheck = (& $pythonExe -X utf8 -m pip check 2>&1 | Out-String).Trim()
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($LASTEXITCODE -ne 0) {
        Add-Issue "Python dependency check failed: $pipCheck"
    }

    if (Test-Path -LiteralPath $PythonLockPath -PathType Leaf) {
        $expected = @(Get-Content -LiteralPath $PythonLockPath -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') } | Sort-Object)
        $actual = @(& $pythonExe -X utf8 -m pip freeze --all | Sort-Object)
        $difference = @(Compare-Object -ReferenceObject $expected -DifferenceObject $actual)
        if ($difference.Count -gt 0) {
            $preview = ($difference | Select-Object -First 12 | Out-String).Trim()
            Add-Issue "Python package lock mismatch:`n$preview"
        }
    } elseif ($EnforceLock) {
        Add-Issue "Python package lock is missing: $PythonLockPath"
    }
}

if ($EnforceLock) {
    if (-not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
        Add-Issue "Runtime lock is missing: $LockPath"
    } else {
        $lock = Get-Content -LiteralPath $LockPath -Encoding UTF8 | ConvertFrom-Json
        if ($lock.runtimeVersion -ne $manifest.runtimeVersion) {
            Add-Issue "Runtime lock version does not match the manifest"
        }
        foreach ($property in $lock.components.PSObject.Properties) {
            if (-not $componentStats.Contains($property.Name)) {
                Add-Issue "Locked component is missing: $($property.Name)"
                continue
            }
            $actualStats = $componentStats[$property.Name]
            if ($actualStats.Files -ne [int]$property.Value.files -or $actualStats.Bytes -ne [int64]$property.Value.bytes) {
                Add-Issue "Locked component changed: $($property.Name) (files $($actualStats.Files)/$($property.Value.files), bytes $($actualStats.Bytes)/$($property.Value.bytes))"
            }
        }
        foreach ($probeProperty in $lock.probes.PSObject.Properties) {
            $probePath = Join-Path $runtime ($probeProperty.Name -replace '/', '\')
            if (-not (Test-Path -LiteralPath $probePath -PathType Leaf)) {
                Add-Issue "Locked probe is missing: $($probeProperty.Name)"
                continue
            }
            $hash = (Get-FileHash -LiteralPath $probePath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -ne $probeProperty.Value.sha256) {
                Add-Issue "Locked probe hash changed: $($probeProperty.Name)"
            }
        }
    }
}

if ($issues.Count -gt 0) {
    $issues | ForEach-Object { Write-Error $_ }
    throw "Runtime validation failed with $($issues.Count) issue(s)."
}

[pscustomobject]@{
    RuntimeDir = $runtime
    RuntimeVersion = $manifest.runtimeVersion
    Components = $componentStats
    TotalBytes = $totalBytes
    Status = 'Valid'
} | Format-List
