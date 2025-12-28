# ui/widgets/top_ticker_bar.py
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt


class TopTickerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(52)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-bottom: 1px solid #1f1f1f;
            }
        """)

        price_font = QFont("Arial", 16, QFont.Weight.Bold)
        normal_font = QFont("Arial", 11)

        self.lblSymbol = QLabel("ETHUSDT ▼")
        self.lblSymbol.setFont(normal_font)
        self.lblSymbol.setStyleSheet("color:#ff5fa2;")

        self.lblPrice = QLabel("2,951.55")
        self.lblPrice.setFont(price_font)
        self.lblPrice.setStyleSheet("color:#ffd54f;")

        self.lblChange = QLabel("+0.00 (+0.00%)")
        self.lblChange.setFont(normal_font)
        self.lblChange.setStyleSheet("color:#aaaaaa;")

        self.lblMetrics = QLabel(
            "고가 2,980.20   저가 2,910.40   거래량 12,430   펀딩 +0.01%"
        )
        self.lblMetrics.setFont(normal_font)
        self.lblMetrics.setStyleSheet("color:#cccccc;")

        self.lblStatus = QLabel("● LIVE   WS 12ms")
        self.lblStatus.setFont(normal_font)
        self.lblStatus.setStyleSheet("color:#2ecc71;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        layout.addWidget(self.lblSymbol)
        layout.addWidget(self.lblPrice)
        layout.addWidget(self.lblChange)
        layout.addSpacing(20)
        layout.addWidget(self.lblMetrics)
        layout.addStretch()
        layout.addWidget(self.lblStatus)
