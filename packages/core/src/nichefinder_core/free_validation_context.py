from datetime import UTC, datetime
from dataclasses import asdict
import json

from pydantic import BaseModel, Field

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.models import BuyerProblem
from nichefinder_core.pre_serp import PreSerpCandidateScore
from nichefinder_core.settings import Settings


class FrozenShortlistItem(BaseModel):
    keyword_id: str
    term: str
    score: float
    breakdown: dict[str, float]
    canonical_key: str
    selected: bool = False
    notes: list[str] = Field(default_factory=list)


class FreeValidationContext(BaseModel):
    seed_keyword: str
    location: str
    created_at: datetime
    keywords_found: int
    keywords_saved: int
    buyer_problems: list[BuyerProblem]
    shortlist: list[FrozenShortlistItem]


def load_free_validation_context(
    settings: Settings,
    *,
    seed_keyword: str,
    location: str,
    site_config: dict,
) -> FreeValidationContext | None:
    payload = load_json_cache(
        settings,
        namespace="free-validation-context",
        key=_context_key(seed_keyword, location, site_config),
        max_age_hours=settings.free_validation_context_ttl_hours,
    )
    if payload is None:
        return None
    try:
        return FreeValidationContext.model_validate(payload)
    except Exception:
        return None


def save_free_validation_context(
    settings: Settings,
    *,
    seed_keyword: str,
    location: str,
    site_config: dict,
    keywords_found: int,
    keywords_saved: int,
    buyer_problems: list[BuyerProblem],
    shortlist: list[PreSerpCandidateScore],
) -> None:
    context = FreeValidationContext(
        seed_keyword=seed_keyword,
        location=location,
        created_at=datetime.now(UTC),
        keywords_found=keywords_found,
        keywords_saved=keywords_saved,
        buyer_problems=buyer_problems,
        shortlist=[FrozenShortlistItem.model_validate(asdict(item)) for item in shortlist],
    )
    save_json_cache(
        settings,
        namespace="free-validation-context",
        key=_context_key(seed_keyword, location, site_config),
        payload=context.model_dump(mode="json"),
    )


def thaw_shortlist(context: FreeValidationContext) -> list[PreSerpCandidateScore]:
    return [
        PreSerpCandidateScore(
            keyword_id=item.keyword_id,
            term=item.term,
            score=item.score,
            breakdown=dict(item.breakdown),
            canonical_key=item.canonical_key,
            selected=item.selected,
            notes=list(item.notes),
        )
        for item in context.shortlist
    ]


def _context_key(seed_keyword: str, location: str, site_config: dict) -> str:
    site_fingerprint = json.dumps(
        {
            "site_name": site_config.get("site_name"),
            "site_description": site_config.get("site_description"),
            "target_audience": site_config.get("target_audience"),
            "services": site_config.get("services", []),
        },
        sort_keys=True,
    )
    return f"{seed_keyword.lower().strip()}::{location.lower().strip()}::{site_fingerprint}"
