from PyQt6 import QtWidgets, QtCore

class BalanceWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.equity = QtWidgets.QLabel("0")
        self.free_margin = QtWidgets.QLabel("0")
        self.used_margin = QtWidgets.QLabel("0")
        self.realized_pnl = QtWidgets.QLabel("0")
        self.unrealized_pnl = QtWidgets.QLabel("0")

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("총자산(Equity):"), 0, 0)
        grid.addWidget(self.equity, 0, 1)

        grid.addWidget(QtWidgets.QLabel("가용(Margin Free):"), 1, 0)
        grid.addWidget(self.free_margin, 1, 1)

        grid.addWidget(QtWidgets.QLabel("사용중(Margin Used):"), 2, 0)
        grid.addWidget(self.used_margin, 2, 1)

        grid.addWidget(QtWidgets.QLabel("실현손익:"), 3, 0)
        grid.addWidget(self.realized_pnl, 3, 1)

        grid.addWidget(QtWidgets.QLabel("미실현손익:"), 4, 0)
        grid.addWidget(self.unrealized_pnl, 4, 1)

        self.setLayout(grid)

    def update_balance(self, data: dict):
        self.equity.setText(f"{data['equity']:,}")
        self.free_margin.setText(f"{data['free_margin']:,}")
        self.used_margin.setText(f"{data['used_margin']:,}")

        rp = data["realized_pnl"]
        up = data["unrealized_pnl"]

        self.realized_pnl.setText(f"{rp:+,.2f}")
        self.unrealized_pnl.setText(f"{up:+,.2f}")

        # 색상 적용
        self.realized_pnl.setStyleSheet("color: green;" if rp >= 0 else "color: red;")
        self.unrealized_pnl.setStyleSheet("color: green;" if up >= 0 else "color: red;")
