[CmdletBinding()]
param(
    [ValidateSet('pfx', 'azure')]
    [string]$Provider = $(if ($env:ARHUB_SIGNING_PROVIDER) { $env:ARHUB_SIGNING_PROVIDER } else { 'pfx' }),
    [string]$PublisherName = $env:ARHUB_PUBLISHER_NAME
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'signing-helpers.ps1')

if ([string]::IsNullOrWhiteSpace($PublisherName)) {
    throw 'ARHUB_PUBLISHER_NAME must exactly match the certificate common name.'
}

if ($Provider -eq 'azure') {
    $required = @(
        'AZURE_TRUSTED_SIGNING_ENDPOINT',
        'AZURE_TRUSTED_SIGNING_ACCOUNT',
        'AZURE_TRUSTED_SIGNING_PROFILE'
    )
    $missing = @($required | Where-Object { [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_)) })
    if ($missing.Count -gt 0) {
        throw "Azure Trusted Signing configuration is incomplete: $($missing -join ', ')"
    }
    Write-Host "Azure Trusted Signing preflight passed for '$PublisherName'."
    return
}

$password = $env:CSC_KEY_PASSWORD
if (-not $password) { $password = $env:WINDOWS_CERTIFICATE_PASSWORD }
$certificatePath = $env:CSC_LINK

if (-not $certificatePath -and $env:WINDOWS_CERTIFICATE_BASE64) {
    $signingDir = Join-Path ([System.IO.Path]::GetTempPath()) 'ArHub-signing'
    New-Item -ItemType Directory -Path $signingDir -Force | Out-Null
    $certificatePath = Join-Path $signingDir "arhub-signing-$PID.pfx"
    try {
        [System.IO.File]::WriteAllBytes($certificatePath, [Convert]::FromBase64String($env:WINDOWS_CERTIFICATE_BASE64))
    } catch {
        throw 'WINDOWS_CERTIFICATE_BASE64 is not valid base64.'
    }
    $env:CSC_LINK = $certificatePath
    $env:ARHUB_EPHEMERAL_CERTIFICATE_PATH = $certificatePath
}

if (-not $certificatePath) {
    throw 'No signing certificate was provided. Set CSC_LINK or WINDOWS_CERTIFICATE_BASE64.'
}
if ($certificatePath -match '^(https?|file)://') {
    Write-Host "Remote signing certificate preflight passed for '$PublisherName'."
    return
}
if (-not (Test-Path -LiteralPath $certificatePath -PathType Leaf)) {
    throw "Signing certificate was not found: $certificatePath"
}

$flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable
$certificate = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certificatePath, $password, $flags)
if (-not $certificate.HasPrivateKey) {
    throw 'The signing certificate does not contain a private key.'
}
if ($certificate.NotAfter -le (Get-Date).AddDays(1)) {
    throw "The signing certificate is expired or expires within 24 hours: $($certificate.NotAfter)"
}
if ($certificate.NotBefore -gt (Get-Date)) {
    throw "The signing certificate is not valid before $($certificate.NotBefore)."
}
$codeSigningOid = '1.3.6.1.5.5.7.3.3'
$ekuOids = @(
    $certificate.Extensions |
        Where-Object { $_ -is [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension] } |
        ForEach-Object { $_.EnhancedKeyUsages } |
        ForEach-Object { $_.Value }
)
if ($codeSigningOid -notin $ekuOids) {
    throw 'The certificate is not valid for Authenticode code signing.'
}
$commonName = $certificate.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
if ($commonName -ne $PublisherName) {
    throw "Publisher mismatch. Certificate common name is '$commonName', expected '$PublisherName'."
}

$trust = Assert-PublicCertificateTrust -Certificate $certificate -Label 'The signing certificate'

$env:CSC_KEY_PASSWORD = $password
Write-Host "PFX signing preflight passed for '$commonName' (public root '$($trust.RootSubject)', expires $($certificate.NotAfter.ToString('u')))."
