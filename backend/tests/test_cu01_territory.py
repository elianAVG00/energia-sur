"""CU01 BUILD 2 territory: coverage catalog, GeoRef adapter and resolve API."""

import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session
from starlette.types import Message, Scope

from app import georef
from app.coverage import CoverageCatalog, CoverageCatalogError, _load, load_catalog
from app.enre_parser import parse_feed
from app.main import app
from app.models import OutageFetchRun, OutageReport, OutageSnapshot
from app.outage_store import _store_snapshot, current_snapshot
from app.outages_api import reset_rate_limit

FEED = (Path(__file__).parent / "fixtures" / "enre_data_eds_redacted.js").read_text(
    encoding="utf-8",
)

CATALOG = {
    "version": "test-1",
    "retrieved_on": "2026-11-10",
    "source": "synthetic test catalog",
    "entries": [
        {"partido": "QUILMES", "localidad": "QUILMES", "status": "covered"},
        {"partido": "LOMAS DE ZAMORA", "localidad": None, "status": "covered"},
        {"partido": "CAPITAL", "localidad": None, "status": "out_of_coverage"},
    ],
}


def _address(nomenclatura: str, partido: str, localidad: str, province: str,
             lat: float = -34.73, lon: float = -58.30) -> dict[str, object]:
    return {
        "nomenclatura": nomenclatura,
        "departamento": {"id": "000", "nombre": partido},
        "localidad_censal": {"id": "000", "nombre": localidad},
        "provincia": {"id": province, "nombre": "Test"},
        "ubicacion": {"lat": lat, "lon": lon},
    }


def _catalog() -> CoverageCatalog:
    path = Path(tempfile.gettempdir()) / f"cu01-catalog-{uuid4().hex}.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    return load_catalog(str(path))


class CoverageTests(unittest.TestCase):
    def test_statuses_and_absence(self) -> None:
        catalog = _catalog()
        self.assertEqual(catalog.classify("Quilmes", "quilmes"), "covered")
        self.assertEqual(catalog.classify("Lomas de Zamora", None), "covered")
        self.assertEqual(catalog.classify("Lomas de Zamora", "Banfield"),
                         "coverage_unverified")
        self.assertEqual(catalog.classify("Capital", None), "out_of_coverage")
        self.assertEqual(catalog.classify("Quilmes", "Bernal"), "coverage_unverified")
        self.assertEqual(catalog.classify("Avellaneda", None), "coverage_unverified")

    def test_absence_is_never_out_of_coverage(self) -> None:
        catalog = _catalog()
        for partido in ("Avellaneda", "San Isidro", "Desconocido"):
            self.assertEqual(catalog.classify(partido, None), "coverage_unverified")

    def test_packaged_catalog_has_provenance(self) -> None:
        catalog = load_catalog()
        self.assertTrue(catalog.version)
        self.assertTrue(catalog.retrieved_on)
        self.assertIn("enre.gov.ar", catalog.source)
        self.assertNotIn("out_of_coverage",
                         {entry.status for entry in catalog.entries.values()})

    def test_malformed_catalog_is_rejected(self) -> None:
        path = Path(tempfile.gettempdir()) / f"cu01-bad-{uuid4().hex}.json"
        path.write_text('{"version": "x", "entries": [{"partido": "A", "status": "bad"}]}',
                        encoding="utf-8")
        with self.assertRaises(CoverageCatalogError):
            _load(path)

    def test_unreadable_catalog_falls_back_to_unverified(self) -> None:
        path = Path(tempfile.gettempdir()) / f"cu01-binary-{uuid4().hex}.json"
        path.write_bytes(b"\xff\xfe\x00")
        catalog = load_catalog(str(path))
        self.assertEqual(catalog.version, "unavailable")
        self.assertEqual(catalog.classify("Quilmes", "Quilmes"),
                         "coverage_unverified")


class GeorefAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = _catalog()
        self.known: georef.KnownAreas = {("lomas de zamora", "banfield"): "BANFIELD"}

    def test_forward_resolves_partido_and_catalog_localidad(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "06":
                return {"direcciones": [_address("AV CALCHAQUI 100", "Quilmes",
                                                 "Quilmes", "06")]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            zones = georef.resolve_address("calchaqui 100", self.catalog, self.known)
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0].partido, "QUILMES")
        self.assertEqual(zones[0].localidad, "QUILMES")
        self.assertEqual(zones[0].granularity, "localidad")
        self.assertEqual(zones[0].coverage, "covered")

    def test_forward_retries_without_av_prefix(self) -> None:
        calls: list[str] = []

        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            calls.append(params["direccion"])
            if params["direccion"].startswith("hipolito") and params["provincia"] == "06":
                return {"direcciones": [
                    _address("HIPOLITO YRIGOYEN 10000", "Lomas de Zamora",
                             "Banfield", "06"),
                ]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            zones = georef.resolve_address(
                "av hipolito yrigoyen 10000", self.catalog, self.known,
            )
        self.assertIn("hipolito yrigoyen 10000", calls)
        self.assertEqual(zones[0].localidad, "BANFIELD")

    def test_ambiguous_results_hint_filter_and_degradation(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "06":
                return {"direcciones": [
                    _address("CALCHAQUI 100", "La Matanza", "La Matanza", "06"),
                    _address("AV CALCHAQUI 100", "Quilmes", "Quilmes", "06"),
                ]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            zones = georef.resolve_address("calchaqui 100", self.catalog, {})
            hinted = georef.resolve_address(
                "calchaqui 100", self.catalog, {}, partido_hint="Quilmes",
            )
        self.assertEqual(len(zones), 2)
        self.assertIsNone(zones[0].localidad)
        self.assertEqual(len(hinted), 1)
        self.assertEqual(hinted[0].partido, "QUILMES")

    def test_other_provinces_are_excluded(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "06":
                return {"direcciones": [_address("CALLE 1", "Córdoba", "Córdoba", "14")]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            with self.assertRaises(georef.GeorefNotFound):
                georef.resolve_address("calle 1", self.catalog, {})

    def test_caba_address_maps_to_capital_without_localidad(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "02":
                return {"direcciones": [_address(
                    "AV RIVADAVIA 1000", "Comuna 1",
                    "Ciudad Autónoma de Buenos Aires", "02",
                )]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            zones = georef.resolve_address("rivadavia 1000", self.catalog, {})
        self.assertEqual(zones[0].partido, "CAPITAL")
        self.assertIsNone(zones[0].localidad)
        self.assertEqual(zones[0].granularity, "partido")

    def test_reverse_geocoding_and_scope(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            latitude = float(params.get("lat", "0"))
            if latitude == -31.42:
                return {"ubicacion": {"departamento": {"nombre": "Córdoba"},
                                      "provincia": {"id": "14"}}}
            if latitude == -34.6:
                return {"ubicacion": {"departamento": {"nombre": "Comuna 1"},
                                      "provincia": {"id": "02"}}}
            return {"ubicacion": {"departamento": {"nombre": "Lomas de Zamora"},
                                  "provincia": {"id": "06"}}}

        with patch("app.georef._get", side_effect=fake_get):
            zone = georef.resolve_location(-34.76, -58.40, self.catalog, {})
            self.assertEqual(zone.partido, "LOMAS DE ZAMORA")
            self.assertEqual(zone.localidad, None)
            self.assertEqual(zone.coverage, "covered")
            caba = georef.resolve_location(-34.60, -58.38, self.catalog, {})
            self.assertEqual(caba.partido, "CAPITAL")
            self.assertIsNone(caba.localidad)
            with self.assertRaises(georef.GeorefOutsideScope):
                georef.resolve_location(-31.42, -64.18, self.catalog, {})

    def test_invalid_coordinates_and_unavailable_service(self) -> None:
        with self.assertRaises(georef.GeorefOutsideScope):
            georef.resolve_location(999, 999, self.catalog, {})
        with patch("app.georef._get", side_effect=georef.GeorefUnavailable("x")):
            with self.assertRaises(georef.GeorefUnavailable):
                georef.resolve_address("calle 1", self.catalog, {})


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ResolveApiTests(unittest.IsolatedAsyncioTestCase):
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
        reset_rate_limit()
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.commit()

    async def _call(self, method: str, path: str,
                    payload: dict[str, object] | None = None,
                    query: dict[str, str] | None = None
                    ) -> tuple[int, dict[str, bytes], dict[str, object]]:
        body = json.dumps(payload).encode() if payload is not None else b""
        scope: Scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "method": method, "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": urlencode(query or {}).encode(),
            "root_path": "", "headers": [(b"host", b"test"),
                                          (b"content-type", b"application/json")],
            "client": ("127.0.0.1", 1234), "server": ("test", 8000),
        }
        messages: list[Message] = []

        async def receive() -> Message:
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: Message) -> None:
            messages.append(message)

        await app(scope, receive, send)
        raw = b"".join(message.get("body", b"") for message in messages[1:])
        parsed: object = json.loads(raw) if raw else {}
        if not isinstance(parsed, dict):
            raise AssertionError("expected a JSON object")
        return int(messages[0]["status"]), dict(messages[0]["headers"]), parsed

    async def test_resolve_address_with_hint_and_privacy(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "06":
                return {"direcciones": [
                    _address("CALCHAQUI 100", "La Matanza", "La Matanza", "06"),
                    _address("AV CALCHAQUI 100", "Quilmes", "Quilmes", "06"),
                ]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            status, headers, payload = await self._call(
                "POST", "/outages/resolve",
                {"address": "calchaqui 100", "partido": "Quilmes"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "resolved")
        self.assertEqual(payload["zone"]["partido"], "QUILMES")
        self.assertNotIn("calchaqui", json.dumps(payload).lower())
        self.assertNotIn("lat", payload)
        self.assertEqual(headers.get(b"cache-control"), b"no-store")

    async def test_ambiguous_address_returns_candidates(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            if path == "direcciones" and params["provincia"] == "06":
                return {"direcciones": [
                    _address("CALCHAQUI 100", "La Matanza", "La Matanza", "06"),
                    _address("AV CALCHAQUI 100", "Quilmes", "Quilmes", "06"),
                ]}
            return {"direcciones": []}

        with patch("app.georef._get", side_effect=fake_get):
            status, _, payload = await self._call(
                "POST", "/outages/resolve", {"address": "calchaqui 100"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "candidates")
        self.assertEqual(len(payload["candidates"]), 2)

    async def test_resolve_location_and_out_of_scope(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            return {"ubicacion": {"departamento": {"nombre": "Lomas de Zamora"},
                                  "provincia": {"id": "06"}}}

        with patch("app.georef._get", side_effect=fake_get):
            status, _, payload = await self._call(
                "POST", "/outages/resolve-location", {"lat": -34.76, "lon": -58.40},
            )
        self.assertEqual(status, 200)
        self.assertEqual(payload["zone"]["partido"], "LOMAS DE ZAMORA")
        self.assertEqual(payload["zone"]["granularity"], "partido")

        status, _, _ = await self._call(
            "POST", "/outages/resolve-location", {"lat": 999, "lon": 0},
        )
        self.assertEqual(status, 422)

    async def test_georef_failure_is_a_geographic_error(self) -> None:
        with patch("app.georef._get", side_effect=georef.GeorefUnavailable("x")):
            status, _, payload = await self._call(
                "POST", "/outages/resolve", {"address": "calle 1"},
            )
        self.assertEqual(status, 422)
        self.assertIn("detail", payload)

    async def test_rate_limit_returns_429_without_georef_call(self) -> None:
        def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
            return {"ubicacion": {"departamento": {"nombre": "Lomas de Zamora"},
                                  "provincia": {"id": "06"}}}

        with patch("app.georef._get", side_effect=fake_get) as mocked:
            for _ in range(20):
                status, _, _ = await self._call(
                    "POST", "/outages/resolve-location", {"lat": -34.76, "lon": -58.40},
                )
                self.assertEqual(status, 200)
            calls_before = mocked.call_count
            status, headers, _ = await self._call(
                "POST", "/outages/resolve-location", {"lat": -34.76, "lon": -58.40},
            )
            self.assertEqual(mocked.call_count, calls_before)
        self.assertEqual(status, 429)
        self.assertEqual(headers.get(b"retry-after"), b"60")


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class CoverageApiTests(unittest.IsolatedAsyncioTestCase):
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
        self.catalog_patch = patch("app.outages_api.load_catalog",
                                   return_value=_catalog())
        self.catalog_patch.start()
        self.addCleanup(self.catalog_patch.stop)
        reset_rate_limit()
        with Session(self.engine) as db:
            db.execute(delete(OutageReport))
            db.execute(delete(OutageSnapshot))
            db.execute(delete(OutageFetchRun))
            db.commit()
        with Session(self.engine) as db:
            _store_snapshot(db, parse_feed(FEED), datetime.now(UTC), "c" * 64,
                            datetime.now(UTC))
            snapshot = current_snapshot(db)
            assert snapshot is not None
            db.add(OutageReport(
                snapshot_id=snapshot.id, category="low_voltage",
                partido="CAPITAL", localidad="VILLA RIACHUELO",
                partido_key="capital", localidad_key="villa riachuelo",
                subestacion_alimentador=None, affected_users=1, normalizacion=None,
            ))
            db.commit()

    async def _get(self, path: str, query: dict[str, str] | None = None
                   ) -> tuple[int, dict[str, object]]:
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
        body = b"".join(message.get("body", b"") for message in messages[1:])
        parsed: object = json.loads(body) if body else {}
        if not isinstance(parsed, dict):
            raise AssertionError("expected a JSON object")
        return int(messages[0]["status"]), parsed

    async def test_covered_area_without_reports(self) -> None:
        status, payload = await self._get(
            "/outages", {"partido": "QUILMES", "localidad": "QUILMES"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "no_reports")
        self.assertEqual(payload["coverage"]["status"], "covered")
        self.assertEqual(payload["outages"], [])

    async def test_localidad_absent_from_catalog_is_unverified(self) -> None:
        status, payload = await self._get(
            "/outages", {"partido": "LOMAS DE ZAMORA", "localidad": "BANFIELD"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["coverage"]["status"], "coverage_unverified")
        self.assertEqual(payload["state"], "reported")

    async def test_out_of_coverage_suppresses_rows(self) -> None:
        status, payload = await self._get("/outages", {"partido": "CAPITAL"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "out_of_coverage")
        self.assertEqual(payload["coverage"]["status"], "out_of_coverage")
        self.assertNotIn("outages", payload)

    async def test_unknown_area_is_unverified(self) -> None:
        status, payload = await self._get("/outages", {"partido": "AVELLANEDA"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "coverage_unverified")
        self.assertNotIn("outages", payload)

    async def test_areas_merge_catalog_and_snapshot(self) -> None:
        status, payload = await self._get("/outages/areas")
        self.assertEqual(status, 200)
        self.assertEqual(payload["coverage_version"], "test-1")
        self.assertTrue(payload["coverage_retrieved_on"])
        areas = {area["partido"]: area for area in payload["areas"]}
        self.assertIn("QUILMES", areas)
        self.assertIn("ALMIRANTE BROWN", areas)
        quilmes = areas["QUILMES"]["localidades"][0]
        self.assertEqual(quilmes["coverage"], "covered")
        self.assertFalse(quilmes["reported"])
        brown = {entry["localidad"]: entry
                 for entry in areas["ALMIRANTE BROWN"]["localidades"]}
        self.assertTrue(brown["SAN JOSE"]["reported"])


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL") and os.environ.get("TEST_GEOREF_LIVE"),
    "Needs isolated PostgreSQL and live GeoRef access",
)
class LiveGeorefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog()

    def test_zona_sur_address(self) -> None:
        zones = georef.resolve_address(
            "calchaqui 100", self.catalog, {}, partido_hint="Quilmes",
        )
        self.assertTrue(zones)
        self.assertEqual(zones[0].partido, "QUILMES")
        self.assertIn(zones[0].granularity, {"partido", "localidad"})

    def test_caba_address(self) -> None:
        zones = georef.resolve_address(
            "rivadavia 1000", self.catalog, {}, partido_hint="CAPITAL",
        )
        self.assertEqual(zones[0].partido, "CAPITAL")
        self.assertIsNone(zones[0].localidad)

    def test_reverse_zona_sur_and_outside_scope(self) -> None:
        zone = georef.resolve_location(-34.76, -58.40, self.catalog, {})
        self.assertEqual(zone.partido, "LOMAS DE ZAMORA")
        with self.assertRaises(georef.GeorefOutsideScope):
            georef.resolve_location(-31.42, -64.18, self.catalog, {})

    def test_unknown_address(self) -> None:
        with self.assertRaises(georef.GeorefNotFound):
            georef.resolve_address("calle inexistente 99999", self.catalog, {})
