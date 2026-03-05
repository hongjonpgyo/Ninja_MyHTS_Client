from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from ui.utils.ls_symbol_name import display_symbol_name


class LSPositionProtectionPanel(QWidget):
    cancelRequested = pyqtSignal()

    def __init__(self, order_controller, parent=None):
        super().__init__(parent)
        self.order_controller = order_controller
        # 상태
        self.account_id = None  # ✅ 추가
        self.current_position = None
        self.last_clicked_price = None
        self._tp_price = None
        self._sl_price = None
        self.tick_size = 1.0  # TODO: 종목별로 주입 가능
        self.protect_qty = 1

        self._build_ui()
        self.setEnabled(False)

    # -------------------------------------------------
    # UI 구성
    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(3, 3, 3, 3)
        root.setSpacing(4)

        # # -----------------------------
        # # 제목
        # # -----------------------------
        # title = QLabel("포지션 보호 (손절 / 익절)")
        # title.setFont(self._bold_font(12))
        # root.addWidget(title)

        root.addWidget(self._separator())

        # -----------------------------
        # 포지션 정보
        # -----------------------------
        info = QHBoxLayout()

        self.lbl_symbol = self._info_label("종목: -")
        self.lbl_side = self._info_label("방향: -")
        self.lbl_qty = self._info_label("수량: -")
        self.lbl_avg = self._info_label("평균가: -")

        info.addWidget(self.lbl_symbol)
        info.addSpacing(20)
        info.addWidget(self.lbl_side)
        info.addSpacing(20)
        info.addWidget(self.lbl_qty)
        info.addSpacing(20)
        info.addWidget(self.lbl_avg)
        info.addSpacing(20)
        info.addStretch()

        root.addLayout(info)
        root.addWidget(self._separator())

        # -----------------------------
        # 보호 수량 버튼
        # -----------------------------
        qty_row = QHBoxLayout()
        qty_row.setSpacing(6)

        lbl_qty_title = QLabel("수량")
        lbl_qty_title.setFont(self._bold_font(10))

        qty_row.addWidget(lbl_qty_title)
        qty_row.addSpacing(10)

        self.qty_buttons = {}

        for q in [1, 2, 3, 5, 10]:
            btn = QPushButton(str(q))
            btn.setCheckable(True)
            btn.setFixedSize(36, 24)
            btn.setProperty("protectQty", "true")

            btn.clicked.connect(lambda checked, v=q: self._on_qty_selected(v))

            self.qty_buttons[q] = btn
            qty_row.addWidget(btn)

        qty_row.addStretch()
        root.addLayout(qty_row)

        root.addWidget(self._separator())

        # -----------------------------
        # TP (익절)
        # -----------------------------
        tp_row = QHBoxLayout()

        self.chk_tp = QCheckBox("익절 (TP)")
        self.chk_tp.setStyleSheet("color:#0051FF; font-weight:bold;")

        self.sp_tp_ticks = QSpinBox()
        self.sp_tp_ticks.setRange(0, 999)
        self.sp_tp_ticks.setFixedWidth(70)

        self.lbl_tp_price = QLabel("계산가: -")

        tp_row.addWidget(self.chk_tp)
        tp_row.addSpacing(10)
        tp_row.addWidget(QLabel("틱"))
        tp_row.addWidget(self.sp_tp_ticks)
        tp_row.addSpacing(20)
        tp_row.addWidget(self.lbl_tp_price)
        tp_row.addStretch()

        root.addLayout(tp_row)

        # -----------------------------
        # SL (손절)
        # -----------------------------
        sl_row = QHBoxLayout()

        self.chk_sl = QCheckBox("손절 (SL)")
        self.chk_sl.setStyleSheet("color:#e74c3c; font-weight:bold;")

        self.sp_sl_ticks = QSpinBox()
        self.sp_sl_ticks.setRange(0, 999)
        self.sp_sl_ticks.setFixedWidth(70)

        self.lbl_sl_price = QLabel("계산가: -")

        sl_row.addWidget(self.chk_sl)
        sl_row.addSpacing(10)
        sl_row.addWidget(QLabel("틱"))
        sl_row.addWidget(self.sp_sl_ticks)
        sl_row.addSpacing(20)
        sl_row.addWidget(self.lbl_sl_price)
        sl_row.addStretch()

        root.addLayout(sl_row)

        root.addWidget(self._separator())

        # -----------------------------
        # 기준가 + 버튼 (하단 액션 바)
        # -----------------------------
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(0, 8, 0, 0)
        action_bar.setSpacing(12)

        self.lbl_base_price = QLabel("기준가: -")
        self.lbl_base_price.setFont(self._bold_font(10))
        self.lbl_base_price.setStyleSheet("color:#e0e0e0;")

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setFixedWidth(80)


        self.btn_apply = QPushButton("적용")
        self.btn_apply.setFixedWidth(80)
        self.btn_apply.setEnabled(False)

        self.btn_clear = QPushButton("해제")
        self.btn_clear.setFixedWidth(80)

        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_clear.clicked.connect(self._on_clear)

        action_bar.addWidget(self.lbl_base_price)
        action_bar.addStretch()
        action_bar.addWidget(self.btn_cancel)
        action_bar.addSpacing(40)
        action_bar.addWidget(self.btn_apply)
        action_bar.addWidget(self.btn_clear)

        root.addLayout(action_bar)

        # -----------------------------
        # 이벤트 연결
        # -----------------------------
        self.chk_tp.stateChanged.connect(self._recalc)
        self.chk_sl.stateChanged.connect(self._recalc)
        self.sp_tp_ticks.valueChanged.connect(self._recalc)
        self.sp_sl_ticks.valueChanged.connect(self._recalc)

    # -------------------------------------------------
    # 외부 API
    # -------------------------------------------------
    def load_position(self, pos: dict):
        """
        pos = { symbol, side, qty, avg_price }
        """
        self.current_position = pos
        self.account_id = pos.get("account_id")  # ✅ 여기
        self.setEnabled(True)
        self._on_qty_selected(1)
        self.tick_size = pos.get("price_tick", 1.0)

        display_nm, full_nm = display_symbol_name(pos['symbol'])
        self.lbl_symbol.setText(f"종목: {display_nm}")

        if pos["side"] == "LONG":
            self.lbl_side.setText("포지션: 매수")
            self.lbl_side.setStyleSheet("color:#0051FF;")
        else:
            self.lbl_side.setText("포지션: 매도")
            self.lbl_side.setStyleSheet("color:#e74c3c;")

        self.lbl_qty.setText(f"수량: {pos['qty']}")
        self.lbl_avg.setText(f"평균가: {pos['avg_price']:.2f}")

        # 초기화
        self.chk_tp.setChecked(False)
        self.chk_sl.setChecked(False)
        self.sp_tp_ticks.setValue(0)
        self.sp_sl_ticks.setValue(0)
        self.lbl_tp_price.setText("계산가: -")
        self.lbl_sl_price.setText("계산가: -")

        self._update_apply_state()
        self.lbl_base_price.setText(f"기준가: {pos['avg_price']:.2f}")

    def clear(self):
        self.current_position = None
        self.last_clicked_price = None
        self.setEnabled(False)

        self.lbl_symbol.setText("종목: -")
        self.lbl_side.setText("포지션: -")
        self.lbl_qty.setText("수량: -")
        self.lbl_avg.setText("평균가: -")
        self.lbl_base_price.setText("기준가: -")
        self.lbl_tp_price.setText("계산가: -")
        self.lbl_sl_price.setText("계산가: -")
        self.btn_apply.setText("적용")

    # -------------------------------------------------
    # 내부 로직
    # -------------------------------------------------
    def _recalc(self):
        if not self.current_position:
            self._clear_prices()
            return

        side = self.current_position["side"]
        base = float(self.current_position["avg_price"])  # 🔥 평균가 기준
        ts = self.tick_size

        has_any = False

        # TP
        if self.chk_tp.isChecked() and self.sp_tp_ticks.value() > 0:
            sign = +1 if side == "LONG" else -1
            tp = base + sign * self.sp_tp_ticks.value() * ts
            self._tp_price = tp
            self.lbl_tp_price.setText(f"계산가: {tp:,.2f}")
            has_any = True
        else:
            self._tp_price = None
            self.lbl_tp_price.setText("계산가: -")

        # SL
        if self.chk_sl.isChecked() and self.sp_sl_ticks.value() > 0:
            sign = -1 if side == "LONG" else +1
            sl = base + sign * self.sp_sl_ticks.value() * ts
            self._sl_price = sl
            self.lbl_sl_price.setText(f"계산가: {sl:,.2f}")
            has_any = True
        else:
            self._sl_price = None
            self.lbl_sl_price.setText("계산가: -")

        self.btn_apply.setEnabled(has_any)

    def _clear_prices(self):
        self.lbl_tp_price.setText("계산가: -")
        self.lbl_sl_price.setText("계산가: -")
        self.btn_apply.setEnabled(False)

    def _update_apply_state(self):
        self.btn_apply.setEnabled(False)

    def _on_qty_selected(self, qty: int):
        # 포지션 수량 초과 방어
        max_qty = abs(int(self.current_position["qty"])) if self.current_position else qty
        self.protect_qty = min(qty, max_qty)

        for q, btn in self.qty_buttons.items():
            btn.setChecked(q == qty)

    def _on_apply(self):
        if not self.current_position or not self.account_id:
            return

        if self._tp_price is None and self._sl_price is None:
            return

        pos = self.current_position

        payload = {
            "account_id": int(self.account_id),
            "symbol": pos["symbol"],
            "side": pos["side"],  # 반드시 LONG / SHORT
            "source": "UI",  # 🔥 명시
            "protections": [],
        }

        # qty = abs(int(pos["qty"]))
        qty = self.protect_qty

        if self._tp_price is not None:
            payload["protections"].append({
                "type": "TP",
                "price": float(round(self._tp_price, 2)),
                "qty": qty,
            })

        if self._sl_price is not None:
            payload["protections"].append({
                "type": "SL",
                "price": float(round(self._sl_price, 2)),
                "qty": qty,
            })
        # -------------------------
        # 🚀 Service 호출
        # -------------------------
        self._send_protection(payload)

        if hasattr(self, "on_applied"):
            self.on_applied(self.current_position["symbol"])

    def _on_cancel_clicked(self):
        self.reset_base_price()
        self.cancelRequested.emit()

    def _on_clear(self):
        if not self.current_position:
            return

        self.order_controller.cancel_protections(
            account_id=self.account_id,
            symbol=self.current_position["symbol"],
        )

        # 🔥 취소 후 즉시 재조회
        if hasattr(self, "on_cleared"):
            self.on_cleared(self.current_position["symbol"])

    @pyqtSlot(float)
    def on_price_clicked(self, price: float):
        if not self.current_position:
            return

        base = float(self.current_position["avg_price"])
        side = self.current_position["side"]
        diff = price - base

        ticks = int(round(abs(diff) / self.tick_size))
        if ticks <= 0:
            return

        if side == "LONG":
            if diff > 0:
                self.chk_tp.setChecked(True)
                self.sp_tp_ticks.setValue(ticks)
            else:
                self.chk_sl.setChecked(True)
                self.sp_sl_ticks.setValue(ticks)

        elif side == "SHORT":
            if diff < 0:
                self.chk_tp.setChecked(True)
                self.sp_tp_ticks.setValue(ticks)
            else:
                self.chk_sl.setChecked(True)
                self.sp_sl_ticks.setValue(ticks)

        self._recalc()

    def reset_base_price(self):
        self.last_clicked_price = None
        self._tp_price = None
        self._sl_price = None

        self.chk_tp.setChecked(False)
        self.chk_sl.setChecked(False)
        self.sp_tp_ticks.setValue(0)
        self.sp_sl_ticks.setValue(0)

        self.lbl_base_price.setText("기준가: -")
        self.lbl_tp_price.setText("계산가: -")
        self.lbl_sl_price.setText("계산가: -")

        self.btn_apply.setEnabled(False)

    def _send_protection(self, payload):
        self.order_controller.place_protection_order(payload)

    def load_protections(self, rows: list[dict]):
        if not rows:
            self.chk_tp.setChecked(False)
            self.chk_sl.setChecked(False)
            self.sp_tp_ticks.setValue(0)
            self.sp_sl_ticks.setValue(0)

            self._tp_price = None
            self._sl_price = None

            self.lbl_tp_price.setText("계산가: -")
            self.lbl_sl_price.setText("계산가: -")

            self.btn_apply.setText("적용")  # 🔥 핵심
            self.btn_apply.setEnabled(False)

            return

        # 🔥 기준가 방어 (핵심)
        if self.last_clicked_price is None:
            if self.current_position:
                self.last_clicked_price = float(self.current_position["avg_price"])
                self.lbl_base_price.setText(
                    f"기준가: {self.last_clicked_price:,.2f}"
                )
            else:
                # 기준가 자체가 없으면 복원 불가
                return

        # 🔒 시그널 차단
        self.chk_tp.blockSignals(True)
        self.chk_sl.blockSignals(True)
        self.sp_tp_ticks.blockSignals(True)
        self.sp_sl_ticks.blockSignals(True)

        base = float(self.current_position["avg_price"])
        ts = self.tick_size

        self._tp_price = None
        self._sl_price = None

        for r in rows:
            price = float(r["price"])
            ticks = int(round(abs(price - base) / ts))

            if r["type"] == "TP":
                self.chk_tp.setChecked(True)
                self.sp_tp_ticks.setValue(ticks)
                self._tp_price = price
                self.lbl_tp_price.setText(f"계산가: {price:,.2f}")

            elif r["type"] == "SL":
                self.chk_sl.setChecked(True)
                self.sp_sl_ticks.setValue(ticks)
                self._sl_price = price
                self.lbl_sl_price.setText(f"계산가: {price:,.2f}")

        # 🔓 시그널 복구
        self.chk_tp.blockSignals(False)
        self.chk_sl.blockSignals(False)
        self.sp_tp_ticks.blockSignals(False)
        self.sp_sl_ticks.blockSignals(False)

        self.btn_apply.setText("수정")
        self.btn_apply.setEnabled(True)

    # -------------------------------------------------
    # Helper
    # -------------------------------------------------
    def _separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#333333;")
        return line

    def _info_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(self._bold_font(10))
        return lbl

    def _bold_font(self, size):
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        return f
