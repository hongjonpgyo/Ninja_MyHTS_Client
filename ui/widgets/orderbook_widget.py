# widgets/orderbook_widget.py
from PyQt6.QtWidgets import QWidget, QTableWidgetItem


class OrderbookWidget(QWidget):
    def __init__(self, table_widget):
        self.table = table_widget
        self.table.setRowCount(20)
        self.table.setColumnWidth(0, 70)   # Bid
        self.table.setColumnWidth(1, 90)   # Price
        self.table.setColumnWidth(2, 70)   # Ask

    def update(self, bid, ask, price):
        """하나의 실시간 가격 update로 간단히 표시"""
        self.table.setItem(0, 0, QTableWidgetItem(str(bid)))
        self.table.setItem(0, 1, QTableWidgetItem(str(price)))
        self.table.setItem(0, 2, QTableWidgetItem(str(ask)))
