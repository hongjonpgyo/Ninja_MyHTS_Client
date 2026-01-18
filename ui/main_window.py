# ui/main_window.py
import asyncio

from PyQt6.QtWidgets import QMainWindow, QSizePolicy, QWidget, QHBoxLayout, QPushButton
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer, Qt

# -------------------------
# API
# -------------------------
from api.ls.ls_api_client import LSAPIClient
from api.ls.ls_account_api import LSAccountApi
from api.ls.ls_order_api import LSOrderApi
from api.position_api import PositionApi
from api.order_api import OrderApi
from api.favorite_api import FavoriteApiClient

# -------------------------
# Services / Store
# -------------------------
from services.execution_ws_client import ExecutionWSClient
from services.ls.ls_account_ws_client import LSAccountWSClient
from services.trade_ws_client import TradesWSClient
from services.ls.my_order_store import MyOrderStore

# -------------------------
# Controllers
# -------------------------
from ui.controllers.price_controller import PriceController
from ui.controllers.background_controller import BackgroundController
from ui.controllers.time_sales_controller import TimeSalesController
from ui.controllers.execution_strength import ExecutionStrength
from ui.ls_controllers.ls_reservation_controller import ReservationController
from ui.ls_controllers.ls_watchlist_controller import LSWatchListController
from ui.ls_controllers.ls_order_controller import OrderController
from ui.settings.trade_setting import UserTradeSetting

# -------------------------
# Widgets
# -------------------------
from ui.widgets.favorite_bar import FavoriteBar
from ui.widgets.ls_reservation.reservation_widget import ReservationWidget
from ui.widgets.order_control_bar import OrderControlBar
from ui.widgets.ls_orderbook.ls_orderbook_widget import LSOrderBookWidget
from ui.widgets.ls_position.ls_position_table import LSPositionsTable
from ui.widgets.ls_balance.ls_balance_table import LSBalanceTable
from ui.widgets.executions_table import ExecutionsTable
from ui.widgets.open_orders_widget import OpenOrdersWidget
from ui.widgets.symbol_summary_widget import SymbolSummaryWidget
from ui.widgets.toast import ToastMessage
from ui.widgets.top_bar import TopBarWidget

from ui.utils.formatter import fmt_money, fmt_pnl, fmt_rate
from ui.workers.execution_stream_worker import ExecutionStreamWorker

from config.settings import LS_BASE_URL

FIXED_WIDTH = 1400
PRICE_COL = 4


