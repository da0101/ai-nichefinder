from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from nichefinder_cli.api_responses import error_response
from nichefinder_cli.viewer_html import HTML


def register_static_routes(app: FastAPI) -> None:
    @app.get("/", response_model=None)
    async def root():
        index = _dist_dir() / "index.html"
        return FileResponse(index) if index.exists() else HTMLResponse(HTML)

    @app.get("/{path:path}", response_model=None)
    async def static_or_not_found(path: str):
        if path.startswith("api/"):
            return error_response("not found", status=404)
        target = _static_target(path)
        if target is False:
            return error_response("forbidden", status=403)
        if target is None:
            return error_response("not found", status=404)
        return FileResponse(target)


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
