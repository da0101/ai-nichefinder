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
)


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
    candidates = [item for item in validations if item.score > 0][:max_keywords]
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
        question_bank = _question_bank(pages)
        suggested_secondary = _secondary_keywords(
            validation.query,
            recurring_phrases,
            recurring_headings,
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
            score = _heading_quality_score(normalized)
            if score < 0:
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
        if count >= 2 and not _phrase_is_noise(phrase) and not _phrase_looks_marketing(phrase)
    ]
    return ranked[:limit]


def _question_bank(pages: list[ArticleEvidencePage], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    questions: list[str] = []
    for page in pages:
        for heading in page.h2_list + page.h3_list:
            normalized = heading.strip()
            if not normalized:
                continue
            if _heading_quality_score(normalized) < 1:
                continue
            lower = normalized.lower()
            starts_as_question = lower.split(" ", 1)[0] in QUESTION_WORDS
            if "?" in normalized or starts_as_question:
                key = lower.rstrip("?")
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
                if _phrase_is_noise(phrase) or _phrase_looks_marketing(phrase):
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
    headings: list[str],
    body_terms: list[str],
    limit: int = 8,
) -> list[str]:
    query_tokens = set(_tokenize(query))
    candidates: list[str] = []
    for phrase in [*phrases, *body_terms, *headings]:
        normalized_tokens = set(_tokenize(phrase))
        if not normalized_tokens:
            continue
        if normalized_tokens <= query_tokens:
            continue
        if phrase not in candidates:
            candidates.append(phrase)
        if len(candidates) >= limit:
            break
    return candidates


def _phrase_is_noise(phrase: str) -> bool:
    if phrase.count(" ") < 1:
        return True
    if all(token in STOP_WORDS for token in phrase.split()):
        return True
    return bool(re.fullmatch(r"(montreal|quebec|canada)( (montreal|quebec|canada))*", phrase))


def _heading_quality_score(heading: str) -> int:
    normalized = " ".join(heading.lower().split())
    if len(normalized.split()) < 3:
        return -2
    penalty = 0
    if any(pattern in normalized for pattern in MARKETING_COPY_PATTERNS):
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
