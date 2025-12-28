from datetime import datetime

def format_num(n):
    return f"{n:,.2f}"

from datetime import datetime

def fmt_time(ts) -> str:
    if not ts:
        return ""

    try:
        # 🔥 Unix timestamp (float / int)
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%H:%M:%S")

        # 문자열인 경우 (ISO)
        s = str(ts).replace("Z", "").replace(" ", "T")
        dt = datetime.fromisoformat(s)
        return dt.strftime("%H:%M:%S")

    except Exception:
        return ""


def fmt(value, digits=2):
    if value is None:
        return ""
    return f"{value:,.{digits}f}"


DISPLAY_FORMAT = {
    "BTCUSDT": {"price": 2, "qty": 3, "pnl": 2},
    "ETHUSDT": {"price": 2, "qty": 3, "pnl": 2},
    "SOLUSDT": {"price": 2, "qty": 2, "pnl": 2},
}

DEFAULT_FMT = {"price": 2, "qty": 2, "pnl": 2}

