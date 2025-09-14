<#
install_anchornote.ps1
PowerShell installer script for Anchor Note (Windows).
Run as Administrator.

What it does:
- Copies build artifacts into Program Files
- Creates Start Menu shortcut for the agent
- Installs the service using sc.exe
- Starts the service
- Registers a Scheduled Task to run the agent at logon (WakeToRun should be set in Task Scheduler UI if needed)
#>

param(
    [string]$SourceAgent = ".\dist\anchor_note_agent",
    [string]$SourceService = ".\dist\anchor_note_service",
    [string]$InstallDir = "C:\Program Files\AnchorNote",
    [string]$ServiceName = "AnchorNoteService",
    [string]$AgentExe = "anchor_note_agent.exe",
    [string]$ServiceExe = "anchor_note_service.exe"
)

function Test-IsAdministrator {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    if (-not $isAdmin) {
        Write-Error "Please run this script as Administrator."
        exit 1
    }
}

Test-IsAdministrator

# Normalize paths
$SourceAgent = (Resolve-Path $SourceAgent).ProviderPath
$SourceService = (Resolve-Path $SourceService).ProviderPath
$InstallDir = (Resolve-Path -LiteralPath $InstallDir -ErrorAction SilentlyContinue) -or $InstallDir

# Create install dir
Write-Host "Creating install directory: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Copy agent files
Write-Host "Copying agent files from $SourceAgent to $InstallDir"
Copy-Item -Path (Join-Path $SourceAgent '*') -Destination $InstallDir -Recurse -Force

# Copy service files
Write-Host "Copying service files from $SourceService to $InstallDir"
Copy-Item -Path (Join-Path $SourceService '*') -Destination $InstallDir -Recurse -Force

# Create Start Menu shortcut
$shortcutDir = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Anchor Note"
New-Item -ItemType Directory -Force -Path $shortcutDir | Out-Null
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path $shortcutDir "Anchor Note.lnk"))
$lnk.TargetPath = Join-Path $InstallDir $AgentExe
$lnk.WorkingDirectory = $InstallDir
$lnk.Save()
Write-Host "Start Menu shortcut created."

# Install Windows service
$serviceExePath = Join-Path $InstallDir $ServiceExe
Write-Host "Installing service $ServiceName -> $serviceExePath"

# If service exists, try to stop and delete it first
$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc) {
    Write-Host "Service exists; stopping and removing existing service."
    sc.exe stop $ServiceName 2>$null
    sc.exe delete $ServiceName 2>$null
    Start-Sleep -Seconds 1
}

# create service
$createCmd = "create $ServiceName binPath= `"$serviceExePath`" DisplayName= `"$ServiceName`" start= auto"
sc.exe $createCmd | Out-Null

# start service
Start-Sleep -Seconds 1
sc.exe start $ServiceName

Write-Host "Service installed and started (verify in Services.msc)."

# Register scheduled task to run agent at logon (interactive)
$taskName = "AnchorNoteAgent"
$action = New-ScheduledTaskAction -Execute (Join-Path $InstallDir $AgentExe)
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Remove existing task if present
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force

Write-Host "Scheduled Task registered to run the agent at logon."

Write-Host "Installation complete. Please verify the service, task, and Start Menu shortcut."
