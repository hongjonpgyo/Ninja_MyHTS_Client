from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel.ui", self)

        # 수량 단위
        self.qty_step = 0.01

        # 주문타입 콤보박스 변경 이벤트
        self.comboType.currentTextChanged.connect(self.on_type_changed)

        # 버튼 연결
        self.btnQtyPlus.clicked.connect(self.on_qty_plus)
        self.btnQtyMinus.clicked.connect(self.on_qty_minus)
        self.btnQtyHalf.clicked.connect(self.on_qty_half)
        self.btnQtyDouble.clicked.connect(self.on_qty_double)

    # -----------------------------
    #   Market / Limit 변경 처리
    # -----------------------------
    def on_type_changed(self, text):
        if text == "Market":
            self.editOrderPrice.setEnabled(False)
            self.editOrderPrice.setPlaceholderText("Market Price")
        else:
            self.editOrderPrice.setEnabled(True)
            self.editOrderPrice.setPlaceholderText("Limit Price 입력")

    def get_order_type(self) -> str:
        return self.comboType.currentText()

    def get_limit_price(self) -> float | None:
        if self.get_order_type() != "Limit":
            return None

        text = self.editOrderPrice.text().replace(",", "").strip()

        if not text:
            return None

        try:
            return float(text)
        except:
            return None

    # -----------------------------
    #   수량 처리
    # -----------------------------
    def get_qty(self) -> float:
        try:
            return float(self.editQty.text())
        except:
            return 0.0

    def _set_qty(self, value: float):
        if value < 0:
            value = 0
        self.editQty.setText(f"{value:.2f}".rstrip("0").rstrip("."))

    # qty 조정 버튼
    def on_qty_plus(self):
        self._set_qty(self.get_qty() + self.qty_step)

    def on_qty_minus(self):
        self._set_qty(self.get_qty() - self.qty_step)

    def on_qty_half(self):
        self._set_qty(self.get_qty() / 2)

    def on_qty_double(self):
        self._set_qty(self.get_qty() * 2)

    def set_symbol(self, symbol: str):
        self.labelSymbol.setText(symbol)
