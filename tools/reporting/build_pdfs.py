from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "tmp" / "report_assets"
OUT = ROOT / "Informes" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE = OUT / "Informe_Proyecto_Investigacion_Parques_Solares.pdf"
ARTICLE = OUT / "Articulo_Catedra_Parques_Solares.pdf"


def load_run_summary() -> dict:
    metadata = json.loads((ROOT / "results" / "optimization_run.json").read_text(encoding="utf-8"))
    candidates = pd.read_csv(ROOT / "results" / "candidate_locations.csv")
    ranking = pd.read_csv(ROOT / "results" / "ranking.csv").sort_values("rank")
    valid = candidates[candidates.valid.astype(bool)].copy()
    valid["fitness"] = (
        metadata["fitness_weights"]["weight_solar"] * valid.solar_score
        + metadata["fitness_weights"]["weight_grid_distance"] * valid.grid_proximity_score
        + metadata["fitness_weights"]["weight_transformer_distance"] * valid.transformer_proximity_score
    )
    exhaustive = valid.nlargest(10, "fitness")
    ga_ids = ranking.grid_cell_id.astype(int).tolist()
    exhaustive_ids = exhaustive.grid_cell_id.astype(int).tolist()
    return {
        "metadata": metadata, "ranking": ranking, "total": len(candidates), "valid": len(valid),
        "excluded": len(candidates) - len(valid),
        "excluded_pct": 100 * (len(candidates) - len(valid)) / len(candidates),
        "first": ranking.iloc[0], "solar_min": ranking.solar_annual_kwh_m2.min(),
        "solar_max": ranking.solar_annual_kwh_m2.max(),
        "zero_lines": int((ranking.distance_to_power_line_km == 0).sum()),
        "exhaustive_best": exhaustive.iloc[0],
        "overlap": len(set(ga_ids) & set(exhaustive_ids)),
    }


RUN = load_run_summary()


REFERENCES = [
    "[1] J. H. Holland, Adaptation in Natural and Artificial Systems. University of Michigan Press, 1975.",
    "[2] D. E. Goldberg, Genetic Algorithms in Search, Optimization and Machine Learning. Addison-Wesley, 1989.",
    "[3] M. Srinivas y L. M. Patnaik, Genetic algorithms: a survey, Computer, vol. 27, no. 6, pp. 17-26, 1994. https://doi.org/10.1109/2.294849",
    "[4] J. Malczewski, GIS-based multicriteria decision analysis: a survey of the literature, International Journal of Geographical Information Science, vol. 20, no. 7, pp. 703-726, 2006. https://doi.org/10.1080/13658810600661508",
    "[5] M. Uyan, GIS-based solar farms site selection using analytic hierarchy process in Karapinar region, Renewable and Sustainable Energy Reviews, vol. 28, pp. 11-17, 2013. https://doi.org/10.1016/j.rser.2013.07.042",
    "[6] H. Z. Al Garni y A. Awasthi, Solar PV power plant site selection using a GIS-AHP based approach with application in Saudi Arabia, Applied Energy, vol. 206, pp. 1225-1240, 2017. https://doi.org/10.1016/j.apenergy.2017.10.024",
    "[7] J. Munoz-Sabater et al., ERA5-Land: a state-of-the-art global reanalysis dataset for land applications, Earth System Science Data, vol. 13, pp. 4349-4383, 2021. https://doi.org/10.5194/essd-13-4349-2021",
    "[8] Copernicus Climate Change Service y ECMWF, ERA5-Land hourly Analysis Ready Cloud Optimised data on single levels from 1950 to present Product User Guide, 2026. https://confluence.ecmwf.int/spaces/CKB/pages/536218894/",
    "[9] Instituto Geografico Nacional, Unidades Territoriales. Datos Argentina. https://datos.gob.ar/ar/dataset/ign-unidades-territoriales",
    "[10] Jefatura de Gabinete de Ministros, Localidades BAHRA. Datos Argentina. https://datos.gob.ar/dataset/jgm-servicio-normalizacion-datos-geograficos/archivo/jgm_8.21",
    "[11] Secretaria de Energia, Redes de distribucion electrica. Datos Argentina. https://datos.gob.ar/dataset/energia-redes-distribucion-electrica",
    "[12] Secretaria de Energia, Transporte Electrico AT Estaciones Transformadoras. Datos Argentina. https://www.datos.gob.ar/dataset/energia-transporte-electrico-at-estaciones-transformadoras",
    "[13] OpenStreetMap contributors, Copyright and License. https://www.openstreetmap.org/copyright",
]


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="ProfileTitle", fontName="Times-Bold", fontSize=21, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#222222"), spaceAfter=14))
    s.add(ParagraphStyle(name="ProfileSubtitle", fontName="Times-Italic", fontSize=13, leading=16, alignment=TA_CENTER, spaceAfter=12))
    s.add(ParagraphStyle(name="H1x", fontName="Times-Bold", fontSize=16, leading=19, spaceBefore=12, spaceAfter=7, keepWithNext=True))
    s.add(ParagraphStyle(name="H2x", fontName="Times-Bold", fontSize=13, leading=16, spaceBefore=9, spaceAfter=5, keepWithNext=True))
    s.add(ParagraphStyle(name="Bodyx", fontName="Times-Roman", fontSize=11.5, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=6))
    s.add(ParagraphStyle(name="Smallx", fontName="Times-Roman", fontSize=9.3, leading=11.1, alignment=TA_LEFT, spaceAfter=3))
    s.add(ParagraphStyle(name="Captionx", fontName="Times-Italic", fontSize=9.5, leading=11, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8))
    s.add(ParagraphStyle(name="TOCx", fontName="Times-Roman", fontSize=11.5, leading=15, leftIndent=10, spaceAfter=2))
    s.add(ParagraphStyle(name="Bulletx", fontName="Times-Roman", fontSize=11.2, leading=13.6, leftIndent=16, firstLineIndent=-8, alignment=TA_JUSTIFY, spaceAfter=3))
    s.add(ParagraphStyle(name="ArticleH", fontName="Times-Bold", fontSize=12, leading=13.5, spaceBefore=6, spaceAfter=3, keepWithNext=True))
    s.add(ParagraphStyle(name="ArticleBody", fontName="Times-Roman", fontSize=12, leading=13.2, alignment=TA_JUSTIFY, spaceAfter=4))
    s.add(ParagraphStyle(name="Abstract", fontName="Times-Italic", fontSize=10, leading=11.2, alignment=TA_JUSTIFY, spaceAfter=4))
    s.add(ParagraphStyle(name="ArticleRef", fontName="Times-Roman", fontSize=8.4, leading=9.5, leftIndent=8, firstLineIndent=-8, spaceAfter=2))
    s.add(ParagraphStyle(name="ArticleCaption", fontName="Times-Italic", fontSize=8.5, leading=9.5, alignment=TA_CENTER, spaceAfter=5))
    return s


