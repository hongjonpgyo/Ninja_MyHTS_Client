# ui/widgets/order_panel.py
from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel.ui", self)

        # 버튼 연결은 MainWindow에서 처리
        # 여기서는 버튼 자체만 제공
        # 수량 단위 (원하면 1.0 으로 바꿔도 됨)
        self.qty_step = 0.01

        # 버튼 연결
        self.btnQtyPlus.clicked.connect(self.on_qty_plus)
        self.btnQtyMinus.clicked.connect(self.on_qty_minus)
        self.btnQtyHalf.clicked.connect(self.on_qty_half)
        self.btnQtyDouble.clicked.connect(self.on_qty_double)

    def get_qty(self) -> float:
        text = self.editQty.text().strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0
        
    def _set_qty(self, value: float):
        # 0 밑으로 내려가면 0으로 고정
        if value < 0:
            value = 0.0

        # 소수점 두 자리 정도로 표현
        self.editQty.setText(f"{value:.2f}".rstrip('0').rstrip('.'))

    def set_symbol(self, symbol: str):
        """심볼 변경 시 UI 업데이트 (필요 시 확장)"""
        self.labelSymbol.setText(symbol)


    # ------------------------
    #  버튼 동작 구현
    # ------------------------
    def on_qty_plus(self):
        cur = self.get_qty()
        new = cur + self.qty_step
        self._set_qty(new)

    def on_qty_minus(self):
        cur = self.get_qty()
        new = cur - self.qty_step
        self._set_qty(new)

    def on_qty_half(self):
        cur = self.get_qty()
        new = cur / 2.0
        self._set_qty(new)

    def on_qty_double(self):
        cur = self.get_qty()
        new = cur * 2.0
        self._set_qty(new)
