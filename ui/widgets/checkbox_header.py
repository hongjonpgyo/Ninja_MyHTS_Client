from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter

class CheckBoxHeader(QHeaderView):
    toggled = pyqtSignal(bool)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.checked = False
        self.setSectionsClickable(True)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        super().paintSection(painter, rect, logicalIndex)

        # 가격 컬럼 헤더에만 체크박스 표시
        PRICE_COL = 4
        if logicalIndex != PRICE_COL:
            return

        option_rect = QRect(
            rect.left() + 4,
            rect.top() + 4,
            16,
            16
        )

        painter.save()
        painter.drawRect(option_rect)

        if self.checked:
            painter.drawLine(
                option_rect.topLeft(),
                option_rect.bottomRight()
            )
            painter.drawLine(
                option_rect.bottomLeft(),
                option_rect.topRight()
            )

        painter.restore()

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        PRICE_COL = 4

        if index == PRICE_COL:
            self.checked = not self.checked
            self.toggled.emit(self.checked)
            self.viewport().update()

        super().mousePressEvent(event)