S = styles()


def P(text, style="Bodyx"):
    return Paragraph(text, S[style])


def bullet(text):
    return P("• " + text, "Bulletx")


def figure(filename, width, caption, article=False):
    img = Image(str(ASSETS / filename), width=width, height=width * Image(str(ASSETS / filename)).imageHeight / Image(str(ASSETS / filename)).imageWidth)
    return KeepTogether([img, P(caption, "ArticleCaption" if article else "Captionx")])


def table(data, widths, font_size=8.7, header=True, repeat=1):
    t = Table(data, colWidths=widths, repeatRows=repeat if header else 0, hAlign="CENTER")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 1.6),
        ("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#555555")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ])
    t.setStyle(TableStyle(commands))
    return t


def profile_pdf():
    doc = SimpleDocTemplate(str(PROFILE), pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.5 * cm, bottomMargin=2.5 * cm, title="Optimización de ubicaciones de parques solares mediante algoritmos genéticos", author="")
    story = []
    story += [Spacer(1, 1.5 * cm), P("Universidad Tecnológica Nacional", "ProfileTitle"), P("Facultad Regional Buenos Aires", "ProfileSubtitle"), Spacer(1, 1.2 * cm), P("Optimización de ubicaciones de parques solares mediante algoritmos genéticos", "ProfileTitle"), P("Documento guía de la investigación y concreción del modelo", "ProfileSubtitle"), Spacer(1, .8 * cm), P("Asignatura Algoritmos Genéticos", "ProfileSubtitle")]
    story.append(table([["Integrantes", "Legajos"], ["", ""], ["", ""]], [8 * cm, 6 * cm], 11))
    story += [Spacer(1, 1.2 * cm), P("Ciclo lectivo 2026", "ProfileSubtitle"), PageBreak()]
    story += [P("Índice de contenidos", "H1x")]
    for item in ["1 Denominación del proyecto", "2 Situación problemática", "3 Problema de investigación", "4 Objetivos de la investigación", "5 Hipótesis y alcance", "6 Marco teórico", "7 Concreción del modelo", "8 Diseño experimental", "9 Resultados", "10 Discusión", "11 Conclusiones", "12 Líneas de continuidad", "Referencias", "Anexo técnico"]:
        story.append(P(item, "TOCx"))
    story += [P("Resumen ejecutivo", "H1x"), P(f"Este proyecto desarrolla y verifica un prototipo en Python que clasifica celdas de una grilla sobre la provincia de Santa Fe. La corrida analizada evaluó {RUN['total']} celdas de 9 km, excluyó {RUN['excluded']} por intersección urbana y optimizó las {RUN['valid']} restantes. La mejor solución hallada por el algoritmo fue la celda {int(RUN['first'].grid_cell_id)}, con fitness {RUN['first'].fitness:.4f} y radiación anual estimada de {RUN['first'].solar_annual_kwh_m2:.1f} kWh/m2/año. El TOP 10 genético compartió {RUN['overlap']} posiciones con el exhaustivo y no recuperó su mejor alternativa, la celda {int(RUN['exhaustive_best'].grid_cell_id)}. La salida constituye una herramienta de preselección y no una decisión de inversión.")]
    story += [P("1 Denominación del proyecto", "H1x"), P("Optimización de ubicaciones potenciales para parques solares fotovoltaicos en Santa Fe mediante algoritmos genéticos y análisis geoespacial.")]
    story += [P("2 Situación problemática", "H1x"), P("La selección preliminar de un sitio para generación fotovoltaica es un problema espacial de decisión multicriterio. Una ubicación puede recibir buena radiación y, al mismo tiempo, encontrarse lejos de la infraestructura eléctrica, dentro de una zona poblada o sobre un terreno que no admite el desarrollo. La bibliografía de selección de sitios solares combina información geográfica con criterios técnicos, ambientales y económicos, y advierte que los resultados dependen de la calidad de las capas y de los pesos asignados [4]-[6]."), P("En Santa Fe existen fuentes públicas para límites administrativos, asentamientos, redes eléctricas y estaciones transformadoras, pero presentan escalas, geometrías y coberturas diferentes [9]-[12]. BAHRA representa los asentamientos como puntos; por lo tanto, no entrega polígonos urbanos listos para excluir. La red de distribución y las estaciones transformadoras provienen de conjuntos distintos. La radiación solar se obtiene de un reanálisis climático y no de mediciones de campo. Integrar esas fuentes exige transformar sistemas de coordenadas, validar capas, normalizar métricas y conservar la trazabilidad de cada decisión."), P("El proyecto aborda ese problema con un producto mínimo viable reproducible. La provincia se divide en celdas; cada celda recibe métricas de radiación y proximidad a infraestructura; las celdas que intersectan la aproximación de área urbana quedan excluidas. El algoritmo genético trabaja sobre candidatos válidos y devuelve un ranking. La salida no pretende establecer la ubicación económicamente óptima, sino reducir el espacio de búsqueda y producir evidencia verificable para estudios posteriores.")]
    story += [P("3 Problema de investigación", "H1x"), P("¿Cómo integrar datos climáticos y geoespaciales heterogéneos en un algoritmo genético reproducible que permita identificar y ordenar, dentro de Santa Fe, celdas potencialmente favorables para un parque solar fotovoltaico de dos hectáreas, respetando la exclusión urbana y explicitando las limitaciones que impiden interpretar el resultado como una decisión definitiva de localización?")]
    story += [P("4 Objetivos de la investigación", "H1x"), P("4 1 Objetivo general", "H2x"), P("Desarrollar y verificar un prototipo de optimización geoespacial basado en algoritmos genéticos que produzca un ranking trazable de ubicaciones potencialmente favorables para parques solares fotovoltaicos en Santa Fe."), P("4 2 Objetivos específicos", "H2x")]
    for item in ["Integrar fuentes oficiales de límites, asentamientos e infraestructura eléctrica con radiación ERA5-Land ARCO.", "Construir una grilla configurable y calcular radiación estimada y distancias a líneas y estaciones transformadoras.", "Excluir las celdas que intersecten áreas urbanas aproximadas mediante un buffer configurable.", "Definir una función de aptitud normalizada y configurable cuyos pesos sumen uno.", "Implementar selección por torneo, elitismo, cruce, mutación y registro de mejores soluciones.", "Comparar el TOP 10 genético con el ranking exhaustivo de las celdas válidas.", "Documentar arquitectura, parámetros, fuentes, salidas y limitaciones del prototipo."]:
        story.append(bullet(item))
    story += [P("5 Hipótesis y alcance", "H1x"), P("Hipótesis de trabajo. Si las métricas de radiación y proximidad a infraestructura se normalizan de manera consistente, las restricciones urbanas se aplican antes de la búsqueda y la ejecución utiliza una semilla fija, entonces un algoritmo genético puede recuperar de forma reproducible las celdas con mayor aptitud del conjunto analizado."), P("La hipótesis se evalúa en una corrida sobre Santa Fe con celdas de 9 km y pesos iniciales de 0,50 para radiación, 0,20 para proximidad a líneas y 0,30 para proximidad a transformadores. La superficie nominal de dos hectáreas se conserva como requisito de trazabilidad; el MVP no verifica continuidad ni disponibilidad física del terreno. El alcance es de preselección regional.")]
    story += [P("6 Marco teórico", "H1x"), P("6 1 Selección espacial multicriterio", "H2x"), P("Un problema de localización convierte alternativas geográficas en unidades comparables mediante criterios y restricciones. Los sistemas de información geográfica permiten superponer capas, medir distancias y excluir zonas; el análisis multicriterio combina esas evidencias en una regla de decisión [4]. En plantas solares, la irradiación, la proximidad a la red, las restricciones de uso del suelo y la accesibilidad aparecen de forma recurrente [5], [6]. El presente modelo adopta una suma ponderada de tres criterios activos y separa la exclusión urbana como una restricción dura."), P("6 2 Algoritmos genéticos", "H2x"), P("Los algoritmos genéticos son métodos de búsqueda poblacional inspirados en selección, recombinación y mutación [1]-[3]. Cada individuo codifica una solución; la función de aptitud cuantifica su calidad; la selección aumenta la presencia de individuos aptos; el cruce produce descendencia y la mutación mantiene diversidad. El elitismo conserva las mejores soluciones. Al usar una semilla pseudoaleatoria fija se obtiene repetibilidad, aunque no desaparece la naturaleza heurística del método."), P("En este prototipo, un individuo es un índice entero que referencia una fila del conjunto fijo de celdas válidas. La selección se realiza por torneos de tres individuos. El cruce mezcla dos índices y redondea el resultado; la mutación reemplaza el índice por otro candidato uniforme. Un registro de mejores soluciones conserva los individuos observados. Esta representación es compacta, pero el orden de las filas no es una variable geográfica continua; por eso el cruce aritmético no garantiza proximidad espacial ni semántica."), P("6 3 Función de aptitud", "H2x"), P("Las métricas se normalizan al intervalo [0, 1]. Para radiación, el valor más alto recibe uno. Para distancias, la normalización se invierte para que la menor distancia reciba uno. La aptitud se calcula como fitness = ws x radiación + wl x proximidad a líneas + wt x proximidad a transformadores. Los pesos deben sumar uno y un peso nulo desactiva el criterio. Los valores usados son iniciales y no fueron calibrados con expertos ni análisis de sensibilidad."), P("6 4 Radiación solar y ERA5 Land", "H2x"), P("ERA5-Land es un reanálisis terrestre global con resolución espacial aproximada de 9 km y muestreo horario [7]. El producto ARCO permite acceder a subconjuntos de variables sin descargar archivos completos [8]. El prototipo convierte J/m2 a kWh/m2 y resume enero, abril, julio y octubre desde 1970. Cada media mensual histórica se lleva a una media diaria, se proyecta a los días de su estación y luego se suman las cuatro estaciones. El resultado es una estimación anual basada en meses representativos, no una suma observada de los doce meses."), P("6 5 Calidad de datos y trazabilidad", "H2x"), P("La validez del ranking depende de la correspondencia entre fuente, geometría, fecha y variable. El límite proviene del IGN [9]; los asentamientos, de BAHRA [10]; las líneas y estaciones, de la Secretaría de Energía [11], [12]. El sistema registra metadatos, usa caché, detiene el procesamiento cuando falta una capa activa y evita llamadas de red dentro del algoritmo genético.")]
    story += [P("7 Concreción del modelo", "H1x"), P("7 1 Arquitectura", "H2x"), figure("figura_arquitectura.png", 15.5 * cm, "Figura 1 Arquitectura funcional del prototipo"), P("La separación entre adquisición, procesamiento y optimización evita que el algoritmo dependa de servicios externos durante la búsqueda. La ingesta descarga y valida las capas; el preprocesamiento construye la grilla, transforma coordenadas, calcula distancias y genera métricas; el repositorio persiste los datos en SQLite; el módulo genético lee candidatos válidos; el reporte produce CSV, JSON y un mapa HTML."), P("7 2 Fuentes y transformaciones", "H2x")]
    source_rows = [["Capa", "Fuente", "Geometría", "Uso"], ["Límite", "IGN", "Polígono", "Recorte de Santa Fe"], ["Áreas urbanas", "BAHRA", "Puntos", "Buffer de 3 km"], ["Líneas", "Secretaría de Energía", "Líneas", "Distancia mínima"], ["Transformadores", "Secretaría de Energía", "Puntos", "Distancia mínima"], ["Radiación", "ERA5-Land ARCO", "Grilla", "Vecino más cercano"]]
    story += [table(source_rows, [3 * cm, 4.4 * cm, 2.7 * cm, 5.5 * cm], 8.8), P("Tabla 1 Fuentes y función dentro del modelo", "Captionx"), P("7 3 Flujo de procesamiento", "H2x")]
    for item in ["Validar configuración, región y suma de pesos.", "Descargar o recuperar de caché las capas activas.", "Construir la grilla de 9 km en un sistema métrico.", "Bufferizar 3 km los puntos LOCALIDAD y excluir intersecciones.", "Calcular distancias a líneas y transformadores.", "Consultar ERA5-Land ARCO por bloques y resumir 227 meses.", "Normalizar métricas, persistir candidatos y ejecutar el algoritmo.", "Generar ranking, metadatos, candidatos y mapa."]:
        story.append(bullet(item))
    story += [P("7 4 Especificación técnica", "H2x"), table([["Componente", "Especificación"], ["Lenguaje", "Python 3.11 o superior"], ["Cálculo", "pandas, NumPy, xarray y Zarr"], ["Geoespacial", "GeoPandas, Shapely, pyproj y pyogrio"], ["Persistencia", "SQLite mediante SQLAlchemy"], ["Visualización", "Folium y OpenStreetMap"], ["Configuración", "YAML, Pydantic y credencial en .env"], ["Infraestructura", "Windows, conexión inicial y almacenamiento local"]], [4.2 * cm, 11.4 * cm], 9.1), P("Tabla 2 Software e infraestructura", "Captionx")]
    story += [P("8 Diseño experimental", "H1x"), P(f"La corrida {RUN['metadata']['run_id']} utilizó celdas de 9 km, un parque nominal de 2 ha, período 1970-01 a 2026-07 y los meses 1, 4, 7 y 10. El algoritmo usó 50 individuos, 100 generaciones, cruce 0,75, mutación 0,05, elitismo 2, torneo 3 y semilla 42."), table([["Parámetro", "Valor"], ["Pesos", "Radiación 0,50; líneas 0,20; transformadores 0,30"], ["Población", "50"], ["Generaciones", "100"], ["Cruce", "0,75"], ["Mutación", "0,05"], ["Elitismo", "2"], ["Torneo", "3"], ["Semilla", "42"]], [5.8 * cm, 9.8 * cm], 9.3), P("Tabla 3 Configuración de la corrida", "Captionx"), P(f"La verificación revisó salidas y log, ejecutó 11 pruebas automatizadas y comparó el TOP 10 genético contra el ranking exhaustivo de las {RUN['valid']} celdas válidas.")]
    r = RUN["ranking"]
    story += [P("9 Resultados", "H1x"), P(f"La grilla produjo {RUN['total']} celdas. El criterio urbano excluyó {RUN['excluded']}, equivalentes al {RUN['excluded_pct']:.1f} %; no hubo exclusiones por falta de datos climáticos. El algoritmo consideró {RUN['valid']} candidatos."), figure("figura_mapa_candidatos.png", 10.8 * cm, "Figura 2 Celdas evaluadas y posiciones del ranking TOP 10")]
    rank_rows = [["R", "Celda", "Lat", "Lon", "Fitness", "kWh/m2/año", "Línea km", "Trafo km"]]
    for x in r.itertuples():
        rank_rows.append([str(int(x.rank)), str(int(x.grid_cell_id)), f"{x.latitude:.3f}", f"{x.longitude:.3f}", f"{x.fitness:.4f}", f"{x.solar_annual_kwh_m2:.1f}", f"{x.distance_to_power_line_km:.1f}", f"{x.distance_to_transformer_km:.1f}"])
    story += [table(rank_rows, [1 * cm, 1.2 * cm, 1.8 * cm, 1.8 * cm, 1.7 * cm, 2.3 * cm, 2 * cm, 2 * cm], 7.8), P("Tabla 4 Ranking de ubicaciones potencialmente favorables", "Captionx"), P(f"La celda {int(RUN['first'].grid_cell_id)} obtuvo fitness {RUN['first'].fitness:.4f}, radiación anual estimada de {RUN['first'].solar_annual_kwh_m2:.1f} kWh/m2/año y distancia nula a una línea. Su distancia al transformador más cercano fue {RUN['first'].distance_to_transformer_km:.1f} km. Las diez celdas presentaron entre {RUN['solar_min']:.1f} y {RUN['solar_max']:.1f} kWh/m2/año; las {RUN['zero_lines']} registraron 0 km a una línea."), figure("figura_componentes_fitness.png", 15.5 * cm, "Figura 3 Contribución ponderada de cada criterio al fitness"), P(f"La ejecución genética compartió {RUN['overlap']} celdas con el TOP 10 exhaustivo y omitió su mejor alternativa, la celda {int(RUN['exhaustive_best'].grid_cell_id)} con fitness {RUN['exhaustive_best'].fitness:.4f}."), figure("figura_convergencia.png", 15.5 * cm, "Figura 4 Evolución del mejor fitness y del fitness medio")]
    story += [P("10 Discusión", "H1x"), P(f"La corrida es reproducible, pero el TOP 10 genético solo comparte {RUN['overlap']} celdas con el exhaustivo. La grilla de 9 km amplió el espacio a {RUN['valid']} alternativas y expuso una limitación de exploración que no aparecía con 30 km. La búsqueda completa sigue siendo una referencia necesaria."), P("La función de aptitud hace visible el compromiso entre recurso solar e infraestructura. Antes de una decisión real deben ejecutarse análisis de sensibilidad y una formulación multiobjetivo."), P("La representación genética requiere revisión. El índice de fila es categórico, aunque el cruce lo trata como continuo. Dos índices próximos pueden corresponder a celdas lejanas. Una versión futura debería usar coordenadas, orden espacial u operadores categóricos y comparar múltiples semillas."), P("La exclusión urbana es aproximada: BAHRA aporta puntos y un buffer uniforme no reproduce extensiones reales. Una celda de 9 km sigue siendo mucho mayor que un parque de 2 ha. Además, la radiación con cuatro meses representativos no equivale a una simulación fotovoltaica completa.")]
    story += [P("11 Conclusiones", "H1x"), P(f"La corrida identificó {RUN['valid']} celdas válidas entre {RUN['total']} y situó a la celda {int(RUN['first'].grid_cell_id)} en primer lugar genético con fitness {RUN['first'].fitness:.4f}. Las 11 pruebas finalizaron sin errores, pero el TOP 10 no coincidió con el exhaustivo."), P("La conclusión defendible es acotada: el sistema produce un ranking reproducible según las variables y pesos incorporados, pero la configuración genética actual no garantiza recuperar las mejores alternativas y no prueba viabilidad técnica, ambiental, legal o económica.")]
    story += [P("12 Líneas de continuidad", "H1x")]
    for item in ["Reemplazar buffers urbanos por polígonos actualizados.", "Mantener fuera del modelo las variables orográficas y de nubosidad en esta etapa.", "Agregar capacidad eléctrica, costos y restricciones regulatorias.", "Ejecutar sensibilidad de pesos y optimización multiobjetivo.", "Rediseñar la codificación genética y comparar métodos.", "Validar ubicaciones con cartografía detallada y trabajo de campo."]:
        story.append(bullet(item))
    story += [P("Referencias", "H1x")]
    for ref in REFERENCES:
        story.append(P(ref, "Smallx"))
    story += [P("Anexo técnico", "H1x"), P("A Configuración reproducible", "H2x"), P("Comando principal en Windows: .\\.venv\\Scripts\\python.exe -m src.main --run-all"), P("Comando de pruebas: .\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v"), Spacer(1, 6), P("B Productos de la corrida", "H2x")]
    for item in ["results/ranking.csv con el TOP 10.", f"results/candidate_locations.csv con las {RUN['total']} celdas.", "results/optimization_run.json con parámetros y alcance.", "results/map.html con capas y ranking.", "data/processed/parque_solar.sqlite con datos persistidos."]:
        story.append(bullet(item))
    doc.build(story)


