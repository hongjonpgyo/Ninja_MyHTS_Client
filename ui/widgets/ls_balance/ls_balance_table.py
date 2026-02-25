from ui.utils.formatter import fmt_money, fmt_pnl, fmt_rate
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LSBalanceTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("LSBalanceTable")

        # ===============================
        # Fonts
        # ===============================
        self.font_key = QFont()
        self.font_key.setPointSize(11)

        self.font_value = QFont()
        self.font_value.setPointSize(12)
        self.font_value.setBold(True)

        self.font_pnl = QFont()
        self.font_pnl.setPointSize(15)
        self.font_pnl.setBold(True)

        # ===============================
        # Layout
        # ===============================
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(6)

        # ===============================
        # Value Widgets
        # ===============================
        self.lblDeposit = self._make_value()
        self.lblUsedMargin = self._make_value()
        self.lblAvailable = self._make_value()

        self.lblPnL = self._make_value(font=self.font_pnl)
        self.lblPnLRate = self._make_value()
        self.lblEquity = self._make_value()

        # ===============================
        # Grid Layout (3열 × 2행)
        # ===============================
        # Row 0
        layout.addWidget(self._make_key("예탁금"),       0, 0)
        layout.addWidget(self.lblDeposit,               0, 1)

        layout.addWidget(self._make_key("사용증거금"),   0, 2)
        layout.addWidget(self.lblUsedMargin,            0, 3)

        layout.addWidget(self._make_key("가용예탁금"),   0, 4)
        layout.addWidget(self.lblAvailable,             0, 5)

        # Row 1
        layout.addWidget(self._make_key("평가손익"),     1, 0)
        layout.addWidget(self.lblPnL,                   1, 1)

        layout.addWidget(self._make_key("평가손익률"),   1, 2)
        layout.addWidget(self.lblPnLRate,               1, 3)

        layout.addWidget(self._make_key("계좌평가"),     1, 4)
        layout.addWidget(self.lblEquity,                1, 5)

        # 컬럼 비율 조정 (숫자 영역 넓게)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(3, 2)
        layout.setColumnStretch(5, 2)

    # ==================================================
    # Widget factories
    # ==================================================
    def _make_key(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self.font_key)
        lbl.setStyleSheet("color:#9a9a9a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    def _make_value(self, font: QFont | None = None) -> QLabel:
        lbl = QLabel("0")
        lbl.setFont(font or self.font_value)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet("color:#e0e0e0;")
        return lbl

    # ==================================================
    # Update
    # ==================================================
    def update_balance(self, data: dict):
        if not data:
            return

        deposit = float(data.get("deposit", 0))
        used_margin = float(data.get("used_margin", 0))
        available = float(data.get("available", 0))
        pnl = float(data.get("unrealized_pnl", 0))
        rate = float(data.get("unrealized_pnl_rate", 0))
        equity = float(data.get("equity", 0))

        # 텍스트 반영
        self.lblDeposit.setText(fmt_money(deposit))
        self.lblUsedMargin.setText(fmt_money(used_margin))
        self.lblAvailable.setText(fmt_money(available))
        self.lblPnL.setText(fmt_pnl(pnl))
        self.lblPnLRate.setText(fmt_rate(rate) + "%")
        self.lblEquity.setText(fmt_money(equity))

        # 색상 적용
        self._apply_pnl_color(pnl)
        self._apply_available_color(available)
        self._apply_used_margin_style()

    # ==================================================
    # Color / Style
    # ==================================================
    def _apply_pnl_color(self, pnl: float):
        if pnl > 0:
            color = "#2ecc71"   # 초록
        elif pnl < 0:
            color = "#e74c3c"   # 빨강
        else:
            color = "#cccccc"

        self.lblPnL.setStyleSheet(f"color:{color};")
        self.lblPnLRate.setStyleSheet(f"color:{color};")

    def _apply_available_color(self, available: float):
        # 가용예탁금이 0 이하이면 위험 표시
        if available < 0:
            self.lblAvailable.setStyleSheet("color:#e74c3c;")
        else:
            self.lblAvailable.setStyleSheet("color:#e0e0e0;")

    def _apply_used_margin_style(self):
        # 사용증거금은 주황색 고정
        self.lblUsedMargin.setStyleSheet("color:#f39c12;")