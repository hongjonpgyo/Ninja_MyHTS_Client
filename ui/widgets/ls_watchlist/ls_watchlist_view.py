from PyQt6.QtWidgets import QTableView
from PyQt6.QtCore import pyqtSignal, Qt, QModelIndex
from .ls_watchlist_model import LSWatchListModel


class LSWatchListView(QTableView):
    symbolSelected = pyqtSignal(str, object)  # symbol, price(None 가능)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)

        self.clicked.connect(self._on_click)

    def setModel(self, model: LSWatchListModel):
        super().setModel(model)

        # 컬럼 너비
        # self.setColumnWidth(model.COL_FAV, 40)
        self.setColumnWidth(model.COL_NAME, 120)
        self.setColumnWidth(model.COL_CODE, 80)
        self.setColumnWidth(model.COL_PRICE, 100)
        self.setColumnWidth(model.COL_CHANGE, 90)

        # self.setSortingEnabled(True)

    def _on_click(self, index: QModelIndex):
        model: LSWatchListModel = self.model()
        row = index.row()

        # 즐겨찾기 클릭
        if index.column() == model.COL_FAV:
            model.toggle_favorite(row)
            return

        # 일반 행 선택 → 주문 패널용 signal
        sym = model.symbols[row]
        self.symbolSelected.emit(sym.symbol, sym.price)
