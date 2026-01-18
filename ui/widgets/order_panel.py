from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi

from config.tick_size import TICK_SIZE


class OrderPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/order_panel_20251214.ui", self)

        self.main_window = parent

        # -----------------------------
        # 기본 설정
        # -----------------------------
        self.symbol = None
        # self.tick_size = 0.01
        self.tick_size = 1
        self.price_locked = False

        self._all_close_timer = QTimer(self)
        self._all_close_timer.setSingleShot(True)
        self._all_close_timer.timeout.connect(self._on_all_close_confirm)

        self._all_close_hold_ms = 1500
        self._all_close_holding = False  # 눌러서 대기 중
        self._all_close_inflight = False  # 서버 요청 보낸 상태

        # -----------------------------
        # UI 밀도 조정 (중요)
        # -----------------------------
        self._tune_layout_density()

        # -----------------------------
        # 시그널 연결
        # -----------------------------
        self.comboType.currentTextChanged.connect(self.on_order_type_changed)
        self.editOrderPrice.editingFinished.connect(self._on_price_edit_finished)

        self.btnQtyPlus.clicked.connect(self.on_qty_plus)
        self.btnQtyMinus.clicked.connect(self.on_qty_minus)
        self.btnQtyHalf.clicked.connect(self.on_qty_half)
        self.btnQtyDouble.clicked.connect(self.on_qty_double)
        self.btnSymbolClose.clicked.connect(self.on_symbol_close)
        self.btnAllClose.clicked.connect(self.on_all_close)

        self.btnAllClose.pressed.connect(self._on_all_close_pressed)
        self.btnAllClose.released.connect(self._on_all_close_released)

    # =====================================================
    # 🔧 UI 밀도 / 버튼 톤 조정
    # =====================================================
    def _tune_layout_density(self):
        # Price / Qty 입력 폭 축소
        self.editOrderPrice.setFixedWidth(140)
        self.editQty.setFixedWidth(100)

        # +/- 버튼 사이즈 통일
        for btn in (self.btnQtyPlus, self.btnQtyMinus):
            btn.setFixedSize(28, 28)

        # ÷2 / ×2 버튼 → 보조 버튼 톤
        for btn in (self.btnQtyHalf, self.btnQtyDouble):
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    color: #dddddd;
                    font-size: 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
            """)

    # =====================================================
    # 🔢 Price 처리
    # =====================================================
    def _round_to_tick(self, price: float) -> float:
        tick = self.tick_size
        return round(round(price / tick) * tick, 8)

    def _on_price_edit_finished(self):
        price = self.get_limit_price()
        if price is None:
            return

        price = self._round_to_tick(price)
        self.editOrderPrice.setText(f"{price:.2f}")

    # =====================================================
    # 외부(현재가, 호가 클릭)에서 가격 세팅
    # =====================================================
    def set_price(self, price: float, lock=False):
        price = self._round_to_tick(price)

        if hasattr(self, "labelPrice"):
            self.labelPrice.setText(f"{price:,.2f}")

        if lock:
            self.price_locked = True

        # ✅ Market일 때만 자동 반영
        if not self.price_locked and self.get_order_type() == "Market":
            self.editOrderPrice.setText(f"{price:.2f}")

    # =====================================================
    # 주문 타입
    # =====================================================
    def on_order_type_changed(self, text):
        if text == "Market":
            self.price_locked = False
            self.editOrderPrice.setEnabled(False)
            self.editOrderPrice.setPlaceholderText("Market Price")
            self.editOrderPrice.setText("")  # 🔥 혼동 방지
        else:
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
        except ValueError:
            return None

    # =====================================================
    # 🔢 수량 처리
    # =====================================================
    def get_qty(self) -> float:
        try:
            return float(self.editQty.text())
        except ValueError:
            return 0.0

    def _set_qty(self, value: float):
        if value < 0:
            value = 0
        self.editQty.setText(f"{value:.2f}".rstrip("0").rstrip("."))

    def on_qty_plus(self):
        self._set_qty(self.get_qty() + self.tick_size)

    def on_qty_minus(self):
        self._set_qty(self.get_qty() - self.tick_size)

    def on_qty_half(self):
        self._set_qty(self.get_qty() / 2)

    def on_qty_double(self):
        self._set_qty(self.get_qty() * 2)

    def on_symbol_close(self):
        self.main_window.enqueue_async(
            self.main_window.close_symbol_position
        )

    def on_all_close(self):
        if self._all_close_holding:
            return
        self._all_close_holding = True
        self.btnAllClose.setText("CLOSING...")
        self.btnAllClose.setEnabled(False)

        self.main_window.request_all_close()

    # =====================================================
    # 📊 포지션 표시
    # =====================================================
    def reset_position(self):
        gray = "color:#888;"
        self.valuePostionQty.setText("0")
        self.valueAvgPrice.setText("0.00")
        self.valuePnl.setText("0.00")
        self.valueLiq.setText("-")

        self.valuePostionQty.setStyleSheet(gray)
        self.valueAvgPrice.setStyleSheet(gray)
        self.valuePnl.setStyleSheet(gray)
        self.valueLiq.setStyleSheet(gray)

    def update_position(self, pos: dict):
        qty = float(pos.get("qty", 0))
        pnl = float(pos.get("unrealized_pnl", 0))
        entry = float(pos.get("entry_price", 0))
        liq = pos.get("liq_price")

        self.valuePostionQty.setText(f"{qty:.4f}".rstrip("0").rstrip("."))
        self.valueAvgPrice.setText(f"{entry:.2f}")
        self.valuePnl.setText(f"{pnl:.2f}")
        self.valueLiq.setText(f"{liq:.2f}" if liq else "-")

        # 수량 색상
        if qty > 0:
            self.valuePostionQty.setStyleSheet("color:#2ecc71;")
        elif qty < 0:
            self.valuePostionQty.setStyleSheet("color:#e74c3c;")
        else:
            self.reset_position()

        # PnL 색상
        if pnl > 0:
            self.valuePnl.setStyleSheet("color:#2ecc71;")
        elif pnl < 0:
            self.valuePnl.setStyleSheet("color:#e74c3c;")
        else:
            self.valuePnl.setStyleSheet("color:#aaa;")

    # =====================================================
    # 심볼 변경
    # =====================================================
    def set_symbol(self, symbol: str):
        self.symbol = symbol
        self.labelSymbol.setText(symbol)
        self.tick_size = TICK_SIZE.get(symbol, 0.01)

        # 🔥 Limit일 때만 가격 초기화
        if self.get_order_type() == "Limit":
            self.price_locked = False
            self.editOrderPrice.setText("")

        # Limit일 때만 리셋

    def _on_all_close_pressed(self):
        self._all_close_holding = True
        self.btnAllClose.setText("HOLD TO CLOSE...")
        self.btnAllClose.setStyleSheet("""
            background-color:#b71c1c;
            color:white;
            font-weight:bold;
        """)

        self._all_close_timer.start(self._all_close_hold_ms)

    def _on_all_close_released(self):
        if self._all_close_timer.isActive():
            # ❌ 중간 취소
            self._all_close_timer.stop()
            self._reset_all_close_button()

        self._all_close_holding = False

    def _on_all_close_confirm(self):
        if not self._all_close_holding or self._all_close_inflight:
            return

        self._all_close_inflight = True
        self._all_close_holding = False

        self.btnAllClose.setEnabled(False)
        self.btnAllClose.setText("CLOSING...")

        self.main_window.enqueue_async(
            self.main_window.close_all_positions()
        )

    def _reset_all_close_button(self):
        self._all_close_holding = False
        self._all_close_inflight = False
        self.btnAllClose.setEnabled(True)
        self.btnAllClose.setText("ALL CLOSE")




