"""Synthetic CU05 ASGI/PostgreSQL tests; requires an isolated migrated database."""

import asyncio
import json
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier, Event, Timer
from unittest.mock import patch
from uuid import uuid4

import test_api
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.types import Message, Scope

from app import reading_api
from app.main import app
from app.models import Account
from app.reading_store import create_reading, prepare_creation, stage_creation


class ReadingClient(test_api.Client):
    async def reading_request(self, method: str, path: str, payload: object, key: str = "",
                              origin: str = "http://127.0.0.1:5173", raw: str | None = None) -> int:
        headers = [(b"content-type", b"application/json"), (b"origin", origin.encode())]
        if self.cookie:
            headers.append((b"cookie", self.cookie.encode()))
        if self.csrf:
            headers.append((b"x-csrf-token", self.csrf.encode()))
        if key:
            headers.append((b"idempotency-key", key.encode()))
        scope: Scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "method": method, "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": b"", "root_path": "",
            "headers": headers, "client": ("127.0.0.1", 1234), "server": ("test", 8000),
        }
        messages: list[Message] = []

        async def receive() -> Message:
            return {"type": "http.request", "body": (raw if raw is not None else json.dumps(payload)).encode(),
                    "more_body": False}

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        self.headers = dict(messages[0]["headers"])
        self.content = b"".join(message.get("body", b"") for message in messages[1:])
        return int(messages[0]["status"])


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ReadingPostgresTests(test_api.ApiTests):
    def setUp(self) -> None:
        super().setUp()
        clock = patch("app.reading_api.now", return_value=datetime(2026, 11, 7, 15, tzinfo=UTC))
        clock.start()
        self.addCleanup(clock.stop)

    async def prepare(self) -> tuple[ReadingClient, str]:
        owner = await self.login()
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        meter_id = test_api.string(owner.data()["id"])
        return ReadingClient(cookie=owner.cookie, csrf=owner.csrf), meter_id

    def payload(self, value: str = "9007199254740993", when: str = "2026-11-07T12:00:00-03:00") -> dict[str, object]:
        return {"recorded_at": when, "value_kwh": value, "confirmed": True, "photo_base64": None}

    async def test_create_replay_conflict_and_edit(self) -> None:
        owner, meter_id = await self.prepare()
        path, key = f"/meters/{meter_id}/readings", str(uuid4())
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), key), 201)
        original = owner.data()
        self.assertEqual(original["value_kwh"], "9007199254740993")
        self.assertEqual(original["recorded_at"], "2026-11-07T15:00:00Z")
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), key), 201)
        self.assertEqual(owner.data(), original)
        self.assertEqual(await owner.reading_request("POST", path, self.payload("2"), key), 409)
        self.assertEqual(owner.data()["code"], "IDEMPOTENCY_KEY_REUSED")
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), str(uuid4())), 409)
        self.assertEqual(owner.data()["code"], "DUPLICATE_READING")
        edit = {**self.payload("42"), "version": 1, "photo_action": "keep"}
        target = f"{path}/{original['id']}"
        self.assertEqual(await owner.reading_request("PATCH", target, edit), 200)
        self.assertEqual(owner.data()["version"], 2)
        self.assertEqual(await owner.reading_request("PATCH", target, edit), 409)
        self.assertEqual(owner.data()["code"], "VERSION_CONFLICT")
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), key), 201)
        self.assertEqual(owner.data(), original)

    async def test_foreign_and_invalid_input(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        other = await self.login(self.username_b)
        stranger = ReadingClient(cookie=other.cookie, csrf=other.csrf)
        self.assertEqual(await stranger.reading_request("POST", path, self.payload(), str(uuid4())), 404)
        self.assertEqual(await owner.reading_request("POST", path, self.payload("-1"), str(uuid4())), 422)
        self.assertEqual(await owner.reading_request("POST", path,
                                                    {**self.payload(), "confirmed": 1}, str(uuid4())), 422)
        self.assertEqual(await owner.reading_request("POST", path, self.payload(when="2026-11-07T15:00:01Z"), str(uuid4())), 422)
        without_csrf = ReadingClient(cookie=owner.cookie)
        self.assertEqual(await without_csrf.reading_request("POST", path, self.payload(), str(uuid4())), 403)
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), str(uuid4()),
                                                     origin="https://foreign.invalid"), 403)
        self.assertEqual(await owner.reading_request("POST", path, self.payload(when="\ud800"), str(uuid4())), 422)
        self.assertEqual(await owner.reading_request("POST", path,
                                                    {**self.payload(), "photo_base64": "c3ludGhldGlj"},
                                                    str(uuid4())), 422)
        self.assertEqual(await owner.reading_request("POST", path, None, str(uuid4()),
                                                     raw="[" * 1100 + "0" + "]" * 1100), 422)
        self.assertEqual(owner.headers.get(b"cache-control"), b"no-store")
        self.assertEqual(await owner.reading_request("GET", path, None), 200)
        self.assertEqual(json.loads(owner.content), [])

    async def test_concurrent_identical_attempts_replay(self) -> None:
        owner, meter_id = await self.prepare()
        path, key, gate = f"/meters/{meter_id}/readings", str(uuid4()), Barrier(2)

        def execute() -> tuple[int, dict[str, object]]:
            client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
            gate.wait(timeout=10)
            status = asyncio.run(client.reading_request("POST", path, self.payload(), key))
            return status, client.data()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = await asyncio.gather(loop.run_in_executor(executor, execute),
                                                 loop.run_in_executor(executor, execute))
        self.assertEqual((first[0], second[0]), (201, 201))
        self.assertEqual(first[1], second[1])

    async def test_concurrent_distinct_keys_and_concurrent_patch(self) -> None:
        owner, meter_id = await self.prepare()
        path, gate = f"/meters/{meter_id}/readings", Barrier(2)

        def create() -> tuple[int, dict[str, object]]:
            client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
            gate.wait(timeout=10)
            status = asyncio.run(client.reading_request("POST", path, self.payload(), str(uuid4())))
            return status, client.data()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = await asyncio.gather(loop.run_in_executor(executor, create),
                                                 loop.run_in_executor(executor, create))
        self.assertCountEqual([first[0], second[0]], [201, 409])
        original = first[1] if first[0] == 201 else second[1]
        target = f"{path}/{original['id']}"
        gate = Barrier(2)

        def edit(value: str) -> tuple[int, dict[str, object]]:
            client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
            gate.wait(timeout=10)
            status = asyncio.run(client.reading_request("PATCH", target,
                                 {**self.payload(value), "version": 1, "photo_action": "keep"}))
            return status, client.data()

        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = await asyncio.gather(loop.run_in_executor(executor, edit, "5"),
                                                 loop.run_in_executor(executor, edit, "6"))
        self.assertCountEqual([first[0], second[0]], [200, 409])
        self.assertEqual(await owner.reading_request("GET", target, None), 200)
        self.assertEqual(owner.data()["version"], 2)

    async def test_rollback_releases_creation_attempt(self) -> None:
        owner, meter_id = await self.prepare()
        key = str(uuid4())
        with Session(self.engine) as db:
            account = db.scalar(select(Account).where(Account.username == self.username_a))
            assert account is not None
            create_reading(db, account_id=account.id, meter_id=meter_id, key=key,
                           recorded_at="2026-11-07T12:00:00-03:00", value_kwh="1",
                           photo=None, photo_key=None, photo_type=None,
                           now=datetime(2026, 11, 7, 15, tzinfo=UTC))
            db.rollback()
        self.assertEqual(await owner.reading_request("POST", f"/meters/{meter_id}/readings",
                                                     self.payload("1"), key), 201)

    async def test_creation_prepare_rejects_nested_transaction(self) -> None:
        _, meter_id = await self.prepare()
        with Session(self.engine) as db:
            account = db.scalar(select(Account).where(Account.username == self.username_a))
            assert account is not None
            with db.begin_nested():
                with self.assertRaises(RuntimeError):
                    prepare_creation(
                        db, account_id=account.id, meter_id=meter_id, key=str(uuid4()),
                        recorded_at="2026-11-07T12:00:00-03:00", value_kwh="1", photo=None,
                    )

    async def test_creation_stage_rejects_savepoint_after_prepare(self) -> None:
        _, meter_id = await self.prepare()
        with Session(self.engine) as db:
            account = db.scalar(select(Account).where(Account.username == self.username_a))
            assert account is not None
            prepared, replay = prepare_creation(
                db, account_id=account.id, meter_id=meter_id, key=str(uuid4()),
                recorded_at="2026-11-07T12:00:00-03:00", value_kwh="1", photo=None,
            )
            self.assertIsNone(replay)
            with db.begin_nested():
                with self.assertRaises(RuntimeError):
                    stage_creation(db, prepared=prepared, photo_key=None, photo_type=None,
                                   now=datetime(2026, 11, 7, 15, tzinfo=UTC))

    async def test_creation_prepare_rejects_external_connection_savepoint(self) -> None:
        _, meter_id = await self.prepare()
        with self.engine.connect() as connection:
            with connection.begin():
                with connection.begin_nested():
                    with Session(bind=connection) as db:
                        account = db.scalar(select(Account).where(Account.username == self.username_a))
                        assert account is not None
                        with self.assertRaises(RuntimeError):
                            prepare_creation(
                                db, account_id=account.id, meter_id=meter_id, key=str(uuid4()),
                                recorded_at="2026-11-07T12:00:00-03:00", value_kwh="1", photo=None,
                            )

    async def test_creation_stage_rejects_external_root_rollback(self) -> None:
        _, meter_id = await self.prepare()
        with self.engine.connect() as connection:
            transaction = connection.begin()
            with Session(bind=connection) as db:
                account = db.scalar(select(Account).where(Account.username == self.username_a))
                assert account is not None
                prepared, replay = prepare_creation(
                    db, account_id=account.id, meter_id=meter_id, key=str(uuid4()),
                    recorded_at="2026-11-07T12:00:00-03:00", value_kwh="1", photo=None,
                )
                self.assertIsNone(replay)
                transaction.rollback()
                with self.assertRaisesRegex(RuntimeError, "Creation transaction changed before staging"):
                    stage_creation(db, prepared=prepared, photo_key=None, photo_type=None,
                                   now=datetime(2026, 11, 7, 15, tzinfo=UTC))

    async def test_concurrent_key_reuse_with_different_payloads(self) -> None:
        owner, meter_id = await self.prepare()
        path, gate, key = f"/meters/{meter_id}/readings", Barrier(2), str(uuid4())

        def create(value: str) -> tuple[int, dict[str, object]]:
            client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
            gate.wait(timeout=10)
            status = asyncio.run(client.reading_request("POST", path, self.payload(value), key))
            return status, client.data()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = await asyncio.gather(loop.run_in_executor(executor, create, "1"),
                                                 loop.run_in_executor(executor, create, "2"))
        self.assertCountEqual([first[0], second[0]], [201, 409])
        conflict = first[1] if first[0] == 409 else second[1]
        self.assertEqual(conflict["code"], "IDEMPOTENCY_KEY_REUSED")

    async def test_foreign_and_mismatched_detail_and_edit(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        self.assertEqual(await owner.reading_request("POST", path, self.payload(), str(uuid4())), 201)
        reading_id = owner.data()["id"]
        other = await self.login(self.username_b)
        stranger = ReadingClient(cookie=other.cookie, csrf=other.csrf)
        edit = {**self.payload("2"), "version": 1, "photo_action": "keep"}
        for method, target, client in (
            ("GET", f"{path}/{reading_id}", stranger),
            ("PATCH", f"{path}/{reading_id}", stranger),
            ("GET", f"{path}/{uuid4()}", owner),
            ("PATCH", f"{path}/{uuid4()}", owner),
        ):
            self.assertEqual(await client.reading_request(method, target, edit), 404)
            self.assertEqual(client.data()["detail"], "El recurso no está disponible.")

    async def test_history_is_descending_edit_keeps_meter_and_deletion_unavailable(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        older = self.payload("100", "2026-11-06T15:00:00Z")
        newer = self.payload("90", "2026-11-07T15:00:00Z")
        self.assertEqual(await owner.reading_request("POST", path, older, str(uuid4())), 201)
        older_id = owner.data()["id"]
        self.assertEqual(await owner.reading_request("POST", path, newer, str(uuid4())), 201)
        newer_id = owner.data()["id"]
        self.assertEqual(await owner.reading_request("GET", path, None), 200)
        rows = json.loads(owner.content)
        self.assertEqual([row["id"] for row in rows], [newer_id, older_id])
        target = f"{path}/{older_id}"
        self.assertEqual(await owner.reading_request("PATCH", target,
                         {**older, "version": 1, "photo_action": "keep"}), 200)
        self.assertEqual(owner.data()["meter_id"], meter_id)
        self.assertEqual(owner.data()["version"], 2)
        self.assertEqual(await owner.reading_request("DELETE", target, None), 405)
        self.assertEqual(await owner.reading_request("GET", target, None), 200)
        self.assertEqual(owner.data()["version"], 2)

    async def test_advisory_lock_wait_does_not_block_event_loop(self) -> None:
        owner, meter_id = await self.prepare()
        key, ready, release, entered = str(uuid4()), Event(), Event(), Event()
        holder_pid: list[int] = []
        with Session(self.engine) as db:
            account = db.scalar(select(Account).where(Account.username == self.username_a))
            assert account is not None
            scope = f"cu05:{account.id}:{meter_id}:{key}"

        def hold_lock() -> None:
            with self.engine.begin() as connection:
                pid = connection.scalar(text("SELECT pg_backend_pid()"))
                assert isinstance(pid, int)
                holder_pid.append(pid)
                connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                                   {"scope": scope})
                ready.set()
                release.wait(timeout=10)

        original = reading_api._post_reading

        def mark_entry(*args: object, **kwargs: object) -> object:
            entered.set()
            return original(*args, **kwargs)

        def wait_for_database_waiter() -> bool:
            deadline = time.monotonic() + 5
            with self.engine.connect() as connection:
                while time.monotonic() < deadline:
                    waiting = connection.scalar(text(
                        "SELECT EXISTS (SELECT 1 FROM pg_locks "
                        "WHERE locktype = 'advisory' AND NOT granted "
                        "AND :holder = ANY (pg_blocking_pids(pid)))"
                    ), {"holder": holder_pid[0]})
                    if waiting:
                        return True
                    release.wait(timeout=0.02)
            return False

        watchdog = Timer(10, release.set)
        watchdog.start()
        holder = asyncio.create_task(asyncio.to_thread(hold_lock))
        try:
            self.assertTrue(await asyncio.to_thread(ready.wait, 5))
            with patch("app.reading_api._post_reading", side_effect=mark_entry):
                request = asyncio.create_task(owner.reading_request("POST", f"/meters/{meter_id}/readings",
                                                                    self.payload(), key))
                self.assertTrue(await asyncio.to_thread(entered.wait, 5))
                self.assertTrue(await asyncio.to_thread(wait_for_database_waiter))
                self.assertFalse(request.done())
                health = ReadingClient()
                self.assertEqual(await asyncio.wait_for(health.reading_request("GET", "/health", None), 2), 200)
                release.set()
                self.assertEqual(await asyncio.wait_for(request, 5), 201)
        finally:
            release.set()
            watchdog.cancel()
            await holder
