from datetime import date, timedelta
from models.database import get_session
from models.daily_log import DailyLog
from models.study_session import StudySession


class RoutineSuggester:

    def __init__(self, user_id):
        self.user_id = user_id

    def _get_logs(self, days=7):
        session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            return session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since
            ).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def _get_sessions_this_week(self):
        session = get_session()
        try:
            since = date.today() - timedelta(days=7)
            from datetime import datetime
            since_dt = datetime.combine(since, datetime.min.time())
            return session.query(StudySession).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.statut == "complete",
                StudySession.date_heure_debut >= since_dt
            ).count()
        finally:
            session.close()

    def get_routine(self) -> list:
        logs = self._get_logs(7)
        sessions_count = self._get_sessions_this_week()
        avg_sleep = sum(l.sommeil for l in logs) / len(logs) if logs else 7
        avg_energy = sum(l.energie for l in logs) / len(logs) if logs else 3
        avg_mood = sum(l.humeur for l in logs) / len(logs) if logs else 3
        routine = []
        wake = "07:00" if avg_sleep >= 7 else "07:30"
        routine.append({"time": wake, "activity": "☀️ Réveil & hydratation", "duration": "10 min", "reason": "Un verre d'eau au réveil booste ton énergie immédiatement."})
        routine.append({"time": "07:15" if avg_sleep >= 7 else "07:45", "activity": "📋 Check-in du jour", "duration": "5 min", "reason": "Suivre ton humeur et ton énergie chaque matin."})
        pomodoros_morning = 3 if avg_energy >= 3.5 else 2
        routine.append({"time": "08:00", "activity": f"🍅 Bloc de travail ({pomodoros_morning} Pomodoros)", "duration": f"{pomodoros_morning * 30} min", "reason": "L'énergie est maximale le matin — réserve-le au travail difficile."})
        routine.append({"time": "09:30" if pomodoros_morning == 3 else "09:00", "activity": "🚶 Pause active", "duration": "15 min", "reason": "Marcher recharge mieux que le café après un bloc de travail."})
        pomodoros_afternoon = 2 if avg_energy < 3 else 3
        routine.append({"time": "14:00", "activity": f"🍅 Bloc de travail ({pomodoros_afternoon} Pomodoros)", "duration": f"{pomodoros_afternoon * 30} min", "reason": "Bloc moins intense pour l'après-déjeuner."})
        if avg_mood < 3:
            routine.append({"time": "17:00", "activity": "😊 Activité plaisir", "duration": "30 min", "reason": "Ton humeur est basse — réserve du temps pour toi."})
        else:
            routine.append({"time": "17:00", "activity": "📚 Lecture ou apprentissage", "duration": "30 min", "reason": "Profite de ta bonne humeur pour apprendre quelque chose de nouveau."})
        routine.append({"time": "21:00", "activity": "📓 Journal du soir", "duration": "10 min", "reason": "Écrire le soir améliore la qualité du sommeil."})
        sleep_time = "22:30" if avg_sleep < 7 else "23:00"
        routine.append({"time": sleep_time, "activity": "🌙 Coucher (vise 8h de sommeil)", "duration": "—", "reason": f"Tu dors en moyenne {avg_sleep:.1f}h — {'insuffisant, couche-toi plus tôt !' if avg_sleep < 7 else 'continue ainsi !'}"})
        return routine

    def get_summary(self) -> str:
        logs = self._get_logs(7)
        if not logs:
            return "Fais quelques check-ins pour obtenir une routine personnalisée."
        avg_energy = sum(l.energie for l in logs) / len(logs)
        sessions = self._get_sessions_this_week()
        pomodoros = 5 if avg_energy >= 3.5 else 3
        return f"Routine suggérée : {pomodoros} Pomodoros/jour · coucher {'22h30' if sum(l.sommeil for l in logs)/len(logs) < 7 else '23h'} · journal le soir"
