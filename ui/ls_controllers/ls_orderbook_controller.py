import time


class OrderBookController:
    def __init__(self, api_client, view):
        self.api = api_client
        self.view = view
        self.current_symbol = None
        self._last_switch_ts = 0.0

    async def set_symbol(self, symbol: str):
        if symbol == self.current_symbol:
            return

        # ⏱ 연타 방지 (200ms)
        now = time.time()
        if now - self._last_switch_ts < 0.2:
            return
        self._last_switch_ts = now

        prev_symbol = self.current_symbol
        self.current_symbol = symbol

        # UI 초기화
        self.view.clear()

        try:
            # 🔥 백엔드에 심볼 변경 요청
            await self.api.set_orderbook_symbol(symbol)
        except Exception as e:
            # ❌ 실패 시 롤백
            self.current_symbol = prev_symbol
            self.view.clear()
            # self.view.show_error("호가 구독 실패")
            print("[OrderBook] set_symbol error:", e)
