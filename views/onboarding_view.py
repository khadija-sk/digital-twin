from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from utils.theme import Theme, DARK_CHOCOLATE, BORDER_RADIUS, BORDER_RADIUS_LG, FONT_FAMILY


class OnboardingView(QFrame):
    def __init__(self, user, on_complete):
        super().__init__()
        self.user = user
        self.on_complete = on_complete
        self.setObjectName("onboarding_overlay")
        c = Theme.colors()
        self.setStyleSheet(f"""
            #onboarding_overlay {{
                background: {c['MODAL_OVERLAY']};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("onboarding_card")
        card.setFixedSize(520, 480)
        c2 = Theme.colors()
        card.setStyleSheet(f"""
            #onboarding_card {{
                background: {c2['CARD_BG']};
                border: 1px solid {c2['CARD_BORDER']};
                border-radius: {BORDER_RADIUS_LG}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 36, 40, 36)
        layout.setSpacing(0)

        icon = QLabel("👋")
        icon.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 36))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: transparent;")
        layout.addWidget(icon)
        layout.addSpacing(12)

        title = QLabel("Bienvenue sur Digital Twin !")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(6)

        sub = QLabel("Je vais apprendre à te connaître\npour mieux t'accompagner.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {c2['TEXT_SECONDARY']}; font-size: 13px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(28)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(6)
        name_label = QLabel("Comment t'appelles-tu ?")
        name_label.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; font-size: 12px; font-weight: 600; background: transparent;")
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit(self.user.nom)
        self.name_input.setFixedHeight(44)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {c2['INPUT_BG']}; border: 1.5px solid {c2['INPUT_BORDER']};
                border-radius: {BORDER_RADIUS}px; padding: 0 14px;
                font-size: 14px; color: {c2['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{ border-color: {c2['INPUT_FOCUS']}; }}
        """)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        layout.addSpacing(16)

        goal_layout = QVBoxLayout()
        goal_layout.setSpacing(6)
        goal_label = QLabel("Quel est ton principal objectif ?")
        goal_label.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; font-size: 12px; font-weight: 600; background: transparent;")
        goal_layout.addWidget(goal_label)
        self.goal_combo = QComboBox()
        self.goal_combo.addItems([
            "Améliorer ma productivité",
            "Mieux gérer mon stress",
            "Développer une routine saine",
            "Suivre mes progrès",
            "Optimiser mon temps",
        ])
        self.goal_combo.setFixedHeight(44)
        self.goal_combo.setStyleSheet(f"""
            QComboBox {{
                background: {c2['INPUT_BG']}; border: 1.5px solid {c2['INPUT_BORDER']};
                border-radius: {BORDER_RADIUS}px; padding: 0 14px;
                font-size: 14px; color: {c2['TEXT_PRIMARY']};
            }}
            QComboBox:focus {{ border-color: {c2['INPUT_FOCUS']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{ image: none; border: none; }}
            QComboBox QAbstractItemView {{
                background: {c2['CARD_BG']}; border: 1px solid {c2['CARD_BORDER']};
                selection-background-color: {c2['ACCENT']}; color: {c2['TEXT_PRIMARY']};
            }}
        """)
        goal_layout.addWidget(self.goal_combo)
        layout.addLayout(goal_layout)
        layout.addSpacing(16)

        wake_layout = QVBoxLayout()
        wake_layout.setSpacing(6)
        wake_label = QLabel("À quelle heure te réveilles-tu habituellement ?")
        wake_label.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; font-size: 12px; font-weight: 600; background: transparent;")
        wake_layout.addWidget(wake_label)
        self.wake_input = QLineEdit("07:00")
        self.wake_input.setFixedHeight(44)
        self.wake_input.setStyleSheet(f"""
            QLineEdit {{
                background: {c2['INPUT_BG']}; border: 1.5px solid {c2['INPUT_BORDER']};
                border-radius: {BORDER_RADIUS}px; padding: 0 14px;
                font-size: 14px; color: {c2['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{ border-color: {c2['INPUT_FOCUS']}; }}
        """)
        wake_layout.addWidget(self.wake_input)
        layout.addLayout(wake_layout)
        layout.addSpacing(24)

        btn = QPushButton("Commencer l'aventure ✨")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {c2['BTN_PRIMARY_BG']}; color: {c2['BTN_PRIMARY_TEXT']};
                border: none; border-radius: {BORDER_RADIUS}px;
                font-size: 15px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {c2['ACCENT_HOVER']}; }}
        """)
        btn.clicked.connect(self._complete)
        layout.addWidget(btn)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _complete(self):
        name = self.name_input.text().strip() or self.user.nom
        goal = self.goal_combo.currentText()
        wake = self.wake_input.text().strip() or "07:00"
        self.on_complete({"name": name, "goal": goal, "wake_time": wake})


class WeeklyReportPopup(QFrame):
    def __init__(self, data: dict, on_close):
        super().__init__()
        self.on_close = on_close
        self.setObjectName("report_overlay")
        c = Theme.colors()
        self.setStyleSheet(f"#report_overlay {{ background: {c['MODAL_OVERLAY']}; }}")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("report_card")
        card.setFixedSize(460, 380)
        c2 = Theme.colors()
        card.setStyleSheet(f"""
            #report_card {{
                background: {c2['CARD_BG']};
                border: 1px solid {c2['CARD_BORDER']};
                border-radius: {BORDER_RADIUS_LG}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 36, 32, 36, 32)
        layout.setSpacing(0)

        title = QLabel("📊 Rapport Hebdomadaire")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(4)
        sub = QLabel("Voici un résumé de ta semaine dernière.")
        sub.setStyleSheet(f"color: {c2['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(20)

        stats = [
            ("Score moyen", f"{data.get('avg_score', '-')}/100"),
            ("Check-ins", str(data.get('checkins', 0))),
            ("Sessions Pomodoro", str(data.get('sessions', 0))),
            ("Objectifs complétés", str(data.get('goals', 0))),
            ("Journals écrits", str(data.get('journals', 0))),
        ]
        for label, value in stats:
            row = QHBoxLayout()
            row.setSpacing(12)
            dot = QLabel()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background: {c2['ACCENT']}; border-radius: 3px;")
            row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {c2['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
            row.addWidget(lbl, stretch=1)
            val = QLabel(value)
            val.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 14, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {c2['TEXT_PRIMARY']}; background: transparent;")
            row.addWidget(val)
            layout.addLayout(row)
            layout.addSpacing(10)

        layout.addSpacing(16)

        btn = QPushButton("Super, merci !")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {c2['BTN_PRIMARY_BG']}; color: {c2['BTN_PRIMARY_TEXT']};
                border: none; border-radius: {BORDER_RADIUS}px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {c2['ACCENT_HOVER']}; }}
        """)
        btn.clicked.connect(lambda: (self.deleteLater(), self.on_close() if self.on_close else None))
        layout.addWidget(btn)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
