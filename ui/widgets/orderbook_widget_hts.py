from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

from ui.settings.trade_setting import OrderClickMode
from ui.widgets.orderbook_delegate import OrderbookDelegate

from config.settings import LMT_BUY_COL, LMT_SELL_COL, MIT_SELL_COL, MIT_BUY_COL

class OrderbookWidgetHTS:
    def __init__(self, table, trade_setting, depth_rows=10):
        self.table = table
        self.depth_rows = depth_rows
        self.trade_setting = trade_setting


        self.total_rows = depth_rows * 2 + 1
        self.mid_row = depth_rows
        self.PRICE_COL = 4

        # delegate (⚠️ 테두리 그리는 로직은 delegate에서 제거되어 있어야 함)
        self.delegate = OrderbookDelegate(table)
        self.delegate.mid_row = self.mid_row
        self.table.setItemDelegate(self.delegate)

        self.setup()

        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

    # ---------------------------------------------------------
    # Table Setup
    # ---------------------------------------------------------
    def setup(self):
        self.table.setRowCount(self.total_rows)
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "MIT", "매도", "건수", "잔량",
            "가격",
            "잔량", "건수", "매수", "MIT"
        ])

        # 🔥 다크 HTS 톤 (선 없음)
        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #1e1e1e;
            gridline-color: #2a2a2a;
            color: #e0e0e0;
        }
        QTableWidget::item {
            padding: 4px;
        }
        QHeaderView::section {
            background-color: #2b2b2b;
            color: #dddddd;
            border: none;
            padding: 4px;
        }
        """)

        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            if col == self.PRICE_COL:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    # ---------------------------------------------------------
    # Update Depth
    # ---------------------------------------------------------
    def update_depth(self, bids, asks, mit_buys=None, mit_sells=None):
        mit_buys = mit_buys or {}
        mit_sells = mit_sells or {}

        asks_sorted = sorted(asks, key=lambda x: x["price"])
        bids_sorted = sorted(bids, key=lambda x: x["price"], reverse=True)

        pivot_price = bids_sorted[0]["price"] if bids_sorted else None

        max_qty = max(
            [x["db_all_qty"] for x in asks_sorted + bids_sorted] or [1]
        )

        # ----------------------------
        # ASK (위)
        # ----------------------------
        for i in range(self.depth_rows):
            row = self.mid_row - 1 - i

            if i < len(asks_sorted):
                a = asks_sorted[i]
                price = a["price"]
                qty = a["db_all_qty"]
                count = a["db_all_count"]

                self._set(row, 0, mit_sells.get(price, ""))
                self._set(row, 1, "")
                self._set(row, 2, count)
                self._set(row, 3, qty)
                self._set(row, 4, f"{price:,.2f}")

                self._clear_cols(row, [5, 6, 7, 8])
                self._apply_ask_depth(row, qty, max_qty)
            else:
                self._clear_row(row)

        # ----------------------------
        # Pivot Row (중앙 기준 면)
        # ----------------------------
        self._row_bg(self.mid_row, QColor("#2b2b2b"))
        self._set(self.mid_row, 4, f"{pivot_price:,.2f}" if pivot_price else "")

        pivot_item = self.table.item(self.mid_row, self.PRICE_COL)
        if pivot_item:
            pivot_item.setForeground(QColor("#f1c40f"))
            font = pivot_item.font()
            font.setBold(True)
            pivot_item.setFont(font)

        self._clear_cols(self.mid_row, [0,1,2,3,5,6,7,8])

        # ----------------------------
        # BID (아래)
        # ----------------------------
        for i in range(self.depth_rows):
            row = self.mid_row + 1 + i

            if i < len(bids_sorted):
                b = bids_sorted[i]
                price = b["price"]
                qty = b["db_all_qty"]
                count = b["db_all_count"]

                self._clear_cols(row, [0,1,2,3])
                self._set(row, 4, f"{price:,.2f}")
                self._set(row, 5, qty)
                self._set(row, 6, count)
                self._set(row, 7, "")
                self._set(row, 8, mit_buys.get(price, ""))

                self._apply_bid_depth(row, qty, max_qty)
            else:
                self._clear_row(row)

        # Delegate best rows (선 없음)
        self.delegate.best_ask_row = self.mid_row - 1 if asks_sorted else None
        self.delegate.best_bid_row = self.mid_row + 1 if bids_sorted else None

        self.table.viewport().update()

    # ---------------------------------------------------------
    # Depth Coloring (면 기반)
    # ---------------------------------------------------------
    def _apply_ask_depth(self, row, qty, max_qty):
        # ✅ 항상 초기화
        self._cell_bg(row, 3, QColor("#1e1e1e"))
        if qty <= 0:
            return
        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)
        self._cell_bg(row, 3, QColor(231, 76, 60, alpha))  # red

    def _apply_bid_depth(self, row, qty, max_qty):
        # ✅ 항상 초기화
        self._cell_bg(row, 3, QColor("#1e1e1e"))
        if qty <= 0:
            return
        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)
        self._cell_bg(row, 5, QColor(46, 204, 113, alpha))  # green

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _cell_bg(self, row, col, color):
        item = self.table.item(row, col)
        if item:
            item.setBackground(QBrush(color))

    def _row_bg(self, row, color):
        for c in range(self.table.columnCount()):
            item = self.table.item(row, c)
            if not item:
                item = QTableWidgetItem("")
                self.table.setItem(row, c, item)
            item.setBackground(QBrush(color))

    def _clear_cols(self, row, cols):
        for c in cols:
            item = self.table.item(row, c)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#1e1e1e")))

    def _set(self, r, c, val):
        item = self.table.item(r, c)
        if not item:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, c, item)

        item.setText(str(val))
        item.setForeground(QBrush(QColor("#e0e0e0")))

        if c == self.PRICE_COL:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

    def _clear_row(self, r):
        for c in range(self.table.columnCount()):
            item = self.table.item(r, c)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#1e1e1e")))

    def on_cell_clicked(self, row, col):
        self._handle_orderbook_click(row, col, click_type="single")

    def on_cell_double_clicked(self, row, col):
        self._handle_orderbook_click(row, col, click_type="double")

    def _increase_my_order(self, symbol, price, side):
        book = self.my_orders.setdefault(symbol, {})
        side_map = book.setdefault(side, {})
        side_map[price] = side_map.get(price, 0) + 1

    def _update_orderbook_my_count(self, symbol, price, side):
        row = self._find_row_by_price(price)
        if row is None:
            return

        col = COL_SELL_CNT if side == "SELL" else COL_BUY_CNT

        cnt = self.my_orders[symbol][side][price]

        item = self.tableOrderbook.item(row, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableOrderbook.setItem(row, col, item)

        item.setText(str(cnt))
        item.setForeground(QColor("#ffd54f"))  # 내 주문 강조

    def _place_entry_from_orderbook(self, row, side):
        price = self._get_price_from_row(row)
        qty = self.order_panel.get_qty()

        self.main_window.enqueue_async(
            self.main_window.order_controller.place_limit_order(
                symbol=self.current_symbol,
                side=side,
                price=price,
                qty=qty
            )
        )

        self._increase_my_order(self.current_symbol, price, side)
        self._update_orderbook_my_count(self.current_symbol, price, side)

    def _handle_orderbook_click(self, row, col, click_type):
        mode = self.trade_setting.order_click_mode
        print(mode)
        if mode == OrderClickMode.SINGLE and click_type != "single":
            return
        if mode == OrderClickMode.DOUBLE and click_type != "double":
            return

        # if col == LMT_SELL_COL:
        #     self.place_order(row, "SELL")
        # elif col == LMT_BUY_COL:
        #     self.place_order(row, "BUY")

