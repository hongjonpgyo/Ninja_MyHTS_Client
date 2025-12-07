from PyQt6 import QtWidgets, QtCore, QtGui

class OpenOrdersWidget(QtWidgets.QWidget):
    def __init__(self, order_api, account_id):
        super().__init__()

        self.order_api = order_api   # ✅ 동기 API 사용
        self.account_id = account_id

        self.setWindowTitle("미체결 주문")
        self.resize(850, 420)

        layout = QtWidgets.QVBoxLayout(self)

        # 테이블
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "OrderID", "Symbol", "Side", "Price",
            "Qty", "Status", "Time"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QTableWidget.SelectionMode.MultiSelection)

        layout.addWidget(self.table)

        # 버튼
        btn_layout = QtWidgets.QHBoxLayout()
        self.btnCancel = QtWidgets.QPushButton("선택 주문 취소")
        self.btnRefresh = QtWidgets.QPushButton("새로고침")

        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnRefresh)
        layout.addLayout(btn_layout)

        # 시그널
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnCancel.clicked.connect(self.cancel_selected_orders)

        # 타이머
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.refresh()

    # -----------------------------------------------------
    def refresh(self):
        try:
            orders = self.order_api.get_open_orders(self.account_id)  # ✅ 동기 API

            if not isinstance(orders, list):
                print("[OpenOrdersWidget] Unexpected response:", orders)
                return

            self.update_table(orders)

        except Exception as e:
            print("[OpenOrdersWidget] fetch error:", e)

    # -----------------------------------------------------
    def update_table(self, orders):
        self.table.setRowCount(len(orders))

        for row, od in enumerate(orders):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(od["order_id"])))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(od["symbol"]))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(od["side"]))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(od["price"])))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(od["qty"])))
            # self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(od["filled_qty"])))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(od["status"]))
            self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(od["created_at"]))

            # 색상 처리
            side_item = self.table.item(row, 2)
            if od["side"] == "BUY":
                side_item.setForeground(QtGui.QBrush(QtGui.QColor("#2ecc71")))
            else:
                side_item.setForeground(QtGui.QBrush(QtGui.QColor("#e74c3c")))

    # -----------------------------------------------------
    def cancel_selected_orders(self):
        rows = {idx.row() for idx in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "알림", "선택된 주문이 없습니다.")
            return

        order_ids = [int(self.table.item(r, 0).text()) for r in rows]

        res = self.order_api.cancel_orders(order_ids)

        if res.get("ok"):
            QtWidgets.QMessageBox.information(self, "완료", "주문 취소 완료되었습니다.")
        else:
            QtWidgets.QMessageBox.warning(self, "오류", f"취소 실패: {res}")

        self.refresh()
