from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox,
    QStackedWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from controllers.auth_controller import AuthController
from views.reset_password_view import ResetPasswordView
from utils.theme import Theme, DARK_CHOCOLATE, ALOEWOOD, MILK_TEA, SAKURA, MISTY_ROSE, BORDER_RADIUS, BORDER_RADIUS_LG, FONT_FAMILY


class LoginView(QWidget):

    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.auth_controller = AuthController()
        self.setWindowTitle("Personal Digital Twin")
        self.setMinimumSize(900, 580)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left())
        root.addWidget(self._build_right(), stretch=1)

    def _build_left(self):
        left = QFrame()
        left.setFixedWidth(340)
        left.setStyleSheet(f"background-color: {MISTY_ROSE};")
        layout = QVBoxLayout(left)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(0)

        layout.addStretch(1)

        mark = QLabel()
        mark.setFixedSize(40, 40)
        mark.setStyleSheet(f"background: {SAKURA}; border-radius: 10px;")
        layout.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(24)

        brand = QLabel("Personal\nDigital Twin")
        brand.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 26, QFont.Weight.Bold))
        brand.setStyleSheet(f"color: {Theme.get('TEXT_PRIMARY')}; background: transparent;")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)
        layout.addSpacing(14)

        tagline = QLabel("Your digital self\ntracking and growing with you")
        tagline.setStyleSheet(f"color: {Theme.get('TEXT_SECONDARY')}; font-size: 13px; background: transparent;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)
        layout.addSpacing(30)

        layout.addStretch(1)

        version = QLabel("v1.0 - Personal tracker")
        version.setStyleSheet(f"color: {Theme.get('TEXT_MUTED')}; font-size: 11px; background: transparent;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        return left

    def _build_right(self):
        c = Theme.colors()
        right = QFrame()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right.setStyleSheet(f"background-color: {c['BG']};")
        outer = QVBoxLayout(right)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)  # 60, 40, 60, 40)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.setFixedWidth(420)

        self.welcome_page = self._build_welcome_page()
        self.login_form = self._build_login_form()
        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.login_form)

        outer.addWidget(self.stack, alignment=Qt.AlignmentFlag.AlignCenter)
        return right

    def _build_welcome_page(self):
        c = Theme.colors()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Bienvenue sur\nDigital Twin")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 30, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(12)

        sub = QLabel("Suis tes habitudes, développe ton esprit,\net comprends-toi mieux.")
        sub.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 14px; line-height: 1.5; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(36)

        features = [
            ("Check-ins quotidiens", "Humeur, énergie et sommeil"),
            ("Focus Pomodoro", "Reste productif avec le timer"),
            ("IA intelligente", "Analyse personnalisée"),
            ("Journal & objectifs", "Écris, réfléchis et progresse"),
        ]
        for feat_title, feat_desc in features:
            row = QHBoxLayout()
            row.setSpacing(12)
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {SAKURA}; border-radius: 4px;")
            row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(0)
            ft = QLabel(feat_title)
            ft.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 13, QFont.Weight.DemiBold))
            ft.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
            col.addWidget(ft)
            fd = QLabel(feat_desc)
            fd.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
            col.addWidget(fd)
            row.addLayout(col, stretch=1)
            layout.addLayout(row)
            layout.addSpacing(14)

        layout.addSpacing(24)

        btn = QPushButton("Se connecter")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['BTN_PRIMARY_BG']};
                color: {c['BTN_PRIMARY_TEXT']};
                border: none;
                border-radius: {BORDER_RADIUS + 2}px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['ACCENT_HOVER']};
            }}
        """)
        btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.login_form))
        layout.addWidget(btn)
        layout.addSpacing(12)

        link = QPushButton("Creer un compte")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {c['TEXT_SECONDARY']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {c['ACCENT']};
            }}
        """)
        link.clicked.connect(self._show_register)
        layout.addWidget(link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return w

    def _build_login_form(self):
        c = Theme.colors()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Bon retour")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(6)
        sub = QLabel("Connecte-toi à ton compte")
        sub.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 14px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(36)

        layout.addWidget(self._label("Email"))
        layout.addSpacing(8)
        self.login_email = self._input("email@example.com")
        layout.addWidget(self.login_email)
        layout.addSpacing(22)

        layout.addWidget(self._label("Mot de passe"))
        layout.addSpacing(8)
        self.login_password = self._input("password", password=True)
        self.login_password.returnPressed.connect(self._handle_login)
        layout.addWidget(self.login_password)
        layout.addSpacing(36)

        btn = QPushButton("Se connecter")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._btn_style())
        btn.clicked.connect(self._handle_login)
        layout.addWidget(btn)
        layout.addSpacing(14)

        btn_forgot = QPushButton("Mot de passe oublié ?")
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.setStyleSheet(self._link_style())
        btn_forgot.clicked.connect(self._show_reset_password)
        layout.addWidget(btn_forgot, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(4)

        link = QPushButton("Pas de compte ? Crées-en un")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet(self._link_style())
        link.clicked.connect(self._show_register)
        layout.addWidget(link, alignment=Qt.AlignmentFlag.AlignCenter)

        back = QPushButton("Retour à l'accueil")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {c['TEXT_MUTED']};
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {c['ACCENT']};
            }}
        """)
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.welcome_page))
        layout.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return w

    def _build_register_form(self):
        c = Theme.colors()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Créer un compte")
        title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(6)
        sub = QLabel("Rejoins ton Digital Twin")
        sub.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 14px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(28)

        layout.addWidget(self._label("Prénom"))
        layout.addSpacing(8)
        self.register_nom = self._input("Ton prénom")
        layout.addWidget(self.register_nom)
        layout.addSpacing(18)

        layout.addWidget(self._label("Email"))
        layout.addSpacing(8)
        self.register_email = self._input("email@example.com")
        layout.addWidget(self.register_email)
        layout.addSpacing(18)

        layout.addWidget(self._label("Mot de passe"))
        layout.addSpacing(8)
        self.register_password = self._input("Au moins 6 caractères", password=True)
        layout.addWidget(self.register_password)
        layout.addSpacing(30)

        btn = QPushButton("Créer mon compte")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._btn_style())
        btn.clicked.connect(self._handle_register)
        layout.addWidget(btn)
        layout.addSpacing(16)

        link = QPushButton("Déjà un compte ? Connecte-toi")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet(self._link_style())
        link.clicked.connect(self._show_login)
        layout.addWidget(link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return w

    def _show_login(self):
        self.stack.setCurrentWidget(self.login_form)
        for i in range(self.stack.count() - 1, -1, -1):
            w = self.stack.widget(i)
            if w is not self.welcome_page and w is not self.login_form and not isinstance(w, ResetPasswordView):
                self.stack.removeWidget(w)
                w.deleteLater()

    def _show_register(self):
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w is not self.welcome_page and w is not self.login_form and not isinstance(w, ResetPasswordView):
                self.stack.setCurrentWidget(w)
                return
        register_form = self._build_register_form()
        self.stack.addWidget(register_form)
        self.stack.setCurrentWidget(register_form)

    def _show_reset_password(self):
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if isinstance(w, ResetPasswordView):
                self.stack.setCurrentWidget(w)
                return
        reset_view = ResetPasswordView(on_back_to_login=self._back_to_login)
        self.stack.addWidget(reset_view)
        self.stack.setCurrentWidget(reset_view)

    def _back_to_login(self):
        self.stack.setCurrentWidget(self.login_form)
        for i in range(self.stack.count() - 1, -1, -1):
            w = self.stack.widget(i)
            if w is not self.welcome_page and w is not self.login_form and not isinstance(w, ResetPasswordView):
                self.stack.removeWidget(w)
                w.deleteLater()

    def _handle_login(self):
        try:
            email = self.login_email.text().strip()
            password = self.login_password.text()
            if not email or not password:
                QMessageBox.warning(self, "Missing fields", "Please fill in email and password.")
                return
            if "@" not in email or "." not in email.split("@")[-1]:
                QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
                return
            success, result = self.auth_controller.login(email, password)
            if success:
                self.on_login_success(result)
            else:
                QMessageBox.warning(self, "Sign in error", str(result))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{traceback.format_exc()}")

    def _handle_register(self):
        try:
            nom = self.register_nom.text().strip()
            email = self.register_email.text().strip()
            password = self.register_password.text()
            if not nom or not email or not password:
                QMessageBox.warning(self, "Missing fields", "Please fill in all fields.")
                return
            if "@" not in email or "." not in email.split("@")[-1]:
                QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
                return
            success, message = self.auth_controller.register(nom, email, password)
            if success:
                QMessageBox.information(self, "Account created", message)
                self._back_to_login()
                self.login_email.setText(email)
            else:
                QMessageBox.warning(self, "Error", str(message))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{traceback.format_exc()}")

    def _label(self, text):
        c = Theme.colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {c['TEXT_SECONDARY']}; font-size: 11px; "
            f"font-weight: 600; letter-spacing: 0.4px; background: transparent;"
        )
        return lbl

    def _input(self, placeholder, password=False):
        c = Theme.colors()
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(48)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['INPUT_BG']};
                border: 1.5px solid {c['INPUT_BORDER']};
                border-radius: {BORDER_RADIUS}px;
                padding: 0 14px;
                font-size: 14px;
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {c['INPUT_FOCUS']};
            }}
            QLineEdit::placeholder {{
                color: {c['TEXT_MUTED']};
            }}
        """)
        if password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        return inp

    def _btn_style(self):
        c = Theme.colors()
        return f"""
            QPushButton {{
                background-color: {c['BTN_PRIMARY_BG']};
                color: {c['BTN_PRIMARY_TEXT']};
                border: none;
                border-radius: {BORDER_RADIUS + 2}px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['ACCENT_HOVER']};
            }}
        """

    def _link_style(self):
        c = Theme.colors()
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {c['TEXT_SECONDARY']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {c['ACCENT']};
            }}
        """
