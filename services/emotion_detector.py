import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.daily_log import DailyLog
from services.journal_analyzer import JournalAnalyzer


logger = logging.getLogger(__name__)


class EmotionDetector:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_emotion_state(self, days: int = 7) -> dict:
        session = get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= cutoff.date(),
            ).order_by(DailyLog.date.asc()).all()

            if not logs:
                return self._empty_state()

            moods = [l.humeur for l in logs if l.humeur]
            energies = [l.energie for l in logs if l.energie]
            scores = [l.score_productivite for l in logs if l.score_productivite]

            avg_mood = float(np.mean(moods)) if moods else 3.0
            avg_energy = float(np.mean(energies)) if energies else 3.0
            avg_score = float(np.mean(scores)) if scores else 50.0
            mood_trend = self._compute_trend(moods)
            energy_trend = self._compute_trend(energies)
            burnout_risk = self._compute_burnout_risk(energies)
            stability = self._compute_stability(moods)

            journal = JournalAnalyzer(self.user_id)
            journal_sentiment = self._get_journal_sentiment(journal, days)

            happiness = (avg_mood / 5.0) * 0.4 + (avg_energy / 5.0) * 0.2 + (1 - burnout_risk) * 0.2 + journal_sentiment * 0.2
            stress_level = burnout_risk * 0.6 + (1 - stability) * 0.4
            motivation = (avg_score / 100.0) * 0.3 + (avg_energy / 5.0) * 0.3 + journal_sentiment * 0.4

            return {
                "happiness": round(min(1.0, happiness), 2),
                "stress": round(min(1.0, stress_level), 2),
                "motivation": round(min(1.0, motivation), 2),
                "burnout_risk": round(min(1.0, burnout_risk), 2),
                "stability": round(stability, 2),
                "mood_trend": mood_trend,
                "energy_trend": energy_trend,
                "avg_mood": round(avg_mood, 1),
                "avg_energy": round(avg_energy, 1),
                "avg_score": round(avg_score, 1),
            }
        except Exception as e:
            logger.exception("Error computing emotion state")
            return self._empty_state()
        finally:
            session.close()

    def get_emotion_trend(self, days: int = 30) -> list[dict]:
        session = get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            logs = session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= cutoff.date(),
            ).order_by(DailyLog.date.asc()).all()

            trend = []
            journal = JournalAnalyzer(self.user_id)

            for log in logs:
                mood_norm = (log.humeur or 3) / 5.0
                energy_norm = (log.energie or 3) / 5.0
                score_norm = (log.score_productivite or 50) / 100.0
                happiness = mood_norm * 0.5 + energy_norm * 0.3 + score_norm * 0.2

                trend.append({
                    "date": log.date.isoformat() if hasattr(log.date, 'isoformat') else str(log.date),
                    "happiness": round(happiness, 2),
                    "mood": log.humeur,
                    "energy": log.energie,
                    "score": log.score_productivite,
                })

            if not trend and logs:
                last_date = logs[-1].date
                journal_analysis = journal.get_recent_analyses(7)
                if journal_analysis:
                    for ja in journal_analysis:
                        trend.append({
                            "date": ja["date"],
                            "happiness": round(mood_norm * 0.5 + 0.3 + ja["sentiment"] * 0.2, 2) if logs else 0.5,
                            "mood": None,
                            "energy": None,
                            "score": None,
                        })
            return trend
        except Exception as e:
            logger.exception("Error computing emotion trend")
            return []
        finally:
            session.close()

    def _compute_trend(self, values: list[float]) -> str:
        if len(values) < 3:
            return "stable"
        recent = np.mean(values[-3:])
        earlier = np.mean(values[:3])
        diff = recent - earlier
        if diff > 0.3:
            return "hausse"
        elif diff < -0.3:
            return "baisse"
        return "stable"

    def _compute_burnout_risk(self, energies: list[float]) -> float:
        if len(energies) < 3:
            return 0.0
        recent = energies[-3:]
        if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            return min(1.0, 0.3 + (5 - recent[-1]) * 0.15)
        if np.mean(recent) < 2.0:
            return 0.5
        return 0.0

    def _compute_stability(self, moods: list[float]) -> float:
        if len(moods) < 3:
            return 1.0
        std = float(np.std(moods))
        return max(0.0, 1.0 - std / 2.0)

    def _get_journal_sentiment(self, journal: JournalAnalyzer, days: int) -> float:
        try:
            analyses = journal.get_recent_analyses(days)
            if analyses:
                return float(np.mean([a["sentiment"] for a in analyses]))
        except Exception:
            pass
        return 0.5

    def _empty_state(self) -> dict:
        return {
            "happiness": 0.5, "stress": 0.0, "motivation": 0.5,
            "burnout_risk": 0.0, "stability": 1.0,
            "mood_trend": "stable", "energy_trend": "stable",
            "avg_mood": 0.0, "avg_energy": 0.0, "avg_score": 0.0,
        }
