# ui/widgets/balance_widget.py

from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class BalanceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    # -------------------------------------------------
    def _init_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 8, 12, 8)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)

        title_font = QFont()
        title_font.setPointSize(11)

        value_font = QFont()
        value_font.setPointSize(12)
        value_font.setBold(True)

        def make_title(text):
            lbl = QLabel(text)
            lbl.setFont(title_font)
            lbl.setStyleSheet("color:#b0b0b0;")
            return lbl

        def make_value(text="0"):
            lbl = QLabel(text)
            lbl.setFont(value_font)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color:#e0e0e0;")
            return lbl

        # ==========================
        # 상단 요약
        # ==========================
        self.lbl_deposit = make_value("0")
        self.lbl_over = make_value("0")
        self.lbl_available = make_value("0")
        self.lbl_cut = make_value("0")
        self.lbl_margin = make_value("0")

        titles_top = [
            ("예탁금", self.lbl_deposit),
            ("오버금액", self.lbl_over),
            ("가용예탁금", self.lbl_available),
            ("로스컷기준", self.lbl_cut),
            ("로스컷여유", self.lbl_margin),
        ]

        col = 0
        for title, value in titles_top:
            grid.addWidget(make_title(title), 0, col, Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(value, 1, col, Qt.AlignmentFlag.AlignRight)
            col += 1

        # ==========================
        # 하단 요약
        # ==========================
        self.lbl_eval_pnl = make_value("0")
        self.lbl_eval_rate = make_value("0.00%")
        self.lbl_today_pnl = make_value("0")
        self.lbl_eval_margin = make_value("0")

        titles_bottom = [
            ("평가손익", self.lbl_eval_pnl),
            ("평가손익률", self.lbl_eval_rate),
            ("당일실현손익", self.lbl_today_pnl),
            ("평가증거금", self.lbl_eval_margin),
        ]

        col = 0
        for title, value in titles_bottom:
            grid.addWidget(make_title(title), 2, col, Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(value, 3, col, Qt.AlignmentFlag.AlignRight)
            col += 1

        self.setLayout(grid)

        self.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
        }
        """)

    # -------------------------------------------------
    # 🔥 나중에 연결할 API
    # -------------------------------------------------
    def update_balance(self, account: dict):
        """
        account 예시:
        {
          deposit, over_amount, available,
          cut_price, margin,
          eval_pnl, eval_rate, today_pnl, eval_margin
        }
        """

        def set_money(label, value):
            label.setText(f"{value:,.0f}")

        def set_pnl(label, value):
            label.setText(f"{value:,.0f}")
            if value > 0:
                label.setStyleSheet("color:#2ecc71;")
            elif value < 0:
                label.setStyleSheet("color:#e74c3c;")
            else:
                label.setStyleSheet("color:#e0e0e0;")

        set_money(self.lbl_deposit, account.get("deposit", 0))
        set_money(self.lbl_over, account.get("over_amount", 0))
        set_money(self.lbl_available, account.get("available", 0))
        set_money(self.lbl_cut, account.get("cut_price", 0))
        set_money(self.lbl_margin, account.get("margin", 0))

        pnl = account.get("eval_pnl", 0)
        set_pnl(self.lbl_eval_pnl, pnl)

        rate = account.get("eval_rate", 0.0)
        self.lbl_eval_rate.setText(f"{rate:.2f}%")

        set_pnl(self.lbl_today_pnl, account.get("today_pnl", 0))
        set_money(self.lbl_eval_margin, account.get("eval_margin", 0))
