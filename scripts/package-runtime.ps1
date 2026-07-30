[CmdletBinding()]
param(
    [string]$RuntimeDir = (Join-Path $env:LOCALAPPDATA 'Programs\ArHub\runtime'),
    [string]$OutputDir,
    [ValidateRange(100, 1900)]
    [int]$VolumeSizeMB = 1800,
    [ValidateRange(0, 9)]
    [int]$CompressionLevel = 7,
    [string]$ArchiveSeedDir,
    [switch]$ReuseExistingArchives,
    [switch]$UpdateRepositoryManifest
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manifestPath = Join-Path $projectRoot 'packaging\runtime-manifest.json'
$lockPath = Join-Path $projectRoot 'packaging\runtime-lock.json'
$pythonLockPath = Join-Path $projectRoot 'packaging\python-requirements.lock.txt'
$manifest = Get-Content -LiteralPath $manifestPath -Encoding UTF8 | ConvertFrom-Json
$runtime = (Resolve-Path -LiteralPath $RuntimeDir).Path
$archiveSeed = $null
$expectedBundle = $null
if ($ArchiveSeedDir) {
    $archiveSeed = (Resolve-Path -LiteralPath $ArchiveSeedDir).Path
    $expectedBundlePath = Join-Path $projectRoot 'packaging\runtime-bundle.json'
    if (-not (Test-Path -LiteralPath $expectedBundlePath -PathType Leaf)) {
        throw "Committed runtime bundle manifest is required when ArchiveSeedDir is used: $expectedBundlePath"
    }
    $expectedBundle = Get-Content -LiteralPath $expectedBundlePath -Encoding UTF8 | ConvertFrom-Json
    if ($expectedBundle.runtimeVersion -ne $manifest.runtimeVersion) {
        throw 'Archive seed manifest version does not match the runtime manifest.'
    }
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $projectRoot ".runtime\bundles\$($manifest.runtimeVersion)"
}
$output = [System.IO.Path]::GetFullPath($OutputDir)
if (Test-Path -LiteralPath $output) {
    $existing = @(Get-ChildItem -LiteralPath $output -Force -ErrorAction Stop)
    if ($existing.Count -gt 0 -and -not $ReuseExistingArchives) {
        throw "Runtime bundle output is not empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output -Force | Out-Null
}

& (Join-Path $PSScriptRoot 'assert-runtime.ps1') -RuntimeDir $runtime -EnforceLock

$sevenZipCandidates = @(
    (Join-Path $projectRoot 'node_modules\7zip-bin\win\x64\7za.exe'),
    (Join-Path $projectRoot 'node_modules\7zip-bin\win\ia32\7za.exe')
)
$sevenZip = $sevenZipCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $sevenZip) { throw '7za.exe was not found. Run npm ci first.' }

$componentRecords = @()
$totalDownloadBytes = [int64]0
Push-Location $runtime
try {
    foreach ($component in $manifest.components) {
        $name = [string]$component.name
        $archiveName = "arhub-runtime-$($manifest.runtimeVersion)-$name.7z"
        $archivePath = Join-Path $output $archiveName
        $parts = @(Get-ChildItem -LiteralPath $output -File | Where-Object {
            $_.Name -eq $archiveName -or $_.Name -like "$archiveName.*"
        } | Sort-Object Name)
        if ($parts.Count -eq 0 -and $archiveSeed) {
            $expectedComponent = $expectedBundle.components | Where-Object name -eq $name | Select-Object -First 1
            if (-not $expectedComponent) { throw "Committed bundle does not contain component: $name" }
            foreach ($expectedPart in @($expectedComponent.parts)) {
                $source = Join-Path $archiveSeed ([string]$expectedPart.name)
                if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
                    throw "Locked archive seed is missing: $source"
                }
                $sourceItem = Get-Item -LiteralPath $source
                if ($sourceItem.Length -ne [int64]$expectedPart.bytes) {
                    throw "Locked archive seed size mismatch: $($expectedPart.name)"
                }
                $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
                if ($sourceHash -ne [string]$expectedPart.sha256) {
                    throw "Locked archive seed hash mismatch: $($expectedPart.name)"
                }
                Copy-Item -LiteralPath $source -Destination (Join-Path $output ([string]$expectedPart.name))
            }
            $parts = @(Get-ChildItem -LiteralPath $output -File | Where-Object {
                $_.Name -eq $archiveName -or $_.Name -like "$archiveName.*"
            } | Sort-Object Name)
            Write-Host "Staged locked runtime archive: $name"
        }
        if ($parts.Count -eq 0 -or -not $ReuseExistingArchives) {
            if ($parts.Count -gt 0) { throw "Archive already exists for ${name}. Use -ReuseExistingArchives or an empty output directory." }
            $arguments = @(
                'a', '-t7z', "-mx=$CompressionLevel", '-mmt=on', '-ms=on', '-y',
                '-mtm=off', '-mta=off', '-mtc=off',
                '-bsp0', '-bso0', '-bse1', $archivePath, $name
            )
            if ($name -eq 'python') { $arguments = $arguments[0..5] + "-v${VolumeSizeMB}m" + $arguments[6..($arguments.Count - 1)] }
            Write-Host "Packing runtime component: $name"
            & $sevenZip @arguments
            if ($LASTEXITCODE -ne 0) { throw "7-Zip failed for $name with exit code $LASTEXITCODE" }
            $parts = @(Get-ChildItem -LiteralPath $output -File | Where-Object {
                $_.Name -eq $archiveName -or $_.Name -like "$archiveName.*"
            } | Sort-Object Name)
        } else {
            Write-Host "Reusing runtime archive: $name"
        }
        if ($parts.Count -eq 0) { throw "No archive was created for $name" }
        $partRecords = @($parts | ForEach-Object {
            [ordered]@{
                name = $_.Name
                bytes = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
        $downloadBytes = [int64](($parts | Measure-Object -Property Length -Sum).Sum)
        $totalDownloadBytes += $downloadBytes
        $componentRecords += [pscustomobject][ordered]@{
            name = $name
            extractFrom = $parts[0].Name
            downloadBytes = $downloadBytes
            parts = $partRecords
        }
    }
} finally {
    Pop-Location
}

$bundle = [ordered]@{
    schemaVersion = 1
    runtimeVersion = $manifest.runtimeVersion
    architecture = $manifest.architecture
    releaseTag = "runtime-v$($manifest.runtimeVersion)"
    baseUrl = "https://github.com/jiashuoyan0-maker/ArHub/releases/download/runtime-v$($manifest.runtimeVersion)"
    totalDownloadBytes = $totalDownloadBytes
    components = @($componentRecords)
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
$bundleJson = $bundle | ConvertTo-Json -Depth 10
$bundlePath = Join-Path $output 'runtime-bundle.json'
if ($UpdateRepositoryManifest) {
    [System.IO.File]::WriteAllText($bundlePath, $bundleJson + "`n", $utf8)
} elseif (Test-Path -LiteralPath (Join-Path $projectRoot 'packaging\runtime-bundle.json') -PathType Leaf) {
    $committedBundlePath = Join-Path $projectRoot 'packaging\runtime-bundle.json'
    $committedJson = Get-Content -LiteralPath $committedBundlePath -Encoding UTF8 | ConvertFrom-Json | ConvertTo-Json -Depth 10
    $generatedJson = $bundle | ConvertTo-Json -Depth 10
    if ($committedJson -ne $generatedJson) {
        throw 'Generated runtime bundle does not match the committed lock.'
    }
    Copy-Item -LiteralPath $committedBundlePath -Destination $bundlePath
} else {
    [System.IO.File]::WriteAllText($bundlePath, $bundleJson + "`n", $utf8)
}
Copy-Item -LiteralPath $manifestPath, $lockPath, $pythonLockPath -Destination $output

$checksumFiles = @(Get-ChildItem -LiteralPath $output -File | Where-Object { $_.Name -ne 'SHA256SUMS.txt' } | Sort-Object Name)
$checksumLines = @($checksumFiles | ForEach-Object {
    "{0}  {1}" -f ((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()), $_.Name
})
[System.IO.File]::WriteAllLines((Join-Path $output 'SHA256SUMS.txt'), $checksumLines, $utf8)

if ($UpdateRepositoryManifest) {
    [System.IO.File]::WriteAllText((Join-Path $projectRoot 'packaging\runtime-bundle.json'), $bundleJson + "`n", $utf8)
}

Write-Host "Runtime bundle: $output"
Write-Host ("Compressed size: {0:N2} GiB" -f ($bundle.totalDownloadBytes / 1GB))
