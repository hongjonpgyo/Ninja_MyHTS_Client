# services/api_client.py
import aiohttp
import httpx
from config.settings import REST_URL


class APIClient:
    def __init__(self):
        self.base_url = REST_URL
        # 한 번만 생성해서 재사용
        self.token = None
        self.account_id = None
        self.user_id = None
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)

    # ----------------------------
    # 로그인
    # ----------------------------
    async def login(self, email: str, password: str) -> dict:
        try:
            res = await self._client.post(
                "/auth/login",
                json={           # ★★★ 반드시 json 이용 ★★★
                    "email": email,
                    "password": password,
                },
            )
            res.raise_for_status()
            data = res.json()

            # 토큰/계좌 정보 저장
            self.access_token = data["access_token"]
            self.user_id = data["user_id"]
            self.account_id = data["account_id"]

            return data
        except httpx.HTTPStatusError as e:
            # 서버에서 400/401 등 에러 내려보낼 때
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise Exception(f"HTTP {e.response.status_code}: {detail}")
        except Exception as e:
            raise Exception(f"API 로그인 오류: {e}")

    # 공통 Header
    def _headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}


    async def get(self, path: str, params: dict | None = None):
        res = await self._client.get(path, params=params)
        res.raise_for_status()
        return res.json()

    async def post(self, path: str, json: dict):
        import aiohttp

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"   # 백엔드에서 Bearer 기대한다면

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url + path, json=json, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def place_market(self, account_id: int, symbol: str, side: str, qty: float):
        payload = {
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "qty": qty
        }
        return self.post(f"{REST_URL}/orders/market", json=payload)

    async def order_market(self, account_id : int, symbol, side, qty):
        if not account_id:
            raise Exception("로그인이 필요합니다(account_id 없음).")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/orders/market",
                        json={"account_id" : account_id, "symbol": symbol, "side": side, "qty": qty}, headers=self._headers()
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

    async def login(self, email, password):
        try:
            payload = {
                "email": email,
                "password": password
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/auth/login",
                        json=payload,
                ) as res:
                    return await res.json()
        except Exception as e:
            print("[API ERROR]", e)
            return {"ok": False, "error": str(e)}

    def set_token(self, token):
        self.token = token
