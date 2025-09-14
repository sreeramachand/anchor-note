"""
checklist.py

Thin layer providing checklist operations backed by the scheduler's SQLite DB.
This allows UI layers (gui_agent, kivy_app) to read pending tasks and mark them done.
"""

from .settings import load_user_config
from .scheduler import get_pending_tasks, mark_done as _mark_done
from datetime import datetime, timezone

def list_pending_tasks():
    cfg = load_user_config()
    rows = get_pending_tasks(cfg["db_path"])
    out = []
    for r in rows:
        task_id, uid, title, start_ts, end_ts, status, red_alert = r
        start = datetime.fromtimestamp(start_ts, tz=timezone.utc).astimezone() if start_ts else None
        end = datetime.fromtimestamp(end_ts, tz=timezone.utc).astimezone() if end_ts else None
        out.append({
            "id": int(task_id),
            "uid": uid,
            "title": title,
            "start": start,
            "end": end,
            "status": status,
            "red": bool(red_alert),
        })
    return out

def mark_task_done(task_id: int):
    cfg = load_user_config()
    _mark_done(cfg["db_path"], int(task_id))
