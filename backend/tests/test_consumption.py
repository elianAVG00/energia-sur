"""Synthetic domain tests for CU08 deterministic evolution and estimation."""

import unittest
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app import consumption
from app.diary import BUENOS_AIRES


def reading(identifier: str, local: datetime, value: str) -> consumption.Reading:
    return consumption.Reading(identifier, local, Decimal(value))


def local(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=BUENOS_AIRES)


class ConsumptionDomainTests(unittest.TestCase):
    def test_local_date_uses_buenos_aires(self) -> None:
        self.assertEqual(consumption.local_date(datetime(2026, 11, 1, 1, tzinfo=UTC)),
                         date(2026, 10, 31))
        self.assertEqual(consumption.local_date(datetime(2026, 11, 1, 3, tzinfo=UTC)),
                         date(2026, 11, 1))

    def test_canonical_has_no_rounding(self) -> None:
        self.assertEqual(consumption.canonical(Decimal("10.000")), "10")
        self.assertEqual(consumption.canonical(Decimal("1.125")), "1.125")
        self.assertEqual(consumption.canonical(Decimal("0")), "0")
        self.assertEqual(consumption.canonical(Decimal("15")), "15")

    def test_two_intervals_from_three_readings(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
            reading("c", local(2026, 11, 7), "1080"),
        ]
        intervals = consumption.build_intervals(rows)
        self.assertEqual(len(intervals), 2)
        first, second = intervals
        self.assertTrue(first.calculable)
        self.assertEqual(first.consumption_kwh, "20")
        self.assertEqual(first.daily_average_kwh_day, "10")
        self.assertTrue(second.calculable)
        self.assertEqual(second.consumption_kwh, "60")
        self.assertEqual(second.daily_average_kwh_day, "15")

    def test_irregular_and_same_day_intervals(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1, 0), "1000"),
            reading("b", local(2026, 11, 6, 0), "1030"),
            reading("c", local(2026, 11, 6, 12), "1038"),
        ]
        intervals = consumption.build_intervals(rows)
        self.assertEqual(len(intervals), 2)
        first, second = intervals
        self.assertFalse(first.sub_day)
        self.assertEqual(first.consumption_kwh, "30")
        self.assertEqual(first.daily_average_kwh_day, "6")
        self.assertTrue(second.sub_day)
        self.assertEqual(second.consumption_kwh, "8")
        self.assertEqual(second.daily_average_kwh_day, "16")

    def test_estimate_uses_last_interval(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
            reading("c", local(2026, 11, 7), "1080"),
        ]
        estimate = consumption.build_estimate(rows, 7)
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate.daily_average_kwh_day, "15")
        self.assertEqual(estimate.estimate_kwh, "105")
        self.assertEqual(estimate.start.id, "b")
        self.assertEqual(estimate.end.id, "c")
        self.assertFalse(estimate.sub_day)
        self.assertFalse(estimate.below_minimum)

    def test_decreasing_last_interval_yields_no_estimate(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1080"),
            reading("c", local(2026, 11, 7), "1020"),
        ]
        self.assertIsNone(consumption.build_estimate(rows, 7))

    def test_decreasing_interval_is_visible_but_not_calculable(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1080"),
            reading("c", local(2026, 11, 7), "1020"),
        ]
        intervals = consumption.build_intervals(rows)
        self.assertEqual(len(intervals), 2)
        first, second = intervals
        self.assertTrue(first.calculable)
        self.assertEqual(first.consumption_kwh, "80")
        self.assertFalse(second.calculable)
        self.assertIsNone(second.consumption_kwh)
        self.assertIsNone(second.daily_average_kwh_day)

    def test_zero_interval_and_zero_estimate(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1000"),
        ]
        intervals = consumption.build_intervals(rows)
        self.assertEqual(len(intervals), 1)
        self.assertTrue(intervals[0].calculable)
        self.assertEqual(intervals[0].consumption_kwh, "0")
        self.assertEqual(intervals[0].daily_average_kwh_day, "0")
        self.assertFalse(intervals[0].below_minimum)
        estimate = consumption.build_estimate(rows, 90)
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate.estimate_kwh, "0")
        self.assertFalse(estimate.below_minimum)

    def test_below_minimum_threshold(self) -> None:
        self.assertTrue(consumption.below_minimum(Decimal("0.004")))
        self.assertTrue(consumption.below_minimum(Decimal("0.004999")))
        self.assertFalse(consumption.below_minimum(Decimal("0.005")))
        self.assertFalse(consumption.below_minimum(Decimal("0.01")))
        self.assertFalse(consumption.below_minimum(Decimal("0")))

    def test_insufficient_readings_yield_no_estimate(self) -> None:
        self.assertIsNone(consumption.build_estimate([], 7))
        self.assertIsNone(consumption.build_estimate(
            [reading("a", local(2026, 11, 1), "1000")], 7))

    def test_large_readings_keep_precision(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "0"),
            reading("b", local(2026, 11, 3), "9" * 30),
        ]
        intervals = consumption.build_intervals(rows)
        self.assertEqual(intervals[0].consumption_kwh, "9" * 30)

    def test_estimate_scales_with_horizon(self) -> None:
        rows = [
            reading("a", local(2026, 11, 1), "1000"),
            reading("b", local(2026, 11, 3), "1020"),
        ]
        one = consumption.build_estimate(rows, 1)
        ninety = consumption.build_estimate(rows, 90)
        assert one is not None and ninety is not None
        self.assertEqual(one.estimate_kwh, "10")
        self.assertEqual(ninety.estimate_kwh, "900")

    def test_estimate_daily_average_below_minimum_is_flagged(self) -> None:
        start = local(2026, 1, 1)
        end = start + timedelta(days=400)
        rows = [
            reading("a", start, "0"),
            reading("b", end, "1"),
        ]
        estimate = consumption.build_estimate(rows, 30)
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertTrue(estimate.daily_average_below_minimum)
        self.assertFalse(estimate.below_minimum)


if __name__ == "__main__":
    unittest.main()
