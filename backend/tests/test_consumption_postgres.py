"""Synthetic CU08 ASGI/PostgreSQL tests against an explicitly isolated database."""

import os
import unittest
from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import uuid4

import test_api
from sqlalchemy.orm import Session

from app.diary import BUENOS_AIRES
from app.models import MeterReading


def instant(local: date, hour: int = 12) -> datetime:
    return datetime.combine(local, time(hour), tzinfo=BUENOS_AIRES).astimezone(UTC)


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class ConsumptionPostgresTests(test_api.ApiTests):
    async def prepare(self) -> tuple[test_api.Client, str]:
        owner = await self.login()
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        return owner, test_api.string(owner.data()["id"])

    def seed(self, meter_id: str, readings: list[tuple[date, str]]) -> list[str]:
        ids: list[str] = []
        with Session(self.engine) as db:
            for local, value in readings:
                row = MeterReading(id=str(uuid4()), meter_id=meter_id, recorded_at=instant(local),
                                   value_kwh=Decimal(value), photo_key=None, photo_type=None,
                                   version=1)
                db.add(row)
                ids.append(row.id)
            db.commit()
        return ids

    async def test_evolution_and_estimate(self) -> None:
        owner, meter = await self.prepare()
        self.seed(meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1020"),
                          (date(2026, 11, 7), "1080")])
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-evolution"), 200)
        data = owner.data()
        self.assertEqual(data["meter_id"], meter)
        self.assertEqual([(i["consumption_kwh"], i["daily_average_kwh_day"]) for i in data["intervals"]],
                         [("20", "10"), ("60", "15")])
        self.assertEqual(owner.headers[b"cache-control"], b"no-store")

        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-estimate?days=7"), 200)
        estimate = owner.data()
        self.assertEqual(estimate["estimate_kwh"], "105")
        self.assertEqual(estimate["daily_average_kwh_day"], "15")
        self.assertTrue(estimate["orientative"])

    async def test_date_filter_is_inclusive_and_whole_interval(self) -> None:
        owner, meter = await self.prepare()
        self.seed(meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 6), "1030")])
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-evolution?from=2026-11-02&to=2026-11-03"), 200)
        data = owner.data()
        # The 11-01 -> 11-06 interval crosses the range, so it is included whole.
        self.assertEqual(len(data["intervals"]), 1)
        self.assertEqual(data["intervals"][0]["start_local_date"], "2026-11-01")
        self.assertEqual(data["intervals"][0]["end_local_date"], "2026-11-06")

    async def test_decreasing_insufficient_and_zero(self) -> None:
        owner, meter = await self.prepare()
        self.seed(meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1080"),
                          (date(2026, 11, 7), "1020")])
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-evolution"), 200)
        self.assertFalse(owner.data()["intervals"][1]["calculable"])
        self.assertIsNone(owner.data()["intervals"][1]["consumption_kwh"])
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-estimate?days=7"), 200)
        self.assertEqual(owner.data()["status"], "base_unavailable")
        self.assertEqual(owner.data()["reason"], "decreasing_latest")

        empty, empty_meter = await self.prepare()
        self.seed(empty_meter, [(date(2026, 11, 1), "1000")])
        self.assertEqual(await empty.request(
            "GET", f"/meters/{empty_meter}/consumption-estimate?days=7"), 200)
        self.assertEqual(empty.data()["reason"], "insufficient_readings")

        zero, zero_meter = await self.prepare()
        self.seed(zero_meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1000")])
        self.assertEqual(await zero.request(
            "GET", f"/meters/{zero_meter}/consumption-estimate?days=30"), 200)
        self.assertEqual(zero.data()["estimate_kwh"], "0")
        self.assertFalse(zero.data()["below_minimum"])

    async def test_out_of_range_horizon_is_rejected(self) -> None:
        owner, meter = await self.prepare()
        self.seed(meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1020")])
        for days in (0, 91):
            self.assertEqual(await owner.request(
                "GET", f"/meters/{meter}/consumption-estimate?days={days}"), 422)
        self.assertEqual(await owner.request(
            "GET", f"/meters/{meter}/consumption-estimate?days=90"), 200)
        self.assertEqual(owner.data()["estimate_kwh"], "900")

    async def test_cross_account_isolation(self) -> None:
        owner, meter = await self.prepare()
        self.seed(meter, [(date(2026, 11, 1), "1000"), (date(2026, 11, 3), "1020")])
        foreign = await self.login(self.username_b)
        for path in (
            f"/meters/{meter}/consumption-evolution",
            f"/meters/{meter}/consumption-estimate?days=7",
        ):
            self.assertEqual(await foreign.request("GET", path), 404)
            self.assertEqual(foreign.data(), {"detail": "El recurso no está disponible."})


if __name__ == "__main__":
    unittest.main()
