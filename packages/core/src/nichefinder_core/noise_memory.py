import json
import re
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.settings import Settings

STOP_WORDS = {
    "a",
    "an",
    "and",
    "be",
    "does",
    "do",
    "for",
    "how",
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
    "what",
    "when",
    "why",
}
LOCAL_TERMS = {"canada", "montreal", "qc", "quebec"}
GENERIC_QUERY_TERMS = {
    "budget",
    "business",
    "compare",
    "comparison",
    "cost",
    "costs",
    "guide",
    "guides",
    "price",
    "prices",
    "pricing",
    "quote",
    "quotes",
}
SignalLabel = Literal["noise", "validity", "legitimacy"]
SignalScope = Literal["domain", "keyword_phrase", "secondary_phrase"]


class LearnedSignalEntry(BaseModel):
    scope: SignalScope
    label: SignalLabel
    value: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MemoryObservation(BaseModel):
    scope: SignalScope
    label: SignalLabel
    value: str
    source_query: str = ""
    example: str = ""


class ValidationRunObservation(BaseModel):
    run_id: str
    seed_keyword: str
    location: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    observations: list[MemoryObservation] = Field(default_factory=list)


class NoiseMemory(BaseModel):
    site_fingerprint: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    runs: list[ValidationRunObservation] = Field(default_factory=list)
    approved_entries: list[LearnedSignalEntry] = Field(default_factory=list)
    approved_noise: list[dict | LearnedSignalEntry] = Field(default_factory=list)


class LearnedNoiseCandidate(BaseModel):
    scope: SignalScope
    label: SignalLabel
    value: str
    support_runs: int
    support_count: int
    examples: list[str] = Field(default_factory=list)


class LearnedNoiseProfile(BaseModel):
    domains: list[str] = Field(default_factory=list)
    keyword_phrases: list[str] = Field(default_factory=list)
    secondary_phrases: list[str] = Field(default_factory=list)
    trusted_domains: list[str] = Field(default_factory=list)
    valid_keyword_phrases: list[str] = Field(default_factory=list)
    valid_secondary_phrases: list[str] = Field(default_factory=list)

    @property
    def has_entries(self) -> bool:
        return bool(
            self.domains
            or self.keyword_phrases
            or self.secondary_phrases
            or self.trusted_domains
            or self.valid_keyword_phrases
            or self.valid_secondary_phrases
        )


def load_noise_memory(settings: Settings, *, site_config: dict) -> NoiseMemory:
    fingerprint = _site_fingerprint(site_config)
    payload = load_json_cache(settings, namespace="noise-memory", key=fingerprint, max_age_hours=0)
    if not payload:
        return NoiseMemory(site_fingerprint=fingerprint)
    try:
        memory = NoiseMemory.model_validate(payload)
    except Exception:
        return NoiseMemory(site_fingerprint=fingerprint)
    if memory.site_fingerprint != fingerprint:
        return NoiseMemory(site_fingerprint=fingerprint)
    migrated = _migrate_legacy_entries(memory)
    if migrated:
        save_noise_memory(settings, site_config=site_config, memory=memory)
    return memory


def save_noise_memory(settings: Settings, *, site_config: dict, memory: NoiseMemory) -> None:
    memory.updated_at = datetime.now(UTC)
    save_json_cache(
        settings,
        namespace="noise-memory",
        key=_site_fingerprint(site_config),
        payload=memory.model_dump(mode="json"),
    )


def load_noise_profile(settings: Settings, *, site_config: dict) -> LearnedNoiseProfile:
    approved = _approved_entries(load_noise_memory(settings, site_config=site_config))
    return LearnedNoiseProfile(
        domains=sorted({normalize_domain(entry.value) for entry in approved if entry.scope == "domain" and entry.label == "noise"}),
        keyword_phrases=sorted({normalize_text(entry.value) for entry in approved if entry.scope == "keyword_phrase" and entry.label == "noise"}),
        secondary_phrases=sorted({normalize_text(entry.value) for entry in approved if entry.scope == "secondary_phrase" and entry.label == "noise"}),
        trusted_domains=sorted({normalize_domain(entry.value) for entry in approved if entry.scope == "domain" and entry.label == "legitimacy"}),
        valid_keyword_phrases=sorted({normalize_text(entry.value) for entry in approved if entry.scope == "keyword_phrase" and entry.label == "validity"}),
        valid_secondary_phrases=sorted({normalize_text(entry.value) for entry in approved if entry.scope == "secondary_phrase" and entry.label == "validity"}),
    )


def approve_noise_entries(
    settings: Settings,
    *,
    site_config: dict,
    keyword_phrases: list[str] | None = None,
    secondary_phrases: list[str] | None = None,
    domains: list[str] | None = None,
) -> LearnedNoiseProfile:
    return approve_training_entries(
        settings,
        site_config=site_config,
        noise_keyword_phrases=keyword_phrases,
        noise_secondary_phrases=secondary_phrases,
        noise_domains=domains,
    )


