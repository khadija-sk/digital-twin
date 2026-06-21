# controllers/timer_controller.py

import os
import json
import logging
from datetime import datetime, date
from models.database import get_session
from models.study_session import StudySession
from controllers.notification_controller import NotificationController
from controllers.preferences_controller import PreferencesController
from utils.sound_manager import SoundManager

class TimerController:

    def __init__(self, user_id):
        self.user_id = user_id
        self.is_running = False
        self.is_break = False
        self.work_duration = 25 * 60
        self.break_duration = 5 * 60
        self._load_config()
        self.time_left = self.work_duration
        self.session_start = None
        self.pomodoros_done = 0
        self.prefs = PreferencesController(user_id)

    def _load_config(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "pomodoro_config.json")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = json.load(f)
                self.work_duration = cfg.get("work", 25) * 60
                self.break_duration = cfg.get("break", 5) * 60
        except Exception as e:
            logging.getLogger(__name__).warning("Erreur lors du chargement de la configuration pomodoro")

    def start(self):
        if not self.is_running:
            self.is_running = True
            if not self.is_break:
                self.session_start = datetime.now()
            return True
        return False

    def pause(self):
        self.is_running = False

    def reset(self):
        if self.session_start and not self.is_break:
            elapsed = (datetime.now() - self.session_start).seconds // 60
            if elapsed > 0:
                self._save_session(elapsed, "abandonne")
        self.is_running = False
        self.is_break = False
        self.time_left = self.work_duration
        self.session_start = None

    def tick(self):
        if not self.is_running:
            return None
        self.time_left -= 1
        if self.time_left <= 0:
            if not self.is_break:
                self._save_session(self.work_duration // 60, "complete")
                self.pomodoros_done += 1
                if self.prefs.should_notif("pomodoro"):
                    NotificationController.pomodoro_done()
                if self.prefs.should_play_sound():
                    SoundManager.play_done()
                self.is_break = True
                self.time_left = self.break_duration
                return "work_done"
            else:
                if self.prefs.should_notif("pomodoro"):
                    NotificationController.break_done()
                if self.prefs.should_play_sound():
                    SoundManager.play_break_done()
                self.is_break = False
                self.time_left = self.work_duration
                self.is_running = False
                return "break_done"
        return None

    def _save_session(self, duree, statut):
        session = get_session()
        try:
            study_session = StudySession(
                utilisateur_id=self.user_id,
                date_heure_debut=self.session_start or datetime.now(),
                duree=duree,
                statut=statut
            )
            session.add(study_session)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur sauvegarde session : {e}")
        finally:
            session.close()

    def send_notification_start(self):
        if self.prefs.should_notif("pomodoro"):
            NotificationController.pomodoro_start()
        if self.prefs.should_play_sound():
            SoundManager.play_start()

    def get_time_string(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_progress(self):
        total = self.break_duration if self.is_break else self.work_duration
        return 1.0 - (self.time_left / total)

    def get_total_sessions(self):
        session = get_session()
        try:
            return session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete"
            ).count()
        finally:
            session.close()

    # 🔥 NOUVEAU : sessions d'aujourd'hui
    def get_today_sessions(self):
        session = get_session()
        try:
            today_start = datetime.combine(date.today(), datetime.min.time())
            return session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= today_start
            ).count()
        finally:
            session.close()