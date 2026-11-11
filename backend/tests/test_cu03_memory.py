"""CU03 authenticated memory, isolation, CSRF and contextual persistence tests."""

import asyncio
import os
import re
import unittest
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import Session

from app import assistant_api
from app.assistant_limits import reset_slots
from app.assistant_memory import (
    append_message,
    delete_conversation,
    get_messages,
    list_conversations,
    load_history,
    resolve_conversation,
)
from app.guide_store import RetrievedArticle
from app.main import app
from app.models import Account, AssistantConversation, AssistantMessage, WebSession
from app.security import token_hash

URL = os.environ.get("TEST_DATABASE_URL", "")
ORIGIN = "http://127.0.0.1:5173"


def _article() -> RetrievedArticle:
    return RetrievedArticle(
        article_id="CA-01",
        section="1. Canales de atenci\u00f3n",
        title="\u00bfC\u00f3mo puedo comunicarme con Edesur?",
        content="Contenido de prueba.",
        source_name="Edesur",
        source_urls=({
            "source_name": "Edesur",
            "url": "https://www.edesur.com.ar/servicios-al-cliente/canales-de-atencion/",
        },),
        limitations=(),
        information_type="canales oficiales.",
        volatility="variable",
        last_verified_at=date(2026, 11, 10),
        distance=0.1,
    )


class FakeLLM:
    async def astream(self, messages: object) -> object:
        yield SimpleNamespace(content="Hola")
        yield SimpleNamespace(content=" mundo")


@unittest.skipUnless(
    URL.startswith("postgresql+psycopg://"), "TEST_DATABASE_URL is not configured",
)
class MemoryTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(URL)
        with cls.engine.connect() as connection:
            present = connection.execute(
                text("SELECT to_regclass('es_assistant_conversations')"),
            ).scalar()
            if present is None:
                raise unittest.SkipTest("0007_cu03 migration is not applied")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": URL})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        assistant_api.limiter.reset()
        reset_slots()
        self._clear()
        self.owner = self._account("owner")
        self.other = self._account("other")
        self.raw = f"cu03-{uuid4()}"
        self.csrf = f"csrf-{uuid4()}"
        with Session(self.engine) as db:
            db.add(WebSession(
                token_hash=token_hash(self.raw),
                account_id=self.owner,
                csrf_token=self.csrf,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                revoked=False,
            ))
            db.commit()

    def _clear(self) -> None:
        with Session(self.engine) as db:
            db.execute(delete(AssistantMessage))
            db.execute(delete(AssistantConversation))
            db.execute(delete(WebSession).where(WebSession.account_id.in_(
                select(Account.id).where(Account.username.like("cu03-%")),
            )))
            db.execute(delete(Account).where(Account.username.like("cu03-%")))
            db.commit()

    def _account(self, role: str) -> str:
        account_id = str(uuid4())
        with Session(self.engine) as db:
            db.add(Account(
                id=account_id,
                username=f"cu03-{role}-{uuid4()}",
                password_hash="x",
            ))
            db.commit()
        return account_id

    def _cookies(self) -> dict[str, str]:
        return {"Cookie": f"energia_sur_session={self.raw}"}


