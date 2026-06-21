import logging
from datetime import date, timedelta, datetime
from typing import Optional
from models.database import get_session
from models.objective import Objective
from models.daily_log import DailyLog
from models.study_session import StudySession
from controllers.llm_controller import LLMController

logger = logging.getLogger(__name__)


class SmartGoalsService:

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._llm = LLMController.get_instance()

    def get_goals_with_insights(self) -> list[dict]:
        session = get_session()
        try:
            goals = session.query(Objective).filter_by(
                utilisateur_id=self.user_id
            ).order_by(Objective.date_creation.desc()).all()
            results = []
            for g in goals:
                progress = self._compute_progress(g, session)
                results.append({
                    "id": g.id,
                    "description": g.description,
                    "target": g.valeur_cible,
                    "unit": g.unite or "",
                    "status": g.statut,
                    "created": str(g.date_creation),
                    "progress_pct": progress["pct"],
                    "current": progress["current"],
                    "days_since_creation": (date.today() - g.date_creation).days,
                    "is_inactive": self._is_inactive(g, session),
                    "next_action": self._suggest_next_action(g, progress["pct"]),
                    "estimated_completion": self._estimate_completion(g, progress),
                })
            return results
        finally:
            session.close()

    def _compute_progress(self, goal: Objective, session) -> dict:
        current = self._get_current_value(goal, session)
        target = goal.valeur_cible or 1
        pct = min(int((current / target) * 100), 100) if target > 0 else 0
        return {"current": current, "pct": pct}

    def _get_current_value(self, goal: Objective, session) -> float:
        desc = goal.description.lower() if goal.description else ""
        today_log = session.query(DailyLog).filter_by(
            utilisateur_id=self.user_id, date=date.today()
        ).first()
        if "sommeil" in desc:
            return today_log.sommeil if today_log else 0
        if "humeur" in desc:
            return today_log.humeur if today_log else 0
        if "energie" in desc or "énergie" in desc:
            return today_log.energie if today_log else 0
        if "pomodoro" in desc or "session" in desc:
            today_start = datetime.combine(date.today(), datetime.min.time())
            return session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= today_start,
            ).count()
        if "score" in desc:
            return today_log.score_productivite if today_log else 0
        return 0

    def _is_inactive(self, goal: Objective, session) -> bool:
        if goal.statut == "atteint":
            return False
        if not goal.date_creation:
            return True
        days_since = (date.today() - goal.date_creation).days
        if days_since < 7:
            return False
        logs = session.query(DailyLog).filter_by(
            utilisateur_id=self.user_id
        ).order_by(DailyLog.date.desc()).limit(7).all()
        for log in logs:
            desc = goal.description.lower() if goal.description else ""
            if "sommeil" in desc and log.sommeil is not None:
                return False
            if "humeur" in desc and log.humeur is not None:
                return False
            if "energie" in desc and log.energie is not None:
                return False
            if "score" in desc and log.score_productivite is not None:
                return False
        return days_since > 14

    def _suggest_next_action(self, goal: Objective, pct: int) -> str:
        if pct >= 100:
            return "Objectif atteint ! Célèbre cette victoire."
        if pct >= 75:
            return "Plus que quelques efforts. Continue !"
        if pct >= 50:
            return "Bonne progression. Maintiens le rythme."
        if pct >= 25:
            return "Bon début. Focus sur la régularité."
        if goal.statut == "actif" and pct == 0:
            return "Ajoute des check-ins quotidiens pour suivre ce goal."
        return "Petits pas chaque jour. Commence maintenant."

    def _estimate_completion(self, goal: Objective, progress: dict) -> Optional[str]:
        if progress["pct"] >= 100:
            return "Déjà complété"
        if progress["pct"] == 0:
            return None
        needed = 100 - progress["pct"]
        if progress["current"] == 0:
            return None
        days_at_current_rate = max(1, needed / progress["pct"]) * max(
            1, (date.today() - goal.date_creation).days
        )
        estimated = date.today() + timedelta(days=int(days_at_current_rate))
        return str(estimated)

    def celebrate_milestone(self, goal_id: int) -> Optional[str]:
        session = get_session()
        try:
            goal = session.query(Objective).filter_by(id=goal_id).first()
            if not goal:
                return None
            progress = self._compute_progress(goal, session)
            if progress["pct"] >= 100 and goal.statut == "actif":
                goal.statut = "atteint"
                session.commit()
                return f"Félicitations ! Tu as atteint ton objectif : {goal.description}"
            if progress["pct"] >= 50 and progress["pct"] < 100:
                return f"Belle progression sur '{goal.description}' — tu es à {progress['pct']}% !"
            return None
        finally:
            session.close()

    def get_inactive_goals(self) -> list[dict]:
        return [g for g in self.get_goals_with_insights() if g["is_inactive"]]

    def get_summary_stats(self) -> dict:
        insights = self.get_goals_with_insights()
        active = [g for g in insights if g["status"] == "actif"]
        achieved = [g for g in insights if g["status"] == "atteint"]
        inactive = [g for g in insights if g["is_inactive"]]
        avg_progress = (
            sum(g["progress_pct"] for g in active) / len(active)
            if active else 0
        )
        return {
            "total": len(insights),
            "active": len(active),
            "achieved": len(achieved),
            "inactive": len(inactive),
            "avg_progress": round(avg_progress, 1),
        }
