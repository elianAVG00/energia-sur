"""Synthetic CU06 transport validation tests, without database or files."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.bill_api import BillCreate, BillEdit, _payload


class BillTransportInputTests(unittest.TestCase):
    def test_extra_fields_and_strict_version_rejected(self) -> None:
        data = {"period_start": "2026-01-01", "period_end": "2026-01-31",
                "value_kwh": "1.125", "amount_ars": None, "version": True,
                "file_action": "keep", "file_base64": None}
        with self.assertRaises(ValidationError):
            BillEdit.model_validate(data)
        with self.assertRaises(ValidationError):
            BillCreate.model_validate({**data, "file_base64": "abc"})

    def test_keep_and_replace_file_consistency(self) -> None:
        base = {"period_start": "2026-01-01", "period_end": "2026-01-31",
                "value_kwh": "1.125", "amount_ars": None, "version": 1}
        keep = BillEdit.model_validate({**base, "file_action": "keep"})
        payload, data, content_type = _payload(keep)
        self.assertEqual(payload.file_action, "keep")
        self.assertIsNone(data)
        self.assertIsNone(content_type)
        for update in ({"file_action": "replace"},
                       {"file_action": "keep", "file_base64": "YQ=="}):
            with self.subTest(update=update), self.assertRaises(HTTPException) as error:
                _payload(BillEdit.model_validate({**base, **update}))
            self.assertEqual(error.exception.status_code, 422)

    def test_create_decoded_bytes_and_canonical_values(self) -> None:
        model = BillCreate.model_validate({"period_start": "2026-01-01",
            "period_end": "2026-01-31", "value_kwh": "001.120", "amount_ars": "0.00",
            "file_base64": "eA=="})
        with patch("app.bill_api._decode", return_value=(b"x", "application/pdf")):
            payload, data, content_type = _payload(model)
        self.assertEqual((payload.value_kwh, payload.amount_ars), ("1.12", "0"))
        self.assertEqual((data, content_type), (b"x", "application/pdf"))


if __name__ == "__main__":
    unittest.main()
