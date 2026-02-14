from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


def to_kst(ts):
    if not ts:
        return None

    try:
        if isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.fromisoformat(ts)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        return dt.astimezone(KST)

    except Exception:
        return None


def to_kst_str(ts, fmt="%Y-%m-%d %H:%M:%S"):
    dt = to_kst(ts)
    return dt.strftime(fmt) if dt else "--"
