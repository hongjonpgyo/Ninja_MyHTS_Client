from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox,
    QRadioButton, QPushButton, QHBoxLayout
)
from ui.settings.trade_setting import OrderClickMode

class PreferencesDialog(QDialog):
    def __init__(self, setting, parent=None):
        super().__init__(parent)
        self.setting = setting
        self.setWindowTitle("환경설정")
        self.setFixedSize(320, 220)

        root = QVBoxLayout(self)

        # ==========================
        # 주문 방식
        # ==========================
        group = QGroupBox("주문 방식")
        v = QVBoxLayout(group)

        self.radioSingle = QRadioButton("싱글 클릭 주문")
        self.radioDouble = QRadioButton("더블 클릭 주문 (권장)")

        v.addWidget(self.radioSingle)
        v.addWidget(self.radioDouble)

        root.addWidget(group)

        # ==========================
        # 버튼
        # ==========================
        btns = QHBoxLayout()
        btns.addStretch()

        btnOk = QPushButton("확인")
        btnCancel = QPushButton("취소")

        btnOk.clicked.connect(self.apply)
        btnCancel.clicked.connect(self.reject)

        btns.addWidget(btnOk)
        btns.addWidget(btnCancel)

        root.addLayout(btns)

        self._load_setting()

    def _load_setting(self):
        if self.setting.order_click_mode == OrderClickMode.SINGLE:
            self.radioSingle.setChecked(True)
        else:
            self.radioDouble.setChecked(True)

    def apply(self):
        if self.radioSingle.isChecked():
            self.setting.order_click_mode = OrderClickMode.SINGLE
        else:
            self.setting.order_click_mode = OrderClickMode.DOUBLE

        self.accept()
