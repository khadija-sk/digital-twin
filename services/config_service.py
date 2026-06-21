import os
from typing import Optional


class ConfigService:
    _instance: Optional["ConfigService"] = None

    def __init__(self, env_path: str = ""):
        self._env_path = env_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env"
        )

    @classmethod
    def initialize(cls, env_path: str = "") -> "ConfigService":
        if cls._instance is None:
            cls._instance = cls(env_path)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Optional["ConfigService"]:
        return cls._instance

    def _read_env(self) -> dict[str, str]:
        result = {}
        if os.path.exists(self._env_path):
            with open(self._env_path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        continue
                    key, _, value = stripped.partition("=")
                    result[key.strip()] = value.strip()
        return result

    def _write_env(self, env_vars: dict[str, str]):
        existing = {}
        if os.path.exists(self._env_path):
            lines = []
            with open(self._env_path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped.startswith("#") and "=" in stripped:
                        key = stripped.partition("=")[0].strip()
                        if key in env_vars:
                            lines.append(f"{key}={env_vars[key]}\n")
                            existing[key] = True
                            continue
                    lines.append(line)
            for key, value in env_vars.items():
                if key not in existing:
                    lines.append(f"{key}={value}\n")
            with open(self._env_path, "w") as f:
                f.writelines(lines)
        else:
            with open(self._env_path, "w") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

    # ── Gemini ────────────────────────────────────────────

    def get_gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    def get_gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    def save_gemini_api_key(self, api_key: str):
        self._write_env({"GEMINI_API_KEY": api_key})

    def save_gemini_model(self, model_name: str):
        self._write_env({"GEMINI_MODEL": model_name})

    def save_gemini_config(self, api_key: str, model_name: str):
        self._write_env({"GEMINI_API_KEY": api_key, "GEMINI_MODEL": model_name})

    # ── Anthropic ─────────────────────────────────────────

    def get_anthropic_api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    def get_anthropic_model(self) -> str:
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def save_anthropic_api_key(self, api_key: str):
        self._write_env({"ANTHROPIC_API_KEY": api_key})

    def save_anthropic_model(self, model_name: str):
        self._write_env({"ANTHROPIC_MODEL": model_name})

    def save_anthropic_config(self, api_key: str, model_name: str):
        self._write_env({"ANTHROPIC_API_KEY": api_key, "ANTHROPIC_MODEL": model_name})

    # ── Ollama ─────────────────────────────────────────────

    def get_ollama_host(self) -> str:
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def get_ollama_model(self) -> str:
        return os.getenv("OLLAMA_MODEL", "tinyllama:latest")

    def save_ollama_host(self, host: str):
        self._write_env({"OLLAMA_HOST": host})

    def save_ollama_model(self, model_name: str):
        self._write_env({"OLLAMA_MODEL": model_name})

    def save_ollama_config(self, host: str, model_name: str):
        self._write_env({"OLLAMA_HOST": host, "OLLAMA_MODEL": model_name})

    # ── xAI Grok ─────────────────────────────────────────

    def get_xai_api_key(self) -> str:
        return os.getenv("XAI_API_KEY", "")

    def get_xai_model(self) -> str:
        return os.getenv("XAI_MODEL", "grok-2-1212")

    def save_xai_api_key(self, api_key: str):
        self._write_env({"XAI_API_KEY": api_key})

    def save_xai_model(self, model_name: str):
        self._write_env({"XAI_MODEL": model_name})

    def save_xai_config(self, api_key: str, model_name: str):
        self._write_env({"XAI_API_KEY": api_key, "XAI_MODEL": model_name})

    # ── Provider selection ───────────────────────────────

    def get_llm_provider(self) -> str:
        return os.getenv("LLM_PROVIDER", "ollama")

    def save_llm_provider(self, provider: str):
        self._write_env({"LLM_PROVIDER": provider})

    # ── Legacy compatibility ─────────────────────────────

    def get_api_key(self) -> str:
        return self.get_gemini_api_key()

    def get_model_name(self) -> str:
        return self.get_gemini_model()

    def save_api_key(self, api_key: str):
        self.save_gemini_api_key(api_key)

    def save_model_name(self, model_name: str):
        self.save_gemini_model(model_name)

    def save_ai_config(self, api_key: str, model_name: str):
        self.save_gemini_config(api_key, model_name)
