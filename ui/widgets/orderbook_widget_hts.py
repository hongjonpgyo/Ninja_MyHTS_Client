from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

from ui.widgets.orderbook_delegate import OrderbookDelegate


class OrderbookWidgetHTS:

    def __init__(self, table, depth_rows=10):
        self.table = table
        self.depth_rows = depth_rows

        self.total_rows = depth_rows * 2 + 1
        self.mid_row = depth_rows

        # delegate
        self.delegate = OrderbookDelegate(table)
        self.delegate.mid_row = self.mid_row
        self.PRICE_COL = 4

        self.table.setItemDelegate(self.delegate)

        self.setup()

    # ---------------------------------------------------------
    # Table Setup
    # ---------------------------------------------------------
    def setup(self):
        self.table.setRowCount(self.total_rows)
        self.table.setColumnCount(9)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #444444;
            }
        """)

        self.table.setHorizontalHeaderLabels([
            "MIT", "매도", "건수", "잔량",
            "고정",
            "잔량", "건수", "매수", "MIT"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for r in range(self.total_rows):
            for c in range(9):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

    # ---------------------------------------------------------
    # Update Depth
    # ---------------------------------------------------------
    def update_depth(self, bids, asks, mit_buys=None, mit_sells=None):

        mit_buys = mit_buys or {}
        mit_sells = mit_sells or {}

        asks_sorted = sorted(asks, key=lambda x: x["price"])
        bids_sorted = sorted(bids, key=lambda x: x["price"], reverse=True)

        # Pivot
        pivot_price = bids_sorted[0]["price"] if bids_sorted else None

        # ----------------------------
        # ASK (위쪽)
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

                self._set(row, 5, "")
                self._set(row, 6, "")
                self._set(row, 7, "")
                self._set(row, 8, "")

                self._apply_ask_color(row, qty)
            else:
                self._clear_row(row)

        # ----------------------------
        # Pivot Row
        # ----------------------------
        self._set(self.mid_row, 4, f"{pivot_price:,.2f}" if pivot_price else "")
        self._apply_pivot_color(self.mid_row)

        for c in [0,1,2,3,5,6,7,8]:
            self._set(self.mid_row, c, "")
            self.table.item(self.mid_row, c).setBackground(QBrush(QColor("#FFF2A6")))

        # ----------------------------
        # BID (아래쪽)
        # ----------------------------
        for i in range(self.depth_rows):
            row = self.mid_row + 1 + i

            if i < len(bids_sorted):
                b = bids_sorted[i]
                price = b["price"]
                qty = b["db_all_qty"]
                count = b["db_all_count"]

                self._set(row, 0, "")
                self._set(row, 1, "")
                self._set(row, 2, "")
                self._set(row, 3, "")

                self._set(row, 4, f"{price:,.2f}")
                self._set(row, 5, qty)
                self._set(row, 6, count)
                self._set(row, 7, "")
                self._set(row, 8, mit_buys.get(price, ""))

                self._apply_bid_color(row, qty)
            else:
                self._clear_row(row)

        # Delegate highlight
        self.delegate.best_ask_row = self.mid_row - 1 if asks_sorted else None
        self.delegate.best_bid_row = self.mid_row + 1 if bids_sorted else None

        self.table.viewport().update()

    def _cell_bg(self, row, col, color):
        item = self.table.item(row, col)
        if item:
            item.setBackground(QBrush(color))


    # ---------------------------------------------------------
    # Color functions
    # ---------------------------------------------------------
    def _apply_ask_color(self, row, qty, max_qty=10):

        # 잔량이 0 → 흰색
        if qty <= 0:
            self._cell_bg(row, 2, QColor("#FFFFFF"))  # 건수
            self._cell_bg(row, 3, QColor("#FFFFFF"))  # 잔량
            return

        ratio = min(qty / max_qty, 1)
        base = QColor("#F6D6D6")
        strong = QColor("#EBA8A8")
        color = base if ratio < 0.3 else strong

        self._cell_bg(row, 2, color)  # 건수
        self._cell_bg(row, 3, color)  # 잔량

    def _apply_bid_color(self, row, qty, max_qty=10):

        if qty <= 0:
            self._cell_bg(row, 5, QColor("#FFFFFF"))  # 잔량
            self._cell_bg(row, 6, QColor("#FFFFFF"))  # 건수
            return

        ratio = min(qty / max_qty, 1)
        base = QColor("#D3E6F9")
        strong = QColor("#A6CCE8")
        color = base if ratio < 0.3 else strong

        self._cell_bg(row, 5, color)
        self._cell_bg(row, 6, color)


    def _apply_pivot_color(self, row):
        self._row_bg(row, QColor("#FFF2A6"))

    # ---------------------------------------------------------
    # Helper
    # ---------------------------------------------------------
    def _row_bg(self, row, color):
        for c in range(9):
            self.table.item(row, c).setBackground(QBrush(color))

    def _set(self, r, c, val):
        item = self.table.item(r, c)
        if not item:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, c, item)

        # 텍스트 세팅
        item.setText(str(val))

        # 글자 색상 — 전체 검정색
        item.setForeground(QBrush(QColor(0, 0, 0)))

        # 가격(고정) 컬럼만 Bold 처리
        if c == self.PRICE_COL:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        else:
            font = item.font()
            font.setBold(False)
            item.setFont(font)

    def _clear_row(self, r):
        for c in range(9):
            item = self.table.item(r, c)
            if item:
                item.setText("")
                item.setBackground(QBrush(QColor("#FFFFFF")))  # 투명 → 흰색


