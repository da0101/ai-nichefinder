from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response
from nichefinder_cli.api_security import read_json_body, write_access_error


def register_article_routes(
    app: FastAPI,
    settings: Settings,
    *,
    approve_article_action: Callable[..., object],
    publish_article_action: Callable[..., object],
) -> None:
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
