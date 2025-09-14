# Windows packaging & installation (Sticky Remind)

This folder contains the packaging and installer artifacts for Windows:

- `pyinstaller-agent.spec`        - PyInstaller spec to build GUI agent (user session app)
- `pyinstaller-service.spec`      - PyInstaller spec to build Windows service exe
- `StickyRemindInstaller.iss`     - Inno Setup script to build an installer
- `install_stickyremind.ps1`      - Admin PowerShell installer script

## Prerequisites (build machine)

- Python 3.9+ (same as project)
- virtualenv recommended
- PyInstaller
- pygame (for audio)
- plyer (for notifications)
- pywin32 (for service code) — install on Windows build agent only
- Inno Setup (for producing installer .exe) — optional

Install build deps (example):
```powershell
python -m pip install --upgrade pip
pip install pyinstaller pygame plyer pywin32
