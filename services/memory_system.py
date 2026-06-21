import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from models.database import get_session
from models.extensions import MemoryEntry, MemorySummary


logger = logging.getLogger(__name__)


class MemorySystem:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def store(self, content: str, category: str = "general", memory_type: str = "episodic",
              importance: float = 0.5, source: str = "", embedding: Optional[list[float]] = None):
        session = get_session()
        try:
            entry = MemoryEntry(
                utilisateur_id=self.user_id, content=content, category=category,
                memory_type=memory_type, importance=importance,
                embedding=json.dumps(embedding) if embedding else None,
                source=source,
            )
            session.add(entry)
            session.commit()
            self._trim_if_needed(session)
            return entry.id
        except Exception as e:
            logger.exception("Error storing memory")
            session.rollback()
            return None
        finally:
            session.close()

    def retrieve(self, query_embedding: Optional[list[float]] = None, category: str = "",
                 limit: int = 10, min_importance: float = 0.0) -> list[dict]:
        session = get_session()
        try:
            query = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.importance >= min_importance,
            )
            if category:
                query = query.filter(MemoryEntry.category == category)
            entries = query.order_by(MemoryEntry.last_accessed.desc()).limit(limit * 3).all()

            if query_embedding and entries:
                entries = self._rank_by_similarity(entries, query_embedding)[:limit]

            results = []
            for e in entries:
                e.access_count += 1
                e.last_accessed = datetime.utcnow()
                results.append({
                    "id": e.id, "content": e.content, "category": e.category,
                    "memory_type": e.memory_type, "importance": e.importance,
                    "source": e.source, "created_at": e.created_at.isoformat(),
                })
            session.commit()
            return results
        except Exception as e:
            logger.exception("Error retrieving memories")
            return []
        finally:
            session.close()

    def search_by_keyword(self, keyword: str, limit: int = 10) -> list[dict]:
        session = get_session()
        try:
            entries = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.content.ilike(f"%{keyword}%"),
            ).order_by(MemoryEntry.importance.desc()).limit(limit).all()

            return [{
                "id": e.id, "content": e.content, "category": e.category,
                "memory_type": e.memory_type, "importance": e.importance,
                "source": e.source, "created_at": e.created_at.isoformat(),
            } for e in entries]
        finally:
            session.close()

    def get_summary(self, category: str = "general", days: int = 7) -> str:
        session = get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            entries = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.category == category,
                MemoryEntry.created_at >= cutoff,
            ).order_by(MemoryEntry.importance.desc()).all()

            if not entries:
                return ""
            texts = [f"[{e.created_at.date()}] {e.content}" for e in entries[:5]]
            return "\n".join(texts)
        finally:
            session.close()

    def get_context_for_prompt(self, question: str = "", limit: int = 5) -> str:
        memories = self.retrieve(category="", limit=limit)
        if not memories:
            return ""
        lines = []
        for m in memories:
            cat = m["category"]
            lines.append(f"[{cat}] {m['content']}")
        return "\n".join(lines)

    def update_importance(self, memory_id: int, delta: float = 0.1):
        session = get_session()
        try:
            entry = session.query(MemoryEntry).filter_by(id=memory_id).first()
            if entry:
                entry.importance = min(1.0, max(0.0, entry.importance + delta))
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def create_summary(self, period_start: datetime, period_end: datetime, category: str = "general"):
        session = get_session()
        try:
            entries = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.category == category,
                MemoryEntry.created_at >= period_start,
                MemoryEntry.created_at <= period_end,
            ).order_by(MemoryEntry.importance.desc()).all()

            if not entries:
                return None
            combined = " | ".join([e.content[:200] for e in entries[:10]])
            summary = MemorySummary(
                utilisateur_id=self.user_id, summary=combined,
                period_start=period_start, period_end=period_end, category=category,
            )
            session.add(summary)
            session.commit()
            return summary.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()

    def get_timeline_events(self, days: int = 30) -> list[dict]:
        session = get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            entries = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id,
                MemoryEntry.created_at >= cutoff,
            ).order_by(MemoryEntry.created_at.desc()).limit(50).all()

            return [{
                "date": e.created_at.isoformat(), "title": e.content[:80],
                "category": e.category, "type": e.memory_type,
            } for e in entries]
        finally:
            session.close()

    def _rank_by_similarity(self, entries: list, query_embedding: list[float]) -> list:
        scored = []
        for e in entries:
            if e.embedding:
                try:
                    stored = json.loads(e.embedding)
                    sim = self._cosine_similarity(query_embedding, stored)
                    score = sim * 0.7 + e.importance * 0.3
                    scored.append((score, e))
                except Exception:
                    scored.append((e.importance, e))
            else:
                scored.append((e.importance * 0.5, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        arr_a = np.array(a)
        arr_b = np.array(b)
        if np.linalg.norm(arr_a) == 0 or np.linalg.norm(arr_b) == 0:
            return 0.0
        return float(np.dot(arr_a, arr_b) / (np.linalg.norm(arr_a) * np.linalg.norm(arr_b)))

    def _trim_if_needed(self, session, max_entries: int = 500):
        count = session.query(MemoryEntry).filter(
            MemoryEntry.utilisateur_id == self.user_id
        ).count()
        if count > max_entries:
            old = session.query(MemoryEntry).filter(
                MemoryEntry.utilisateur_id == self.user_id
            ).order_by(MemoryEntry.last_accessed.asc()).limit(count - max_entries).all()
            for e in old:
                session.delete(e)
            session.commit()
