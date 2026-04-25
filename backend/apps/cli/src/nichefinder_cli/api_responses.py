from fastapi.responses import JSONResponse


def safe_json(loader, *, status: int = 200) -> JSONResponse:
    try:
        return json_response(loader(), status=status)
    except Exception as exc:
        return error_response(str(exc), status=500)


def json_response(payload: object, *, status: int = 200) -> JSONResponse:
    return JSONResponse(content=_json_ready(payload), status_code=status)


def error_response(message: str, *, status: int) -> JSONResponse:
    return JSONResponse(content={"error": message}, status_code=status)


def _json_ready(value: object):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
