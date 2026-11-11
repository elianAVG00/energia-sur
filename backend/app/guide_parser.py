"""Deterministic parser for the approved Edesur guide (article-level units)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

PARSER_VERSION = "cu03-guide-parser-1"
GUIDE_DOCUMENT_ID = "energia-sur-kb-edesur-001"
EMBEDDING_MODEL = "text-embedding-3-small"
EXPECTED_ARTICLE_COUNT = 53
EXPECTED_SECTION_NUMBERS = frozenset(range(1, 10))
ARTICLE_RE = re.compile(
    r"^### ((?:CA|PA|CO|TS|EL|EE|CR|TR|LI)-\d{2}) \u2014 (.+)$",
)
SECTION_RE = re.compile(r"^## (\d+)\. (.+)$")
SOURCE_RE = re.compile(r"^\*\*(Fuente[^*]*):\*\*\s*(\S+)\s*$", re.MULTILINE)
INFO_TYPE_RE = re.compile(r"^\*\*Tipo de informaci\u00f3n:\*\*\s*(.+)$", re.MULTILINE)
REQUIRED_FRONTMATTER = (
    "document_id", "version", "last_verified_at", "title",
    "source_organizations", "source_type",
)
GUIDE_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "guia-oficial-edesur.md"
ALLOWED_HOSTS = (
    "edesur.com.ar", "ov.edesur.com.ar", "argentina.gob.ar", "www.enre.gov.ar",
)
LIMITATION_RE = re.compile(
    r"\*\*(Informaci\u00f3n no publicada|L\u00edmite|Limitaci\u00f3n|No asumir|"
    r"Advertencia(?: esencial)?|Importante(?: para Energ\u00eda Sur)?|"
    r"Aclaraci\u00f3n(?: para Energ\u00eda Sur)?):\*\*",
)
_MARKER_LABELS = {
    "Informaci\u00f3n no publicada": "informacion_no_publicada",
    "L\u00edmite": "limite",
    "Limitaci\u00f3n": "limitacion",
    "No asumir": "no_asumir",
    "Advertencia esencial": "advertencia",
    "Advertencia": "advertencia",
    "Importante para Energ\u00eda Sur": "importante",
    "Importante": "importante",
    "Aclaraci\u00f3n para Energ\u00eda Sur": "aclaracion",
    "Aclaraci\u00f3n": "aclaracion",
}
_VOLATILE = (
    "variable", "sujeto a cambio", "sujetos a cambio", "comercial", "puede variar",
)
_REVALIDATE = (
    "revalidaci\u00f3n", "sensible a regulaci\u00f3n", "sujeto a evaluaci\u00f3n",
    "prioridad", "no contiene disponibilidad actual",
)


class GuideParseError(ValueError):
    """The guide is missing, malformed or incomplete."""


@dataclass(frozen=True)
class SourceRef:
    name: str
    url: str


@dataclass(frozen=True)
class GuideArticle:
    document_id: str
    version: str
    last_verified_at: date
    section: str
    article_id: str
    title: str
    content: str
    content_sha256: str
    source_name: str
    source_urls: tuple[SourceRef, ...]
    limitations: tuple[str, ...]
    information_type: str
    volatility: str
    source_type: str
    chunk_index: int

    @property
    def embedding_text(self) -> str:
        return f"{self.section}\n{self.title}\n{self.content}"


@dataclass(frozen=True)
class ParsedGuide:
    document_id: str
    version: str
    last_verified_at: date
    title: str
    source_type: str
    source_name: str
    articles: tuple[GuideArticle, ...]


def _host_matches(host: str, allowed: str) -> bool:
    return host == allowed or host.endswith("." + allowed)


def is_official_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    return any(_host_matches(parsed.hostname, allowed) for allowed in ALLOWED_HOSTS)


def _source_name(url: str) -> str:
    host = urlparse(url).hostname or ""
    if _host_matches(host, "edesur.com.ar"):
        return "Edesur"
    if _host_matches(host, "argentina.gob.ar"):
        return "Argentina.gob.ar / ENRE"
    if _host_matches(host, "enre.gov.ar"):
        return "ENRE"
    return host


def _normalize_content(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _volatility(information_type: str) -> str:
    lowered = information_type.lower()
    if any(token in lowered for token in _VOLATILE):
        return "variable"
    if any(token in lowered for token in _REVALIDATE):
        return "revalidate"
    if (
        re.search(r"\bestable\b", lowered)
        and "inestable" not in lowered
        and "no estable" not in lowered
    ):
        return "stable"
    return "revalidate"


def _limitations(body: str) -> tuple[str, ...]:
    found: list[str] = []
    for match in LIMITATION_RE.finditer(body):
        label = _MARKER_LABELS.get(match.group(1))
        if label and label not in found:
            found.append(label)
    lowered = body.lower()
    if (
        "no detalla" in lowered or "no proporciona un listado exhaustivo" in lowered
    ) and "documentacion_parcial" not in found:
        found.append("documentacion_parcial")
    return tuple(found)


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise GuideParseError("guide frontmatter is missing")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise GuideParseError("guide frontmatter is not closed")
    try:
        raw = yaml.safe_load(text[4:end])
    except yaml.YAMLError as error:
        raise GuideParseError("guide frontmatter is invalid") from error
    if not isinstance(raw, dict):
        raise GuideParseError("guide frontmatter is not an object")
    for key in REQUIRED_FRONTMATTER:
        if key not in raw:
            raise GuideParseError(f"guide frontmatter is missing {key}")
    return raw, text[end + 5:]


def parse_guide(path: Path | None = None) -> ParsedGuide:
    source = path or GUIDE_PATH
    try:
        text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    except OSError as error:
        raise GuideParseError("guide cannot be read") from error
    meta, body = _frontmatter(text)

    document_id = meta["document_id"]
    version = meta["version"]
    title = meta["title"]
    source_type = meta["source_type"]
    last_verified_at = meta["last_verified_at"]
    organizations = meta["source_organizations"]
    if not all(isinstance(value, str) and value.strip() for value in (
        document_id, version, title, source_type, last_verified_at,
    )):
        raise GuideParseError("guide frontmatter has invalid scalar values")
    if not isinstance(organizations, list) or not organizations:
        raise GuideParseError("guide frontmatter has no source_organizations")
    if str(document_id) != GUIDE_DOCUMENT_ID:
        raise GuideParseError("unexpected guide document_id")
    try:
        verified = date.fromisoformat(str(last_verified_at))
    except ValueError as error:
        raise GuideParseError("guide last_verified_at is invalid") from error
    document_name = " / ".join(str(value) for value in organizations)

    articles: list[GuideArticle] = []
    section: str | None = None
    section_numbers: set[int] = set()
    current_id: str | None = None
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        if current_id is None:
            return
        body_text = _normalize_content("\n".join(current_lines))
        info_match = INFO_TYPE_RE.search(body_text)
        information_type = info_match.group(1).strip() if info_match else ""
        refs: list[SourceRef] = []
        seen: set[str] = set()
        dropped = False
        for match in SOURCE_RE.finditer(body_text):
            url = match.group(2).strip()
            if not is_official_url(url):
                dropped = True
                continue
            if url in seen:
                continue
            seen.add(url)
            refs.append(SourceRef(name=_source_name(url), url=url))
        limitations = _limitations(body_text)
        if dropped and "fuente_no_oficial" not in limitations:
            limitations = (*limitations, "fuente_no_oficial")
        volatility = _volatility(information_type)
        canonical = "\n".join([
            PARSER_VERSION, str(source_type), current_title.strip(), body_text,
            information_type, volatility,
            "|".join(sorted(ref.url for ref in refs)),
            "|".join(sorted(limitations)),
        ])
        articles.append(GuideArticle(
            document_id=str(document_id),
            version=str(version),
            last_verified_at=verified,
            section=section or "",
            article_id=current_id,
            title=current_title.strip(),
            content=body_text,
            content_sha256=_hash(canonical),
            source_name=refs[0].name if refs else document_name,
            source_urls=tuple(refs),
            limitations=limitations,
            information_type=information_type,
            volatility=volatility,
            source_type=str(source_type),
            chunk_index=len(articles),
        ))

    for line in body.split("\n"):
        section_match = SECTION_RE.match(line)
        if section_match:
            flush()
            current_id = None
            current_title = ""
            current_lines = []
            section = f"{section_match.group(1)}. {section_match.group(2).strip()}"
            section_numbers.add(int(section_match.group(1)))
            continue
        article_match = ARTICLE_RE.match(line)
        if article_match:
            flush()
            current_id = article_match.group(1)
            current_title = article_match.group(2)
            current_lines = []
            continue
        if line.startswith("### "):
            raise GuideParseError(f"malformed article heading: {line[:40]}")
        if current_id is not None:
            current_lines.append(line)
    flush()

    if not EXPECTED_SECTION_NUMBERS.issubset(section_numbers):
        raise GuideParseError("guide content sections 1-9 are incomplete")
    if len(articles) != EXPECTED_ARTICLE_COUNT:
        raise GuideParseError(
            f"guide article count is {len(articles)}, expected {EXPECTED_ARTICLE_COUNT}",
        )
    ids = [article.article_id for article in articles]
    if len(set(ids)) != len(ids):
        raise GuideParseError("guide article IDs are duplicated")

    return ParsedGuide(
        document_id=str(document_id),
        version=str(version),
        last_verified_at=verified,
        title=str(title),
        source_type=str(source_type),
        source_name=document_name,
        articles=tuple(articles),
    )
