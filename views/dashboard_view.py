from datetime import date, datetime
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

from views.heatmap_widget import HeatmapWidget
from controllers.checkin_controller import CheckinController
from controllers.journal_controller import JournalController
from controllers.timer_controller import TimerController
from controllers.gamification_controller import GamificationController
from utils.quote_manager import QuoteManager
from ia.pattern_detector import PatternDetector
from services.context_retriever import ContextRetriever
from services.prompt_builder import PromptBuilder
from views.spinner_widget import SpinnerWidget
from utils.theme import Theme, BORDER_RADIUS, BORDER_RADIUS_SM, FONT_FAMILY, MILK_TEA


class LLMInsightWorker(QThread):
    result_ready = Signal(str)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            from controllers.llm_controller import LLMController
            llm = LLMController.get_instance()
            if not llm or not llm.is_available:
                self.result_ready.emit("")
                return
            retriever = ContextRetriever(self.user_id)
            context = retriever.get_complete_context(7)
            prompt = PromptBuilder.build_insight_prompt(context)
            result = llm.generate_content(prompt)
            llm.log_model_usage(llm.active_model_name, "dashboard_insight")
            self.result_ready.emit(result.strip())
        except Exception as e:
            logging.getLogger(__name__).warning("Error generating LLM insight")
            self.result_ready.emit("")


class SectionLabel(QWidget):
    def __init__(self, text):
        super().__init__()
        c = Theme.colors()
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(8)
        label = QLabel(text)
        label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 13, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()


class Card(QFrame):
    def __init__(self, object_name="card"):
        super().__init__()
        self.setObjectName(object_name)


