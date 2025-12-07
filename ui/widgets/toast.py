# ui/widgets/toast.py

from PyQt6 import QtWidgets, QtGui, QtCore


class ToastMessage(QtWidgets.QWidget):
    def __init__(self, parent, text: str, duration=2000):
        super().__init__(parent)

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Fade 애니메이션
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)

        # label
        self.label = QtWidgets.QLabel(text, self)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 220);
                color: white;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 15px;
            }
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.label)

        self.duration = duration

    # -----------------------------
    def show_toast(self):
        """Fade-in → 유지 → Fade-out"""
        self.opacity_effect.setOpacity(0.0)
        self.show()

        # 위치: 부모 우측 상단
        parent_rect = self.parent().rect()
        x = parent_rect.right() - self.width() - 20
        y = parent_rect.top() + 20
        self.move(x, y)

        # Fade-in
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        # Fade-out 예약
        QtCore.QTimer.singleShot(self.duration, self.fade_out)

    # -----------------------------
    def fade_out(self):
        self.anim.stop()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close)
        self.anim.start()
