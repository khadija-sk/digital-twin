from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QProgressBar, QSizePolicy,
    QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from controllers.gamification_controller import GamificationController
from controllers.checkin_controller import CheckinController
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA


class ProfileView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.gami = GamificationController(user.id)
        self.checkin = CheckinController(user.id)
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        c = Theme.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        title = QLabel("My Profile")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)
        layout.addStretch()
        root.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 24)
        self.content_layout.setSpacing(16)

        self._populate()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _populate(self):
        cl = self.content_layout
        cl.addWidget(self._build_hero_card())
        cl.addWidget(self._build_stats_row())
        cl.addWidget(self._build_badges_section())
        cl.addStretch()

    def _build_hero_card(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("hero_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 28, 24, 28, 24)
        layout.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(20)

        avatar = QLabel(self.user.nom[:2].upper())
        avatar.setFixedSize(72, 72)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background: {SAKURA}; color: {DARK_CHOCOLATE}; "
            "border-radius: 36px; font-size: 26px; font-weight: bold;"
        )
        top.addWidget(avatar)

        info = QVBoxLayout()
        info.setSpacing(4)
        name = QLabel(self.user.nom)
        name.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        info.addWidget(name)

        email = QLabel(self.user.email)
        email.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        info.addWidget(email)

        since = QLabel(f"Member since {self.user.date_creation.strftime('%d/%m/%Y') if self.user.date_creation else 'N/A'}")
        since.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        info.addWidget(since)

        top.addLayout(info)
        top.addStretch()

        level_badge = QLabel(f"Level {self.user.niveau}")
        level_badge.setFixedHeight(32)
        level_badge.setStyleSheet(
            f"background: {SAKURA}; color: {DARK_CHOCOLATE}; "
            "border-radius: 16px; padding: 0 14px; "
            "font-size: 13px; font-weight: bold;"
        )
        top.addWidget(level_badge)

        layout.addLayout(top)

        xp, xp_next, niveau = self.gami.get_xp_for_next_level()
        xp_label = QLabel(f"XP - {xp} / {xp_next}")
        xp_label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(xp_label)

        bar = QProgressBar()
        bar.setObjectName("xp_bar")
        bar.setMinimum(0)
        bar.setMaximum(xp_next)
        bar.setValue(min(xp, xp_next))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        layout.addWidget(bar)

        return card

    def _build_stats_row(self):
        c = Theme.colors()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(12)

        streak = self.checkin.get_current_streak()
        total = self.gami.get_total_checkins()
        sessions = self.gami.get_total_sessions()
        badges = len(self.gami.get_all_badges())

        for label, value, sub in [
            ("Streak", f"{streak}", "days"),
            ("Check-ins", f"{total}", "total"),
            ("Pomodoros", f"{sessions}", "completed"),
            ("Badges", f"{badges}", "unlocked"),
        ]:
            card = QFrame()
            card.setObjectName("stat_card")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(0, 0, 0, 0)  # 16, 14, 16, 14)
            cl.setSpacing(3)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {MILK_TEA}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px; background: transparent;")
            cl.addWidget(lbl)

            val = QLabel(value)
            val.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {c['ACCENT']}; background: transparent;")
            cl.addWidget(val)

            s = QLabel(sub)
            s.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
            cl.addWidget(s)

            layout.addWidget(card)

        return widget

    def _build_badges_section(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("Badges obtained")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)

        badges = self.gami.get_all_badges()

        if not badges:
            empty = QLabel("No badges yet.\nComplete your first check-in to unlock one!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {MILK_TEA}; font-size: 13px; padding: 20px; background: transparent;")
            layout.addWidget(empty)
        else:
            grid_widget = QWidget()
            grid_widget.setStyleSheet("background: transparent;")
            grid_layout = QHBoxLayout(grid_widget)
            grid_layout.setSpacing(10)
            grid_layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)

            for i, badge in enumerate(badges):
                grid_layout.addWidget(self._build_badge_card(badge))
                if (i + 1) % 4 == 0:
                    layout.addWidget(grid_widget)
                    grid_widget = QWidget()
                    grid_widget.setStyleSheet("background: transparent;")
                    grid_layout = QHBoxLayout(grid_widget)
                    grid_layout.setSpacing(10)
                    grid_layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)

            if len(badges) % 4 != 0:
                grid_layout.addStretch()
                layout.addWidget(grid_widget)

        layout.addWidget(self._h_sep(c))
        locked_title = QLabel("Badges to unlock")
        locked_title.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(locked_title)

        obtained_names = {b.nom for b in badges}
        all_badges = [
            ("First check-in", "First check-in completed"),
            ("Regular check-in", "7 check-ins completed"),
            ("Check-in expert", "30 check-ins completed"),
            ("Streak 3 days", "3 consecutive days"),
            ("Streak 7 days", "7 consecutive days"),
            ("First session", "First Pomodoro session"),
            ("10 Pomodoros", "10 sessions completed"),
            ("50 Pomodoros", "50 sessions completed"),
        ]

        locked_row = QHBoxLayout()
        locked_row.setSpacing(10)
        count = 0
        for nom, desc in all_badges:
            if nom not in obtained_names:
                locked_row.addWidget(self._build_locked_badge(desc))
                count += 1
                if count % 4 == 0:
                    layout.addLayout(locked_row)
                    locked_row = QHBoxLayout()
                    locked_row.setSpacing(10)

        if count > 0 and count % 4 != 0:
            locked_row.addStretch()
            layout.addLayout(locked_row)

        return card

    def _build_badge_card(self, badge):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("badge_card")
        card.setFixedSize(140, 100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel(badge.icone or "\u2606")
        icon.setStyleSheet(f"font-size: 24px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        name = QLabel(badge.nom)
        name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        layout.addWidget(name)

        xp = QLabel(f"+{badge.xp_gagne} XP")
        xp.setStyleSheet(f"color: {SAKURA}; font-size: 10px; background: transparent;")
        xp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(xp)

        return card

    def _build_locked_badge(self, desc):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("badge_locked")
        card.setFixedSize(140, 100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("\u2606")
        icon.setStyleSheet(f"font-size: 20px; color: {c['TEXT_MUTED']}; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        name = QLabel(desc)
        name.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        layout.addWidget(name)

        return card

    def refresh(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._populate()

    def _build_topbar(self):
        c = Theme.colors()
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)

        title = QLabel("My Profile")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)
        layout.addStretch()
        return topbar

    def _h_sep(self, c):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['DIVIDER']};")
        return sep

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QFrame#topbar {{
                background-color: {c['BG']};
                border-bottom: 0.5px solid {c['TOPBAR_BORDER']};
            }}
            QWidget#content_area {{ background-color: {c['BG']}; }}
            QFrame#hero_card {{
                background-color: {c['BG_SECONDARY']};
                border-radius: 16px;
            }}
            QFrame#hero_card QLabel {{ background: transparent; }}
            QProgressBar#xp_bar {{
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
                border: none;
            }}
            QProgressBar#xp_bar::chunk {{
                background: {SAKURA};
                border-radius: 3px;
            }}
            QFrame#stat_card {{
                background: {c['CARD_BG']};
                border-radius: 12px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
            QFrame#section_card {{
                background: {c['CARD_BG']};
                border-radius: 14px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
            QFrame#badge_card {{
                background: rgba(248,215,218,0.06);
                border-radius: 12px;
                border: 0.5px solid rgba(248,215,218,0.15);
            }}
            QFrame#badge_locked {{
                background: rgba(255,255,255,0.03);
                border-radius: 12px;
                border: 0.5px solid rgba(255,255,255,0.05);
            }}
        """
