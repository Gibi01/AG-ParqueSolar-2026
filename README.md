# Optimización de ubicaciones de parques solares — MVP (Argentina)

Sistema que usa un **Algoritmo Genético** para identificar celdas de una grilla
configurable dentro de Santa Fe que resulten **potencialmente
favorables** para instalar un parque solar fotovoltaico de 2 ha, en base a:

1. Radiación solar (Copernicus **ERA5-Land hourly time-series data from 1950
   to present** — el dataset ARCO/Time-Series, no ERA5 ni ERA5-Land mensual).
2. Distancia a líneas de la red eléctrica.
3. Distancia a centros/subestaciones transformadoras (criterio opcional).
4. Exclusión total (no penalización) de celdas que intersectan zonas urbanas.

> **Importante:** este es un MVP. Los resultados son *"ubicaciones
> potencialmente favorables según las variables espaciales y climáticas
> consideradas"* — no una determinación de ubicación económicamente óptima.
> Ver [Limitaciones](#limitaciones-del-mvp).

---

## Cómo ejecutar en Windows

1. Instalar Python 3.11 o superior y comprobar que el comando `py -3`
   funciona en la consola.
2. Crear el entorno virtual e instalar las dependencias (solo la primera vez),
   desde PowerShell o Símbolo del sistema en la carpeta del proyecto:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Guardar el token de Copernicus en `.env` como se explica abajo. ARCO usa
   ese token para acceder al almacén Zarr.
4. Revisar las variables de `config.yaml` antes de la corrida. La región
   está fijada en Santa Fe; ver la [guía breve de configuración](#guía-breve-para-preparar-una-corrida).
5. Ejecutar el pipeline desde la misma carpeta:

   ```powershell
   .\.venv\Scripts\python.exe -m src.main --run-all
   ```

6. Si el comando termina sin errores, abrir `results/map.html` en el navegador.
   El HTML no se abre automáticamente; si la corrida falla, no confundir un
   archivo de una corrida anterior con un resultado nuevo.

La primera corrida descarga datos externos. La radiación se lee directamente
del almacén ARCO Zarr de Copernicus por bloques espaciales y se resume
localmente a los cuatro meses
representativos desde 1970. Los resúmenes se guardan en
`data/cache/arco_blocks/` para reutilizarlos en corridas posteriores.
El acceso directo utiliza el [almacén ARCO geo-chunked de ERA5-Land](https://confluence.ecmwf.int/spaces/CKB/pages/536218894/ERA5-Land+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1950+to+present+Product+User+Guide+PUG).

Los resultados adicionales se guardan en `results/ranking.csv`,
`results/candidate_locations.csv` y `results/optimization_run.json`.

El mapa usa mosaicos públicos de OpenStreetMap y necesita conexión para
mostrar el fondo. Al abrir el HTML localmente, el navegador no envía un
`Referer` web válido; el cargador de mosaicos envía en su lugar un encabezado
`X-Requested-With` estable que identifica al proyecto, según la
[guía de OSM para páginas `file://`](https://wiki.openstreetmap.org/wiki/Referer).
Solo se solicitan los mosaicos visibles y se usa la caché HTTP normal del
navegador. No se descargan regiones por adelantado ni se ofrecen mapas sin
conexión. Si siguen apareciendo imágenes de bloqueo, inspeccionar en Network
una solicitud completada y su vista previa: el mensaje genérico no indica
una causa única.

Las comprobaciones acotadas del cargador se ejecutan con
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`. La prueba de
JavaScript usa Node.js si está disponible; no hace solicitudes a OSM.

Probado con Python 3.14 sobre Windows (usa
`pyogrio` en vez de `fiona` como motor de I/O de GeoPandas porque `fiona`
todavía no publica wheels binarios para versiones muy nuevas de Python;
funcionalmente son intercambiables).

### Credencial para ARCO

**Nunca se hardcodean credenciales.** Para leer ERA5-Land desde ARCO:

1. Crear una cuenta gratuita en <https://cds.climate.copernicus.eu>.
2. Iniciar sesión y abrir <https://cds.climate.copernicus.eu/how-to-api> para
   obtener tu *personal access token*.
3. En la carpeta del proyecto, copiar `.env.example` a `.env` con
   `copy .env.example .env` y completar:
   ```
   CDS_API_KEY=tu-token-aquí
   ```
4. `.env` está en `.gitignore` — nunca se sube al repositorio.
5. El nombre `CDS_API_KEY` se conserva para compatibilidad con los `.env`
   existentes. El programa ya no usa la API de solicitudes CDS.

---

## Ejecución por etapas (opcional)

Si se necesita repetir solo una etapa, usar el Python del entorno virtual
desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m src.main --setup       # valida configuración
.\.venv\Scripts\python.exe -m src.main --download    # descarga capas espaciales
.\.venv\Scripts\python.exe -m src.main --process     # grilla, distancias y clima
.\.venv\Scripts\python.exe -m src.main --optimize    # ranking y mapa
.\.venv\Scripts\python.exe -m src.main --run-all     # todas las etapas
```

Agregar `--force` a `--download` para ignorar la caché en disco y volver a
descargar todo. `--config ruta.yaml` permite usar un archivo de configuración
alternativo.

La corrida usa enero, abril, julio y octubre desde 1970. `end_year: latest`
incluye el mes representativo más reciente que terminó con al menos un mes
de margen para la publicación de datos. Para cada celda se calcula primero la
media histórica de la radiación mensual de cada mes elegido. Cada valor se
divide por los días de ese mes para obtener la irradiación diaria media; se
proyecta a los días de su estación (enero→verano, abril→otoño, julio→invierno,
octubre→primavera) y se suman las cuatro estaciones. El resultado es una
**estimación de radiación anual en kWh/m²/año**, no una medición de los doce
meses. El ranking muestra esa estimación y las cuatro medias mensuales;
`optimization_run.json` registra el período utilizado.

## Arquitectura

```
Fuentes (datos.gob.ar, IGN, Copernicus ARCO)
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
  api/                    Clientes HTTP de datos.gob.ar
  data/                   Descarga genérica, caché, validadores, conversión de unidades
  gis/                    CRS, grilla, operaciones espaciales, distancias
  database/               Modelos SQLAlchemy + repositorio (único punto de acceso a la DB)
  climate/                Lectura ARCO y agregación de radiación
  optimization/           Fitness, selección, cruce, mutación, algoritmo genético
  visualization/          Mapa Folium
  pipeline/               Orquestación: ingest -> preprocess -> reporting
  config/                 Carga y validación de config.yaml + .env
  main.py                 CLI
config.yaml               Toda la configuración editable del MVP
.env.example              Documenta el token ARCO sin exponer ningún valor real
```

El GA (`src/optimization/genetic_algorithm.py`) **solo lee** de la tabla
`candidate_locations` a través del repositorio — nunca llama una API ni hace
I/O de red. Esto está verificado por diseño (el módulo no importa `requests`
ni los módulos de `src/api/`).

---

## Configuración (`config.yaml`)

La grilla, las variables de evaluación y el algoritmo son configurables sin
tocar código. La región permanece fija en Santa Fe en esta versión:

```yaml
region:
  name: "Santa Fe"
  admin_source: {...}      # de dónde sale el límite administrativo (IGN)
grid:
  resolution_km: 9
park:
  area_hectares: 2
urban_exclusion:
  buffer_km: 3.0
  include_types: ["LOCALIDAD"]
climate:
  dataset: "reanalysis-era5-land-timeseries"   # validado, no se puede cambiar sin justificar
  variable: "surface_solar_radiation_downwards"
  start_year: 1970
  end_year: latest
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
- La región debe ser `region.name: "Santa Fe"` y
  `region.admin_source.code_value: "82"`; otra combinación se rechaza antes
  de descargar datos.
- Un peso `0` desactiva ese criterio: no se exige ni descarga su fuente y
  sus métricas quedan vacías. Ejemplo sin transformadores:
  `weight_solar: 0.60`, `weight_grid_distance: 0.40`,
  `weight_transformer_distance: 0.00`. La exclusión urbana permanece activa.
- `climate.dataset` debe ser exactamente `reanalysis-era5-land-timeseries`
  (rechaza sustituirlo silenciosamente por ERA5, ERA5-Land mensual, etc.).
- `elitism < population_size`, meses en 1-12, años ≥1950, etc.

Los pesos de fitness son **valores iniciales del MVP, no pesos
científicamente validados** — están pensados para ser recalibrados.

### Guía breve para preparar una corrida

1. Mantener `region.name: "Santa Fe"` y
   `region.admin_source.code_value: "82"`. El límite provincial y las zonas
   urbanas se cargan automáticamente; no hay que indicar localidades.
2. Elegir el tamaño de celda con `grid.resolution_km` (por ejemplo, `9`
   para celdas de 9×9 km). `park.area_hectares` describe la superficie
   buscada para el parque; **no** cambia el tamaño de la grilla.
3. Ajustar `fitness.weight_solar`, `fitness.weight_grid_distance` (distancia
   a líneas eléctricas) y `fitness.weight_transformer_distance` (distancia
   a transformadores). Deben sumar `1.0`; poner un peso en `0` desactiva
   ese criterio y evita necesitar su fuente. Por ejemplo, para no usar
   transformadores: `0.60`, `0.40`, `0.00`, respectivamente. La exclusión
   urbana sigue activa y se regula aparte con `urban_exclusion`.
4. Mantener las fuentes espaciales configuradas para Santa Fe. Si una fuente
   activa no devuelve datos, el proceso se detiene; no inventa ubicaciones.
5. Si interesa otro período climático, cambiar `climate.start_year` y
   `climate.end_year` (`latest` para llegar al último mes disponible).
   Mantener `climate.months: [1, 4, 7, 10]`: son los cuatro meses
   representativos exigidos para la estimación anual. La única fuente
   climática implementada es ARCO.
6. Para conservar los resultados de otra configuración, usar un
   archivo YAML separado con rutas distintas en `paths.database` y
   `paths.results`, y ejecutar:

   ```powershell
   .\.venv\Scripts\python.exe -m src.main --config otra-corrida.yaml --run-all
   ```

   Sin rutas separadas, una nueva corrida reutiliza la misma base procesada
   y los mismos archivos de salida. Abrir el `map.html` de la ruta
   `paths.results` elegida **solo después** de que el comando termine bien.

### Alcance regional actual

Esta versión solo analiza Santa Fe. La fuente de líneas eléctricas activa
corresponde a esa provincia. La estructura `region` y la lógica de recorte
espacial siguen separadas para facilitar una futura ampliación, pero cambiar
la provincia en el YAML **no está habilitado**. No hay que modificar `NAM`
ni `IN1`: son los nombres de los campos del archivo del IGN. Las localidades
BAHRA se seleccionan automáticamente dentro del límite de Santa Fe.

La tabla histórica `optimization_results` no se modifica. Las nuevas
corridas guardan sus métricas en `optimization_results_flexible`, donde los
criterios desactivados pueden quedar vacíos. La primera corrida con esta
versión crea esa tabla automáticamente sin borrar resultados anteriores.

---

## Fuentes de datos y trazabilidad

| Capa | Fuente | Tipo de geometría (confirmado por inspección) | Notas |
|---|---|---|---|
| Límite provincial | IGN — Unidades Territoriales (`ign_provincia.zip`) | Polygon/MultiPolygon, EPSG:4326 | https://datos.gob.ar/dataset/unidades-territoriales |
| Zonas urbanas | BAHRA (datos.gob.ar DataStore, resource `c1fc1f5b-...`) | **Point** (no polígono) | Se aproxima el área urbana con un buffer configurable — ver abajo |
| Líneas eléctricas | Redes de distribución eléctrica del Consejo Federal (datos.gob.ar, resource `3d5eda86-...`) | MultiLineString + atributo `tension` | Sin subestaciones — solo `tension` (voltaje) |
| Centros transformadores | Secretaría de Energía — "Transporte Eléctrico AT Estaciones Transformadoras" (CSV directo, datos.gob.ar) | Point (normalizado desde MultiPoint) | Fuente independiente, requerida solo si su peso es positivo |
| Radiación solar | Copernicus ARCO Zarr `reanalysis-era5-land-timeseries` | Punto (nearest-neighbour) | Ver sección dedicada |

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

El proyecto usa únicamente el almacén ARCO Zarr de ERA5-Land. Para cada
centroide de la grilla, `src/climate/arco.py` selecciona el punto ERA5-Land
más cercano en las coordenadas del propio almacén, lee los bloques espaciales
necesarios y resume los valores horarios de los cuatro meses representativos.
La radiación se expresa en kWh/m² tras convertir los J/m² originales con
el factor 3,6×10⁶. Los resúmenes por bloque se conservan en
`data/cache/arco_blocks/`; no se guardan ni se solicitan series por punto
a la API CDS. La caché permite reanudar una corrida sin releer los bloques
ya procesados. Las mediciones locales iniciales de ARCO fueron de 7,4 s para
cuatro meses en un punto, 9,8 s para un bloque completo y 36,6 s para cinco
bloques; son muestras, no una garantía para una provincia entera.

---

## Superficie del parque (2 ha) — qué se garantiza y qué no

`park.area_hectares` (2 ha = 20.000 m² = 0.02 km²) se **almacena** como
parámetro y aparece en `optimization_run.json`, pero este MVP **no verifica**
que existan 20.000 m² contiguos realmente disponibles dentro de una celda
(no hay todavía una capa de cobertura/uso de suelo). La celda de tamaño
configurable es una unidad espacial de análisis — no una afirmación de que
toda esa área esté disponible para el parque.

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

Los pesos de la función de fitness (`fitness.weight_*`) son valores
iniciales de MVP, no pesos científicamente calibrados.

---

## Extensiones futuras (arquitectura ya preparada)

- Estadísticos de variabilidad interanual (mediana, desvío, percentiles) — las
  tablas `solar_radiation` ya son (celda, año, mes) por fila.
- Interpolación espacial en vez de nearest-neighbour.
- Capas adicionales de exclusión/ponderación: uso de suelo (WorldCover),
  elevación/pendiente (SRTM), áreas protegidas, cuerpos de agua.
- Capacidad de subestación, tensión de línea, costo de conexión.
- Habilitar otras provincias en una versión futura, con fuentes eléctricas
  verificadas para cada región.

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
  cache/arco_blocks/       # resúmenes climáticos por bloque espacial ARCO
  processed/parque_solar.sqlite
```
