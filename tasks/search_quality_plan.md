# Comparación de calidad de búsqueda con compactación

Diseño fijado antes de observar resultados. Referencia:
`results/spatial/run-20261007T003424-8b60c1ab/optimization_run.json`.
Se conserva dataset, configuración, normalizaciones y código de producción.

- Enumerar todos los rectángulos de celdas completas válidas de 500 m,
  con h y w positivos y h*w <= 10, incluyendo ambas orientaciones.
  Se excluyen componentes recortados de borde de esta familia de referencia.
  Evaluación vectorizada independiente; comprobar los finalistas contra
  ParkEvaluator y las geometrías exactas. No demuestra óptimo global.
- Diez semillas: 7,21,42,63,84,105,126,147,168,2026. AG vigente:
  población 50, 200 generaciones, cruce competitivo 0.75, mutación 0.20,
  torneo 3, élites 2. Registrar todas las solicitudes y fallos de caché.
- Búsqueda aleatoria pura y aleatoria + local reciben, para cada semilla,
  el mismo número de evaluaciones efectivas del objetivo (fallos de caché)
  que el AG. Registrar solicitudes, parques distintos y tiempos también.
  El AG puede evaluar distintos cromosomas del mismo parque: informar esta
  diferencia; igualar evaluaciones no implica igualdad de parques únicos.
- Muestreo aleatorio de semillas balanceado en los mismos sectores de 50 km;
  crecimiento directo sin selección, crossover ni mutación del AG. Elegir
  tamaño inicial uniforme de 1 a 11 celdas; agregar vecinas aleatorias que
  caben bajo el límite. No es una distribución uniforme de todos los parques.
- Método híbrido: 40% de evaluaciones para muestreo aleatorio y 60% para
  búsqueda local con reinicios desde candidatos retenidos, ordenados por
  fitness. Vecindario: agregar, quitar e intercambiar una celda, manteniendo
  conexión por lados y capacidad. Mejor mejora estricta; reiniciar al
  agotar el vecindario. Si se agotan las semillas de inicio, muestrear otra.
- Archivos de los métodos aleatorios: hasta 10 candidatos por sector, igual
  capacidad de retención territorial que el AG. Top 5 territorial con la
  misma regla de ausencia de superposición y separación adicional 0 km.
- Rectángulos: retener suficientes finalistas para obtener exactamente el
  top 5 territorial de esta familia: cada parque excluye como máximo
  10*sum(h*w) colocaciones; conservar 4*10*sum(h*w)+5 antes de filtrar.
- Exportar manifiesto/hashes, corridas, curvas por evaluaciones, rankings,
  geometrías y reporte en español. Comparar fitness absoluto, diferencias
  pareadas, percentiles de la referencia y métricas físicas. No interpretar
  mejora de fitness como mejora equivalente de energía o rentabilidad.

El óptimo global sigue sin certificarse. Superar al AG con cualquier parque
válido refuta su optimalidad para ese escenario; no superarlo no la prueba.

## Auditoría adicional de retención (exploratoria)

Al finalizar la enumeración se observó una diferencia marcada entre ranking
general y territorial. Se añade una reproducción de la semilla 42, sin
cambiar operadores, decisiones ni números aleatorios, para registrar todas
las propuestas ya evaluadas. Comparar el top 5 territorial publicado con
el que se obtiene reteniendo todas esas propuestas y con el archivo AG
ampliado con rectángulos. Esta auditoría es posterior al hallazgo y no
forma parte del presupuesto de las treinta corridas comparativas.
