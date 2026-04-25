import asyncio
import json
from dataclasses import dataclass

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from nichefinder_core.settings import Settings
from nichefinder_core.utils.logger import get_logger
from nichefinder_core.utils.rate_limiter import gemini_limiter, gemini_pro_limiter

logger = get_logger(__name__)


@dataclass
class UsageStats:
    requests: int = 0
    prompt_tokens: int = 0
    response_tokens: int = 0

    @property
    def estimated_cost_usd(self) -> float:
        return 0.0


class GeminiClient:
    def __init__(self, settings: Settings):
        if not settings.google_gemini_api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is required")
        self.settings = settings
        self.client = genai.Client(api_key=settings.google_gemini_api_key)
        self.usage_stats = UsageStats()

    async def _generate(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        response_json: bool,
        temperature: float,
    ):
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )
        if response_json:
            config.response_mime_type = "application/json"
        return await asyncio.to_thread(
            self.client.models.generate_content,
            model=model,
            contents=user_content,
            config=config,
        )

    def _track_usage(self, response) -> None:
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        response_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        self.usage_stats.requests += 1
        self.usage_stats.prompt_tokens += prompt_tokens
        self.usage_stats.response_tokens += response_tokens
        if prompt_tokens + response_tokens > 100_000:
            logger.warning("Large Gemini call detected: %s tokens", prompt_tokens + response_tokens)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze(self, system_prompt: str, user_content: str) -> dict:
        await gemini_limiter.acquire()
        response = await self._generate(
            model=self.settings.gemini_flash_model,
            system_prompt=system_prompt,
            user_content=user_content,
            response_json=True,
            temperature=0.2,
        )
        self._track_usage(response)
        if getattr(response, "parsed", None) is not None:
            parsed = response.parsed
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()
            if isinstance(parsed, list):
                return {"items": parsed}
            return parsed
        text = getattr(response, "text", "") or "{}"
        parsed_text = json.loads(text)
        if isinstance(parsed_text, list):
            return {"items": parsed_text}
        return parsed_text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def write(self, system_prompt: str, content_brief: str) -> str:
        await gemini_pro_limiter.acquire()
        response = await self._generate(
            model=self.settings.gemini_pro_model,
            system_prompt=system_prompt,
            user_content=content_brief,
            response_json=False,
            temperature=0.7,
        )
        self._track_usage(response)
        return getattr(response, "text", "")

    def get_usage_stats(self) -> dict:
        return {
            "requests": self.usage_stats.requests,
            "prompt_tokens": self.usage_stats.prompt_tokens,
            "response_tokens": self.usage_stats.response_tokens,
            "estimated_cost_usd": self.usage_stats.estimated_cost_usd,
        }
