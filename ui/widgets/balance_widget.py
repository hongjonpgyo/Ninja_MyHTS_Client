from PyQt6 import QtWidgets, QtCore, QtGui


class BalanceWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------------------
        # Label Components
        # ---------------------------
        self.lblEquity = QtWidgets.QLabel("0.00")
        self.lblMarginFree = QtWidgets.QLabel("0.00")
        self.lblMarginUsed = QtWidgets.QLabel("0.00")
        self.lblRealizedPnL = QtWidgets.QLabel("0.00")
        self.lblUnrealizedPnL = QtWidgets.QLabel("0.00")

        # 숫자 정렬
        for w in [
            self.lblEquity, self.lblMarginFree, self.lblMarginUsed,
            self.lblRealizedPnL, self.lblUnrealizedPnL
        ]:
            w.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # ---------------------------
        # Layout 구성
        # ---------------------------
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("총자산 (Equity):"), 0, 0)
        grid.addWidget(self.lblEquity, 0, 1)

        grid.addWidget(QtWidgets.QLabel("가용 (Margin Free):"), 1, 0)
        grid.addWidget(self.lblMarginFree, 1, 1)

        grid.addWidget(QtWidgets.QLabel("사용중 (Margin Used):"), 2, 0)
        grid.addWidget(self.lblMarginUsed, 2, 1)

        grid.addWidget(QtWidgets.QLabel("실현손익:"), 3, 0)
        grid.addWidget(self.lblRealizedPnL, 3, 1)

        grid.addWidget(QtWidgets.QLabel("미실현손익:"), 4, 0)
        grid.addWidget(self.lblUnrealizedPnL, 4, 1)

        self.setLayout(grid)

    # ---------------------------------------------------------
    # Balance 갱신 (MainWindow → safe_ui 로 호출됨)
    # ---------------------------------------------------------
    def update_balance(self, data: dict):
        """
        백엔드 응답 예시:
        {
            "balance": 12634.9516,
            "margin_used": 1704,
            "margin_available": 5365.1278,
            "pnl_realized": 2634.9516,
            "pnl_unrealized": -5565.8238
        }
        """
        try:
            equity = float(data.get("balance", 0.0))
            margin_free = float(data.get("margin_available", 0.0))
            margin_used = float(data.get("margin_used", 0.0))
            pnl_realized = float(data.get("pnl_realized", 0.0))
            pnl_unrealized = float(data.get("pnl_unrealized", 0.0))

            # 숫자 표시
            self.lblEquity.setText(f"{equity:,.2f}")
            self.lblMarginFree.setText(f"{margin_free:,.2f}")
            self.lblMarginUsed.setText(f"{margin_used:,.2f}")
            self.lblRealizedPnL.setText(f"{pnl_realized:,.2f}")
            self.lblUnrealizedPnL.setText(f"{pnl_unrealized:,.2f}")

            # ---------------------------
            # Color Styling
            # ---------------------------

            # 실현손익 (Realized)
            if pnl_realized >= 0:
                self.lblRealizedPnL.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.lblRealizedPnL.setStyleSheet("color: #F44336; font-weight: bold;")

            # 미실현손익 (Unrealized)
            if pnl_unrealized >= 0:
                self.lblUnrealizedPnL.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.lblUnrealizedPnL.setStyleSheet("color: #F44336; font-weight: bold;")

        except Exception as e:
            print("[BalanceWidget] Update Error:", e)
