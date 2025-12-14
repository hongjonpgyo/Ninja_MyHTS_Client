from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

from config.colors import ORDERBOOK_COLORS
from ui.utils.color_utils import make_color_with_intensity
from ui.widgets.orderbook_delegate import OrderbookDelegate


def fmt_number(x):
    try:
        v = float(x)
        if v == 0:
            return "0"
        # 소수점 8자리 유지 (Binance 수량 기준)
        s = f"{v:.8f}"
        return s.rstrip("0").rstrip(".")  # 불필요한 0 제거
    except:
        return str(x)



class OrderbookWidget:

    def __init__(self, table):
        self.table = table
        self.delegate = OrderbookDelegate(table)
        self.table.setItemDelegate(self.delegate)
        self.setup()

    def setup(self):

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Bin Bid", "DB All", "My Bid",
            "Price",
            "My Ask", "DB All", "Bin Ask"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(20)

        for r in range(20):
            for c in range(7):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor(ORDERBOOK_COLORS["text"])))
                self.table.setItem(r, c, item)

    # -------------------------------------------------------------
    # 🔥 v3 Orderbook 표시
    # -------------------------------------------------------------
    def update_depth(self, bids, asks):

        rows = 20

        # → 수량 최대값을 구해 intensity 계산에 사용
        max_bid_qty = max((b["binance_qty"] + b["db_all_qty"] + b["db_my_qty"] for b in bids), default=1)
        max_ask_qty = max((a["binance_qty"] + a["db_all_qty"] + a["db_my_qty"] for a in asks), default=1)

        for i in range(rows):

            # -------------------- BIDS --------------------
            if i < len(bids):
                b = bids[i]
                self._set(i, 0, b["binance_qty"])
                self._set(i, 1, b["db_all_qty"])
                self._set(i, 2, b["db_my_qty"])
                self._set(i, 3, f"{b['price']:,.2f}")

                self._apply_bid_color(i, b, max_bid_qty)

            else:
                self._clear_bid(i)

            # -------------------- ASKS --------------------
            if i < len(asks):
                a = asks[i]
                self._set(i, 3, f"{a['price']:,.2f}")
                self._set(i, 4, a["db_my_qty"])
                self._set(i, 5, a["db_all_qty"])
                self._set(i, 6, a["binance_qty"])

                self._apply_ask_color(i, a, max_ask_qty)

            else:
                self._clear_ask(i)

        # 🔥 Best Bid row 찾기
        if bids:
            best_bid_price = max(b['price'] for b in bids)
            best_bid_row = next(i for i, b in enumerate(bids) if b['price'] == best_bid_price)
        else:
            best_bid_row = None

        # 🔥 Best Ask row 찾기
        if asks:
            best_ask_price = min(a['price'] for a in asks)
            best_ask_row = next(i for i, a in enumerate(asks) if a['price'] == best_ask_price)
        else:
            best_ask_row = None

        self.delegate.best_bid_row = best_bid_row
        self.delegate.best_ask_row = best_ask_row

        self.table.viewport().update()

    def _clear_all_borders(self):
        for r in range(20):
            for c in range(7):
                item = self.table.item(r, c)
                if item:
                    item.setStyleSheet("")


    # -------------------------------------------------------------
    # 🔵 색상 적용 (BID)
    # -------------------------------------------------------------
    def _apply_bid_color(self, row, bid, max_qty):
        qty = bid["binance_qty"] + bid["db_all_qty"] + bid["db_my_qty"]
        intensity = qty / max_qty

        bg = make_color_with_intensity(
            ORDERBOOK_COLORS["bid_base"],
            intensity,
            ORDERBOOK_COLORS["bid_min_alpha"],
            ORDERBOOK_COLORS["bid_max_alpha"]
        )

        for c in range(0, 3):  # Bid 컬럼만 색 적용
            self.table.item(row, c).setBackground(QBrush(bg))

    # -------------------------------------------------------------
    # 🔴 색상 적용 (ASK)
    # -------------------------------------------------------------
    def _apply_ask_color(self, row, ask, max_qty):
        qty = ask["binance_qty"] + ask["db_all_qty"] + ask["db_my_qty"]
        intensity = qty / max_qty

        bg = make_color_with_intensity(
            ORDERBOOK_COLORS["ask_base"],
            intensity,
            ORDERBOOK_COLORS["ask_min_alpha"],
            ORDERBOOK_COLORS["ask_max_alpha"]
        )

        for c in range(4, 7):  # Ask 컬럼만 색 적용
            self.table.item(row, c).setBackground(QBrush(bg))

    # -------------------------------------------------------------
    # 헬퍼 함수들
    # -------------------------------------------------------------
    def _set(self, r, c, val):
        item = self.table.item(r, c)
        txt = fmt_number(val)

        if item:
            item.setText(txt)
        else:
            new_item = QTableWidgetItem(txt)
            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, c, new_item)

    def _clear_bid(self, r):
        for c in range(0, 4):
            self._set(r, c, "")
            self.table.item(r, c).setBackground(QBrush(Qt.GlobalColor.transparent))

    def _clear_ask(self, r):
        for c in range(3, 7):
            self._set(r, c, "")
            self.table.item(r, c).setBackground(QBrush(Qt.GlobalColor.transparent))


    def _highlight_best_bid(self, row):
        color = ORDERBOOK_COLORS["best_bid_border"]
        style = f"border-right: 2px solid {color}; border-left: 2px solid {color};"
        for c in range(0, 3):  # Bid 컬럼만
            self._apply_style(row, c, style)


    def _highlight_best_ask(self, row):
        color = ORDERBOOK_COLORS["best_ask_border"]
        style = f"border-right: 2px solid {color}; border-left: 2px solid {color};"
        for c in range(4, 6 + 1):  # Ask 컬럼 4~6
            self._apply_style(row, c, style)

    def _apply_style(self, r, c, style):
        item = self.table.item(r, c)
        if item:
            item.setData(Qt.ItemDataRole.UserRole, style)  # 저장
            item.setStyleSheet(style)

