from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QColor, QPainter


class Dot(QFrame):
    def __init__(self, color="#E8A5B5", parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self._opacity = 1.0
        self._color = QColor(color)
        self._anim = QPropertyAnimation(self, b"opacity")
        self._anim.setDuration(600)
        self._anim.setStartValue(0.3)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, val):
        self._opacity = val
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def start(self):
        self._anim.start()

    def stop(self):
        self._anim.stop()
        self._opacity = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        painter.setBrush(c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 8, 8)
        painter.end()


class TypingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("typing_indicator")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        label = QLabel("IA réfléchit")
        label.setStyleSheet("color: #8B827A; font-size: 12px; background: transparent;")
        label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(label)

        self._dots = []
        for i in range(3):
            d = Dot()
            layout.addWidget(d)
            self._dots.append(d)

        layout.addStretch()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._stagger)
        self._timer.setSingleShot(True)

    def show(self):
        super().show()
        for i, d in enumerate(self._dots):
            QTimer.singleShot(i * 200, d.start)

    def hide(self):
        for d in self._dots:
            d.stop()
        super().hide()

    def _stagger(self):
        pass
