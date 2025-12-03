# 포지션 테이블
# widgets/positions_table.py
from PyQt6.QtWidgets import QTableWidgetItem

class PositionsTable:
    def __init__(self, table):
        self.table = table

    def render(self, data):
        rows = len(data)
        self.table.setRowCount(rows)

        for r, row in enumerate(data):
            self.table.setItem(r, 0, QTableWidgetItem(row["symbol"]))
            self.table.setItem(r, 1, QTableWidgetItem(str(row["qty"])))
            self.table.setItem(r, 2, QTableWidgetItem(str(row["entry_price"])))
            self.table.setItem(r, 3, QTableWidgetItem(str(row["unrealized_pnl"])))
