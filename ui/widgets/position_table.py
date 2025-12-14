# widgets/positions_table.py
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from ui.utils.formatter import fmt
from ui.utils.formatter import DISPLAY_FORMAT
from ui.utils.formatter import DEFAULT_FMT

class PositionsTable(QTableWidget):


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            ["Symbol", "Side", "Qty", "Entry", "PnL", "Liq"]
        )

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(self.columnCount() - 1):
            header.setSectionResizeMode(i, header.ResizeMode.Stretch)

        self._prev_rows = []

    # ----------------------------------------------------------
    # 🔥 Flicker-Free Render
    # ----------------------------------------------------------
    def render(self, rows):
        """rows: [{symbol, side, qty, entry_price, unrealized_pnl, liq_price}, ...]"""

        total = len(rows)
        self.setRowCount(total)

        # 길이가 달라지면 전체 리셋
        if len(self._prev_rows) != total:
            self._prev_rows = [None] * total

        for r, row in enumerate(rows):
            prev = self._prev_rows[r]

            # 첫 렌더링
            if prev is None:
                self._draw_row(r, row)
                self._prev_rows[r] = row
                continue

            # 값이 동일하면 skip → 깜빡임 없음
            if prev == row:
                continue

            # 변경된 경우에만 해당 셀만 갱신
            self._update_changed_cells(r, prev, row)

            # 캐시 업데이트
            self._prev_rows[r] = row

    # ----------------------------------------------------------
    # 전체 Row 최초 생성
    # ----------------------------------------------------------
    def _draw_row(self, r, row):
        symbol = row.get("symbol", "")
        fmt_value = DISPLAY_FORMAT.get(symbol, DEFAULT_FMT)

        self._set_item(r, 0, symbol)
        self._set_item(r, 1, row.get("side", ""))

        # Qty
        self._set_item(
            r, 2,
            fmt(row.get("qty"), fmt_value["qty"])
        )

        # Entry Price
        self._set_item(
            r, 3,
            fmt(row.get("entry_price"), fmt_value["price"])
        )

        # PnL
        self._set_item(
            r, 4,
            fmt(row.get("unrealized_pnl"), fmt_value["pnl"])
        )

        # Liquidation Price
        self._set_item(
            r, 5,
            fmt(row.get("liq_price"), fmt_value["price"])
        )

        self._apply_color(r, row)

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
            old_val = prev.get(key)
            new_val = new.get(key)

            if old_val == new_val:
                continue

            # 포맷 적용 여부 분기
            if fmt_key:
                formatted = fmt(new_val, fmt_value[fmt_key])
                self._set_item(r, c, formatted)
            else:
                self._set_item(r, c, new_val)

        # 컬러 재적용
        self._apply_color(r, new)

    # ----------------------------------------------------------
    # SetItem Helper
    # ----------------------------------------------------------
    def _set_item(self, row, col, value):
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, col, item)

        item.setText(str(value))

    def get_cached_rows(self):
        return self._prev_rows or []

    # ----------------------------------------------------------
    # 🔥 색상 적용 (Side / PnL)
    # ----------------------------------------------------------
    def _apply_color(self, row, row_data):
        # Side 색상
        side_item = self.item(row, 1)
        if side_item:
            if row_data.get("side") == "LONG":
                side_item.setForeground(QColor("#2ecc71"))
            elif row_data.get("side") == "SHORT":
                side_item.setForeground(QColor("#e74c3c"))
            else:
                side_item.setForeground(QColor("white"))

        # PnL 색상
        pnl_item = self.item(row, 4)
        if pnl_item:
            pnl = float(row_data.get("unrealized_pnl", 0))
            if pnl > 0:
                pnl_item.setForeground(QColor("#2ecc71"))
            elif pnl < 0:
                pnl_item.setForeground(QColor("#e74c3c"))
            else:
                pnl_item.setForeground(QColor("white"))
