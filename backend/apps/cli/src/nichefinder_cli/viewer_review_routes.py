from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response, safe_json
from nichefinder_cli.api_security import read_json_body, write_access_error
from nichefinder_cli.viewer_api_models import NoiseApprovalRequest, TrainingApprovalRequest


def register_review_routes(
    app: FastAPI,
    settings: Settings,
    *,
    load_training_review: Callable[..., object],
    load_noise_review: Callable[..., object],
    load_final_review: Callable[..., object],
    approve_training_review: Callable[..., object],
    approve_noise_review: Callable[..., object],
) -> None:
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
