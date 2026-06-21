# models/user_preference.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    theme = Column(String(10), default="light", nullable=False)

    notif_checkin = Column(Boolean, default=True, nullable=False)
    notif_pomodoro = Column(Boolean, default=True, nullable=False)
    notif_badge = Column(Boolean, default=True, nullable=False)
    notif_sound = Column(Boolean, default=True, nullable=False)

    onboarding_complete = Column(Boolean, default=False, nullable=False)
    main_goal = Column(String(200), default="")
    wake_time = Column(String(10), default="07:00")

    user = relationship("User")

    def __repr__(self):
        return f"<UserPreference(user_id={self.utilisateur_id}, theme={self.theme})>"
