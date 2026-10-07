from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, SimpleDocTemplate, Table, TableStyle,
)

from current_run import ROOT, RUN
from report_content import TITLE, SUBTITLE, REFERENCES, article_blocks, config_rows, ranking_rows, report_sections


ASSETS = ROOT / "tmp" / "report_assets"
OUT = ROOT / "Informes" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE = OUT / "Informe_Proyecto_Investigacion_Parques_Solares.pdf"
ARTICLE = OUT / "Articulo_Catedra_Parques_Solares.pdf"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("titlex", parent=base["Title"], fontName="Times-Bold", fontSize=21, leading=24, alignment=TA_CENTER, spaceAfter=14),
        "subtitle": ParagraphStyle("subtitlex", parent=base["Normal"], fontName="Times-Italic", fontSize=13, leading=16, alignment=TA_CENTER, spaceAfter=12),
        "h1": ParagraphStyle("h1x", parent=base["Heading1"], fontName="Times-Bold", fontSize=15, leading=18, spaceBefore=12, spaceAfter=6, keepWithNext=True),
        "h2": ParagraphStyle("h2x", parent=base["Heading2"], fontName="Times-Bold", fontSize=12, leading=14, spaceBefore=9, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("bodyx", parent=base["BodyText"], fontName="Times-Roman", fontSize=10.4, leading=13.1, alignment=TA_JUSTIFY, spaceAfter=6),
        "small": ParagraphStyle("smallx", parent=base["BodyText"], fontName="Times-Roman", fontSize=8.2, leading=9.7, spaceAfter=2),
        "caption": ParagraphStyle("captionx", parent=base["BodyText"], fontName="Times-Italic", fontSize=8.7, leading=10.3, alignment=TA_CENTER, spaceAfter=7),
        "ref": ParagraphStyle("refx", parent=base["BodyText"], fontName="Times-Roman", fontSize=6.8, leading=7.7, leftIndent=8, firstLineIndent=-8, spaceAfter=1),
        "article_h": ParagraphStyle("articlehx", parent=base["Heading2"], fontName="Times-Bold", fontSize=12, leading=13.5, spaceBefore=5, spaceAfter=2, keepWithNext=True),
        "article_body": ParagraphStyle("articlebodyx", parent=base["BodyText"], fontName="Times-Roman", fontSize=12, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=5),
        "article_front_h": ParagraphStyle("articlefronthx", parent=base["Heading2"], fontName="Times-Bold", fontSize=10, leading=11.5, spaceBefore=4, spaceAfter=2, keepWithNext=True),
        "article_abstract": ParagraphStyle("articleabstractx", parent=base["BodyText"], fontName="Times-Italic", fontSize=10, leading=11.5, alignment=TA_JUSTIFY, spaceAfter=5),
        "article_small": ParagraphStyle("articlesmallx", parent=base["BodyText"], fontName="Times-Roman", fontSize=10, leading=11.5, alignment=TA_JUSTIFY, spaceAfter=5),
        "article_ref": ParagraphStyle("articlerefx", parent=base["BodyText"], fontName="Times-Roman", fontSize=10, leading=11.3, leftIndent=7, firstLineIndent=-7, spaceAfter=2),
        "article_caption": ParagraphStyle("articlecaptionx", parent=base["BodyText"], fontName="Times-Italic", fontSize=10, leading=11.2, alignment=TA_CENTER, spaceAfter=5),
    }


S = styles()


def p(text, style="body"):
    return Paragraph(text.replace("&", "&amp;"), S[style])


def table(rows, widths, font_size=7.5):
    result = Table(rows, colWidths=[width * cm for width in widths], repeatRows=1, hAlign="CENTER")
    result.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 1.4),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return result


def figure(filename, width_cm, caption, caption_style="caption"):
    image = Image(str(ASSETS / filename))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth = width_cm * cm
    image.drawHeight = width_cm * ratio * cm
    return KeepTogether([image, p(caption, caption_style)])


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, str(document.page))
    canvas.restoreState()


