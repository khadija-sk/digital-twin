import logging
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.objective import Objective
from models.study_session import StudySession
from models.daily_log import DailyLog
from services.academic_service import AcademicService


logger = logging.getLogger(__name__)


class SmartPlanner:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_today_plan(self) -> dict:
        today = datetime.now().date()
        session = get_session()
        try:
            objectives = session.query(Objective).filter(
                Objective.utilisateur_id == self.user_id,
                Objective.statut != "atteint"
            ).order_by(Objective.date_creation.desc()).all()

            today_log = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id, date=today
            ).first()

            academic = AcademicService(self.user_id)
            deadlines = academic.get_upcoming_deadlines(7)

            return {
                "date": today.isoformat(),
                "objectives": [{
                    "id": o.id, "title": o.description, "category": "",
                    "priority": 0, "due": None,
                    "estimated_minutes": 25,
                } for o in objectives[:8]],
                "deadlines": [d["title"] for d in deadlines[:3]],
                "has_mood": today_log is not None,
                "mood": today_log.humeur if today_log else None,
                "productivity_score": today_log.score_productivite if today_log else None,
            }
        finally:
            session.close()

    def get_weekly_schedule(self) -> dict:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        session = get_session()
        try:
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= week_start,
                DailyLog.date <= week_end,
            ).order_by(DailyLog.date.asc()).all()

            log_by_date = {str(l.date): l for l in logs}

            days = []
            for i in range(7):
                d = week_start + timedelta(days=i)
                d_str = d.isoformat()
                log = log_by_date.get(d_str)
                days.append({
                    "date": d_str,
                    "mood": log.humeur if log else None,
                    "score": log.score_productivite if log else None,
                    "has_log": log is not None,
                })

            from datetime import datetime as dt_module
            week_start_dt = dt_module.combine(week_start, dt_module.min.time())
            week_end_dt = dt_module.combine(week_end, dt_module.min.time())
            study_sessions = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.date_heure_debut >= week_start_dt,
                StudySession.date_heure_debut <= week_end_dt,
            ).all()

            total_study_hours = sum(
                (s.duree / 60) for s in study_sessions
                if s.duree
            )

            return {
                "week": f"{week_start.isoformat()} - {week_end.isoformat()}",
                "days": days,
                "total_study_hours": round(total_study_hours, 1),
                "logged_days": sum(1 for d in days if d["has_log"]),
            }
        finally:
            session.close()

    def suggest_focus_time(self) -> Optional[int]:
        session = get_session()
        try:
            study_sessions = session.query(StudySession).filter_by(
                utilisateur_id=self.user_id
            ).order_by(StudySession.date_heure_debut.desc()).limit(10).all()

            if not study_sessions:
                return 25

            durations = [
                s.duree for s in study_sessions
                if s.duree and s.duree > 0
            ]
            if not durations:
                return 25
            avg = sum(durations) / len(durations)
            return max(15, min(120, int(round(avg / 5) * 5)))
        finally:
            session.close()

    def get_productivity_insights(self, days: int = 14) -> list[str]:
        session = get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= cutoff.date(),
            ).order_by(DailyLog.date.asc()).all()

            if len(logs) < 2:
                return ["Ajoute plus de données pour des insights personnalisés."]

            scores = [l.score_productivite or 50 for l in logs]
            moods = [l.humeur or 3 for l in logs]
            avg_score = sum(scores) / len(scores)
            avg_mood = sum(moods) / len(moods)
            best_day = max(logs, key=lambda l: l.score_productivite or 0)
            worst_day = min(logs, key=lambda l: l.score_productivite or 100)

            insights = []
            if avg_score > 75:
                insights.append(f"Bonne productivité générale ({avg_score:.0f}%) — tu es dans une bonne dynamique.")
            elif avg_score < 40:
                insights.append(f"Productivité basse ({avg_score:.0f}%) — peut-être besoin de revoir ton organisation.")

            if len(scores) >= 3:
                recent_avg = sum(scores[-3:]) / 3
                earlier_avg = sum(scores[:3]) / 3
                if recent_avg > earlier_avg + 10:
                    insights.append("Ta productivité est en hausse cette semaine !")
                elif recent_avg < earlier_avg - 10:
                    insights.append("Ta productivité est en baisse — rien de grave, ça arrive.")

            if avg_mood < 3.0:
                insights.append("Ton humeur générale est basse — n'oublie pas de prendre soin de toi.")

            correlations = self._compute_correlations(logs)
            if correlations:
                insights.append(correlations)

            best_day_str = best_day.date.isoformat() if hasattr(best_day.date, 'isoformat') else str(best_day.date)
            insights.append(f"Meilleur jour : {best_day_str} ({best_day.score_productivite}%)")

            return insights[:5]
        finally:
            session.close()

    def _compute_correlations(self, logs: list) -> str:
        if len(logs) < 5:
            return ""
        high_mood = [l.score_productivite or 50 for l in logs if (l.humeur or 3) >= 4]
        low_mood = [l.score_productivite or 50 for l in logs if (l.humeur or 3) <= 2]
        if high_mood and low_mood:
            high_avg = sum(high_mood) / len(high_mood)
            low_avg = sum(low_mood) / len(low_mood)
            if high_avg > low_avg + 20:
                return "Quand tu es de bonne humeur, ta productivité est bien meilleure."
        return ""
