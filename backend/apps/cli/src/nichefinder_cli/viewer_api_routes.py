from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response, safe_json
from nichefinder_cli.api_security import as_string_list, read_json_body, write_access_error
from nichefinder_cli.services.article_service import approve_article_action, publish_article_action
from nichefinder_cli.services.profile_service import (
    create_profile_action,
    delete_profile_action,
    load_profile_config,
    save_profile_config_action,
)
from nichefinder_cli.services.research_service import run_validate_free_action
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


def register_api_routes(app: FastAPI, settings: Settings) -> None:
    @app.get("/api/dashboard")
    async def dashboard() -> JSONResponse:
        return safe_json(lambda: load_dashboard(settings))

    @app.get("/api/keywords")
    async def keywords() -> JSONResponse:
        return safe_json(lambda: load_keywords(settings))

    @app.get("/api/keyword-clusters")
    async def keyword_clusters() -> JSONResponse:
        return safe_json(lambda: load_keyword_clusters(settings))

    @app.get("/api/keywords/{keyword_id}")
    async def keyword_detail(keyword_id: str) -> JSONResponse:
        try:
            detail = load_keyword_detail(settings, keyword_id)
        except Exception as exc:
            return error_response(str(exc), status=500)
        if detail is None:
            return error_response("keyword not found", status=404)
        return json_response(detail)

    @app.get("/api/profiles")
    async def profiles() -> JSONResponse:
        return safe_json(load_profiles)

    @app.get("/api/training-review")
    async def training_review(profile: str | None = None, min_runs: int = 2, limit: int = 18) -> JSONResponse:
        return safe_json(lambda: load_training_review(profile_slug=profile, min_runs=min_runs, limit=limit))

    @app.get("/api/noise-review")
    async def noise_review(profile: str | None = None, min_runs: int = 2, limit: int = 12) -> JSONResponse:
        return safe_json(lambda: load_noise_review(profile_slug=profile, min_runs=min_runs, limit=limit))

    @app.get("/api/final-review")
    async def final_review(profiles: str | None = None, min_runs: int = 2, limit: int = 9) -> JSONResponse:
        selected = [item for item in (profiles or "").split(",") if item]
        return safe_json(lambda: load_final_review(profiles=selected or None, min_runs=min_runs, limit=limit))

    @app.get("/api/profile-config")
    async def profile_config(profile: str | None = None) -> JSONResponse:
        return safe_json(lambda: load_profile_config(profile_slug=profile))

    @app.get("/api/status")
    async def status() -> JSONResponse:
        return json_response({"status": "ok", "api": "nichefinder-local", "mode": "local"})

    @app.get("/api/status/detail")
    async def status_detail() -> JSONResponse:
        return safe_json(lambda: load_status(settings))

    @app.get("/api/articles")
    async def articles() -> JSONResponse:
        return safe_json(lambda: load_articles(settings))

    @app.get("/api/report")
    async def report() -> JSONResponse:
        return safe_json(lambda: load_report(settings))

    @app.get("/api/budget")
    async def budget() -> JSONResponse:
        return safe_json(lambda: load_budget(settings))

    @app.get("/api/jobs")
    async def jobs() -> JSONResponse:
        return json_response(list_jobs(settings))

    @app.get("/api/jobs/{job_id}")
    async def job(job_id: str) -> JSONResponse:
        payload = get_job(job_id, settings)
        if payload is None:
            return error_response("job not found", status=404)
        return json_response(payload)

    @app.post("/api/profiles/active")
    async def switch_profile(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            return json_response(switch_active_profile(payload.get("profile")))
        except ValueError as exc:
            return error_response(str(exc), status=404)
        except Exception as exc:
            return error_response(str(exc), status=500)

    @app.post("/api/training-approve")
    async def training_approve(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            approved = TrainingApprovalRequest.model_validate(payload)
            return json_response(
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
            return error_response(str(exc), status=400)

    @app.post("/api/noise-approve")
    async def noise_approve(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            approved = NoiseApprovalRequest.model_validate(payload)
            return json_response(
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
            return error_response(str(exc), status=400)

    @app.post("/api/profiles")
    async def create_profile(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            return json_response(
                create_profile_action(
                    slug=str(payload.get("slug", "")).strip(),
                    from_current=bool(payload.get("from_current", False)),
                    use=bool(payload.get("use", False)),
                    payload=payload.get("site_config"),
                ),
                status=201,
            )
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.post("/api/profile-config")
    async def save_profile_config(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            return json_response(
                save_profile_config_action(
                    profile_slug=payload.get("profile"),
                    payload=payload.get("site_config", {}),
                )
            )
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.post("/api/profiles/delete")
    async def delete_profile_post(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            return json_response(delete_profile_action(profile_slug=str(payload.get("profile", "")).strip()))
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.post("/api/validate-free")
    async def validate_free(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            return json_response(
                run_validate_free_action(
                    profile_slug=payload.get("profile"),
                    keyword=str(payload.get("keyword", "")).strip(),
                    sources=tuple(as_string_list(payload.get("sources")) or ["ddgs", "bing", "yahoo"]),
                )
            )
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.post("/api/jobs")
    async def create_job(request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            params = payload.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            return json_response(submit_job(str(payload.get("action", "")).strip(), params, settings), status=202)
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.post("/api/articles/{article_id}/{article_action}")
    async def mutate_article(article_id: str, article_action: str, request: Request) -> JSONResponse:
        if article_action not in {"approve", "publish"}:
            return error_response("not found", status=404)
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            payload = await read_json_body(request)
            if article_action == "approve":
                return json_response(
                    approve_article_action(
                        profile_slug=payload.get("profile"),
                        article_id=article_id,
                        settings_override=settings,
                    )
                )
            return json_response(
                publish_article_action(
                    profile_slug=payload.get("profile"),
                    article_id=article_id,
                    url=str(payload.get("url", "")).strip(),
                    settings_override=settings,
                )
            )
        except Exception as exc:
            return error_response(str(exc), status=400)

    @app.delete("/api/profiles/{slug}")
    async def delete_profile_delete(slug: str, request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            return json_response(delete_profile_action(profile_slug=slug.strip()))
        except Exception as exc:
            return error_response(str(exc), status=400)
