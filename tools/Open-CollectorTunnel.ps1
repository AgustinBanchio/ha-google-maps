#requires -Version 7.0
param([ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.@:-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
if (-not $Target) {
    $connectionPath = Join-Path (Split-Path $PSScriptRoot -Parent) '.local/connection.json'
    $Target = (Get-Content -LiteralPath $connectionPath -Raw | ConvertFrom-Json).target
}
Write-Host 'Keep this terminal open, then visit http://127.0.0.1:8787. Close with Ctrl+C.'
& "$env:WINDIR/System32/OpenSSH/ssh.exe" -a -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -N -L '127.0.0.1:8787:127.0.0.1:8787' $Target
