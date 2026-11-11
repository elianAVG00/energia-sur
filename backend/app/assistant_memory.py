"""Owner-scoped persistent assistant conversations and bounded history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.assistant_limits import history_max_chars, history_max_messages
from app.db import get_engine
from app.models import AssistantConversation, AssistantMessage


@dataclass(frozen=True)
class ConversationSummary:
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


@dataclass(frozen=True)
class StoredMessage:
    id: str
    role: str
    content: str
    sources: list[dict[str, str]]
    created_at: datetime


def _now() -> datetime:
    return datetime.now(UTC)


def resolve_conversation(
    account_id: str, conversation_id: str | None,
) -> tuple[str, str]:
    """Return an owned conversation id and scope; never attach a foreign id."""
    with Session(get_engine()) as db:
        if conversation_id is not None:
            owned = db.scalar(select(AssistantConversation).where(
                AssistantConversation.id == conversation_id,
                AssistantConversation.account_id == account_id,
            ))
            if owned is not None:
                return owned.id, "persistent"
        conversation = AssistantConversation(
            id=str(uuid4()),
            account_id=account_id,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(conversation)
        db.commit()
        return conversation.id, "persistent"


def append_message(
    account_id: str,
    conversation_id: str,
    role: str,
    content: str,
    sources: list[dict[str, str]],
) -> bool:
    with Session(get_engine()) as db:
        conversation = db.scalar(select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.account_id == account_id,
        ))
        if conversation is None:
            return False
        db.add(AssistantMessage(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=list(sources),
            created_at=_now(),
        ))
        conversation.updated_at = _now()
        db.commit()
        return True


def load_history(
    account_id: str, conversation_id: str, limit: int | None = None,
) -> list[dict[str, str]]:
    """Return the newest bounded turns for the authorized conversation only."""
    with Session(get_engine()) as db:
        owned = db.scalar(select(AssistantConversation.id).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.account_id == account_id,
        ))
        if owned is None:
            return []
        rows = list(db.scalars(select(AssistantMessage).where(
            AssistantMessage.conversation_id == conversation_id,
        ).order_by(
            AssistantMessage.created_at.desc(), AssistantMessage.id.desc(),
        ).limit(limit or history_max_messages())))
        kept: list[dict[str, str]] = []
        total = 0
        cap = history_max_chars()
        for row in rows:  # newest first, so the character cap keeps recent turns
            if row.role not in {"user", "assistant"}:
                continue
            if total + len(row.content) > cap:
                break
            kept.append({"role": row.role, "content": row.content})
            total += len(row.content)
        kept.reverse()
        return kept


def list_conversations(account_id: str) -> list[ConversationSummary]:
    with Session(get_engine()) as db:
        counts = dict(db.execute(
            select(AssistantMessage.conversation_id, func.count())
            .join(
                AssistantConversation,
                AssistantConversation.id == AssistantMessage.conversation_id,
            )
            .where(AssistantConversation.account_id == account_id)
            .group_by(AssistantMessage.conversation_id),
        ).all())
        rows = db.scalars(select(AssistantConversation).where(
            AssistantConversation.account_id == account_id,
        ).order_by(AssistantConversation.updated_at.desc()))
        return [
            ConversationSummary(
                id=row.id,
                created_at=row.created_at,
                updated_at=row.updated_at,
                message_count=int(counts.get(row.id, 0)),
            )
            for row in rows
            if int(counts.get(row.id, 0)) > 0
        ]


def get_messages(account_id: str, conversation_id: str) -> list[StoredMessage] | None:
    """Return the owned conversation messages, or None for unknown/foreign ids."""
    with Session(get_engine()) as db:
        owned = db.scalar(select(AssistantConversation.id).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.account_id == account_id,
        ))
        if owned is None:
            return None
        rows = db.scalars(select(AssistantMessage).where(
            AssistantMessage.conversation_id == conversation_id,
        ).order_by(AssistantMessage.created_at, AssistantMessage.id))
        return [
            StoredMessage(
                id=row.id,
                role=row.role,
                content=row.content,
                sources=list(row.sources),
                created_at=row.created_at,
            )
            for row in rows
        ]


def delete_conversation(account_id: str, conversation_id: str) -> bool:
    with Session(get_engine()) as db:
        conversation = db.scalar(select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.account_id == account_id,
        ))
        if conversation is None:
            return False
        db.delete(conversation)
        db.commit()
        return True
