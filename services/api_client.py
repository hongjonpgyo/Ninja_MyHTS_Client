# services/api_client.py
import httpx
from config.settings import REST_URL

# BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    def __init__(self):
        self.client = httpx.Client()

    def place_market(self, account_id: int, symbol: str, side: str, qty: float):
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        return self.client.post(f"{REST_URL}/orders/market", json=payload).json()

    def get_positions(self, account_id: int):
        return self.client.get(f"{REST_URL}/positions/{account_id}").json()

    def get_executions(self, account_id: int):
        return self.client.get(f"{REST_URL}/executions/{account_id}").json()

    def get_account(self, account_id: int):
        return self.client.get(f"{REST_URL}/accounts/{account_id}").json()
