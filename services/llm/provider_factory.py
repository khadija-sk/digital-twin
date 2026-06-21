from typing import Optional
from services.llm.base_provider import LLMProvider
from services.llm.gemini_provider import GeminiProvider
from services.llm.anthropic_provider import AnthropicProvider
from services.llm.ollama_provider import OllamaProvider
from services.llm.grok_provider import GrokProvider



class ProviderFactory:

    _registry: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[LLMProvider]):
        cls._registry[name] = provider_class

    @classmethod
    def create(cls, provider_name: str, api_key: str = "", model_name: str = "",
               **kwargs) -> Optional[LLMProvider]:
        provider_name = provider_name.lower()
        if provider_name in cls._registry:
            provider_class = cls._registry[provider_name]
            if provider_name == "ollama":
                host = kwargs.get("host", "http://localhost:11434")
                return provider_class(host, model_name)
            return provider_class(api_key, model_name)

        if provider_name == "gemini":
            return GeminiProvider(api_key, model_name)
        if provider_name == "anthropic":
            return AnthropicProvider(api_key, model_name)
        if provider_name == "ollama":
            host = kwargs.get("host", "http://localhost:11434")
            return OllamaProvider(host, model_name)
        if provider_name == "grok":
            return GrokProvider(api_key, model_name)
        return None

    @classmethod
    def supported_providers(cls) -> list[str]:
        base = ["gemini", "grok"]
        for name in cls._registry:
            if name not in base:
                base.append(name)
        return base

    @classmethod
    def get_provider_display_name(cls, provider_name: str) -> str:
        names = {
            "gemini": "Google Gemini",
            "anthropic": "Anthropic Claude",
            "ollama": "Ollama (local)",
            "grok": "xAI Grok",
        }
        return names.get(provider_name.lower(), provider_name)


ProviderFactory.register("gemini", GeminiProvider)
ProviderFactory.register("grok", GrokProvider)
ProviderFactory.register("anthropic", AnthropicProvider)
ProviderFactory.register("ollama", OllamaProvider)
