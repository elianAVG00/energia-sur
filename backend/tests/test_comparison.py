"""Synthetic domain tests for exact CU07 comparison values."""

import unittest
from datetime import UTC, date, datetime
from decimal import Decimal

from app import comparison


class ComparisonDomainTests(unittest.TestCase):
    def test_local_date_uses_buenos_aires(self) -> None:
        self.assertEqual(comparison.local_date(datetime(2026, 11, 1, 1, 0, tzinfo=UTC)),
                         date(2026, 10, 31))
        self.assertEqual(comparison.local_date(datetime(2026, 11, 1, 3, 0, tzinfo=UTC)),
                         date(2026, 11, 1))

    def test_window_is_seven_days_inclusive(self) -> None:
        boundary = date(2026, 11, 1)
        self.assertTrue(comparison.in_window(date(2026, 10, 25), boundary))
        self.assertTrue(comparison.in_window(date(2026, 11, 8), boundary))
        self.assertFalse(comparison.in_window(date(2026, 10, 24), boundary))
        self.assertFalse(comparison.in_window(date(2026, 11, 9), boundary))

    def test_canonical_has_no_rounding(self) -> None:
        self.assertEqual(comparison.canonical(Decimal("10.000")), "10")
        self.assertEqual(comparison.canonical(Decimal("1.125")), "1.125")
        self.assertEqual(comparison.canonical(Decimal("0")), "0")
        self.assertEqual(comparison.canonical(Decimal("-0")), "0")

    def test_recorded_higher_billed_higher_and_equal(self) -> None:
        self.assertEqual(
            comparison.compare_values(Decimal("1000"), Decimal("1120"), Decimal("100")),
            comparison.Values("120", "20", "recorded_higher"),
        )
        self.assertEqual(
            comparison.compare_values(Decimal("1000"), Decimal("1080"), Decimal("100")),
            comparison.Values("80", "20", "billed_higher"),
        )
        self.assertEqual(
            comparison.compare_values(Decimal("1000"), Decimal("1100"), Decimal("100")),
            comparison.Values("100", "0", "equal"),
        )

    def test_zero_consumption_and_fractional_billed_value(self) -> None:
        self.assertEqual(
            comparison.compare_values(Decimal("1000"), Decimal("1000"), Decimal("100")),
            comparison.Values("0", "100", "billed_higher"),
        )
        self.assertEqual(
            comparison.compare_values(Decimal("1000"), Decimal("1120"), Decimal("100.125")),
            comparison.Values("120", "19.875", "recorded_higher"),
        )

    def test_decreasing_reading_is_rejected(self) -> None:
        with self.assertRaises(comparison.DecreasingReading):
            comparison.compare_values(Decimal("1200"), Decimal("1100"), Decimal("100"))

    def test_large_readings_are_exact_beyond_default_precision(self) -> None:
        huge = Decimal("9" * 30)
        values = comparison.compare_values(Decimal("0"), huge, Decimal("1"))
        self.assertEqual(values.recorded_kwh, "9" * 30)
        self.assertEqual(values.difference_kwh, "9" * 29 + "8")
        self.assertEqual(values.outcome, "recorded_higher")

    def test_window_clamps_at_date_extremes(self) -> None:
        self.assertEqual(comparison.window(date.min), (date.min, date(1, 1, 8)))
        self.assertEqual(comparison.window(date.max), (date(9999, 12, 24), date.max))


if __name__ == "__main__":
    unittest.main()
