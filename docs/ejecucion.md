# Ejecución del proyecto

Python 3.11 o superior. Desde la raíz, en PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main --setup
.\.venv\Scripts\python.exe -m src.main --download
.\.venv\Scripts\python.exe -m src.main --process
.\.venv\Scripts\python.exe -m src.main --optimize
```

Guardar `CDS_API_KEY=tu_token` en `.env`, con acceso al dataset Copernicus.
El token no se exporta ni se versiona. `--download` obtiene capas vectoriales;
`--process` prepara clima, grilla, máscara y vecindad; `--optimize` usa datos
locales. La preparación inicial puede ser costosa. `--run-all` encadena etapas.
`--download --force` renueva capas vectoriales, no la caché ARCO.

| Cambio | Acción |
|---|---|
| Capacidad, densidad, pesos sin activar/desactivar fuentes, parámetros del AG | `--optimize` |
| Grilla, margen urbano, huecos o período climático | `--process`, `--optimize` |
| Fuentes o activación de una fuente | `--download`, `--process`, `--optimize` |
| Desactivación de una fuente | `--process`, `--optimize` |

Nombre y código de región deben permanecer en Santa Fe y 82. Para un escenario
usar `--config ruta.yaml` en todas sus etapas. `config.test.yaml` también cubre
Santa Fe, con clima 2024 y rutas independientes. No es una prueba unitaria.
Con `end_year: latest` los meses avanzan con el calendario; conservar períodos,
configuración y dataset para reproducir resultados.

## Salidas por corrida

| Archivo | Contenido |
|---|---|
| `optimization_run.json` | Dataset, configuración, versiones, semilla, escalas y supuestos |
| `candidates.csv` | Archivo de candidatos retenidos |
| `ranking.csv`, `parks.geojson` | Top 5 general |
| `ranking_territorial.csv`, `parks_territorial.geojson` | Hasta cinco alternativas compatibles |
| `history.csv` | Fitness, dispersión, diversidad, mutaciones y evaluaciones |
| `evolution.html` | Seis gráficas visibles sin conexión |
| `map.html` | Mapa territorial; las teselas requieren conexión |
| `climate_coverage.csv` | Años válidos por píxel y mes cuando solar está activo |

Cada ejecución crea `results/spatial/run-*`. `general_rank` refiere al archivo
completo de candidatos. El historial incluye generación 0: 201 filas para 200
generaciones. Fitness no es eficiencia energética. Diversidad cuenta conjuntos
de celdas, no distancia espacial. Mutación efectiva significa cambio territorial,
no mejora. Solicitudes, decodificaciones y parques únicos son cantidades diferentes.

## Informes y pruebas

Los generadores usan la última corrida completa compatible de Santa Fe:

```powershell
.\.venv\Scripts\python.exe tools/reporting/build_figures.py
.\.venv\Scripts\python.exe tools/reporting/build_reports.py
.\.venv\Scripts\python.exe tools/reporting/build_pdfs.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Los informes quedan en `Informes/docx` e `Informes/pdf`. Las cifras proceden de
los archivos de corrida. Los generadores requieren las bibliotecas documentales.
Las pruebas utilizan fixtures locales y no descargan clima.

Faltan capas: `--download`. No hay dataset compatible: `--process`. Cobertura
incompleta: revisar clima y logs sin rellenar datos. No hay semillas compatibles:
revisar capacidad. Mapa sin fondo: verificar conexión. Consultar `--help` y logs.
