import asyncio
from datetime import datetime, timedelta, timezone

from nichefinder_core.agents.trend_agent import TrendAgentInput
from nichefinder_core.pre_serp import build_pre_serp_shortlist

TREND_FRESHNESS_WINDOW = timedelta(days=14)


async def build_trend_assisted_shortlist(
    keyword_ids: list[str],
    repository,
    trend_agent,
    *,
    site_config: dict,
    location: str,
    max_keywords: int,
    noise_profile=None,
    candidate_multiplier: int = 2,
    max_candidates: int = 12,
    concurrency: int = 3,
):
    provisional = build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config=site_config,
        location=location,
        max_keywords=min(max_candidates, max(max_keywords, max_keywords * candidate_multiplier)),
        noise_profile=noise_profile,
    )
    candidate_count = min(len(provisional), max(max_keywords, min(max_candidates, max_keywords * candidate_multiplier)))
    candidates = provisional[:candidate_count]

    pending = []
    for item in candidates:
        keyword = repository.get_keyword(item.keyword_id)
        if keyword is None or not _needs_trend_refresh(keyword):
            continue
        pending.append(keyword)

    if pending:
        semaphore = asyncio.Semaphore(concurrency)

        async def refresh(keyword):
            async with semaphore:
                await trend_agent.run(TrendAgentInput(keyword_id=keyword.id, keyword_term=keyword.term))

        await asyncio.gather(*(refresh(keyword) for keyword in pending))

    return build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config=site_config,
        location=location,
        max_keywords=max_keywords,
        noise_profile=noise_profile,
    )


def _needs_trend_refresh(keyword) -> bool:
    if not keyword.trend_direction or not keyword.trend_fresh_at:
        return True
    fresh_at = keyword.trend_fresh_at
    if fresh_at.tzinfo is None:
        fresh_at = fresh_at.replace(tzinfo=timezone.utc)
    return fresh_at < datetime.now(timezone.utc) - TREND_FRESHNESS_WINDOW
