from typing import Generator, Optional
import anthropic

from services.llm.base_provider import LLMProvider, LLMConfig, ModelInfo, GenerationConfig

KNOWN_MODELS = [
    ("claude-sonnet-4-20250514", "Claude Sonnet 4"),
    ("claude-3-5-haiku-latest", "Claude 3.5 Haiku"),
    ("claude-3-opus-20240229", "Claude 3 Opus"),
    ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
    ("claude-3-haiku-20240307", "Claude 3 Haiku"),
]

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = ""):
        super().__init__(api_key, model_name or DEFAULT_MODEL)
        self.client = anthropic.Anthropic(api_key=api_key)

    def _build_system(self, system_prompt: str) -> list[dict]:
        return [{"type": "text", "text": system_prompt}]

    def _make_messages(self, message: str, history: list[dict] | None) -> list[dict]:
        messages = []
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

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        system = self._build_system(system_prompt)
        messages = self._make_messages(message, history)
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
        generation: GenerationConfig | None = None,
    ) -> Generator[str, None, None]:
        system = self._build_system(system_prompt)
        messages = self._make_messages(message, history)
        max_tokens = generation.max_output_tokens if generation else 4096
        with self.client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def generate_content(self, prompt: str, generation: GenerationConfig | None = None) -> str:
        max_tokens = generation.max_output_tokens if generation else 4096
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def generate_embeddings(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model="claude-3-haiku-20240307",
            input=text,
        )
        return response.embedding

    def discover_models(self) -> list[ModelInfo]:
        return self._fallback_models()

    def _fallback_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                name=n,
                display_name=d,
                provider="Anthropic",
                status="Online",
                context_window=200_000,
                is_active=(n == self.model_name),
            )
            for n, d in KNOWN_MODELS
        ]

    def verify_connection(self) -> tuple[bool, str]:
        for model_name, _ in KNOWN_MODELS:
            try:
                self.client.messages.create(
                    model=model_name,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
                self.model_name = model_name
                return True, f"Connecté via {model_name}"
            except Exception:
                continue
        return False, "Aucun modèle Claude disponible"

    @classmethod
    def from_config(cls, config: LLMConfig) -> "AnthropicProvider":
        return cls(config.api_key, config.model_name)
