# ui/main_window.py
import asyncio
from datetime import datetime

from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QSizePolicy, QWidget, QHBoxLayout, QPushButton, QMessageBox, QCheckBox
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
from core import global_rates

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
from ui.ls_controllers.ls_orderbook_controller import OrderBookController
from ui.ls_controllers.ls_reservation_controller import ReservationController
from ui.ls_controllers.ls_watchlist_controller import LSWatchListController
from ui.ls_controllers.ls_order_controller import OrderController
from ui.settings.trade_setting import UserTradeSetting

# -------------------------
# Widgets
# -------------------------
from ui.widgets.favorite_bar import FavoriteBar
from ui.widgets.ls_position.ls_position_protection_panel import LSPositionProtectionPanel
from ui.widgets.ls_reservation.reservation_widget import ReservationWidget
from ui.widgets.ls_orderbook.ls_orderbook_widget import LSOrderBookWidget
from ui.widgets.ls_position.ls_position_table import LSPositionsTable
from ui.widgets.ls_balance.ls_balance_table import LSBalanceTable
from ui.widgets.executions_table import ExecutionsTable
from ui.widgets.ls_trade.trades_table import TradesTable
from ui.widgets.open_orders_widget import OpenOrdersWidget
from ui.widgets.symbol_summary_widget import SymbolSummaryWidget
from ui.widgets.toast import ToastMessage
from ui.widgets.top_bar import TopBarWidget

from ui.utils.formatter import fmt_money, fmt_pnl, fmt_rate
from ui.workers.execution_stream_worker import ExecutionStreamWorker

from config.settings import LS_BASE_URL
from ui.workers.price_stream_worker import PriceStreamWorker

