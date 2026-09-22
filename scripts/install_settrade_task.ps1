[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$DryRun,
    [string]$TaskName = 'SET50 Settrade Daily Collector'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$launcher = Join-Path $repoRoot 'scripts\start_settrade_daily.bat'
$userId = if ($env:USERDOMAIN) { "$($env:USERDOMAIN)\$($env:USERNAME)" } else { $env:USERNAME }

if (-not (Test-Path -LiteralPath $launcher)) { throw "Launcher not found: $launcher" }
if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) { throw 'Windows Task Scheduler cmdlets are unavailable.' }

Write-Output "TaskName: $TaskName"
Write-Output "Trigger: Monday-Friday at 09:45 local Windows time"
Write-Output "Action: $launcher"
Write-Output "Instance policy: IgnoreNew"
Write-Output "Run identity: $userId (interactive, limited)"
Write-Output "WakeToRun: enabled where supported"

if ($DryRun) {
    Write-Output 'DRY_RUN: no scheduler task was changed.'
    exit 0
}

$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument "/d /c `"$launcher`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '09:45'
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 1)
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, 'Register or update scheduled task')) {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Output "INSTALLED: $TaskName"
}
