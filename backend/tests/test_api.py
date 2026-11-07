"""Actual ASGI + PostgreSQL integration; retain unique synthetic fixtures."""

import json
import os
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from http.cookies import SimpleCookie
from io import BytesIO
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4

from pypdf import PdfReader
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from starlette.types import Message, Scope

from app.diary import BUENOS_AIRES
from app.main import app
from app.models import Account, Interruption, WebSession
from app.security import hash_password


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise AssertionError("Expected a JSON object")
    return dict(value)


def string(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("Expected a string")
    return value


def version(value: object) -> int:
    if not isinstance(value, int):
        raise AssertionError("Expected an integer version")
    return value


@dataclass
class Client:
    cookie: str = ""
    csrf: str = ""
    headers: dict[bytes, bytes] = field(default_factory=dict)
    content: bytes = b""

    async def request(self, method: str, path: str, payload: object = None,
                      *, csrf: bool = True, origin: str = "http://127.0.0.1:5173") -> int:
        route, _, query = path.partition("?")
        headers = [(b"content-type", b"application/json")]
        if origin:
            headers.append((b"origin", origin.encode()))
        if self.cookie:
            headers.append((b"cookie", self.cookie.encode()))
        if csrf and self.csrf:
            headers.append((b"x-csrf-token", self.csrf.encode()))
        scope: Scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "method": method, "scheme": "http", "path": route,
            "raw_path": route.encode(), "query_string": query.encode(), "root_path": "",
            "headers": headers, "client": ("127.0.0.1", 1234), "server": ("test", 8000),
        }
        messages: list[Message] = []

        async def receive() -> Message:
            return {"type": "http.request", "body": json.dumps(payload).encode(), "more_body": False}

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        self.headers = dict(messages[0]["headers"])
        self.content = b"".join(message.get("body", b"") for message in messages[1:])
        if b"set-cookie" in self.headers:
            cookies = SimpleCookie()
            cookies.load(self.headers[b"set-cookie"].decode())
            self.cookie = "; ".join(f"{key}={value.value}" for key, value in cookies.items())
        return int(messages[0]["status"])

    def data(self) -> dict[str, object]:
        return obj(json.loads(self.content))


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)
        cls.username_a, cls.username_b = f"test-a-{uuid4()}", f"test-b-{uuid4()}"
        cls.password = "Synthetic-only-unit-password"
        with Session(cls.engine) as db:
            db.add_all([Account(username=name, password_hash=hash_password(cls.password))
                        for name in (cls.username_a, cls.username_b)])
            db.commit()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": self.url})
        self.environment.start()
        self.clock = patch("app.api.now", return_value=datetime(2026, 11, 7, 12, tzinfo=BUENOS_AIRES))
        self.clock.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.clock.stop)

    async def login(self, username: str | None = None) -> Client:
        client = Client()
        self.assertEqual(await client.request("POST", "/login", {
            "username": username or self.username_a, "password": self.password,
        }), 200)
        client.csrf = string(client.data()["csrf_token"])
        self.assertIn(b"httponly", client.headers[b"set-cookie"].lower())
        self.assertIn(b"samesite=lax", client.headers[b"set-cookie"].lower())
        return client

    async def domicile(self, client: Client) -> str:
        self.assertEqual(await client.request("POST", "/domiciles", {"display_address": "Synthetic own address"}), 201)
        return string(client.data()["id"])

    def cut_input(self, start: str = "2026-11-01T10:00", end: str | None = "2026-11-01T12:00") -> dict[str, object]:
        return {"start_at": start, "end_at": end, "observations": "Synthetic energía", "complaint_number": "TEST-001"}

    async def cut(self, client: Client, domicile: str, start: str = "2026-11-01T10:00", end: str | None = "2026-11-01T12:00") -> dict[str, object]:
        self.assertEqual(await client.request("POST", f"/domiciles/{domicile}/interruptions", self.cut_input(start, end)), 201)
        return client.data()

    def period(self) -> str:
        return urlencode({"period_start": "2026-11-01T00:00", "period_end": "2026-11-02T00:00"})

    async def stored(self, client: Client, domicile: str) -> list[dict[str, object]]:
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/interruptions"), 200)
        rows = json.loads(client.content)
        self.assertIsInstance(rows, list)
        return [obj(row) for row in rows]

    @classmethod
    def tearDownClass(cls) -> None:
        from app.db import get_engine
        with patch.dict(os.environ, {"DATABASE_URL": cls.url}):
            get_engine().dispose()
        cls.engine.dispose()

    async def test_real_registration_cut_storage_summary_pdf(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        await self.cut(client, domicile)
        await self.cut(client, domicile, "2026-11-01T11:00", "2026-11-01T13:00")
        await self.cut(client, domicile, "2026-10-31T23:00", "2026-11-01T00:00")
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{self.period()}"), 200)
        data = client.data()
        self.assertEqual(data["total_minutes"], 180)
        self.assertEqual(len(data["entries"]), 2)
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{self.period()}"), 200)
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(client.content)).pages)
        for expected in ("Synthetic own address", "energía", "TEST-001", "3 h 0 min"):
            self.assertIn(expected, text)
        self.assertEqual(client.headers[b"cache-control"], b"no-store")

    async def test_other_account_denied_all_paths(self) -> None:
        owner, foreign = await self.login(), await self.login(self.username_b)
        domicile = await self.domicile(owner)
        cut = await self.cut(owner, domicile, end=None)
        identifier = string(cut["id"])
        before = await self.stored(owner, domicile)
        for method, path, body in (
            ("GET", f"/domiciles/{domicile}/interruptions", None),
            ("POST", f"/domiciles/{domicile}/interruptions", self.cut_input()),
            ("PATCH", f"/interruptions/{identifier}", {**self.cut_input(), "version": 1}),
            ("POST", f"/interruptions/{identifier}/close", {"end_at": "2026-11-01T12:00", "version": 1}),
            ("GET", f"/domiciles/{domicile}/summary?{self.period()}", None),
            ("GET", f"/domiciles/{domicile}/report.pdf?{self.period()}", None),
        ):
            with self.subTest(method=method, path=path):
                self.assertEqual(await foreign.request(method, path, body), 404)
                self.assertEqual(foreign.data(), {"detail": "El recurso no está disponible."})
        self.assertEqual(await foreign.request("GET", "/domiciles"), 200)
        self.assertNotIn(domicile, foreign.content.decode())
        self.assertEqual(await self.stored(owner, domicile), before)
        foreign_domicile = await self.domicile(foreign)
        self.assertEqual(await owner.request("GET", "/domiciles"), 200)
        self.assertNotIn(foreign_domicile, owner.content.decode())
        self.assertEqual(await foreign.request("GET", "/domiciles"), 200)
        self.assertIn(foreign_domicile, foreign.content.decode())
        self.assertNotIn(domicile, foreign.content.decode())
        self.assertEqual(await foreign.request("POST", "/domiciles//interruptions", self.cut_input()), 404)

    async def test_invalid_correction_and_closure_leave_every_field_and_version_unchanged(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        opened = await self.cut(client, domicile, end=None)
        closed = await self.cut(client, domicile)
        before = await self.stored(client, domicile)
        invalid = (
            self.cut_input("2026-11-07T12:01", None),
            self.cut_input(end="2026-11-07T12:01"),
            self.cut_input(end="2026-11-01T10:00"),
            self.cut_input(end="2026-11-01T09:59"),
            self.cut_input("2026-11-01T10:00:01", None),
        )
        for record in (opened, closed):
            for body in invalid:
                with self.subTest(state=record["status"], body=body):
                    self.assertEqual(await client.request("PATCH", f"/interruptions/{record['id']}", {**body, "version": 1}), 422)
                    self.assertEqual(await self.stored(client, domicile), before)
        for end in ("2026-11-07T12:01", "2026-11-01T10:00", "2026-11-01T09:59"):
            self.assertEqual(await client.request("POST", f"/interruptions/{opened['id']}/close", {"end_at": end, "version": 1}), 422)
            self.assertEqual(await self.stored(client, domicile), before)
        self.assertEqual(await client.request("PATCH", f"/interruptions/{opened['id']}", {**self.cut_input(), "version": 99}), 409)
        self.assertEqual(await self.stored(client, domicile), before)

    async def test_fixed_clock_report_pdf_and_stored_nonmutation_scenarios(self) -> None:
        client = await self.login()
        cases = (
            (("2026-10-31T23:00", "2026-11-01T02:00"), "2026-11-07T12:00", 120, "2 h 0 min"),
            (("2026-11-01T10:00", None), "2026-11-01T15:00", 300, "5 h 0 min"),
            (("2026-11-01T22:00", None), "2026-11-02T03:00", 120, "2 h 0 min"),
        )
        for (start, end), generation, total, displayed in cases:
            domicile = await self.domicile(client)
            await self.cut(client, domicile, start, end)
            before = await self.stored(client, domicile)
            with patch("app.api.now", return_value=datetime.fromisoformat(generation).replace(tzinfo=BUENOS_AIRES)):
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{self.period()}"), 200)
                self.assertEqual(client.data()["total_minutes"], total)
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{self.period()}"), 200)
                text = " ".join(p.extract_text() for p in PdfReader(BytesIO(client.content)).pages)
                self.assertIn(displayed, text)
                if end is None:
                    self.assertEqual(text.count("En curso"), 2)
            self.assertEqual(await self.stored(client, domicile), before)

    async def test_minute_union_zero_exclusion_and_thirty_minute_closure_persist(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        await self.cut(client, domicile, "2026-11-01T10:05", "2026-11-01T10:50")
        await self.cut(client, domicile, "2026-11-01T10:35", "2026-11-01T11:10")
        for start, end in (("2026-10-31T23:00", "2026-11-01T00:00"), ("2026-11-02T00:00", "2026-11-02T01:00")):
            body = {**self.cut_input(start, end), "observations": "EXCLUDED-BOUNDARY"}
            self.assertEqual(await client.request("POST", f"/domiciles/{domicile}/interruptions", body), 201)
        before = await self.stored(client, domicile)
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{self.period()}"), 200)
        self.assertEqual(client.data()["total_minutes"], 65)
        self.assertEqual(len(client.data()["entries"]), 2)
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{self.period()}"), 200)
        text = " ".join(p.extract_text() for p in PdfReader(BytesIO(client.content)).pages)
        self.assertIn("1 h 5 min", text)
        self.assertNotIn("EXCLUDED-BOUNDARY", text)
        self.assertEqual(await self.stored(client, domicile), before)
        other = await self.domicile(client)
        cut = await self.cut(client, other, "2026-11-01T10:00", None)
        self.assertEqual(await client.request("POST", f"/interruptions/{cut['id']}/close", {"end_at": "2026-11-01T10:30", "version": 1}), 200)
        self.assertEqual(await client.request("GET", f"/domiciles/{other}/summary?{self.period()}"), 200)
        self.assertEqual(client.data()["total_minutes"], 30)

    async def test_origin_csrf_and_sensitive_validation(self) -> None:
        client = await self.login()
        for kwargs in ({"csrf": False}, {"origin": "https://untrusted.invalid"}, {"origin": ""}):
            self.assertEqual(await client.request("POST", "/domiciles", {"display_address": "Synthetic"}, **kwargs), 403)
        self.assertEqual(await client.request("POST", "/login", {"username": self.username_a, "password": self.password}, origin="https://untrusted.invalid"), 403)
        self.assertEqual(await client.request("POST", "/login", {"username": [], "password": "DO-NOT-REFLECT"}), 422)
        self.assertNotIn("DO-NOT-REFLECT", client.content.decode())
        for body in ({"display_address": " "}, {"display_address": "x" * 301}, {"display_address": "Synthetic", "account_id": "foreign"}):
            self.assertEqual(await client.request("POST", "/domiciles", body), 422)

    async def test_login_requires_explicit_trusted_origin_without_pre_auth_csrf(self) -> None:
        client = Client()
        payload = {"username": self.username_a, "password": self.password}
        for untrusted in (
            "", "null", "https://untrusted.invalid", "http://127.0.0.1:5173.evil.invalid",
            "http://127.0.0.1:5173/", "http://127.0.0.1:5173 https://untrusted.invalid",
        ):
            with self.subTest(origin=untrusted):
                self.assertEqual(await client.request(
                    "POST", "/login", payload, csrf=False, origin=untrusted,
                ), 403)
                self.assertEqual(client.data(), {"detail": "El origen de la solicitud no está autorizado."})
                self.assertNotIn(b"set-cookie", client.headers)
                self.assertEqual(client.cookie, "")
                self.assertEqual(await client.request("GET", "/session"), 401)
        self.assertEqual(await client.request("POST", "/login", payload, csrf=False), 200)
        self.assertTrue(string(client.data()["csrf_token"]))
        self.assertEqual(await client.request("GET", "/session"), 200)

    async def test_every_authenticated_mutation_rejects_missing_or_invalid_csrf(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        cut = await self.cut(client, domicile, end=None)
        identifier = string(cut["id"])
        before = await self.stored(client, domicile)
        self.assertEqual(await client.request("GET", "/domiciles"), 200)
        homes_before = client.content
        valid_csrf = client.csrf
        for supplied in ("", "invalid-token", "token-ñ"):
            client.csrf = supplied
            for method, path, body in (
                ("POST", "/logout", None),
                ("POST", "/domiciles", {"display_address": "Must not persist"}),
                ("POST", f"/domiciles/{domicile}/interruptions", self.cut_input()),
                ("PATCH", f"/interruptions/{identifier}", {**self.cut_input(), "version": 1}),
                ("POST", f"/interruptions/{identifier}/close", {"end_at": "2026-11-01T12:00", "version": 1}),
            ):
                with self.subTest(token_case="missing" if not supplied else "invalid", path=path):
                    self.assertEqual(await client.request(method, path, body), 403)
                    self.assertEqual(client.data(), {"detail": "La solicitud no tiene un token CSRF válido."})
                    self.assertNotIn(b"set-cookie", client.headers)
                    self.assertEqual(await self.stored(client, domicile), before)
                    self.assertEqual(await client.request("GET", "/domiciles"), 200)
                    self.assertEqual(client.content, homes_before)
                    self.assertEqual(await client.request("GET", "/session"), 200)
        client.csrf = valid_csrf
        self.assertEqual(await client.request("POST", "/logout"), 204)
        self.assertEqual(await client.request("GET", "/session"), 401)

    async def test_date_mutations_versions_and_closure(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        cut = await self.cut(client, domicile, end=None)
        identifier = string(cut["id"])
        self.assertEqual(await client.request("PATCH", f"/interruptions/{identifier}", {**self.cut_input(end=None), "start_at": "2026-11-01T09:45", "version": 1}), 200)
        self.assertEqual(client.data()["version"], 2)
        opened = (await self.stored(client, domicile))[0]
        self.assertEqual(opened["id"], identifier)
        self.assertEqual(opened["start_at"], "2026-11-01T09:45:00-03:00")
        self.assertIsNone(opened["end_at"])
        self.assertEqual(opened["status"], "ongoing")
        self.assertEqual(await client.request("POST", f"/interruptions/{identifier}/close", {"end_at": "2026-11-01T12:00", "version": 1}), 409)
        self.assertEqual(await client.request("POST", f"/interruptions/{identifier}/close", {"end_at": "2026-11-01T12:00", "version": 2}), 200)
        current = version(client.data()["version"])
        self.assertEqual(await client.request("PATCH", f"/interruptions/{identifier}", {**self.cut_input("2026-11-01T10:15", "2026-11-01T11:45"), "version": current}), 200)
        current = version(client.data()["version"])
        corrected = (await self.stored(client, domicile))[0]
        self.assertEqual(corrected["id"], identifier)
        self.assertEqual(corrected["start_at"], "2026-11-01T10:15:00-03:00")
        self.assertEqual(corrected["end_at"], "2026-11-01T11:45:00-03:00")
        self.assertEqual(corrected["status"], "closed")
        self.assertEqual(corrected["version"], current)
        self.assertEqual(await client.request("PATCH", f"/interruptions/{identifier}", {**self.cut_input(end=None), "version": current}), 422)
        for start, end in (("2026-11-07T12:01", None), ("2026-11-01T10:00", "2026-11-07T12:01"), ("2026-11-01T10:00", "2026-11-01T10:00"), ("2026-11-01T10:00:01", None)):
            self.assertEqual(await client.request("POST", f"/domiciles/{domicile}/interruptions", self.cut_input(start, end)), 422)

    async def test_sqlalchemy_concurrent_update_does_not_overwrite(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        cut = await self.cut(client, domicile)
        with Session(self.engine) as first, Session(self.engine) as second:
            a = first.get(Interruption, string(cut["id"]))
            b = second.get(Interruption, string(cut["id"]))
            self.assertIsNotNone(a)
            self.assertIsNotNone(b)
            a.observations = "First writer"
            first.commit()
            b.observations = "Stale writer"
            with self.assertRaises(StaleDataError):
                second.commit()
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/interruptions"), 200)
        self.assertIn("First writer", client.content.decode())
        self.assertNotIn("Stale writer", client.content.decode())

    async def test_session_rotation_logout_and_expiry(self) -> None:
        client = await self.login()
        old_cookie = client.cookie
        self.assertEqual(await client.request("POST", "/login", {"username": self.username_a, "password": self.password}), 200)
        client.csrf = string(client.data()["csrf_token"])
        self.assertNotEqual(old_cookie, client.cookie)
        old = Client(cookie=old_cookie)
        self.assertEqual(await old.request("GET", "/session"), 401)
        cookie = client.cookie
        self.assertEqual(await client.request("POST", "/logout"), 204)
        self.assertEqual(await Client(cookie=cookie).request("GET", "/session"), 401)
        client = await self.login()
        with Session(self.engine) as db:
            rows = db.scalars(select(WebSession).where(WebSession.csrf_token == client.csrf))
            for row in rows:
                row.expires_at = datetime(2026, 11, 1, tzinfo=BUENOS_AIRES)
            db.commit()
        self.assertEqual(await client.request("GET", "/session"), 401)

    async def test_safe_failures_and_storage_free_health(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        with patch("app.api.render_pdf", side_effect=OSError("private renderer detail")):
            self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{self.period()}"), 503)
            self.assertNotIn("private renderer", client.content.decode())
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            self.assertEqual(await client.request("GET", "/health"), 200)
            self.assertEqual(client.content, b'{"status":"ok"}')
            self.assertEqual(await client.request("GET", "/domiciles"), 503)

    async def test_iso_transport_and_conversion_boundaries_are_sanitized_422(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        opened = await self.cut(client, domicile, end=None)
        before = await self.stored(client, domicile)
        for raw in (0, "0", "2026-11-01", "0001-01-01T00:00Z", "1969-12-31T23:59", "9999-12-31T23:59-12:00"):
            with self.subTest(raw=raw):
                body = {**self.cut_input(end=None), "start_at": raw}
                self.assertEqual(await client.request("POST", f"/domiciles/{domicile}/interruptions", body), 422)
                self.assertEqual(await client.request("PATCH", f"/interruptions/{opened['id']}", {**body, "version": 1}), 422)
                self.assertEqual(await client.request("POST", f"/interruptions/{opened['id']}/close", {"end_at": raw, "version": 1}), 422)
                query = urlencode({"period_start": raw, "period_end": "2026-11-02T00:00"})
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{query}"), 422)
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{query}"), 422)
                self.assertEqual(await self.stored(client, domicile), before)

    async def test_pre_1970_rejected_and_exact_boundary_round_trips(self) -> None:
        client = await self.login()
        domicile = await self.domicile(client)
        before = await self.stored(client, domicile)
        for raw, floor_error in (
            ("1969-12-31T23:59", True),
            ("1969-12-31T23:59:59-03:00", False),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(await client.request(
                    "POST",
                    f"/domiciles/{domicile}/interruptions",
                    self.cut_input(raw, "1970-01-01T01:00"),
                ), 422)
                detail = string(client.data()["detail"])
                self.assertNotIn(raw, detail)
                if floor_error:
                    self.assertIn("1970-01-01", detail)
                query = urlencode({"period_start": raw, "period_end": "1970-01-02T00:00"})
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{query}"), 422)
                self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{query}"), 422)
        self.assertEqual(await self.stored(client, domicile), before)
        boundary = await self.cut(client, domicile, "1970-01-01T00:00", "1970-01-01T01:00")
        self.assertEqual(boundary["start_at"], "1970-01-01T00:00:00-03:00")
        self.assertEqual(boundary["end_at"], "1970-01-01T01:00:00-03:00")
        self.assertEqual(await client.request(
            "PATCH",
            f"/interruptions/{string(boundary['id'])}",
            {**self.cut_input("1970-01-01T00:00", "1970-01-01T01:00"),
             "version": version(boundary["version"])},
        ), 200)
        query = urlencode({"period_start": "1970-01-01T00:00", "period_end": "1970-01-02T00:00"})
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/summary?{query}"), 200)
        self.assertEqual(client.data()["total_minutes"], 60)
        self.assertEqual(await client.request("GET", f"/domiciles/{domicile}/report.pdf?{query}"), 200)
        self.assertIn(b"pdf", client.headers[b"content-type"].lower())
        ongoing = await self.cut(client, domicile, "1970-01-02T00:00", None)
        self.assertEqual(await client.request(
            "POST",
            f"/interruptions/{string(ongoing['id'])}/close",
            {"end_at": "1970-01-02T00:30", "version": version(ongoing["version"])},
        ), 200)
        self.assertEqual(client.data()["end_at"], "1970-01-02T00:30:00-03:00")
        self.assertEqual(client.data()["status"], "closed")
        aware = await self.cut(
            client, domicile, "1969-12-31T23:00:00-04:00", "1970-01-01T01:00"
        )
        self.assertEqual(aware["start_at"], "1970-01-01T00:00:00-03:00")
