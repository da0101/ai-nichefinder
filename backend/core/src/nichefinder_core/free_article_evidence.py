import asyncio
import re
from collections import Counter
from dataclasses import dataclass, field

from nichefinder_core.noise_memory import LearnedNoiseProfile, domain_matches_url, phrase_matches_text
from nichefinder_core.pre_serp import ARTICLE_TERMS, BUYER_TERMS, FAMILY_TERMS, LOCAL_TERMS, STOP_WORDS, _normalize_token, _tokenize
from nichefinder_core.pre_serp_external import ExternalEvidenceValidation

QUESTION_WORDS = {"can", "do", "does", "how", "is", "should", "what", "when", "why"}
MARKETING_COPY_PATTERNS = (
    "contact us",
    "get started",
    "book a call",
    "request a quote",
    "free quote",
    "why choose us",
    "ready to",
    "don't want to",
    "frequently asked questions",
    "faq",
    "sources and references",
    "sources",
    "references",
    "table of contents",
)
GENERIC_HEADING_PATTERNS = (
    "premium tier",
    "starter tier",
    "pricing tier",
    "how this fits with",
    "questions to ask",
    "save money on",
)
COMPARISON_NOISE_PATTERNS = (
    "more than other",
    "other cities",
    "local seo",
    "trade business",
    "e-commerce store",
    "google business profile",
    "laval",
    "longueuil",
    "cheapest quote",
)
GENERIC_SECONDARY_PATTERNS = (
    "montreal web design",
    "web design cost",
    "design cost",
    "design price",
    "design company",
)
EDGE_NOISE_TOKENS = {
    "actually",
    "building",
    "break",
    "complete",
    "free",
    "factor",
    "factors",
    "guide",
    "guides",
    "much",
    "online",
    "presence",
    "route",
    "that",
    "this",
    "whether",
    "will",
    "you",
    "your",
}
WEAK_SIGNAL_TOKENS = {
    "building",
    "complete",
    "design",
    "factor",
    "factors",
    "guide",
    "guides",
    "price",
    "prices",
    "scene",
    "tech",
    "that",
    "this",
    "will",
}
GENERIC_PHRASE_PATTERNS = (
    "how much",
    "questions to ask",
    "save money on",
)
GENERIC_PHRASE_TOKENS = {
    "agency",
    "agencies",
    "ask",
    "business",
    "checklist",
    "how",
    "much",
    "montreal",
    "questions",
    "web",
    "website",
    "what",
    "whether",
    "you",
    "your",
    "design",
    "guide",
    "guides",
    "price",
    "prices",
    "this",
    "that",
    "will",
}
SECONDARY_SIGNAL_TOKENS = ARTICLE_TERMS | BUYER_TERMS | {
    "custom",
    "hosting",
    "integration",
    "license",
    "maintain",
    "maintenance",
    "ongoing",
    "ownership",
    "platform",
    "plugin",
    "project",
    "quote",
    "requirement",
    "scope",
    "security",
    "support",
    "timeline",
    "update",
}
DISPLAY_TOKEN_OVERRIDES = {"develop": "development"}


@dataclass(slots=True)
class ArticleEvidencePage:
    url: str
    title: str
    h1: str
    h2_list: list[str]
    h3_list: list[str]
    clean_text: str
    word_count: int


@dataclass(slots=True)
class ArticleEvidenceSummary:
    query: str
    validation_score: float
    source: str
    source_urls: list[str]
    pages_scraped: int
    recurring_headings: list[str] = field(default_factory=list)
    recurring_phrases: list[str] = field(default_factory=list)
    body_signal_terms: list[str] = field(default_factory=list)
    question_bank: list[str] = field(default_factory=list)
    suggested_primary_keyword: str = ""
    suggested_secondary_keywords: list[str] = field(default_factory=list)
    pages: list[ArticleEvidencePage] = field(default_factory=list)


