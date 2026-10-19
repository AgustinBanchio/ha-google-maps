#requires -Version 7.0
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.@:-]*$')][string]$Target,
    [Parameter(Mandatory)][string]$RemoteCommand,
    [string]$InputText = ''
)
$ErrorActionPreference = 'Stop'
# Keep 1Password's normal authorization in the logged-in desktop session.
# No key is exported, agent forwarded, service changed, or persistent task installed.
$requestId = [guid]::NewGuid().ToString('N')
$workspacePath = Split-Path $PSScriptRoot -Parent
$runDirectory = Join-Path $workspacePath ('.ssh-runs\' + $requestId)
$null = New-Item -ItemType Directory -Path $runDirectory
$requestPath = Join-Path $runDirectory 'request.json'
$resultPath = Join-Path $runDirectory 'result.json'
$workerPath = Join-Path $PSScriptRoot 'DesktopSshWorker.ps1'
$request = @{ target = $Target; command = $RemoteCommand; input_text = $InputText }
[System.IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json), [System.Text.UTF8Encoding]::new($false))
$taskName = 'T3 Desktop SSH ' + $requestId
$registered = $false
try {
    $action = New-ScheduledTaskAction -Execute (Get-Process -Id $PID).Path -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $workerPath + '" -RequestPath "' + $requestPath + '"')
    $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $null = Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings -Description 'One-shot SSH request using the user desktop session and normal 1Password approval.'
    $registered = $true
    Start-ScheduledTask -TaskName $taskName
    $deadline = [datetime]::UtcNow.AddSeconds(180)
    while (-not (Test-Path -LiteralPath $resultPath)) {
        if ([datetime]::UtcNow -gt $deadline) { throw 'Desktop SSH helper timed out. The desktop must be logged in and 1Password available.' }
        Start-Sleep -Milliseconds 300
    }
    $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
    if ($result.exit_code -ne 0) { throw ('SSH failed: ' + $result.stderr.Trim()) }
    if ($result.stderr) { Write-Warning $result.stderr.Trim() }
    Write-Output $result.stdout.TrimEnd()
} finally {
    if ($registered) {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task.State -eq 'Running') { Stop-ScheduledTask -TaskName $taskName }
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
}