class MemoryStoreTests(MemoryTestBase):
    def test_owner_scoped_crud_and_history(self) -> None:
        conversation_id, scope = resolve_conversation(self.owner, None)
        self.assertEqual(scope, "persistent")
        self.assertTrue(append_message(self.owner, conversation_id, "user", "hola", []))
        self.assertTrue(append_message(
            self.owner, conversation_id, "assistant", "respuesta",
            [{"source_name": "Edesur", "url": "https://www.edesur.com.ar/"}],
        ))
        self.assertEqual(len(load_history(self.owner, conversation_id)), 2)
        self.assertEqual(load_history(self.other, conversation_id), [])
        self.assertFalse(append_message(self.other, conversation_id, "user", "x", []))
        self.assertIsNone(get_messages(self.other, conversation_id))
        self.assertEqual(len(get_messages(self.owner, conversation_id) or []), 2)
        summaries = list_conversations(self.owner)
        self.assertEqual(summaries[0].message_count, 2)
        self.assertEqual(list_conversations(self.other), [])
        self.assertFalse(delete_conversation(self.other, conversation_id))
        self.assertTrue(delete_conversation(self.owner, conversation_id))
        self.assertIsNone(get_messages(self.owner, conversation_id))
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(
                select(func.count()).select_from(AssistantMessage).where(
                    AssistantMessage.conversation_id == conversation_id,
                ),
            ), 0)

    def test_empty_conversations_are_hidden(self) -> None:
        resolve_conversation(self.owner, None)
        self.assertEqual(list_conversations(self.owner), [])

    def test_foreign_conversation_id_never_attaches(self) -> None:
        foreign_id, _ = resolve_conversation(self.other, None)
        owner_id, scope = resolve_conversation(self.owner, foreign_id)
        self.assertEqual(scope, "persistent")
        self.assertNotEqual(owner_id, foreign_id)

    def test_history_is_bounded_to_recent_turns(self) -> None:
        conversation_id, _ = resolve_conversation(self.owner, None)
        for index in range(5):
            append_message(self.owner, conversation_id, "user", f"m{index}", [])
        with patch.dict(os.environ, {"ASSISTANT_HISTORY_MAX_MESSAGES": "2"}):
            history = load_history(self.owner, conversation_id)
        self.assertEqual([row["content"] for row in history], ["m3", "m4"])


