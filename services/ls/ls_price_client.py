# services/ls_price_client.py
import requests

from config.ls_settings import LS_BASE_URL


def fetch_ls_quote(symbol: str):
    try:
        res = requests.get(
            f"{LS_BASE_URL}/ls/futures/quote/{symbol}",
            timeout=0.5
        )
        if res.status_code != 200:
            return None
        print(res)
        return res.json()
    except Exception:
        return None
