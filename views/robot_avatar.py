import math
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath


class RobotAvatar(QFrame):
    STATES = ["idle", "thinking", "blinking", "speaking"]

    def __init__(self, size=48, parent=None, animated=False):
        super().__init__(parent)
        self._size = size
        self._state = "idle"
        self._blinking = False
        self._eye_offset = 0
        self._antenna_glow = 0
        self._breath_phase = 0.0
        self._animated = animated
        self._glow_alpha = 0

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_timer.start(3000)

        if self._animated:
            self._breath_timer = QTimer(self)
            self._breath_timer.timeout.connect(self._breathe)
            self._breath_timer.start(50)

    def set_animated(self, animated: bool):
        self._animated = animated
        if animated:
            if not hasattr(self, '_breath_timer'):
                t = QTimer(self)
                t.timeout.connect(self._breathe)
                t.start(50)
                self._breath_timer = t
        else:
            t = getattr(self, '_breath_timer', None)
            if t:
                t.stop()

    def set_state(self, state: str):
        if state in self.STATES:
            self._state = state
            self.update()

    def _blink(self):
        if self._state == "idle":
            self._blinking = True
            self.update()
            QTimer.singleShot(150, self._end_blink)

    def _end_blink(self):
        self._blinking = False
        self.update()

    def _breathe(self):
        self._breath_phase = (self._breath_phase + 0.025) % 1.0
        glow = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._breath_phase * 2 * math.pi))
        self._glow_alpha = int(80 * glow)
        self._antenna_glow = int(40 * (0.5 + 0.5 * math.sin(self._breath_phase * 2 * math.pi)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        cx, cy = s // 2, s // 2
        r = s // 2 - 2

        head_color = QColor("#4fc3f7")
        face_color = QColor("#0d0d24")
        eye_color = QColor("#e0e0f0")
        accent_color = QColor("#7c4dff")
        glow_color = QColor(79, 195, 247, self._glow_alpha)

        if self._glow_alpha > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(
                cx - r - 4, cy - r + 2 - 4, r * 2 + 8, r * 2 + 6, 10, 10
            )

        head = QPainterPath()
        head.addRoundedRect(cx - r, cy - r + 2, r * 2, r * 2 - 2, 6, 6)
        painter.fillPath(head, head_color)

        face = QPainterPath()
        face.addRoundedRect(
            cx - r + 5, cy - r + 8, r * 2 - 10, r * 2 - 12, 4, 4
        )
        painter.fillPath(face, face_color)

        if self._blinking:
            eye_w, eye_h = 4, 1
            eye_y = cy - 2
        else:
            eye_w, eye_h = 5, 6
            eye_y = cy - 4 + self._eye_offset

        left_eye_rect = (cx - 8 - eye_w // 2, eye_y, eye_w, eye_h)
        right_eye_rect = (cx + 8 - eye_w // 2, eye_y, eye_w, eye_h)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(eye_color)
        painter.drawRoundedRect(*left_eye_rect, 2, 2)
        painter.drawRoundedRect(*right_eye_rect, 2, 2)

        mouth_y = cy + 6
        if self._state == "speaking":
            painter.setBrush(QColor("#7c4dff"))
            painter.drawRoundedRect(cx - 5, mouth_y, 10, 3, 2, 2)
        else:
            painter.setPen(QPen(eye_color, 1.5))
            painter.drawArc(cx - 4, mouth_y, 8, 4, 0, -180 * 16)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent_color)
        painter.drawEllipse(cx - 2, cy - r + 1, 4, 4)

        if self._state == "thinking":
            painter.setPen(QPen(accent_color, 1.5))
            for i, (dx, dy) in enumerate(
                [(-10, -r - 2), (0, -r - 6), (10, -r - 2)]
            ):
                alpha = 100 + int(80 * (i / 2))
                painter.setOpacity(0.3 + 0.7 * (alpha / 180))
                painter.drawEllipse(cx + dx - 2, cy + dy - 2, 4, 4)
            painter.setOpacity(1.0)

        painter.end()
