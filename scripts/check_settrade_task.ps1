[CmdletBinding()]
param([string]$TaskName = 'SET50 Settrade Daily Collector')

$ErrorActionPreference = 'Stop'
if (-not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) { throw 'Windows Task Scheduler cmdlets are unavailable.' }
$reportPath = Join-Path $PSScriptRoot '..\reports\settrade_scheduler_status.json'
function Write-SchedulerStatus($value) {
    $json = $value | ConvertTo-Json -Depth 5
    $fullPath = [System.IO.Path]::GetFullPath($reportPath)
    $directory = [System.IO.Path]::GetDirectoryName($fullPath)
    if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory | Out-Null }
    [System.IO.File]::WriteAllText($fullPath, $json, [System.Text.UTF8Encoding]::new($false))
    Write-Output $json
}
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-SchedulerStatus ([pscustomobject]@{ checked_at = (Get-Date).ToUniversalTime().ToString('o'); installed = $false; task_name = $TaskName; enabled = $false; state = 'NOT_INSTALLED'; next_run = $null; last_run = $null; last_result = $null; actions = @() })
    exit 0
}
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-SchedulerStatus ([pscustomobject]@{
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    installed = $true
    task_name = $TaskName
    enabled = ($task.State -ne 'Disabled')
    state = [string]$task.State
    next_run = $info.NextRunTime
    last_run = $info.LastRunTime
    last_result = $info.LastTaskResult
    actions = @($task.Actions | ForEach-Object { [pscustomobject]@{ execute = $_.Execute; arguments = $_.Arguments; working_directory = $_.WorkingDirectory } })
})
