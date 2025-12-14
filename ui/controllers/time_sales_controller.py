# ui/controllers/time_sales_controller.py
from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime


class TimeSalesController:
    def __init__(self, table):
        self.table = table
        self.max_rows = 200

        self._setup()

    def _setup(self):
        t = self.table
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["Time", "Price", "Qty", "Side"])

        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        h = t.horizontalHeader()
        h.setStretchLastSection(True)
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def clear(self):
        self.table.setRowCount(0)

    def on_trade(self, trade: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # -------------------------
        # Time 처리
        # -------------------------
        ts = trade.get("ts")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = "--:--:--"
        else:
            time_str = "--:--:--"

        # -------------------------
        # 값 추출
        # -------------------------
        price = trade.get("price", 0)
        qty = trade.get("qty", 0)
        side = trade.get("side", "")

        # -------------------------
        # 아이템 생성
        # -------------------------
        item_time = QTableWidgetItem(time_str)
        item_price = QTableWidgetItem(f"{price:.2f}")
        item_qty = QTableWidgetItem(f"{qty:g}")
        item_side = QTableWidgetItem(side)

        # 정렬/정렬 방지
        for it in (item_time, item_price, item_qty, item_side):
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # -------------------------
        # 색상 처리
        # -------------------------
        if side == "BUY":
            color = "#2ecc71"   # 초록
        else:
            color = "#e74c3c"   # 빨강

        item_price.setForeground(Qt.GlobalColor.green if side == "BUY" else Qt.GlobalColor.red)
        item_side.setForeground(Qt.GlobalColor.green if side == "BUY" else Qt.GlobalColor.red)

        # -------------------------
        # 테이블 삽입
        # -------------------------
        self.table.setItem(row, 0, item_time)
        self.table.setItem(row, 1, item_price)
        self.table.setItem(row, 2, item_qty)
        self.table.setItem(row, 3, item_side)

        # 최신 체결 위로
        self.table.scrollToTop()


