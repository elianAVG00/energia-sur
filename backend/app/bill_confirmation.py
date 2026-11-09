"""Integrity-protected, payload-bound CU06 overlap confirmation primitives.

The caller supplies a secret and must recompute the snapshot while holding the
meter lock. These functions do not authorize access or perform persistence.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(frozen=True, slots=True)
class Overlap:
    bill_id: str
    version: int
    start: date
    end: date


@dataclass(frozen=True, slots=True)
class Confirmation:
    account_id: str
    meter_id: str
    operation: Literal["create", "edit"]
    bill_id: str | None
    version: int | None
    start: date
    end: date
    value_kwh: str
    amount_ars: str | None
    file_action: Literal["create", "replace", "keep"]
    file_digest: str | None
    overlaps: tuple[Overlap, ...]


def file_digest(data: bytes) -> str:
    """Fingerprint decoded bytes rather than their transport encoding."""
    return hashlib.sha256(data).hexdigest()


def confirmation_token(secret: bytes, confirmation: Confirmation) -> str:
    """Sign canonical fields and a deterministically ordered overlap snapshot.

    Values must already be validated and decimals canonicalized by the caller.
    JSON arrays encode boundaries and null values unambiguously.
    """
    if len(secret) < 32:
        raise ValueError("Confirmation secret is too short.")
    if confirmation.file_action == "keep":
        if confirmation.file_digest is not None:
            raise ValueError("Keep cannot include file bytes.")
    elif (confirmation.file_digest is None or len(confirmation.file_digest) != 64
          or any(c not in "0123456789abcdef" for c in confirmation.file_digest)):
        raise ValueError("Invalid file digest.")
    snapshot = sorted(
        (item.bill_id, item.version, item.start.isoformat(), item.end.isoformat())
        for item in confirmation.overlaps
    )
    payload = [
        "cu06-overlap-v1", confirmation.account_id, confirmation.meter_id,
        confirmation.operation, confirmation.bill_id, confirmation.version,
        confirmation.start.isoformat(), confirmation.end.isoformat(),
        confirmation.value_kwh, confirmation.amount_ars, confirmation.file_action,
        confirmation.file_digest, snapshot,
    ]
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hmac.new(secret, encoded, hashlib.sha256).hexdigest()


def matches_confirmation(secret: bytes, confirmation: Confirmation, supplied: str) -> bool:
    """Compare a token against a freshly reconstructed, locked snapshot."""
    if len(supplied) != 64 or not supplied.isascii():
        return False
    return hmac.compare_digest(confirmation_token(secret, confirmation), supplied)
