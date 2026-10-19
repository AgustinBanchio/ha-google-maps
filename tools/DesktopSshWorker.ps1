#requires -Version 7.0
param([Parameter(Mandatory)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
$request = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
$runDirectory = Split-Path -Parent $RequestPath
$resultPath = Join-Path $runDirectory 'result.json'
$result = [ordered]@{ session = (Get-Process -Id $PID).SessionId; exit_code = 1; stdout = ''; stderr = '' }
try {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in @('-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', '-o', 'ForwardAgent=no', [string]$request.target, [string]$request.command)) {
        $startInfo.ArgumentList.Add($argument)
    }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $null = $process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if ($request.input_text) { $process.StandardInput.Write([string]$request.input_text) }
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(150000)) {
        $process.Kill()
        throw 'This SSH request exceeded its 150-second limit.'
    }
    $result.exit_code = $process.ExitCode
    $result.stdout = $stdoutTask.GetAwaiter().GetResult()
    $result.stderr = $stderrTask.GetAwaiter().GetResult()
    $process.Dispose()
} catch {
    $result.stderr = $_.Exception.Message
} finally {
    $temporaryPath = Join-Path $runDirectory 'result.pending'
    [System.IO.File]::WriteAllText($temporaryPath, ($result | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::Move($temporaryPath, $resultPath)
}
