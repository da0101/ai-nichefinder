import asyncio
import random
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pydantic import BaseModel
from readability import Document

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.settings import Settings
from nichefinder_core.utils.logger import get_logger
from nichefinder_core.utils.rate_limiter import scraper_limiter
from nichefinder_core.utils.robots import RobotsChecker

logger = get_logger(__name__)


class ScrapedContent(BaseModel):
    url: str
    title: str
    h1: str
    h2_list: list[str]
    h3_list: list[str]
    clean_text: str
    word_count: int
    internal_links: list[str]
    external_links: list[str]
    has_schema_markup: bool
    fetched_at: datetime


class ContentScraper:
    def __init__(self, robots_checker: RobotsChecker, settings: Settings):
        self.robots = robots_checker
        self.settings = settings
        self.browser = None
        self.playwright = None

    async def init_browser(self):
        if self.browser is not None:
            return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def fetch_article(self, url: str) -> ScrapedContent | None:
        cache_key = url.strip()
        cached = load_json_cache(
            self.settings,
            namespace="scraped-articles",
            key=cache_key,
            max_age_hours=self.settings.free_article_cache_ttl_hours,
        )
        if cached is not None:
            return ScrapedContent.model_validate(cached)
        if not await self.robots.can_fetch(url):
            logger.warning("Robots.txt disallows scraping: %s", url)
            return None
        await scraper_limiter.acquire()
        await asyncio.sleep(
            random.uniform(
                self.settings.scrape_delay_min_seconds,
                self.settings.scrape_delay_max_seconds,
            )
        )
        await self.init_browser()
        page = await self.browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        )
        try:
            await page.goto(url, wait_until="networkidle", timeout=45_000)
            html = await page.content()
        finally:
            await page.close()
        document = Document(html)
        clean_html = document.summary(html_partial=True)
        soup = BeautifulSoup(clean_html, "lxml")
        text = soup.get_text(" ", strip=True)
        h1 = soup.find("h1")
        h2_list = [tag.get_text(" ", strip=True) for tag in soup.find_all("h2")]
        h3_list = [tag.get_text(" ", strip=True) for tag in soup.find_all("h3")]
        links = [tag.get("href", "") for tag in soup.find_all("a", href=True)]
        parsed_domain = urlparse(url).netloc
        internal_links = [link for link in links if parsed_domain in link or link.startswith("/")]
        external_links = [link for link in links if link not in internal_links]
        has_schema_markup = bool(
            BeautifulSoup(html, "lxml").find_all("script", attrs={"type": "application/ld+json"})
        )
        scraped = ScrapedContent(
            url=url,
            title=document.short_title() or "",
            h1=h1.get_text(" ", strip=True) if h1 else "",
            h2_list=h2_list,
            h3_list=h3_list,
            clean_text=text,
            word_count=len(text.split()),
            internal_links=internal_links,
            external_links=external_links,
            has_schema_markup=has_schema_markup,
            fetched_at=datetime.now(timezone.utc),
        )
        save_json_cache(
            self.settings,
            namespace="scraped-articles",
            key=cache_key,
            payload=scraped.model_dump(mode="json"),
        )
        return scraped

    async def close(self):
        if self.browser is not None:
            await self.browser.close()
            self.browser = None
        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None
