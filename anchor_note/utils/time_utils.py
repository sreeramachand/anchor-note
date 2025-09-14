"""Time helper utilities"""

from datetime import datetime, timezone

def utc_now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())
