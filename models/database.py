# models/database.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "digital_twin.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def init_db():
    from models.user import User
    from models.daily_log import DailyLog
    from models.study_session import StudySession
    from models.badge import Badge
    from models.objective import Objective
    from models.journal import Journal
    from models.user_preference import UserPreference
    from models.extensions import MemoryEntry, MemorySummary, AcademicCourse, AcademicAssignment, StudySubject, TimelineEvent, UserInterest

    Base.metadata.create_all(bind=engine)

    conn = engine.connect()
    try:
        conn.execute(text("ALTER TABLE user_preferences ADD COLUMN onboarding_complete BOOLEAN DEFAULT 0"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE user_preferences ADD COLUMN main_goal VARCHAR(200) DEFAULT ''"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE user_preferences ADD COLUMN wake_time VARCHAR(10) DEFAULT '07:00'"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE timeline_events ADD COLUMN icon VARCHAR(10) DEFAULT '📌'"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE timeline_events ADD COLUMN importance FLOAT DEFAULT 0.5"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE user_interests ADD COLUMN name VARCHAR(200)"))
    except Exception:
        pass
    try:
        conn.execute(text("UPDATE user_interests SET name = interest WHERE name IS NULL"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE user_interests ADD COLUMN weight FLOAT DEFAULT 1.0"))
    except Exception:
        pass
    try:
        conn.execute(text("UPDATE user_interests SET weight = strength WHERE weight IS NULL"))
    except Exception:
        pass
    finally:
        conn.close()

    print("Base de donnees initialisee avec succes")

def get_session():
    return SessionLocal()