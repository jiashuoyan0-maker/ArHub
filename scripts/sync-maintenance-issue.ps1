[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Open', 'Close')]
    [string]$Action,
    [Parameter(Mandatory = $true)]
    [string]$Title,
    [string]$BodyFile,
    [string]$Label,
    [string]$LabelColor = '0366d6',
    [string]$LabelDescription = 'Automated maintenance',
    [string]$ResolvedComment = 'The automated maintenance check is healthy again.'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $env:GH_TOKEN) { throw 'GH_TOKEN is required.' }
if ($Action -eq 'Open' -and (-not $BodyFile -or -not (Test-Path -LiteralPath $BodyFile -PathType Leaf))) {
    throw 'BodyFile must point to a report when opening a maintenance issue.'
}

$rawIssues = & gh issue list --state all --limit 100 --json number,title,state
if ($LASTEXITCODE -ne 0) { throw 'Unable to list repository issues.' }
$issues = @($rawIssues | ConvertFrom-Json)
$matches = @(
    $issues |
        Where-Object { $_.title -ceq $Title } |
        Sort-Object number
)

if ($Action -eq 'Close') {
    foreach ($issue in @($matches | Where-Object state -eq 'OPEN')) {
        & gh issue close ([string]$issue.number) --comment $ResolvedComment
        if ($LASTEXITCODE -ne 0) { throw "Unable to close issue #$($issue.number)." }
    }
    Write-Host "Closed $(@($matches | Where-Object state -eq 'OPEN').Count) matching maintenance issue(s)."
    return
}

if ($Label) {
    & gh label create $Label --color $LabelColor --description $LabelDescription --force
    if ($LASTEXITCODE -ne 0) { throw "Unable to create or update label '$Label'." }
}

if ($matches.Count -eq 0) {
    $arguments = @('issue', 'create', '--title', $Title, '--body-file', $BodyFile)
    if ($Label) { $arguments += @('--label', $Label) }
    & gh @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create maintenance issue.' }
    return
}

$canonical = $matches[0]
if ($canonical.state -ne 'OPEN') {
    & gh issue reopen ([string]$canonical.number)
    if ($LASTEXITCODE -ne 0) { throw "Unable to reopen issue #$($canonical.number)." }
}
$editArguments = @('issue', 'edit', [string]$canonical.number, '--body-file', $BodyFile)
if ($Label) { $editArguments += @('--add-label', $Label) }
& gh @editArguments
if ($LASTEXITCODE -ne 0) { throw "Unable to update issue #$($canonical.number)." }

foreach ($duplicate in @($matches | Select-Object -Skip 1 | Where-Object state -eq 'OPEN')) {
    & gh issue close ([string]$duplicate.number) --comment "Superseded by #$($canonical.number); closing this duplicate maintenance alert."
    if ($LASTEXITCODE -ne 0) { throw "Unable to close duplicate issue #$($duplicate.number)." }
}

Write-Host "Synchronized maintenance issue #$($canonical.number)."
