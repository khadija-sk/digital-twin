from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QCheckBox, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from controllers.goals_controller import GoalsController
from controllers.gamification_controller import GamificationController
from services.smart_goals_service import SmartGoalsService
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA, ALOEWOOD


class GoalsInsightWorker(QThread):
    result_ready = Signal(dict)

    def __init__(self, service):
        super().__init__()
        self.service = service

    def run(self):
        try:
            stats = self.service.get_summary_stats()
            inactive = self.service.get_inactive_goals()
            self.result_ready.emit({"stats": stats, "inactive": inactive})
        except Exception:
            self.result_ready.emit({"stats": {}, "inactive": []})


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())


class GoalsView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.ctrl = GoalsController(user.id)
        self.gami = GamificationController(user.id)
        self.smart = SmartGoalsService(user.id)
        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._load_insights()

    def _build_ui(self):
        c = Theme.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 32, 24, 32, 24)
        root.setSpacing(0)

        title = QLabel("My Goals")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        root.addWidget(title)
        root.addSpacing(20)

        self.insight_banner = QFrame()
        self.insight_banner.setObjectName("insight_banner")
        self.insight_banner.hide()
        root.addWidget(self.insight_banner)
        root.addSpacing(12)

        add_card = QFrame()
        add_card.setObjectName("goal_add_card")
        add_layout = QHBoxLayout(add_card)
        add_layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)

        self.new_task_input = QLineEdit()
        self.new_task_input.setObjectName("goal_input")
        self.new_task_input.setPlaceholderText("Add a goal...")
        self.new_task_input.returnPressed.connect(self._handle_add)
        add_layout.addWidget(self.new_task_input)

        btn_add = QPushButton("Add")
        btn_add.setObjectName("goal_btn_add")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._handle_add)
        add_layout.addWidget(btn_add)

        root.addWidget(add_card)
        root.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("goal_content")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        self.content_layout.setSpacing(6)

        self._populate()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _load_insights(self):
        self._insight_worker = GoalsInsightWorker(self.smart)
        self._insight_worker.result_ready.connect(self._on_insights)
        self._insight_worker.start()

    def _on_insights(self, data):
        stats = data.get("stats", {})
        inactive = data.get("inactive", [])
        if not stats:
            return
        c = Theme.colors()
        self.insight_banner.show()
        layout = self.insight_banner.layout() or QHBoxLayout(self.insight_banner)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 12, 16, 12)
        clear_layout(layout)

        stats_text = (
            f"Actifs: {stats.get('active', 0)}  |  "
            f"Atteints: {stats.get('achieved', 0)}  |  "
            f"Progression moyenne: {stats.get('avg_progress', 0)}%"
        )
        lbl = QLabel(stats_text)
        lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
        layout.addWidget(lbl)
        layout.addStretch()

        if inactive:
            inactive_lbl = QLabel(
                f"⚠️ {len(inactive)} objectif(s) inactif(s) depuis +14 jours"
            )
            inactive_lbl.setStyleSheet(
                f"color: {c['WARNING']}; font-size: 12px; background: transparent;"
            )
            layout.addWidget(inactive_lbl)

    def _populate(self):
        cl = self.content_layout
        goals = self.smart.get_goals_with_insights()

        active = [g for g in goals if g["status"] == "actif"]
        achieved = [g for g in goals if g["status"] == "atteint"]

        for goal in active:
            cl.addWidget(self._build_task_row_smart(goal, False))
        for goal in achieved:
            cl.addWidget(self._build_task_row_smart(goal, True))
        cl.addStretch()

    def _build_task_row_smart(self, goal, done=False):
        c = Theme.colors()
        row = QFrame()
        row.setObjectName("goal_row")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)  # 16, 10, 16, 10)

        top = QHBoxLayout()
        top.setSpacing(8)

        checkbox = QCheckBox()
        checkbox.setChecked(done)
        checkbox.setEnabled(not done)
        checkbox.stateChanged.connect(
            lambda state, gid=goal["id"], d=done: self._handle_check(gid, state, d)
        )
        top.addWidget(checkbox)

        text = QLabel(goal["description"])
        text.setStyleSheet(
            f"color: {c['TEXT_MUTED'] if done else c['TEXT_PRIMARY']}; "
            f"font-size: 13px; background: transparent;"
            f"{'text-decoration: line-through;' if done else ''}"
        )
        top.addWidget(text)
        top.addStretch()

        if not done and goal["next_action"]:
            tip = QLabel(goal["next_action"])
            tip.setStyleSheet(f"color: {c['ACCENT']}; font-size: 11px; background: transparent;")
            top.addWidget(tip)

        btn_del = QPushButton("Remove")
        btn_del.setObjectName("goal_btn_del")
        btn_del.clicked.connect(lambda _, gid=goal["id"]: self._handle_delete(gid))
        top.addWidget(btn_del)

        layout.addLayout(top)

        if not done:
            bar_row = QHBoxLayout()
            bar = QProgressBar()
            bar.setObjectName("goal_progress")
            bar.setRange(0, 100)
            bar.setValue(goal["progress_pct"])
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setFixedWidth(200)
            bar_row.addWidget(bar)
            pct_lbl = QLabel(f"{goal['progress_pct']}%")
            pct_lbl.setStyleSheet(
                f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;"
            )
            bar_row.addWidget(pct_lbl)
            bar_row.addStretch()
            layout.addSpacing(4)
            layout.addLayout(bar_row)

            if goal.get("estimated_completion"):
            #     est_lbl = QLabel(f"Estimation: {goal['estimated_completion']}")
            #     est_lbl.setStyleSheet(
            #         f"color: {c.get('TEXT_MUTED', '#888')}; font-size: 10px; background: transparent;"
            #     )
            #     bar_row.addWidget(est_lbl)
                pass

        return row

    def _handle_add(self):
        desc = self.new_task_input.text().strip()
        if not desc:
            return
        success, _ = self.ctrl.create_goal(desc, 1, "")
        if success:
            self.new_task_input.clear()
            self.refresh()

    def _handle_check(self, goal_id, state, already_done):
        if already_done:
            self.ctrl.mark_active(goal_id)
            self.refresh()
        elif state == 2:
            self.ctrl.mark_achieved(goal_id)
            self.gami.add_xp(30)
            self.refresh()

    def _handle_delete(self, goal_id):
        self.ctrl.delete_goal(goal_id)
        self.refresh()

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
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QWidget#goal_content {{ background-color: transparent; }}
            QFrame#goal_add_card {{
                background: {c['CARD_BG']};
                border-radius: 10px;
                border: 1px solid {c['CARD_BORDER']};
            }}
            QLineEdit#goal_input {{
                background: transparent;
                border: none;
                border-bottom: 1.5px solid {c['CARD_BORDER']};
                padding: 0 8px;
                font-size: 14px;
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit#goal_input:focus {{
                border-bottom: 2px solid {SAKURA};
            }}
            QPushButton#goal_btn_add {{
                background: {SAKURA};
                color: {DARK_CHOCOLATE};
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton#goal_btn_add:hover {{
                background: {c['ACCENT_HOVER']};
            }}
            QFrame#goal_row {{
                background: {c['CARD_BG']};
                border-radius: 8px;
                border: 1px solid {c['CARD_BORDER']};
            }}
            QPushButton#goal_btn_del {{
                background: transparent;
                color: {c['TEXT_MUTED']};
                border: 1px solid {c['CARD_BORDER']};
                border-radius: 14px;
                font-size: 11px;
                padding: 4px 12px;
            }}
            QPushButton#goal_btn_del:hover {{
                border-color: {SAKURA};
                color: {SAKURA};
            }}
            QFrame#insight_banner {{
                background: {c['BG_SECONDARY']};
                border-radius: 10px;
                border: 1px solid {c['CARD_BORDER']};
            }}
            QProgressBar#goal_progress {{
                background: {c['INPUT_BG']};
                border: none;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar#goal_progress::chunk {{
                background: {SAKURA};
                border-radius: 3px;
            }}
            QCheckBox {{
                spacing: 8px;
                color: {c['TEXT_PRIMARY']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1.5px solid {MILK_TEA};
                border-radius: 4px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {SAKURA};
                border-color: {SAKURA};
            }}
        """