async def collect_free_article_evidence(
    validations: list[ExternalEvidenceValidation],
    scraper,
    *,
    max_keywords: int,
    max_pages_per_keyword: int,
    concurrency: int = 2,
    noise_profile: LearnedNoiseProfile | None = None,
) -> list[ArticleEvidenceSummary]:
    candidates = [
        item
        for item in validations
        if item.score > 0 and bool(getattr(item, "usable_for_article_evidence", True))
    ][:max_keywords]
    if not candidates:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async def scrape(url: str):
        async with semaphore:
            try:
                return await scraper.fetch_article(url)
            except Exception:
                return None

    summaries: list[ArticleEvidenceSummary] = []
    for validation in candidates:
        source_urls = [
            result.url
            for result in _prioritize_results(validation.results, noise_profile)[:max_pages_per_keyword]
            if result.url and not _url_matches_learned_noise(result.url, noise_profile)
        ]
        scraped_results = await asyncio.gather(*(scrape(url) for url in source_urls))
        pages = [
            ArticleEvidencePage(
                url=item.url,
                title=item.title,
                h1=item.h1,
                h2_list=item.h2_list,
                h3_list=item.h3_list,
                clean_text=getattr(item, "clean_text", ""),
                word_count=item.word_count,
            )
            for item in scraped_results
            if item is not None
        ]
        if len(pages) < 2:
            continue
        recurring_headings = _top_headings(pages)
        recurring_phrases = _top_phrases(pages, noise_profile=noise_profile)
        body_signal_terms = _body_signal_terms(pages, noise_profile=noise_profile)
        question_bank = _question_bank(validation.query, pages)
        suggested_secondary = _secondary_keywords(
            validation.query,
            recurring_phrases,
            body_signal_terms,
            noise_profile=noise_profile,
        )
        summaries.append(
            ArticleEvidenceSummary(
                query=validation.query,
                validation_score=validation.score,
                source=validation.source,
                source_urls=source_urls,
                pages_scraped=len(pages),
                recurring_headings=recurring_headings,
                recurring_phrases=recurring_phrases,
                body_signal_terms=body_signal_terms,
                question_bank=question_bank,
                suggested_primary_keyword=validation.query,
                suggested_secondary_keywords=suggested_secondary,
                pages=pages,
            )
        )
    return summaries


def _top_headings(pages: list[ArticleEvidencePage], limit: int = 6) -> list[str]:
    counter: Counter[str] = Counter()
    quality: dict[str, int] = {}
    for page in pages:
        for heading in page.h2_list + page.h3_list:
            normalized = heading.strip()
            if not normalized:
                continue
            if _is_question_heading(normalized):
                continue
            score = _heading_quality_score(normalized)
            if score < 1:
                continue
            counter[normalized] += 1
            quality[normalized] = score
    ranked = sorted(
        counter.items(),
        key=lambda item: (-item[1], -quality.get(item[0], 0), len(item[0]), item[0].lower()),
    )
    return [heading for heading, count in ranked if count >= 2][:limit]


def _top_phrases(
    pages: list[ArticleEvidencePage],
    limit: int = 8,
    noise_profile: LearnedNoiseProfile | None = None,
) -> list[str]:
    counter: Counter[str] = Counter()
    for page in pages:
        headings = [
            heading
            for heading in [page.title, page.h1, *page.h2_list, *page.h3_list]
            if heading and _heading_quality_score(heading) >= 0
        ]
        text = " ".join(headings)
        tokens = [
            _display_token(token)
            for token in _tokenize(text)
            if _normalize_token(token) not in STOP_WORDS and len(_normalize_token(token)) > 2
        ]
        for size in (2, 3):
            for index in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[index : index + size])
                if phrase:
                    counter[phrase] += 1
    ranked = [
        phrase
        for phrase, count in counter.most_common()
        if count >= 2 and _phrase_quality_score(phrase, noise_profile=noise_profile) >= 1
    ]
    return ranked[:limit]