def approve_training_entries(
    settings: Settings,
    *,
    site_config: dict,
    noise_keyword_phrases: list[str] | None = None,
    noise_secondary_phrases: list[str] | None = None,
    noise_domains: list[str] | None = None,
    valid_keyword_phrases: list[str] | None = None,
    valid_secondary_phrases: list[str] | None = None,
    trusted_domains: list[str] | None = None,
) -> LearnedNoiseProfile:
    memory = load_noise_memory(settings, site_config=site_config)
    existing = {
        (
            entry.scope,
            entry.label,
            normalize_domain(entry.value) if entry.scope == "domain" else normalize_text(entry.value),
        )
        for entry in _approved_entries(memory)
    }
    for scope, label, values in (
        ("keyword_phrase", "noise", noise_keyword_phrases or []),
        ("secondary_phrase", "noise", noise_secondary_phrases or []),
        ("domain", "noise", noise_domains or []),
        ("keyword_phrase", "validity", valid_keyword_phrases or []),
        ("secondary_phrase", "validity", valid_secondary_phrases or []),
        ("domain", "legitimacy", trusted_domains or []),
    ):
        for value in values:
            normalized = normalize_domain(value) if scope == "domain" else normalize_text(value)
            key = (scope, label, normalized)
            if not normalized or key in existing:
                continue
            existing.add(key)
            memory.approved_entries.append(LearnedSignalEntry(scope=scope, label=label, value=normalized))
    save_noise_memory(settings, site_config=site_config, memory=memory)
    return load_noise_profile(settings, site_config=site_config)


def record_validation_run(
    settings: Settings,
    *,
    site_config: dict,
    seed_keyword: str,
    location: str,
    shortlist: list,
    keyword_validations: list,
    article_evidence: list,
) -> NoiseMemory:
    memory = load_noise_memory(settings, site_config=site_config)
    seen: set[tuple[str, str, str, str]] = set()
    observations: list[MemoryObservation] = []

    validated_queries = {normalize_text(getattr(item, "query", "")) for item in keyword_validations}
    for validation in keyword_validations:
        query = getattr(validation, "query", "")
        positive_signal = float(getattr(validation, "score", 0.0)) > 0 and not bool(getattr(validation, "degraded", False))
        phrase_label: SignalLabel = "validity" if positive_signal else "noise"
        domain_label: SignalLabel = "legitimacy" if positive_signal else "noise"
        for phrase in extract_keyword_phrases(query, seed_keyword=seed_keyword):
            _append_observation(
                observations,
                seen,
                scope="keyword_phrase",
                label=phrase_label,
                value=phrase,
                source_query=query,
                example=query,
            )
        for domain in getattr(validation, "top_domains", [])[:3]:
            _append_observation(
                observations,
                seen,
                scope="domain",
                label=domain_label,
                value=domain,
                source_query=query,
                example=query,
            )

    for item in shortlist[:4]:
        term = getattr(item, "term", "")
        if normalize_text(term) in validated_queries:
            continue
        label: SignalLabel = "validity" if float(getattr(item, "score", 0.0)) >= 70 else "noise"
        for phrase in extract_keyword_phrases(term, seed_keyword=seed_keyword):
            _append_observation(
                observations,
                seen,
                scope="keyword_phrase",
                label=label,
                value=phrase,
                source_query=term,
                example=term,
            )

    for summary in article_evidence:
        query = getattr(summary, "query", "")
        for phrase in getattr(summary, "suggested_secondary_keywords", [])[:8]:
            _append_observation(
                observations,
                seen,
                scope="secondary_phrase",
                label="validity",
                value=phrase,
                source_query=query,
                example=query,
            )
        for url in getattr(summary, "source_urls", [])[:3]:
            _append_observation(
                observations,
                seen,
                scope="domain",
                label="legitimacy",
                value=url,
                source_query=query,
                example=query,
            )

    memory.runs.append(
        ValidationRunObservation(
            run_id=f"{datetime.now(UTC).timestamp():.6f}",
            seed_keyword=seed_keyword,
            location=location,
            observations=observations,
        )
    )
    memory.runs = memory.runs[-50:]
    save_noise_memory(settings, site_config=site_config, memory=memory)
    return memory


def summarize_noise_candidates(
    settings: Settings,
    *,
    site_config: dict,
    min_runs: int = 2,
    limit: int = 10,
) -> list[LearnedNoiseCandidate]:
    return summarize_training_candidates(
        settings,
        site_config=site_config,
        min_runs=min_runs,
        limit=limit,
        label="noise",
    )


