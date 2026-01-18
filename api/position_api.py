import requests
from config.settings import LS_BASE_URL

class PositionApi:
    def __init__(self, api_client):
        self.api = api_client   # async api client

    async def get_positions(self, account_id: int):
        return await self.api.get(f"/positions/{account_id}")

    async def get_position(self, account_id: int, symbol: str):
        rows = await self.get_positions(account_id)
        return next((p for p in rows if p.get("symbol") == symbol), None)

    def get_my_positions(self, account_id: int):
        r = requests.get(f"{LS_BASE_URL}/positions/my?account_id={account_id}")
        return r.json()

    def close_symbol(self, account_id: int, symbol: str):
        r = requests.post(
            f"{LS_BASE_URL}/positions/close_symbol",
            json={
                "account_id": account_id,
                "symbol": symbol
            }
        )
        r.raise_for_status()
        return r.json()

    def close_all(self, account_id: int):
        r = requests.post(
            f"{LS_BASE_URL}/positions/close_all",
            json={"account_id": account_id}
        )
        r.raise_for_status()
        return r.json()


    def close(self, position_id: int):
        r = requests.post(f"{LS_BASE_URL}/positions/close", json={"position_id": position_id})
        return r.json()
