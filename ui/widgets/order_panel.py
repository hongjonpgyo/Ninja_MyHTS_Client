# ui/widgets/order_panel.py
from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel.ui", self)

        # 버튼 연결은 MainWindow에서 처리
        # 여기서는 버튼 자체만 제공

    def get_qty(self) -> float:
        """수량(Qty) 가져오기 (실패 시 0 반환)"""
        try:
            return float(self.editQty.text())
        except:
            return 0

    def set_symbol(self, symbol: str):
        """심볼 변경 시 UI 업데이트 (필요 시 확장)"""
        self.labelSymbol.setText(symbol)
