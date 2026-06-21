import logging
import urllib.parse
import urllib.request
import json

logger = logging.getLogger(__name__)


class WebSearchService:
    DUCKDUCKGO_API = "https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
    DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/?q={q}"

    @classmethod
    def search(cls, query: str, max_results: int = 5) -> list[dict]:
        try:
            results = cls._search_duckduckgo_api(query)
            if results:
                return results[:max_results]
        except Exception as e:
            logger.warning(f"DuckDuckGo API search failed: {e}")
        try:
            results = cls._search_duckduckgo_html(query)
            if results:
                return results[:max_results]
        except Exception as e:
            logger.warning(f"DuckDuckGo HTML search failed: {e}")
        return []

    @classmethod
    def _search_duckduckgo_api(cls, query: str) -> list[dict]:
        url = cls.DUCKDUCKGO_API.format(q=urllib.parse.quote(query))
        req = urllib.request.Request(url, headers={"User-Agent": "DigitalTwin/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", ""),
                "snippet": data.get("AbstractText", ""),
                "source": data.get("AbstractSource", ""),
                "url": data.get("AbstractURL", ""),
            })
        for topic in data.get("RelatedTopics", []):
            if "Text" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0],
                    "snippet": topic.get("Text", ""),
                    "source": "DuckDuckGo",
                    "url": topic.get("FirstURL", ""),
                })
        return results

    @classmethod
    def _search_duckduckgo_html(cls, query: str) -> list[dict]:
        import html.parser

        url = cls.DUCKDUCKGO_HTML.format(q=urllib.parse.quote(query))
        req = urllib.request.Request(url, headers={"User-Agent": "DigitalTwin/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html_content = resp.read().decode()

        class ResultParser(html.parser.HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.in_result = False
                self.in_link = False
                self.in_snippet = False
                self.current = {}
                self.tag_stack = []
                self.skip_a = False

            def handle_starttag(self, tag, attrs):
                self.tag_stack.append(tag)
                attrs_dict = dict(attrs)
                if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                    self.in_link = True
                    self.current["url"] = attrs_dict.get("href", "")
                if tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
                    self.in_snippet = True

            def handle_data(self, data):
                if self.in_link and "title" not in self.current:
                    self.current["title"] = data.strip()
                if self.in_snippet:
                    if "snippet" not in self.current:
                        self.current["snippet"] = data.strip()
                    else:
                        self.current["snippet"] += " " + data.strip()

            def handle_endtag(self, tag):
                self.tag_stack.pop()
                if tag == "a":
                    if self.in_link:
                        self.in_link = False
                        if self.current.get("title"):
                            self.current["source"] = "DuckDuckGo"
                            self.results.append(self.current)
                        self.current = {}
                    self.in_snippet = False

        parser = ResultParser()
        parser.feed(html_content)
        return parser.results

    @classmethod
    def format_results_for_prompt(cls, results: list[dict], query: str) -> str:
        if not results:
            return f"\n[Résultats de recherche pour '{query}']\nAucun résultat trouvé.\n"
        lines = [f"\n[Résultats de recherche pour '{query}']"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "") or r.get("snippet", "")[:60]
            snippet = r.get("snippet", "")
            lines.append(f"{i}. {title}")
            if snippet:
                lines.append(f"   {snippet[:300]}")
        return "\n".join(lines)

    @classmethod
    def search_and_format(cls, query: str) -> str:
        results = cls.search(query)
        return cls.format_results_for_prompt(results, query)
