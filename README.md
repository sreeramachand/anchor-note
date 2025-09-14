# Sticky Remind

Persistent reminder & checklist tool that syncs with calendars (ICS, CalDAV, Google Calendar) and presents persistent repeating alerts for critical tasks (e.g., medication).

This repo contains:
- A shared Python library (`sticky_remind/`) with calendar sync, scheduler, alerting and UI entry points.
- Windows packaging artifacts (PyInstaller specs, Inno Setup, PowerShell installer).
- Android/Kivy packaging (Buildozer) and Google Play metadata.

## Quickstart (dev)

1. create venv & install
```bash
python -m venv .venv
source .venv/bin/activate       # or .venv\Scripts\activate on Windows
pip install -U pip
pip install -r requirements.txt
pip install -e .
