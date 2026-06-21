from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QKeyEvent, QTextCursor

from utils.theme import Theme


class MessageInput(QFrame):
    send_requested = Signal(str)
    voice_requested = Signal()
    attach_requested = Signal()

    def __init__(self, placeholder="Pose une question...", parent=None):
        super().__init__(parent)
        self.setObjectName("message_input")
        self._setup_ui(placeholder)

    def _setup_ui(self, placeholder):
        c = Theme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 14)
        layout.setSpacing(8)

        self.btn_attach = QPushButton("📎")
        self.btn_attach.setObjectName("input_btn")
        self.btn_attach.setFixedSize(40, 40)
        self.btn_attach.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_attach.clicked.connect(self.attach_requested.emit)
        layout.addWidget(self.btn_attach)

        self.input_field = QTextEdit()
        self.input_field.setObjectName("chat_input")
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setFixedHeight(40)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_field.setFont(QFont("Segoe UI", 13))
        self.input_field.textChanged.connect(self._auto_resize)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field, stretch=1)

        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setObjectName("input_btn")
        self.btn_mic.setFixedSize(40, 40)
        self.btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic.clicked.connect(self.voice_requested.emit)
        layout.addWidget(self.btn_mic)

        self.btn_send = QPushButton("➤")
        self.btn_send.setObjectName("input_send_btn")
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._send)
        layout.addWidget(self.btn_send)

        self._update_style(c)

    def _update_style(self, c=None):
        if c is None:
            c = Theme.colors()
        self.setStyleSheet(f"""
            QFrame#message_input {{
                background: {c['BG']};
                border-top: 0.5px solid {c['DIVIDER']};
            }}
            QTextEdit#chat_input {{
                background: {c['INPUT_BG']};
                border: 1.5px solid {c['INPUT_BORDER']};
                border-radius: 20px;
                padding: 8px 14px;
                font-size: 13px;
                color: {c['TEXT_PRIMARY']};
                selection-background-color: {c['ACCENT']};
            }}
            QTextEdit#chat_input:focus {{
                border-color: {c['INPUT_FOCUS']};
            }}
            QPushButton#input_btn {{
                background: transparent;
                color: {c['TEXT_SECONDARY']};
                border: 1.5px solid {c['INPUT_BORDER']};
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton#input_btn:hover {{
                border-color: {c['ACCENT']};
                color: {c['ACCENT']};
            }}
            QPushButton#input_btn:disabled {{
                opacity: 0.5;
            }}
            QPushButton#input_send_btn {{
                background: {c['ACCENT']};
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                font-size: 18px;
            }}
            QPushButton#input_send_btn:hover {{
                background: {c['ACCENT_HOVER']};
            }}
            QPushButton#input_send_btn:disabled {{
                background: {c['TEXT_MUTED']};
                color: {c['BG']};
            }}
        """)

    def _auto_resize(self):
        doc = self.input_field.document().toPlainText()
        lines = doc.count("\n") + 1
        height = min(max(lines, 1) * 22 + 16, 120)
        self.input_field.setFixedHeight(height)

    def _send(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        self.send_requested.emit(text)

    def clear(self):
        self.input_field.clear()
        self.input_field.setFixedHeight(40)

    def set_placeholder(self, text):
        self.input_field.setPlaceholderText(text)

    def set_enabled(self, enabled):
        self.input_field.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        self.btn_mic.setEnabled(enabled)
        self.btn_attach.setEnabled(enabled)

    def focus(self):
        self.input_field.setFocus()

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key.Key_Return and key_event.modifiers() == Qt.KeyboardModifier.NoModifier:
                self._send()
                return True
            if key_event.key() == Qt.Key.Key_Return and key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                cursor = self.input_field.textCursor()
                cursor.insertText("\n")
                return True
        return super().eventFilter(obj, event)
