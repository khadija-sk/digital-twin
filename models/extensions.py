from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models.database import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="general")
    memory_type = Column(String(30), default="episodic")
    importance = Column(Float, default=0.5)
    embedding = Column(Text, nullable=True)
    source = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=1)

    user = relationship("User")


class MemorySummary(Base):
    __tablename__ = "memory_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class AcademicCourse(Base):
    __tablename__ = "academic_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    code = Column(String(50), default="")
    instructor = Column(String(200), default="")
    semester = Column(String(50), default="")
    credits = Column(Integer, default=0)
    grade = Column(String(10), default="")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    assignments = relationship("AcademicAssignment", back_populates="course", cascade="all, delete")


class AcademicAssignment(Base):
    __tablename__ = "academic_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("academic_courses.id", ondelete="CASCADE"), nullable=False)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    grade = Column(String(10), default="")
    priority = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("AcademicCourse", back_populates="assignments")


class StudySubject(Base):
    __tablename__ = "study_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    total_hours = Column(Float, default=0.0)
    session_count = Column(Integer, default=0)
    last_studied = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), default="general")
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(10), default="📌")
    event_date = Column(DateTime, default=datetime.utcnow)
    importance = Column(Float, default=0.5)
    metadata_json = Column(Text, default="{}")

    user = relationship("User")


class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50), default="general")
    weight = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
