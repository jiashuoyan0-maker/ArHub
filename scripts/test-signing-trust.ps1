[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'signing-helpers.ps1')

$rsa = [System.Security.Cryptography.RSA]::Create(2048)
$certificate = $null
try {
    $request = New-Object System.Security.Cryptography.X509Certificates.CertificateRequest(
        'CN=ArHub CI Self-Signed Certificate',
        $rsa,
        [System.Security.Cryptography.HashAlgorithmName]::SHA256,
        [System.Security.Cryptography.RSASignaturePadding]::Pkcs1
    )
    $certificate = $request.CreateSelfSigned((Get-Date).AddMinutes(-5), (Get-Date).AddDays(1))
    $rejected = $false
    try {
        $null = Assert-PublicCertificateTrust -Certificate $certificate -Label 'The test certificate'
    } catch {
        $rejected = $true
        if ($_.Exception.Message -notmatch 'trusted|public root') {
            throw "The self-signed certificate failed for an unexpected reason: $($_.Exception.Message)"
        }
    }
    if (-not $rejected) {
        throw 'The public-trust gate accepted a self-signed certificate.'
    }
    Write-Host 'Signing trust test passed: a self-signed certificate was rejected.'
} finally {
    if ($certificate) { $certificate.Dispose() }
    $rsa.Dispose()
}
