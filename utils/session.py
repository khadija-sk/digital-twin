import time
from typing import Optional


class SessionManager:
    _instance: Optional["SessionManager"] = None

    def __init__(self, timeout_minutes: int = 10):
        self._timeout = timeout_minutes * 60
        self._last_activity: float = 0.0
        self._active: bool = False
        self._user_id: Optional[int] = None

    @classmethod
    def initialize(cls, timeout_minutes: int = 10) -> "SessionManager":
        if cls._instance is None:
            cls._instance = cls(timeout_minutes)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Optional["SessionManager"]:
        return cls._instance

    def start_session(self, user_id: int):
        self._active = True
        self._user_id = user_id
        self._last_activity = time.time()

    def end_session(self):
        self._active = False
        self._user_id = None
        self._last_activity = 0.0

    def update_activity(self):
        if self._active:
            self._last_activity = time.time()

    def is_expired(self) -> bool:
        if not self._active:
            return True
        return (time.time() - self._last_activity) > self._timeout

    @property
    def user_id(self) -> Optional[int]:
        return self._user_id

    @property
    def is_active(self) -> bool:
        return self._active and not self.is_expired()

    @property
    def seconds_until_expiry(self) -> float:
        if not self._active:
            return 0.0
        elapsed = time.time() - self._last_activity
        return max(0.0, self._timeout - elapsed)
