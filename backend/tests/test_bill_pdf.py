"""Synthetic PDFs only; no private invoices are used."""

import io
import unittest

from pypdf import PdfWriter
from pypdf.generic import NameObject, TextStringObject

from app.bill_pdf import MAX_FILE_BYTES, InvalidBillPdf, validate_bill_pdf


def document(*, encrypted: bool = False, active: bool = False, pages: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if active:
        writer.root_object[NameObject("/OpenAction")] = TextStringObject("synthetic")
    if encrypted:
        writer.encrypt("synthetic-password")
    result = io.BytesIO()
    writer.write(result)
    return result.getvalue()


class BillPdfTests(unittest.TestCase):
    def test_accept_synthetic_pdf(self) -> None:
        validate_bill_pdf(document())

    def test_reject_encrypted_active_malformed_and_empty(self) -> None:
        for payload in (document(encrypted=True), document(active=True),
                        document(pages=0), b"%PDF-1.7\ninvalid", b"", b"X" * (MAX_FILE_BYTES + 1)):
            with self.subTest(size=len(payload)), self.assertRaises(InvalidBillPdf):
                validate_bill_pdf(payload)
