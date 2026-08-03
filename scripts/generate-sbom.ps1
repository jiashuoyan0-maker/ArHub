[CmdletBinding()]
param(
    [string]$RuntimeDir,
    [string]$OutputDir
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'runtime-paths.ps1')
$RuntimeDir = Resolve-ArHubRuntimeDir -RuntimeDir $RuntimeDir -ProjectRoot $projectRoot
if (-not $OutputDir) { $OutputDir = Join-Path $PSScriptRoot '..\release' }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$output = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Path $output -Force | Out-Null

$npmSbom = (& npm sbom --omit=dev --sbom-format cyclonedx 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "npm SBOM generation failed: $npmSbom" }
[System.IO.File]::WriteAllText((Join-Path $output 'sbom-node.cdx.json'), $npmSbom.Trim() + "`n", $utf8)

$pythonExe = Join-Path $RuntimeDir 'python\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) { throw "Python runtime not found: $pythonExe" }
$packagesJson = (& $pythonExe -B -X utf8 -m pip list --format=json 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "Python package inventory failed: $packagesJson" }
$packages = $packagesJson | ConvertFrom-Json
$components = @($packages | Sort-Object name | ForEach-Object {
    [ordered]@{
        type = 'library'
        name = $_.name
        version = $_.version
        purl = "pkg:pypi/$($_.name.ToLowerInvariant())@$($_.version)"
    }
})
$pythonSbom = [ordered]@{
    bomFormat = 'CycloneDX'
    specVersion = '1.5'
    serialNumber = "urn:uuid:$([guid]::NewGuid())"
    version = 1
    metadata = [ordered]@{
        timestamp = (Get-Date).ToUniversalTime().ToString('o')
        component = [ordered]@{ type = 'application'; name = 'ArHub Python runtime' }
    }
    components = $components
}
[System.IO.File]::WriteAllText((Join-Path $output 'sbom-python.cdx.json'), ($pythonSbom | ConvertTo-Json -Depth 8) + "`n", $utf8)
Write-Host "SBOM files written to $output"
