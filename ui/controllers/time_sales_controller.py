from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from datetime import datetime


class TimeSalesController:
    def __init__(self, table):
        self.table = table
        self.max_rows = 200

        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self._setup()

    # -------------------------------------------------
    def _setup(self):
        t = self.table
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["Time", "Price", "Qty", "Side"])

        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        t.setShowGrid(False)

        h = t.horizontalHeader()
        h.setStretchLastSection(True)
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # 🎨 스타일 통일
        t.setStyleSheet("""
        QTableWidget {
            background-color: #1f1f1f;
            color: #e0e0e0;
            font-size: 12px;
        }
        QHeaderView::section {
            background-color: #2b2b2b;
            color: #cccccc;
            font-size: 11px;
            padding: 6px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: transparent;
        }
        """)

    # -------------------------------------------------
    def clear(self):
        self.table.setRowCount(0)

    # -------------------------------------------------
    def on_trade(self, trade: dict):
        """
        trade = {
            ts, price, qty, side
        }
        """

        # 최신 체결을 위에
        self.table.insertRow(0)

        # -------------------------
        # Time
        # -------------------------
        ts = trade.get("ts")
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts)
                time_str = dt.strftime("%H:%M:%S")
            else:
                time_str = "--:--:--"
        except Exception:
            time_str = "--:--:--"

        price = trade.get("price", 0)
        qty = trade.get("qty", 0)
        side = trade.get("side", "")

        # -------------------------
        # 아이템 생성
        # -------------------------
        item_time = QTableWidgetItem(time_str)
        item_price = QTableWidgetItem(f"{price:,.2f}")
        item_qty = QTableWidgetItem(f"{qty:g}")
        item_side = QTableWidgetItem(side)

        for it in (item_time, item_price, item_qty, item_side):
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it.setBackground(QColor("#232323"))

        # -------------------------
        # 색상 / 강조
        # -------------------------
        if side == "BUY":
            fg = QColor("#2ecc71")
            bg = QColor(46, 204, 113, 35)
        else:
            fg = QColor("#e74c3c")
            bg = QColor(231, 76, 60, 35)

        item_price.setForeground(fg)
        item_price.setFont(self.bold_font)

        item_side.setForeground(fg)
        item_side.setFont(self.bold_font)

        # Qty는 중립
        item_qty.setForeground(QColor("#dddddd"))

        # 행 배경 강조
        for it in (item_time, item_price, item_qty, item_side):
            it.setBackground(bg)

        # -------------------------
        # 테이블 삽입
        # -------------------------
        self.table.setItem(0, 0, item_time)
        self.table.setItem(0, 1, item_price)
        self.table.setItem(0, 2, item_qty)
        self.table.setItem(0, 3, item_side)

        # -------------------------
        # 하이라이트 페이드
        # -------------------------
        QTimer.singleShot(250, lambda: self._clear_highlight(0))

        # -------------------------
        # Row 제한
        # -------------------------
        if self.table.rowCount() > self.max_rows:
            self.table.removeRow(self.table.rowCount() - 1)

    # -------------------------------------------------
    def _clear_highlight(self, row):
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor("#232323"))
