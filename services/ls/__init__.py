# services/ls_price_client.py
import requests



def fetch_ls_quote(symbol: str):
    try:
        res = requests.get(
            f"{LS_BASE_URL}/ls/futures/quote/{symbol}",
            timeout=0.5
        )
        if res.status_code != 200:
            return None
        return res.json()
    except Exception:
        return None
