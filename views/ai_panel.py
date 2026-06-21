import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont

from controllers.ai_controller import AIController
from utils.theme import Theme
from views.chat.conversation_widget import ConversationWidget
from views.chat.message_input import MessageInput
from views.chat.chat_bubble import AssistantBubble


class AIWorker(QThread):
    chunk_received = Signal(str)
    stream_done = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, controller, message, history):
        super().__init__()
        self.controller = controller
        self.message = message
        self.history = history

    def run(self):
        try:
            full_text = ""
            for chunk in self.controller.ask_stream(self.message, self.history):
                full_text += chunk
                self.chunk_received.emit(chunk)
            self.stream_done.emit(full_text)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIPanel(QFrame):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.controller = AIController(user.id) if user else None
        self.history = []
        self._worker = None
        self._zombie_workers = []
        self._current_assistant_bubble = None
        self._full_stream_text = ""
        self.setObjectName("ai_panel")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.conversation = ConversationWidget()
        layout.addWidget(self.conversation, stretch=1)

        sep = QFrame()
        sep.setFixedHeight(1)
        c = Theme.colors()
        sep.setStyleSheet(f"background: {c['DIVIDER']};")
        layout.addWidget(sep)

        self.input_area = MessageInput(placeholder="Pose une question...")
        self.input_area.send_requested.connect(self._on_send)
        self.input_area.set_enabled(self.controller is not None)
        layout.addWidget(self.input_area)

    def _on_send(self, text):
        if not self.controller:
            return
        self.input_area.clear()
        self._do_send(text)

    def _do_send(self, text):
        self.conversation.add_user_message(text)
        self.history.append({"role": "user", "content": text})

        self.input_area.set_enabled(False)
        self.conversation.show_typing()

        self._current_assistant_bubble = None
        self._full_stream_text = ""

        if self._worker is not None and self._worker.isRunning():
            try:
                self._worker.chunk_received.disconnect()
                self._worker.stream_done.disconnect()
                self._worker.error_occurred.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._zombie_workers.append(self._worker)
            self._worker.finished.connect(lambda w=self._worker: self._zombie_workers.remove(w))

        self._worker = AIWorker(self.controller, text, list(self.history))
        self._worker.chunk_received.connect(self._on_chunk)
        self._worker.stream_done.connect(self._on_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_chunk(self, chunk):
        self.conversation.typing.hide()
        if self._current_assistant_bubble is None:
            self._current_assistant_bubble = self.conversation.add_assistant_message("")
            self._current_assistant_bubble.text_browser.setTextFormat(Qt.TextFormat.RichText)
        self._full_stream_text += chunk
        self._current_assistant_bubble.set_stream_text(self._full_stream_text)
        self.conversation._scroll_to_bottom()

    def _on_done(self, full_text):
        bubble = self._current_assistant_bubble
        self._remove_running_state()
        if bubble:
            bubble.set_stream_text(full_text)
        else:
            self.conversation.add_assistant_message(full_text)
        self.history.append({"role": "assistant", "content": full_text})
        self.input_area.set_enabled(True)
        self.input_area.focus()

    def _on_error(self, error):
        bubble = self._current_assistant_bubble
        self._remove_running_state()
        if bubble:
            bubble.set_plain_text(f"Erreur : {error}")
        else:
            self.conversation.add_assistant_message(f"Erreur : {error}")
        self.input_area.set_enabled(True)
        self.input_area.focus()

    def _remove_running_state(self):
        self._current_assistant_bubble = None
        self._full_stream_text = ""
        self.conversation.typing.hide()

    def refresh_theme(self):
        self.conversation.refresh_theme()

    def set_user(self, user):
        self.user = user
        if user:
            self.controller = AIController(user.id)
            self.input_area.set_enabled(True)