def build_profile():
    doc = SimpleDocTemplate(str(PROFILE), pagesize=A4, rightMargin=2.2 * cm, leftMargin=2.2 * cm,
                            topMargin=2.1 * cm, bottomMargin=1.8 * cm, title=TITLE)
    story = [p(TITLE, "title"), p(SUBTITLE, "subtitle"),
             p(f"Informe actualizado a partir de la corrida {RUN['metadata']['run_id']}", "subtitle"), PageBreak(),
             p("Contenido", "h1")]
    story.extend(p(title) for title, _ in report_sections())
    story.append(PageBreak())
    for title, paragraphs in report_sections():
        story.append(p(title, "h1"))
        story.extend(p(text) for text in paragraphs)
        if title == "4 Objetivos":
            story.append(figure("figura_arquitectura.png", 16, "Figura 1. Relación entre el problema territorial, el modelo y las salidas."))
        elif title == "7 Diseño experimental":
            story.extend([table(config_rows(), [5.0, 10.2], 8.1), p("Tabla 1. Configuración efectiva registrada por la corrida.", "caption"),
                          figure("figura_convergencia.png", 16, "Figura 2. Evolución del mejor fitness visto y del fitness medio.")])
        elif title == "8 Resultados":
            story.extend([figure("figura_mapa_territorial.png", 10.2, "Figura 3. Cinco alternativas territoriales sin superposición."),
                          p("8.1 Ranking territorial", "h2"),
                          table(ranking_rows(RUN["territorial"]), [0.8, 1.0, 1.25, 1.25, 0.7, 1.1, 1.1, 1.25, 1.1], 6.9),
                          p("Tabla 2. TOP 5 territorial. Solar en kWh/m²/año; distancias en km.", "caption"),
                          figure("figura_componentes_fitness.png", 16, "Figura 4. Contribución ponderada de los cinco componentes.")])
    story.append(p("Referencias", "h1"))
    story.extend(p(reference, "ref") for reference in REFERENCES)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_article():
    page_width, page_height = A4
    margin = 2.5 * cm
    gap = 1.0 * cm
    column_width = (page_width - 2 * margin - gap) / 2
    first_top = page_height - margin - 4.2 * cm
    first_height = first_top - margin
    later_height = page_height - 2 * margin

    first_frames = [
        Frame(margin, margin, column_width, first_height, id="first_left", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(margin + column_width + gap, margin, column_width, first_height, id="first_right", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ]
    later_frames = [
        Frame(margin, margin, column_width, later_height, id="left", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(margin + column_width + gap, margin, column_width, later_height, id="right", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ]

    def first_page(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setFont("Times-Bold", 16)
        title_lines = ["Optimización de configuraciones contiguas", "para parques solares en Santa Fe"]
        y = page_height - margin - 8
        for line in title_lines:
            canvas.drawCentredString(page_width / 2, y, line)
            y -= 19
        y -= 16  # La línea de autores queda intencionalmente en blanco para evaluación ciega.
        canvas.setFont("Times-BoldItalic", 12)
        canvas.drawCentredString(page_width / 2, y, "Universidad Tecnológica Nacional")
        canvas.restoreState()

    doc = BaseDocTemplate(str(ARTICLE), pagesize=A4, rightMargin=margin, leftMargin=margin,
                          topMargin=margin, bottomMargin=margin, title=TITLE)
    doc.addPageTemplates([
        PageTemplate(id="first", frames=first_frames, onPage=first_page),
        PageTemplate(id="later", frames=later_frames),
    ])
    story = [NextPageTemplate("later")]
    for title_text, paragraphs in article_blocks():
        front = title_text in {"Abstract", "Palabras Clave"}
        story.append(p(title_text, "article_front_h" if front else "article_h"))
        for paragraph in paragraphs:
            story.append(p(paragraph, "article_abstract" if title_text == "Abstract" else "article_small" if front else "article_body"))
        if title_text == "Resultados":
            story.append(figure("figura_mapa_territorial.png", 7.1, "Figura 1. TOP 5 territorial sin superposición.", "article_caption"))
            compact_rows = [["Puesto", "ET", "Línea km", "ET km", "Fitness"]]
            for row in RUN["territorial"].itertuples():
                compact_rows.append([str(int(row.rank)), row.station_id, f"{row.distance_to_power_line_km:.2f}",
                                     f"{row.distance_to_transformer_km:.2f}", f"{row.fitness:.4f}"])
            story.append(KeepTogether([
                table(compact_rows, [1.05, 0.8, 1.55, 1.35, 1.45], 7.4),
                p("Tabla 1. Resultados territoriales; distancias en km.", "article_caption"),
            ]))
    story.append(p("Referencias", "article_front_h"))
    story.extend(p(reference, "article_ref") for reference in REFERENCES)
    doc.build(story)


if __name__ == "__main__":
    build_profile()
    build_article()
    print(PROFILE)
    print(ARTICLE)
