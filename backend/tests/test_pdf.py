"""Inspect generated PDF content, Unicode and multipage tables with synthetic data."""

import unittest
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader

from app.diary import BUENOS_AIRES, Interruption, ReportPeriod, generate_report
from app.pdf import render_pdf


def local(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=BUENOS_AIRES)


class PdfTests(unittest.TestCase):
    def test_unicode_optional_text_order_and_ongoing_end(self) -> None:
        records = [
            Interruption("early", "D", local("2026-11-01T10:00"), local("2026-11-01T11:00"), "Observación <segura> & energía", "TEST-001"),
            Interruption("later", "D", local("2026-11-01T12:00")),
        ]
        report = generate_report(domicile_id="D", interruptions=records,
            period=ReportPeriod(local("2026-11-01T00:00"), local("2026-11-02T00:00")),
            clock=lambda: local("2026-11-01T13:30"))
        content = render_pdf("Domicilio sintético Álvarez", report)
        self.assertTrue(content.startswith(b"%PDF-"))
        text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
        for expected in ("Álvarez", "Observación <segura> & energía", "TEST-001", "En curso", "2 h 30 min", "2026-11-02 00:00"):
            self.assertIn(expected, text)
        self.assertLess(text.index("2026-11-01 12:00"), text.index("2026-11-01 10:00"))
        self.assertIn("Cerrado", text)
        self.assertEqual(text.count("En curso"), 2)  # End cell AND ongoing status.

    def test_long_rows_and_repeated_headers_span_pages(self) -> None:
        records = [Interruption(str(i), "D", local("2026-11-01T10:00"), local("2026-11-01T11:00"),
            ("Observación sintética larga con espacios. " * 90)[:4000], str(i)) for i in range(6)]
        report = generate_report(domicile_id="D", interruptions=records,
            period=ReportPeriod(local("2026-11-01T00:00"), local("2026-11-02T00:00")),
            clock=lambda: local("2026-11-07T12:00"))
        reader = PdfReader(BytesIO(render_pdf("D" * 300, report)))
        self.assertGreater(len(reader.pages), 1)
        for page in reader.pages:
            self.assertIn("Inicio", page.extract_text())
        self.assertIn("1 h 0 min", reader.pages[0].extract_text())
