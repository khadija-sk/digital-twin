import math
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QPointF
from PySide6.QtGui import (
    QFont, QPainter, QColor, QPen, QBrush, QPainterPath, QFontMetrics,
)
from services.analytics_service import AnalyticsService
from utils.theme import Theme


class AnalyticsWorker(QThread):
    result_ready = Signal(dict)

    def __init__(self, service):
        super().__init__()
        self.service = service

    def run(self):
        try:
            data = self.service.full_analysis()
            self.result_ready.emit(data)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Analytics error: {e}")
            self.result_ready.emit({})


class RadarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._data = {}
        self._labels = []

    def set_data(self, prod: dict, mood: dict, learning: dict, habits: dict):
        self._data = {
            "Productivité": min(prod.get("avg_score", 0) / 100, 1.0),
            "Humeur": min((mood.get("avg_mood", 0) or 0) / 5, 1.0),
            "Énergie": min((mood.get("avg_energy", 0) or 0) / 5, 1.0),
            "Sommeil": min((mood.get("avg_sleep", 0) or 0) / 10, 1.0),
            "Consistance": min(prod.get("consistency", 0) / 100, 1.0),
            "Sessions": min(learning.get("total_sessions", 0) / 20, 1.0),
        }
        self._labels = list(self._data.keys())
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = Theme.colors()
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 50
        if radius < 30:
            return

        n = len(self._data)
        if n < 3:
            return

        self._draw_rings(painter, cx, cy, radius, n, c)
        self._draw_axes(painter, cx, cy, radius, n, c)
        self._draw_data(painter, cx, cy, radius, n, c)
        self._draw_labels(painter, cx, cy, radius, n, c)

    def _point(self, cx, cy, radius, angle_deg):
        rad = math.radians(angle_deg - 90)
        return QPointF(cx + radius * math.cos(rad), cy + radius * math.sin(rad))

    def _draw_rings(self, painter, cx, cy, radius, n, c):
        pen = QPen(QColor(c.get("TEXT_MUTED", "#555")), 1)
        pen.setStyle(Qt.PenStyle.DotLine)
        for level in [0.25, 0.5, 0.75, 1.0]:
            r = radius * level
            path = QPainterPath()
            first = True
            for i in range(n):
                angle = 360.0 / n * i
                pt = self._point(cx, cy, r, angle)
                if first:
                    path.moveTo(pt)
                    first = False
                else:
                    path.lineTo(pt)
            path.closeSubpath()
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def _draw_axes(self, painter, cx, cy, radius, n, c):
        pen = QPen(QColor(c.get("TEXT_MUTED", "#555")), 1)
        painter.setPen(pen)
        for i in range(n):
            angle = 360.0 / n * i
            pt = self._point(cx, cy, radius, angle)
            painter.drawLine(QPointF(cx, cy), pt)

    def _draw_data(self, painter, cx, cy, radius, n, c):
        values = list(self._data.values())
        path = QPainterPath()
        first = True
        for i in range(n):
            val = max(0.0, min(values[i], 1.0))
            angle = 360.0 / n * i
            pt = self._point(cx, cy, radius * val, angle)
            if first:
                path.moveTo(pt)
                first = False
            else:
                path.lineTo(pt)
        path.closeSubpath()

        accent = QColor(c.get("ACCENT", "#E8A5B5"))
        fill = QColor(accent)
        fill.setAlpha(50)
        painter.setBrush(QBrush(fill))
        pen = QPen(accent, 2)
        painter.setPen(pen)
        painter.drawPath(path)

        for i in range(n):
            val = max(0.0, min(values[i], 1.0))
            angle = 360.0 / n * i
            pt = self._point(cx, cy, radius * val, angle)
            painter.setBrush(QBrush(accent))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pt, 4, 4)

    def _draw_labels(self, painter, cx, cy, radius, n, c):
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text_color = QColor(c.get("TEXT_PRIMARY", "#FFF"))
        painter.setPen(text_color)

        for i in range(n):
            label = self._labels[i]
            angle = 360.0 / n * i
            pt = self._point(cx, cy, radius + 30, angle)
            tw = metrics.horizontalAdvance(label)
            th = metrics.height()

            if angle == 0:
                x = pt.x() - tw / 2
                y = pt.y() + th / 4
            elif angle < 90:
                x = pt.x()
                y = pt.y() + th / 4
            elif angle == 90:
                x = pt.x() + 4
                y = pt.y() + th / 4
            elif angle < 180:
                x = pt.x() + 4
                y = pt.y()
            elif angle == 180:
                x = pt.x() - tw / 2
                y = pt.y()
            elif angle < 270:
                x = pt.x() - tw - 4
                y = pt.y()
            elif angle == 270:
                x = pt.x() - tw - 4
                y = pt.y() + th / 4
            else:
                x = pt.x() - tw
                y = pt.y() + th / 4

            painter.drawText(int(x), int(y), label)


