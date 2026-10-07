# Experimento de estabilidad territorial y aporte del crossover

Solicitud: ejecutar varias semillas con y sin crossover, conservando el AG vigente.
Este plan es independiente del plan MVA pendiente en `tasks/plan.md`.

## Diseño fijado antes de observar resultados

- Dataset persistido de la corrida `run-20261006T231108-428e45c4`; comprobar identidad.
- Semillas: 7, 21, 42, 63, 84, 105, 126, 147, 168, 2026.
- Dos variantes por semilla: crossover 0.75 y 0; todo lo demás idéntico, 50 individuos,
  200 generaciones, mutación 0.20 y elitismo 2. Mismas poblaciones iniciales por pareja.
- Conservar código actual, registrar hashes de módulos (incluidas modificaciones locales).
- Presupuesto primario: generaciones y población iguales. Registrar solicitudes reales,
  decodificaciones y tiempo: el presupuesto de evaluaciones puede diferir por operadores
  y reemplazo de duplicados. Analizar también curvas hasta un presupuesto común observado.
- Geografía: frecuencia del ganador por sectores proyectados de 50 km (mismo origen del AG),
  y sensibilidad a 10 y 25 km; distancia al ganador de referencia y repetición de celdas.
  Separar ganador por corrida de presencia en el TOP 5 territorial; contar presencia una
  sola vez por corrida/sector. Reportar ET más cercana como referencia, no conexión real.
- Estadística exploratoria: diferencias pareadas de fitness, victorias/empates,
  bootstrap de la media y prueba de cambio de signos; no afirmar óptimo ni ventaja
  general del AG sobre otros métodos. Sin crossover sigue habiendo selección y mutación.

## Entregables y límites

Resultados individuales, CSV consolidados, geometrías, curvas y mapas estáticos, informe
en español y manifiesto reproducible, en un directorio nuevo dentro de results/experiments.
No actualizar config.yaml ni la corrida principal. Diez parejas son una exploración inicial.
Validar potencia, contigüidad, poblaciones iniciales y completitud de las 20 corridas.
