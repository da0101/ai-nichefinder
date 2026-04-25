from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nichefinder_core.settings import Settings

from nichefinder_cli.api_responses import error_response, json_response, safe_json
from nichefinder_cli.api_security import read_json_body, write_access_error


def register_profile_routes(
    app: FastAPI,
    settings: Settings,
    *,
    load_profiles: Callable[[], object],
    switch_active_profile: Callable[[str | None], object],
    load_profile_config: Callable[..., object],
    save_profile_config_action: Callable[..., object],
    create_profile_action: Callable[..., object],
    delete_profile_action: Callable[..., object],
) -> None:
    @app.get("/api/profiles")
    async def profiles() -> JSONResponse:
        return safe_json(load_profiles)

    @app.get("/api/profile-config")
    async def profile_config(profile: str | None = None) -> JSONResponse:
        return safe_json(lambda: load_profile_config(profile_slug=profile))

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

    @app.delete("/api/profiles/{slug}")
    async def delete_profile_delete(slug: str, request: Request) -> JSONResponse:
        if error := write_access_error(request, settings):
            return error_response(error, status=403)
        try:
            return json_response(delete_profile_action(profile_slug=slug.strip()))
        except Exception as exc:
            return error_response(str(exc), status=400)
