# 주문 화면 패널
# widgets/order_panel.py
from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi
from services.api_client import APIClient


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel.ui", self)

        self.api = APIClient()
        self.account_id = 1  # 기본 계좌

        self.btnBuy.clicked.connect(self._on_buy)
        self.btnSell.clicked.connect(self._on_sell)

    def _on_buy(self):
        qty = float(self.editQty.text())
        symbol = self.parent().current_symbol
        res = self.api.place_market(self.account_id, symbol, "BUY", qty)
        print("BUY Result:", res)

    def _on_sell(self):
        qty = float(self.editQty.text())
        symbol = self.parent().current_symbol
        res = self.api.place_market(self.account_id, symbol, "SELL", qty)
        print("SELL Result:", res)
