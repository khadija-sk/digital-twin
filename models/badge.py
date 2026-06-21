# models/badge.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import date
from models.database import Base

class Badge(Base):
    __tablename__ = "badges"
    __table_args__ = (
        Index("ix_badges_user", "utilisateur_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nom = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    date_obtention = Column(Date, default=date.today, nullable=False)
    xp_gagne = Column(Integer, default=10, nullable=False)
    icone = Column(String(10), default="*", nullable=True)

    user = relationship("User", back_populates="badges")

    def __repr__(self):
        return f"<Badge(nom={self.nom}, xp={self.xp_gagne}, date={self.date_obtention})>"