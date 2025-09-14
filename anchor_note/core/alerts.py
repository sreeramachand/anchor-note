"""
alerts.py

Notification + repeating sound control.

- notify_and_alert(task_id, title, red_flag, config)
    -> shows desktop notification and starts repeating audio alert (if red_flag)
- stop_alert_for_task(task_id) -> stops repeating alert
"""

import threading
import logging
from plyer import notification
from ..utils.audio import RepeatingAlert
from .settings import load_user_config

LOG = logging.getLogger(__name__)

# keep registry of active alerts
_ACTIVE: dict[int, RepeatingAlert] = {}
_LOCK = threading.Lock()

def notify_and_alert(task_id: int, title: str, red_flag: int, config: dict | None = None):
    cfg = (config or load_user_config()).copy()
    # show desktop notification (non-blocking)
    try:
        notification.notify(title=f"Due: {title}", message="Open checklist to mark done.", timeout=10)
    except Exception:
        LOG.exception("desktop notification failed")

    if red_flag:
        # start repeating sound alert
        sound_file = cfg.get("sound_file")
        burst = int(cfg.get("red_alert_burst_seconds", 30))
        interval = int(cfg.get("red_alert_repeat_seconds", 120))
        try:
            ra = RepeatingAlert(sound_file=sound_file, burst_seconds=burst, repeat_interval_seconds=interval)
            with _LOCK:
                _ACTIVE[int(task_id)] = ra
            ra.start()
        except Exception:
            LOG.exception("failed starting repeating alert for task %s", task_id)

def stop_alert_for_task(task_id: int):
    with _LOCK:
        ra = _ACTIVE.pop(int(task_id), None)
    if ra:
        try:
            ra.stop()
        except Exception:
            LOG.exception("failed stopping alert %s", task_id)