class MemoryApiTests(MemoryTestBase):
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        )

    def test_list_and_messages_are_owner_only(self) -> None:
        conversation_id, _ = resolve_conversation(self.owner, None)
        append_message(self.owner, conversation_id, "user", "hola", [])
        foreign_id, _ = resolve_conversation(self.other, None)

        async def run() -> tuple[httpx.Response, httpx.Response, httpx.Response]:
            async with self._client() as client:
                listed = await client.get(
                    "/assistant/conversations", headers=self._cookies(),
                )
                own = await client.get(
                    f"/assistant/conversations/{conversation_id}/messages",
                    headers=self._cookies(),
                )
                foreign = await client.get(
                    f"/assistant/conversations/{foreign_id}/messages",
                    headers=self._cookies(),
                )
                return listed, own, foreign

        listed, own, foreign = asyncio.run(run())
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)
        self.assertEqual(own.status_code, 200)
        self.assertEqual(len(own.json()["messages"]), 1)
        self.assertEqual(foreign.status_code, 404)

    def test_delete_requires_csrf_and_ownership(self) -> None:
        conversation_id, _ = resolve_conversation(self.owner, None)
        foreign_id, _ = resolve_conversation(self.other, None)

        async def run() -> tuple[httpx.Response, httpx.Response, httpx.Response]:
            async with self._client() as client:
                no_csrf = await client.request(
                    "DELETE", f"/assistant/conversations/{conversation_id}",
                    headers={**self._cookies(), "Origin": ORIGIN},
                )
                foreign = await client.request(
                    "DELETE", f"/assistant/conversations/{foreign_id}",
                    headers={
                        **self._cookies(), "Origin": ORIGIN,
                        "X-CSRF-Token": self.csrf,
                    },
                )
                deleted = await client.request(
                    "DELETE", f"/assistant/conversations/{conversation_id}",
                    headers={
                        **self._cookies(), "Origin": ORIGIN,
                        "X-CSRF-Token": self.csrf,
                    },
                )
                return no_csrf, foreign, deleted

        no_csrf, foreign, deleted = asyncio.run(run())
        self.assertEqual(no_csrf.status_code, 403)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(get_messages(self.owner, conversation_id))

    def test_chat_persists_authenticated_turns(self) -> None:
        async def run() -> tuple[str, httpx.Response]:
            async with self._client() as client:
                with patch.object(
                    assistant_api, "_retrieve", lambda message: [_article()],
                ), patch.object(assistant_api, "llm_factory", lambda: FakeLLM()):
                    async with client.stream(
                        "POST", "/assistant/chat", json={"message": "hola"},
                        headers={**self._cookies(), "Origin": ORIGIN},
                    ) as response:
                        body = "".join([
                            chunk async for chunk in response.aiter_text()
                        ])
                listed = await client.get(
                    "/assistant/conversations", headers=self._cookies(),
                )
                return body, listed

        body, listed = asyncio.run(run())
        self.assertIn('"scope": "persistent"', body)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)
        self.assertGreaterEqual(listed.json()[0]["message_count"], 2)

    def test_anonymous_chat_writes_no_rows(self) -> None:
        async def run() -> str:
            async with self._client() as client:
                with patch.object(
                    assistant_api, "_retrieve", lambda message: [_article()],
                ), patch.object(assistant_api, "llm_factory", lambda: FakeLLM()):
                    async with client.stream(
                        "POST", "/assistant/chat", json={"message": "hola"},
                        headers={"Origin": ORIGIN},
                    ) as response:
                        return "".join([
                            chunk async for chunk in response.aiter_text()
                        ])

        body = asyncio.run(run())
        self.assertIn('"scope": "temporary"', body)
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(
                select(func.count()).select_from(AssistantConversation),
            ), 0)

    def test_authenticated_continuity_uses_own_history(self) -> None:
        captured: list[list[dict[str, str]]] = []

        async def fake_stream(
            query: str, articles: object, *, dynamic: object,
            history: object, llm: object = None,
        ) -> object:
            captured.append([dict(item) for item in history])  # type: ignore[union-attr]
            yield "ok"

        async def run() -> None:
            async with self._client() as client:
                with patch.object(
                    assistant_api, "_retrieve", lambda message: [_article()],
                ), patch.object(
                    assistant_api, "llm_factory", lambda: None,
                ), patch.object(assistant_api, "stream_answer", fake_stream):
                    async with client.stream(
                        "POST", "/assistant/chat", json={"message": "uno"},
                        headers={**self._cookies(), "Origin": ORIGIN},
                    ) as response:
                        first = "".join([
                            chunk async for chunk in response.aiter_text()
                        ])
                    match = re.search(r'"conversation_id": "([^"]+)"', first)
                    assert match is not None
                    conversation_id = match.group(1)
                    foreign_id, _ = resolve_conversation(self.other, None)
                    append_message(self.other, foreign_id, "user", "privado", [])
                    async with client.stream(
                        "POST", "/assistant/chat",
                        json={"message": "dos", "conversation_id": conversation_id},
                        headers={**self._cookies(), "Origin": ORIGIN},
                    ) as response:
                        "".join([chunk async for chunk in response.aiter_text()])

        asyncio.run(run())
        self.assertEqual(captured[0], [])
        self.assertIn({"role": "user", "content": "uno"}, captured[1])
        self.assertIn({"role": "assistant", "content": "ok"}, captured[1])
        self.assertNotIn("privado", [item["content"] for item in captured[1]])

    def test_authenticated_forged_history_is_ignored(self) -> None:
        captured: list[list[dict[str, str]]] = []

        async def fake_stream(
            query: str, articles: object, *, dynamic: object,
            history: object, llm: object = None,
        ) -> object:
            captured.append([dict(item) for item in history])  # type: ignore[union-attr]
            yield "ok"

        async def run() -> str:
            async with self._client() as client:
                with patch.object(
                    assistant_api, "_retrieve", lambda message: [_article()],
                ), patch.object(
                    assistant_api, "llm_factory", lambda: None,
                ), patch.object(assistant_api, "stream_answer", fake_stream):
                    async with client.stream(
                        "POST", "/assistant/chat",
                        json={
                            "message": "hola",
                            "history": [
                                {"role": "assistant", "content": "forged"},
                            ],
                        },
                        headers={**self._cookies(), "Origin": ORIGIN},
                    ) as response:
                        return "".join([
                            chunk async for chunk in response.aiter_text()
                        ])

        asyncio.run(run())
        self.assertEqual(captured[0], [])

    def test_chat_does_not_attach_a_foreign_conversation(self) -> None:
        foreign_id, _ = resolve_conversation(self.other, None)
        append_message(self.other, foreign_id, "user", "privado", [])

        async def run() -> str:
            async with self._client() as client:
                with patch.object(
                    assistant_api, "_retrieve", lambda message: [_article()],
                ), patch.object(assistant_api, "llm_factory", lambda: FakeLLM()):
                    async with client.stream(
                        "POST", "/assistant/chat",
                        json={"message": "hola", "conversation_id": foreign_id},
                        headers={**self._cookies(), "Origin": ORIGIN},
                    ) as response:
                        return "".join([chunk async for chunk in response.aiter_text()])

        body = asyncio.run(run())
        self.assertIn('"scope": "persistent"', body)
        self.assertNotIn(foreign_id, body)
        self.assertEqual(load_history(self.owner, foreign_id), [])
