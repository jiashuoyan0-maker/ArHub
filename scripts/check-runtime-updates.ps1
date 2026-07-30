[CmdletBinding()]
param(
    [string]$ManifestPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $ManifestPath) { $ManifestPath = Join-Path $PSScriptRoot '..\packaging\runtime-manifest.json' }
$manifest = Get-Content -LiteralPath $ManifestPath -Encoding UTF8 | ConvertFrom-Json
$headers = @{ 'User-Agent' = 'ArHub-runtime-maintenance' }

function Get-ComponentVersion([string]$Name) {
    [string](($manifest.components | Where-Object name -eq $Name | Select-Object -First 1).version)
}

function Get-ComponentPackageVersion([string]$Component, [string]$Package) {
    $entry = $manifest.components | Where-Object name -eq $Component | Select-Object -First 1
    if (-not $entry -or -not $entry.packages) { return '' }
    [string]$entry.packages.$Package
}

function Convert-Version([string]$Value) {
    $match = [regex]::Match($Value, '\d+(?:\.\d+){1,3}')
    if (-not $match.Success) { throw "Cannot parse version: $Value" }
    [version]$match.Value
}

$checks = New-Object System.Collections.Generic.List[object]

$nodeCurrent = Get-ComponentVersion 'node'
$nodeMajor = (Convert-Version $nodeCurrent).Major
$nodeIndex = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -Headers $headers
$nodeLatest = @($nodeIndex | Where-Object { $_.version -match "^v$nodeMajor\." } | ForEach-Object { $_.version.TrimStart('v') } | Sort-Object { Convert-Version $_ } -Descending)[0]
$checks.Add([pscustomobject]@{ Component = "Node.js $nodeMajor"; Current = $nodeCurrent; Latest = $nodeLatest; Url = 'https://nodejs.org/en/download' })

$pythonCurrent = Get-ComponentVersion 'python'
$pythonVersion = Convert-Version $pythonCurrent
$pythonSeries = "$($pythonVersion.Major).$($pythonVersion.Minor)"
$pythonInfo = Invoke-RestMethod -Uri "https://endoflife.date/api/python/$pythonSeries.json" -Headers $headers
$checks.Add([pscustomobject]@{ Component = "Python $pythonSeries"; Current = $pythonCurrent; Latest = [string]$pythonInfo.latest; Url = 'https://www.python.org/downloads/' })

$npmPackages = @(
    @{ Component = 'Claude Code'; Runtime = '@anthropic-ai/claude-code'; Registry = '@anthropic-ai%2fclaude-code' },
    @{ Component = 'npm'; Runtime = 'npm'; Registry = 'npm' },
    @{ Component = 'Corepack'; Runtime = 'corepack'; Registry = 'corepack' }
)
foreach ($package in $npmPackages) {
    $current = Get-ComponentPackageVersion 'node' $package.Runtime
    if (-not $current) { continue }
    $latest = Invoke-RestMethod -Uri "https://registry.npmjs.org/$($package.Registry)/latest" -Headers $headers
    $checks.Add([pscustomobject]@{
        Component = $package.Component
        Current = $current
        Latest = [string]$latest.version
        Url = "https://www.npmjs.com/package/$($package.Runtime)"
    })
}

$githubChecks = @(
    @{ Component = 'Git for Windows'; Runtime = 'git'; Repo = 'git-for-windows/git' },
    @{ Component = 'Pandoc'; Runtime = 'pandoc'; Repo = 'jgm/pandoc' },
    @{ Component = 'Draw.io'; Runtime = 'draw.io'; Repo = 'jgraph/drawio-desktop' }
)
foreach ($check in $githubChecks) {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$($check.Repo)/releases/latest" -Headers $headers
    $checks.Add([pscustomobject]@{
        Component = $check.Component
        Current = Get-ComponentVersion $check.Runtime
        Latest = ([string]$release.tag_name).TrimStart('v')
        Url = [string]$release.html_url
    })
}

$updates = @($checks | Where-Object { (Convert-Version $_.Latest) -gt (Convert-Version $_.Current) })
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Runtime update report')
$lines.Add('')
$lines.Add('| Component | Locked | Latest | Source |')
$lines.Add('|---|---:|---:|---|')
foreach ($check in $checks) {
    $lines.Add("| $($check.Component) | $($check.Current) | $($check.Latest) | [release]($($check.Url)) |")
}
$lines.Add('')
$lines.Add('MiKTeX is a rolling distribution and remains a manual review item.')
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines((Join-Path (Get-Location) 'runtime-update-report.md'), $lines, $utf8)

$hasUpdates = if ($updates.Count -gt 0) { 'true' } else { 'false' }
if ($env:GITHUB_OUTPUT) { "updates=$hasUpdates" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append }
Write-Host "Runtime updates available: $hasUpdates"
$checks | Format-Table -AutoSize
