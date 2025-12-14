from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtCore import Qt


class OrderbookDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.best_bid_row = None
        self.best_ask_row = None
        self.mid_row = None  # pivot row index

        # 테두리 색상 (HTS 스타일)
        self.best_bid_color = QColor("#4FC3F7")   # 청록색(파랑 계열)
        self.best_ask_color = QColor("#EF5350")   # 빨강 계열

    def paint(self, painter, option, index):
        row = index.row()

        # 기본 페인팅
        super().paint(painter, option, index)

        # ---- Pivot Row Border 제거 ----
        if row == self.mid_row:
            return  # 테두리 그리지 않음

        # ---- Best Bid / Best Ask 테두리만 유지 ----
        if row == self.best_bid_row:
            painter.setPen(QPen(QColor("#00C8FF"), 1))
            painter.drawRect(option.rect)
            return

        if row == self.best_ask_row:
            painter.setPen(QPen(QColor("#FF4D4D"), 1))
            painter.drawRect(option.rect)
            return

