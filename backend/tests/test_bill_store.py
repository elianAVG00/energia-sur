"""Synthetic CU06 create fingerprint regression tests."""

import unittest
from dataclasses import replace
from datetime import date

from app.bill_confirmation import file_digest
from app.bill_store import BillInput, creation_fingerprint


class BillFingerprintTests(unittest.TestCase):
    def test_creation_fingerprint_binds_values_and_confirmation(self) -> None:
        payload = BillInput(date(2026, 1, 1), date(2026, 1, 31), "1.125", None,
                            "create", file_digest(b"synthetic"), None)
        fingerprint = creation_fingerprint("meter-a", payload)
        variants = (
            replace(payload, start=date(2026, 1, 2)),
            replace(payload, end=date(2026, 2, 1)),
            replace(payload, value_kwh="1.126"),
            replace(payload, amount_ars="0"),
            replace(payload, file_digest=file_digest(b"different")),
            replace(payload, overlap_token="confirmation"),
        )
        self.assertNotEqual(fingerprint, creation_fingerprint("meter-b", payload))
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(fingerprint, creation_fingerprint("meter-a", variant))


if __name__ == "__main__":
    unittest.main()
