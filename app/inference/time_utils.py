# app/inference/time_utils.py

from datetime import datetime, timezone


def unix_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
