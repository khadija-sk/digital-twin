# controllers/auth_controller.py

import bcrypt
import secrets
from datetime import datetime, timedelta
from models.database import get_session
from models.user import User


class UserData:
    def __init__(self, id, nom, email, xp_total=0, niveau=1, date_creation=None):
        self.id = id
        self.nom = nom
        self.email = email
        self.xp_total = xp_total
        self.niveau = niveau
        self.date_creation = date_creation


class AuthController:

    def __init__(self):
        self.current_user  = None
        self.last_activity = None

    # ─────────────────────────────────────────
    # REGISTER (inchangé)
    # ─────────────────────────────────────────
    def register(self, nom, email, password):
        session = get_session()
        try:
            existing = session.query(User).filter_by(email=email).first()
            if existing:
                return False, "Cet email est déjà utilisé"

            if len(password) < 6:
                return False, "Le mot de passe doit avoir au moins 6 caractères"

            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            new_user = User(
                nom=nom,
                email=email,
                password_hash=password_hash
            )
            session.add(new_user)
            session.commit()
            return True, "Compte créé avec succès !"

        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    # ─────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────
    def login(self, email, password):
        session = get_session()
        try:
            user = session.query(User).filter_by(email=email).first()

            if not user:
                return False, "Email ou mot de passe incorrect"

            password_correct = bcrypt.checkpw(
                password.encode('utf-8'),
                user.password_hash.encode('utf-8')
            )

            if not password_correct:
                return False, "Email ou mot de passe incorrect"

            session.refresh(user)
            user_obj = UserData(
                id=user.id,
                nom=user.nom,
                email=user.email,
                xp_total=user.xp_total,
                niveau=user.niveau,
                date_creation=user.date_creation,
            )

            self.current_user  = user_obj
            self.last_activity = datetime.now()

            return True, user_obj

        except Exception as e:
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    # ─────────────────────────────────────────
    # LOGOUT (inchangé)
    # ─────────────────────────────────────────
    def logout(self):
        self.current_user  = None
        self.last_activity = None

    # ─────────────────────────────────────────
    # TIMEOUT (inchangé)
    # ─────────────────────────────────────────
    def check_timeout(self):
        if not self.current_user or not self.last_activity:
            return False
        if datetime.now() - self.last_activity > timedelta(minutes=10):
            self.logout()
            return True
        return False

    def update_activity(self):
        self.last_activity = datetime.now()

    def is_logged_in(self):
        return self.current_user is not None

    def get_current_user(self):
        return self.current_user

    # ─────────────────────────────────────────
    # 🔥 NOUVEAU : DEMANDE DE RÉINITIALISATION
    # ─────────────────────────────────────────
    def request_password_reset(self, email):
        """
        Génère un token, l'enregistre en BDD avec une expiration (15 min),
        et retourne le token (simulation d'envoi par email).
        """
        session = get_session()
        try:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                return False, "Aucun compte associé à cet email"

            # Génération d'un token sécurisé
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(minutes=15)

            user.reset_token = token
            user.reset_token_expiry = expiry
            session.commit()

            # Dans un vrai système, on enverrait l'email ici
            # Pour la simulation, on retourne le token pour l'afficher à l'utilisateur
            return True, token

        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    # ─────────────────────────────────────────
    # 🔥 NOUVEAU : RÉINITIALISATION AVEC TOKEN
    # ─────────────────────────────────────────
    def reset_password(self, token, new_password):
        """
        Vérifie le token et met à jour le mot de passe si valide.
        """
        if len(new_password) < 6:
            return False, "Le mot de passe doit avoir au moins 6 caractères"

        session = get_session()
        try:
            user = session.query(User).filter_by(reset_token=token).first()
            if not user:
                return False, "Token invalide"

            if user.reset_token_expiry is None or user.reset_token_expiry < datetime.utcnow():
                return False, "Token expiré (15 min)"

            # Mise à jour du mot de passe
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            user.password_hash = password_hash

            # Invalidation du token
            user.reset_token = None
            user.reset_token_expiry = None
            session.commit()

            return True, "Mot de passe réinitialisé avec succès"

        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()