# models/journal.py

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import date
from models.database import Base

class Journal(Base):
    __tablename__ = "journals"
    __table_args__ = (
        Index("ix_journals_user_date", "utilisateur_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    contenu = Column(Text, nullable=False)

    user = relationship("User", back_populates="journals")

    def __repr__(self):
        return f"<Journal(date={self.date}, contenu={self.contenu[:30]}...)>"