"""Synthetic, storage-independent CU05 value and retry identity checks."""

import unittest
from datetime import UTC, datetime

from app.readings import (
    MAX_READING_DIGITS,
    canonical_kwh,
    creation_fingerprint,
    is_decreasing,
    reading_instant,
)


class ReadingPrimitivesTest(unittest.TestCase):
    def test_decimal_is_exact_and_canonical(self) -> None:
        self.assertEqual(canonical_kwh("00056538"), "56538")
        self.assertEqual(canonical_kwh("000"), "0")
        self.assertEqual(canonical_kwh("9" * MAX_READING_DIGITS), "9" * MAX_READING_DIGITS)

    def test_invalid_inputs_are_rejected(self) -> None:
        for value in ("", "-1", "+1", "1.0", " 1", "１", "9" * (MAX_READING_DIGITS + 1)):
            with self.subTest(value=value[:20]), self.assertRaises(ValueError):
                canonical_kwh(value)

    def test_fingerprint_preserves_payload_identity(self) -> None:
        original = creation_fingerprint("2026-01-01T00:00:00Z", "01", b"synthetic")
        self.assertEqual(original, creation_fingerprint("2026-01-01T00:00:00Z", "01", b"synthetic"))
        self.assertNotEqual(original, creation_fingerprint("2026-01-01T00:00:00Z", "1", b"synthetic"))
        self.assertNotEqual(original, creation_fingerprint("2026-01-01T00:00:00Z", "01", b"other"))
        self.assertNotEqual(original, creation_fingerprint("2026-01-01T00:00:00Z", "01", None))
        self.assertNotEqual(original, creation_fingerprint("2026-01-02T00:00:00Z", "01", b"synthetic"))
        self.assertNotEqual(
            creation_fingerprint("2026-01-01T00:00:00Z", "1", None),
            creation_fingerprint("2026-01-01T00:00:00Z", "1", b""),
        )
        self.assertNotEqual(
            creation_fingerprint("a", "12", None), creation_fingerprint("a1", "2", None),
        )

    def test_exact_large_decrease_comparison(self) -> None:
        self.assertTrue(is_decreasing("9" * 5000, "1" + "0" * 5000))
        self.assertFalse(is_decreasing("0001", "1"))
        self.assertFalse(is_decreasing("10", "9"))

    def test_timestamp_normalization_and_future(self) -> None:
        now = datetime(2026, 11, 7, 15, 0, tzinfo=UTC)
        self.assertEqual(reading_instant("2026-11-07T12:00:00-03:00", now=now), now)
        self.assertEqual(reading_instant("2026-11-07T16:00:00+01:00", now=now), now)
        for value in (
            "2026-11-07T15:00:01Z", "2026-11-07T15:00:00.0Z",
            "2026-11-07T15:00:00", "2026-11-07T15:00Z", "not-a-date",
            "2026-01-01T00:00:00+00:99", "2026-01-01T00:00:00+24:00",
            "2026-02-30T00:00:00Z", "0001-01-01T00:00:00+23:59",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reading_instant(value, now=now)


if __name__ == "__main__":
    unittest.main()
