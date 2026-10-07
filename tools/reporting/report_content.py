from __future__ import annotations

from current_run import RUN


CFG = RUN["configuration"]
META = RUN["metadata"]
FIRST = RUN["first"]
GA = CFG["genetic_algorithm"]
FIT = CFG["fitness"]
if CFG['infrastructure']['urban_areas'].get('provider') != 'INDEC':
    raise ValueError('Los informes requieren envolventes urbanas INDEC.')


def urban_method_description():
    margin = CFG['urban_exclusion']['buffer_km']
    holes = 'Se excluyen también los huecos interiores encerrados.' if CFG['urban_exclusion']['fill_holes'] else 'Se conservan los huecos interiores de la fuente.'
    return (f'Restricción urbana. Se usan envolventes INDEC del Censo 2022, con un margen de {margin:g} km '
            f'desde el perímetro. {holes} Toda celda que intersecta la máscara queda excluida antes de la búsqueda. '
            'La máscara final se recorta a Santa Fe. La cartografía censal no acredita límites catastrales ni actualización posterior a 2022.')


TITLE = "Optimización de configuraciones contiguas para parques solares en Santa Fe"
SUBTITLE = "Preselección territorial multicriterio mediante algoritmos genéticos"


REFERENCES = [
    "[1] J. H. Holland, Adaptation in Natural and Artificial Systems. University of Michigan Press, 1975.",
    "[2] D. E. Goldberg, Genetic Algorithms in Search, Optimization and Machine Learning. Addison-Wesley, 1989.",
    "[3] M. Srinivas y L. M. Patnaik, “Genetic algorithms: a survey”, Computer, vol. 27, n.º 6, pp. 17-26, 1994. https://doi.org/10.1109/2.294849",
    "[4] J. Malczewski, “GIS-based multicriteria decision analysis: a survey of the literature”, International Journal of Geographical Information Science, vol. 20, n.º 7, pp. 703-726, 2006. https://doi.org/10.1080/13658810600661508",
    "[5] M. Uyan, “GIS-based solar farms site selection using analytic hierarchy process in Karapinar region”, Renewable and Sustainable Energy Reviews, vol. 28, pp. 11-17, 2013. https://doi.org/10.1016/j.rser.2013.07.042",
    "[6] H. Z. Al Garni y A. Awasthi, “Solar PV power plant site selection using a GIS-AHP based approach with application in Saudi Arabia”, Applied Energy, vol. 206, pp. 1225-1240, 2017. https://doi.org/10.1016/j.apenergy.2017.10.024",
    "[7] J. Muñoz-Sabater et al., “ERA5-Land: a state-of-the-art global reanalysis dataset for land applications”, Earth System Science Data, vol. 13, pp. 4349-4383, 2021. https://doi.org/10.5194/essd-13-4349-2021",
    "[8] Copernicus Climate Change Service y ECMWF, ERA5-Land hourly Analysis Ready Cloud Optimised data on single levels from 1950 to present, Product User Guide, 2026. https://confluence.ecmwf.int/spaces/CKB/pages/536218894/",
    "[9] Instituto Geográfico Nacional, Unidades Territoriales. Datos Argentina. https://datos.gob.ar/ar/dataset/ign-unidades-territoriales",
    "[10] Instituto Nacional de Estadística y Censos (2022), Marco Geoestadístico Nacional: Localidades censales. https://portalgeoestadistico.indec.gob.ar/geoportal/documents/metadato_localidades_censales.pdf",
    "[11] Secretaría de Energía, Redes de distribución eléctrica. Datos Argentina. https://datos.gob.ar/dataset/energia-redes-distribucion-electrica",
    "[12] Secretaría de Energía, Transporte Eléctrico AT — Estaciones Transformadoras. Datos Argentina. https://www.datos.gob.ar/dataset/energia-transporte-electrico-at-estaciones-transformadoras",
    "[13] S. Ong et al., Land-Use Requirements for Solar Power Plants in the United States. NREL, 2013, tabla ES-1: 7,9 acres/MWac de área total para fotovoltaica grande. https://docs.nrel.gov/docs/fy13osti/56290.pdf",
]

