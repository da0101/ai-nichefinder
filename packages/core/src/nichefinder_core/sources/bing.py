from xml.etree import ElementTree as ET
from urllib.parse import parse_qs, unquote, urlparse

from nichefinder_core.sources.html_search_engine import HtmlSearchEngineClient


class BingClient(HtmlSearchEngineClient):
    provider = "bing"
    base_url = "https://www.bing.com/search"
    limit_setting = "bing_calls_per_month"
    ready_setting = "bing_ready"
    debug_on_empty_results = True

    def _params(self, query: str, *, max_results: int) -> dict[str, str | int]:
        return {
            "q": query,
            "format": "rss",
            "count": max(10, max_results),
            "setlang": "en-US",
            "cc": "us",
            "mkt": "en-US",
        }

    def _parse_results(self, html: str, *, max_results: int) -> list[dict[str, str]]:
        if "<rss" in html[:200].lower():
            rss_results = self._parse_rss_results(html, max_results=max_results)
            if rss_results:
                return rss_results
        soup = self._soup(html)
        results: list[dict[str, str]] = []
        nodes = []
        for selector in ["li.b_algo", "#b_results > li", "main li", "ol li"]:
            nodes = soup.select(selector)
            if nodes:
                break
        for node in nodes:
            link = None
            for selector in ["h2 a", ".b_algoheader a", "a[href]"]:
                link = node.select_one(selector)
                if link is not None:
                    break
            if link is None:
                continue
            url = self._unwrap_url((link.get("href") or "").strip())
            if urlparse(url).scheme not in {"http", "https"}:
                continue
            snippet = ""
            for selector in [".b_caption p", ".b_lineclamp2", ".b_snippet", ".b_algoSlug", "p"]:
                snippet_node = node.select_one(selector)
                if snippet_node is not None:
                    snippet = self._clean_text(snippet_node.get_text(" ", strip=True))
                if snippet:
                    break
            title = self._clean_text(link.get_text(" ", strip=True))
            if not title:
                continue
            results.append({"title": title, "url": url, "content": snippet})
            if len(results) >= max_results:
                break
        return results

    def _parse_rss_results(self, xml_text: str, *, max_results: int) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []
        results: list[dict[str, str]] = []
        for item in root.findall("./channel/item"):
            title = self._clean_text(item.findtext("title", default=""))
            url = self._unwrap_url(self._clean_text(item.findtext("link", default="")))
            content = self._clean_text(item.findtext("description", default=""))
            if not title or urlparse(url).scheme not in {"http", "https"}:
                continue
            results.append({"title": title, "url": url, "content": content})
            if len(results) >= max_results:
                break
        return results

    @staticmethod
    def _unwrap_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc not in {"www.bing.com", "bing.com"}:
            return url
        if parsed.path.startswith("/ck/"):
            target = parse_qs(parsed.query).get("u")
            if target:
                value = target[0]
                if len(value) > 2 and value[:2].isalnum():
                    value = value[2:]
                return unquote(value)
        return url
