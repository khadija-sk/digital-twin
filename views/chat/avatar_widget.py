from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen


class AvatarWidget(QWidget):
    def __init__(self, text, color="#E8A5B5", size=32, parent=None):
        super().__init__(parent)
        self._text = text[0].upper() if text else "?"
        self._color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        r = self._size // 2
        painter.drawRoundedRect(0, 0, self._size, self._size, r, r)
        painter.setPen(QColor("#FFFFFF"))
        f = QFont("Segoe UI", self._size // 2, QFont.Weight.Bold)
        painter.setFont(f)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()
