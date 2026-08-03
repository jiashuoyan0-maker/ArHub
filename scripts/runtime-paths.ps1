function Resolve-ArHubRuntimeDir {
    [CmdletBinding()]
    param(
        [string]$RuntimeDir,
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot
    )

    $candidate = if (-not [string]::IsNullOrWhiteSpace($RuntimeDir)) {
        $RuntimeDir
    } elseif (-not [string]::IsNullOrWhiteSpace($env:ARHUB_RUNTIME_DIR)) {
        $env:ARHUB_RUNTIME_DIR
    } else {
        Join-Path $ProjectRoot 'runtime'
    }

    if (-not [System.IO.Path]::IsPathRooted($candidate)) {
        $candidate = Join-Path $ProjectRoot $candidate
    }
    return [System.IO.Path]::GetFullPath($candidate)
}
