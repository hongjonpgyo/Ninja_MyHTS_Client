import asyncio
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class ReservationWidget(QWidget):
    """
    예약 주문 탭 UI (최종 안정 버전)

    - 체결/미체결과 동일한 다크 톤
    - WAITING만 취소 가능
    - TRIGGERED → DONE 상태 자연스러운 전이
    """

    COL_TIME = 0
    COL_SYMBOL = 1
    COL_SIDE = 2
    COL_QTY = 3
    COL_TRIGGER = 4
    COL_ORDER = 5
    COL_STATUS = 6
    COL_CANCEL = 7

    def __init__(self, parent=None):
        super().__init__(parent)

        self.table = QTableWidget()
        self._row_reservation_map: dict[int, int] = {}

        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self._setup_table()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.table)

    # ==================================================
    # Setup
    # ==================================================
    def _setup_table(self):
        t = self.table
        t.setColumnCount(8)
        t.setHorizontalHeaderLabels([
            "시간", "종목", "구분", "수량", "조건", "주문", "상태", "취소"
        ])

        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        # ❌ 제거: 흰 줄 / 강한 경계 원인
        t.setAlternatingRowColors(False)
        t.setShowGrid(False)

        h = t.horizontalHeader()
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setStretchLastSection(True)

        t.setStyleSheet("""
        QTableWidget {
            background-color: #1f1f1f;
            color: #e0e0e0;
            font-size: 12px;
            border: none;
        }

        QTableWidget::item {
            padding: 6px;
            border: none;
        }

        QHeaderView::section {
            background-color: #2a2a2a;
            color: #bfbfbf;
            font-size: 11px;
            padding: 6px;
            border: none;
        }
        """)

    # ==================================================
    # Public API
    # ==================================================
    def update_rows(self, rows: list[dict]):
        self.table.setRowCount(0)
        self._row_reservation_map.clear()

        rows = sorted(rows, key=lambda r: r["created_at"], reverse=True)
        for r in rows:
            self._append_row(r)

    # ==================================================
    # Row Rendering
    # ==================================================
    def _append_row(self, r: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, self.COL_TIME, self._time_item(r["created_at"]))
        self.table.setItem(row, self.COL_SYMBOL, self._center_item(r["symbol"], bold=True))
        self.table.setItem(row, self.COL_SIDE, self._side_item(r["side"]))
        self.table.setItem(row, self.COL_QTY, self._center_item(str(int(r["qty"])), bold=True))
        self.table.setItem(row, self.COL_TRIGGER, self._trigger_item(r))
        self.table.setItem(row, self.COL_ORDER, self._order_item(r))
        self.table.setItem(row, self.COL_STATUS, self._status_item(r["status"]))

        self._row_reservation_map[row] = r["reservation_id"]

        # 취소 버튼 (WAITING만)
        if r["status"] == "WAITING":
            btn = QPushButton("✕")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: #777777;
                    font-size: 13px;
                    border: none;
                }
                QPushButton:hover {
                    color: #e74c3c;
                }
            """)
            btn.clicked.connect(
                lambda _, rid=r["reservation_id"]:
                asyncio.create_task(self.on_cancel(rid))
            )
            self.table.setCellWidget(row, self.COL_CANCEL, btn)

    # ==================================================
    # Item Builders
    # ==================================================
    def _time_item(self, created_at):
        if isinstance(created_at, str):
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", ""))
                text = dt.strftime("%H:%M:%S")
            except Exception:
                text = "--:--:--"
        else:
            text = created_at.strftime("%H:%M:%S")

        return self._center_item(text)

    def _side_item(self, side: str):
        it = QTableWidgetItem("매수" if side == "BUY" else "매도")
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it.setFont(self.bold_font)

        if side == "BUY":
            it.setForeground(QColor("#2ecc71"))
        else:
            it.setForeground(QColor("#e74c3c"))

        return it

    def _trigger_item(self, r):
        op_map = {"<=": "≤", ">=": "≥"}
        op = op_map.get(r["trigger_op"], r["trigger_op"])
        price = f'{r["trigger_price"]:,.0f}'
        it = QTableWidgetItem(f"{op} {price}")
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it.setForeground(QColor("#d4ac0d"))  # 톤 다운
        return it

    def _order_item(self, r):
        if r["order_type"] == "MARKET":
            return self._center_item("시장가")
        return self._center_item(f'지정가 {r["request_price"]:,.0f}')

    def _status_item(self, status: str):
        text_map = {
            "WAITING": "대기",
            "TRIGGERED": "트리거",
            "DONE": "완료",
            "CANCELED": "취소",
        }
        color_map = {
            "WAITING": "#6fa8dc",
            "TRIGGERED": "#f1c40f",
            "DONE": "#2ecc71",
            "CANCELED": "#888888",
        }

        it = QTableWidgetItem(text_map.get(status, status))
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it.setForeground(QColor(color_map.get(status, "#cccccc")))
        return it

    def _center_item(self, text: str, bold: bool = False):
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if bold:
            it.setFont(self.bold_font)
        return it

    # ==================================================
    # Hooks (Controller에서 override)
    # ==================================================
    async def on_cancel(self, reservation_id: int):
        """Controller에서 구현"""
        pass

    def update_status(self, reservation_id: int, status: str):
        for row, rid in self._row_reservation_map.items():
            if rid != reservation_id:
                continue

            self.table.setItem(row, self.COL_STATUS, self._status_item(status))
            if status != "WAITING":
                self.table.setCellWidget(row, self.COL_CANCEL, None)
            break
