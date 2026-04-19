import asyncio
import time
from collections import deque

from nichefinder_core.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    def __init__(self, calls_per_period: int, period_seconds: float):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            wait_time = 0.0
            async with self._lock:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= self.period_seconds:
                    self._timestamps.popleft()
                if len(self._timestamps) < self.calls_per_period:
                    self._timestamps.append(time.monotonic())
                    return
                wait_time = self.period_seconds - (now - self._timestamps[0])
            if wait_time > 1:
                logger.info("Rate limiter waiting %.2fs", wait_time)
            await asyncio.sleep(max(wait_time, 0.0))


serpapi_limiter = RateLimiter(calls_per_period=10, period_seconds=60)
scraper_limiter = RateLimiter(calls_per_period=5, period_seconds=30)
gemini_limiter = RateLimiter(calls_per_period=15, period_seconds=60)
gemini_pro_limiter = RateLimiter(calls_per_period=2, period_seconds=60)
