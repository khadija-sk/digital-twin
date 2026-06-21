# views/search_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from controllers.search_controller import SearchController
from utils.theme import Theme, SAKURA, MILK_TEA


class SearchView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.ctrl = SearchController(user.id)
        self._build()

    def refresh_theme(self):
        self.setStyleSheet(self._get_style())

    def _build(self):
        c = Theme.colors()
        self.setStyleSheet(self._get_style())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar(c))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        self.cl = QVBoxLayout(content)
        self.cl.setContentsMargins(0, 0, 0, 0)  # 32, 24, 32, 32)
        self.cl.setSpacing(12)

        self.results_container = QVBoxLayout()
        self.results_container.setSpacing(8)
        self.cl.addLayout(self.results_container)
        self.cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)
        QTimer.singleShot(100, self._focus_search)

    def _build_topbar(self, c):
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(60)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        layout.setSpacing(12)

        title = QLabel("Search")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("Search journals, goals, check-ins...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input, stretch=1)

        count = QLabel("Global search")
        count.setObjectName("search_count")
        count.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(count)
        self.result_count = count

        return topbar

    def _focus_search(self):
        self.search_input.setFocus()

    def _on_search(self):
        c = Theme.colors()
        query = self.search_input.text()
        self._clear_results()
        if not query.strip():
            self.result_count.setText("Global search")
            return

        results = self.ctrl.search_all(query)
        self.result_count.setText(f"{len(results)} résultat(s)")

        if not results:
            empty = QLabel("No results found.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {c['TEXT_MUTED']}; font-size: 14px; "
                f"padding: 40px; background: transparent;"
            )
            self.results_container.addWidget(empty)
            return

        for r in results:
            self.results_container.addWidget(self._result_card(r))

    def _clear_results(self):
        while self.results_container.count():
            item = self.results_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _result_card(self, result):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("search_result_card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)
        layout.setSpacing(12)

        icon = QLabel(result["icon"])
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel(result["title"])
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        text_col.addWidget(title)

        preview = QLabel(result["preview"])
        preview.setWordWrap(True)
        preview.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 11px; background: transparent;")
        text_col.addWidget(preview)
        layout.addLayout(text_col, stretch=1)

        date_lbl = QLabel(result["date"])
        date_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        layout.addWidget(date_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        type_badge = QLabel(result["type"])
        type_badge.setFixedHeight(22)
        type_badge.setStyleSheet(
            f"background: rgba(215,192,174,0.1); color: {MILK_TEA}; "
            f"border-radius: 11px; padding: 0 10px; font-size: 10px; font-weight: bold;"
        )
        layout.addWidget(type_badge, alignment=Qt.AlignmentFlag.AlignTop)

        return card

    def refresh(self):
        self.refresh_theme()
        self._on_search()

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
            QWidget#content_area {{
                background-color: {c['BG']};
            }}
            QLineEdit#search_input {{
                background: transparent;
                border: none;
                border-bottom: 1.5px solid rgba(215,192,174,0.25);
                padding: 0 8px;
                font-size: 15px;
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit#search_input:focus {{
                border-bottom: 2px solid {SAKURA};
            }}
            QFrame#search_result_card {{
                background: {c['CARD_BG']};
                border-radius: 10px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
        """
