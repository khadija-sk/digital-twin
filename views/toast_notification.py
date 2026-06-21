from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Property, QEasingCurve
from PySide6.QtGui import QFont
from utils.theme import Theme, BORDER_RADIUS, FONT_FAMILY


class ToastNotification(QFrame):
    def __init__(self, message, toast_type="error", duration=5000, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        c = Theme.colors()
        color_map = {
            "error": c["ERROR"],
            "warning": c["WARNING"],
            "success": c["SUCCESS"],
            "info": c["INFO"],
        }
        icon_map = {
            "error": "✕",
            "warning": "⚠",
            "success": "✓",
            "info": "ℹ",
        }
        accent = color_map.get(toast_type, c["ERROR"])
        icon_char = icon_map.get(toast_type, "ℹ")

        self.setStyleSheet(f"""
            #toast {{
                background: {c['CARD_BG']};
                border: 1px solid {accent};
                border-radius: {BORDER_RADIUS}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)
        layout.setSpacing(10)

        icon = QLabel(icon_char)
        icon.setStyleSheet(f"color: {accent}; font-size: 16px; font-weight: bold; background: transparent;")
        layout.addWidget(icon)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; font-size: 12px; background: transparent;")
        layout.addWidget(msg, stretch=1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {c['TEXT_MUTED']}; font-size: 14px;
            }}
            QPushButton:hover {{ color: {c['TEXT_PRIMARY']}; }}
        """)
        close_btn.clicked.connect(self._fade_out)
        layout.addWidget(close_btn)

        if duration > 0:
            QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.height())
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()
