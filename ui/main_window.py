# ui/main_window.py
import asyncio
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer
from PyQt6.uic.Compiler.qtproxies import QtWidgets

from ui.widgets.orderbook_widget import OrderbookWidget
from ui.widgets.order_panel import OrderPanel
from ui.widgets.position_table import PositionsTable
from ui.widgets.balance_widget import BalanceWidget
from ui.widgets.OpenOrdersWidget import OpenOrdersWidget
from ui.widgets.executions_table import ExecutionsTable

from services.api_client import APIClient
from services.ws_client import PriceWSClient

from api.account_api import AccountApi
from api.position_api import PositionApi
from api.order_api import OrderApi


class MainWindow(QMainWindow):

    def __init__(self, api_client: APIClient, show_login_window_callback):
        super().__init__()
        loadUi("ui/main_window.ui", self)

        # API
        self.api = api_client
        self.account_api = AccountApi()
        self.position_api = PositionApi()
        self.order_api = OrderApi()

        # State
        self.user = None
        self.account_id = None
        self.current_symbol = "BTCUSDT"

        self.ws = None
        self.ws_task = None
        self.bg_task = None  # background loop task

        self.running = True  # 전체 윈도우 동작 제어

        # UI Setup
        self.order_panel = OrderPanel(self)
        self.orderPanelLayout.addWidget(self.order_panel)

        self.orderbook = OrderbookWidget(self.tableOrderbook)
        self.positions_table = PositionsTable(self.tablePositions)
        self.balance_widget = BalanceWidget()

        self.executions_table = ExecutionsTable()  # 새 테이블 생성
        self.executionsLayout.addWidget(self.executions_table)

        self.order_panel.btnBuy.clicked.connect(lambda: self.on_order_click("BUY"))
        self.order_panel.btnSell.clicked.connect(lambda: self.on_order_click("SELL"))

        self.btnLogout.clicked.connect(self.logout)

        # 심볼 콤보박스
        self.symbolCombo.clear()
        self.symbolCombo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        self.symbolCombo.setCurrentText(self.current_symbol)
        self.symbolCombo.currentTextChanged.connect(self.change_symbol)

        # 레이아웃 교체
        self.tablePositions.setParent(None)
        self.positionsLayout.addWidget(self.positions_table)

        self.tableAccount.setParent(None)
        self.accountLayout.addWidget(self.balance_widget)

    # ======================================================
    # 로그인 완료 후 초기화
    # ======================================================
    def init_user(self, token, user, account_id):
        self.api.set_token(token)
        self.user = user
        self.account_id = account_id

        self.open_orders_widget = OpenOrdersWidget(self.order_api, account_id)
        self.openOrdersLayout.addWidget(self.open_orders_widget)

        asyncio.create_task(self.fetch_balance())  # 여기만 변경

        self.start_async_tasks()
        self.show()

    # ======================================================
    # 안전한 UI 업데이트 함수
    # ======================================================
    def safe_ui(self, func, *args):
        QTimer.singleShot(0, lambda: func(*args))


    # ======================================================
    # 시작 시 실행할 작업들
    # ======================================================
    def start_async_tasks(self):
        # Price WebSocket
        self.ws_task = asyncio.create_task(self.start_price_ws())

        # Background Loop (orderbook / positions / balance)
        self.bg_task = asyncio.create_task(self.background_loop())


    # ======================================================
    # Price WebSocket
    # ======================================================
    async def start_price_ws(self):
        if self.ws:
            await self.ws.stop()
            self.ws = None

        await asyncio.sleep(0.05)

        self.ws = PriceWSClient(self.current_symbol, self.safe_ui_update_price)
        asyncio.create_task(self.ws.start())  # fire & forget


    # UI 업데이트 전달만 함
    def safe_ui_update_price(self, data):
        last = data.get("last")
        if last:
            self.safe_ui(lambda: self.labelPrice.setText(f"{last:,.2f}"))


    # ======================================================
    # 심볼 변경 시
    # ======================================================
    def change_symbol(self, symbol):
        if symbol == self.current_symbol:
            return

        print(f"[UI] Symbol changed: {self.current_symbol} → {symbol}")
        self.current_symbol = symbol
        self.order_panel.set_symbol(symbol)

        # WS 재시작
        asyncio.create_task(self.start_price_ws())


    # ======================================================
    # Background Loop (Orderbook / Positions / Balance)
    # ======================================================
    async def background_loop(self):
        while self.running:
            try:
                await self.fetch_orderbook()
                await self.fetch_positions()
                await self.fetch_balance()
                await self.fetch_open_orders()
                await self.fetch_executions()
            except Exception as e:
                print("[BG Loop ERROR]", e)

            await asyncio.sleep(0.5)


    # ======================================================
    # Fetch — Orderbook / Positions / Balance
    # ======================================================
    async def fetch_orderbook(self):
        try:
            data = await self.api.get(f"/orderbook/{self.current_symbol}")
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            self.safe_ui(self.orderbook.update_depth, bids, asks)
        except Exception as e:
            print("[Orderbook ERROR]", e)

    async def fetch_positions(self):
        try:
            positions = await self.api.get_positions(self.account_id)
            self.safe_ui(self.positions_table.render, positions)
        except Exception as e:
            print("[Positions ERROR]", e)

    async def fetch_balance(self):
        try:
            balance = await self.api.get_account(self.account_id)
            self.safe_ui(self.balance_widget.update_balance, balance)
        except Exception as e:
            print("[Balance ERROR]", e)

    async def fetch_open_orders(self):
        try:
            # → 반드시 await 필요!
            orders = await asyncio.to_thread(self.order_api.get_open_orders, self.account_id)

            if not isinstance(orders, list):
                print("[OpenOrders] Invalid data:", orders)
                return

            # → UI Thread에서 실행하도록 람다로 감싸기
            self.safe_ui(lambda: self.open_orders_widget.update_table(orders))

        except Exception as e:
            print("[OpenOrders ERROR]", e)

    async def fetch_executions(self):
        try:
            rows = await self.api.get_executions(self.account_id)

            if not isinstance(rows, list):
                print("[Executions ERROR] Invalid response:", rows)
                return

            self.safe_ui(lambda: self.executions_table.update_table(rows))

        except Exception as e:
            print("[Executions ERROR]", e)

    # ======================================================
    # 주문 버튼 클릭 → 비동기 함수 실행
    # ======================================================
    def on_order_click(self, side):
        asyncio.create_task(self.async_place_order(side))

    async def cancel_selected_orders(self):
        order_ids = self.open_orders_widget.cancel_selected_orders()
        if not order_ids:
            QMessageBox.warning(self, "Cancel", "선택된 주문이 없습니다.")
            return

        payload = {"order_ids": order_ids}
        try:
            res = await self.api.post("/orders/cancel", json=payload)
            if res.get("ok"):
                QMessageBox.information(self, "Cancel", "주문이 취소되었습니다.")
                await self.fetch_open_orders()
                await self.fetch_orderbook()
            else:
                QMessageBox.warning(self, "Cancel Error", str(res.get("error")))
        except Exception as e:
            QMessageBox.warning(self, "Cancel Error", str(e))

    async def async_place_order(self, side):
        """모든 주문 API는 이 비동기 함수에서 처리한다."""
        try:
            order_type = self.order_panel.get_order_type()
            qty = self.order_panel.get_qty()
            symbol = self.current_symbol

            if qty <= 0:
                self.safe_ui(lambda: QMessageBox.warning(self, "Error", "수량 오류"))
                return

            # MARKET
            if order_type == "Market":
                result = await self.api.order_market(
                    account_id=self.account_id,
                    symbol=symbol,
                    side=side,
                    qty=qty
                )
            # LIMIT
            else:
                price = self.order_panel.get_limit_price()
                if not price:
                    self.safe_ui(lambda: QMessageBox.warning(self, "Error", "가격 입력 필요"))
                    return

                result = await self.api.order_limit(
                    account_id=self.account_id,
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    price=price
                )

            # 성공 메시지는 UI Thread로
            self.safe_ui(lambda: QMessageBox.information(
                self,
                "Order",
                f"{side} {order_type} 주문 완료!"
            ))

            # 주문 후 즉시 UI 갱신
            asyncio.create_task(self.fetch_orderbook())
            asyncio.create_task(self.fetch_positions())
            asyncio.create_task(self.fetch_balance())

        except Exception as e:
            print("[ORDER ERROR]", e)
            self.safe_ui(lambda: QMessageBox.warning(self, "Order Error", str(e)))


    # ======================================================
    # 로그아웃 처리
    # ======================================================
    def logout(self):
        print("[LOGOUT]")
        self.running = False
        self.api.clear_token()
        self.close()
        self.show_login_window_callback()


    # ======================================================
    # 종료 시 WS 정리
    # ======================================================
    def closeEvent(self, event):
        self.running = False

        async def shutdown():
            try:
                if self.ws:
                    await self.ws.stop()
            except Exception as e:
                print("[WS Close Error]", e)

        asyncio.create_task(shutdown())
        event.accept()
