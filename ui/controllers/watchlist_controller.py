# ui/controllers/watchlist_controller.py

from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class WatchlistController:
    def __init__(self, table):
        self.table = table
        self.row_map = {}          # symbol_code -> row index
        self.prev_price = {}       # symbol_code -> last price

        self._setup_table()

    def _setup_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["종목명", "코드", "현재가", "전일대비"]
        )

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.horizontalHeader().setFixedHeight(26)

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

    # ✅ MainWindow가 기대하는 메서드
    def load_default(self):
        rows = [
            ("코스피 선물", "101WC000", 469.40, +2.35),
            ("S&P 500", "ESZ25", 6658.75, -0.10),
            ("미니항셍", "HMHU25", 26105, +1.20),
            ("유로화", "UROZ25", 1.17220, -0.04),
            ("나스닥100", "NQZ25", 24590.75, +0.18),
            ("금선물", "GCZ25", 3777.5, -0.16),
        ]

        self.table.setRowCount(len(rows))

        for r, (name, code, price, diff) in enumerate(rows):
            self.row_map[code] = r
            self.prev_price[code] = price

            self.table.setItem(r, 0, self._item(name, "white"))
            self.table.setItem(r, 1, self._item(code, "#cccccc"))
            self.table.setItem(r, 2, self._item(f"{price:,.2f}", "#FFD700", Qt.AlignmentFlag.AlignRight))

            arrow, color = self._diff_style(diff)
            self.table.setItem(
                r, 3,
                self._item(f"{arrow} {diff:+.2f}".strip(), color, Qt.AlignmentFlag.AlignRight)
            )

    def update_price(self, code: str, last_price: float):
        if code not in self.row_map:
            return

        row = self.row_map[code]
        prev = self.prev_price.get(code, last_price)
        diff = last_price - prev

        price_item = self.table.item(row, 2)
        diff_item = self.table.item(row, 3)

        if price_item:
            price_item.setText(f"{last_price:,.2f}")
            price_item.setForeground(
                QColor("#ff4d4d" if diff > 0 else "#4da6ff" if diff < 0 else "#FFD700")
            )

        if diff_item:
            arrow, color = self._diff_style(diff)
            diff_item.setText(f"{arrow} {diff:+.2f}".strip())
            diff_item.setForeground(QColor(color))

        self.prev_price[code] = last_price

    # --------------------
    # helpers
    # --------------------
    def _item(self, text, color, align=None):
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        if align:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _diff_style(self, diff):
        if diff > 0:
            return "▲", "#ff4d4d"
        elif diff < 0:
            return "▼", "#4da6ff"
        return "", "#aaaaaa"
