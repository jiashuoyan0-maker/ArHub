Set-StrictMode -Version Latest

function Assert-PublicCertificateTrust {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
    try {
        $chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::Online
        $chain.ChainPolicy.RevocationFlag = [System.Security.Cryptography.X509Certificates.X509RevocationFlag]::ExcludeRoot
        $chain.ChainPolicy.VerificationFlags = [System.Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag
        $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(30)
        if (-not $chain.Build($Certificate)) {
            $status = @($chain.ChainStatus | ForEach-Object { $_.Status.ToString() }) -join ', '
            throw "$Label does not build to a trusted, non-revoked chain: $status"
        }

        $elements = @($chain.ChainElements)
        if ($elements.Count -eq 0) {
            throw "$Label produced an empty certificate chain."
        }
        $root = $elements[$elements.Count - 1].Certificate
        $authRootStores = @(
            'Cert:\LocalMachine\AuthRoot',
            'Cert:\CurrentUser\AuthRoot'
        )
        $isMicrosoftTrustedPublicRoot = $false
        foreach ($store in $authRootStores) {
            if (-not (Test-Path -LiteralPath $store)) { continue }
            $match = Get-ChildItem -LiteralPath $store -ErrorAction Stop | Where-Object {
                $_.Thumbprint -eq $root.Thumbprint
            } | Select-Object -First 1
            if ($match) {
                $isMicrosoftTrustedPublicRoot = $true
                break
            }
        }
        if (-not $isMicrosoftTrustedPublicRoot) {
            throw "$Label terminates at '$($root.Subject)', which is not in the Windows Microsoft-trusted public root store. Private, enterprise and locally trusted self-signed certificates are not valid for a formal ArHub release."
        }

        [pscustomobject]@{
            Subject = $Certificate.Subject
            Thumbprint = $Certificate.Thumbprint
            RootSubject = $root.Subject
            RootThumbprint = $root.Thumbprint
        }
    } finally {
        $chain.Dispose()
    }
}
