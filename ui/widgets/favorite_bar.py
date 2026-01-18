from PyQt6.QtWidgets import (
    QFrame, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal


class FavoriteBar(QFrame):
    symbolClicked = pyqtSignal(str)  # 🔥 심볼 클릭 시

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('FavoriteBar')
        self.buttons = {}   # symbol -> button
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFixedHeight(36)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 6)
        self.layout.setSpacing(6)
        self.layout.addStretch()

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

    # -----------------------------
    # 외부 API
    # -----------------------------
    def add_symbol(self, symbol: str):
        if symbol in self.buttons:
            return

        btn = QPushButton(symbol)
        btn.clicked.connect(lambda: self.symbolClicked.emit(symbol))

        self.layout.insertWidget(
            self.layout.count() - 1, btn
        )
        self.buttons[symbol] = btn

    def remove_symbol(self, symbol: str):
        btn = self.buttons.pop(symbol, None)
        if btn:
            btn.setParent(None)
            btn.deleteLater()
