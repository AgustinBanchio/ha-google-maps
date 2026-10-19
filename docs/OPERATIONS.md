# Operations and access

The primary development checkout is D:/repos/ha-google-maps on Windows. The origin remote is the owner's fork; upstream is pnbruckner/ha-google-maps.

## 1Password-backed SSH from background T3

T3 Connect on the Windows workstation runs as a scheduled background task in Session 0. 1Password runs in the user's desktop session and rejected direct background SSH with a pipe authentication Access is denied error. A non-admin Interactive scheduled task successfully used normal 1Password authentication.

From PowerShell 7 in this repository:

```powershell
$target = (Get-Content .local/connection.json -Raw | ConvertFrom-Json).target
& ./tools/Invoke-DesktopSsh.ps1 -Target $target -RemoteCommand 'hostname; id'
```

The helper creates a uniquely named on-demand desktop task, captures command output locally, then removes the task. There is no recurring task, exported key, agent forwarding or replacement SSH agent. It requires a logged-in desktop and available 1Password; approve a normal 1Password request if prompted.

The private target is recorded in .local/connection.json on the owner's checkout. The helper is generic and has no embedded host/account.

Commands and results are stored under ignored .ssh-runs/. Never put secrets in a remote command or InputText. Keep original host-key checking. Do not widen remote authorization: the preparation phase allows read-only inspection only.

## Optional development on the Pi

A Pi checkout is not needed to import the Windows project into T3. The owner authorized an optional Pi source checkout if useful. Before creating it, confirm an unused checkout path and clone the fork there over HTTPS; do not copy cookie files or Windows operational reports. Working in a T3 instance on the Pi can avoid repeated SSH for development, but that agent has the same administrator trust implications.

Use the same Git branch and tracker for handoff, commit/push before switching hosts, and do not develop independently in two dirty checkouts. No Pi clone has been created by this preparation.

## Release and deployment

Do not run the original integration concurrently with the collector against the same Google session during validation. Session handling must have one writer.

Deployment requires the completed acceptance suite, explicit owner authorization, a pinned image and a documented rollback. Show the concrete proposed collector-only Compose changes. Do not restart the existing HA/OTBR/Matter stack or the Pi without explicit approval for that action.

The planned credential import happens in the local authenticated collector UI, never in chat. Collector code is not implemented yet.
