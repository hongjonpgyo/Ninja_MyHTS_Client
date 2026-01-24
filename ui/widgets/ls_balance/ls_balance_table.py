from ui.utils.formatter import fmt_money, fmt_pnl, fmt_rate
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LSBalanceTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("LSBalanceTable")
        self.setAutoFillBackground(True)

        # ===============================
        # Fonts
        # ===============================
        self.font_label = QFont()
        self.font_label.setPointSize(11)

        self.font_value = QFont()
        self.font_value.setPointSize(12)
        self.font_value.setBold(True)

        # ===============================
        # Layout
        # ===============================
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setHorizontalSpacing(24)
        layout.setVerticalSpacing(6)

        # ===============================
        # Widgets
        # ===============================
        self.lblDeposit = QLabel("0")
        self.lblAvailable = QLabel("0")
        self.lblPnL = QLabel("0")
        self.lblPnLRate = QLabel("0.00%")

        # ===============================
        # Apply styles
        # ===============================
        for lbl in (
            self.lblDeposit,
            self.lblAvailable,
            self.lblPnL,
            self.lblPnLRate,
        ):
            lbl.setFont(self.font_value)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color:#e0e0e0;")

        def title(text):
            l = QLabel(text)
            l.setFont(self.font_label)
            l.setStyleSheet("color:#aaaaaa;")
            l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            return l

        # ===============================
        # Grid
        # ===============================
        layout.addWidget(title("예탁금"),        0, 0)
        layout.addWidget(self.lblDeposit,        0, 1)

        layout.addWidget(title("가용예탁금"),    0, 2)
        layout.addWidget(self.lblAvailable,      0, 3)

        layout.addWidget(title("평가손익"),      1, 0)
        layout.addWidget(self.lblPnL,            1, 1)

        layout.addWidget(title("평가손익률"),    1, 2)
        layout.addWidget(self.lblPnLRate,        1, 3)

    # ==================================================
    # Update
    # ==================================================
    def update_balance(self, data: dict):
        if not data:
            return

        deposit = float(data.get("deposit", 0))
        available = float(data.get("available", 0))
        pnl = float(data.get("unrealized_pnl", 0))
        rate = float(data.get("unrealized_pnl_rate", 0))

        self.lblDeposit.setText(fmt_money(deposit))
        self.lblAvailable.setText(fmt_money(available))
        self.lblPnL.setText(fmt_pnl(pnl))
        self.lblPnLRate.setText(fmt_rate(rate) + "%")

        # 손익 컬러
        if pnl > 0:
            color = "#2ecc71"
        elif pnl < 0:
            color = "#e74c3c"
        else:
            color = "#cccccc"

        self.lblPnL.setStyleSheet(f"color:{color};")
        self.lblPnLRate.setStyleSheet(f"color:{color};")
