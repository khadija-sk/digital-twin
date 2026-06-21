from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ModelInfo:
    name: str
    display_name: str
    provider: str
    status: str
    context_window: int
    is_active: bool = False
    description: str = ""


@dataclass
class GenerationConfig:
    temperature: float = 0.7
    max_output_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40


class LLMProvider:
    def __init__(self, api_key: str, model_name: str = ""):
        self.api_key = api_key
        self.model_name = model_name

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        raise NotImplementedError

    def chat_stream(self, system_prompt: str, message: str, history: list[dict] | None = None):
        raise NotImplementedError

    def generate_content(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_embeddings(self, text: str) -> list[float]:
        raise NotImplementedError

    def discover_models(self) -> list[ModelInfo]:
        raise NotImplementedError

    def verify_connection(self) -> tuple[bool, str]:
        raise NotImplementedError

    @classmethod
    def from_config(cls, config: "LLMConfig") -> "LLMProvider":
        raise NotImplementedError


class LLMConfig:
    def __init__(
        self,
        provider: str = "gemini",
        api_key: str = "",
        model_name: str = "",
        generation: GenerationConfig | None = None,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.generation = generation or GenerationConfig()
