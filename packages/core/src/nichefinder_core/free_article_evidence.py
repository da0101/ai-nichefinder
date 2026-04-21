import asyncio
import re
from collections import Counter
from dataclasses import dataclass, field

from nichefinder_core.pre_serp import STOP_WORDS, _normalize_token, _tokenize
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
}


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
            for result in validation.results[:max_pages_per_keyword]
            if result.url
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
        recurring_phrases = _top_phrases(pages)
        body_signal_terms = _body_signal_terms(pages)
        question_bank = _question_bank(validation.query, pages)
        suggested_secondary = _secondary_keywords(
            validation.query,
            recurring_phrases,
            body_signal_terms,
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
    return [heading for heading, _ in ranked[:limit]]


def _top_phrases(pages: list[ArticleEvidencePage], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    for page in pages:
        headings = [
            heading
            for heading in [page.title, page.h1, *page.h2_list, *page.h3_list]
            if heading and _heading_quality_score(heading) >= 0
        ]
        text = " ".join(headings)
        tokens = [
            _normalize_token(token)
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
        if count >= 2 and _phrase_quality_score(phrase) >= 1
    ]
    return ranked[:limit]


def _question_bank(query: str, pages: list[ArticleEvidencePage], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    questions: list[str] = []
    for page in pages:
        for heading in page.h2_list + page.h3_list:
            normalized = heading.strip()
            if not normalized:
                continue
            if not _question_is_useful(normalized, query):
                continue
            key = normalized.lower().rstrip("?")
            if key in seen:
                continue
            seen.add(key)
            questions.append(normalized.rstrip("?") + "?")
            if len(questions) >= limit:
                return questions
    return questions


def _body_signal_terms(pages: list[ArticleEvidencePage], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    page_presence: Counter[str] = Counter()
    for page in pages:
        seen: set[str] = set()
        tokens = [
            _normalize_token(token)
            for token in _tokenize(" ".join(page.clean_text.split()[:160]))
            if _normalize_token(token) not in STOP_WORDS and len(_normalize_token(token)) > 2
        ]
        for size in (2, 3):
            for index in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[index : index + size])
                if _phrase_quality_score(phrase) < 1:
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
) -> list[str]:
    query_tokens = set(_tokenize(query))
    candidates: list[str] = []
    for phrase in [*phrases, *body_terms]:
        normalized_tokens = set(_tokenize(phrase))
        if not normalized_tokens:
            continue
        if normalized_tokens <= query_tokens:
            continue
        if _phrase_quality_score(phrase) < 2:
            continue
        if phrase not in candidates:
            candidates.append(phrase)
        if len(candidates) >= limit:
            break
    return candidates


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


def _phrase_quality_score(phrase: str) -> int:
    cleaned = " ".join(str(phrase).split()).strip().lower()
    if _phrase_is_noise(cleaned) or _phrase_looks_marketing(cleaned):
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
    if cleaned.startswith(("how ", "why ", "what ", "when ")):
        score -= 2
    if tokens[-1] in {"checklist", "questions"}:
        score -= 2
    return score


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
