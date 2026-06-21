# views/health_view.py

import logging
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QProgressBar,
    QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from controllers.checkin_controller import CheckinController
from controllers.journal_controller import JournalController
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA
from ia.pattern_detector import PatternDetector
from ia.predictor import Predictor
from ia.routine_suggester import RoutineSuggester


class HealthView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.checkin_ctrl = CheckinController(user.id)
        self.journal_ctrl = JournalController(user.id)
        self.detector = PatternDetector(user.id)
        self.predictor = Predictor(user.id)
        self.suggester = RoutineSuggester(user.id)
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 24)
        cl.setSpacing(14)
        self.content_layout = cl

        self._populate()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def _populate(self):
        cl = self.content_layout

        logs = self.checkin_ctrl.get_last_30_days()
        streak = self.checkin_ctrl.get_current_streak()
        burnout = self.checkin_ctrl.detect_burnout()
        patterns = []
        try:
            patterns = self.detector.detect_all()
        except Exception as e:
            logging.getLogger(__name__).warning("Erreur lors de la d\u00e9tection des patterns")
        prediction = self.predictor.predict_tomorrow_score()
        burnout_days = self.predictor.predict_burnout_risk_days()

        today_log = self.checkin_ctrl.get_today_checkin()

        if today_log:
            cl.addWidget(self._build_metrics_card(today_log, streak, logs))

        if burnout:
            cl.addWidget(self._build_alert_card())

        cl.addWidget(self._build_prediction_card(prediction, burnout_days))

        if patterns:
            cl.addWidget(self._build_patterns_card(patterns))

        if logs:
            cl.addWidget(self._build_trend_card(logs))
            try:
                summary = self.suggester.get_summary()
                cl.addWidget(self._build_routine_card(summary))
            except Exception as e:
                logging.getLogger(__name__).warning("Erreur lors de la r\u00e9cup\u00e9ration du r\u00e9sum\u00e9 de routine")

        if not logs:
            empty = QLabel("Fais tes premiers check-ins pour voir ton \u00e9tat de sant\u00e9 ici \u2728")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {Theme.get('TEXT_MUTED')}; font-size: 14px; "
                f"padding: 60px; background: transparent;"
            )
            cl.addWidget(empty)

        cl.addStretch()

    def _build_metrics_card(self, log, streak, logs):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("metric_card_main")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(12)

        header = QLabel("Vue d\u2019ensemble aujourd\u2019hui")
        header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        grid = QHBoxLayout()
        grid.setSpacing(10)
        metrics = [
            ("Score", f"{log.score_productivite}/100", SAKURA),
            ("Humeur", f"{log.humeur}/5", SAKURA),
            ("\u00c9nergie", f"{log.energie}/5", MILK_TEA),
            ("S\u00e9rie", f"{streak}j", c['ACCENT']),
        ]
        for label, value, color in metrics:
            chip = QFrame()
            chip.setObjectName("health_chip")
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(0, 0, 0, 0)  # 12, 10, 12, 10)
            chip_layout.setSpacing(4)
            chip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(value)
            vl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            vl.setStyleSheet(f"color: {color}; background: transparent;")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(vl)
            ll = QLabel(label)
            ll.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(ll)
            grid.addWidget(chip)

        layout.addLayout(grid)
        return card

    def _build_alert_card(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("alert_card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)
        layout.setSpacing(10)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {SAKURA}; border-radius: 4px;")
        layout.addWidget(dot)
        msg = QLabel("\u00c9nergie en baisse 3 jours de suite \u2014 risque de burnout d\u00e9tect\u00e9. Prends soin de toi.")
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {SAKURA}; font-size: 12px; background: transparent;")
        layout.addWidget(msg)
        layout.addStretch()
        return card

    def _build_prediction_card(self, prediction, burnout_days):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("health_section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(10)

        header = QLabel("Pr\u00e9dictions")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        if prediction.get("predicted") is not None:
            pred_row = QHBoxLayout()
            pred_row.setSpacing(16)
            pred_lbl = QLabel("Score demain :")
            pred_lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 13px; background: transparent;")
            pred_row.addWidget(pred_lbl)

            score_val = prediction["predicted"]
            score_color = SAKURA if score_val >= 60 else (MILK_TEA if score_val >= 40 else SAKURA)
            score_lbl = QLabel(str(score_val))
            score_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            score_lbl.setStyleSheet(f"color: {score_color}; background: transparent;")
            pred_row.addWidget(score_lbl)

            conf = prediction.get("confidence", "low")
            conf_map = {"high": SAKURA, "medium": MILK_TEA, "low": c["TEXT_MUTED"]}
            conf_dot = conf_map.get(conf, c["TEXT_MUTED"])
            conf_lbl = QLabel(f"\u00b7 {conf}")
            conf_lbl.setStyleSheet(f"color: {conf_dot}; font-size: 11px; background: transparent;")
            pred_row.addWidget(conf_lbl)

            tip = prediction.get("tip", "")
            if tip:
                tip_lbl = QLabel(tip)
                tip_lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 11px; background: transparent;")
                pred_row.addWidget(tip_lbl, alignment=Qt.AlignmentFlag.AlignRight)

            pred_row.addStretch()
            layout.addLayout(pred_row)
        else:
            no_data = QLabel("Pas assez de donn\u00e9es pour pr\u00e9dire. Continue tes check-ins !")
            no_data.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
            layout.addWidget(no_data)

        if burnout_days >= 0:
            burnout_row = QHBoxLayout()
            burnout_row.setSpacing(8)
            warn = QLabel()
            warn.setFixedSize(6, 6)
            warn.setStyleSheet(f"background: {MILK_TEA}; border-radius: 3px;")
            burnout_row.addWidget(warn, alignment=Qt.AlignmentFlag.AlignVCenter)
            b_text = f"Risque de burnout estim\u00e9 dans {burnout_days} jour(s) si la tendance continue" if burnout_days > 0 else "Risque de burnout imminent"
            b_lbl = QLabel(b_text)
            b_lbl.setStyleSheet(f"color: {MILK_TEA}; font-size: 12px; background: transparent;")
            burnout_row.addWidget(b_lbl)
            burnout_row.addStretch()
            layout.addLayout(burnout_row)

        return card

    def _build_patterns_card(self, patterns):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("health_section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(8)

        header = QLabel("Patterns d\u00e9tect\u00e9s")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        for p in patterns:
            row = QLabel(f"  {p}")
            row.setWordWrap(True)
            row.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
            layout.addWidget(row)
        return card

    def _build_trend_card(self, logs):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("health_section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(10)

        header = QLabel("Tendances (30 jours)")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        scores = [l.score_productivite or 0 for l in logs]
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_sleep = sum(l.sommeil for l in logs) / len(logs)
        avg_energy = sum(l.energie for l in logs) / len(logs)
        avg_mood = sum(l.humeur for l in logs) / len(logs)

        recent = scores[-7:] if len(scores) >= 7 else scores
        older = scores[:-7] if len(scores) >= 14 else scores[:len(scores)//2]
        trend_arrow = "\U0001f4c8" if (recent and older and sum(recent)/len(recent) > sum(older)/len(older)) else "\U0001f4c9" if (recent and older) else "\u27a1\ufe0f"

        grid = QHBoxLayout()
        grid.setSpacing(10)
        for label, value, color in [
            ("Moy. Score", f"{avg_score:.0f}", SAKURA),
            ("Moy. Sommeil", f"{avg_sleep:.1f}h", MILK_TEA),
            ("Moy. \u00c9nergie", f"{avg_energy:.1f}/5", SAKURA),
            ("Moy. Humeur", f"{avg_mood:.1f}/5", MILK_TEA),
            ("Tendance", trend_arrow, c['ACCENT']),
        ]:
            chip = QFrame()
            chip.setObjectName("health_chip")
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(0, 0, 0, 0)  # 8, 8, 8, 8)
            chip_layout.setSpacing(2)
            chip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(str(value))
            vl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            vl.setStyleSheet(f"color: {color}; background: transparent;")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(vl)
            ll = QLabel(label)
            ll.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 9px; background: transparent;")
            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(ll)
            grid.addWidget(chip)

        layout.addLayout(grid)

        bar_card = QFrame()
        bar_card.setObjectName("health_bar_card")
        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(0, 0, 0, 0)  # 14, 10, 14, 10)
        bar_layout.setSpacing(6)

        bar_layout.addWidget(self._labeled_bar("\u00c9nergie", avg_energy, 5, MILK_TEA))
        bar_layout.addWidget(self._labeled_bar("Humeur", avg_mood, 5, SAKURA))
        bar_layout.addWidget(self._labeled_bar("Sommeil", avg_sleep / 12, 1, MILK_TEA))

        layout.addWidget(bar_card)
        return card

    def _labeled_bar(self, label, value, max_val, color):
        c = Theme.colors()
        row = QHBoxLayout()
        row.setSpacing(10)
        lbl = QLabel(label)
        lbl.setFixedWidth(60)
        lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        row.addWidget(lbl)

        bar = QProgressBar()
        bar.setObjectName("health_progress")
        bar.setMinimum(0)
        bar.setMaximum(int(max_val * 100))
        bar.setValue(int(value * 100))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(f"""
            QProgressBar#health_progress {{
                background: rgba(215,192,174,0.1);
                border-radius: 4px;
                border: none;
            }}
            QProgressBar#health_progress::chunk {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        row.addWidget(bar, stretch=1)

        vl = QLabel(f"{value:.1f}")
        vl.setFixedWidth(30)
        vl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; background: transparent;")
        row.addWidget(vl)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setLayout(row)
        return w

    def _build_routine_card(self, summary):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("health_section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(8)

        header = QLabel("Routine sugg\u00e9r\u00e9e")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        text = QLabel(summary)
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 13px; background: transparent;")
        layout.addWidget(text)

        btn = QPushButton("Voir la routine compl\u00e8te \u2192")
        btn.setObjectName("health_link_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.on_navigate("routine"))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

        return card

    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)

        title = QLabel("Sant\u00e9 & Bien-\u00eatre")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')};")
        layout.addWidget(title)
        layout.addStretch()

        return bar

    def refresh(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._populate()

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c["TEXT_PRIMARY"]};
                background-color: {c["BG"]};
                font-family: Segoe UI;
            }}
            QFrame#topbar {{
                background-color: {c["BG"]};
                border-bottom: 0.5px solid {c["TOPBAR_BORDER"]};
            }}
            QWidget#main_area, QWidget#content_area {{
                background-color: {c["BG"]};
            }}
            QFrame#metric_card_main {{
                background: {c["CARD_BG"]};
                border-radius: 14px;
                border: 0.5px solid {c["CARD_BORDER"]};
            }}
            QFrame#health_chip {{
                background: rgba(215,192,174,0.08);
                border-radius: 10px;
            }}
            QFrame#health_section_card {{
                background: {c["CARD_BG"]};
                border-radius: 12px;
                border: 0.5px solid {c["CARD_BORDER"]};
            }}
            QFrame#health_bar_card {{
                background: rgba(215,192,174,0.08);
                border-radius: 8px;
            }}
            QFrame#alert_card {{
                background: rgba(248,215,218,0.07);
                border: 0.5px solid rgba(248,215,218,0.2);
                border-radius: 8px;
            }}
            QPushButton#health_link_btn {{
                background: transparent;
                color: {c["MILK_TEA"]};
                border: none;
                font-size: 11px;
                padding: 2px;
            }}
            QPushButton#health_link_btn:hover {{
                text-decoration: underline;
            }}
        """
