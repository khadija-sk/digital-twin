import logging
from datetime import datetime, timedelta
from typing import Optional
from services.memory_system import MemorySystem
from services.emotion_detector import EmotionDetector
from services.journal_analyzer import JournalAnalyzer
from services.academic_service import AcademicService
from services.profile_service import ProfileService
from services.timeline_service import TimelineService
from services.smart_planner import SmartPlanner


logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_recommendations(self, limit: int = 5) -> list[dict]:
        emotion = EmotionDetector(self.user_id)
        planner = SmartPlanner(self.user_id)
        profile = ProfileService(self.user_id)
        journal = JournalAnalyzer(self.user_id)
        academic = AcademicService(self.user_id)
        memory = MemorySystem(self.user_id)

        emotional_state = emotion.get_emotion_state(7)
        interests = profile.get_interests()
        traits = profile.get_user_traits()
        deadlines = academic.get_upcoming_deadlines(7)
        mood_trend = emotional_state.get("mood_trend", "stable")
        stress = emotional_state.get("stress", 0)
        burnout = emotional_state.get("burnout_risk", 0)
        motivation = emotional_state.get("motivation", 0.5)

        recs = []

        if stress > 0.6:
            recs.append({
                "type": "bien-être",
                "icon": "🧘",
                "title": "Pause bien-être",
                "description": "Tu sembles stressé — prends 5 minutes pour respirer ou méditer.",
                "priority": "haute",
            })

        if burnout > 0.4:
            recs.append({
                "type": "repos",
                "icon": "😴",
                "title": "Repos recommandé",
                "description": "Signes de fatigue détectés — accorde-toi une vraie pause aujourd'hui.",
                "priority": "haute",
            })

        if motivation < 0.4:
            recs.append({
                "type": "motivation",
                "icon": "💪",
                "title": "Boost motivation",
                "description": "Revois tes objectifs — commence par une petite tâche facile.",
                "priority": "moyenne",
            })

        if deadlines:
            recs.append({
                "type": "académique",
                "icon": "📚",
                "title": f"{len(deadlines)} échéance(s) à venir",
                "description": f"Révise {'tes cours' if len(deadlines) > 1 else 'ton cours'} — utilise la technique Pomodoro.",
                "priority": "moyenne",
            })

        if "sport" in interests:
            recs.append({
                "type": "sport",
                "icon": "🏃",
                "title": "Bouge un peu",
                "description": "Tu aimes le sport — une courte séance peut améliorer ta concentration.",
                "priority": "basse",
            })

        if traits.get("communication_style") == "analytique":
            recs.append({
                "type": "défi",
                "icon": "🧩",
                "title": "Défi du jour",
                "description": "Résous un petit problème ou apprends un nouveau concept.",
                "priority": "basse",
            })

        daily_summary = memory.get_summary("general", 1)
        if not daily_summary:
            recs.append({
                "type": "journal",
                "icon": "📝",
                "title": "Journal du jour",
                "description": "Écrire dans ton journal aide à clarifier tes pensées.",
                "priority": "moyenne",
            })

        if mood_trend == "baisse":
            recs.append({
                "type": "social",
                "icon": "👥",
                "title": "Contact social",
                "description": "Ta tendance est en baisse — parler à quelqu'un peut aider.",
                "priority": "moyenne",
            })

        if len(recs) > limit:
            recs = recs[:limit]

        return recs

    def get_daily_challenge(self) -> Optional[dict]:
        emotion = EmotionDetector(self.user_id)
        state = emotion.get_emotion_state(1)

        challenges = [
            {"title": "Pomodoro parfait", "desc": "30 min de travail focus sans distraction",
             "points": 30, "category": "productivité"},
            {"title": "Gratitude", "desc": "Note 3 choses positives aujourd'hui",
             "points": 20, "category": "bien-être"},
            {"title": "Lecture rapide", "desc": "Lis un article et résume-le en 3 phrases",
             "points": 25, "category": "apprentissage"},
            {"title": "Marche active", "desc": "15 min de marche sans téléphone",
             "points": 20, "category": "sport"},
            {"title": "Méditation", "desc": "5 min de respiration consciente",
             "points": 15, "category": "bien-être"},
            {"title": "Code propre", "desc": "Refactorise un morceau de code existant",
             "points": 35, "category": "programmation"},
            {"title": "Organisation", "desc": "Planifie ta semaine en 5 min",
             "points": 20, "category": "productivité"},
            {"title": "Rangement", "desc": "Range ton espace de travail",
             "points": 15, "category": "organisation"},
            {"title": "Nouveau mot", "desc": "Apprends un mot dans une langue étrangère",
             "points": 10, "category": "apprentissage"},
            {"title": "Compliment", "desc": "Fais un compliment sincère à quelqu'un",
             "points": 20, "category": "social"},
        ]

        stress_level = state.get("stress", 0)
        if stress_level > 0.5:
            filtered = [c for c in challenges if c["category"] in ("bien-être", "sport")]
        elif state.get("motivation", 0.5) < 0.4:
            filtered = [c for c in challenges if c["points"] <= 20]
        else:
            filtered = challenges

        import random
        return random.choice(filtered) if filtered else challenges[0]
