# ADR-001: crecimiento contiguo con clima compartido

## Estado y fecha

Aceptado por autorización del usuario, 2026-09-27.

## Contexto

El modelo anterior elegía una ubicación; no evolucionaba superficie ni forma.
La grilla de 500 m aumenta considerablemente el número de celdas sin mejorar
la resolución de ERA5-Land. Los resultados históricos deben conservarse.

## Decisión

- Semilla y secuencia variable de enteros. Cada entero selecciona una posición
  de la frontera ordenada; el grafo de bordes compartidos garantiza conexión.
- Una expansión que supera la capacidad se omite y se procesa el siguiente gen.
  No se repara el cromosoma ni se elige una alternativa para ese gen.
- Componentes provinciales parciales conservan su geometría y área real.
- Las series mensuales pertenecen al píxel climático nativo. Las celdas sólo
  guardan su referencia; no hay interpolación. Se exige cobertura horaria completa.
- Distancias desde el centroide: una expansión puede empeorar proximidad.
- Capacidad experimental independiente de las cuatro ET geográficas.
- Energía ideal como salida, no como un segundo término solar del fitness.
- Snapshots append-only en otra base SQLite y carpetas por corrida. Los módulos
  históricos se conservan, pero no participan en el CLI espacial.

## Alternativas descartadas

IDs arbitrarios con reparación no garantizan conectividad por construcción.
Detenerse en el primer exceso impediría aceptar después una celda parcial menor.
Filtrar la frontera por capacidad cambiaría el significado solicitado de cada gen.
Distancia mínima al polígono nunca empeora al expandirlo. Replicar clima por celda
aumentaría almacenamiento sin aportar información. Modificar la base histórica
haría ambiguos sus IDs. No se añadieron dependencias ni una interfaz gráfica.

## Consecuencias

Genes omitidos y algunas mutaciones pueden ser neutrales. No se garantiza que
el óptimo use toda la capacidad ni que tenga tamaño pequeño. Eliminar el último
gen no siempre reduce área. La energía no es producción AC calibrada.
Los snapshots requieren más espacio cuando cambian los datos, pero preservan
el grafo, la grilla y el clima de cada experimento. Reutilizar un dataset permite
comparar capacidades sin volver a descargar radiación.
