from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt


class OrderbookDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.best_bid_row = None
        self.best_ask_row = None
        self.mid_row = None  # pivot row index

        # 은은한 HTS 톤 (alpha 아주 낮게)
        self.bid_bg = QColor(46, 204, 113, 35)   # green, very soft
        self.ask_bg = QColor(231, 76, 60, 35)    # red, very soft

    def paint(self, painter, option, index):
        row = index.row()

        # 🔥 기본 셀 렌더링
        super().paint(painter, option, index)

        # Pivot row는 Delegate에서 절대 건드리지 않음
        if row == self.mid_row:
            return

        # Best Ask (위)
        if row == self.best_ask_row:
            painter.save()
            painter.fillRect(option.rect, QBrush(self.ask_bg))
            painter.restore()
            return

        # Best Bid (아래)
        if row == self.best_bid_row:
            painter.save()
            painter.fillRect(option.rect, QBrush(self.bid_bg))
            painter.restore()
            return
