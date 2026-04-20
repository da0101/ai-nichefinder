import re
from dataclasses import dataclass, field

from sqlmodel import func, select

from nichefinder_core.models import Keyword, SearchConsoleRecord, SearchIntent

STOP_WORDS = {
    "a",
    "an",
    "and",
    "be",
    "does",
    "do",
    "for",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "of",
    "or",
    "should",
    "the",
    "to",
    "vs",
}
LOCAL_TERMS = {"montreal", "quebec", "canada", "qc"}
ARTICLE_TERMS = {
    "automate",
    "automation",
    "budget",
    "compare",
    "comparison",
    "cost",
    "how",
    "long",
    "mistake",
    "mistakes",
    "need",
    "process",
    "processes",
    "price",
    "pricing",
    "roi",
    "should",
    "take",
    "timeline",
    "time",
    "versus",
    "vs",
    "what",
    "when",
    "worth",
}
BUYER_TERMS = {
    "agency",
    "cost",
    "costs",
    "developer",
    "developers",
    "freelance",
    "freelancer",
    "freelancers",
    "hire",
    "price",
    "pricing",
    "quote",
    "quotes",
    "service",
    "services",
}
DEVELOPER_PENALTY_PATTERNS = (
    "architecture",
    "best practice",
    "best practices",
    "boilerplate",
    "ci/cd",
    "example",
    "examples",
    "framework",
    "hooks",
    "implementation",
    "interview",
    "job",
    "jobs",
    "library",
    "multi tenancy",
    "multitenancy",
    "pattern",
    "patterns",
    "salary",
    "template",
    "testing",
    "tutorial",
    "unit test",
    "unit testing",
    "react native",
    "react",
    "progressive web app",
    "flutter",
    "nextjs",
    "next.js",
    "vue",
    "angular",
    "swiftui",
)
QUERY_PENALTY_PATTERNS = ("hire ", "freelance", "job ", "jobs", "salary", "interview")
STRONG_TRANSACTIONAL_TERMS = {"agency", "freelance", "freelancer", "hire", "service", "services"}
FAMILY_TERMS = {
    "comparison": {"compare", "comparison", "or", "versus", "vs"},
    "cost": {"budget", "cost", "price", "pricing", "quote", "quotes"},
    "decision": {"build", "need", "necessary", "right", "should", "worth"},
    "process": {"automate", "automation", "process", "processes", "task", "tasks", "workflow", "workflows"},
    "scope": {"brief", "checklist", "define", "include", "project", "requirement", "requirements", "scope"},
    "timeline": {"duration", "how", "long", "take", "time", "timeline", "when"},
}
TOKEN_NORMALIZATION = {
    "apps": "app",
    "consulting": "consultant",
    "costs": "cost",
    "developers": "developer",
    "development": "develop",
    "developing": "develop",
    "freelancers": "freelancer",
    "pricing": "price",
    "quotes": "quote",
    "services": "service",
    "website": "web",
    "websites": "website",
}
CANONICAL_DROP_TERMS = LOCAL_TERMS | {
    "agency",
    "best",
    "cost",
    "find",
    "freelance",
    "freelancer",
    "near",
    "price",
    "quote",
    "service",
    "top",
}
SEED_FIDELITY_DROP_TERMS = {
    "average",
    "best",
    "budget",
    "build",
    "business",
    "canada",
    "compare",
    "comparison",
    "cost",
    "define",
    "development",
    "developer",
    "developers",
    "guide",
    "how",
    "long",
    "montreal",
    "price",
    "pricing",
    "quebec",
    "quote",
    "quotes",
    "service",
    "services",
    "take",
    "timeline",
    "what",
    "when",
}


@dataclass(slots=True)
class PreSerpCandidateScore:
    keyword_id: str
    term: str
    score: float
    breakdown: dict[str, float]
    canonical_key: str
    selected: bool = False
    notes: list[str] = field(default_factory=list)


