from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

from utils.theme import Theme, DARK_CHOCOLATE, ALOEWOOD, SAKURA


class BadgePopup(QWidget):
    def __init__(self, parent, badge_name, badge_icon="*", xp=10):
        super().__init__(parent)
        c = Theme.colors()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 88)
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['CARD_BG']};
                border-radius: 14px;
                border: 0.5px solid {c['CARD_BORDER']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)
        layout.setSpacing(14)

        icon_lbl = QLabel(badge_icon)
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: rgba(248,215,218,0.1); border-radius: 22px; font-size: 22px; color: {SAKURA};"
        )
        layout.addWidget(icon_lbl)

        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("Badge unlocked")
        title.setStyleSheet(f"color: {SAKURA}; font-size: 10px; font-weight: bold; background: transparent;")
        col.addWidget(title)
        name = QLabel(badge_name)
        name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        col.addWidget(name)
        xp_lbl = QLabel(f"+{xp} XP")
        xp_lbl.setStyleSheet(f"color: {SAKURA}; font-size: 11px; background: transparent;")
        col.addWidget(xp_lbl)
        layout.addLayout(col)
        layout.addStretch()

    def show_animated(self):
        parent = self.parent()
        if parent:
            px = parent.x() + parent.width() - self.width() - 20
            py = parent.y() + parent.height() - self.height() - 20
            self.move(px, py + 60)
        self.show()

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(350)
        anim.setStartValue(self.pos())
        anim.setEndValue(QPoint(self.x(), self.y() - 60))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim
        QTimer.singleShot(3500, self._dismiss)

    def _dismiss(self):
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setStartValue(self.pos())
        anim.setEndValue(QPoint(self.x(), self.y() + 80))
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.deleteLater)
        anim.start()
        self._anim2 = anim


def show_badge_popups(parent_window, badge_names: list):
    icon_map = {
        "premier": ("*", 10),
        "check-in": ("+", 25),
        "expert": ("*", 100),
        "3 jours": ("~", 20),
        "7 jours": ("*", 50),
        "30 jours": ("^", 200),
        "session": ("~", 10),
        "10 pomodo": ("o", 40),
        "50 pomodo": ("*", 150),
    }
    for i, name in enumerate(badge_names):
        icon, xp = "*", 10
        for key, val in icon_map.items():
            if key in name.lower():
                icon, xp = val
                break
        clean = name.strip()
        popup = BadgePopup(parent_window, clean, icon, xp)
        QTimer.singleShot(i * 600, popup.show_animated)