class ChartCard(QFrame):
    def __init__(self, title, chart_view, height=260):
        super().__init__()
        self.setObjectName("chart_card")
        c = Theme.colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(12)

        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)

        chart_view.setStyleSheet("background: transparent; border: none;")
        chart_view.setMinimumHeight(height)
        chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(chart_view, stretch=1)


class AnalyticsView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user = user
        self.on_navigate = on_navigate
        self.service = AnalyticsService(user.id)
        self._layout = None
        self._zombie_workers = []
        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        c = Theme.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)
        title = QLabel("Analytics")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        tl.addWidget(title)
        tl.addStretch()
        root.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("analytics_content")
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)  # 32, 20, 32, 20)
        scroll_layout.setSpacing(16)

        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)
        scroll_layout.addLayout(self.stats_grid)

        self.radar_card = QFrame()
        self.radar_card.setObjectName("chart_card")
        rl = QVBoxLayout(self.radar_card)
        rl.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        rl.setSpacing(12)
        radar_header = QLabel("Vue d'ensemble")
        radar_header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        radar_header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        rl.addWidget(radar_header)
        self.radar = RadarChart()
        rl.addWidget(self.radar, stretch=1)
        scroll_layout.addWidget(self.radar_card)

        self.recs_container = QVBoxLayout()
        scroll_layout.addLayout(self.recs_container)
        scroll_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _load_data(self):
        if hasattr(self, '_worker') and self._worker is not None:
            if self._worker.isRunning():
                try:
                    self._worker.result_ready.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self._zombie_workers.append(self._worker)
                self._worker.finished.connect(
                    lambda w=self._worker: self._zombie_workers.remove(w)
                )
            else:
                self._worker.deleteLater()
        self._worker = AnalyticsWorker(self.service)
        self._worker.result_ready.connect(self._on_data)
        self._worker.start()

    def _clear_grid(self, grid):
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_data(self, data):
        if not data:
            return

        prod = data.get("productivity", {})
        mood = data.get("mood", {})
        learning = data.get("learning", {})
        topics = data.get("topics", {})
        habits = data.get("habits", {})
        recs = data.get("recommendations", [])

        self._clear_grid(self.stats_grid)
        self._clear_layout(self.recs_container)

        c = Theme.colors()
        accent = c.get("ACCENT", "#E8A5B5")

        try:
            self._build_stat_cards(prod, mood, learning, habits, c, accent)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Stat cards error: {e}")

        try:
            self.radar.set_data(prod, mood, learning, habits)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Radar error: {e}")

        try:
            self._build_recommendations(recs, c)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Recs error: {e}")

    def _build_stat_cards(self, prod, mood, learning, habits, c, accent):
        stats = [
            ("Score Moyen", f"{prod.get('avg_score', '—')}/100", f"Meilleur: {prod.get('best_score', '—')}"),
            ("Consistance", f"{prod.get('consistency', 0)}%", f"{prod.get('total_logs', 0)}/30 jours"),
            ("Sommeil", f"{mood.get('avg_sleep', '—')}h", f"Humeur: {mood.get('avg_mood', '—')}/5"),
            ("Sessions", str(learning.get('total_sessions', 0)), f"{learning.get('total_hours', 0)}h"),
        ]
        for i, (title, value, sub) in enumerate(stats):
            card = QFrame()
            card.setObjectName("stat_card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
            layout.setSpacing(6)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
            layout.addWidget(lbl_title)
            lbl_val = QLabel(value)
            lbl_val.setStyleSheet(f"color: {accent}; font-size: 28px; font-weight: bold; background: transparent;")
            layout.addWidget(lbl_val)
            lbl_sub = QLabel(sub)
            lbl_sub.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 11px; background: transparent;")
            layout.addWidget(lbl_sub)
            layout.addStretch()
            self.stats_grid.addWidget(card, i // 2, i % 2)

    def _build_recommendations(self, recs, c):
        if not recs:
            return
        card = QFrame()
        card.setObjectName("recs_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 20, 16, 20, 16)
        layout.setSpacing(8)
        header = QLabel("Recommandations")
        header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(header)
        for r in recs:
            lbl = QLabel(f"• {r.get('message', '')}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
            layout.addWidget(lbl)
        self.recs_container.addWidget(card)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        self.setStyleSheet(self._get_style())
        self._load_data()

    def _get_style(self):
        c = Theme.colors()
        accent = c.get("ACCENT", "#E8A5B5")
        card_bg = c.get("CARD_BG", "#2F2723")
        border = c.get("CARD_BORDER", "rgba(207,198,190,0.10)")
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: Segoe UI;
            }}
            QFrame#topbar {{
                background: {c['BG']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QWidget#analytics_content {{ background: transparent; }}
            QFrame#stat_card {{
                background: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QFrame#chart_card {{
                background: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QFrame#recs_card {{
                background: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
        """
