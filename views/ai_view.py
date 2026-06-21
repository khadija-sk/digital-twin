import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from datetime import date
from PySide6.QtWidgets import QFileDialog, QMessageBox
from controllers.ai_controller import AIController
from ia.pattern_detector import PatternDetector
from ia.predictor import Predictor
from services.web_search_service import WebSearchService
from services.voice_service import VoiceService
from utils.pdf_exporter import PDFExporter
from views.spinner_widget import SpinnerWidget
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA
from views.chat.conversation_widget import ConversationWidget
from views.chat.message_input import MessageInput
from views.chat.chat_bubble import AssistantBubble, UserBubble


class StreamWorker(QThread):
    chunk_received = Signal(str)
    stream_done    = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, controller, message, history):
        super().__init__()
        self.controller = controller
        self.message    = message
        self.history    = history

    def run(self):
        try:
            full_text = ""
            for chunk in self.controller.ask_stream(self.message, self.history):
                full_text += chunk
                self.chunk_received.emit(chunk)
            self.stream_done.emit(full_text)
        except Exception as e:
            self.error_occurred.emit(str(e))


class InsightWorker(QThread):
    result_ready = Signal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            text = self.controller.get_daily_insight()
            self.result_ready.emit(text)
        except Exception:
            self.result_ready.emit("")


