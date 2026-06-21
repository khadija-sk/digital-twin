import logging
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.daily_log import DailyLog
from models.journal import Journal
from models.study_session import StudySession
from services.emotion_detector import EmotionDetector
from services.journal_analyzer import JournalAnalyzer
from services.academic_service import AcademicService
from services.timeline_service import TimelineService


logger = logging.getLogger(__name__)


class BriefingService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def generate_briefing(self) -> dict:
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)

        session = get_session()
        try:
            today_log = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id, date=today
            ).first()
            yesterday_log = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id, date=yesterday
            ).first()

            week_start = today - timedelta(days=today.weekday())
            week_logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= week_start,
                DailyLog.date <= today,
            ).all()

            today_journal = session.query(Journal).filter_by(
                utilisateur_id=self.user_id, date=today
            ).first()

            week_avg_mood = (
                sum(l.humeur or 3 for l in week_logs) / len(week_logs)
            ) if week_logs else 3.0

            week_avg_productivity = (
                sum(l.score_productivite or 50 for l in week_logs) / len(week_logs)
            ) if week_logs else 50.0

            journal = JournalAnalyzer(self.user_id)
            emotion = EmotionDetector(self.user_id)
            emo_state = emotion.get_emotion_state(7)
            journal_summary = journal.generate_summary(7)

            academic = AcademicService(self.user_id)
            deadlines = academic.get_upcoming_deadlines(7)

            _ = TimelineService(self.user_id)
            timeline_events = _.get_timeline_summary(3)

            greeting = self._time_based_greeting()

            briefing = {
                "greeting": greeting,
                "date": today.isoformat(),
                "streak": self._compute_streak(session),
                "yesterday": self._format_yesterday(yesterday_log),
                "today_mood": today_log.humeur if today_log else None,
                "today_score": today_log.score_productivite if today_log else None,
                "today_journal": today_journal.contenu[:200] if today_journal else None,
                "week_mood": round(week_avg_mood, 1),
                "week_productivity": round(week_avg_productivity, 1),
                "emotion": emo_state,
                "journal_insight": journal_summary,
                "deadlines": [d["title"] for d in deadlines[:3]],
                "deadline_count": len(deadlines),
                "recent_timeline": timeline_events,
                "has_logged_today": today_log is not None,
                "productivity_comparison": self._compare_productivity(
                    week_logs, yesterday_log
                ),
            }

            self._infer_recommendations(briefing, emo_state, week_avg_mood)
            return briefing
        except Exception as e:
            logger.exception("Error generating briefing")
            return {"greeting": "Bonjour", "date": today.isoformat(), "error": str(e)}
        finally:
            session.close()

    def _time_based_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Bonjour"
        elif hour < 18:
            return "Bon après-midi"
        return "Bonsoir"

    def _compute_streak(self, session) -> int:
        streak = 0
        day = datetime.now().date()
        while True:
            log = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id, date=day
            ).first()
            if not log:
                break
            streak += 1
            day -= timedelta(days=1)
        return streak

    def _format_yesterday(self, log) -> Optional[dict]:
        if not log:
            return None
        return {
            "mood": log.humeur, "energy": log.energie,
            "score": log.score_productivite, "notes": None,
        }

    def _compare_productivity(self, week_logs: list, yesterday: object) -> str:
        if len(week_logs) < 2 or not yesterday:
            return ""
        week_scores = [l.score_productivite or 50 for l in week_logs]
        week_avg = sum(week_scores) / len(week_scores)
        yesterday_score = yesterday.score_productivite or 50
        diff = yesterday_score - week_avg
        if diff > 15:
            return "Ta journée d'hier était bien plus productive que la moyenne de la semaine."
        elif diff < -15:
            return "Hier était moins productif que ta moyenne — peut-être un jour de repos ?"
        return ""

    def _infer_recommendations(self, briefing: dict, emo_state: dict, week_mood: float):
        recs = []
        if not briefing.get("has_logged_today"):
            recs.append("Ajoute ton journal du jour pour suivre ta progression.")

        if emo_state["burnout_risk"] > 0.5:
            recs.append("Risque de surmenage détecté — pense à prendre du temps pour toi.")

        if emo_state["stress"] > 0.6:
            recs.append("Tu sembles stressé — une courte pause ou une respiration pourrait t'aider.")

        if week_mood < 3.0:
            recs.append("Ta semaine a été difficile — concentre-toi sur une petite victoire aujourd'hui.")

        if briefing.get("deadline_count", 0) > 0:
            recs.append(f"Tu as {briefing['deadline_count']} échéance(s) à venir — organise ton planning.")

        briefing["recommendations"] = recs
