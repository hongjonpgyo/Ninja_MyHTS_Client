from typing import List, Optional

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QTimer

from services.ls.ls_orderbook_engine import OrderBookRow


class OrderBookRenderer:
    COL_MIT_SELL = 0
    COL_SELL = 1
    COL_SELL_CNT = 2
    COL_SELL_QTY = 3
    COL_PRICE = 4
    COL_BUY_QTY = 5
    COL_BUY_CNT = 6
    COL_BUY = 7
    COL_MIT_BUY = 8

    def __init__(self, table: QTableWidget):
        self.table = table

        # -----------------------------
        # Colors
        # -----------------------------
        self.bg_default = QColor("#1e1e1e")
        self.bg_center = QColor("#242424")
        self.bg_ls = QColor("#203a52")

        self.tp_line = QColor(46, 204, 113)
        self.sl_line = QColor(231, 76, 60)

        self.tp_bg = QColor(46, 204, 113, 25)
        self.sl_bg = QColor(231, 76, 60, 25)

        self.ask_base = QColor(231, 76, 60)
        self.bid_base = QColor(46, 204, 113)

        self.fg_normal = QColor("#e0e0e0")
        self.fg_ls = QColor("#ffd54f")

        # -----------------------------
        # Fonts
        # -----------------------------
        self.font_price = QFont()
        self.font_price.setBold(True)

        self.font_tag = QFont()
        self.font_tag.setPointSize(9)
        self.font_tag.setBold(True)

        self._last_rows: List[OrderBookRow] = []

    # =================================================
    # Table setup
    # =================================================
    def configure_table(self, total_rows: int):
        self.table.setRowCount(total_rows)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "MIT", "매도", "건수", "잔량",
            "가격",
            "잔량", "건수", "매수", "MIT"
        ])

        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMouseTracking(True)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.Shape.NoFrame)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_PRICE, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COL_PRICE, 120)

        self.table.verticalHeader().setVisible(False)

        for r in range(total_rows):
            for c in range(9):
                it = self._get_item(r, c)
                it.setBackground(QBrush(self.bg_default))
                it.setForeground(self.fg_normal)

    # =================================================
    # Render
    # =================================================
    def render(self, rows: List[OrderBookRow]):
        self._last_rows = rows
        self.table.setRowCount(len(rows))

        if not rows:
            return

        max_qty = max([1] + [r.ask_qty for r in rows] + [r.bid_qty for r in rows])

        for r, row in enumerate(rows):
            self._render_row(r, row, max_qty)

    # =================================================
    # FX
    # =================================================
    def pulse_center(self, row_idx: int, ms: int = 140):
        self._tint_row(row_idx, QColor("#355f7a"))
        QTimer.singleShot(ms, self._restore_all)

    def flash_row(self, row_idx: int, side: Optional[str] = None, ms: int = 180):
        if side == "BUY":
            color = QColor(46, 204, 113, 140)
        elif side == "SELL":
            color = QColor(231, 76, 60, 140)
        else:
            color = QColor("#4b4b4b")

        self._tint_row(row_idx, color)
        QTimer.singleShot(ms, self._restore_all)

    # =================================================
    # Row render
    # =================================================
    def _render_row(self, r: int, row: OrderBookRow, max_qty: int):
        # -----------------
        # Background priority
        # -----------------
        bg = self.bg_default

        if row.is_center:
            bg = self.bg_center
        if row.is_ls_price:
            bg = self.bg_ls
        if row.is_tp:
            bg = self.tp_bg
        elif row.is_sl:
            bg = self.sl_bg

        self._paint_row_bg(r, bg)

        # -----------------
        # PRICE
        # -----------------
        price_it = self._get_item(r, self.COL_PRICE)
        price_text = f"{row.price:,.2f}"

        if row.is_tp:
            price_it.setForeground(self.tp_line)
            price_text += "  TP"
        elif row.is_sl:
            price_it.setForeground(self.sl_line)
            price_text += "  SL"
        else:
            price_it.setForeground(self.fg_ls if row.is_ls_price else self.fg_normal)

        price_it.setText(price_text)
        price_it.setFont(self.font_price)

        # -----------------
        # ASK / BID
        # -----------------
        self._set_text(r, self.COL_SELL_QTY, "" if row.ask_qty <= 0 else str(row.ask_qty))
        self._set_text(r, self.COL_SELL_CNT, "" if row.ask_cnt <= 0 else str(row.ask_cnt))
        self._set_text(r, self.COL_BUY_QTY, "" if row.bid_qty <= 0 else str(row.bid_qty))
        self._set_text(r, self.COL_BUY_CNT, "" if row.bid_cnt <= 0 else str(row.bid_cnt))

        # -----------------
        # MY LIMIT ORDERS
        # -----------------
        self._set_text(r, self.COL_SELL, "")
        self._set_text(r, self.COL_BUY, "")

        if row.my_sell_cnt > 0:
            it = self._get_item(r, self.COL_SELL)
            it.setText(str(row.my_sell_cnt))
            it.setForeground(QColor("#ffd54f"))
            it.setFont(self.font_tag)

        if row.my_buy_cnt > 0:
            it = self._get_item(r, self.COL_BUY)
            it.setText(str(row.my_buy_cnt))
            it.setForeground(QColor("#ffd54f"))
            it.setFont(self.font_tag)

        # -----------------
        # MY MIT ORDERS (TP / SL)
        # -----------------
        self._set_text(r, self.COL_MIT_SELL, "")
        self._set_text(r, self.COL_MIT_BUY, "")

        if row.my_mit_sell > 0:
            it = self._get_item(r, self.COL_MIT_SELL)
            it.setText(f"●{row.my_mit_sell}")
            it.setForeground(QColor("#ff7675"))
            it.setFont(self.font_tag)

        if row.my_mit_buy > 0:
            it = self._get_item(r, self.COL_MIT_BUY)
            it.setText(f"●{row.my_mit_buy}")
            it.setForeground(QColor("#74b9ff"))
            it.setFont(self.font_tag)

        # -----------------
        # Depth shading
        # -----------------
        self._shade_qty(r, self.COL_SELL_QTY, row.ask_qty, max_qty, self.ask_base, bg)
        self._shade_qty(r, self.COL_BUY_QTY, row.bid_qty, max_qty, self.bid_base, bg)

    # =================================================
    # Helpers
    # =================================================
    def _restore_all(self):
        if self._last_rows:
            self.render(self._last_rows)

    def _get_item(self, r: int, c: int) -> QTableWidgetItem:
        it = self.table.item(r, c)
        if it is None:
            it = QTableWidgetItem("")
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, c, it)
        return it

    def _set_text(self, r: int, c: int, text: str):
        it = self._get_item(r, c)
        it.setText(text)
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def _paint_row_bg(self, r: int, color: QColor):
        for c in range(self.table.columnCount()):
            self._get_item(r, c).setBackground(QBrush(color))

    def _shade_qty(
        self,
        r: int,
        c: int,
        qty: int,
        max_qty: int,
        base: QColor,
        base_bg: QColor,
    ):
        it = self._get_item(r, c)

        if qty <= 0 or max_qty <= 0:
            it.setBackground(QBrush(base_bg))
            return

        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)
        it.setBackground(QBrush(QColor(base.red(), base.green(), base.blue(), alpha)))

    def _tint_row(self, row_idx: int, color: QColor):
        for c in range(self.table.columnCount()):
            it = self.table.item(row_idx, c)
            if it:
                it.setBackground(QBrush(color))
