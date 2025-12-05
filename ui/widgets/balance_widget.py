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
        try:
            equity = float(data.get("balance", 0))
            margin_free = float(data.get("margin_available", 0))
            margin_used = float(data.get("margin_used", 0))
            pnl_realized = float(data.get("pnl_realized", 0))
            pnl_unrealized = float(data.get("pnl_unrealized", 0))

            # 숫자 포맷 적용
            self.equity.setText(f"{equity:,.2f}")
            self.free_margin.setText(f"{margin_free:,.2f}")
            self.used_margin.setText(f"{margin_used:,.2f}")
            self.realized_pnl.setText(f"{pnl_realized:,.2f}")
            self.unrealized_pnl.setText(f"{pnl_unrealized:,.2f}")

            # 색상 처리 (Realized PnL)
            if pnl_realized >= 0:
                self.realized_pnl.setStyleSheet("color: #4CAF50;")
            else:
                self.realized_pnl.setStyleSheet("color: #F44336;")

            # 색상 처리 (Unrealized PnL)
            if pnl_unrealized >= 0:
                self.unrealized_pnl.setStyleSheet("color: #4CAF50;")
            else:
                self.unrealized_pnl.setStyleSheet("color: #F44336;")

        except Exception as e:
            print("[BalanceWidget] Update Error:", e)
