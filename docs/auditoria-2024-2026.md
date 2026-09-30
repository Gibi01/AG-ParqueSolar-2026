# Auditoría de la corrida 2024–2026

Corrida: `run-20260927T203525-c33c9918`. Dataset: `718b7cb4ad0ea8879a04613054d60f9708ea12eddb16c978879cf9c5779bc9c4`.

## Dictamen

Los resultados son internamente coherentes con el dataset y las fórmulas implementadas, pero **no demuestran buena calidad de optimización ni viabilidad de conexión**. Se encontraron alternativas sencillas con mejor fitness. No corresponde presentar el ranking como los mejores emplazamientos de Santa Fe.

## Comprobaciones reproducidas

Se abrió SQLite en modo de solo lectura y se reconstruyeron los diez polígonos desde sus celdas, sin modificar el ranking ni reejecutar el AG.

- Las celdas existen y están marcadas válidas; los polígonos son válidos y conexos, coinciden con el WKT exportado, quedan dentro del límite provincial y no invaden los buffers urbanos configurados (tolerancia de área 0,01 m²).
- Superficie de cada parque: 2,5 km² / 250 ha, formada por diez celdas.
- Potencia: 2,5 × 31,3 = 78,25 MWac, menor que el límite experimental de 80 MW; utilización 97,8125%.
- Irradiación ponderada: 1.873,739286 kWh/m²/año; referencia energética ideal: 146.620,099148 MWh/año. No es producción neta estimada.
- Se recalcularon centroides geométricos, distancias mínimas a líneas y estaciones, normalizaciones y fitness. Error máximo de fitness: aproximadamente 2,4e-15.
- Los diez parques usan un píxel climático cada uno. Sus once registros mensuales constan como completos en la base. En el dataset completo hay 1.369 píxeles y once meses por píxel, todos marcados completos.
- El período comprende enero/abril/julio/octubre de 2024 y 2025, y enero/abril/julio de 2026. No son tres años completos ni una integración de todos los meses.

Estas comprobaciones validan consistencia contra la base persistida, no certifican la exactitud física de los datos de origen. No se repitió la descarga ni se contrastaron las series horarias contra otra fuente independiente.

## Hallazgos relevantes

### 1. La búsqueda no encontró las mejores soluciones ni dentro de su propio modelo

Una referencia independiente enumera 451.759 rectángulos de 2 × 5 celdas completas válidas (una orientación), todos de 78,25 MW, y aplica exactamente los mismos pesos y límites de normalización. **1.282 superan el fitness del ganador del AG.**

| Métrica | Ganador AG | Mejor rectángulo de referencia |
|---|---:|---:|
| Fitness | 0,7559737915 | 0,8238991047 |
| Irradiación kWh/m²/año | 1.873,7393 | 1.895,9582 |
| Distancia a línea km | 0,004429 | 0,037325 |
| Distancia a ET km | 149,5625 | 170,3903 |
| Potencia MWac | 78,25 | 78,25 |

El contraejemplo utiliza celdas `258701,258702,258703,258704,258705,259170,259171,259172,259173,259174`. Su unión se verificó como un rectángulo válido de 2.500.000 m². No demuestra un óptimo global ni viabilidad real: incluso queda más lejos de la ET; demuestra que el AG dejó soluciones mejores según su objetivo sin encontrar.

La población termina con **2 parques distintos entre 50 individuos**, frente a 50 al inicio. Esto es compatible con pérdida de diversidad y convergencia prematura. La causalidad exacta requiere experimentos con varias semillas; no se modificó el algoritmo durante esta auditoría.

También hay genomas con hasta 682 genes para parques que aceptan solo nueve adiciones de celda. Es una señal de crecimiento de genes sin efecto en la solución; su impacto causal en la convergencia aún no fue medido.

### 2. El top 5 no equivale a cinco emplazamientos independientes

Comparten ocho de sus diez celdas y su unión contiene solo catorce. Son variantes del mismo entorno. El mapa nuevo separa las capas para compararlas; no altera el ranking para inventar diversidad geográfica.

### 3. La proximidad eléctrica no acredita una conexión apta

La línea más cercana a cada parque del top 10 es de **13.200 V**. La capa evaluada incluye 121.418 segmentos de 13,2 kV, 56.747 de 7,62 kV, 27.716 de 33 kV y 17 de 132 kV. La función objetivo premia cercanía sin discriminar tensión o capacidad disponible. Los conteos son segmentos del dataset, no líneas físicas distintas.

El ganador está a 149,56 km de Santo Tomé, la estación más cercana **entre las cuatro incluidas**. No significa que no existan otras estaciones más próximas. El límite de 80 MW es un supuesto experimental, no capacidad verificada de esa estación o línea.

### 4. Alcance territorial y energético limitado

Los buffers de localidades no cubren todas las restricciones posibles: no se comprobó propiedad, disponibilidad del suelo, inundabilidad, áreas protegidas, pendientes, accesos ni servidumbres. La grilla de 500 m no implica clima observado a 500 m. El fitness solar usa una normalización relativa al dataset, no un umbral de suficiencia técnica/económica.

## Cambio del mapa

Las futuras exportaciones muestran cinco capas visibles independientes con colores distintos y encuadre del conjunto. Para esta corrida se creó `map_top5.html`; `map.html`, CSV, GeoJSON y SQLite originales se conservaron. La superposición está advertida en el mapa.

## Próximo paso recomendado

Antes de interpretar el ranking como selección de sitios: corregir/validar la búsqueda contra referencias sencillas y varias semillas; definir si se requieren cinco alternativas geográficamente distintas; decidir qué tensiones y estaciones son admisibles; obtener capacidad real y restricciones territoriales. Ampliar el período climático por sí solo no resuelve estos problemas.

## Reproducibilidad

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m tasks.check_run_2024
.\.venv\Scripts\python.exe -m tasks.baseline_2024
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El primer script regenera únicamente `map_top5.html` y verifica el top 10; el segundo imprime la comparación rectangular sin guardar cambios. Ambos están ligados deliberadamente a esta corrida. La revisión externa mediante Claude fue ofrecida y descartada por el usuario; no se enviaron datos a ese servicio.
