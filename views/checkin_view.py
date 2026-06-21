from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from controllers.checkin_controller import CheckinController
from controllers.gamification_controller import GamificationController
from views.badge_popup import show_badge_popups
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA


class CheckinView(QWidget):

    checkin_done = Signal()

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.controller = CheckinController(user.id)
        self.gami = GamificationController(user.id)
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        c = Theme.colors()
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
        else:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)  # 48, 36, 48, 36)
            layout.setSpacing(0)

        btn_back = QPushButton("Back to Dashboard")
        btn_back.setObjectName("btn_back")
        btn_back.setFixedHeight(36)
        btn_back.setFixedWidth(160)
        btn_back.clicked.connect(lambda: self.on_navigate("dashboard"))
        layout.addWidget(btn_back)

        title = QLabel("Daily Check-in")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(6)

        if self.controller.has_checkin_today():
            self._show_already_done(layout)
            return

        sub = QLabel(f"Hello {self.user.nom}, how are you today?")
        sub.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 13px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(32)

        layout.addWidget(self._section_title("Sleep hours"))
        layout.addSpacing(16)
        self.sommeil_slider = self._make_slider(1, 12, 7)
        self.sommeil_label = self._value_label("7h")
        self.sommeil_slider.valueChanged.connect(lambda v: self.sommeil_label.setText(f"{v}h"))
        layout.addWidget(self._slider_row(self.sommeil_slider, self.sommeil_label, "1h", "12h"))
        layout.addSpacing(28)

        layout.addWidget(self._section_title("Mood"))
        layout.addSpacing(10)
        self.humeur_slider = self._make_slider(1, 5, 3)
        self.humeur_label = self._value_label("3/5")
        self.humeur_slider.valueChanged.connect(lambda v: self.humeur_label.setText(f"{v}/5"))
        layout.addWidget(self._slider_row(self.humeur_slider, self.humeur_label, "1", "5"))
        layout.addSpacing(28)

        layout.addWidget(self._section_title("Energy level"))
        layout.addSpacing(10)
        self.energie_slider = self._make_slider(1, 5, 3)
        self.energie_label = self._value_label("3/5")
        self.energie_slider.valueChanged.connect(lambda v: self.energie_label.setText(f"{v}/5"))
        layout.addWidget(self._slider_row(self.energie_slider, self.energie_label, "1", "5"))
        layout.addSpacing(36)

        btn = QPushButton("Save check-in")
        btn.setFixedHeight(52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SAKURA}; color: {DARK_CHOCOLATE};
                border: none; border-radius: 26px;
                font-size: 15px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {c['ACCENT_HOVER']}; }}
        """)
        btn.clicked.connect(self._handle_save)
        layout.addWidget(btn)
        layout.addStretch()

    def _show_already_done(self, layout):
        c = Theme.colors()
        log = self.controller.get_today_checkin()
        if log:
            msg = QLabel("You already did your check-in today!")
            msg.setFont(QFont("Segoe UI", 15))
            msg.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; background: transparent;")
            layout.addWidget(msg)
            layout.addSpacing(12)
            values = [
                (f"Sleep: {log.sommeil}h", c['CARD_BG']),
                (f"Mood: {log.humeur}/5", c['CARD_BG']),
                (f"Energy: {log.energie}/5", c['CARD_BG']),
                (f"Score: {log.score_productivite}/100", c['CARD_BG']),
            ]
            for text, color in values:
                lbl = QLabel(text)
                lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: {color}; font-size: 14px; padding: 6px 12px; border-radius: 6px;")
                layout.addWidget(lbl)
        else:
            empty = QLabel("No check-in found.")
            empty.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 14px; background: transparent;")
            layout.addWidget(empty)

    def _handle_save(self):
        try:
            humeur = self.humeur_slider.value()
            energie = self.energie_slider.value()
            sommeil = self.sommeil_slider.value()
            success, result = self.controller.save_checkin(humeur, energie, sommeil)
            if success:
                self.checkin_done.emit()
                QMessageBox.information(self, "Check-in saved",
                    f"Sleep: {sommeil}h\nMood: {humeur}/5\nEnergy: {energie}/5\nScore: {result.score_productivite}/100")
                streak = self.controller.get_current_streak()
                total_checkins = self.gami.get_total_checkins()
                total_sessions = self.gami.get_total_sessions()
                unlocked = self.gami.check_and_unlock_badges(streak, total_sessions, total_checkins)
                if unlocked:
                    show_badge_popups(self.window(), unlocked)
                self._build_ui()
            else:
                QMessageBox.warning(self, "Error", str(result))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", traceback.format_exc())

    def _section_title(self, text):
        c = Theme.colors()
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        return lbl

    def _make_slider(self, min_val, max_val, default):
        c = Theme.colors()
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(1)
        slider.setFixedHeight(32)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: rgba(215,192,174,0.15);
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {SAKURA};
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {SAKURA};
                height: 4px;
                border-radius: 2px;
            }}
        """)
        return slider

    def _value_label(self, text):
        c = Theme.colors()
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        lbl.setFixedWidth(50)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _slider_row(self, slider, value_label, min_text, max_text):
        c = Theme.colors()
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        row.setSpacing(12)
        min_lbl = QLabel(min_text)
        min_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        min_lbl.setFixedWidth(24)
        row.addWidget(min_lbl)
        row.addWidget(slider, stretch=1)
        max_lbl = QLabel(max_text)
        max_lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        max_lbl.setFixedWidth(24)
        row.addWidget(max_lbl)
        row.addSpacing(8)
        row.addWidget(value_label)
        return container

    def refresh(self):
        self._build_ui()

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{ color: {c['TEXT_PRIMARY']}; background-color: {c['BG']}; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton#btn_back {{
                background: transparent;
                color: {MILK_TEA};
                border: 1.5px solid rgba(215,192,174,0.15);
                border-radius: 18px;
                font-size: 13px;
                font-weight: bold;
                padding: 4px 12px;
            }}
            QPushButton#btn_back:hover {{
                border-color: {SAKURA};
                color: {SAKURA};
            }}
        """
