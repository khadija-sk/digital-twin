class ConversationManager:

    def __init__(self, max_tokens: int = 8000):
        self.history: list[dict] = []
        self.max_tokens = max_tokens

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "parts": [content]})

    def add_model_message(self, content: str):
        self.history.append({"role": "model", "parts": [content]})

    def get_history(self) -> list[dict]:
        return list(self.history)

    def get_recent_history(self, count: int = 10) -> list[dict]:
        return self.history[-count:]

    def clear(self):
        self.history.clear()

    def truncate_history(self):
        while len(self.history) > 30:
            self.history.pop(0)

    def estimate_token_count(self) -> int:
        total = 0
        for msg in self.history:
            for part in msg.get("parts", []):
                if isinstance(part, str):
                    total += len(part) // 4
        return total

    @property
    def message_count(self) -> int:
        return len(self.history)

    @classmethod
    def from_legacy_history(cls, legacy: list[dict]):
        cm = cls()
        for msg in legacy:
            role = msg.get("role", "user")
            if role == "assistant":
                role = "model"
            content = msg.get("content", "")
            cm.history.append({"role": role, "parts": [content]})
        return cm
