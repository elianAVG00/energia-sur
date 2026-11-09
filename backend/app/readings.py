"""CU05 exact-value and idempotency primitives, without transport or storage."""

import hashlib
import re
from datetime import UTC, datetime

MAX_READING_DIGITS = 131_072
_READING_TIME = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z",
    re.ASCII,
)


def canonical_kwh(value: str) -> str:
    """Validate decimal input without a floating-point or integer conversion."""
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_READING_DIGITS:
        raise ValueError("Invalid reading value.")
    if any(char < "0" or char > "9" for char in value):
        raise ValueError("Invalid reading value.")
    return value.lstrip("0") or "0"


def creation_fingerprint(recorded_at: str, value_kwh: str, photo: bytes | None) -> str:
    """Hash length-delimited validated inputs, retaining exact input-string identity."""
    canonical_kwh(value_kwh)
    photo_digest = hashlib.sha256(photo).digest() if photo is not None else b""
    try:
        timestamp = recorded_at.encode("ascii")
    except UnicodeError:
        raise ValueError("Invalid reading timestamp.") from None
    fields = (timestamp, value_kwh.encode("ascii"), photo_digest)
    digest = hashlib.sha256()
    for field in fields:
        digest.update(len(field).to_bytes(8, "big"))
        digest.update(field)
    return digest.hexdigest()


def reading_instant(value: str, *, now: datetime) -> datetime:
    """Validate an offset-aware second-resolution reading against a trusted clock."""
    if not isinstance(value, str) or _READING_TIME.fullmatch(value) is None:
        raise ValueError("Invalid reading timestamp.")
    if not value.endswith("Z") and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError("Invalid reading timestamp.")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Clock must be timezone-aware.")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, OverflowError):
        raise ValueError("Invalid reading timestamp.") from None
    if instant > now.astimezone(UTC):
        raise ValueError("Reading timestamp is in the future.")
    return instant


def is_decreasing(value: str, previous: str) -> bool:
    """Compare arbitrary-size decimal readings without converting to integers."""
    current = canonical_kwh(value)
    earlier = canonical_kwh(previous)
    return (len(current), current) < (len(earlier), earlier)
