# models/study_session.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class StudySession(Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        Index("ix_study_sessions_user_statut_date", "utilisateur_id", "statut", "date_heure_debut"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_heure_debut = Column(DateTime, default=datetime.utcnow, nullable=False)
    duree = Column(Integer, default=25, nullable=False)
    statut = Column(String(20), default="complete", nullable=False)
    energie_mi_session = Column(Integer, nullable=True)

    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<StudySession(date={self.date_heure_debut}, duree={self.duree}, statut={self.statut})>"