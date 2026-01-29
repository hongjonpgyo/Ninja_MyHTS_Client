from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

from ui.ls_controllers import ls_order_controller
from ui.ls_controllers.ls_order_controller import OrderController
from ui.utils.formatter import fmt
from ui.utils.formatter import DISPLAY_FORMAT, DEFAULT_FMT
from ui.widgets.ls_position.ls_protection_editor import LSProtectionEditor


class LSPositionsTable(QTableWidget):
    positionSelected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            ["종목명", "포지션", "수량", "평균단가", "평가손익", "강제청산가"]
        )
        self._open_protections = set()  # symbol set
        self._protection_rows = {}

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

        self._prev_rows = []

        # 공통 폰트
        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self.itemSelectionChanged.connect(self._on_selection_changed)

    # ----------------------------------------------------------
    # 🔥 Flicker-Free Render
    # ----------------------------------------------------------
    def render(self, rows):
        # 🔥 원본 데이터 보관
        self._rows = [r for r in rows if float(r.get("qty", 0)) != 0]

        total = len(self._rows)
        self.setRowCount(total)

        if len(self._prev_rows) != total:
            self._prev_rows = [None] * total

        for r, row in enumerate(self._rows):
            prev = self._prev_rows[r]

            if prev is None:
                self._draw_row(r, row)
            elif prev != row:
                self._update_changed_cells(r, prev, row)

            self._prev_rows[r] = row

    # ----------------------------------------------------------
    # 최초 Row 생성
    # ----------------------------------------------------------
    def _draw_row(self, r, row):
        symbol = row.get("symbol", "")
        fmt_value = DISPLAY_FORMAT.get(symbol, DEFAULT_FMT)

        self._set_item(r, 0, symbol)

        # -------------------------
        # 포지션 방향 (용어 통일)
        # -------------------------
        side = row.get("side", "")
        if side == "LONG":
            side_kr = "매수"
        elif side == "SHORT":
            side_kr = "매도"
        else:
            side_kr = ""

        self._set_item(r, 1, side_kr)

        # -------------------------
        # 수량 / 평균단가 / 손익
        # -------------------------
        self._set_item(r, 2, fmt(row.get("qty"), fmt_value["qty"]))
        self._set_item(r, 3, fmt(row.get("avg_price"), fmt_value["price"]))
        self._set_item(r, 4, fmt(row.get("unrealized_pnl"), fmt_value["pnl"]))

        # -------------------------
        # 강제청산가
        # -------------------------
        liq = row.get("liquidation_price")
        self._set_item(
            r,
            5,
            "-" if liq is None else fmt(liq, fmt_value["price"])
        )

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

            # 🔥 Side 한글 변환 (UI 전용)
            if key == "side":
                side = new.get("side")
                side_kr = "롱" if side == "LONG" else "숏" if side == "SHORT" else ""
                self._set_item(r, c, side_kr)
                continue

            # 숫자 포맷 컬럼
            if fmt_key:
                self._set_item(
                    r,
                    c,
                    fmt(new.get(key), fmt_value[fmt_key])
                )
            else:
                self._set_item(r, c, new.get(key))

        # 스타일은 항상 마지막에
        self._apply_style(r, new)

    def _insert_protection_row(self, position_row: int, symbol: str):
        if symbol in self._protection_rows:
            return

        protection_row = position_row + 1
        self.insertRow(protection_row)

        # 전체 span
        self.setSpan(protection_row, 0, 1, self.columnCount())

        editor = LSProtectionEditor(symbol, self)

        self.setCellWidget(protection_row, 0, editor)
        self.setRowHeight(protection_row, 44)

        self._protection_rows[symbol] = protection_row

        # --- 버튼 이벤트 연결 (임시 로그용) ---
        editor.btn_apply.clicked.connect(
            lambda: print(f"[PROTECT APPLY] {symbol}")
        )
        editor.btn_clear.clicked.connect(
            lambda: self._remove_protection_row(symbol)
        )

    def load_protections(self, rows: list[dict]):
        """
        rows = [{ symbol, side, type, price, qty }]
        """
        if not rows:
            return

        symbol = rows[0]["symbol"]

        editor = self._get_protection_editor(symbol)
        if not editor:
            return

        editor.load_protections(rows)

    def _get_protection_editor(self, symbol: str):
        row = self._protection_rows.get(symbol)
        if row is None:
            return None

        return self.cellWidget(row, 0)

    def _on_selection_changed(self):
        row_index = self.currentRow()
        if row_index < 0:
            return

        if not hasattr(self, "_rows") or row_index >= len(self._rows):
            return

        row_data = self._rows[row_index]

        print("SELECT:", row_data)

        data = {

            "symbol": row_data["symbol"],
            "side": row_data["side"],
            "qty": int(row_data["qty"]),
            "avg_price": float(row_data["avg_price"]),
        }

        self.positionSelected.emit(data)

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
                side_item.setForeground(QColor("#2ecc71"))
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
