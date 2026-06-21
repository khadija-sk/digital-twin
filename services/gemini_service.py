from typing import Generator, Optional

from controllers.llm_controller import LLMController
from services.llm.base_provider import GenerationConfig


class AIService:
    _instance: Optional["AIService"] = None

    def __init__(self, api_key: str, model_name: str = ""):
        from services.config_service import ConfigService
        ConfigService.initialize()
        LLMController.initialize()
        self._ctrl = LLMController.get_instance()
        self._ctrl.configure(api_key, model_name)

    @property
    def api_key(self) -> str:
        ctrl = LLMController.get_instance()
        return ctrl._config.api_key if ctrl and ctrl._config else ""

    @api_key.setter
    def api_key(self, value: str):
        ctrl = LLMController.get_instance()
        if ctrl:
            ctrl.configure(value, self.model_name)

    @property
    def model_name(self) -> str:
        ctrl = LLMController.get_instance()
        return ctrl.active_model_name if ctrl else ""

    @model_name.setter
    def model_name(self, value: str):
        ctrl = LLMController.get_instance()
        if ctrl:
            ctrl.set_active_model(value)

    @property
    def client(self):
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.provider:
            from services.llm.gemini_provider import GeminiProvider
            if isinstance(ctrl.provider, GeminiProvider):
                return ctrl.provider.client
        return None

    @classmethod
    def initialize(cls, api_key: str, model_name: str = ""):
        from services.config_service import ConfigService
        ConfigService.initialize()
        LLMController.initialize()
        ctrl = LLMController.get_instance()
        if ctrl:
            ctrl.configure(api_key, model_name)
            if cls._instance is None:
                cls._instance = cls(api_key, model_name)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance

    @classmethod
    def is_available(cls) -> bool:
        ctrl = LLMController.get_instance()
        return ctrl is not None and ctrl.is_available

    @classmethod
    def reset(cls):
        cls._instance = None

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.is_available:
            return ctrl.chat(system_prompt, message, history)
        raise RuntimeError("LLM non configuré")

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.is_available:
            return ctrl.chat_stream(system_prompt, message, history)
        raise RuntimeError("LLM non configuré")

    def generate_content(self, prompt: str) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.is_available:
            return ctrl.generate_content(prompt)
        raise RuntimeError("LLM non configuré")

    def generate_embeddings(self, text: str) -> list[float]:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.provider:
            return ctrl.provider.generate_embeddings(text)
        raise RuntimeError("LLM non configuré")
