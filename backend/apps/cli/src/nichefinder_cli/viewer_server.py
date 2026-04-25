import json
from hmac import compare_digest
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.viewer_actions import (
    approve_article_action,
    create_profile_action,
    delete_profile_action,
    load_profile_config,
    publish_article_action,
    run_validate_free_action,
    save_profile_config_action,
)
from nichefinder_cli.viewer_api_models import NoiseApprovalRequest, TrainingApprovalRequest
from nichefinder_cli.viewer_data import (
    load_articles,
    load_budget,
    load_dashboard,
    load_keyword_clusters,
    load_keyword_detail,
    load_keywords,
    load_report,
    load_status,
)
from nichefinder_cli.viewer_html import HTML
from nichefinder_cli.viewer_jobs import get_job, list_jobs, submit_job
from nichefinder_cli.viewer_profile_data import (
    approve_noise_review,
    approve_training_review,
    load_final_review,
    load_noise_review,
    load_profiles,
    load_training_review,
    switch_active_profile,
)


def create_viewer_app(settings: Settings) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/api/dashboard")
    async def dashboard() -> JSONResponse:
        return _safe_json(lambda: load_dashboard(settings))

    @app.get("/api/keywords")
    async def keywords() -> JSONResponse:
        return _safe_json(lambda: load_keywords(settings))

    @app.get("/api/keyword-clusters")
    async def keyword_clusters() -> JSONResponse:
        return _safe_json(lambda: load_keyword_clusters(settings))

    @app.get("/api/keywords/{keyword_id}")
    async def keyword_detail(keyword_id: str) -> JSONResponse:
        try:
            detail = load_keyword_detail(settings, keyword_id)
        except Exception as exc:
            return _error(str(exc), status=500)
        if detail is None:
            return _error("keyword not found", status=404)
        return _json(detail)

    @app.get("/api/profiles")
    async def profiles() -> JSONResponse:
        return _safe_json(load_profiles)

    @app.get("/api/training-review")
    async def training_review(profile: str | None = None, min_runs: int = 2, limit: int = 18) -> JSONResponse:
        return _safe_json(lambda: load_training_review(profile_slug=profile, min_runs=min_runs, limit=limit))

    @app.get("/api/noise-review")
    async def noise_review(profile: str | None = None, min_runs: int = 2, limit: int = 12) -> JSONResponse:
        return _safe_json(lambda: load_noise_review(profile_slug=profile, min_runs=min_runs, limit=limit))

    @app.get("/api/final-review")
    async def final_review(profiles: str | None = None, min_runs: int = 2, limit: int = 9) -> JSONResponse:
        selected = [item for item in (profiles or "").split(",") if item]
        return _safe_json(lambda: load_final_review(profiles=selected or None, min_runs=min_runs, limit=limit))

    @app.get("/api/profile-config")
    async def profile_config(profile: str | None = None) -> JSONResponse:
        return _safe_json(lambda: load_profile_config(profile_slug=profile))

    @app.get("/api/status")
    async def status() -> JSONResponse:
        return _json({"status": "ok", "api": "nichefinder-local", "mode": "local"})

    @app.get("/api/status/detail")
    async def status_detail() -> JSONResponse:
        return _safe_json(lambda: load_status(settings))

    @app.get("/api/articles")
    async def articles() -> JSONResponse:
        return _safe_json(lambda: load_articles(settings))

    @app.get("/api/report")
    async def report() -> JSONResponse:
        return _safe_json(lambda: load_report(settings))

    @app.get("/api/budget")
    async def budget() -> JSONResponse:
        return _safe_json(lambda: load_budget(settings))

    @app.get("/api/jobs")
    async def jobs() -> JSONResponse:
        return _json(list_jobs(settings))

    @app.get("/api/jobs/{job_id}")
    async def job(job_id: str) -> JSONResponse:
        payload = get_job(job_id, settings)
        if payload is None:
            return _error("job not found", status=404)
        return _json(payload)

    @app.post("/api/profiles/active")
    async def switch_profile(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            return _json(switch_active_profile(payload.get("profile")))
        except ValueError as exc:
            return _error(str(exc), status=404)
        except Exception as exc:
            return _error(str(exc), status=500)

    @app.post("/api/training-approve")
    async def training_approve(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            approved = TrainingApprovalRequest.model_validate(payload)
            return _json(
                approve_training_review(
                    profile_slug=approved.profile,
                    noise_keyword_phrases=approved.noise_keyword_phrases,
                    noise_secondary_phrases=approved.noise_secondary_phrases,
                    noise_domains=approved.noise_domains,
                    valid_keyword_phrases=approved.valid_keyword_phrases,
                    valid_secondary_phrases=approved.valid_secondary_phrases,
                    trusted_domains=approved.trusted_domains,
                    min_runs=approved.min_runs,
                    limit=approved.limit,
                )
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/noise-approve")
    async def noise_approve(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            approved = NoiseApprovalRequest.model_validate(payload)
            return _json(
                approve_noise_review(
                    profile_slug=approved.profile,
                    keyword_phrases=approved.keyword_phrases,
                    secondary_phrases=approved.secondary_phrases,
                    domains=approved.domains,
                    min_runs=approved.min_runs,
                    limit=approved.limit,
                )
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/profiles")
    async def create_profile(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            return _json(
                create_profile_action(
                    slug=str(payload.get("slug", "")).strip(),
                    from_current=bool(payload.get("from_current", False)),
                    use=bool(payload.get("use", False)),
                    payload=payload.get("site_config"),
                ),
                status=201,
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/profile-config")
    async def save_profile_config(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            return _json(
                save_profile_config_action(
                    profile_slug=payload.get("profile"),
                    payload=payload.get("site_config", {}),
                )
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/profiles/delete")
    async def delete_profile_post(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            return _json(delete_profile_action(profile_slug=str(payload.get("profile", "")).strip()))
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/validate-free")
    async def validate_free(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            return _json(
                run_validate_free_action(
                    profile_slug=payload.get("profile"),
                    keyword=str(payload.get("keyword", "")).strip(),
                    sources=tuple(_as_list(payload.get("sources")) or ["ddgs", "bing", "yahoo"]),
                )
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/jobs")
    async def create_job(request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            params = payload.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            return _json(submit_job(str(payload.get("action", "")).strip(), params, settings), status=202)
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.post("/api/articles/{article_id}/{article_action}")
    async def mutate_article(article_id: str, article_action: str, request: Request) -> JSONResponse:
        if article_action not in {"approve", "publish"}:
            return _error("not found", status=404)
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            payload = await _read_json(request)
            if article_action == "approve":
                return _json(
                    approve_article_action(
                        profile_slug=payload.get("profile"),
                        article_id=article_id,
                        settings_override=settings,
                    )
                )
            return _json(
                publish_article_action(
                    profile_slug=payload.get("profile"),
                    article_id=article_id,
                    url=str(payload.get("url", "")).strip(),
                    settings_override=settings,
                )
            )
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.delete("/api/profiles/{slug}")
    async def delete_profile_delete(slug: str, request: Request) -> JSONResponse:
        if error := _write_access_error(request, settings):
            return _error(error, status=403)
        try:
            return _json(delete_profile_action(profile_slug=slug.strip()))
        except Exception as exc:
            return _error(str(exc), status=400)

    @app.get("/", response_model=None)
    async def root():
        index = _dist_dir() / "index.html"
        return FileResponse(index) if index.exists() else HTMLResponse(HTML)

    @app.get("/{path:path}", response_model=None)
    async def static_or_not_found(path: str):
        if path.startswith("api/"):
            return _error("not found", status=404)
        target = _static_target(path)
        if target is False:
            return _error("forbidden", status=403)
        if target is None:
            return _error("not found", status=404)
        return FileResponse(target)

    return app


def serve_viewer(settings: Settings, host: str, port: int) -> None:
    uvicorn.run(create_viewer_app(settings), host=host, port=port, log_level="warning", access_log=False)


def _dist_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent.parent / "frontend" / "dashboard" / "dist"


def _static_target(path: str) -> Path | None | bool:
    if any(part == ".." for part in Path(path).parts):
        return False
    dist = _dist_dir().resolve()
    target = (dist / path.lstrip("/")).resolve()
    try:
        target.relative_to(dist)
    except ValueError:
        return False
    if target.exists() and target.is_file():
        return target
    return None


async def _read_json(request: Request) -> dict:
    raw = await request.body()
    if not raw:
        return {}
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid json body") from exc
    if not isinstance(payload, dict):
        raise ValueError("json body must be an object")
    return payload


def _safe_json(loader, *, status: int = 200) -> JSONResponse:
    try:
        return _json(loader(), status=status)
    except Exception as exc:
        return _error(str(exc), status=500)


def _json(payload: object, *, status: int = 200) -> JSONResponse:
    return JSONResponse(content=_json_ready(payload), status_code=status)


def _error(message: str, *, status: int) -> JSONResponse:
    return JSONResponse(content={"error": message}, status_code=status)


def _write_access_error(request: Request, settings: Settings) -> str | None:
    expected_token = (settings.viewer_api_token or "").strip()
    provided_token = _bearer_token(request.headers.get("Authorization"))
    if expected_token:
        if provided_token is not None and compare_digest(provided_token, expected_token):
            return None
        return "write access requires Authorization: Bearer <VIEWER_API_TOKEN>"
    if not _client_is_loopback(request):
        return "write access is limited to loopback clients unless VIEWER_API_TOKEN is configured"
    if not _write_origin_is_allowed(request):
        return "write access origin must be loopback when VIEWER_API_TOKEN is not configured"
    return None


def _client_is_loopback(request: Request) -> bool:
    client = request.client.host if request.client else None
    return _is_loopback_host(client)


def _write_origin_is_allowed(request: Request) -> bool:
    origin = request.headers.get("Origin")
    if origin:
        return _origin_host_is_loopback(origin)
    referer = request.headers.get("Referer")
    if referer:
        return _origin_host_is_loopback(referer)
    return True


def _as_list(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else None
    raise ValueError("approval payload fields must be strings or arrays")


def _bearer_token(header_value: str | None) -> str | None:
    if not header_value:
        return None
    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "bearer":
        return None
    cleaned = token.strip()
    return cleaned or None


def _origin_host_is_loopback(origin: str) -> bool:
    return _is_loopback_host(urlparse(origin).hostname)


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    cleaned = host.strip().strip("[]").split("%", 1)[0].lower()
    if cleaned == "localhost":
        return True
    try:
        return ip_address(cleaned).is_loopback
    except ValueError:
        return False


def _json_ready(value: object):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
