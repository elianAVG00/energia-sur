"""CU02 scheduled-works parser, persistence, concurrency and public API tests."""

import hashlib
import json
import os
import threading
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

import httpx
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session
from starlette.types import Message, Scope

from app.db import DatabaseUnavailable
from app.enre_client import FetchedFeed
from app.main import app
from app.models import ScheduledFetchRun, ScheduledSnapshot, ScheduledWork
from app.scheduled_api import _state
from app.scheduled_parser import (
    ScheduledParseError,
    ScheduledSchemaError,
    parse_scheduled,
)
from app.scheduled_store import (
    _prune,
    _store_snapshot,
    current_snapshot,
    record_run,
    refresh_once,
)

FIXTURES = Path(__file__).parent / "fixtures"
FEED = (FIXTURES / "enre_data_eds_scheduled.js").read_text(encoding="utf-8")
DATED = (FIXTURES / "enre_data_eds_scheduled_dated.js").read_text(encoding="utf-8")
EMPTY = """var data = {empresa: 'EDESUR', ultimaActualizacion: '--:--',
cortesProgramados: [], cortesComunicados: []}"""
SENTINEL_TOTAL = FEED.replace("totalUsuariosSinSuministro: '7.233'",
                              "totalUsuariosSinSuministro: 'N/A'")
WITH_COMUNICADOS = FEED.replace(
    "cortesComunicados:  [],",
    "cortesComunicados:  [{fecha: '2026-11-11 08:00', partido: 'GLEW', localidad: 'GLEW'}],",
)


class ParserTests(unittest.TestCase):
    def test_live_capture_parses_only_maintenance_works(self) -> None:
        feed = parse_scheduled(FEED)
        self.assertEqual(feed.distributor, "EDESUR")
        self.assertEqual(feed.source_reported_time, "11:05")
        self.assertFalse(feed.comunicados_present)
        self.assertEqual(feed.row_counts, {"maintenance": 4, "comunicados": 0})
        self.assertEqual(len(feed.rows), 4)
        self.assertEqual({row.category for row in feed.rows}, {"maintenance"})
        first = feed.rows[0]
        self.assertEqual(first.partido, "ALMIRANTE BROWN")
        self.assertEqual(first.localidad, "GLEW")
        self.assertEqual(first.affected_users, 2742)
        self.assertEqual(first.restoration_estimate_text, "Sin datos")
        self.assertEqual(first.partido_key, "almirante brown")

    def test_archived_full_datetime_is_kept_verbatim(self) -> None:
        feed = parse_scheduled(DATED)
        self.assertEqual(len(feed.rows), 1)
        self.assertEqual(feed.source_reported_time, "13:15")
        self.assertEqual(feed.rows[0].localidad, "AVELLANEDA")
        self.assertEqual(feed.rows[0].restoration_estimate_text, "2026-01-14 15:33")

    def test_comunicados_are_counted_but_not_emitted(self) -> None:
        feed = parse_scheduled(WITH_COMUNICADOS)
        self.assertTrue(feed.comunicados_present)
        self.assertEqual(feed.row_counts["comunicados"], 1)
        self.assertIn("cortesComunicados", feed.unverified_collections)
        self.assertEqual(len(feed.rows), 4)
        self.assertEqual({row.category for row in feed.rows}, {"maintenance"})

    def test_missing_or_non_list_comunicados_is_flagged_without_failing(self) -> None:
        missing = parse_scheduled(FEED.replace("cortesComunicados:  [],", ""))
        self.assertFalse(missing.comunicados_present)
        self.assertIn("cortesComunicados", missing.unverified_collections)
        self.assertEqual(len(missing.rows), 4)
        null = parse_scheduled(FEED.replace("cortesComunicados:  [],",
                                            "cortesComunicados:  null,"))
        self.assertFalse(null.comunicados_present)
        self.assertIn("cortesComunicados", null.unverified_collections)
        self.assertEqual(len(null.rows), 4)

    def test_missing_programados_fails_closed(self) -> None:
        with self.assertRaises(ScheduledSchemaError):
            parse_scheduled(FEED.replace(
                "cortesProgramados:  [{partido: 'ALMIRANTE BROWN',",
                "cortesProgramadosOmitted:  [{partido: 'ALMIRANTE BROWN',",
            ))
        with self.assertRaises(ScheduledSchemaError):
            parse_scheduled(FEED.replace(
                "cortesProgramados:  [{",
                "cortesProgramados:  null, ignored: [{",
            ))

    def test_invalid_rows_and_distributor(self) -> None:
        with self.assertRaises(ScheduledSchemaError):
            parse_scheduled(FEED.replace(
                "partido: 'ALMIRANTE BROWN',localidad: 'GLEW',", ""))
        with self.assertRaises(ScheduledSchemaError):
            parse_scheduled(FEED.replace("usuarios: '2742'", "usuarios: 'many'"))
        with self.assertRaises(ScheduledSchemaError):
            parse_scheduled(FEED.replace("empresa: 'EDESUR'", "empresa: 'EDENOR'"))
        with self.assertRaises(ScheduledParseError):
            parse_scheduled("<html>not the feed</html>")

    def test_empty_feed_and_sentinel_total(self) -> None:
        empty = parse_scheduled(EMPTY)
        self.assertEqual(empty.rows, ())
        self.assertIsNone(empty.source_reported_time)
        self.assertEqual(empty.row_counts["maintenance"], 0)
        sentinel = parse_scheduled(SENTINEL_TOTAL)
        self.assertEqual(len(sentinel.rows), 4)

    def test_count_sentinels_and_thousands(self) -> None:
        thousands = parse_scheduled(FEED.replace("usuarios: '2742'", "usuarios: '1.234'"))
        self.assertEqual(thousands.rows[0].affected_users, 1234)
        missing = parse_scheduled(FEED.replace("usuarios: '2742'",
                                               "usuarios: 'Sin datos'"))
        self.assertIsNone(missing.rows[0].affected_users)


