# widgets/balance_widget.py
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QColor


class BalanceWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # =========================
        # 카드 생성
        # =========================
        self.cardEquity, self.lblEquity = self._make_card("총자산 (Equity)", 24, "#f1c40f")
        self.cardFree, self.lblMarginFree = self._make_card("가용 (Margin Free)")
        self.cardUsed, self.lblMarginUsed = self._make_card("사용중 (Margin Used)")
        self.cardRealized, self.lblRealizedPnL = self._make_card("실현손익")
        self.cardUnrealized, self.lblUnrealizedPnL = self._make_card("미실현손익")

        # =========================
        # Margin Progress Bar
        # =========================
        self.marginBar = QtWidgets.QProgressBar()
        self.marginBar.setRange(0, 100)
        self.marginBar.setFixedHeight(18)
        self.marginBar.setTextVisible(True)
        self.marginBar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.marginBar.setStyleSheet("""
            QProgressBar {
                background-color: #1f1f1f;
                border-radius: 6px;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 6px;
            }
        """)

        # =========================
        # Layout 구성
        # =========================
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self.cardEquity)
        top.addWidget(self.cardFree)
        top.addWidget(self.cardUsed)

        pnl = QtWidgets.QHBoxLayout()
        pnl.setSpacing(12)
        pnl.addWidget(self.cardRealized)
        pnl.addWidget(self.cardUnrealized)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addLayout(top)
        layout.addLayout(pnl)
        layout.addSpacing(6)

        lbl = QtWidgets.QLabel("Margin Usage")
        lbl.setStyleSheet("color:#aaaaaa; font-size:12px;")
        layout.addWidget(lbl)
        layout.addWidget(self.marginBar)

    # -------------------------------------------------
    # 카드 위젯 생성
    # -------------------------------------------------
    def _make_card(self, title, value_size=20, value_color="#ffffff"):
        title_lbl = QtWidgets.QLabel(title)
        title_lbl.setStyleSheet("color:#aaaaaa; font-size:12px;")

        value_lbl = QtWidgets.QLabel("0.00")
        value_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        value_lbl.setStyleSheet(
            f"color:{value_color}; font-size:{value_size}px; font-weight:600;"
        )

        box = QtWidgets.QVBoxLayout()
        box.setSpacing(4)
        box.addWidget(title_lbl)
        box.addWidget(value_lbl)

        wrap = QtWidgets.QWidget()
        wrap.setLayout(box)
        wrap.setStyleSheet("""
            QWidget {
                background-color: #2f2f2f;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        return wrap, value_lbl

    # -------------------------------------------------
    # Balance 갱신
    # -------------------------------------------------
    def update_balance(self, data: dict):
        """
        data 예시:
        {
            "balance": 8578.24,
            "margin_available": -39762.16,
            "margin_used": 45000.00,
            "pnl_realized": -1421.76,
            "pnl_unrealized": -3340.40
        }
        """
        try:
            equity = float(data.get("balance", 0.0))
            free = float(data.get("margin_available", 0.0))
            used = float(data.get("margin_used", 0.0))
            realized = float(data.get("pnl_realized", 0.0))
            unrealized = float(data.get("pnl_unrealized", 0.0))

            # 값 세팅
            self.lblEquity.setText(f"{equity:,.2f}")
            self.lblMarginFree.setText(f"{free:,.2f}")
            self.lblMarginUsed.setText(f"{used:,.2f}")
            self.lblRealizedPnL.setText(f"{realized:,.2f}")
            self.lblUnrealizedPnL.setText(f"{unrealized:,.2f}")

            # 손익 색상
            self.lblRealizedPnL.setStyleSheet(
                f"color:{'#2ecc71' if realized >= 0 else '#e74c3c'}; "
                "font-size:20px; font-weight:600;"
            )
            self.lblUnrealizedPnL.setStyleSheet(
                f"color:{'#2ecc71' if unrealized >= 0 else '#e74c3c'}; "
                "font-size:20px; font-weight:600;"
            )

            # Margin Usage 계산
            total = abs(free) + used
            usage = int((used / total) * 100) if total > 0 else 0
            usage = min(max(usage, 0), 100)

            self.marginBar.setValue(usage)

            # 위험도 색상
            if usage >= 80:
                color = "#e74c3c"     # 위험
            elif usage >= 60:
                color = "#f39c12"     # 경고
            else:
                color = "#2ecc71"     # 안전

            self.marginBar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)

        except Exception as e:
            print("[BalanceWidget] update_balance error:", e)
