from typing import Generator, Optional
import json
import requests

from services.llm.base_provider import LLMProvider, LLMConfig, ModelInfo, GenerationConfig

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "tinyllama:latest"


class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "", model_name: str = ""):
        super().__init__("", model_name or DEFAULT_MODEL)
        self.host = (host or DEFAULT_HOST).rstrip("/")
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def _build_messages(self, system_prompt: str, message: str, history: list[dict] | None) -> list[dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for msg in history:
                role = msg.get("role", "user")
                if role == "model":
                    role = "assistant"
                parts = msg.get("parts", [])
                text = ""
                for p in parts:
                    if isinstance(p, str):
                        text += p
                    elif isinstance(p, dict) and "text" in p:
                        text += p["text"]
                if text:
                    messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": message})
        return messages

    def _chat_request(self, messages: list[dict], stream: bool = False) -> requests.Response:
        return self._session.post(
            f"{self.host}/api/chat",
            headers=self._headers(),
            json={"model": self.model_name, "messages": messages, "stream": stream},
            timeout=300,
        )

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        messages = self._build_messages(system_prompt, message, history)
        resp = self._chat_request(messages, stream=False)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        messages = self._build_messages(system_prompt, message, history)
        resp = self._chat_request(messages, stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
                if data.get("done"):
                    return
            except json.JSONDecodeError:
                continue

    def generate_content(self, prompt: str) -> str:
        return self.chat("", prompt, None)

    def generate_embeddings(self, text: str) -> list[float]:
        resp = self._session.post(
            f"{self.host}/api/embeddings",
            headers=self._headers(),
            json={"model": self.model_name, "prompt": text},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("embedding", [])

    def discover_models(self) -> list[ModelInfo]:
        try:
            resp = self._session.get(f"{self.host}/api/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                models.append(ModelInfo(
                    name=name,
                    display_name=name,
                    provider="Ollama (local)",
                    status="Online",
                    context_window=8192,
                    is_active=(name == self.model_name),
                ))
            return models
        except Exception:
            return self._fallback_models()

    def _fallback_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                name="llama3.2", display_name="Llama 3.2",
                provider="Ollama (local)", status="Online",
                context_window=8192, is_active=("llama3.2" == self.model_name),
            ),
            ModelInfo(
                name="llama3.1", display_name="Llama 3.1",
                provider="Ollama (local)", status="Online",
                context_window=8192, is_active=("llama3.1" == self.model_name),
            ),
            ModelInfo(
                name="mistral", display_name="Mistral",
                provider="Ollama (local)", status="Online",
                context_window=8192, is_active=("mistral" == self.model_name),
            ),
            ModelInfo(
                name="gemma2", display_name="Gemma 2",
                provider="Ollama (local)", status="Online",
                context_window=8192, is_active=("gemma2" == self.model_name),
            ),
        ]

    def verify_connection(self) -> tuple[bool, str]:
        try:
            resp = self._session.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return True, f"Ollama connecté ({self.host})"
            return False, f"Ollama retourne {resp.status_code}"
        except requests.ConnectionError:
            return False, f"Ollama inaccessible sur {self.host}. Vérifie qu'Ollama est lancé."
        except Exception as e:
            return False, str(e)
