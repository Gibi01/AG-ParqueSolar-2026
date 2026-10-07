# Modelo vigente: parques solares en Santa Fe

## Territorio y ciudades

La única región admitida es **Santa Fe**, código IGN/INDEC **82**. La configuración
valida nombre y código. La grilla se recorta por su límite oficial IGN y los
fragmentos conservan área y geometría reales. Componentes desconectados de un
cuadrado son unidades independientes. El CRS métrico se estima desde ese límite.

Las ciudades se determinan mediante **polígonos de localidades censales INDEC,
Censo 2022**, capa WFS `geonode:localidades_censales`. La ingesta valida páginas,
identificadores, cantidades y geometrías. No acepta una fuente no poligonal.

La preparación selecciona localidades que alcanzan Santa Fe y mantiene completos
los aglomerados seleccionados para conservar su topología. Une los contornos y,
con `fill_holes: true`, excluye los huecos interiores encerrados. Mantiene
concavidades y componentes separados; no utiliza una envolvente convexa.
La máscara final se intersecta con Santa Fe.

`urban_exclusion.buffer_km: 0.0` significa **sin margen adicional**. El parámetro
permite un margen opcional desde el perímetro de los polígonos, que requiere
reprocesamiento y calibración si se cambia. Toda celda que intersecta la máscara,
incluso por contacto con el borde, queda completamente excluida antes del AG.
Los insumos nacionales no amplían el dominio de búsqueda.

## Fuentes y preparación

| Fuente | Dato | Acceso |
|---|---|---|
| IGN | Límite de Santa Fe | Shapefile ZIP y selección del código 82 |
| INDEC | Envolventes censales 2022 | WFS paginado |
| Secretaría de Energía | Líneas | CKAN/DataStore |
| Secretaría de Energía | Río Coronda, Romang, Rosario Oeste y Santo Tomé | CSV de estaciones |
| Copernicus | SSRD horario ERA5-Land | Time-Series / ARCO Zarr |

SSRD se convierte de J/m² a kWh/m² dividiendo por 3.600.000. Se exigen horas
únicas, completas y finitas para enero, abril, julio y octubre. Se promedian
años por mes y se ponderan medias diarias por días de estación. El indicador
anual es una estimación estacional, no integración de doce meses.
Cada celda referencia el píxel climático nativo más cercano, sin interpolación.

Las distancias se calculan desde el **centroide del parque ponderado por área**,
en un CRS métrico. Las estaciones consideradas son CN Río Coronda, RM Romang,
RO Rosario Oeste y ST Santo Tomé. La capa de líneas incluye distribución y no
demuestra aptitud para conectar una planta. No hay capacidad libre en MVA.

## Cromosoma y crecimiento

`Individual(seed_cell_id, growth_genes)` contiene una celda inicial y una
secuencia variable de enteros. Cada gen elige `gene % len(frontier)` sobre una
frontera ordenada. Su significado depende de esa frontera, no de una dirección fija.

Solo se incorporan celdas válidas conectadas por un segmento de borde. Las
esquinas no conectan. Si la elegida excede capacidad, se omite la instrucción y
se continúa. Termina al agotar genes, frontera o posibilidad de crecimiento.
La semilla debe caber por sí sola. No hay superficie mínima adicional.
Distintos cromosomas pueden representar el mismo conjunto de celdas.

## Potencia y fitness

Potencia = área real en km² × 31,3 MWac/km². La densidad se refiere al **área
total del parque**, con separaciones y caminos. Deriva de 7,9 acres/MWac para
grandes plantas en [NREL, tabla ES-1](https://docs.nrel.gov/docs/fy13osti/56290.pdf).
No calcula el porcentaje exacto cubierto por paneles. Una celda completa de
500 × 500 m representa 25 ha y 7,825 MWac. El máximo actual es 80 MW experimentales.

| Criterio | Score | Peso |
|---|---|---:|
| Irradiación media ponderada por área | Min-max del dataset | 0,35 |
| Distancia a línea | Min-max invertido | 0,10 |
| Distancia a estación | Min-max invertido | 0,35 |
| Potencia | P / 80 MW | 0,10 |
| Compactación | 4πA / perímetro² | 0,10 |

Los scores se recortan a [0,1]. Las escalas permanecen fijas durante la corrida.
Los cinco pesos suman 1 y son experimentales. Exclusión urbana, contigüidad y
capacidad son restricciones obligatorias.

El perímetro total incluye huecos. Se calcula sumando perímetros de celdas y
restando dos veces sus bordes compartidos, precalculados una vez. Compactación
es una preferencia geométrica, no un costo constructivo. Un cuadrado puntúa π/4.

La energía ideal de referencia es `P_MW × H_kWh/m² / (1 kW/m²)`. No integra
pérdidas, temperatura, inclinación o diseño DC/AC y no es generación vendible.

## Algoritmo y salidas

Población 50, generaciones 200, torneo 3 y elitismo 2. La inicialización recorre
sectores ocupados de 50 km en orden aleatorio, elige una celda en cada sector y
genera secuencias de longitud variable. La semilla aleatoria controla
reproducibilidad y es distinta de la celda semilla.

Crossover `competitive_homologous`, probabilidad 0,75: compacta instrucciones
efectivas, ensaya hasta tres cortes comunes e intercambia sufijos conservando
la celda inicial propia. Acepta mejoras o empates con otro parque. La garantía
corresponde al operador; mutación y reemplazo posteriores pueden cambiar el hijo.

Mutación, probabilidad 0,20: agregar, truncar, cambiar una instrucción efectiva
o cambiar semilla. Las operaciones aplicables tienen igual probabilidad. Hasta
cuatro intentos buscan cambiar celdas; si no lo logran, conserva el original.
Cambio efectivo no significa mejor fitness.

Hasta ocho reintentos reemplazan duplicados. Agotarlos permite una repetición
y registra el evento, garantizando terminación. Parada fija en 200 generaciones.

Archivo: hasta diez candidatos por sector del centroide. Top 5 general: mejores
scores, puede incluir variantes superpuestas. Top 5 territorial: selección voraz
sin superposición y con separación adicional configurable, actualmente 0 km.
No garantiza cinco sitios ni la mejor combinación conjunta. El archivo puede
descartar alternativas útiles. Mejorar retención y combinar semillas son pendientes.

## Límites

Faltan capacidad libre y flujos de red, inundaciones, áreas protegidas, pendiente,
propiedad y uso del terreno, accesos y costos. Las omisiones delimitan el alcance.
Un candidato válido dentro del modelo necesita evaluación de viabilidad posterior.
No se certifica optimalidad global. La cartografía urbana es censal, no catastral,
y el historial climático disponible es breve.

Implementación: `src/config/settings.py`, `src/pipeline/`, `src/gis/`,
`src/climate/`, `src/optimization/` y `src/database/spatial.py`.
