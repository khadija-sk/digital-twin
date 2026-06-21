import json
import logging
from datetime import datetime, timedelta
from models.database import get_session
from models.extensions import TimelineEvent

logger = logging.getLogger(__name__)

TIMELINE_ICONS = {
    "journal": "📝", "study": "📚", "exam": "🎓", "project": "💼",
    "sport": "🏃", "health": "💊", "social": "👥", "hobby": "🎨",
    "work": "💻", "travel": "✈️", "achievement": "🏆", "general": "📌",
}


class TimelineService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def add_event(self, title: str, description: str = "", event_type: str = "general",
                  date: Optional[datetime] = None, importance: float = 0.5,
                  icon: str = "") -> Optional[int]:
        session = get_session()
        try:
            event = TimelineEvent(
                utilisateur_id=self.user_id, title=title, description=description,
                event_type=event_type, event_date=date or datetime.utcnow(),
                importance=importance, icon=icon or TIMELINE_ICONS.get(event_type, "📌"),
            )
            session.add(event)
            session.commit()
            return event.id
        except Exception as e:
            logger.exception("Error adding timeline event")
            session.rollback()
            return None
        finally:
            session.close()

    def get_events(self, days: int = 30, event_type: str = "",
                   limit: int = 50, offset: int = 0) -> list[dict]:
        session = get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = session.query(TimelineEvent).filter(
                TimelineEvent.utilisateur_id == self.user_id,
                TimelineEvent.event_date >= cutoff,
            )
            if event_type:
                query = query.filter(TimelineEvent.event_type == event_type)
            events = query.order_by(TimelineEvent.event_date.desc()).offset(offset).limit(limit).all()
            return [{
                "id": e.id, "title": e.title, "description": e.description,
                "type": e.event_type, "icon": e.icon,
                "date": e.event_date.isoformat(),
                "importance": e.importance,
            } for e in events]
        finally:
            session.close()

    def get_events_grouped(self, days: int = 30) -> list[dict]:
        events = self.get_events(days)
        grouped = {}
        for e in events:
            day = e["date"][:10]
            if day not in grouped:
                grouped[day] = {"date": day, "events": []}
            grouped[day]["events"].append(e)
        return sorted(grouped.values(), key=lambda x: x["date"], reverse=True)

    def delete_event(self, event_id: int):
        session = get_session()
        try:
            event = session.query(TimelineEvent).filter_by(id=event_id).first()
            if event:
                session.delete(event)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def add_from_daily_log(self, daily_log: dict):
        title = daily_log.get("titre", "Entrée journalière")
        desc = daily_log.get("notes", "")
        mood = daily_log.get("humeur", 3)
        score = daily_log.get("score_productivite", 50)
        date_str = daily_log.get("date")

        if score and score >= 80:
            self.add_event(f"Bonne productivité ({score}%)", desc,
                           "achievement", importance=0.7)

        if mood and mood <= 2:
            self.add_event(f"Humeur difficile ({mood}/5)", desc[:200],
                           "health", importance=0.6 if mood <= 1 else 0.4)

    def get_timeline_summary(self, days: int = 7) -> str:
        events = self.get_events(days=days, limit=5)
        if not events:
            return "Aucun événement récent."
        lines = []
        for e in events:
            day = e["date"][:10]
            lines.append(f"- {e['icon']} [{day}] {e['title']}")
        return "\n".join(lines)
