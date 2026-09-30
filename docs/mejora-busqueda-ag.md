# Búsqueda territorial, sin reinicios ni rectángulos

Implementación autorizada el 28-09-2026. No modifica fitness, infraestructura,
capacidad experimental, clima ni el plan anterior de MVA.

- [x] Inicialización territorial aleatoria y reproducible.
- [x] Élites distintas y reemplazo acotado de descendientes duplicados.
- [x] Detención del crecimiento imposible; mantiene celdas parciales admisibles.
- [x] Mutaciones efectivas con intentos limitados; sin compactación indiscriminada.
- [x] Instrumentación y comparación con la búsqueda anterior.
- [x] Top 5 general y territorial, CSV y GeoJSON independientes.
- [x] Gráficas SVG en HTML local, sin dependencias nuevas.

## Verificación comparativa

`python -m tasks.benchmark_search` usa el dataset exacto y los pesos de la corrida
auditada del 27-09-2026: 0,40 solar / 0,10 línea / 0,25 ET / 0,25 potencia.
No usa los pesos actuales de config.yaml, que cambiaron. No descarga datos.
Compara los operadores anteriores con los nuevos usando el mismo evaluador
(incluida su detención temprana, que no cambia el fenotipo). No es una comparación
del tiempo total del pipeline ni de las versiones históricas completas.

| Semilla | Mejor anterior | Mejor nuevo | Consultas anterior / nuevo | Diversidad final anterior / nueva |
|---|---:|---:|---:|---:|
| 42 | 0,792997 | 0,817838 | 25.700 / 25.655 | 15 / 50 |
| 7 | 0,794449 | 0,819613 | 25.650 / 25.603 | 6 / 50 |
| 2026 | 0,819784 | 0,821928 | 25.850 / 25.815 | 5 / 50 |

Las consultas incluyen aciertos de caché y reintentos; se da al algoritmo anterior
un número al menos igual ajustando generaciones. Esto no iguala las decodificaciones
ni el tiempo exacto. Tiempos orientativos de búsqueda, excluyendo carga/evaluador:
5,5–6,3 segundos nuevo y 7,7–15,2 anterior en esta máquina.

Las tres pruebas son favorables, pero no acreditan óptimo global. El rectángulo
de referencia de la auditoría (0,823899) todavía supera los mejores resultados
de estas tres semillas. No se incorporó a la búsqueda por decisión del usuario.

## Reglas de salida

`ranking.csv` y `parks.geojson`: top 5 general. `ranking_territorial.csv` y
`parks_territorial.geojson`: hasta cinco alternativas sin superposición y con
separación entre bordes configurable. Por defecto 0 km adicionales, no una
garantía de sitios lejanos. `map.html` muestra el ranking territorial.
`candidates.csv` conserva el archivo acotado del que se seleccionaron.
`evolution.html` permite inspeccionar cuatro gráficas sin conexión.

Las variantes de un territorio pueden ocupar su reserva completa; un archivo
acotado puede descartar candidatos útiles para otras separaciones. Se informa
si la selección no alcanza cinco, sin inventar alternativas.

## Fuera de alcance

No se validó capacidad real de conexión. No se cambiaron pesos ni tensiones.
No hay reinicio parcial, umbral de estancamiento ni rectángulos de inicialización.
Los genes rechazados pueden seguir acumulándose: se evita recorrer una cola
incapaz de crecer y se miden genes no procesados, sin cambiar agresivamente el cruce.
