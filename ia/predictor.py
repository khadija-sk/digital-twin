# ia/predictor.py

from datetime import date, timedelta
from models.database import get_session
from models.daily_log import DailyLog

class Predictor:

    def __init__(self, user_id):
        self.user_id = user_id

    def _get_logs(self, days=14):
        session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            return session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since
            ).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def predict_tomorrow_score(self) -> dict:
        logs = self._get_logs(7)
        if len(logs) < 3:
            return {"predicted": None, "confidence": "low", "tip": "Pas assez de données."}
        scores = [l.score_productivite for l in logs if l.score_productivite is not None]
        if not scores:
            return {"predicted": None, "confidence": "low", "tip": "Pas assez de données."}
        avg_recent = sum(scores[-3:]) / 3
        avg_older = sum(scores[:-3]) / max(len(scores) - 3, 1)
        trend = avg_recent - avg_older
        predicted = round(min(100, max(0, avg_recent + trend * 0.5)))
        confidence = "high" if len(scores) >= 5 else "medium"
        if trend > 5:
            tip = "📈 Ta tendance est positive — maintiens tes bonnes habitudes !"
        elif trend < -5:
            tip = "📉 Ta tendance baisse — dors bien ce soir pour inverser la courbe."
        else:
            tip = "➡️ Score stable — continue sur ta lancée."
        return {"predicted": predicted, "confidence": confidence, "tip": tip}

    def predict_burnout_risk_days(self) -> int:
        logs = self._get_logs(7)
        if len(logs) < 3:
            return -1
        energy = [l.energie for l in logs]
        if len(energy) < 2:
            return -1
        trend = energy[-1] - energy[0]
        if trend >= 0:
            return -1
        current = energy[-1]
        daily_drop = abs(trend) / len(energy)
        if daily_drop == 0:
            return -1
        days_to_burnout = round((current - 1) / daily_drop)
        return max(0, days_to_burnout)