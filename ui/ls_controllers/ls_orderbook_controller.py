import time

class OrderBookController:
    def __init__(self, api_client, view):
        self.api = api_client
        self.view = view
        self.current_symbol = None
        self._last_switch_ts = 0.0

    # ==================================================
    # Symbol Switch
    # ==================================================
    async def set_symbol(self, symbol: str):
        if symbol == self.current_symbol:
            return

        now = time.time()
        if now - self._last_switch_ts < 0.2:
            return
        self._last_switch_ts = now

        prev_symbol = self.current_symbol
        self.current_symbol = symbol

        self.view.clear()

        try:
            await self.api.set_orderbook_symbol(symbol)
        except Exception as e:
            self.current_symbol = prev_symbol
            self.view.clear()
            print("[OrderBook] set_symbol error:", e)

    # ==================================================
    # 🔥 PUSH EVENT (핵심)
    # ==================================================
    def on_orderbook_event(self, event: dict):
        symbol = event.get("symbol")
        if symbol != self.current_symbol:
            return

        bids = event.get("bids", [])
        asks = event.get("asks", [])

        if not bids or not asks:
            return

        # 🔥 중심가를 호가 기준으로 재계산
        center_price = (bids[0]["price"] + asks[0]["price"]) / 2

        self.view.update_depth(
            bids=bids,
            asks=asks,
            center_price=center_price,
        )


