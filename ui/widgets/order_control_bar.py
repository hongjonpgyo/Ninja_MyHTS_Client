from PyQt6.QtWidgets import QFrame, QPushButton, QHBoxLayout


class OrderControlBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        layout.addStretch()
        
        self.btnSellReserveCancel = QPushButton("매도예약취소")
        self.btnSellCancel = QPushButton("매도취소")
        self.btnCancelAll = QPushButton("일괄취소")
        self.btnCancelSymbol = QPushButton("종목취소")
        self.btnBuyCancel = QPushButton("매수취소")
        self.btnBuyReserveCancel = QPushButton("매수예약취소")

        for btn in (
            self.btnSellReserveCancel,
            self.btnSellCancel,
            self.btnCancelAll,
            self.btnCancelSymbol,
            self.btnBuyCancel,
            self.btnBuyReserveCancel,
        ):
            btn.setFixedHeight(28)
            layout.addWidget(btn)

        layout.addStretch()

    def _apply_style(self):
        self.setStyleSheet("""
        QFrame {
            background: transparent;
            border: none;
        }
        QPushButton {
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            color: #dddddd;
        }
        QPushButton:hover {
            background-color: #333333;
        }
        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        """)

