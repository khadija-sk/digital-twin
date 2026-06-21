from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QApplication
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from services.model_manager import ModelManager
from utils.theme import Theme, SAKURA, BORDER_RADIUS_SM


class ModelSelectorWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._animating = False
        self._manager = ModelManager.get_instance()

        self.setObjectName("modelSelector")
        self.setFixedWidth(220)
        self._collapsed_h = 32

        self._build_ui()
        self._refresh_button()

    def _build_ui(self):
        self.setStyleSheet(self._base_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(0)

        self._btn = QPushButton()
        self._btn.setObjectName("modelToggleBtn")
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setFixedHeight(self._collapsed_h)
        self._btn.clicked.connect(self._toggle)

        inner_layout = QHBoxLayout(self._btn)
        inner_layout.setContentsMargins(0, 0, 0, 0)  # 10, 0, 10, 0)
        self._btn_label = QLabel("Model")
        self._btn_label.setObjectName("modelBtnText")
        inner_layout.addWidget(self._btn_label)
        inner_layout.addStretch()
        self._btn_status = QLabel()
        self._btn_status.setObjectName("modelStatusDot")
        self._btn_status.setFixedSize(8, 8)
        inner_layout.addWidget(self._btn_status)
        inner_layout.addSpacing(4)
        arrow_lbl = QLabel(">")
        arrow_lbl.setObjectName("modelArrow")
        inner_layout.addWidget(arrow_lbl)

        layout.addWidget(self._btn)

        self._panel = QFrame()
        self._panel.setObjectName("modelPanel")
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)  # 8, 8, 8, 8)
        panel_layout.setSpacing(4)

        panel_title = QLabel("Available Models")
        panel_title.setObjectName("modelPanelTitle")
        panel_layout.addWidget(panel_title)

        self._model_widgets = []
        models = self._manager.get_models() if self._manager else []
        active_name = self._manager.get_active_model() if self._manager else ""
        for model in models:
            mw = self._model_row(model, active_name)
            self._model_widgets.append(mw)
            panel_layout.addWidget(mw)

        panel_layout.addStretch()
        self._panel.setVisible(False)
        self._panel.setFixedHeight(min(len(models) * 36 + 40, 240))
        layout.addWidget(self._panel)

        self.setFixedHeight(self._collapsed_h)
        self._anim = QPropertyAnimation(self, b"maximumHeight")

    def _model_row(self, model, active_name):
        c = Theme.colors()
        row = QFrame()
        row.setObjectName("modelRow")
        row.setFixedHeight(32)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)  # 8, 0, 8, 0)
        rl.setSpacing(6)

        is_active = model.name == active_name
        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(
            f"background: {SAKURA}; border-radius: 3px;" if is_active
            else f"background: {c['TEXT_MUTED']}; border-radius: 3px;"
        )
        rl.addWidget(dot)

        name = QLabel(model.display_name or model.name)
        name.setStyleSheet(
            f"color: {c['TEXT_PRIMARY']}; font-size: 11px; background: transparent;"
            if is_active
            else f"color: {c['TEXT_SECONDARY']}; font-size: 11px; background: transparent;"
        )
        rl.addWidget(name)
        rl.addStretch()

        row.mousePressEvent = lambda e, m=model: self._select_model(m)
        return row

    def _select_model(self, model):
        if self._manager:
            self._manager.set_active_model(model.name)
        self._refresh_button()
        self._toggle()

    def _refresh_button(self):
        c = Theme.colors()
        active_name = self._manager.get_active_model() if self._manager else ""
        models = self._manager.get_models() if self._manager else []
        active = None
        for m in models:
            if m.name == active_name:
                active = m
                break
        if active:
            self._btn_label.setText(active.display_name or active.name)
        else:
            self._btn_label.setText("No model")
        self._update_status_dot()

    def _update_status_dot(self):
        c = Theme.colors()
        active_name = self._manager.get_active_model() if self._manager else ""
        models = self._manager.get_models() if self._manager else []
        active = None
        for m in models:
            if m.name == active_name:
                active = m
                break
        if active and active.status == "Online":
            self._btn_status.setStyleSheet(f"background: {SAKURA}; border-radius: 4px;")
        else:
            self._btn_status.setStyleSheet(f"background: {c['TEXT_MUTED']}; border-radius: 4px;")

    def _toggle(self):
        if self._animating:
            return
        self._expanded = not self._expanded
        self._animating = True

        start_h = self._collapsed_h
        end_h = start_h + self._panel.height() if self._expanded else start_h

        self._anim.setDuration(200)
        self._anim.setStartValue(start_h)
        self._anim.setEndValue(end_h)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self._on_anim_done)

        if self._expanded:
            self._panel.setVisible(True)

        self._anim.start()

        arrow = self.findChild(QLabel, "modelArrow")
        if arrow:
            arrow.setText("v" if self._expanded else ">")

    def _on_anim_done(self):
        self._animating = False
        if not self._expanded:
            self._panel.setVisible(False)
        self.updateGeometry()

    def _base_style(self):
        c = Theme.colors()
        return f"""
            #modelSelector {{
                background: {c['CARD_BG']};
                border: 0.5px solid {c['CARD_BORDER']};
                border-radius: {BORDER_RADIUS_SM}px;
            }}
            #modelToggleBtn {{
                background: transparent;
                border: none;
                border-radius: {BORDER_RADIUS_SM}px;
            }}
            #modelToggleBtn:hover {{
                background: {c['CARD_HOVER']};
            }}
            #modelBtnText {{
                color: {c['TEXT_PRIMARY']};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }}
            #modelStatusDot {{
                background: {c['TEXT_MUTED']};
                border-radius: 4px;
            }}
            #modelArrow {{
                color: {c['TEXT_MUTED']};
                font-size: 10px;
                background: transparent;
            }}
            #modelPanel {{
                background: {c['BG']};
                border-top: 0.5px solid {c['DIVIDER']};
                border-radius: 0 0 {BORDER_RADIUS_SM}px {BORDER_RADIUS_SM}px;
            }}
            #modelPanelTitle {{
                color: {c['TEXT_MUTED']};
                font-size: 9px;
                letter-spacing: 0.8px;
                padding: 4px 4px 8px;
                background: transparent;
            }}
            #modelRow {{
                background: transparent;
                border-radius: 4px;
            }}
            #modelRow:hover {{
                background: {c['CARD_HOVER']};
            }}
        """
