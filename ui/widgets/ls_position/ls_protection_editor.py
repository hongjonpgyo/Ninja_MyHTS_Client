from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class LSProtectionEditor(QWidget):

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        # --- TP ---
        self.lbl_tp = QLabel("TP")
        self.lbl_tp.setStyleSheet("color:#2ecc71; font-weight:bold;")

        self.tp_price = QLineEdit()
        self.tp_price.setPlaceholderText("익절가")
        self.tp_price.setFixedWidth(90)

        self.tp_qty = QSpinBox()
        self.tp_qty.setMinimum(1)
        self.tp_qty.setFixedWidth(60)

        # --- SL ---
        self.lbl_sl = QLabel("SL")
        self.lbl_sl.setStyleSheet("color:#e74c3c; font-weight:bold;")

        self.sl_price = QLineEdit()
        self.sl_price.setPlaceholderText("손절가")
        self.sl_price.setFixedWidth(90)

        self.sl_qty = QSpinBox()
        self.sl_qty.setMinimum(1)
        self.sl_qty.setFixedWidth(60)

        # --- Buttons ---
        self.btn_apply = QPushButton("적용")
        self.btn_apply.setFixedWidth(70)

        self.btn_clear = QPushButton("해제")
        self.btn_clear.setFixedWidth(70)

        # --- Layout ---
        layout.addWidget(self.lbl_tp)
        layout.addWidget(self.tp_price)
        layout.addWidget(QLabel("수량"))
        layout.addWidget(self.tp_qty)

        layout.addSpacing(20)

        layout.addWidget(self.lbl_sl)
        layout.addWidget(self.sl_price)
        layout.addWidget(QLabel("수량"))
        layout.addWidget(self.sl_qty)

        layout.addStretch()

        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_clear)

        # --- Background ---
        self.setStyleSheet("""
            QWidget {
                background-color: #1c1c1c;
                color: #cccccc;
            }
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                padding: 2px;
            }
            QSpinBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                padding: 2px;
            }
        """)
