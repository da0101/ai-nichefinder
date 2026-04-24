from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone

from nichefinder_cli.viewer_actions import run_research_action, run_validate_free_action
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
    _validate_action(action, params)
    job_params = _public_params(params)
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
            )
        elif action == "research":
            result = run_research_action(
                profile_slug=params.get("profile"),
                keyword=str(params.get("keyword", "")).strip(),
            )
        else:
            raise ValueError(f"unsupported job action: {action}")
    except Exception as exc:
        _update_job(settings, job_id, status="failed", error=str(exc), finished_at=_utcnow())
        return
    _update_job(settings, job_id, status="succeeded", result_json=_json_dump(result), finished_at=_utcnow())


def _validate_action(action: str, params: dict) -> None:
    if action not in {"validate-free", "research"}:
        raise ValueError(f"unsupported job action: {action}")
    keyword = str(params.get("keyword", "")).strip()
    if not keyword:
        raise ValueError("keyword is required")
    sources = params.get("sources")
    if action == "research" and sources is not None:
        raise ValueError("sources are only supported for validate-free jobs")
    if sources is not None and not isinstance(sources, list):
        raise ValueError("sources must be a list")
    if sources is not None and not all(isinstance(item, str) and item for item in sources):
        raise ValueError("sources must contain non-empty strings")


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
    allowed = {"profile", "keyword", "sources"}
    public = {key: value for key, value in params.items() if key in allowed}
    public["keyword"] = str(public.get("keyword", "")).strip()
    return public


@contextmanager
def _repository(settings: Settings | None = None):
    resolved_settings = settings or get_settings()
    create_db_and_tables(resolved_settings)
    with get_session(resolved_settings) as session:
        yield SeoRepository(session)


def _json_dump(value: object) -> str:
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
