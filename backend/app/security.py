"""Approved local session, password and registration security primitives."""

import hashlib
import os
import secrets
import threading
import time
from math import ceil

from fastapi import HTTPException, Request

COOKIE_NAME = "energia_sur_session"
SESSION_SECONDS = 8 * 60 * 60
REGISTRATION_LIMIT = 5
REGISTRATION_WINDOW_SECONDS = 15 * 60
_PREFIX = "scrypt$131072$8$1$"
DUMMY_HASH = _PREFIX + "00" * 16 + "$" + "00" * 64


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=131072, r=8, p=1,
        dklen=64, maxmem=256 * 1024 * 1024,
    )
    return _PREFIX + salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    if not encoded.startswith(_PREFIX):
        return False
    try:
        salt_text, digest_text = encoded[len(_PREFIX):].split("$")
        salt, expected = bytes.fromhex(salt_text), bytes.fromhex(digest_text)
        if len(salt) != 16 or len(expected) != 64:
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=131072, r=8, p=1,
            dklen=64, maxmem=256 * 1024 * 1024,
        )
        return secrets.compare_digest(actual, expected)
    except ValueError:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def matches_csrf(supplied: str, expected: str) -> bool:
    return supplied.isascii() and secrets.compare_digest(supplied, expected)


def origin(request: Request) -> None:
    """Reject a request whose exact Origin is not in the configured allowlist."""
    allowed = os.environ.get(
        "APP_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if request.headers.get("origin", "") not in [
        value.strip() for value in allowed if value.strip()
    ]:
        raise HTTPException(403, "El origen de la solicitud no est\u00e1 autorizado.")


class RegistrationRateLimiter:
    """Limit peers in-process, capped at 1024 keys.

    When the cap is full of unexpired peers, a new peer is rejected for one full
    window instead of growing memory state. The key is the ASGI socket peer only.
    """

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        """Clear limiter state for isolated tests."""
        with self._lock:
            self._hits.clear()

    def retry_after(self, client: str) -> int | None:
        """Record an allowed attempt or return seconds until the oldest hit expires."""
        current = time.monotonic()
        with self._lock:
            hits = [
                hit for hit in self._hits.get(client, [])
                if current - hit < REGISTRATION_WINDOW_SECONDS
            ]
            if len(hits) >= REGISTRATION_LIMIT:
                self._hits[client] = hits
                return max(1, ceil(REGISTRATION_WINDOW_SECONDS - (current - hits[0])))
            hits.append(current)
            if len(self._hits) >= 1024 and client not in self._hits:
                expired = [
                    key for key, values in self._hits.items()
                    if not values or current - values[-1] >= REGISTRATION_WINDOW_SECONDS
                ]
                for key in expired:
                    self._hits.pop(key, None)
                if len(self._hits) >= 1024:
                    return REGISTRATION_WINDOW_SECONDS
            self._hits[client] = hits
            return None


registration_limiter = RegistrationRateLimiter()
