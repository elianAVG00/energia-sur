"""Exercise the actual ASGI route without an HTTP client dependency."""

import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from starlette.types import Message, Scope

from app.main import HealthResponse, app


class HealthContractTests(unittest.IsolatedAsyncioTestCase):
    """Check the public health contract and configuration-free startup."""

    async def get_health(self) -> list[Message]:
        scope: Scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/health",
            "raw_path": b"/health",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
        }
        messages: list[Message] = []

        async def receive() -> Message:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        return messages

    def assert_health_response(self, messages: list[Message]) -> None:
        self.assertEqual(len(messages), 2)
        start, body = messages
        self.assertEqual(start["type"], "http.response.start")
        self.assertEqual(start["status"], 200)
        headers = dict(start["headers"])
        self.assertEqual(headers[b"content-type"], b"application/json")
        self.assertEqual(body["type"], "http.response.body")
        self.assertEqual(body["body"], b'{"status":"ok"}')
        self.assertFalse(body.get("more_body", False))

    async def test_public_health_returns_exact_json_contract(self) -> None:
        self.assert_health_response(await self.get_health())

    async def test_health_requires_no_environment_configuration(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assert_health_response(await self.get_health())

    async def test_lifespan_requires_no_environment_configuration(self) -> None:
        scope: Scope = {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "state": {},
        }
        incoming: list[Message] = [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
        outgoing: list[Message] = []

        async def receive() -> Message:
            return incoming.pop(0)

        async def send(message: Message) -> None:
            outgoing.append(message)

        with patch.dict(os.environ, {}, clear=True):
            await app(scope, receive, send)

        self.assertEqual(
            outgoing,
            [
                {"type": "lifespan.startup.complete"},
                {"type": "lifespan.shutdown.complete"},
            ],
        )
        self.assertEqual(incoming, [])

    def test_response_schema_allows_only_ok_status(self) -> None:
        self.assertEqual(HealthResponse(status="ok").model_dump(), {"status": "ok"})
        for payload in ({}, {"status": "unavailable"}, {"status": None}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError):
                    HealthResponse.model_validate(payload)
