import asyncio

from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView, QHeaderView, QTableWidget
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

    # COL_FAV = 0  # ⭐ 추가
    COL_NAME = 0
    COL_SYMBOL = 1
    COL_PRICE = 2
    COL_DIFF = 3

    def __init__(self, table, on_symbol_click=None, on_favorite_toggle=None, on_favorite_remove=None):
        self.table = table
        self.on_symbol_click = on_symbol_click
        self.on_favorite_toggle = on_favorite_toggle
        self.on_favorite_remove = on_favorite_remove

        self.bold_font = QFont()
        # self.bold_font.setBold(True)

        self.favorites: set[str] = set()
        self._price_items: dict[str, QTableWidgetItem] = {}
        self._diff_items: dict[str, QTableWidgetItem] = {}

        self._init_table()
        # self._apply_style()

        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    # -------------------------------------------------
    # Table init
    # -------------------------------------------------
    def _init_table(self):
        headers = ["종목명", "코드", "현재가", "대비"]
        self._symbol_row_map = {}  # 🔥 핵심

        t = self.table
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(0)

        t.verticalHeader().setVisible(False)
        t.setSortingEnabled(False)
        t.setSelectionMode(t.SelectionMode.SingleSelection)
        t.setSelectionBehavior(t.SelectionBehavior.SelectRows)

        t.verticalHeader().setDefaultSectionSize(24)

        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = t.horizontalHeader()

        # ⭐ 컬럼은 고정 20px
        # header.setSectionResizeMode(self.COL_FAV, QHeaderView.ResizeMode.Fixed)
        # t.setColumnWidth(self.COL_FAV, 28)

        # 나머지는 Stretch
        for col in range(t.columnCount()):
           # if col != self.COL_FAV:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

    # -------------------------------------------------
    # Public
    # -------------------------------------------------
    def load_rows(self, rows: list[dict]):
        self.table.setRowCount(0)
        self._symbol_row_map.clear()
        self._price_items.clear()
        self._diff_items.clear()

        for row in rows:
            self._append_row(row)
            self._symbol_row_map[row["symbol"]] = self.table.rowCount() - 1

    def select_symbol(self, symbol: str):
        if symbol not in self._symbol_row_map:
            return None

        row_idx = self._symbol_row_map[symbol]
        self.table.selectRow(row_idx)

        row_data = self.table.property(f"_row_{row_idx}")
        return row_data

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _append_row(self, row: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setProperty(f"_row_{r}", row)

        def make_item(text, align, color=None):
            item = QTableWidgetItem(text)
            item.setTextAlignment(int(align | Qt.AlignmentFlag.AlignVCenter))
            if color:
                item.setForeground(color)
            return item

        symbol = row.get("symbol", "")
        trd_p = row.get("last_price")
        change_rate = row.get("change_rate") or row.get("diff")

        display_nm, _ = display_symbol_name(symbol)

        name_item = make_item(display_nm, Qt.AlignmentFlag.AlignLeft)
        symbol_item = make_item(symbol, Qt.AlignmentFlag.AlignLeft)
        price_item = make_item("--", Qt.AlignmentFlag.AlignRight, QColor("#777777"))
        diff_item = make_item("―", Qt.AlignmentFlag.AlignCenter, QColor("#777777"))

        self.table.setItem(r, self.COL_NAME, name_item)
        self.table.setItem(r, self.COL_SYMBOL, symbol_item)
        self.table.setItem(r, self.COL_PRICE, price_item)
        self.table.setItem(r, self.COL_DIFF, diff_item)

        self._price_items[symbol] = price_item
        self._diff_items[symbol] = diff_item

        if not trd_p:
            return

        price = float(trd_p)
        rate = float(change_rate or 0)

        if rate > 0:
            color = QColor("#e74c3c")
            arrow = "▲"
        elif rate < 0:
            color = QColor("#3498db")
            arrow = "▼"
        else:
            color = QColor("#aaaaaa")
            arrow = "―"

        price_item.setText(f"{price:,.2f}")
        price_item.setForeground(color)

        diff_item.setText(f"{arrow} {abs(rate):.2f}%")
        diff_item.setForeground(color)

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

    def _on_cell_double_clicked(self, row: int, col: int):
        # ⭐ 컬럼에서만 동작하게 하고 싶다면 조건 추가 가능
        # if col != self.COL_FAV:
        #     return

        symbol_item = self.table.item(row, self.COL_SYMBOL)
        if not symbol_item:
            return

        symbol = symbol_item.text()

        if self.on_favorite_toggle:
            self.on_favorite_toggle(symbol)

    # def _update_favorite_icon(self, row: int, symbol: str):
    #     fav_item = self.table.item(row, self.COL_FAV)
    #     if not fav_item:
    #         fav_item = QTableWidgetItem("")
    #         fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    #         self.table.setItem(row, self.COL_FAV, fav_item)
    #
    #     if symbol in self.favorites:
    #         fav_item.setText("❤")
    #         fav_item.setForeground(QColor("#FFD700"))
    #     else:
    #         fav_item.setText("")
    #         fav_item.setForeground(QColor("#555555"))

    def update_price(self, symbol: str, price: float, change: float, change_rate: float):
        """
        PriceController 에서 호출하는 표준 인터페이스
        """
        if symbol not in self._symbol_row_map:
            return

        row = self._symbol_row_map[symbol]
        self._update_price_cell(row, price, change, change_rate)

    def update_price(self, symbol: str, price: float, change: float, change_rate: float):
        symbol = (symbol or "").strip().upper()

        price_item = self._price_items.get(symbol)
        diff_item = self._diff_items.get(symbol)

        if not price_item or not diff_item:
            return

        if change_rate > 0:
            color = QColor("#e74c3c")
            arrow = "▲"
        elif change_rate < 0:
            color = QColor("#3498db")
            arrow = "▼"
        else:
            color = QColor("#aaaaaa")
            arrow = "―"

        price_text = f"{price:,.2f}"
        diff_text = f"{arrow} {abs(change_rate):.2f}%"

        if price_item.text() != price_text:
            price_item.setText(price_text)

        if diff_item.text() != diff_text:
            diff_item.setText(diff_text)

        if price_item.foreground().color() != color:
            price_item.setForeground(color)

        if diff_item.foreground().color() != color:
            diff_item.setForeground(color)

    def batch_update_prices(self, updates: dict[str, dict]):
        if not updates:
            return

        self.table.setUpdatesEnabled(False)
        try:
            for symbol, event in updates.items():
                price = event.get("price")
                change = event.get("change")
                change_rate = event.get("change_rate")

                if price is None or change_rate is None:
                    continue

                self.update_price(symbol, price, change, change_rate)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.viewport().update()

    def set_favorites(self, favorites: set[str]):
        """
        외부(MainWindow)에서 즐겨찾기 set을 주입받아
        ⭐ 컬럼 표시를 즉시 갱신한다.
        """
        self.favorites = set(favorites)

        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, self.COL_SYMBOL)
            if not symbol_item:
                continue

            symbol = symbol_item.text()

            # fav_item = self.table.item(row, self.COL_FAV)
            # if fav_item is None:
            #     fav_item = QTableWidgetItem()
            #     fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            #     fav_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 선택/편집 방지
            #     self.table.setItem(row, self.COL_FAV, fav_item)
            #
            # fav_item.setText("❤" if symbol in self.favorites else "")


