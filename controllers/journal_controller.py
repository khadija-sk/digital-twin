# controllers/journal_controller.py

from datetime import date, timedelta
from models.database import get_session
from models.journal import Journal

class JournalController:

    def __init__(self, user_id):
        self.user_id = user_id

    def save_entry(self, contenu, entry_date=None):
        if entry_date is None:
            entry_date = date.today()
        if not contenu.strip():
            return False, "Le contenu ne peut pas être vide."
        session = get_session()
        try:
            existing = session.query(Journal).filter_by(utilisateur_id=self.user_id, date=entry_date).first()
            if existing:
                existing.contenu = contenu.strip()
                session.commit()
                session.refresh(existing)
                return True, existing
            else:
                entry = Journal(utilisateur_id=self.user_id, date=entry_date, contenu=contenu.strip())
                session.add(entry)
                session.commit()
                session.refresh(entry)
                return True, entry
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    def get_today_entry(self):
        session = get_session()
        try:
            return session.query(Journal).filter_by(utilisateur_id=self.user_id, date=date.today()).first()
        finally:
            session.close()

    def get_all_entries(self):
        session = get_session()
        try:
            return session.query(Journal).filter_by(utilisateur_id=self.user_id).order_by(Journal.date.desc()).all()
        finally:
            session.close()

    def get_last_n_entries(self, n=10):
        session = get_session()
        try:
            return session.query(Journal).filter_by(utilisateur_id=self.user_id).order_by(Journal.date.desc()).limit(n).all()
        finally:
            session.close()

    def get_entry_by_date(self, entry_date):
        session = get_session()
        try:
            return session.query(Journal).filter_by(utilisateur_id=self.user_id, date=entry_date).first()
        finally:
            session.close()

    def delete_entry(self, entry_id):
        session = get_session()
        try:
            entry = session.query(Journal).filter_by(id=entry_id, utilisateur_id=self.user_id).first()
            if entry:
                session.delete(entry)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def get_total_entries(self):
        session = get_session()
        try:
            return session.query(Journal).filter_by(utilisateur_id=self.user_id).count()
        finally:
            session.close()

    def has_entry_today(self):
        return self.get_today_entry() is not None

    def get_streak(self):
        session = get_session()
        try:
            entries = session.query(Journal).filter_by(utilisateur_id=self.user_id).order_by(Journal.date.desc()).limit(31).all()
            if not entries:
                return 0
            streak = 0
            check_date = date.today()
            for entry in entries:
                if entry.date == check_date:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
            return streak
        finally:
            session.close()