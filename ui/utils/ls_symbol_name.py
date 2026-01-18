# ui/utils/ls_symbol_name.py
import re

LS_SYMBOL_KR_MAP = {
    # China / H-Share
    "HSI": "항셍",
    "HCEI": "항셍중국",
    "HSCEI": "항셍중국",
    "CUSH": "위안",
    "CUS": "위안",
    "LHC": "구리",
    "MCA": "옥수수",

    # US
    "ES": "S&P",
    "NQ": "나스닥",
    "YM": "다우",
}

MONTH_RE = re.compile(r"^([A-Z]+)([FGHJKMNQUVXZ])(\d{2})$")


def symbol_to_kr(symbol: str) -> str:
    m = MONTH_RE.match(symbol)
    if not m:
        return symbol

    base, month, year = m.groups()

    kr_base = (
        LS_SYMBOL_KR_MAP.get(base[:4])
        or LS_SYMBOL_KR_MAP.get(base[:3])
        or base
    )

    return f"{kr_base}{month}{year}"


def display_symbol_name(symbol: str, max_len: int = 8) -> tuple[str, str]:
    """
    return (display_text, full_text)
    """
    full = symbol_to_kr(symbol)
    if len(full) <= max_len:
        return full, full
    return full[:max_len] + "…", full
