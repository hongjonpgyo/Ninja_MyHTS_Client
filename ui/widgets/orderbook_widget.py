from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor, QBrush


class OrderbookWidget:

    def __init__(self, table: QTableWidget):
        self.table = table
        self.setup()

    def setup(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Bid", "Price", "Ask"])
        self.table.setRowCount(20)

        for row in range(20):
            for col in range(3):
                item = QTableWidgetItem("")
                item.setTextAlignment(0x0004 | 0x0080)
                self.table.setItem(row, col, item)

    def update_depth(self, bids, asks):
        """
        bids, asks = [[price, my_qty], ...]
            → price: Binance 실시간 가격
            → my_qty: 내 주문 수량 (없으면 0)
        """

        for i in range(20):
            # --------------------------
            # BID 영역 (좌측)
            # --------------------------
            if i < len(bids):
                price = float(bids[i][0])
                my_qty = float(bids[i][1])

                item_bid = self.table.item(i, 0)
                item_price = self.table.item(i, 1)

                item_bid.setText(f"{my_qty:,.3f}" if my_qty else "")
                item_price.setText(f"{price:,.2f}")

                # ---- BID 하이라이트 ----
                if my_qty > 0:
                    color = QColor(25, 118, 210, 80)  # 블루 투명
                    item_bid.setBackground(QBrush(color))
                    item_price.setBackground(QBrush(color))
                else:
                    item_bid.setBackground(QBrush())
                    item_price.setBackground(QBrush())

            else:
                self.table.item(i, 0).setText("")
                self.table.item(i, 1).setText("")

        # --------------------------
        # ASK 영역 (오른쪽)
        # --------------------------
        for i in range(20):
            if i < len(asks):
                price = float(asks[i][0])
                my_qty = float(asks[i][1])

                item_ask = self.table.item(i, 2)

                item_ask.setText(f"{my_qty:,.3f}" if my_qty else "")

                # ---- ASK 하이라이트 ----
                if my_qty > 0:
                    color = QColor(211, 47, 47, 80)  # 레드 투명
                    item_ask.setBackground(QBrush(color))
                else:
                    item_ask.setBackground(QBrush())

            else:
                self.table.item(i, 2).setText("")

    def clear(self):
        self.table.clearContents()
        self.table.setRowCount(0)