def _question_bank(query: str, pages: list[ArticleEvidencePage], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    display_value: dict[str, str] = {}
    for page in pages:
        for heading in page.h2_list + page.h3_list:
            normalized = heading.strip()
            if not normalized:
                continue
            if not _question_is_useful(normalized, query):
                continue
            key = normalized.lower().rstrip("?")
            counter[key] += 1
            display_value[key] = normalized.rstrip("?") + "?"
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [display_value[key] for key, count in ranked if count >= 2][:limit]


def _body_signal_terms(
    pages: list[ArticleEvidencePage],
    limit: int = 8,
    noise_profile: LearnedNoiseProfile | None = None,
) -> list[str]:
    counter: Counter[str] = Counter()
    page_presence: Counter[str] = Counter()
    for page in pages:
        seen: set[str] = set()
        tokens = [
            _display_token(token)
            for token in _tokenize(" ".join(page.clean_text.split()[:160]))
            if _normalize_token(token) not in STOP_WORDS and len(_normalize_token(token)) > 2
        ]
        for size in (2, 3):
            for index in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[index : index + size])
                if _phrase_quality_score(phrase, noise_profile=noise_profile) < 1:
                    continue
                counter[phrase] += 1
                if phrase not in seen:
                    page_presence[phrase] += 1
                    seen.add(phrase)
    ranked = sorted(
        (
            (phrase, page_presence[phrase], count)
            for phrase, count in counter.items()
            if page_presence[phrase] >= 2
        ),
        key=lambda item: (-item[1], -item[2], item[0]),
    )
    return [phrase for phrase, _, _ in ranked[:limit]]


def _secondary_keywords(
    query: str,
    phrases: list[str],
    body_terms: list[str],
    limit: int = 8,
    noise_profile: LearnedNoiseProfile | None = None,
) -> list[str]:
    query_tokens = set(_tokenize(query))
    candidates: list[str] = []
    for phrase in [*phrases, *body_terms]:
        normalized_tokens = set(_tokenize(phrase))
        if not normalized_tokens:
            continue
        if normalized_tokens <= query_tokens:
            continue
        if _phrase_quality_score(phrase, noise_profile=noise_profile) < 2:
            continue
        if not _supports_query_family(phrase, query):
            continue
        if phrase not in candidates:
            candidates.append(phrase)
        if len(candidates) >= limit:
            break
    return candidates


def _supports_query_family(phrase: str, query: str) -> bool:
    phrase_tokens = {_normalize_token(token) for token in _tokenize(phrase)}
    query_tokens = {
        _normalize_token(token)
        for token in _tokenize(query)
        if _normalize_token(token) not in STOP_WORDS and _normalize_token(token) not in LOCAL_TERMS
    }
    signal_tokens = phrase_tokens & SECONDARY_SIGNAL_TOKENS
    if not signal_tokens:
        return False
    if signal_tokens & query_tokens:
        return True
    query_families = _query_families(query_tokens)
    phrase_families = _query_families(phrase_tokens)
    if query_families & phrase_families:
        return True
    return len(signal_tokens) >= 2


def _query_families(tokens: set[str]) -> set[str]:
    return {
        family
        for family, family_terms in FAMILY_TERMS.items()
        if tokens & family_terms
    }


def _display_token(token: str) -> str:
    return DISPLAY_TOKEN_OVERRIDES.get(_normalize_token(token), _normalize_token(token))


def _phrase_is_noise(phrase: str) -> bool:
    cleaned = " ".join(str(phrase).split()).strip().lower()
    if cleaned.count(" ") < 1:
        return True
    tokens = cleaned.split()
    alpha_tokens = [token for token in tokens if re.search(r"[a-z]", token)]
    if len(alpha_tokens) < 2:
        return True
    if all(token in STOP_WORDS for token in tokens):
        return True
    if tokens[0] in EDGE_NOISE_TOKENS or tokens[-1] in EDGE_NOISE_TOKENS:
        return True
    if any(re.fullmatch(r"\d+", token) for token in tokens):
        return True
    if any(re.fullmatch(r"(19|20)\d{2}", token) for token in tokens):
        return True
    if any(token in {"montreal", "quebec", "canada"} for token in tokens) and any(
        re.fullmatch(r"(19|20)\d{2}", token) for token in tokens
    ):
        return True
    if cleaned.startswith(GENERIC_PHRASE_PATTERNS):
        return True
    if any(pattern in cleaned for pattern in GENERIC_PHRASE_PATTERNS):
        return True
    if any(pattern == cleaned or cleaned.startswith(f"{pattern} ") or cleaned.endswith(f" {pattern}") for pattern in GENERIC_SECONDARY_PATTERNS):
        return True
    if any(pattern in cleaned for pattern in GENERIC_HEADING_PATTERNS):
        return True
    return bool(re.fullmatch(r"(montreal|quebec|canada)( (montreal|quebec|canada))*", cleaned))


