from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView, QTableWidget, QAbstractItemView
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

from ui.settings.trade_setting import OrderClickMode
from ui.widgets.orderbook_delegate import OrderbookDelegate
from config.ls_settings import (
    LMT_BUY_COL, LMT_SELL_COL,
    MIT_SELL_COL, MIT_BUY_COL,
    COL_SELL_CNT, COL_BUY_CNT
)
from config.ls_settings import ORDERBOOK_DEPTH
from ui.widgets.checkbox_header import CheckBoxHeader

class OrderbookWidgetHTS:
    def __init__(self, table, trade_setting, main_window, depth_rows=ORDERBOOK_DEPTH):
        self.table = table
        self.trade_setting = trade_setting
        self.main_window = main_window
        self.depth_rows = depth_rows

        self.total_rows = depth_rows * 2 + 1
        self.mid_row = depth_rows
        self.PRICE_COL = 4
        self.orderbook_center_lock = False

        # 🔥 내 주문 저장 구조
        # { symbol: { side: { price: count } } }
        self.my_orders = {}

        self.delegate = OrderbookDelegate(table)
        self.delegate.mid_row = self.mid_row
        self.table.setItemDelegate(self.delegate)

        self.setup()

        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)



    # =====================================================
    # Table Setup
    # =====================================================
    def setup(self):
        PRICE_COL_WIDTH = 120
        self.table.setRowCount(self.total_rows)
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "MIT", "매도", "건수", "잔량",
            "고정",
            "잔량", "건수", "매수", "MIT"
        ])

        # header = self.table.horizontalHeader()
        header = CheckBoxHeader(Qt.Orientation.Horizontal, self.table)
        self.table.setHorizontalHeader(header)
        header.toggled.connect(self.on_center_lock_toggled)

        for col in range(self.table.columnCount()):
            if col == self.PRICE_COL:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(col, PRICE_COL_WIDTH)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 포커스 차단
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection  # 선택 차단
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers  # 편집 차단
        )
        self.table.setTabKeyNavigation(False)  # 탭 이동 차단
        self.table.setMouseTracking(True)  # hover만 허용

    def on_center_lock_toggled(self, enabled: bool):
        self.orderbook_center_lock = enabled

    def update_orderbook(self, current_price_row: int):
        if not self.orderbook_center_lock:
            return

        item = self.table.item(current_price_row, 4)
        if not item:
            return

        self.table.scrollToItem(
            item,
            self.table.ScrollHint.PositionAtCenter
        )

    # =====================================================
    # Depth Update (기존 로직 유지)
    # =====================================================
    def update_depth(self, bids, asks, mit_buys=None, mit_sells=None):
        mit_buys = mit_buys or {}
        mit_sells = mit_sells or {}

        asks = sorted(asks, key=lambda x: x["price"])
        bids = sorted(bids, key=lambda x: x["price"], reverse=True)

        pivot_price = bids[0]["price"] if bids else None
        max_qty = max([x["db_all_qty"] for x in asks + bids] or [1])

        # ASK
        for i in range(self.depth_rows):
            row = self.mid_row - 1 - i
            if i < len(asks):
                a = asks[i]
                self._set(row, 3, a["db_all_qty"])
                self._set(row, 4, f"{a['price']:,.2f}")
                self._apply_ask_depth(row, a["db_all_qty"], max_qty)
            else:
                self._clear_row(row)

        # Pivot
        self._row_bg(self.mid_row, QColor("#2b2b2b"))
        self._set(self.mid_row, 4, f"{pivot_price:,.2f}" if pivot_price else "")

        # BID
        for i in range(self.depth_rows):
            row = self.mid_row + 1 + i
            if i < len(bids):
                b = bids[i]
                self._set(row, 4, f"{b['price']:,.2f}")
                self._set(row, 5, b["db_all_qty"])
                self._apply_bid_depth(row, b["db_all_qty"], max_qty)
            else:
                self._clear_row(row)

        self.table.viewport().update()

        # ✅ 중앙 고정 (헤더 체크 ON일 때만 동작)
        self.update_orderbook(self.mid_row)

    # =====================================================
    # 주문 증가 / 감소 (🔥 핵심)
    # =====================================================
    def increase_my_order(self, symbol, price, side):
        book = self.my_orders.setdefault(symbol, {})
        side_map = book.setdefault(side, {})
        side_map[price] = side_map.get(price, 0) + 1
        self._render_my_order(symbol, price, side)

    def decrease_my_order(self, symbol, price, side):
        book = self.my_orders.get(symbol, {})
        side_map = book.get(side, {})
        if price not in side_map:
            return

        side_map[price] -= 1
        if side_map[price] <= 0:
            del side_map[price]

        self._render_my_order(symbol, price, side)

    # =====================================================
    # Orderbook 내 표시
    # =====================================================
    def _render_my_order(self, symbol, price, side):
        row = self._find_row_by_price(price)
        if row is None:
            return

        col = COL_SELL_CNT if side == "SELL" else COL_BUY_CNT
        count = self.my_orders.get(symbol, {}).get(side, {}).get(price, 0)

        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

        if count > 0:
            item.setText(str(count))
            item.setForeground(QColor("#ffd54f"))  # 🔥 내 주문 강조
        else:
            item.setText("")

    def _find_row_by_price(self, price):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, self.PRICE_COL)
            if item and item.text().replace(",", "") == f"{price:.2f}":
                return r
        return None

    # =====================================================
    # Click Handling
    # =====================================================
    def on_cell_clicked(self, row, col):
        self._handle_click(row, col, "single")

    def on_cell_double_clicked(self, row, col):
        self._handle_click(row, col, "double")

    def _handle_click(self, row, col, click_type):
        mode = self.trade_setting.order_click_mode
        if mode == OrderClickMode.SINGLE and click_type != "single":
            return
        if mode == OrderClickMode.DOUBLE and click_type != "double":
            return

        if col == LMT_SELL_COL:
            self._place_order(row, "SELL")
        elif col == LMT_BUY_COL:
            self._place_order(row, "BUY")

    def _place_order(self, row, side):
        price_item = self.table.item(row, self.PRICE_COL)
        if not price_item:
            return

        price = float(price_item.text().replace(",", ""))
        qty = 1  # 오더북 클릭 기본 수량
        symbol = self.main_window.current_symbol

        # ✅ OrderController에 위임 (enqueue_async는 내부에서 처리)
        self.main_window.order_controller.place_limit_from_book(
            side=side,
            price=price,
            qty=qty
        )

        # ✅ 내 주문 카운트 증가 (UI 전용)
        self.increase_my_order(symbol, price, side)

    # =====================================================
    # Helpers (누락 방지)
    # =====================================================
    def _set(self, r, c, val):
        item = self.table.item(r, c)
        if not item:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, c, item)
        item.setText(str(val))

    def _clear_row(self, r):
        for c in range(self.table.columnCount()):
            item = self.table.item(r, c)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#1e1e1e")))

    def _cell_bg(self, row, col, color):
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

        item.setBackground(QBrush(color))

    def _row_bg(self, r, color):
        for c in range(self.table.columnCount()):
            item = self.table.item(r, c)
            if not item:
                item = QTableWidgetItem("")
                self.table.setItem(r, c, item)
            item.setBackground(QBrush(color))

    def _apply_ask_depth(self, row, qty, max_qty):
        # ✅ 항상 초기화
        self._cell_bg(row, 3, QColor("#1e1e1e"))

        # 🔥 방어 코드 (핵심)
        if qty <= 0 or max_qty <= 0:
            return

        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)

        self._cell_bg(row, 3, QColor(231, 76, 60, alpha))  # ASK red

    def _apply_bid_depth(self, row, qty, max_qty):
        # ✅ 항상 초기화
        self._cell_bg(row, 5, QColor("#1e1e1e"))

        if qty <= 0 or max_qty <= 0:
            return

        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)

        self._cell_bg(row, 5, QColor(46, 204, 113, alpha))  # BID green

