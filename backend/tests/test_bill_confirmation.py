"""Synthetic overlap-token binding and canonicalization regression tests."""

import unittest
from dataclasses import replace
from datetime import date

from app.bill_confirmation import (
    Confirmation,
    Overlap,
    confirmation_token,
    file_digest,
    matches_confirmation,
)


class BillConfirmationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = b"synthetic-confirmation-secret-32bytes"
        self.overlap = Overlap("bill-a", 1, date(2026, 1, 1), date(2026, 1, 7))
        self.confirmation = Confirmation(
            "account-a", "meter-a", "edit", "bill-b", 2,
            date(2026, 1, 7), date(2026, 1, 10), "1.125", "0.01",
            "replace", file_digest(b"synthetic file"), (self.overlap,),
        )

    def test_all_bound_fields_invalidate_confirmation(self) -> None:
        original = self.confirmation
        token = confirmation_token(self.secret, original)
        self.assertTrue(matches_confirmation(self.secret, original, token))
        changes = (
            {"account_id": "account-b"}, {"meter_id": "meter-b"},
            {"operation": "create"}, {"bill_id": "bill-c"}, {"version": 3},
            {"start": date(2026, 1, 6)}, {"end": date(2026, 1, 11)},
            {"value_kwh": "1.126"}, {"amount_ars": None},
            {"file_action": "keep", "file_digest": None},
            {"file_digest": file_digest(b"different synthetic file")},
            {"overlaps": ()},
            {"overlaps": (replace(self.overlap, version=2),)},
            {"overlaps": (replace(self.overlap, start=date(2025, 12, 31)),)},
            {"overlaps": (replace(self.overlap, end=date(2026, 1, 8)),)},
            {"overlaps": (replace(self.overlap, bill_id="bill-z"),)},
        )
        for change in changes:
            with self.subTest(change=change):
                self.assertFalse(matches_confirmation(self.secret, replace(original, **change), token))

    def test_order_is_canonical_and_invalid_tokens_fail(self) -> None:
        other = Overlap("bill-c", 1, date(2026, 1, 9), date(2026, 1, 11))
        first = replace(self.confirmation, overlaps=(self.overlap, other))
        second = replace(first, overlaps=(other, self.overlap))
        token = confirmation_token(self.secret, first)
        self.assertTrue(matches_confirmation(self.secret, second, token))
        self.assertFalse(matches_confirmation(self.secret, second, "é" * 64))
        self.assertFalse(matches_confirmation(self.secret, second, "0" * 64))
        with self.assertRaises(ValueError):
            confirmation_token(b"short", first)
        with self.assertRaises(ValueError):
            confirmation_token(self.secret, replace(first, file_digest=None))


if __name__ == "__main__":
    unittest.main()
