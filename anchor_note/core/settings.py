"""Default configuration and user-overrides"""

from pathlib import Path
import json

HOME = Path.home()
DEFAULT_CONFIG = {
    "db_path": str(HOME / ".anchor_note" / "tasks.db"),
    "ics_path": str(HOME / "calendar.ics"),
    "check_interval_seconds": 60,        # poll every 60s
    "checklist_interval_hours": 6,
    "red_alert_burst_seconds": 30,
    "red_alert_repeat_seconds": 120,
    "sound_file": str(Path(__file__).parent.parent / "assets" / "alert.wav"),
    "socket_host": "127.0.0.1",
    "socket_port": 8765,
}

def load_user_config() -> dict:
    cfgfile = HOME / ".anchor_note" / "config.json"
    cfg = DEFAULT_CONFIG.copy()
    if cfgfile.exists():
        try:
            with open(cfgfile, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            cfg.update(data)
        except Exception:
            pass
    return cfg
