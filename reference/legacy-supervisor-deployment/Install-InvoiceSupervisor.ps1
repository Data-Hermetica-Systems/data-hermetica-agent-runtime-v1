[CmdletBinding()]
param(
    [string]$EngineRoot = 'H:\DataHermetica\InvoiceEngine',
    [switch]$RegisterTask
)

$ErrorActionPreference = 'Stop'
$taskName = 'DataHermetica-InvoiceEngine-Supervisor'
$packageRoot = Split-Path -Parent $PSScriptRoot
$sourceApp = Join-Path $packageRoot 'app'
$sourceConfig = Join-Path $packageRoot 'config'
$destinationApp = Join-Path $EngineRoot 'app'
$destinationConfig = Join-Path $EngineRoot 'config'

foreach ($sourcePath in @(
    (Join-Path $sourceApp 'invoice_supervisor.py'),
    (Join-Path $sourceConfig 'invoice_supervisor_config.json')
)) {
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Required package file was not found: $sourcePath"
    }
}

foreach ($destination in @($EngineRoot, $destinationApp, $destinationConfig)) {
    if (-not (Test-Path -LiteralPath $destination -PathType Container)) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
    }
}

$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    throw 'python.exe was not found in PATH. Install or expose Python 3.12 before installing the supervisor.'
}

$pythonExe = $pythonCommand.Source
$pythonwExe = Join-Path (Split-Path -Parent $pythonExe) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonwExe -PathType Leaf)) {
    $pythonwExe = $pythonExe
    Write-Warning 'pythonw.exe was not found. The scheduled task may open a console window.'
}

if ([string]::IsNullOrWhiteSpace($env:OneDriveCommercial)) {
    throw 'OneDriveCommercial is not defined in this PowerShell session. Sign in to OneDrive and reopen PowerShell.'
}
$intakePath = Join-Path $env:OneDriveCommercial 'InvoiceIntake\Incoming'
if (-not (Test-Path -LiteralPath $intakePath -PathType Container)) {
    New-Item -ItemType Directory -Path $intakePath -Force | Out-Null
}

$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$existingSupervisor = Join-Path $destinationApp 'invoice_supervisor.py'
$existingConfig = Join-Path $destinationConfig 'invoice_supervisor_config.json'
$existingFiles = @($existingSupervisor, $existingConfig) |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }

if ($existingFiles.Count -gt 0) {
    $backupStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupDirectory = Join-Path $EngineRoot "backup\supervisor_before_install_$backupStamp"
    New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
    foreach ($existingFile in $existingFiles) {
        Copy-Item -LiteralPath $existingFile -Destination $backupDirectory -Force
    }
    Write-Host "Existing supervisor files backed up to: $backupDirectory" -ForegroundColor Yellow
}

Copy-Item -LiteralPath (Join-Path $sourceApp 'invoice_supervisor.py') `
    -Destination $destinationApp -Force
Copy-Item -LiteralPath (Join-Path $sourceConfig 'invoice_supervisor_config.json') `
    -Destination $destinationConfig -Force

$envFile = [Environment]::GetEnvironmentVariable('DATA_HERMETICA_INVOICE_ENGINE_ROOT', 'User')
if ($envFile -ne $EngineRoot) {
    [Environment]::SetEnvironmentVariable('DATA_HERMETICA_INVOICE_ENGINE_ROOT', $EngineRoot, 'User')
    Write-Host 'Set the user-level DATA_HERMETICA_INVOICE_ENGINE_ROOT environment variable.' -ForegroundColor Cyan
    Write-Warning 'Open a new PowerShell session before running the supervisor so the updated environment is available.'
}

Write-Host "Installed supervisor: $existingSupervisor" -ForegroundColor Green
Write-Host "Supervisor config:    $existingConfig" -ForegroundColor Green
Write-Host "Incoming folder:      $intakePath" -ForegroundColor Green

if ($RegisterTask) {
    $userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
    $actionArguments = '"{0}" --continuous' -f $existingSupervisor
    $action = New-ScheduledTaskAction `
        -Execute $pythonwExe `
        -Argument $actionArguments `
        -WorkingDirectory $destinationApp
    $principal = New-ScheduledTaskPrincipal `
        -UserId $userId `
        -LogonType Interactive `
        -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable `
        -ExecutionTimeLimit ([TimeSpan]::Zero)

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description 'Polls the OneDrive InvoiceIntake Incoming folder and runs the local Data Hermetica invoice extraction worker.' `
        -Force | Out-Null

    Write-Host "Registered Task Scheduler task: $taskName" -ForegroundColor Green
    Write-Host 'The task is registered for the next user sign-in and was not started immediately.' -ForegroundColor Yellow
} else {
    Write-Host 'Task Scheduler registration was skipped. Run the one-time supervisor scan and review its outputs before registering the task.' -ForegroundColor Yellow
}
