from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer


class LSOrderBookTickEngine(QObject):
    """
    OrderBook batching engine

    - tick을 symbol 기준 마지막 값만 유지
    - 일정 주기로 UI update
    """

    def __init__(self, controller, interval_ms: int = 40, parent=None):
        super().__init__(parent)

        self.controller = controller
        self.interval_ms = interval_ms

        self._buffer: dict[str, float] = {}

        self._timer = QTimer(self)
        self._timer.setInterval(self.interval_ms)
        self._timer.timeout.connect(self.flush)

    # -----------------------------
    # lifecycle
    # -----------------------------

    def start(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()

    def clear(self):
        self._buffer.clear()

    # -----------------------------
    # enqueue
    # -----------------------------

    def enqueue_tick(self, symbol: str, price: float):

        if not symbol:
            return

        symbol = symbol.strip().upper()

        # 🔥 symbol 기준 마지막 값만 유지
        self._buffer[symbol] = price

    # -----------------------------
    # flush
    # -----------------------------

    def flush(self):

        if not self._buffer:
            return

        updates = self._buffer
        self._buffer = {}

        current_symbol = self.controller.current_symbol

        if current_symbol not in updates:
            return

        price = updates[current_symbol]

        self.controller.view.update_ls_price(price)