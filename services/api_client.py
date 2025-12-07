# services/api_client.py
import aiohttp
import httpx
from config.settings import REST_URL


class APIClient:
    def __init__(self):
        self.base_url = REST_URL
        self.token = None
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)

    # 공통 헤더
    def _headers(self):
        if not self.token:
            return {"Content-Type": "application/json"}
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def set_token(self, token):
        self.token = token

    # ======================================================
    # GET
    # ======================================================
    async def get(self, path, params=None):
        res = await self._client.get(path, params=params, headers=self._headers())
        res.raise_for_status()
        return res.json()

    # ======================================================
    # POST
    # ======================================================
    async def post(self, path, json):
        res = await self._client.post(path, json=json, headers=self._headers())
        res.raise_for_status()
        return res.json()

    # ======================================================
    # LOGIN
    # ======================================================
    async def login(self, email, password):
        payload = {"email": email, "password": password}
        res = await self._client.post("/auth/login", json=payload)
        data = res.json()

        self.token = data.get("access_token")
        return data

    # ======================================================
    # POSITIONS
    # ======================================================
    async def get_positions(self, account_id: int):
        res = await self._client.get(
            f"/positions/{account_id}",
            headers=self._headers()
        )
        res.raise_for_status()
        return res.json()

    # ======================================================
    # ACCOUNT
    # ======================================================
    async def get_account(self, account_id: int):
        res = await self._client.get(
            f"/accounts/{account_id}",
            headers=self._headers()
        )
        res.raise_for_status()
        return res.json()

    # ======================================================
    # MARKET ORDER
    # ======================================================
    async def order_market(self, account_id, symbol, side, qty):
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        return await self.post("/orders/market", json=payload)

    # ======================================================
    # LIMIT ORDER
    # ======================================================
    async def order_limit(self, account_id, symbol, side, qty, price):
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price
        }
        return await self.post("/orders/limit", json=payload)

    async def get_executions(self, account_id: int):
        return await self.get(f"/executions/my/{account_id}")

    # async def get_open_orders(self, account_id):
    #     return await self.get(f"/orders/open/{account_id}")
    #
    # async def cancel_orders(self, order_ids):
    #     return await self.post("/orders/cancel_bulk", {"order_ids": order_ids})
