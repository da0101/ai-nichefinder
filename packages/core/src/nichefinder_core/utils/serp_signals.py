from nichefinder_core.models import SerpFeatures, SerpPage

# Domains with very high authority — hard to outrank for any keyword they target.
_HIGH_AUTHORITY = frozenset({
    "wikipedia.org",
    "youtube.com",
    "reddit.com",
    "stackoverflow.com",
    "quora.com",
})

# Mid-tier authority domains relevant to tech/AI/web-dev space.
_MED_AUTHORITY = frozenset({
    "github.com",
    "medium.com",
    "dev.to",
    "hashnode.com",
    "forbes.com",
    "hubspot.com",
    "indeed.com",
    "glassdoor.com",
    "upwork.com",
    "clutch.co",
    "toptal.com",
    "smashingmagazine.com",
    "css-tricks.com",
})


def estimate_difficulty(features: SerpFeatures, pages: list[SerpPage]) -> int:
    """
    Deterministic 0-100 difficulty estimate from existing SerpAPI data.

    Higher = harder to rank. Maps directly into the existing difficulty_score
    field (which is inverted to a scoring benefit: 100 - difficulty).

    Breakdown of max possible points:
      featured snippet   20
      PAA                10
      ads (capped)       15
      shopping results    5
      local pack          5
      authority domains  45  (3 × high @15 or mid @8, capped at 5 pages)
    Total max            100
    """
    score = 0

    if features.has_featured_snippet:
        score += 20
    if features.has_people_also_ask:
        score += 10
    score += min(features.ad_count_top * 5, 15)
    if features.has_shopping_results:
        score += 5
    if features.has_local_pack:
        score += 5

    for page in pages[:5]:
        domain = page.domain.lower()
        if any(auth in domain for auth in _HIGH_AUTHORITY):
            score += 15
        elif any(auth in domain for auth in _MED_AUTHORITY):
            score += 8

    return min(score, 100)


def avg_interest_to_volume_score(avg_interest: float) -> float:
    """
    Convert pytrends average interest (0–100) to a volume_score (0–100).

    Linear mapping: interest reflects relative search demand on the same
    scale the scoring formula already uses, so no transformation needed.
    """
    return round(min(100.0, max(0.0, avg_interest)), 2)
