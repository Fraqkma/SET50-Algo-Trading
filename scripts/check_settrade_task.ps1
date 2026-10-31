[CmdletBinding()]
param([string]$TaskName = 'SET50 Settrade Daily Collector')

$ErrorActionPreference = 'Stop'
$reportPath = Join-Path $PSScriptRoot '..\reports\settrade_scheduler_status.json'
function Write-SchedulerStatus($value) {
    $json = $value | ConvertTo-Json -Depth 5
    $fullPath = [System.IO.Path]::GetFullPath($reportPath)
    $directory = [System.IO.Path]::GetDirectoryName($fullPath)
    if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory | Out-Null }
    [System.IO.File]::WriteAllText($fullPath, $json, [System.Text.UTF8Encoding]::new($false))
    Write-Output $json
}
$service = New-Object -ComObject Schedule.Service
$service.Connect()
$folder = $service.GetFolder('\')
try { $task = $folder.GetTask($TaskName) }
catch {
    if ($_.Exception.HResult -eq -2147024894) {
    Write-SchedulerStatus ([pscustomobject]@{ checked_at = (Get-Date).ToUniversalTime().ToString('o'); installed = $false; task_name = $TaskName; enabled = $false; state = 'NOT_INSTALLED'; next_run = $null; last_run = $null; last_result = $null; actions = @() })
    exit 0
    }
    throw
}
$definition = $task.Definition
$logonNames = @{ 1 = 'Password'; 2 = 'S4U'; 3 = 'InteractiveToken'; 4 = 'Group'; 5 = 'ServiceAccount'; 6 = 'InteractiveTokenOrPassword' }
$runLevelNames = @{ 0 = 'Limited'; 1 = 'HighestAvailable' }
$instanceNames = @{ 0 = 'Parallel'; 1 = 'Queue'; 2 = 'IgnoreNew'; 3 = 'StopExisting' }
$logonType = $logonNames[[int]$definition.Principal.LogonType]
$taskState = @{ 0 = 'Unknown'; 1 = 'Disabled'; 2 = 'Queued'; 3 = 'Ready'; 4 = 'Running' }[[int]$task.State]
Write-SchedulerStatus ([pscustomobject]@{
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    installed = $true
    task_name = $TaskName
    enabled = [bool]$task.Enabled
    state = $taskState
    principal_user = [string]$definition.Principal.UserId
    next_run = ([datetime]$task.NextRunTime).ToString('o')
    last_run = ([datetime]$task.LastRunTime).ToString('o')
    last_result = [int]$task.LastTaskResult
    missed_runs = [int]$task.NumberOfMissedRuns
    logon_type = $logonType
    interactive_only = ($logonType -eq 'InteractiveToken')
    logged_out_capable = ($logonType -in @('Password', 'S4U', 'ServiceAccount', 'InteractiveTokenOrPassword'))
    run_level = $runLevelNames[[int]$definition.Principal.RunLevel]
    triggers = @($definition.Triggers | ForEach-Object { [pscustomobject]@{ type = [int]$_.Type; start_boundary = $_.StartBoundary; days_of_week = $_.DaysOfWeek; enabled = $_.Enabled } })
    settings = [pscustomobject]@{ start_when_available = $definition.Settings.StartWhenAvailable; wake_to_run = $definition.Settings.WakeToRun; multiple_instances = $instanceNames[[int]$definition.Settings.MultipleInstances]; execution_time_limit = $definition.Settings.ExecutionTimeLimit }
    actions = @($definition.Actions | ForEach-Object { [pscustomobject]@{ execute = $_.Path; arguments = $_.Arguments; working_directory = $_.WorkingDirectory } })
})
