# Sustitución y validación del crossover

El usuario autoriza cambiar el crossover, manteniendo el AG y sus criterios espaciales.
Este plan no reemplaza el plan MVA ni el experimento histórico.

## Diseño inicial

Cruce de punto común con competencia por fitness:
- Decodificar ambos padres y retirar genes saltados/no procesados sin cambiar sus parques.
- Probar hasta tres cortes comunes distintos. Cada hijo conserva su semilla y combina
  el prefijo propio con el sufijo del otro padre, con cortes en la misma posición.
- Competir cada propuesta contra su padre; conservarla si mejora su fitness, o si empata
  y aporta un parque distinto. La garantía local es antes de mutación y reemplazo de duplicados.
- Acotar los intentos a tres cortes y registrar solicitudes y decodificaciones;
  demostrar cambios y mejoras con pruebas de parques conocidos. Actualizar versión
  de búsqueda para distinguir nuevas corridas de las históricas.

## Validación y criterios

- Pruebas: hijos factibles, reproducibilidad, padres inmutables, ningún hijo peor que
  su padre, neutralidad de compactación y caso conocido con mejora real por recombinación.
- Mantener el operador anterior para comparación experimental explícita.
- Evaluar primero las 10 semillas anteriores (exploración), luego semillas nuevas
  301–310 para validación independiente, con/sin cruce y operador anterior.
- Registrar generaciones, solicitudes, decodificaciones y tiempo. Una mejora con más
  evaluaciones no se presentará como una mejora demostrada de eficiencia.
- Si los resultados no respaldan el nuevo operador, revisar el diseño y mostrar todas
  las variantes probadas; no seleccionar semillas favorables ni afirmar mejora universal.

## Tareas

- [x] Prueba roja, implementación mínima del operador y verificación focalizada.
- [x] Experimento exploratorio e independiente; comparar calidad y presupuestos.
- [x] Integración del operador, conteos de evaluaciones, metadatos, documentación y regresión.

## Resultado

La calidad media a 200 generaciones mejora en ambas fases. En validación:
anterior 0,716648; sin cruce 0,717709; nuevo 0,723141. El nuevo gana 6/10 frente
al anterior y 8/10 frente a sin cruce. Los IC de validación incluyen cero.
La ventaja no está demostrada con presupuestos iguales; el nuevo evalúa más alternativas.
Se integra por la calidad observada y la aceptación local no degradante,
sin afirmar superioridad universal ni mayor eficiencia.

Informe: `results/experiments/crossover-mejora/informe.md`.
Se conservó el código de cruce anterior para reproducción experimental explícita.
