from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from current_run import ROOT, RUN
from report_content import TITLE, REFERENCES, SUBTITLE, article_blocks, config_rows, ranking_rows, report_sections


ASSETS = ROOT / "tmp" / "report_assets"
OUT = ROOT / "Informes" / "docx"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE = OUT / "Informe_Proyecto_Investigacion_Parques_Solares.docx"
ARTICLE = OUT / "Articulo_Catedra_Parques_Solares.docx"
BLACK = "222222"


def keep(paragraph, next_paragraph=False):
    props = paragraph._p.get_or_add_pPr()
    props.append(OxmlElement("w:keepLines"))
    if next_paragraph:
        props.append(OxmlElement("w:keepNext"))


def configure(doc, article=False):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(10.5 if article else 11.5)
    normal.font.color.rgb = RGBColor.from_string(BLACK)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08 if article else 1.12
    for name, size in (("Title", 21), ("Heading 1", 15), ("Heading 2", 12.5)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(BLACK)
        style.paragraph_format.keep_with_next = True
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.2)
    section.left_margin = section.right_margin = Cm(2.2)


def add_title(doc, title, subtitle):
    paragraph = doc.add_paragraph(style="Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(title)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(subtitle)
    run.italic = True
    run.font.size = Pt(13)


def add_heading(doc, text, level=1):
    paragraph = doc.add_heading(text, level=level)
    keep(paragraph, True)
    return paragraph


def add_paragraph(doc, text, italic=False):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(text)
    run.italic = italic
    keep(paragraph)
    return paragraph


def add_table(doc, rows, widths=None):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    if widths:
        table.autofit = False
        for column, width in zip(table.columns, widths):
            column.width = Cm(width)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text = str(value)
            if widths:
                cell.width = Cm(widths[j])
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(1)
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.4)
                    run.bold = i == 0
            if i == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "E6E6E6")
                cell._tc.get_or_add_tcPr().append(shading)
    header_props = table.rows[0]._tr.get_or_add_trPr()
    header_props.append(OxmlElement("w:tblHeader"))
    return table


def add_figure(doc, filename, caption, width=15.5):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(ASSETS / filename), width=Cm(width))
    keep(paragraph, True)
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = caption_paragraph.add_run(caption)
    run.italic = True
    run.font.size = Pt(9)
    keep(caption_paragraph)


def add_page_number(section):
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def set_columns(section, count=2, spacing_twips=567):
    section_properties = section._sectPr
    columns = section_properties.find(qn("w:cols"))
    if columns is None:
        columns = OxmlElement("w:cols")
        section_properties.append(columns)
    columns.set(qn("w:num"), str(count))
    columns.set(qn("w:space"), str(spacing_twips))


def article_paragraph(doc, text, size=12, italic=False, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=4):
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    keep(paragraph)
    return paragraph


def article_heading(doc, text, abstract=False):
    return article_paragraph(doc, text, size=10 if abstract else 12, bold=True,
                             align=WD_ALIGN_PARAGRAPH.LEFT, after=2)


def build_profile():
    doc = Document()
    configure(doc)
    add_title(doc, TITLE, SUBTITLE)
    add_paragraph(doc, f"Informe actualizado a partir de la corrida {RUN['metadata']['run_id']}", italic=True).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    add_heading(doc, "Contenido", 1)
    for title, _ in report_sections():
        add_paragraph(doc, title)
    doc.add_page_break()
    for title, paragraphs in report_sections():
        add_heading(doc, title, 1)
        for text in paragraphs:
            add_paragraph(doc, text)
        if title == "4 Objetivos":
            add_figure(doc, "figura_arquitectura.png", "Figura 1. Relación entre el problema territorial, el modelo y las salidas.")
        elif title == "7 Diseño experimental":
            add_table(doc, config_rows(), [5.2, 10.2])
            add_paragraph(doc, "Tabla 1. Configuración efectiva registrada por la corrida.", italic=True).alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_figure(doc, "figura_convergencia.png", "Figura 2. Evolución del mejor fitness visto y del fitness medio.")
        elif title == "8 Resultados":
            add_figure(doc, "figura_mapa_territorial.png", "Figura 3. Distribución de las cinco alternativas territoriales sin superposición.", 11.5)
            add_heading(doc, "8.1 Ranking territorial", 2)
            add_table(doc, ranking_rows(RUN["territorial"]), [1.0, 1.2, 1.5, 1.5, 0.9, 1.3, 1.3, 1.5, 1.3])
            add_paragraph(doc, "Tabla 2. TOP 5 territorial. Solar en kWh/m²/año; distancias en km.", italic=True).alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_figure(doc, "figura_componentes_fitness.png", "Figura 4. Contribución ponderada de los cinco componentes.")
    add_heading(doc, "Referencias", 1)
    for reference in REFERENCES:
        add_paragraph(doc, reference)
    add_page_number(doc.sections[0])
    doc.save(PROFILE)


def build_article():
    doc = Document()
    configure(doc, article=True)
    for section in doc.sections:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.top_margin = section.bottom_margin = Cm(2.5)
        section.left_margin = section.right_margin = Cm(2.5)

    title = article_paragraph(doc, TITLE, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    title.style = doc.styles["Title"]
    title.runs[0].font.size = Pt(16)
    article_paragraph(doc, "", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    article_paragraph(doc, "Universidad Tecnológica Nacional",
                      size=12, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

    two_column = doc.add_section(WD_SECTION.CONTINUOUS)
    two_column.page_width, two_column.page_height = Cm(21), Cm(29.7)
    two_column.top_margin = two_column.bottom_margin = Cm(2.5)
    two_column.left_margin = two_column.right_margin = Cm(2.5)
    set_columns(two_column, 2, 567)

    for title_text, paragraphs in article_blocks():
        is_front = title_text in {"Abstract", "Palabras Clave"}
        article_heading(doc, title_text, abstract=is_front)
        for paragraph in paragraphs:
            article_paragraph(doc, paragraph, size=10 if is_front else 12,
                              italic=title_text == "Abstract", after=5)
        if title_text == "Resultados":
            add_figure(doc, "figura_mapa_territorial.png", "Figura 1. TOP 5 territorial sin superposición.", 7.3)
            compact_rows = [["Puesto", "ET", "Línea km", "ET km", "Fitness"]]
            for row in RUN["territorial"].itertuples():
                compact_rows.append([str(int(row.rank)), row.station_id, f"{row.distance_to_power_line_km:.2f}",
                                     f"{row.distance_to_transformer_km:.2f}", f"{row.fitness:.4f}"])
            compact_table = add_table(doc, compact_rows, [1.1, 1.0, 1.6, 1.4, 1.5])
            for row_index, row in enumerate(compact_table.rows):
                cannot_split = OxmlElement("w:cantSplit")
                row._tr.get_or_add_trPr().append(cannot_split)
                if row_index < len(compact_table.rows) - 1:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            keep(paragraph, True)
            article_paragraph(doc, "Tabla 1. Resultados territoriales; distancias en km.", size=10,
                              italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    article_heading(doc, "Referencias", abstract=True)
    for reference in REFERENCES:
        article_paragraph(doc, reference, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, after=2)
    doc.save(ARTICLE)


if __name__ == "__main__":
    build_profile()
    build_article()
    print(PROFILE)
    print(ARTICLE)
