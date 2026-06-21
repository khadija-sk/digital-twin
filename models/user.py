# models/user.py

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_reset_token", "reset_token"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    xp_total = Column(Integer, default=0)
    niveau = Column(Integer, default=1)

    # 🔥 Nouveaux champs pour la réinitialisation
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)

    logs = relationship("DailyLog", back_populates="user", cascade="all, delete")
    sessions = relationship("StudySession", back_populates="user", cascade="all, delete")
    badges = relationship("Badge", back_populates="user", cascade="all, delete")
    objectives = relationship("Objective", back_populates="user", cascade="all, delete")
    journals = relationship("Journal", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, nom={self.nom}, email={self.email})>"