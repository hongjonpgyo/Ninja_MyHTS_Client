# services/dummy_ticker_engine.py
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import random


class DummyTickerEngine(QObject):
    tick = pyqtSignal(dict)

    def __init__(self, symbol="ETHUSDT"):
        super().__init__()
        self.symbol = symbol
        self.price = 2951.55
        self.high = self.price
        self.low = self.price
        self.volume = 12430
        self.funding = 0.01

        self.timer = QTimer()
        self.timer.timeout.connect(self._update)

    def start(self, interval=800):
        self.timer.start(interval)

    def _update(self):
        delta = random.uniform(-2.5, 2.5)
        self.price = round(self.price + delta, 2)

        self.high = max(self.high, self.price)
        self.low = min(self.low, self.price)
        self.volume += random.randint(20, 150)

        self.tick.emit({
            "symbol": self.symbol,
            "price": self.price,
            "change": delta,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "funding": self.funding,
        })
