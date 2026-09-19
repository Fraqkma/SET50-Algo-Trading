[CmdletBinding()]
param([string]$TaskName = 'SET50 Settrade Daily Collector')

$ErrorActionPreference = 'Stop'
if (-not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) { throw 'Windows Task Scheduler cmdlets are unavailable.' }
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    [pscustomobject]@{ installed = $false; task_name = $TaskName; enabled = $false; state = 'NOT_INSTALLED'; next_run = $null; last_run = $null; last_result = $null } | ConvertTo-Json
    exit 0
}
$info = Get-ScheduledTaskInfo -TaskName $TaskName
[pscustomobject]@{
    installed = $true
    task_name = $TaskName
    enabled = ($task.State -ne 'Disabled')
    state = [string]$task.State
    next_run = $info.NextRunTime
    last_run = $info.LastRunTime
    last_result = $info.LastTaskResult
} | ConvertTo-Json
