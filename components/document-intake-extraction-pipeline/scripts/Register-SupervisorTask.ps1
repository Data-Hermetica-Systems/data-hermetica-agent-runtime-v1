<#
.SYNOPSIS
    Registers the pipeline supervisor as a Windows scheduled task that starts at logon.
.DESCRIPTION
    The task runs the supervisor without a console window, under the current user, with
    limited privileges. The script refuses to replace an existing task and does not start
    the task it registers.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$EngineRoot,
    [string]$TaskName = 'DataHermetica-InvoiceEngine-Supervisor'
)
$ErrorActionPreference = 'Stop'

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw "Task already exists: $TaskName. Inspect it before changing registration."
}
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repositoryRoot 'src\document_pipeline\supervisor.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Missing supervisor: $script" }
if (-not (Test-Path -LiteralPath $EngineRoot -PathType Container)) { throw "Missing engine root: $EngineRoot" }

$python = (Get-Command python.exe -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { $pythonw = $python }

$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$arguments = '"{0}" --engine-root "{1}" --continuous' -f $script, $EngineRoot
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $repositoryRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Write-Host "Registered $TaskName. The task was not started."
