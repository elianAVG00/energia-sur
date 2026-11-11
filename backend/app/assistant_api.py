"""Public CU03 assistant SSE endpoint, persistence and owner-scoped history."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app import assistant_memory as memory
from app import guide_store
from app.api import Auth, OptionalAuth, Writer, no_cache
from app.assistant import (
    FALLBACK_MESSAGE,
    REFUSAL_MESSAGE,
    DynamicOutcome,
    dynamic_sources,
    sources,
    stream_answer,
)
from app.assistant_limits import (
    acquire_slot,
    first_byte_timeout,
    history_max_chars,
    history_max_messages,
    limiter,
    message_max_chars,
    rate_window_seconds,
    release_slot,
    timeout_seconds,
)
from app.assistant_tools import (
    Plan,
    lookup_current_outages,
    lookup_scheduled_works,
    plan_question,
)
from app.guide_store import AssistantUnavailable, RetrievedArticle
from app.security import origin

_LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(no_cache)])

_INVALID = "Revis\u00e1 los datos ingresados."
_BUSY = "El asistente est\u00e1 ocupado. Intent\u00e1 nuevamente en unos segundos."


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=2000)


class ChatInput(BaseModel):
    message: str
    conversation_id: str | None = Field(default=None, max_length=36)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=10)


class ConversationOut(BaseModel):
    id: str
    created_at: str
    updated_at: str
    message_count: int


class StoredMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list[dict[str, str]]
    created_at: str


class ConversationMessagesOut(BaseModel):
    conversation_id: str
    messages: list[StoredMessageOut]


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _client(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _retrieve(message: str) -> list[RetrievedArticle]:
    return guide_store.retrieve(message)


def llm_factory() -> object | None:
    """Injection point for tests; None selects the configured OpenAI client."""
    return None


def _plan(message: str) -> Plan:
    return plan_question(message)


def _execute(plan: Plan) -> list[DynamicOutcome]:
    if not (plan.use_outages or plan.use_scheduled):
        return []
    if plan.zone is None:
        return [DynamicOutcome("zone", {
            "state": "zone_required",
            "detail": "Se necesita un partido y, si se conoce, una localidad.",
        })]
    partido, localidad = plan.zone
    outcomes: list[DynamicOutcome] = []
    if plan.use_outages:
        outcomes.append(DynamicOutcome(
            "current_outages", asdict(lookup_current_outages(partido, localidad)),
        ))
    if plan.use_scheduled:
        outcomes.append(DynamicOutcome(
            "scheduled_works", asdict(lookup_scheduled_works(partido, localidad)),
        ))
    return outcomes


def _tool_event(outcome: DynamicOutcome) -> dict[str, object]:
    return {
        "name": outcome.name,
        "status": outcome.payload.get("state"),
        "sources": dynamic_sources([outcome]),
    }


def _merge_sources(
    articles: list[RetrievedArticle], outcomes: list[DynamicOutcome],
) -> list[dict[str, str]]:
    merged = sources(articles)
    seen = {(item["source_name"], item["url"]) for item in merged}
    for item in dynamic_sources(outcomes):
        key = (item["source_name"], item["url"])
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def _validate(payload: ChatInput) -> str:
    message = payload.message.strip()
    if not message or len(message) > message_max_chars():
        raise HTTPException(422, _INVALID)
    for character in message:
        if ord(character) < 32 and character not in "\n\t":
            raise HTTPException(422, _INVALID)
    return message


def _persist_user(account_id: str | None, conversation_id: str | None, message: str) -> None:
    if account_id is None or conversation_id is None:
        return
    try:
        memory.append_message(account_id, conversation_id, "user", message, [])
    except Exception as error:
        _LOGGER.warning("Assistant user persistence failed (%s).", type(error).__name__)


def _persist_assistant(
    account_id: str | None,
    conversation_id: str | None,
    content: str,
    sources_value: list[dict[str, str]],
) -> None:
    if account_id is None or conversation_id is None:
        return
    try:
        memory.append_message(
            account_id, conversation_id, "assistant", content, sources_value,
        )
    except Exception as error:
        _LOGGER.warning("Assistant message persistence failed (%s).", type(error).__name__)


async def _persist_assistant_async(
    account_id: str | None,
    conversation_id: str | None,
    content: str,
    sources_value: list[dict[str, str]],
) -> None:
    await run_in_threadpool(
        _persist_assistant, account_id, conversation_id, content, sources_value,
    )


def _client_history(items: list[HistoryMessage]) -> list[dict[str, str]]:
    """Bound the visitor's Zustand history; authenticated turns use the DB."""
    recent = list(items)[-history_max_messages():]
    kept: list[dict[str, str]] = []
    total = 0
    cap = history_max_chars()
    for item in reversed(recent):  # newest first, so the cap keeps recent turns
        if not item.content.strip():
            continue
        if total + len(item.content) > cap:
            break
        kept.append({"role": item.role, "content": item.content})
        total += len(item.content)
    kept.reverse()
    return kept