def fmt(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def report_sections():
    return [
        ("Resumen ejecutivo", [
            f"El problema de investigación es cómo reducir un espacio territorial muy amplio y heterogéneo hasta obtener configuraciones de parque solar comparables, contiguas y trazables, sin confundir una preselección computacional con una decisión de inversión. La radiación es necesaria, pero no suficiente: también importan la cercanía a infraestructura, la ocupación urbana, la forma del terreno y una escala compatible con la potencia pretendida.",
            f"La corrida vigente {META['run_id']} discretiza Santa Fe en celdas de 500 × 500 m y representa cada alternativa como un conjunto contiguo de celdas. Se analizaron {RUN['total_cells']:,} celdas; {RUN['urban_excluded']:,} se excluyeron por intersección con la máscara urbana y {RUN['valid_cells']:,} quedaron disponibles para construir soluciones. El algoritmo trabajó con un límite experimental de 80 MW, población de {GA['population_size']} individuos y {GA['generations']} generaciones.",
            f"El mejor parque observado reúne {int(FIRST.number_of_cells)} celdas, ocupa {fmt(FIRST.park_area_ha, 0)} ha y alcanza {fmt(FIRST.installed_power_mw)} MW, con fitness {fmt(FIRST.fitness, 4)}. La corrida terminó con {RUN['final_unique']} configuraciones distintas entre {RUN['final_population']} individuos. Se obtuvieron dos lecturas complementarias: un TOP 5 general, que puede contener variantes superpuestas, y un TOP 5 territorial sin superposición. El resultado cumple una función de preselección y experimentación; no prueba óptimo global, capacidad eléctrica disponible ni viabilidad predial, ambiental o económica.",
        ]),
        ("1 Denominación y tema", [
            TITLE + ".",
            "Tema: aplicación de optimización evolutiva y análisis geoespacial a la preselección de configuraciones territoriales para parques solares fotovoltaicos en la provincia de Santa Fe.",
        ]),
        ("2 Situación problemática", [
            "Localizar un parque solar no consiste en elegir el punto con mayor radiación. La alternativa debe reunir superficie continua, evitar áreas incompatibles, mantener una relación razonable con la red y alcanzar una potencia útil sin exceder límites técnicos. Cuando esos criterios se observan simultáneamente aparecen compensaciones: una zona con mejor recurso puede quedar lejos de una estación, mientras otra mejor conectada puede ofrecer menor radiación o una geometría territorial menos conveniente.",
            f"La escala agrava el problema. La base vigente contiene {RUN['total_cells']:,} celdas de 0,25 km². Las combinaciones contiguas posibles son demasiadas para enumerarlas de manera directa. Por eso el objeto de estudio no es el software en sí mismo, sino el problema de seleccionar configuraciones espaciales factibles bajo información incompleta y criterios que compiten. El sistema es el instrumento para formular, explorar y auditar esa decisión.",
            "Además, varias variables decisivas aún no están modeladas: disponibilidad y precio del suelo, titularidad, inundabilidad, áreas protegidas, pendiente, caminos, servidumbres, trazado efectivo de conexión, capacidad real de líneas y estaciones, pérdidas y costos. El ranking solo puede responder por los criterios que efectivamente incorpora.",
        ]),
        ("3 Problema de investigación", [
            "Pregunta principal. ¿En qué medida un algoritmo genético con representación espacial puede producir, de forma reproducible, configuraciones contiguas y diversas de parques solares para Santa Fe, ordenadas por radiación, proximidad a infraestructura, potencia instalada y compactación, y qué límites condicionan el uso territorial de ese ranking?",
            "Preguntas derivadas: ¿cómo representar una alternativa para que su geometría tenga sentido físico? ¿cómo combinar criterios heterogéneos sin ocultar sus compensaciones? ¿cómo evitar que la población colapse en duplicados? ¿cómo distinguir las mejores variantes matemáticas de un conjunto geográficamente diverso? ¿qué afirmaciones permite sostener la evidencia disponible y cuáles requieren estudios adicionales?",
        ]),
        ("4 Objetivos", [
            "Objetivo general. Evaluar un método reproducible de preselección territorial que genere y ordene configuraciones contiguas de parques solares en Santa Fe, explicitando sus compromisos, resultados y límites de validez.",
            "Objetivos específicos: representar cada alternativa como un parque formado por celdas contiguas; integrar radiación, distancias a líneas y transformadores, potencia, compactación y exclusión urbana; mantener diversidad durante la búsqueda; producir rankings general y territorial; medir convergencia y repetibilidad; auditar trazabilidad de datos y parámetros; e identificar la información faltante antes de cualquier decisión de emplazamiento.",
        ]),
        ("5 Hipótesis y alcance", [
            "Hipótesis de trabajo. Si las alternativas se representan como conjuntos contiguos de celdas de 500 m y la búsqueda incorpora inicialización territorial, control de duplicados y mutaciones que alteran efectivamente el fenotipo, entonces el algoritmo genético puede explorar de forma reproducible configuraciones factibles bajo el modelo, conservar diversidad poblacional y producir tanto un ranking de máxima aptitud como una selección territorial sin superposición.",
            f"La hipótesis se evalúa en una corrida sobre Santa Fe con cinco componentes de aptitud: radiación {FIT['weight_solar']:.2f}, proximidad a líneas {FIT['weight_grid_distance']:.2f}, proximidad a transformadores {FIT['weight_transformer_distance']:.2f} potencia instalada {FIT['weight_installed_power']:.2f} y compactación {FIT['weight_compactness']:.2f}. El crecimiento se limita por una capacidad experimental de {CFG['park']['max_connection_capacity_mw']:.0f} MW y una densidad de {CFG['park']['pv_power_density_mw_per_km2']:.1f} MW/km². El área resulta de las celdas aceptadas hasta el límite de potencia.",
            "El alcance es de preselección regional y validación metodológica. “Factible” significa solamente que la configuración es contigua, está formada por celdas admitidas y respeta el límite experimental. La hipótesis no afirma que el algoritmo encuentre el óptimo global ni que las configuraciones sean construibles, conectables o económicamente convenientes.",
        ]),
        ("6 Modelo del problema", [
            "Unidad de decisión. Un individuo se codifica mediante una celda semilla y una secuencia de genes de crecimiento. Al decodificarlo, el parque incorpora celdas vecinas que comparten borde; las diagonales no crean continuidad. Los genes que exceden la capacidad se omiten y el crecimiento continúa mientras exista frontera y alguna celda pueda incorporarse.",
            "Criterios. La irradiación del parque es un promedio ponderado por área. Las distancias se calculan desde el centroide ponderado por área del parque a las geometrías de líneas y a las cuatro estaciones transformadoras incluidas —Santo Tomé, Río Coronda, Rosario Oeste y Romang—. La potencia surge del área por una densidad experimental. La forma se valora con 4πA/P². Irradiación y distancias usan min-max fijo, potencia usa P/Pmáx y compactación ya está en [0,1]. Los cinco componentes forman una suma ponderada.",
            urban_method_description(),
            "Clima. Cada celda apunta al píxel nativo ERA5-Land más cercano; la grilla de 500 m no representa resolución climática de 500 m. La corrida exige cobertura horaria completa y finita para los meses representativos disponibles entre 2024 y julio de 2026. La irradiación anual se estima con enero, abril, julio y octubre; no es una integración de los doce meses.",
        ]),
        ("7 Diseño experimental", [
            f"La corrida {META['run_id']} utilizó semilla {META['random_seed']}, población {GA['population_size']}, {GA['generations']} generaciones, cruce {GA['crossover_probability']:.2f}, mutación {GA['mutation_probability']:.2f}, elitismo {GA['elitism']} y torneo {GA['tournament_size']}. La inicialización territorial empleó sectores de {GA['territory_size_km']:.0f} km; el archivo conservó hasta {GA['archive_per_territory']} soluciones por territorio y produjo {RUN['archive_size']} candidatos únicos para el ranking territorial.",
            "La evaluación usa una caché por genotipo y un registro histórico por fenotipo. El control de duplicados intenta reemplazar individuos repetidos y la mutación dispone de varios intentos para generar un cambio observable. Estos mecanismos sostienen la exploración y permiten registrar cambios territoriales efectivos.",
            "La verificación separa tres preguntas: validez geométrica y de restricciones; desempeño del proceso evolutivo; e interpretación territorial. La primera se controla mediante conectividad, área, potencia y exclusiones. La segunda mediante fitness, historia y cantidad de parques únicos. La tercera mediante los rankings general y territorial.",
        ]),
        ("8 Resultados", [
            f"Preprocesamiento. Se generaron {RUN['total_cells']:,} celdas; {RUN['urban_excluded']:,} ({fmt(RUN['excluded_pct'], 1)} %) quedaron excluidas por intersección urbana y {RUN['valid_cells']:,} permanecieron válidas. La cobertura climática registrada es “{META['dataset']['coverage']}”.",
            f"Búsqueda. El mejor fitness observado fue {fmt(FIRST.fitness, 4)}. El parque correspondiente tiene {int(FIRST.number_of_cells)} celdas, {fmt(FIRST.park_area_km2)} km², {fmt(FIRST.installed_power_mw)} MW y utiliza {fmt(FIRST.capacity_used_percent, 1)} % del límite experimental. Su irradiación estimada es {fmt(FIRST.solar_annual_kwh_m2, 1)} kWh/m²/año y su energía anual ideal de referencia es {fmt(FIRST.estimated_annual_energy_mwh, 0)} MWh; esta última no incluye pérdidas ni modelado DC/AC.",
            f"Diversidad. La última generación contiene {RUN['final_unique']} parques distintos sobre {RUN['final_population']} individuos. El TOP 5 general concentra variantes alrededor de la misma semilla y puede superponerse; no debe interpretarse como cinco emplazamientos independientes. El TOP 5 territorial selecciona cinco polígonos sin superposición a partir de {RUN['archive_size']} candidatos. Como la separación configurada es 0 km, evita compartir superficie pero no garantiza una distancia mínima entre alternativas.",
        ]),
        ("9 Discusión", [
            "La evidencia apoya la parte operativa de la hipótesis: la representación produce parques contiguos, la corrida es reproducible con la semilla y los parámetros registrados, la población final mantiene diversidad completa y se obtienen cinco alternativas territoriales no superpuestas. El objeto de evaluación es el parque completo construido por cada cromosoma.",
            "La evidencia no demuestra óptimo global. El experimento documentado en docs/validacion-busqueda.md compara el AG con azar y azar con búsqueda local, usando el mismo dataset y los cinco pesos actuales. El AG ganó 10 de 10 comparaciones frente al azar y 8 de 10 frente a azar con mejora local. La enumeración de rectángulos resuelve esa familia de formas, no el dominio completo.",
            "Los pesos favorecen por igual radiación y cercanía a transformadores (0,35 cada uno), y asignan 0,10 a líneas, potencia y compactación. Son supuestos de investigación y no una preferencia validada por especialistas. Las distancias del ranking corresponden únicamente a cuatro estaciones consideradas. El compromiso elegido por la función no constituye una recomendación de conexión.",
            "La convergencia matemática tampoco sustituye la validación territorial. Las líneas pueden corresponder a tensiones no adecuadas, y distancia geométrica no significa disponibilidad de capacidad ni derecho de paso. Antes de usar el ranking para inversión se requieren datos eléctricos, prediales, ambientales, hidrológicos, viales y económicos de mayor detalle.",
        ]),
        ("10 Conclusiones", [
            "El proyecto busca configuraciones contiguas de superficie variable que aproximan el tamaño de una planta dentro de un límite experimental de potencia. La grilla de 500 m permite construir geometrías explícitas y el algoritmo ofrece una forma trazable de recorrer un espacio combinatorio muy grande.",
            f"En la corrida vigente se alcanzaron {RUN['final_unique']} fenotipos únicos en una población de {RUN['final_population']} y se generaron cinco alternativas territoriales sin superposición. Por ello, la hipótesis queda respaldada respecto de reproducibilidad, factibilidad interna, diversidad y generación de rankings complementarios. No queda demostrada respecto de optimalidad global ni viabilidad real.",
            "El principal valor del resultado es reducir y estructurar la incertidumbre: identifica configuraciones que merecen análisis posterior y hace visibles los supuestos que las favorecen. El sistema debe entenderse como apoyo a una etapa temprana de decisión, no como sustituto de la ingeniería de conexión ni del estudio de sitio.",
        ]),
        ("11 Trabajo futuro", [
            "Incorporar inventario completo y capacidad real de la red; validar tensión y trazados; agregar inundabilidad, áreas protegidas, pendiente, accesos, catastro y costos; realizar sensibilidad de pesos y escenarios; ejecutar múltiples semillas; comparar contra heurísticas y cotas independientes; exigir separación territorial positiva cuando el uso lo requiera; y validar en campo las alternativas que superen esos filtros.",
        ]),
        ("Anexo de trazabilidad", [
            f"Corrida: {META['run_id']}. Dataset: {META['dataset_id']}. Versión de procesamiento: {META['dataset']['processing_version']}. Versión de búsqueda: {META['search_version']}. CRS proyectado: {META['dataset']['projected_crs']}.",
            "Archivos auditados: optimization_run.json, ranking.csv, ranking_territorial.csv, candidates.csv, history.csv, parks.geojson, parks_territorial.geojson, código de optimización y configuración vigente.",
            "Advertencia registrada por la corrida: " + META["disclaimer"],
        ]),
    ]


def config_rows():
    return [
        ["Parámetro", "Valor vigente"],
        ["Grilla", "500 × 500 m; 0,25 km² por celda completa"],
        ["Densidad de potencia", f"{CFG['park']['pv_power_density_mw_per_km2']:.1f} MW/km²"],
        ["Límite de capacidad", f"{CFG['park']['max_connection_capacity_mw']:.0f} MW (experimental)"],
        ["Pesos", "; ".join(f"{name} {FIT[key]:.2f}" for name, key in [("Solar", "weight_solar"), ("Líneas", "weight_grid_distance"), ("ET", "weight_transformer_distance"), ("Potencia", "weight_installed_power"), ("Compactación", "weight_compactness")])],
        ["Clima", "ERA5-Land; 2024–julio 2026; meses 1, 4, 7 y 10"],
        ["Población / generaciones", f"{GA['population_size']} / {GA['generations']}"],
        ["Cruce / mutación", f"{GA['crossover_probability']:.2f} / {GA['mutation_probability']:.2f}"],
        ["Semilla", str(META["random_seed"])],
    ]


def ranking_rows(data):
    rows = [["Puesto", "General", "Lat.", "Lon.", "ET", "Línea km", "ET km", "Solar", "Fitness"]]
    for row in data.itertuples():
        rows.append([
            str(int(row.rank)), str(int(getattr(row, "general_rank", row.rank))),
            fmt(row.latitude, 3), fmt(row.longitude, 3), row.station_id,
            fmt(row.distance_to_power_line_km, 2), fmt(row.distance_to_transformer_km, 2),
            fmt(row.solar_annual_kwh_m2, 1), fmt(row.fitness, 4),
        ])
    return rows


def article_blocks():
    sections = dict(report_sections())
    abstract = (
        f"La preselección de parques solares exige construir configuraciones territoriales continuas y comparar "
        f"criterios que pueden entrar en conflicto. El objetivo fue evaluar si un algoritmo genético con "
        f"representación espacial puede generar alternativas contiguas, diversas y reproducibles para Santa Fe. "
        f"La corrida {META['run_id']} utilizó una grilla de 500 m, exclusión urbana previa, cinco componentes de "
        f"aptitud y un límite experimental de 80 MW. Se analizaron {RUN['total_cells']:,} celdas, de las cuales "
        f"{RUN['valid_cells']:,} quedaron disponibles. El mejor parque reunió {int(FIRST.number_of_cells)} celdas, {fmt(FIRST.park_area_ha)} ha y {fmt(FIRST.installed_power_mw,3)} MW, con "
        f"fitness {fmt(FIRST.fitness, 4)}. La población final conservó {RUN['final_unique']} configuraciones distintas "
        f"entre {RUN['final_population']} individuos y permitió obtener cinco alternativas territoriales sin "
        f"superposición. El método resulta útil como preselección y como instrumento de investigación, pero no "
        f"demuestra óptimo global, capacidad eléctrica disponible ni viabilidad predial, ambiental o económica."
    )
    introduction = sections["2 Situación problemática"] + [
        sections["3 Problema de investigación"][0],
        sections["4 Objetivos"][0],
        sections["4 Objetivos"][1],
    ]
    methodology = sections["5 Hipótesis y alcance"] + sections["6 Modelo del problema"] + sections["7 Diseño experimental"]
    return [
        ("Abstract", [abstract]),
        ("Palabras Clave", ["algoritmos genéticos; parques solares; análisis geoespacial; optimización multicriterio; Santa Fe"]),
        ("Introducción", introduction),
        ("Elementos del Trabajo y metodología", methodology),
        ("Resultados", sections["8 Resultados"]),
        ("Discusión", sections["9 Discusión"]),
        ("Conclusión", sections["10 Conclusiones"]),
    ]
