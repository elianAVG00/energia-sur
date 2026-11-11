"""Guide embedding ingestion and semantic retrieval over PostgreSQL/pgvector."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Protocol

from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from app.assistant_limits import (
    EMBEDDING_DIMENSION,
    INGEST_LOCK_KEY,
    api_key,
    embedding_model,
    max_distance,
    top_k,
)
from app.db import get_engine
from app.guide_parser import (
    GUIDE_DOCUMENT_ID,
    PARSER_VERSION,
    GuideArticle,
    parse_guide,
)
from app.models import GuideChunk, GuideDocument


class AssistantUnavailable(RuntimeError):
    """The provider or the vector store is not available."""


class GuideVersionError(ValueError):
    """The guide version/content change is not allowed without an explicit force."""


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbedder:
    """OpenAI embeddings, created only when an API key is configured."""

    def __init__(self) -> None:
        key = api_key()
        if key is None:
            raise AssistantUnavailable("OpenAI API key is not configured")
        self._client = OpenAIEmbeddings(
            model=embedding_model(), api_key=SecretStr(key),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)


@dataclass(frozen=True)
class IngestResult:
    document_id: str
    version: str
    outcome: str
    article_count: int


@dataclass(frozen=True)
class GuideStatus:
    document_id: str
    current_version: str
    last_verified_at: date
    indexed_at: datetime
    article_count: int
    embedding_model: str
    embedding_dimension: int


@dataclass(frozen=True)
class RetrievedArticle:
    article_id: str
    section: str
    title: str
    content: str
    source_name: str
    source_urls: tuple[dict[str, str], ...]
    limitations: tuple[str, ...]
    information_type: str
    volatility: str
    last_verified_at: date
    distance: float
    document_id: str = ""
    source_type: str = ""


def _default_embedder() -> Embedder:
    return OpenAIEmbedder()


def _version_key(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts) if parts else (0,)


def _compare_versions(current: str, incoming: str) -> int:
    current_key, incoming_key = _version_key(current), _version_key(incoming)
    if incoming_key > current_key:
        return 1
    if incoming_key < current_key:
        return -1
    return 0


def _source_payload(article: GuideArticle) -> list[dict[str, str]]:
    return [
        {"source_name": ref.name, "url": ref.url}
        for ref in article.source_urls
    ]


def ingest_guide(
    path: Path | None = None,
    *,
    embedder: Embedder | None = None,
    force: bool = False,
) -> IngestResult:
    """Idempotently ingest the guide under an advisory lock and version guard."""
    parsed = parse_guide(path)
    client = embedder or _default_embedder()
    vectors = client.embed_documents(
        [article.embedding_text for article in parsed.articles],
    )
    if len(vectors) != len(parsed.articles):
        raise AssistantUnavailable("embedding count does not match article count")
    for vector in vectors:
        if len(vector) != EMBEDDING_DIMENSION:
            raise AssistantUnavailable("embedding dimension is not 1536")

    now = datetime.now(UTC)
    with Session(get_engine()) as db:
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": INGEST_LOCK_KEY})
        document = db.get(GuideDocument, GUIDE_DOCUMENT_ID)
        if document is not None:
            comparison = _compare_versions(document.current_version, parsed.version)
            if comparison < 0 and not force:
                return IngestResult(
                    parsed.document_id, parsed.version, "skipped_older", len(parsed.articles),
                )
            if comparison == 0:
                active = list(db.scalars(select(GuideChunk).where(
                    GuideChunk.document_id == parsed.document_id,
                    GuideChunk.version == parsed.version,
                    GuideChunk.is_active.is_(True),
                )))
                active_hashes = {row.article_id: row.content_sha256 for row in active}
                incoming_hashes = {
                    article.article_id: article.content_sha256
                    for article in parsed.articles
                }
                same_content = (
                    len(active) == len(parsed.articles)
                    and active_hashes == incoming_hashes
                )
                model_changed = document.embedding_model != embedding_model()
                if same_content and not model_changed:
                    if parsed.last_verified_at <= document.last_verified_at:
                        return IngestResult(
                            parsed.document_id, parsed.version, "unchanged",
                            len(parsed.articles),
                        )
                    db.execute(update(GuideChunk).where(
                        GuideChunk.document_id == parsed.document_id,
                        GuideChunk.version == parsed.version,
                    ).values(last_verified_at=parsed.last_verified_at))
                    document.last_verified_at = parsed.last_verified_at
                    document.indexed_at = now
                    db.commit()
                    return IngestResult(
                        parsed.document_id, parsed.version, "revalidated",
                        len(parsed.articles),
                    )
                if not force:
                    raise GuideVersionError(
                        "guide content changed without a newer version",
                    )

        if document is None:
            document = GuideDocument(
                document_id=parsed.document_id,
                current_version=parsed.version,
                last_verified_at=parsed.last_verified_at,
                indexed_at=now,
                source_name=parsed.source_name,
                source_type=parsed.source_type,
                embedding_model=embedding_model(),
                embedding_dimension=EMBEDDING_DIMENSION,
                parser_version=PARSER_VERSION,
            )
            db.add(document)
            db.flush()
        else:
            document.current_version = parsed.version
            document.last_verified_at = parsed.last_verified_at
            document.indexed_at = now
            document.source_name = parsed.source_name
            document.source_type = parsed.source_type
            document.embedding_model = embedding_model()
            document.embedding_dimension = EMBEDDING_DIMENSION
            document.parser_version = PARSER_VERSION
        db.execute(delete(GuideChunk).where(
            GuideChunk.document_id == parsed.document_id,
            GuideChunk.version == parsed.version,
        ))
        db.execute(update(GuideChunk).where(
            GuideChunk.document_id == parsed.document_id,
            GuideChunk.is_active.is_(True),
        ).values(is_active=False))
        for article, vector in zip(parsed.articles, vectors, strict=True):
            db.add(GuideChunk(
                document_id=parsed.document_id,
                version=parsed.version,
                last_verified_at=parsed.last_verified_at,
                section=article.section,
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                content_sha256=article.content_sha256,
                source_name=article.source_name,
                source_urls=_source_payload(article),
                limitations=list(article.limitations),
                information_type=article.information_type,
                volatility=article.volatility,
                source_type=article.source_type,
                chunk_index=article.chunk_index,
                embedding=vector,
                is_active=True,
                created_at=now,
            ))
        db.commit()
        return IngestResult(
            parsed.document_id, parsed.version, "indexed", len(parsed.articles),
        )


def guide_status() -> GuideStatus | None:
    with Session(get_engine()) as db:
        document = db.scalar(select(GuideDocument).where(
            GuideDocument.document_id == GUIDE_DOCUMENT_ID,
        ))
        if document is None:
            return None
        count = db.scalar(select(func.count()).select_from(GuideChunk).where(
            GuideChunk.document_id == document.document_id,
            GuideChunk.version == document.current_version,
            GuideChunk.is_active.is_(True),
        )) or 0
        return GuideStatus(
            document_id=document.document_id,
            current_version=document.current_version,
            last_verified_at=document.last_verified_at,
            indexed_at=document.indexed_at,
            article_count=int(count),
            embedding_model=document.embedding_model,
            embedding_dimension=document.embedding_dimension,
        )


def retrieve(
    query: str,
    *,
    limit: int | None = None,
    embedder: Embedder | None = None,
) -> list[RetrievedArticle]:
    """Return the current active-version articles closest to the query."""
    cleaned = query.strip()
    if not cleaned:
        return []
    client = embedder or _default_embedder()
    vector = client.embed_query(cleaned)
    if len(vector) != EMBEDDING_DIMENSION:
        raise AssistantUnavailable("query embedding dimension is not 1536")
    with Session(get_engine()) as db:
        document = db.scalar(select(GuideDocument).where(
            GuideDocument.document_id == GUIDE_DOCUMENT_ID,
        ))
        if document is None:
            return []
        distance = GuideChunk.embedding.cosine_distance(vector).label("distance")
        rows = db.execute(
            select(GuideChunk, distance).where(
                GuideChunk.document_id == document.document_id,
                GuideChunk.version == document.current_version,
                GuideChunk.is_active.is_(True),
            ).order_by(distance).limit(limit or top_k()),
        ).all()
        threshold = max_distance()
        return [
            RetrievedArticle(
                article_id=chunk.article_id,
                section=chunk.section,
                title=chunk.title,
                content=chunk.content,
                source_name=chunk.source_name,
                source_urls=tuple(chunk.source_urls),
                limitations=tuple(chunk.limitations),
                information_type=chunk.information_type,
                volatility=chunk.volatility,
                last_verified_at=chunk.last_verified_at,
                distance=float(row_distance),
                document_id=chunk.document_id,
                source_type=chunk.source_type,
            )
            for chunk, row_distance in rows
            if float(row_distance) <= threshold
        ]
