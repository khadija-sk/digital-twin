from datetime import date, timedelta, datetime
from models.database import get_session
from models.user import User
from models.daily_log import DailyLog
from models.study_session import StudySession
from models.journal import Journal
from models.objective import Objective
from models.badge import Badge
from services.memory_system import MemorySystem


class ContextRetriever:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_user_profile(self, session=None) -> dict:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            user = session.query(User).filter_by(id=self.user_id).first()
            if not user:
                return {}
            total_checkins = session.query(DailyLog).filter_by(
                utilisateur_id=self.user_id
            ).count()
            total_sessions = session.query(StudySession).filter_by(
                utilisateur_id=self.user_id, statut="complete"
            ).count()
            total_journals = session.query(Journal).filter_by(
                utilisateur_id=self.user_id
            ).count()
            streak = self._compute_streak(session)
            return {
                "name": user.nom,
                "email": user.email,
                "level": user.niveau,
                "xp": user.xp_total,
                "member_since": user.date_creation.strftime("%Y-%m-%d") if user.date_creation else "N/A",
                "total_checkins": total_checkins,
                "total_sessions": total_sessions,
                "total_journals": total_journals,
                "checkin_streak": streak,
            }
        finally:
            if own_session:
                session.close()

    def get_recent_logs(self, days: int = 7, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            logs = (
                session.query(DailyLog)
                .filter(
                    DailyLog.utilisateur_id == self.user_id,
                    DailyLog.date >= since,
                )
                .order_by(DailyLog.date.asc())
                .all()
            )
            return [
                {
                    "date": str(log.date),
                    "mood": log.humeur,
                    "energy": log.energie,
                    "sleep": log.sommeil,
                    "score": log.score_productivite,
                }
                for log in logs
            ]
        finally:
            if own_session:
                session.close()

    def get_log_summary(self, days: int = 7, session=None) -> dict:
        logs = self.get_recent_logs(days, session=session)
        if not logs:
            return {}
        moods = [l["mood"] for l in logs]
        energies = [l["energy"] for l in logs]
        sleeps = [l["sleep"] for l in logs]
        scores = [l["score"] for l in logs if l["score"] is not None]
        mood_avg = sum(moods) / len(moods)
        energy_avg = sum(energies) / len(energies)
        sleep_avg = sum(sleeps) / len(sleeps)
        score_avg = round(sum(scores) / len(scores)) if scores else None

        if len(scores) >= 2:
            trend = "up" if scores[-1] > scores[0] else "down" if scores[-1] < scores[0] else "stable"
        else:
            trend = "insufficient_data"

        mood_trend_text = "stable"
        if len(moods) >= 3:
            if moods[-1] > moods[-3]:
                mood_trend_text = "improving"
            elif moods[-1] < moods[-3]:
                mood_trend_text = "declining"

        energy_trend_text = "stable"
        if len(energies) >= 3:
            if energies[-1] > energies[-3]:
                energy_trend_text = "improving"
            elif energies[-1] < energies[-3]:
                energy_trend_text = "declining"

        burnout_risk = False
        if len(energies) >= 3 and energies[-1] < energies[-2] < energies[-3]:
            burnout_risk = True

        return {
            "period_days": days,
            "log_count": len(logs),
            "average_mood": round(mood_avg, 1),
            "average_energy": round(energy_avg, 1),
            "average_sleep": round(sleep_avg, 1),
            "average_score": score_avg,
            "score_trend": trend,
            "mood_trend": mood_trend_text,
            "energy_trend": energy_trend_text,
            "burnout_risk": burnout_risk,
            "latest_score": scores[-1] if scores else None,
            "best_score": max(scores) if scores else None,
            "worst_score": min(scores) if scores else None,
            "logs": logs,
        }

    def get_today_log(self, session=None) -> dict | None:
        logs = self.get_recent_logs(1, session=session)
        if logs and logs[0]["date"] == str(date.today()):
            return logs[0]
        return None

    def get_recent_sessions(self, days: int = 7, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            rows = (
                session.query(StudySession)
                .filter(
                    StudySession.utilisateur_id == self.user_id,
                    StudySession.date_heure_debut >= datetime.combine(since, datetime.min.time()),
                    StudySession.statut == "complete",
                )
                .order_by(StudySession.date_heure_debut.asc())
                .all()
            )
            return [
                {
                    "date": str(row.date_heure_debut.strftime("%Y-%m-%d")),
                    "duration": row.duree,
                    "energy_mid": row.energie_mi_session,
                }
                for row in rows
            ]
        finally:
            if own_session:
                session.close()

    def get_session_summary(self, days: int = 7, session=None) -> dict:
        sessions = self.get_recent_sessions(days, session=session)
        if not sessions:
            return {"total_sessions": 0, "total_hours": 0, "average_duration": 0, "sessions": []}
        total = len(sessions)
        total_minutes = sum(s["duration"] for s in sessions)
        avg_duration = round(total_minutes / total, 1)
        return {
            "total_sessions": total,
            "total_hours": round(total_minutes / 60, 1),
            "total_minutes": total_minutes,
            "average_duration": avg_duration,
            "sessions": sessions,
        }

    def get_recent_journals(self, days: int = 7, max_chars: int = 300, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            rows = (
                session.query(Journal)
                .filter(
                    Journal.utilisateur_id == self.user_id,
                    Journal.date >= since,
                )
                .order_by(Journal.date.desc())
                .all()
            )
            return [
                {
                    "date": str(row.date),
                    "content": row.contenu[:max_chars],
                    "word_count": len(row.contenu.split()),
                }
                for row in rows
            ]
        finally:
            if own_session:
                session.close()

    def search_journals(self, query: str, days: int = 30, max_results: int = 5, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
            rows = (
                session.query(Journal)
                .filter(
                    Journal.utilisateur_id == self.user_id,
                    Journal.date >= since,
                )
                .all()
            )
            scored = []
            for entry in rows:
                content = entry.contenu.lower()
                score = sum(1 for kw in keywords if kw in content)
                if score > 0:
                    scored.append((score, entry))
            scored.sort(key=lambda x: -x[0])
            return [
                {"date": str(entry.date), "content": entry.contenu[:300], "relevance": s}
                for s, entry in scored[:max_results]
            ]
        finally:
            if own_session:
                session.close()

    def get_active_objectives(self, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            rows = (
                session.query(Objective)
                .filter(
                    Objective.utilisateur_id == self.user_id,
                    Objective.statut == "actif",
                )
                .all()
            )
            return [
                {
                    "description": row.description,
                    "target_value": row.valeur_cible,
                    "unit": row.unite,
                    "created": str(row.date_creation),
                }
                for row in rows
            ]
        finally:
            if own_session:
                session.close()

    def get_all_objectives(self, session=None) -> dict:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            from sqlalchemy import func
            counts = (
                session.query(Objective.statut, func.count(Objective.id))
                .filter(Objective.utilisateur_id == self.user_id)
                .group_by(Objective.statut)
                .all()
            )
            result = {"active": 0, "achieved": 0, "total": 0}
            for statut, count in counts:
                if statut == "actif":
                    result["active"] = count
                elif statut == "atteint":
                    result["achieved"] = count
            result["total"] = result["active"] + result["achieved"]
            return result
        finally:
            if own_session:
                session.close()

    def get_badges(self, session=None) -> list[dict]:
        own_session = session is None
        if session is None:
            session = get_session()
        try:
            rows = (
                session.query(Badge)
                .filter(Badge.utilisateur_id == self.user_id)
                .order_by(Badge.date_obtention.desc())
                .all()
            )
            return [
                {
                    "name": row.nom,
                    "description": row.description,
                    "date": str(row.date_obtention),
                    "icon": row.icone,
                    "xp": row.xp_gagne,
                }
                for row in rows
            ]
        finally:
            if own_session:
                session.close()

    def get_complete_context(self, days: int = 7) -> dict:
        session = get_session()
        try:
            return {
                "profile": self.get_user_profile(session=session),
                "logs": self.get_log_summary(days, session=session),
                "sessions": self.get_session_summary(days, session=session),
                "journals": self.get_recent_journals(days, session=session),
                "active_objectives": self.get_active_objectives(session=session),
                "objective_stats": self.get_all_objectives(session=session),
                "badges": self.get_badges(session=session),
            }
        finally:
            session.close()

    def get_rag_context(self, question: str) -> dict:
        context = self.get_complete_context(14)
        journal_hits = self.search_journals(question, days=30)
        if journal_hits:
            context["relevant_journals"] = journal_hits
        memory = MemorySystem(self.user_id)
        context["memories"] = memory.retrieve(category="", limit=5)
        return context

    def _compute_streak(self, session) -> int:
        logs = (
            session.query(DailyLog)
            .filter_by(utilisateur_id=self.user_id)
            .order_by(DailyLog.date.desc())
            .limit(31)
            .all()
        )
        if not logs:
            return 0
        streak = 0
        check = date.today()
        for log in logs:
            if log.date == check:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
        return streak