def build_pre_serp_shortlist(
    keyword_ids: list[str],
    repository,
    *,
    site_config: dict,
    location: str,
    max_keywords: int,
) -> list[PreSerpCandidateScore]:
    location_terms = {_normalize_token(token) for token in _tokenize(location)} | LOCAL_TERMS
    service_terms = _service_terms(site_config)
    scored: list[PreSerpCandidateScore] = []

    for keyword_id in keyword_ids:
        keyword = repository.get_keyword(keyword_id)
        if keyword is None:
            continue
        breakdown, notes = _score_keyword(
            keyword,
            repository,
            service_terms=service_terms,
            location_terms=location_terms,
        )
        scored.append(
            PreSerpCandidateScore(
                keyword_id=keyword.id,
                term=keyword.term,
                score=round(sum(breakdown.values()), 2),
                breakdown=breakdown,
                canonical_key=_canonical_key(keyword.term, location_terms),
                notes=notes,
            )
        )

    scored.sort(key=lambda item: (-item.score, item.term))
    seen_canonicals: dict[str, int] = {}
    seen_terms: dict[str, int] = {}
    for item in scored:
        normalized_term = " ".join(_tokenize(item.term))
        exact_duplicate_index = seen_terms.get(normalized_term, 0)
        if exact_duplicate_index > 0:
            penalty = 36.0
            item.breakdown["duplicate_penalty"] = item.breakdown.get("duplicate_penalty", 0.0) - penalty
            item.score = round(item.score - penalty, 2)
            item.notes.append(f"duplicate term {normalized_term}")
        duplicate_index = seen_canonicals.get(item.canonical_key, 0)
        if duplicate_index > 0:
            penalty = min(18.0, duplicate_index * 18.0)
            item.breakdown["duplicate_penalty"] = item.breakdown.get("duplicate_penalty", 0.0) - penalty
            item.score = round(item.score - penalty, 2)
            item.notes.append(f"duplicate group {item.canonical_key}")
        seen_canonicals[item.canonical_key] = duplicate_index + 1
        seen_terms[normalized_term] = exact_duplicate_index + 1

    scored.sort(key=lambda item: (-item.score, item.term))
    for item in scored[:max_keywords]:
        item.selected = True
    return scored


def _score_keyword(
    keyword: Keyword,
    repository,
    *,
    service_terms: set[str],
    location_terms: set[str],
) -> tuple[dict[str, float], list[str]]:
    tokens = {_normalize_token(token) for token in _tokenize(keyword.term)}
    breakdown = {
        "intent": _intent_score(keyword.search_intent),
        "seed_fidelity": _seed_fidelity_score(keyword.term, keyword.seed_keyword or ""),
        "article_fit": _article_fit_score(tokens),
        "business_fit": _business_fit_score(tokens, service_terms),
        "local_intent": _local_intent_score(tokens, location_terms, keyword.seed_keyword or ""),
        "buyer_language": _buyer_language_score(tokens),
        "query_drift": _query_drift_penalty(keyword.term, keyword.seed_keyword or ""),
        "query_penalty": _query_penalty(keyword.term),
        "developer_penalty": _developer_penalty(keyword.term),
        "historical_trend": _historical_trend_score(keyword),
        "gsc_history": _gsc_history_score(keyword.term, repository),
    }
    notes = [
        name
        for name, value in breakdown.items()
        if value > 0
    ]
    if breakdown["developer_penalty"] < 0:
        notes.append("developer-education penalty")
    if breakdown["query_drift"] < 0:
        notes.append("query-drift penalty")
    return breakdown, notes


def _intent_score(intent: SearchIntent | None) -> float:
    if intent == SearchIntent.TRANSACTIONAL:
        return 18.0
    if intent == SearchIntent.COMMERCIAL:
        return 12.0
    if intent == SearchIntent.INFORMATIONAL:
        return 2.0
    return 0.0


def _business_fit_score(tokens: set[str], service_terms: set[str]) -> float:
    overlap = len(tokens & service_terms)
    return float(min(24, overlap * 6))


def _article_fit_score(tokens: set[str]) -> float:
    overlap = len(tokens & ARTICLE_TERMS)
    return float(min(16, overlap * 8))


def _local_intent_score(tokens: set[str], location_terms: set[str], seed_keyword: str) -> float:
    overlap = tokens & location_terms
    seed_tokens = {_normalize_token(token) for token in _tokenize(seed_keyword)}
    seed_is_local = bool(seed_tokens & location_terms)
    if {"montreal", "quebec"} & overlap:
        return 20.0 if seed_is_local else 6.0
    if overlap:
        return 8.0 if seed_is_local else 4.0
    return 0.0


def _buyer_language_score(tokens: set[str]) -> float:
    overlap = len(tokens & BUYER_TERMS)
    return float(min(18, overlap * 6))


