from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt


class OrderbookWidget:

    def __init__(self, table):
        self.table = table
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
                self.table.setItem(r, c, item)

    # -------------------------------------------------------------
    # 🔥 v3 Orderbook 표시
    # -------------------------------------------------------------
    def update_depth(self, bids, asks):

        rows = 20

        for i in range(rows):

            # -------------------- BIDS --------------------
            if i < len(bids):
                b = bids[i]
                self._set(i, 0, b["binance_qty"])
                self._set(i, 1, b["db_all_qty"])
                self._set(i, 2, b["db_my_qty"])
                self._set(i, 3, f"{b['price']:,.2f}")
            else:
                self._clear_bid(i)

            # -------------------- ASKS --------------------
            if i < len(asks):
                a = asks[i]
                self._set(i, 3, f"{a['price']:,.2f}")  # center price update
                self._set(i, 4, a["db_my_qty"])
                self._set(i, 5, a["db_all_qty"])
                self._set(i, 6, a["binance_qty"])
            else:
                self._clear_ask(i)

    # -------------------------------------------------------------
    # 헬퍼 함수: 셀 세팅
    # -------------------------------------------------------------
    def _set(self, r, c, val):
        item = self.table.item(r, c)
        if item:
            item.setText(str(val))
        else:
            self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def _clear_bid(self, r):
        for c in range(0, 4):
            self._set(r, c, "")

    def _clear_ask(self, r):
        for c in range(3, 7):
            self._set(r, c, "")
