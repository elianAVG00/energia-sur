"""Synthetic CU07 ASGI/PostgreSQL tests against an explicitly isolated database."""

import os
import unittest
from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import uuid4

import test_api
from sqlalchemy.orm import Session

from app.diary import BUENOS_AIRES
from app.models import ElectricityBill, MeterReading


def instant(local: date) -> datetime:
    return datetime.combine(local, time(12), tzinfo=BUENOS_AIRES).astimezone(UTC)


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ComparisonPostgresTests(test_api.ApiTests):
    async def prepare(self) -> tuple[test_api.Client, str]:
        owner = await self.login()
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        return owner, test_api.string(owner.data()["id"])

    def seed(self, meter_id: str, *, start: date, end: date,
             start_value: str = "1000", end_value: str = "1120",
             period: tuple[date, date] = (date(2026, 11, 1), date(2026, 11, 7)),
             billed: str = "100") -> tuple[str, str, str]:
        bill_id, start_id, end_id = str(uuid4()), str(uuid4()), str(uuid4())
        with Session(self.engine) as db:
            db.add(ElectricityBill(
                id=bill_id, meter_id=meter_id, period_start=period[0], period_end=period[1],
                value_kwh=Decimal(billed), amount_ars=None, file_key="synthetic",
                file_type="application/pdf", version=1,
            ))
            db.add_all([
                MeterReading(id=start_id, meter_id=meter_id, recorded_at=instant(start),
                             value_kwh=Decimal(start_value), photo_key=None, photo_type=None,
                             version=1),
                MeterReading(id=end_id, meter_id=meter_id, recorded_at=instant(end),
                             value_kwh=Decimal(end_value), photo_key=None, photo_type=None,
                             version=1),
            ])
            db.commit()
        return bill_id, start_id, end_id

    async def test_exact_candidates_and_comparison(self) -> None:
        owner, meter = await self.prepare()
        bill, start, end = self.seed(
            meter, start=date(2026, 11, 1), end=date(2026, 11, 30),
            period=(date(2026, 11, 1), date(2026, 11, 30)),
        )
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/bills/{bill}/comparison-candidates"), 200)
        candidates = owner.data()
        self.assertEqual([row["reading_id"] for row in candidates["start_candidates"]], [start])
        self.assertEqual([row["reading_id"] for row in candidates["end_candidates"]], [end])
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/bills/{bill}/comparison"
                    f"?start_reading_id={start}&end_reading_id={end}"), 200)
        result = owner.data()
        self.assertEqual(result["status"], "comparable")
        self.assertTrue(result["exact"])
        self.assertEqual(result["recorded_kwh"], "120")
        self.assertEqual(result["difference_kwh"], "20")
        self.assertEqual(result["outcome"], "recorded_higher")
        self.assertEqual(owner.headers[b"cache-control"], b"no-store")

    async def test_approximate_confirmation_and_eight_day_rejection(self) -> None:
        owner, meter = await self.prepare()
        bill, start, end = self.seed(
            meter, start=date(2026, 10, 25), end=date(2026, 11, 14),
            period=(date(2026, 11, 1), date(2026, 11, 7)),
        )
        path = (f"/meters/{meter}/bills/{bill}/comparison"
                f"?start_reading_id={start}&end_reading_id={end}")
        self.assertEqual(await owner.request("GET", path), 409)
        self.assertEqual(owner.data()["code"], "CONFIRMATION_REQUIRED")
        self.assertEqual(await owner.request("GET", f"{path}&confirm_approximate=true"), 200)
        self.assertFalse(owner.data()["exact"])
        self.assertEqual(owner.data()["recorded_kwh"], "120")

        far_owner, far_meter = await self.prepare()
        far_bill, far_start, far_end = self.seed(
            far_meter, start=date(2026, 10, 24), end=date(2026, 11, 7),
            period=(date(2026, 11, 1), date(2026, 11, 7)),
        )
        self.assertEqual(await far_owner.request(
            "GET", f"/meters/{far_meter}/bills/{far_bill}/comparison"
                    f"?start_reading_id={far_start}&end_reading_id={far_end}&confirm_approximate=true"),
            422)

    async def test_decreasing_duplicate_and_zero_consumption(self) -> None:
        owner, meter = await self.prepare()
        bill, start, end = self.seed(
            meter, start=date(2026, 11, 1), end=date(2026, 11, 7),
            start_value="1200", end_value="1100",
        )
        path = (f"/meters/{meter}/bills/{bill}/comparison"
                f"?start_reading_id={start}&end_reading_id={end}")
        self.assertEqual(await owner.request("GET", path), 200)
        self.assertEqual(owner.data()["status"], "no_comparison")
        self.assertEqual(owner.data()["reason"], "decreasing_reading")
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/bills/{bill}/comparison"
                    f"?start_reading_id={start}&end_reading_id={start}"), 422)

        zero_bill, zero_start, zero_end = self.seed(
            meter, start=date(2026, 11, 3), end=date(2026, 11, 4),
            start_value="1000", end_value="1000",
            period=(date(2026, 11, 3), date(2026, 11, 4)),
        )
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/bills/{zero_bill}/comparison"
                    f"?start_reading_id={zero_start}&end_reading_id={zero_end}"), 200)
        self.assertEqual(owner.data()["recorded_kwh"], "0")
        self.assertEqual(owner.data()["outcome"], "billed_higher")

    async def test_cross_account_isolation(self) -> None:
        owner, meter = await self.prepare()
        bill, start, end = self.seed(
            meter, start=date(2026, 11, 1), end=date(2026, 11, 30),
            period=(date(2026, 11, 1), date(2026, 11, 30)),
        )
        foreign = await self.login(self.username_b)
        for path in (
            f"/meters/{meter}/bills/{bill}/comparison-candidates",
            f"/meters/{meter}/bills/{bill}/comparison"
            f"?start_reading_id={start}&end_reading_id={end}",
        ):
            self.assertEqual(await foreign.request("GET", path), 404)
            self.assertEqual(foreign.data(), {"detail": "El recurso no está disponible."})


if __name__ == "__main__":
    unittest.main()
