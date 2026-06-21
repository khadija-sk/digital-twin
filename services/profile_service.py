import logging
import json
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.extensions import UserInterest


logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_interests(self) -> list[str]:
        session = get_session()
        try:
            interests = session.query(UserInterest).filter_by(
                utilisateur_id=self.user_id
            ).order_by(UserInterest.weight.desc()).all()
            return [i.name for i in interests]
        finally:
            session.close()

    def add_interest(self, name: str, category: str = "general", weight: float = 1.0):
        session = get_session()
        try:
            existing = session.query(UserInterest).filter_by(
                utilisateur_id=self.user_id, name=name
            ).first()
            if existing:
                existing.weight = min(10.0, existing.weight + weight * 0.5)
            else:
                interest = UserInterest(
                    utilisateur_id=self.user_id, name=name,
                    category=category, weight=min(10.0, weight),
                )
                session.add(interest)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def learn_from_chat(self, message: str):
        topics = {
            "programmation": ["python", "code", "développement", "programmation", "algorithme"],
            "design": ["design", "ui", "ux", "interface", "maquette", "figma"],
            "data_science": ["data", "machine learning", "ia", "analyse", "statistique"],
            "productivité": ["productivité", "organisation", "méthode", "todo", "planning"],
            "santé": ["santé", "bien-être", "méditation", "sommeil", "nutrition"],
            "sport": ["sport", "course", "gym", "entraînement", "fitness"],
        }
        msg_lower = message.lower()
        for category, keywords in topics.items():
            if any(kw in msg_lower for kw in keywords):
                self.add_interest(category, category, weight=0.3)

    def get_user_traits(self) -> dict:
        session = get_session()
        try:
            interests = session.query(UserInterest).filter_by(
                utilisateur_id=self.user_id
            ).order_by(UserInterest.weight.desc()).all()
            top_interests = [(i.name, i.weight) for i in interests[:5]]
            interest_count = len(interests)
            total_weight = sum(i.weight for i in interests) if interests else 1

            communication_style = self._infer_style(interests)

            return {
                "top_interests": top_interests,
                "interest_count": interest_count,
                "communication_style": communication_style,
                "versatility": min(1.0, interest_count / 8),
                "total_weight": round(total_weight, 1),
            }
        finally:
            session.close()

    def _infer_style(self, interests: list) -> str:
        names = [i.name for i in interests]
        if "programmation" in names or "data_science" in names:
            return "analytique"
        if "design" in names:
            return "créatif"
        if "productivité" in names:
            return "structuré"
        if "santé" in names or "sport" in names:
            return "réfléchi"
        return "équilibré"
