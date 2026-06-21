# ia/pattern_detector.py

from datetime import date, timedelta
from models.database import get_session
from models.daily_log import DailyLog

class PatternDetector:

    def __init__(self, user_id):
        self.user_id = user_id

    def _get_logs(self, days=30):
        session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            return session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since
            ).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def detect_all(self) -> list:
        logs = self._get_logs(30)
        if len(logs) < 5:
            return []
        patterns = []
        patterns += self._detect_burnout_risk(logs)
        patterns += self._detect_best_day(logs)
        patterns += self._detect_sleep_mood_correlation(logs)
        patterns += self._detect_consistency(logs)
        return patterns

    def _detect_burnout_risk(self, logs):
        energy = [l.energie for l in logs]
        if len(energy) >= 3 and energy[-1] < energy[-2] < energy[-3]:
            return ["⚠️ Énergie en baisse 3 jours de suite — risque de burnout"]
        return []

    def _detect_best_day(self, logs):
        if not logs:
            return []
        scores = [(l.date.weekday(), l.score_productivite or 0) for l in logs]
        day_totals = {}
        day_counts = {}
        for wd, score in scores:
            day_totals[wd] = day_totals.get(wd, 0) + score
            day_counts[wd] = day_counts.get(wd, 0) + 1
        if not day_totals:
            return []
        best_wd = max(day_totals, key=lambda d: day_totals[d] / day_counts[d])
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        return [f"📅 Ton meilleur jour est le {days_fr[best_wd]}"]

    def _detect_sleep_mood_correlation(self, logs):
        good_sleep = [l for l in logs if l.sommeil >= 7.5]
        bad_sleep = [l for l in logs if l.sommeil < 6]
        if len(good_sleep) >= 3 and len(bad_sleep) >= 3:
            avg_mood_good = sum(l.humeur for l in good_sleep) / len(good_sleep)
            avg_mood_bad = sum(l.humeur for l in bad_sleep) / len(bad_sleep)
            if avg_mood_good - avg_mood_bad >= 1:
                return [f"😴 Quand tu dors 7.5h+, ton humeur est {avg_mood_good:.1f}/5 vs {avg_mood_bad:.1f}/5 — le sommeil t'impacte beaucoup"]
        return []

    def _detect_consistency(self, logs):
        if len(logs) >= 14:
            return [f"🔥 {len(logs)} check-ins sur 30 jours — belle régularité !"]
        elif len(logs) >= 7:
            return [f"📋 {len(logs)} check-ins — continue pour des analyses plus précises"]
        return []