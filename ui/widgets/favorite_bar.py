from PyQt6.QtWidgets import (
    QFrame, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from ui.utils.ls_symbol_name import display_symbol_name


class FavoriteBar(QFrame):
    symbolClicked = pyqtSignal(str)  # 🔥 심볼 클릭 시

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('FavoriteBar')
        self.buttons = {}   # symbol -> button
        self.active_symbol = None
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
            border-radius: 0px;
            padding: 4px 10px;
            font-size: 14px;
            color: #dddddd;
            min-height: 21px;
            padding-top: 4px;
            padding-bottom: 4px;
        }
        QPushButton:hover {
            background-color: #333333;
        }
        QPushButton:checked {
            background-color: #355f7a;
            border: 1px solid #4da3ff;
            color: #ffffff;
            font-weight: bold;
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

        display_name, _ = display_symbol_name(symbol)

        btn = QPushButton(display_name)
        btn.setCheckable(True)  # 🔥 토글 버튼
        btn.setToolTip(symbol)
        btn.clicked.connect(lambda _, s=symbol: self._on_button_clicked(s))

        self.layout.insertWidget(
            self.layout.count() - 1, btn
        )
        self.buttons[symbol] = btn

    def _on_button_clicked(self, symbol: str):
        self.set_active(symbol)
        self.symbolClicked.emit(symbol)

    def set_active(self, symbol: str):
        if self.active_symbol == symbol:
            return

        for sym, btn in self.buttons.items():
            btn.setChecked(sym == symbol)

        self.active_symbol = symbol

    def remove_symbol(self, symbol: str):
        btn = self.buttons.pop(symbol, None)
        if btn:
            btn.setParent(None)
            btn.deleteLater()


    def clear(self):
        """
        모든 즐겨찾기 버튼 제거
        """
        for btn in self.buttons.values():
            btn.deleteLater()

        self.buttons.clear()
