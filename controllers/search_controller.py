# controllers/search_controller.py

from datetime import date
from models.database import get_session
from models.journal import Journal
from models.objective import Objective
from models.daily_log import DailyLog


class SearchController:

    def __init__(self, user_id):
        self.user_id = user_id

    def search_all(self, query):
        if not query or not query.strip():
            return []
        q = query.strip().lower()
        results = []
        results.extend(self._search_journals(q))
        results.extend(self._search_goals(q))
        results.extend(self._search_checkins(q))
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        return results[:50]

    def _search_journals(self, query):
        session = get_session()
        try:
            entries = session.query(Journal).filter_by(utilisateur_id=self.user_id).order_by(Journal.date.desc()).all()
            results = []
            for e in entries:
                if query in e.contenu.lower():
                    preview = e.contenu[:150] + ("..." if len(e.contenu) > 150 else "")
                    results.append({
                        "type": "journal",
                        "title": f"Journal - {e.date}",
                        "preview": preview,
                        "date": str(e.date),
                        "icon": "ðŸ““",
                    })
            return results
        finally:
            session.close()

    def _search_goals(self, query):
        session = get_session()
        try:
            goals = session.query(Objective).filter_by(utilisateur_id=self.user_id).order_by(Objective.date_creation.desc()).all()
            results = []
            for g in goals:
                if query in g.description.lower():
                    results.append({
                        "type": "goal",
                        "title": g.description,
                        "preview": f"Cible: {g.valeur_cible} {g.unite or ''} Â· {g.statut}",
                        "date": str(g.date_creation),
                        "icon": "ðŸŽ¯",
                    })
            return results
        finally:
            session.close()

    def _search_checkins(self, query):
        session = get_session()
        try:
            logs = session.query(DailyLog).filter_by(utilisateur_id=self.user_id).order_by(DailyLog.date.desc()).all()
            results = []
            score_strs = [str(l.score_productivite) for l in logs]
            for l in logs:
                if query in str(l.date) or query in str(l.humeur) or query in str(l.energie) or query in str(l.sommeil):
                    results.append({
                        "type": "checkin",
                        "title": f"Check-in - {l.date}",
                        "preview": f"Score: {l.score_productivite}/100 Â· Humeur: {l.humeur}/5 Â· Ã‰nergie: {l.energie}/5 Â· Sommeil: {l.sommeil}h",
                        "date": str(l.date),
                        "icon": "ðŸ“‹",
                    })
            return results
        finally:
            session.close()
