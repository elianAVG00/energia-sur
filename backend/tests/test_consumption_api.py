"""CU08 adapter tests with synthetic objects, without database claims."""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import Actor
from app.consumption_api import (
    EstimateOut,
    EstimateUnavailableOut,
    EvolutionOut,
    consumption_estimate,
    consumption_evolution,
)
from app.diary import BUENOS_AIRES
from app.models import Account, Meter, MeterReading, WebSession


def meter() -> Meter:
    return Meter(id="meter", domicile_id="domicile", account_id="account",
                 meter_number="M-1", alias=None, version=1)


def reading(identifier: str, local: datetime, value: str) -> MeterReading:
    return MeterReading(
        id=identifier, meter_id="meter", recorded_at=local,
        value_kwh=Decimal(value), photo_key=None, photo_type=None, version=1,
    )


def local(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=BUENOS_AIRES)


class ConsumptionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock(spec=Session)
        self.actor = Actor(Account(id="account", username="synthetic", password_hash="unused"),
                           WebSession())

    def test_missing_or_foreign_meter_is_not_disclosed(self) -> None:
        self.db.scalar.return_value = None
        with self.assertRaises(HTTPException) as error:
            consumption_evolution("meter", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 404)
        query = str(self.db.scalar.call_args.args[0])
        self.assertIn("es_meters.account_id", query)
        with self.assertRaises(HTTPException) as error:
            consumption_estimate("meter", self.actor, self.db, days=7)
        self.assertEqual(error.exception.status_code, 404)

    def test_evolution_returns_intervals(self) -> None:
        self.db.scalar.return_value = meter()
        self.db.scalars.return_value = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
            reading("c", local(2026, 11, 7), "1080"),
        ]
        result = consumption_evolution("meter", self.actor, self.db)
        self.assertIsInstance(result, EvolutionOut)
        assert isinstance(result, EvolutionOut)
        self.assertEqual(result.meter_id, "meter")
        self.assertEqual([(i.consumption_kwh, i.daily_average_kwh_day) for i in result.intervals],
                         [("20", "10"), ("60", "15")])
        self.assertTrue(all(i.calculable for i in result.intervals))

    def test_evolution_filters_by_inclusive_date_range(self) -> None:
        self.db.scalar.return_value = meter()
        self.db.scalars.return_value = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
            reading("c", local(2026, 11, 7), "1080"),
        ]
        result = consumption_evolution(
            "meter", self.actor, self.db, from_=date(2026, 11, 4), to=date(2026, 11, 7))
        assert isinstance(result, EvolutionOut)
        self.assertEqual([i.start_reading_id for i in result.intervals], ["b"])

    def test_reversed_date_range_is_rejected(self) -> None:
        self.db.scalar.return_value = meter()
        with self.assertRaises(HTTPException) as error:
            consumption_evolution("meter", self.actor, self.db,
                                  from_=date(2026, 11, 7), to=date(2026, 11, 1))
        self.assertEqual(error.exception.status_code, 422)

    def test_estimate_returns_value(self) -> None:
        self.db.scalar.return_value = meter()
        self.db.scalars.return_value = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
            reading("c", local(2026, 11, 7), "1080"),
        ]
        result = consumption_estimate("meter", self.actor, self.db, days=7)
        self.assertIsInstance(result, EstimateOut)
        assert isinstance(result, EstimateOut)
        self.assertEqual(result.estimate_kwh, "105")
        self.assertEqual(result.daily_average_kwh_day, "15")
        self.assertTrue(result.orientative)
        self.assertFalse(result.below_minimum)

    def test_insufficient_readings_returns_unavailable(self) -> None:
        self.db.scalar.return_value = meter()
        self.db.scalars.return_value = [reading("a", local(2026, 11, 1), "1000")]
        result = consumption_estimate("meter", self.actor, self.db, days=7)
        self.assertIsInstance(result, EstimateUnavailableOut)
        assert isinstance(result, EstimateUnavailableOut)
        self.assertEqual(result.reason, "insufficient_readings")

    def test_decreasing_latest_returns_unavailable_without_fallback(self) -> None:
        self.db.scalar.return_value = meter()
        self.db.scalars.return_value = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1080"),
            reading("c", local(2026, 11, 7), "1020"),
        ]
        result = consumption_estimate("meter", self.actor, self.db, days=7)
        self.assertIsInstance(result, EstimateUnavailableOut)
        assert isinstance(result, EstimateUnavailableOut)
        self.assertEqual(result.reason, "decreasing_latest")


if __name__ == "__main__":
    unittest.main()
