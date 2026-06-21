from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient

from utils.theme import Theme
from views.chat.chat_bubble import UserBubble, AssistantBubble
from views.chat.typing_indicator import TypingIndicator


class ChatBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        c = Theme.colors()
        bg = QColor(c['BG'])
        painter.fillRect(self.rect(), bg)
        accent = QColor(c['ACCENT'])
        accent.setAlphaF(0.02)
        for i in range(5):
            x = (i * 180 + 50) % self.width()
            y = (i * 120 + 30) % self.height()
            grad = QRadialGradient(x, y, 250)
            grad.setColorAt(0, accent)
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillRect(self.rect(), grad)
        painter.end()


class ConversationWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("conversation_widget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._bg = ChatBackground(self)
        self._bg.lower()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.verticalScrollBar().setObjectName("chat_scrollbar")

        self.container = QWidget()
        self.container.setObjectName("conv_container")
        self.container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.container)
        self.chat_layout.setContentsMargins(20, 16, 20, 16)
        self.chat_layout.setSpacing(10)

        self.typing = TypingIndicator()
        self.typing.hide()

        self.chat_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, stretch=1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._bg.setGeometry(self.rect())

    def add_user_message(self, text):
        self._hide_typing()
        bubble = UserBubble(text)
        idx = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(idx, bubble)
        self._scroll_to_bottom()
        return bubble

    def add_assistant_message(self, text=""):
        self._hide_typing()
        bubble = AssistantBubble(text)
        idx = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(idx, bubble)
        self._scroll_to_bottom()
        return bubble

    def show_typing(self):
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.typing)
        self.typing.show()
        self._scroll_to_bottom()

    def _hide_typing(self):
        self.typing.hide()
        idx = self.chat_layout.indexOf(self.typing)
        if idx >= 0:
            self.chat_layout.removeWidget(self.typing)

    def clear(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chat_layout.addStretch()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def refresh_theme(self):
        self.container.setStyleSheet("background: transparent;")
        self.update()