class MainWindow(QMainWindow):
    # =====================================================
    # INIT
    # =====================================================
    def __init__(self, api_client, show_login_window_callback):
        super().__init__()

        # -------------------------
        # UI Load
        # -------------------------
        loadUi("ui/main_window_20260111.ui", self)
        self.setFixedWidth(FIXED_WIDTH)

        # -------------------------
        # Core State
        # -------------------------
        self.api = api_client
        self.ls_api = LSAPIClient()
        self.show_login_window_callback = show_login_window_callback

        self.user = None
        self.account_id = None
        self.current_symbol = "HSIF26"
        self.running = True
        self._fetching_open_orders = False

        self.my_order_store = MyOrderStore()
        self.exec_strength = ExecutionStrength(window_sec=5)

        # -------------------------
        # Async Queue (🔥 핵심)
        # -------------------------
        self._queue = asyncio.Queue()
        self._worker_task = None

        self.trade_setting = UserTradeSetting()

        # -------------------------
        # API Wrappers
        # -------------------------
        self.ls_account_api = LSAccountApi(self.ls_api)
        self.position_api = PositionApi(self.api)
        self.order_api = LSOrderApi(self.ls_api)

        # -------------------------
        # UI Components
        # -------------------------
        self._init_top_bar()
        self._init_orderbook()
        self._init_watchlist()
        self._init_bottom_tabs()
        self._init_right_panel()

        # -------------------------
        # Controllers
        # -------------------------
        self.price_controller = PriceController(top_bar=self.topBar)
        self.order_controller = OrderController(main_window=self, api=self.ls_api)
        self.bg_controller = BackgroundController(self, interval=0.5)

        self.orderbook.set_order_controller(self.order_controller)

        # -------------------------
        # WS Clients
        # -------------------------
        self.exec_ws = None
        self.account_ws = None
        # self.trade_ws = None

        # -------------------------
        # Clock
        # -------------------------
        self._last_ls_time = None
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._on_clock_tick)
        self.clock_timer.start(1000)

        self.labelClock.setStyleSheet(
            "color:#00ff99;font-weight:bold;font-size:13px;"
        )

        # -------------------------
        # Layout tuning
        # -------------------------
        self._tune_splitters()

        # -------------------------
        # Initial Load
        # -------------------------
        self.enqueue_async(self.load_ls_watchlist())

        self.execution_worker = ExecutionStreamWorker(
            base_url=LS_BASE_URL
        )

        self.execution_worker.execution_received.connect(
            self.on_execution_received
        )

        self.execution_worker.start()  # ← 이게 없으면 100% 안 뜸

        self.orderbookControlLayout.setContentsMargins(8, 6, 8, 6)
        self.orderbookControlBar.setStyleSheet("""
        QFrame#orderbookControlBar {
            background-color: #1f1f1f;
            border-bottom: 1px solid #2b2b2b;
        }

        QFrame#orderbookControlBar QLabel {
            color: #cccccc;
            font-size: 11px;
        }

        QFrame#orderbookControlBar QLabel#lblPnL {
            font-weight: bold;
        }
        """)

        self.bottomTabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        print('tabName : ' + self.bottomTabs.widget(idx).objectName())

        if self.bottomTabs.widget(idx).objectName() == "tabOpenOrders":
            asyncio.create_task(self.reload_reservations())

    # =====================================================
    # UI INIT
    # =====================================================
    def _init_top_bar(self):
        self.topBar = TopBarWidget(self)
        self.centralWidget().layout().insertWidget(0, self.topBar)

        self.topBar.comboSymbol.currentTextChanged.connect(
            lambda s: self.enqueue_async(self.change_symbol(s))
        )

    def _init_orderbook(self):
        self.orderbook = LSOrderBookWidget(
            table=self.tableOrderbook,
            tick_size=1.0,
        )
        self.orderbook.set_symbol(self.current_symbol, 1.0)

        # self.tableOrderbook.cellClicked.connect(self.on_orderbook_click)

        self.favoriteBar = FavoriteBar()
        self.favoriteBar.symbolClicked.connect(self.on_favorite_clicked)
        # self.splitterLeft.insertWidget(0, self.favoriteBar)
        self.topBarLayout.addWidget(self.favoriteBar)

        # self.orderControlBar = OrderControlBar(self)
        # self.splitterLeft.insertWidget(2, self.orderControlBar)

    def _init_watchlist(self):
        self.ls_watchlist_controller = LSWatchListController(
            table=self.tableWatchlist,
            on_symbol_click=self.on_watchlist_symbol_clicked,
        )
        self.tableWatchlist.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def _init_bottom_tabs(self):
        self.positions_table = LSPositionsTable()
        self.positionsLayout.addWidget(self.positions_table)

        self.balance_widget = LSBalanceTable()
        self.accountLayout.addWidget(self.balance_widget)

        self.executions_table = ExecutionsTable()
        self.executionsLayout.addWidget(self.balance_widget)

        # self.reservation_widget = ReservationWidget()
        # self.reservationLayout.addWidget(self.reservation_widget)
        self.setup_reservation_tab()

    def _init_right_panel(self):
        self.time_sales_controller = TimeSalesController(self.tableTimeSales)
        self.symbolSummary = SymbolSummaryWidget(self)

        self.rightPanelLayout.insertWidget(
            self.rightPanelLayout.indexOf(self.tableWatchlist),
            self.symbolSummary,
        )

    def _tune_splitters(self):
        # self.splitterRoot.setStretchFactor(0, 6)
        # self.splitterRoot.setStretchFactor(1, 5)
        #
        # self.splitterLeft.setStretchFactor(0, 8)
        # self.splitterLeft.setStretchFactor(1, 2)
        #
        # self.splitterTop.setStretchFactor(0, 5)
        # self.splitterTop.setStretchFactor(1, 4)
        self.splitterRoot.setStretchFactor(0, 6)
        self.splitterRoot.setStretchFactor(1, 5)

        # 🔥 여기만 바꾸면 됨
        self.splitterLeft.setStretchFactor(0, 3)  # 상단(요약)
        self.splitterLeft.setStretchFactor(1, 5)  # 오더북
        self.splitterLeft.setStretchFactor(2, 2)  # 하단탭 ↓

    # =====================================================
    # SAFE UI / ASYNC QUEUE
    # =====================================================
    def safe_ui(self, func, *args):
        QTimer.singleShot(0, lambda: func(*args))

    def enqueue_async(self, coro):
        if coro and asyncio.iscoroutine(coro):
            self._queue.put_nowait(coro)

    async def _queue_worker(self):
        while True:
            coro = await self._queue.get()
            if coro is None:
                break
            try:
                await coro
            except Exception as e:
                print("[QUEUE ERROR]", e)
            finally:
                self._queue.task_done()

    # =====================================================
    # LOGIN / INIT
    # =====================================================
    def init_user(self, token, user, account_id):
        self.api.set_token(token)
        self.user = user
        self.account_id = account_id

        self.open_orders_widget = OpenOrdersWidget(
            main_window=self,
            order_api=self.order_api,
            account_id=account_id,
        )

        self.accountLayout.addWidget(self.open_orders_widget)

        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._queue_worker())

        self.exec_ws = ExecutionWSClient(
            token=token,
            account_id=account_id,
            callback=self.safe_ui_handle_execution,
            main_window=self,
        )

        # self.account_ws = LSAccountWSClient(
        #     token=token,
        #     account_id=account_id,
        #     callback=self.safe_ui_update_account_ws,
        #     main_window=self,
        # )

        self.favorite_api = FavoriteApiClient(token=token)
        self.load_favorites()

        self.bg_controller.start()
        # self.enqueue_async(self.exec_ws.start())
        # self.enqueue_async(self.account_ws.start())
        self.reservation_controller = ReservationController(
            self.reservationWidget,
            self.api,
            self.account_id,
        )
        self.enqueue_async(self.reservation_controller.refresh())

        self.show()

    # =====================================================
    # WATCHLIST / SYMBOL
    # =====================================================
    def on_watchlist_symbol_clicked(self, symbol: str, row: dict):
        tick_size = row.get("tick_size") or row.get("price_unit") or 1.0
        self.selected_ls_row = row
        self.enqueue_async(self.change_symbol(symbol, tick_size))

    async def change_symbol(self, symbol: str, tick_size: float | None = None):
        symbol = symbol.upper()
        if symbol == self.current_symbol:
            return

        self.current_symbol = symbol
        self.orderbook.set_symbol(symbol, tick_size=tick_size)
        self.price_controller.set_symbol(symbol)
        self.price_controller.reset()

        # if self.trade_ws:
        #     await self.trade_ws.stop()

        self.time_sales_controller.clear()
        # self.trade_ws = TradesWSClient(symbol=symbol, callback=self._on_trade_ws)
        # await self.trade_ws.start()

        if hasattr(self, "selected_ls_row"):
            self.symbolSummary.update_ls_symbol(self.selected_ls_row)

    # =====================================================
    # FAVORITE
    # =====================================================
    def on_favorite_clicked(self, symbol: str):
        """
        FavoriteBar에서 심볼 클릭 시
        """
        if not symbol:
            return

        # Watchlist 클릭과 동일한 흐름으로 처리
        self.enqueue_async(self.change_symbol(symbol))

    async def fetch_open_orders(self):
        try:
            if self._fetching_open_orders:
                return
            self._fetching_open_orders = True

            orders = await self.order_api.get_open_orders(self.account_id)

            # 1️⃣ OpenOrders 테이블 갱신
            self.safe_ui(
                self.open_orders_widget.update_table,
                orders
            )

            # 2️⃣ OrderBook용 my_orders 생성 (DB 기준)
            my_orders = {"SELL": {}, "BUY": {}}
            for o in orders:
                price = round(float(o["price"]), 6)
                side = o["side"]

                my_orders[side][price] = my_orders[side].get(price, 0) + 1

            # 3️⃣ OrderBook 갱신 (항상 DB 기준)
            self.safe_ui(
                self.orderbook.update_my_orders,
                my_orders
            )

        except Exception as e:
            print("[fetch_open_orders ERROR]", e)

        finally:
            self._fetching_open_orders = False

    async def fetch_ls_quote(self):
        try:
            data = await self.ls_api.get(
                f"/ls/futures/quote/{self.current_symbol}"
            )

            price = data.get("price")
            if price is None:
                return

            # 1️⃣ 상단 가격 갱신
            self.safe_ui(
                self.price_controller.on_price,
                {
                    "symbol": self.current_symbol,
                    "price": price,
                    "source": "LS",
                }
            )

            # 2️⃣ OrderBook 기준가 이동
            self.safe_ui(
                self.orderbook.update_ls_price,
                float(price)
            )

        except Exception as e:
            print("[fetch_ls_quote ERROR]", e)

    async def fetch_executions(self):
        """
        체결 내역 조회 (BackgroundController 전용)
        """
        try:
            rows = await self.order_api.get_executions(self.account_id)
            self.safe_ui(
                self.executions_table.update_table,
                rows
            )
        except Exception as e:
            print("[fetch_executions ERROR]", e)

    async def fetch_account_state(self):
        try:
            balance = await self.ls_account_api.get_balance(self.account_id)

            positions = await self.ls_account_api.get_positions(self.account_id)
            # self.safe_ui(
            #     self.balance_widget.update_balance,
            #     balance
            # )
            self.safe_ui(
                self.update_account_summary,
                balance
            )

            self.safe_ui(
                self.positions_table.render,
                positions
            )

        except Exception as e:
            print("[fetch_account_state ERROR]", e)

    async def reload_reservations(self):
        await self.reservation_controller.refresh()
        # self.reservationWidget.update_rows(rows)

    # # =====================================================
    # # ORDERBOOK
    # # =====================================================
    # def on_orderbook_click(self, row, col):
    #     if col == PRICE_COL:
    #         return
    #
    #     item = self.tableOrderbook.item(row, PRICE_COL)
    #     if not item:
    #         return
    #
    #     try:
    #         price = float(item.text().replace(",", ""))
    #     except ValueError:
    #         return
    #
    #     side = "SELL" if col <= 3 else "BUY"
    #     self.order_controller.place_limit_from_book(
    #         side=side, price=price, qty=1
    #     )

    def update_account_summary(self, data: dict):
        if not data:
            return

        deposit = float(data.get("deposit", 0))
        available = float(data.get("available", 0))
        pnl = float(data.get("unrealized_pnl", 0))
        rate = float(data.get("unrealized_pnl_rate", 0))

        self.lblDeposit.setText(fmt_money(deposit))
        self.lblAvailable.setText(fmt_money(available))
        self.lblPnL.setText(fmt_pnl(pnl))
        self.lblPnLRate.setText(fmt_rate(rate) + "%")

        # 색상
        if pnl > 0:
            self.lblPnL.setStyleSheet("color:#2ecc71;")
        elif pnl < 0:
            self.lblPnL.setStyleSheet("color:#e74c3c;")
        else:
            self.lblPnL.setStyleSheet("color:#cccccc;")

    # =====================================================
    # WS CALLBACKS
    # =====================================================
    # def _on_trade_ws(self, data: dict):
    #     self.exec_strength.add_trade(data)
    #     strength = self.exec_strength.calc()
    #
    #     self.safe_ui(self.topBar.update_exec_strength, strength)
    #     self.safe_ui(self.time_sales_controller.on_trade, data)

    # async def _start_trade_ws_initial(self):
    #     if self.trade_ws:
    #         return
    #
    #     self.time_sales_controller.clear()
    #
    #     self.trade_ws = TradesWSClient(
    #         symbol=self.current_symbol,
    #         callback=self._on_trade_ws,
    #     )
    #     await self.trade_ws.start()

    def safe_ui_handle_execution(self, msg: dict):
        data = msg.get("data", {}) if msg.get("type") == "execution" else msg
        if not data:
            return

        self.executions_table.append_row(data)
        self.show_toast(
            f"{data.get('symbol')} {data.get('side')} {data.get('qty')} @ {data.get('price')} 체결"
        )

    def safe_ui_update_account_ws(self, data):
        if data.get("type") != "account_update":
            return

        # self.positions_table.render(data.get("positions", []))
        # self.balance_widget.update_balance(data.get("account", {}))

    def setup_reservation_tab(self):
        # 버튼 바
        self.reservationActionBar = QWidget()
        bar = QHBoxLayout(self.reservationActionBar)
        bar.setContentsMargins(6, 6, 6, 6)
        bar.setSpacing(8)

        self.btnSellReserveCancel = QPushButton("매도예약취소")
        self.btnBuyReserveCancel = QPushButton("매수예약취소")
        self.btnSymbolCancel = QPushButton("종목취소")
        self.btnAllCancel = QPushButton("일괄취소")

        self.btnAllCancel.clicked.connect(self.cancel_all_reservations)
        self.btnSymbolCancel.clicked.connect(self.cancel_symbol_reservations)


        for btn in (
                self.btnSellReserveCancel,
                self.btnBuyReserveCancel,
                self.btnSymbolCancel,
                self.btnAllCancel,
        ):
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        bar.addWidget(self.btnSellReserveCancel)
        bar.addWidget(self.btnBuyReserveCancel)
        bar.addStretch()
        bar.addWidget(self.btnSymbolCancel)
        bar.addWidget(self.btnAllCancel)

        # 예약 테이블
        self.reservationWidget = ReservationWidget()

        self.reservationLayout.addWidget(self.reservationActionBar)
        self.reservationLayout.addWidget(self.reservationWidget)

    async def cancel_all_reservations(self):
        await self.api.cancel_reservations(scope="ALL")

    async def cancel_symbol_reservations(self):
        symbol = self.current_symbol
        await self.api.cancel_reservations(scope="SYMBOL", symbol=symbol)

    def on_execution_received(self, event: dict):
        exec_type = event.get("exec_type")

        if exec_type == "TRADE":
            self.time_sales_controller.on_trade(event)
        elif exec_type == "STATUS":
            self.reservation_controller.on_status_event(event)


    # =====================================================
    # FETCHERS
    # =====================================================
    async def load_ls_watchlist(self):
        rows = await self.ls_api.get(
            "/ls/futures/watchlist",
            params={"only_has_price": False, "limit": 200},
        )
        self.safe_ui(self.ls_watchlist_controller.load_rows, rows)

    def load_favorites(self):
        try:
            for fav in self.favorite_api.list():
                self.favoriteBar.add_symbol(fav["symbol_code"])
        except Exception as e:
            print("[Favorite] load failed:", e)

    # =====================================================
    # CLOCK
    # =====================================================
    def _on_clock_tick(self):
        asyncio.create_task(self.update_ls_clock())

    async def update_ls_clock(self):
        try:
            data = await self.ls_api.get("/ls/futures/time")
            t = data.get("ls_time")
            if isinstance(t, str) and len(t) >= 6:
                self._last_ls_time = f"{t[:2]}:{t[2:4]}:{t[4:6]}"
            if self._last_ls_time:
                self.labelClock.setText(self._last_ls_time)
        except Exception:
            if self._last_ls_time:
                self.labelClock.setText(self._last_ls_time)

    # =====================================================
    # UTIL
    # =====================================================
    def show_toast(self, text: str):
        ToastMessage(self, text).show_toast()

    # =====================================================
    # SHUTDOWN
    # =====================================================
    def closeEvent(self, event):
        self.running = False
        self.enqueue_async(self.shutdown())
        event.accept()

    async def shutdown(self):
        try:
            if self.bg_controller:
                await self.bg_controller.stop()
            if self.exec_ws:
                await self.exec_ws.stop()
            if self.account_ws:
                await self.account_ws.stop()
            # if self.trade_ws:
            #     await self.trade_ws.stop()
            self._queue.put_nowait(None)
        finally:
            if self._worker_task:
                self._worker_task.cancel()

    # =====================================================
    # LOGOUT
    # =====================================================
    def logout(self):
        """
        TopBar / 메뉴에서 호출되는 로그아웃
        """
        self.running = False

        # WS / 백그라운드 정리
        self.enqueue_async(self.shutdown())

        # 토큰 제거
        if self.api:
            self.api.clear_token()

        # 창 닫고 로그인 화면으로
        self.close()
        self.show_login_window_callback()

