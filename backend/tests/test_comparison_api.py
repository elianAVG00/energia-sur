"""CU07 adapter tests with synthetic objects, without database claims."""

import json
import unittest
from datetime import UTC, date, datetime, time
from decimal import Decimal
from unittest.mock import Mock

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api import Actor
from app.comparison_api import CandidatesOut, ComparisonOut, compare, comparison_candidates
from app.diary import BUENOS_AIRES
from app.models import Account, ElectricityBill, MeterReading, WebSession


def reading(identifier: str, local: date, value: str) -> MeterReading:
    instant = datetime.combine(local, time(12, 0), tzinfo=BUENOS_AIRES).astimezone(UTC)
    return MeterReading(
        id=identifier, meter_id="meter", recorded_at=instant,
        value_kwh=Decimal(value), photo_key=None, photo_type=None, version=1,
    )


def bill(start: date = date(2026, 11, 1), end: date = date(2026, 11, 7),
         value: str = "100") -> ElectricityBill:
    return ElectricityBill(
        id="bill", meter_id="meter", period_start=start, period_end=end,
        value_kwh=Decimal(value), amount_ars=None, file_key="synthetic-key",
        file_type="application/pdf", version=1,
    )


class ComparisonApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock(spec=Session)
        self.actor = Actor(Account(id="account", username="synthetic", password_hash="unused"),
                           WebSession())

    def test_missing_and_foreign_bill_is_not_disclosed(self) -> None:
        self.db.scalar.return_value = None
        with self.assertRaises(HTTPException) as error:
            compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 404)
        query = str(self.db.scalar.call_args.args[0])
        self.assertIn("es_meters.account_id", query)

    def test_missing_or_foreign_reading_is_not_disclosed(self) -> None:
        self.db.scalar.side_effect = [bill(), None]
        with self.assertRaises(HTTPException) as error:
            compare("meter", "bill", "foreign", "end", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_exact_comparison_returns_exact_values(self) -> None:
        self.db.scalar.side_effect = [
            bill(), reading("start", date(2026, 11, 1), "1000"),
            reading("end", date(2026, 11, 7), "1120"),
        ]
        result = compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertIsInstance(result, ComparisonOut)
        assert isinstance(result, ComparisonOut)
        self.assertEqual(result.status, "comparable")
        self.assertTrue(result.exact)
        self.assertEqual(result.recorded_kwh, "120")
        self.assertEqual(result.difference_kwh, "20")
        self.assertEqual(result.outcome, "recorded_higher")
        self.assertNotIn("percentage", result.model_dump())

    def test_approximate_requires_and_accepts_confirmation(self) -> None:
        points = [
            bill(), reading("start", date(2026, 10, 25), "1000"),
            reading("end", date(2026, 11, 14), "1120"),
        ]
        self.db.scalar.side_effect = list(points)
        self.db.scalars.return_value = []
        pending = compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertIsInstance(pending, JSONResponse)
        assert isinstance(pending, JSONResponse)
        self.assertEqual(pending.status_code, 409)
        body = json.loads(pending.body)
        self.assertEqual(body["code"], "CONFIRMATION_REQUIRED")
        self.assertEqual(body["start_local_date"], "2026-10-25")
        self.assertEqual(body["end_local_date"], "2026-11-14")

        self.db.scalar.side_effect = list(points)
        result = compare("meter", "bill", "start", "end", self.actor, self.db,
                         confirm_approximate=True)
        self.assertIsInstance(result, ComparisonOut)
        assert isinstance(result, ComparisonOut)
        self.assertEqual(result.status, "comparable")
        self.assertFalse(result.exact)
        self.assertEqual(result.recorded_kwh, "120")

    def test_eight_day_difference_is_rejected(self) -> None:
        self.db.scalar.side_effect = [
            bill(), reading("start", date(2026, 10, 24), "1000"),
            reading("end", date(2026, 11, 7), "1120"),
        ]
        with self.assertRaises(HTTPException) as error:
            compare("meter", "bill", "start", "end", self.actor, self.db,
                    confirm_approximate=True)
        self.assertEqual(error.exception.status_code, 422)

    def test_duplicate_or_reversed_selection_is_rejected(self) -> None:
        self.db.scalar.side_effect = [
            bill(), reading("same", date(2026, 11, 1), "1000"),
            reading("same", date(2026, 11, 7), "1120"),
        ]
        with self.assertRaises(HTTPException) as error:
            compare("meter", "bill", "same", "same", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 422)

        self.db.scalar.side_effect = [
            bill(), reading("start", date(2026, 11, 5), "1000"),
            reading("end", date(2026, 11, 2), "1120"),
        ]
        with self.assertRaises(HTTPException) as error:
            compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertEqual(error.exception.status_code, 422)

    def test_decreasing_reading_returns_no_comparison(self) -> None:
        self.db.scalar.side_effect = [
            bill(), reading("start", date(2026, 11, 1), "1200"),
            reading("end", date(2026, 11, 7), "1100"),
        ]
        result = compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertIsInstance(result, ComparisonOut)
        assert isinstance(result, ComparisonOut)
        self.assertEqual(result.status, "no_comparison")
        self.assertEqual(result.reason, "decreasing_reading")
        self.assertIsNone(result.recorded_kwh)
        self.assertIsNone(result.difference_kwh)

    def test_zero_consumption_is_valid(self) -> None:
        self.db.scalar.side_effect = [
            bill(), reading("start", date(2026, 11, 1), "1000"),
            reading("end", date(2026, 11, 7), "1000"),
        ]
        result = compare("meter", "bill", "start", "end", self.actor, self.db)
        self.assertIsInstance(result, ComparisonOut)
        assert isinstance(result, ComparisonOut)
        self.assertEqual(result.recorded_kwh, "0")
        self.assertEqual(result.difference_kwh, "100")
        self.assertEqual(result.outcome, "billed_higher")

    def test_candidates_use_local_window(self) -> None:
        target = bill(start=date(2026, 11, 1), end=date(2026, 11, 30))
        self.db.scalar.return_value = target
        self.db.scalars.return_value = [
            reading("start", date(2026, 11, 1), "1000"),
            reading("end", date(2026, 11, 30), "1120"),
        ]
        result = comparison_candidates("meter", "bill", self.actor, self.db)
        self.assertIsInstance(result, CandidatesOut)
        assert isinstance(result, CandidatesOut)
        self.assertEqual([row.reading_id for row in result.start_candidates], ["start"])
        self.assertEqual([row.reading_id for row in result.end_candidates], ["end"])
        self.assertEqual(result.billed_kwh, "100")


if __name__ == "__main__":
    unittest.main()
