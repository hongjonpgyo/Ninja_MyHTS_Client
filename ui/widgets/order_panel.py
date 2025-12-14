from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QTableWidget, QHeaderView
from PyQt6.uic import loadUi

from config.tick_size import TICK_SIZE


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel.ui", self)

        # 수량 단위
        self.tick_size = 0.01

        # 주문타입 콤보박스 변경 이벤트
        self.comboType.currentTextChanged.connect(self.on_order_type_changed)

        self.editOrderPrice.editingFinished.connect(self._on_price_edit_finished)

        # 버튼 연결
        self.btnQtyPlus.clicked.connect(self.on_qty_plus)
        self.btnQtyMinus.clicked.connect(self.on_qty_minus)
        self.btnQtyHalf.clicked.connect(self.on_qty_half)
        self.btnQtyDouble.clicked.connect(self.on_qty_double)

        self.price_locked = False

    def _round_to_tick(self, price: float) -> float:
        tick = self.tick_size
        return round(round(price / tick) * tick, 8)

    def _on_price_edit_finished(self):
        price = self.get_limit_price()
        if price is None:
            return

        price = self._round_to_tick(price)
        self.editOrderPrice.setText(f"{price:.2f}")

    # =========================
    # ⭐ 현재가 세팅 (PriceController용)
    # =========================
    def set_price(self, price: float):
        price = self._round_to_tick(price)
        # labelPrice가 있다면 갱신
        if hasattr(self, "labelPrice"):
            self.labelPrice.setText(f"{price:,.2f}")

        # 🔒 사용자가 호가 클릭해서 가격 잠그면 editOrderPrice 덮어쓰지 않음
        if getattr(self, "price_locked", False):
            return

        if hasattr(self, "editOrderPrice"):
            self.editOrderPrice.setText(f"{price:.2f}")

    def reset_position(self):
        self.valuePostionQty.setText("0")
        self.valueAvgPrice.setText("0.00")
        self.valuePnl.setText("0.00")
        self.valueLiq.setText("-")

        gray = "color:#888;"
        self.valuePostionQty.setStyleSheet(gray)
        self.valueAvgPrice.setStyleSheet(gray)
        self.valuePnl.setStyleSheet(gray)
        self.valueLiq.setStyleSheet(gray)

    def update_position(self, pos):
        qty = float(pos.get("qty", 0))
        pnl = float(pos.get("unrealized_pnl", 0))
        entry = float(pos.get("entry_price", 0))
        liq = pos.get("liq_price")

        self.valuePostionQty.setText(f"{qty:.4f}".rstrip("0").rstrip("."))
        self.valueAvgPrice.setText(f"{entry:.2f}")
        self.valuePnl.setText(f"{pnl:.2f}")
        self.valueLiq.setText(f"{liq:.2f}" if liq else "-")

        if qty > 0:
            self.valuePostionQty.setStyleSheet("color:#2ecc71;")
        elif qty < 0:
            self.valuePostionQty.setStyleSheet("color:#e74c3c;")
        else:
            self.reset_position()

        if pnl > 0:
            self.valuePnl.setStyleSheet("color:#2ecc71;")
        elif pnl < 0:
            self.valuePnl.setStyleSheet("color:#e74c3c;")
        else:
            self.valuePnl.setStyleSheet("color:#aaa;")

    # -----------------------------
    #   Market / Limit 변경 처리
    # -----------------------------
    def on_order_type_changed(self, text):
        if text == "Market":
            self.price_locked = False
            self.editOrderPrice.setEnabled(False)
            self.editOrderPrice.setPlaceholderText("Market Price")
        else:
            # 🔥 Limit으로 바뀌는 순간만 잠금
            self.price_locked = True
            self.editOrderPrice.setEnabled(True)
            self.editOrderPrice.setPlaceholderText("Limit Price 입력")

    def get_order_type(self) -> str:
        return self.comboType.currentText()

    def get_limit_price(self) -> float | None:
        if self.get_order_type() != "Limit":
            return None

        text = self.editOrderPrice.text().replace(",", "").strip()

        if not text:
            return None

        try:
            return float(text)
        except:
            return None

    # -----------------------------
    #   수량 처리
    # -----------------------------
    def get_qty(self) -> float:
        try:
            return float(self.editQty.text())
        except:
            return 0.0

    def _set_qty(self, value: float):
        if value < 0:
            value = 0
        self.editQty.setText(f"{value:.2f}".rstrip("0").rstrip("."))

    # qty 조정 버튼
    def on_qty_plus(self):
        self._set_qty(self.get_qty() + self.tick_size)

    def on_qty_minus(self):
        self._set_qty(self.get_qty() - self.tick_size)

    def on_qty_half(self):
        self._set_qty(self.get_qty() / 2)

    def on_qty_double(self):
        self._set_qty(self.get_qty() * 2)

    def set_symbol(self, symbol: str):
        self.labelSymbol.setText(symbol)
        self.tick_size = TICK_SIZE.get(symbol, 0.01)

class WatchlistTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ["종목명", "코드", "현재가", "전일대비"]
        )

        # 스크롤 제거
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 컬럼 자동 분배
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 행 높이
        self.verticalHeader().setDefaultSectionSize(28)
        self.verticalHeader().setVisible(False)

        self.setShowGrid(False)

        # 스타일
        self.setStyleSheet("""
        QTableWidget {
            background-color: #1b1b1b;
            color: white;
            font-size: 12px;
        }
        QHeaderView::section {
            background-color: #333;
            color: #ccc;
            font-size: 11px;
            padding: 4px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: #0a46c7;
            color: white;
        }
        """)
