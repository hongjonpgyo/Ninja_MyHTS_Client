# widgets/positions_table.py
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class PositionsTable(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # 컬럼 정의
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Symbol", "Side", "Qty",
            "Entry", "PnL", "Liq"
        ])

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)

        # 이전 데이터 캐싱 → 변화 감지용
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
        self._set_item(r, 0, row["symbol"])
        self._set_item(r, 1, row.get("side", ""))
        self._set_item(r, 2, row["qty"])
        self._set_item(r, 3, row["entry_price"])
        self._set_item(r, 4, row["unrealized_pnl"])
        self._set_item(r, 5, row.get("liq_price", ""))  # ← 수정! QTableWidgetItem 제거

        self._apply_color(r, row)

    # ----------------------------------------------------------
    # 변경된 셀만 업데이트
    # ----------------------------------------------------------
    def _update_changed_cells(self, r, prev, new):
        columns = ["symbol", "side", "qty", "entry_price", "unrealized_pnl", "liq_price"]

        for c, key in enumerate(columns):
            old_val = str(prev.get(key, ""))
            new_val = str(new.get(key, ""))

            if old_val != new_val:
                self._set_item(r, c, new_val)

        # 컬러는 side 또는 PnL이 바뀌면 다시 적용
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
