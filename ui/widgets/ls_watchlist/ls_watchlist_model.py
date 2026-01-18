from dataclasses import dataclass
from typing import Optional, List
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor


# -----------------------------
# LS Symbol (프론트 기준 모델)
# -----------------------------
@dataclass
class LSSymbol:
    symbol: str
    name: str
    exchange: str = ""
    price: Optional[float] = None
    change: Optional[float] = None


# -----------------------------
# WatchList Model
# -----------------------------
class LSWatchListModel(QAbstractTableModel):
    COL_FAV = 0
    COL_NAME = 1
    COL_CODE = 2
    COL_PRICE = 3
    COL_CHANGE = 4

    headers = ["★", "종목명", "코드", "현재가", "전일대비"]

    def __init__(self, symbols: List[LSSymbol]):
        super().__init__()
        self.symbols = symbols
        self.favorites = set()  # symbol code set

        # 빠른 row lookup (WS 붙일 때 사용)
        self._symbol_index = {s.symbol: i for i, s in enumerate(symbols)}

    # ---- basic ----
    def rowCount(self, parent=QModelIndex()):
        return len(self.symbols)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    # ---- data ----
    def data(self, index, role):
        if not index.isValid():
            return None

        sym = self.symbols[index.row()]
        col = index.column()

        # 표시 텍스트
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_FAV:
                return "★" if sym.symbol in self.favorites else ""
            if col == self.COL_NAME:
                return sym.name
            if col == self.COL_CODE:
                return sym.symbol
            if col == self.COL_PRICE:
                return "--" if sym.price is None else f"{sym.price:,.2f}"
            if col == self.COL_CHANGE:
                return "--" if sym.change is None else f"{sym.change:+.2f}"

        # 색상
        if role == Qt.ItemDataRole.ForegroundRole:
            if col in (self.COL_PRICE, self.COL_CHANGE) and sym.change is not None:
                if sym.change > 0:
                    return QColor("#00e676")
                elif sym.change < 0:
                    return QColor("#ff5252")
                else:
                    return QColor("#aaaaaa")

        # 정렬용 (숫자 정렬)
        if role == Qt.ItemDataRole.UserRole:
            if col == self.COL_PRICE:
                return sym.price if sym.price is not None else -1e18
            if col == self.COL_CHANGE:
                return sym.change if sym.change is not None else -1e18

        # 가운데 정렬
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (self.COL_PRICE, self.COL_CHANGE, self.COL_FAV):
                return Qt.AlignmentFlag.AlignCenter

        return None

    # ---- flags ----
    def flags(self, index):
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if index.column() == self.COL_FAV:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    # ---- favorite toggle ----
    def toggle_favorite(self, row: int):
        symbol = self.symbols[row].symbol
        if symbol in self.favorites:
            self.favorites.remove(symbol)
        else:
            self.favorites.add(symbol)

        idx = self.index(row, self.COL_FAV)
        self.dataChanged.emit(idx, idx)

    # ---- future: price update hook ----
    def update_price(self, symbol: str, price: float, change: float):
        if symbol not in self._symbol_index:
            return

        row = self._symbol_index[symbol]
        sym = self.symbols[row]
        sym.price = price
        sym.change = change

        left = self.index(row, self.COL_PRICE)
        right = self.index(row, self.COL_CHANGE)
        self.dataChanged.emit(left, right)
