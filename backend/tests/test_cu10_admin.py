"""CU10 admin persistence, authorization, configuration and retry tests."""

import json
import os
import threading
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.types import Message, Scope

from app import assistant_tools, promote, source_config
from app.enre_client import EnreTimeout, FetchedFeed
from app.enre_parser import parse_feed
from app.main import app, next_interval, run_cycle
from app.models import (
    Account,
    OutageFetchRun,
    OutageReport,
    OutageSnapshot,
    ScheduledFetchRun,
    ScheduledSnapshot,
    ScheduledWork,
    SourceConfig,
    WebSession,
)
from app.outage_store import _store_snapshot
from app.security import hash_password

FEED = (Path(__file__).parent / "fixtures" / "enre_data_eds_redacted.js").read_text(
    encoding="utf-8",
)
SCHEDULED_FEED = (
    Path(__file__).parent / "fixtures" / "enre_data_eds_scheduled.js"
).read_text(encoding="utf-8")
OUTAGE_LOCK = 0x43553031


def string(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("Expected a string")
    return value


@dataclass
class Client:
    cookie: str = ""
    csrf: str = ""
    headers: dict[bytes, bytes] = field(default_factory=dict)
    content: bytes = b""

    async def request(
        self, method: str, path: str, payload: object = None,
        *, csrf: bool = True, origin: str = "http://127.0.0.1:5173",
    ) -> int:
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
            return {
                "type": "http.request", "body": json.dumps(payload).encode(),
                "more_body": False,
            }

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        self.headers = dict(messages[0]["headers"])
        self.content = b"".join(message.get("body", b"") for message in messages[1:])
        if b"set-cookie" in self.headers:
            raw = self.headers[b"set-cookie"].decode()
            self.cookie = raw.split(";", 1)[0]
        return int(messages[0]["status"])


class SourceConfigUnitTests(unittest.TestCase):
    def test_allowed_intervals(self) -> None:
        self.assertEqual(
            source_config.ALLOWED_INTERVALS,
            frozenset({300, 600, 900, 1800, 3600}),
        )
        self.assertFalse(source_config.is_allowed(301))

    def test_get_interval_falls_back_on_database_error(self) -> None:
        with patch("app.source_config.get_engine", side_effect=RuntimeError("down")):
            self.assertEqual(source_config.get_interval("outages"), 300)


class AssistantToolTests(unittest.TestCase):
    def test_no_admin_capability_is_exposed(self) -> None:
        names = {tool.name for tool in assistant_tools.TOOLS}
        self.assertEqual(names, {"current_outages", "scheduled_works"})
        self.assertFalse(any(
            word in name for name in names for word in ("admin", "refresh", "interval")
        ))


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class DatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.url,
            "OUTAGE_SCHEDULER_ENABLED": "false",
            "SCHEDULED_WORKS_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.execute(delete(ScheduledFetchRun))
            db.execute(delete(SourceConfig))
            db.add_all([
                SourceConfig(source_key="outages", interval_seconds=300, version=1),
                SourceConfig(source_key="scheduled_works", interval_seconds=300, version=1),
            ])
            db.commit()


class MigrationAndRoleTests(DatabaseTestCase):
    def test_seeded_configuration_rows(self) -> None:
        with Session(self.engine) as db:
            rows = {
                row.source_key: (row.interval_seconds, row.version)
                for row in db.scalars(select(SourceConfig))
            }
        self.assertEqual(rows, {"outages": (300, 1), "scheduled_works": (300, 1)})

    def test_account_role_defaults_to_user_and_rejects_unknown(self) -> None:
        username = f"cu10-role-{uuid4()}"
        with Session(self.engine) as db:
            account = Account(username=username, password_hash=hash_password("synthetic"))
            db.add(account)
            db.commit()
            db.refresh(account)
            self.assertEqual(account.role, "user")
            account_id = account.id
        with Session(self.engine) as db:
            with self.assertRaises(IntegrityError):
                db.execute(
                    text("UPDATE es_accounts SET role='super' WHERE id=:id"),
                    {"id": account_id},
                )
            db.rollback()
        with Session(self.engine) as db:
            db.execute(delete(Account).where(Account.id == account_id))
            db.commit()


class PromoteTests(DatabaseTestCase):
    def _account(self, username: str) -> tuple[str, str]:
        with Session(self.engine) as db:
            account = Account(username=username, password_hash=hash_password("synthetic"))
            db.add(account)
            db.commit()
            return account.id, account.password_hash

    def test_promote_existing_account_only_changes_role(self) -> None:
        username = f"cu10-promote-{uuid4()}"
        account_id, original_hash = self._account(username)
        with patch("sys.argv", ["promote", "--username", username]):
            self.assertEqual(promote.main(), 0)
        with Session(self.engine) as db:
            account = db.get(Account, account_id)
            assert account is not None
            self.assertEqual(account.role, "admin")
            self.assertEqual(account.password_hash, original_hash)
            db.execute(delete(Account).where(Account.id == account_id))
            db.commit()

    def test_missing_account_fails_without_creating(self) -> None:
        username = f"cu10-missing-{uuid4()}"
        with patch("sys.argv", ["promote", "--username", username]):
            self.assertEqual(promote.main(), 1)
        with Session(self.engine) as db:
            self.assertIsNone(
                db.scalar(select(Account).where(Account.username == username)),
            )

    def test_missing_username_exits(self) -> None:
        with patch("sys.argv", ["promote"]):
            with self.assertRaises(SystemExit):
                promote.main()


class SourceConfigPostgresTests(DatabaseTestCase):
    def test_get_and_set_interval_per_source(self) -> None:
        self.assertEqual(source_config.get_interval("outages"), 300)
        with Session(self.engine) as db:
            row = source_config.set_interval(db, "outages", 600, 1)
            self.assertEqual((row.interval_seconds, row.version), (600, 2))
        self.assertEqual(source_config.get_interval("outages"), 600)
        self.assertEqual(source_config.get_interval("scheduled_works"), 300)

    def test_stale_version_conflicts_without_overwrite(self) -> None:
        with Session(self.engine) as db:
            source_config.set_interval(db, "outages", 600, 1)
        with Session(self.engine) as db:
            with self.assertRaises(source_config.VersionConflict):
                source_config.set_interval(db, "outages", 900, 1)
        self.assertEqual(source_config.get_interval("outages"), 600)

    def test_invalid_interval_is_rejected(self) -> None:
        with Session(self.engine) as db:
            with self.assertRaises(source_config.InvalidInterval):
                source_config.set_interval(db, "outages", 999, 1)

    def test_missing_row_falls_back_to_default(self) -> None:
        with Session(self.engine) as db:
            db.execute(delete(SourceConfig).where(SourceConfig.source_key == "outages"))
            db.commit()
        self.assertEqual(source_config.get_interval("outages"), 300)
        with Session(self.engine) as db:
            db.add(SourceConfig(source_key="outages", interval_seconds=300, version=1))
            db.commit()

    def test_concurrent_updates_only_one_wins(self) -> None:
        barrier = threading.Barrier(2)
        results: list[tuple[str, int | None]] = []

        def worker(value: int) -> None:
            with Session(self.engine) as db:
                barrier.wait()
                try:
                    row = source_config.set_interval(db, "outages", value, 1)
                    results.append(("ok", row.interval_seconds))
                except source_config.VersionConflict:
                    results.append(("conflict", None))

        threads = [
            threading.Thread(target=worker, args=(value,)) for value in (600, 900)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(1 for result in results if result[0] == "ok"), 1)
        self.assertEqual(sum(1 for result in results if result[0] == "conflict"), 1)
        with Session(self.engine) as db:
            row = db.get(SourceConfig, "outages")
            assert row is not None
            self.assertEqual(row.version, 2)
            winner = next(value for state, value in results if state == "ok")
            self.assertEqual(row.interval_seconds, winner)


class SchedulerIntervalTests(DatabaseTestCase):
    def test_next_interval_reads_the_current_value(self) -> None:
        with Session(self.engine) as db:
            source_config.set_interval(db, "outages", 600, 1)
        self.assertEqual(next_interval("outages"), 600)

    def test_next_cycle_reads_the_new_interval_without_restart(self) -> None:
        # Controlled timing check: the same process reads the DB again, so a PATCH
        # applies at the next cycle without a backend restart or a wall-clock wait.
        self.assertEqual(next_interval("outages"), 300)
        with Session(self.engine) as db:
            source_config.set_interval(db, "outages", 600, 1)
        self.assertEqual(next_interval("outages"), 600)

    def test_next_interval_falls_back_on_read_failure(self) -> None:
        with patch("app.main.source_config.get_interval", side_effect=RuntimeError("x")):
            self.assertEqual(next_interval("outages"), 300)


class SchedulerCycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_cycle_reads_interval_and_survives_refresh_failure(self) -> None:
        with patch("app.main.next_interval", return_value=600):
            self.assertEqual(await run_cycle("outages", lambda: "ok"), 600)
        with patch("app.main.next_interval", return_value=300):
            def boom() -> str:
                raise RuntimeError("synthetic")
            self.assertEqual(await run_cycle("outages", boom), 300)

    async def test_second_cycle_uses_the_changed_interval(self) -> None:
        # The loop calls run_cycle again for the next cycle; a PATCH is re-read
        # without a restart or a wall-clock wait.
        values = iter([300, 600])
        with patch("app.main.next_interval", side_effect=lambda _key: next(values)):
            first = await run_cycle("outages", lambda: "ok")
            second = await run_cycle("outages", lambda: "ok")
        self.assertEqual((first, second), (300, 600))


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class AdminApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)
        cls.password = "Synthetic-only-cu10-password"
        cls.admin_user = f"cu10-admin-{uuid4()}"
        cls.user_user = f"cu10-user-{uuid4()}"
        with Session(cls.engine) as db:
            db.add_all([
                Account(
                    username=cls.admin_user,
                    password_hash=hash_password(cls.password),
                    role="admin",
                ),
                Account(
                    username=cls.user_user,
                    password_hash=hash_password(cls.password),
                    role="user",
                ),
            ])
            db.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        with Session(cls.engine) as db:
            account_ids = list(db.scalars(select(Account.id).where(
                Account.username.in_([cls.admin_user, cls.user_user]),
            )))
            if account_ids:
                db.execute(delete(WebSession).where(
                    WebSession.account_id.in_(account_ids),
                ))
                db.execute(delete(Account).where(Account.id.in_(account_ids)))
            db.commit()
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.url,
            "OUTAGE_SCHEDULER_ENABLED": "false",
            "SCHEDULED_WORKS_SCHEDULER_ENABLED": "true",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.execute(delete(ScheduledFetchRun))
            db.execute(delete(SourceConfig))
            db.add_all([
                SourceConfig(source_key="outages", interval_seconds=300, version=1),
                SourceConfig(source_key="scheduled_works", interval_seconds=300, version=1),
            ])
            db.commit()

    async def login(self, username: str) -> Client:
        client = Client()
        status = await client.request("POST", "/login", {
            "username": username, "password": self.password,
        })
        self.assertEqual(status, 200)
        client.csrf = string(json.loads(client.content)["csrf_token"])
        return client

    async def test_unauthenticated_is_401_and_non_admin_is_403(self) -> None:
        calls = [
            ("GET", "/admin/sources", None),
            ("POST", "/admin/sources/outages/refresh", None),
            ("PATCH", "/admin/sources/outages/interval",
             {"interval_seconds": 600, "version": 1}),
        ]
        anonymous = Client()
        for method, path, payload in calls:
            self.assertEqual(await anonymous.request(method, path, payload), 401)
        user = await self.login(self.user_user)
        for method, path, payload in calls:
            self.assertEqual(await user.request(method, path, payload), 403)

    async def test_status_reports_real_state(self) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            _store_snapshot(db, parse_feed(FEED), now, "a" * 64, now)
            db.add(OutageFetchRun(
                started_at=now, finished_at=now, outcome="ok", http_status=200,
                detail_code=None, content_sha256="a" * 64,
            ))
            db.add(ScheduledFetchRun(
                started_at=now + timedelta(seconds=1),
                finished_at=now + timedelta(seconds=1), outcome="timeout",
                http_status=None, detail_code="EnreTimeout", content_sha256=None,
            ))
            db.add(ScheduledFetchRun(
                started_at=now, finished_at=now, outcome="skipped_locked",
                http_status=None, detail_code=None, content_sha256=None,
            ))
            db.commit()
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request("GET", "/admin/sources"), 200)
        sources = {
            row["key"]: row for row in json.loads(admin.content)["sources"]
        }
        self.assertEqual(set(sources), {"outages", "scheduled_works"})
        outages = sources["outages"]
        self.assertFalse(outages["scheduler_enabled"])
        self.assertEqual(outages["interval_seconds"], 300)
        self.assertEqual(outages["version"], 1)
        self.assertEqual(outages["last_attempt_outcome"], "ok")
        self.assertIsNotNone(outages["last_success_at"])
        self.assertIsNone(outages["last_attempt_error"])
        scheduled = sources["scheduled_works"]
        self.assertTrue(scheduled["scheduler_enabled"])
        self.assertEqual(scheduled["last_attempt_outcome"], "timeout")
        self.assertEqual(scheduled["last_attempt_error"], "EnreTimeout")
        self.assertIsNone(scheduled["last_success_at"])
        self.assertIsNotNone(scheduled["last_skipped_locked_at"])
        self.assertEqual(admin.headers.get(b"cache-control"), b"no-store")

    async def test_interval_valid_invalid_and_stale(self) -> None:
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 600, "version": 1},
        ), 200)
        self.assertEqual(json.loads(admin.content), {
            "key": "outages", "interval_seconds": 600, "version": 2,
        })
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 999, "version": 2},
        ), 422)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 900, "version": 1},
        ), 409)
        self.assertEqual(json.loads(admin.content)["code"], "VERSION_CONFLICT")
        with Session(self.engine) as db:
            outages = db.get(SourceConfig, "outages")
            scheduled = db.get(SourceConfig, "scheduled_works")
            assert outages is not None and scheduled is not None
            self.assertEqual(outages.interval_seconds, 600)
            self.assertEqual(scheduled.interval_seconds, 300)

    async def test_mutations_require_csrf_and_trusted_origin(self) -> None:
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 600, "version": 1}, csrf=False,
        ), 403)
        self.assertEqual(await admin.request(
            "POST", "/admin/sources/outages/refresh", None, csrf=False,
        ), 403)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 600, "version": 1},
            origin="http://untrusted.example",
        ), 403)
        with Session(self.engine) as db:
            row = db.get(SourceConfig, "outages")
            assert row is not None
            self.assertEqual(row.interval_seconds, 300)

    async def test_refresh_success_then_failure_preserves_last_success(self) -> None:
        now = datetime.now(UTC)
        admin = await self.login(self.admin_user)
        with patch("app.outage_store.fetch_feed", return_value=FetchedFeed(
            text=FEED, last_modified=now, status=200,
        )):
            self.assertEqual(await admin.request(
                "POST", "/admin/sources/outages/refresh",
            ), 200)
        self.assertIn(json.loads(admin.content)["outcome"], {"ok", "not_modified"})
        self.assertEqual(await admin.request("GET", "/admin/sources"), 200)
        first = {row["key"]: row for row in json.loads(admin.content)["sources"]}
        success = first["outages"]["last_success_at"]
        self.assertIsNotNone(success)
        with patch("app.outage_store.fetch_feed", side_effect=EnreTimeout("slow")):
            self.assertEqual(await admin.request(
                "POST", "/admin/sources/outages/refresh",
            ), 200)
        failed = json.loads(admin.content)
        self.assertEqual(failed["outcome"], "timeout")
        self.assertEqual(failed["detail_code"], "EnreTimeout")
        self.assertEqual(await admin.request("GET", "/admin/sources"), 200)
        after = {row["key"]: row for row in json.loads(admin.content)["sources"]}
        self.assertEqual(after["outages"]["last_success_at"], success)
        self.assertEqual(after["outages"]["last_attempt_outcome"], "timeout")

    async def test_refresh_busy_returns_409_without_recording_a_run(self) -> None:
        admin = await self.login(self.admin_user)
        with Session(self.engine) as db:
            before = db.scalar(select(func.count()).select_from(OutageFetchRun))
        with self.engine.connect() as lock:
            acquired = lock.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": OUTAGE_LOCK},
            ).scalar_one()
            self.assertTrue(acquired)
            lock.commit()
            try:
                self.assertEqual(await admin.request(
                    "POST", "/admin/sources/outages/refresh",
                ), 409)
                self.assertEqual(json.loads(admin.content)["code"], "SOURCE_BUSY")
            finally:
                lock.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": OUTAGE_LOCK},
                )
                lock.commit()
        with Session(self.engine) as db:
            after = db.scalar(select(func.count()).select_from(OutageFetchRun))
        self.assertEqual(before, after)

    async def test_login_and_session_expose_role(self) -> None:
        user = await self.login(self.user_user)
        self.assertEqual(json.loads(user.content)["account"]["role"], "user")
        admin = await self.login(self.admin_user)
        self.assertEqual(json.loads(admin.content)["account"]["role"], "admin")
        self.assertEqual(await admin.request("GET", "/session"), 200)
        self.assertEqual(json.loads(admin.content)["account"]["role"], "admin")

    async def test_status_read_needs_no_csrf(self) -> None:
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "GET", "/admin/sources", csrf=False,
        ), 200)

    async def test_conflict_envelopes_include_code_and_no_store(self) -> None:
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 600, "version": 2},
        ), 409)
        self.assertEqual(json.loads(admin.content)["code"], "VERSION_CONFLICT")
        self.assertEqual(admin.headers.get(b"cache-control"), b"no-store")
        with self.engine.connect() as lock:
            lock.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": OUTAGE_LOCK},
            ).scalar_one()
            lock.commit()
            try:
                self.assertEqual(await admin.request(
                    "POST", "/admin/sources/outages/refresh",
                ), 409)
                self.assertEqual(json.loads(admin.content)["code"], "SOURCE_BUSY")
                self.assertEqual(admin.headers.get(b"cache-control"), b"no-store")
            finally:
                lock.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": OUTAGE_LOCK},
                )
                lock.commit()

    async def test_sources_retry_independently(self) -> None:
        admin = await self.login(self.admin_user)
        now = datetime.now(UTC)
        with self.engine.connect() as lock:
            self.assertTrue(lock.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": OUTAGE_LOCK},
            ).scalar_one())
            lock.commit()
            try:
                with patch("app.scheduled_store.fetch_feed", return_value=FetchedFeed(
                    text=SCHEDULED_FEED, last_modified=now, status=200,
                )):
                    self.assertEqual(await admin.request(
                        "POST", "/admin/sources/scheduled_works/refresh",
                    ), 200)
                self.assertIn(
                    json.loads(admin.content)["outcome"], {"ok", "not_modified"},
                )
            finally:
                lock.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": OUTAGE_LOCK},
                )
                lock.commit()

    async def test_login_and_interval_reject_role_fields(self) -> None:
        client = Client()
        self.assertEqual(await client.request("POST", "/login", {
            "username": self.admin_user, "password": self.password, "role": "admin",
        }), 422)
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/outages/interval",
            {"interval_seconds": 600, "version": 1, "role": "admin"},
        ), 422)
        with Session(self.engine) as db:
            row = db.get(SourceConfig, "outages")
            assert row is not None
            self.assertEqual(row.interval_seconds, 300)

    async def test_unknown_source_returns_404(self) -> None:
        admin = await self.login(self.admin_user)
        self.assertEqual(await admin.request(
            "POST", "/admin/sources/other/refresh", None,
        ), 404)
        self.assertEqual(await admin.request(
            "PATCH", "/admin/sources/other/interval",
            {"interval_seconds": 600, "version": 1},
        ), 404)
