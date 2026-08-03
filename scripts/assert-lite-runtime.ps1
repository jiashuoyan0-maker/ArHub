[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimeDir
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$runtime = [System.IO.Path]::GetFullPath($RuntimeDir)
if (-not (Test-Path -LiteralPath $runtime -PathType Container)) {
    throw "Lite runtime directory does not exist: $runtime"
}

$python = Join-Path $runtime 'python\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Lite runtime is missing Python: $python"
}

$excludedComponents = @('node', 'git', 'pandoc', 'draw.io', 'texlive')
foreach ($component in $excludedComponents) {
    if (Test-Path -LiteralPath (Join-Path $runtime $component)) {
        throw "Lite runtime unexpectedly contains optional component: $component"
    }
}

$probe = @'
import importlib
modules = [
    'fastapi', 'uvicorn', 'aiosqlite', 'httpx', 'websockets', 'pydantic',
    'multipart', 'docx', 'openpyxl', 'PIL'
]
for name in modules:
    importlib.import_module(name)
print('lite-runtime-core-ok')
'@
$output = (& $python -B -X utf8 -c $probe 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $output -notmatch 'lite-runtime-core-ok') {
    throw "Lite Python runtime dependency probe failed: $output"
}

[pscustomobject]@{
    RuntimeDir = $runtime
    Profile = 'lite'
    Status = 'Valid'
} | Format-List
