from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsChecker:
    def __init__(self, *, allow_on_error: bool = False):
        self._cache: dict[str, RobotFileParser] = {}
        self._client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        self._allow_on_error = allow_on_error

    def _apply_error_policy(self, parser: RobotFileParser) -> None:
        if self._allow_on_error:
            parser.allow_all = True
            return
        parser.disallow_all = True

    async def _get_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        cached = self._cache.get(domain)
        if cached is not None:
            return cached
        parser = RobotFileParser()
        robots_url = f"{domain}/robots.txt"
        try:
            response = await self._client.get(robots_url)
            if response.is_success:
                parser.parse(response.text.splitlines())
            else:
                self._apply_error_policy(parser)
        except httpx.HTTPError:
            self._apply_error_policy(parser)
        self._cache[domain] = parser
        return parser

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        parser = await self._get_parser(url)
        return parser.can_fetch(user_agent, url)

    async def get_crawl_delay(self, url: str) -> float:
        parser = await self._get_parser(url)
        delay = parser.crawl_delay("*")
        return float(delay) if delay is not None else 3.0