class StateTests(unittest.TestCase):
    def test_state_precedence(self) -> None:
        self.assertEqual(_state("fresh", "out_of_coverage", True, "ok"), "out_of_coverage")
        self.assertEqual(_state("unavailable", "covered", True, "ok"), "unavailable")
        self.assertEqual(_state("stale", "covered", True, "ok"), "stale")
        self.assertEqual(_state("fresh", "covered", True, "ok"), "works_reported")
        self.assertEqual(_state("fresh", "covered", False, "ok"), "no_works")
        self.assertEqual(_state("fresh", "coverage_unverified", False, "ok"),
                         "coverage_unverified")
        self.assertEqual(_state("fresh", "covered", False, "degraded"), "unavailable")
        self.assertEqual(_state("fresh", "coverage_unverified", False, "degraded"),
                         "coverage_unverified")


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.url, "SCHEDULED_WORKS_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self._clear()

    def _clear(self) -> None:
        with Session(self.engine) as db:
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.execute(delete(ScheduledFetchRun))
            db.commit()

    def _seed(self, last_modified: datetime | None, text: str = FEED) -> ScheduledSnapshot:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with Session(self.engine) as db:
            _store_snapshot(db, parse_scheduled(text), last_modified, digest,
                            datetime.now(UTC))
            db.commit()
            snapshot = current_snapshot(db)
        assert snapshot is not None
        return snapshot

    def test_not_modified_updates_timestamps_without_duplicate(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.scheduled_store.fetch_feed",
                   return_value=FetchedFeed(text=FEED, last_modified=now, status=200)):
            self.assertEqual(refresh_once(), "not_modified")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ScheduledSnapshot)), 1)
            row = current_snapshot(db)
        assert row is not None
        self.assertGreaterEqual(row.last_checked_at, now)
        self.assertEqual(row.source_last_modified, now)

    def test_new_content_replaces_current_and_prune_bounds_retention(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.scheduled_store.fetch_feed", return_value=FetchedFeed(
            text=FEED.replace("'1.599'", "'1.600'"), last_modified=now, status=200,
        )):
            self.assertEqual(refresh_once(), "ok")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(
                select(func.count()).select_from(ScheduledSnapshot).where(
                    ScheduledSnapshot.is_current),
            ), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(ScheduledSnapshot)), 2)
            self.assertEqual(db.scalar(select(func.count()).select_from(ScheduledWork)), 8)

        with Session(self.engine) as db:
            for index in range(30):
                _store_snapshot(db, parse_scheduled(FEED), now - timedelta(seconds=index),
                                f"{index:064d}", now - timedelta(seconds=index))
            db.commit()
            _prune(db)
            db.commit()
            total = db.scalar(select(func.count()).select_from(ScheduledSnapshot))
            current = db.scalar(select(func.count()).select_from(ScheduledSnapshot).where(
                ScheduledSnapshot.is_current))
        self.assertEqual(total, 24)
        self.assertEqual(current, 1)

    def test_sentinel_total_does_not_freeze_snapshot(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.scheduled_store.fetch_feed",
                   return_value=FetchedFeed(text=SENTINEL_TOTAL, last_modified=now,
                                            status=200)):
            self.assertEqual(refresh_once(), "ok")
        with patch("app.scheduled_store.parse_scheduled",
                   side_effect=ScheduledParseError("bad")):
            self.assertEqual(refresh_once(), "parse_error")
        with patch("app.scheduled_store.parse_scheduled",
                   side_effect=ScheduledSchemaError("bad")):
            self.assertEqual(refresh_once(), "schema_error")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ScheduledSnapshot)), 2)
            outcomes = list(db.scalars(select(ScheduledFetchRun.outcome)))
        self.assertIn("ok", outcomes)
        self.assertIn("parse_error", outcomes)
        self.assertIn("schema_error", outcomes)
        self.assertNotIn("source_degraded", outcomes)

    def test_not_modified_without_last_modified(self) -> None:
        self._seed(None)
        with patch("app.scheduled_store.fetch_feed",
                   return_value=FetchedFeed(text=FEED, last_modified=None, status=200)):
            self.assertEqual(refresh_once(), "not_modified")
        with Session(self.engine) as db:
            snapshot = current_snapshot(db)
        assert snapshot is not None
        self.assertIsNone(snapshot.source_last_modified)

    def test_run_retention_prunes_older_than_30_days(self) -> None:
        old = datetime.now(UTC) - timedelta(days=31)
        with Session(self.engine) as db:
            db.add(ScheduledFetchRun(started_at=old, finished_at=old, outcome="ok"))
            db.commit()
        record_run("ok", started_at=datetime.now(UTC))
        with Session(self.engine) as db:
            outcomes = list(db.scalars(select(ScheduledFetchRun.outcome)))
        self.assertEqual(outcomes, ["ok"])

    def test_concurrent_refresh_skips_locked(self) -> None:
        started = threading.Event()

        def slow_fetch() -> FetchedFeed:
            started.set()
            time.sleep(0.5)
            return FetchedFeed(text=FEED, last_modified=datetime.now(UTC), status=200)

        with patch("app.scheduled_store.fetch_feed", side_effect=slow_fetch):
            thread = threading.Thread(target=refresh_once)
            thread.start()
            self.assertTrue(started.wait(2))
            self.assertEqual(refresh_once(), "skipped_locked")
            thread.join(5)
        with Session(self.engine) as db:
            outcomes = list(db.scalars(select(ScheduledFetchRun.outcome)))
            snapshots = db.scalar(select(func.count()).select_from(ScheduledSnapshot))
        self.assertEqual(outcomes.count("skipped_locked"), 1)
        self.assertEqual(snapshots, 1)

    def test_failed_refresh_releases_the_lock(self) -> None:
        with patch("app.scheduled_store.fetch_feed", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                refresh_once()
        with patch("app.scheduled_store.fetch_feed", return_value=FetchedFeed(
            text=FEED, last_modified=datetime.now(UTC), status=200,
        )):
            self.assertEqual(refresh_once(), "ok")


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.url, "SCHEDULED_WORKS_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.headers: dict[bytes, bytes] = {}
        with Session(self.engine) as db:
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.execute(delete(ScheduledFetchRun))
            db.commit()

    def _seed(self, last_modified: datetime | None, text: str = FEED) -> None:
        with Session(self.engine) as db:
            _store_snapshot(db, parse_scheduled(text), last_modified, "b" * 64,
                            datetime.now(UTC))
            db.add(ScheduledFetchRun(started_at=datetime.now(UTC),
                                     finished_at=datetime.now(UTC), outcome="ok",
                                     http_status=200, detail_code=None,
                                     content_sha256="b" * 64))
            db.commit()

    async def _get(self, path: str, query: dict[str, str] | None = None
                   ) -> tuple[int, bytes]:
        scope: Scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "method": "GET", "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": urlencode(query or {}).encode(),
            "root_path": "", "headers": [(b"host", b"test")],
            "client": ("127.0.0.1", 1234), "server": ("test", 8000),
        }
        messages: list[Message] = []

        async def receive() -> Message:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        self.headers = dict(messages[0]["headers"])
        return int(messages[0]["status"]), b"".join(
            message.get("body", b"") for message in messages[1:]
        )

    async def test_reported_works_contract_and_unpublished_fields(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "works_reported")
        self.assertEqual(payload["source_status"], "ok")
        self.assertEqual(payload["freshness"], "fresh")
        self.assertEqual(payload["granularity"], "partido")
        self.assertEqual(payload["source"], "ENRE")
        self.assertEqual(payload["source_reported_time"], "11:05")
        self.assertIn("dates_not_published", payload["limitations"])
        self.assertIn("reason_not_published", payload["limitations"])
        self.assertIn("proximity_not_available", payload["limitations"])
        self.assertNotIn("announced_works_not_displayed", payload["limitations"])
        self.assertEqual(len(payload["works"]), 2)
        for work in payload["works"]:
            self.assertEqual(work["category"], "maintenance")
            self.assertIsNone(work["planned_start_at"])
            self.assertIsNone(work["planned_end_at"])
            self.assertIsNone(work["reason_text"])
            self.assertEqual(work["restoration_estimate_text"], "Sin datos")
        self.assertNotIn("totals_scope", payload)

    async def test_localidad_filter_and_case_normalization(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/scheduled-works", {
            "partido": "  almirante   brown ", "localidad": "glew",
        })
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["granularity"], "localidad")
        self.assertEqual(len(payload["works"]), 1)
        self.assertEqual(payload["works"][0]["localidad"], "GLEW")

    async def test_no_works_only_with_fresh_covered_snapshot(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/scheduled-works", {
            "partido": "BERAZATEGUI", "localidad": "BERAZATEGUI",
        })
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "no_works")
        self.assertEqual(payload["works"], [])
        self.assertEqual(payload["coverage"]["status"], "covered")

    async def test_unverified_coverage_omits_works(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/scheduled-works", {"partido": "CAPITAL"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "coverage_unverified")
        self.assertNotIn("works", payload)

    async def test_stale_and_unavailable_states(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=30))
        status, body = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["state"], "stale")
        self.assertIn("works", json.loads(body))

        with Session(self.engine) as db:
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.commit()
        self._seed(datetime.now(UTC) - timedelta(minutes=90))
        status, body = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertIn("works", payload)

    async def test_no_snapshot_is_unavailable(self) -> None:
        status, body = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertNotIn("works", payload)

    async def test_degraded_source_never_reports_no_works(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        with Session(self.engine) as db:
            db.add(ScheduledFetchRun(started_at=datetime.now(UTC) + timedelta(seconds=1),
                                     finished_at=datetime.now(UTC), outcome="timeout",
                                     http_status=None, detail_code="Timeout",
                                     content_sha256=None))
            db.commit()
        status, body = await self._get("/scheduled-works", {
            "partido": "BERAZATEGUI", "localidad": "BERAZATEGUI",
        })
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["source_status"], "degraded")
        self.assertEqual(payload["state"], "unavailable")
        self.assertNotEqual(payload["state"], "no_works")

    async def test_announced_limitation_when_comunicados_present(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2), WITH_COMUNICADOS)
        status, body = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        self.assertIn("announced_works_not_displayed", json.loads(body)["limitations"])

    async def test_restoration_datetime_is_verbatim(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2), DATED)
        status, body = await self._get("/scheduled-works", {"partido": "AVELLANEDA"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "works_reported")
        work = payload["works"][0]
        self.assertEqual(work["restoration_estimate_text"], "2026-01-14 15:33")
        self.assertIsNone(work["planned_end_at"])

    async def test_input_validation(self) -> None:
        status, _ = await self._get("/scheduled-works", {"partido": "x" * 121})
        self.assertEqual(status, 422)
        status, _ = await self._get("/scheduled-works", {"partido": "x\ty"})
        self.assertEqual(status, 422)
        status, _ = await self._get("/scheduled-works", {"localidad": "GLEW"})
        self.assertEqual(status, 422)

    async def test_cache_control_is_no_store(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, _ = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 200)
        self.assertEqual(self.headers.get(b"cache-control"), b"no-store")

    async def test_database_unavailable_returns_503(self) -> None:
        with patch("app.scheduled_api.current_snapshot",
                   side_effect=DatabaseUnavailable("down")):
            status, _ = await self._get("/scheduled-works", {"partido": "almirante brown"})
        self.assertEqual(status, 503)

    async def test_areas_list_from_catalog_and_snapshot(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/scheduled-works/areas")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertIsNotNone(payload["coverage_version"])
        partidos = {area["partido"]: area for area in payload["areas"]}
        self.assertIn("ALMIRANTE BROWN", partidos)
        glew = [row for row in partidos["ALMIRANTE BROWN"]["localidades"]
                if row["localidad"] == "GLEW"]
        self.assertEqual(len(glew), 1)
        self.assertTrue(glew[0]["reported"])
        self.assertEqual(glew[0]["coverage"], "covered")


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL") and os.environ.get("TEST_ENRE_LIVE"),
    "Needs isolated PostgreSQL and live ENRE access",
)
class LiveEnreTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(cls.url)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.url, "SCHEDULED_WORKS_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with Session(self.engine) as db:
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.execute(delete(ScheduledFetchRun))
            db.commit()

    async def test_real_feed_reaches_the_public_api(self) -> None:
        self.assertIn(refresh_once(), {"ok", "not_modified"})
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            areas = (await client.get("/scheduled-works/areas")).json()
            self.assertIsNotNone(areas["coverage_version"])
            reported = [
                (area["partido"], row["localidad"])
                for area in areas["areas"]
                for row in area["localidades"]
                if row["reported"]
            ]
            if reported:
                partido, localidad = reported[0]
            elif areas["areas"]:
                partido = areas["areas"][0]["partido"]
                localidad = None
            else:
                partido, localidad = "ALMIRANTE BROWN", None
            params = {"partido": partido}
            if localidad:
                params["localidad"] = localidad
            response = await client.get("/scheduled-works", params=params)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(payload["state"], {
            "works_reported", "no_works", "coverage_unverified", "unavailable", "stale",
        })
        self.assertIn(payload["source_status"], {"ok", "degraded"})
        self.assertEqual(payload["source"], "ENRE")
        self.assertIn("dates_not_published", payload["limitations"])
        for work in payload.get("works") or []:
            self.assertEqual(work["category"], "maintenance")
            self.assertIsNone(work["planned_start_at"])
            self.assertIsNone(work["planned_end_at"])
            self.assertIsNone(work["reason_text"])
