from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
import os
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient
from PySide6.QtWidgets import QFileDialog, QMessageBox
from controllers.checkin_controller import CheckinController
from models.database import get_session
from models.study_session import StudySession
from views.heatmap_widget import HeatmapWidget
from utils.pdf_exporter import PDFExporter
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA


class LineChart(QWidget):
    def __init__(self, series, y_max=10, parent=None):
        super().__init__(parent)
        self.series  = series
        self.y_max   = y_max
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        if not self.series:
            return
        c = Theme.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pad_left, pad_right, pad_top, pad_bottom = 36, 16, 16, 36
        chart_w = W - pad_left - pad_right
        chart_h = H - pad_top - pad_bottom

        grid_color = QColor(c['CHART_GRID'])
        grid_pen = QPen(grid_color)
        painter.setPen(grid_pen)
        steps = 4
        for i in range(steps + 1):
            y = pad_top + int(chart_h * i / steps)
            painter.drawLine(pad_left, y, pad_left + chart_w, y)
            val = self.y_max * (1 - i / steps)
            painter.setPen(QColor(c['TEXT_MUTED']))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(0, y - 7, pad_left, 14,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             str(int(val)))
            painter.setPen(grid_pen)

        first_series = next(iter(self.series.values()))
        x_labels = first_series.get("labels", [])
        n = len(x_labels)
        if n > 1:
            for i, lbl in enumerate(x_labels):
                x = pad_left + int(chart_w * i / (n - 1))
                painter.setPen(QColor(c['TEXT_MUTED']))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(x - 20, H - pad_bottom + 4, 40, 20,
                                 Qt.AlignmentFlag.AlignCenter, lbl)

        for name, data in self.series.items():
            values = data.get("values", [])
            color  = QColor(data.get("color", c['MILK_TEA']))
            n_vals = len(values)
            if n_vals < 2:
                continue
            path   = QPainterPath()
            points = []
            for i, v in enumerate(values):
                x = pad_left + int(chart_w * i / (n_vals - 1))
                y = pad_top + int(chart_h * (1 - min(v, self.y_max) / self.y_max))
                points.append(QPoint(x, y))
            path.moveTo(points[0])
            for i in range(1, len(points)):
                p0, p1 = points[i - 1], points[i]
                cx = (p0.x() + p1.x()) / 2
                path.cubicTo(cx, p0.y(), cx, p1.y(), p1.x(), p1.y())

            fill_path = QPainterPath(path)
            fill_path.lineTo(points[-1].x(), pad_top + chart_h)
            fill_path.lineTo(points[0].x(),  pad_top + chart_h)
            fill_path.closeSubpath()
            gradient = QLinearGradient(0, pad_top, 0, pad_top + chart_h)
            fc = QColor(color); fc.setAlpha(40)
            gradient.setColorAt(0, fc)
            fc2 = QColor(color); fc2.setAlpha(0)
            gradient.setColorAt(1, fc2)
            painter.fillPath(fill_path, QBrush(gradient))

            pen = QPen(color); pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(c['TEXT_PRIMARY']), 2))
            for pt in points:
                painter.drawEllipse(pt.x() - 4, pt.y() - 4, 8, 8)
        painter.end()


class BarChart(QWidget):
    def __init__(self, values=None, labels=None, color=None, parent=None):
        super().__init__(parent)
        self.values = values or []
        self.labels = labels or []
        self.color  = color or Theme.colors()['ACCENT']
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        if not self.values:
            return
        c = Theme.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pad_left, pad_right, pad_top, pad_bottom = 10, 10, 16, 28
        chart_w = W - pad_left - pad_right
        chart_h = H - pad_top - pad_bottom
        n       = len(self.values)
        y_max   = max(self.values) if max(self.values) > 0 else 1
        bar_total_w = chart_w / n
        bar_w       = bar_total_w * 0.55
        base_color  = QColor(self.color)

        for i, (val, lbl) in enumerate(zip(self.values, self.labels)):
            x     = pad_left + i * bar_total_w + (bar_total_w - bar_w) / 2
            bar_h = int(chart_h * val / y_max) if val > 0 else 2
            y     = pad_top + chart_h - bar_h
            gradient = QLinearGradient(x, y, x, y + bar_h)
            gradient.setColorAt(0, base_color)
            gradient.setColorAt(1, QColor(base_color).lighter(130))
            path = QPainterPath()
            path.addRoundedRect(x, y, bar_w, bar_h, min(4, bar_w / 2), min(4, bar_w / 2))
            painter.fillPath(path, QBrush(gradient))
            painter.setPen(QColor(c['STAT_VALUE']))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(int(x), y - 14, int(bar_w), 14, Qt.AlignmentFlag.AlignCenter, str(val))
            painter.setPen(QColor(c['TEXT_MUTED']))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(int(x) - 8, H - pad_bottom + 4, int(bar_w) + 16, 20,
                             Qt.AlignmentFlag.AlignCenter, lbl)
        painter.end()


