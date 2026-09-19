[CmdletBinding(SupportsShouldProcess)]
param([string]$TaskName = 'SET50 Settrade Daily Collector')

$ErrorActionPreference = 'Stop'
if (-not (Get-Command Unregister-ScheduledTask -ErrorAction SilentlyContinue)) { throw 'Windows Task Scheduler cmdlets are unavailable.' }
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) { Write-Output "NOT_INSTALLED: $TaskName"; exit 0 }
if ($PSCmdlet.ShouldProcess($TaskName, 'Unregister scheduled task')) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "UNINSTALLED: $TaskName"
}
