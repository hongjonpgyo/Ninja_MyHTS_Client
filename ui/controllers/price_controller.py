from PyQt6.QtGui import QColor

class PriceController:
    def __init__(self, label_price, label_change, order_panel, watchlist_controller):
        self.label_price = label_price
        self.label_change = label_change
        self.order_panel = order_panel
        self.watchlist = watchlist_controller

        self.prev_price = None

    def reset(self):
        self.prev_price = None
        self.label_price.setText("--")
        self.label_change.setText("+0.00")
        self.label_change.setStyleSheet("color:#aaaaaa;")

    def on_price(self, data: dict):
        raw_price = data.get("last") or data.get("price")
        if raw_price is None:
            return

        try:
            price = float(raw_price)
        except (TypeError, ValueError):
            return

        symbol = data.get("symbol")

        # 현재가 표시
        self.label_price.setText(f"{price:,.2f}")

        # 주문패널 가격 (Market일 때만 자동)
        if (
            not self.order_panel.price_locked
            and self.order_panel.get_order_type() == "Market"
        ):
            self.order_panel.set_price(price)

        # Watchlist
        if symbol:
            self.watchlist.update_price(symbol, price)

        self._update_change(price)

    def _update_change(self, price: float):
        if self.prev_price is None:
            self.prev_price = price
            self.label_change.setText("+0.00")
            self.label_change.setStyleSheet("color:#aaaaaa;")
            return

        diff = price - self.prev_price

        if diff > 0:
            self.label_change.setStyleSheet("color:#ff4d4d;")
        elif diff < 0:
            self.label_change.setStyleSheet("color:#4da6ff;")
        else:
            self.label_change.setStyleSheet("color:#aaaaaa;")

        self.label_change.setText(f"{diff:+.2f}")
        self.prev_price = price
