[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$safeDirectory = $repoRoot -replace '\\', '/'
$gitOptions = @('-c', "safe.directory=$safeDirectory")
Push-Location $repoRoot
try {
    $tracked = @(& git @gitOptions ls-files)
    if ($LASTEXITCODE -ne 0) {
        throw 'git ls-files failed'
    }

    $candidateFiles = @($tracked)
    $candidateFiles += @(
        & git @gitOptions ls-files --others --exclude-standard
    )
    $candidateFiles = @($candidateFiles | Sort-Object -Unique)

    $requiredFiles = @(
        'backend/db/schema.sql'
        'backend/workflow_templates.json'
        'backend/routers/editor.py'
        'backend/services/editor_agent.py'
        'backend/services/docx_exporter.py'
        'backend/extension_registry.py'
        'backend/routers/extensions.py'
        'extension.schema.json'
        'extensions/diagram/manifest.json'
        'extensions/web/manifest.json'
        'dist/index.html'
        'dist/splash.html'
        'dist/assets/index-BabYh3e1.js'
        'dist/assets/apple-ui-20260727.css'
        'dist/assets/arhub-icons.js'
        'dist/assets/arhub-codex-desktop.css'
        'dist/assets/arhub-codex-desktop.js'
        'dist/assets/arhub-glass.css'
        'licenses/LUCIDE-ISC.txt'
        'scripts/set-executable-resources.ps1'
    )
    $missingRequired = @($requiredFiles | Where-Object {
        -not (Test-Path -LiteralPath $_ -PathType Leaf)
    })
    $excludedRequired = @($requiredFiles | Where-Object {
        $candidateFiles -notcontains $_
    })
    if ($missingRequired.Count -gt 0 -or $excludedRequired.Count -gt 0) {
        if ($missingRequired.Count -gt 0) {
            Write-Host 'Missing required runtime files:'
            $missingRequired | ForEach-Object { Write-Host "  $_" }
        }
        if ($excludedRequired.Count -gt 0) {
            Write-Host 'Required runtime files excluded from the public candidate set:'
            $excludedRequired | ForEach-Object { Write-Host "  $_" }
        }
        throw 'Required runtime file audit failed'
    }

    $forbiddenName = '(?i)(^|/)(license\.json|proxy_config\.ya?ml|[^/]*_openai\.json|\.env(?:\..*)?|.*\.(?:db|sqlite|sqlite3|pem|p12|pfx|key|crt|cer|der|sig|asc|cat|pyc|pyd|exe|dll|node|msi|sys|cab))$'
    $forbidden = @($candidateFiles | Where-Object {
        $_ -match $forbiddenName -and $_ -notmatch '(?i)\.example\.'
    })

    $patterns = [ordered]@{
        'private key' = '-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'
        'certificate block' = ('-----BEGIN ' + 'CERTIFICATE-----')
        'provider API key' = '\bsk-[A-Za-z0-9_-]{16,}\b'
        'activation code' = '\b[A-Z]{2}[0-9]{2}(?:-[A-Z0-9]{4}){3}\b'
        'absolute user path' = '(?i)[A-Z]:\\Users\\[^\\\s]+\\'
        'retired project identity' = ('(?i)Mo' + 'dex|MH[ -]?A' + 'gent|mhco' + 'ding|\u660e' + '\u73e9')
    }
    $skipExtensions = @('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.ttf', '.otf', '.woff', '.woff2')
    $hits = New-Object System.Collections.Generic.List[string]

    foreach ($path in $candidateFiles) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        $item = Get-Item -LiteralPath $path
        if ($item.Length -gt 5MB -or $skipExtensions -contains $item.Extension.ToLowerInvariant()) {
            continue
        }
        $lineNumber = 0
        foreach ($line in [System.IO.File]::ReadLines($item.FullName)) {
            $lineNumber++
            foreach ($entry in $patterns.GetEnumerator()) {
                if ($line -match $entry.Value) {
                    $hits.Add(('{0}: {1}:{2}' -f $entry.Key, $path, $lineNumber))
                    break
                }
            }
        }
    }

    $jsonFiles = @('package.json', 'updater-config.json', 'extension.schema.json', 'extensions/core/manifest.json', 'extensions/diagram/manifest.json', 'extensions/web/manifest.json')
    foreach ($path in $jsonFiles) {
        Get-Content -LiteralPath $path -Encoding UTF8 | ConvertFrom-Json | Out-Null
    }

    & git @gitOptions diff --check
    if ($LASTEXITCODE -ne 0) {
        throw 'git diff --check failed'
    }

    if ($forbidden.Count -gt 0 -or $hits.Count -gt 0) {
        if ($forbidden.Count -gt 0) {
            Write-Host 'Forbidden repository files:'
            $forbidden | ForEach-Object { Write-Host "  $_" }
        }
        if ($hits.Count -gt 0) {
            Write-Host 'Potential secrets or machine-specific paths:'
            $hits | ForEach-Object { Write-Host "  $_" }
        }
        throw 'Open-source audit failed'
    }

    Write-Host "Open-source audit passed for $($candidateFiles.Count) repository files."
} finally {
    Pop-Location
}
