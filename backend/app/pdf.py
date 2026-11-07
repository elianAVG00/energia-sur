"""On-demand Unicode report rendering from already authorized domain results."""

from io import BytesIO
from pathlib import Path
from threading import Lock
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.diary import DiaryReport

_FONT_LOCK = Lock()


def render_pdf(address: str, report: DiaryReport) -> bytes:
    with _FONT_LOCK:
        if "DiaryVera" not in pdfmetrics.getRegisteredFontNames():
            font_path = Path(reportlab.__file__).parent / "fonts" / "Vera.ttf"
            pdfmetrics.registerFont(TTFont("DiaryVera", str(font_path)))
    style = ParagraphStyle("Diary", fontName="DiaryVera", fontSize=8, leading=11)

    def paragraph(text: str) -> Paragraph:
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    def stamp(value: object) -> str:
        # Callers pass named-zone datetime objects from the domain report.
        return str(value).replace("T", " ")[:16]

    content = BytesIO()
    document = SimpleDocTemplate(
        content, pagesize=landscape(A4), leftMargin=25, rightMargin=25,
        topMargin=25, bottomMargin=25, title="Diario de interrupciones",
    )
    table_rows = [[paragraph(x) for x in (
        "Inicio", "Fin", "Estado", "Observaciones", "Reclamo",
    )]]
    for row in report.rows:
        cut = row.interruption
        table_rows.append([paragraph(x) for x in (
            stamp(cut.start_at),
            stamp(cut.end_at) if cut.end_at is not None else "En curso",
            "Cerrado" if cut.end_at is not None else "En curso",
            cut.observations or "", cut.complaint_number or "",
        )])
    table = Table(
        table_rows, colWidths=[115, 115, 65, 330, 115], repeatRows=1,
        splitByRow=1, splitInRow=1,
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce8ef")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ]))
    document.build([
        paragraph("Diario de interrupciones"),
        paragraph(f"Domicilio: {address}"),
        paragraph(f"Período: {stamp(report.period.start_at)} a {stamp(report.period.end_at)}"),
        paragraph("Hora de Buenos Aires"),
        paragraph(f"Total sin servicio: {report.hours} h {report.minutes} min"),
        Spacer(1, 12), table,
    ])
    return content.getvalue()
