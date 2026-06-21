# models/daily_log.py

from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import date
from models.database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (
        Index("ix_daily_logs_user_date", "utilisateur_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    humeur = Column(Integer, nullable=False)
    energie = Column(Integer, nullable=False)
    sommeil = Column(Float, nullable=False)
    score_productivite = Column(Integer, nullable=True)

    user = relationship("User", back_populates="logs")

    def __repr__(self):
        return f"<DailyLog(date={self.date}, humeur={self.humeur}, energie={self.energie}, sommeil={self.sommeil})>"