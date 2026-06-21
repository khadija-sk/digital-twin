# models/objective.py

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import date
from models.database import Base

class Objective(Base):
    __tablename__ = "objectives"
    __table_args__ = (
        Index("ix_objectives_user_statut", "utilisateur_id", "statut"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
    valeur_cible = Column(Float, nullable=False)
    unite = Column(String(20), default="heures", nullable=True)
    date_creation = Column(Date, default=date.today, nullable=False)
    statut = Column(String(20), default="actif", nullable=False)

    user = relationship("User", back_populates="objectives")

    def __repr__(self):
        return f"<Objective(description={self.description}, cible={self.valeur_cible}, statut={self.statut})>"