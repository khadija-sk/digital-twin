import re
from typing import Optional


class QuestionRouter:
    COMPLEX_PATTERNS = re.compile(
        r"(explain|analyze|compare|contrast|why|how does|write me|"
        r"explique|analyse|compare|pourquoi|comment|écris|rédige|"
        r"difference between|différence entre|what is the best|"
        r"quel est le meilleur|should i|devrais-je|est-ce que)",
        re.IGNORECASE,
    )

    CODE_PATTERNS = re.compile(
        r"(code|function|algorithm|implement|program|debug|bug|"
        r"script|api|endpoint|class|method|import|syntax|"
        r"code|fonction|algorithme|implémente|déboguer|"
        r"programme|script|classe|méthode|syntaxe)",
        re.IGNORECASE,
    )

    CREATIVE_PATTERNS = re.compile(
        r"(poem|story|poésie|histoire|raconte|écris un|"
        r"write a|create a|imagine|invente|crée une|"
        r"joke|blague|chanson|song|poem|poème)",
        re.IGNORECASE,
    )

    DATA_PATTERNS = re.compile(
        r"(sommeil|sleep|humeur|mood|énergie|energy|score|"
        r"productiv|burnout|pomodoro|session|objectif|goal|"
        r"badge|journal|check.?in|progression|trend|"
        r"semaine|week|bilan|summary|plan|conseil|tip|"
        r"ma progression|mes données|mon score|mes objectifs)",
        re.IGNORECASE,
    )

    ROUTE_GENERAL = "general"
    ROUTE_COMPLEX = "complex"
    ROUTE_CODE = "code"
    ROUTE_CREATIVE = "creative"
    ROUTE_DATA = "data"

    def __init__(self):
        self._route_names = {
            self.ROUTE_GENERAL: "General knowledge",
            self.ROUTE_COMPLEX: "Complex reasoning",
            self.ROUTE_CODE: "Code / technical",
            self.ROUTE_CREATIVE: "Creative writing",
            self.ROUTE_DATA: "App data analysis",
        }

    def route(self, question: str, context_available: bool = False) -> str:
        if context_available and self.DATA_PATTERNS.search(question):
            return self.ROUTE_DATA

        if len(question) > 200:
            return self.ROUTE_COMPLEX

        if self.CODE_PATTERNS.search(question):
            return self.ROUTE_CODE

        if self.CREATIVE_PATTERNS.search(question):
            return self.ROUTE_CREATIVE

        if self.COMPLEX_PATTERNS.search(question):
            return self.ROUTE_COMPLEX

        return self.ROUTE_GENERAL

    def get_model_for_route(self, route: str, anthropic_available: bool, gemini_available: bool,
                            ollama_available: bool = False, grok_available: bool = False) -> tuple:
        if route == self.ROUTE_DATA:
            if gemini_available:
                return ("gemini", "gemini-2.0-flash")
            if ollama_available:
                return ("ollama", "tinyllama:latest")
            if grok_available:
                return ("grok", "grok-2-1212")
            if anthropic_available:
                return ("anthropic", "claude-sonnet-4-20250514")
            return (None, None)

        if route == self.ROUTE_COMPLEX:
            if ollama_available:
                return ("ollama", "tinyllama:latest")
            if grok_available:
                return ("grok", "grok-2-1212")
            if gemini_available:
                return ("gemini", "gemini-2.5-pro-preview-03-25")
            if anthropic_available:
                return ("anthropic", "claude-sonnet-4-20250514")
            return (None, None)

        if route == self.ROUTE_CODE:
            if ollama_available:
                return ("ollama", "tinyllama:latest")
            if grok_available:
                return ("grok", "grok-2-1212")
            if gemini_available:
                return ("gemini", "gemini-2.0-flash")
            if anthropic_available:
                return ("anthropic", "claude-sonnet-4-20250514")
            return (None, None)

        if route == self.ROUTE_CREATIVE:
            if ollama_available:
                return ("ollama", "tinyllama:latest")
            if grok_available:
                return ("grok", "grok-2-1212")
            if gemini_available:
                return ("gemini", "gemini-2.0-flash")
            if anthropic_available:
                return ("anthropic", "claude-sonnet-4-20250514")
            return (None, None)

        if ollama_available:
            return ("ollama", "qwen3.5:0.8b")
        if grok_available:
            return ("grok", "grok-2-1212")
        if gemini_available:
            return ("gemini", "gemini-2.0-flash")
        if anthropic_available:
            return ("anthropic", "claude-sonnet-4-20250514")
        return (None, None)

    def route_name(self, route: str) -> str:
        return self._route_names.get(route, "General")
