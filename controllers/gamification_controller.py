# controllers/gamification_controller.py

from datetime import date
from models.database import get_session
from models.user import User
from models.badge import Badge
from models.study_session import StudySession
from models.daily_log import DailyLog

class GamificationController:

    def __init__(self, user_id):
        self.user_id = user_id

    def add_xp(self, amount):
        session = get_session()
        try:
            user = session.query(User).filter_by(id=self.user_id).first()
            if not user:
                return
            user.xp_total += amount
            user.niveau = self._calculate_level(user.xp_total)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur add_xp : {e}")
        finally:
            session.close()

    def _calculate_level(self, xp):
        if xp >= 1000: return 5
        elif xp >= 600: return 4
        elif xp >= 300: return 3
        elif xp >= 100: return 2
        else: return 1

    def _add_xp_in_session(self, session, amount):
        user = session.query(User).filter_by(id=self.user_id).first()
        if not user:
            return
        user.xp_total += amount
        user.niveau = self._calculate_level(user.xp_total)

    def unlock_badge(self, nom, description, xp_gagne, icone="🏆"):
        session = get_session()
        try:
            existing = session.query(Badge).filter_by(utilisateur_id=self.user_id, nom=nom).first()
            if existing:
                return False
            badge = Badge(
                utilisateur_id=self.user_id,
                nom=nom,
                description=description,
                date_obtention=date.today(),
                xp_gagne=xp_gagne,
                icone=icone
            )
            session.add(badge)
            self._add_xp_in_session(session, xp_gagne)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Erreur unlock_badge : {e}")
            return False
        finally:
            session.close()

    def check_and_unlock_badges(self, streak, total_sessions, total_checkins):
        unlocked = []
        # Badges Check-in
        if total_checkins >= 1:
            if self.unlock_badge("Premier check-in", "Tu as fait ton premier check-in !", 10, "✨"):
                unlocked.append("Premier check-in ✨")
        if total_checkins >= 7:
            if self.unlock_badge("Check-in régulier", "7 check-ins complétés !", 25, "📋"):
                unlocked.append("Check-in régulier 📋")
        if total_checkins >= 30:
            if self.unlock_badge("Check-in expert", "30 check-ins complétés !", 100, "🌟"):
                unlocked.append("Check-in expert 🌟")
        # Streak
        if streak >= 3:
            if self.unlock_badge("Streak 3 jours", "3 jours consécutifs de check-in !", 20, "🔥"):
                unlocked.append("Streak 3 jours 🔥")
        if streak >= 7:
            if self.unlock_badge("Streak 7 jours", "Une semaine complète sans interruption !", 50, "💫"):
                unlocked.append("Streak 7 jours 💫")
        if streak >= 30:
            if self.unlock_badge("Streak 30 jours", "Un mois de régularité — impressionnant !", 200, "👑"):
                unlocked.append("Streak 30 jours 👑")
        # Pomodoro
        if total_sessions >= 1:
            if self.unlock_badge("Première session", "Ta première session Pomodoro complétée !", 10, "⏱️"):
                unlocked.append("Première session ⏱️")
        if total_sessions >= 10:
            if self.unlock_badge("10 Pomodoros", "10 sessions de travail complétées !", 40, "🍅"):
                unlocked.append("10 Pomodoros 🍅")
        if total_sessions >= 50:
            if self.unlock_badge("50 Pomodoros", "50 sessions — tu es une machine !", 150, "🚀"):
                unlocked.append("50 Pomodoros 🚀")
        return unlocked

    def reward_checkin(self):
        self.add_xp(10)

    def reward_pomodoro(self):
        self.add_xp(15)

    def get_all_badges(self):
        session = get_session()
        try:
            return session.query(Badge).filter_by(utilisateur_id=self.user_id).order_by(Badge.date_obtention.desc()).all()
        finally:
            session.close()

    def get_xp_for_next_level(self):
        session = get_session()
        try:
            user = session.query(User).filter_by(id=self.user_id).first()
            if not user:
                return 0, 100, 1
            xp = user.xp_total
            niveau = user.niveau
            thresholds = {1: 100, 2: 300, 3: 600, 4: 1000, 5: 9999}
            xp_next = thresholds.get(niveau, 9999)
            return xp, xp_next, niveau
        finally:
            session.close()

    def get_total_checkins(self):
        session = get_session()
        try:
            return session.query(DailyLog).filter_by(utilisateur_id=self.user_id).count()
        finally:
            session.close()

    def get_total_sessions(self):
        session = get_session()
        try:
            return session.query(StudySession).filter_by(utilisateur_id=self.user_id, statut="complete").count()
        finally:
            session.close()