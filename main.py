import os
import sys
from datetime import datetime, date, timedelta

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout,
    QWidget, QStackedWidget, QMessageBox, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtGui import QFont

from models.database import init_db, get_session
from models.user import User
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.home_view import HomeView
from views.checkin_view import CheckinView
from views.timer_view import TimerView
from views.stats_view import StatsView
from views.goals_view import GoalsView
from views.journal_view import JournalView
from views.settings_view import SettingsView
from views.profile_view import ProfileView
from views.routine_view import RoutineView
from views.search_view import SearchView
from views.health_view import HealthView
from views.ai_view import AIView
from views.sidebar_widget import SidebarWidget
from views.ai_panel import AIPanel
from views.model_selector_widget import ModelSelectorWidget
from views.onboarding_view import OnboardingView, WeeklyReportPopup
from views.toast_notification import ToastNotification
from views.spinner_widget import SpinnerWidget
from views.briefing_view import BriefingView, EmptyStateView
from views.recommendations_view import RecommendationsView
from views.analytics_view import AnalyticsView
from views.calendar_view import CalendarView

from services.gemini_service import AIService as GeminiService
from services.anthropic_service import AnthropicService
from services.model_manager import ModelManager
from services.config_service import ConfigService
from controllers.llm_controller import LLMController
from controllers.preferences_controller import PreferencesController
from controllers.checkin_controller import CheckinController
from controllers.journal_controller import JournalController
from controllers.timer_controller import TimerController
from controllers.gamification_controller import GamificationController
from utils.theme import Theme, FONT_FAMILY
from utils.session import SessionManager



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Twin")
        self.setMinimumSize(1200, 760)

        self._pages = {}
        self.current_user = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(1)

        self._stack = QStackedWidget()
        self._sidebar = None
        self._ai_panel = None
        self._model_selector = None

        self.login_view = LoginView(on_login_success=self._on_login_success)
        self._stack.addWidget(self.login_view)
        root.addWidget(self._stack)

    def _on_login_success(self, user):
        self.current_user = user
        SessionManager.initialize(30).start_session(user.id)
        self._pending_user = user
        QTimer.singleShot(0, self._build_main_interface)

    def _build_main_interface(self):
        user = self._pending_user
        self._pending_user = None

        try:
            c = Theme.colors()
            central = self.centralWidget()
            root_layout = central.layout()

            old_widgets = []
            for i in range(root_layout.count()):
                w = root_layout.itemAt(i).widget()
                if w != self._stack:
                    old_widgets.append(w)
            for w in old_widgets:
                root_layout.removeWidget(w)
                w.deleteLater()

            self._sidebar = SidebarWidget(user=user, on_navigate=self._navigate, current_page="home")
            root_layout.insertWidget(0, self._sidebar)

            content_wrap = QWidget()
            content_wrap.setObjectName("content_wrap")
            self._content_wrap = content_wrap
            content_layout = QVBoxLayout(content_wrap)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)

            centered_wrapper = QFrame()
            centered_wrapper.setObjectName("centered_wrapper")
            cw_layout = QVBoxLayout(centered_wrapper)
            cw_layout.setContentsMargins(40, 0, 40, 0)
            cw_layout.setSpacing(0)

            topbar = QFrame()
            topbar.setObjectName("content_topbar")
            topbar.setFixedHeight(48)
            tb_layout = QHBoxLayout(topbar)
            tb_layout.setContentsMargins(0, 0, 0, 0)

            page_title = QLabel("Home")
            page_title.setObjectName("page_title")
            page_title.setFont(QFont(FONT_FAMILY.split(",")[0].strip("'"), 22, QFont.Weight.Bold))
            page_title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
            tb_layout.addWidget(page_title)
            self._page_title = page_title

            tb_layout.addStretch()

            self._model_selector = ModelSelectorWidget()
            tb_layout.addWidget(self._model_selector)

            cw_layout.addWidget(topbar)

            self._stack.setParent(None)
            cw_layout.addWidget(self._stack, stretch=1)

            content_layout.addWidget(centered_wrapper, stretch=1)

            root_layout.insertWidget(1, content_wrap, stretch=1)

            self._ai_toggle_btn = QPushButton("AI")
            self._ai_toggle_btn.setFixedWidth(32)
            self._ai_toggle_btn.setFixedHeight(80)
            self._ai_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._ai_toggle_btn.setObjectName("ai_toggle_btn")
            self._ai_toggle_btn.clicked.connect(self._toggle_ai_panel)
            root_layout.insertWidget(2, self._ai_toggle_btn)

            self._ai_panel = AIPanel(user)
            self._ai_panel.setFixedWidth(340)
            self._ai_panel.setVisible(False)
            root_layout.insertWidget(3, self._ai_panel)

            self._ai_panel_visible = False

            self._apply_theme()

            self._session_timer = QTimer(self)
            self._session_timer.timeout.connect(self._check_session)
            self._session_timer.start(60_000)

            self._stack.removeWidget(self.login_view)
            self.login_view.setParent(None)

            home = HomeView(user=user, on_navigate=self._navigate)
            self._pages["home"] = home
            self._stack.addWidget(home)

            dashboard = DashboardView(user=user, on_navigate=self._navigate)
            self._pages["dashboard"] = dashboard
            self._stack.addWidget(dashboard)

            self._stack.setCurrentWidget(home)

            QTimer.singleShot(200, lambda: self._check_onboarding(user))
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self._show_toast(f"Erreur d'initialisation : {str(e)[:100]}", "error", 8000)

    def _apply_theme(self):
        c = Theme.colors()
        app = QApplication.instance()
        if app:
            app.setStyleSheet(Theme.stylesheet())
        self.setStyleSheet(f"""
            QMainWindow {{ background: {c['BG']}; }}
            QWidget {{ font-family: {FONT_FAMILY}; color: {c['TEXT_PRIMARY']}; }}
            QWidget#content_wrap {{ background: {c['BG']}; }}
            QFrame#centered_wrapper {{ background: transparent; }}
            QFrame#content_topbar {{
                background: {c['TOPBAR_BG']};
                border-bottom: 1px solid {c['TOPBAR_BORDER']};
            }}
            QPushButton#ai_toggle_btn {{
                background: {c['SIDEBAR_BG']};
                color: {c['ACCENT']};
                border: none;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton#ai_toggle_btn:hover {{
                background: {c['SIDEBAR_HOVER']};
                color: {c['TEXT_PRIMARY']};
            }}
        """)
        if self._ai_panel:
            self._ai_panel.setStyleSheet(f"""
                QFrame#ai_panel {{
                    background: {c['BG']};
                    border-left: 1px solid {c['CARD_BORDER']};
                }}
                QWidget#ai_chat_container {{
                    background: {c['BG']};
                }}
                QFrame#ai_input_bar {{
                    background: {c['BG']};
                }}
                QLineEdit#ai_input {{
                    background: {c['INPUT_BG']};
                    border: 1.5px solid {c['INPUT_BORDER']};
                    border-radius: 19px; padding: 0 14px;
                    font-size: 13px; color: {c['TEXT_PRIMARY']};
                }}
                QLineEdit#ai_input:focus {{
                    border-color: {c['INPUT_FOCUS']};
                }}
                QPushButton#ai_send_btn {{
                    background: {c['BTN_PRIMARY_BG']};
                    color: {c['BTN_PRIMARY_TEXT']};
                    border: none; border-radius: 19px;
                    font-size: 13px; font-weight: bold;
                }}
                QPushButton#ai_send_btn:hover {{
                    background: {c['ACCENT_HOVER']};
                }}
                QPushButton#ai_send_btn:disabled {{
                    background: {c['TEXT_MUTED']};
                    color: {c['BG']};
                }}
                QFrame#bubble_user {{
                    background: {c['BUBBLE_USER']};
                    border-radius: 18px;
                    border-bottom-right-radius: 4px;
                }}
                QFrame#bubble_ai {{
                    background: {c['BUBBLE_AI']};
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    border: 0.5px solid {c['CARD_BORDER']};
                }}
            """)

    def _on_theme_changed(self):
        self._apply_theme()
        for widget in self._pages.values():
            if hasattr(widget, "refresh"):
                widget.refresh()
            if hasattr(widget, "_get_style"):
                try:
                    widget.setStyleSheet(widget._get_style())
                except Exception:
                    pass
        if self._sidebar and hasattr(self._sidebar, 'refresh'):
            self._sidebar.refresh()
        if self._model_selector and hasattr(self._model_selector, 'refresh'):
            self._model_selector.refresh()
        if self._page_title:
            c = Theme.colors()
            self._page_title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'refresh_theme'):
                widget.refresh_theme()
            elif hasattr(widget, '_get_style'):
                try:
                    widget.setStyleSheet(widget._get_style())
                except Exception:
                    pass

    def _check_onboarding(self, user):
        prefs_ctrl = PreferencesController(user.id)
        if not prefs_ctrl.is_onboarding_complete():
            self._onboarding = OnboardingView(user, on_complete=self._on_onboarding_done)
            self._onboarding.setGeometry(self.rect())
            self._onboarding.show()

    def _on_onboarding_done(self, data):
        if hasattr(self, '_onboarding') and self._onboarding:
            self._onboarding.deleteLater()
            self._onboarding = None
        prefs_ctrl = PreferencesController(self.current_user.id)
        prefs_ctrl.complete_onboarding(goal=data.get("goal", ""), wake_time=data.get("wake_time", "07:00"))
        self._show_toast("Merci ! Digital Twin connaît mieux tes habitudes 🎯", "success", 4000)
        QTimer.singleShot(500, lambda: self._check_weekly_report())

    def _check_weekly_report(self):
        if date.today().weekday() != 0:
            return
        try:
            user_id = self.current_user.id
            session = get_session()
            from models.daily_log import DailyLog
            from models.study_session import StudySession
            from models.objective import Objective
            from models.journal import Journal
            today = date.today()
            week_ago = today - timedelta(days=7)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == user_id,
                DailyLog.date >= week_ago,
            ).all()
            checkins_count = len(logs)
            avg_score = round(sum(l.score_productivite for l in logs if l.score_productivite) / max(len(logs), 1))
            sessions_count = session.query(StudySession).filter(
                StudySession.utilisateur_id == user_id,
                StudySession.date_heure_debut >= week_ago,
            ).count()
            goals_count = session.query(Objective).filter(
                Objective.utilisateur_id == user_id,
                Objective.statut == "atteint",
                Objective.date_creation >= week_ago,
            ).count()
            journals_count = session.query(Journal).filter(
                Journal.utilisateur_id == user_id,
                Journal.date >= week_ago,
            ).count()
            session.close()
            self._weekly_report = WeeklyReportPopup({
                "avg_score": avg_score,
                "checkins": checkins_count,
                "sessions": sessions_count,
                "goals": goals_count,
                "journals": journals_count,
            }, on_close=lambda: setattr(self, '_weekly_report', None))
            self._weekly_report.setGeometry(self.rect())
            self._weekly_report.show()
        except Exception:
            pass

    def _show_toast(self, message, toast_type="error", duration=5000):
        parent = getattr(self, '_content_wrap', self)
        toast = ToastNotification(message, toast_type=toast_type, duration=duration, parent=parent)
        toast.setMinimumWidth(360)
        toast.move(parent.width() - 380, 8)
        toast.show()
        toast.raise_()

    def _toggle_ai_panel(self):
        self._ai_panel_visible = not self._ai_panel_visible
        self._ai_panel.setVisible(self._ai_panel_visible)
        self._ai_toggle_btn.setText("✕" if self._ai_panel_visible else "AI")

    def _navigate(self, page):
        if page == "logout":
            self.logout()
            return

        if page in self._pages:
            widget = self._pages[page]
            if hasattr(widget, "refresh"):
                widget.refresh()
            if hasattr(widget, "load_data"):
                widget.load_data()
            if hasattr(self, '_page_title'):
                self._fade_to(widget)
            self._update_page_title(page)
            if self._sidebar:
                self._sidebar.set_active(page)
            return

        view = self._create_page(page)
        if view is None:
            return
        self._pages[page] = view
        self._stack.addWidget(view)
        if hasattr(view, "load_data"):
            view.load_data()
        if hasattr(self, '_page_title'):
            self._fade_to(view)
        self._update_page_title(page)
        if self._sidebar:
            self._sidebar.set_active(page)

    def _generate_briefing(self, user_id: int) -> dict:
        try:
            from services.briefing_service import BriefingService
            svc = BriefingService(user_id)
            return svc.generate_briefing()
        except Exception:
            return {}

    def _fade_to(self, widget):
        if hasattr(self, '_fade_anim') and self._fade_anim:
            self._fade_anim.stop()
        self._fade_anim = QPropertyAnimation(widget, b"windowOpacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._stack.setCurrentWidget(widget)
        widget.setWindowOpacity(0.0)
        self._fade_anim.start()

    def _update_page_title(self, page):
        titles = {
            "home": "Accueil", "dashboard": "Tableau de bord", "checkin": "Check-in",
            "timer": "Timer", "stats": "Statistiques", "goals": "Objectifs",
            "journal": "Journal", "ai": "IA Chat", "profile": "Profil",
            "routine": "Routine", "search": "Recherche", "health": "Santé",
            "settings": "Paramètres",
            "briefing": "Briefing",
            "recommendations": "Recommandations",
            "analytics": "Analytics",
            "calendar": "Calendrier",
        }
        t = titles.get(page, page.capitalize())
        self._page_title.setText(t)

    def _check_session(self):
        session_mgr = SessionManager.get_instance()
        if session_mgr and session_mgr.is_expired():
            self.logout()
            self._show_toast("Session expirée — reconnecte-toi", "warning", 5000)

    def _create_page(self, page):
        u = self.current_user
        nav = self._navigate
        if page == "checkin":
            v = CheckinView(user=u, on_navigate=nav)
            v.checkin_done.connect(lambda: self._pages.get("dashboard", None) and self._pages["dashboard"].refresh())
            return v
        elif page == "timer":
            return TimerView(user=u, on_navigate=nav)
        elif page == "stats":
            return StatsView(user=u, on_navigate=nav)
        elif page == "goals":
            return GoalsView(user=u, on_navigate=nav)
        elif page == "journal":
            return JournalView(user=u, on_navigate=nav)
        elif page == "settings":
            return SettingsView(user=u, on_navigate=nav)
        elif page == "ai":
            return AIView(user=u, on_navigate=nav)
        elif page == "profile":
            return ProfileView(user=u, on_navigate=nav)
        elif page == "routine":
            return RoutineView(user=u, on_navigate=nav)
        elif page == "search":
            return SearchView(user=u, on_navigate=nav)
        elif page == "health":
            return HealthView(user=u, on_navigate=nav)
        elif page == "briefing":
            return BriefingView()
        elif page == "recommendations":
            return RecommendationsView(user_id=u.id)
        elif page == "analytics":
            return AnalyticsView(user=u, on_navigate=nav)
        elif page == "calendar":
            return CalendarView(user_id=u.id)
        return None

    def logout(self):
        session_mgr = SessionManager.get_instance()
        if session_mgr:
            session_mgr.end_session()
        self.current_user = None
        for key in list(self._pages.keys()):
            widget = self._pages.pop(key)
            self._stack.removeWidget(widget)
            widget.deleteLater()
        if self._sidebar:
            self._sidebar.deleteLater()
            self._sidebar = None
        if self._ai_panel:
            self._ai_panel.deleteLater()
            self._ai_panel = None
        if self._model_selector:
            self._model_selector.deleteLater()
            self._model_selector = None
        self._stack.addWidget(self.login_view)
        self._stack.setCurrentWidget(self.login_view)


def _global_excepthook(exc_type, exc_value, exc_tb):
    import traceback
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"Unhandled: {msg}", file=sys.stderr)

