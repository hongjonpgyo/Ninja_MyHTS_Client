from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

from ui.utils.ls_symbol_name import display_symbol_name


class TradesTable(QTableWidget):
    """
    하단 체결내역 탭용 테이블
    - 누적형
    - 최근 체결이 위로
    - HTS 다크톤
    """

    COL_TIME = 0
    COL_SYMBOL = 1
    COL_SIDE = 2
    COL_QTY = 3
    COL_PRICE = 4
    COL_STATUS = 5

    HEADERS = [
        "시간", "종목", "구분", "수량", "체결가", "상태"
    ]

    def __init__(self, parent=None):
        super().__init__(0, len(self.HEADERS), parent)

        self.setHorizontalHeaderLabels(self.HEADERS)
        self._init_style()

    def _init_style(self):
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 마지막 컬럼만 과도하게 늘어나는 것 방지
        header.setStretchLastSection(False)

    def append_trade(
            self,
            symbol: str,
            side: str,
            qty: int,
            price: float,
            status: str,
            trade_time: datetime,
    ):
        row = 0
        self.insertRow(row)

        # 시간 (날짜 + 시간)

        self._set_item(
            row,
            self.COL_TIME,
            trade_time.strftime("%Y-%m-%d %H:%M:%S"),
            align=Qt.AlignmentFlag.AlignCenter
        )

        display_nm, full_nm = display_symbol_name(symbol)
        # 종목
        self._set_item(row, self.COL_SYMBOL, display_nm, bold=True, align=Qt.AlignmentFlag.AlignCenter)

        # 구분
        side_text = "매수" if side == "BUY" else "매도"
        side_color = QColor("#2ecc71") if side == "BUY" else QColor("#e74c3c")
        self._set_item(
            row, self.COL_SIDE, side_text,
            color=side_color,
            bold=True,
            align=Qt.AlignmentFlag.AlignCenter
        )

        # 수량
        self._set_item(
            row, self.COL_QTY, str(qty),
            align=Qt.AlignmentFlag.AlignCenter
        )

        # 가격
        self._set_item(
            row, self.COL_PRICE,
            f"{price:,.0f}",
            color=QColor("#f1c40f"),
            align=Qt.AlignmentFlag.AlignRight
        )

        # 상태
        status_color = QColor("#2ecc71") if status == "완료" else QColor("#7f8c8d")
        self._set_item(
            row, self.COL_STATUS, status,
            color=status_color,
            align=Qt.AlignmentFlag.AlignCenter
        )

    def _set_item(
        self,
        row: int,
        col: int,
        text: str,
        color: QColor | None = None,
        bold: bool = False,
        align: Qt.AlignmentFlag | None = None,
    ):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

        if color:
            item.setForeground(color)

        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)

        if col == self.COL_TIME:
            item.setFont(QFont("JetBrains Mono", 12))

        if align:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)

        self.setItem(row, col, item)