def article_pdf():
    page_w, page_h = A4
    margin = 2.5 * cm
    gap = 1 * cm
    col_w = (page_w - 2 * margin - gap) / 2
    first_top = page_h - 6.4 * cm
    first_frames = [Frame(margin, margin, col_w, first_top - margin, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), Frame(margin + col_w + gap, margin, col_w, first_top - margin, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
    later_frames = [Frame(margin, margin, col_w, page_h - 2 * margin, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), Frame(margin + col_w + gap, margin, col_w, page_h - 2 * margin, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]

    def first_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setFont("Times-Bold", 16)
        title = "Optimización de ubicaciones de parques solares mediante algoritmos genéticos"
        lines = ["Optimización de ubicaciones de parques solares", "mediante algoritmos genéticos"]
        y = page_h - 2.0 * cm
        for line in lines:
            canvas.drawCentredString(page_w / 2, y, line)
            y -= .65 * cm
        canvas.setFont("Times-Bold", 14)
        canvas.drawCentredString(page_w / 2, y - .15 * cm, " ")
        canvas.setFont("Times-BoldItalic", 12)
        canvas.drawCentredString(page_w / 2, y - .85 * cm, "Universidad Tecnológica Nacional Facultad Regional Buenos Aires")
        canvas.setFont("Times-Italic", 10)
        canvas.drawCentredString(page_w / 2, y - 1.45 * cm, "Versión para evaluación ciega")
        canvas.restoreState()

    doc = BaseDocTemplate(str(ARTICLE), pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin, title="Optimización de ubicaciones de parques solares mediante algoritmos genéticos", author="")
    doc.addPageTemplates([PageTemplate(id="First", frames=first_frames, onPage=first_page, autoNextPageTemplate="Later"), PageTemplate(id="Later", frames=later_frames)])
    story = []
    story += [P("Abstract", "ArticleH"), P(f"Este trabajo presenta un prototipo reproducible para identificar celdas potencialmente favorables para un parque solar fotovoltaico en Santa Fe. La corrida generó {RUN['total']} celdas de 9 km; {RUN['excluded']} fueron excluidas y {RUN['valid']} ingresaron a la optimización. La celda {int(RUN['first'].grid_cell_id)} encabezó el ranking genético con fitness {RUN['first'].fitness:.4f} y radiación anual estimada de {RUN['first'].solar_annual_kwh_m2:.1f} kWh/m2. El TOP 10 genético compartió {RUN['overlap']} celdas con el exhaustivo y omitió su mejor alternativa. Las 11 pruebas automatizadas finalizaron correctamente. El resultado confirma la ejecución reproducible, pero muestra que la configuración genética actual no garantiza recuperar las mejores alternativas al aumentar la resolución.", "Abstract"), P("<b>Palabras Clave</b> algoritmos genéticos, energía solar, análisis geoespacial, selección de sitios, ERA5-Land", "Smallx")]
    story += [P("Introducción", "ArticleH"), P("La localización preliminar de una planta fotovoltaica exige comparar alternativas espaciales según recurso solar, infraestructura, restricciones territoriales y costos. Los enfoques GIS-MCDA organizan esas evidencias, pero el resultado depende de las capas, las reglas de exclusión y los pesos [4]-[6]. Este proyecto estudia si un algoritmo genético puede recuperar de manera reproducible las mejores celdas de una grilla provincial a partir de tres criterios y una restricción urbana.", "ArticleBody"), P("La contribución es un flujo completo y trazable. La ingesta usa fuentes oficiales argentinas para límite, asentamientos y red eléctrica [9]-[12], y ERA5-Land ARCO para radiación [7], [8]. El algoritmo opera sobre métricas persistidas en una base local. La salida es un ranking de preselección, no una decisión de inversión.", "ArticleBody")]
    story += [P("Elementos del trabajo y metodología", "ArticleH"), P(f"Santa Fe se discretizó en {RUN['total']} celdas de 9 km. BAHRA describe asentamientos como puntos; se seleccionaron registros LOCALIDAD y se aplicó un buffer de 3 km. Toda celda que intersectó un buffer se marcó como inválida. Para las restantes se calculó la distancia mínima a líneas eléctricas y estaciones transformadoras.", "ArticleBody"), P("ERA5-Land ofrece reanálisis horario terrestre con resolución aproximada de 9 km [7]. ARCO permite leer subconjuntos sin descargar archivos completos [8]. Para cada centroide se eligió el punto climático más cercano y se resumieron enero, abril, julio y octubre desde 1970 hasta 2026. Las medias mensuales se convirtieron a irradiación diaria, se proyectaron a los días de cada estación y se sumaron como estimación anual.", "ArticleBody"), P("Las métricas se normalizaron entre cero y uno. La radiación conserva el sentido creciente; las distancias se invierten. La función fue fitness = 0,50 x radiación + 0,20 x proximidad a líneas + 0,30 x proximidad a transformadores. Los pesos son iniciales y no están calibrados.", "ArticleBody"), P(f"Cada individuo representa el índice de una celda válida. La población fue de 50 individuos durante 100 generaciones, con torneo de tres, elitismo de dos, cruce 0,75, mutación 0,05 y semilla 42. La verificación incluyó 11 pruebas y una comparación contra el ordenamiento exhaustivo de las {RUN['valid']} celdas válidas [1]-[3].", "ArticleBody")]
    r = RUN["ranking"]
    story += [P("Resultados", "ArticleH"), P(f"El procesamiento excluyó {RUN['excluded']} celdas por intersección urbana, {RUN['excluded_pct']:.1f} % del total, y no registró faltantes climáticos. La primera ubicación genética fue la celda {int(RUN['first'].grid_cell_id)}, en latitud {RUN['first'].latitude:.4f} y longitud {RUN['first'].longitude:.4f}, con fitness {RUN['first'].fitness:.4f}. Su radiación anual estimada fue {RUN['first'].solar_annual_kwh_m2:.1f} kWh/m2; la distancia a una línea fue {RUN['first'].distance_to_power_line_km:.1f} km y la distancia al transformador más cercano, {RUN['first'].distance_to_transformer_km:.1f} km.", "ArticleBody"), figure("figura_mapa_candidatos.png", 7.2 * cm, "Figura 1 Celdas y ubicaciones TOP 10", True)]
    rows = [["R", "Celda", "Fit", "Solar", "Trafo"]]
    for x in r.itertuples():
        rows.append([str(int(x.rank)), str(int(x.grid_cell_id)), f"{x.fitness:.3f}", f"{x.solar_annual_kwh_m2:.0f}", f"{x.distance_to_transformer_km:.1f}"])
    story += [table(rows, [.65 * cm, 1.1 * cm, 1.15 * cm, 1.35 * cm, 1.45 * cm], 7.4), P("Tabla 1 Ranking y métricas principales", "ArticleCaption"), P(f"Las diez celdas presentaron entre {RUN['solar_min']:.1f} y {RUN['solar_max']:.1f} kWh/m2/año. Las {RUN['zero_lines']} registraron distancia nula a una línea. El TOP 10 genético compartió {RUN['overlap']} celdas con el exhaustivo y omitió la mejor alternativa de referencia, la celda {int(RUN['exhaustive_best'].grid_cell_id)}.", "ArticleBody"), figure("figura_componentes_fitness.png", 7.2 * cm, "Figura 2 Aportes ponderados al fitness", True)]
    story += [P("Discusión", "ArticleH"), P(f"La comparación exhaustiva muestra que la configuración genética no alcanzó el ranking de referencia: solo {RUN['overlap']} de sus diez soluciones pertenecen al TOP 10 exhaustivo. La mayor resolución hizo visible una limitación de exploración.", "ArticleBody"), P(f"El primer puesto genético, la celda {int(RUN['first'].grid_cell_id)}, combina el máximo puntaje solar con distancia nula a líneas. La mejor alternativa exhaustiva fue la celda {int(RUN['exhaustive_best'].grid_cell_id)}, con fitness {RUN['exhaustive_best'].fitness:.4f}.", "ArticleBody"), P("La codificación también limita la interpretación. El índice de fila es categórico, pero el cruce aritmético supone continuidad. Una extensión debería usar una codificación espacial u operador categórico, ejecutar múltiples semillas y comparar estabilidad.", "ArticleBody"), P("Un buffer uniforme alrededor de puntos BAHRA no representa límites urbanos reales. Una celda de 9 km tampoco demuestra que haya 20.000 m2 contiguos utilizables. La estimación climática usa cuatro meses representativos y no modela el rendimiento eléctrico.", "ArticleBody")]
    story += [P("Conclusión", "ArticleH"), P(f"El prototipo identificó {RUN['valid']} candidatos válidos entre {RUN['total']} celdas. La corrida no permite aceptar la hipótesis de recuperación de las mejores alternativas, porque el TOP 10 genético no coincidió con el exhaustivo.", "ArticleBody"), P("El siguiente avance metodológico debe concentrarse en revisar la representación genética, la exploración, el tamaño poblacional y la estabilidad entre semillas, manteniendo fuera del alcance actual las variables orográficas y de nubosidad.", "ArticleBody")]
    story.append(P("Referencias", "ArticleH"))
    for ref in REFERENCES:
        story.append(P(ref, "ArticleRef"))
    story += [P("Datos de contacto", "ArticleH"), P("Universidad Tecnológica Nacional Facultad Regional Buenos Aires", "ArticleRef")]
    doc.build(story)


if __name__ == "__main__":
    profile_pdf()
    article_pdf()
    print(PROFILE)
    print(ARTICLE)