class DashboardView(QWidget):

    def __init__(self, user, on_navigate):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.checkin_ctrl = CheckinController(user.id)
        self.journal_ctrl = JournalController(user.id)
        self.timer_ctrl = TimerController(user.id)
        self.gami_ctrl = GamificationController(user.id)
        self._loading = True
        self._error = None
        self._data = {}
        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)
        QTimer.singleShot(50, self._load_all_data)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_main_area())

    def _build_main_area(self):
        c = Theme.colors()

        area = QWidget()
        area.setObjectName("main_area")
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        greeting = QLabel(f"Bonjour, {self.user.nom}")
        greeting.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 14, QFont.Weight.Medium))
        greeting.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        tb.addWidget(greeting)
        tb.addStretch()
        today_str = date.today().strftime("%A, %b %d %Y")
        date_badge = QLabel(today_str)
        date_badge.setStyleSheet(
            f"color: {c['ACCENT']}; background: {c['CARD_BORDER']}; "
            f"font-size: 11px; padding: 4px 10px; border-radius: 20px;"
        )
        tb.addWidget(date_badge)
        layout.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._scroll_content = QWidget()
        self._scroll_content.setObjectName("content_area")
        self._content_layout = QVBoxLayout(self._scroll_content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        self._content_layout.setSpacing(16)

        self._loading_spinner = SpinnerWidget("Chargement du tableau de bord...", size=36)
        self._content_layout.addWidget(self._loading_spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll)
        return area

    def _load_all_data(self):
        try:
            log = self.checkin_ctrl.get_today_checkin()
            score = log.score_productivite if log else None
            streak = self.checkin_ctrl.get_current_streak()
            burnout = self.checkin_ctrl.detect_burnout()
            last_30 = self.checkin_ctrl.get_last_30_days()
            total_checkins = self.gami_ctrl.get_total_checkins()
            total_sessions = self.gami_ctrl.get_total_sessions()
            today_sessions = self.timer_ctrl.get_today_sessions()
            badges = self.gami_ctrl.get_all_badges()
            journal_entries = self.journal_ctrl.get_last_n_entries(5)
            patterns = []
            try:
                detector = PatternDetector(self.user.id)
                patterns = detector.detect_all()
            except Exception:
                pass

            self._data = dict(
                log=log, score=score, streak=streak,
                burnout=burnout, last_30=last_30,
                total_checkins=total_checkins,
                total_sessions=total_sessions,
                today_sessions=today_sessions,
                badges=badges, journal_entries=journal_entries,
                patterns=patterns
            )
            self._loading = False
            self._error = None
        except Exception as e:
            self._error = str(e)
            self._loading = False

        self._rebuild_content()

    def _rebuild_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        c = Theme.colors()

        if self._error:
            ec = self._build_error_card(f"Could not load data: {self._error}")
            self._content_layout.addWidget(ec)
            self._content_layout.addStretch()
            return

        if self._loading:
            spinner = SpinnerWidget("Chargement...", size=36)
            self._content_layout.addWidget(spinner, alignment=Qt.AlignmentFlag.AlignCenter)
            self._content_layout.addStretch()
            return

        d = self._data

        if d.get("burnout"):
            self._content_layout.addWidget(self._build_alert())

        self._content_layout.addWidget(self._build_metrics(
            d.get("score"), d.get("streak"),
            d.get("total_checkins"), d.get("today_sessions")
        ))

        insight_card = self._build_gemini_insight_card()
        if insight_card:
            self._content_layout.addWidget(insight_card)

        self._content_layout.addWidget(self._build_quote_card(d.get("log")))

        if d.get("patterns"):
            self._content_layout.addWidget(self._build_patterns_card(d["patterns"]))

        self._content_layout.addWidget(self._build_heatmap_card(d.get("last_30", [])))

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        bottom_row.addWidget(self._build_checkin_card(d.get("log")), stretch=2)
        bottom_row.addWidget(self._build_shortcuts_card(), stretch=1)
        bw = QWidget()
        bw.setLayout(bottom_row)
        bw.setStyleSheet("background: transparent;")
        self._content_layout.addWidget(bw)

        self._content_layout.addWidget(self._build_activity_log(
            d.get("last_30", []),
            d.get("journal_entries", []),
            d.get("badges", []),
        ))

        self._content_layout.addWidget(self._build_usage_stats(
            d.get("total_checkins", 0),
            d.get("total_sessions", 0),
            d.get("last_30", []),
        ))

        self._content_layout.addStretch()

    def _build_error_card(self, message):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("error_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {c['ERROR']}; font-size: 13px; background: transparent;")
        layout.addWidget(msg)
        retry = QPushButton("Retry")
        retry.setObjectName("retry_btn")
        retry.setCursor(Qt.CursorShape.PointingHandCursor)
        retry.clicked.connect(self._load_all_data)
        layout.addWidget(retry, alignment=Qt.AlignmentFlag.AlignCenter)
        return card

    def _build_alert(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("alert_bar")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 14, 10, 14, 10)
        layout.setSpacing(10)
        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background: {c['WARNING']}; border-radius: 3px;")
        layout.addWidget(dot)
        msg = QLabel("Energy declining for 3 days - burnout risk detected. Take care of yourself.")
        msg.setStyleSheet(f"color: {c['WARNING']}; font-size: 12px; background: transparent;")
        layout.addWidget(msg)
        layout.addStretch()
        return card

    def _build_metrics(self, score, streak, total_checkins, today_sessions):
        c = Theme.colors()
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(10)

        score_display = str(score) if score is not None else "-"
        cards = [
            ("Productivity Score", score_display, "out of 100"),
            ("Current Streak", str(streak or 0), "days in a row"),
            ("Total Check-ins", str(total_checkins or 0), "all time"),
            ("Sessions Today", str(today_sessions or 0), "Pomodoro done"),
        ]
        for i, (label, value, sub) in enumerate(cards):
            card = self._metric_card(label, value, sub)
            layout.addWidget(card, i // 2, i % 2)
        return widget

    def _metric_card(self, label, value, sub):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("metric_card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setFixedHeight(100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 14, 18, 14)
        layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {c['STAT_LABEL']}; font-size: 11px; background: transparent;")
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 24, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {c['STAT_VALUE']}; background: transparent;")
        layout.addWidget(val)

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        layout.addWidget(sub_lbl)

        return card

    def _build_gemini_insight_card(self):
        from controllers.llm_controller import LLMController
        llm = LLMController.get_instance()
        if not llm or not llm.is_available:
            return None
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("insight_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 14, 20, 14)
        layout.setSpacing(8)

        header = QLabel("Daily Insight")
        header.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        header.setStyleSheet(f"color: {c['ACCENT']}; background: transparent;")
        layout.addWidget(header)

        self.gemini_insight_label = QLabel("Analyzing your data...")
        self.gemini_insight_label.setWordWrap(True)
        self.gemini_insight_label.setStyleSheet(
            f"color: {c['TEXT_PRIMARY']}; font-size: 13px; background: transparent;"
        )
        layout.addWidget(self.gemini_insight_label)

        if hasattr(self, '_gemini_worker') and self._gemini_worker is not None:
            if self._gemini_worker.isRunning():
                return card
            self._gemini_worker.deleteLater()
        self._gemini_worker = LLMInsightWorker(self.user.id)
        self._gemini_worker.result_ready.connect(self._on_gemini_insight)
        self._gemini_worker.start()
        return card

    def _on_gemini_insight(self, text):
        label = getattr(self, 'gemini_insight_label', None)
        if label and label.isWidgetType():
            if text:
                label.setText(text)
            else:
                label.setText("No insights available right now.")

    def _build_quote_card(self, log=None):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("quote_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(6)

        if log:
            quote = QuoteManager.get_quote(log.humeur, log.energie)
        else:
            quote = QuoteManager.get_random_quote()

        text_lbl = QLabel(f'"{quote["text"]}"')
        text_lbl.setWordWrap(True)
        text_lbl.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 14))
        text_lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent; font-style: italic;")
        layout.addWidget(text_lbl)

        author_lbl = QLabel(f"- {quote['author']}")
        author_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(author_lbl)

        return card

    def _build_patterns_card(self, patterns):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("patterns_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 14, 20, 14)
        layout.setSpacing(8)

        title = QLabel("Detected Patterns")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)

        for pattern in patterns:
            row = QLabel(f"  {pattern}")
            row.setWordWrap(True)
            row.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
            layout.addWidget(row)

        return card

    def _build_heatmap_card(self, logs):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("30-Day Activity")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        header.addWidget(title)
        header.addStretch()
        count_lbl = QLabel(f"{len(logs)} check-ins")
        count_lbl.setStyleSheet(
            f"color: {c['TEXT_SECONDARY']}; font-size: 10px;"
        )
        header.addWidget(count_lbl)
        layout.addLayout(header)

        checkin_dates = {log.date for log in logs}
        heatmap = HeatmapWidget(checkin_dates=checkin_dates, days=30)
        layout.addWidget(heatmap)

        return card

    def _build_checkin_card(self, log=None):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Today's Check-in")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)

        if log:
            ci_row = QHBoxLayout()
            ci_row.setSpacing(8)
            for value, sub_label in [
                (f"{log.sommeil}h", "Sleep"),
                (f"{log.humeur}/5", "Mood"),
                (f"{log.energie}/5", "Energy"),
            ]:
                ci_row.addWidget(self._ci_chip(value, sub_label))
            layout.addLayout(ci_row)

            prog_lbl = QLabel(f"Score: {log.score_productivite}/100")
            prog_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10.5px; background: transparent;")
            layout.addWidget(prog_lbl)

            bar = QProgressBar()
            bar.setObjectName("prog_bar")
            bar.setValue(log.score_productivite)
            bar.setTextVisible(False)
            bar.setFixedHeight(4)
            layout.addWidget(bar)
        else:
            msg = QLabel("No check-in recorded yet today.")
            msg.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
            layout.addWidget(msg)
            btn = QPushButton("Do my check-in")
            btn.setObjectName("btn_action")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.on_navigate("checkin"))
            layout.addWidget(btn)

        layout.addStretch()
        return card

    def _ci_chip(self, value, label):
        c = Theme.colors()
        chip = QFrame()
        chip.setObjectName("ci_chip")
        chip_layout = QVBoxLayout(chip)
        chip_layout.setContentsMargins(0, 0, 0, 0)  # 8, 10, 8, 10)
        chip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_layout.setSpacing(3)

        val_lbl = QLabel(value)
        val_lbl.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 18, QFont.Weight.Medium))
        val_lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_layout.addWidget(val_lbl)

        sub_lbl = QLabel(label)
        sub_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_layout.addWidget(sub_lbl)

        return chip

    def _build_shortcuts_card(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Quick Access")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(7)
        shortcuts = [
            ("Timer",       "timer"),
            ("Statistics",  "stats"),
            ("AI Analysis", "ai"),
            ("Objectives",  "goals"),
            ("Journal",     "journal"),
            ("Settings",    "settings"),
        ]
        for i, (label, page) in enumerate(shortcuts):
            btn = QPushButton(label)
            btn.setObjectName("shortcut_btn")
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=page: self.on_navigate(p))
            grid.addWidget(btn, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()
        return card

    def _build_activity_log(self, checkins, journal_entries, badges):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Recent Activity")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        items = []
        for log in checkins[-7:]:
            label = f"Check-in: mood {log.humeur}/5, energy {log.energie}/5, sleep {log.sommeil}h"
            items.append((log.date, "checkin", label))
        for entry in journal_entries:
            preview = entry.contenu[:60] + "..." if len(entry.contenu) > 60 else entry.contenu
            items.append((entry.date, "journal", f"Journal: {preview}"))
        for badge in badges[:5]:
            items.append((badge.date_obtention, "badge", f"Badge unlocked: {badge.nom} (+{badge.xp_gagne} XP)"))

        items.sort(key=lambda x: x[0], reverse=True)
        items = items[:10]

        if not items:
            empty = QLabel("No recent activity.")
            empty.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; padding: 8px 0; background: transparent;")
            layout.addWidget(empty)
        else:
            for d, typ, text in items:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)  # 0, 4, 0, 4)
                row.setSpacing(8)

                dot_color = {
                    "checkin": MILK_TEA,
                    "journal": c['ACCENT'],
                    "badge": c['ACCENT'],
                }.get(typ, MILK_TEA)
                dot = QLabel()
                dot.setFixedSize(6, 6)
                dot.setStyleSheet(f"background: {dot_color}; border-radius: 3px;")
                row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)

                date_lbl = QLabel(d.strftime("%d %b") if isinstance(d, date) else str(d)[:10])
                date_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; min-width: 50px; background: transparent;")
                date_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
                row.addWidget(date_lbl)

                text_lbl = QLabel(text)
                text_lbl.setWordWrap(True)
                text_lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 11.5px; background: transparent;")
                row.addWidget(text_lbl, stretch=1)

                layout.addLayout(row)

        view_all = QPushButton("View full history")
        view_all.setObjectName("text_link")
        view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all.clicked.connect(lambda: self.on_navigate("stats"))
        layout.addWidget(view_all, alignment=Qt.AlignmentFlag.AlignRight)

        return card

    def _build_usage_stats(self, total_checkins, total_sessions, last_30):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Usage Statistics")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        active_days = len(last_30)
        total = total_checkins + total_sessions
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        stat_items = [
            ("Total Check-ins", str(total_checkins)),
            ("Pomodoro Sessions", str(total_sessions)),
            ("Active Days (30d)", f"{active_days}/30"),
            ("Activity Rate", f"{int(active_days / 30 * 100)}%" if active_days else "0%"),
        ]
        for i, (label, value) in enumerate(stat_items):
            col = i % 2
            row = i // 2
            sw = QFrame()
            sw.setObjectName("stat_box")
            sl = QVBoxLayout(sw)
            sl.setContentsMargins(0, 0, 0, 0)  # 14, 10, 14, 10)
            sl.setSpacing(2)
            vl = QLabel(value)
            vl.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 20, QFont.Weight.Bold))
            vl.setStyleSheet(f"color: {c['STAT_VALUE']}; background: transparent;")
            sl.addWidget(vl)
            ll = QLabel(label)
            ll.setStyleSheet(f"color: {c['STAT_LABEL']}; font-size: 10px; background: transparent;")
            sl.addWidget(ll)
            stats_grid.addWidget(sw, row, col)

        layout.addLayout(stats_grid)

        if total > 0:
            dist_layout = QVBoxLayout()
            dist_layout.setSpacing(6)
            dist_title = QLabel("Activity Distribution")
            dist_title.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
            dist_layout.addWidget(dist_title)

            ci_pct = int(total_checkins / total * 100)
            ss_pct = int(total_sessions / total * 100)
            for pct, color, label in [
                (ci_pct, c['ACCENT'], f"Check-ins ({ci_pct}%)"),
                (ss_pct, c['TEXT_MUTED'], f"Sessions ({ss_pct}%)"),
            ]:
                bar_row = QHBoxLayout()
                bar_row.setSpacing(8)
                ll = QLabel(label)
                ll.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; min-width: 120px; background: transparent;")
                bar_row.addWidget(ll)
                bar_w = QFrame()
                bar_w.setFixedHeight(8)
                bar_w.setStyleSheet(f"background: {c['SKELETON']}; border-radius: 4px;")
                fill = QFrame()
                fill.setFixedHeight(8)
                fill.setStyleSheet(f"background: {color}; border-radius: 4px;")
                fill.setFixedWidth(max(int(pct * 3), 4))
                inner = QHBoxLayout(bar_w)
                inner.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
                inner.setSpacing(0)
                inner.addWidget(fill)
                inner.addStretch()
                bar_row.addWidget(bar_w, stretch=1)
                dist_layout.addLayout(bar_row)

            layout.addLayout(dist_layout)

        return card

    def refresh_theme(self):
        self.setStyleSheet(self._get_style())

    def refresh(self):
        self.refresh_theme()
        old_layout = self.layout()
        if old_layout is not None:
            tmp = QWidget()
            tmp.setLayout(old_layout)
            tmp.deleteLater()
        self._loading = True
        self._build_ui()
        QTimer.singleShot(50, self._load_all_data)

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: {FONT_FAMILY};
            }}
            QFrame#topbar {{
                background-color: {c['BG']};
                border-bottom: 1px solid {c['TOPBAR_BORDER']};
            }}
            QWidget#main_area,
            QWidget#content_area {{
                background-color: {c['BG']};
            }}
            QFrame#alert_bar {{
                background: {c['BG']};
                border: 1px solid {c['WARNING']}44;
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#metric_card {{
                background: {c['STAT_CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#quote_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#patterns_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#insight_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-left: 3px solid {c['ACCENT']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS}px;
            }}
            QFrame#ci_chip {{
                background: {c['SKELETON']};
                border-radius: {BORDER_RADIUS_SM}px;
            }}
            QFrame#stat_box {{
                background: {c['SKELETON']};
                border-radius: {BORDER_RADIUS_SM}px;
            }}
            QFrame#error_card {{
                background: {c['CARD_BG']};
                border: 1px solid {c['ERROR']}44;
                border-radius: {BORDER_RADIUS}px;
            }}
            QProgressBar#prog_bar {{
                background: {c['SKELETON']};
                border-radius: 2px;
                border: none;
            }}
            QProgressBar#prog_bar::chunk {{
                background: {c['ACCENT']};
                border-radius: 2px;
            }}
            QPushButton#shortcut_btn {{
                background: {c['INPUT_BG']};
                border: 1px solid {c['INPUT_BORDER']};
                border-radius: {BORDER_RADIUS_SM}px;
                font-size: 11px;
                color: {c['TEXT_SECONDARY']};
            }}
            QPushButton#shortcut_btn:hover {{
                border-color: {c['ACCENT']};
                color: {c['TEXT_PRIMARY']};
            }}
            QPushButton#btn_action {{
                background: {c['BTN_PRIMARY_BG']};
                color: {c['BTN_PRIMARY_TEXT']};
                border: none;
                border-radius: {BORDER_RADIUS}px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#btn_action:hover {{
                background: {c['ACCENT_HOVER']};
            }}
            QPushButton#retry_btn {{
                background: transparent;
                color: {c['ACCENT']};
                border: 1px solid {c['ACCENT']}44;
                border-radius: {BORDER_RADIUS}px;
                font-size: 12px;
                padding: 6px 18px;
            }}
            QPushButton#retry_btn:hover {{
                background: {c['CARD_HOVER']};
            }}
            QPushButton#text_link {{
                background: transparent;
                color: {c['TEXT_MUTED']};
                border: none;
                font-size: 11px;
                padding: 2px;
            }}
            QPushButton#text_link:hover {{
                color: {c['ACCENT']};
            }}
        """