def _heading_quality_score(heading: str) -> int:
    normalized = " ".join(heading.lower().split())
    if len(normalized.split()) < 3:
        return -2
    penalty = 0
    if any(pattern in normalized for pattern in MARKETING_COPY_PATTERNS):
        penalty += 3
    if any(pattern in normalized for pattern in GENERIC_HEADING_PATTERNS):
        penalty += 3
    if "checklist" in normalized:
        penalty += 2
    if re.search(r"\$|\d{3,}", normalized):
        penalty += 3
    if normalized.endswith("!") or normalized.count("?") > 1:
        penalty += 2
    if normalized.startswith(("our ", "your ", "why ", "ready ", "need ")):
        penalty += 1
    base = 2
    if normalized.split(" ", 1)[0] in QUESTION_WORDS:
        base += 1
    return base - penalty


def _phrase_looks_marketing(phrase: str) -> bool:
    normalized = phrase.lower()
    return any(pattern in normalized for pattern in MARKETING_COPY_PATTERNS)


def _phrase_quality_score(phrase: str, *, noise_profile: LearnedNoiseProfile | None = None) -> int:
    cleaned = " ".join(str(phrase).split()).strip().lower()
    if _phrase_is_noise(cleaned) or _phrase_looks_marketing(cleaned):
        return -2
    if _phrase_matches_learned_noise(cleaned, noise_profile):
        return -2
    tokens = cleaned.split()
    score = 2
    if len(tokens) >= 3:
        score += 1
    alpha_tokens = [token for token in tokens if re.search(r"[a-z]", token)]
    non_generic = [token for token in alpha_tokens if token not in GENERIC_PHRASE_TOKENS]
    if not non_generic:
        score -= 3
    elif len(non_generic) == 1:
        score -= 1
    if non_generic and all(token in WEAK_SIGNAL_TOKENS for token in non_generic):
        score -= 3
    if cleaned.startswith(("how ", "why ", "what ", "when ")):
        score -= 2
    if tokens[-1] in {"checklist", "questions"}:
        score -= 2
    if _phrase_matches_learned_validity(cleaned, noise_profile):
        score += 2
    return score


def _phrase_matches_learned_noise(phrase: str, noise_profile: LearnedNoiseProfile | None) -> bool:
    if noise_profile is None:
        return False
    return any(phrase_matches_text(candidate, phrase) for candidate in noise_profile.secondary_phrases)


def _url_matches_learned_noise(url: str, noise_profile: LearnedNoiseProfile | None) -> bool:
    if noise_profile is None:
        return False
    return any(domain_matches_url(domain, url) for domain in noise_profile.domains)


def _phrase_matches_learned_validity(phrase: str, noise_profile: LearnedNoiseProfile | None) -> bool:
    if noise_profile is None:
        return False
    return any(phrase_matches_text(candidate, phrase) for candidate in noise_profile.valid_secondary_phrases)


def _prioritize_results(results: list, noise_profile: LearnedNoiseProfile | None) -> list:
    if noise_profile is None or not noise_profile.trusted_domains:
        return list(results)
    return sorted(
        results,
        key=lambda item: (
            0 if any(domain_matches_url(domain, getattr(item, "url", "")) for domain in noise_profile.trusted_domains) else 1,
            getattr(item, "title", ""),
        ),
    )


def _question_is_useful(question: str, query: str) -> bool:
    normalized = " ".join(question.lower().split()).strip()
    if _heading_quality_score(normalized) < 1:
        return False
    tokens = normalized.rstrip("?").split()
    if not _is_question_heading(normalized):
        return False
    if len(tokens) > 8:
        return False
    if re.search(r"\$|\d{3,}", normalized):
        return False
    if normalized.startswith(("what is a ", "what is an ", "what is the ", "what are ")):
        if any(term in normalized for term in ("document", "template", "platform", "cms", "builder")):
            return False
    if any(pattern in normalized for pattern in COMPARISON_NOISE_PATTERNS):
        return False
    return bool(set(_tokenize(normalized)) & set(_tokenize(query)))


def _is_question_heading(heading: str) -> bool:
    normalized = " ".join(heading.lower().split()).strip()
    if not normalized:
        return False
    if "\"" in normalized or "'" in normalized:
        return True
    return normalized.endswith("?")
