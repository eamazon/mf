"""Simple file-based cache to avoid hammering free APIs."""

import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "mf_recommender"
DEFAULT_TTL = 24 * 3600  # 24 hours


def _cache_path(key: str) -> Path:
    hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{hashed}.json"


def get(key: str, ttl: int = DEFAULT_TTL):
    """Return cached value if it exists and hasn't expired, else None."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if time.time() - data["ts"] > ttl:
            path.unlink(missing_ok=True)
            return None
        return data["value"]
    except (json.JSONDecodeError, KeyError):
        path.unlink(missing_ok=True)
        return None


def put(key: str, value):
    """Store a value in the cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    path.write_text(json.dumps({"ts": time.time(), "value": value}))


def clear():
    """Remove all cached files."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            f.unlink(missing_ok=True)
