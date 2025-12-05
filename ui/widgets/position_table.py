# widgets/positions_table.py
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView

class PositionsTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 컬럼 정의
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Symbol", "Side", "Qty",
            "Entry", "PnL", "Liq"
        ])

        # 🔥 PyQt6 스타일의 Edit Block
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)


    def render(self, data):
        """data: [{symbol, side, qty, entry_price, unrealized_pnl, liq_price}, ...]"""
        rows = len(data)
        self.setRowCount(rows)

        for r, row in enumerate(data):
            self.setItem(r, 0, QTableWidgetItem(row["symbol"]))
            self.setItem(r, 1, QTableWidgetItem(row.get("side", "")))
            self.setItem(r, 2, QTableWidgetItem(str(row["qty"])))
            self.setItem(r, 3, QTableWidgetItem(str(row["entry_price"])))
            self.setItem(r, 4, QTableWidgetItem(str(row["unrealized_pnl"])))
            self.setItem(r, 5, QTableWidgetItem(str(row.get("liq_price", ""))))
