from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTextEdit,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
import os
from PySide6.QtWidgets import QFileDialog
from controllers.journal_controller import JournalController
from controllers.ai_controller import AIController
from controllers.llm_controller import LLMController
from services.prompt_builder import PromptBuilder
from utils.pdf_exporter import PDFExporter
from utils.csv_exporter import CSVExporter
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA

DAYS_FR = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_FR = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]

PROMPTS = [
    "What made you proud today?",
    "What could you have done better?",
    "What put you in a good mood?",
    "Describe your day in three words.",
    "What lesson did you learn today?",
    "What surprised you today?",
]

SUMMARY_WORKERS = []
ANALYSIS_WORKERS = []


def _format_date(d):
    return f"{DAYS_FR[d.weekday()]} {d.day} {MONTHS_FR[d.month]} {d.year}"


class SummaryWorker(QThread):
    result_ready = Signal(str)

    def __init__(self, user_id, entries):
        super().__init__()
        self.user_id = user_id
        self.entries = entries

    def run(self):
        try:
            llm = LLMController.get_instance()
            if llm and llm.is_available:
                combined = "\n\n".join(f"[{e.date}] {e.contenu[:300]}" for e in self.entries)
                prompt = PromptBuilder.build_journal_summary_prompt(combined)
                result = llm.generate_content(prompt)
                llm.log_model_usage(llm.active_model_name, "journal_summary")
                self.result_ready.emit(result)
            else:
                ctrl = AIController(self.user_id)
                combined = "\n\n".join(f"[{e.date}] {e.contenu[:300]}" for e in self.entries)
                result = ctrl.ask(
                    f"Here are my journal entries for the week:\n\n{combined}\n\n"
                    "Make a kind summary in 4-5 sentences: recurring themes, "
                    "emotional evolution, and one piece of advice."
                )
                self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit(f"Error: {str(e)}")


