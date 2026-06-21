from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ia.routine_suggester import RoutineSuggester
from utils.theme import Theme, SAKURA, MILK_TEA


class RoutineView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.suggester = RoutineSuggester(user.id)
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        summary = self.suggester.get_summary()
        summary_card = QFrame()
        summary_card.setObjectName("summary_card")
        sl = QHBoxLayout(summary_card)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(10)
        spark = QLabel("✨")
        spark.setStyleSheet("font-size: 18px; background: transparent;")
        sl.addWidget(spark)
        sum_lbl = QLabel(summary)
        sum_lbl.setWordWrap(True)
        sum_lbl.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; font-size: 13px; background: transparent;")
        sl.addWidget(sum_lbl, stretch=1)
        cl.addWidget(summary_card)

        routine = self.suggester.get_routine()
        for i, block in enumerate(routine):
            cl.addWidget(self._build_block(block, i, last=(i == len(routine) - 1)))

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _build_block(self, block, index, last=False):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        time_lbl = QLabel(block["time"])
        time_lbl.setFixedWidth(52)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_lbl.setStyleSheet(f"color: {MILK_TEA}; font-size: 12px; font-weight: bold; background: transparent; padding-top: 6px;")
        layout.addWidget(time_lbl)

        dot_col = QWidget()
        dot_col.setFixedWidth(20)
        dot_col.setStyleSheet("background: transparent;")
        dl = QVBoxLayout(dot_col)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(0)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: {SAKURA}; border-radius: 6px;")
        dl.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)

        if not last:
            line = QFrame()
            line.setFixedWidth(2)
            line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            line.setStyleSheet(f"background: rgba(215,192,174,0.2);")
            dl.addWidget(line, stretch=1, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(dot_col)

        card = QFrame()
        card.setObjectName("block_card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(4)

        top_row = QHBoxLayout()
        act_lbl = QLabel(block["activity"])
        act_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        act_lbl.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; background: transparent;")
        top_row.addWidget(act_lbl)
        top_row.addStretch()

        dur_lbl = QLabel(block["duration"])
        dur_lbl.setStyleSheet(f"color: {MILK_TEA}; font-size: 11px; background: rgba(215,192,174,0.08); border-radius: 8px; padding: 2px 8px;")
        top_row.addWidget(dur_lbl)
        card_layout.addLayout(top_row)

        reason_lbl = QLabel(block["reason"])
        reason_lbl.setWordWrap(True)
        reason_lbl.setStyleSheet(f"color: {Theme.get('TEXT_SECONDARY')}; font-size: 12px; background: transparent;")
        card_layout.addWidget(reason_lbl)

        layout.addWidget(card, stretch=1)
        return row

    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Ma Routine ✨")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')};")
        layout.addWidget(title)
        layout.addStretch()
        return bar

    def refresh(self):
        pass

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{ color: {c["TEXT_PRIMARY"]}; background-color: {c["BG"]}; font-family: Segoe UI; }}
            QFrame#topbar {{ background-color: {c["BG"]}; border-bottom: 0.5px solid {c["TOPBAR_BORDER"]}; }}
            QWidget#content_area {{ background-color: {c["BG"]}; }}
            QFrame#summary_card {{ background: rgba(248,215,218,0.12); border-radius: 12px; border: 0.5px solid {c["CARD_BORDER"]}; }}
            QFrame#block_card {{ background: {c["CARD_BG"]}; border-radius: 12px; border: 0.5px solid {c["CARD_BORDER"]}; }}
        """
