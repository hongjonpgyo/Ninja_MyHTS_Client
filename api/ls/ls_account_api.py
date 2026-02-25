# api/ls_account_api.py

class LSAccountApi:
    """
    LS Account API
    - 잔고
    - 포지션
    - 계좌 요약
    """

    def __init__(self, api_client):
        self.api = api_client

    # -------------------------
    # 잔고
    # -------------------------
    async def get_balance(self, account_id: str):
        # return await self.api.get(
        #     f"/ls/futures/accounts/{account_id}/balance"
        # )
        return await self.api.get(
            f"/ls/futures/accounts/{account_id}/balance"
        )

    # -------------------------
    # 포지션 전체
    # -------------------------
    async def get_positions(self, account_id: str):
        return await self.api.get(
            f"/ls/futures/accounts/{account_id}/positions"
        )

    # -------------------------
    # 단일 심볼 포지션
    # -------------------------
    async def get_position(self, account_id: str, symbol: str):
        return await self.api.get(
            f"/ls/futures/accounts/{account_id}/positions/{symbol}"
        )