class StatsView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user        = user
        self.on_navigate = on_navigate
        self.ctrl        = CheckinController(user.id)
        self.period      = 7
        self.setStyleSheet(self._get_style())
        self._build_ui()
        self._build_content()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.content = QWidget()
        self.content.setObjectName("content_area")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(24, 20, 24, 24)
        self.content_layout.setSpacing(16)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

    def _build_topbar(self):
        c = Theme.colors()
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("Statistics")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)
        layout.addStretch()

        self.btn_7  = self._toggle_btn("7 days",  active=(self.period == 7))
        self.btn_30 = self._toggle_btn("30 days", active=(self.period == 30))
        self.btn_7.clicked.connect(lambda: self._switch_period(7))
        self.btn_30.clicked.connect(lambda: self._switch_period(30))
        layout.addWidget(self.btn_7)
        layout.addWidget(self.btn_30)
        layout.addSpacing(8)
        btn_export = QPushButton("Exported")
        btn_export.setObjectName("toggle_inactive")
        btn_export.setFixedHeight(30)
        btn_export.setFixedWidth(120)
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_analytics)
        layout.addWidget(btn_export)
        return topbar

    def _toggle_btn(self, label, active=False):
        btn = QPushButton(label)
        btn.setFixedHeight(30)
        btn.setFixedWidth(80)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("toggle_active" if active else "toggle_inactive")
        return btn

    def _switch_period(self, days):
        self.period = days
        self.btn_7.setObjectName("toggle_active"   if days == 7  else "toggle_inactive")
        self.btn_30.setObjectName("toggle_active"  if days == 30 else "toggle_inactive")
        self.btn_7.setStyle(self.btn_7.style())
        self.btn_30.setStyle(self.btn_30.style())
        self.refresh()

    def refresh(self):
        cl = self.content_layout
        while cl.count():
            item = cl.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._build_content()
        self.setStyleSheet(self._get_style())

    def _build_content(self):
        c   = Theme.colors()
        logs = self.ctrl.get_last_7_days() if self.period == 7 else self.ctrl.get_last_30_days()

        if logs:
            scores = [l.score_productivite or 0 for l in logs if l.score_productivite is not None]
            avg_score  = round(sum(scores) / len(scores)) if scores else 0
            avg_sleep  = round(sum(l.sommeil  for l in logs) / len(logs), 1)
            avg_mood   = round(sum(l.humeur   for l in logs) / len(logs), 1)
            avg_energy = round(sum(l.energie  for l in logs) / len(logs), 1)
            streak     = self.ctrl.get_current_streak()
        else:
            avg_score = avg_sleep = avg_mood = avg_energy = streak = 0

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        for label, value, sub in [
            ("Avg Score", str(avg_score), f"out of 100"),
            ("Avg Sleep", f"{avg_sleep}h", f"last {self.period} days"),
            ("Avg Mood", f"{avg_mood}/5", f"last {self.period} days"),
            ("Streak", str(streak), "days in a row"),
        ]:
            stats_row.addWidget(self._stat_card(label, value, sub, c))
        self.content_layout.addLayout(stats_row)

        if not logs:
            empty = QLabel("No data yet - complete your first check-in to see stats here.")
            empty.setObjectName("stats_empty_label")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {c['MILK_TEA']}; font-size: 14px; padding: 40px;")
            self.content_layout.addWidget(empty)
            return

        all_logs = self.ctrl.get_last_30_days()
        checkin_dates = {l.date for l in all_logs}
        heatmap = HeatmapWidget(checkin_dates, days=30)
        self.content_layout.addWidget(self._chart_card("Check-in Heatmap \xb7 30 derniers jours", heatmap, c))

        today       = date.today()
        date_map    = {l.date: l for l in logs}
        dates_range = [today - timedelta(days=i) for i in range(self.period - 1, -1, -1)]
        score_vals  = [date_map[d].score_productivite or 0 if d in date_map else 0 for d in dates_range]
        sleep_vals  = [date_map[d].sommeil  if d in date_map else 0 for d in dates_range]
        mood_vals   = [date_map[d].humeur   if d in date_map else 0 for d in dates_range]
        energy_vals = [date_map[d].energie  if d in date_map else 0 for d in dates_range]
        step        = max(1, self.period // 7)
        x_labels    = [d.strftime("%d/%m") if i % step == 0 else "" for i, d in enumerate(dates_range)]

        score_chart = LineChart({"Score": {"color": c['ACCENT'], "values": score_vals, "labels": x_labels}}, y_max=100)
        self.content_layout.addWidget(self._chart_card("Productivity Score", score_chart, c))

        sleep_chart = LineChart({
            "Sleep (h)": {"color": c['MILK_TEA'], "values": sleep_vals, "labels": x_labels},
            "Energy /5": {"color": c['ACCENT'],   "values": energy_vals, "labels": x_labels},
        }, y_max=12)
        self.content_layout.addWidget(self._chart_card(
            "Sleep & Energy", sleep_chart, c,
            legend=[(c['MILK_TEA'], "Sleep (h)"), (c['ACCENT'], "Energy /5")]
        ))

        mood_chart = LineChart({"Mood": {"color": c['MILK_TEA'], "values": mood_vals, "labels": x_labels}}, y_max=5)
        self.content_layout.addWidget(self._chart_card("Mood", mood_chart, c))

        session_data = self._get_session_data(dates_range, step)
        if any(v > 0 for v in session_data["values"]):
            bar_chart = BarChart(session_data["values"], session_data["labels"], c['ACCENT'])
            self.content_layout.addWidget(self._chart_card("Pomodoro Sessions", bar_chart, c))

    def _get_session_data(self, dates_range, step):
        session = get_session()
        try:
            sessions = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user.id,
                StudySession.statut == "complete"
            ).all()
            count_map = {}
            for s in sessions:
                d = s.date_heure_debut.date()
                count_map[d] = count_map.get(d, 0) + 1
            return {
                "values": [count_map.get(d, 0) for d in dates_range],
                "labels": [d.strftime("%d/%m") if i % step == 0 else "" for i, d in enumerate(dates_range)]
            }
        finally:
            session.close()

    def _stat_card(self, label, value, sub, c):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setFixedHeight(100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(3)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {c['STAT_LABEL']}; font-size: 10px; letter-spacing: 0.5px; background: transparent;")
        layout.addWidget(lbl)
        val = QLabel(str(value))
        val.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {c['STAT_VALUE']}; background: transparent;")
        layout.addWidget(val)
        if sub:
            s = QLabel(sub)
            s.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
            layout.addWidget(s)
        return card

    def _chart_card(self, title, chart_widget, c, legend=None):
        card = QFrame()
        card.setObjectName("chart_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        t.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        header.addWidget(t)
        header.addStretch()
        if legend:
            for color, name in legend:
                dot = QLabel("\u25cf")
                dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")
                header.addWidget(dot)
                lbl = QLabel(name)
                lbl.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 10px; background: transparent;")
                header.addWidget(lbl)
                header.addSpacing(8)
        layout.addLayout(header)
        layout.addWidget(chart_widget)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return card

    def _export_analytics(self):
        logs = self.ctrl.get_last_7_days() if self.period == 7 else self.ctrl.get_last_30_days()
        if not logs:
            QMessageBox.information(self, "Aucune donn\xe9e", "Fais d'abord des check-ins.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exported",
            os.path.join(os.path.expanduser("~/Desktop"), f"digital_twin_analytics_{date.today()}.pdf"),
            "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return
        try:
            scores = [l.score_productivite or 0 for l in logs if l.score_productivite is not None]
            avg_score = round(sum(scores) / len(scores)) if scores else 0
            avg_sleep = round(sum(l.sommeil for l in logs) / len(logs), 1)
            avg_mood  = round(sum(l.humeur for l in logs) / len(logs), 1)
            avg_energy = round(sum(l.energie for l in logs) / len(logs), 1)
            streak = self.ctrl.get_current_streak()
            total_checkins = len(logs)
            today = date.today()
            from datetime import timedelta
            dates_range = [today - timedelta(days=i) for i in range(self.period - 1, -1, -1)]
            date_map = {l.date: l for l in logs}
            score_series = []
            for d in dates_range:
                log = date_map.get(d)
                if log:
                    score_series.append({
                        "date": str(d),
                        "score": str(log.score_productivite or "0"),
                        "sleep": str(log.sommeil),
                        "mood": str(log.humeur),
                        "energy": str(log.energie),
                    })
            session = get_session()
            try:
                total_sessions = session.query(StudySession).filter(
                    StudySession.utilisateur_id == self.user.id,
                    StudySession.statut == "complete"
                ).count()
            finally:
                session.close()
            PDFExporter.export_analytics(
                path, user_name=self.user.nom,
                score_series=score_series,
                avg_score=avg_score, avg_sleep=avg_sleep,
                avg_mood=avg_mood, avg_energy=avg_energy,
                streak=streak, total_checkins=total_checkins,
                total_sessions=total_sessions, period_days=self.period,
            )
            QMessageBox.information(self, "Exported", f"Analytical report saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: Segoe UI;
            }}
            QFrame#topbar {{
                background-color: {c['BG']};
                border-bottom: 0.5px solid {c['DIVIDER']};
            }}
            QWidget#content_area {{
                background-color: {c['BG']};
            }}
            QFrame#chart_card {{
                background: {c['CARD_BG']};
                border-radius: 12px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
            QFrame#stat_card {{
                background: {c['CARD_BG']};
                border-radius: 10px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
            QPushButton#toggle_active {{
                background: {c['BG']};
                color: {c['TEXT_PRIMARY']};
                border: none;
                border-radius: 15px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton#toggle_inactive {{
                background: transparent;
                color: {c['MILK_TEA']};
                border: 1px solid {c['MILK_TEA']};
                border-radius: 15px;
                font-size: 11px;
            }}
            QPushButton#toggle_inactive:hover {{
                border-color: {c['ACCENT']};
                color: {c['TEXT_PRIMARY']};
            }}
        """