FIXED_WIDTH = 1490
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
        loadUi("ui/main_window_20260123.ui", self)
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
        self.selected_ls_row = None

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
        self.order_api = LSOrderApi(self.api)

        # -------------------------
        # Clock
        # -------------------------
        self._last_ls_time = None
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._on_clock_tick)
        self.clock_timer.start(1000)

        self.labelClock.setFixedWidth(125)
        self.labelClock.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chkAutoCenter = QCheckBox("고정")
        self.chkAutoCenter.setChecked(False)
        self.chkAutoCenter.setCursor(Qt.CursorShape.PointingHandCursor)

        self.clockLayout.addWidget(self.labelClock)
        self.clockLayout.addSpacing(6)
        self.clockLayout.addWidget(self.chkAutoCenter)

        # -------------------------
        # UI Components
        # -------------------------
        self._init_top_bar()
        self._init_orderbook()
        self.order_controller = OrderController(main_window=self, api=self.ls_api, account_api=self.ls_account_api)
        self._init_watchlist()
        self._init_bottom_tabs()
        self._init_right_panel()

        self.orderbook_controller = OrderBookController(
            api_client=self.ls_api,
            view=self.orderbook,
        )

        self.price_controller = PriceController(top_bar=self.topBar, watchlist_controller=self.ls_watchlist_controller)
        self.bg_controller = BackgroundController(self, interval=0.5)

        self.orderbook.priceClicked.connect(self.protection_panel.on_price_clicked)
        self.orderbook.set_order_controller(self.order_controller)

        self.protection_panel.cancelRequested.connect(self.orderbook.clear_base_price_visual)

        # -------------------------
        # WS Clients
        # -------------------------
        self.exec_ws = None
        self.account_ws = None
        # self.trade_ws = None

        # -------------------------
        # Layout tuning
        # -------------------------
        self._tune_splitters()

        # -------------------------
        # Initial Load
        # -------------------------
        self.enqueue_async(self.load_fx_rates())

        self.enqueue_async(self.load_ls_watchlist())

        self.execution_worker = ExecutionStreamWorker(
            base_url=LS_BASE_URL
        )

        self.execution_worker.execution_received.connect(
            self.on_execution_received
        )

        self.execution_worker.start()  # ← 이게 없으면 100% 안 뜸

        self.price_worker = PriceStreamWorker(
            base_url=self.api.base_url,
            token=self.api.token,
        )

        self.price_worker.price_received.connect(
            self.on_price_event
        )

        self.price_worker.start()

        self.orderbookControlLayout.setContentsMargins(8, 6, 8, 6)

        self.bottomTabs.currentChanged.connect(self.on_tab_changed)

        self.btnMarketSell.clicked.connect(
            lambda: self._place_market("SELL")
        )
        self.btnMarketBuy.clicked.connect(
            lambda: self._place_market("BUY")
        )

        # F4 = 시장가 매도
        act_sell = QAction(self)
        act_sell.setShortcut(QKeySequence("F4"))
        act_sell.triggered.connect(lambda: self._place_market("SELL"))
        self.addAction(act_sell)

        # F9 = 시장가 매수
        act_buy = QAction(self)
        act_buy.setShortcut(QKeySequence("F9"))
        act_buy.triggered.connect(lambda: self._place_market("BUY"))
        self.addAction(act_buy)

        self.btnCloseSymbol.clicked.connect(self.on_close_current_symbol)
        QShortcut(QKeySequence("F8"), self, self.on_close_current_symbol)

        self.btnCloseAll.clicked.connect(self.on_close_all_positions)
        QShortcut(QKeySequence("F5"), self, self.on_close_all_positions)

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
        self.chkAutoCenter.stateChanged.connect(
            self.on_auto_center_changed
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
        self.topBarLayout.addWidget(self.favoriteBar)

        # self.orderControlBar = OrderControlBar(self)
        # self.splitterLeft.insertWidget(2, self.orderControlBar)

    def _init_watchlist(self):
        self.ls_watchlist_controller = LSWatchListController(
            table=self.tableWatchlist,
            on_symbol_click=self.on_watchlist_symbol_clicked,
            on_favorite_toggle=self.on_favorite_toggled,
            on_favorite_remove=self.on_favorite_remove
        )
        self.tableWatchlist.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def _init_bottom_tabs(self):
        self.positions_table = LSPositionsTable()

        self.protection_panel = LSPositionProtectionPanel(order_controller=self.order_controller, parent=self)
        self.protection_panel.setMinimumHeight(180)
        self.protection_panel.setMaximumHeight(220)
        self.protection_panel.on_applied = self._reload_protections

        self.positionsLayout.addWidget(self.positions_table)
        self.positionsLayout.addWidget(self.protection_panel)
        self.positions_table.positionSelected.connect(
            # self.protection_panel.load_position
            self.on_position_selected
        )
        self.positions_table.setMinimumHeight(125)



        self.balance_widget = LSBalanceTable()
        self.accountSummaryLayout.addWidget(self.balance_widget)

        # self.executions_table = ExecutionsTable()
        # self.executionsLayout.addWidget(self.balance_widget)

        # self.reservation_widget = ReservationWidget()
        # self.reservationLayout.addWidget(self.reservation_widget)
        self.setup_reservation_tab()
        self.setup_trades_tab()
        # self.tradesTable = TradesTable()
        # self.tradesTabLayout.addWidget(self.tradesTable)

    def _init_right_panel(self):
        self.time_sales_controller = TimeSalesController(self.tableTimeSales)
        self.symbolSummary = SymbolSummaryWidget(self)

        self.rightPanelLayout.insertWidget(
            self.rightPanelLayout.indexOf(self.tableWatchlist),
            self.symbolSummary,
        )

    async def init_my_order_store(self):
        orders = await self.order_api.get_open_orders(self.account_id)

        self.my_order_store.clear()
        for o in orders:
            self.my_order_store.add_order(o)

        print(self.my_order_store.get_my_orders())

    def set_qty(self, value: int):
        self.spinQty.setValue(value)

    def _tune_splitters(self):
        self.splitterRoot.setStretchFactor(0, 5)
        self.splitterRoot.setStretchFactor(1, 5)

        # 🔥 여기 핵심
        self.splitterLeft.setStretchFactor(0, 2)  # 상단 요약 ↓
        self.splitterLeft.setStretchFactor(1, 6)  # 포지션 테이블 ↑↑
        self.splitterLeft.setStretchFactor(2, 2)  # 보호 패널 ↓

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
        self.enqueue_async(self._load_initial_executions())
        self.enqueue_async(self.init_my_order_store())

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

        self.current_symbol = symbol

        # OrderBook View (로컬 UI)
        self.orderbook.set_symbol(symbol, tick_size=tick_size)

        # Price
        self.price_controller.set_symbol(symbol)
        self.price_controller.reset()

        # 🔥 OrderBook WS / REST 연동 (반드시 await)
        await self.orderbook_controller.set_symbol(symbol)

        # Time & Sales
        self.time_sales_controller.clear()

        # 요약 패널
        if hasattr(self, "selected_ls_row"):
            self.symbolSummary.update_ls_symbol(self.selected_ls_row)

        pos = await self.ls_account_api.get_position(self.account_id, symbol)
        if pos:
            self.on_position_selected(pos)

    def on_price_event(self, event: dict):
        etype = event.get("event_type")
        if etype == "PRICE":
            self.on_price_tick(event)

        elif etype == "ORDERBOOK":
            self.orderbook_controller.on_orderbook_event(event)

    def on_price_tick(self, event: dict):
        symbol = event.get("symbol")
        price = event.get("price")

        # 1️⃣ WatchList
        if hasattr(self, "ls_watchlist_controller"):
            self.ls_watchlist_controller.update_price(symbol, price)

        # 2️⃣ OrderBook 현재가만 갱신
        if (
                self.orderbook_controller.current_symbol == symbol
                and price is not None
        ):
            self.orderbook_controller.view.update_ls_price(price)

    def on_close_current_symbol(self):
        self.enqueue_async(self._close_current_symbol_worker())

    def on_close_all_positions(self):
        self.enqueue_async(self._close_all_positions_worker())

    def on_auto_center_changed(self, state: int):
        enabled = (state == Qt.CheckState.Checked.value)
        self.orderbook.auto_center_enabled = enabled

    async def _close_current_symbol_worker(self):
        symbol = self.current_symbol
        if not symbol:
            return

        pos = await self.ls_account_api.get_position(self.account_id, symbol)
        if not pos:
            QMessageBox.information(self, "알림", "청산할 포지션이 없습니다.")
            return

        qty_raw = pos.get("qty", 0)
        if not qty_raw:
            QMessageBox.information(self, "알림", "청산할 포지션이 없습니다.")
            return

        qty = abs(qty_raw)
        close_side = "SELL" if qty_raw > 0 else "BUY"  # ✅ 부호로 결정

        self.order_controller.place_market_close(
            symbol=symbol,
            side=close_side,
            qty=qty,
        )

    async def _close_all_positions_worker(self):
        positions = await self.ls_account_api.get_positions(self.account_id)

        if not positions:
            QMessageBox.information(self, "알림", "청산할 포지션이 없습니다.")
            return

        for pos in positions:
            qty_raw = pos.get("qty", 0)
            if qty_raw == 0:
                continue

            symbol = pos["symbol"]
            qty = abs(qty_raw)
            side = "SELL" if qty_raw > 0 else "BUY"

            # 🔥 시장가 청산
            self.order_controller.place_market_close(
                symbol=symbol,
                side=side,
                qty=qty,
                # source="UI:ALL_CLOSE"
            )

        self.safe_ui(
            self.show_toast,
            "🚨 전종목 청산 요청 완료"
        )

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

    def on_favorite_toggled(self, symbol: str):
        try:
            # 현재 즐겨찾기 목록
            favorites = {f["symbol_code"] for f in self.favorite_api.list()}

            if symbol in favorites:
                self.favorite_api.remove(symbol)
            else:
                self.favorite_api.add(symbol)

            # ⭐ 모든 UI 동기화
            self._apply_favorites_ui()

        except Exception as e:
            print("[Favorite] toggle failed:", e)

    def on_favorite_remove(self, symbol: str):
        try:
            favorites = {f["symbol_code"] for f in self.favorite_api.list()}

            if symbol in favorites:
                self.favorite_api.remove(symbol)
                self._apply_favorites_ui()

        except Exception as e:
            print("[Favorite] remove failed:", e)

    def _apply_favorites_ui(self):
        """
        현재 favorite_api 상태를 기준으로
        모든 UI(FavoriteBar, WatchList)를 동기화
        """
        favs = {fav["symbol_code"] for fav in self.favorite_api.list()}

        # 1️⃣ FavoriteBar
        self.favoriteBar.clear()
        for symbol in favs:
            self.favoriteBar.add_symbol(symbol)

        # 2️⃣ WatchList ⭐
        self.ls_watchlist_controller.set_favorites(favs)

    def on_position_selected(self, pos: dict):
        enriched = {
            **pos,
            "account_id": self.account_id,
        }

        # 🔥 1. 보호 패널 완전 초기화
        self.protection_panel.clear()

        # 🔥 2. 포지션 정보 로드
        self.protection_panel.load_position(enriched)
        self.orderbook.renderer.set_position_side(pos["side"])
        # 🔥 3. 서버에서 보호주문 조회
        self.order_controller.load_protections(pos["symbol"])

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

            # 2️⃣ OrderBook용 my_orders 생성 (엔진 기준 정규화)
            my_orders = {"SELL": {}, "BUY": {}}

            engine = self.orderbook.engine
            for o in orders:
                raw_price = float(o["price"])
                side = o["side"]

                # ✅ 엔진과 100% 동일한 price key
                price = engine.normalize_price(raw_price)

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
            self.safe_ui(
                self.balance_widget.update_balance,
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

    def setup_trades_tab(self):
        # 체결내역 테이블
        self.tradesTable = TradesTable()
        # 버튼 바
        self.tradesActionBar = QWidget()
        bar = QHBoxLayout(self.tradesActionBar)
        bar.setContentsMargins(6, 6, 6, 6)
        bar.setSpacing(8)

        self.btnTradeDeleteSelected = QPushButton("선택삭제")
        self.btnTradeDeleteAll = QPushButton("전체삭제")

        self.btnTradeDeleteSelected.clicked.connect(
            self.tradesTable.delete_selected_trades
        )
        self.btnTradeDeleteAll.clicked.connect(
            self.tradesTable.clear_all_trades
        )

        for btn in (
                self.btnTradeDeleteSelected,
                self.btnTradeDeleteAll,
        ):
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        bar.addStretch()
        bar.addWidget(self.btnTradeDeleteSelected)
        bar.addWidget(self.btnTradeDeleteAll)

        self.tradesTabLayout.addWidget(self.tradesActionBar)
        self.tradesTabLayout.addWidget(self.tradesTable)

    async def cancel_symbol_reservations(self):
        symbol = self.current_symbol
        await self.api.cancel_reservations(scope="SYMBOL", symbol=symbol)

    def on_execution_received(self, event: dict):
        exec_type = event.get("exec_type")
        if exec_type == "TRADE":
            self.time_sales_controller.on_trade(event)
            # 🔥 0.8초 후 계좌 재조회
            QTimer.singleShot(
                800,
                lambda: self.enqueue_async(self.fetch_account_state())
            )
        elif exec_type == "STATUS":
            self.reservation_controller.on_status_event(event)

    async def load_fx_rates(self):
        global_rates.FX_RATES = await self.api.get("/ls/futures/fx/rates")

    async def _load_initial_executions(self):
        try:
            executions = await self.api.get_executions(self.account_id)

            # 최초 1회만 clear
            self.tradesTable.setRowCount(0)

            self.last_exec_time = None

            # ⚠️ 서버 응답이 최신순인지 확인 필요
            # 최신순이면 reversed()
            for exec in reversed(executions):
                exec_time = datetime.fromisoformat(exec["created_at"])

                self.tradesTable.append_trade(
                    symbol=exec["symbol"],
                    side=exec["side"],
                    qty=exec["qty"],
                    price=exec["price"],
                    status="완료" if exec["exec_type"] == "TRADE" else "취소",
                    trade_time=exec_time,
                )

                if self.last_exec_time is None or exec_time > self.last_exec_time:
                    self.last_exec_time = exec_time

            # 🔥 히스토리 로딩 끝난 뒤 SSE 연결
            # self._start_execution_sse()

        except Exception as e:
            print("[Executions] initial load failed:", e)

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

            self._apply_favorites_ui()
        except Exception as e:
            print("[Favorite] load failed:", e)

    def _reload_protections(self, symbol: str):
        self.order_controller.load_protections(symbol)

    # ui/main_window.py

    def _place_market(self, side: str):
        if not self.current_symbol:
            return

        qty = 1
        # qty = self.spinQty.value()
        # if qty <= 0:
        #     return

        # 실제 주문
        self.order_controller.place_market_from_book(
            side=side,
            qty=qty,
        )

        # UX 피드백 (선택)
        if hasattr(self, "orderbook"):
            self.orderbook.flash_execution(
                price=self.orderbook.center_price,
                side=side
            )

    # =====================================================
    # CLOCK
    # =====================================================
    def _on_clock_tick(self):
        self.enqueue_async(self.update_ls_clock())

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

