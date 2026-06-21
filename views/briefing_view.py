from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QScrollArea)
from utils.theme import Theme


class BriefingView(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("briefingView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)

        title = QLabel("📋 Briefing du jour")
        title.setObjectName("pageTitle")

        self.card = QFrame()
        self.card.setObjectName("briefingCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(12)

        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("greetingLabel")
        self.greeting_label.setWordWrap(True)

        self.streak_label = QLabel()
        self.streak_label.setObjectName("streakLabel")

        self.week_mood_label = QLabel()
        self.week_mood_label.setObjectName("weekMoodLabel")

        self.week_productivity_label = QLabel()

        self.deadlines_label = QLabel()
        self.deadlines_label.setWordWrap(True)

        self.journal_label = QLabel()
        self.journal_label.setWordWrap(True)

        self.recommendations_label = QLabel()
        self.recommendations_label.setWordWrap(True)

        self.insight_label = QLabel()
        self.insight_label.setWordWrap(True)

        for w in [self.greeting_label, self.streak_label, self.week_mood_label,
                   self.week_productivity_label, self.deadlines_label,
                   self.journal_label, self.recommendations_label, self.insight_label]:
            card_layout.addWidget(w)

        layout.addWidget(title)
        layout.addWidget(self.card)
        layout.addStretch()

        self.setup_style()

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#briefingView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{
                font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 16px;
            }}
            QFrame#briefingCard {{
                background-color: {c["CARD_BG"]}; border-radius: 12px;
                padding: 24px; max-width: 640px;
            }}
            QLabel#greetingLabel {{
                font-size: 22px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
            }}
            QLabel#streakLabel, QLabel#weekMoodLabel {{
                font-size: 15px; color: {c["TEXT_SECONDARY"]};
            }}
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        win = self.window()
        if win and hasattr(win, '_generate_briefing') and hasattr(win, 'current_user') and win.current_user:
            briefing = win._generate_briefing(win.current_user.id)
            self.show_briefing(briefing)

    def show_briefing(self, briefing: dict):
        self.greeting_label.setText(f"{briefing.get('greeting', 'Bonjour')} ! 👋")
        streak = briefing.get("streak", 0)
        self.streak_label.setText(f"🔥 Série : {streak} jour{'s' if streak > 1 else ''}")

        week_mood = briefing.get("week_mood")
        if week_mood:
            self.week_mood_label.setText(f"📊 Humeur moyenne de la semaine : {'⭐' * int(round(week_mood))} ({week_mood}/5)")

        week_prod = briefing.get("week_productivity")
        if week_prod:
            self.week_productivity_label.setText(f"📈 Productivité moyenne : {week_prod}%")

        deadlines = briefing.get("deadlines", [])
        if deadlines:
            self.deadlines_label.setText(f"📚 Échéances : {', '.join(deadlines[:3])}")
        else:
            self.deadlines_label.setText("✅ Aucune échéance urgente cette semaine.")

        recs = briefing.get("recommendations", [])
        if recs:
            rec_text = "💡 Suggestions :\n" + "\n".join(f"• {r}" for r in recs)
            self.recommendations_label.setText(rec_text)
        else:
            self.recommendations_label.setText("💡 Tout va bien, continue !")

        journal_insight = briefing.get("journal_insight", "")
        if journal_insight:
            self.insight_label.setText(f"📖 Analyse journal : {journal_insight}")
        else:
            self.insight_label.setText("📖 Ajoute des entrées journal pour des insights personnalisés.")


class EmptyStateView(QFrame):
    def __init__(self, title: str, message: str, icon: str = "📌", parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel(icon)
        self.icon_label.setObjectName("emptyIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("emptyTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.message_label = QLabel(message)
        self.message_label.setObjectName("emptyMessage")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        layout.addStretch()
        self.setup_style()

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#emptyState {{ background-color: {c["BG"]}; }}
            QLabel#emptyIcon {{ font-size: 48px; margin-bottom: 8px; }}
            QLabel#emptyTitle {{
                font-size: 20px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 4px;
            }}
            QLabel#emptyMessage {{
                font-size: 14px; color: {c["TEXT_SECONDARY"]};
                max-width: 400px;
            }}
        """)

    def refresh_theme(self):
        self.setup_style()
