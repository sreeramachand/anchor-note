"""
scheduler.py

Simple scheduler that:
- keeps a local SQLite tasks DB (for pending/due tasks)
- syncs calendar sources via calendar_sync
- polls for due tasks and triggers alerts via alerts.notify_and_alert
- exposes a lightweight Scheduler class with start/stop
"""

from datetime import datetime, timezone
import sqlite3
from pathlib import Path
import threading
import time
import logging

from .settings import load_user_config
from .calendar_sync import sync_from_ics
from .alerts import notify_and_alert, stop_alert_for_task

LOG = logging.getLogger(__name__)

# DB helper functions (kept here so core package is self-contained)
def _ensure_db(db_path: str):
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            uid TEXT UNIQUE,
            title TEXT,
            start_ts INTEGER,
            end_ts INTEGER,
            status TEXT DEFAULT 'pending',
            red_alert INTEGER DEFAULT 0
        )
    """)
    con.commit()
    con.close()

def upsert_task(db_path: str, uid: str, title: str, start_ts: int, end_ts: int, red_alert: int = 0):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO tasks(uid,title,start_ts,end_ts,red_alert)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(uid) DO UPDATE SET
            title=excluded.title,
            start_ts=excluded.start_ts,
            end_ts=excluded.end_ts,
            red_alert=excluded.red_alert
    """, (uid, title, int(start_ts), int(end_ts), int(red_alert)))
    con.commit()
    con.close()

def get_pending_tasks(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id, uid, title, start_ts, end_ts, status, red_alert FROM tasks WHERE status!='done'")
    rows = cur.fetchall()
    con.close()
    return rows

def mark_done(db_path: str, task_id: int):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("UPDATE tasks SET status='done' WHERE id=?", (int(task_id),))
    con.commit()
    con.close()

# Scheduler class
class Scheduler:
    def __init__(self, config: dict | None = None):
        self.config = (config or load_user_config()).copy()
        self.db_path = self.config["db_path"]
        _ensure_db(self.db_path)
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._active_alerts = {}  # task_id -> True (used to avoid duplicate alert starts)

    def _sync_calendars(self):
        """
        Sync calendars into DB by reading .ics (simple fallback).
        For more advanced CalDAV/Google sync, call calendar_sync functions externally.
        """
        ics_path = self.config.get("ics_path")
        if ics_path:
            try:
                # sync_from_ics should call upsert (we import its implementation)
                sync_from_ics(ics_path)  # calendar_sync module is expected to upsert into same DB
            except Exception:
                LOG.exception("calendar sync failed")

    def _poll_loop(self):
        check_interval = int(self.config.get("check_interval_seconds", 60))
        while not self._stop.is_set():
            try:
                # optionally sync (every loop is simple; you can make sync less frequent)
                self._sync_calendars()

                now_ts = int(datetime.now(timezone.utc).timestamp())
                rows = get_pending_tasks(self.db_path)
                for row in rows:
                    task_id, uid, title, start_ts, end_ts, status, red_alert = row
                    # due if end_ts <= now (or if event time passed)
                    if end_ts and end_ts <= now_ts and status != "done":
                        # start persistent alert if not already active
                        if task_id not in self._active_alerts:
                            self._active_alerts[task_id] = True
                            notify_and_alert(task_id, title, red_alert, config=self.config)
                # small sleep
            except Exception:
                LOG.exception("scheduler loop error")
            for _ in range(max(1, check_interval)):
                if self._stop.is_set():
                    break
                time.sleep(1)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        LOG.info("Scheduler started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        # stop active alerts
        for tid in list(self._active_alerts.keys()):
            try:
                stop_alert_for_task(tid)
            except Exception:
                LOG.exception("failed stopping alert for task %s", tid)
        LOG.info("Scheduler stopped")

# convenience
def init_db():
    _ensure_db(load_user_config()["db_path"])
