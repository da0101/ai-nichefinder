from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response
from nichefinder_cli.api_security import as_string_list, read_json_body, write_access_error


def register_job_routes(
    app: FastAPI,
    settings: Settings,
    *,
    run_validate_free_action: Callable[..., object],
    list_jobs: Callable[[Settings], object],
    get_job: Callable[[str, Settings], object | None],
    submit_job: Callable[[str, dict, Settings], object],
) -> None:
    @app.get("/api/jobs")
    async def jobs() -> JSONResponse:
        return json_response(list_jobs(settings))

    @app.get("/api/jobs/{job_id}")
    async def job(job_id: str) -> JSONResponse:
        payload = get_job(job_id, settings)
        if payload is None:
            return error_response("job not found", status=404)
        return json_response(payload)

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
