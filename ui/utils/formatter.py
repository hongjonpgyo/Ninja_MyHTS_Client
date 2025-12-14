def format_num(n):
    return f"{n:,.2f}"

def fmt_time(ts) -> str:
    if not ts:
        return ""  # None / "" 처리
    # ISO 문자열일 가능성이 큼: "2025-12-14T13:22:11" / "2025-12-14 13:22:11"
    try:
        s = str(ts).replace("Z", "").replace(" ", "T")
        from datetime import datetime
        dt = datetime.fromisoformat(s)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(ts)  # 파싱 실패 시 원본 표시

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

