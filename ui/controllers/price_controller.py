from PyQt6.QtGui import QColor
import time

class PriceController:
    def __init__(
        self,
        label_price,
        label_change,
        top_bar,
        order_panel=None,
        watchlist_controller=None,
    ):
        # 상단 표시용 (간단 버전 유지)
        self.label_price = label_price
        self.label_change = label_change

        # 확장 UI
        self.top_bar = top_bar
        self.order_panel = order_panel
        self.watchlist = watchlist_controller

        # 상태값
        self.prev_price: float | None = None
        self.current_symbol: str | None = None

        self.last_tick_ts = None

    # -------------------------------------------------
    # 심볼 변경 (Watchlist / Symbol ComboBox 등)
    # -------------------------------------------------
    def set_symbol(self, symbol: str):
        if symbol == self.current_symbol:
            return

        self.current_symbol = symbol
        self.prev_price = None

        # --- TopBar Reset ---
        if self.top_bar:
            self.top_bar.reset(symbol)

        # --- 상단 간단 라벨 ---
        # self.label_price.setText("--")
        # self.label_change.setText("+0.00")
        # self.label_change.setStyleSheet("color:#aaaaaa;")

        # --- 주문 패널 ---
        # if self.order_panel:
        #     self.order_panel.on_symbol_changed(symbol)
        #
        # # --- Watchlist는 그대로 (선택 강조만)
        # if self.watchlist:
        #     self.watchlist.set_selected(symbol)

    # -------------------------------------------------
    def reset(self):
        self.prev_price = None

        # self.label_price.setText("--")
        # self.label_change.setText("+0.00")
        # self.label_change.setStyleSheet("color:#aaaaaa;")

        if self.top_bar:
            self.top_bar.update_price(0.0, 0.0, 0.0)

    # -------------------------------------------------
    # ✅ 단일 진입점
    # -------------------------------------------------
    def on_price(self, *args):
        """
        지원 형태
        1) on_price(data: dict)
           {
             symbol, price/last,
             high, low, volume, funding, latency
           }

        2) on_price(symbol: str, price: float)
        """
        self.last_tick_ts = time.time()

        symbol = None
        price = None
        data = {}

        # -------------------------
        # 1) dict 형태
        # -------------------------
        if len(args) == 1 and isinstance(args[0], dict):
            data = args[0]
            symbol = data.get("symbol")
            raw_price = data.get("price") or data.get("last")

            if raw_price is None:
                return

            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                return

        # -------------------------
        # 2) (symbol, price)
        # -------------------------
        elif len(args) == 2:
            symbol = args[0]
            try:
                price = float(args[1])
            except (TypeError, ValueError):
                return

        else:
            return

        # -------------------------
        # Watchlist는 항상 갱신
        # -------------------------
        if self.watchlist and symbol:
            self.watchlist.update_price(symbol, price)

        # -------------------------
        # 선택 심볼이 있으면 필터
        # -------------------------
        if self.current_symbol and symbol != self.current_symbol:
            return

        # -------------------------
        # diff / pct 계산
        # -------------------------
        if self.prev_price is None:
            diff = 0.0
            pct = 0.0
        else:
            diff = price - self.prev_price
            pct = (diff / self.prev_price) * 100 if self.prev_price else 0.0

        self.prev_price = price

        # -------------------------
        # 상단 라벨 (간단)
        # -------------------------
        # self._update_simple_labels(price, diff, pct)

        # -------------------------
        # TopBar (확장 UI)
        # -------------------------
        if self.top_bar:
            self.top_bar.update_price(price, diff, pct)

            if data:
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

        # -------------------------
        # 주문 패널 (Market일 때만)
        # -------------------------
        if (
            self.order_panel
            and not self.order_panel.price_locked
            and self.order_panel.get_order_type() == "Market"
        ):
            self.order_panel.set_price(price)

    # -------------------------------------------------
    # 내부: 상단 간단 라벨
    # -------------------------------------------------
    def _update_simple_labels(self, price: float, diff: float, pct: float):
        self.label_price.setText(f"{price:,.2f}")

        sign = "+" if diff >= 0 else ""
        self.label_change.setText(f"{sign}{diff:.2f} ({sign}{pct:.2f}%)")

        if diff > 0:
            color = "#ff4d4d"
        elif diff < 0:
            color = "#4da6ff"
        else:
            color = "#aaaaaa"

        self.label_price.setStyleSheet(f"color:{color};")
        self.label_change.setStyleSheet(f"color:{color};")

    def get_feed_status(self):
        if self.last_tick_ts is None:
            return "OFF"

        gap = time.time() - self.last_tick_ts

        if gap < 2:
            return "LIVE"
        elif gap < 5:
            return "DELAY"
        else:
            return "OFF"
