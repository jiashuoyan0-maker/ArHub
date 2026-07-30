[CmdletBinding()]
param(
    [string]$BundlePath,
    [string]$FrontendSourcePath
)

$ErrorActionPreference = 'Stop'
if (-not $BundlePath) {
    $BundlePath = Join-Path $PSScriptRoot '..\dist\assets\index-BabYh3e1.js'
}
$resolved = (Resolve-Path -LiteralPath $BundlePath).Path
$utf8 = New-Object System.Text.UTF8Encoding($false)
$content = [System.IO.File]::ReadAllText($resolved, $utf8)
$tick = [char]96

$replacements = @(
    [pscustomobject]@{ From = "executor_model_id:$($tick)claude-opus-4-6$($tick)"; To = "executor_model_id:$($tick)$($tick)" }
    [pscustomobject]@{ From = "reviewer_model_id:$($tick)claude-opus-4-6$($tick)"; To = "reviewer_model_id:$($tick)$($tick)" }
    [pscustomobject]@{ From = "editor_ai_model_id:$($tick)claude-opus-4-6$($tick)"; To = "editor_ai_model_id:$($tick)$($tick)" }
    [pscustomobject]@{
        From = 'let t=async()=>{try{let t=await fetch(`/api/workflows/${e}/artifacts`);t.ok&&d(await t.json())}catch{}try{let t=await fetch(`/api/workflows/${e}/artifacts/extract-status`);t.ok&&C((await t.json()).files||{})}catch{}try{let t=await fetch(`/api/workflows/${e}/artifacts/paper%2FPAPER_IMPROVEMENT_LOG.md`);'
        To = 'let t=async()=>{let n=[];try{let t=await fetch(`/api/workflows/${e}/artifacts`);t.ok&&(n=await t.json(),d(n))}catch{}try{let t=await fetch(`/api/workflows/${e}/artifacts/extract-status`);t.ok&&C((await t.json()).files||{})}catch{}if(!n.some(e=>e.path===`paper/PAPER_IMPROVEMENT_LOG.md`)){_([]);return}try{let t=await fetch(`/api/workflows/${e}/artifacts/paper%2FPAPER_IMPROVEMENT_LOG.md`);'
    }
    [pscustomobject]@{
        From = 'placeholder:n===`executor`?`例如 claude-opus-4-6 / claude-sonnet-4-5-20250929（传给 Claude CLI --model）`:`例如 gpt-4o / claude-sonnet-4-5-20250929`'
        To = 'placeholder:`例如 deepseek-chat / glm-4.5 / gpt-4o`'
    }
    [pscustomobject]@{
        From = '说明：暂停会立即终止本地进程。但 Anthropic 服务端已发出的 API 请求会继续生成响应（约 1-3 分钟），这部分 token 仍会计费——这是 Anthropic API 的原生行为，所有 Claude CLI 工具都一样。'
        To = '说明：暂停会立即终止本地执行，但已经提交给模型服务商的 API 请求可能继续处理，并按服务商规则计费。'
    }
)

foreach ($entry in $replacements) {
    if ($content.Contains($entry.From)) {
        $content = $content.Replace($entry.From, $entry.To)
    } elseif (-not $content.Contains($entry.To)) {
        throw "Expected source or replacement text is missing: $($entry.From)"
    }
}

$distCliRegex = [regex]::new(
    '\(0,P\.jsx\)\(p1,\{label:`Claude CLI 路径`.*?children:`自动探测`\}\)\}\)',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if ($distCliRegex.IsMatch($content)) {
    $content = $distCliRegex.Replace($content, '', 1)
} elseif ($content.Contains('Claude CLI 路径')) {
    throw 'Could not isolate the obsolete Claude CLI controls in the distribution bundle.'
}

[System.IO.File]::WriteAllText($resolved, $content, $utf8)
Write-Host "Synchronized ArHub branding in $resolved"

if (-not $FrontendSourcePath) {
    $FrontendSourcePath = Join-Path $PSScriptRoot '..\frontend-src\index.js'
}
$sourceResolved = (Resolve-Path -LiteralPath $FrontendSourcePath).Path
$sourceContent = [System.IO.File]::ReadAllText($sourceResolved, $utf8)
$sourceReplacements = @(
    [pscustomobject]@{
        From = 'placeholder={n === `executor` ? `例如 claude-opus-4-6 / claude-sonnet-4-5-20250929（传给 Claude CLI --model）` : `例如 gpt-4o / claude-sonnet-4-5-20250929`}'
        To = 'placeholder={`例如 deepseek-chat / glm-4.5 / gpt-4o`}'
    }
    [pscustomobject]@{
        From = '说明：暂停会立即终止本地进程。但 Anthropic 服务端已发出的 API 请求会继续生成响应（约 1-3 分钟），这部分 token 仍会计费——这是 Anthropic API 的原生行为，所有 Claude CLI 工具都一样。'
        To = '说明：暂停会立即终止本地执行，但已经提交给模型服务商的 API 请求可能继续处理，并按服务商规则计费。'
    }
)

foreach ($entry in $sourceReplacements) {
    if ($sourceContent.Contains($entry.From)) {
        $sourceContent = $sourceContent.Replace($entry.From, $entry.To)
    } elseif (-not $sourceContent.Contains($entry.To)) {
        throw "Expected frontend source or replacement text is missing: $($entry.From)"
    }
}

$sourceCliRegex = [regex]::new(
    '<_Component12 label=\{`Claude CLI 路径`\}.*?</Component997>',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if ($sourceCliRegex.IsMatch($sourceContent)) {
    $sourceContent = $sourceCliRegex.Replace($sourceContent, '', 1)
} elseif ($sourceContent.Contains('Claude CLI 路径')) {
    throw 'Could not isolate the obsolete Claude CLI controls in the recovered frontend source.'
}

[System.IO.File]::WriteAllText($sourceResolved, $sourceContent, $utf8)
Write-Host "Synchronized provider-neutral frontend source in $sourceResolved"
