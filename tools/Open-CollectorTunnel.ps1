#requires -Version 7.0
param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.@:-]*$')][string]$Target,
    [ValidateRange(5, 28800)][int]$DurationSeconds = 28800
)
$ErrorActionPreference = 'Stop'
$workspacePath = Split-Path $PSScriptRoot -Parent
if (-not $Target) {
    $connectionPath = Join-Path $workspacePath '.local/connection.json'
    $Target = (Get-Content -LiteralPath $connectionPath -Raw | ConvertFrom-Json).target
}
if ($Target -notmatch '^[A-Za-z0-9][A-Za-z0-9_.@:-]*$') { throw 'Invalid SSH target.' }
if (Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Local port 8787 is already in use. Close the existing local tunnel before opening another.'
}
$runDirectory = Join-Path $workspacePath ('.ssh-runs/tunnel-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $runDirectory
$requestPath = Join-Path $runDirectory 'request.json'
$resultPath = Join-Path $runDirectory 'result.json'
$readyPath = Join-Path $runDirectory 'ready.json'
$cancelPath = Join-Path $runDirectory 'cancel'
$request = @{ target = $Target; duration_seconds = $DurationSeconds }
[IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
$taskName = 'T3 Collector Tunnel ' + [guid]::NewGuid().ToString('N')
$registered = $false
try {
    # 1Password authorization must happen in the logged-in, non-admin desktop
    # session, even when this command is launched from T3's Session 0 terminal.
    $workerPath = Join-Path $PSScriptRoot 'DesktopCollectorTunnelWorker.ps1'
    $action = New-ScheduledTaskAction -Execute (Get-Process -Id $PID).Path -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $workerPath + '" -RequestPath "' + $requestPath + '"')
    $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds ($DurationSeconds + 120)) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $null = Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings -Description 'Temporary collector SSH tunnel with normal desktop 1Password approval.'
    $registered = $true
    Start-ScheduledTask -TaskName $taskName
    Write-Host 'Connecting with your SSH key through the desktop 1Password agent. Approve its normal request if prompted.'
    $deadline = [datetime]::UtcNow.AddSeconds(90)
    while (-not (Test-Path -LiteralPath $readyPath)) {
        if (Test-Path -LiteralPath $resultPath) { throw 'SSH key authentication or tunnel setup failed. Unlock desktop 1Password and approve its normal SSH request. Private diagnostics are in .ssh-runs/.' }
        if ([datetime]::UtcNow -gt $deadline) { throw 'Desktop SSH tunnel timed out. Keep the Windows desktop logged in and 1Password available.' }
        Start-Sleep -Milliseconds 250
    }
    Write-Host 'Connected. Open http://127.0.0.1:8787. Keep this terminal open; Ctrl+C closes this tunnel.'
    $finishDeadline = [datetime]::UtcNow.AddSeconds($DurationSeconds + 10)
    while (-not (Test-Path -LiteralPath $resultPath)) {
        if ([datetime]::UtcNow -ge $finishDeadline) { break }
        $workerTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if (-not $workerTask -or $workerTask.State -ne 'Running') { throw 'Desktop tunnel worker ended unexpectedly; closing its SSH process.' }
        Start-Sleep -Milliseconds 250
    }
    $result = if (Test-Path -LiteralPath $resultPath) { Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json } else { @{ exit_code = 0 } }
    if ($result.exit_code -ne 0) { throw 'The SSH tunnel ended unexpectedly. Private diagnostics are in .ssh-runs/.' }
} finally {
    # Ask the desktop worker to stop its own SSH process, then remove its task.
    [IO.File]::WriteAllText($cancelPath, 'cancel')
    if ($registered) {
        $cleanupDeadline = [datetime]::UtcNow.AddSeconds(5)
        while (-not (Test-Path -LiteralPath $resultPath) -and [datetime]::UtcNow -lt $cleanupDeadline) { Start-Sleep -Milliseconds 100 }
        if (Test-Path -LiteralPath $readyPath) {
            $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
            $ownedProcess = Get-Process -Id $ready.process_id -ErrorAction SilentlyContinue
            if ($ownedProcess -and $ownedProcess.Path -eq (Join-Path $env:WINDIR 'System32/OpenSSH/ssh.exe') -and $ownedProcess.StartTime.ToUniversalTime().Ticks -eq $ready.started_utc_ticks) {
                Stop-Process -Id $ownedProcess.Id
            }
        }
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            if ($task.State -eq 'Running') { Stop-ScheduledTask -TaskName $taskName }
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }
    }
}
