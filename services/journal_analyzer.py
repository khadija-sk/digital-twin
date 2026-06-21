import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.journal import Journal


logger = logging.getLogger(__name__)

POSITIVE_WORDS = {"fier", "content", "heureux", "joyeux", "excellent", "super", "génial",
    "formidable", "merveilleux", "réussi", "progrès", "accompli", "satisfait",
    "motivé", "énergique", "calme", "paisible", "reconnaissant", "optimiste"}
NEGATIVE_WORDS = {"triste", "fatigué", "épuisé", "stressé", "anxieux", "inquiet",
    "déprimé", "découragé", "frustré", "énervé", "en colère", "déçu",
    "submergé", "échec", "difficile", "dur", "pénible", "seul", "isolé"}
STRESS_WORDS = {"stress", "pression", "urgence", "deadline", "examen", "devoir",
    "travail", "chargé", "débordé", "insomnie", "anxiété", "inquiétude"}
ACHIEVEMENT_WORDS = {"terminé", "fini", "complété", "réussi", "obtenu", "progressé",
    "avancé", "amélioré", "gagné", "atteint", "finalisé", "validé"}
MOTIVATION_WORDS = {"motivé", "déterminé", "volonté", "objectif", "projet", "ambition",
    "rêve", "envie", "passion", "enthousiasme", "inspiré", "défi"}


class JournalAnalyzer:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def analyze_entry(self, content: str) -> dict:
        text = content.lower()
        words = set(re.findall(r'\b\w+\b', text))

        pos_count = len(words & POSITIVE_WORDS)
        neg_count = len(words & NEGATIVE_WORDS)
        stress_count = len(words & STRESS_WORDS)
        ach_count = len(words & ACHIEVEMENT_WORDS)
        mot_count = len(words & MOTIVATION_WORDS)

        total = pos_count + neg_count
        sentiment = 0.5
        if total > 0:
            sentiment = pos_count / total

        mood_tags = []
        if sentiment > 0.6:
            mood_tags.append("positive")
        elif sentiment < 0.4:
            mood_tags.append("negative")
        else:
            mood_tags.append("neutre")
        if stress_count > 0:
            mood_tags.append("stress")
        if ach_count > 0:
            mood_tags.append("accomplissement")
        if mot_count > 0:
            mood_tags.append("motivé")

        topics = self._extract_topics(text)

        return {
            "sentiment": round(sentiment, 2),
            "mood_tags": mood_tags,
            "stress_level": min(1.0, stress_count / 5),
            "achievement_count": ach_count,
            "motivation_score": min(1.0, mot_count / 3),
            "topics": list(topics),
            "word_count": len(words),
        }

    def _extract_topics(self, text: str) -> set:
        topic_patterns = {
            "études": r"\b(étude|école|cours|examen|devoir|note|prof|matière)\b",
            "travail": r"\b(travail|boulot|projet|collègue|réunion|client)\b",
            "santé": r"\b(santé|malade|douleur|médecin|hôpital|médicament)\b",
            "sommeil": r"\b(sommeil|dormir|insomnie|réveil|cauchemar)\b",
            "sport": r"\b(sport|course|gym|entraînement|exercice|yoga)\b",
            "famille": r"\b(famille|parent|mère|père|frère|soeur|enfant)\b",
            "amis": r"\b(ami|copain|sortie|soirée|rencontre)\b",
            "finances": r"\b(argent|budget|dépense|salaire|facture|économie)\b",
            "projets": r"\b(projet|objectif|but|rêve|ambition|plan)\b",
        }
        topics = set()
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, text):
                topics.add(topic)
        return topics

    def get_recent_analyses(self, days: int = 7) -> list[dict]:
        session = get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            entries = session.query(Journal).filter(
                Journal.utilisateur_id == self.user_id,
                Journal.date >= cutoff.date(),
            ).order_by(Journal.date.desc()).all()

            results = []
            for e in entries:
                analysis = self.analyze_entry(e.contenu)
                analysis["date"] = e.date.isoformat() if hasattr(e.date, 'isoformat') else str(e.date)
                analysis["preview"] = e.contenu[:100]
                results.append(analysis)
            return results
        finally:
            session.close()

    def generate_summary(self, days: int = 7) -> str:
        analyses = self.get_recent_analyses(days)
        if not analyses:
            return ""

        avg_sentiment = sum(a["sentiment"] for a in analyses) / len(analyses)
        avg_stress = sum(a["stress_level"] for a in analyses) / len(analyses)
        avg_motivation = sum(a["motivation_score"] for a in analyses) / len(analyses)
        all_topics = set()
        for a in analyses:
            all_topics.update(a["topics"])

        lines = []
        if avg_sentiment > 0.65:
            lines.append("Tu semblais de bonne humeur cette période.")
        elif avg_sentiment < 0.4:
            lines.append("Tu avais l'air plus préoccupé que d'habitude.")

        if avg_stress > 0.4:
            lines.append("Quelques signes de stress détectés — pense à prendre des pauses.")

        if avg_motivation > 0.6:
            lines.append("Bonne motivation générale — continue comme ça !")

        if all_topics:
            topics_str = ", ".join(sorted(all_topics)[:5])
            lines.append(f"Sujets abordés : {topics_str}.")

        return " ".join(lines) if lines else "Analyse terminée."
