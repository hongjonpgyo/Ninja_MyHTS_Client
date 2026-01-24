from PyQt6.QtWidgets import (
    QFrame, QLabel, QComboBox,
    QHBoxLayout, QVBoxLayout, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class SymbolSummaryWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(120)

        grid = QGridLayout(self)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(4)

        fields = [
            ("전일", "--"), ("틱가치", "--"),
            ("시가", "--"), ("환율", "--"),
            ("저가", "--"), ("만기일", "--"),
            ("고가", "--"), ("잔존일수", "--"),
        ]

        self.labels = {}

        for i, (k, v) in enumerate(fields):
            r = i // 2
            c = (i % 2) * 2

            key = QLabel(k)
            val = QLabel(v)

            key.setAlignment(Qt.AlignmentFlag.AlignLeft)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)

            grid.addWidget(key, r, c)
            grid.addWidget(val, r, c + 1)

            self.labels[k] = val

    def update_ls_symbol(self, row: dict):
        self.labels["전일"].setText(f"{row.get('close_p', '--')}")
        self.labels["시가"].setText(f"{row.get('open_p', '--')}")
        self.labels["고가"].setText(f"{row.get('high_p', '--')}")
        self.labels["저가"].setText(f"{row.get('low_p', '--')}")
        self.labels["틱가치"].setText(f"{row.get('tick_value', '--')}")
        self.labels["환율"].setText(row.get("crncy_cd", "--"))

        self.labels["만기일"].setText(row.get("mrtr_dt", "--"))
        self.labels["잔존일수"].setText(
            f"{row['remain_days']}일" if row.get("remain_days") is not None else "--"
        )


