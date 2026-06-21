from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QScrollArea, QGridLayout,
                               QLineEdit, QTextEdit, QDateEdit)
from utils.theme import Theme
from services.academic_service import AcademicService


class AcademicView(QFrame):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setObjectName("academicView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 40, 30, 40, 30)

        title = QLabel("🎓 Assistant Académique")
        title.setObjectName("pageTitle")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setSpacing(16)

        self.readiness_card = QFrame()
        self.readiness_card.setObjectName("readinessCard")
        r_layout = QVBoxLayout(self.readiness_card)
        self.readiness_title = QLabel("Préparation aux examens")
        self.readiness_title.setObjectName("readinessTitle")
        self.readiness_bar = QFrame()
        self.readiness_bar.setObjectName("readinessBar")
        self.readiness_bar.setFixedHeight(12)
        self.readiness_fill = QFrame()
        self.readiness_fill.setObjectName("readinessFill")
        r_bar_layout = QVBoxLayout(self.readiness_bar)
        r_bar_layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        r_bar_layout.addWidget(self.readiness_fill)
        self.readiness_label = QLabel()
        self.readiness_label.setObjectName("readinessLabel")
        r_layout.addWidget(self.readiness_title)
        r_layout.addWidget(self.readiness_bar)
        r_layout.addWidget(self.readiness_label)

        self.scroll_layout.addWidget(self.readiness_card)

        self.assignments_section = QLabel("📝 Devoirs à venir")
        self.assignments_section.setObjectName("sectionTitle")
        self.assignments_container = QVBoxLayout()
        self.assignments_container.setSpacing(8)

        self.courses_section = QLabel("📚 Cours")
        self.courses_section.setObjectName("sectionTitle")
        self.courses_container = QVBoxLayout()
        self.courses_container.setSpacing(8)

        self.subjects_section = QLabel("⏱️ Sujets étudiés")
        self.subjects_section.setObjectName("sectionTitle")
        self.subjects_container = QVBoxLayout()
        self.subjects_container.setSpacing(8)

        self.scroll_layout.addWidget(self.assignments_section)
        self.scroll_layout.addLayout(self.assignments_container)
        self.scroll_layout.addWidget(self.courses_section)
        self.scroll_layout.addLayout(self.courses_container)
        self.scroll_layout.addWidget(self.subjects_section)
        self.scroll_layout.addLayout(self.subjects_container)
        self.scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)

        layout.addWidget(title)
        layout.addWidget(scroll)
        self.setup_style()

        self._loader = None

    def setup_style(self):
        c = Theme.colors()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {c["BG"]}; color: {c["TEXT_PRIMARY"]}; }}
            QFrame#academicView {{ background-color: {c["BG"]}; }}
            QLabel#pageTitle {{
                font-size: 26px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-bottom: 16px;
            }}
            QLabel#sectionTitle {{
                font-size: 18px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
                margin-top: 8px;
            }}
            QFrame#readinessCard {{
                background-color: {c["CARD_BG"]}; border-radius: 12px;
                padding: 20px;
            }}
            QLabel#readinessTitle {{
                font-size: 16px; font-weight: bold; color: {c["TEXT_PRIMARY"]};
            }}
            QFrame#readinessBar {{
                background-color: {c["BG"]}; border-radius: 6px;
            }}
            QFrame#readinessFill {{
                background-color: {c["ACCENT"]}; border-radius: 6px;
            }}
            QLabel#readinessLabel {{
                font-size: 14px; color: {c["TEXT_SECONDARY"]};
            }}
        """)
        c = Theme.colors()
        self.readiness_fill.setStyleSheet(f"""
            background-color: {c["ACCENT"]}; border-radius: 6px;
        """)

    def refresh_theme(self):
        self.setup_style()

    def load_data(self):
        if self._loader:
            if self._loader.isRunning():
                self._loader.quit()
                self._loader.wait(500)
        self._loader = AcademicLoader(self.user_id)
        self._loader.data_ready.connect(self._on_data)
        self._loader.start()

    def _on_data(self, readiness: dict, assignments: list, courses: list, subjects: list):
        r = readiness.get("readiness", 0)
        self.readiness_fill.setFixedWidth(int(self.readiness_bar.width() * r / 100))
        self.readiness_label.setText(
            f"Préparation : {r}% · {readiness.get('total_hours', 0)}h étudiées · "
            f"{readiness.get('pending_assignments', 0)} devoir(s) en attente"
        )
        # Clear old items
        self._clear_layout(self.assignments_container)
        self._clear_layout(self.courses_container)
        self._clear_layout(self.subjects_container)

        if assignments:
            for a in assignments:
                self.assignments_container.addWidget(self._make_assignment_card(a))
        else:
            self.assignments_container.addWidget(QLabel("✅ Aucun devoir en attente."))

        if courses:
            for c in courses:
                self.courses_container.addWidget(self._make_course_card(c))
        else:
            self.courses_container.addWidget(QLabel("Ajoute des cours depuis les paramètres."))

        if subjects:
            for s in subjects:
                self.subjects_container.addWidget(self._make_subject_card(s))
        else:
            self.subjects_container.addWidget(QLabel("Aucune session d'étude enregistrée."))

    def _make_assignment_card(self, a: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("itemCard")
        cl = QHBoxLayout(card)
        t = QLabel(f"📌 {a['title']}")
        t.setObjectName("itemText")
        due = a.get("due_date", "")
        d_label = QLabel(due[:10] if due else "Pas de date")
        d_label.setObjectName("itemDate")
        cl.addWidget(t)
        cl.addStretch()
        cl.addWidget(d_label)
        return card

    def _make_course_card(self, c: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("itemCard")
        cl = QHBoxLayout(card)
        t = QLabel(f"📖 {c['name']} ({c.get('code', '')})")
        t.setObjectName("itemText")
        s = QLabel(f"{c.get('credits', 0)} crédits · {c.get('status', 'en cours')}")
        s.setObjectName("itemDate")
        cl.addWidget(t)
        cl.addStretch()
        cl.addWidget(s)
        return card

    def _make_subject_card(self, s: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("itemCard")
        cl = QHBoxLayout(card)
        t = QLabel(f"📚 {s['name']}")
        t.setObjectName("itemText")
        info = QLabel(f"{s['total_hours']}h · {s['session_count']} séances")
        info.setObjectName("itemDate")
        cl.addWidget(t)
        cl.addStretch()
        cl.addWidget(info)
        return card

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class AcademicLoader(QThread):
    data_ready = Signal(dict, list, list, list)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            svc = AcademicService(self.user_id)
            readiness = svc.get_exam_readiness()
            assignments = svc.get_assignments()
            courses = svc.get_all_courses()
            subjects = svc.get_study_subjects()
            self.data_ready.emit(readiness, assignments, courses, subjects)
        except Exception as e:
            print(f"AcademicLoader error: {e}")
            self.data_ready.emit(
                {"readiness":0,"total_hours":0,"courses":0,"pending_assignments":0,"subjects":0},
                [], [], [])
