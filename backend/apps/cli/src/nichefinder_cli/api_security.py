import json
from hmac import compare_digest
from ipaddress import ip_address
from urllib.parse import urlparse

from fastapi import Request

from nichefinder_core.settings import Settings


async def read_json_body(request: Request) -> dict:
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


def write_access_error(request: Request, settings: Settings) -> str | None:
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


def as_string_list(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else None
    raise ValueError("approval payload fields must be strings or arrays")


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
