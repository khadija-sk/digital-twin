from datetime import date, datetime, timedelta
from typing import Optional
from models.database import get_session
from models.extensions import AcademicAssignment, TimelineEvent
from models.objective import Objective
from models.study_session import StudySession
from sqlalchemy import func


class UnifiedCalendarService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30,
    ) -> list:
        if start_date is None:
            end_date = date.today() + timedelta(days=days)
            start_date = date.today() - timedelta(days=days // 2)
        if end_date is None:
            end_date = start_date + timedelta(days=days)

        session = get_session()
        try:
            events = []

            deadlines = session.query(AcademicAssignment).filter(
                AcademicAssignment.utilisateur_id == self.user_id,
                func.date(AcademicAssignment.due_date) >= start_date,
                func.date(AcademicAssignment.due_date) <= end_date,
                AcademicAssignment.completed == False,
            ).all()
            for a in deadlines:
                events.append({
                    "type": "deadline",
                    "title": a.title,
                    "description": f"À rendre pour {a.course.name if a.course else 'Cours'}" if a.course else "",
                    "date": a.due_date.date() if hasattr(a.due_date, "date") else a.due_date,
                    "icon": "📝",
                    "source": "Campus",
                    "priority": a.priority or 0.5,
                })

            timeline = session.query(TimelineEvent).filter(
                TimelineEvent.utilisateur_id == self.user_id,
                TimelineEvent.event_date >= start_date,
                TimelineEvent.event_date <= end_date,
            ).all()
            for t in timeline:
                events.append({
                    "type": "timeline",
                    "title": t.title,
                    "description": t.description or "",
                    "date": t.event_date,
                    "icon": t.icon or "📌",
                    "source": "Timeline",
                    "priority": t.importance or 0.5,
                })

            goals = session.query(Objective).filter(
                Objective.utilisateur_id == self.user_id,
                Objective.date_creation >= start_date - timedelta(days=365),
                Objective.statut != "atteint",
            ).all()
            for g in goals:
                ev_date = g.date_creation
                if isinstance(ev_date, datetime):
                    ev_date = ev_date.date()
                events.append({
                    "type": "goal",
                    "title": g.description[:80],
                    "description": f"Objectif {g.statut} — Cible: {g.valeur_cible} {g.unite or ''}",
                    "date": ev_date,
                    "icon": "🎯",
                    "source": "Objectifs",
                    "priority": 0.7,
                })

            sessions_data = session.query(
                func.date(StudySession.date_heure_debut).label("d"),
                func.sum(StudySession.duree).label("total_durée"),
                func.count("*").label("cnt"),
            ).filter(
                StudySession.utilisateur_id == self.user_id,
                StudySession.date_heure_debut >= start_date,
                StudySession.date_heure_debut <= end_date,
                StudySession.statut == "complete",
            ).group_by(func.date(StudySession.date_heure_debut)).all()
            for s in sessions_data:
                hours = (s.total_durée or 0) / 3600
                events.append({
                    "type": "study",
                    "title": f"{s.cnt} session{'s' if s.cnt > 1 else ''} d'étude",
                    "description": f"{hours:.1f}h de travail",
                    "date": s.d,
                    "icon": "📚",
                    "source": "Pomodoro",
                    "priority": 0.3,
                })

            events.sort(key=lambda e: (e["date"], -e["priority"]))
            return events
        finally:
            session.close()

    def get_grouped_events(self, days: int = 30, start_date=None, end_date=None) -> dict:
        if start_date and end_date:
            events = self.get_events(start_date=start_date, end_date=end_date)
        else:
            events = self.get_events(days=days)
        grouped = {}
        for e in events:
            d = e["date"]
            if isinstance(d, datetime):
                d = d.date()
            key = str(d)
            if key not in grouped:
                grouped[key] = {"date": d, "events": []}
            grouped[key]["events"].append(e)
        return dict(sorted(grouped.items()))
