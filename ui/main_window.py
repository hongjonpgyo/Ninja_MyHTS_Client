# ui/main_window.py
import asyncio
from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer

from ui.widgets.orderbook_widget import OrderbookWidget
from ui.widgets.order_panel import OrderPanel
from ui.widgets.position_table import PositionsTable
from services.ws_client import PriceWSClient
from services.api_client import APIClient


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        loadUi("ui/main_window.ui", self)

        self.current_symbol = "BTCUSDT"

        # API 연결
        self.api = APIClient()

        # 주문 패널 attach
        self.order_panel = OrderPanel(self)
        self.orderPanelLayout.addWidget(self.order_panel)

        # 오더북 attach
        self.orderbook = OrderbookWidget(self.tableOrderbook)

        # 포지션 테이블 attach
        self.positions_table = PositionsTable(self.tablePositions)

        # 심볼 콤보 박스
        self.symbolCombo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        self.symbolCombo.currentTextChanged.connect(self.change_symbol)

        # WS 시작
        self.ws_started = False


    def showEvent(self, event):
        super().showEvent(event)

        if not self.ws_started:
            self.ws_started = True
            QTimer.singleShot(0, self.start_async)


    def start_async(self):
        asyncio.create_task(self.start_ws())
        asyncio.create_task(self.refresh_tables())


    async def start_ws(self):
        print("[WS] start:", self.current_symbol)
        self.ws = PriceWSClient(self.current_symbol, self.update_price)
        await self.ws.connect()


    def change_symbol(self, symbol):
        print("[UI] Symbol changed:", symbol)
        self.current_symbol = symbol
        if hasattr(self, "ws"):
            self.ws.change_symbol(symbol)


    async def refresh_tables(self):
        while True:
            await self.positions_table.refresh()
            await asyncio.sleep(1)


    def update_price(self, data):
        last = data.get("last")
        self.labelPrice.setText(f"{last}")