def main():
    sys.excepthook = _global_excepthook

    load_dotenv()

    ConfigService.initialize()
    LLMController.initialize()

    cfg = ConfigService.get_instance()

    gemini_key = cfg.get_gemini_api_key()
    if gemini_key:
        gemini_model = cfg.get_gemini_model() or "gemini-2.0-flash"
        try:
            GeminiService.initialize(gemini_key, gemini_model)
            print(f"Gemini AI configured with model {gemini_model}")
        except Exception as e:
            print(f"Gemini config error: {e}")
    else:
        print("Gemini AI not configured (no API key).")

    anthropic_key = cfg.get_anthropic_api_key()
    if anthropic_key:
        anthropic_model = cfg.get_anthropic_model() or "claude-sonnet-4-20250514"
        try:
            AnthropicService.initialize(anthropic_key, anthropic_model)
            print(f"Anthropic AI configured with model {anthropic_model}")
        except Exception as e:
            print(f"Anthropic config error: {e}")
    else:
        print("Anthropic AI not configured (no API key).")

    grok_key = cfg.get_xai_api_key()
    if grok_key:
        grok_model = cfg.get_xai_model() or "grok-2-1212"
        print(f"xAI Grok configured with model {grok_model}")
    else:
        print("xAI Grok not configured (no API key).")

    ModelManager.initialize()
    init_db()

    app = QApplication(sys.argv)
    app.setStyleSheet(Theme.stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
