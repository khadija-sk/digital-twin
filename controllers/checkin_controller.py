# controllers/checkin_controller.py

from datetime import date, timedelta
from models.database import get_session
from models.daily_log import DailyLog
from utils.cache import get_insight_cache

class CheckinController:

    def __init__(self, user_id):
        self.user_id = user_id

    def save_checkin(self, humeur, energie, sommeil):
        session = get_session()
        try:
            existing = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id, date=date.today()
            ).first()
            if existing:
                return False, "Tu as déjà fait ton check-in aujourd'hui !"
            score = self._calculate_score(humeur, energie, sommeil)
            log = DailyLog(
                utilisateur_id=self.user_id,
                date=date.today(),
                humeur=humeur,
                energie=energie,
                sommeil=sommeil,
                score_productivite=score
            )
            session.add(log)
            session.commit()
            from controllers.gamification_controller import GamificationController
            gami = GamificationController(self.user_id)
            gami.reward_checkin()
            streak = self.get_current_streak()
            total_checkins = session.query(DailyLog).filter_by(utilisateur_id=self.user_id).count()
            total_sessions = gami.get_total_sessions()
            gami.check_and_unlock_badges(streak, total_sessions, total_checkins)
            session.refresh(log)
            return True, log
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    def has_checkin_today(self):
        session = get_session()
        try:
            log = session.query(DailyLog).filter_by(utilisateur_id=self.user_id, date=date.today()).first()
            return log is not None
        finally:
            session.close()

    def get_today_checkin(self):
        session = get_session()
        try:
            return session.query(DailyLog).filter_by(utilisateur_id=self.user_id, date=date.today()).first()
        finally:
            session.close()

    def get_last_7_days(self):
        session = get_session()
        try:
            seven_days_ago = date.today() - timedelta(days=7)
            return session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= seven_days_ago
            ).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def get_last_30_days(self):
        cache = get_insight_cache(self.user_id)
        cached_val = cache.get("last_30_days")
        if cached_val is not None:
            return cached_val
        session = get_session()
        try:
            thirty_days_ago = date.today() - timedelta(days=30)
            result = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= thirty_days_ago
            ).order_by(DailyLog.date.asc()).all()
            cache.set("last_30_days", result)
            return result
        finally:
            session.close()

    def invalidate_cache(self):
        cache = get_insight_cache(self.user_id)
        cache.invalidate()

    def get_all_logs(self):
        session = get_session()
        try:
            return session.query(DailyLog).filter_by(utilisateur_id=self.user_id).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def _calculate_score(self, humeur, energie, sommeil):
        sommeil_score = min(sommeil / 8.0, 1.0) * 100
        humeur_score = (humeur - 1) / 4.0 * 100
        energie_score = (energie - 1) / 4.0 * 100
        score = (sommeil_score * 0.4) + (humeur_score * 0.3) + (energie_score * 0.3)
        return round(score)

    def detect_burnout(self):
        session = get_session()
        try:
            logs = session.query(DailyLog).filter_by(utilisateur_id=self.user_id).order_by(DailyLog.date.desc()).limit(3).all()
            if len(logs) < 3:
                return False
            if logs[0].energie < logs[1].energie < logs[2].energie:
                return True
            return False
        finally:
            session.close()

    def get_current_streak(self):
        session = get_session()
        try:
            logs = session.query(DailyLog).filter_by(utilisateur_id=self.user_id).order_by(DailyLog.date.desc()).limit(31).all()
            if not logs:
                return 0
            streak = 0
            check_date = date.today()
            for log in logs:
                if log.date == check_date:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
            return streak
        finally:
            session.close()