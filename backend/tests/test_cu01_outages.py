"""CU01 parser, persistence, concurrency and public API tests (synthetic fixtures)."""

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
from app.enre_parser import EnreParseError, EnreSchemaError, parse_feed
from app.main import app
from app.models import OutageFetchRun, OutageReport, OutageSnapshot
from app.outage_store import _prune, _store_snapshot, current_snapshot, refresh_once
from app.outages_api import _state

FEED = (Path(__file__).parent / "fixtures" / "enre_data_eds_redacted.js").read_text(
    encoding="utf-8",
)

DEGRADED = FEED.replace("'7.202'", "'N/A'")
EMPTY = """var data = {empresa: 'EDESUR', totalUsuariosSinSuministro: '-',
totalUsuariosConSuministro: '-', ultimaActualizacion: '--:--',
cortesPreventivos: [], cortesServicioMedia: [], cortesServicioBaja: []}"""


class ParserTests(unittest.TestCase):
    def test_real_shape_parses_and_keeps_only_current_categories(self) -> None:
        feed = parse_feed(FEED)
        self.assertEqual(feed.distributor, "EDESUR")
        self.assertEqual(feed.total_users_without, 7202)
        self.assertEqual(feed.total_users_with, 2819682)
        self.assertEqual(feed.users_affected_yesterday, 1580)
        self.assertEqual(feed.source_reported_time, "0:25")
        self.assertFalse(feed.degraded)
        self.assertEqual(feed.row_counts, {
            "medium_voltage": 1, "low_voltage": 2, "preventive": 1,
        })
        self.assertEqual({row.category for row in feed.rows},
                         {"medium_voltage", "low_voltage", "preventive"})

    def test_tolerant_of_extra_keys_and_empty_collections(self) -> None:
        feed = parse_feed(FEED.replace(
            "usuarios: '65', normalizacion: '12:30'",
            "usuarios: '65', normalizacion: '12:30', extra: 'ignored'",
        ))
        self.assertEqual(len(feed.rows), 4)
        empty = parse_feed(EMPTY)
        self.assertEqual(empty.rows, ())
        self.assertIsNone(empty.source_reported_time)
        self.assertTrue(empty.degraded)

    def test_degraded_and_sentinels(self) -> None:
        feed = parse_feed(DEGRADED)
        self.assertTrue(feed.degraded)
        self.assertIsNone(feed.total_users_without)

    def test_normalization_and_thousands(self) -> None:
        feed = parse_feed(FEED)
        low = [row for row in feed.rows if row.category == "low_voltage"]
        self.assertEqual(low[0].partido_key, "almirante brown")
        self.assertEqual(low[1].partido, "CA\u00d1UELAS")
        self.assertEqual(low[1].partido_key, "ca\u00f1uelas")

    def test_schema_and_parse_errors(self) -> None:
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace(
                "partido: 'ALMIRANTE BROWN', localidad: 'SAN JOSE', ", "",
            ))
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace("usuarios: '1'", "usuarios: 'many'"))
        with self.assertRaises(EnreParseError):
            parse_feed("<html>not the feed</html>")
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace("empresa: 'EDESUR'", "empresa: 'EDENOR'"))
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace("totalUsuariosSinSuministro: '7.202'",
                                    "totalUsuariosSinSuministro: 'Sin datos'"))
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace("totalUsuariosSinSuministro: '7.202',", ""))

    def test_unknown_collections_and_unobserved_category_rows_are_safe(self) -> None:
        # Synthetic fixtures only: no populated media/preventivo capture exists.
        feed = parse_feed(FEED.replace(
            "cortesServicioMedia:  [{",
            "cortesServicioAlta: [{partido: 'X', localidad: 'Y', usuarios: '1'}],\n"
            "    cortesServicioMedia:  [{",
        ))
        self.assertEqual({row.category for row in feed.rows},
                         {"medium_voltage", "low_voltage", "preventive"})
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace(
                "cortesServicioMedia:  [{partido: 'LOMAS DE ZAMORA', localidad: 'BANFIELD',",
                "cortesServicioMedia:  [{localidad: 'BANFIELD',",
            ))
        # A known collection omitted by an upstream change fails closed.
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace("cortesServicioMedia:  [{",
                                    "cortesServicioMediaOmitted:  [{"))
        # A null known collection is an invalid structure, not an empty list.
        media = ("cortesServicioMedia:  [{partido: 'LOMAS DE ZAMORA', localidad: 'BANFIELD', "
                 "subestacion_alimentador: '87-ESCALADA / R:087-2', usuarios: '120', "
                 "normalizacion: '11:00'}]")
        with self.assertRaises(EnreSchemaError):
            parse_feed(FEED.replace(media, "cortesServicioMedia: null"))


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
            "DATABASE_URL": self.url, "OUTAGE_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self._clear()

    def _clear(self) -> None:
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.commit()

    def _seed(self, last_modified: datetime | None, text: str = FEED) -> OutageSnapshot:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with Session(self.engine) as db:
            _store_snapshot(db, parse_feed(text), last_modified, digest,
                            datetime.now(UTC))
            db.commit()
            snapshot = current_snapshot(db)
        assert snapshot is not None
        return snapshot

    def test_not_modified_updates_timestamps_without_duplicate(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.outage_store.fetch_feed",
                   return_value=FetchedFeed(text=FEED, last_modified=now, status=200)):
            self.assertEqual(refresh_once(), "not_modified")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(OutageSnapshot)), 1)
            row = current_snapshot(db)
        assert row is not None
        self.assertGreaterEqual(row.last_checked_at, now)
        self.assertEqual(row.source_last_modified, now)

    def test_new_content_replaces_current_and_prune_bounds_retention(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.outage_store.fetch_feed", return_value=FetchedFeed(
            text=FEED.replace("'1.580'", "'1.581'"), last_modified=now, status=200,
        )):
            self.assertEqual(refresh_once(), "ok")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(
                select(func.count()).select_from(OutageSnapshot).where(
                    OutageSnapshot.is_current),
            ), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(OutageSnapshot)), 2)

        with Session(self.engine) as db:
            for index in range(30):
                _store_snapshot(db, parse_feed(FEED), now - timedelta(seconds=index),
                                f"{index:064d}", now - timedelta(seconds=index))
            db.commit()
            _prune(db)
            db.commit()
            total = db.scalar(select(func.count()).select_from(OutageSnapshot))
            current = db.scalar(select(func.count()).select_from(OutageSnapshot).where(
                OutageSnapshot.is_current))
        self.assertEqual(total, 24)
        self.assertEqual(current, 1)

    def test_degraded_and_parse_failure_keep_last_valid_snapshot(self) -> None:
        now = datetime.now(UTC)
        self._seed(now)
        with patch("app.outage_store.fetch_feed",
                   return_value=FetchedFeed(text=DEGRADED, last_modified=now, status=200)):
            self.assertEqual(refresh_once(), "source_degraded")
        with patch("app.outage_store.parse_feed", side_effect=EnreParseError("bad")):
            self.assertEqual(refresh_once(), "parse_error")
        with patch("app.outage_store.parse_feed", side_effect=EnreSchemaError("bad")):
            self.assertEqual(refresh_once(), "schema_error")
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(OutageSnapshot)), 1)
            outcomes = list(db.scalars(select(OutageFetchRun.outcome)))
        self.assertIn("source_degraded", outcomes)
        self.assertIn("parse_error", outcomes)
        self.assertIn("schema_error", outcomes)

    def test_concurrent_refresh_skips_locked(self) -> None:
        started = threading.Event()

        def slow_fetch() -> FetchedFeed:
            started.set()
            time.sleep(0.5)
            return FetchedFeed(text=FEED, last_modified=datetime.now(UTC), status=200)

        with patch("app.outage_store.fetch_feed", side_effect=slow_fetch):
            thread = threading.Thread(target=refresh_once)
            thread.start()
            self.assertTrue(started.wait(2))
            self.assertEqual(refresh_once(), "skipped_locked")
            thread.join(5)
        with Session(self.engine) as db:
            outcomes = list(db.scalars(select(OutageFetchRun.outcome)))
            snapshots = db.scalar(select(func.count()).select_from(OutageSnapshot))
        self.assertIn("skipped_locked", outcomes)
        self.assertEqual(outcomes.count("skipped_locked"), 1)
        self.assertEqual(snapshots, 1)

    def test_failed_refresh_releases_the_lock(self) -> None:
        with patch("app.outage_store.fetch_feed", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                refresh_once()
        with patch("app.outage_store.fetch_feed", return_value=FetchedFeed(
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
            "DATABASE_URL": self.url, "OUTAGE_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.headers: dict[bytes, bytes] = {}
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.commit()

    def _seed(self, last_modified: datetime | None, text: str = FEED) -> None:
        with Session(self.engine) as db:
            _store_snapshot(db, parse_feed(text), last_modified, "b" * 64,
                            datetime.now(UTC))
            db.add(OutageFetchRun(started_at=datetime.now(UTC),
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

    async def test_reported_state_with_provenance_and_no_summation(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "reported")
        self.assertEqual(payload["source_status"], "ok")
        self.assertEqual(payload["freshness"], "fresh")
        self.assertEqual(payload["granularity"], "partido")
        self.assertEqual(payload["totals_scope"], "edesur")
        self.assertEqual(payload["total_users_without"], 7202)
        self.assertIn("source_updated_at", payload)
        self.assertIn("fetched_at", payload)
        self.assertEqual(len(payload["outages"]), 2)
        self.assertEqual({row["category"] for row in payload["outages"]},
                         {"medium_voltage", "preventive"})

    async def test_localidad_filter_and_case_normalization(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/outages", {
            "partido": "  LOMAS   DE ZAMORA ", "localidad": "banfield",
        })
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["granularity"], "localidad")
        self.assertEqual(len(payload["outages"]), 2)
        self.assertTrue(all(row["localidad"] == "BANFIELD" for row in payload["outages"]))

    async def test_stale_unavailable_and_unverified_states(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=30))
        status, body = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["state"], "stale")

        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.commit()
        self._seed(datetime.now(UTC) - timedelta(minutes=90))
        status, body = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertIn("outages", payload)

        status, body = await self._get("/outages", {"partido": "san vicente"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["state"], "unavailable")
        self.assertNotIn("outages", json.loads(body))

    async def test_no_snapshot_and_unverified_area(self) -> None:
        status, body = await self._get("/outages", {"partido": "banfield"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertNotIn("outages", payload)
        status, body = await self._get("/outages/areas")
        self.assertEqual(status, 200)
        areas = json.loads(body)["areas"]
        self.assertTrue(areas)
        self.assertIsNotNone(json.loads(body)["coverage_version"])

        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/outages", {"partido": "san vicente"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "coverage_unverified")
        self.assertEqual(payload["coverage"]["status"], "coverage_unverified")
        self.assertNotIn("outages", payload)

    async def test_degraded_status_and_input_validation(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        with Session(self.engine) as db:
            db.add(OutageFetchRun(started_at=datetime.now(UTC) + timedelta(seconds=1),
                                  finished_at=datetime.now(UTC), outcome="timeout",
                                  http_status=None, detail_code="Timeout",
                                  content_sha256=None))
            db.commit()
        status, body = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["source_status"], "degraded")

        status, _ = await self._get("/outages", {"partido": "x" * 121})
        self.assertEqual(status, 422)
        status, _ = await self._get("/outages", {"partido": "x\ty"})
        self.assertEqual(status, 422)

    async def test_areas_list_from_snapshot(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, body = await self._get("/outages/areas")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertIsNotNone(payload["coverage_version"])
        partidos = {area["partido"]: area for area in payload["areas"]}
        self.assertIn("LOMAS DE ZAMORA", partidos)
        self.assertEqual(
            partidos["LOMAS DE ZAMORA"]["localidades"][0]["coverage"],
            "coverage_unverified",
        )

    async def test_areas_group_by_normalized_key(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        with Session(self.engine) as db:
            snapshot = current_snapshot(db)
            assert snapshot is not None
            db.add(OutageReport(
                snapshot_id=snapshot.id, category="low_voltage",
                partido="Lomas de Zamora", localidad="Banfield",
                partido_key="lomas de zamora", localidad_key="banfield",
                subestacion_alimentador=None, affected_users=1, normalizacion=None,
            ))
            db.commit()
        status, body = await self._get("/outages/areas")
        self.assertEqual(status, 200)
        matches = [area for area in json.loads(body)["areas"]
                   if area["partido"].casefold() == "lomas de zamora"]
        self.assertEqual(len(matches), 1)

    async def test_missing_last_modified_is_unavailable_without_fabrication(self) -> None:
        self._seed(None)
        status, body = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["freshness"], "unavailable")
        self.assertNotIn("source_updated_at", payload)

    async def test_localidad_without_partido_and_empty_values(self) -> None:
        status, _ = await self._get("/outages", {"localidad": "banfield"})
        self.assertEqual(status, 422)
        status, _ = await self._get("/outages", {})
        self.assertEqual(status, 422)
        status, _ = await self._get("/outages", {"partido": "   "})
        self.assertEqual(status, 422)

    async def test_database_unavailable_returns_503(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        with patch("app.outages_api.current_snapshot",
                   side_effect=DatabaseUnavailable("x")):
            status, _ = await self._get("/outages/areas")
        self.assertEqual(status, 503)

    async def test_public_response_is_no_store_and_unauthenticated(self) -> None:
        self._seed(datetime.now(UTC) - timedelta(minutes=2))
        status, _ = await self._get("/outages", {"partido": "lomas de zamora"})
        self.assertEqual(status, 200)
        self.assertEqual(self.headers.get(b"cache-control"), b"no-store")
        self.assertNotIn(b"set-cookie", self.headers)

    async def test_degraded_first_fetch_reports_unavailable(self) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            db.add(OutageFetchRun(started_at=now, finished_at=now,
                                  outcome="source_degraded", http_status=200,
                                  detail_code="degraded_totals", content_sha256=None))
            db.commit()
        status, body = await self._get("/outages", {"partido": "banfield"})
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["source_status"], "degraded")
        self.assertNotIn("outages", payload)


class StateTests(unittest.TestCase):
    def test_precedence_and_degraded_source(self) -> None:
        self.assertEqual(_state("fresh", "out_of_coverage", False, "ok"),
                         "out_of_coverage")
        self.assertEqual(_state("unavailable", "covered", True, "ok"), "unavailable")
        self.assertEqual(_state("stale", "covered", True, "ok"), "stale")
        self.assertEqual(_state("fresh", "coverage_unverified", True, "ok"), "reported")
        self.assertEqual(_state("fresh", "covered", False, "ok"), "no_reports")
        self.assertEqual(_state("fresh", "coverage_unverified", False, "ok"),
                         "coverage_unverified")
        self.assertEqual(_state("fresh", "covered", False, "degraded"), "unavailable")
        self.assertEqual(_state("fresh", "coverage_unverified", False, "degraded"),
                         "coverage_unverified")



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
            "DATABASE_URL": self.url, "OUTAGE_SCHEDULER_ENABLED": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.commit()

    async def test_real_feed_reaches_the_public_api(self) -> None:
        self.assertIn(refresh_once(), {"ok", "not_modified"})
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            areas = (await client.get("/outages/areas")).json()
            self.assertIsNotNone(areas["coverage_version"])
            partido = areas["areas"][0]["partido"] if areas["areas"] else "LOMAS DE ZAMORA"
            response = await client.get("/outages", params={"partido": partido})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(payload["state"],
                      {"reported", "coverage_unverified", "unavailable"})
        self.assertIn(payload["source_status"], {"ok", "degraded"})
        self.assertEqual(payload["totals_scope"], "edesur")
        self.assertIn("source_updated_at", payload)
        self.assertTrue(areas["areas"] or payload.get("total_users_without") is not None)
        for row in payload.get("outages") or []:
            self.assertIn(row["category"],
                          {"medium_voltage", "low_voltage", "preventive"})
