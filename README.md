# Optimización de ubicaciones de parques solares — MVP (Santa Fe, Argentina)

Sistema que usa un **Algoritmo Genético** para identificar celdas de una grilla
de 5×5 km dentro de la provincia de Santa Fe que resulten **potencialmente
favorables** para instalar un parque solar fotovoltaico de 2 ha, en base a:

1. Radiación solar (Copernicus **ERA5-Land hourly time-series data from 1950
   to present** — el dataset ARCO/Time-Series, no ERA5 ni ERA5-Land mensual).
2. Distancia a líneas de la red eléctrica.
3. Distancia a centros/subestaciones transformadoras (con **mayor peso** que
   la cercanía a líneas).
4. Exclusión total (no penalización) de celdas que intersectan zonas urbanas.

> **Importante:** este es un MVP. Los resultados son *"ubicaciones
> potencialmente favorables según las variables espaciales y climáticas
> consideradas"* — no una determinación de ubicación económicamente óptima.
> Ver [Limitaciones](#limitaciones-del-mvp).

---

## Instalación

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

Requiere Python ≥3.11. Probado con Python 3.14 sobre Windows (usa
`pyogrio` en vez de `fiona` como motor de I/O de GeoPandas porque `fiona`
todavía no publica wheels binarios para versiones muy nuevas de Python;
funcionalmente son intercambiables).

### Credenciales de Copernicus CDS

**Nunca se hardcodean credenciales.** Para usar ERA5-Land Time-Series:

1. Crear una cuenta gratuita en <https://cds.climate.copernicus.eu>.
2. Iniciar sesión y abrir <https://cds.climate.copernicus.eu/how-to-api> para
   obtener tu *personal access token*.
3. Copiar `.env.example` a `.env` y completar:
   ```
   CDS_API_KEY=tu-token-aquí
   ```
4. `.env` está en `.gitignore` — nunca se sube al repositorio.
5. Aceptar los términos de uso del dataset en su página (requisito de CDS
   antes de poder descargar datos).

---

## Uso (CLI)

```bash
python -m src.main --setup       # valida configuración, crea directorios
python -m src.main --download    # descarga/cachea capas de datos.gob.ar + IGN
python -m src.main --process     # grilla + distancias + clima -> candidatos
python -m src.main --optimize    # corre el AG, genera ranking + mapa
python -m src.main --run-all     # las 4 anteriores en secuencia
python -m src.main --test-era5   # diagnóstico de UN punto (ver Fase 10 abajo)
```

Agregar `--force` a `--download` para ignorar la caché en disco y volver a
descargar todo. `--config ruta.yaml` permite usar un archivo de configuración
alternativo.

### Antes de la primera descarga masiva de clima: `--test-era5`

Antes de descargar el clima de toda la grilla, correr:

```bash
python -m src.main --test-era5
```

Esto pide **una sola coordenada** (el centroide de la región) para **un solo
mes**, y muestra explícitamente: coordenada solicitada, coordenada ERA5-Land
realmente usada (nearest-neighbour, confirmado por el propio servidor CDS),
período, cantidad de registros horarios, unidad, primeros valores, método de
agregación, y si el resultado es físicamente plausible. Esto es intencional:
el mecanismo de acceso al dataset Time-Series fue confirmado contra el
esquema real de CDS (ver [Nota técnica ERA5-Land](#nota-técnica-era5-land)),
pero **nunca fue ejercido con credenciales reales** durante el desarrollo de
este MVP — este comando es el punto donde se verifica empíricamente antes de
confiar en una descarga masiva.

---

## Arquitectura

```
APIs (datos.gob.ar, IGN, Copernicus CDS)
        |  src/api/*
        v
ETL (ingesta + caché)         src/pipeline/ingest.py, src/data/*
        v
Procesamiento geoespacial     src/gis/*, src/climate/*
        v
Base de datos local (SQLite)  src/database/*
        v
Algoritmo Genético            src/optimization/*   (nunca llama APIs)
        v
Resultados (CSV/JSON/HTML)    src/pipeline/reporting.py, src/visualization/*
```

```
src/
  api/                    Clientes HTTP crudos (datos.gob.ar, Copernicus CDS)
  data/                   Descarga genérica, caché, validadores, conversión de unidades
  gis/                    CRS, grilla, operaciones espaciales, distancias
  database/               Modelos SQLAlchemy + repositorio (único punto de acceso a la DB)
  climate/                Asociación grilla<->ERA5-Land, agregación de radiación
  optimization/           Fitness, selección, cruce, mutación, algoritmo genético
  visualization/          Mapa Folium
  pipeline/               Orquestación: ingest -> preprocess -> reporting
  config/                 Carga y validación de config.yaml + .env
  main.py                 CLI
tests/                    Tests unitarios (sin red — todo mockeado)
config.yaml               Toda la configuración editable del MVP
.env.example              Documenta CDS_API_KEY sin exponer ningún valor real
```

El GA (`src/optimization/genetic_algorithm.py`) **solo lee** de la tabla
`candidate_locations` a través del repositorio — nunca llama una API ni hace
I/O de red. Esto está verificado por diseño (el módulo no importa `requests`,
`cdsapi` ni los módulos de `src/api/`).

---

## Configuración (`config.yaml`)

Todos los parámetros del MVP son editables sin tocar código:

```yaml
region:
  name: "Santa Fe"
  admin_source: {...}      # de dónde sale el límite administrativo (IGN)
grid:
  resolution_km: 5
park:
  area_hectares: 2
urban_exclusion:
  buffer_km: 3.0
  include_types: ["LOCALIDAD"]
climate:
  dataset: "reanalysis-era5-land-timeseries"   # validado, no se puede cambiar sin justificar
  variable: "surface_solar_radiation_downwards"
  years: [2024]
  months: [1, 4, 7, 10]
infrastructure:
  urban_areas: {resource_id: "..."}
  power_lines: {resource_id: "..."}
  transformers: {source_url: "..."}
fitness:
  weight_solar: 0.50
  weight_grid_distance: 0.20
  weight_transformer_distance: 0.30
genetic_algorithm:
  population_size: 50
  generations: 100
  crossover_probability: 0.75
  mutation_probability: 0.05
  elitism: 2
  tournament_size: 3
  random_seed: 42
```

`src/config/settings.py` valida con Pydantic, entre otras cosas:

- Los tres pesos de fitness **suman 1.0** (± 1e-6).
- `weight_transformer_distance >= weight_grid_distance` (la cercanía a
  transformadores nunca puede pesar menos que la cercanía a líneas).
- `climate.dataset` debe ser exactamente `reanalysis-era5-land-timeseries`
  (rechaza sustituirlo silenciosamente por ERA5, ERA5-Land mensual, etc.).
- `elitism < population_size`, meses en 1-12, años ≥1950, etc.

Los pesos de fitness son **valores iniciales del MVP, no pesos
científicamente validados** — están pensados para ser recalibrados.

### Cambiar de provincia

`region.name` **no está hardcodeado en ningún módulo de lógica** — todo el
código de grilla/distancias/CRS lee `settings.region`. Para apuntar a otra
provincia argentina:

1. Cambiar `region.name` y `region.admin_source.code_value` (código
   INDEC/GeoRef de la provincia; el shapefile del IGN usado ya cubre las 23
   provincias + CABA).
2. **Revisar las fuentes de infraestructura**: `infrastructure.power_lines`
   y `infrastructure.transformers` son datasets específicos que en la
   práctica solo cubren Santa Fe (ver nota en
   `src/pipeline/ingest.py::ingest_power_lines` — el dataset de líneas,
   pese a su nombre genérico "Consejo Federal", resultó cubrir solo el
   área de Santa Fe al inspeccionarlo). Para otra provincia hay que
   encontrar y configurar una fuente equivalente, y el pipeline **fallará
   explícitamente** (no en silencio) si el resultado clippeado da vacío.
3. `infrastructure.urban_areas` (BAHRA) sí es un dataset nacional real y
   funciona para cualquier provincia sin cambios.
4. El CRS proyectado se recalcula automáticamente vía
   `estimate_utm_crs()` — nunca hay que tocar un EPSG a mano.

---

## Fuentes de datos y trazabilidad

| Capa | Fuente | Tipo de geometría (confirmado por inspección) | Notas |
|---|---|---|---|
| Límite provincial | IGN — Unidades Territoriales (`ign_provincia.zip`) | Polygon/MultiPolygon, EPSG:4326 | https://datos.gob.ar/dataset/unidades-territoriales |
| Zonas urbanas | BAHRA (datos.gob.ar DataStore, resource `c1fc1f5b-...`) | **Point** (no polígono) | Se aproxima el área urbana con un buffer configurable — ver abajo |
| Líneas eléctricas | Redes de distribución eléctrica del Consejo Federal (datos.gob.ar, resource `3d5eda86-...`) | MultiLineString + atributo `tension` | Sin subestaciones — solo `tension` (voltaje) |
| Centros transformadores | Secretaría de Energía — "Transporte Eléctrico AT Estaciones Transformadoras" (CSV directo, datos.gob.ar) | Point (normalizado desde MultiPoint) | Fuente independiente, obligatoria — ver más abajo |
| Radiación solar | Copernicus CDS `reanalysis-era5-land-timeseries` | Punto (nearest-neighbour) | Ver sección dedicada |

Cada capa ingerida se cachea en `data/raw/layers/*.gpkg` junto a un
`*.meta.json` con: fuente, URL, timestamp de descarga, CRS nativo, y
conteos. `solar_radiation` en la base guarda además `era5_latitude`,
`era5_longitude`, `source` y `download_timestamp` por fila.

### Por qué existe una fuente separada para transformadores

El dataset de líneas eléctricas (`redes-de-distribucion-electrica-del-consejo-federal`)
fue inspeccionado (Fase 3) y **no contiene subestaciones ni centros
transformadores** — solo geometría de línea + voltaje. Como el requisito de
distinguir línea vs. transformador es obligatorio, se buscó y confirmó una
fuente oficial alternativa (Secretaría de Energía de la Nación, dataset
"Transporte Eléctrico AT Estaciones Transformadoras"), verificando que
efectivamente cubre Santa Fe antes de integrarla. **Si esta fuente
desaparece, el pipeline debe fallar explícitamente** (`validate_layer_present`
en `src/data/validators.py`) — nunca corre el AG ignorando el criterio en
silencio.

### Por qué las zonas urbanas usan un buffer

BAHRA (`localidades-bahra`) resultó ser, al inspeccionar su schema real, una
capa de **puntos**, no de polígonos. Para aproximar un área urbana se
bufferiza cada punto por `urban_exclusion.buffer_km` en un CRS proyectado.
Además, BAHRA mezcla localidades reales (`tipo=LOCALIDAD`, 386 en Santa Fe)
con sitios edificados aislados (`tipo=SITIO EDIFICADO`, 473 — escuelas
rurales, estancias, edificios sueltos) y una categoría rara
(`tipo=ENTIDAD`, 6). Bufferizar **todos** los tipos a 3 km excluye ≈48% de
toda la provincia (dominado por los puntos aislados, que no son zonas
urbanas reales); por eso `urban_exclusion.include_types` sólo usa
`LOCALIDAD` por defecto (≈26% de exclusión, mucho más razonable). Esta es
una aproximación de MVP documentada, no un límite catastral real — queda
preparado para reemplazarse por una capa de polígonos urbanos reales.

---

## Nota técnica: ERA5-Land Time-Series

Antes de escribir el cliente (`src/api/copernicus_era5_land.py`) se
inspeccionó el **schema real** que expone el propio servicio CDS para este
dataset específico (`form.json`, `constraints.json`, y la descripción OGC
del proceso en `/api/retrieve/v1/processes/reanalysis-era5-land-timeseries`)
en vez de asumir un formato de request. Hallazgos confirmados:

- **Acceso oficial**: librería `cdsapi` (`cdsapi.Client().retrieve(...)`),
  con `~/.cdsapirc` o los kwargs equivalentes (`url`, `key`) — usados aquí
  para que la clave venga de `CDS_API_KEY` en el entorno, nunca de un
  archivo versionado.
- **Selección espacial**: el schema formal del dataset expone un campo
  `area` (bounding box `[N, W, S, E]`), no una clave `location` separada —
  aunque el formulario interactivo ofrece un selector "por ubicación" como
  atajo de UI sobre ese mismo campo. Este cliente reproduce ese
  comportamiento pidiendo una caja mínima centrada en el punto
  (`climate.point_bbox_epsilon_deg`, muy por debajo de los 0.1° de
  separación de la grilla nativa). La documentación del propio dataset dice
  textualmente: *"When a user's requested location does not exactly match a
  grid point, the nearest grid point is automatically selected"* — es
  decir, el nearest-neighbour lo aplica el servidor, no este cliente.
- **Semántica de SSRD — el detalle más importante**: CDS etiqueta la
  variable en este dataset específico como **"Surface solar radiation
  downwards (de-accumulated)"**. A diferencia del archivo crudo/bulk de
  ERA5-Land (donde SSRD es un acumulado desde el inicio del forecast y hay
  que de-acumular restando horas consecutivas), en el dataset Time-Series
  **cada valor horario ya representa la radiación de esa hora puntual**.
  Por eso la agregación mensual implementada
  (`src/climate/radiation.py::aggregate_monthly_kwh_m2`) es una simple
  suma de los J/m² horarios del mes.
- **Transformación de unidad**: valor original en **J/m²** →
  suma horaria del mes → división por 3.6×10⁶ (1 kWh = 3.6×10⁶ J) →
  **kWh/m²/mes** (unidad final, elegida por interpretabilidad).

**Advertencia honesta**: este mapeo se derivó del schema real de CDS, pero
**no se ejerció contra el servicio con credenciales reales** (no había una
`CDS_API_KEY` disponible al construir este MVP). Por eso existe
`python -m src.main --test-era5`: antes de cualquier descarga masiva, corre
una solicitud de un solo punto/mes y imprime todos los diagnósticos
necesarios (coordenada solicitada vs. usada, unidad, primeros valores,
plausibilidad física) para confirmar o corregir el supuesto de
de-acumulación antes de confiar en el resto del pipeline. Si CDS cambiara
el schema, sólo `src/api/copernicus_era5_land.py` y
`src/climate/radiation.py` deberían necesitar ajustes.

### Caché ERA5-Land y por qué no se pide una vez por celda

La grilla de análisis es de 5 km; ERA5-Land tiene resolución nativa de
~9 km (0.1° × 0.1°). Por lo tanto varias celdas comparten el mismo punto
ERA5-Land. `src/climate/era5_land.py::predict_nearest_era5_grid_point`
redondea cada centroide de celda al punto de grilla 0.1° más cercano
**localmente**, solo para **agrupar** celdas antes de consultar — el CDS
hace su propia selección de vecino más cercano autoritativa en el servidor.
`src/data/cache.py::Era5LandCache` persiste en
`data/cache/era5_land_cache/` una serie horaria por
`(variable, año, mes, punto)`, así que si dos celdas mapean al mismo punto,
la segunda se sirve desde disco. No se interpola: se usa nearest-neighbour,
igual que la metodología documentada del propio dataset — la arquitectura
queda preparada para agregar interpolación como una estrategia alternativa
sin tocar la lógica de agrupación/caché.

---

## Superficie del parque (2 ha) — qué se garantiza y qué no

`park.area_hectares` (2 ha = 20.000 m² = 0.02 km²) se **almacena** como
parámetro y aparece en `optimization_run.json`, pero este MVP **no verifica**
que existan 20.000 m² contiguos realmente disponibles dentro de una celda
(no hay todavía una capa de cobertura/uso de suelo). La celda de 5×5 km es
una unidad espacial de análisis — no una afirmación de que toda esa área
esté disponible para el parque.

---

## Limitaciones del MVP

Los resultados son **"ubicaciones potencialmente favorables según las
variables espaciales y climáticas consideradas"** — no una determinación de
ubicación económicamente óptima. Explícitamente **no** se considera todavía:

- Costo de terreno ni costo de conexión.
- Capacidad disponible de subestación o de línea.
- Permisos, restricciones legales completas, áreas protegidas.
- Cobertura/uso de suelo completo, pendiente, hidrografía.
- Disponibilidad física real de los 20.000 m² contiguos.
- Sombras, orientación, análisis financiero, mediciones in situ.
- Más de un año / más meses de clima (queda preparado, no implementado).

Los pesos de la función de fitness (`fitness.weight_*`) son valores
iniciales de MVP, no pesos científicamente calibrados.

---

## Extensiones futuras (arquitectura ya preparada)

- Más años/meses de ERA5-Land (2015-2024, etc.) y estadísticos de
  variabilidad interanual (media, mediana, desvío, percentiles) — las
  tablas `solar_radiation` ya son (celda, año, mes) por fila.
- Interpolación espacial en vez de nearest-neighbour.
- Capas adicionales de exclusión/ponderación: uso de suelo (WorldCover),
  elevación/pendiente (SRTM), áreas protegidas, cuerpos de agua.
- Capacidad de subestación, tensión de línea, costo de conexión.
- Otras provincias argentinas (ver "Cambiar de provincia" arriba).

---

## Tests

```bash
pytest tests/ -v
```

56 tests, **ninguno toca la red** (los clientes HTTP/CDS se mockean).
Cubren: generación de grilla, selección de CRS, distancias en CRS
proyectado, normalización y fitness, conversión de SSRD y agregación
mensual, asociación celda↔punto ERA5-Land, exclusión urbana, validación de
configuración, y el algoritmo genético (selección/cruce/mutación/elitismo,
convergencia hacia un óptimo conocido).

---

## Salidas

```
results/
  ranking.csv              # TOP 10 con desglose mensual de radiación
  candidate_locations.csv  # todas las celdas evaluadas (válidas e inválidas)
  optimization_run.json    # config usada, pesos, parámetros del AG, disclaimer
  map.html                 # límite, grilla, zonas urbanas, líneas, transformadores, TOP 10
logs/
  run_<timestamp>.log
data/
  raw/layers/*.gpkg        # capas ingeridas, cacheadas, con metadata de trazabilidad
  cache/era5_land_cache/   # series horarias ERA5-Land, cacheadas por punto/año/mes
  processed/parque_solar.sqlite
```
