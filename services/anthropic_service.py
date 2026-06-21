from typing import Generator, Optional

from controllers.llm_controller import LLMController


class AnthropicService:
    _instance: Optional["AnthropicService"] = None

    def __init__(self, api_key: str, model_name: str = ""):
        from services.config_service import ConfigService
        ConfigService.initialize()
        LLMController.initialize()
        self._ctrl = LLMController.get_instance()
        if self._ctrl:
            self._ctrl.configure_anthropic(api_key, model_name)

    @property
    def api_key(self) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            return ctrl.anthropic_provider.api_key
        return ""

    @api_key.setter
    def api_key(self, value: str):
        ctrl = LLMController.get_instance()
        if ctrl:
            ctrl.configure_anthropic(value, self.model_name)

    @property
    def model_name(self) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            return ctrl.anthropic_provider.model_name
        return ""

    @model_name.setter
    def model_name(self, value: str):
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            ctrl.anthropic_provider.model_name = value

    @classmethod
    def initialize(cls, api_key: str, model_name: str = ""):
        from services.config_service import ConfigService
        ConfigService.initialize()
        LLMController.initialize()
        ctrl = LLMController.get_instance()
        if ctrl:
            ctrl.configure_anthropic(api_key, model_name)
            if cls._instance is None:
                cls._instance = cls(api_key, model_name)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance

    @classmethod
    def is_available(cls) -> bool:
        ctrl = LLMController.get_instance()
        return ctrl is not None and ctrl.anthropic_provider is not None

    @classmethod
    def reset(cls):
        cls._instance = None

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            return ctrl.anthropic_provider.chat(system_prompt, message, history)
        raise RuntimeError("Anthropic non configuré")

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            return ctrl.anthropic_provider.chat_stream(system_prompt, message, history)
        raise RuntimeError("Anthropic non configuré")

    def generate_content(self, prompt: str) -> str:
        ctrl = LLMController.get_instance()
        if ctrl and ctrl.anthropic_provider:
            return ctrl.anthropic_provider.generate_content(prompt)
        raise RuntimeError("Anthropic non configuré")
