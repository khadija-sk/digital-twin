from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from controllers.auth_controller import AuthController
from utils.theme import Theme, DARK_CHOCOLATE, SAKURA, MILK_TEA


class ResetPasswordView(QWidget):
    def __init__(self, on_back_to_login):
        super().__init__()
        self.on_back_to_login = on_back_to_login
        self.auth = AuthController()
        self.setStyleSheet(self._get_style())
        self._build_ui()

    def _build_ui(self):
        c = Theme.colors()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 60, 40, 60, 40)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        self.stack.setFixedWidth(420)
        self.stack.setStyleSheet("background: transparent;")

        self.step_email = self._build_email_step()
        self.stack.addWidget(self.step_email)

        self.step_reset = self._build_reset_step()
        self.stack.addWidget(self.step_reset)

        main_layout.addWidget(self.stack, alignment=Qt.AlignmentFlag.AlignCenter)

    def _build_email_step(self):
        c = Theme.colors()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(20)

        title = QLabel("Forgot password")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)

        desc = QLabel("Enter your email address to receive a reset link.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {MILK_TEA}; font-size: 13px;")
        layout.addWidget(desc)

        layout.addSpacing(12)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@email.com")
        self.email_input.setFixedHeight(44)
        self.email_input.setStyleSheet(self._input_style())
        layout.addWidget(self.email_input)

        btn_request = QPushButton("Send link")
        btn_request.setFixedHeight(44)
        btn_request.setStyleSheet(self._btn_primary_style())
        btn_request.clicked.connect(self._handle_request)
        layout.addWidget(btn_request)

        btn_back = QPushButton("Back to login")
        btn_back.setStyleSheet(self._link_style())
        btn_back.clicked.connect(self.on_back_to_login)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return w

    def _build_reset_step(self):
        c = Theme.colors()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(18)

        title = QLabel("Reset")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)

        desc = QLabel("Enter the received token and your new password.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {MILK_TEA}; font-size: 13px;")
        layout.addWidget(desc)

        layout.addSpacing(8)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Reset token")
        self.token_input.setFixedHeight(44)
        self.token_input.setStyleSheet(self._input_style())
        layout.addWidget(self.token_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("New password (min 6 characters)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setFixedHeight(44)
        self.new_password_input.setStyleSheet(self._input_style())
        layout.addWidget(self.new_password_input)

        btn_reset = QPushButton("Reset")
        btn_reset.setFixedHeight(44)
        btn_reset.setStyleSheet(self._btn_primary_style())
        btn_reset.clicked.connect(self._handle_reset)
        layout.addWidget(btn_reset)

        btn_back = QPushButton("Back to login")
        btn_back.setStyleSheet(self._link_style())
        btn_back.clicked.connect(self.on_back_to_login)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return w

    def _handle_request(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Empty field", "Please enter your email.")
            return
        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return

        success, result = self.auth.request_password_reset(email)
        if success:
            self.token_input.setText(result)
            QMessageBox.information(
                self, "Token generated",
                "A reset email has been simulated.\n\n"
                "The token has been auto-filled below.\n"
                "Enter your new password to complete."
            )
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Error", str(result))

    def _handle_reset(self):
        token = self.token_input.text().strip()
        new_password = self.new_password_input.text()

        if not token or not new_password:
            QMessageBox.warning(self, "Missing fields", "Please fill all fields.")
            return

        success, message = self.auth.reset_password(token, new_password)
        if success:
            QMessageBox.information(self, "Password reset", message)
            self.on_back_to_login()
        else:
            QMessageBox.warning(self, "Error", message)

    def _input_style(self):
        c = Theme.colors()
        return f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                border-bottom: 1.5px solid {c['CARD_BORDER']};
                padding: 0 6px;
                font-size: 14px;
                color: {c['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border-bottom: 2px solid {SAKURA};
            }}
        """

    def _btn_primary_style(self):
        c = Theme.colors()
        return f"""
            QPushButton {{
                background-color: {DARK_CHOCOLATE};
                color: {MILK_TEA};
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {SAKURA};
                color: {DARK_CHOCOLATE};
            }}
        """

    def _link_style(self):
        c = Theme.colors()
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {MILK_TEA};
                font-size: 13px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {SAKURA};
            }}
        """

    def _get_style(self):
        c = Theme.colors()
        return f"""
            QWidget {{
                color: {c['TEXT_PRIMARY']};
                background-color: {c['BG']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """
