import json
from datetime import UTC, datetime, timedelta
from hashlib import sha1
from pathlib import Path
from typing import Any

from nichefinder_core.settings import Settings


def load_json_cache(
    settings: Settings,
    *,
    namespace: str,
    key: str,
    max_age_hours: int,
) -> dict[str, Any] | None:
    path = _cache_path(settings, namespace=namespace, key=key)
    if not path.exists():
        return None
    if max_age_hours > 0:
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if modified_at < cutoff:
            return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_json_cache(
    settings: Settings,
    *,
    namespace: str,
    key: str,
    payload: dict[str, Any],
) -> Path:
    path = _cache_path(settings, namespace=namespace, key=key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    return path


def _cache_path(settings: Settings, *, namespace: str, key: str) -> Path:
    digest = sha1(key.encode("utf-8")).hexdigest()
    return settings.resolved_cache_dir / namespace / f"{digest}.json"
