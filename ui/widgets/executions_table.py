from datetime import datetime

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem
import time

class ExecutionsTable(QtWidgets.QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ["Time", "Symbol", "Side", "Price", "Qty", "Fee", "Type"]
        )
        self.horizontalHeader().setStretchLastSection(True)

        # 마지막 데이터 수 tracking → 신규 체결 감지용
        self.last_row_count = 0

    # ===================================================================
    def update_table(self, executions: list[dict]):
        """
        executions: [
            {"time": "...", "symbol": "...", "side": "...", ...},
            ...
        ]
        """
        if not executions:
            return

        new_row_count = len(executions)
        is_new_data = new_row_count > self.last_row_count

        self.setRowCount(new_row_count)

        for row, ex in enumerate(executions):
            self._set_item(row, 0, ex["created_at"])
            self._set_item(row, 1, ex["symbol"])
            self._set_item(row, 2, ex["side"])
            self._set_item(row, 3, f"{ex['price']}")
            self._set_item(row, 4, f"{ex['qty']}")
            self._set_item(row, 5, f"{ex['fee']}")
            self._set_item(row, 6, ex["type"])

            # 🎨 컬러 적용
            self._color_side(row, ex["side"])

        # 신규 체결 깜빡임 효과
        if is_new_data:
            self._highlight_new_row(new_row_count - 1)

        self.last_row_count = new_row_count

    # ===================================================================
    def _set_item(self, row, col, text):
        item = QtWidgets.QTableWidgetItem(str(text))
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, col, item)

    # ===================================================================
    def _color_side(self, row, side):
        """ BUY/SELL 색상 처리 """
        item = self.item(row, 2)
        if not item:
            return

        if side == "BUY":
            item.setForeground(QtGui.QColor("#2ecc71"))   # 청록
        else:
            item.setForeground(QtGui.QColor("#e74c3c"))   # 빨강

    # ===================================================================
    def _highlight_new_row(self, row):
        """ 신규 체결이 들어오면 배경이 0.3초간 노란색 → 원래색으로 """
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if not item:
                continue
            item.setBackground(QtGui.QColor("#FFF59D"))  # 연노랑

        # 0.3초 후 원래색으로 복귀
        QtCore.QTimer.singleShot(300, lambda: self._clear_highlight(row))

    def _clear_highlight(self, row):
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QtGui.QColor("#FFFFFF"))

    def append_row(self, ex: dict):
        row = self.rowCount()
        self.insertRow(row)

        self._set_item(row, 0, ex["created_at"])
        self._set_item(row, 1, ex["symbol"])
        self._set_item(row, 2, ex["side"])
        self._set_item(row, 3, ex["price"])
        self._set_item(row, 4, ex["qty"])
        self._set_item(row, 5, ex.get("fee", 0))
        self._set_item(row, 6, ex.get("type", "AUTO"))

        self._color_side(row, ex["side"])
        self._highlight_new_row(row)

    def append_tick(self, price: float, side: str):
        row = self.rowCount()
        self.insertRow(row)

        time_str = datetime.now().strftime("%H:%M:%S")

        self.setItem(row, 0, QTableWidgetItem(time_str))
        self.setItem(row, 1, QTableWidgetItem(f"{price:,.2f}"))
        self.setItem(row, 2, QTableWidgetItem("1"))
        self.setItem(row, 3, QTableWidgetItem(side))

        # 색상
        if side == "BUY":
            color = QColor("#ff4d4d")
        else:
            color = QColor("#4da6ff")

        for c in range(4):
            self.item(row, c).setForeground(color)
            self.item(row, c).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 최근 100개만 유지
        if self.rowCount() > 100:
            self.removeRow(0)

    def append_trade(self, trade: dict):
        """
        trade = {
            symbol, price, qty, side, ts
        }
        """
        row = self.rowCount()
        self.insertRow(row)

        ts = trade.get("ts", 0)
        price = trade["price"]
        qty = trade["qty"]
        side = trade["side"]

        time_str = time.strftime(
            "%H:%M:%S",
            time.localtime(ts / 1000)
        )

        self.setItem(row, 0, QTableWidgetItem(time_str))
        self.setItem(row, 1, QTableWidgetItem(side))
        self.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
        self.setItem(row, 3, QTableWidgetItem(f"{qty:.4f}"))

        # 색상
        color = QColor("#2ecc71") if side == "BUY" else QColor("#e74c3c")
        for c in range(4):
            self.item(row, c).setForeground(color)
            self.item(row, c).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 최근 N개 유지
        if self.rowCount() > 200:
            self.removeRow(0)

        self.scrollToBottom()