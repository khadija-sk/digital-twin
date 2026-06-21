# views/settings_view.py

import os
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QSpinBox, QMessageBox, QFileDialog, QSizePolicy, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from models.database import get_session
from models.user import User
from controllers.checkin_controller import CheckinController
from controllers.gamification_controller import GamificationController
from services.gemini_service import AIService as GeminiService
from services.anthropic_service import AnthropicService
from utils.csv_exporter import CSVExporter
from utils.pdf_exporter import PDFExporter
from utils.theme import Theme
from controllers.preferences_controller import PreferencesController
from models.database import DB_PATH
from controllers.llm_controller import LLMController
from services.config_service import ConfigService
from services.llm.provider_factory import ProviderFactory


class SettingsView(QWidget):

    def __init__(self, user, on_navigate=None):
        super().__init__()
        self.user        = user
        self.on_navigate = on_navigate
        self.checkin_ctrl = CheckinController(user.id)
        self.gami_ctrl    = GamificationController(user.id)
        self.prefs_ctrl = PreferencesController(user.id)

        self.setStyleSheet(self._get_style())
        self._build_ui()

    # ─── BUILD UI ────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setObjectName("content_area")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)  # 32, 28, 32, 32)
        cl.setSpacing(24)

        cl.addWidget(self._build_profile_section())
        cl.addWidget(self._build_ai_section())
        cl.addWidget(self._build_pomodoro_section())
        cl.addWidget(self._build_preferences_section())
        cl.addWidget(self._build_export_section())
        cl.addWidget(self._build_privacy_section())
        cl.addWidget(self._build_backup_section())
        cl.addWidget(self._build_danger_section())
        cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ─── TOPBAR ──────────────────────────────────────────────
    def _build_topbar(self):
        c = Theme.colors()
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(52)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 0, 24, 0)

        title = QLabel("Paramètres")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {c['TEXT_PRIMARY']};")
        layout.addWidget(title)
        layout.addStretch()
        return topbar

    # ─── SECTIONS ────────────────────────────────────────────
    def _build_profile_section(self):
        c = Theme.colors()
        card = self._section_card()
        layout = card.layout()

        layout.addWidget(self._section_header("ðŸ‘¤  Profil", "Modifie tes informations personnelles"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        top_row = QHBoxLayout()
        avatar = QLabel(self.user.nom[:2].upper())
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {c['SAKURA']}; color: {c['TEXT_PRIMARY']};
            border-radius: 28px; font-size: 20px; font-weight: bold;
        """)
        top_row.addWidget(avatar)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_big = QLabel(self.user.nom)
        name_big.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_big.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        info.addWidget(name_big)
        email_lbl = QLabel(self.user.email)
        email_lbl.setStyleSheet(f"color: {c['MILK_TEA']}; font-size: 12px; background: transparent;")
        info.addWidget(email_lbl)
        top_row.addLayout(info)
        top_row.addStretch()
        layout.addLayout(top_row)
        layout.addSpacing(16)

        layout.addWidget(self._field_label("Prénom"))
        self.input_nom = self._input(self.user.nom)
        layout.addWidget(self.input_nom)
        layout.addSpacing(12)

        layout.addWidget(self._field_label("Email"))
        self.input_email = self._input(self.user.email)
        layout.addWidget(self.input_email)
        layout.addSpacing(12)

        layout.addWidget(self._field_label("Nouveau mot de passe"))
        self.input_password = self._input("Laisser vide pour ne pas changer", password=True)
        layout.addWidget(self.input_password)
        layout.addSpacing(20)

        btn = self._primary_btn("Sauvegarder les modifications")
        btn.clicked.connect(self._handle_save_profile)
        layout.addWidget(btn)

        return card

    def _build_ai_section(self):
        c = Theme.colors()
        card = self._section_card()
        layout = card.layout()

        layout.addWidget(self._section_header("Intelligence Artificielle", "Configure l'assistant IA"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        ctrl = LLMController.get_instance()
        gemini_ok = GeminiService.is_available()
        anthropic_ok = AnthropicService.is_available()
        grok_ok = ctrl is not None and ctrl.grok_provider is not None
        ollama_ok = ctrl is not None and ctrl.ollama_provider is not None

        connected = []
        if gemini_ok: connected.append("Gemini")
        if anthropic_ok: connected.append("Anthropic")
        if grok_ok: connected.append("Grok")
        if ollama_ok: connected.append("Ollama")
        status_text = f"Connecté: {' + '.join(connected)}" if connected else "Non configuré"

        self.ai_status = QLabel(f"Status: {status_text}")
        self.ai_status.setStyleSheet(
            f"color: {c['SAKURA']}; "
            f"font-size: 13px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(self.ai_status)
        layout.addSpacing(12)

        # ── Fournisseur actif ──
        active_prov = ctrl.active_provider_name if ctrl else "ollama"
        layout.addWidget(self._field_label("Fournisseur actif"))
        prov_row = QHBoxLayout()
        prov_row.setSpacing(10)
        self.provider_buttons = {}
        for pid, pname in [("ollama", "Ollama"), ("gemini", "Gemini"), ("grok", "Grok"), ("anthropic", "Anthropic")]:
            if ctrl and ctrl._get_provider(pid) is not None:
                btn = self._toggle_btn(pname, active=(active_prov == pid))
                btn.clicked.connect(lambda checked, x=pid: self._set_active_provider(x))
                self.provider_buttons[pid] = btn
                prov_row.addWidget(btn)
        prov_row.addStretch()
        layout.addLayout(prov_row)
        layout.addSpacing(16)

        # ── Gemini ──
        gemini_title = QLabel("Google Gemini")
        gemini_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        gemini_title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(gemini_title)

        desc = QLabel(
            "Obtiens une clé gratuitement sur ai.google.dev."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(desc)
        layout.addSpacing(8)

        layout.addWidget(self._field_label("Clé API Google Gemini"))
        self.input_gemini_key = self._input(
            "Clé déjà configurée (laisser vide)" if gemini_ok else "Entrez votre clé API...",
            password=True
        )
        layout.addWidget(self.input_gemini_key)
        layout.addSpacing(12)

        # ── xAI Grok ──
        grok_title = QLabel("xAI Grok")
        grok_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        grok_title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(grok_title)

        grok_desc = QLabel(
            "Configure une clé API sur console.x.ai. "
            "Grok utilise l'API compatible OpenAI."
        )
        grok_desc.setWordWrap(True)
        grok_desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(grok_desc)
        layout.addSpacing(8)

        layout.addWidget(self._field_label("Clé API xAI Grok"))
        self.input_grok_key = self._input(
            "Clé déjà configurée (laisser vide)" if grok_ok else "xai-...",
            password=True
        )
        layout.addWidget(self.input_grok_key)
        layout.addSpacing(12)

        # ── Anthropic ──
        anthropic_title = QLabel("Anthropic Claude")
        anthropic_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        anthropic_title.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(anthropic_title)

        desc2 = QLabel(
            "Obtiens une clé sur console.anthropic.com."
        )
        desc2.setWordWrap(True)
        desc2.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(desc2)
        layout.addSpacing(8)

        layout.addWidget(self._field_label("Clé API Anthropic"))
        self.input_anthropic_key = self._input(
            "Clé déjà configurée (laisser vide)" if anthropic_ok else "sk-ant-...",
            password=True
        )
        layout.addWidget(self.input_anthropic_key)
        layout.addSpacing(20)

        btn = self._primary_btn("Sauvegarder la configuration IA")
        btn.clicked.connect(self._handle_save_ai_config)
        layout.addWidget(btn)

        return card

    def _build_pomodoro_section(self):
        c = Theme.colors()
        card = self._section_card()
        layout = card.layout()

        layout.addWidget(self._section_header("⏱️  Pomodoro", "Personnalise tes durées de travail et de pause"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(24)

        work_col = QVBoxLayout()
        work_col.setSpacing(6)
        work_col.addWidget(self._field_label("Durée de travail (minutes)"))
        self.spin_work = QSpinBox()
        self.spin_work.setMinimum(5)
        self.spin_work.setMaximum(90)
        self.spin_work.setValue(25)
        self.spin_work.setFixedHeight(42)
        self.spin_work.setObjectName("spin_box")
        work_col.addWidget(self.spin_work)
        row.addLayout(work_col)

        break_col = QVBoxLayout()
        break_col.setSpacing(6)
        break_col.addWidget(self._field_label("Durée de pause (minutes)"))
        self.spin_break = QSpinBox()
        self.spin_break.setMinimum(1)
        self.spin_break.setMaximum(30)
        self.spin_break.setValue(5)
        self.spin_break.setFixedHeight(42)
        self.spin_break.setObjectName("spin_box")
        break_col.addWidget(self.spin_break)
        row.addLayout(break_col)

        row.addStretch()
        layout.addLayout(row)
        layout.addSpacing(16)

        note = QLabel("ℹ️  Les modifications s'appliquent à la prochaine session démarrée.")
        note.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(note)
        layout.addSpacing(16)

        btn = self._primary_btn("Appliquer")
        btn.clicked.connect(self._handle_save_pomodoro)
        layout.addWidget(btn)

        return card

    def _build_preferences_section(self):
        c = Theme.colors()
        card = self._section_card()
        layout = card.layout()

        layout.addWidget(self._section_header("Préférences", "Personnalise l'application"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(12)

        prefs = self.prefs_ctrl.get_preferences()

        appearance_label = QLabel("Apparence")
        appearance_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        appearance_label.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(appearance_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(10)
        theme_lbl = QLabel("Thème")
        theme_lbl.setStyleSheet(f"color: {c['TEXT_SECONDARY']}; font-size: 12px; background: transparent;")
        theme_row.addWidget(theme_lbl)
        self.btn_theme_light = self._toggle_btn("Clair", active=(prefs.theme == "light"))
        self.btn_theme_dark = self._toggle_btn("Sombre", active=(prefs.theme == "dark"))
        self.btn_theme_light.clicked.connect(lambda: self._set_theme("light"))
        self.btn_theme_dark.clicked.connect(lambda: self._set_theme("dark"))
        theme_row.addWidget(self.btn_theme_light)
        theme_row.addWidget(self.btn_theme_dark)
        theme_row.addStretch()
        layout.addLayout(theme_row)
        layout.addSpacing(16)

        notif_label = QLabel("Notifications")
        notif_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        notif_label.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(notif_label)

        notif_label = QLabel("Notifications")
        notif_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        notif_label.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(notif_label)

        self.chk_notif_checkin = QCheckBox("Rappel de check-in quotidien")
        self.chk_notif_checkin.setChecked(prefs.notif_checkin)
        self.chk_notif_checkin.setObjectName("pref_checkbox")
        self.chk_notif_checkin.toggled.connect(lambda v: self.prefs_ctrl.set_notif("checkin", v))
        layout.addWidget(self.chk_notif_checkin)

        self.chk_notif_pomodoro = QCheckBox("Notifications Pomodoro (début/fin/pause)")
        self.chk_notif_pomodoro.setChecked(prefs.notif_pomodoro)
        self.chk_notif_pomodoro.setObjectName("pref_checkbox")
        self.chk_notif_pomodoro.toggled.connect(lambda v: self.prefs_ctrl.set_notif("pomodoro", v))
        layout.addWidget(self.chk_notif_pomodoro)

        self.chk_notif_badge = QCheckBox("Notifications de déblocage de badges")
        self.chk_notif_badge.setChecked(prefs.notif_badge)
        self.chk_notif_badge.setObjectName("pref_checkbox")
        self.chk_notif_badge.toggled.connect(lambda v: self.prefs_ctrl.set_notif("badge", v))
        layout.addWidget(self.chk_notif_badge)

        self.chk_notif_sound = QCheckBox("Sons (bip Pomodoro)")
        self.chk_notif_sound.setChecked(prefs.notif_sound)
        self.chk_notif_sound.setObjectName("pref_checkbox")
        self.chk_notif_sound.toggled.connect(lambda v: self.prefs_ctrl.set_notif("sound", v))
        layout.addWidget(self.chk_notif_sound)

        layout.addSpacing(8)
        note = QLabel("ðŸ’¡ Les notifications utilisent le système de notification de votre OS.")
        note.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 11px; background: transparent;")
        layout.addWidget(note)

        return card

    def _build_export_section(self):
        c = Theme.colors()
        card = self._section_card()
        layout = card.layout()

        layout.addWidget(self._section_header("ðŸ“¥  Exporter mes données", "Télécharge tes données en PDF ou CSV"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        format_row = QHBoxLayout()
        format_row.setSpacing(8)
        fmt_label = QLabel("Format :")
        fmt_label.setStyleSheet(f"color: {c['MILK_TEA']}; font-size: 12px; font-weight: bold; background: transparent;")
        format_row.addWidget(fmt_label)

        self.btn_fmt_pdf = self._toggle_btn("PDF", active=True)
        self.btn_fmt_csv = self._toggle_btn("CSV", active=False)
        self.btn_fmt_pdf.clicked.connect(lambda: self._set_export_format("pdf"))
        self.btn_fmt_csv.clicked.connect(lambda: self._set_export_format("csv"))
        format_row.addWidget(self.btn_fmt_pdf)
        format_row.addWidget(self.btn_fmt_csv)
        format_row.addStretch()
        self._export_format = "pdf"
        layout.addLayout(format_row)
        layout.addSpacing(12)

        desc = QLabel(
            "Exporte tes donnees au format PDF (tableaux propres, mise en forme professionnelle) "
            "ou CSV (compatible Excel, Google Sheets)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 12px; background: transparent;")
        layout.addWidget(desc)
        layout.addSpacing(12)

        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(10)
        btn_checkins = self._export_btn("Check-ins", "checkins")
        btn_sessions = self._export_btn("Sessions Pomodoro", "sessions")
        btn_journal  = self._export_btn("Journal", "journal")
        btn_row1.addWidget(btn_checkins)
        btn_row1.addWidget(btn_sessions)
        btn_row1.addWidget(btn_journal)
        btn_row1.addStretch()
        layout.addLayout(btn_row1)
        layout.addSpacing(8)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)
        btn_goals  = self._export_btn("Objectifs", "goals")
        btn_badges = self._export_btn("Badges", "badges")
        btn_report = self._export_btn("Rapport complet", "report")
        btn_row2.addWidget(btn_goals)
        btn_row2.addWidget(btn_badges)
        btn_row2.addWidget(btn_report)
        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        return card

    def _toggle_btn(self, label, active=False):
        btn = QPushButton(label)
        btn.setFixedHeight(30)
        btn.setFixedWidth(60)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("toggle_active" if active else "toggle_inactive")
        return btn

    def _set_export_format(self, fmt):
        self._export_format = fmt
        self.btn_fmt_pdf.setObjectName("toggle_active" if fmt == "pdf" else "toggle_inactive")
        self.btn_fmt_csv.setObjectName("toggle_active" if fmt == "csv" else "toggle_inactive")
        self.btn_fmt_pdf.setStyle(self.btn_fmt_pdf.style())
        self.btn_fmt_csv.setStyle(self.btn_fmt_csv.style())

    def _export_btn(self, label, data_type):
        btn = QPushButton(label)
        btn.setObjectName("btn_export")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._handle_export(data_type))
        return btn

    def _build_privacy_section(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("privacy_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(self._section_header("🔒  Vie privée", "Contrôle de tes données"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        btn_clear_memories = self._secondary_btn("Effacer les souvenirs IA")
        btn_clear_memories.clicked.connect(self._handle_clear_memories)
        layout.addWidget(btn_clear_memories)

        btn_clear_conversations = self._secondary_btn("Effacer l'historique des conversations")
        btn_clear_conversations.clicked.connect(self._handle_clear_conversations)
        layout.addWidget(btn_clear_conversations)

        btn_export_data = self._secondary_btn("Exporter toutes mes données")
        btn_export_data.clicked.connect(self._handle_export_all_data)
        layout.addWidget(btn_export_data)

        return card

    def _handle_clear_memories(self):
        reply = QMessageBox.question(
            self, "Effacer les souvenirs",
            "Tous les souvenirs de l'IA seront supprimés. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from services.memory_system import MemorySystem
            mem = MemorySystem(self.user.id)
            from models.database import get_session
            from models.extensions import MemoryEntry
            session = get_session()
            try:
                session.query(MemoryEntry).filter_by(utilisateur_id=self.user.id).delete()
                session.commit()
                QMessageBox.information(self, "Souvenirs effacés", "Tous les souvenirs ont été supprimés.")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", str(e))
            finally:
                session.close()

    def _handle_clear_conversations(self):
        reply = QMessageBox.question(
            self, "Effacer l'historique",
            "Toutes les conversations seront supprimées. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from services.conversation_manager import ConversationManager
            cm = ConversationManager.get_instance() if hasattr(ConversationManager, 'get_instance') else ConversationManager()
            cm.clear()
            QMessageBox.information(self, "Historique effacé", "Les conversations ont été supprimées.")

    def _handle_export_all_data(self):
        from datetime import datetime
        import os, json
        from PySide6.QtWidgets import QFileDialog
        from models.database import get_session
        from models.user import User
        from models.daily_log import DailyLog
        from models.journal import Journal
        from models.objective import Objective
        from models.study_session import StudySession
        from models.extensions import MemoryEntry

        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter toutes mes données",
            os.path.join(os.path.expanduser("~/Desktop"), f"digital_twin_data_{datetime.now().strftime('%Y%m%d')}.json"),
            "JSON Files (*.json)"
        )
        if not path:
            return

        session = get_session()
        try:
            user = session.query(User).filter_by(id=self.user.id).first()
            logs = session.query(DailyLog).filter_by(utilisateur_id=self.user.id).all()
            journals = session.query(Journal).filter_by(utilisateur_id=self.user.id).all()
            goals = session.query(Objective).filter_by(utilisateur_id=self.user.id).all()
            study_sessions = session.query(StudySession).filter_by(utilisateur_id=self.user.id).all()
            memories = session.query(MemoryEntry).filter_by(utilisateur_id=self.user.id).all()

            data = {
                "export_date": datetime.now().isoformat(),
                "user": {"name": user.nom, "email": user.email, "level": user.niveau} if user else {},
                "daily_logs": [{"date": str(l.date), "mood": l.humeur, "energy": l.energie, "sleep": l.sommeil, "score": l.score_productivite} for l in logs],
                "journals": [{"date": str(j.date), "content": j.contenu} for j in journals],
                "goals": [{"description": g.description, "status": g.statut, "created": str(g.date_creation)} for g in goals],
                "sessions": [{"date": str(s.date_heure_debut), "duration": s.duree} for s in study_sessions],
                "memories": [{"content": m.content, "category": m.category, "importance": m.importance, "date": str(m.created_at.date())} for m in memories],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exporté", f"Données exportées :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _secondary_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("btn_secondary")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _build_backup_section(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("privacy_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(self._section_header("💾  Sauvegarde & Restauration", "Protège et restaure tes données"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        desc = QLabel(
            "Sauvegarde l'intégralité de ta base de données (check-ins, sessions, objectifs, "
            "journal, souvenirs IA, etc.) ou restaure une sauvegarde précédente."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)
        layout.addSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(10)
        btn_backup = QPushButton("📤  Sauvegarder")
        btn_backup.setObjectName("btn_export")
        btn_backup.setFixedHeight(40)
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.clicked.connect(self._handle_backup)
        row.addWidget(btn_backup)

        btn_restore = QPushButton("📥  Restaurer")
        btn_restore.setObjectName("btn_export")
        btn_restore.setFixedHeight(40)
        btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore.clicked.connect(self._handle_restore)
        row.addWidget(btn_restore)

        row.addStretch()
        layout.addLayout(row)

        self._backup_info = QLabel(
            f"Base actuelle : {os.path.getsize(DB_PATH) / 1024:.0f} Ko"
        )
        self._backup_info.setStyleSheet(
            f"color: {c['MILK_TEA']}; font-size: 11px; background: transparent;"
        )
        layout.addWidget(self._backup_info)

        return card

    def _handle_backup(self):
        from datetime import datetime
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder la base de données",
            os.path.join(os.path.expanduser("~/Desktop"),
                         f"digital_twin_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"),
            "SQLite Database (*.db);;All Files (*)"
        )
        if not path:
            return
        try:
            import shutil
            shutil.copy2(DB_PATH, path)
            QMessageBox.information(self, "Sauvegarde réussie ✓",
                f"Base de données sauvegardée :\n{path}\n\n"
                f"Taille : {os.path.getsize(path) / 1024:.0f} Ko")
            self._backup_info.setText(
                f"Base actuelle : {os.path.getsize(DB_PATH) / 1024:.0f} Ko"
                f"  |  Dernière sauvegarde : {datetime.now().strftime('%H:%M')}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder :\n{e}")

    def _handle_restore(self):
        reply = QMessageBox.warning(
            self, "Restaurer une sauvegarde",
            "⚠️  La restauration va REMPLACER toutes les données actuelles "
            "par celles de la sauvegarde.\n\n"
            "L'application va se fermer après la restauration.\n\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir une sauvegarde",
            os.path.expanduser("~/Desktop"),
            "SQLite Database (*.db);;All Files (*)"
        )
        if not path:
            return
        try:
            import shutil
            shutil.copy2(path, DB_PATH)
            QMessageBox.information(self, "Restauration réussie ✓",
                "Base de données restaurée.\n\nL'application va maintenant se fermer "
                "pour appliquer les changements.")
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de restaurer :\n{e}")

    def _build_danger_section(self):
        c = Theme.colors()
        card = QFrame()
        card.setObjectName("danger_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(self._section_header("⚠️  Zone dangereuse", "Actions irréversibles"))
        layout.addWidget(self._h_sep_light())
        layout.addSpacing(8)

        desc = QLabel(
            "Réinitialise toutes tes données (check-ins, sessions, badges, objectifs, journal). "
            "Cette action est permanente et ne peut pas être annulée."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['TEXT_MUTED']}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)
        layout.addSpacing(12)

        btn = QPushButton("Réinitialiser toutes mes données")
        btn.setObjectName("btn_danger")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._handle_reset_data)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    # ─── HANDLERS ────────────────────────────────────────────

    def _set_active_provider(self, provider_name: str):
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.set_active_provider(provider_name):
            for pid, btn in self.provider_buttons.items():
                active = (pid == provider_name)
                btn.setObjectName("toggle_active" if active else "toggle_inactive")
                btn.setStyleSheet(self._get_style())
            QMessageBox.information(self, "Fournisseur changé",
                f"Fournisseur actif : {ProviderFactory.get_provider_display_name(provider_name)}\n\n"
                "Les nouvelles conversations utiliseront ce modèle.")
            self._update_ai_status()

    def _update_ai_status(self):
        ctrl = LLMController.get_instance()
        gemini_ok = GeminiService.is_available()
        anthropic_ok = AnthropicService.is_available()
        grok_ok = ctrl is not None and ctrl.grok_provider is not None
        ollama_ok = ctrl is not None and ctrl.ollama_provider is not None
        connected = []
        if gemini_ok: connected.append("Gemini")
        if anthropic_ok: connected.append("Anthropic")
        if grok_ok: connected.append("Grok")
        if ollama_ok: connected.append("Ollama")
        status = f"Connecté: {' + '.join(connected)}" if connected else "Non configuré"
        if ctrl:
            status += f" | Actif: {ProviderFactory.get_provider_display_name(ctrl.active_provider_name)}"
        self.ai_status.setText(f"Status: {status}")

    def _handle_save_ai_config(self):
        gemini_key = self.input_gemini_key.text().strip()
        anthropic_key = self.input_anthropic_key.text().strip()
        grok_key = self.input_grok_key.text().strip()
        cfg = ConfigService.get_instance()
        ctrl = LLMController.get_instance()
        saved_any = False

        if gemini_key:
            try:
                model = cfg.get_gemini_model()
                if ctrl:
                    ctrl.configure(gemini_key, model)
                GeminiService.initialize(gemini_key, model)
                saved_any = True
                self.input_gemini_key.clear()
                self.input_gemini_key.setPlaceholderText("Clé déjà configurée (laisser vide)")
            except Exception as e:
                QMessageBox.critical(self, "Erreur Gemini", str(e))

        if anthropic_key:
            try:
                model = cfg.get_anthropic_model()
                if ctrl:
                    ctrl.configure_anthropic(anthropic_key, model)
                AnthropicService.initialize(anthropic_key, model)
                saved_any = True
                self.input_anthropic_key.clear()
                self.input_anthropic_key.setPlaceholderText("Clé déjà configurée (laisser vide)")
            except Exception as e:
                QMessageBox.critical(self, "Erreur Anthropic", str(e))

        if grok_key:
            try:
                model = cfg.get_xai_model()
                if ctrl:
                    ctrl.configure_grok(grok_key, model)
                saved_any = True
                self.input_grok_key.clear()
                self.input_grok_key.setPlaceholderText("Clé déjà configurée (laisser vide)")
            except Exception as e:
                QMessageBox.critical(self, "Erreur xAI Grok", str(e))

        self._update_ai_status()
        self.ai_status.setStyleSheet(f"color: {Theme.colors()['SAKURA']}; font-size: 13px; font-weight: bold; background: transparent;")

        if saved_any:
            QMessageBox.information(
                self, "Sauvegardé ✓",
                "Configuration IA mise à jour avec succès !\n\n"
                "Note : Les clés API sont stockées en texte clair dans le fichier .env.\n"
                "Assurez-vous que personne d'autre n'a accès à votre ordinateur."
            )
        else:
            QMessageBox.information(self, "Aucun changement", "Aucune nouvelle clé fournie. La configuration existante est conservée.")

    def _handle_save_profile(self):
        nom   = self.input_nom.text().strip()
        email = self.input_email.text().strip()
        pwd   = self.input_password.text()

        if not nom or not email:
            QMessageBox.warning(self, "Champs manquants", "Nom et email sont obligatoires.")
            return

        session = get_session()
        try:
            user = session.query(User).filter_by(id=self.user.id).first()
            if not user:
                return

            if email != self.user.email:
                existing = session.query(User).filter_by(email=email).first()
                if existing:
                    QMessageBox.warning(self, "Email déjà utilisé", "Cet email est déjà associé à un autre compte.")
                    return

            user.nom   = nom
            user.email = email

            if pwd:
                if len(pwd) < 6:
                    QMessageBox.warning(self, "Mot de passe trop court", "Au moins 6 caractères.")
                    return
                import bcrypt
                user.password_hash = bcrypt.hashpw(
                    pwd.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

            session.commit()

            self.user.nom   = nom
            self.user.email = email

            self.input_password.clear()
            QMessageBox.information(self, "Sauvegardé ✓", "Profil mis à jour avec succès !")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _handle_save_pomodoro(self):
        work  = self.spin_work.value()
        brk   = self.spin_break.value()
        import json
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pomodoro_config.json"
        )
        with open(config_path, "w") as f:
            json.dump({"work": work, "break": brk}, f)
        QMessageBox.information(
            self, "Sauvegardé ✓",
            f"Durée de travail : {work} min\nDurée de pause : {brk} min\n\nActif à la prochaine session."
        )

    def _handle_export(self, data_type):
        ext = "pdf" if self._export_format == "pdf" else "csv"
        filters = {
            "pdf": "PDF Files (*.pdf)",
            "csv": "CSV Files (*.csv)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier",
            os.path.join(os.path.expanduser("~/Desktop"), f"digital_twin_{data_type}_{date.today()}.{ext}"),
            f"{filters[ext]};;All Files (*)"
        )
        if not path:
            return

        try:
            session = get_session()
            user_name = self.user.nom
            if data_type == "checkins":
                logs = self.checkin_ctrl.get_all_logs()
                if self._export_format == "pdf":
                    PDFExporter.export_checkins(logs, path, user_name)
                else:
                    CSVExporter.export_checkins(logs, path)
            elif data_type == "sessions":
                from models.study_session import StudySession
                sessions = session.query(StudySession).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(StudySession.date_heure_debut.asc()).all()
                if self._export_format == "pdf":
                    PDFExporter.export_sessions(sessions, path, user_name)
                else:
                    CSVExporter.export_sessions(sessions, path)
            elif data_type == "journal":
                from models.journal import Journal
                entries = session.query(Journal).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Journal.date.desc()).all()
                if self._export_format == "pdf":
                    PDFExporter.export_journal(entries, path, user_name)
                else:
                    CSVExporter.export_journal(entries, path)
            elif data_type == "goals":
                from models.objective import Objective
                goals = session.query(Objective).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Objective.date_creation.desc()).all()
                if self._export_format == "pdf":
                    PDFExporter.export_goals(goals, path, user_name)
                else:
                    CSVExporter.export_goals(goals, path)
            elif data_type == "badges":
                from models.badge import Badge
                badges = session.query(Badge).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Badge.date_obtention.desc()).all()
                if self._export_format == "pdf":
                    PDFExporter.export_badges(badges, path, user_name)
                else:
                    CSVExporter.export_badges(badges, path)
            elif data_type == "report":
                from models.journal import Journal
                from models.objective import Objective
                from models.badge import Badge
                from models.study_session import StudySession
                checkins = self.checkin_ctrl.get_all_logs()
                sessions = session.query(StudySession).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(StudySession.date_heure_debut.desc()).all()
                journals = session.query(Journal).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Journal.date.desc()).all()
                goals = session.query(Objective).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Objective.date_creation.desc()).all()
                badges = session.query(Badge).filter_by(
                    utilisateur_id=self.user.id
                ).order_by(Badge.date_obtention.desc()).all()
                if self._export_format == "pdf":
                    PDFExporter.export_report(
                        path, user_name=user_name,
                        checkins=checkins, sessions=sessions,
                        journals=journals, goals=goals, badges=badges,
                    )
                else:
                    CSVExporter.export_checkins(checkins, path.replace(".csv", "_checkins.csv"))
                    CSVExporter.export_sessions(sessions, path.replace(".csv", "_sessions.csv"))
                    CSVExporter.export_journal(journals, path.replace(".csv", "_journal.csv"))
                    CSVExporter.export_goals(goals, path.replace(".csv", "_goals.csv"))
                    CSVExporter.export_badges(badges, path.replace(".csv", "_badges.csv"))
                    QMessageBox.information(self, "Exporté ✓",
                        "Plusieurs fichiers CSV ont été créés dans le même dossier.")
                    session.close()
                    return
            session.close()
            QMessageBox.information(self, "Exporté ✓", f"Fichier sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            try:
                session.close()
            except Exception:
                pass

    def _handle_reset_data(self):
        confirm = QMessageBox.question(
            self, "Confirmer la réinitialisation",
            "⚠️  Tu es sur le point de supprimer TOUTES tes données.\n\n"
            "Check-ins, sessions Pomodoro, badges, objectifs et journal seront effacés.\n\n"
            "Cette action est irréversible. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        session = get_session()
        try:
            from models.daily_log import DailyLog
            from models.study_session import StudySession
            from models.badge import Badge
            from models.objective import Objective
            from models.journal import Journal

            for model in [DailyLog, StudySession, Badge, Objective, Journal]:
                session.query(model).filter_by(utilisateur_id=self.user.id).delete()

            user = session.query(User).filter_by(id=self.user.id).first()
            if user:
                user.xp_total = 0
                user.niveau   = 1

            session.commit()
            QMessageBox.information(self, "Réinitialisé", "Toutes tes données ont été supprimées.")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _set_theme(self, theme):
        self.prefs_ctrl.set_theme(theme)
        Theme.set_palette(theme)
        self.btn_theme_light.setObjectName("toggle_active" if theme == "light" else "toggle_inactive")
        self.btn_theme_dark.setObjectName("toggle_active" if theme == "dark" else "toggle_inactive")
        self.btn_theme_light.setStyle(self.btn_theme_light.style())
        self.btn_theme_dark.setStyle(self.btn_theme_dark.style())
        window = self.window()
        if window and hasattr(window, '_on_theme_changed'):
            window._on_theme_changed()

    # ─── UI HELPERS ──────────────────────────────────────────
    def _section_card(self):
        card = QFrame()
        card.setObjectName("section_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)  # 24, 20, 24, 20)
        layout.setSpacing(10)
        return card

    def _section_header(self, title, subtitle):
        c = Theme.colors()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)  # 0, 0, 0, 0)
        layout.setSpacing(2)

        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {c['TEXT_PRIMARY']}; background: transparent;")
        layout.addWidget(t)

        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {c['MILK_TEA']}; font-size: 12px; background: transparent;")
        layout.addWidget(s)
        return w

    def _field_label(self, text):
        c = Theme.colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {c['MILK_TEA']}; font-size: 11px; font-weight: bold; "
            "letter-spacing: 0.4px; background: transparent;"
        )
        return lbl

    def _input(self, placeholder, password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(44)
        inp.setObjectName("input_field")
        if password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        return inp

    def _primary_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(46)
        btn.setObjectName("btn_primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _h_sep_light(self):
        c = Theme.colors()
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['DIVIDER']};")
        return sep

    def refresh(self):
        if hasattr(self, "ai_status"):
            self._update_ai_status()
            self.ai_status.setStyleSheet(
                f"color: {Theme.colors()['SAKURA']}; "
                f"font-size: 13px; font-weight: bold; background: transparent;"
            )

    # --- STYLE ---
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
                border-bottom: 0.5px solid {c['TOPBAR_BORDER']};
            }}
            QWidget#content_area {{
                background-color: {c['BG']};
            }}
            QFrame#section_card {{
                background: {c['CARD_BG']};
                border-radius: 14px;
                border: 0.5px solid {c['CARD_BORDER']};
            }}
            QFrame#danger_card {{
                background: {c['CARD_BG']};
                border-radius: 14px;
                border: 0.5px solid {c['SAKURA']}4D;
            }}
            QLineEdit#input_field {{
                background: {c['INPUT_BG']};
                border: none;
                border-bottom: 1.5px solid {c['CARD_BORDER']};
                padding: 0 8px;
                font-size: 14px;
                color: {c['TEXT_PRIMARY']};
                border-radius: 0px;
            }}
            QLineEdit#input_field:focus {{
                border-bottom: 2px solid {c['SAKURA']};
                background: {c['INPUT_BG']};
            }}
            QSpinBox#spin_box {{
                background: {c['INPUT_BG']};
                border: 1.5px solid {c['CARD_BORDER']};
                border-radius: 8px;
                padding: 0 10px;
                font-size: 15px;
                font-weight: bold;
                color: {c['TEXT_PRIMARY']};
            }}
            QSpinBox#spin_box:focus {{
                border-color: {c['SAKURA']};
            }}
            QSpinBox#spin_box::up-button, QSpinBox#spin_box::down-button {{
                width: 24px;
                border: none;
                background: transparent;
            }}
            QPushButton#btn_primary {{
                background-color: {c['BG']};
                color: {c['TEXT_PRIMARY']};
                border: none;
                border-radius: 23px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#btn_primary:hover {{
                background-color: {c['SAKURA']};
            }}
            QPushButton#btn_secondary {{
                background-color: transparent;
                color: {c['TEXT_PRIMARY']};
                border: 1.5px solid {c['TEXT_MUTED']};
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#btn_secondary:hover {{
                border-color: {c['SAKURA']};
                color: {c['SAKURA']};
            }}
            QPushButton#btn_danger {{
                background-color: transparent;
                color: {c['SAKURA']};
                border: 1.5px solid {c['SAKURA']}4D;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton#btn_danger:hover {{
                background-color: {c['SAKURA']}12;
                border-color: {c['SAKURA']};
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
                border: 1px solid {c['CARD_BORDER']};
                border-radius: 15px;
                font-size: 11px;
            }}
            QPushButton#toggle_inactive:hover {{
                border-color: {c['SAKURA']};
                color: {c['TEXT_PRIMARY']};
            }}
            QPushButton#btn_export {{
                background: transparent;
                color: {c['TEXT_PRIMARY']};
                border: 1.5px solid {c['TEXT_MUTED']};
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 18px;
            }}
            QPushButton#btn_export:hover {{
                border-color: {c['SAKURA']};
                color: {c['SAKURA']};
                background: {c['SAKURA']}12;
            }}
            QCheckBox#pref_checkbox {{
                spacing: 8px;
                font-size: 13px;
                color: {c['TEXT_PRIMARY']};
                padding: 6px 0;
                background: transparent;
            }}
            QCheckBox#pref_checkbox::indicator {{
                width: 18px;
                height: 18px;
                border: 1.5px solid {c['CARD_BORDER']};
                border-radius: 4px;
                background: {c['INPUT_BG']};
            }}
            QCheckBox#pref_checkbox::indicator:checked {{
                background: {c['SAKURA']};
                border-color: {c['SAKURA']};
            }}
            QFrame#privacy_card {{
                background: {c['BG_SECONDARY']};
                border-radius: 14px;
                border: 1px solid {c['CARD_BORDER']};
            }}
            QPushButton#btn_secondary {{
                background: transparent;
                color: {c['TEXT_PRIMARY']};
                border: 1.5px solid {c['TEXT_MUTED']};
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 18px;
            }}
            QPushButton#btn_secondary:hover {{
                border-color: {c['SAKURA']};
                color: {c['SAKURA']};
            }}
        """
