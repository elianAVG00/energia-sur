"""CU03 guide parser: real guide, article units, metadata and fail-closed."""

import tempfile
import unittest
from pathlib import Path

from app.guide_parser import GUIDE_PATH, GuideParseError, parse_guide


class GuideParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = parse_guide()

    def test_metadata_and_counts(self) -> None:
        self.assertEqual(self.guide.document_id, "energia-sur-kb-edesur-001")
        self.assertEqual(self.guide.version, "1.0.0")
        self.assertEqual(self.guide.last_verified_at.isoformat(), "2026-11-10")
        self.assertEqual(len(self.guide.articles), 53)
        self.assertEqual(len({article.section for article in self.guide.articles}), 9)

    def test_article_ids_and_order(self) -> None:
        ids = [article.article_id for article in self.guide.articles]
        self.assertEqual(len(set(ids)), 53)
        self.assertEqual(ids[0], "CA-01")
        self.assertEqual(ids[-1], "LI-04")
        for article in self.guide.articles:
            self.assertRegex(
                article.article_id, r"^(CA|PA|CO|TS|EL|EE|CR|TR|LI)-\d{2}$",
            )
            self.assertTrue(article.title)
            self.assertTrue(article.content)

    def test_mixed_organism_provenance(self) -> None:
        ts01 = next(a for a in self.guide.articles if a.article_id == "TS-01")
        names = {ref.name for ref in ts01.source_urls}
        self.assertIn("Edesur", names)
        self.assertIn("Argentina.gob.ar / ENRE", names)
        self.assertTrue(
            all(ref.url.startswith("https://") for ref in ts01.source_urls),
        )

    def test_incomplete_and_volatile_metadata(self) -> None:
        pa07 = next(a for a in self.guide.articles if a.article_id == "PA-07")
        self.assertIn("informacion_no_publicada", pa07.limitations)
        tr03 = next(a for a in self.guide.articles if a.article_id == "TR-03")
        self.assertIn("documentacion_parcial", tr03.limitations)
        tr04 = next(a for a in self.guide.articles if a.article_id == "TR-04")
        self.assertIn("documentacion_parcial", tr04.limitations)
        ca01 = next(a for a in self.guide.articles if a.article_id == "CA-01")
        self.assertEqual(ca01.volatility, "variable")
        ts01 = next(a for a in self.guide.articles if a.article_id == "TS-01")
        self.assertEqual(ts01.volatility, "revalidate")

    def test_capability_statement_has_no_source(self) -> None:
        li01 = next(a for a in self.guide.articles if a.article_id == "LI-01")
        self.assertEqual(li01.source_urls, ())

    def test_no_false_positive_limit_marker(self) -> None:
        pa01 = next(a for a in self.guide.articles if a.article_id == "PA-01")
        self.assertNotIn("limite", pa01.limitations)

    def test_non_official_source_is_dropped(self) -> None:
        text = GUIDE_PATH.read_text(encoding="utf-8")
        broken = text.replace(
            "**Fuente principal:** https://www.edesur.com.ar/servicios-al-cliente/canales-de-atencion/",
            "**Fuente principal:** https://evil-edesur.com.ar/phishing",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text(broken, encoding="utf-8")
            guide = parse_guide(path)
        ca01 = next(a for a in guide.articles if a.article_id == "CA-01")
        self.assertNotIn(
            "https://evil-edesur.com.ar/phishing",
            {ref.url for ref in ca01.source_urls},
        )
        self.assertIn("fuente_no_oficial", ca01.limitations)

    def test_frontmatter_and_index_are_not_chunks(self) -> None:
        for article in self.guide.articles:
            self.assertNotIn("document_id:", article.content)
            self.assertNotIn("document_id:", article.title)
            self.assertNotIn("\u00cdndice de fuentes", article.section)

    def test_fail_closed_on_missing_article(self) -> None:
        text = GUIDE_PATH.read_text(encoding="utf-8")
        broken = text.replace("### CA-01 \u2014", "### ZZ-01 \u2014")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaises(GuideParseError):
                parse_guide(path)

    def test_fail_closed_on_unexpected_document_id(self) -> None:
        text = GUIDE_PATH.read_text(encoding="utf-8")
        broken = text.replace(
            "document_id: energia-sur-kb-edesur-001",
            "document_id: otro-documento",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaises(GuideParseError):
                parse_guide(path)

    def test_fail_closed_on_bad_frontmatter(self) -> None:
        text = GUIDE_PATH.read_text(encoding="utf-8")
        broken = text.replace('version: "1.0.0"', "version:")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaises(GuideParseError):
                parse_guide(path)
