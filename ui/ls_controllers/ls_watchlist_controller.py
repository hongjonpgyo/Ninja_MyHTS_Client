from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from ui.utils.ls_symbol_name import display_symbol_name


class LSWatchListController:
    """
    HTS Style LS WatchList
    - 체결현황과 동일한 다크 테이블 톤
    - 선 제거 / 선택 강조 최소화
    - 종목 선택용 리스트에 최적화
    """

    COL_NAME = 0
    COL_SYMBOL = 1
    COL_PRICE = 2
    COL_DIFF = 3

    def __init__(self, table, on_symbol_click=None):
        self.table = table
        self.on_symbol_click = on_symbol_click

        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self._init_table()
        self._apply_style()

        self.table.cellClicked.connect(self._on_cell_clicked)

    # -------------------------------------------------
    # Table init
    # -------------------------------------------------
    def _init_table(self):
        headers = ["종목명", "코드", "현재가", "대비"]

        t = self.table
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(0)

        t.verticalHeader().setVisible(False)
        t.setSortingEnabled(False)
        t.setSelectionMode(t.SelectionMode.SingleSelection)
        t.setSelectionBehavior(t.SelectionBehavior.SelectRows)

        t.horizontalHeader().setStretchLastSection(True)
        t.verticalHeader().setDefaultSectionSize(24)

    # -------------------------------------------------
    # Style (체결현황과 동일 계열)
    # -------------------------------------------------
    def _apply_style(self):
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #1f1f1f;
            color: #e0e0e0;
            font-size: 12px;
            border: none;
        }

        QTableWidget::item {
            border: none;
            padding: 4px 6px;
        }

        QTableWidget::item:selected {
            background-color: #2b2b2b;
        }

        QHeaderView::section {
            background-color: #2a2a2a;
            color: #bfbfbf;
            font-size: 11px;
            padding: 6px;
            border: none;
        }
        """)

    # -------------------------------------------------
    # Public
    # -------------------------------------------------
    def load_rows(self, rows: list[dict]):
        self.table.setRowCount(0)
        for row in rows:
            self._append_row(row)

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _append_row(self, row: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setProperty(f"_row_{r}", row)

        def set_item(col, text, align, color=None, bold=False):
            item = QTableWidgetItem(text)
            item.setTextAlignment(align)
            if color:
                item.setForeground(color)
            if bold:
                item.setFont(self.bold_font)
            self.table.setItem(r, col, item)

        symbol = row.get("symbol", "")
        trd_p = row.get("trd_p")
        diff = row.get("diff")

        # -----------------------
        # 종목명 / 코드
        # -----------------------
        display_nm, full_nm = display_symbol_name(symbol)

        set_item(
            self.COL_NAME,
            display_nm,
            Qt.AlignmentFlag.AlignLeft,
            bold=True,
        )
        set_item(
            self.COL_SYMBOL,
            symbol,
            Qt.AlignmentFlag.AlignCenter,
            QColor("#bbbbbb"),
        )

        # -----------------------
        # 현재가 / 대비
        # -----------------------
        if not trd_p:
            set_item(
                self.COL_PRICE,
                "--",
                Qt.AlignmentFlag.AlignRight,
                QColor("#777777"),
            )
            set_item(
                self.COL_DIFF,
                "―",
                Qt.AlignmentFlag.AlignCenter,
                QColor("#777777"),
            )
            return

        price = float(trd_p)
        diff_val = float(diff or 0)

        diff_rate = (diff_val / price) * 100 if price else 0

        if diff_rate > 0:
            color = QColor("#e74c3c")   # 상승
            arrow = "▲"
        elif diff_rate < 0:
            color = QColor("#3498db")   # 하락
            arrow = "▼"
        else:
            color = QColor("#aaaaaa")
            arrow = "―"

        set_item(
            self.COL_PRICE,
            f"{price:,.2f}",
            Qt.AlignmentFlag.AlignRight,
            color,
            bold=True,
        )
        set_item(
            self.COL_DIFF,
            f"{arrow} {abs(diff_rate):.2f}%",
            Qt.AlignmentFlag.AlignCenter,
            color,
        )

    # -------------------------------------------------
    # Click handling
    # -------------------------------------------------
    def _on_cell_clicked(self, row: int, col: int):
        if not self.on_symbol_click:
            return

        item = self.table.item(row, self.COL_SYMBOL)
        if not item:
            return

        symbol = item.text().strip()
        if not symbol:
            return

        row_data = self.table.property(f"_row_{row}")

        # 🔥 symbol + 원본 row dict 전달
        self.on_symbol_click(symbol, row_data)
