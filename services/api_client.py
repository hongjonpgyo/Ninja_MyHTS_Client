# services/api_client.py
import aiohttp
import httpx
from config.settings import REST_URL

# BASE_URL = "http://127.0.0.1:8000"



class APIClient:
    def __init__(self):
        self.base_url = REST_URL
        # 한 번만 생성해서 재사용
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)

    async def get(self, path: str, params: dict | None = None):
        res = await self._client.get(path, params=params)
        res.raise_for_status()
        return res.json()

    async def post(self, path: str, json: dict):
        res = await self._client.post(path, json=json)
        res.raise_for_status()
        return res.json()

    async def place_market(self, account_id: int, symbol: str, side: str, qty: float):
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        return self.post(f"{REST_URL}/orders/market", json=payload)

    async def order_market(self, account_id : int, symbol, side, qty):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/orders/market",
                        json={"account_id" : account_id, "symbol": symbol, "side": side, "qty": qty}
                ) as res:
                    return await res.json()
        except Exception as e:
            print("[API ERROR]", e)
            return {"ok": False, "error": str(e)}

    def get_positions(self, account_id: int):
        return self.get(f"{REST_URL}/positions/{account_id}").json()

    def get_executions(self, account_id: int):
        return self.get(f"{REST_URL}/executions/{account_id}").json()

    def get_account(self, account_id: int):
        return self.get(f"{REST_URL}/accounts/{account_id}").json()
