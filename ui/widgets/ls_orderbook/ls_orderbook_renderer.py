from typing import List, Optional

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QMargins, QEasingCurve, QPoint

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
        self._nudge_anim = None
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

        # Depth base colors
        self.ask_base = QColor(231, 76, 60)
        self.bid_base = QColor(46, 204, 113)

        # --- Zone guide (좌/우 영역용, 아주 연함)
        self.ask_zone = QColor(231, 76, 60, 14)
        self.bid_zone = QColor(46, 204, 113, 14)

        # Text colors
        self.fg_normal = QColor("#e0e0e0")
        self.fg_ls = QColor("#ffd54f")

        # Tag colors (my orders)
        self.fg_my_sell = QColor("#ffd54f")
        self.fg_my_buy = QColor("#ffd54f")

        # MIT dots
        self.fg_mit_sell = QColor("#ff7675")
        self.fg_mit_buy = QColor("#74b9ff")

        # -----------------------------
        # Fonts
        # -----------------------------
        self.font_price = QFont()
        self.font_price.setBold(True)

        self.font_tag = QFont()
        self.font_tag.setPointSize(9)
        self.font_tag.setBold(True)

        self.font_qty = QFont()
        self.font_qty.setPointSize(15)
        self.font_qty.setBold(True)

        self.font_mit = QFont()
        self.font_mit.setPointSize(14)
        self.font_mit.setBold(True)

        # ---- Protection guide state ----
        self.base_price: Optional[float] = None
        self.hover_price: Optional[float] = None
        self.position_side: Optional[str] = None  # LONG / SHORT

        # ---- Protection guide colors ----
        self.base_line_bg = QColor(255, 214, 79, 80)  # 기준가 (노랑)
        self.tp_preview_bg = QColor(46, 204, 113, 60)  # TP 미리보기
        self.sl_preview_bg = QColor(231, 76, 60, 60)  # SL 미리보기

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

        # Init items
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

    # OrderBookRenderer.py
    def nudge(self, dy: int, ms: int = 1000):
        """
        dy > 0 : 가격 상승 느낌 (살짝 아래로 눌렸다가 복원)
        dy < 0 : 가격 하락 느낌 (살짝 위로 눌렸다가 복원)
        """
        vp = self.table.viewport()

        start_pos = vp.pos()
        end_pos = QPoint(start_pos.x(), start_pos.y() + dy)

        if self._nudge_anim:
            self._nudge_anim.stop()

        self._nudge_anim = QPropertyAnimation(vp, b"pos", self.table)
        self._nudge_anim.setDuration(ms)
        self._nudge_anim.setStartValue(start_pos)
        self._nudge_anim.setEndValue(end_pos)
        self._nudge_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 🔥 끝나면 즉시 원래 자리로 복원
        self._nudge_anim.finished.connect(
            lambda: vp.move(start_pos)
        )

        self._nudge_anim.start()

    # =================================================
    # Row render
    # =================================================
    def _render_row(self, r: int, row: OrderBookRow, max_qty: int):
        # -----------------
        # Base background priority
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

        # -----------------
        # 🔥 Protection guide (base / hover)
        # -----------------
        if self.base_price is not None and row.price == self.base_price:
            bg = self.base_line_bg

        elif (
                self.base_price is not None
                and self.hover_price is not None
                and row.price == self.hover_price
                and self.position_side is not None
        ):
            diff = row.price - self.base_price

            if self.position_side == "LONG":
                bg = self.tp_preview_bg if diff > 0 else self.sl_preview_bg
            else:  # SHORT
                bg = self.tp_preview_bg if diff < 0 else self.sl_preview_bg

        # self._paint_row_bg(r, bg)
        self._paint_price_row_bg(r, bg)
        # 좌/우 영역 가이드 (항상 동일)
        self._paint_side_zone(r)

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
        # ASK / BID (text)
        #   - 건수/잔량은 데이터 있을 때만 표시
        # -----------------
        self._set_text(r, self.COL_SELL_QTY, "" if row.ask_qty <= 0 else str(row.ask_qty))
        self._set_text(r, self.COL_SELL_CNT, "" if row.ask_cnt <= 0 else str(row.ask_cnt))
        self._set_text(r, self.COL_BUY_QTY, "" if row.bid_qty <= 0 else str(row.bid_qty))
        self._set_text(r, self.COL_BUY_CNT, "" if row.bid_cnt <= 0 else str(row.bid_cnt))

        # -----------------
        # MY LIMIT ORDERS (매도/매수)
        # -----------------
        self._set_text(r, self.COL_SELL, "")
        self._set_text(r, self.COL_BUY, "")

        if row.my_sell_cnt > 0:
            it = self._get_item(r, self.COL_SELL)
            it.setText(str(row.my_sell_cnt))
            it.setForeground(self.fg_my_sell)
            it.setFont(self.font_tag)

        if row.my_buy_cnt > 0:
            it = self._get_item(r, self.COL_BUY)
            it.setText(str(row.my_buy_cnt))
            it.setForeground(self.fg_my_buy)
            it.setFont(self.font_tag)

        # -----------------
        # MY MIT ORDERS (TP/SL)
        # -----------------
        self._set_text(r, self.COL_MIT_SELL, "")
        self._set_text(r, self.COL_MIT_BUY, "")

        if row.my_mit_sell > 0:
            it = self._get_item(r, self.COL_MIT_SELL)
            it.setText(f"●{row.my_mit_sell}")
            it.setForeground(self.fg_mit_sell)
            it.setFont(self.font_tag)

        if row.my_mit_buy > 0:
            it = self._get_item(r, self.COL_MIT_BUY)
            it.setText(f"●{row.my_mit_buy}")
            it.setForeground(self.fg_mit_buy)
            it.setFont(self.font_tag)

        # -----------------
        # Depth shading
        #   ✅ 잔량(QTY)만 shading
        #   ❌ 건수(CNT)는 shading 금지 (데이터 있어도 배경은 기본)
        # -----------------
        self._shade_qty_cell_only(r, self.COL_SELL_QTY, row.ask_qty, max_qty, self.ask_base, bg)
        self._shade_qty_cell_only(r, self.COL_BUY_QTY, row.bid_qty, max_qty, self.bid_base, bg)

        # CNT는 절대 건드리지 않음 (기본 bg 유지)
        self._reset_cell_bg_if_empty(r, self.COL_SELL_CNT, row.ask_cnt, bg)
        self._reset_cell_bg_if_empty(r, self.COL_BUY_CNT, row.bid_cnt, bg)

        # MIT / 매도 / 매수 컬럼도 기본 bg 유지(현재가 위/아래로 분리 X)
        # (필요 시 여기서만 “셀 단위” 표시를 추가 가능)

    # =================================================
    # Helpers
    # =================================================
    def _restore_all(self):
        if self._last_rows:
            self.render(self._last_rows)

    def set_position_side(self, side: str):
        self.position_side = side  # "LONG" | "SHORT"

    def set_base_price(self, price: Optional[float]):
        self.base_price = price
        self.hover_price = None
        self._restore_all()

    def set_hover_price(self, price: Optional[float]):
        self.hover_price = price
        self._restore_all()

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

    def _paint_price_row_bg(self, r: int, color: QColor):
        self._get_item(r, self.COL_PRICE).setBackground(QBrush(color))

    def _paint_side_zone(self, r: int):
        # 🔴 매도 영역 (MIT + 매도)
        for c in (self.COL_MIT_SELL, self.COL_SELL):
            it = self._get_item(r, c)
            it.setBackground(QBrush(self.ask_zone))

        # 🟢 매수 영역 (매수 + MIT)
        for c in (self.COL_BUY, self.COL_MIT_BUY):
            it = self._get_item(r, c)
            it.setBackground(QBrush(self.bid_zone))

    def _shade_qty_cell_only(
        self,
        r: int,
        c: int,
        qty: int,
        max_qty: int,
        base: QColor,
        base_bg: QColor,
    ):
        """
        ✅ 잔량 셀만 depth shading
        - 데이터 있을 때만 셀에 색상
        - 데이터 없으면 완전 기본 배경
        """
        it = self._get_item(r, c)

        if qty <= 0 or max_qty <= 0:
            it.setBackground(QBrush(base_bg))
            return

        ratio = min(qty / max_qty, 1.0)
        alpha = int(18 + ratio * 55)  # 연하게 (더 연하게 하고 싶으면 12~45로)
        it.setBackground(QBrush(QColor(base.red(), base.green(), base.blue(), alpha)))

    def _reset_cell_bg_if_empty(self, r: int, c: int, value: int, base_bg: QColor):
        """
        ✅ 건수(CNT) 같은 곳:
        - 값이 없으면 무조건 기본 배경
        - 값이 있어도 '기본 배경 유지'가 원칙 (여기서는 empty만 리셋)
        """
        if value <= 0:
            self._get_item(r, c).setBackground(QBrush(base_bg))

    def _tint_row(self, row_idx: int, color: QColor):
        for c in range(self.table.columnCount()):
            it = self.table.item(row_idx, c)
            if it:
                it.setBackground(QBrush(color))
