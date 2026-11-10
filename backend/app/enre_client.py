"""Read-only ENRE feed transport with an isolated legacy-TLS context.

The ENRE Domino server only negotiates legacy RSA-key-exchange ciphers, which
OpenSSL rejects at its default security level. The reduced level is applied to
this single origin only; certificate and hostname verification stay enabled.
"""

import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

import httpx

FEED_URL = "https://www.enre.gov.ar/paginacorte/js/data_EDS.js"
_ALLOWED_HOST = "www.enre.gov.ar"
_MAX_BYTES = 256 * 1024
_TIMEOUT_SECONDS = 20.0
_MAX_REDIRECTS = 3


class EnreError(Exception):
    """Base transport failure with a persisted outcome code."""

    code = "http_error"


class EnreTimeout(EnreError):
    code = "timeout"


class EnreTlsError(EnreError):
    code = "tls_error"


class EnrePayloadError(EnreError):
    code = "parse_error"


class EnreHttpError(EnreError):
    def __init__(self, status: int) -> None:
        super().__init__(f"ENRE returned HTTP {status}")
        self.status = status
        self.code = "http_error"


@dataclass(frozen=True)
class FetchedFeed:
    text: str
    last_modified: datetime | None
    status: int


def _context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.set_ciphers("DEFAULT@SECLEVEL=1")
    return context


def _parse_last_modified(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_tls_failure(error: BaseException) -> bool:
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, ssl.SSLError):
            return True
        current = current.__cause__ or current.__context__
    return False


def fetch_feed() -> FetchedFeed:
    """Fetch the feed once, following only same-host HTTPS redirects."""
    headers = {
        "Accept": "application/javascript, text/javascript, */*",
        "User-Agent": "EnergiaSur/1.0 (proyecto educativo)",
        "Cache-Control": "no-cache",
    }
    url = FEED_URL
    try:
        with httpx.Client(verify=_context(), timeout=_TIMEOUT_SECONDS,
                          follow_redirects=False, trust_env=False) as client:
            for _ in range(_MAX_REDIRECTS + 1):
                with client.stream("GET", url, headers=headers) as response:
                    if response.is_redirect:
                        target = urljoin(url, response.headers.get("location", ""))
                        parts = urlsplit(target)
                        try:
                            port = parts.port
                        except ValueError:
                            raise EnreHttpError(response.status_code) from None
                        if (parts.scheme != "https" or parts.hostname != _ALLOWED_HOST
                                or port not in (None, 443)):
                            raise EnreHttpError(response.status_code)
                        url = target
                        continue
                    if response.status_code != 200:
                        raise EnreHttpError(response.status_code)
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > _MAX_BYTES:
                            raise EnrePayloadError("ENRE payload exceeds the size limit")
                    return FetchedFeed(
                        text=body.decode("utf-8"),
                        last_modified=_parse_last_modified(
                            response.headers.get("last-modified"),
                        ),
                        status=response.status_code,
                    )
            raise EnreHttpError(310)
    except httpx.TimeoutException as error:
        raise EnreTimeout("ENRE request timed out") from error
    except httpx.HTTPError as error:
        if _is_tls_failure(error):
            raise EnreTlsError("ENRE TLS handshake failed") from error
        raise EnreHttpError(0) from error
    except UnicodeDecodeError as error:
        raise EnrePayloadError("ENRE payload is not valid UTF-8") from error
