"""CU03 read-only CU01/CU02 tools and deterministic routing tests."""

import json
import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from app.assistant_tools import (
    current_outages,
    lookup_current_outages,
    lookup_scheduled_works,
    plan_question,
    resolve_zone,
)
from app.coverage import load_catalog
from app.enre_client import FEED_URL
from app.enre_parser import normalized_key
from app.models import (
    OutageReport,
    OutageSnapshot,
    ScheduledSnapshot,
    ScheduledWork,
)

URL = os.environ.get("TEST_DATABASE_URL", "")


@unittest.skipUnless(
    URL.startswith("postgresql+psycopg://"), "TEST_DATABASE_URL is not configured",
)
class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(URL)
        with cls.engine.connect() as connection:
            present = connection.execute(
                text("SELECT to_regclass('es_outage_snapshots')"),
            ).scalar()
            if present is None:
                raise unittest.SkipTest("CU01 migration is not applied")
        entry = next(
            (item for item in load_catalog().entries.values() if item.status == "covered"),
            None,
        )
        if entry is None or entry.localidad is None:
            raise unittest.SkipTest("No covered localidad in the catalog")
        cls.partido = entry.partido
        cls.localidad = entry.localidad

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": URL})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self._clear()

    def _clear(self) -> None:
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(ScheduledWork))
            db.execute(delete(ScheduledSnapshot))
            db.commit()

    def _seed_outage(self, *, fresh: bool = True, rows: int = 1) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            snapshot = OutageSnapshot(
                distributor="EDESUR",
                source_url=FEED_URL,
                source_last_modified=now if fresh else now - timedelta(minutes=30),
                fetched_at=now,
                last_checked_at=now,
                content_sha256="a" * 64,
                is_current=True,
                row_counts={"low_voltage": rows},
            )
            db.add(snapshot)
            db.flush()
            for _ in range(rows):
                db.add(OutageReport(
                    snapshot_id=snapshot.id,
                    category="low_voltage",
                    partido=self.partido,
                    localidad=self.localidad,
                    partido_key=normalized_key(self.partido),
                    localidad_key=normalized_key(self.localidad),
                    affected_users=10,
                    normalizacion="12:00",
                ))
            db.commit()

    def _seed_scheduled(self, *, rows: int = 1) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            snapshot = ScheduledSnapshot(
                source="ENRE",
                source_url=FEED_URL,
                source_last_modified=now,
                fetched_at=now,
                last_checked_at=now,
                content_sha256="b" * 64,
                is_current=True,
                row_counts={"maintenance": rows},
                unverified_collections=[],
                comunicados_present=False,
            )
            db.add(snapshot)
            db.flush()
            for _ in range(rows):
                db.add(ScheduledWork(
                    snapshot_id=snapshot.id,
                    category="maintenance",
                    partido=self.partido,
                    localidad=self.localidad,
                    partido_key=normalized_key(self.partido),
                    localidad_key=normalized_key(self.localidad),
                    affected_users=20,
                    restoration_estimate_text="Sin datos",
                ))
            db.commit()

    def test_outage_states_and_provenance(self) -> None:
        self._seed_outage()
        result = lookup_current_outages(self.partido, self.localidad)
        self.assertEqual(result.state, "reported")
        self.assertEqual(result.freshness, "fresh")
        self.assertEqual(result.coverage, "covered")
        self.assertEqual(result.source, "ENRE")
        self.assertTrue(result.source_url.startswith("https://"))
        self.assertEqual(len(result.outages), 1)

        self._clear()
        self._seed_outage(fresh=False)
        stale = lookup_current_outages(self.partido, self.localidad)
        self.assertEqual(stale.state, "stale")
        self.assertEqual(stale.freshness, "stale")

        self._clear()
        self._seed_outage(rows=0)
        empty = lookup_current_outages(self.partido, self.localidad)
        self.assertEqual(empty.state, "no_reports")
        self.assertEqual(empty.outages, ())

    def test_scheduled_works_respects_u22(self) -> None:
        self._seed_scheduled()
        result = lookup_scheduled_works(self.partido, self.localidad)
        self.assertEqual(result.state, "works_reported")
        self.assertIn("dates_not_published", result.limitations)
        self.assertEqual(result.works[0]["planned_start_at"], None)
        self.assertEqual(result.works[0]["planned_end_at"], None)
        self.assertEqual(result.works[0]["reason_text"], None)

    def test_langchain_tool_wrapper_is_read_only_json(self) -> None:
        self._seed_outage()
        payload = json.loads(current_outages.invoke({
            "partido": self.partido, "localidad": self.localidad,
        }))
        self.assertEqual(payload["state"], "reported")
        self.assertEqual(payload["source"], "ENRE")

    def test_router_selects_guide_dynamic_and_mixed(self) -> None:
        zone = resolve_zone(f"Hay cortes en {self.localidad}")
        self.assertIsNotNone(zone)
        self.assertEqual(zone[0], self.partido)

        guide = plan_question("¿Cómo pago la factura?")
        self.assertTrue(guide.use_guide)
        self.assertFalse(guide.use_outages)
        self.assertFalse(guide.use_scheduled)

        scheduled = plan_question(f"¿Hay trabajos programados en {self.localidad}?")
        self.assertTrue(scheduled.use_scheduled)
        self.assertFalse(scheduled.use_outages)

        mixed_dynamic = plan_question(
            f"¿Hay cortes y trabajos programados en {self.localidad}?",
        )
        self.assertTrue(mixed_dynamic.use_outages)
        self.assertTrue(mixed_dynamic.use_scheduled)

        mixed_guide = plan_question(
            f"¿Hay cortes en {self.localidad} y cómo reclamo?",
        )
        self.assertTrue(mixed_guide.use_outages)
        self.assertTrue(mixed_guide.use_guide)

        generic = plan_question("¿Cuál es la capital de Francia?")
        self.assertTrue(generic.use_guide)
        self.assertFalse(generic.use_outages)
        self.assertFalse(generic.use_scheduled)
