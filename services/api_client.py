# services/api_client.py
import httpx
import requests

from config.settings import LS_BASE_URL


class APIClient:
    def __init__(self):
        self.base_url = LS_BASE_URL
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

    def clear_token(self):
        self.token = None

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
        res = await self._client.post("/ls/futures/login", json=payload)
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

    # ✅ 아이디 찾기
    def find_id(self, email: str) -> dict:
        url = f"{self.base_url}/auth/find-id"
        payload = {"email": email}

        res = requests.post(url, json=payload, headers=self._headers(), timeout=5)

        if res.status_code != 200:
            raise Exception("아이디 찾기 실패")

        return res.json()

    # -------------------------
    # PASSWORD RESET
    # -------------------------
    async def reset_password(self, token: str, new_password: str):
        data = await self.post(
            "/auth/password/reset/confirm",
            {
                "token": token,
                "new_password": new_password
            }
        )
        if not data.get("ok"):
            raise Exception(data.get("message", "비밀번호 변경 실패"))
        return data

    async def request_password_reset(self, email: str) -> dict:
        # 로그인 없이 호출되는 공개 API
        return await self.post("/auth/password/reset/request", json={"email": email})

    async def confirm_password_reset(self, token: str, new_password: str) -> dict:
        # 로그인 없이 호출되는 공개 API
        return await self.post(
            "/auth/password/reset/confirm",
            json={"token": token, "new_password": new_password},
        )

    async def place_protection_order(self, payload: dict):
        return await self.post(
            "/ls/futures/protections",
            json=payload,
        )

    async def get_protections(self, account_id: int, symbol: str | None = None):
        params = {"account_id": account_id}
        if symbol:
            params["symbol"] = symbol

        return await self.get(
            "/ls/futures/protections",
            params=params,
        )

    # -------------------------
    # 🔥 OrderBook 심볼 변경
    # -------------------------
    async def set_orderbook_symbol(self, symbol: str):
        payload = {"symbol": symbol}
        return await self.post(
            "/ls/futures/orderbook/symbol",
            json=payload,
        )