async def _events(
    message: str,
    account_id: str | None,
    requested_conversation_id: str | None,
    client_history: list[HistoryMessage],
) -> AsyncIterator[str]:
    conversation_id: str | None = None
    scope = "temporary"
    if account_id is not None:
        try:
            conversation_id, scope = await run_in_threadpool(
                memory.resolve_conversation, account_id, requested_conversation_id,
            )
        except Exception as error:
            _LOGGER.warning(
                "Assistant conversation resolution failed (%s).", type(error).__name__,
            )
            conversation_id = None
            scope = "temporary"
    event_id = conversation_id or str(uuid.uuid4())
    history: list[dict[str, str]] = []
    if account_id is not None:
        if conversation_id is not None:
            try:
                history = await run_in_threadpool(
                    memory.load_history, account_id, conversation_id,
                )
            except Exception as error:
                _LOGGER.warning(
                    "Assistant history load failed (%s).", type(error).__name__,
                )
            await run_in_threadpool(
                _persist_user, account_id, conversation_id, message,
            )
        # An authenticated resolution failure never trusts client-supplied history.
    else:
        history = _client_history(client_history)
    persisted = False
    answer_parts: list[str] = []
    try:
        yield _sse("conversation", {"conversation_id": event_id, "scope": scope})
        try:
            plan = await run_in_threadpool(_plan, message)
            outcomes = await run_in_threadpool(_execute, plan)
            articles = (
                await run_in_threadpool(_retrieve, message) if plan.use_guide else []
            )
        except AssistantUnavailable:
            await _persist_assistant_async(account_id, conversation_id, FALLBACK_MESSAGE, [])
            persisted = True
            yield _sse("error", {
                "code": "provider_unavailable", "message": FALLBACK_MESSAGE,
            })
            yield _sse("delta", {"text": FALLBACK_MESSAGE})
            yield _sse("sources", {"sources": []})
            yield _sse("done", {"ok": False})
            return
        except Exception:
            await _persist_assistant_async(account_id, conversation_id, FALLBACK_MESSAGE, [])
            persisted = True
            yield _sse("error", {
                "code": "retrieval_unavailable", "message": FALLBACK_MESSAGE,
            })
            yield _sse("delta", {"text": FALLBACK_MESSAGE})
            yield _sse("sources", {"sources": []})
            yield _sse("done", {"ok": False})
            return
        context_articles = articles[:1]
        merged = _merge_sources(context_articles, outcomes)
        for outcome in outcomes:
            yield _sse("tool", _tool_event(outcome))
        if not context_articles and not outcomes:
            await _persist_assistant_async(account_id, conversation_id, REFUSAL_MESSAGE, [])
            persisted = True
            yield _sse("delta", {"text": REFUSAL_MESSAGE})
            yield _sse("sources", {"sources": []})
            yield _sse("done", {"ok": True})
            return
        failed = False
        try:
            async with asyncio.timeout(timeout_seconds()):
                stream = stream_answer(
                    message,
                    context_articles,
                    dynamic=outcomes,
                    history=history,
                    llm=llm_factory(),
                )
                try:
                    first = await asyncio.wait_for(
                        anext(stream), timeout=first_byte_timeout(),
                    )
                except StopAsyncIteration:
                    first = None
                if first is not None:
                    answer_parts.append(first)
                    yield _sse("delta", {"text": first})
                    async for token in stream:
                        answer_parts.append(token)
                        yield _sse("delta", {"text": token})
        except TimeoutError:
            failed = True
            answer_parts.append(FALLBACK_MESSAGE)
            yield _sse("error", {"code": "timeout", "message": FALLBACK_MESSAGE})
            yield _sse("delta", {"text": FALLBACK_MESSAGE})
        except AssistantUnavailable:
            failed = True
            answer_parts.append(FALLBACK_MESSAGE)
            yield _sse("error", {
                "code": "provider_unavailable", "message": FALLBACK_MESSAGE,
            })
            yield _sse("delta", {"text": FALLBACK_MESSAGE})
        except Exception:
            failed = True
            answer_parts.append(FALLBACK_MESSAGE)
            yield _sse("error", {
                "code": "provider_error", "message": FALLBACK_MESSAGE,
            })
            yield _sse("delta", {"text": FALLBACK_MESSAGE})
        final_sources = [] if failed else merged
        await _persist_assistant_async(
            account_id,
            conversation_id,
            "".join(answer_parts) or REFUSAL_MESSAGE,
            final_sources,
        )
        persisted = True
        yield _sse("sources", {"sources": final_sources})
        yield _sse("done", {"ok": not failed})
    finally:
        if not persisted and answer_parts:
            await _persist_assistant_async(
                account_id, conversation_id, "".join(answer_parts), [],
            )
        release_slot()


