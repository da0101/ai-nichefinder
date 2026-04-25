import re
from collections import Counter, defaultdict
from typing import Any

from nichefinder_core.models.evidence import ArticleEvidenceBank, EvidenceSignal

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "what",
    "when",
    "why",
    "with",
}
MIN_WORD_COUNT = 80
MAX_SENTENCE_QUESTIONS = 4


async def build_article_evidence_bank(
    query: str,
    results: list[Any],
    scraper,
    *,
    max_pages: int = 2,
) -> tuple[ArticleEvidenceBank | None, list[str]]:
    candidate_urls = _candidate_urls(results, max_pages=max_pages)
    if not candidate_urls:
        return None, []

    notes: list[str] = []
    scraped_pages = []
    for url in candidate_urls:
        try:
            scraped = await scraper.fetch_article(url)
        except Exception as exc:  # pragma: no cover - live-network defensive path
            notes.append(f"article evidence failed: {url} ({exc})")
            continue
        if scraped is None:
            notes.append(f"article evidence skipped: {url}")
            continue
        scraped_pages.append(scraped)

    if not scraped_pages:
        return None, notes

    heading_counts: Counter[str] = Counter()
    question_counts: Counter[str] = Counter()
    phrase_counts: Counter[str] = Counter()
    token_counts: Counter[str] = Counter()
    page_presence: dict[str, int] = defaultdict(int)
    display_text: dict[str, str] = {}

    for page in scraped_pages:
        headings = {
            _normalize_text(text): _clean_display_text(text)
            for text in [page.h1, *page.h2_list, *page.h3_list]
            if _normalize_text(text)
        }
        questions = {
            _normalize_text(text): _clean_display_text(text)
            for text in _question_candidates(page)
            if _normalize_text(text)
        }
        phrases = {
            _normalize_text(text): _clean_display_text(text)
            for text in _phrase_candidates(page.clean_text)
            if _normalize_text(text)
        }

        for key, value in headings.items():
            heading_counts[key] += 1
            display_text.setdefault(key, value)
        for key, value in questions.items():
            question_counts[key] += 1
            display_text.setdefault(key, value)
        for key, value in phrases.items():
            phrase_counts[key] += 1
            display_text.setdefault(key, value)

        page_tokens = set()
        combined_text = " ".join([page.title, page.h1, *page.h2_list, *page.h3_list, page.clean_text])
        for token in _term_tokens(combined_text):
            token_counts[token] += 1
            page_tokens.add(token)
        for token in page_tokens:
            page_presence[token] += 1

    pages_scraped = len(scraped_pages)
    query_tokens = set(_term_tokens(query))
    thin_pages = sum(1 for page in scraped_pages if page.word_count < MIN_WORD_COUNT)
    bank = ArticleEvidenceBank(
        query=query,
        pages_scraped=pages_scraped,
        source_urls=[page.url for page in scraped_pages],
        recurring_headings=_top_signals(heading_counts, display_text, min_count=2, limit=6),
        recurring_questions=_top_signals(question_counts, display_text, min_count=2, limit=6),
        recurring_phrases=_top_signals(phrase_counts, display_text, min_count=2, limit=6),
        primary_terms=_primary_terms(token_counts, page_presence, query_tokens),
        secondary_terms=_secondary_terms(token_counts, page_presence, query_tokens),
    )
    if thin_pages:
        notes.append(f"article evidence used {pages_scraped} pages ({thin_pages} thin)")
    return bank, notes


def _candidate_urls(results: list[Any], *, max_pages: int) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for result in results:
        if isinstance(result, dict):
            url = result.get("url") or result.get("href") or ""
        else:
            url = getattr(result, "url", "") or getattr(result, "href", "")
        normalized = url.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        urls.append(normalized)
        if len(urls) >= max_pages:
            break
    return urls


def _question_candidates(page) -> list[str]:
    items = [text for text in [page.h1, *page.h2_list, *page.h3_list] if "?" in text]
    items.extend(re.findall(r"[^?!.]{12,140}\?", page.clean_text)[:MAX_SENTENCE_QUESTIONS])
    return items


def _phrase_candidates(text: str) -> set[str]:
    tokens = _term_tokens(text)
    phrases: set[str] = set()
    for size in (2, 3, 4):
        for index in range(len(tokens) - size + 1):
            window = tokens[index : index + size]
            if window[0] in STOP_WORDS or window[-1] in STOP_WORDS:
                continue
            if len([token for token in window if token not in STOP_WORDS]) < 2:
                continue
            phrase = " ".join(window)
            if 8 <= len(phrase) <= 64:
                phrases.add(phrase)
    return phrases


def _top_signals(
    counts: Counter[str],
    display_text: dict[str, str],
    *,
    min_count: int,
    limit: int,
) -> list[EvidenceSignal]:
    signals = [
        EvidenceSignal(text=display_text.get(key, key), count=count)
        for key, count in counts.items()
        if count >= min_count
    ]
    return sorted(signals, key=lambda item: (-item.count, item.text))[:limit]


def _primary_terms(
    token_counts: Counter[str],
    page_presence: dict[str, int],
    query_tokens: set[str],
) -> list[str]:
    ranked = _ranked_terms(token_counts, page_presence, query_tokens)
    primary = [term for term, _, _, _ in ranked if term in query_tokens][:4]
    for term, _, presence, _ in ranked:
        if term in primary:
            continue
        if len(primary) >= 4:
            break
        if presence >= 2:
            primary.append(term)
    return primary[:4]


def _secondary_terms(
    token_counts: Counter[str],
    page_presence: dict[str, int],
    query_tokens: set[str],
) -> list[str]:
    ranked = _ranked_terms(token_counts, page_presence, query_tokens)
    primary = set(_primary_terms(token_counts, page_presence, query_tokens))
    return [term for term, _, _, _ in ranked if term not in primary][:6]


def _ranked_terms(
    token_counts: Counter[str],
    page_presence: dict[str, int],
    query_tokens: set[str],
) -> list[tuple[str, int, int, int]]:
    items = []
    for term, count in token_counts.items():
        presence = page_presence.get(term, 0)
        if presence == 0 or count < 2:
            continue
        score = presence * 3 + min(count, 4) + (2 if term in query_tokens else 0)
        items.append((term, score, presence, count))
    return sorted(items, key=lambda item: (-item[1], -item[2], -item[3], item[0]))


def _term_tokens(text: str) -> list[str]:
    tokens = [_normalize_token(token) for token in re.findall(r"[a-z0-9][a-z0-9\\-]+", text.lower())]
    return [
        token
        for token in tokens
        if token
        and token not in STOP_WORDS
        and (len(token) >= 3 or token == "ai")
    ]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9? ]+", " ", text.lower())).strip()


def _clean_display_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip(" \n\t-:;,.")).strip()


def _normalize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token
