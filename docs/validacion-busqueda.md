# Validación de la búsqueda vigente

Santa Fe, INDEC 2022, margen 0 km, huecos excluidos, grilla 500 m, capacidad
experimental 80 MW, densidad 31,3 MWac/km². Pesos solar 0,35, líneas 0,10,
estaciones 0,35, potencia 0,10 y compactación 0,10. Crossover competitivo.
Dataset: `6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e`.

## Corridas disponibles

`results/spatial/run-20261007T021047-df88ea4d`: semilla 20261007, 50 individuos
y 200 generaciones. Mejor fitness de 0,608389 a 0,728288. Ganador de nueve
celdas, 225 ha, 70,425 MW estimados, perímetro 6.000 m y compactación 0,785398.
Línea más cercana a 104,45 m y estación considerada más cercana (Santo Tomé)
a 169,87 km. Su `evidence.json` registra ejemplos reales de operadores y crecimiento.
Los líderes de distintas generaciones no representan una genealogía única.

`results/spatial/run-20261007T003424-8b60c1ab`: mismo modelo, semilla 42,
fitness ganador 0,733180. Ambas carpetas incluyen configuración e historial.

## Comparación independiente

`results/experiments/search-quality-compactness-20261006` contiene diez semillas
por método, 30 corridas. Igual presupuesto de decodificaciones por par, entre
13.182 y 15.084, promedio 14.016.

| Método | Media del mejor fitness | Mejor observado |
|---|---:|---:|
| AG | 0,722499 | 0,734673 |
| Azar | 0,691615 | 0,702616 |
| Azar y búsqueda local | 0,711258 | 0,727512 |

AG supera azar en 10/10 semillas y azar con mejora local en 8/10. El híbrido
destina 40% al azar y 60% a agregar, quitar o intercambiar una celda conservando
conectividad y capacidad.

La enumeración evalúa 13.691.836 rectángulos válidos de hasta diez celdas completas
en 27 dimensiones. Mejor: 3 × 3, fitness 0,728288. Resuelve esa familia, excluyendo
formas irregulares y fragmentos. Dos de diez corridas AG superan ese mejor valor.
La corrida de ejemplo lo alcanza dentro de tolerancia numérica.

La auditoría de semilla 42 recupera parques ya evaluados y eleva el fitness medio
del top 5 territorial de 0,699143 a 0,704591. Incluye pruebas internas de operadores
y no añade búsqueda. Retener más alternativas y combinar semillas son pendientes.

La evidencia respalda competitividad bajo el modelo y presupuesto utilizados.
No certifica óptimo global, viabilidad ni beneficio económico. Fuentes:
`manifest.json`, `summary.csv`, `analysis.json`, `audit_archive/analysis.json`.
Código reproducible: `tasks/compare_search_quality.py`.
