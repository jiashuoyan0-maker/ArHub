[CmdletBinding()]
param(
    [string]$ReleaseDir,
    [string]$PublisherName = $env:ARHUB_PUBLISHER_NAME,
    [switch]$AllowUnsigned,
    [switch]$RequireUnsigned
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'signing-helpers.ps1')
if (-not $ReleaseDir) { $ReleaseDir = Join-Path $PSScriptRoot '..\release' }
$release = (Resolve-Path -LiteralPath $ReleaseDir).Path
$issues = New-Object System.Collections.Generic.List[string]
if ($AllowUnsigned -and $RequireUnsigned) { throw 'AllowUnsigned and RequireUnsigned are mutually exclusive.' }

$installers = @(Get-ChildItem -LiteralPath $release -File -Filter 'ArHub-Setup-*.exe')
if ($installers.Count -ne 1) { $issues.Add("Expected exactly one installer, found $($installers.Count).") }
$latest = Join-Path $release 'latest.yml'
if (-not (Test-Path -LiteralPath $latest -PathType Leaf)) { $issues.Add('latest.yml is missing.') }

$unpacked = Join-Path $release 'win-unpacked'
$appExe = Join-Path $unpacked 'ArHub.exe'
$requiredLayout = @(
    'resources\app\main.js',
    'resources\app\backend\main.py',
    'resources\app\dist\index.html',
    'resources\app\node_modules\electron-updater\package.json',
    'resources\app-update.yml',
    'runtime\python\python.exe',
    'runtime\node\node.exe',
    'runtime\git\cmd\git.exe',
    'runtime\pandoc\pandoc.exe',
    'runtime\draw.io\draw.io.exe',
    'runtime\texlive\miktex\bin\x64\xelatex.exe'
)
foreach ($relative in $requiredLayout) {
    if (-not (Test-Path -LiteralPath (Join-Path $unpacked $relative))) {
        $issues.Add("Packaged layout is missing: $relative")
    }
}
if (Test-Path -LiteralPath (Join-Path $unpacked 'resources\app.asar')) {
    $issues.Add('app.asar exists, but ArHub requires unpacked backend source.')
}

$signatureTargets = @()
if (Test-Path -LiteralPath $appExe) { $signatureTargets += Get-Item -LiteralPath $appExe }
$elevationHelper = Join-Path $unpacked 'resources\elevate.exe'
if (Test-Path -LiteralPath $elevationHelper) { $signatureTargets += Get-Item -LiteralPath $elevationHelper }
$signatureTargets += $installers
foreach ($target in $signatureTargets) {
    $signature = Get-AuthenticodeSignature -LiteralPath $target.FullName
    if ($RequireUnsigned) {
        if ($signature.Status -ne 'NotSigned') {
            $issues.Add("Official unsigned release target must be NotSigned: $($target.Name) ($($signature.Status))")
        }
        continue
    }
    if ($AllowUnsigned) {
        if ($signature.Status -notin @('Valid', 'NotSigned')) {
            $issues.Add("Unexpected signature status for $($target.Name): $($signature.Status)")
        }
        continue
    }
    if ($signature.Status -ne 'Valid') {
        $issues.Add("Invalid Authenticode signature for $($target.Name): $($signature.Status)")
        continue
    }
    $commonName = $signature.SignerCertificate.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
    if ($commonName -ne $PublisherName) {
        $issues.Add("Publisher mismatch for $($target.Name): '$commonName'")
    }
    try {
        $null = Assert-PublicCertificateTrust -Certificate $signature.SignerCertificate -Label "The signature on $($target.Name)"
    } catch {
        $issues.Add($_.Exception.Message)
    }
    if (-not $signature.TimeStamperCertificate) {
        $issues.Add("Timestamp signature is missing for $($target.Name).")
    } else {
        try {
            $null = Assert-PublicCertificateTrust -Certificate $signature.TimeStamperCertificate -Label "The timestamp on $($target.Name)"
        } catch {
            $issues.Add($_.Exception.Message)
        }
    }
}

if (Test-Path -LiteralPath $latest) {
    $yaml = Get-Content -LiteralPath $latest -Encoding UTF8 | Out-String
    if ($yaml -notmatch '(?m)^sha512:\s*\S+') { $issues.Add('latest.yml does not contain sha512.') }
}
if (($RequireUnsigned -or -not $AllowUnsigned) -and @($installers | Where-Object Name -Like '*-unsigned.exe').Count -gt 0) {
    $issues.Add('A formal release cannot contain the local-test -unsigned suffix.')
}
if (-not $AllowUnsigned -and -not $RequireUnsigned) {
    $appUpdatePath = Join-Path $unpacked 'resources\app-update.yml'
    if (Test-Path -LiteralPath $appUpdatePath) {
        $appUpdateYaml = Get-Content -LiteralPath $appUpdatePath -Encoding UTF8 | Out-String
        if ($appUpdateYaml -notmatch [regex]::Escape([string]$PublisherName)) {
            $issues.Add('app-update.yml does not contain the expected publisherName.')
        }
    }
}

if ($issues.Count -gt 0) {
    $issues | ForEach-Object { Write-Error $_ }
    throw "Release verification failed with $($issues.Count) issue(s)."
}

Write-Host "Release verification passed: $release"
