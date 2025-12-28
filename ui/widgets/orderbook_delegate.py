from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from config.settings import LMT_BUY_COL, LMT_SELL_COL, MIT_SELL_COL, MIT_BUY_COL

class OrderbookDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)



        self.best_bid_row = None
        self.best_ask_row = None
        self.mid_row = None

        self.mit_sell_bg = QColor(183, 28, 28, 80)
        self.mit_buy_bg = QColor(27, 94, 32, 80)
        # ✅ 소프트 HTS 글로우 (아주 은은)
        self.bid_bg = QColor(46, 204, 113, 22)   # ⭐ 20~25가 베스트
        self.ask_bg = QColor(231, 76, 60, 22)

    def paint(self, painter, option, index):
        col = index.column()
        row = index.row()

        # ---------------------------
        # 🌟 1️⃣ 배경 글로우 먼저
        # ---------------------------
        # 좌측 MIT (매도)
        if col == MIT_SELL_COL or col == LMT_SELL_COL:
            painter.save()
            painter.fillRect(option.rect, QBrush(self.mit_sell_bg))
            painter.restore()
            return

        # 우측 MIT (매수)
        if col == MIT_BUY_COL or col == LMT_BUY_COL:
            painter.save()
            painter.fillRect(option.rect, QBrush(self.mit_buy_bg))
            painter.restore()
            return

        if row == self.best_ask_row:
            painter.save()
            painter.fillRect(option.rect, self.ask_bg)
            painter.restore()

        elif row == self.best_bid_row:
            painter.save()
            painter.fillRect(option.rect, self.bid_bg)
            painter.restore()

        # Pivot row는 위젯에서만 처리
        elif row == self.mid_row:
            pass

        # ---------------------------
        # 2️⃣ 기본 셀 렌더링
        # ---------------------------
        super().paint(painter, option, index)
