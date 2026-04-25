from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone

from nichefinder_cli.viewer_actions import (
    run_generate_brief_action,
    run_monitor_sync_action,
    run_rank_check_action,
    run_research_action,
    run_rewrite_article_action,
    run_validate_free_action,
    run_write_article_action,
)
from nichefinder_cli.viewer_api_models import (
    JobEnvelope,
    KeywordIdJobParams,
    MonitorSyncJobParams,
    RankCheckJobParams,
    ResearchJobParams,
    RewriteJobParams,
    ValidateFreeJobParams,
)
from nichefinder_core.models import JobRecord
from nichefinder_core.settings import Settings, get_settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="nichefinder-job")


def list_jobs(settings: Settings | None = None) -> dict:
    with _repository(settings) as repository:
        jobs = [_public_job(job) for job in repository.list_jobs()]
    return {"jobs": jobs}


def get_job(job_id: str, settings: Settings | None = None) -> dict | None:
    with _repository(settings) as repository:
        job = repository.get_job(job_id)
        return _public_job(job) if job is not None else None


def submit_job(action: str, payload: dict | None = None, settings: Settings | None = None) -> dict:
    params = payload or {}
    job_params = _validated_job_params(action, params)
    resolved_settings = settings or get_settings()
    with _repository(resolved_settings) as repository:
        job = repository.create_job(action=action, params_json=_json_dump(job_params))
    _executor.submit(_run_job, job.id, action, job_params, resolved_settings)
    return _public_job(job)


def _run_job(job_id: str, action: str, params: dict, settings: Settings) -> None:
    _update_job(settings, job_id, status="running", started_at=_utcnow())
    try:
        if action == "validate-free":
            result = run_validate_free_action(
                profile_slug=params.get("profile"),
                keyword=str(params.get("keyword", "")).strip(),
                sources=tuple(params.get("sources") or ["ddgs", "bing", "yahoo"]),
                settings_override=settings,
            )
        elif action == "research":
            result = run_research_action(
                profile_slug=params.get("profile"),
                keyword=str(params.get("keyword", "")).strip(),
                settings_override=settings,
            )
        elif action == "brief":
            result = run_generate_brief_action(
                profile_slug=params.get("profile"),
                keyword_id=str(params.get("keyword_id", "")).strip(),
                force=bool(params.get("force", False)),
                settings_override=settings,
            )
        elif action == "write":
            result = run_write_article_action(
                profile_slug=params.get("profile"),
                keyword_id=str(params.get("keyword_id", "")).strip(),
                force=bool(params.get("force", False)),
                settings_override=settings,
            )
        elif action == "rewrite":
            result = run_rewrite_article_action(
                profile_slug=params.get("profile"),
                url=str(params.get("url", "")).strip(),
                settings_override=settings,
            )
        elif action == "monitor-sync":
            result = run_monitor_sync_action(
                profile_slug=params.get("profile"),
                days=int(params.get("days", 7)),
                property_url=params.get("property_url"),
                settings_override=settings,
            )
        elif action == "rank-check":
            result = run_rank_check_action(
                profile_slug=params.get("profile"),
                skip_recent=bool(params.get("skip_recent", True)),
                settings_override=settings,
            )
        else:
            raise ValueError(f"unsupported job action: {action}")
    except Exception as exc:
        _update_job(settings, job_id, status="failed", error=str(exc), finished_at=_utcnow())
        return
    _update_job(settings, job_id, status="succeeded", result_json=_json_dump(result), finished_at=_utcnow())


def _validated_job_params(action: str, params: dict) -> dict:
    if action == "validate-free":
        validated = ValidateFreeJobParams.model_validate(params)
    elif action == "research":
        validated = ResearchJobParams.model_validate(params)
    elif action in {"brief", "write"}:
        validated = KeywordIdJobParams.model_validate(params)
    elif action == "rewrite":
        validated = RewriteJobParams.model_validate(params)
    elif action == "monitor-sync":
        validated = MonitorSyncJobParams.model_validate(params)
    elif action == "rank-check":
        validated = RankCheckJobParams.model_validate(params)
    else:
        raise ValueError(f"unsupported job action: {action}")
    envelope = JobEnvelope(action=action, params=validated)
    return envelope.params.model_dump(exclude_none=True)


def _update_job(settings: Settings, job_id: str, **changes) -> None:
    with _repository(settings) as repository:
        repository.update_job(job_id, **changes)


def _public_job(job: JobRecord) -> dict:
    return {
        "id": job.id,
        "action": job.action,
        "status": job.status,
        "params": _json_load(job.params_json, default={}),
        "result": _json_load(job.result_json, default=None),
        "error": job.error,
        "created_at": _format_datetime(job.created_at),
        "updated_at": _format_datetime(job.updated_at),
        "started_at": _format_datetime(job.started_at),
        "finished_at": _format_datetime(job.finished_at),
    }


def _public_params(params: dict) -> dict:
    allowed = {"profile", "keyword", "keyword_id", "sources", "force", "url", "days", "property_url", "skip_recent"}
    public = {key: value for key, value in params.items() if key in allowed}
    if "keyword" in public or "keyword" in params:
        public["keyword"] = str(public.get("keyword", "")).strip()
    if "keyword_id" in public or "keyword_id" in params:
        public["keyword_id"] = str(public.get("keyword_id", "")).strip()
    return public


@contextmanager
def _repository(settings: Settings | None = None):
    resolved_settings = settings or get_settings()
    create_db_and_tables(resolved_settings)
    with get_session(resolved_settings) as session:
        yield SeoRepository(session)


def _json_dump(value: object) -> str:
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"))
    return json.dumps(value)


def _json_load(value: str | None, *, default):
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _format_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
