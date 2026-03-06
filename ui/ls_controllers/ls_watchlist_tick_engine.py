from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer


class LSWatchListTickEngine(QObject):
    """
    WatchList 전용 tick batching 엔진

    - enqueue_tick()으로 들어온 tick을 symbol 기준 최신값으로 덮어씀
    - flush interval마다 controller.batch_update_prices() 호출
    - UI thread에서만 동작하도록 설계
    """

    def __init__(self, controller, interval_ms: int = 50, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval_ms = interval_ms

        self._buffer: dict[str, dict] = {}

        self._timer = QTimer(self)
        self._timer.setInterval(self.interval_ms)
        self._timer.timeout.connect(self.flush)

    def start(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()

    def clear(self):
        self._buffer.clear()

    def enqueue_tick(
        self,
        symbol: str,
        price: float | None,
        change: float | None,
        change_rate: float | None,
    ):
        if not symbol:
            return

        symbol = symbol.strip().upper()

        self._buffer[symbol] = {
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_rate": change_rate,
        }

    def flush(self):
        if not self._buffer:
            return

        updates = self._buffer
        self._buffer = {}

        self.controller.batch_update_prices(updates)