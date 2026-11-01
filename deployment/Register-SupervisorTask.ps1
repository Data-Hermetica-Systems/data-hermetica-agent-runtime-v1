[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$EngineRoot,
      [string]$TaskName = 'DataHermetica-InvoiceEngine-Supervisor')
$ErrorActionPreference = 'Stop'
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { throw "Task already exists: $TaskName. Inspect it before changing registration." }
$script = Join-Path $EngineRoot 'app\invoice_supervisor.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Missing supervisor: $script" }
$python = (Get-Command python.exe -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { $pythonw = $python }
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$arguments = '"{0}" --engine-root "{1}" --continuous' -f $script,$EngineRoot
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory (Join-Path $EngineRoot 'app')
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Write-Host "Registered $TaskName. Task was not started."
