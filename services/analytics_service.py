import logging
from collections import Counter, defaultdict
from datetime import date, timedelta, datetime
from statistics import mean, stdev

from sqlalchemy import func
from models.database import get_session
from models.daily_log import DailyLog
from models.study_session import StudySession
from models.journal import Journal
from models.objective import Objective
from models.extensions import MemoryEntry, TimelineEvent

logger = logging.getLogger(__name__)


class AnalyticsService:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def full_analysis(self) -> dict:
        return {
            "productivity": self.productivity_analysis(),
            "learning": self.learning_analysis(),
            "mood": self.mood_analysis(),
            "topics": self.topic_analysis(),
            "habits": self.habit_analysis(),
            "recommendations": self.generate_recommendations(),
        }

    def productivity_analysis(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since,
            ).order_by(DailyLog.date).all()

            if not logs:
                return {"best_day": None, "avg_score": 0, "peak_hours": [], "consistency": 0}

            scores = [l.score_productivite for l in logs if l.score_productivite is not None]
            if not scores:
                return {"best_day": None, "avg_score": 0, "peak_hours": [], "consistency": 0}

            best_idx = scores.index(max(scores))
            best_day = str(logs[best_idx].date) if best_idx < len(logs) else None
            avg_score = round(mean(scores), 1)

            sessions = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= datetime.combine(since, datetime.min.time()),
            ).all()
            hour_counts = Counter(s.date_heure_debut.hour for s in sessions if s.date_heure_debut)
            peak_hours = [h for h, _ in hour_counts.most_common(3)]

            consistency = round(len(logs) / 30 * 100, 1)

            score_history = [
                {"date": str(l.date), "score": l.score_productivite}
                for l in logs if l.score_productivite is not None
            ]

            return {
                "best_day": best_day,
                "avg_score": avg_score,
                "latest_score": scores[-1] if scores else None,
                "best_score": max(scores),
                "worst_score": min(scores),
                "score_volatility": round(stdev(scores), 1) if len(scores) > 1 else 0,
                "peak_hours": peak_hours,
                "consistency": consistency,
                "total_logs": len(logs),
                "trend": self._compute_trend(scores),
                "score_history": score_history,
            }
        finally:
            session.close()

    def _compute_trend(self, scores: list) -> str:
        if len(scores) < 7:
            return "insufficient_data"
        first_half = mean(scores[:len(scores)//2])
        second_half = mean(scores[len(scores)//2:])
        diff = second_half - first_half
        if diff >= 5:
            return "strong_up"
        if diff >= 2:
            return "slight_up"
        if diff <= -5:
            return "strong_down"
        if diff <= -2:
            return "slight_down"
        return "stable"

    def learning_analysis(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            sessions = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= datetime.combine(since, datetime.min.time()),
            ).all()

            total_sessions = len(sessions)
            total_minutes = sum(s.duree for s in sessions)
            avg_duration = round(total_minutes / total_sessions, 1) if total_sessions else 0
            day_counts = Counter(s.date_heure_debut.strftime("%A") for s in sessions if s.date_heure_debut)
            most_productive_day = day_counts.most_common(1)[0][0] if day_counts else None
            weekdays_count = sum(
                1 for s in sessions if s.date_heure_debut and s.date_heure_debut.weekday() < 5
            )
            weekend_count = total_sessions - weekdays_count

            day_names_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
            weekday_distribution = [0] * 7
            for s in sessions:
                if s.date_heure_debut:
                    weekday_distribution[s.date_heure_debut.weekday()] += 1

            memories = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.category == "learning",
                MemoryEntry.created_at >= datetime.utcnow() - timedelta(days=30),
            ).count()

            objectives = session.query(Objective).filter_by(
                utilisateur_id=self.user_id, statut="atteint"
            ).count()

            return {
                "total_sessions": total_sessions,
                "total_hours": round(total_minutes / 60, 1),
                "avg_duration_min": avg_duration,
                "most_productive_day": most_productive_day,
                "weekday_sessions": weekdays_count,
                "weekend_sessions": weekend_count,
                "weekday_distribution": weekday_distribution,
                "day_labels": day_names_fr,
                "study_consistency": round(total_sessions / 30 * 100, 1) if total_sessions < 30 else 100,
                "new_memories_30d": memories,
                "goals_achieved_30d": objectives,
            }
        finally:
            session.close()

    def mood_analysis(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since,
            ).order_by(DailyLog.date).all()

            if not logs:
                return {"avg_mood": 0, "avg_energy": 0, "avg_sleep": 0, "trend": "insufficient_data"}

            moods = [l.humeur for l in logs if l.humeur]
            energies = [l.energie for l in logs if l.energie]
            sleeps = [l.sommeil for l in logs if l.sommeil]

            history = [
                {
                    "date": str(l.date), "mood": l.humeur,
                    "energy": l.energie, "sleep": l.sommeil,
                    "score": l.score_productivite,
                }
                for l in logs
            ]

            return {
                "avg_mood": round(mean(moods), 1) if moods else 0,
                "avg_energy": round(mean(energies), 1) if energies else 0,
                "avg_sleep": round(mean(sleeps), 1) if sleeps else 0,
                "mood_trend": self._compute_trend(moods) if len(moods) >= 7 else "insufficient_data",
                "energy_trend": self._compute_trend(energies) if len(energies) >= 7 else "insufficient_data",
                "best_mood": max(moods) if moods else 0,
                "worst_mood": min(moods) if moods else 0,
                "mood_volatility": round(stdev(moods), 1) if len(moods) > 1 else 0,
                "history": history,
            }
        finally:
            session.close()

    def topic_analysis(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            journals = session.query(Journal).filter(
                Journal.utilisateur_id == self.user_id,
                Journal.date >= since,
            ).all()

            topics = Counter()
            keywords = {
                "programmation": ["python", "code", "programmation", "algorithme", "développement", "javascript", "react"],
                "étude": ["étude", "apprendre", "cours", "lecture", "révision", "examen"],
                "santé": ["santé", "médecin", "bien-être", "stress", "anxiété", "fatigue"],
                "projet": ["projet", "portfolio", "github", "site", "application"],
                "carrière": ["carrière", "stage", "entretien", "travail", "job", "recruteur"],
                "productivité": ["pomodoro", "productivité", "focus", "concentration", "organisation"],
                "social": ["famille", "ami", "relation", "sortie", "rencontre"],
                "finance": ["argent", "budget", "économie", "finance", "achat"],
            }

            for entry in journals:
                content = entry.contenu.lower()
                for topic, kw_list in keywords.items():
                    if any(kw in content for kw in kw_list):
                        topics[topic] += 1

            return {
                "top_topics": [t for t, _ in topics.most_common(5)],
                "topic_counts": dict(topics.most_common(10)),
                "total_journals": len(journals),
            }
        finally:
            session.close()

    def habit_analysis(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since,
            ).order_by(DailyLog.date).all()

            if len(logs) < 7:
                return {"streak": 0, "most_consistent_metric": None, "patterns": []}

            sleeps = [l.sommeil for l in logs if l.sommeil]
            consistent_sleep = (
                round(stdev(sleeps), 1) <= 1.5 if len(sleeps) > 1 else False
            )
            energies = [l.energie for l in logs if l.energie]
            consistent_energy = (
                round(stdev(energies), 1) <= 1.0 if len(energies) > 1 else False
            )
            moods = [l.humeur for l in logs if l.humeur]
            consistent_mood = (
                round(stdev(moods), 1) <= 0.8 if len(moods) > 1 else False
            )

            metrics = {
                "sommeil": consistent_sleep,
                "énergie": consistent_energy,
                "humeur": consistent_mood,
            }
            consistent_metrics = [m for m, v in metrics.items() if v]
            most_consistent = consistent_metrics[0] if consistent_metrics else None

            streak = self._compute_streak(logs)
            patterns = self._detect_patterns(logs)

            return {
                "streak": streak,
                "most_consistent_metric": most_consistent,
                "metrics_consistent": metrics,
                "patterns": patterns,
                "total_logs": len(logs),
            }
        finally:
            session.close()

    def _compute_streak(self, logs: list) -> int:
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

    def _detect_patterns(self, logs: list) -> list[str]:
        patterns = []
        if len(logs) >= 3:
            recent_sleep = mean([l.sommeil for l in logs[-3:] if l.sommeil])
            early_sleep = mean([l.sommeil for l in logs[:3] if l.sommeil])
            if recent_sleep and early_sleep and recent_sleep > early_sleep + 0.5:
                patterns.append("Amélioration du sommeil cette semaine")
            elif recent_sleep and early_sleep and recent_sleep < early_sleep - 0.5:
                patterns.append("Baisse du sommeil cette semaine")
        if len(logs) >= 7:
            weekend_moods = mean(
                [l.humeur for l in logs if l.humeur and l.date.weekday() >= 5]
            ) if any(l.date.weekday() >= 5 for l in logs) else None
            weekday_moods = mean(
                [l.humeur for l in logs if l.humeur and l.date.weekday() < 5]
            ) if any(l.date.weekday() < 5 for l in logs) else None
            if weekend_moods and weekday_moods and weekend_moods > weekday_moods + 0.5:
                patterns.append("Meilleure humeur le week-end")
            elif weekend_moods and weekday_moods and weekday_moods > weekend_moods + 0.5:
                patterns.append("Meilleure humeur en semaine")
        return patterns

    def generate_recommendations(self) -> list[dict]:
        recs = []
        try:
            prod = self.productivity_analysis()
            mood = self.mood_analysis()
            habits = self.habit_analysis()

            if prod.get("consistency", 100) < 50:
                recs.append({
                    "priority": "high",
                    "area": "consistance",
                    "message": "Vise un check-in quotidien pour améliorer ta régularité.",
                })

            if mood.get("avg_sleep", 8) < 6.5:
                recs.append({
                    "priority": "high",
                    "area": "sommeil",
                    "message": f"Ta moyenne de sommeil ({mood['avg_sleep']}h) est trop basse. Vise 7-8h.",
                })

            if prod.get("score_volatility", 0) > 15:
                recs.append({
                    "priority": "medium",
                    "area": "stabilité",
                    "message": "Ta productivité est instable. Essaie une routine fixe.",
                })

            if habits.get("streak", 0) > 7 and prod.get("avg_score", 0) < 60:
                recs.append({
                    "priority": "medium",
                    "area": "plafond",
                    "message": "Bonne régularité mais score moyen. Augmente progressivement ta charge.",
                })

            if not recs:
                recs.append({
                    "priority": "low",
                    "area": "général",
                    "message": "Continue sur cette lancée — la régularité est ta meilleure alliée.",
                })
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")

        return recs

    def get_focus_stats(self) -> dict:
        session = get_session()
        try:
            since = date.today() - timedelta(days=30)
            total_sessions = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
            ).count()

            completed = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= since,
            ).count()

            abandoned = session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "abandonne",
                StudySession.date_heure_debut >= since,
            ).count()

            total = completed + abandoned
            completion_rate = round(completed / total * 100) if total > 0 else 0

            active_days = session.query(
                func.count(func.distinct(func.date(StudySession.date_heure_debut)))
            ).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= since,
            ).scalar() or 0

            return {
                "total_sessions": total_sessions,
                "completed": completed,
                "abandoned": abandoned,
                "completion_rate": completion_rate,
                "active_days": active_days,
            }
        finally:
            session.close()
