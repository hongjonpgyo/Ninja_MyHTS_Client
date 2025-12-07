from PyQt6 import QtWidgets, QtGui, QtCore

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
