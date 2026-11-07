"""Approved local session primitives; no public account provisioning endpoint."""

import hashlib
import secrets

COOKIE_NAME = "energia_sur_session"
SESSION_SECONDS = 8 * 60 * 60
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
