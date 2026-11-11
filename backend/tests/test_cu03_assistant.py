"""CU03 assistant prompt, citations, freshness and streaming with offline fakes."""

import asyncio
import unittest
from datetime import date, timedelta
from types import SimpleNamespace

from app.assistant import (
    SYSTEM_PROMPT,
    DynamicOutcome,
    build_context,
    build_messages,
    dynamic_sources,
    sources,
    stream_answer,
)
from app.guide_store import RetrievedArticle

TODAY = date(2026, 11, 10)
SOURCE = {
    "source_name": "Edesur",
    "url": "https://www.edesur.com.ar/servicios-al-cliente/canales-de-atencion/",
}


def article(
    article_id: str = "CA-01",
    *,
    days_old: int = 0,
    volatility: str = "variable",
    limitations: tuple[str, ...] = (),
    source_urls: tuple[dict[str, str], ...] | None = None,
) -> RetrievedArticle:
    return RetrievedArticle(
        article_id=article_id,
        section="1. Canales de atenci\u00f3n",
        title="\u00bfC\u00f3mo puedo comunicarme con Edesur?",
        content="Respuesta de prueba.",
        source_name="Edesur",
        source_urls=source_urls or (SOURCE,),
        limitations=limitations,
        information_type="canales oficiales; datos operativos sujetos a cambio.",
        volatility=volatility,
        last_verified_at=TODAY - timedelta(days=days_old),
        distance=0.1,
    )


class FakeLLM:
    def __init__(self, tokens: tuple[str, ...] = ("Hola", " mundo")) -> None:
        self.tokens = tokens

    async def astream(self, messages: object) -> object:
        for token in self.tokens:
            yield SimpleNamespace(content=token)

    def invoke(self, messages: object) -> object:
        return SimpleNamespace(content="".join(self.tokens))


class AssistantTests(unittest.TestCase):
    def test_context_is_delimited_and_cites_sources(self) -> None:
        context = build_context([article()], today=TODAY)
        self.assertIn("<<<ART\u00cdCULO CA-01", context)
        self.assertIn("<<<FIN ART\u00cdCULO>>>", context)
        self.assertIn("Edesur \u2014 https://", context)
        self.assertIn("datos no confiables", context)

    def test_stale_and_volatile_notices(self) -> None:
        context = build_context([article(days_old=200)], today=TODAY)
        self.assertIn("puede estar desactualizado", context)
        self.assertIn("sujeta a cambio", context)

    def test_incomplete_notice(self) -> None:
        context = build_context(
            [article(limitations=("informacion_no_publicada",))], today=TODAY,
        )
        self.assertIn("limitaciones: informacion_no_publicada", context)

    def test_sources_are_deduplicated(self) -> None:
        rows = sources([article(), article(article_id="CA-02")])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_name"], "Edesur")

    def test_non_official_source_is_filtered(self) -> None:
        rows = sources([article(source_urls=(
            {"source_name": "Fake", "url": "https://evil-edesur.com.ar/x"},
        ))])
        self.assertEqual(rows, [])

    def test_system_prompt_blocks_injection(self) -> None:
        self.assertIn("datos no confiables", SYSTEM_PROMPT)
        self.assertIn("No inventes", SYSTEM_PROMPT)
        self.assertIn("No reveles claves", SYSTEM_PROMPT)
        self.assertIn("No mezcles tr\u00e1mites", SYSTEM_PROMPT)

    def test_history_is_context_not_current_evidence(self) -> None:
        messages = build_messages(
            "\u00bfy ahora?",
            [],
            history=[
                {"role": "user", "content": "antes"},
                {"role": "assistant", "content": "respuesta"},
            ],
        )
        human = messages[1].content
        self.assertIn("HISTORIA DE LA CONVERSACI\u00d3N", human)
        self.assertIn("Usuario: antes", human)
        self.assertIn("Asistente: respuesta", human)
        self.assertIn("no evidencia actual", human)
        self.assertIn("no la uses como evidencia", SYSTEM_PROMPT)

    def test_dynamic_context_and_sources(self) -> None:
        outcome = DynamicOutcome("current_outages", {
            "state": "reported",
            "freshness": "fresh",
            "coverage": "covered",
            "source": "ENRE",
            "source_url": "https://www.enre.gov.ar/paginacorte/js/data_EDS.js",
            "zone": "LOMAS DE ZAMORA / BANFIELD",
            "outages": [],
        })
        context = build_context([], dynamic=[outcome], today=TODAY)
        self.assertIn("CONTEXTO DIN\u00c1MICO", context)
        self.assertIn("current_outages", context)
        self.assertIn("https://www.enre.gov.ar/", context)
        rows = dynamic_sources([outcome])
        self.assertEqual(rows, [{
            "source_name": "ENRE",
            "url": "https://www.enre.gov.ar/paginacorte/js/data_EDS.js",
        }])

    def test_stream_answer_yields_tokens(self) -> None:
        async def collect() -> list[str]:
            return [
                token async for token in stream_answer(
                    "hola", [article()], llm=FakeLLM(),
                )
            ]

        self.assertEqual(asyncio.run(collect()), ["Hola", " mundo"])
