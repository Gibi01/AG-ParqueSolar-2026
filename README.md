# Parques solares en Santa Fe mediante un algoritmo genético

El proyecto explora **ubicación, forma y superficie** de parques solares dentro
de **Santa Fe, Argentina**. Construye parques contiguos con celdas de 500 × 500 m
y los compara mediante cinco criterios. Es una preselección territorial que no
acredita conexión eléctrica, disponibilidad del terreno, rentabilidad ni óptimo global.

## Documentación del modelo vigente

- [Modelo y decisiones](docs/modelo.md): territorio, ciudades, fuentes, cromosoma,
  evaluación, operadores y limitaciones.
- [Ejecución y resultados](docs/ejecucion.md): entorno, comandos, parámetros y salidas.
- [Validación de la búsqueda](docs/validacion-busqueda.md): experimentos del modelo
  actual y conclusiones respaldadas.
- [Representación espacial](docs/decisions/001-spatial-growth.md).

Para NotebookLM, compartir estos documentos, `config.yaml`, el código y las corridas
identificadas en la validación. Los informes de `Informes/` usan la última corrida
completa compatible. El ámbito es exclusivamente Santa Fe, nombre y código 82
validados en configuración y selección del límite oficial IGN.

Para compartir un paquete de fuentes actuales, ejecutar
`.\.venv\Scripts\python.exe tools/export_notebooklm.py` y extraer
`NotebookLM_Proyecto_Actual.zip`. Incluye documentación, código, informes y
evidencia; omite credenciales, historial Git y archivos temporales.

## Cómo se determinan las ciudades

**Polígonos de localidades censales INDEC, Censo 2022**, capa WFS
`geonode:localidades_censales`. La máscara mantiene contornos, concavidades y
componentes separados. Con `fill_holes: true` también excluye huecos internos
encerrados. Toda celda que intersecta la máscara queda fuera de la búsqueda.

```yaml
urban_exclusion:
  buffer_km: 0.0
  fill_holes: true
```

El valor actual significa **sin margen adicional**. `buffer_km` permite un margen
opcional desde el perímetro de los polígonos y requiere reprocesamiento si se cambia.
La máscara final se recorta a Santa Fe. Se conservan completos los aglomerados
seleccionados durante la preparación para mantener su topología. Los insumos
nacionales no amplían el dominio de búsqueda. La fuente censal no es catastral.

## Evaluación y parámetros

| Criterio | Peso actual |
|---|---:|
| Irradiación media ponderada por área | 0,35 |
| Proximidad a líneas | 0,10 |
| Proximidad a estaciones | 0,35 |
| Potencia estimada | 0,10 |
| Compactación | 0,10 |

Los pesos suman 1 y son experimentales. Contigüidad, exclusión urbana y capacidad
son restricciones. Irradiación y distancias usan escalas min-max fijas del dataset
(invertidas para distancias). Potencia usa P/Pmáx. Compactación usa `4πA/P²` con
perímetro total. El fitness no representa producción ni ahorro económico.

Grilla configurable de 0,5 km. Densidad 31,3 MWac/km² de área total, incluidos
caminos y separaciones. Referencia: 7,9 acres/MWac, [NREL, tabla ES-1](https://docs.nrel.gov/docs/fy13osti/56290.pdf).
Celda completa: 25 ha, 7,825 MWac. Fragmentos usan área real. Límite experimental
80 MW, sin acreditar capacidad libre de ninguna estación.

AG: 50 individuos, 200 generaciones, torneo 3, elitismo 2, cruce 0,75, mutación
0,20, semilla predeterminada 42. Inicialización por sectores de 50 km, hasta 8
reintentos de duplicados, 4 de mutación y 10 candidatos archivados por sector.
El crossover competitivo combina instrucciones efectivas y elige alternativas
que no empeoran al padre dentro del operador. El top 5 territorial aplica una
selección voraz sin superposición, con separación adicional actual de 0 km.

## Fuentes y flujo

IGN aporta el límite, INDEC las envolventes urbanas, Secretaría de Energía las
líneas y cuatro estaciones (Río Coronda, Romang, Rosario Oeste, Santo Tomé), y
Copernicus ERA5-Land el SSRD horario vía Time-Series / ARCO Zarr.

Se validan y cachean fuentes, se preparan grilla y atributos y se guarda un dataset
local. El AG no consulta APIs. El clima usa meses completos de enero, abril, julio
y octubre desde 2024, con una estimación estacional anual. Las celdas referencian
píxeles nativos sin interpolación.

## Ejecución en PowerShell

Python 3.11 o superior. Desde la raíz:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main --setup
.\.venv\Scripts\python.exe -m src.main --download
.\.venv\Scripts\python.exe -m src.main --process
.\.venv\Scripts\python.exe -m src.main --optimize
```

Guardar `CDS_API_KEY` en `.env`. No se exporta ni se versiona. `--run-all`
encadena las etapas. `--force` renueva descargas vectoriales. `--help` detalla
opciones. La preparación inicial puede ser costosa.

Cambios de capacidad, densidad, pesos sin activar/desactivar fuentes o parámetros
del AG permiten repetir `--optimize`. Cambios de grilla, exclusión o período
requieren `--process`. Fuentes nuevas requieren descarga y preparación.
`config.test.yaml` es un escenario real de Santa Fe con clima 2024 y rutas propias,
no una prueba unitaria. Las corridas quedan en carpetas separadas `results/spatial/`.

## Implementación y verificación

Python y NumPy/pandas implementan el AG y registros. GeoPandas/Shapely/PyProj
procesan geometrías. xarray/Zarr/Dask/fsspec leen clima. SQLite/SQLAlchemy
persisten datos y Folium presenta mapas.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Las pruebas locales cubren fuentes INDEC, ámbito Santa Fe, restricciones,
compactación, operadores, reproducibilidad, persistencia y salidas sin descargas.

## Alcance y tareas pendientes

Faltan capacidad libre y estudios de red, inundaciones, pendiente, áreas protegidas,
catastro, accesos y costos. La energía calculada es ideal y no incluye pérdidas
ni modelado DC/AC. Distancia geográfica no equivale a trazado ni prueba de conexión.
Los resultados respaldan competitividad en los ensayos, sin certificar optimalidad.
Mejorar retención y combinar varias semillas son tareas pendientes.
