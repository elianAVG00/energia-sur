"""CU05 read adapter tests using synthetic objects, without database claims."""

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import Actor, current, database
from app.main import app
from app.models import Account, MeterReading, WebSession
from app.reading_api import get_reading, list_readings, reading_out
from tests.test_api import Client


class ReadingApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock(spec=Session)
        self.actor = Actor(Account(id="account", username="synthetic", password_hash="unused"),
                           WebSession())
        self.row = MeterReading(
            id="reading", meter_id="meter", recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
            value_kwh=Decimal("9007199254740993"), photo_key=None, photo_type=None, version=1,
        )

    def test_value_is_serialized_without_precision_loss(self) -> None:
        output = reading_out(self.row)
        self.assertEqual(output.value_kwh, "9007199254740993")
        self.assertEqual(output.recorded_at, "2026-01-01T00:00:00Z")
        self.row.value_kwh = Decimal("1.00")
        self.assertEqual(reading_out(self.row).value_kwh, "1")

    def test_unowned_meter_is_not_disclosed(self) -> None:
        self.db.scalar.return_value = None
        with self.assertRaises(HTTPException) as error:
            list_readings("foreign", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 404)
        self.db.scalars.assert_not_called()
        query = str(self.db.scalar.call_args.args[0])
        self.assertIn("es_meters.account_id", query)

    def test_missing_reading_is_not_disclosed(self) -> None:
        self.db.scalar.side_effect = [object(), None]
        with self.assertRaises(HTTPException) as error:
            get_reading("meter", "missing", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_list_retains_server_order(self) -> None:
        self.db.scalar.return_value = object()
        self.db.scalars.return_value = [self.row]
        self.assertEqual(list_readings("meter", self.actor, self.db)[0].id, "reading")
        self.assertIn("ORDER BY es_meter_readings.recorded_at DESC", str(self.db.scalars.call_args.args[0]))


class ReadingHttpTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.db = Mock(spec=Session)
        self.actor = Actor(Account(id="account", username="synthetic", password_hash="unused"),
                           WebSession())
        app.dependency_overrides[database] = lambda: self.db
        self.addCleanup(app.dependency_overrides.clear)

    async def test_unauthenticated_request_is_rejected_without_cache(self) -> None:
        client = Client()
        self.assertEqual(await client.request("GET", "/meters/meter/readings"), 401)
        self.assertEqual(client.headers.get(b"cache-control"), b"no-store")

    async def test_owned_and_foreign_responses_do_not_cache(self) -> None:
        app.dependency_overrides[current] = lambda: self.actor
        client = Client()
        self.db.scalar.return_value = None
        self.assertEqual(await client.request("GET", "/meters/foreign/readings"), 404)
        self.assertEqual(client.headers.get(b"cache-control"), b"no-store")
        self.db.scalar.return_value = object()
        self.db.scalars.return_value = []
        self.assertEqual(await client.request("GET", "/meters/meter/readings"), 200)
        self.assertEqual(client.headers.get(b"cache-control"), b"no-store")

    async def test_http_detail_serializes_nonempty_synthetic_row(self) -> None:
        app.dependency_overrides[current] = lambda: self.actor
        self.db.scalar.side_effect = [object(), MeterReading(
            id="reading", meter_id="meter", recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
            value_kwh=Decimal("9007199254740993.00"), photo_key=None, photo_type=None, version=1,
        )]
        client = Client()
        self.assertEqual(await client.request("GET", "/meters/meter/readings/reading"), 200)
        self.assertEqual(client.data()["value_kwh"], "9007199254740993")
        self.assertEqual(client.headers.get(b"cache-control"), b"no-store")


if __name__ == "__main__":
    unittest.main()
