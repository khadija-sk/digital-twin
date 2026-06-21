import logging
from datetime import datetime, timedelta
from models.database import get_session
from models.extensions import AcademicCourse, AcademicAssignment, StudySubject


logger = logging.getLogger(__name__)


class AcademicService:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def add_course(self, name: str, code: str = "", instructor: str = "",
                    semester: str = "", credits: int = 0) -> Optional[int]:
        session = get_session()
        try:
            course = AcademicCourse(
                utilisateur_id=self.user_id, name=name, code=code,
                instructor=instructor, semester=semester, credits=credits,
            )
            session.add(course)
            session.commit()
            return course.id
        except Exception as e:
            logger.exception("Error adding course")
            session.rollback()
            return None
        finally:
            session.close()

    def get_all_courses(self) -> list[dict]:
        session = get_session()
        try:
            courses = session.query(AcademicCourse).filter_by(
                utilisateur_id=self.user_id
            ).order_by(AcademicCourse.created_at.desc()).all()
            return [self._course_to_dict(c) for c in courses]
        finally:
            session.close()

    def add_assignment(self, course_id: int, title: str, description: str = "",
                       due_date: Optional[datetime] = None, priority: int = 3) -> Optional[int]:
        session = get_session()
        try:
            assignment = AcademicAssignment(
                course_id=course_id, utilisateur_id=self.user_id,
                title=title, description=description,
                due_date=due_date, priority=priority,
            )
            session.add(assignment)
            session.commit()
            return assignment.id
        except Exception as e:
            logger.exception("Error adding assignment")
            session.rollback()
            return None
        finally:
            session.close()

    def get_assignments(self, course_id: Optional[int] = None,
                        upcoming_days: int = 30) -> list[dict]:
        session = get_session()
        try:
            query = session.query(AcademicAssignment).filter_by(
                utilisateur_id=self.user_id, completed=False
            )
            if course_id:
                query = query.filter_by(course_id=course_id)
            if upcoming_days:
                cutoff = datetime.utcnow() + timedelta(days=upcoming_days)
                query = query.filter(
                    AcademicAssignment.due_date <= cutoff
                ) if cutoff else query
            assignments = query.order_by(AcademicAssignment.due_date.asc()).all()
            return [self._assignment_to_dict(a) for a in assignments]
        finally:
            session.close()

    def complete_assignment(self, assignment_id: int, grade: str = ""):
        session = get_session()
        try:
            a = session.query(AcademicAssignment).filter_by(id=assignment_id).first()
            if a:
                a.completed = True
                if grade:
                    a.grade = grade
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def record_study_session(self, subject_name: str, hours: float):
        session = get_session()
        try:
            sub = session.query(StudySubject).filter_by(
                utilisateur_id=self.user_id, name=subject_name
            ).first()
            if not sub:
                sub = StudySubject(utilisateur_id=self.user_id, name=subject_name)
                session.add(sub)
            sub.total_hours = (sub.total_hours or 0) + hours
            sub.session_count = (sub.session_count or 0) + 1
            sub.last_studied = datetime.utcnow()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_study_subjects(self) -> list[dict]:
        session = get_session()
        try:
            subjects = session.query(StudySubject).filter_by(
                utilisateur_id=self.user_id
            ).order_by(StudySubject.total_hours.desc()).all()
            return [{
                "id": s.id, "name": s.name, "total_hours": s.total_hours or 0,
                "session_count": s.session_count or 0,
                "last_studied": s.last_studied.isoformat() if s.last_studied else None,
            } for s in subjects]
        finally:
            session.close()

    def get_upcoming_deadlines(self, days: int = 14) -> list[dict]:
        assignments = self.get_assignments(upcoming_days=days)
        return [a for a in assignments if a.get("due_date")]

    def get_exam_readiness(self) -> dict:
        courses = self.get_all_courses()
        subjects = self.get_study_subjects()
        assignments = self.get_assignments(upcoming_days=30)
        total_hours = sum(s["total_hours"] for s in subjects)
        pending = sum(1 for a in assignments if not a.get("completed", True))
        readiness = min(100, max(0, int(total_hours / max(len(courses), 1) * 10 - pending * 5)))
        return {
            "readiness": readiness,
            "total_hours": total_hours,
            "courses": len(courses),
            "pending_assignments": pending,
            "subjects": len(subjects),
        }

    def _course_to_dict(self, c) -> dict:
        return {
            "id": c.id, "name": c.name, "code": c.code,
            "instructor": c.instructor, "semester": c.semester,
            "credits": c.credits, "grade": c.grade, "status": c.status,
        }

    def _assignment_to_dict(self, a) -> dict:
        return {
            "id": a.id, "course_id": a.course_id, "title": a.title,
            "description": a.description,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "completed": a.completed, "grade": a.grade, "priority": a.priority,
        }
