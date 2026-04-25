from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response, safe_json


def register_read_routes(
    app: FastAPI,
    settings: Settings,
    *,
    load_dashboard: Callable[[Settings], object],
    load_keywords: Callable[[Settings], object],
    load_keyword_clusters: Callable[[Settings], object],
    load_keyword_detail: Callable[[Settings, str], object | None],
    load_status: Callable[[Settings], object],
    load_articles: Callable[[Settings], object],
    load_report: Callable[[Settings], object],
    load_budget: Callable[[Settings], object],
) -> None:
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