def _seed_fidelity_score(term: str, seed_keyword: str) -> float:
    seed_tokens = _meaningful_seed_tokens(seed_keyword)
    if not seed_tokens:
        return 0.0

    term_tokens = {_normalize_token(token) for token in _tokenize(term)}
    overlap_score = min(18.0, len(seed_tokens & term_tokens) * 6.0)
    if term.strip().lower() == seed_keyword.strip().lower():
        overlap_score += 18.0
    elif seed_tokens <= term_tokens:
        overlap_score += 8.0

    seed_families = _query_families(seed_keyword)
    term_families = _query_families(term)
    family_score = min(16.0, len(seed_families & term_families) * 8.0)
    return overlap_score + family_score


def _query_drift_penalty(term: str, seed_keyword: str) -> float:
    seed_families = _query_families(seed_keyword)
    if not seed_families and not _meaningful_seed_tokens(seed_keyword):
        return 0.0

    penalty = 0.0
    term_families = _query_families(term)
    family_drift = (term_families - seed_families) & {"comparison", "cost", "decision", "process", "scope", "timeline"}
    penalty -= min(20.0, len(family_drift) * 10.0)
    missing_seed_families = seed_families - term_families
    penalty -= min(20.0, len(missing_seed_families) * 10.0)

    seed_tokens = {_normalize_token(token) for token in _tokenize(seed_keyword)}
    term_tokens = {_normalize_token(token) for token in _tokenize(term)}
    if not (seed_tokens & LOCAL_TERMS) and term_tokens & LOCAL_TERMS:
        penalty -= 6.0
    if not (seed_tokens & STRONG_TRANSACTIONAL_TERMS) and term_tokens & STRONG_TRANSACTIONAL_TERMS:
        penalty -= 10.0
    if _meaningful_seed_tokens(seed_keyword) and not (_meaningful_seed_tokens(seed_keyword) & term_tokens):
        penalty -= 20.0
    return penalty


def _developer_penalty(term: str) -> float:
    lowered = term.lower()
    for pattern in DEVELOPER_PENALTY_PATTERNS:
        if pattern in lowered:
            return -18.0
    return 0.0


def _query_penalty(term: str) -> float:
    lowered = term.lower()
    for pattern in QUERY_PENALTY_PATTERNS:
        if pattern in lowered:
            return -20.0
    return 0.0


def _historical_trend_score(keyword: Keyword) -> float:
    if keyword.trend_direction == "rising":
        return 6.0
    if keyword.trend_direction == "stable":
        return 2.0
    if keyword.trend_direction == "declining":
        return -2.0
    return 0.0


def _gsc_history_score(term: str, repository) -> float:
    statement = select(
        func.coalesce(func.sum(SearchConsoleRecord.impressions), 0),
        func.coalesce(func.sum(SearchConsoleRecord.clicks), 0),
        func.min(SearchConsoleRecord.position),
    ).where(func.lower(SearchConsoleRecord.query) == term.lower())
    impressions, clicks, best_position = repository.session.exec(statement).one()
    score = 0.0
    if impressions >= 100:
        score += 8.0
    elif impressions > 0:
        score += 4.0
    if clicks > 0:
        score += 4.0
    if best_position is not None and best_position <= 20:
        score += 4.0
    return float(min(12.0, score))


def _service_terms(site_config: dict) -> set[str]:
    fields = [
        site_config.get("site_description", ""),
        site_config.get("target_audience", ""),
        " ".join(site_config.get("services", [])),
    ]
    return {
        _normalize_token(token)
        for field in fields
        for token in _tokenize(field)
        if token not in STOP_WORDS
    }


def _canonical_key(term: str, location_terms: set[str]) -> str:
    tokens = [
        _normalize_token(token)
        for token in _tokenize(term)
        if _normalize_token(token) not in STOP_WORDS
        and _normalize_token(token) not in CANONICAL_DROP_TERMS
        and _normalize_token(token) not in location_terms
    ]
    return " ".join(sorted(tokens)) or term.lower()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _normalize_token(token: str) -> str:
    token = TOKEN_NORMALIZATION.get(token, token)
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        return token[:-1]
    return token


def _meaningful_seed_tokens(seed_keyword: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in _tokenize(seed_keyword)
        if _normalize_token(token) not in STOP_WORDS
        and _normalize_token(token) not in LOCAL_TERMS
        and _normalize_token(token) not in SEED_FIDELITY_DROP_TERMS
    }


def _query_families(text: str) -> set[str]:
    tokens = {_normalize_token(token) for token in _tokenize(text)}
    return {
        family
        for family, family_terms in FAMILY_TERMS.items()
        if tokens & family_terms
    }
