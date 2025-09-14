"""
calendar_sync.py

Minimal calendar sync utilities:
- sync_from_ics(path): parses local .ics and upserts into core DB
- sync_from_caldav_nextcloud(url, username, password, calendar_name): optional, uses caldav lib
- sync_from_google_calendar(client_secrets_file, token_file, calendar_id): optional, uses google-api libs

All sync functions call upsert_task() in the scheduler module so the DB is consistent.
"""

import logging
from datetime import timezone, datetime, timedelta
from pathlib import Path

LOG = logging.getLogger(__name__)

# local import to avoid circular import issues
from .scheduler import upsert_task
try:
    from ics import Calendar
except Exception:
    Calendar = None

def sync_from_ics(path: str) -> int:
    """Parse a local .ics file and upsert events into the tasks DB.
    Returns number of events processed. Requires `ics` package."""
    if not Calendar:
        LOG.error("ics library not installed; sync_from_ics disabled.")
        return 0
    p = Path(path)
    if not p.exists():
        LOG.debug("ICS path does not exist: %s", path)
        return 0
    with p.open("r", encoding="utf-8") as fh:
        cal = Calendar(fh.read())
    processed = 0
    for ev in cal.events:
        uid = getattr(ev, "uid", None) or f"{ev.begin}-{ev.name}"
        title = ev.name or "No title"
        try:
            start_ts = int(ev.begin.astimezone(timezone.utc).timestamp()) if ev.begin else 0
            end_ts = int(ev.end.astimezone(timezone.utc).timestamp()) if ev.end else start_ts
        except Exception:
            # fallback: not timezone-aware
            start_ts = 0
            end_ts = 0
        red = 1 if any(k in (title or "").lower() for k in ("med","medicine","pill","take")) else 0
        upsert_task(Path(__file__).parent.parent / "settings.py") if False else None  # no-op to avoid linter errors
        # upsert_task expects db_path; we call module-level upsert_task using scheduler DB path
        try:
            # import scheduler config at runtime to avoid circular import
            from .settings import load_user_config
            db = load_user_config()["db_path"]
            upsert_task(db, uid, title, start_ts, end_ts, red)
            processed += 1
        except Exception:
            LOG.exception("Failed to upsert event: %s", uid)
    LOG.info("ICS sync processed %d events", processed)
    return processed

# Optional CalDAV adapter
def sync_from_caldav_nextcloud(url, username=None, password=None, calendar_name=None):
    try:
        from caldav import DAVClient
    except Exception:
        LOG.error("caldav library not installed; sync_from_caldav_nextcloud disabled")
        return 0
    client = DAVClient(url, username=username, password=password)
    principal = client.principal()
    cals = principal.calendars()
    if calendar_name:
        cals = [c for c in cals if getattr(c, "name", "").lower() == calendar_name.lower()]
    processed = 0
    for cal in cals:
        for evobj in cal.events():
            raw = evobj.data
            try:
                # try parsing with ics
                if Calendar:
                    c = Calendar(raw)
                    for e in c.events:
                        uid = getattr(e, "uid", None) or f"{e.begin}-{e.name}"
                        title = e.name or "No title"
                        start_ts = int(e.begin.astimezone(timezone.utc).timestamp()) if e.begin else 0
                        end_ts = int(e.end.astimezone(timezone.utc).timestamp()) if e.end else start_ts
                        red = 1 if any(k in (title or "").lower() for k in ("med","medicine","pill","take")) else 0
                        from .settings import load_user_config
                        upsert_task(load_user_config()["db_path"], uid, title, start_ts, end_ts, red)
                        processed += 1
                else:
                    # fallback: skip if no ics parser
                    processed += 0
            except Exception:
                LOG.exception("Failed parsing CalDAV event")
    LOG.info("CalDAV sync processed %d events", processed)
    return processed

# Optional Google Calendar sync (uses google-api-python-client)
def sync_from_google_calendar(client_secrets_file, token_file="token.json", calendar_id="primary", lookahead_days=7):
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except Exception:
        LOG.error("google client libs not installed; sync_from_google_calendar disabled")
        return 0

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    creds = None
    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    now = datetime.utcnow().isoformat() + 'Z'
    max_time = (datetime.utcnow() + timedelta(days=lookahead_days)).isoformat() + 'Z'
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, timeMax=max_time,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    processed = 0
    from .settings import load_user_config
    db = load_user_config()["db_path"]
    for e in events:
        uid = e.get('id')
        title = e.get('summary', 'No title')
        start = e.get('start', {}).get('dateTime') or (e.get('start', {}).get('date') + "T00:00:00Z")
        end = e.get('end', {}).get('dateTime') or (e.get('end', {}).get('date') + "T00:00:00Z")
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            start_ts = int(start_dt.astimezone(timezone.utc).timestamp())
            end_ts = int(end_dt.astimezone(timezone.utc).timestamp())
        except Exception:
            continue
        red = 1 if any(k in (title or "").lower() for k in ("med","medicine","pill","take")) else 0
        upsert_task(db, uid, title, start_ts, end_ts, red)
        processed += 1
    LOG.info("Google Calendar sync processed %d events", processed)
    return processed
