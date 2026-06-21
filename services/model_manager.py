import os
import threading
import logging
from typing import Optional

from controllers.llm_controller import LLMController
from services.config_service import ConfigService
from services.llm.base_provider import ModelInfo


class ModelManager:
    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._models: list[ModelInfo] = []
        self._active_model: Optional[str] = None
        self._ctrl: Optional[LLMController] = None
        self._init_llm()

    def _init_llm(self):
        ConfigService.initialize()
        LLMController.initialize()
        self._ctrl = LLMController.get_instance()
        self._active_model = self._ctrl.active_model_name if self._ctrl else ""

    @classmethod
    def initialize(cls) -> "ModelManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def get_instance(cls) -> Optional["ModelManager"]:
        return cls._instance

    def discover_models(self) -> list[ModelInfo]:
        if not self._ctrl or not self._ctrl.is_available:
            self._models = []
            return self._models
        try:
            self._models = self._ctrl.discover_models()
        except Exception as e:
            logging.getLogger(__name__).warning("Erreur lors de la découverte des modèles, utilisation des modèles de secours")
            self._models = self._fallback_models()
        return list(self._models)

    def _fallback_models(self) -> list[ModelInfo]:
        models = [
            ModelInfo(
                name="gemini-2.0-flash", display_name="Gemini 2.0 Flash",
                provider="Google Gemini", status="Online",
                context_window=1_048_576, is_active=("gemini-2.0-flash" == self._active_model),
            ),
            ModelInfo(
                name="gemini-2.0-flash-lite", display_name="Gemini 2.0 Flash Lite",
                provider="Google Gemini", status="Online",
                context_window=1_048_576, is_active=("gemini-2.0-flash-lite" == self._active_model),
            ),
            ModelInfo(
                name="gemini-2.5-pro-preview-03-25", display_name="Gemini 2.5 Pro Preview",
                provider="Google Gemini", status="Online",
                context_window=1_048_576, is_active=("gemini-2.5-pro-preview-03-25" == self._active_model),
            ),
            ModelInfo(
                name="claude-sonnet-4-20250514", display_name="Claude Sonnet 4",
                provider="Anthropic", status="Online",
                context_window=200_000, is_active=("claude-sonnet-4-20250514" == self._active_model),
            ),
            ModelInfo(
                name="claude-3-5-haiku-latest", display_name="Claude 3.5 Haiku",
                provider="Anthropic", status="Online",
                context_window=200_000, is_active=("claude-3-5-haiku-latest" == self._active_model),
            ),
            ModelInfo(
                name="claude-3-opus-20240229", display_name="Claude 3 Opus",
                provider="Anthropic", status="Online",
                context_window=200_000, is_active=("claude-3-opus-20240229" == self._active_model),
            ),
        ]
        return models

    def get_models(self) -> list[ModelInfo]:
        if not self._models:
            self.discover_models()
        return list(self._models)

    def get_active_model(self) -> Optional[str]:
        return self._active_model

    def set_active_model(self, model_name: str) -> bool:
        if not self._ctrl:
            return False
        try:
            result = self._ctrl.set_active_model(model_name)
            if result:
                self._active_model = model_name
            return result
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur lors du changement de modèle actif")
            return False

    def verify_connection(self) -> tuple[bool, str]:
        if not self._ctrl:
            return False, "API non configurée"
        return self._ctrl.verify_connection()
