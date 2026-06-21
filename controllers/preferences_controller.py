# controllers/preferences_controller.py

import logging
from models.database import get_session
from models.user_preference import UserPreference


class PreferencesController:

    def __init__(self, user_id):
        self.user_id = user_id

    def get_preferences(self):
        session = get_session()
        try:
            prefs = session.query(UserPreference).filter_by(utilisateur_id=self.user_id).first()
            if prefs:
                return prefs
            prefs = UserPreference(utilisateur_id=self.user_id)
            session.add(prefs)
            session.commit()
            session.refresh(prefs)
            return prefs
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur lors de la récupération des préférences")
            session.rollback()
            return UserPreference(utilisateur_id=self.user_id)
        finally:
            session.close()

    def set_theme(self, theme):
        session = get_session()
        try:
            prefs = session.query(UserPreference).filter_by(utilisateur_id=self.user_id).first()
            if not prefs:
                prefs = UserPreference(utilisateur_id=self.user_id)
                session.add(prefs)
            prefs.theme = theme
            session.commit()
            return True
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur lors du changement de thème")
            session.rollback()
            return False
        finally:
            session.close()

    def set_notif(self, notif_type, value):
        session = get_session()
        try:
            prefs = session.query(UserPreference).filter_by(utilisateur_id=self.user_id).first()
            if not prefs:
                prefs = UserPreference(utilisateur_id=self.user_id)
                session.add(prefs)
            setattr(prefs, f"notif_{notif_type}", value)
            session.commit()
            return True
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur lors du changement de notification")
            session.rollback()
            return False
        finally:
            session.close()

    def get_theme(self):
        prefs = self.get_preferences()
        return prefs.theme if prefs else "light"

    def should_notif(self, notif_type):
        prefs = self.get_preferences()
        if not prefs:
            return True
        return getattr(prefs, f"notif_{notif_type}", True)

    def should_play_sound(self):
        prefs = self.get_preferences()
        if not prefs:
            return True
        return prefs.notif_sound

    def is_onboarding_complete(self):
        prefs = self.get_preferences()
        return prefs.onboarding_complete if prefs else False

    def complete_onboarding(self, goal="", wake_time="07:00"):
        session = get_session()
        try:
            prefs = session.query(UserPreference).filter_by(utilisateur_id=self.user_id).first()
            if not prefs:
                prefs = UserPreference(utilisateur_id=self.user_id)
                session.add(prefs)
            prefs.onboarding_complete = True
            prefs.main_goal = goal
            prefs.wake_time = wake_time
            session.commit()
            return True
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur lors du complétion de l'onboarding")
            session.rollback()
            return False
        finally:
            session.close()
