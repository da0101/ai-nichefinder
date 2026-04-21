import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from nichefinder_core.pre_serp import PreSerpCandidateScore, STOP_WORDS, _normalize_token, _tokenize


@dataclass(slots=True)
class ExternalEvidenceResult:
    title: str
    url: str
    content: str


@dataclass(slots=True)
class ExternalEvidenceValidation:
    source: str
    query: str
    score: float
    result_count: int
    top_domains: list[str]
    degraded: bool = False
    usable_for_article_evidence: bool = True
    query_variants: list[str] = field(default_factory=list)
    results: list[ExternalEvidenceResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProblemQuery:
    query: str
    group_query: str


async def apply_external_validation(
    shortlist: list[PreSerpCandidateScore],
    buyer_problems: list[Any],
    *,
    source: str,
    ready: bool,
    search: Callable[[str], Awaitable[dict]],
    max_keywords: int,
    max_keyword_validations: int,
    max_problem_validations: int,
    concurrency: int,
    base_weight: float,
) -> tuple[
    list[PreSerpCandidateScore],
    list[ExternalEvidenceValidation],
    list[ExternalEvidenceValidation],
]:
    if not ready:
        return shortlist, [], []

    candidate_keywords = shortlist[:max_keyword_validations]
    problem_queries = _problem_queries(buyer_problems[:max_problem_validations])
    query_list = list(
        dict.fromkeys([item.term for item in candidate_keywords] + [item.query for item in problem_queries])
    )
    if not query_list:
        return shortlist, [], []

    semaphore = asyncio.Semaphore(concurrency)

    async def run_search(query: str) -> tuple[str, dict]:
        async with semaphore:
            try:
                return query, await search(query)
            except Exception as exc:
                return query, {"_error": str(exc), "results": []}

    payloads = dict(await asyncio.gather(*(run_search(query) for query in query_list)))

    for item in shortlist:
        if item.term not in payloads:
            continue
        raw_score, notes, _, _, _, _, _ = _score_payload(item.term, payloads[item.term], source=source)
        score = _weighted_keyword_score(item, raw_score, base_weight=base_weight)
        item.breakdown[f"{source}_validation_raw"] = raw_score
        item.breakdown[f"{source}_validation"] = score
        item.score = round(item.score + score, 2)
        item.notes.extend(notes)

    shortlist.sort(key=lambda item: (-item.score, item.term))
    for item in shortlist:
        item.selected = False
    for item in shortlist[:max_keywords]:
        item.selected = True

    keyword_validations = []
    for item in candidate_keywords:
        score, notes, result_count, domains, results, degraded, usable_for_article_evidence = _score_payload(
            item.term,
            payloads.get(item.term, {}),
            source=source,
        )
        keyword_validations.append(
            ExternalEvidenceValidation(
                source=source,
                query=item.term,
                score=score,
                result_count=result_count,
                top_domains=domains,
                degraded=degraded,
                usable_for_article_evidence=usable_for_article_evidence,
                results=results,
                notes=notes,
            )
        )

    problem_validations = []
    grouped_queries: dict[str, list[ProblemQuery]] = {}
    for item in problem_queries:
        grouped_queries.setdefault(item.group_query, []).append(item)
    for group_query, items in grouped_queries.items():
        problem_validations.append(
            _aggregate_problem_validation(
                group_query,
                items,
                payloads,
                source=source,
            )
        )
    return shortlist, keyword_validations, problem_validations


def _problem_queries(buyer_problems: list[Any]) -> list[ProblemQuery]:
    queries: list[ProblemQuery] = []
    seen: set[tuple[str, str]] = set()
    for item in buyer_problems:
        if hasattr(item, "keyword_seed"):
            query = getattr(item, "keyword_seed", "") or getattr(item, "problem", "")
        elif isinstance(item, dict):
            query = item.get("keyword_seed") or item.get("problem") or ""
        else:
            query = ""
        query = query.strip()
        lowered = query.lower()
        if not query:
            continue
        for atomic_query in _split_problem_query(query):
            key = (lowered, atomic_query.lower())
            if key in seen:
                continue
            seen.add(key)
            queries.append(ProblemQuery(query=atomic_query, group_query=query))
    return queries


def _split_problem_query(query: str) -> list[str]:
    parts = [segment.strip() for segment in query.replace("\n", ",").replace(";", ",").split(",")]
    atomic = [item for item in parts if item]
    return atomic or [query.strip()]


def _aggregate_problem_validation(
    group_query: str,
    queries: list[ProblemQuery],
    payloads: dict[str, dict],
    *,
    source: str,
) -> ExternalEvidenceValidation:
    scores: list[float] = []
    notes: list[str] = []
    top_domains: list[str] = []
    results: list[ExternalEvidenceResult] = []
    seen_domains: set[str] = set()
    seen_urls: set[str] = set()
    result_count = 0
    degraded = False
    usable_for_article_evidence = True

    for item in queries:
        (
            score,
            item_notes,
            item_result_count,
            domains,
            item_results,
            item_degraded,
            item_usable_for_article_evidence,
        ) = _score_payload(
            item.query,
            payloads.get(item.query, {}),
            source=source,
        )
        scores.append(score)
        result_count = max(result_count, item_result_count)
        notes.extend(item_notes)
        degraded = degraded or item_degraded
        usable_for_article_evidence = usable_for_article_evidence and item_usable_for_article_evidence
        for domain in domains:
            lowered = domain.lower()
            if lowered in seen_domains:
                continue
            seen_domains.add(lowered)
            top_domains.append(domain)
        for result in item_results:
            key = result.url.strip().lower()
            if not key or key in seen_urls:
                continue
            seen_urls.add(key)
            results.append(result)

    positive_variants = sum(1 for score in scores if score > 0)
    aggregate_score = max(scores, default=0.0)
    if positive_variants >= 2:
        aggregate_score += 1.0
        notes.append(f"{source} variant agreement")
    notes.append(f"{positive_variants}/{len(queries)} seed variants matched")
    return ExternalEvidenceValidation(
        source=source,
        query=group_query,
        score=round(aggregate_score, 2),
        result_count=result_count,
        top_domains=top_domains[:3],
        degraded=degraded,
        usable_for_article_evidence=usable_for_article_evidence,
        query_variants=[item.query for item in queries],
        results=results[:3],
        notes=list(dict.fromkeys(notes)),
    )


def _score_payload(
    query: str,
    payload: dict,
    *,
    source: str,
) -> tuple[float, list[str], int, list[str], list[ExternalEvidenceResult], bool, bool]:
    meta = payload.get("_meta") if isinstance(payload, dict) and isinstance(payload.get("_meta"), dict) else {}
    degraded_reason = str(meta.get("degraded_reason", "")).strip()
    reason_suffix = f" ({degraded_reason.replace('_', ' ')})" if degraded_reason else ""
    if not isinstance(payload, dict):
        return 0.0, [f"{source}: unavailable"], 0, [], [], True, False
    if payload.get("_error"):
        return 0.0, [f"{source}: unavailable{reason_suffix}"], 0, [], [], True, False

    results = payload.get("results", [])
    degraded = bool(meta.get("degraded"))
    if not results:
        notes = [f"{source}: no evidence"]
        if degraded:
            notes.append(f"{source}: degraded{reason_suffix}")
        return -6.0, notes, 0, [], [], degraded, False

    query_tokens = {
        _normalize_token(token)
        for token in _tokenize(query)
        if _normalize_token(token) not in STOP_WORDS
    }
    result_count = min(len(results), 3)
    relevant_hits = 0
    exact_hits = 0
    domains: list[str] = []
    normalized_results: list[ExternalEvidenceResult] = []
    for result in results[:3]:
        title = result.get("title", "")
        content = result.get("content") or result.get("body") or result.get("snippet") or ""
        url = result.get("url") or result.get("href") or ""
        text = f"{title} {content}".lower()
        result_tokens = {
            _normalize_token(token)
            for token in _tokenize(text)
            if _normalize_token(token) not in STOP_WORDS
        }
        overlap_needed = max(1, min(3, len(query_tokens) // 2 or 1))
        if query_tokens and len(query_tokens & result_tokens) >= overlap_needed:
            relevant_hits += 1
        if query.lower() in text:
            exact_hits += 1
        domain = urlparse(url).netloc
        if domain:
            domains.append(domain)
        normalized_results.append(
            ExternalEvidenceResult(title=title, url=url, content=content)
        )

    unique_domains = list(dict.fromkeys(domains))
    score = 0.0
    notes: list[str] = []
    if result_count >= 2:
        score += 2.0
        notes.append(f"{source} results")
    if relevant_hits >= 2:
        score += 4.0
        notes.append(f"{source} relevance")
    elif relevant_hits == 0:
        score -= 4.0
        notes.append(f"weak {source} relevance")
    if exact_hits:
        score += 2.0
        notes.append(f"{source} exact match")
    if len(unique_domains) >= 2:
        score += 2.0
        notes.append(f"{source} diversity")
    usable_for_article_evidence = score > 0
    if degraded:
        score = min(score, 0.0)
        usable_for_article_evidence = False
        notes.append(f"{source}: degraded{reason_suffix}")
    return score, notes, result_count, unique_domains[:3], normalized_results, degraded, usable_for_article_evidence


def _weighted_keyword_score(item: PreSerpCandidateScore, raw_score: float, *, base_weight: float) -> float:
    seed_fidelity = item.breakdown.get("seed_fidelity", 0.0)
    query_drift = item.breakdown.get("query_drift", 0.0)
    developer_penalty = item.breakdown.get("developer_penalty", 0.0)
    local_intent = item.breakdown.get("local_intent", 0.0)

    weight = base_weight
    if seed_fidelity >= 30:
        weight += 0.45
    elif seed_fidelity >= 20:
        weight += 0.25
    elif seed_fidelity >= 12:
        weight += 0.1

    if query_drift < 0:
        weight -= min(0.35, abs(query_drift) / 40.0)
    if developer_penalty < 0:
        weight -= 0.25
    if local_intent > 0 and seed_fidelity < 20:
        weight -= 0.1

    weight = max(0.15, min(1.0, weight))
    return round(raw_score * weight, 2)
