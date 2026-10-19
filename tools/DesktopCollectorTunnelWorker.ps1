#requires -Version 7.0
param([Parameter(Mandatory)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
$request = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
if ([string]$request.target -notmatch '^[A-Za-z0-9][A-Za-z0-9_.@:-]*$') { throw 'Invalid SSH target.' }
$runDirectory = Split-Path -Parent $RequestPath
$resultPath = Join-Path $runDirectory 'result.json'
$readyPath = Join-Path $runDirectory 'ready.json'
$cancelPath = Join-Path $runDirectory 'cancel'
$result = [ordered]@{ session = (Get-Process -Id $PID).SessionId; exit_code = 1; stderr = '' }
$process = $null
function Save-TunnelResult {
    if (-not (Test-Path -LiteralPath $resultPath)) {
        $temporary = Join-Path $runDirectory 'result.pending'
        [IO.File]::WriteAllText($temporary, ($result | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporary, $resultPath)
    }
}
try {
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = Join-Path $env:WINDIR 'System32/OpenSSH/ssh.exe'
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in @('-T', '-a', '-o', 'BatchMode=yes', '-o', 'PreferredAuthentications=publickey', '-o', 'PasswordAuthentication=no', '-o', 'KbdInteractiveAuthentication=no', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', '-o', 'ForwardAgent=no', '-o', 'ExitOnForwardFailure=yes', '-N', '-L', '127.0.0.1:8787:127.0.0.1:8787', [string]$request.target)) {
        $startInfo.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $null = $process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.StandardInput.Close()
    $ready = $false
    $readyDeadline = [datetime]::UtcNow.AddSeconds(80)
    $finishDeadline = $null
    while (-not $process.HasExited) {
        if (Test-Path -LiteralPath $cancelPath) { $result.exit_code = 0; Save-TunnelResult; $process.Kill(); break }
        if (-not $ready) {
            $listener = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue | Where-Object OwningProcess -eq $process.Id
            if ($listener) {
                $metadata = @{ process_id = $process.Id; started_utc_ticks = $process.StartTime.ToUniversalTime().Ticks; session = $result.session }
                $temporary = Join-Path $runDirectory 'ready.pending'
                [IO.File]::WriteAllText($temporary, ($metadata | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
                [IO.File]::Move($temporary, $readyPath)
                $ready = $true
                $finishDeadline = [datetime]::UtcNow.AddSeconds([int]$request.duration_seconds)
            } elseif ([datetime]::UtcNow -gt $readyDeadline) { throw 'SSH key authentication or listener setup timed out.' }
        } elseif ([datetime]::UtcNow -ge $finishDeadline) { $result.exit_code = 0; Save-TunnelResult; $process.Kill(); break }
        Start-Sleep -Milliseconds 200
    }
    $process.WaitForExit()
    if ($result.exit_code -ne 0) { $result.exit_code = $process.ExitCode }
    $null = $stdoutTask.GetAwaiter().GetResult()
    $result.stderr = $stderrTask.GetAwaiter().GetResult()
} catch {
    $result.stderr = $_.Exception.Message
} finally {
    if ($process) {
        if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
        $process.Dispose()
    }
    Save-TunnelResult
}