@router.post("/assistant/chat", response_model=None)
def chat(
    payload: ChatInput,
    request: Request,
    actor: OptionalAuth,
) -> StreamingResponse | JSONResponse:
    origin(request)
    if not limiter.allow(_client(request)):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intent\u00e1 nuevamente en un minuto."},
            headers={
                "Retry-After": str(int(rate_window_seconds())),
                "Cache-Control": "no-store",
            },
        )
    message = _validate(payload)
    if not acquire_slot():
        return JSONResponse(
            status_code=429,
            content={"detail": _BUSY},
            headers={"Retry-After": "5", "Cache-Control": "no-store"},
        )
    account_id = actor.account.id if actor is not None else None
    return StreamingResponse(
        _events(message, account_id, payload.conversation_id, payload.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/assistant/conversations", response_model=list[ConversationOut])
def conversations(actor: Auth) -> list[ConversationOut]:
    return [
        ConversationOut(
            id=item.id,
            created_at=_iso(item.created_at),
            updated_at=_iso(item.updated_at),
            message_count=item.message_count,
        )
        for item in memory.list_conversations(actor.account.id)
    ]


@router.get(
    "/assistant/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesOut,
)
def conversation_messages(
    conversation_id: str, actor: Auth,
) -> ConversationMessagesOut:
    rows = memory.get_messages(actor.account.id, conversation_id)
    if rows is None:
        raise HTTPException(404, "El recurso no est\u00e1 disponible.")
    return ConversationMessagesOut(
        conversation_id=conversation_id,
        messages=[
            StoredMessageOut(
                id=row.id,
                role=row.role,
                content=row.content,
                sources=row.sources,
                created_at=_iso(row.created_at),
            )
            for row in rows
        ],
    )


@router.delete("/assistant/conversations/{conversation_id}", status_code=204)
def remove_conversation(conversation_id: str, actor: Writer) -> Response:
    if not memory.delete_conversation(actor.account.id, conversation_id):
        raise HTTPException(404, "El recurso no est\u00e1 disponible.")
    return Response(status_code=204)
