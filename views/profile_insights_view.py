from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QScrollArea, QProgressBar)
from utils.theme import Theme
from services.profile_service import ProfileService


class ProfileInsightsView(QFrame):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setObjectName("profileInsightsView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)

        title = QLabel("👤 Profil & Intérêts")
        title.setObjectName("pageTitle")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_w = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_w)
        self.scroll_layout.setSpacing(16)

        self.stats_card = QFrame()
        self.stats_card.setObjectName("statsCard")
        sl = QVBoxLayout(self.stats_card)
        self.stats_title = QLabel("Statistiques du profil")
        self.stats_title.setObjectName("cardTitle")
        self.stats_container = QVBoxLayout()
        self.stats_container.setSpacing(4)
        sl.addWidget(self.stats_title)
        sl.addLayout(self.stats_container)

        self.interests_card = QFrame()
        self.interests_card.setObjectName("interestsCard")
        il = QVBoxLayout(self.interests_card)
        self.interests_title = QLabel("Centres d'intérêt")
        self.interests_title.setObjectName("cardTitle")
        self.interests_container = QVBoxLayout()
        self.interests_container.setSpacing(6)
        il.addWidget(self.interests_title)
        il.addLayout(self.interests_container)

        self.scroll_layout.addWidget(self.stats_card)
        self.scroll_layout.addWidget(self.interests_card)
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_w)

        layout.addWidget(title)
        layout.addWidget(scroll)
        self.setup_style()

        self._loader = None

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#profileInsightsView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{
                font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 16px;
            }}
            QFrame#statsCard, QFrame#interestsCard {{
                background-color: {c["CARD_BG"]}; border-radius: 12px;
                padding: 20px;
            }}
            QLabel#cardTitle {{
                font-size: 18px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 8px;
            }}
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        if self._loader:
            if self._loader.isRunning():
                self._loader.quit()
                self._loader.wait(500)
        self._loader = ProfileLoader(self.user_id)
        self._loader.data_ready.connect(self._on_data)
        self._loader.start()

    def _on_data(self, traits: dict, interests: list):
        c = Theme.colors()
        self._clear_layout(self.stats_container)
        self._clear_layout(self.interests_container)

        stats = [
            f"🎯 Style de communication : {traits.get('communication_style', 'équilibré')}",
            f"📊 Polyvalence : {traits.get('versatility', 0) * 100:.0f}%",
            f"🏷️ {traits.get('interest_count', 0)} centre(s) d'intérêt",
        ]
        for s in stats:
            l = QLabel(s)
            l.setStyleSheet(f"font-size: 14px; color: {c['TEXT_SECONDARY']};")
            self.stats_container.addWidget(l)

        if interests:
            for name in interests:
                chip = QFrame()
                chip.setObjectName("interestChip")
                chip.setStyleSheet(f"""
                    QFrame#interestChip {{
                        background-color: {c["ACCENT"]}44; border-radius: 12px;
                        padding: 6px 14px;
                    }}
                """)
                cl = QHBoxLayout(chip)
                cl.setContentsMargins(0, 0, 0, 0)  # 10, 4, 10, 4)
                l = QLabel(f"# {name}")
                l.setStyleSheet(f"font-size: 14px; color: {c['TEXT_PRIMARY']};")
                cl.addWidget(l)
                self.interests_container.addWidget(chip)
        else:
            self.interests_container.addWidget(QLabel("Pas encore de centres d'intérêt détectés."))

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ProfileLoader(QThread):
    data_ready = Signal(dict, list)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            svc = ProfileService(self.user_id)
            traits = svc.get_user_traits()
            interests = svc.get_interests()
            self.data_ready.emit(traits, interests)
        except Exception as e:
            print(f"ProfileLoader error: {e}")
            self.data_ready.emit(
                {"top_interests":[],"interest_count":0,"communication_style":"équilibré","versatility":0,"total_weight":0},
                [])
