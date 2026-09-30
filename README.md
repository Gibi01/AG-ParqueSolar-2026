# AG-ParqueSolar-2026 — parques contiguos de superficie variable

Algoritmo genético para explorar ubicación, forma y superficie de parques solares
en Santa Fe. Cada individuo contiene una semilla y decisiones de crecimiento
sobre una grilla de **500 × 500 m**, independiente de la resolución climática.
No determina viabilidad eléctrica, disponibilidad de terreno ni óptimo económico.

## Índice

- [Ejecución en Windows](#ejecucion-windows)
- [Guía de uso paso a paso](#guia-ejecucion)
  - [1. Preparar el entorno](#manual-entorno)
  - [2. Configurar credenciales y parámetros](#manual-configuracion)
  - [3. Ejecutar el proyecto por etapas](#manual-etapas)
  - [4. Consultar los resultados](#manual-resultados)
  - [5. Comparar capacidades y repetir experimentos](#manual-experimentos)
  - [6. Usar otra configuración](#manual-otra-configuracion)
  - [7. Resolver problemas frecuentes](#manual-problemas)
- [Configuración](#configuracion)
- [Representación y crecimiento](#representacion-crecimiento)
- [Clima: resolución nativa, no interpolada](#clima)
- [Fitness y energía](#fitness-energia)
- [Infraestructura y exclusiones](#infraestructura-exclusiones)
- [Persistencia y salidas](#persistencia-salidas)
- [Pruebas y arquitectura](#pruebas-arquitectura)

<a id="ejecucion-windows"></a>

## Ejecución en Windows

Python 3.11 o superior. Desde PowerShell, en la raíz del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main --setup
.\.venv\Scripts\python.exe -m src.main --download
.\.venv\Scripts\python.exe -m src.main --process
.\.venv\Scripts\python.exe -m src.main --optimize
```

Guardar el token Copernicus en `.env` como `CDS_API_KEY=...`; no se exporta a
resultados ni se versiona. ARCO requiere acceso al dataset y las condiciones
correspondientes aceptadas en Copernicus. `--download` obtiene las capas
vectoriales; `--process` obtiene/resume ARCO y prepara el dataset espacial.
`--run-all` ejecuta las cuatro etapas. `--force` fuerza la descarga vectorial.

`--optimize` consume exclusivamente el dataset local: no reconstruye la grilla
ni consulta APIs. La primera preparación provincial puede ser costosa.
No confundir el mapa sintético de validación con un resultado provincial.

<a id="guia-ejecucion"></a>

## Guía de uso paso a paso

Esta guía utiliza **PowerShell en Windows**. Ejecutar los comandos desde la
carpeta raíz del proyecto, donde están `config.yaml`, `requirements.txt` y `src`.
No hace falta activar el entorno virtual: los comandos usan su Python directamente.

<a id="manual-entorno"></a>

### 1. Preparar el entorno

Abrir una terminal en la carpeta del proyecto. Si se abre en otra ubicación,
cambiar de carpeta, sustituyendo la ruta del ejemplo por la propia:

```powershell
Set-Location "C:\ruta\AG-ParqueSolar-2026"
py -3 --version
```

Se necesita Python 3.11 o superior. Si todavía no existe `.venv`, crearlo:

```powershell
py -3 -m venv .venv
```

Instalar las dependencias la primera vez, o después de que cambie `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se necesita conexión a Internet para instalar dependencias y obtener los datos.
El AG, una vez preparado el dataset, puede ejecutarse sin acceso a las APIs.
El mapa usa recursos web y teselas de OpenStreetMap, por lo que su visualización
completa sí puede requerir Internet.

<a id="manual-configuracion"></a>

### 2. Configurar credenciales y parámetros

Crear o editar `.env` en la raíz, conservando cualquier contenido existente.
Agregar el token personal de Copernicus con este formato, sin compartirlo ni
incluirlo en Git:

```dotenv
CDS_API_KEY=tu_token_personal
```

El archivo debe llamarse `.env`, no `.env.txt`. El token debe tener acceso al
dataset ARCO utilizado por el proyecto. No se debe guardar en `config.yaml`.

Revisar el bloque `park` de `config.yaml`:

```yaml
park:
  pv_power_density_mw_per_km2: 31.3
  max_connection_capacity_mw: 80
```

La capacidad puede cambiarse, por ejemplo, a 40, 120 o 160 MW. Es una restricción
experimental, no capacidad eléctrica real. Mantener la grilla en `0.5` km y los
meses climáticos `[1, 4, 7, 10]`. Los cuatro pesos de fitness deben sumar 1.
Consultar [Configuración](#configuracion) para conocer el efecto de cada cambio.

<a id="manual-etapas"></a>

### 3. Ejecutar el proyecto por etapas

Para la primera corrida, ejecutar cada comando y esperar a que termine
correctamente antes de pasar al siguiente. Si aparece un error, resolverlo
antes de continuar.

**Validar la configuración y preparar carpetas:**

```powershell
.\.venv\Scripts\python.exe -m src.main --setup
```

La consola debe indicar Santa Fe, grilla de 0,5 km, capacidad experimental y
pesos que suman 1. Este paso informa si falta el token, pero **no comprueba que
Copernicus lo acepte**.

**Descargar o reutilizar las capas vectoriales:**

```powershell
.\.venv\Scripts\python.exe -m src.main --download
```

Obtiene el límite provincial, localidades y las fuentes de infraestructura
activas. Reutiliza la caché disponible; todavía no procesa la radiación.

**Preparar la grilla, el clima y la vecindad:**

```powershell
.\.venv\Scripts\python.exe -m src.main --process
```

Este paso consulta ARCO cuando corresponde, comprueba la cobertura mensual y
guarda un dataset espacial compatible con la configuración. Puede ser la etapa
más costosa, especialmente en la primera ejecución y con un período histórico
largo. Al finalizar informa cuántas celdas son válidas. Los detalles quedan en
`logs/run_*.log`.

**Ejecutar el algoritmo genético y generar las salidas:**

```powershell
.\.venv\Scripts\python.exe -m src.main --optimize
```

La consola muestra el ranking y las rutas de los archivos generados. No descarga
clima ni reconstruye la grilla.

Como alternativa a los cuatro comandos, una vez revisada la configuración:

```powershell
.\.venv\Scripts\python.exe -m src.main --run-all
```

No es necesario ejecutar `--run-all` después de completar las cuatro etapas:
es otra forma de ejecutar el mismo flujo. Para consultar las opciones disponibles:

```powershell
.\.venv\Scripts\python.exe -m src.main --help
```

<a id="manual-resultados"></a>

### 4. Consultar los resultados

Al terminar `--optimize`, abrir la carpeta indicada en la consola. Con la
configuración principal será una carpeta nueva dentro de `results/spatial/`.

| Archivo | Para qué sirve |
|---|---|
| `map.html` | Top 5 territorial en capas individuales, sin superposición y con separación configurable; no acredita conexión eléctrica. |
| `ranking.csv` | Top 5 general por fitness; puede contener variantes superpuestas. |
| `ranking_territorial.csv` | Hasta cinco alternativas compatibles; conserva `general_rank` dentro del archivo de candidatos. |
| `candidates.csv` | Archivo acotado de candidatos, retenidos por territorio para auditar ambos rankings. |
| `evolution.html` | Cuatro gráficas sin conexión: fitness, diversidad, mutaciones efectivas y genes. |
| `history.csv` | Revisar la evolución del fitness, diversidad y tamaño medio por generación. |
| `parks.geojson` | Abrir los polígonos en un programa GIS. |
| `optimization_run.json` | Consultar configuración, semilla efectiva, dataset y supuestos de esa corrida. |
| `climate_coverage.csv` | Revisar los años válidos por píxel y mes; se genera cuando el criterio solar está activo. |

El mapa se centra en el mejor parque. Abrir el archivo de la **corrida recién
finalizada**, no un mapa histórico ni el de `spatial-validation`, que usa datos
sintéticos. La energía mostrada es ideal de referencia; no es producción AC validada.

<a id="manual-experimentos"></a>

### 5. Comparar capacidades y repetir experimentos

Después de preparar el dataset, cambiar únicamente
`park.max_connection_capacity_mw` y volver a ejecutar:

```powershell
.\.venv\Scripts\python.exe -m src.main --optimize
```

Repetir para 40, 80, 120 y 160 MW, conservando el resto de la configuración.
Cada ejecución guarda sus resultados en otra carpeta; no sobrescribe la anterior.
Para comparar corridas, revisar también área, potencia y distancias: el fitness
incluye un cociente cuyo denominador cambia con la capacidad.

Mantener el mismo `random_seed` permite repetir el experimento bajo el mismo
dataset y entorno. Cambiarlo permite explorar la variabilidad de la búsqueda.
Para reproducir una corrida que usó `random_seed: null`, copiar al YAML la semilla
efectiva registrada en `optimization_run.json`.

| Cambio realizado | Qué ejecutar después |
|---|---|
| Capacidad, densidad, parámetros del AG o pesos sin activar/desactivar fuentes | `--optimize` |
| Grilla, exclusión urbana o período climático | `--process`, luego `--optimize` |
| Fuentes, o activación de una fuente antes desactivada | `--download`, luego `--process` y `--optimize` |
| Desactivación de una fuente | `--process`, luego `--optimize` |

Con `end_year: latest`, el conjunto de meses puede cambiar con el calendario.
Si se informa que no hay dataset compatible, volver a procesar. Para comparaciones
controladas conviene fijar el año final y conservar los metadatos de cada corrida.

<a id="manual-otra-configuracion"></a>

### 6. Usar otra configuración

Se puede copiar `config.yaml` con otro nombre, editar la copia e indicar su ruta
con `--config`. Usar **el mismo archivo en todas las etapas** de ese experimento.
Por ejemplo, la configuración incluida `config.test.yaml` usa solamente 2024:

```powershell
.\.venv\Scripts\python.exe -m src.main --config config.test.yaml --run-all
```

Este comando usa fuentes reales y cubre la provincia a 500 m: **no es una prueba
unitaria ni garantiza una ejecución inmediata**. Sus rutas de base y resultados
están separadas de la configuración principal. Las pruebas locales sin descargas
están explicadas en [Pruebas y arquitectura](#pruebas-arquitectura).

<a id="manual-problemas"></a>

### 7. Resolver problemas frecuentes

| Mensaje o síntoma | Acción sugerida |
|---|---|
| No se encuentra `py` o `.venv\Scripts\python.exe` | Comprobar la instalación de Python, la carpeta actual y la creación de `.venv`. |
| `No module named ...` | Instalar `requirements.txt` con el Python de `.venv`, no con otro intérprete. |
| Falta `CDS_API_KEY`, o ARCO rechaza el acceso | Revisar `.env`, el token y los permisos/condiciones del dataset. No publicar el token al pedir ayuda. |
| Faltan capas en caché | Ejecutar `--download` con el mismo `--config` y después `--process`. |
| No hay dataset compatible | Ejecutar `--process` con la configuración actual antes de `--optimize`. |
| Base histórica rechazada | Usar una ruta nueva en `paths.database`; no borrar ni modificar la base histórica. |
| No hay semillas compatibles con la capacidad | Revisar el límite experimental y el área de las celdas válidas; una celda completa requiere 7,825 MW con la densidad inicial. |
| No quedan celdas válidas por cobertura climática | Revisar el período y los registros de cobertura; no rellenar datos faltantes ni reducir el requisito de horas completas. |
| El mapa no muestra el fondo | Comprobar conexión a Internet y posibles bloqueos de los recursos web o las teselas. |

Para actualizar deliberadamente las capas vectoriales desde su fuente:

```powershell
.\.venv\Scripts\python.exe -m src.main --download --force
.\.venv\Scripts\python.exe -m src.main --process
.\.venv\Scripts\python.exe -m src.main --optimize
```

`--force` no fuerza la renovación de la caché climática ARCO. Si se interrumpe
`--process`, se puede volver a ejecutar para reutilizar los bloques climáticos
que ya se hayan guardado; la grilla y otros pasos pueden recalcularse.
Consultar el último archivo de `logs/` para localizar el error.

<a id="configuracion"></a>

## Configuración

Editar `config.yaml`, o utilizar `--config otra-configuracion.yaml`.
No existe una superficie fija del parque.

```yaml
grid:
  resolution_km: 0.5
park:
  pv_power_density_mw_per_km2: 31.3
  max_connection_capacity_mw: 80
fitness:
  weight_solar: 0.40
  weight_grid_distance: 0.10
  weight_transformer_distance: 0.25
  weight_installed_power: 0.25
genetic_algorithm:
  population_size: 50
  generations: 200
  crossover_probability: 0.75
  mutation_probability: 0.20
  elitism: 2
  tournament_size: 3
  random_seed: 42
```

La capacidad es una **restricción experimental**, no una capacidad real de las
estaciones. Potencia instalada = área real en km² × densidad en MWac/km².
Una celda completa representa 0,25 km², 25 ha y 7,825 MWac.

La densidad de referencia deriva de 7,9 acres/MWac de área total para grandes
instalaciones fotovoltaicas en [NREL, tabla ES-1](https://docs.nrel.gov/docs/fy13osti/56290.pdf).
Es una referencia empírica, no un relevamiento local ni un diseño de paneles.

Cambiar capacidad, densidad, pesos positivos o parámetros del AG permite repetir
`--optimize` sin descargar clima. Cambiar grilla, exclusiones, período, fuentes
o activar/desactivar una fuente requiere `--process`. Con `end_year: latest`,
la selección de meses resueltos avanza con el calendario y puede requerir una
nueva preparación. Para experimentos comparables, fijar `end_year`.
`config.test.yaml` conserva 500 m y utiliza solamente 2024; no es una grilla gruesa.

Los pesos deben sumar 1. Un peso cero conserva la opción de desactivar su
criterio; con radiación desactivada, irradiación y energía quedan ausentes, no
se inventan. Las exclusiones urbanas siguen activas.

<a id="representacion-crecimiento"></a>

## Representación y crecimiento

`Individual(seed_cell_id, growth_genes)` no contiene polígonos ni coordenadas.
El fenotipo contiene celdas aceptadas, área, potencia, irradiación, distancias,
ET asociada, fitness y energía ideal.

- Los recortes provinciales mantienen su área real. Fragmentos desconectados
  del mismo cuadrado son componentes independientes.
- Identidad y orden: `(row, column, component)`, dentro de un dataset versionado.
  Se conservan origen, CRS, geometría y grafo de vecindad.
- Vecindad: segmento de borde compartido de longitud positiva. Una esquina
  no conecta. El grafo se calcula antes del AG.
- Cada gen selecciona `gene % len(frontier)` sobre la frontera ordenada.
- Si la celda excede la capacidad, **se omite ese gen y se continúa**.
  No se busca otra candidata para el mismo gen ni se modifica la frontera.
- Termina cuando no hay frontera, se agotan los genes o ninguna celda de la frontera cabe. La semilla debe caber.
- No hay superficie mínima ni número mínimo arbitrario: solamente la semilla.
- Crossover: prefijo y sufijo con cortes independientes. Cada hijo conserva
  la semilla del progenitor que aporta su prefijo.
- Mutación: agregar una celda que cabe, truncar antes de la última incorporación
  aceptada, cambiar un gen aceptado o cambiar semilla. Las operaciones aplicables
  tienen igual probabilidad; hasta `mutation_attempts` intentos buscan cambiar
  el conjunto de celdas. Si no lo logran, se conserva el individuo original.
- Los genes omitidos se conservan: pueden adquirir significado tras otros cambios.
- El ranking no repite conjuntos de celdas, aunque distintos cromosomas los generen.

La inicialización recorre sectores ocupados de `territory_size_km` (50 km por
defecto) en orden aleatorio, sin repetir sector hasta completar el ciclo. La
semilla dentro de cada sector es aleatoria; el parque puede cruzar sus límites.
No se introducen rectángulos ni reinicios por estancamiento. La élite conserva
parques distintos. Para completar cada generación, un descendiente duplicado
se reemplaza por candidatos territoriales, hasta `duplicate_attempts` (8).
Agotados los intentos, se permite repetición y se registra `duplicate_fallbacks`;
así se garantiza terminación incluso en espacios pequeños.

El archivo retiene hasta `archive_per_territory` (10) candidatos por territorio
del centroide. El top 5 territorial se selecciona por fitness, sin superposición
y con distancia entre bordes de al menos `territorial_separation_km` (0 por
defecto: permite contacto). Es una selección voraz sobre candidatos retenidos,
no una optimización conjunta ni garantía de cinco sitios. Si faltan alternativas,
se informa en `optimization_run.json`. `general_rank` es el puesto en ese archivo,
no solo en las cinco filas de `ranking.csv`.

`history.csv` conserva tiempo, consultas al evaluador (incluidas caché/reintentos),
decodificaciones, parques distintos vistos en las poblaciones y métricas de genes.
Aceptados, rechazados y no procesados suman la longitud del genoma. La efectividad
de mutación se mide por evento; sin eventos el porcentaje queda vacío, no en cero.
Cambiar estos parámetros no requiere descargar clima ni ejecutar `--process` de
nuevo si el dataset sigue siendo compatible. Las semillas antiguas no reproducen
el algoritmo anterior: los metadatos nuevos incluyen `search_version: 3`.

La longitud inicial se escala con la capacidad y el área mediana de las celdas;
no es un máximo de tamaño del parque. Elitismo y torneo se aplican al fitness
del parque decodificado. La semilla aleatoria efectiva se guarda incluso si
`random_seed` es nulo.

<a id="clima"></a>

## Clima: resolución nativa, no interpolada

Fuente exclusiva: ERA5-Land ARCO Zarr, `surface_solar_radiation_downwards`
(`ssrd`). La variable ARCO está desacumulada y expresa J/m². Se suman sus
valores horarios y se divide por 3.600.000 para obtener kWh/m².
[Guía oficial ECMWF](https://confluence.ecmwf.int/spaces/CKB/pages/536218894/ERA5-Land+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1950+to+present+Product+User+Guide+PUG).

Cada celda apunta al píxel nativo más cercano. La serie mensual se almacena
una sola vez por píxel y versión del dataset, nunca una copia por celda.
No se interpola ni se atribuye resolución climática de 500 m.

Un mes/año necesita **100 % de horas esperadas, únicas y finitas**. Se excluyen
meses incompletos, sin rellenar ni reescalar. Se registran las horas observadas
y los años válidos por mes. Si algún mes representativo carece de años válidos,
el píxel no aporta una estimación anual y sus celdas se excluyen cuando el
criterio solar está activo.

Con las medias históricas de totales mensuales:

```text
H_anual = H_enero / 31 × 90,25
        + H_abril / 30 × 92
        + H_julio / 31 × 92
        + H_octubre / 31 × 91
```

La salida es **irradiación anual estimada**, en kWh/m²/año, no integración de
los doce meses de cada año. Los cuatro meses pueden tener cantidades de años
válidos distintas; la cobertura se exporta. Los bloques antiguos sin validación
del calendario horario no se reutilizan como si cumplieran el nuevo criterio.

<a id="fitness-energia"></a>

## Fitness y energía

```text
fitness = 0,40 × radiation_score
        + 0,10 × grid_distance_score
        + 0,25 × transformer_distance_score
        + 0,25 × installed_power_score
```

La irradiación es el promedio ponderado por área de todas las celdas.
Las distancias se miden desde el centroide del parque, en CRS métrico.
La ET más cercana se elige automáticamente; un empate exacto se resuelve por ID.

La normalización min–max utiliza referencias fijas de la grilla válida:
irradiación y distancias de centroides individuales. Los valores fuera del rango
se limitan a [0,1]; una variable constante tiene score 1. Las distancias se
invierten para favorecer proximidad. No se renormaliza por generación ni
por población. El score de potencia es potencia/capacidad experimental.

Agregar celdas puede aumentar potencia y empeorar otros componentes, pero no
se garantiza un óptimo pequeño. Dentro del mismo píxel climático, con distancias
parecidas, es esperable que predomine el crecimiento. Comparar también métricas
físicas entre capacidades: el denominador del score de potencia cambia.

```text
energía anual ideal de referencia [MWh/año]
  = potencia instalada [MW] × H_anual [kWh/m²/año] / (1 kW/m²)
```

Es una referencia idealizada: no modela pérdidas, inclinación, relación DC/AC
ni clipping del inversor. **No es producción AC validada y no entra al fitness.**

<a id="infraestructura-exclusiones"></a>

## Infraestructura y exclusiones

Se mantienen exclusivamente las cuatro ET existentes de la fuente nacional:
Santo Tomé (ST), Río Coronda (CN), Rosario Oeste (RO) y Romang (RM).
La versión espacial utiliza sus IDs, nombres y posiciones, no atributos de capacidad.

Se conservan las líneas del Consejo Federal, el límite provincial IGN y
la exclusión por buffers de 3 km alrededor de puntos BAHRA de tipo LOCALIDAD.
Se excluye todo componente que intersecta un buffer. Son aproximaciones
geográficas, no límites catastrales ni trazados de conexión.

No se incorpora inventario EPE, población, demanda, MVA, factor de potencia,
clasificaciones LOW/MEDIUM/HIGH, flujo de potencia, costos, pendiente ni Pareto.

<a id="persistencia-salidas"></a>

## Persistencia y salidas

La base nueva es `data/processed/parque_solar_spatial.sqlite`. Cada preparación
crea un snapshot identificado por contenido, sin reemplazar snapshots previos.
Una base histórica del formato anterior se rechaza: usar otra ruta, no migrarla
destructivamente. Los módulos de repositorio/modelos antiguos se conservan para
acceso al formato histórico; el CLI espacial utiliza `src/database/spatial.py`.

Cada ejecución crea una carpeta independiente:

```text
results/spatial/run-<fecha>-<id>/
  ranking.csv
  ranking_territorial.csv
  candidates.csv
  history.csv
  evolution.html
  parks.geojson
  parks_territorial.geojson
  optimization_run.json
  climate_coverage.csv       # cuando el criterio solar está activo
  map.html
```

El ranking incluye genotipo, IDs de celdas, traza de genes, geometría, área,
potencia, capacidad experimental, utilización, irradiación, energía ideal,
ET y distancias. Los metadatos contienen configuración sin credenciales, versión
del dataset, semilla aleatoria efectiva, límites de normalización y versiones
de librerías. Las corridas también quedan registradas en SQLite.

El mapa muestra polígonos, celdas de las soluciones y capas de infraestructura.
Se centra en el conjunto territorial seleccionado; no incrusta toda la grilla provincial.
Los archivos y planes anteriores sobre MVA permanecen intactos y fuera de alcance.

<a id="pruebas-arquitectura"></a>

## Pruebas y arquitectura

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src
```

Las pruebas locales no descargan datos: usan calendarios horarios y geometrías
sintéticas para comprobar unidades, cobertura, contigüidad, genes omitidos,
operadores, reproducibilidad, snapshots y exportaciones para cuatro capacidades.

Flujo: ingesta vectorial → grilla/clima/grafo → snapshot SQLite → AG local →
CSV/GeoJSON/HTML. No se añadieron dependencias.
Decisiones y alternativas: [ADR espacial](docs/decisions/001-spatial-growth.md).

Los resultados siguen siendo una exploración académica: no certifican terreno
disponible, permisos, conexión posible ni factibilidad económica o energética.
