"""CU03 PostgreSQL/pgvector integration: ingest, idempotency, versions, retrieval."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session

from app.guide_parser import GUIDE_PATH
from app.guide_store import guide_status, ingest_guide, retrieve
from app.models import GuideChunk, GuideDocument

URL = os.environ.get("TEST_DATABASE_URL", "")
DIMENSION = 1536


class CategoryEmbedder:
    """Deterministic offline embedder: one dimension per guide category."""

    SECTIONS = (
        ("1. Canales", 0), ("2. Opciones de pago", 1), ("3. Calcul", 2),
        ("4. Tarifa Social", 3), ("5. Electrodependientes", 4),
        ("6. Eficiencia", 5), ("7. Cortes", 6), ("8. Tr\u00e1mites", 7),
        ("9. Alcance", 8),
    )
    QUERIES = (
        ("tel\u00e9fono", 0), ("contacto", 0), ("comunicarme", 0), ("canal", 0),
        ("pago", 1), ("factura", 1), ("pagar", 1),
        ("kwh", 2), ("consumo", 2), ("calcul", 2),
        ("tarifa social", 3), ("subsidio", 3),
        ("recs", 4), ("electrodependiente", 4),
        ("ahorro", 5), ("eficiencia", 5), ("led", 5),
        ("corte", 6), ("reclamo", 6),
        ("titularidad", 7), ("tr\u00e1mite", 7), ("tramite", 7),
        ("alcance", 8), ("l\u00edmite", 8), ("limite", 8),
    )

    def _vector(self, value: str) -> list[float]:
        lowered = value.lower()
        dimension = 9
        for marker, index in self.SECTIONS:
            if marker.lower() in lowered:
                dimension = index
                break
        else:
            for marker, index in self.QUERIES:
                if marker in lowered:
                    dimension = index
                    break
        vector = [0.0] * DIMENSION
        vector[dimension] = 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(item) for item in texts]

    def embed_query(self, value: str) -> list[float]:
        return self._vector(value)


@unittest.skipUnless(
    URL.startswith("postgresql+psycopg://"), "TEST_DATABASE_URL is not configured",
)
class GuidePostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(URL)
        with cls.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            present = connection.execute(
                text("SELECT to_regclass('es_guide_chunks')"),
            ).scalar()
            if present is None:
                raise unittest.SkipTest("0007_cu03 migration is not applied")
        cls.embedder = CategoryEmbedder()
        cls._clean()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": URL})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self._clean()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._clean()
        cls.engine.dispose()

    @classmethod
    def _clean(cls) -> None:
        with Session(cls.engine) as db:
            db.execute(delete(GuideChunk))
            db.execute(delete(GuideDocument))
            db.commit()

    def test_ingest_retrieve_idempotent_and_versions(self) -> None:
        first = ingest_guide(embedder=self.embedder)
        self.assertEqual(first.outcome, "indexed")
        status = guide_status()
        self.assertIsNotNone(status)
        self.assertEqual(status.article_count, 53)

        again = ingest_guide(embedder=self.embedder)
        self.assertEqual(again.outcome, "unchanged")

        cases = (
            ("\u00bfCu\u00e1l es el tel\u00e9fono de Edesur?", "CA"),
            ("\u00bfC\u00f3mo pago la factura?", "PA"),
            ("\u00bfC\u00f3mo calculo los kWh?", "CO"),
            ("\u00bfQu\u00e9 es la tarifa social?", "TS"),
            ("\u00bfQu\u00e9 es el RECS?", "EL"),
            ("\u00bfC\u00f3mo ahorro energ\u00eda?", "EE"),
            ("\u00bfC\u00f3mo consulto un corte?", "CR"),
            ("\u00bfC\u00f3mo cambio la titularidad?", "TR"),
            ("\u00bfCu\u00e1l es el alcance de la gu\u00eda?", "LI"),
        )
        for question, prefix in cases:
            results = retrieve(question, embedder=self.embedder, limit=3)
            self.assertTrue(results, question)
            self.assertTrue(
                results[0].article_id.startswith(prefix),
                f"{question}: {results[0].article_id}",
            )
            self.assertTrue(results[0].source_urls or results[0].article_id == "LI-01")

        off_topic = retrieve(
            "\u00bfCu\u00e1l es la capital de Francia?", embedder=self.embedder,
        )
        self.assertEqual(off_topic, [])

        original = GUIDE_PATH.read_text(encoding="utf-8")
        updated = original.replace('version: "1.0.0"', 'version: "1.0.1"')
        updated = updated.replace(
            "### CA-01 \u2014 \u00bfC\u00f3mo puedo comunicarme con Edesur?",
            "### CA-01 \u2014 \u00bfC\u00f3mo puedo comunicarme con Edesur? (v1.0.1)",
        )
        updated = updated.replace(
            "**Tipo de informaci\u00f3n:** canales oficiales; datos operativos sujetos a cambio.",
            "**Tipo de informaci\u00f3n:** canales oficiales; datos operativos sujetos a cambio. (v1.0.1)",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text(updated, encoding="utf-8")
            versioned = ingest_guide(path, embedder=self.embedder)
            self.assertEqual(versioned.outcome, "indexed")
            self.assertEqual(guide_status().current_version, "1.0.1")
            results = retrieve(
                "\u00bfCu\u00e1l es el tel\u00e9fono de Edesur?",
                embedder=self.embedder, limit=53,
            )
            self.assertTrue(any("v1.0.1" in row.title for row in results))
            with Session(self.engine) as db:
                stored = db.scalar(select(GuideChunk).where(
                    GuideChunk.article_id == "CA-01",
                    GuideChunk.is_active.is_(True),
                ))
                self.assertIsNotNone(stored)
                self.assertIn("(v1.0.1)", stored.information_type)

        older = ingest_guide(embedder=self.embedder)
        self.assertEqual(older.outcome, "skipped_older")
        self.assertEqual(guide_status().current_version, "1.0.1")
