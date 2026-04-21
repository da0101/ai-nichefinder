from collections import Counter
from dataclasses import dataclass, field

from nichefinder_core.pre_serp import LOCAL_TERMS, STOP_WORDS, _normalize_token, _tokenize

SOURCE_ORDER = {"ddgs": 0, "bing": 1, "yahoo": 2, "tavily": 3, "serp": 4}
FAMILY_DROP_TERMS = STOP_WORDS | LOCAL_TERMS | {"does", "kind", "much"}


@dataclass(slots=True)
class CrossSourcePatternSummary:
    query: str
    sources: list[str]
    agreement: str
    query_variants: list[str] = field(default_factory=list)
    repeated_domains: list[str] = field(default_factory=list)
    repeated_secondary_keywords: list[str] = field(default_factory=list)
    repeated_questions: list[str] = field(default_factory=list)


def summarize_cross_source_patterns(
    validations: list,
    article_evidence: list | None = None,
    *,
    grouping: str = "exact",
) -> list[CrossSourcePatternSummary]:
    if not validations:
        return []

    evidence_by_key: dict[tuple[str, str], object] = {}
    for item in article_evidence or []:
        key = (_normalize_query(getattr(item, "query", "")), str(getattr(item, "source", "")).lower())
        evidence_by_key[key] = item

    grouped: dict[str, list] = {}
    query_labels: dict[str, str] = {}
    query_variants: dict[str, set[str]] = {}
    for item in validations:
        if bool(getattr(item, "degraded", False)):
            continue
        if float(getattr(item, "score", 0.0)) <= 0:
            continue
        raw_query = getattr(item, "query", "")
        key = _group_key(raw_query, grouping=grouping)
        if not key:
            continue
        grouped.setdefault(key, []).append(item)
        query_labels.setdefault(key, raw_query)
        query_variants.setdefault(key, set()).add(raw_query)

    summaries: list[CrossSourcePatternSummary] = []
    for key, items in grouped.items():
        ordered_items = sorted(
            items,
            key=lambda item: (
                SOURCE_ORDER.get(str(getattr(item, "source", "")).lower(), 99),
                str(getattr(item, "source", "")).lower(),
            ),
        )
        sources = [str(getattr(item, "source", "")).upper() for item in ordered_items]
        domain_counts = Counter()
        secondary_counts = Counter()
        question_counts = Counter()

        for item in ordered_items:
            for domain in _unique_lower(getattr(item, "top_domains", [])):
                domain_counts[domain] += 1
            evidence = evidence_by_key.get((key, str(getattr(item, "source", "")).lower()))
            if evidence is None:
                continue
            for keyword in _unique_lower(getattr(evidence, "suggested_secondary_keywords", [])):
                secondary_counts[keyword] += 1
            for question in _unique_lower(getattr(evidence, "question_bank", [])):
                question_counts[question] += 1

        source_count = len(sources)
        summaries.append(
            CrossSourcePatternSummary(
                query=query_labels[key],
                sources=sources,
                agreement=_agreement_label(source_count),
                query_variants=sorted(query_variants[key]),
                repeated_domains=_rank_items(domain_counts),
                repeated_secondary_keywords=_rank_items(secondary_counts),
                repeated_questions=_rank_items(question_counts),
            )
        )

    summaries.sort(
        key=lambda item: (
            -len(item.sources),
            -len(item.repeated_domains),
            -len(item.repeated_secondary_keywords),
            item.query.lower(),
        )
    )
    return summaries


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().split())


def _group_key(query: str, *, grouping: str) -> str:
    if grouping == "family":
        return _family_key(query)
    return _normalize_query(query)


def _unique_lower(items: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        value = " ".join(str(item).split()).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(value)
    return normalized


def _rank_items(counter: Counter[str], limit: int = 3) -> list[str]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    repeated = [value for value, count in ranked if count >= 2]
    if repeated:
        return repeated[:limit]
    return [value for value, _ in ranked[:limit]]


def _agreement_label(source_count: int) -> str:
    if source_count >= 3:
        return "3-source"
    if source_count == 2:
        return "2-source"
    return "single-source"


def _family_key(query: str) -> str:
    tokens = [
        _normalize_token(token)
        for token in _tokenize(query)
        if _normalize_token(token) not in FAMILY_DROP_TERMS
    ]
    unique_tokens = sorted(dict.fromkeys(tokens))
    return " ".join(unique_tokens)


def apply_overlap_confidence(shortlist: list, exact_patterns: list, family_patterns: list) -> list:
    if not shortlist:
        return shortlist

    exact_by_query = {_normalize_query(item.query): item for item in exact_patterns}
    family_by_key = {_family_key(item.query): item for item in family_patterns}
    for item in shortlist:
        exact_pattern = exact_by_query.get(_normalize_query(getattr(item, "term", "")))
        family_pattern = family_by_key.get(_family_key(getattr(item, "term", "")))
        bonus = 0.0
        if exact_pattern is not None:
            bonus += _pattern_bonus(exact_pattern, is_family=False)
        if family_pattern is not None and len(getattr(family_pattern, "query_variants", [])) >= 2:
            bonus += _pattern_bonus(family_pattern, is_family=True)
        if bonus <= 0:
            continue
        item.breakdown["free_overlap_bonus"] = round(bonus, 2)
        item.score = round(item.score + bonus, 2)
        item.notes.append(f"free overlap +{bonus:.1f}")
    shortlist.sort(key=lambda row: (-row.score, row.term))
    return shortlist


def _pattern_bonus(pattern: CrossSourcePatternSummary, *, is_family: bool) -> float:
    source_count = len(pattern.sources)
    if source_count < 2:
        return 0.0
    bonus = 1.5 if source_count == 2 else 3.0
    if is_family:
        bonus *= 0.5
    if len(pattern.repeated_domains) >= 2:
        bonus += 0.5
    if pattern.repeated_secondary_keywords or pattern.repeated_questions:
        bonus += 0.5
    return bonus
