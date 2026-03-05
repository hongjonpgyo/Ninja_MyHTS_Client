import time
from typing import Optional


class PriceController:
    def __init__(
        self,
        top_bar,
        order_panel=None,
        watchlist_controller=None,
    ):
        self.top_bar = top_bar
        self.order_panel = order_panel
        self.watchlist = watchlist_controller

        # 상태
        self.prev_price: Optional[float] = None
        self.current_symbol: Optional[str] = None
        self.last_tick_ts: Optional[float] = None

    # -------------------------------------------------
    # 심볼 변경
    # -------------------------------------------------
    def set_symbol(self, symbol: str):
        if symbol == self.current_symbol:
            return

        self.current_symbol = symbol
        self.prev_price = None

        if self.top_bar:
            self.top_bar.reset(symbol)

    # -------------------------------------------------
    def reset(self):
        self.prev_price = None

        if self.top_bar:
            self.top_bar.reset_display()

    # -------------------------------------------------
    # ✅ 단일 진입점
    # -------------------------------------------------
    def on_price(self, *args):
        self.last_tick_ts = time.time()

        parsed = self._parse_price_args(*args)
        if not parsed:
            return

        symbol, price, data = parsed

        # -------------------------
        # diff / pct 계산
        # -------------------------
        diff, pct = self._calc_diff(price)
        self.prev_price = price

        # -------------------------
        # Watchlist는 항상 갱신
        # -------------------------
        if self.watchlist and symbol:
            self.watchlist.update_price(
                symbol,
                price,
                data.get("change", 0.0),
                data.get("change_rate", 0.0),
            )

        # -------------------------
        # 선택 심볼 필터
        # -------------------------
        if self.current_symbol and symbol != self.current_symbol:
            return

        # -------------------------
        # TopBar
        # -------------------------
        # 🔥 LS가 준 값 그대로 사용
        diff = float(data.get("change", 0.0))
        pct = float(data.get("change_rate", 0.0))

        self._update_top_bar(symbol, price, diff, pct, data)

        # -------------------------
        # 주문 패널 (Market만)
        # -------------------------
        self._update_order_panel(price)

    # =================================================
    # 내부 유틸
    # =================================================
    def _parse_price_args(self, *args):
        """
        return (symbol, price, data) or None
        """
        if len(args) == 1 and isinstance(args[0], dict):
            data = args[0]
            symbol = data.get("symbol")
            raw_price = data.get("price") or data.get("last")

            if raw_price is None:
                return None

            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                return None

            return symbol, price, data

        if len(args) == 2:
            symbol = args[0]
            try:
                price = float(args[1])
            except (TypeError, ValueError):
                return None

            return symbol, price, {}

        return None

    # -------------------------------------------------
    def _calc_diff(self, price: float):
        if self.prev_price is None:
            return 0.0, 0.0

        diff = price - self.prev_price
        pct = (diff / self.prev_price) * 100 if self.prev_price else 0.0
        return diff, pct

    # -------------------------------------------------
    def _update_top_bar(self, symbol, price, diff, pct, data):
        if not self.top_bar:
            return

        self.top_bar.update_price(symbol, price, diff, pct)

        if not data:
            return

        self.top_bar.update_stats(
            high=data.get("high", price),
            low=data.get("low", price),
            volume=data.get("volume", 0),
            funding=data.get("funding", 0.0),
        )

        self.top_bar.update_status(
            live=True,
            latency_ms=data.get("latency", 0),
        )

        bid = data.get("bid")
        ask = data.get("ask")

        if bid and ask:
            self.top_bar.update_spread(bid, ask)

    # -------------------------------------------------
    def _update_order_panel(self, price: float):
        if not self.order_panel:
            return

        if self.order_panel.price_locked:
            return

        if self.order_panel.get_order_type() != "Market":
            return

        self.order_panel.set_price(price)

    # -------------------------------------------------
    def get_feed_status(self):
        if not self.last_tick_ts:
            return "OFF"

        gap = time.time() - self.last_tick_ts

        if gap < 2:
            return "LIVE"
        if gap < 5:
            return "DELAY"
        return "OFF"
