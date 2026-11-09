"""Synthetic tests for exact CU06 bill domain input."""

import unittest
from datetime import date

from app.bills import calendar_date, decimal_value, overlaps, period


class BillInputTests(unittest.TestCase):
    def test_dates_and_inclusive_overlap(self) -> None:
        self.assertEqual(period("2026-11-07", "2026-11-07"), (date(2026, 11, 7),) * 2)
        self.assertTrue(overlaps(date(2026, 11, 1), date(2026, 11, 7),
                                 date(2026, 11, 7), date(2026, 11, 10)))
        self.assertFalse(overlaps(date(2026, 11, 1), date(2026, 11, 6),
                                  date(2026, 11, 7), date(2026, 11, 10)))
        for value in ("2026-2-01", "2026-02-29", "0000-01-01", "2026-01-01Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calendar_date(value)
        with self.assertRaises(ValueError):
            period("2026-11-08", "2026-11-07")

    def test_exact_decimal(self) -> None:
        self.assertEqual(decimal_value("0001.125", 3), "1.125")
        self.assertEqual(decimal_value("0.00", 2), "0")
        self.assertEqual(decimal_value("9" * 18, 3), "9" * 18)
        for value in ("-1", "+1", "1e3", "1.1234", "1.", ".1", "9" * 19, "１", "NaN"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decimal_value(value, 3)
        with self.assertRaises(ValueError):
            decimal_value("1.001", 2)


if __name__ == "__main__":
    unittest.main()
