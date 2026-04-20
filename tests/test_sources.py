import asyncio
from types import SimpleNamespace

import httpx

from nichefinder_core.settings import Settings
from nichefinder_core.sources.bing import BingClient
from nichefinder_core.sources.scraper import ContentScraper
from nichefinder_core.sources.trends import TrendsClient
from nichefinder_core.sources.yahoo import YahooClient
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


class FakeUsageStore:
    def __init__(self):
        self.calls: dict[str, int] = {}

    def get_api_usage(self, provider: str, usage_month=None):
        count = self.calls.get(provider, 0)
        if not count:
            return None
        return SimpleNamespace(call_count=count)

    def record_api_usage(self, provider: str, calls: int = 1, **kwargs):
        self.calls[provider] = self.calls.get(provider, 0) + calls


class FakeHtmlResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


async def test_bing_client_parses_search_results_and_tracks_usage(monkeypatch, tmp_path):
    html = """<?xml version="1.0" encoding="utf-8" ?>
    <rss version="2.0"><channel>
      <item>
        <title>Website Cost in Montreal</title>
        <link>https://example.com/pricing</link>
        <description>Pricing factors for websites and web apps.</description>
      </item>
      <item>
        <title>How to Budget a Website</title>
        <link>https://example.org/budget</link>
        <description>Budget planning for founders.</description>
      </item>
    </channel></rss>
    """
    usage = FakeUsageStore()
    client = BingClient(Settings(cache_dir=tmp_path / "cache"), usage)

    async def fake_get(url: str, params: dict):
        return FakeHtmlResponse(html)

    monkeypatch.setattr(client.client, "get", fake_get)
    payload = await client.search("website cost montreal", max_results=2)

    assert [item["url"] for item in payload["results"]] == [
        "https://example.com/pricing",
        "https://example.org/budget",
    ]
    assert usage.calls["bing"] == 1


async def test_yahoo_client_unwraps_redirect_urls_and_tracks_usage(monkeypatch, tmp_path):
    html = """
    <html><body>
      <div id="web">
        <ol>
          <li>
            <div class="algo">
              <div class="compTitle">
                <h3>
                  <a href="https://r.search.yahoo.com/_ylt=Awr/RU=https%3A%2F%2Fexample.com%2Fcost-guide/RK=2/RS=abc">
                    Website Cost Guide
                  </a>
                </h3>
              </div>
              <div class="compText"><p>How much a website costs in Montreal.</p></div>
            </div>
          </li>
          <li>
            <div class="algo">
              <div class="compTitle">
                <h3>
                  <a href="https://video.search.yahoo.com/video/play?p=website+cost">
                    Video result
                  </a>
                </h3>
              </div>
              <div class="compText"><p>Video vertical that should be filtered.</p></div>
            </div>
          </li>
        </ol>
      </div>
    </body></html>
    """
    usage = FakeUsageStore()
    client = YahooClient(Settings(cache_dir=tmp_path / "cache"), usage)

    async def fake_get(url: str, params: dict):
        return FakeHtmlResponse(html)

    monkeypatch.setattr(client.client, "get", fake_get)
    payload = await client.search("website cost montreal", max_results=2)

    assert payload["results"][0]["url"] == "https://example.com/cost-guide"
    assert payload["results"][0]["title"] == "Website Cost Guide"
    assert len(payload["results"]) == 1
    assert usage.calls["yahoo"] == 1


async def test_bing_client_saves_raw_html_when_parser_finds_no_results(monkeypatch, tmp_path):
    html = "<html><body><div id='b_results'><div>unexpected layout</div></div></body></html>"
    settings = Settings(cache_dir=tmp_path / "cache")
    client = BingClient(settings, FakeUsageStore())

    async def fake_get(url: str, params: dict):
        return FakeHtmlResponse(html)

    monkeypatch.setattr(client.client, "get", fake_get)
    payload = await client.search("website cost montreal", max_results=2)

    assert payload["results"] == []
    debug_files = list((settings.resolved_cache_dir / "search-debug" / "bing").glob("*.html"))
    assert len(debug_files) == 1
    assert "unexpected layout" in debug_files[0].read_text(encoding="utf-8")


async def test_yahoo_client_uses_cached_search_payload_without_usage(monkeypatch, tmp_path):
    html = """
    <html><body><div id="web"><ol><li><div class="algo"><div class="compTitle">
    <h3><a href="https://example.com/guide">Guide</a></h3></div><div class="compText"><p>Snippet</p></div>
    </div></li></ol></div></body></html>
    """
    usage = FakeUsageStore()
    settings = Settings(cache_dir=tmp_path / "cache")
    client = YahooClient(settings, usage)
    calls = {"count": 0}

    async def fake_get(url: str, params: dict):
        calls["count"] += 1
        return FakeHtmlResponse(html)

    monkeypatch.setattr(client.client, "get", fake_get)
    first = await client.search("website cost montreal", max_results=2)
    second = await client.search("website cost montreal", max_results=2)

    assert first == second
    assert calls["count"] == 1
    assert usage.calls["yahoo"] == 1


async def test_scraper_uses_cached_article_snapshot(monkeypatch, tmp_path):
    checker = RobotsChecker()
    settings = Settings(
        cache_dir=tmp_path / "cache",
        scrape_delay_min_seconds=0.0,
        scrape_delay_max_seconds=0.0,
    )
    scraper = ContentScraper(checker, settings)
    html = """
    <html><body><article><h1>Main Title</h1><h2>First</h2><p>Some useful article text.</p></article></body></html>
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
    first = await scraper.fetch_article("https://example.com/post")

    async def fail_can_fetch(url: str, user_agent: str = "*"):
        raise AssertionError("cache should satisfy second fetch before robots/network")

    checker.can_fetch = fail_can_fetch
    second = await scraper.fetch_article("https://example.com/post")

    assert first is not None and second is not None
    assert second.h1 == "Main Title"
