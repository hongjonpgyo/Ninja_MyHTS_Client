from datetime import datetime

UP_COLOR = "#ea3943"      # 상승
DOWN_COLOR = "#2979ff"    # 하락
FLAT_COLOR = "#cccccc"


# -------------------------
# 기본 숫자 포맷
# -------------------------
def format_num(n):
    if n is None:
        return ""
    return f"{n:,.2f}"


# -------------------------
# 시간 포맷
# -------------------------
def fmt_time(ts) -> str:
    if not ts:
        return ""

    try:
        # Unix timestamp
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%H:%M:%S")

        # ISO 문자열
        s = str(ts).replace("Z", "").replace(" ", "T")
        dt = datetime.fromisoformat(s)
        return dt.strftime("%H:%M:%S")

    except Exception:
        return ""


# -------------------------
# 🔥 포맷 정의
# -------------------------
DISPLAY_FORMAT = {
    "money": 2,
    "rate": 2,
    "price": 2,
    "qty": 2,
    "pnl": 2,

    # 종목별 override
    "BTCUSDT": {"price": 2, "qty": 3, "pnl": 2},
    "ETHUSDT": {"price": 2, "qty": 3, "pnl": 2},
    "SOLUSDT": {"price": 2, "qty": 2, "pnl": 2},
}

DEFAULT_FMT = {"price": 2, "qty": 2, "pnl": 2}


# -------------------------
# 🔥 핵심 fmt
# -------------------------
def fmt(value, fmt_type="price", symbol: str | None = None):
    if value is None:
        return ""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return ""

    # 종목별 포맷 우선
    if symbol and symbol in DISPLAY_FORMAT:
        digits = DISPLAY_FORMAT[symbol].get(fmt_type, DEFAULT_FMT.get(fmt_type, 2))
    else:
        digits = DISPLAY_FORMAT.get(fmt_type, 2)

    return f"{value:,.{digits}f}"

def fmt_money(v):
    return "" if v is None else f"{v:,.0f}"

def fmt_money_2(v):
    return "" if v is None else f"{v:,.2f}"

def fmt_rate(v):
    return "" if v is None else f"{v:.2f}"

def fmt_pnl(v):
    return "" if v is None else f"{v:,.0f}"

def fmt_fx(rate: float | None, currency: str) -> str:
    if rate is None:
        return "-"

    # 소수점 처리: 원화 기준이므로 기본은 정수
    value = int(round(rate))

    return f"{value:,}원({currency})"

def format_date(date_str: str | None) -> str:
    if not date_str or len(date_str) != 8:
        return "-"
    return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")

def get_price_color(value: float, prev: float | None):
    if prev is None:
        return FLAT_COLOR
    if value > prev:
        return UP_COLOR
    elif value < prev:
        return DOWN_COLOR
    else:
        return FLAT_COLOR




