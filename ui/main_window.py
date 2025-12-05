# ui/main_window.py
import asyncio
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer

from ui.widgets.orderbook_widget import OrderbookWidget
from ui.widgets.order_panel import OrderPanel
from ui.widgets.position_table import PositionsTable
from ui.widgets.balance_widget import BalanceWidget

from services.ws_client import PriceWSClient, DepthWSClient
from services.api_client import APIClient

from api.account_api import AccountApi
from api.position_api import PositionApi


class MainWindow(QMainWindow):

    # -------------------------------------------------------
    # 1) 초기화
    # -------------------------------------------------------
    def __init__(self, api_client: APIClient, show_login_window_callback):
        super().__init__()
        loadUi("ui/main_window.ui", self)

        # API
        self.api = api_client
        self.account_api = AccountApi()
        self.position_api = PositionApi()

        # 상태 값
        self.user = None
        self.account_id = None
        self.current_symbol = "BTCUSDT"
        self.ws = None
        self.depth_client = None
        self.ws_started = False

        # ---------------------------------------------------
        # UI 컴포넌트 연결
        # ---------------------------------------------------
        self.order_panel = OrderPanel(self)
        self.orderPanelLayout.addWidget(self.order_panel)

        self.orderbook = OrderbookWidget(self.tableOrderbook)
        self.positions_table = PositionsTable(self.tablePositions)
        self.balance_widget = BalanceWidget()

        # 주문 버튼
        self.order_panel.btnBuy.clicked.connect(
            lambda: self.safe_async(self.place_order("BUY"))
        )
        self.order_panel.btnSell.clicked.connect(
            lambda: self.safe_async(self.place_order("SELL"))
        )

        # 로그아웃
        self.btnLogout.clicked.connect(self.logout)
        self.show_login_window_callback = show_login_window_callback

        # ---------------------------------------------------
        # 심볼 콤보박스
        # ---------------------------------------------------
        self.symbolCombo.blockSignals(True)
        self.symbolCombo.clear()
        self.symbolCombo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        self.symbolCombo.setCurrentText(self.current_symbol)
        self.symbolCombo.blockSignals(False)

        self.symbolCombo.currentTextChanged.connect(self.change_symbol)

        # main_window.py __init__ 끝부분에 추가

        # ===============================
        # Replace placeholder tables
        # ===============================

        # --- Positions ---
        try:
            self.tablePositions.setParent(None)  # UI에서 제거
        except:
            pass

        self.positionsLayout.addWidget(self.positions_table)

        # --- Account ---
        try:
            self.tableAccount.setParent(None)
        except:
            pass

        self.accountLayout.addWidget(self.balance_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.safe_async(self.refresh_loop()))
        self.timer.start(1000)

    # -------------------------------------------------------
    # 2) 로그인 후 초기 데이터 주입
    # -------------------------------------------------------
    def init_user(self, token: str, user, account_id: int):
        self.api.set_token(token)
        self.user = user
        self.account_id = account_id

        # self.labelUser.setText(f"{user['name']} ({user['email']})")
        # self.labelAccount.setText(f"계좌번호: {self.account_id}")
        self.safe_async(self.refresh_all())
        self.show()

    # -------------------------------------------------------
    # 3) 안전한 비동기 실행
    # -------------------------------------------------------
    def safe_async(self, coro):
        try:
            asyncio.create_task(coro)
        except Exception as e:
            print("[ASYNC ERROR]", e)

    # -------------------------------------------------------
    # 4) 화면 표시 이벤트 → WS 시작
    # -------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if not self.ws_started:
            self.ws_started = True
            QTimer.singleShot(0, self.start_async)

    def start_async(self):
        asyncio.create_task(self.start_price_ws())
        asyncio.create_task(self.start_depth_ws())
        asyncio.create_task(self.refresh_tables())

    # -------------------------------------------------------
    # 5) WS: Price
    # -------------------------------------------------------
    async def start_price_ws(self):
        # 기존 연결 종료
        if self.ws:
            try:
                await self.ws.stop()
            except Exception as e:
                print("[WS STOP ERROR]", e)
            self.ws = None

        print("[WS] PriceWS start:", self.current_symbol)
        self.ws = PriceWSClient(self.current_symbol, self.update_price)
        asyncio.create_task(self.ws.connect())

    # -------------------------------------------------------
    # 6) WS: Depth
    # -------------------------------------------------------
    async def start_depth_ws(self):
        if self.depth_client:
            try:
                await self.depth_client.stop()
            except Exception as e:
                print("[Depth STOP ERROR]", e)
            self.depth_client = None

        print("[WS] DepthWS start:", self.current_symbol)
        self.depth_client = DepthWSClient(self.current_symbol, self.on_depth_update)
        asyncio.create_task(self.depth_client.connect())

    # -------------------------------------------------------
    # 7) Symbol 변경
    # -------------------------------------------------------
    def change_symbol(self, symbol):
        symbol = symbol.upper()
        if symbol == self.current_symbol:
            return

        print(f"[UI] Symbol changed: {self.current_symbol} → {symbol}")
        self.current_symbol = symbol
        self.order_panel.set_symbol(symbol)

        # 재연결
        asyncio.create_task(self.restart_streams())

    async def restart_streams(self):
        await self.start_price_ws()
        await self.start_depth_ws()

    # -------------------------------------------------------
    # 8) 가격 UI 업데이트
    # -------------------------------------------------------
    def update_price(self, data):
        last = data.get("last")
        if last:
            self.labelPrice.setText(f"{last:,.2f}")

    # -------------------------------------------------------
    # 9) 오더북 UI 업데이트
    # -------------------------------------------------------
    def on_depth_update(self, bids, asks):
        self.orderbook.update_depth(bids, asks)

    # -------------------------------------------------------
    # 10) 포지션 테이블 갱신
    # -------------------------------------------------------
    async def refresh_tables(self):
        try:
            positions = await self.api.get_positions(self.account_id)
            self.positions_table.render(positions)
        except Exception as e:
            print("[Positions] ERROR:", e)

    async def refresh_all(self):
        try:
            balance = await self.api.get_account(self.account_id)
            self.balance_widget.update_balance(balance)
        except Exception as e:
            print("[Balance] ERROR:", e)

    async def refresh_loop(self):
        await self.refresh_tables()
        await self.refresh_all()

    # -------------------------------------------------------
    # 11) BUY / SELL 주문
    # -------------------------------------------------------
    async def place_order(self, side):
        try:
            qty = self.order_panel.get_qty()
            if qty <= 0:
                QMessageBox.warning(self, "Error", "수량이 올바르지 않습니다.")
                return

            result = await self.api.order_market(
                account_id=self.account_id,
                symbol=self.current_symbol,
                side=side,
                qty=qty,
            )

            print("ORDER RESULT:", result)

            if not result.get("ok"):
                QMessageBox.warning(self, "Order Error", str(result.get("error")))
                return

            QMessageBox.information(self, "Order", f"{side} 주문 완료!")
            self.safe_async(self.refresh_tables())
            self.safe_async(self.refresh_all())

        except Exception as e:
            print("[ORDER ERROR]", e)
            QMessageBox.warning(self, "Order Error", str(e))

    # -------------------------------------------------------
    # 12) 로그아웃
    # -------------------------------------------------------
    def logout(self):
        print("[LOGOUT] 로그아웃 실행")
        self.api.clear_token()
        self.close()
        self.show_login_window_callback()

    # -------------------------------------------------------
    # 13) 창 닫힐 때 WS 종료
    # -------------------------------------------------------
    def closeEvent(self, event):
        try:
            if self.ws:
                asyncio.create_task(self.ws.stop())
            if self.depth_client:
                asyncio.create_task(self.depth_client.stop())
        finally:
            event.accept()
