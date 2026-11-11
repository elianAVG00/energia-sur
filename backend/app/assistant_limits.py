"""Server-side assistant configuration, limits and the in-process rate limiter."""

from __future__ import annotations

import os
import threading
import time

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
INGEST_LOCK_KEY = 0x43553033  # "CU03"


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def api_key() -> str | None:
    value = os.environ.get("OPENAI_API_KEY", "").strip()
    return value or None


def model() -> str:
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def embedding_model() -> str:
    return os.environ.get(
        "OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL,
    ).strip() or DEFAULT_EMBEDDING_MODEL


def message_max_chars() -> int:
    return _int("ASSISTANT_MESSAGE_MAX_CHARS", 2000, 1, 8000)


def max_output_tokens() -> int:
    return _int("ASSISTANT_MAX_OUTPUT_TOKENS", 600, 64, 2000)


def top_k() -> int:
    return _int("ASSISTANT_TOP_K", 4, 1, 12)


def guide_max_age_days() -> int:
    return _int("ASSISTANT_GUIDE_MAX_AGE_DAYS", 90, 1, 3650)


def rate_limit() -> int:
    return _int("ASSISTANT_RATE_LIMIT", 10, 1, 1000)


def rate_window_seconds() -> float:
    return _float("ASSISTANT_RATE_WINDOW_SECONDS", 60.0, 1.0, 3600.0)


def timeout_seconds() -> float:
    return _float("ASSISTANT_TIMEOUT_SECONDS", 30.0, 1.0, 120.0)


def first_byte_timeout() -> float:
    return _float("ASSISTANT_FIRST_BYTE_TIMEOUT", 10.0, 1.0, 120.0)


def max_distance() -> float:
    """Maximum cosine distance accepted as a relevant guide article (0-2)."""
    return _float("ASSISTANT_MAX_DISTANCE", 0.85, 0.0, 2.0)


def max_body_bytes() -> int:
    return _int("ASSISTANT_MAX_BODY_BYTES", 16384, 256, 1048576)


def max_concurrency() -> int:
    return _int("ASSISTANT_MAX_CONCURRENCY", 4, 1, 64)


def history_max_messages() -> int:
    return _int("ASSISTANT_HISTORY_MAX_MESSAGES", 10, 1, 50)


def history_max_chars() -> int:
    return _int("ASSISTANT_HISTORY_MAX_CHARS", 4000, 200, 20000)


def retention_days() -> int:
    """Documented retention for authenticated conversations; no auto-delete yet."""
    return _int("ASSISTANT_RETENTION_DAYS", 30, 1, 3650)


_active = 0
_active_lock = threading.Lock()


def acquire_slot() -> bool:
    """Reserve one concurrent assistant stream; False means the server is busy."""
    global _active
    with _active_lock:
        if _active >= max_concurrency():
            return False
        _active += 1
        return True


def release_slot() -> None:
    global _active
    with _active_lock:
        _active = max(0, _active - 1)


def reset_slots() -> None:
    global _active
    with _active_lock:
        _active = 0


class RateLimiter:
    """Bounded, pruned per-client limiter (single-instance assumption)."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        window = rate_window_seconds()
        limit = rate_limit()
        with self._lock:
            hits = [hit for hit in self._hits.get(client, []) if now - hit < window]
            if len(hits) >= limit:
                self._hits[client] = hits
                return False
            hits.append(now)
            if len(self._hits) > 1024:
                expired = [
                    key for key, values in self._hits.items()
                    if not values or now - values[-1] >= window
                ]
                for key in expired:
                    self._hits.pop(key, None)
            self._hits[client] = hits
            return True


limiter = RateLimiter()
