from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

from ui.utils.formatter import fmt
from ui.utils.formatter import DISPLAY_FORMAT, DEFAULT_FMT


class PositionsTable(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            ["Symbol", "Side", "Qty", "Entry", "PnL", "Liq"]
        )

        # -----------------------------
        # 기본 동작 설정
        # -----------------------------
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)

        # -----------------------------
        # Header 스타일
        # -----------------------------
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(self.columnCount() - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

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
            background-color: #2e3f5f;
        }
        """)

        self._prev_rows = []

        # 공통 폰트
        self.bold_font = QFont()
        self.bold_font.setBold(True)

    # ----------------------------------------------------------
    # 🔥 Flicker-Free Render
    # ----------------------------------------------------------
    def render(self, rows):
        total = len(rows)
        self.setRowCount(total)

        if len(self._prev_rows) != total:
            self._prev_rows = [None] * total

        for r, row in enumerate(rows):
            prev = self._prev_rows[r]

            if prev is None:
                self._draw_row(r, row)
                self._prev_rows[r] = row
                continue

            if prev == row:
                continue

            self._update_changed_cells(r, prev, row)
            self._prev_rows[r] = row

    # ----------------------------------------------------------
    # 최초 Row 생성
    # ----------------------------------------------------------
    def _draw_row(self, r, row):
        symbol = row.get("symbol", "")
        fmt_value = DISPLAY_FORMAT.get(symbol, DEFAULT_FMT)

        self._set_item(r, 0, symbol)
        self._set_item(r, 1, row.get("side", ""))

        self._set_item(r, 2, fmt(row.get("qty"), fmt_value["qty"]))
        self._set_item(r, 3, fmt(row.get("entry_price"), fmt_value["price"]))
        self._set_item(r, 4, fmt(row.get("unrealized_pnl"), fmt_value["pnl"]))
        self._set_item(r, 5, fmt(row.get("liq_price"), fmt_value["price"]))

        self._apply_style(r, row)

    # ----------------------------------------------------------
    # 변경된 셀만 업데이트
    # ----------------------------------------------------------
    def _update_changed_cells(self, r, prev, new):
        columns = [
            ("symbol", None),
            ("side", None),
            ("qty", "qty"),
            ("entry_price", "price"),
            ("unrealized_pnl", "pnl"),
            ("liq_price", "price"),
        ]

        symbol = new.get("symbol", "")
        fmt_value = DISPLAY_FORMAT.get(symbol, DEFAULT_FMT)

        for c, (key, fmt_key) in enumerate(columns):
            if prev.get(key) == new.get(key):
                continue

            if fmt_key:
                self._set_item(r, c, fmt(new.get(key), fmt_value[fmt_key]))
            else:
                self._set_item(r, c, new.get(key))

        self._apply_style(r, new)

    # ----------------------------------------------------------
    # SetItem Helper
    # ----------------------------------------------------------
    def _set_item(self, row, col, value):
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.setItem(row, col, item)

        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setText(str(value))

    # ----------------------------------------------------------
    # 🔥 스타일 적용 (핵심)
    # ----------------------------------------------------------
    def _apply_style(self, row, row_data):
        side = row_data.get("side")
        pnl = float(row_data.get("unrealized_pnl", 0))

        # --- 기본 행 배경 ---
        for c in range(self.columnCount()):
            item = self.item(row, c)
            if item:
                item.setBackground(QColor("#232323"))
                item.setForeground(QColor("#e0e0e0"))
                item.setFont(QFont())

        # --- Symbol ---
        symbol_item = self.item(row, 0)
        if symbol_item:
            symbol_item.setFont(self.bold_font)
            symbol_item.setForeground(QColor("#ffffff"))

        # --- Side ---
        side_item = self.item(row, 1)
        if side_item:
            if side == "LONG":
                side_item.setForeground(QColor("#0051ff"))
                side_item.setBackground(QColor(46, 204, 113, 40))
            elif side == "SHORT":
                side_item.setForeground(QColor("#e74c3c"))
                side_item.setBackground(QColor(231, 76, 60, 40))

        # --- Qty ---
        qty_item = self.item(row, 2)
        if qty_item:
            qty_item.setFont(self.bold_font)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # --- Entry / Liq ---
        for col in (3, 5):
            item = self.item(row, col)
            if item:
                item.setForeground(QColor("#aaaaaa"))

        # --- PnL (주인공) ---
        pnl_item = self.item(row, 4)
        if pnl_item:
            pnl_item.setFont(self.bold_font)
            if pnl > 0:
                pnl_item.setForeground(QColor("#2ecc71"))
            elif pnl < 0:
                pnl_item.setForeground(QColor("#e74c3c"))
            else:
                pnl_item.setForeground(QColor("#cccccc"))