def summarize_training_candidates(
    settings: Settings,
    *,
    site_config: dict,
    min_runs: int = 2,
    limit: int = 10,
    label: SignalLabel | None = None,
) -> list[LearnedNoiseCandidate]:
    memory = load_noise_memory(settings, site_config=site_config)
    approved = {
        (
            entry.scope,
            entry.label,
            normalize_domain(entry.value) if entry.scope == "domain" else normalize_text(entry.value),
        )
        for entry in _approved_entries(memory)
    }
    aggregate: dict[tuple[str, str, str], dict] = {}
    for run in memory.runs:
        seen_in_run: set[tuple[str, str, str]] = set()
        for observation in run.observations:
            normalized = normalize_domain(observation.value) if observation.scope == "domain" else normalize_text(observation.value)
            key = (observation.scope, observation.label, normalized)
            if not normalized or key in approved or (label and observation.label != label):
                continue
            bucket = aggregate.setdefault(key, {"runs": set(), "count": 0, "examples": []})
            bucket["count"] += 1
            if key not in seen_in_run:
                bucket["runs"].add(run.run_id)
                seen_in_run.add(key)
            if observation.example and observation.example not in bucket["examples"]:
                bucket["examples"].append(observation.example)
    candidates = [
        LearnedNoiseCandidate(
            scope=scope,
            label=item_label,
            value=value,
            support_runs=len(bucket["runs"]),
            support_count=bucket["count"],
            examples=bucket["examples"][:3],
        )
        for (scope, item_label, value), bucket in aggregate.items()
        if len(bucket["runs"]) >= min_runs
    ]
    candidates.sort(key=lambda item: (-item.support_runs, -item.support_count, item.label, item.scope, item.value))
    return candidates[:limit]


def learning_memory_stats(settings: Settings, *, site_config: dict) -> dict[str, int]:
    memory = load_noise_memory(settings, site_config=site_config)
    approved = _approved_entries(memory)
    return {
        "runs": len(memory.runs),
        "approved_noise": len([entry for entry in approved if entry.label == "noise"]),
        "approved_validity": len([entry for entry in approved if entry.label == "validity"]),
        "approved_legitimacy": len([entry for entry in approved if entry.label == "legitimacy"]),
    }


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower())).strip()


def normalize_domain(value: str) -> str:
    raw = str(value).strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        raw = urlparse(raw).netloc.lower()
    return raw.removeprefix("www.")


def phrase_matches_text(phrase: str, text: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    normalized_text = normalize_text(text)
    return bool(
        normalized_phrase
        and normalized_text
        and re.search(rf"(^| ){re.escape(normalized_phrase)}($| )", normalized_text)
    )


def domain_matches_url(domain: str, url: str) -> bool:
    normalized_domain = normalize_domain(domain)
    normalized_url_domain = normalize_domain(url)
    return bool(normalized_domain and normalized_url_domain and normalized_url_domain.endswith(normalized_domain))


def extract_keyword_phrases(term: str, *, seed_keyword: str) -> list[str]:
    seed_tokens = set(_meaningful_tokens(seed_keyword))
    tokens = [token for token in _meaningful_tokens(term) if token not in seed_tokens]
    phrases: list[str] = []
    for size in (3, 2):
        for index in range(0, max(0, len(tokens) - size + 1)):
            phrase = " ".join(tokens[index : index + size]).strip()
            if len(phrase.split()) != size or phrase in phrases:
                continue
            phrases.append(phrase)
    return phrases[:3]


def _approved_entries(memory: NoiseMemory) -> list[LearnedSignalEntry]:
    entries = list(memory.approved_entries)
    for entry in memory.approved_noise:
        try:
            legacy = LearnedSignalEntry.model_validate(entry)
        except Exception:
            continue
        if legacy.label != "noise":
            legacy = legacy.model_copy(update={"label": "noise"})
        entries.append(legacy)
    return entries


def _append_observation(
    observations: list[MemoryObservation],
    seen: set[tuple[str, str, str, str]],
    *,
    scope: SignalScope,
    label: SignalLabel,
    value: str,
    source_query: str,
    example: str,
) -> None:
    normalized = normalize_domain(value) if scope == "domain" else normalize_text(value)
    key = (scope, label, normalized, normalize_text(source_query))
    if not normalized or key in seen:
        return
    seen.add(key)
    observations.append(
        MemoryObservation(
            scope=scope,
            label=label,
            value=normalized,
            source_query=source_query,
            example=example,
        )
    )


def _migrate_legacy_entries(memory: NoiseMemory) -> bool:
    if not memory.approved_noise:
        return False
    existing = {(entry.scope, entry.label, entry.value) for entry in memory.approved_entries}
    migrated = False
    for entry in memory.approved_noise:
        try:
            legacy = LearnedSignalEntry.model_validate(entry)
        except Exception:
            continue
        if legacy.label != "noise":
            legacy = legacy.model_copy(update={"label": "noise"})
        key = (legacy.scope, legacy.label, legacy.value)
        if key in existing:
            continue
        memory.approved_entries.append(legacy)
        existing.add(key)
        migrated = True
    if migrated:
        memory.approved_noise = []
    return migrated


def _meaningful_tokens(text: str) -> list[str]:
    tokens = [token for token in normalize_text(text).split() if token]
    return [token for token in tokens if token not in STOP_WORDS and token not in LOCAL_TERMS and token not in GENERIC_QUERY_TERMS]


def _site_fingerprint(site_config: dict) -> str:
    return json.dumps(
        {
            "site_name": site_config.get("site_name"),
            "site_description": site_config.get("site_description"),
            "target_audience": site_config.get("target_audience"),
            "services": site_config.get("services", []),
        },
        sort_keys=True,
    )