class WebSearchWorker(QThread):
    result_ready = Signal(str, str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            results = WebSearchService.search_and_format(self.query)
            augmented = f"{self.query}\n\n{results}\n\nRésume ces résultats en français."
            self.result_ready.emit(augmented, "")
        except Exception as e:
            self.result_ready.emit("", str(e))


class MicWorker(QThread):
    result_ready = Signal(str)

    def __init__(self, voice_service):
        super().__init__()
        self.voice = voice_service

    def run(self):
        text = self.voice.listen(timeout=5, phrase_time_limit=10)
        self.result_ready.emit(text)


class AIView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user        = user
        self.on_navigate = on_navigate
        self.controller  = AIController(user.id)
        self.history     = []
        self._worker     = None
        self._zombie_workers = []
        self._current_assistant_bubble = None
        self._current_web_assistant_bubble = None
        self._full_stream_text = ""
        self._web_search_mode = False
        self._voice = VoiceService()
        self._voice_mode = False

        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._load_insight()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header_bar())
        root.addWidget(self._build_actions_bar())
        root.addWidget(self._build_insight_bar())
        root.addWidget(self._build_patterns_bar())
        root.addWidget(self._build_prediction_bar())

        self.conversation = ConversationWidget()
        root.addWidget(self.conversation, stretch=1)

        self.input_area = MessageInput(placeholder="Pose une question sur tes donnees...")
        self.input_area.send_requested.connect(self._handle_send)
        self.input_area.voice_requested.connect(self._handle_mic)
        self.input_area.btn_attach.hide()
        root.addWidget(self.input_area)

    def _build_header_bar(self):
        bar = QFrame()
        bar.setObjectName("header_bar")
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        title = QLabel("Analyse IA")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; background: transparent;")
        layout.addWidget(title)

        layout.addStretch()

        try:
            provider_name = self.controller.get_provider_name()
            provider_label = QLabel(f"● {provider_name}")
            provider_label.setFont(QFont("Segoe UI", 11))
            provider_label.setStyleSheet(f"color: {Theme.get('TEXT_MUTED')}; background: transparent;")
            layout.addWidget(provider_label)
        except Exception:
            pass

        return bar

    def _build_actions_bar(self):
        bar = QFrame()
        bar.setObjectName("actions_bar")
        bar.setFixedHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(10)

        btn_export = QPushButton("Exporter")
        btn_export.setObjectName("btn_action")
        btn_export.setFixedHeight(26)
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_chat)
        layout.addWidget(btn_export)

        btn_clear = QPushButton("Nouvelle discussion")
        btn_clear.setObjectName("btn_action")
        btn_clear.setFixedHeight(26)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_chat)
        layout.addWidget(btn_clear)

        self.btn_web = QPushButton("🌐 Web")
        self.btn_web.setObjectName("btn_web_toggle")
        self.btn_web.setFixedHeight(26)
        self.btn_web.setCheckable(True)
        self.btn_web.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_web.clicked.connect(self._toggle_web_search)
        layout.addWidget(self.btn_web)

        self.btn_speak = QPushButton("🔊")
        self.btn_speak.setObjectName("btn_action")
        self.btn_speak.setFixedHeight(26)
        self.btn_speak.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_speak.clicked.connect(self._handle_speak_last)
        self.btn_speak.setToolTip("Lire la derniere reponse")
        self.btn_speak.hide()
        layout.addWidget(self.btn_speak)

        layout.addStretch()
        return bar

    def _build_insight_bar(self):
        self.insight_frame = QFrame()
        self.insight_frame.setObjectName("insight_bar")
        layout = QHBoxLayout(self.insight_frame)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(12)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {SAKURA}; border-radius: 4px;")
        layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)

        self.insight_label = QLabel("")
        self.insight_label.setWordWrap(True)
        self.insight_label.setStyleSheet(
            f"color: {Theme.get('TEXT_PRIMARY')}; font-size: 13px; background: transparent;"
        )
        self.insight_label.hide()
        layout.addWidget(self.insight_label, stretch=1)
        self.insight_frame.hide()
        return self.insight_frame

    def _build_patterns_bar(self):
        frame = QFrame()
        frame.setObjectName("patterns_bar")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(6)

        try:
            detector = PatternDetector(self.user.id)
            patterns = detector.detect_all()
        except Exception:
            patterns = []

        if not patterns:
            frame.hide()
            return frame

        header = QLabel("Patterns detectes")
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; background: transparent;")
        layout.addWidget(header)

        for p in patterns:
            row = QHBoxLayout()
            dash = QLabel()
            dash.setFixedSize(4, 4)
            dash.setStyleSheet(f"background: {SAKURA}; border-radius: 2px;")
            row.addWidget(dash, alignment=Qt.AlignmentFlag.AlignTop)
            row.addSpacing(8)
            lbl = QLabel(p)
            lbl.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; font-size: 12px; background: transparent;")
            row.addWidget(lbl, stretch=1)
            layout.addLayout(row)
        return frame

    def _build_prediction_bar(self):
        frame = QFrame()
        frame.setObjectName("prediction_bar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(12)

        try:
            predictor = Predictor(self.user.id)
            result    = predictor.predict_tomorrow_score()
        except Exception:
            frame.hide()
            return frame

        if result["predicted"] is None:
            frame.hide()
            return frame

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {MILK_TEA}; border-radius: 4px;")
        layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)

        pred_lbl = QLabel(f"Score predit demain : {result['predicted']}/100  -  {result['tip']}")
        pred_lbl.setWordWrap(True)
        pred_lbl.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; font-size: 12px; background: transparent;")
        layout.addWidget(pred_lbl, stretch=1)
        return frame

    def _toggle_web_search(self):
        self._web_search_mode = self.btn_web.isChecked()
        self.btn_web.setText("🌐 Web" if self._web_search_mode else "🌐 Web")
        self.input_area.set_placeholder(
            "Recherche sur le Web..." if self._web_search_mode
            else "Pose une question sur tes donnees..."
        )

    def _handle_send(self, text):
        if not text:
            return
        self.input_area.clear()
        if self._web_search_mode:
            self._send_web_search(text)
        else:
            self._send_message(text)

    def _send_web_search(self, query):
        self.history.append({"role": "user", "content": f"[Recherche Web] {query}"})
        self.input_area.set_enabled(False)
        self.conversation.add_user_message(f"🔍 Recherche web : {query}")
        self.conversation.show_typing()

        self._current_web_assistant_bubble = None

        def on_search_ready(augmented_query, error):
            if error:
                self.conversation.typing.hide()
                self.conversation.add_assistant_message(f"Erreur de recherche : {error}")
                self.input_area.set_enabled(True)
                return

            if self._worker is not None and self._worker.isRunning():
                try:
                    self._worker.chunk_received.disconnect()
                    self._worker.stream_done.disconnect()
                    self._worker.error_occurred.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self._zombie_workers.append(self._worker)
                self._worker.finished.connect(lambda w=self._worker: self._zombie_workers.remove(w))
            self._worker = StreamWorker(self.controller, augmented_query, list(self.history))
            self._worker.chunk_received.connect(self._on_chunk)
            self._worker.stream_done.connect(self._on_stream_done)
            self._worker.error_occurred.connect(self._on_stream_error)
            self._worker.start()

        self._search_worker = WebSearchWorker(query)
        self._search_worker.result_ready.connect(on_search_ready)
        self._search_worker.start()

    def _send_message(self, text):
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
        self._worker = StreamWorker(self.controller, text, list(self.history))
        self._worker.chunk_received.connect(self._on_chunk)
        self._worker.stream_done.connect(self._on_stream_done)
        self._worker.error_occurred.connect(self._on_stream_error)
        self._worker.start()

    def _on_chunk(self, chunk):
        self.conversation.typing.hide()
        if self._current_assistant_bubble is None:
            self._current_assistant_bubble = self.conversation.add_assistant_message("")
            self._current_assistant_bubble.text_browser.setTextFormat(Qt.TextFormat.RichText)
        self._full_stream_text += chunk
        self._current_assistant_bubble.set_stream_text(self._full_stream_text)
        self.conversation._scroll_to_bottom()

    def _on_stream_done(self, full_text):
        bubble = self._current_assistant_bubble
        self._remove_running_state()
        if bubble:
            bubble.set_stream_text(full_text)
        else:
            self.conversation.add_assistant_message(full_text)
        self.history.append({"role": "assistant", "content": full_text})
        self.input_area.set_enabled(True)
        self.input_area.focus()
        self.btn_speak.show()

    def _on_stream_error(self, error):
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
        self._current_web_assistant_bubble = None
        self._full_stream_text = ""
        self.conversation.typing.hide()

    def _handle_mic(self):
        if self._voice_mode:
            return
        self._voice_mode = True
        self.input_area.btn_mic.setText("⏳")
        self.input_area.btn_mic.setEnabled(False)
        self.input_area.set_placeholder("Écoute...")
        self._mic_worker = MicWorker(self._voice)
        self._mic_worker.result_ready.connect(self._on_mic_result)
        self._mic_worker.start()

    def _on_mic_result(self, text):
        self.input_area.btn_mic.setText("🎤")
        self.input_area.btn_mic.setEnabled(True)
        self._voice_mode = False
        if text:
            self.input_area.input_field.setText(text)
            self._handle_send(text)
        else:
            self.input_area.set_placeholder(
                "Recherche sur le Web..." if self._web_search_mode
                else "Pose une question sur tes donnees..."
            )

    def _handle_speak_last(self):
        if not self.history:
            return
        last = self.history[-1]
        if last["role"] == "assistant":
            text = last.get("content", "")
            if isinstance(text, list):
                text = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in text)
            self._voice.speak(text)

    def _export_chat(self):
        if not self.history:
            QMessageBox.information(self, "Conversation vide", "Envoie d'abord un message.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la conversation",
            os.path.join(os.path.expanduser("~/Desktop"), f"digital_twin_chat_{date.today()}.pdf"),
            "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return
        try:
            messages = []
            for msg in self.history:
                role = "user" if msg["role"] == "user" else "assistant"
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in content
                    )
                messages.append({"role": role, "content": content})
            PDFExporter.export_chat_history(messages, path, self.user.nom)
            QMessageBox.information(self, "Exporte", f"Conversation sauvegardee :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter la conversation : {e}")

    def _clear_chat(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
        self.conversation.clear()
        self.history.clear()
        self._current_assistant_bubble = None
        self._current_web_assistant_bubble = None

    def _load_insight(self):
        self._insight_worker = InsightWorker(self.controller)
        self._insight_worker.result_ready.connect(self._on_insight_ready)
        self._insight_worker.start()

    def _on_insight_ready(self, text):
        if text:
            self.insight_label.setText(text)
            self.insight_label.show()

    def refresh(self):
        self.setStyleSheet(self._get_style())
        self.conversation.refresh_theme()

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: Segoe UI;
            }}
            QFrame#actions_bar {{
                background-color: {c['BG']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QFrame#header_bar {{
                background-color: {c['BG']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QFrame#insight_bar {{
                background: {c['BG_SECONDARY']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QFrame#patterns_bar {{
                background: {c['BG_SECONDARY']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QFrame#prediction_bar {{
                background: {c['BG_SECONDARY']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QPushButton#btn_action {{
                background: transparent;
                color: {c['TEXT_SECONDARY']};
                border: 1px solid {c['INPUT_BORDER']};
                border-radius: 13px;
                font-size: 11px;
                padding: 0 12px;
            }}
            QPushButton#btn_action:hover {{
                color: {c['ACCENT']};
                border-color: {c['ACCENT']};
            }}
            QPushButton#btn_web_toggle {{
                background: transparent;
                color: {c['TEXT_SECONDARY']};
                border: 1px solid {c['INPUT_BORDER']};
                border-radius: 13px;
                font-size: 11px;
                padding: 0 10px;
            }}
            QPushButton#btn_web_toggle:hover {{
                border-color: {c['ACCENT']};
                color: {c['ACCENT']};
            }}
            QPushButton#btn_web_toggle:checked {{
                background: {c['ACCENT']};
                color: {c['BG']};
                border-color: {c['ACCENT']};
            }}
        """
