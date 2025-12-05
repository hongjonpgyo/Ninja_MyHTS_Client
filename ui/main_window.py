# ui/main_window.py
import asyncio
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer

from ui.widgets.orderbook_widget import OrderbookWidget
from ui.widgets.order_panel import OrderPanel
from ui.widgets.position_table import PositionsTable
from services.ws_client import PriceWSClient, DepthWSClient
from services.api_client import APIClient
from ui.widgets.balance_widget import BalanceWidget
from api.account_api import AccountApi
from api.position_api import PositionApi


class MainWindow(QMainWindow):

    def __init__(self, api_client: APIClient, show_login_window_callback):
        super().__init__()
        loadUi("ui/main_window.ui", self)

        self.account_api = AccountApi()
        self.position_api = PositionApi()

        self.balance_widget = BalanceWidget()
        self.position_table = PositionsTable(self)

        self.current_symbol = "BTCUSDT"
        self.ws = None
        self.depth_client = None
        self.user = None
        self.accounts = None
        self.account_id = None

        self.api = api_client
        self.show_login_window_callback = show_login_window_callback

        # 주문 패널
        self.order_panel = OrderPanel(self)
        self.orderPanelLayout.addWidget(self.order_panel)

        # 버튼 이벤트 (수정 완료)
        self.order_panel.btnBuy.clicked.connect(
            lambda: self.safe_async(self.place_order("BUY"))
        )
        self.order_panel.btnSell.clicked.connect(
            lambda: self.safe_async(self.place_order("SELL"))
        )

        self.btnLogout.clicked.connect(self.logout)

        # 오더북
        self.orderbook = OrderbookWidget(self.tableOrderbook)

        # 포지션 테이블
        self.positions_table = PositionsTable(self.tablePositions)

        # 심볼
        # --- 심볼 콤보 초기화 (신호 차단) ---
        self.symbolCombo.blockSignals(True)
        self.symbolCombo.clear()
        self.symbolCombo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        self.symbolCombo.setCurrentText(self.current_symbol)
        self.symbolCombo.blockSignals(False)

        self.symbolCombo.currentTextChanged.connect(self.change_symbol)

        self.ws_started = False

    def init_user(self, token: str, user, account_id : int):
        self.api.set_token(token)
        self.user = user

        # 기본 계좌 선택
        self.account_id = account_id

        # self.labelUser.setText(f"{user['name']} ({user['email']})")
        # self.labelAccount.setText(f"계좌번호: {self.account_id}")

        self.show()


    def safe_async(self, coro):
        """UI 이벤트에서 안전하게 비동기 실행"""
        try:
            asyncio.create_task(coro)
        except Exception as e:
            print("[ASYNC ERROR]", e)


    def showEvent(self, event):
        super().showEvent(event)

        if not self.ws_started:
            self.ws_started = True
            QTimer.singleShot(0, self.start_async)


    def start_async(self):
        asyncio.create_task(self.start_price_ws())
        asyncio.create_task(self.start_depth_ws())
        asyncio.create_task(self.refresh_tables())


    async def start_price_ws(self):
        if self.ws:
            await self.ws.stop()

        print("[WS] PriceWS start:", self.current_symbol)
        self.ws = PriceWSClient(self.current_symbol, self.update_price)
        asyncio.create_task(self.ws.connect())


    async def start_depth_ws(self):
        if self.depth_client:
            await self.depth_client.stop()

        print("[WS] DepthWS start:", self.current_symbol)
        self.depth_client = DepthWSClient(
            self.current_symbol,
            self.on_depth_update
        )
        asyncio.create_task(self.depth_client.connect())

    def change_symbol(self, symbol: str):
        symbol = symbol.upper()
        if symbol == self.current_symbol:
            # 동일 심볼이면 아무 것도 안 함 (무한 루프 방지)
            return
        print("[UI] Symbol changed:", self.current_symbol, "→", symbol)
        self.current_symbol = symbol

        # 여기서 symbolCombo.setCurrentText(...) 는 절대 호출하지 말기!
        # self.symbolCombo.setCurrentText(symbol)  <-- 이거 하면 시그널 또 발생해서 루프 됨

        # 상단 라벨 / 패널 업데이트
        # self.symbolLabel.setText(symbol)
        self.order_panel.set_symbol(symbol)

        # 🔥 스트림 재시작 (기존 것 stop 후 새로)
        asyncio.create_task(self.restart_streams())

    async def restart_streams(self):
        await self.start_price_ws()
        await self.start_depth_ws()

    def update_price(self, data):
        last = data.get("last")
        if last:
            self.labelPrice.setText(f"{last:,.2f}")


    def on_depth_update(self, bids, asks):
        self.orderbook.update_depth(bids, asks)


    async def refresh_tables(self):
        while True:
            await self.positions_table.refresh()
            await asyncio.sleep(1)

        # ui/main_window.py

    async def place_order(self, side):
        """BUY/SELL 주문 실행"""

        try:
            qty = self.order_panel.get_qty()
            if qty <= 0:
                QMessageBox.warning(self, "Error", "수량이 올바르지 않습니다.")
                return

            if self.account_id is None:
                QMessageBox.warning(self, "Error", "계좌 정보가 없습니다. 먼저 로그인 해 주세요.")
                return

            result = await self.api.order_market(
                account_id=self.account_id,
                symbol=self.current_symbol,
                side=side,
                qty=qty,
            )
            print("ORDER RESULT:", result)

            if not result or not result.get("ok", False):
                # 백엔드 에러 메시지 뽑기
                err = result.get("error")
                if isinstance(err, dict) and "detail" in err:
                    msg = str(err["detail"])
                else:
                    msg = str(err)
                QMessageBox.warning(self, "Order Error", msg)
                return

            # ⬇ 여기까지 오면 성공
            QMessageBox.information(self, "Order", f"{side} 주문 완료!")

            # 포지션 테이블 갱신
            asyncio.create_task(self.positions_table.refresh())

        except Exception as e:
            print("[ORDER ERROR]", e)
            QMessageBox.warning(self, "Order Error", str(e))

    def logout(self):
        """로그아웃 → LoginWindow 다시 표시"""
        try:
            # API 토큰 초기화
            self.api.token = None
            self.api.user_id = None
            self.api.account_id = None
        except:
            pass

        print("[LOGOUT] 로그아웃 실행")

        # 현재 창 닫기
        self.close()

        # LoginWindow 다시 띄우기
        self.show_login_window_callback()

    def refresh_all(self):
        balance = self.account_api.get_balance(self.account_id)
        self.balance_widget.update_balance(balance)

        positions = self.position_api.get_my_positions(self.account_id)
        self.position_table.update_positions(positions)

    def on_close_position(self, position_id):
        res = self.position_api.close(position_id)
        if res and res.get("ok"):
            QMessageBox.information(self, "Close", "Position closed!")
            self.refresh_all()
        else:
            QMessageBox.warning(self, "Error", "Close failed")

    def closeEvent(self, event):
        loop = asyncio.get_event_loop()
        if self.ws:
            loop.create_task(self.ws.stop())
        if self.depth_client:
            loop.create_task(self.depth_client.stop())
        event.accept()

