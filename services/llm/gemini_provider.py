from typing import Generator, Optional
from google import genai
from google.genai import types

from services.llm.base_provider import LLMProvider, LLMConfig, ModelInfo, GenerationConfig


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = ""):
        super().__init__(api_key, model_name or DEFAULT_MODEL)
        self.client = genai.Client(api_key=api_key)

    def _make_contents(self, message: str, history: list[dict] | None) -> list:
        contents = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                parts = msg.get("parts", [])
                text_parts = []
                for p in parts:
                    if isinstance(p, str):
                        text_parts.append(types.Part.from_text(text=p))
                    elif isinstance(p, dict) and "text" in p:
                        text_parts.append(types.Part.from_text(text=p["text"]))
                contents.append(types.Content(role=role, parts=text_parts))
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
        )
        return contents

    def _build_config(self, system_prompt: str, generation: GenerationConfig | None = None) -> types.GenerateContentConfig:
        gen = generation or GenerationConfig()
        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=gen.temperature,
            max_output_tokens=gen.max_output_tokens,
            top_p=gen.top_p,
            top_k=gen.top_k,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
        )

    def chat(self, system_prompt: str, message: str, history: list[dict] | None = None) -> str:
        contents = self._make_contents(message, history)
        config = self._build_config(system_prompt)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        if not response.candidates:
            raise RuntimeError("Gemini a bloqué la réponse (aucun candidat retourné)")
        return response.text

    def chat_stream(
        self,
        system_prompt: str,
        message: str,
        history: list[dict] | None = None,
        generation: GenerationConfig | None = None,
    ) -> Generator[str, None, None]:
        contents = self._make_contents(message, history)
        config = self._build_config(system_prompt, generation)
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text

    def generate_content(self, prompt: str, generation: GenerationConfig | None = None) -> str:
        if generation:
            config = types.GenerateContentConfig(
                temperature=generation.temperature,
                max_output_tokens=generation.max_output_tokens,
                top_p=generation.top_p,
                top_k=generation.top_k,
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        else:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        return response.text

    def generate_embeddings(self, text: str) -> list[float]:
        EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return result.embeddings[0].values

    def discover_models(self) -> list[ModelInfo]:
        import os
        result = []
        try:
            from google.genai import types as genai_types
            raw_models = list(self.client.models.list())
            for m in raw_models:
                supported = getattr(m, "supported_actions", None) or []
                if not any(a in supported for a in ("generateContent", "generateContentStream")):
                    continue
                input_limit = getattr(m, "input_token_limit", 0) or 0
                output_limit = getattr(m, "output_token_limit", 0) or 0
                display = getattr(m, "display_name", None) or m.name
                description = getattr(m, "description", "") or ""
                mdl_name = m.name.replace("models/", "")
                result.append(ModelInfo(
                    name=mdl_name,
                    display_name=display,
                    provider="Google Gemini",
                    status="Online",
                    context_window=input_limit + output_limit,
                    is_active=(mdl_name == self.model_name),
                    description=description,
                ))
        except Exception:
            result = self._fallback_models()
        return result

    def _fallback_models(self) -> list[ModelInfo]:
        names = [
            ("gemini-2.0-flash", "Gemini 2.0 Flash"),
            ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
            ("gemini-2.5-flash-preview-04-17", "Gemini 2.5 Flash Preview"),
            ("gemini-2.5-pro-preview-03-25", "Gemini 2.5 Pro Preview"),
        ]
        return [
            ModelInfo(
                name=n,
                display_name=d,
                provider="Google Gemini",
                status="Online" if n == self.model_name else "Offline",
                context_window=1_048_576,
                is_active=(n == self.model_name),
            )
            for n, d in names
        ]

    def verify_connection(self) -> tuple[bool, str]:
        try:
            self.client.models.list()
            return True, "Connecté"
        except Exception as e:
            return False, str(e)

    @classmethod
    def from_config(cls, config: LLMConfig) -> "GeminiProvider":
        return cls(config.api_key, config.model_name)


import os

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
