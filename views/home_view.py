from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from controllers.checkin_controller import CheckinController
from controllers.gamification_controller import GamificationController
from controllers.journal_controller import JournalController
from controllers.timer_controller import TimerController
from utils.theme import Theme, BORDER_RADIUS, FONT_FAMILY


class StatCard(QFrame):
    def __init__(self, label, value, sub=""):
        super().__init__()
        c = Theme.colors()
        self.setObjectName("stat_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 14, 16, 14)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val = QLabel(str(value))
        val.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 28, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {c['STAT_VALUE']}; background: transparent;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {c['STAT_LABEL']}; font-size: 11px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        if sub:
            s = QLabel(sub)
            s.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 9px; background: transparent;")
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(s)


class ActionCard(QFrame):
    def __init__(self, label, page, description, on_click):
        super().__init__()
        c = Theme.colors()
        self.setObjectName("action_card")
        self.setFixedSize(180, 84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 14, 12, 14, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(label)
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 14, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(description)
        desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        self.mousePressEvent = lambda e: on_click(page)


class HomeView(QWidget):

    def __init__(self, user, on_navigate):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.checkin_ctrl = CheckinController(user.id)
        self.gami_ctrl = GamificationController(user.id)
        self.journal_ctrl = JournalController(user.id)
        self._streak = 0
        self._score = "-"
        self._total_checkins = 0
        self._today_sessions = 0
        self._recent_entries = []
        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._load_stats()

    def _load_stats(self):
        try:
            log = self.checkin_ctrl.get_today_checkin()
            self._score = str(log.score_productivite) if log else "-"
            self._streak = self.checkin_ctrl.get_current_streak() or 0
            self._total_checkins = self.gami_ctrl.get_total_checkins()
            self._today_sessions = TimerController(self.user.id).get_today_sessions()
            self._recent_entries = self.journal_ctrl.get_last_n_entries(3)
        except Exception:
            pass
        self._update_ui()

    def _update_ui(self):
        pass

    def _build_ui(self):
        c = Theme.colors()
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
            layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        title = QLabel("Dashboard")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        tb.addWidget(title)
        tb.addStretch()

        today_str = datetime.now().strftime("%A, %B %d, %Y")
        date_lbl = QLabel(today_str)
        date_lbl.setStyleSheet(
            f"color: {c['ACCENT']}; background: {c['CARD_BORDER']}; "
            f"font-size: 11px; padding: 4px 12px; border-radius: 20px;"
        )
        tb.addWidget(date_lbl)
        layout.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)  # 32, 24, 32, 24)
        cl.setSpacing(20)

        brand = QLabel("Digital Personal Twin")
        brand.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 18, QFont.Weight.DemiBold))
        brand.setStyleSheet(f"color: {c['ACCENT']}; background: transparent;")
        cl.addWidget(brand)

        welcome = QLabel(f"{self._get_greeting()}, {self.user.nom}")
        welcome.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 22, QFont.Weight.Bold))
        welcome.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        cl.addWidget(welcome)

        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(12)

        streak_val = f"{self._streak}d"
        score_val = f"{self._score}/100"
        checkin_val = str(self._total_checkins)
        session_val = str(self._today_sessions)

        for label, value, sub in [
            ("Streak", streak_val, "consecutive days"),
            ("Score", score_val, "productivity"),
            ("Check-ins", checkin_val, "total"),
            ("Sessions", session_val, "today"),
        ]:
            stats_grid.addWidget(StatCard(label, value, sub))

        cl.addLayout(stats_grid)

        actions_label = QLabel("Quick Actions")
        actions_label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 13, QFont.Weight.DemiBold))
        actions_label.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; background: transparent;")
        cl.addWidget(actions_label)

        actions_grid = QHBoxLayout()
        actions_grid.setSpacing(12)
        actions_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for label, page, desc in [
            ("Check-in", "checkin", "Daily status"),
            ("Pomodoro", "timer", "Focus session"),
            ("Journal", "journal", "Write thoughts"),
            ("AI Chat", "ai", "AI insights"),
        ]:
            actions_grid.addWidget(ActionCard(label, page, desc, self.on_navigate))

        cl.addLayout(actions_grid)

        recent_label = QLabel("Recent Activity")
        recent_label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 13, QFont.Weight.DemiBold))
        recent_label.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; background: transparent;")
        cl.addWidget(recent_label)

        recent_card = QFrame()
        recent_card.setObjectName("recent_card")
        rl = QVBoxLayout(recent_card)
        rl.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        rl.setSpacing(8)

        entries = self._recent_entries
        if entries:
            for e in entries:
                row = QHBoxLayout()
                row.setSpacing(10)
                dot = QLabel()
                dot.setFixedSize(6, 6)
                dot.setStyleSheet(f"background: {c['ACCENT']}; border-radius: 3px;")
                row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)
                date_label = QLabel(e.date.strftime("%d %b") if hasattr(e.date, "strftime") else str(e.date)[:10])
                date_label.setStyleSheet(f"color: {c['ACCENT']}; font-size: 10px; background: transparent;")
                date_label.setFixedWidth(50)
                row.addWidget(date_label)
                preview = e.contenu[:80] + "..." if len(e.contenu) > 80 else e.contenu
                text = QLabel(preview)
                text.setWordWrap(True)
                text.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
                row.addWidget(text, stretch=1)
                rl.addLayout(row)
        else:
            empty = QLabel("No recent activity. Start by doing a check-in!")
            empty.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent; padding: 8px 0;")
            rl.addWidget(empty)

        cl.addWidget(recent_card)
        cl.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _get_greeting(self):
        h = datetime.now().hour
        if h < 12:
            return "Bonjour"
        elif h < 18:
            return "Bon après-midi"
        return "Bonsoir"

    def refresh(self):
        self._load_stats()
        cl = self.layout()
        while cl.count():
            item = cl.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._build_ui()

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: {FONT_FAMILY};
            }}
            QFrame#topbar {{
                background-color: {c['BG']};
                border-bottom: 1px solid {c['TOPBAR_BORDER']};
            }}
            QWidget#content_area {{
                background-color: {c['BG']};
            }}
            QFrame#stat_card {{
                background: {c['STAT_CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#action_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#action_card:hover {{
                border-color: {c['ACCENT']};
                background: {c['CARD_HOVER']};
            }}
            QFrame#recent_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
        """
