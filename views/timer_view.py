from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from controllers.timer_controller import TimerController
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA


class RingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._is_break = False
        self.setMinimumSize(220, 220)
        self.setMaximumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_progress(self, value, is_break=False):
        self._progress = value
        self._is_break = is_break
        self.update()

    def paintEvent(self, event):
        c = Theme.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        side = min(w, h)
        cx, cy = w // 2, h // 2
        outer_r = side // 2 - 12
        rect = QRect(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        bg_color = QColor(MILK_TEA)
        bg_color.setAlpha(30)
        fg_color = QColor(SAKURA) if not self._is_break else QColor(MILK_TEA)
        pen_bg = QPen(bg_color, 12)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)
        if self._progress > 0:
            pen_fg = QPen(fg_color, 12)
            pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_fg)
            span = int(360 * 16 * self._progress)
            painter.drawArc(rect, 90 * 16, -span)
        painter.end()


class TimerView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.controller = TimerController(user.id)
        self.qtimer = QTimer()
        self.qtimer.timeout.connect(self._tick)
        self.qtimer.setInterval(1000)
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        c = Theme.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        back = QPushButton("Back to Dashboard")
        back.setObjectName("btn_back")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(lambda: self.on_navigate("dashboard"))
        tb_layout.addWidget(back)
        tb_layout.addStretch()
        title = QLabel("Pomodoro Timer")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        tb_layout.addWidget(title)
        root.addWidget(topbar)

        center = QWidget()
        center.setObjectName("center_area")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)  # 40, 32, 40, 32)
        cl.setSpacing(0)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mode_label = QLabel("Work")
        self.mode_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setStyleSheet(f"color: {c['TEXT_MUTED']}; background: transparent;")
        cl.addWidget(self.mode_label)
        cl.addSpacing(8)

        self.ring = RingWidget()
        cl.addWidget(self.ring, alignment=Qt.AlignmentFlag.AlignCenter)

        self.time_display = QLabel("25:00")
        self.time_display.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_display.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        cl.addWidget(self.time_display)
        cl.addSpacing(4)

        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        cl.addWidget(self.status_label)
        cl.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("timer_btn_primary")
        self.btn_start.setFixedHeight(48)
        self.btn_start.setFixedWidth(160)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._handle_start)
        btn_row.addWidget(self.btn_start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("timer_btn_secondary")
        self.btn_pause.setFixedHeight(48)
        self.btn_pause.setFixedWidth(120)
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.clicked.connect(self._handle_pause)
        self.btn_pause.setEnabled(False)
        btn_row.addWidget(self.btn_pause)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setObjectName("timer_btn_secondary")
        self.btn_reset.setFixedHeight(48)
        self.btn_reset.setFixedWidth(120)
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self._handle_reset)
        btn_row.addWidget(self.btn_reset)

        cl.addLayout(btn_row)
        cl.addSpacing(24)

        self.count_label = QLabel("Sessions completed today: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        cl.addWidget(self.count_label)

        root.addWidget(center)
        self._update_display()

    def _handle_start(self):
        if self.controller.is_running:
            return
        self.controller.start()
        if not self.controller.is_break:
            self.controller.send_notification_start()
        self.qtimer.start()
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.status_label.setText("In progress...")

    def _handle_pause(self):
        self.controller.pause()
        self.qtimer.stop()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Paused")

    def _handle_reset(self):
        self.qtimer.stop()
        self.controller.reset()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Ready to start")
        self._update_display()

    def _tick(self):
        result = self.controller.tick()
        self._update_display()
        if result == "work_done":
            self.qtimer.stop()
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.status_label.setText("Break time!")
            self._update_count()
        elif result == "break_done":
            self.qtimer.stop()
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.status_label.setText("Ready to resume")
            self._update_count()

    def _update_display(self):
        self.time_display.setText(self.controller.get_time_string())
        progress = self.controller.get_progress()
        self.ring.set_progress(progress, is_break=self.controller.is_break)
        self.mode_label.setText("Break" if self.controller.is_break else "Work")
        if not self.controller.is_running:
            self.btn_pause.setEnabled(False)
        self._update_count()

    def _update_count(self):
        count = self.controller.get_today_sessions()
        self.count_label.setText(f"Sessions completed today: {count}")

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QFrame#topbar {{
                background-color: {c['BG']};
                border-bottom: 0.5px solid {c['TOPBAR_BORDER']};
            }}
            QWidget#center_area {{
                background-color: {c['BG']};
            }}
            QPushButton#btn_back {{
                background: transparent;
                color: {c['TEXT_MUTED']};
                border: none;
                font-size: 12px;
            }}
            QPushButton#btn_back:hover {{ color: {SAKURA}; }}
            QPushButton#timer_btn_primary {{
                background-color: {SAKURA};
                color: {DARK_CHOCOLATE};
                border: none;
                border-radius: 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#timer_btn_primary:hover {{
                background-color: {c['ACCENT_HOVER']};
            }}
            QPushButton#timer_btn_primary:disabled {{
                background-color: rgba(248,215,218,0.2);
                color: rgba(59,47,47,0.4);
            }}
            QPushButton#timer_btn_secondary {{
                background: transparent;
                color: {c['TEXT_SECONDARY']};
                border: 1.5px solid rgba(215,192,174,0.2);
                border-radius: 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#timer_btn_secondary:hover {{
                border-color: {SAKURA};
                color: {SAKURA};
            }}
            QPushButton#timer_btn_secondary:disabled {{
                color: rgba(255,255,255,0.2);
                border-color: rgba(215,192,174,0.1);
            }}
        """
