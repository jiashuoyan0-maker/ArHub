[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,
    [string]$InstallDir,
    [string]$PublisherName = $env:ARHUB_PUBLISHER_NAME,
    [switch]$AllowUnsigned,
    [switch]$RequireUnsigned,
    [switch]$PreserveInstallOnFailure,
    [int]$StartupTimeoutSeconds = 120,
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'signing-helpers.ps1')

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ($AllowUnsigned -and $RequireUnsigned) { throw 'AllowUnsigned and RequireUnsigned are mutually exclusive.' }
$smokeRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'ArHub\smoke'))
if (-not $InstallDir) { $InstallDir = Join-Path $smokeRoot 'app' }
$install = [System.IO.Path]::GetFullPath($InstallDir)
$smokePrefix = $smokeRoot.TrimEnd('\') + '\'
if (-not $install.StartsWith($smokePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Smoke-test install directory must stay inside $smokeRoot"
}
if (-not $AllowUnsigned -and -not $RequireUnsigned -and [string]::IsNullOrWhiteSpace($PublisherName)) {
    throw 'PublisherName is required for a signed installer smoke test.'
}

$installer = (Resolve-Path -LiteralPath $InstallerPath).Path
if (-not $ReportPath) { $ReportPath = Join-Path $projectRoot 'release\installer-smoke-report.json' }
$reportFile = [System.IO.Path]::GetFullPath($ReportPath)
$dataRoot = Join-Path $smokeRoot 'data'
$mainLog = Join-Path $dataRoot 'ArHub\logs\desktop-main.log'
$appExe = Join-Path $install 'ArHub.exe'
$elevationHelper = Join-Path $install 'resources\elevate.exe'
$uninstaller = Join-Path $install 'Uninstall ArHub.exe'
$startedAt = Get-Date
$installStartedAt = $null
$installCompletedAt = $null
$startupStartedAt = $null
$startupCompletedAt = $null
$appProcess = $null
$uninstalled = $false

function Assert-SafeSmokePath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($smokePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the smoke-test root: $full"
    }
    return $full
}

function Assert-ReleaseSignature([string]$Path) {
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($RequireUnsigned) {
        if ($signature.Status -ne 'NotSigned') {
            throw "Official unsigned release target must be NotSigned: $Path ($($signature.Status))"
        }
        return $signature.Status.ToString()
    }
    if ($AllowUnsigned) {
        if ($signature.Status -notin @('Valid', 'NotSigned')) {
            throw "Unexpected signature status for $Path`: $($signature.Status)"
        }
        return $signature.Status.ToString()
    }
    if ($signature.Status -ne 'Valid') {
        throw "Invalid Authenticode signature for $Path`: $($signature.Status)"
    }
    if (-not $signature.TimeStamperCertificate) {
        throw "Timestamp signature is missing for $Path"
    }
    $null = Assert-PublicCertificateTrust -Certificate $signature.TimeStamperCertificate -Label "The timestamp on $([System.IO.Path]::GetFileName($Path))"
    $commonName = $signature.SignerCertificate.GetNameInfo(
        [System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName,
        $false
    )
    if ($commonName -ne $PublisherName) {
        throw "Publisher mismatch for $Path`: '$commonName'"
    }
    $null = Assert-PublicCertificateTrust -Certificate $signature.SignerCertificate -Label "The signature on $([System.IO.Path]::GetFileName($Path))"
    return $signature.Status.ToString()
}

function Restore-Shortcut([string]$Path, [string]$BackupPath, [bool]$Existed) {
    if ($Existed) {
        Copy-Item -LiteralPath $BackupPath -Destination $Path -Force
    } else {
        Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    }
}

$desktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'ArHub.lnk'
$startMenuShortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\ArHub.lnk'
$shortcutBackupDir = Join-Path $smokeRoot 'shortcut-backup'
New-Item -ItemType Directory -Path $shortcutBackupDir -Force | Out-Null
$desktopExisted = Test-Path -LiteralPath $desktopShortcut -PathType Leaf
$startMenuExisted = Test-Path -LiteralPath $startMenuShortcut -PathType Leaf
$desktopBackup = Join-Path $shortcutBackupDir 'desktop-ArHub.lnk'
$startMenuBackup = Join-Path $shortcutBackupDir 'start-menu-ArHub.lnk'
if ($desktopExisted) { Copy-Item -LiteralPath $desktopShortcut -Destination $desktopBackup -Force }
if ($startMenuExisted) { Copy-Item -LiteralPath $startMenuShortcut -Destination $startMenuBackup -Force }

$oldAppData = $env:APPDATA
$oldArHubData = $env:ARHUB_DATA_DIR
$oldSmoke = $env:ARHUB_SMOKE_TEST

try {
    if (Test-Path -LiteralPath $install) {
        $safeInstall = Assert-SafeSmokePath $install
        Remove-Item -LiteralPath $safeInstall -Recurse -Force
    }
    if (Test-Path -LiteralPath $dataRoot) {
        $safeData = Assert-SafeSmokePath $dataRoot
        Remove-Item -LiteralPath $safeData -Recurse -Force
    }

    $installerSignature = Assert-ReleaseSignature $installer
    $env:ARHUB_SMOKE_TEST = '1'
    $installStartedAt = Get-Date
    $installProcess = Start-Process -FilePath $installer -ArgumentList @(
        '/S',
        '--no-desktop-shortcut',
        "/D=$install"
    ) -PassThru -Wait
    $installCompletedAt = Get-Date
    if ($installProcess.ExitCode -ne 0) {
        throw "Installer exited with code $($installProcess.ExitCode)"
    }
    if (-not (Test-Path -LiteralPath $appExe -PathType Leaf)) {
        throw "Installed application is missing: $appExe"
    }
    if (-not (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
        throw "Installed uninstaller is missing: $uninstaller"
    }

    $autoRunDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    do {
        $autoRunProcesses = @(
            Get-CimInstance Win32_Process -Filter "Name = 'ArHub.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.ExecutablePath -and $_.ExecutablePath.Equals($appExe, [System.StringComparison]::OrdinalIgnoreCase) }
        )
        if ($autoRunProcesses.Count -gt 0) { Start-Sleep -Milliseconds 500 }
    } while ($autoRunProcesses.Count -gt 0 -and (Get-Date) -lt $autoRunDeadline)
    if ($autoRunProcesses.Count -gt 0) {
        throw 'The installer-launched ArHub process did not finish smoke-test mode.'
    }

    $appSignature = Assert-ReleaseSignature $appExe
    $elevationSignature = Assert-ReleaseSignature $elevationHelper
    $uninstallerSignature = Assert-ReleaseSignature $uninstaller

    & (Join-Path $PSScriptRoot 'assert-runtime.ps1') `
        -RuntimeDir (Join-Path $install 'runtime') `
        -EnforceLock `
        -SkipPythonDependencyCheck

    $env:APPDATA = $dataRoot
    $env:ARHUB_DATA_DIR = Join-Path $dataRoot 'ArHub'
    $startupStartedAt = Get-Date
    $appProcess = Start-Process -FilePath $appExe -ArgumentList '--arhub-smoke-test' -PassThru
    try {
        $appProcess | Wait-Process -Timeout $StartupTimeoutSeconds -ErrorAction Stop
    } catch {
        & taskkill.exe /PID $appProcess.Id /T /F 2>$null | Out-Null
        throw "ArHub did not complete its startup smoke test within $StartupTimeoutSeconds seconds."
    }
    $appProcess.Refresh()
    if ($appProcess.ExitCode -ne 0) {
        throw "ArHub smoke-test process exited with code $($appProcess.ExitCode)"
    }
    $startupCompletedAt = Get-Date
    if (-not (Test-Path -LiteralPath $mainLog -PathType Leaf)) {
        throw "Desktop startup log is missing: $mainLog"
    }
    $logText = Get-Content -LiteralPath $mainLog -Encoding UTF8 | Out-String
    if ($logText -notmatch '\[App\] Backend is ready') {
        throw 'The packaged backend did not report ready.'
    }
    if ($logText -notmatch '\[SmokeTest\] Frontend loaded') {
        throw 'The packaged frontend did not finish loading.'
    }

    $orphaned = @(
        Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($install, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 }
    )
    if ($orphaned.Count -gt 0) {
        throw "The smoke test left $($orphaned.Count) backend process(es) running."
    }

    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList '/S' -PassThru -Wait
    if ($uninstallProcess.ExitCode -ne 0) {
        throw "Uninstaller exited with code $($uninstallProcess.ExitCode)"
    }
    $deadline = (Get-Date).AddSeconds(30)
    while ((Test-Path -LiteralPath $install) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }
    if (Test-Path -LiteralPath $appExe) {
        throw 'Uninstall completed but ArHub.exe is still present.'
    }
    $uninstalled = $true

    $completedAt = Get-Date
    $localAppDataRoot = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA).TrimEnd('\')
    $publicInstallDir = if ($install.StartsWith($localAppDataRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        '%LOCALAPPDATA%\' + $install.Substring($localAppDataRoot.Length).TrimStart('\')
    } else {
        '%ARHUB_SMOKE_ROOT%\app'
    }
    $report = [ordered]@{
        schemaVersion = 1
        status = 'passed'
        startedAt = $startedAt.ToUniversalTime().ToString('o')
        completedAt = $completedAt.ToUniversalTime().ToString('o')
        timings = [ordered]@{
            installationSeconds = [math]::Round(($installCompletedAt - $installStartedAt).TotalSeconds, 3)
            startupSeconds = [math]::Round(($startupCompletedAt - $startupStartedAt).TotalSeconds, 3)
            totalSeconds = [math]::Round(($completedAt - $startedAt).TotalSeconds, 3)
        }
        installer = [System.IO.Path]::GetFileName($installer)
        installDir = $publicInstallDir
        signatures = [ordered]@{
            installer = $installerSignature
            application = $appSignature
            elevationHelper = $elevationSignature
            uninstaller = $uninstallerSignature
        }
        backendReady = $true
        frontendLoaded = $true
        uninstallPassed = $true
    }
    $reportDir = Split-Path -Parent $reportFile
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($reportFile, ($report | ConvertTo-Json -Depth 6), $utf8)
    Write-Host "Installer smoke test passed: $reportFile"
} finally {
    if ($appProcess -and -not $appProcess.HasExited) {
        & taskkill.exe /PID $appProcess.Id /T /F 2>$null | Out-Null
    }
    if (-not $uninstalled -and -not $PreserveInstallOnFailure -and (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
        Start-Process -FilePath $uninstaller -ArgumentList '/S' -Wait -ErrorAction SilentlyContinue
    }
    Restore-Shortcut $desktopShortcut $desktopBackup $desktopExisted
    Restore-Shortcut $startMenuShortcut $startMenuBackup $startMenuExisted
    $env:APPDATA = $oldAppData
    $env:ARHUB_DATA_DIR = $oldArHubData
    $env:ARHUB_SMOKE_TEST = $oldSmoke
}