class JournalView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.ctrl = JournalController(user.id)
        self._selected_entry_id = None
        self._summary_worker = None
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        outer = QHBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch()

        inner = QWidget()
        inner.setObjectName("journal_inner_container")
        inner.setMaximumWidth(900)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(40, 48, 40, 48)
        layout.setSpacing(0)
        self._build_editor_content(layout)

        outer.addWidget(inner)
        outer.addStretch()
        root.addLayout(outer, stretch=1)

    def _build_topbar(self):
        c = Theme.colors()
        bar = QFrame()
        bar.setObjectName("journal_topbar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        btn_back = QPushButton("\u2190  Dashboard")
        btn_back.setObjectName("journal_btn_back")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.on_navigate("dashboard") if self.on_navigate else None)
        layout.addWidget(btn_back)

        title_lbl = QLabel("Journal")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title_lbl)

        streak = self.ctrl.get_streak()
        total = self.ctrl.get_total_entries()
        stats = QLabel(f"{streak}j \xb7 {total} entr.")
        stats.setStyleSheet(f"color: {SAKURA}; font-size: 12px; background: transparent;")
        layout.addWidget(stats)

        layout.addStretch()

        self.btn_summary = QPushButton("AI Summary")
        self.btn_summary.setObjectName("journal_btn_top")
        self.btn_summary.setFixedHeight(32)
        self.btn_summary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_summary.clicked.connect(self._handle_summary)
        layout.addWidget(self.btn_summary)

        btn_new = QPushButton("+ New")
        btn_new.setObjectName("journal_btn_top_new")
        btn_new.setFixedHeight(32)
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._new_entry)
        layout.addWidget(btn_new)

        btn_export = QPushButton("Export")
        btn_export.setObjectName("journal_btn_top")
        btn_export.setFixedHeight(32)
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_journal)
        layout.addWidget(btn_export)

        self._entry_popup_btn = QPushButton("\u25BC")
        self._entry_popup_btn.setObjectName("journal_btn_top")
        self._entry_popup_btn.setFixedWidth(36)
        self._entry_popup_btn.setFixedHeight(32)
        self._entry_popup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._entry_popup_btn.clicked.connect(self._show_entry_popup)
        layout.addWidget(self._entry_popup_btn)

        return bar

    def _show_entry_popup(self):
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        menu.setObjectName("journal_entry_menu")
        c = Theme.colors()
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['CARD_BG']}; border: 0.5px solid {c['CARD_BORDER']};
                border-radius: 10px; padding: 6px;
            }}
            QMenu::item {{ padding: 8px 16px; border-radius: 6px; color: {c['TEXT_PRIMARY']}; }}
            QMenu::item:selected {{ background: rgba(232,165,181,0.15); }}
        """)

        entries = self.ctrl.get_last_n_entries(30)
        if not entries:
            action = menu.addAction("No entries yet")
            action.setEnabled(False)
        else:
            for entry in entries:
                preview = entry.contenu[:40].replace("\n", " ")
                label = f"{_format_date(entry.date)[:15]}...  {preview}"
                action = menu.addAction(label)
                action.setData(entry.id)
                action.triggered.connect(
                    lambda checked=False, eid=entry.id, ec=entry.contenu, ed=entry.date:
                        self._load_entry(eid, ec, ed)
                )

        btn = self.sender() or self._entry_popup_btn
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _build_editor_content(self, parent_layout):
        c = Theme.colors()

        self.date_label = QLabel(_format_date(date.today()))
        self.date_label.setObjectName("journal_editor_date")
        self.date_label.setFont(QFont("Segoe UI", 13))
        parent_layout.addWidget(self.date_label)
        parent_layout.addSpacing(6)

        self.entry_title = QLabel("Today's entry")
        self.entry_title.setObjectName("journal_editor_title")
        self.entry_title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        parent_layout.addWidget(self.entry_title)
        parent_layout.addSpacing(20)

        import random
        self.prompt_label = QLabel(f"Prompt: {random.choice(PROMPTS)}")
        self.prompt_label.setObjectName("journal_prompt_label")
        self.prompt_label.setWordWrap(True)
        parent_layout.addWidget(self.prompt_label)
        parent_layout.addSpacing(24)

        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("journal_summary_frame")
        self.summary_frame.hide()
        sl = QVBoxLayout(self.summary_frame)
        sl.setContentsMargins(18, 14, 18, 14)
        sl.setSpacing(8)
        sum_header = QLabel("AI Weekly Summary")
        sum_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sum_header.setStyleSheet(f"color: {SAKURA}; background: transparent;")
        sl.addWidget(sum_header)
        self.summary_label = QLabel("Analyzing...")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 13px; background: transparent;")
        sl.addWidget(self.summary_label)
        parent_layout.addWidget(self.summary_frame)
        parent_layout.addSpacing(16)

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("journal_text_edit")
        self.text_edit.setPlaceholderText("Write whatever comes to mind...")
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setMinimumHeight(350)

        today_entry = self.ctrl.get_today_entry()
        if today_entry:
            self.text_edit.setPlainText(today_entry.contenu)
            self._selected_entry_id = today_entry.id

        parent_layout.addWidget(self.text_edit, stretch=1)
        parent_layout.addSpacing(24)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("journal_btn_save")
        self.btn_save.setFixedHeight(52)
        self.btn_save.setFixedWidth(140)
        self.btn_save.clicked.connect(self._handle_save)
        btn_row.addWidget(self.btn_save)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("journal_btn_delete")
        self.btn_delete.setFixedHeight(52)
        self.btn_delete.setFixedWidth(120)
        self.btn_delete.clicked.connect(self._handle_delete)
        if not today_entry:
            self.btn_delete.setEnabled(False)
        btn_row.addWidget(self.btn_delete)

        btn_row.addStretch()

        self.word_count = QLabel("0 word(s)")
        self.word_count.setObjectName("journal_word_count")
        self.word_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        btn_row.addWidget(self.word_count)

        parent_layout.addLayout(btn_row)

        self.text_edit.textChanged.connect(self._update_word_count)
        self._update_word_count()
        self._editor_date = date.today()

    def _export_journal(self):
        entries = self.ctrl.get_all_entries()
        if not entries:
            QMessageBox.information(self, "Empty journal", "Write an entry first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export journal",
            os.path.join(os.path.expanduser("~/Desktop"), f"digital_twin_journal_{date.today()}.pdf"),
            "PDF Files (*.pdf);;CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                CSVExporter.export_journal(entries, path)
            else:
                PDFExporter.export_journal(entries, path, self.user.nom)
            QMessageBox.information(self, "Exported", f"Journal saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _handle_summary(self):
        entries = self.ctrl.get_last_n_entries(7)
        if not entries:
            QMessageBox.information(self, "No entries", "Write at least one entry first!")
            return
        self.summary_frame.show()
        self.summary_label.setText("Analyzing...")
        self.btn_summary.setEnabled(False)
        self.btn_summary.setText("Analyzing...")
        self._summary_worker = SummaryWorker(self.user.id, entries)
        self._summary_worker.result_ready.connect(self._on_summary_ready)
        self._summary_worker.start()

    def _on_summary_ready(self, text):
        self.summary_label.setText(text)
        self.btn_summary.setEnabled(True)
        self.btn_summary.setText("AI Weekly Summary")

    def _new_entry(self):
        self._editor_date = date.today()
        self._selected_entry_id = None
        self.text_edit.clear()
        self.date_label.setText(_format_date(date.today()))
        self.entry_title.setText("New entry")
        self.btn_delete.setEnabled(False)
        self.summary_frame.hide()
        today_entry = self.ctrl.get_today_entry()
        if today_entry:
            self.text_edit.setPlainText(today_entry.contenu)
            self._selected_entry_id = today_entry.id
            self.entry_title.setText("Today's entry")
            self.btn_delete.setEnabled(True)

    def _load_entry(self, entry_id, contenu, entry_date):
        self._selected_entry_id = entry_id
        self._editor_date = entry_date
        self.text_edit.setPlainText(contenu)
        self.date_label.setText(_format_date(entry_date))
        self.entry_title.setText("Today's entry" if entry_date == date.today() else "Edit entry")
        self.btn_delete.setEnabled(True)
        self.summary_frame.hide()

    def _handle_save(self):
        contenu = self.text_edit.toPlainText().strip()
        if not contenu:
            QMessageBox.warning(self, "Empty", "Write something before saving!")
            return
        success, result = self.ctrl.save_entry(contenu, self._editor_date)
        if success:
            self._selected_entry_id = result.id
            self.btn_delete.setEnabled(True)
            self.entry_title.setText("Saved")
            QTimer.singleShot(1500, lambda: self.entry_title.setText("Today's entry"))
        else:
            QMessageBox.warning(self, "Error", str(result))

    def _handle_delete(self):
        if not self._selected_entry_id:
            return
        confirm = QMessageBox.question(
            self, "Delete", "Delete this entry permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.ctrl.delete_entry(self._selected_entry_id)
            self._selected_entry_id = None
            self.text_edit.clear()
            self.btn_delete.setEnabled(False)
            self.entry_title.setText("New entry")

    def _update_word_count(self):
        text = self.text_edit.toPlainText().strip()
        words = len(text.split()) if text else 0
        self.word_count.setText(f"{words} word(s)")

    def refresh(self):
        pass

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QFrame#journal_topbar {{
                background: {c['SIDEBAR_BG']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QPushButton#journal_btn_back {{
                background: transparent;
                color: {SAKURA};
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0 8px;
            }}
            QPushButton#journal_btn_back:hover {{ color: {c['TEXT_PRIMARY']}; }}
            QPushButton#journal_btn_top {{
                background: transparent;
                color: {c['TEXT_SECONDARY']};
                border: 1px solid {c['INPUT_BORDER']};
                border-radius: 16px;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton#journal_btn_top:hover {{
                border-color: {SAKURA};
                color: {SAKURA};
            }}
            QPushButton#journal_btn_top_new {{
                background: {SAKURA};
                color: {DARK_CHOCOLATE};
                border: none;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton#journal_btn_top_new:hover {{
                background: {c['ACCENT_HOVER']};
            }}
            QWidget#journal_inner_container {{ background: transparent; }}
            QFrame#journal_summary_frame {{
                background: rgba(248,215,218,0.08);
                border-radius: 10px;
                border: 0.5px solid rgba(248,215,218,0.2);
            }}
            QLabel#journal_editor_date {{
                color: {SAKURA};
                font-size: 13px;
                background: transparent;
            }}
            QLabel#journal_editor_title {{
                color: {c['TEXT_PRIMARY']};
                background: transparent;
            }}
            QLabel#journal_prompt_label {{
                color: {c['TEXT_MUTED']};
                font-size: 13px;
                background: rgba(248,215,218,0.05);
                padding: 10px 14px;
                border-radius: 8px;
                border: 0.5px solid rgba(248,215,218,0.15);
            }}
            QTextEdit#journal_text_edit {{
                background-color: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                color: {c['TEXT_PRIMARY']};
            }}
            QTextEdit#journal_text_edit:focus {{
                border: 1.5px solid {SAKURA};
            }}
            QPushButton#journal_btn_save {{
                background-color: {SAKURA};
                color: {DARK_CHOCOLATE};
                border: none;
                border-radius: 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#journal_btn_save:hover {{
                background-color: {c['ACCENT_HOVER']};
            }}
            QPushButton#journal_btn_delete {{
                background-color: transparent;
                color: {c['TEXT_MUTED']};
                border: 1.5px solid rgba(255,255,255,0.12);
                border-radius: 24px;
                font-size: 14px;
            }}
            QPushButton#journal_btn_delete:hover {{
                color: {SAKURA};
                border-color: {SAKURA};
            }}
            QPushButton#journal_btn_delete:disabled {{
                color: rgba(255,255,255,0.15);
                border-color: rgba(255,255,255,0.08);
            }}
            QLabel#journal_word_count {{
                color: {c['TEXT_MUTED']};
                font-size: 11px;
                background: transparent;
            }}
        """
