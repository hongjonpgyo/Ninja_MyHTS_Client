# ui/controllers/symbol_controller.py
class SymbolController:
    def __init__(self, combo, on_change):
        self.combo = combo
        self.on_change = on_change

        self.symbols = []

        self.combo.currentTextChanged.connect(self._on_changed)

    def load_default(self):
        # 🔥 여기서 심볼 목록 관리
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

        self.combo.clear()
        self.combo.addItems(self.symbols)

        if self.symbols:
            self.combo.setCurrentIndex(0)

    def _on_changed(self, symbol: str):
        if symbol:
            self.on_change(symbol)
