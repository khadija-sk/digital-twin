from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QTimer
from PySide6.QtGui import QFont, QPixmap, QFontMetrics

from utils.theme import Theme
from views.chat.avatar_widget import AvatarWidget
from views.chat.markdown_renderer import MarkdownRenderer


class AnimatedMixin:
    def animate_in(self, delay=0):
        self.setGraphicsEffect(None)
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(delay, self._anim.start)


class UserBubble(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("user_bubble")
        self.setMaximumWidth(480)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        c = Theme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addStretch()

        bubble_wrapper = QFrame()
        bubble_wrapper.setObjectName("user_bubble_bg")
        bubble_wrapper.setStyleSheet(
            f"QFrame#user_bubble_bg {{"
            f"  background: {c['BUBBLE_USER']};"
            f"  border-radius: 18px;"
            f"  border-bottom-right-radius: 4px;"
            f"}}"
        )
        bw_layout = QVBoxLayout(bubble_wrapper)
        bw_layout.setContentsMargins(16, 10, 16, 10)
        bw_layout.setSpacing(2)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setFont(QFont("Segoe UI", 13))
        self.label.setStyleSheet(
            "color: #FFFFFF; background: transparent; "
            "padding: 0px;"
        )
        bw_layout.addWidget(self.label)

        time_label = QLabel("Maintenant")
        time_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; background: transparent;")
        time_label.setFont(QFont("Segoe UI", 10))
        bw_layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(bubble_wrapper)

        self.animate_in()

    def animate_in(self):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(250)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()


class AssistantBubble(QFrame):
    def __init__(self, text="", parent=None, avatar_emoji="🤖"):
        super().__init__(parent)
        self.setObjectName("assistant_bubble")
        self.setMaximumWidth(560)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        c = Theme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.avatar = QLabel(avatar_emoji)
        self.avatar.setFixedSize(32, 32)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(
            f"background: rgba(47,39,35,0.8); border-radius: 16px; "
            f"font-size: 16px;"
        )
        layout.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignTop)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)

        name = QLabel("Assistant IA")
        name.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent; font-weight: bold;")
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v.addWidget(name)

        bubble_wrapper = QFrame()
        bubble_wrapper.setObjectName("assistant_bubble_bg")
        border = f"border: 0.5px solid {c['CARD_BORDER']};"
        bubble_wrapper.setStyleSheet(
            f"QFrame#assistant_bubble_bg {{"
            f"  background: {c['BUBBLE_AI']};"
            f"  border-radius: 18px;"
            f"  border-bottom-left-radius: 4px;"
            f"  {border}"
            f"}}"
        )
        bw_layout = QVBoxLayout(bubble_wrapper)
        bw_layout.setContentsMargins(16, 10, 16, 10)
        bw_layout.setSpacing(0)

        self.text_browser = QLabel()
        self.text_browser.setObjectName("assistant_text")
        self.text_browser.setWordWrap(True)
        self.text_browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet(
            f"color: {c['TEXT_PRIMARY']}; background: transparent; "
            f"font-size: 13px;"
        )
        self.text_browser.setFont(QFont("Segoe UI", 13))

        if text:
            html = MarkdownRenderer.to_html(text)
            self.text_browser.setTextFormat(Qt.TextFormat.RichText)
            self.text_browser.setText(html)

        bw_layout.addWidget(self.text_browser)

        time_label = QLabel("Maintenant")
        time_label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        time_label.setFont(QFont("Segoe UI", 10))
        bw_layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight)

        v.addWidget(bubble_wrapper)
        layout.addLayout(v)
        layout.addStretch()

        self.animate_in()

    def animate_in(self):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def append_text(self, chunk):
        current = self.text_browser.text()
        if self.text_browser.textFormat() == Qt.TextFormat.RichText:
            from PySide6.QtGui import QTextDocument
            doc = QTextDocument()
            doc.setHtml(current)
            new_html = MarkdownRenderer.to_html(current + chunk)
            self.text_browser.setText(new_html)
        else:
            self.text_browser.setText(current + chunk)

    def set_stream_text(self, full_text):
        html = MarkdownRenderer.to_html(full_text)
        self.text_browser.setTextFormat(Qt.TextFormat.RichText)
        self.text_browser.setText(html)

    def set_plain_text(self, text):
        self.text_browser.setTextFormat(Qt.TextFormat.PlainText)
        self.text_browser.setText(text)
