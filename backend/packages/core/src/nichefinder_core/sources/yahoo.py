import re
from urllib.parse import parse_qs, unquote, urlparse

from nichefinder_core.sources.html_search_engine import HtmlSearchEngineClient


class YahooClient(HtmlSearchEngineClient):
    provider = "yahoo"
    base_url = "https://search.yahoo.com/search"
    limit_setting = "yahoo_calls_per_month"
    ready_setting = "yahoo_ready"

    def _params(self, query: str, *, max_results: int) -> dict[str, str | int]:
        return {
            "p": query,
            "n": max(10, max_results),
            "ei": "UTF-8",
        }

    def _parse_results(self, html: str, *, max_results: int) -> list[dict[str, str]]:
        soup = self._soup(html)
        results: list[dict[str, str]] = []
        selectors = ["div#web li", "div.algo", "section li", "ol.searchCenterMiddle li"]
        nodes = []
        for selector in selectors:
            nodes = soup.select(selector)
            if nodes:
                break
        for node in nodes:
            link = None
            for selector in ["h3 a", ".compTitle a", "a"]:
                link = node.select_one(selector)
                if link is not None:
                    break
            if link is None:
                continue
            url = self._unwrap_url((link.get("href") or "").strip())
            if not self._is_allowed_result_url(url):
                continue
            snippet = ""
            for selector in [".compText p", ".compText", "p"]:
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

    @staticmethod
    def _unwrap_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc not in {"r.search.yahoo.com", "search.yahoo.com"}:
            return url
        query_url = parse_qs(parsed.query).get("RU")
        if query_url:
            return unquote(query_url[0])
        match = re.search(r"/RU=([^/]+)/", url)
        if match:
            return unquote(match.group(1))
        return url

    @staticmethod
    def _is_allowed_result_url(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        blocked_hosts = {
            "search.yahoo.com",
            "video.search.yahoo.com",
            "images.search.yahoo.com",
            "news.search.yahoo.com",
            "finance.yahoo.com",
            "sports.yahoo.com",
        }
        if parsed.netloc in blocked_hosts:
            return False
        if parsed.netloc.endswith(".search.yahoo.com"):
            return False
        blocked_path_fragments = ("/video/", "/images/", "/news/")
        return not any(fragment in parsed.path.lower() for fragment in blocked_path_fragments)
