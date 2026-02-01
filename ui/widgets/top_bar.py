import webbrowser

from config.settings import DEFAULT_SYMBOLS
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime

# ui/widgets/top_bar.py
from PyQt6.QtWidgets import (
    QFrame, QLabel, QComboBox,
    QHBoxLayout, QVBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from ui.widgets.preferences_dialog import PreferencesDialog


class TopBarWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._setup_ui()
        self.set_dummy_data()   # 🔥 일단 더미부터

    # -------------------------------------------------
    def _setup_ui(self):
        self.setFixedHeight(40)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 4, 12, 4)
        root.setSpacing(14)

        # ===============================
        # LEFT : Symbol + Price
        # ===============================
        left = QHBoxLayout()
        left.setSpacing(10)

        self.comboSymbol = QComboBox()
        self.comboSymbol.addItems(DEFAULT_SYMBOLS)
        self.comboSymbol.setFixedWidth(130)

        self.labelPrice = QLabel("2,965.94")
        self.labelPrice.setFont(self._font(18, bold=True))
        self.labelPrice.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.labelChange = QLabel("-1.41 (-0.05%)")
        self.labelChange.setFont(self._font(11))

        # left.addWidget(self.comboSymbol)
        left.addWidget(self.labelPrice)
        left.addWidget(self.labelChange)

        # ===============================
        # MIDDLE : Stats
        # ===============================
        mid = QHBoxLayout()
        mid.setSpacing(16)

        self.labelHigh = QLabel("고가 --")
        self.labelLow = QLabel("저가 --")
        self.labelVolume = QLabel("거래량 --")

        for w in (
                self.labelHigh,
                self.labelLow,
                self.labelVolume,
        ):
            w.setFont(self._font(11))
            mid.addWidget(w)

        # ===============================
        # RIGHT : Status + Buttons
        # ===============================
        right = QHBoxLayout()
        right.setSpacing(8)

        self.labelLive = QLabel("● LIVE")
        self.labelLive.setFont(self._font(11, bold=True))

        # 🔥 버튼들
        self.btnSetting = QPushButton("환경설정")
        self.btnChart = QPushButton("차트보기")
        self.btnLogout = QPushButton("로그아웃")

        self.btnSetting.clicked.connect(self.open_preferences)
        self.btnChart.clicked.connect(self.on_open_chart)
        self.btnLogout.clicked.connect(self.logout)

        for btn in (self.btnSetting, self.btnChart, self.btnLogout):
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        right.addWidget(self.labelLive)
        right.addSpacing(12)
        right.addWidget(self.btnSetting)
        right.addWidget(self.btnChart)
        right.addWidget(self.btnLogout)

        # ===============================
        root.addLayout(left)
        root.addStretch()
        root.addLayout(mid)
        root.addStretch()
        root.addLayout(right)

    # -------------------------------------------------
    def _apply_style(self):
        self.setStyleSheet("""
        QFrame {
            background-color: #2b2b2b;
            border-bottom: 1px solid #1a1a1a;
        }
        QLabel {
            color: #dddddd;
        }
        QComboBox {
            background-color: #1f1f1f;
            color: #ff66cc;
            padding: 4px 8px;
            border-radius: 4px;
        }
        """)

        self.labelPrice.setStyleSheet("color:#FFD700;")
        self.labelChange.setStyleSheet("color:#ff4d4d;")
        self.labelHigh.setStyleSheet("color:#cccccc;")
        self.labelLow.setStyleSheet("color:#cccccc;")
        self.labelVolume.setStyleSheet("color:#cccccc;")
        self.labelLive.setStyleSheet("color:#2ecc71;")

    # -------------------------------------------------
    def _font(self, size, bold=False):
        f = QFont()
        f.setPointSize(size)
        f.setBold(bold)
        return f

    # -------------------------------------------------
    # 🔥 Dummy Data
    # -------------------------------------------------
    def set_dummy_data(self):
        self.labelPrice.setText("2,965.94")
        self.labelChange.setText("-1.41 (-0.05%)")

        self.labelHigh.setText("고가 2,967.81")
        self.labelLow.setText("저가 2,951.55")
        self.labelVolume.setText("거래량 15,002")

        self.set_live(True, 12)

    # -------------------------------------------------
    def set_live(self, live: bool, latency_ms: int | None = None):
        if live:
            self.labelLive.setText("● LIVE")
            self.labelLive.setStyleSheet("color:#2ecc71;")
        else:
            self.labelLive.setText("● OFF")
            self.labelLive.setStyleSheet("color:#e74c3c;")

        # TopBarWidget 내부에 추가

    # ===============================
    # 외부 업데이트 API
    # ===============================
    def update_price(self, price: float, diff: float, pct: float):
        self.labelPrice.setText(f"{price:,.2f}")

        sign = "+" if diff >= 0 else ""
        self.labelChange.setText(f"{sign}{diff:.2f} ({sign}{pct:.2f}%)")

        if diff > 0:
            self.labelChange.setStyleSheet("color:#ff4d4d;")
            self.labelPrice.setStyleSheet("color:#ff4d4d;")
        elif diff < 0:
            self.labelChange.setStyleSheet("color:#4da6ff;")
            self.labelPrice.setStyleSheet("color:#4da6ff;")
        else:
            self.labelChange.setStyleSheet("color:#aaaaaa;")
            self.labelPrice.setStyleSheet("color:#FFD700;")

    def update_stats(self, high, low, volume, funding):
        self.labelHigh.setText(f"고가 {high:,.2f}")
        self.labelLow.setText(f"저가 {low:,.2f}")
        self.labelVolume.setText(f"거래량 {volume:,}")

    def update_status(self, live: bool, latency_ms: int):
        if live:
            self.labelLive.setText("● LIVE")
            self.labelLive.setStyleSheet("color:#2ecc71;")
        else:
            self.labelLive.setText("● OFF")
            self.labelLive.setStyleSheet("color:#e74c3c;")

    def update_status_by_controller(self, status: str, latency: int):
        if status == "LIVE":
            self.labelLive.setText("● LIVE")
            self.labelLive.setStyleSheet("color:#2ecc71;")
        elif status == "DELAY":
            self.labelLive.setText("● DELAY")
            self.labelLive.setStyleSheet("color:#f1c40f;")
        else:
            self.labelLive.setText("● OFF")
            self.labelLive.setStyleSheet("color:#e74c3c;")


    # TopBarWidget 내부
    def reset(self, symbol: str):
        self.labelPrice.setText("--")
        self.labelChange.setText("+0.00 (+0.00%)")

        self.labelHigh.setText("고가 --")
        self.labelLow.setText("저가 --")
        self.labelVolume.setText("거래량 --")
        self.update_status(live=False, latency_ms=0)

    def open_preferences(self):
        dlg = PreferencesDialog(
            setting=self.main_window.trade_setting,
            parent=self
        )
        dlg.exec()

    def on_open_chart(self):
        symbol = self.main_window.current_symbol  # 예: "BTCUSDT"
        if symbol:
            self.open_tradingview(symbol)

    def open_tradingview(self, symbol: str):
        url = f"https://www.tradingview.com/chart/?symbol={symbol}"
        webbrowser.open(url)

        # self.chart_popup = ChartPopup(symbol, self)
        # self.chart_popup.show()
        #
        # # 테스트용 더미 캔들
        # candles = [
        #     {"time": "2024-12-01", "open": 88500, "high": 89000, "low": 88000, "close": 88800},
        #     {"time": "2024-12-02", "open": 88800, "high": 89500, "low": 88400, "close": 89200},
        #     {"time": "2024-12-03", "open": 89200, "high": 90000, "low": 89000, "close": 89800},
        # ]
        #
        # self.chart_popup.set_candles(candles)

    def logout(self):
        self.main_window.logout()


