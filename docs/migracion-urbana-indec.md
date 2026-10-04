# Migración de la exclusión urbana a INDEC

Rama: `codex/migracion-envolventes-indec`. Fecha local: 3 de octubre de 2026.

## Fuente y procesamiento

La configuración utiliza [Localidades censales del INDEC](https://geonode.indec.gob.ar/layers/geonode_data:geonode:localidades_censales),
correspondiente al Censo 2022. [Metadatos oficiales](https://portalgeoestadistico.indec.gob.ar/geoportal/documents/metadato_localidades_censales.pdf).
La publicación del catálogo puede ser posterior; no implica que la geometría represente ese año.
La cartografía censal se define por continuidad física y tiene fines estadísticos.

El WFS 2.0 entrega multipolígonos en EPSG:4326. Se descargan todas las páginas
ordenadas por `fid`, verificando el total anunciado, el número de registros
devueltos y la unicidad de los IDs. No se admite una descarga parcial ni un
reemplazo silencioso por BAHRA. Los `clc` compartidos entre provincias se conservan,
como requiere la doble representación geométrica documentada por INDEC.

La caché `urban_areas_envelopes` contiene la fuente nacional completa. Se registra
un SHA-256 de los features GeoJSON ordenados, la URL, capa, año, fecha de descarga,
cantidad y atribución. El SHA no corresponde a los bytes del GeoPackage.

El procesamiento sigue esta secuencia:

1. Validar polígonos, CRS y geometrías no vacías; reparar geometrías inválidas sin
   descartar componentes. Una reparación que produce líneas requiere revisión.
2. Reproyectar al CRS métrico derivado de la región.
3. Seleccionar localidades cuyo contorno o margen alcance la provincia, conservando
   los componentes completos de los aglomerados seleccionados.
4. Unir por `codaglo` válido. `N/A` identifica localidades simples que permanecen
   separadas. No se calcula una envolvente convexa.
5. Rellenar huecos interiores encerrados cuando `fill_holes: true`. Es una política
   conservadora de exclusión, no una reclasificación del suelo como edificado.
6. Aplicar `buffer_km` desde el perímetro y recortar al límite provincial.
7. Excluir toda celda que intersecte o toque la máscara, incluso por borde o vértice.

La máscara se persiste en el CRS métrico del cálculo, con precisión completa.
Los atributos INDEC se guardan en la tabla nueva `layer_urban_envelopes`;
`layer_urban` conserva su esquema de geometrías para admitir la base existente
sin alterar tablas históricas.
El mapa usa esa capa y solamente la reproyecta para su visualización. Se registran
cantidad y área de huecos, reparaciones, áreas antes/después del margen y celdas excluidas.

## Validación del caso Rosario

Corrida histórica: `run-20260928T134148-b01f2d3a`, utilizada por ambos informes.
Parque: puesto 2 territorial, centro aproximado (-32.91569, -60.75001), 250 ha,
10 celdas. Se utilizó su polígono completo y las geometrías originales de sus celdas.

La descarga nacional contiene **4.023 features**. El Gran Rosario tiene código
`0003` y **20 componentes**, todos conservados. Sus envolventes originales cubren
**250 ha del parque (100%)**. Las **10 celdas quedan excluidas con margen 0 m**.
El resultado es idéntico para márgenes 100, 250 y 500 m. El problema del parque
se corrige con la geometría original, sin aumentar artificialmente el margen.

No se encontraron huecos interiores en la unión original del Gran Rosario ni
en las agrupaciones seleccionadas para la validación provincial. La política
de relleno está cubierta con regresiones sintéticas, incluyendo huecos que aparecen
al unir componentes y huecos que se abren si se recorta prematuramente a la provincia.

## Sensibilidad provincial

Comparación sobre las **535.751 celdas de la grilla histórica de 500 m**, sin
reconstruirla ni modificar la base histórica. BAHRA excluía 49.947 celdas.

| Margen | Celdas excluidas INDEC | Nuevas exclusiones respecto de BAHRA | Antes excluidas, ahora sin exclusión urbana |
|---:|---:|---:|---:|
| 0 m | 9.557 | 2.146 | 42.536 |
| 100 m | 11.061 | 2.380 | 41.266 |
| 250 m | 13.391 | 2.754 | 39.310 |
| 500 m | 17.582 | 3.523 | 35.888 |

La menor cantidad total no significa menor protección de Rosario: los círculos
BAHRA también excluían extensas superficies exteriores a localidades pequeñas.
Las nuevas exclusiones y las superficies liberadas deben revisarse territorialmente.
“Sin exclusión urbana” no significa disponibilidad predial, ambiental o climática.

El margen configurado es **0 km**, como línea de base. La sensibilidad no es una
calibración: para seleccionar un margen definitivo faltan referencias recientes e
independientes de bordes urbanos y una evaluación de omisión/exceso en localidades
de distintos tamaños. La fuente representa 2022 y no garantiza cubrir crecimiento posterior.

## Reproducción y resultados

```powershell
.\.venv\Scripts\python.exe -m tools.validate_urban_exclusion --run results/spatial/run-20260928T134148-b01f2d3a --output results/urban-validation/nueva-auditoria
```

El directorio debe ser nuevo. Resultados locales de esta validación:

- `results/urban-validation/indec-20261003/provincial_sensitivity.csv`
- `results/urban-validation/indec-20261003/rosario_sensitivity.csv`
- `results/urban-validation/indec-20261003/historical_parks.csv`
- `results/urban-validation/indec-20261003/provenance.json`
- `results/urban-validation/indec-20261003/rosario_map.html`
- Envolventes del Gran Rosario y máscara provincial exportadas a GeoJSON.

El script abre la base histórica en modo solo lectura. No modifica las corridas
ni regenera los informes previos. La tabla de parques históricos identifica además
intersecciones parciales en otra corrida anterior, no solamente el caso señalado.

## Integración y verificación

El procesamiento pasa a versión 3 y requiere `--download`, `--process` y luego
`--optimize`. Las configuraciones BAHRA (`include_types`, `urban_areas.resource_id`)
se rechazan con validación de esquema. Los snapshots previos permanecen intactos;
no son compatibles con la nueva firma. Si cambia el SHA INDEC tras una descarga
forzada, la optimización exige reprocesar.

Los informes generados describen la fuente registrada en la corrida: BAHRA para
corridas históricas e INDEC para nuevas. No se reescribieron archivos de informes.

Verificación final: **73 pruebas aprobadas**, compilación Python y revisión de
espacios en el diff sin errores. Las dependencias Pillow y python-docx faltantes
en el entorno virtual se instalaron para ejecutar también las pruebas de informes.

Se verifican geometrías irregulares, huecos, márgenes métricos, aglomerados, `N/A`,
localidades fuera de la provincia, contacto por bordes, paginación incompleta,
datos inválidos, persistencia de la máscara y parques que no intersectan la exclusión.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools/validate_urban_exclusion.py
```

La auditoría provincial utiliza datos reales. La prueba integrada de procesamiento,
optimización y mapa utiliza clima y geometrías sintéticos para evitar dependencia
de la red. No se lanzó una nueva optimización provincial ni se descargó clima nuevo.
