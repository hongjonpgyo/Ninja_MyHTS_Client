from typing import List, Optional

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
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

        self.bg_default = QColor("#1e1e1e")
        self.bg_center = QColor("#242424")
        self.bg_ls = QColor("#203a52")       # LS 기준선(center) 기본 배경

        self.grid = QColor("#3a3a3a")

        self.ask_base = QColor(231, 76, 60)   # red
        self.bid_base = QColor(46, 204, 113)  # green

        self.fg_normal = QColor("#e0e0e0")
        self.fg_ls = QColor("#ffd54f")
        self.fg_my = QColor("#ffd54f")

        self.font_price = QFont()
        self.font_price.setBold(True)

    def configure_table(self, total_rows: int):
        self.table.setRowCount(total_rows)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "MIT", "매도", "건수", "잔량",
            "고정",
            "잔량", "건수", "매수", "MIT"
        ])

        # ===== 기본 동작 =====
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMouseTracking(True)
        self.table.setShowGrid(False)  # 🔥 중요
        self.table.setFrameShape(QTableWidget.Shape.NoFrame)

        # ===== Header =====
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_PRICE, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COL_PRICE, 120)

        self.table.verticalHeader().setVisible(False)

        # ===== 스타일 통합 =====
        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #1f1f1f;
            color: #e0e0e0;
            font-size: 12px;
            border: none;
        }

        QTableWidget::item {
            border: none;
            padding: 4px;
        }

        QHeaderView::section {
            background-color: #2a2a2a;
            color: #bfbfbf;
            font-size: 11px;
            padding: 6px;
            border: none;
        }

        QTableWidget::item:selected {
            background-color: transparent;
        }
        """)

        # ===== 기본 아이템 생성 =====
        for r in range(total_rows):
            for c in range(9):
                it = self._get_item(r, c)
                it.setBackground(QBrush(self.bg_default))
                it.setForeground(self.fg_normal)

    def render(self, rows: List[OrderBookRow]):
        # rows=0이면 그냥 비우기
        self.table.setRowCount(len(rows))
        if not rows:
            return

        max_qty = max([1] + [r.ask_qty for r in rows] + [r.bid_qty for r in rows])

        for r, row in enumerate(rows):
            self._render_row(r, row, max_qty)

    # -------------------------------------------------
    # FX: Pulse/Flash
    # -------------------------------------------------
    def pulse_center(self, row_idx: int, ms: int = 140):
        """center row가 바뀔 때 짧게 pulse"""
        self._tint_row(row_idx, QColor("#355f7a"))
        QTimer.singleShot(ms, lambda: self._restore_row(row_idx))

    def flash_row(self, row_idx: int, side: Optional[str] = None, ms: int = 180):
        """체결/이벤트 발생 row flash (BUY=green, SELL=red)"""
        if side == "BUY":
            color = QColor(46, 204, 113, 140)
        elif side == "SELL":
            color = QColor(231, 76, 60, 140)
        else:
            color = QColor("#4b4b4b")

        self._tint_row(row_idx, color)
        QTimer.singleShot(ms, lambda: self._restore_row(row_idx))

    # -------------------------------------------------
    # Row render
    # -------------------------------------------------
    def _render_row(self, r: int, row: OrderBookRow, max_qty: int):
        # base background
        base_bg = self.bg_default
        if row.is_center:
            base_bg = self.bg_center
        if row.is_ls_price:
            base_bg = self.bg_ls  # LS 기준선 우선

        self._paint_row_bg(r, base_bg)

        # PRICE
        price_it = self._get_item(r, self.COL_PRICE)
        price_it.setText(f"{row.price:,.2f}")
        price_it.setFont(self.font_price)
        price_it.setForeground(self.fg_ls if row.is_ls_price else self.fg_normal)

        # ASK/BID values
        self._set_text(r, self.COL_SELL_QTY, "" if row.ask_qty <= 0 else str(row.ask_qty))
        self._set_text(r, self.COL_SELL_CNT, "" if row.ask_cnt <= 0 else str(row.ask_cnt))

        self._set_text(r, self.COL_BUY_QTY, "" if row.bid_qty <= 0 else str(row.bid_qty))
        self._set_text(r, self.COL_BUY_CNT, "" if row.bid_cnt <= 0 else str(row.bid_cnt))

        # -----------------
        # MY ORDERS (우선 적용)
        # -----------------
        if row.my_sell_cnt > 0:
            it = self._get_item(r, self.COL_SELL_CNT)
            it.setText(str(row.my_sell_cnt))
            # it.setForeground(self.fg_my)
            # it.setBackground(QBrush(QColor(231, 76, 60, 90)))
            # price_it.setForeground(self.fg_my)

        if row.my_buy_cnt > 0:
            it = self._get_item(r, self.COL_BUY_CNT)
            it.setText(str(row.my_buy_cnt))
            # it.setForeground(self.fg_my)
            # it.setBackground(QBrush(QColor(46, 204, 113, 90)))
            # price_it.setForeground(self.fg_my)

        # Depth shading (qty 컬럼만)
        self._shade_qty(r, self.COL_SELL_QTY, row.ask_qty, max_qty, self.ask_base, base_bg)
        self._shade_qty(r, self.COL_BUY_QTY, row.bid_qty, max_qty, self.bid_base, base_bg)

        # MIT/매도/매수는 아직 비움
        self._set_text(r, self.COL_MIT_SELL, "")
        self._set_text(r, self.COL_SELL, "")
        self._set_text(r, self.COL_BUY, "")
        self._set_text(r, self.COL_MIT_BUY, "")

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
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
        # 기본 글자색 리셋(내 주문에서 다시 덮어씀)
        # it.setForeground(self.fg_normal)

    def _paint_row_bg(self, r: int, color: QColor):
        for c in range(self.table.columnCount()):
            it = self._get_item(r, c)
            it.setBackground(QBrush(color))

    def _shade_qty(self, r: int, c: int, qty: int, max_qty: int, base: QColor, base_bg: QColor):
        it = self._get_item(r, c)
        if qty <= 0 or max_qty <= 0:
            it.setBackground(QBrush(base_bg))
            return

        ratio = min(qty / max_qty, 1.0)
        alpha = int(30 + ratio * 120)
        shaded = QColor(base.red(), base.green(), base.blue(), alpha)
        it.setBackground(QBrush(shaded))

    def _tint_row(self, row_idx: int, color: QColor):
        for c in range(self.table.columnCount()):
            it = self.table.item(row_idx, c)
            if it:
                it.setBackground(QBrush(color))

    def _restore_row(self, row_idx: int):
        # 전체 재렌더 없이 "해당 row만" 원복하려면 현재 rows 정보가 필요하지만,
        # 여기서는 안전하게 현재 화면 기준으로만 복구: 가격 칼럼 기반으로 기본색으로 되돌림
        # (정확한 원복은 위젯에서 renderer.render(engine.rows)로 한 번 더 호출해도 됨)
        for c in range(self.table.columnCount()):
            it = self.table.item(row_idx, c)
            if it:
                it.setBackground(QBrush(self.bg_default))
