# ui/widgets/executions_table.py
from datetime import datetime
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QHeaderView, QTableWidgetItem

from ui.utils.formatter import fmt_time


class ExecutionsTable(QtWidgets.QTableWidget):
    """
    - WS 체결 PUSH에 맞춰 append_row() 지원
    - 전체 덮어쓰기(update_table)도 유지
    - 신규 체결 highlight
    - BUY/SELL 컬러
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(7)
        # self.setHorizontalHeaderLabels(["Time", "Symbol", "Side", "Price", "Qty", "Fee", "Type"])

        # UI 기본
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        for col in range(1, self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # 스타일(원하는 톤으로 조절 가능)
        self.setStyleSheet("""
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
            background-color: #0a46c7;
            color: white;
        }
        """)

        # 최근 row 수 tracking(옵션)
        self.last_row_count = 0

        # Bold 폰트 (가격/심볼 등)
        self.bold_font = QFont()
        self.bold_font.setBold(True)

    # -------------------------------------------------
    # Public API 1) 전체 갱신
    # -------------------------------------------------
    def update_table(self, executions: list[dict]):
        if not executions:
            return

        new_row_count = len(executions)
        is_new_data = new_row_count > self.last_row_count

        self.setRowCount(new_row_count)

        for row, ex in enumerate(executions):
            self._draw_row(row, ex)

        if is_new_data:
            self._highlight_new_row(new_row_count - 1)

        self.last_row_count = new_row_count
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    # -------------------------------------------------
    # Public API 2) 실시간 append
    # -------------------------------------------------
    def append_row(self, data: dict):
        table = self
        scrollbar = table.verticalScrollBar()

        # 🔥 사용자가 맨 아래를 보고 있었는지
        at_bottom = scrollbar.value() == scrollbar.maximum()

        row = table.rowCount()
        table.insertRow(row)

        created_at = data.get("created_at") or data.get("ts")
        symbol = data.get("symbol", "")
        side = data.get("side", "")
        price = data.get("price")
        qty = data.get("qty")
        fee = data.get("fee", 0)
        typ = data.get("type", "TRADE")

        # 시간
        time_text = fmt_time(created_at) if created_at else "--:--:--"

        table.setItem(row, 0, QTableWidgetItem(time_text))
        table.setItem(row, 1, QTableWidgetItem(symbol))
        table.setItem(row, 2, QTableWidgetItem(side))
        table.setItem(row, 3, QTableWidgetItem(self._fmt_price(price)))
        table.setItem(row, 4, QTableWidgetItem(self._fmt_qty(qty)))
        table.setItem(row, 5, QTableWidgetItem(self._fmt_fee(fee)))
        table.setItem(row, 6, QTableWidgetItem(typ))

        # 스타일
        table.item(row, 1).setFont(self.bold_font)
        self._color_side(row, side)
        self._highlight_new_row(row)

        # ✅ 맨 아래 보고 있을 때만 자동 스크롤
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

        # ✅ 원래 맨 아래 보고 있을 때만 자동 스크롤
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    # -------------------------------------------------
    # Row draw
    # -------------------------------------------------
    def _draw_row(self, row: int, ex: dict):
        created_at = ex.get("created_at") or ex.get("ts") or ""
        symbol = ex.get("symbol", "")
        side = ex.get("side", "")
        price = ex.get("price", "")
        qty = ex.get("qty", "")
        fee = ex.get("fee", 0)
        typ = ex.get("type", "AUTO")

        # 시간 포맷
        time_text = fmt_time(created_at) if created_at else "--:--:--"

        self._set_item(row, 0, time_text)
        self._set_item(row, 1, symbol, bold=True)
        self._set_item(row, 2, side)
        self._set_item(row, 3, self._fmt_price(price), align=Qt.AlignmentFlag.AlignRight)
        self._set_item(row, 4, self._fmt_qty(qty), align=Qt.AlignmentFlag.AlignRight)
        self._set_item(row, 5, self._fmt_fee(fee), align=Qt.AlignmentFlag.AlignRight)
        self._set_item(row, 6, typ)

        # 컬러 처리
        self._color_side(row, side)

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _set_item(self, row, col, text, align=None, bold=False):
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)

        item.setText("" if text is None else str(text))

        if align is None:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)

        if bold:
            item.setFont(self.bold_font)

    def _color_side(self, row: int, side: str):
        """BUY/SELL 컬러 + 가격 컬럼도 같이 컬러링"""
        side = (side or "").upper()
        side_item = self.item(row, 2)
        price_item = self.item(row, 3)

        if side == "BUY":
            fg = QColor("#0051FF")
        elif side == "SELL":
            fg = QColor("#e74c3c")
        else:
            fg = QColor("#aaaaaa")

        if side_item:
            side_item.setForeground(fg)
        if price_item:
            price_item.setForeground(fg)

    def _highlight_new_row(self, row: int):
        """0.25초간 하이라이트"""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 245, 157, 60))  # 연노랑 투명

        QtCore.QTimer.singleShot(250, lambda r=row: self._clear_highlight(r))

    def _clear_highlight(self, row: int):
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor("#1f1f1f"))

    def _fmt_price(self, v):
        try:
            return f"{float(v):,.2f}"
        except Exception:
            return str(v)

    def _fmt_qty(self, v):
        try:
            # qty는 너무 길면 지저분해서 g로
            return f"{float(v):g}"
        except Exception:
            return str(v)

    def _fmt_fee(self, v):
        try:
            return f"{float(v):,.2f}"
        except Exception:
            return str(v)
