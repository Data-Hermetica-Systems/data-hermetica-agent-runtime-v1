[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'DataHermetica-InvoiceEngine-Supervisor'
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Host "Scheduled task not found: $taskName"
    exit 0
}

if ($task.State -eq 'Running') {
    Stop-ScheduledTask -TaskName $taskName
}
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Host "Removed scheduled task: $taskName"
Write-Host 'Supervisor source, configuration, logs, queue state, and invoices were left in place.'
