from datetime import date, timedelta
from PySide6.QtWidgets import QWidget, QSizePolicy, QToolTip
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QCursor

from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, ALOEWOOD, MILK_TEA


class HeatmapWidget(QWidget):
    def __init__(self, checkin_dates: set, days=30, parent=None):
        super().__init__(parent)
        self.checkin_dates = checkin_dates
        self.days = days
        self.setMinimumHeight(110)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self._cells = []

    def mouseMoveEvent(self, event):
        for rect, d, has_ci in self._cells:
            if rect.contains(event.pos()):
                tip = f"{'Check-in' if has_ci else 'No check-in'}  {d.strftime('%A %d %B %Y')}"
                QToolTip.showText(QCursor.pos(), tip, self)
                return

    def paintEvent(self, event):
        c = Theme.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        today = date.today()
        cell_size = 16
        cell_gap = 4
        step = cell_size + cell_gap
        pad_left = 28
        pad_top = 22

        self._cells = []

        start = today - timedelta(days=self.days - 1)
        start = start - timedelta(days=start.weekday())

        all_dates = []
        d = start
        while d <= today:
            all_dates.append(d)
            d += timedelta(days=1)

        num_weeks = (len(all_dates) + 6) // 7

        day_labels = ["M", "", "W", "", "F", "", "S"]
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(MILK_TEA))
        for row, lbl in enumerate(day_labels):
            y = pad_top + row * step
            painter.drawText(0, y, pad_left - 4, cell_size,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, lbl)

        shown_months = set()
        for week_idx in range(num_weeks):
            for dow in range(7):
                idx = week_idx * 7 + dow
                if idx >= len(all_dates):
                    continue
                d = all_dates[idx]
                if d > today:
                    continue

                x = pad_left + week_idx * step
                y = pad_top + dow * step

                in_range = d >= (today - timedelta(days=self.days - 1))
                has_ci = d in self.checkin_dates

                if not in_range:
                    bg = QColor(MILK_TEA)
                    bg.setAlpha(20)
                    color = bg
                elif has_ci:
                    color = QColor(SAKURA)
                elif d == today:
                    color = QColor(ALOEWOOD)
                else:
                    bg = QColor(MILK_TEA)
                    bg.setAlpha(40)
                    color = bg

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                rect = QRect(x, y, cell_size, cell_size)
                painter.drawRoundedRect(rect, 3, 3)

                if in_range:
                    self._cells.append((rect, d, has_ci))

                if d.day <= 7 and d.month not in shown_months and in_range:
                    shown_months.add(d.month)
                    months_en = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    painter.setPen(QColor(MILK_TEA))
                    painter.setFont(QFont("Segoe UI", 8))
                    painter.drawText(x, 0, 40, 18,
                                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                     months_en[d.month])
                    painter.setFont(QFont("Segoe UI", 8))

        legend_x = pad_left
        legend_y = pad_top + 7 * step + 6
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(MILK_TEA).lighter(145))
        painter.drawText(legend_x, legend_y, 36, 14, Qt.AlignmentFlag.AlignLeft, "Less")
        for i, alpha in enumerate([30, 80, 140, 200, 255]):
            col = QColor(SAKURA)
            col.setAlpha(alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(col)
            lx = legend_x + 40 + i * (cell_size - 1)
            painter.drawRoundedRect(lx, legend_y + 2, cell_size - 4, cell_size - 4, 2, 2)
        painter.setPen(QColor(MILK_TEA).lighter(145))
        painter.drawText(legend_x + 40 + 5 * (cell_size - 1) + 4, legend_y, 36, 14,
                         Qt.AlignmentFlag.AlignLeft, "More")

        painter.end()
