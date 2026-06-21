from typing import Optional
from services.llm.base_provider import LLMProvider, LLMConfig, ModelInfo, GenerationConfig
from services.llm.gemini_provider import GeminiProvider
from services.llm.anthropic_provider import AnthropicProvider
from services.llm.ollama_provider import OllamaProvider
from services.llm.grok_provider import GrokProvider
from services.llm.question_router import QuestionRouter
from services.config_service import ConfigService

PROVIDER_GEMINI = "gemini"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OLLAMA = "ollama"
PROVIDER_GROK = "grok"


class LLMController:
    _instance: Optional["LLMController"] = None

    def __init__(self):
        self._provider: Optional[LLMProvider] = None  # Gemini
        self._anthropic_provider: Optional[AnthropicProvider] = None
        self._ollama_provider: Optional[OllamaProvider] = None
        self._grok_provider: Optional[GrokProvider] = None
        self._config: Optional[LLMConfig] = None
        self._models: list[ModelInfo] = []
        self._active_model_name: str = ""
        self._active_provider_name: str = PROVIDER_GEMINI
        self._router = QuestionRouter()

    # ── Provider properties ──────────────────────────────────

    @property
    def router(self) -> QuestionRouter:
        return self._router

    @property
    def anthropic_provider(self) -> Optional[AnthropicProvider]:
        return self._anthropic_provider

    @property
    def ollama_provider(self) -> Optional[OllamaProvider]:
        return self._ollama_provider

    @property
    def grok_provider(self) -> Optional[GrokProvider]:
        return self._grok_provider

    @property
    def active_provider_name(self) -> str:
        return self._active_provider_name

    @active_provider_name.setter
    def active_provider_name(self, name: str):
        self._active_provider_name = name.lower()
        cfg = ConfigService.get_instance()
        if cfg:
            cfg.save_llm_provider(self._active_provider_name)

    @property
    def active_provider(self) -> Optional[LLMProvider]:
        return self._get_provider(self._active_provider_name)

    def _get_provider(self, name: str) -> Optional[LLMProvider]:
        if name == PROVIDER_GROK:
            return self._grok_provider
        if name == PROVIDER_ANTHROPIC:
            return self._anthropic_provider
        if name == PROVIDER_OLLAMA:
            return self._ollama_provider
        return self._provider

    def set_active_provider(self, name: str) -> bool:
        name = name.lower()
        if self._get_provider(name) is not None:
            old = self._active_provider_name
            self._active_provider_name = name
            prov = self._get_provider(name)
            if prov and prov.model_name:
                self._active_model_name = prov.model_name
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_llm_provider(name)
            return True
        return False

    # ── Initialization ──────────────────────────────────────

    @classmethod
    def initialize(cls) -> "LLMController":
        if cls._instance is None:
            cfg = ConfigService.get_instance()
            instance = cls()

            gemini_key = cfg.get_gemini_api_key() if cfg else ""
            gemini_model = cfg.get_gemini_model() if cfg else ""
            anthropic_key = cfg.get_anthropic_api_key() if cfg else ""
            anthropic_model = cfg.get_anthropic_model() if cfg else ""
            ollama_host = cfg.get_ollama_host() if cfg else ""
            ollama_model = cfg.get_ollama_model() if cfg else ""
            xai_key = cfg.get_xai_api_key() if cfg else ""
            xai_model = cfg.get_xai_model() if cfg else ""

            instance._config = LLMConfig(api_key=gemini_key, model_name=gemini_model)

            if gemini_key:
                try:
                    instance._provider = GeminiProvider(gemini_key, gemini_model)
                    instance._active_model_name = gemini_model
                except Exception:
                    instance._provider = None

            if anthropic_key:
                try:
                    instance._anthropic_provider = AnthropicProvider(anthropic_key, anthropic_model)
                    if not instance._active_model_name:
                        instance._active_model_name = anthropic_model or "claude-sonnet-4-20250514"
                except Exception:
                    instance._anthropic_provider = None

            try:
                instance._ollama_provider = OllamaProvider(ollama_host, ollama_model)
            except Exception:
                instance._ollama_provider = None

            if xai_key:
                try:
                    instance._grok_provider = GrokProvider(xai_key, xai_model)
                    if not instance._active_model_name:
                        instance._active_model_name = xai_model or "grok-2-1212"
                except Exception:
                    instance._grok_provider = None

            if not instance._active_model_name:
                if instance._provider:
                    instance._active_model_name = instance._config.model_name or "gemini-2.5-flash"
                elif instance._anthropic_provider:
                    instance._active_model_name = anthropic_model or "claude-sonnet-4-20250514"
                elif instance._grok_provider:
                    instance._active_model_name = xai_model or "grok-2-1212"
                elif instance._ollama_provider:
                    instance._active_model_name = ollama_model or "llama3.2"

            provider_cfg = cfg.get_llm_provider() if cfg else "ollama"
            if instance._get_provider(provider_cfg) is not None:
                instance._active_provider_name = provider_cfg
            elif instance._get_provider(PROVIDER_OLLAMA) is not None:
                instance._active_provider_name = PROVIDER_OLLAMA
            elif instance._get_provider(PROVIDER_GEMINI) is not None:
                instance._active_provider_name = PROVIDER_GEMINI
            elif instance._get_provider(PROVIDER_GROK) is not None:
                instance._active_provider_name = PROVIDER_GROK
            elif instance._get_provider(PROVIDER_ANTHROPIC) is not None:
                instance._active_provider_name = PROVIDER_ANTHROPIC

            cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> Optional["LLMController"]:
        return cls._instance

    @property
    def is_available(self) -> bool:
        return (self._provider is not None or self._anthropic_provider is not None
                or self._ollama_provider is not None or self._grok_provider is not None)

    @property
    def active_model_name(self) -> str:
        prov = self.active_provider
        if prov and prov.model_name:
            return prov.model_name
        return self._active_model_name or ""

    @property
    def provider(self) -> Optional[LLMProvider]:
        return self._provider

    @property
    def available_providers(self) -> list[dict]:
        result = []
        if self._provider:
            result.append({"id": PROVIDER_GEMINI, "name": "Google Gemini", "active": self._active_provider_name == PROVIDER_GEMINI})
        if self._grok_provider:
            result.append({"id": PROVIDER_GROK, "name": "xAI Grok", "active": self._active_provider_name == PROVIDER_GROK})
        if self._anthropic_provider:
            result.append({"id": PROVIDER_ANTHROPIC, "name": "Anthropic Claude", "active": self._active_provider_name == PROVIDER_ANTHROPIC})
        if self._ollama_provider:
            result.append({"id": PROVIDER_OLLAMA, "name": "Ollama (local)", "active": self._active_provider_name == PROVIDER_OLLAMA})
        return result

    # ── Provider config methods ─────────────────────────────

    def configure(self, api_key: str, model_name: str = "") -> bool:
        try:
            self._provider = GeminiProvider(api_key, model_name)
            self._config = LLMConfig(api_key=api_key, model_name=model_name)
            self._active_model_name = model_name
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_gemini_config(api_key, model_name)
            return True
        except Exception:
            self._provider = None
            return False

    def configure_anthropic(self, api_key: str, model_name: str = "") -> bool:
        try:
            self._anthropic_provider = AnthropicProvider(api_key, model_name)
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_anthropic_config(api_key, model_name)
            return True
        except Exception:
            self._anthropic_provider = None
            return False

    def configure_ollama(self, host: str = "", model_name: str = "") -> bool:
        try:
            self._ollama_provider = OllamaProvider(host, model_name)
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_ollama_config(host, model_name)
            return True
        except Exception:
            self._ollama_provider = None
            return False

    def configure_grok(self, api_key: str, model_name: str = "") -> bool:
        try:
            self._grok_provider = GrokProvider(api_key, model_name)
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_xai_config(api_key, model_name)
            return True
        except Exception:
            self._grok_provider = None
            return False

    def set_active_model(self, model_name: str) -> bool:
        provider_type = self._detect_provider_type(model_name)
        if provider_type == PROVIDER_ANTHROPIC and self._anthropic_provider:
            try:
                self._anthropic_provider.model_name = model_name
                self._active_model_name = model_name
                if self._config:
                    self._config.model_name = model_name
                cfg = ConfigService.get_instance()
                if cfg:
                    cfg.save_anthropic_model(model_name)
                for mdl in self._models:
                    mdl.is_active = (mdl.name == model_name)
                return True
            except Exception:
                return False

        if provider_type == PROVIDER_OLLAMA and self._ollama_provider:
            try:
                self._ollama_provider.model_name = model_name
                self._active_model_name = model_name
                for mdl in self._models:
                    mdl.is_active = (mdl.name == model_name)
                return True
            except Exception:
                return False

        if provider_type == PROVIDER_GROK and self._grok_provider:
            try:
                self._grok_provider.model_name = model_name
                self._active_model_name = model_name
                for mdl in self._models:
                    mdl.is_active = (mdl.name == model_name)
                return True
            except Exception:
                return False

        if not self._provider:
            return False
        try:
            self._provider.model_name = model_name
            self._active_model_name = model_name
            if self._config:
                self._config.model_name = model_name
            cfg = ConfigService.get_instance()
            if cfg:
                cfg.save_gemini_model(model_name)
            for mdl in self._models:
                mdl.is_active = (mdl.name == model_name)
            return True
        except Exception:
            return False

    def _detect_provider_type(self, model_name: str) -> str:
        if model_name.startswith("claude-"):
            return PROVIDER_ANTHROPIC
        if model_name.startswith("grok-"):
            return PROVIDER_GROK
        if model_name in ("llama3.2", "llama3.1", "mistral", "gemma2") or self._ollama_provider:
            return PROVIDER_OLLAMA
        return PROVIDER_GEMINI

    def get_active_model(self) -> Optional[str]:
        return self._active_model_name or None

    # ── Model discovery ─────────────────────────────────────

    def discover_models(self) -> list[ModelInfo]:
        all_models = []
        for prov in [self._provider, self._anthropic_provider, self._grok_provider, self._ollama_provider]:
            if prov:
                try:
                    all_models.extend(prov.discover_models())
                except Exception:
                    pass
        if not all_models:
            for prov in [self._provider, self._anthropic_provider, self._grok_provider, self._ollama_provider]:
                if prov:
                    try:
                        all_models = prov.discover_models()
                        if all_models:
                            break
                    except Exception:
                        all_models = []
        self._models = all_models
        return list(self._models)

    def get_models(self) -> list[ModelInfo]:
        if not self._models:
            self.discover_models()
        return list(self._models)

    # ── Routing ────────────────────────────────────────────

    def route_and_chat(self, system_prompt: str, message: str, history: list[dict] | None = None,
                       context_available: bool = False) -> str:
        route = self._router.route(message, context_available)
        provider_name, model_name = self._router.get_model_for_route(
            route,
            anthropic_available=self._anthropic_provider is not None,
            gemini_available=self._provider is not None,
            ollama_available=self._ollama_provider is not None,
            grok_available=self._grok_provider is not None,
        )
        prov = self._get_provider(provider_name)
        if prov:
            prov.model_name = model_name
            result = prov.chat(system_prompt, message, history)
            self.log_model_usage(model_name, f"routed_{route}")
            return result
        raise RuntimeError("Aucun fournisseur AI disponible")

    def route_and_chat_stream(self, system_prompt: str, message: str, history: list[dict] | None = None,
                              context_available: bool = False):
        route = self._router.route(message, context_available)
        provider_name, model_name = self._router.get_model_for_route(
            route,
            anthropic_available=self._anthropic_provider is not None,
            gemini_available=self._provider is not None,
            ollama_available=self._ollama_provider is not None,
            grok_available=self._grok_provider is not None,
        )
        prov = self._get_provider(provider_name)
        if prov:
            prov.model_name = model_name
            yield from prov.chat_stream(system_prompt, message, history)
            self.log_model_usage(model_name, f"routed_{route}")
            return
        raise RuntimeError("Aucun fournisseur AI disponible")

    # ── Active provider methods ────────────────────────────

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        prov = self.active_provider
        if prov:
            return prov.chat(system_prompt, message, history)
        if self._provider:
            return self._provider.chat(system_prompt, message, history)
        if self._anthropic_provider:
            return self._anthropic_provider.chat(system_prompt, message, history)
        if self._ollama_provider:
            return self._ollama_provider.chat(system_prompt, message, history)
        if self._grok_provider:
            return self._grok_provider.chat(system_prompt, message, history)
        raise RuntimeError("LLM non configuré")

    def chat_stream(self, system_prompt: str, message: str, history: list[dict] | None = None):
        prov = self.active_provider
        if prov:
            return prov.chat_stream(system_prompt, message, history)
        if self._provider:
            return self._provider.chat_stream(system_prompt, message, history)
        if self._anthropic_provider:
            return self._anthropic_provider.chat_stream(system_prompt, message, history)
        if self._ollama_provider:
            return self._ollama_provider.chat_stream(system_prompt, message, history)
        if self._grok_provider:
            return self._grok_provider.chat_stream(system_prompt, message, history)
        raise RuntimeError("LLM non configuré")

    def generate_content(self, prompt: str) -> str:
        prov = self.active_provider
        if prov:
            return prov.generate_content(prompt)
        if self._provider:
            return self._provider.generate_content(prompt)
        if self._anthropic_provider:
            return self._anthropic_provider.generate_content(prompt)
        if self._ollama_provider:
            return self._ollama_provider.generate_content(prompt)
        if self._grok_provider:
            return self._grok_provider.generate_content(prompt)
        raise RuntimeError("LLM non configuré")

    def verify_connection(self) -> tuple[bool, str]:
        for prov in [self._ollama_provider, self._anthropic_provider, self._provider, self._grok_provider]:
            if prov:
                ok, msg = prov.verify_connection()
                if ok:
                    return True, msg
        return False, "Aucun fournisseur AI configuré"

    def reset(self):
        self._provider = None
        self._anthropic_provider = None
        self._ollama_provider = None
        self._grok_provider = None
        self._config = None
        self._models = []
        self._active_model_name = ""

    def log_model_usage(self, model_name: str, request_type: str):
        import logging
        logging.getLogger("llm").info(
            f"Model: {model_name} | Type: {request_type}"
        )
