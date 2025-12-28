# services/dummy_price_engine.py
import random
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class DummyPriceEngine(QObject):
    price_updated = pyqtSignal(dict)
    trade_generated = pyqtSignal(dict)

    def __init__(self, symbol="ETHUSDT", start_price=2950.0):
        super().__init__()
        self.symbol = symbol
        self.price = start_price
        self.volume = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

    def start(self, interval=1000):
        self.timer.start(interval)

    def _tick(self):
        # 가격 랜덤 변동
        delta = random.uniform(-1.5, 1.5)
        self.price = max(1, self.price + delta)

        vol = random.uniform(0.1, 3.0)
        self.volume += vol

        self.price_updated.emit({
            "symbol": self.symbol,
            "price": round(self.price, 2),
            "volume": round(vol, 2)
        })

        # 체결 더미
        if random.random() > 0.6:
            self.trade_generated.emit({
                "symbol": self.symbol,
                "price": round(self.price, 2),
                "qty": round(random.uniform(0.1, 2), 2),
                "side": "BUY" if delta > 0 else "SELL"
            })
