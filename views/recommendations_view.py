from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QScrollArea, QGridLayout)
from utils.theme import Theme
from services.recommendation_engine import RecommendationEngine


class RecommendationsView(QFrame):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setObjectName("recommendationsView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)

        title = QLabel("💡 Recommandations")
        title.setObjectName("pageTitle")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_w = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_w)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_w)

        self.challenge_card = QFrame()
        self.challenge_card.setObjectName("challengeCard")
        ch_layout = QVBoxLayout(self.challenge_card)
        ch_layout.setSpacing(4)
        self.challenge_title = QLabel("🎯 Défi du jour")
        self.challenge_title.setObjectName("challengeTitle")
        self.challenge_desc = QLabel()
        self.challenge_desc.setObjectName("challengeDesc")
        self.challenge_points = QLabel()
        self.challenge_points.setObjectName("challengePoints")
        ch_layout.addWidget(self.challenge_title)
        ch_layout.addWidget(self.challenge_desc)
        ch_layout.addWidget(self.challenge_points)

        self.recs_container = QVBoxLayout()
        self.recs_container.setSpacing(8)

        layout.addWidget(title)
        layout.addWidget(self.challenge_card)
        layout.addWidget(QLabel("Suggestions personnalisées"))
        layout.addLayout(self.recs_container)
        layout.addStretch()

        self.setup_style()

        self._loader = None

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#recommendationsView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{
                font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 16px;
            }}
            QFrame#challengeCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c["CARD_BG"]}, stop:1 {c["ACCENT"]}22);
                border-radius: 12px; padding: 20px; margin-bottom: 8px;
            }}
            QLabel#challengeTitle {{
                font-size: 18px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
            }}
            QLabel#challengeDesc {{
                font-size: 14px; color: {c["TEXT_SECONDARY"]};
            }}
            QLabel#challengePoints {{
                font-size: 13px; color: {c["ACCENT"]};
                font-weight: bold;
            }}
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        if self._loader:
            if self._loader.isRunning():
                self._loader.quit()
                self._loader.wait(500)
        self._loader = RecLoader(self.user_id)
        self._loader.data_ready.connect(self._on_data)
        self._loader.start()

    def _on_data(self, recs: list, challenge: dict):
        c = Theme.colors()

        if challenge:
            self.challenge_title.setText(f"🎯 Défi du jour : {challenge['title']}")
            self.challenge_desc.setText(challenge["desc"])
            self.challenge_points.setText(f"+{challenge['points']} points · {challenge['category']}")

        self._clear_layout(self.recs_container)
        if not recs:
            empty = QLabel("Aucune suggestion pour le moment.")
            self.recs_container.addWidget(empty)
            return
        for rec in recs:
            card = QFrame()
            card.setObjectName("recCard")
            card.setStyleSheet(f"""
                QFrame#recCard {{
                    background-color: {c["CARD_BG"]}; border-radius: 10px;
                    padding: 16px; min-height: 60px;
                }}
            """)
            cl = QHBoxLayout(card)
            icon = QLabel(rec.get("icon", "💡"))
            icon.setStyleSheet("font-size: 24px;")
            text_layout = QVBoxLayout()
            t = QLabel(rec["title"])
            t.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {c['TEXT_PRIMARY']};")
            d = QLabel(rec.get("description", ""))
            d.setStyleSheet(f"font-size: 13px; color: {c['TEXT_SECONDARY']};")
            d.setWordWrap(True)
            text_layout.addWidget(t)
            text_layout.addWidget(d)
            priority = QLabel(rec.get("priority", ""))
            priority.setStyleSheet(f"font-size: 12px; color: {c['TEXT_MUTED']};")
            cl.addWidget(icon)
            cl.addLayout(text_layout)
            cl.addStretch()
            cl.addWidget(priority)
            self.recs_container.addWidget(card)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class RecLoader(QThread):
    data_ready = Signal(list, dict)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            engine = RecommendationEngine(self.user_id)
            recs = engine.get_recommendations()
            challenge = engine.get_daily_challenge()
            self.data_ready.emit(recs, challenge)
        except Exception as e:
            print(f"RecLoader error: {e}")
            self.data_ready.emit([], {})
