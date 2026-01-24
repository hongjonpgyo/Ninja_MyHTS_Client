# api/order_api.py

class OrderApi:
    """
    Order API (Async, Thin Wrapper)
    """

    def __init__(self, api_client):
        self.api = api_client  # ✅ 공통 Async API Client

    # -------------------------------
    # 미체결 주문 조회
    # -------------------------------
    async def get_open_orders(self, account_id: int):
        return await self.api.get(
            f"/orders/open/{account_id}"
        )

    # -------------------------------
    # 체결 내역 조회 (REST)
    # -------------------------------
    async def get_executions(self, account_id: int):
        return await self.api.get(
            f"/executions/{account_id}"
        )

    # -------------------------------
    # 주문 취소 (복수)
    # -------------------------------
    async def cancel_orders(self, order_ids: list[int]):
        return await self.api.post(
            "/orders/cancel_orders",
            json={"order_ids": order_ids}
        )

    # -------------------------------
    # 주문 생성 (필요 시)
    # -------------------------------
    async def create_order(self, payload: dict):
        return await self.api.post(
            "/orders",
            json=payload
        )