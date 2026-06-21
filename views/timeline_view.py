from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QScrollArea)
from utils.theme import Theme
from services.timeline_service import TimelineService
from datetime import datetime


class TimelineView(QFrame):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setObjectName("timelineView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)

        title = QLabel("📅 Timeline")
        title.setObjectName("pageTitle")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_w = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_w)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_w)

        layout.addWidget(title)
        layout.addWidget(self.scroll)
        self.setup_style()

        self._loader = None

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#timelineView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{
                font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 16px;
            }}
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        if self._loader:
            if self._loader.isRunning():
                self._loader.quit()
                self._loader.wait(500)
        self._loader = TimelineLoader(self.user_id)
        self._loader.data_ready.connect(self._on_data)
        self._loader.start()

    def _on_data(self, grouped: list):
        self._clear_layout(self.scroll_layout)
        if not grouped:
            empty = QLabel("Aucun événement récent. Commence à journaliser pour voir ta timeline !")
            empty.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(empty)
            return
        c = Theme.colors()
        for group in grouped:
            day_label = QLabel(group["date"])
            day_label.setStyleSheet(f"""
                font-size: 16px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                padding: 8px 0 4px 0;
            """)
            self.scroll_layout.addWidget(day_label)
            for ev in group["events"]:
                card = QFrame()
                card.setObjectName("timelineCard")
                card.setStyleSheet(f"""
                    QFrame#timelineCard {{
                        background-color: {c["CARD_BG"]}; border-radius: 8px;
                        padding: 12px 16px; margin-left: 16px;
                    }}
                """)
                cl = QHBoxLayout(card)
                icon = QLabel(ev.get("icon", "📌"))
                icon.setStyleSheet("font-size: 20px;")
                text = QLabel(ev["title"])
                text.setStyleSheet(f"font-size: 14px; color: {c['TEXT_PRIMARY']}; font-weight: 500;")
                desc = QLabel()
                if ev.get("description"):
                    desc.setText(ev["description"][:120])
                desc.setStyleSheet(f"font-size: 12px; color: {c['TEXT_SECONDARY']};")
                cl.addWidget(icon)
                cl.addWidget(text)
                cl.addWidget(desc)
                cl.addStretch()
                self.scroll_layout.addWidget(card)
        self.scroll_layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class TimelineLoader(QThread):
    data_ready = Signal(list)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            svc = TimelineService(self.user_id)
            grouped = svc.get_events_grouped(30)
            self.data_ready.emit(grouped)
        except Exception as e:
            print(f"TimelineLoader error: {e}")
            self.data_ready.emit([])
