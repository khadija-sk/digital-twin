# controllers/goals_controller.py

from datetime import date
from models.database import get_session
from models.objective import Objective
from models.daily_log import DailyLog
from models.study_session import StudySession

class GoalsController:

    def __init__(self, user_id):
        self.user_id = user_id

    def create_goal(self, description, valeur_cible, unite):
        session = get_session()
        try:
            goal = Objective(
                utilisateur_id=self.user_id,
                description=description,
                valeur_cible=valeur_cible,
                unite=unite,
                date_creation=date.today(),
                statut="actif"
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return True, goal
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def get_active_goals(self):
        session = get_session()
        try:
            return session.query(Objective).filter_by(utilisateur_id=self.user_id, statut="actif").order_by(Objective.date_creation.desc()).all()
        finally:
            session.close()

    def get_all_goals(self):
        session = get_session()
        try:
            return session.query(Objective).filter_by(utilisateur_id=self.user_id).order_by(Objective.date_creation.desc()).all()
        finally:
            session.close()

    def delete_goal(self, goal_id):
        session = get_session()
        try:
            goal = session.query(Objective).filter_by(id=goal_id, utilisateur_id=self.user_id).first()
            if goal:
                session.delete(goal)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def mark_active(self, goal_id):
        session = get_session()
        try:
            goal = session.query(Objective).filter_by(id=goal_id, utilisateur_id=self.user_id).first()
            if goal:
                goal.statut = "actif"
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def mark_achieved(self, goal_id):
        session = get_session()
        try:
            goal = session.query(Objective).filter_by(id=goal_id, utilisateur_id=self.user_id).first()
            if goal:
                goal.statut = "atteint"
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def get_progress(self, goal):
        today_log = self._get_today_log()
        today_sessions = self._get_today_sessions()
        unite = goal.unite.lower() if goal.unite else ""
        if "sommeil" in goal.description.lower() or (unite == "heures" and "pomodoro" not in goal.description.lower()):
            current = today_log.sommeil if today_log else 0
        elif "humeur" in goal.description.lower():
            current = today_log.humeur if today_log else 0
        elif "energie" in goal.description.lower():
            current = today_log.energie if today_log else 0
        elif "pomodoro" in goal.description.lower() or "session" in goal.description.lower():
            current = today_sessions
        elif "score" in goal.description.lower():
            current = today_log.score_productivite if today_log else 0
        else:
            current = 0
        percentage = min(int((current / goal.valeur_cible) * 100), 100) if goal.valeur_cible > 0 else 0
        return current, percentage

    def _get_today_log(self):
        session = get_session()
        try:
            return session.query(DailyLog).filter_by(utilisateur_id=self.user_id, date=date.today()).first()
        finally:
            session.close()

    def _get_today_sessions(self):
        session = get_session()
        try:
            from datetime import datetime
            today_start = datetime.combine(date.today(), datetime.min.time())
            return session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= today_start
            ).count()
        finally:
            session.close()