from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Property
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from utils.theme import Theme, FONT_FAMILY


class SpinnerWidget(QWidget):
    def __init__(self, text="Loading...", size=32, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._text = text
        self._size = size
        self.setFixedSize(size + 20, size + 20 + 24)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(text)
        c = Theme.colors()
        self._label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)

    def _rotate(self):
        self._angle = (self._angle + 15) % 360
        self.update()

    def set_text(self, text):
        self._text = text
        if hasattr(self, '_label'):
            self._label.setText(text)

    def refresh_theme(self):
        c = Theme.colors()
        if hasattr(self, '_label'):
            self._label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = Theme.colors()
        pen_bg = QPen(QColor(c['SKELETON']), 3)
        pen_fg = QPen(QColor(c['ACCENT']), 3)

        cx = self.width() // 2
        cy = self.height() // 3
        r = self._size // 2

        painter.setPen(pen_bg)
        painter.drawEllipse(cx - r, cy - r, self._size, self._size)

        painter.setPen(pen_fg)
        start_angle = self._angle * 16
        span_angle = 270 * 16
        painter.drawArc(cx - r, cy - r, self._size, self._size, start_angle, span_angle)

        painter.end()

    def stop(self):
        self._timer.stop()
        self.hide()
