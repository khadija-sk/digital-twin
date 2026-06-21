import logging
from datetime import date, datetime, timedelta
from calendar import monthrange, day_name
from PySide6.QtCore import Qt, QThread, Signal, QRect
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QGridLayout, QScrollArea,
    QInputDialog, QMessageBox, QDialog, QLineEdit,
)
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from utils.theme import Theme


class CalendarLoader(QThread):
    data_ready = Signal(dict)

    def __init__(self, user_id: int, month: int, year: int):
        super().__init__()
        self.user_id = user_id
        self.month = month
        self.year = year

    def run(self):
        try:
            from services.unified_calendar_service import UnifiedCalendarService
            svc = UnifiedCalendarService(self.user_id)
            start = date(self.year, self.month, 1)
            last_day = monthrange(self.year, self.month)[1]
            end = date(self.year, self.month, last_day)
            data = svc.get_grouped_events(start_date=start, end_date=end)
            self.data_ready.emit(data)
        except Exception as e:
            logging.error("CalendarLoader error", exc_info=True)
            self.data_ready.emit({})


class DayCell(QFrame):
    def __init__(self, day: int, date_obj: date, is_today: bool, is_current_month: bool,
                 events: list, parent=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.events = events
        self._selected = False
        self.setFixedSize(100, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        c = Theme.colors()
        bg = c["CARD_BG"] if is_current_month else c["BG"]
        border = c["SAKURA"] if is_today else c["CARD_BORDER"]
        txt = c["TEXT_PRIMARY"] if is_current_month else c["MILK_TEA"]

        self.setStyleSheet(f"""
            DayCell {{
                background: {bg}; border: 1.5px solid {border};
                border-radius: 6px;
            }}
            DayCell:hover {{
                border-color: {c["SAKURA"]};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 6, 4, 6, 4)
        layout.setSpacing(2)

        day_lbl = QLabel(str(day))
        day_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {txt}; background: transparent;")
        layout.addWidget(day_lbl)

        if events:
            icons = "".join(e.get("icon", "📌") for e in events[:4])
            if len(events) > 4:
                icons += f" +{len(events) - 4}"
            icons_lbl = QLabel(icons)
            icons_lbl.setStyleSheet(f"font-size: 12px; background: transparent;")
            layout.addWidget(icons_lbl)

        layout.addStretch()

    def mousePressEvent(self, event):
        from PySide6.QtCore import QPoint
        self._selected = not self._selected
        c = Theme.colors()
        if self._selected:
            self.setStyleSheet(f"""
                DayCell {{
                    background: {c["SAKURA"]}22; border: 2px solid {c["SAKURA"]};
                    border-radius: 6px;
                }}
            """)
        else:
            bg = self.styleSheet().split("background:")[1].split(";")[0].strip() if "background:" in self.styleSheet() else c["CARD_BG"]
            self.setStyleSheet(self.styleSheet().replace(
                f"border: 2px solid {c['SAKURA']}", f"border: 1.5px solid {c['CARD_BORDER']}"
            ).replace(f"background: {c['SAKURA']}22", f"background: {bg}"))
        super().mousePressEvent(event)


class CalendarView(QFrame):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setObjectName("calendarView")
        self._loader = None
        self._today = date.today()
        self._current_year = self._today.year
        self._current_month = self._today.month
        self._events_data = {}
        self._build_ui()
        self.setup_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)
        layout.setSpacing(12)

        title = QLabel("📅 Calendrier")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        nav = QHBoxLayout()
        nav.setSpacing(10)
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("navBtn")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.clicked.connect(self._prev_month)
        nav.addWidget(self.btn_prev)

        self.month_label = QLabel("")
        self.month_label.setObjectName("monthLabel")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.month_label, stretch=1)

        self.btn_today = QPushButton("Aujourd'hui")
        self.btn_today.setObjectName("todayBtn")
        self.btn_today.clicked.connect(self._go_today)
        nav.addWidget(self.btn_today)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("navBtn")
        self.btn_next.setFixedWidth(40)
        self.btn_next.clicked.connect(self._next_month)
        nav.addWidget(self.btn_next)

        layout.addLayout(nav)

        dow_row = QHBoxLayout()
        dow_row.setSpacing(0)
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for d in days_fr:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("dowLabel")
            dow_row.addWidget(lbl)
        layout.addLayout(dow_row)

        self.grid_w = QWidget()
        self.grid_w.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_w)
        self.grid.setSpacing(4)
        layout.addWidget(self.grid_w, stretch=1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setFixedHeight(160)

        self.event_container = QWidget()
        self.event_container.setStyleSheet("background: transparent;")
        self.event_layout = QVBoxLayout(self.event_container)
        self.event_layout.setSpacing(4)
        self.event_layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        scroll.setWidget(self.event_container)
        layout.addWidget(scroll)

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QFrame#calendarView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{ font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]}; }}
            QLabel#monthLabel {{ font-size: 20px; font-weight: bold; color: {c["TEXT_PRIMARY"]}; }}
            QLabel#dowLabel {{
                font-size: 12px; font-weight: bold; color: {c["MILK_TEA"]};
                padding: 6px 0; background: transparent;
            }}
            QPushButton#navBtn {{
                background: {c["CARD_BG"]}; color: {c["TEXT_PRIMARY"]};
                border: 0.5px solid {c["CARD_BORDER"]}; border-radius: 6px;
                font-size: 14px; padding: 6px 10px;
            }}
            QPushButton#navBtn:hover {{ background: {c["SIDEBAR_HOVER"]}; }}
            QPushButton#todayBtn {{
                background: {c["SAKURA"]}; color: {c["BG"]};
                border: none; border-radius: 6px; font-size: 12px; font-weight: bold;
                padding: 6px 14px;
            }}
            QPushButton#todayBtn:hover {{ opacity: 0.85; }}
            QPushButton#actionBtn {{
                background: {c["CARD_BG"]}; color: {c["TEXT_PRIMARY"]};
                border: 0.5px solid {c["CARD_BORDER"]}; border-radius: 6px;
                font-size: 12px; padding: 6px 12px;
            }}
            QPushButton#actionBtn:hover {{
                border-color: {c["SAKURA"]}; color: {c["SAKURA"]};
            }}
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        self._update_month_label()
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait(500)
        self._loader = CalendarLoader(self.user_id, self._current_month, self._current_year)
        self._loader.data_ready.connect(self._on_data)
        self._loader.start()

    def _on_data(self, grouped: dict):
        self._events_data = grouped
        self._render_grid()
        self._clear_layout(self.event_layout)
        self._show_day_events(self._today)

    def _render_grid(self):
        self._clear_grid()

        first_day = date(self._current_year, self._current_month, 1)
        last_day_num = monthrange(self._current_year, self._current_month)[1]
        start_weekday = first_day.weekday()

        row, col = 0, 0
        for _ in range(start_weekday):
            col += 1

        for day_num in range(1, last_day_num + 1):
            d = date(self._current_year, self._current_month, day_num)
            is_today = d == self._today
            day_events = self._events_data.get(str(d), {}).get("events", [])
            cell = DayCell(day_num, d, is_today, True, day_events)
            cell.mousePressEvent = lambda e, dd=d: self._on_day_click(e, dd)
            self.grid.addWidget(cell, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _on_day_click(self, event, d):
        self._clear_layout(self.event_layout)
        self._show_day_events(d)
        for i in range(self.grid.count()):
            w = self.grid.itemAt(i)
            if w and w.widget() and hasattr(w.widget(), 'date_obj') and w.widget().date_obj == d:
                cell = w.widget()
                c = Theme.colors()
                cell.setStyleSheet(f"""
                    DayCell {{
                        background: {c["SAKURA"]}22; border: 2px solid {c["SAKURA"]};
                        border-radius: 6px;
                    }}
                """)
            elif w and w.widget() and hasattr(w.widget(), 'setStyleSheet'):
                c = Theme.colors()
                is_today = w.widget().date_obj == self._today if hasattr(w.widget(), 'date_obj') else False
                bg = c["CARD_BG"]
                border = c["SAKURA"] if is_today else c["CARD_BORDER"]
                w.widget().setStyleSheet(f"""
                    DayCell {{
                        background: {bg}; border: 1.5px solid {border};
                        border-radius: 6px;
                    }}
                    DayCell:hover {{
                        border-color: {c["SAKURA"]};
                    }}
                """)

    def _show_day_events(self, d):
        key = str(d)
        group = self._events_data.get(key, {})
        events = group.get("events", []) if group else []

        if d == self._today:
            header = f"📌 Aujourd'hui — {d.strftime('%A %d %B %Y')}"
        elif d == self._today + timedelta(days=1):
            header = f"📅 Demain — {d.strftime('%A %d %B %Y')}"
        else:
            header = d.strftime('%A %d %B %Y').capitalize()

        c = Theme.colors()
        h = QLabel(header)
        h.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c['SAKURA']}; padding: 4px 0; background: transparent;")
        self.event_layout.addWidget(h)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        btn_goal = QPushButton("🎯 Ajouter un objectif")
        btn_goal.setObjectName("actionBtn")
        btn_goal.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_goal.clicked.connect(lambda: self._add_goal(d))
        actions.addWidget(btn_goal)

        btn_reminder = QPushButton("⏰ Ajouter un rappel")
        btn_reminder.setObjectName("actionBtn")
        btn_reminder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reminder.clicked.connect(lambda: self._add_reminder(d))
        actions.addWidget(btn_reminder)

        actions.addStretch()
        aw = QWidget()
        aw.setLayout(actions)
        aw.setStyleSheet("background: transparent;")
        self.event_layout.addWidget(aw)

        if not events:
            empty = QLabel("Aucun événement pour ce jour")
            empty.setStyleSheet(f"font-size: 12px; color: {c['MILK_TEA']}; padding: 4px 0; background: transparent;")
            self.event_layout.addWidget(empty)
        else:
            for ev in events:
                card = self._event_card(ev)
                self.event_layout.addWidget(card)

        self.event_layout.addStretch()

    def _add_goal(self, d):
        text, ok = QInputDialog.getText(self, "Nouvel objectif",
            f"Objectif pour le {d.strftime('%d/%m/%Y')} :",
            QLineEdit.EchoMode.Normal)
        if not ok or not text.strip():
            return
        from models.database import get_session
        from models.objective import Objective
        session = get_session()
        try:
            goal = Objective(
                utilisateur_id=self.user_id,
                description=text.strip(),
                valeur_cible=1.0,
                unite="fois",
                statut="actif",
                date_creation=d,
            )
            session.add(goal)
            session.commit()
            QMessageBox.information(self, "✓ Ajouté", f"Objectif ajouté :\n{text.strip()}")
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _add_reminder(self, d):
        text, ok = QInputDialog.getText(self, "Nouveau rappel",
            f"Rappel pour le {d.strftime('%d/%m/%Y')} :",
            QLineEdit.EchoMode.Normal)
        if not ok or not text.strip():
            return
        from models.database import get_session
        from models.extensions import TimelineEvent
        from datetime import datetime
        session = get_session()
        try:
            ev = TimelineEvent(
                utilisateur_id=self.user_id,
                event_type="reminder",
                title=text.strip(),
                description="",
                icon="⏰",
                event_date=datetime.combine(d, datetime.min.time()),
                importance=0.5,
            )
            session.add(ev)
            session.commit()
            QMessageBox.information(self, "✓ Ajouté", f"Rappel ajouté :\n{text.strip()}")
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _event_card(self, ev: dict) -> QFrame:
        c = Theme.colors()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {c["CARD_BG"]}; border-radius: 6px;
                border: 0.5px solid {c["CARD_BORDER"]};
            }}
        """)
        cl = QHBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)  # 12, 8, 12, 8)
        cl.setSpacing(10)

        icon = QLabel(ev.get("icon", "📌"))
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        icon.setFixedWidth(24)
        cl.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        title = QLabel(ev.get("title", ""))
        title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c['TEXT_PRIMARY']}; background: transparent;")
        text_col.addWidget(title)

        if ev.get("description"):
            desc = QLabel(ev["description"])
            desc.setStyleSheet(f"font-size: 11px; color: {c['MILK_TEA']}; background: transparent;")
            text_col.addWidget(desc)

        cl.addLayout(text_col, stretch=1)

        source = QLabel(ev.get("source", ""))
        source.setStyleSheet(f"""
            font-size: 10px; color: {c['SAKURA']};
            padding: 1px 6px; border: 0.5px solid {c['SAKURA']}; border-radius: 8px;
            background: transparent;
        """)
        cl.addWidget(source)

        return card

    def _prev_month(self):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self.load_data()

    def _next_month(self):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self.load_data()

    def _go_today(self):
        self._current_month = self._today.month
        self._current_year = self._today.year
        self.load_data()

    def _update_month_label(self):
        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        self.month_label.setText(f"{months[self._current_month - 1]} {self._current_year}")

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
