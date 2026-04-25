import uvicorn
from fastapi import FastAPI

from nichefinder_core.settings import Settings

from nichefinder_cli.viewer_api_routes import register_api_routes
from nichefinder_cli.viewer_static_routes import register_static_routes


def create_viewer_app(settings: Settings) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    register_api_routes(app, settings)
    register_static_routes(app)
    return app


def serve_viewer(settings: Settings, host: str, port: int) -> None:
    uvicorn.run(create_viewer_app(settings), host=host, port=port, log_level="warning", access_log=False)
