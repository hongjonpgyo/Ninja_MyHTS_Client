from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor


class OrderbookWidget:

    def __init__(self, table: QTableWidget):
        self.table = table
        self.setup()

    def setup(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Bid", "Price", "Ask"])
        self.table.setRowCount(20)

        # 정렬 및 초기화
        for row in range(20):
            for col in range(3):
                item = QTableWidgetItem("")
                item.setTextAlignment(0x0004 | 0x0080)
                self.table.setItem(row, col, item)

    def update_depth(self, bids, asks):
        """
        bids, asks는 Binance depth20 형식:
        bids = [["가격", "수량"], ...]
        asks = [["가격", "수량"], ...]
        """

        # Bid는 가격 높은 순 → HTS 화면은 아래 방향으로(대부분)
        for i in range(20):
            if i < len(bids):
                price = float(bids[i][0])
                size = float(bids[i][1])
                self.table.item(i, 0).setText(f"{size:,.3f}")
                self.table.item(i, 1).setText(f"{price:,.2f}")
            else:
                self.table.item(i, 0).setText("")
                self.table.item(i, 1).setText("")

        # Ask는 가격 낮은 순 → HTS는 위 방향으로 보통 표시
        for i in range(20):
            if i < len(asks):
                price = float(asks[i][0])
                size = float(asks[i][1])
                self.table.item(i, 2).setText(f"{size:,.3f}")
            else:
                self.table.item(i, 2).setText("")
