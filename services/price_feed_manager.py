# services/price_feed_manager.py
from PyQt6.QtCore import QObject, pyqtSignal

class PriceFeedManager(QObject):
    price_updated = pyqtSignal(str, float)

    def emit_price(self, symbol: str, price: float):
        self.price_updated.emit(symbol, price)
