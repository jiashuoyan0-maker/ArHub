[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,
    [string]$InstallDir,
    [string]$PublisherName = $env:ARHUB_PUBLISHER_NAME,
    [switch]$AllowUnsigned,
    [switch]$RequireUnsigned,
    [switch]$PreserveInstallOnFailure,
    [switch]$StopRunningArHub,
    [int]$StartupTimeoutSeconds = 120,
    [ValidateSet('auto', 'full', 'lite')]
    [string]$RuntimeProfile = 'auto',
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'signing-helpers.ps1')

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ($AllowUnsigned -and $RequireUnsigned) { throw 'AllowUnsigned and RequireUnsigned are mutually exclusive.' }
$smokeRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'ArHub\smoke'))
if (-not $InstallDir) { $InstallDir = Join-Path $smokeRoot 'custom install\ArHub' }
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
$registeredInstallPath = $false
$dataPreserved = $false
$stoppedExistingApp = $false

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

function Get-ArHubUninstallEntries {
    $root = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall'
    if (-not (Test-Path -LiteralPath $root)) { return @() }
    return @(
        Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction SilentlyContinue } |
            Where-Object { $_.DisplayName -match '^ArHub(?:\s|$)' }
    )
}

$runningArHub = @(
    Get-CimInstance Win32_Process -Filter "Name = 'ArHub.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath }
)
if ($runningArHub.Count -gt 0 -and -not $StopRunningArHub) {
    throw 'ArHub is running. Close it first or pass -StopRunningArHub to restore it after the smoke test.'
}
$restartExecutable = @($runningArHub | Select-Object -ExpandProperty ExecutablePath -Unique | Select-Object -First 1)

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

$registryBackupDir = Join-Path $smokeRoot 'registry-backup'
New-Item -ItemType Directory -Path $registryBackupDir -Force | Out-Null
$registryBackups = @()
$registryIndex = 0
$registryEntriesBeforeTest = @(Get-ArHubUninstallEntries)
foreach ($entry in $registryEntriesBeforeTest) {
    $nativePath = $entry.PSPath -replace '^Microsoft\.PowerShell\.Core\\Registry::', ''
    $backupPath = Join-Path $registryBackupDir "uninstall-$registryIndex.reg"
    & reg.exe export $nativePath $backupPath /y | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Failed to back up uninstall registry key: $nativePath" }
    $registryBackups += $backupPath
    $registryIndex += 1
}

$oldAppData = $env:APPDATA
$oldArHubData = $env:ARHUB_DATA_DIR
$oldSmoke = $env:ARHUB_SMOKE_TEST

try {
    if ($runningArHub.Count -gt 0) {
        $stoppedExistingApp = $true
        $stopProcess = Start-Process -FilePath 'taskkill.exe' `
            -ArgumentList @('/IM', 'ArHub.exe', '/T', '/F') `
            -PassThru -Wait -WindowStyle Hidden
        $deadline = (Get-Date).AddSeconds(15)
        while ((Get-Process -Name 'ArHub' -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 250
        }
        if (Get-Process -Name 'ArHub' -ErrorAction SilentlyContinue) {
            throw 'Unable to stop the existing ArHub instance before the smoke test.'
        }
    }
    foreach ($entry in $registryEntriesBeforeTest) {
        Remove-Item -LiteralPath $entry.PSPath -Recurse -Force -ErrorAction Stop
    }

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
    # NSIS requires /D to be the final token and forbids quoting it, even for paths with spaces.
    $installArguments = '/S --no-desktop-shortcut /D=' + $install
    $installProcess = Start-Process -FilePath $installer -ArgumentList $installArguments -PassThru -Wait
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

    $matchingEntries = @(
        Get-ArHubUninstallEntries |
            Where-Object {
                $_.UninstallString -and
                ([string]$_.UninstallString).IndexOf($uninstaller, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
            }
    )
    if ($matchingEntries.Count -ne 1) {
        throw "Expected one uninstall entry for the custom install directory, found $($matchingEntries.Count)."
    }
    $registeredInstallPath = $true

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

    $effectiveRuntimeProfile = $RuntimeProfile
    if ($effectiveRuntimeProfile -eq 'auto') {
        $installedPackageJson = Join-Path $install 'resources\app\package.json'
        if (Test-Path -LiteralPath $installedPackageJson -PathType Leaf) {
            $installedMetadata = Get-Content -LiteralPath $installedPackageJson -Encoding UTF8 | ConvertFrom-Json
            $effectiveRuntimeProfile = [string]$installedMetadata.arhubRuntimeProfile
        }
        if ($effectiveRuntimeProfile -notin @('full', 'lite')) {
            $effectiveRuntimeProfile = if (Test-Path -LiteralPath (Join-Path $install 'runtime\node')) { 'full' } else { 'lite' }
        }
    }
    if ($effectiveRuntimeProfile -eq 'lite') {
        & (Join-Path $PSScriptRoot 'assert-lite-runtime.ps1') -RuntimeDir (Join-Path $install 'runtime')
    } else {
        & (Join-Path $PSScriptRoot 'assert-runtime.ps1') `
            -RuntimeDir (Join-Path $install 'runtime') `
            -EnforceLock `
            -SkipPythonDependencyCheck
    }

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
    if (Test-Path -LiteralPath $install) {
        throw "Uninstall completed but the custom install directory still exists: $install"
    }
    if (-not (Test-Path -LiteralPath $mainLog -PathType Leaf)) {
        throw 'Uninstall removed user data even though deleteAppDataOnUninstall is disabled.'
    }
    $dataPreserved = $true
    $uninstalled = $true

    $completedAt = Get-Date
    $localAppDataRoot = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA).TrimEnd('\')
    $publicInstallDir = if ($install.StartsWith($localAppDataRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        '%LOCALAPPDATA%\' + $install.Substring($localAppDataRoot.Length).TrimStart('\')
    } else {
        '%ARHUB_SMOKE_ROOT%\app'
    }
    $report = [ordered]@{
        schemaVersion = 2
        status = 'passed'
        startedAt = $startedAt.ToUniversalTime().ToString('o')
        completedAt = $completedAt.ToUniversalTime().ToString('o')
        timings = [ordered]@{
            installationSeconds = [math]::Round(($installCompletedAt - $installStartedAt).TotalSeconds, 3)
            startupSeconds = [math]::Round(($startupCompletedAt - $startupStartedAt).TotalSeconds, 3)
            totalSeconds = [math]::Round(($completedAt - $startedAt).TotalSeconds, 3)
        }
        installer = [System.IO.Path]::GetFileName($installer)
        runtimeProfile = $effectiveRuntimeProfile
        installDir = $publicInstallDir
        installation = [ordered]@{
            customDirectory = $true
            registryPathMatched = $registeredInstallPath
            userDataPreserved = $dataPreserved
        }
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
    foreach ($entry in @(Get-ArHubUninstallEntries)) {
        if ($entry.UninstallString -and ([string]$entry.UninstallString).IndexOf($install, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            Remove-Item -LiteralPath $entry.PSPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    foreach ($backupPath in $registryBackups) {
        & reg.exe import $backupPath | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Warning "Failed to restore uninstall registry backup: $backupPath" }
    }
    $env:APPDATA = $oldAppData
    $env:ARHUB_DATA_DIR = $oldArHubData
    $env:ARHUB_SMOKE_TEST = $oldSmoke
    if ($stoppedExistingApp -and $restartExecutable.Count -eq 1 -and (Test-Path -LiteralPath $restartExecutable[0] -PathType Leaf)) {
        Start-Process -FilePath $restartExecutable[0] | Out-Null
    }
}
