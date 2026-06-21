from typing import Generator, Optional
import requests

from services.llm.base_provider import LLMProvider, LLMConfig, ModelInfo, GenerationConfig

BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-2-1212"


class GrokProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = ""):
        super().__init__(api_key, model_name or DEFAULT_MODEL)
        self.base_url = BASE_URL
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

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

    def _chat_request(self, messages: list[dict], stream: bool = False,
                      generation: GenerationConfig | None = None) -> requests.Response:
        body = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
        }
        if generation:
            body["temperature"] = generation.temperature
            body["max_tokens"] = generation.max_output_tokens
            body["top_p"] = generation.top_p
        return self._session.post(
            f"{self.base_url}/chat/completions",
            json=body,
            timeout=300,
        )

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        messages = self._build_messages(system_prompt, message, history)
        resp = self._chat_request(messages, stream=False)
        if resp.status_code == 401:
            raise RuntimeError("Clé API xAI invalide")
        if resp.status_code == 429:
            raise RuntimeError("Rate limit xAI atteint — réessaie plus tard")
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("xAI n'a retourné aucune réponse")
        return choices[0].get("message", {}).get("content", "")

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
        generation: GenerationConfig | None = None,
    ) -> Generator[str, None, None]:
        messages = self._build_messages(system_prompt, message, history)
        resp = self._chat_request(messages, stream=True, generation=generation)
        if resp.status_code == 401:
            raise RuntimeError("Clé API xAI invalide")
        if resp.status_code == 429:
            raise RuntimeError("Rate limit xAI atteint — réessaie plus tard")
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                return
            import json
            try:
                data = json.loads(payload)
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
            except json.JSONDecodeError:
                continue

    def generate_content(self, prompt: str, generation: GenerationConfig | None = None) -> str:
        return self.chat("", prompt, None)

    def generate_embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("xAI ne supporte pas les embeddings via l'API OpenAI-compatible")

    def discover_models(self) -> list[ModelInfo]:
        return self._fallback_models()

    def _fallback_models(self) -> list[ModelInfo]:
        names = [
            ("grok-2-1212", "Grok 2"),
            ("grok-2-vision-1212", "Grok 2 Vision"),
            ("grok-beta", "Grok Beta"),
        ]
        return [
            ModelInfo(
                name=n,
                display_name=d,
                provider="xAI (Grok)",
                status="Online",
                context_window=131_072,
                is_active=(n == self.model_name),
            )
            for n, d in names
        ]

    def verify_connection(self) -> tuple[bool, str]:
        try:
            resp = self._session.get(f"{self.base_url}/models", timeout=10)
            if resp.status_code == 200:
                return True, "xAI connecté"
            if resp.status_code == 401:
                return False, "Clé API xAI invalide"
            return False, f"xAI retourne {resp.status_code}"
        except requests.ConnectionError:
            return False, "Impossible de se connecter à l'API xAI"
        except requests.Timeout:
            return False, "Timeout de connexion à l'API xAI"
        except Exception as e:
            return False, str(e)

    @classmethod
    def from_config(cls, config: LLMConfig) -> "GrokProvider":
        return cls(config.api_key, config.model_name)
