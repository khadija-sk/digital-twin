from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QScroller

from utils.theme import Theme, DARK_CHOCOLATE, BORDER_RADIUS, SIDEBAR_WIDTH


NAV_ITEMS = [
    ("H", "Home", "home"),
    ("D", "Dashboard", "dashboard"),
    ("C", "Check-in", "checkin"),
    ("T", "Timer", "timer"),
    ("S", "Stats", "stats"),
    ("G", "Goals", "goals"),
    ("J", "Journal", "journal"),
    ("A", "AI Chat", "ai"),
    ("P", "Profile", "profile"),
    ("R", "Routine", "routine"),
    ("E", "Health", "health"),
    ("B", "Briefing", "briefing"),
    ("K", "Recommandations", "recommendations"),
    ("N", "Analytics", "analytics"),
    ("M", "Calendrier", "calendar"),
]


class SidebarWidget(QFrame):
    def __init__(self, user, on_navigate, current_page=""):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.current_page = current_page
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._build_ui()

    def _build_ui(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            #sidebar {{
                background: {c['SIDEBAR_BG']};
                border-right: 1px solid {c['CARD_BORDER']};
            }}
            #sidebar_nav, #sidebar_nav_active {{
                border-radius: 4px;
            }}
            #sidebar_nav:hover {{
                background: {c['SIDEBAR_HOVER']};
            }}
            #sidebar_nav_active {{
                background: {c['SIDEBAR_ACTIVE']};
            }}
            #sidebar_icon_btn {{
                background: transparent; border: none;
                color: {c['TEXT_SECONDARY']}; font-size: 14px;
                text-align: left; padding-left: 12px; border-radius: {BORDER_RADIUS}px;
            }}
            #sidebar_icon_btn:hover {{
                background: {c['SIDEBAR_HOVER']};
            }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['ALOEWOOD']}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: transparent;
            }}
        """)
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
            layout.setSpacing(0)

        logo = QLabel("D")
        logo.setFixedSize(32, 32)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"background: {c['ACCENT']}; color: {DARK_CHOCOLATE}; "
            f"border-radius: 8px; font-size: 15px; font-weight: bold;"
        )
        logo_wrap = QWidget()
        lw = QHBoxLayout(logo_wrap)
        lw.setContentsMargins(0, 0, 0, 0)  # 10, 10, 10, 8)
        lw.addWidget(logo)
        layout.addWidget(logo_wrap)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent; border: none;")
        QScroller.grabGesture(scroll, QScroller.ScrollerGestureType.TouchGesture)
        QScroller.grabGesture(scroll, QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        nav = QWidget()
        self.nav_layout = QVBoxLayout(nav)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)  # 6, 2, 6, 2)
        self.nav_layout.setSpacing(6)

        self._nav_widgets = []
        self.nav_layout.addStretch()
        for icon_char, label, page in NAV_ITEMS:
            w = self._nav_item(icon_char, label, page, c)
            self._nav_widgets.append(w)
            self.nav_layout.addWidget(w)

        self.nav_layout.addStretch()
        scroll.setWidget(nav)
        layout.addWidget(scroll, stretch=1)

        footer = QWidget()
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(0, 0, 0, 0)  # 6, 2, 6, 6)
        fl.setSpacing(1)

        self._theme_btn = QPushButton()
        self._theme_btn.setObjectName("sidebar_icon_btn")
        self._theme_btn.setFixedHeight(32)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        is_dark = Theme.get_palette() == "dark"
        self._theme_btn.setText("  \u263E Clair" if is_dark else "  \u263E Sombre")
        self._theme_btn.clicked.connect(self._toggle_theme)
        fl.addWidget(self._theme_btn)

        self._logout_btn = QPushButton("  D\u00e9connexion")
        self._logout_btn.setObjectName("sidebar_icon_btn")
        self._logout_btn.setFixedHeight(32)
        self._logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._logout_btn.clicked.connect(lambda: self.on_navigate("logout") if self.on_navigate else None)
        fl.addWidget(self._logout_btn)

        self._user_btn = QPushButton()
        self._user_btn.setObjectName("sidebar_user_btn")
        self._user_btn.setFixedHeight(36)
        self._user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._user_btn.clicked.connect(lambda: self.on_navigate("logout") if self.on_navigate else None)
        fl.addWidget(self._user_btn)

        layout.addWidget(footer)
        self._update_user_btn()

    def _toggle_theme(self):
        from utils.theme import Theme, DARK, LIGHT

        new = "dark" if Theme.get_palette() == "light" else "light"
        Theme.set_palette(new)
        self._theme_btn.setText("  \u263E Clair" if new == "dark" else "  \u263E Sombre")
        c = Theme.colors()
        self.setStyleSheet(f"""
            #sidebar {{
                background: {c['SIDEBAR_BG']};
                border-right: 1px solid {c['CARD_BORDER']};
            }}
            #sidebar_nav, #sidebar_nav_active {{
                border-radius: 4px;
            }}
            #sidebar_nav:hover {{
                background: {c['SIDEBAR_HOVER']};
            }}
            #sidebar_nav_active {{
                background: {c['SIDEBAR_ACTIVE']};
            }}
            #sidebar_icon_btn {{
                background: transparent; border: none;
                color: {c['TEXT_SECONDARY']}; font-size: 14px;
                text-align: left; padding-left: 12px; border-radius: {BORDER_RADIUS}px;
            }}
            #sidebar_icon_btn:hover {{
                background: {c['SIDEBAR_HOVER']};
            }}
        """)
        self._update_user_btn()
        window = self.window()
        if window and hasattr(window, '_on_theme_changed'):
            window._on_theme_changed()

    def _nav_item(self, icon_char, label, page, c):
        btn = QWidget()
        active = page == self.current_page
        btn.setObjectName("sidebar_nav_active" if active else "sidebar_nav")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row = QHBoxLayout(btn)
        row.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        row.setSpacing(0)

        inner = QWidget()
        inner.setObjectName("sidebar_inner_active" if active else "sidebar_inner")
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)  # 10, 6, 10, 6)
        inner_layout.setSpacing(12)

        icon = QLabel(icon_char)
        icon.setFixedWidth(24)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"color: {c['ACCENT'] if active else c['TEXT_SECONDARY']}; "
            f"font-size: 15px; font-weight: bold; background: transparent;"
        )
        inner_layout.addWidget(icon)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {c['TEXT_PRIMARY'] if active else c['TEXT_SECONDARY']}; "
            f"font-size: 13px; background: transparent;"
        )
        inner_layout.addWidget(lbl)
        inner_layout.addStretch()

        row.addWidget(inner)
        btn.mousePressEvent = lambda e, p=page: self.on_navigate(p) if self.on_navigate else None
        return btn

    def _update_user_btn(self):
        c = Theme.colors()
        initial = self.user.nom[:2].upper() if self.user else "?"
        self._user_btn.setText(f"  {initial}")
        self._user_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['SIDEBAR_BG']}; color: {c['TEXT_SECONDARY']};
                border: 1px solid {c['CARD_BORDER']}; border-radius: {BORDER_RADIUS}px;
                font-size: 12px; font-weight: bold; text-align: left; padding-left: 12px;
            }}
            QPushButton:hover {{ background: {c['SIDEBAR_HOVER']}; }}
        """)

    def set_active(self, page):
        self.current_page = page
        self._rebuild()

    def _rebuild(self):
        cl = self.layout()
        if cl:
            while cl.count():
                item = cl.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
        self._build_ui()

    def refresh(self):
        self._rebuild()
