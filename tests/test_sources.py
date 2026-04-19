import asyncio
from types import SimpleNamespace

import httpx

from nichefinder_core.settings import Settings
from nichefinder_core.sources.scraper import ContentScraper
from nichefinder_core.sources.trends import TrendsClient
from nichefinder_core.utils.rate_limiter import RateLimiter
from nichefinder_core.utils.robots import RobotsChecker


class FakeRobotsResponse:
    def __init__(self, text: str, success: bool = True):
        self.text = text
        self.is_success = success


async def test_robots_checker_with_mock_response(monkeypatch):
    checker = RobotsChecker()

    async def fake_get(url: str):
        return FakeRobotsResponse("User-agent: *\nDisallow: /private")

    monkeypatch.setattr(checker._client, "get", fake_get)
    assert await checker.can_fetch("https://example.com/public") is True
    assert await checker.can_fetch("https://example.com/private") is False


async def test_robots_checker_denies_fetch_when_robots_fetch_fails_by_default(monkeypatch):
    checker = RobotsChecker()

    async def fake_get(url: str):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(checker._client, "get", fake_get)

    assert await checker.can_fetch("https://example.com/public") is False


async def test_robots_checker_allows_fetch_on_failure_when_override_enabled(monkeypatch):
    checker = RobotsChecker(allow_on_error=True)

    async def fake_get(url: str):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(checker._client, "get", fake_get)

    assert await checker.can_fetch("https://example.com/public") is True


async def test_rate_limiter_blocks():
    limiter = RateLimiter(calls_per_period=1, period_seconds=0.05)
    start = asyncio.get_running_loop().time()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = asyncio.get_running_loop().time() - start
    assert elapsed >= 0.05


async def test_scraper_with_mock_html_page():
    checker = RobotsChecker()
    settings = Settings(scrape_delay_min_seconds=0.0, scrape_delay_max_seconds=0.0)
    scraper = ContentScraper(checker, settings)
    html = """
    <html><head><title>Test</title><script type="application/ld+json">{}</script></head>
    <body><article><h1>Main Title</h1><h2>First</h2><p>Some useful article text.</p></article></body></html>
    """

    class FakePage:
        async def goto(self, url: str, wait_until: str, timeout: int):
            return None

        async def content(self):
            return html

        async def close(self):
            return None

    class FakeBrowser:
        async def new_page(self, user_agent: str):
            return FakePage()

        async def close(self):
            return None

    class FakePlaywright:
        chromium = SimpleNamespace(launch=lambda headless=True: FakeBrowser())

        async def stop(self):
            return None

    async def fake_can_fetch(url: str, user_agent: str = "*"):
        return True

    async def fake_init_browser():
        scraper.browser = FakeBrowser()
        scraper.playwright = FakePlaywright()

    checker.can_fetch = fake_can_fetch
    scraper.init_browser = fake_init_browser
    result = await scraper.fetch_article("https://example.com/post")
    assert result is not None
    assert result.h1 == "Main Title"
    assert result.has_schema_markup is True


def test_trends_client_returns_empty_topics_when_pytrends_shape_is_unexpected():
    client = TrendsClient()

    class BrokenPytrends:
        def build_payload(self, keywords, timeframe: str):
            return None

        def related_topics(self):
            raise IndexError("rankedList missing")

    client.pytrends = BrokenPytrends()

    assert client._fetch_related_topics("ai tool development") == []
