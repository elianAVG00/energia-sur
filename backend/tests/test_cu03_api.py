"""CU03 public assistant endpoint: SSE, Origin, rate limit and fallback."""

import asyncio
import json
import os
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app import assistant_api
from app.assistant import FALLBACK_MESSAGE, REFUSAL_MESSAGE, DynamicOutcome
from app.assistant_limits import acquire_slot, release_slot, reset_slots
from app.assistant_tools import Plan
from app.guide_store import AssistantUnavailable, RetrievedArticle
from app.main import app

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _article() -> RetrievedArticle:
    return RetrievedArticle(
        article_id="CA-01",
        section="1. Canales de atenci\u00f3n",
        title="\u00bfC\u00f3mo puedo comunicarme con Edesur?",
        content="Respuesta de prueba.",
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


class SlowLLM:
    async def astream(self, messages: object) -> object:
        await asyncio.sleep(1.2)
        yield SimpleNamespace(content="late")


class AssistantApiTests(unittest.TestCase):
    def setUp(self) -> None:
        assistant_api.limiter.reset()
        reset_slots()
        self._original_retrieve = assistant_api._retrieve
        assistant_api._retrieve = lambda message: [_article()]
        assistant_api.llm_factory = lambda: FakeLLM()
        self._original_plan = assistant_api._plan
        self._original_execute = assistant_api._execute

    def tearDown(self) -> None:
        assistant_api.limiter.reset()
        assistant_api.llm_factory = lambda: None
        assistant_api._plan = self._original_plan
        assistant_api._execute = self._original_execute
        assistant_api._retrieve = self._original_retrieve
        reset_slots()
        os.environ.pop("ASSISTANT_RATE_LIMIT", None)
        os.environ.pop("ASSISTANT_MAX_CONCURRENCY", None)
        os.environ.pop("ASSISTANT_TIMEOUT_SECONDS", None)
        os.environ.pop("ASSISTANT_FIRST_BYTE_TIMEOUT", None)

    def _run(self, callback: object) -> object:
        async def runner() -> object:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test",
            ) as client:
                return await callback(client)  # type: ignore[operator]

        return asyncio.run(runner())

    def _stream(
        self,
        client: httpx.AsyncClient,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> object:
        async def read() -> str:
            async with client.stream(
                "POST", "/assistant/chat",
                json={"message": message, "history": history or []},
                headers=ORIGIN,
            ) as response:
                self.assertEqual(response.status_code, 200)
                return "".join([chunk async for chunk in response.aiter_text()])

        return read()

    def test_sse_stream_contains_events(self) -> None:
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn("event: conversation", body)
        self.assertIn("event: delta", body)
        self.assertIn("Hola", body)
        self.assertIn("event: sources", body)
        self.assertIn("event: done", body)

    def test_origin_is_required(self) -> None:
        async def call(client: httpx.AsyncClient) -> httpx.Response:
            return await client.post("/assistant/chat", json={"message": "hola"})

        response = self._run(call)
        self.assertEqual(response.status_code, 403)

    def test_overlong_message_is_rejected(self) -> None:
        async def call(client: httpx.AsyncClient) -> httpx.Response:
            return await client.post(
                "/assistant/chat", json={"message": "x" * 3000}, headers=ORIGIN,
            )

        response = self._run(call)
        self.assertEqual(response.status_code, 422)

    def test_rate_limit_returns_retry_after(self) -> None:
        os.environ["ASSISTANT_RATE_LIMIT"] = "1"

        async def call(client: httpx.AsyncClient) -> tuple[httpx.Response, httpx.Response]:
            first = await client.post(
                "/assistant/chat", json={"message": "hola"}, headers=ORIGIN,
            )
            second = await client.post(
                "/assistant/chat", json={"message": "hola"}, headers=ORIGIN,
            )
            return first, second

        first, second = self._run(call)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers["retry-after"], "60")

    def test_retrieval_failure_falls_back(self) -> None:
        def boom(message: str) -> list[RetrievedArticle]:
            raise RuntimeError("database down")

        assistant_api._retrieve = boom
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn("retrieval_unavailable", body)
        self.assertIn(FALLBACK_MESSAGE, body)
        self.assertIn('"ok": false', body)

    def test_sse_headers_and_done(self) -> None:
        async def read(client: httpx.AsyncClient) -> tuple[str, str, str]:
            async with client.stream(
                "POST", "/assistant/chat", json={"message": "hola"}, headers=ORIGIN,
            ) as response:
                body = "".join([chunk async for chunk in response.aiter_text()])
                return (
                    response.headers.get("content-type", ""),
                    response.headers.get("cache-control", ""),
                    body,
                )

        content_type, cache, body = self._run(read)
        self.assertTrue(content_type.startswith("text/event-stream"))
        self.assertEqual(cache, "no-store")
        self.assertIn('"ok": true', body)

    def test_body_limit(self) -> None:
        async def call(client: httpx.AsyncClient) -> httpx.Response:
            return await client.post(
                "/assistant/chat", json={"message": "x" * 20000}, headers=ORIGIN,
            )

        self.assertEqual(self._run(call).status_code, 413)

    def test_anonymous_history_is_forwarded(self) -> None:
        captured: dict[str, list[dict[str, str]]] = {}

        async def fake_stream(
            query: str, articles: object, *, dynamic: object,
            history: object, llm: object = None,
        ) -> object:
            captured["history"] = [dict(item) for item in history]  # type: ignore[union-attr]
            yield "ok"

        original = assistant_api.stream_answer
        assistant_api.stream_answer = fake_stream
        try:
            body = self._run(lambda client: self._stream(
                client, "hola", [{"role": "user", "content": "antes"}],
            ))
        finally:
            assistant_api.stream_answer = original
        self.assertEqual(
            captured["history"], [{"role": "user", "content": "antes"}],
        )
        self.assertIn("event: delta", body)

    def test_visitor_history_keeps_newest_turns(self) -> None:
        items = [
            assistant_api.HistoryMessage(role="user", content="x" * 1000),
            assistant_api.HistoryMessage(role="assistant", content=""),
            assistant_api.HistoryMessage(role="user", content="nuevo"),
        ]
        with patch.dict(os.environ, {"ASSISTANT_HISTORY_MAX_CHARS": "1000"}):
            history = assistant_api._client_history(items)
        self.assertEqual(history, [{"role": "user", "content": "nuevo"}])

    def test_body_limit_without_content_length(self) -> None:
        payload = json.dumps({"message": "x" * 20000}).encode()
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/assistant/chat",
            "raw_path": b"/assistant/chat",
            "query_string": b"",
            "root_path": "",
            "headers": [
                (b"host", b"test"),
                (b"origin", b"http://127.0.0.1:5173"),
                (b"content-type", b"application/json"),
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
        }
        chunks = [
            {"type": "http.request", "body": payload[:8000], "more_body": True},
            {"type": "http.request", "body": payload[8000:], "more_body": False},
        ]
        sent: list[dict[str, object]] = []

        async def receive() -> dict[str, object]:
            return chunks.pop(0)

        async def send(message: dict[str, object]) -> None:
            sent.append(message)

        async def run() -> None:
            await app(scope, receive, send)  # type: ignore[arg-type]

        asyncio.run(run())
        self.assertEqual(sent[0]["status"], 413)

    def test_sources_cite_only_the_best_article(self) -> None:
        second = RetrievedArticle(
            article_id="PA-01",
            section="2. Opciones de pago",
            title="\u00bfD\u00f3nde pago?",
            content="Contenido de prueba.",
            source_name="Edesur",
            source_urls=({
                "source_name": "Edesur",
                "url": "https://www.edesur.com.ar/preguntas-frecuentes/",
            },),
            limitations=(),
            information_type="medios de pago.",
            volatility="variable",
            last_verified_at=date(2026, 11, 10),
            distance=0.2,
        )
        assistant_api._retrieve = lambda message: [_article(), second]
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn("canales-de-atencion", body)
        self.assertNotIn("preguntas-frecuentes", body)

    def test_timeout_falls_back(self) -> None:
        os.environ["ASSISTANT_TIMEOUT_SECONDS"] = "30"
        os.environ["ASSISTANT_FIRST_BYTE_TIMEOUT"] = "1"
        assistant_api.llm_factory = lambda: SlowLLM()
        try:
            body = self._run(lambda client: self._stream(client, "hola"))
        finally:
            os.environ.pop("ASSISTANT_TIMEOUT_SECONDS", None)
            os.environ.pop("ASSISTANT_FIRST_BYTE_TIMEOUT", None)
        self.assertIn("timeout", body)
        self.assertIn(FALLBACK_MESSAGE, body)
        self.assertIn('"ok": false', body)
        self.assertTrue(acquire_slot())
        release_slot()

    def test_no_articles_refuses(self) -> None:
        assistant_api._retrieve = lambda message: []
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn(REFUSAL_MESSAGE, body)

    def test_provider_failure_falls_back(self) -> None:
        def fail() -> object:
            raise AssistantUnavailable("no key")

        assistant_api.llm_factory = fail
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn("provider_unavailable", body)
        self.assertIn(FALLBACK_MESSAGE, body)
        self.assertIn('"ok": false', body)

    def test_dynamic_tool_event_and_source(self) -> None:
        assistant_api._plan = lambda message: Plan(
            use_guide=False, use_outages=True, use_scheduled=False,
            zone=("LOMAS DE ZAMORA", "BANFIELD"),
        )
        assistant_api._execute = lambda plan: [DynamicOutcome("current_outages", {
            "state": "reported",
            "freshness": "fresh",
            "coverage": "covered",
            "source": "ENRE",
            "source_url": "https://www.enre.gov.ar/paginacorte/js/data_EDS.js",
            "zone": "LOMAS DE ZAMORA / BANFIELD",
            "outages": [],
        })]
        body = self._run(lambda client: self._stream(client, "hola"))
        self.assertIn("event: tool", body)
        self.assertIn("https://www.enre.gov.ar/", body)
        self.assertIn('"ok": true', body)

    def test_stale_cookie_is_anonymous(self) -> None:
        async def call(client: httpx.AsyncClient) -> httpx.Response:
            return await client.post(
                "/assistant/chat",
                json={"message": "hola"},
                headers={**ORIGIN, "Cookie": "energia_sur_session=invalid"},
            )

        self.assertEqual(self._run(call).status_code, 200)

    def test_concurrency_limit(self) -> None:
        os.environ["ASSISTANT_MAX_CONCURRENCY"] = "1"
        reset_slots()
        self.assertTrue(acquire_slot())
        try:
            async def call(client: httpx.AsyncClient) -> httpx.Response:
                return await client.post(
                    "/assistant/chat", json={"message": "hola"}, headers=ORIGIN,
                )

            response = self._run(call)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["retry-after"], "5")
        finally:
            release_slot()
            reset_slots()

    def test_error_does_not_echo_message_or_key(self) -> None:
        def boom(message: str) -> list[RetrievedArticle]:
            raise RuntimeError("database down")

        assistant_api._retrieve = boom
        secret = "sk-" + "x" * 24
        body = self._run(lambda client: self._stream(client, secret))
        self.assertNotIn(secret, body)
        self.assertNotIn("sk-", body)
        self.assertIn(FALLBACK_MESSAGE, body)
