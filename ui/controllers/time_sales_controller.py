from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

from ui.utils.time_utils import to_kst_str


class TimeSalesController:
    def __init__(self, table):
        self.table = table
        self.max_rows = 50

        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self._setup()

    # -------------------------------------------------
    def _setup(self):
        t = self.table
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["체결시간", "체결가", "수량", "구분"])

        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        t.setShowGrid(False)

        h = t.horizontalHeader()
        h.setStretchLastSection(True)
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # -------------------------------------------------
    def clear(self):
        self.table.setRowCount(0)

    # -------------------------------------------------
    def on_trade(self, trade: dict):
        """
        trade = {
            symbol,
            side,
            price,
            qty,
            executed_at,
            account_id,
            order_id
        }
        """

        # 최신 체결을 위에 추가
        self.table.insertRow(0)

        # -------------------------
        # Time formatting
        # -------------------------
        ts = trade.get("executed_at")
        try:
            if isinstance(ts, str):
                # dt = datetime.fromisoformat(ts)
                # time_str = dt.strftime("%H:%M:%S")
                time_str = to_kst_str(ts, "%H:%M:%S")
            else:
                time_str = "--:--:--"
        except Exception:
            time_str = "--:--:--"

        price = float(trade.get("price", 0))
        qty = trade.get("qty", 0)
        side = trade.get("side", "")

        # -------------------------
        # 아이템 생성
        # -------------------------
        item_time = QTableWidgetItem(time_str)
        item_price = QTableWidgetItem(f"{price:,.2f}")
        item_qty = QTableWidgetItem(f"{qty:g}")
        item_side = QTableWidgetItem("매수" if side == "BUY" else "매도")

        # 기본 속성 설정
        for it in (item_time, item_price, item_qty, item_side):
            it.setTextAlignment(
                int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            )
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # it.setBackground(QColor("#232323"))

        # -------------------------
        # 색상 설정
        # -------------------------
        # if side == "BUY":
        #     # fg = QColor("#0051ff")
        #     flash_bg = QColor(46, 204, 113, 60)
        # else:
        #     # fg = QColor("#e74c3c")
        #     flash_bg = QColor(231, 76, 60, 60)

        # item_price.setForeground(fg)
        item_price.setFont(self.bold_font)

        # item_side.setForeground(fg)
        item_side.setFont(self.bold_font)

        # item_qty.setForeground(QColor("#dddddd"))

        # # 하이라이트 적용
        # highlight_items = [item_time, item_price, item_qty, item_side]
        # for it in highlight_items:
        #     it.setBackground(flash_bg)

        # -------------------------
        # 테이블 삽입
        # -------------------------
        self.table.setItem(0, 0, item_time)
        self.table.setItem(0, 1, item_price)
        self.table.setItem(0, 2, item_qty)
        self.table.setItem(0, 3, item_side)

        # -------------------------
        # 안전한 하이라이트 복구
        # -------------------------
        # QTimer.singleShot(
        #     400,
        #     lambda items=highlight_items: self._clear_highlight_items(items)
        # )

        # -------------------------
        # Row 제한
        # -------------------------
        if self.table.rowCount() > self.max_rows:
            self.table.removeRow(self.table.rowCount() - 1)

    # -------------------------------------------------
    def _clear_highlight_items(self, items):
        return None
        # for item in items:
            # if item:
                # item.setBackground(QColor("#232323"))
