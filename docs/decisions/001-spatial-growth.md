# Representación mediante crecimiento espacial contiguo

## Decisión y justificación

El dominio es Santa Fe. Cada individuo contiene una celda inicial y una secuencia
de instrucciones sobre la frontera ordenada de celdas que comparten borde.
Permite explorar ubicación, superficie y forma garantizando conexión durante
la construcción, sin reparación de polígonos desconectados.

Los fragmentos conservan áreas reales. Omitir una incorporación que excede
capacidad permite aceptar después una celda parcial menor. La irradiación se
comparte por píxel nativo, sin duplicar series por celda.

El evaluador usa centroide ponderado para distancias, área real para potencia y
perímetro total para compactación. Los snapshots vinculan resultados a insumos
y permiten repetir búsquedas sin consultas remotas.

## Consecuencias

Distintos cromosomas pueden representar el mismo parque. Un gen depende de su
frontera local y no equivale a una dirección fija. El mejor candidato puede usar
menos que la capacidad máxima. Pesos y restricciones son experimentales. El
archivo territorial acotado puede perder alternativas. La energía es ideal.

Implementación: `src/optimization/`, `src/database/spatial.py`.
