from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QGridLayout
from PyQt6.QtCore import Qt

import core.global_rates as global_rates
from ui.utils.formatter import format_date, fmt, get_price_color


class SymbolSummaryWidget(QFrame):
    ROW_HEIGHT = 22

    def __init__(self, parent=None):
        super().__init__(parent)
        self.labels: dict[str, QLabel] = {}
        self._setup_ui()

    # =====================================================
    # UI
    # =====================================================
    def _setup_ui(self):
        self.setFixedHeight(120)
        self.setObjectName("SymbolSummary")

        grid = QGridLayout(self)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(0)

        # 🔥 컬럼 안정화
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(4, 1)

        fields = [
            ("전일", "틱가치"),
            ("시가", "환율"),
            ("저가", "만기일"),
            ("고가", "잔존일수"),
        ]

        for row, (left, right) in enumerate(fields):
            self._create_row(grid, row, left, right)

        # self._apply_style()

        # 🔥 QSS 이후에도 고정폭 폰트 재적용 (안전장치)
        mono = QFont()
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setFamily("Menlo")
        mono.setPointSize(11)

        for key in ("전일", "시가", "저가", "고가", "틱가치"):
            self.labels[key].setFont(mono)

    def _create_row(self, grid: QGridLayout, row: int, left: str, right: str):
        key_l, val_l = self._create_pair(left)
        key_r, val_r = self._create_pair(right)

        grid.addWidget(key_l, row, 0)
        grid.addWidget(val_l, row, 1)
        grid.addWidget(key_r, row, 3)
        grid.addWidget(val_r, row, 4)

        # 중앙 세로 구분선
        if row == 0:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFixedWidth(1)
            sep.setStyleSheet("background:#2a2a2a;")
            grid.addWidget(sep, 0, 2, 4, 1)

    def _create_pair(self, key: str):
        key_lbl = QLabel(key)
        key_lbl.setObjectName("SummaryKey")
        key_lbl.setProperty("row", "true")
        key_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        val_lbl = QLabel("--")
        val_lbl.setObjectName("SummaryValue")
        val_lbl.setProperty("row", "true")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.labels[key] = val_lbl
        return key_lbl, val_lbl

    # =====================================================
    # DATA
    # =====================================================
    def update_ls_symbol(self, row: dict):
        if not row:
            return

        symbol = row.get("symbol")
        prev_close = row.get("close_p")

        self._set("전일", fmt(prev_close, "price", symbol))
        self._set("시가", fmt(row.get("open_p"), "price", symbol))
        self._set("고가", fmt(row.get("high_p"), "price", symbol))
        self._set("저가", fmt(row.get("low_p"), "price", symbol))

        fx_rate = global_rates.FX_RATES.get(row.get("crncy_cd"))
        self._set("환율", self._fmt_fx(row.get("crncy_cd")))

        # 틱가치 계산
        mn_chg_amt_raw = row.get("mn_chg_amt")
        mn_chg_amt = float(mn_chg_amt_raw) if mn_chg_amt_raw is not None else None

        tick_value_krw = None
        if mn_chg_amt is not None and fx_rate is not None:
            tick_value_krw = mn_chg_amt * fx_rate

        self._set(
            "틱가치",
            f"{tick_value_krw:,.0f}원 / 틱" if tick_value_krw is not None else "--"
        )

        self._set("만기일", format_date(row.get("mrtr_dt")))
        self._set(
            "잔존일수",
            f"{row['remain_days']}일" if row.get("remain_days") is not None else "--"
        )

    def _set(self, key: str, value):
        label = self.labels[key]

        if value in (None, ""):
            label.setText("--")
            label.setStyleSheet("")
            return

        label.setText(str(value))

        # 🔥 가격 컬러 처리 (전일 기준)
        if key in ("시가", "고가", "저가"):
            try:
                current = float(str(value).replace(",", ""))
                prev_text = self.labels["전일"].text().replace(",", "")
                prev = float(prev_text) if prev_text not in ("--", "") else None
            except:
                label.setStyleSheet("")
                return

            if prev is None:
                label.setStyleSheet("")
                return

            color = get_price_color(current, prev)
            label.setStyleSheet(f"color: {color};")
        else:
            label.setStyleSheet("")

    # =====================================================
    # UTIL
    # =====================================================
    @staticmethod
    def _fmt_fx(currency: str | None) -> str:
        if not currency:
            return "--"

        rate = global_rates.FX_RATES.get(currency)
        if rate is None:
            return f"--({currency})"

        return f"{int(round(rate)):,}원 ({currency})"

    # =====================================================
    # STYLE
    # =====================================================
    def _apply_style(self):
        self.setStyleSheet("""
        QFrame#SymbolSummary {
            background: #1f1f1f;
            border-left: 1px solid #2a2a2a;
        }

        QLabel#SummaryKey {
            color: #9a9a9a;
            font-size: 12px;
        }

        QLabel#SummaryValue {
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            font-family: Menlo, Consolas, "SF Mono", monospace;
        }

        QLabel[row="true"] {
            border-bottom: 1px solid #262626;
            padding: 3px 0px;
        }
        """)
