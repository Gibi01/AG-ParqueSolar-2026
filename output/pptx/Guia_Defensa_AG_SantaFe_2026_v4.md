# Guía de defensa de parques solares en Santa Fe

24 diapositivas. Duración sugerida: 26.1 minutos. Reservar 3.9 minutos para margen y preguntas. El tiempo requiere ensayo con cronómetro.

## Esquema

- 1–4: problema, funcionamiento y territorio.
- 5–9: variables, reglas y evaluación.
- 10–16: cromosoma, selección, crossover, mutación, ciclo y manejo de datos.
- 17–21: nueva corrida, resultados y comparación previa.
- 22–24: limitaciones, mejoras futuras y conclusiones.

Las diapositivas priorizan la explicación visual. Las notas contienen fórmulas, bibliotecas, parámetros, fuentes y justificaciones.

## 1. Parques solares en Santa Fe

TIEMPO SUGERIDO: 0.5 minutos

EXPLICACIÓN PARA EXPONER
Presentar el objetivo: explorar ubicaciones y formas de parques solares mediante un algoritmo genético. La pregunta central es dónde ubicar un parque y qué superficie seleccionar cuando hay varias condiciones que considerar al mismo tiempo. Esta defensa recorre el problema, la representación del territorio, la búsqueda y una ejecución nueva con resultados verificables.

DECISIONES Y JUSTIFICACIÓN
La presentación usa una sola corrida como hilo narrativo y reserva el detalle técnico para las notas. El mapa mantiene el límite oficial de Santa Fe del dataset IGN. El resultado constituye una preselección territorial que puede orientar estudios posteriores.

DETALLE PARA EL LECTOR Y LÍMITES
No afirmar que el candidato es un proyecto listo para construir. La ejecución usa el modelo actual con compactación, con semilla 20261007. La comparación con otras búsquedas corresponde a un experimento anterior, identificado expresamente en su diapositiva.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 2. La decisión territorial

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
Explicar que disponer de radiación solar no resuelve por sí solo la ubicación de un parque. La misma superficie puede recibir distinta irradiación, estar a diferente distancia de la infraestructura y atravesar zonas que el modelo excluye. Además de elegir un lugar, el sistema debe construir una superficie conectada y decidir cuánto terreno incorporar.

DECISIONES Y JUSTIFICACIÓN
Se formula una búsqueda multicriterio porque ninguna variable resume por sí sola el problema. El algoritmo permite explorar combinaciones de celdas que una selección manual podría pasar por alto. El alcance elegido es Santa Fe y una grilla configurable.

DETALLE PARA EL LECTOR Y LÍMITES
Los criterios elegidos son aproximaciones para una preselección. Las distancias no representan costos de tendido y los datos de irradiación no son una simulación completa de producción. Estas diferencias permiten explicar por qué un buen puntaje necesita luego una evaluación de ingeniería.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\README.md
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 3. Funcionamiento de un parque solar

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
Seguir el recorrido de la energía en la ilustración: los paneles convierten radiación en corriente continua, el inversor la transforma en corriente alterna y el transformador adecua la tensión para su transporte. La selección territorial se ubica antes del diseño detallado de esas instalaciones. Distinguir potencia, medida en MW, de energía acumulada durante un período, medida en MWh.

DECISIONES Y JUSTIFICACIÓN
Se estima la potencia a partir del área total del parque mediante una densidad de referencia. El terreno incluye separaciones entre filas, caminos y otros espacios. Por eso no se considera que toda la superficie esté cubierta por módulos solares.

DETALLE PARA EL LECTOR Y LÍMITES
La densidad adoptada es 31,3 MWac/km². Proviene de aproximadamente 7,9 acres/MWac de área total para grandes plantas fotovoltaicas en el informe NREL de Ong y colaboradores, 2013, NREL/TP-6A20-56290. Una celda completa de 0,25 km² equivale a 7,825 MW. El modelo no calcula qué porcentaje exacto corresponde a paneles. La fuente es una referencia empírica y requiere calibración local.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
https://www.nrel.gov/docs/fy13osti/56290.pdf
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 4. Santa Fe como conjunto de celdas

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
El territorio se divide en celdas de 500 por 500 metros. Cada una puede integrar un parque candidato si cumple las reglas del modelo. Los bordes de la provincia pueden producir fragmentos de celda con menor superficie. La grilla transforma un territorio continuo en unidades que el algoritmo puede combinar y evaluar.

DECISIONES Y JUSTIFICACIÓN
El tamaño de celda balancea detalle espacial y costo de búsqueda. Es configurable, pero modificarlo requiere volver a procesar el dataset porque cambian áreas, vecindades y candidatos. Las celdas válidas excluyen las envolventes urbanas INDEC según la política configurada.

DETALLE PARA EL LECTOR Y LÍMITES
El dataset contiene 535.751 celdas o componentes y 526.194 válidos. De los válidos, 521.134 son cuadrados completos y 5.060 son fragmentos. El tamaño de celda es una discretización del modelo, no una nueva medición climática. La geometría provincial procede del IGN y no fue inferida por una ilustración.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\pipeline\preprocess.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 5. Variables de ubicación y tamaño

TIEMPO SUGERIDO: 1.1 minutos

EXPLICACIÓN PARA EXPONER
Presentar primero los cuatro criterios visibles: irradiación solar, proximidad a líneas, proximidad a estaciones transformadoras y potencia estimada a partir de la superficie. Luego introducir la forma compacta como un quinto criterio. El objetivo no consiste simplemente en encontrar el lugar con más sol: se combinan preferencias que pueden entrar en conflicto.

DECISIONES Y JUSTIFICACIÓN
La irradiación representa el recurso disponible. Las distancias aportan una referencia espacial de infraestructura. La potencia permite valorar la superficie seleccionada. La compactación favorece formas con menos perímetro relativo a su área. Separar estas variables facilita entender por qué cambia el puntaje de un candidato.

DETALLE PARA EL LECTOR Y LÍMITES
Los pesos actuales son 0,35 solar, 0,10 líneas, 0,35 estaciones, 0,10 potencia y 0,10 compactación. Son decisiones experimentales que suman 1, todavía pendientes de una calibración y un análisis de sensibilidad. No representan porcentajes de costos ni de energía. La exclusión urbana y la contigüidad son restricciones, no términos compensables del puntaje.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\spatial.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 6. Radiación solar

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
El mapa muestra el indicador anual estimado de irradiación construido con ERA5-Land. Los valores provienen de datos horarios, no de colores elegidos para ilustrar la provincia. El procesamiento exige meses completos y utiliza enero, abril, julio y octubre como representantes estacionales. Para cada parque se calcula una media ponderada por el área de sus celdas.

DECISIONES Y JUSTIFICACIÓN
Se eligen cuatro meses para representar estaciones y reducir el volumen de datos. Se promedian los años disponibles de cada mes y se ponderan las medias diarias por los días de cada estación. La cobertura utilizada comprende once períodos completos desde 2024 hasta julio de 2026.

DETALLE PARA EL LECTOR Y LÍMITES
La variable original es SSRD en J/m², convertida a kWh/m² dividiendo por 3.600.000. El mapa utiliza los píxeles climáticos reales y conserva latitud, longitud y escala de color. El rango del dataset es aproximadamente 1.795,94 a 1.895,96 kWh/m²/año. Es una estimación estacional con historial corto, no una climatología de varias décadas ni una producción eléctrica con pérdidas.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\climate\climatology.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\climate\arco.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_nueva\solar_pixels_verificados.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 7. Infraestructura eléctrica

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
El mapa reúne las líneas de la fuente integrada y las cuatro estaciones transformadoras consideradas. El algoritmo mide la distancia desde el centroide del parque a la línea más próxima y a la estación más próxima. Esta cercanía mejora el puntaje, pero no determina si efectivamente se puede conectar un parque.

DECISIONES Y JUSTIFICACIÓN
Se usa una distancia geográfica como aproximación simple y reproducible. Las estaciones mantienen identidades estables: Río Coronda, Romang, Rosario Oeste y Santo Tomé. Limitar el conjunto facilita un primer escenario, aunque también condiciona el resultado de toda la provincia.

DETALLE PARA EL LECTOR Y LÍMITES
La capa de líneas incluye distribución y no equivale a una red de transporte apta para conectar cualquier planta. No se dispone en este modelo de capacidad libre en MVA, estudios de flujos ni rutas de conexión. La distancia se calcula en coordenadas métricas y no sigue caminos. No confundir tensión en kV con capacidad de transformación en MVA.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\pipeline\preprocess.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\spatial.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 8. Reglas para construir un parque

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
Un candidato crece incorporando celdas vecinas que comparten un borde. Las celdas urbanas excluidas no están disponibles para el crecimiento y el parque no puede superar el límite experimental de potencia. Dentro de esas reglas, la compactación agrega una preferencia por formas menos extendidas.

DECISIONES Y JUSTIFICACIÓN
La contigüidad se garantiza durante la construcción del candidato, evitando reparar después una geometría desconectada. El límite de 80 MW permite definir un escenario controlado. La compactación funciona como preferencia, de modo que una forma alargada puede seguir siendo válida si sus otros atributos lo justifican.

DETALLE PARA EL LECTOR Y LÍMITES
La exclusión urbana usa envolventes INDEC con buffer 0 y relleno de huecos internos. El límite de 80 MW no procede de capacidad libre de ninguna ET. La compactación usa 4πA/P² e incluye perímetros de huecos. No equivale a costos, pendiente, orientación de paneles o facilidad real de construcción. Un cuadrado alcanza π/4, no 1.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\spatial.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 9. Cómo comparamos dos candidatos

TIEMPO SUGERIDO: 1.2 minutos

EXPLICACIÓN PARA EXPONER
Explicar el fitness como un puntaje que permite ordenar candidatos válidos. Cada variable se lleva a una escala comparable y luego se combina con un peso. Un parque puede compensar una peor distancia con mayor recurso solar o mejor forma, según la importancia asignada a cada criterio.

DECISIONES Y JUSTIFICACIÓN
Se mantienen escalas fijas a lo largo de la búsqueda para que el significado del puntaje no cambie entre generaciones. Los pesos expresan las prioridades del escenario y permiten repetir experimentos cambiando esas prioridades de manera explícita.

DETALLE PARA EL LECTOR Y LÍMITES
La irradiación usa min-max con los extremos de todas las celdas válidas. Las distancias usan min-max invertido. Ambos se recortan a [0,1]. La potencia se divide por 80 MW y la compactación ya está en [0,1]. No hay z-score ni recalibración por generación. Fitness = 0,35 solar + 0,10 proximidad a línea + 0,35 proximidad a ET + 0,10 potencia + 0,10 compactación. Un cambio porcentual en fitness no equivale a una mejora energética ni económica.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\spatial.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\genetic_algorithm.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 10. El cromosoma construye el parque

TIEMPO SUGERIDO: 1.5 minutos

EXPLICACIÓN PARA EXPONER
El cromosoma contiene una celda inicial y una secuencia de instrucciones de crecimiento. La ilustración muestra prefijos de un individuo de la población inicial real: parte de la celda 535210 y termina con 6 celdas. Cada instrucción elige una celda de la frontera disponible. El orden modifica qué opciones existen después.

DECISIONES Y JUSTIFICACIÓN
Esta representación permite variar ubicación, superficie y forma sin codificar cada posible celda de la provincia como un bit. El crecimiento mantiene la conectividad. El ejemplo usa fragmentos de borde, por lo que su área final es 132,00 ha y no necesariamente 25 ha multiplicadas por el número de celdas.

DETALLE PARA EL LECTOR Y LÍMITES
Genes reales: 95225095, 1731288499, 1172338507, 20626909, 1529489493. Se ordena la frontera por posición en la grilla y se elige gene módulo tamaño de frontera. Un gen no significa norte, sur o una coordenada fija. Algunas instrucciones pueden omitirse o quedar sin procesar por capacidad. Distintos cromosomas pueden representar el mismo parque. Los alias G1…G5 simplifican la lectura y su correspondencia está en el registro de evidencia.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\spatial.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 11. Una población distribuida en el territorio

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
La búsqueda comienza con 50 candidatos. El mapa señala sus centroides en esta corrida. La inicialización reparte los puntos de partida entre sectores ocupados, en lugar de concentrar todos los individuos alrededor de una única ubicación. Cada candidato recibe una secuencia aleatoria que determina su crecimiento.

DECISIONES Y JUSTIFICACIÓN
La distribución territorial busca ampliar la exploración desde el comienzo. La diversidad de tamaños y recorridos aporta alternativas que los operadores pueden combinar. Se evita describir la población como cincuenta parques uniformemente sorteados entre todos los parques posibles: el procedimiento no tiene esa distribución.

DETALLE PARA EL LECTOR Y LÍMITES
Se recorren sectores de 50 km en un orden aleatorio sin repetirlos hasta agotar la tanda. Dentro de cada sector se elige una celda válida. La longitud inicial tiene entre 0 y 10 genes en este escenario. El número efectivo de celdas depende de los límites. La semilla de azar 20261007 es diferente de la celda inicial de cada cromosoma.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\initialization.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 12. Selección de candidatos

TIEMPO SUGERIDO: 0.9 minutos

EXPLICACIÓN PARA EXPONER
En cada generación, el algoritmo compara pequeños grupos de candidatos y selecciona a los de mayor puntaje para producir descendencia. Los mejores tienen más oportunidades de contribuir, pero la selección no elimina toda la variabilidad. La ilustración es conceptual y no asigna puntajes ficticios.

DECISIONES Y JUSTIFICACIÓN
Los torneos ofrecen una regla simple de selección sin depender de probabilidades proporcionales al fitness. Además, el elitismo conserva dos parques distintos de buen desempeño, lo que protege los avances frente a cambios posteriores.

DETALLE PARA EL LECTOR Y LÍMITES
El torneo utiliza tres participantes y la población se mantiene en 50. El elitismo compara identidad territorial para no conservar dos copias del mismo conjunto de celdas. Los duplicados se detectan por el parque construido y pueden reemplazarse por nuevos individuos con hasta ocho reintentos. El límite de intentos evita un ciclo sin fin, por lo que no es una garantía absoluta de diversidad.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\selection.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\genetic_algorithm.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 13. Crossover: combinar instrucciones

TIEMPO SUGERIDO: 1.6 minutos

EXPLICACIÓN PARA EXPONER
Este cruce ocurrió en la generación 1. El hijo conserva la celda inicial del padre A y sus primeras 4 instrucciones, y recibe las instrucciones restantes de B. El nuevo parque se vuelve a construir y evaluar. En el ejemplo, el fitness del padre A pasa de 0,5424 al 0,5507 del hijo aceptado.

DECISIONES Y JUSTIFICACIÓN
El operador actual elimina instrucciones sin efecto antes del cruce, ensaya hasta tres posiciones de corte comunes y conserva, para cada rama, una alternativa que no empeore a su progenitor. También admite empates con un parque diferente para explorar. La mejora se garantiza en este operador, pero una mutación o sustitución posterior puede cambiar al individuo.

DETALLE PARA EL LECTOR Y LÍMITES
Operador competitive_homologous. Probabilidad de cruce por pareja: 0,75. Cortes ensayados en el evento: 5, 3, 4. El corte mostrado es 4. A: 1220993495, 1386554089, 526188376, 1917849625, 363970879, 768858952, 1179490956. B: 990049668, 562402137, 2093737815, 1793146658, 199746400, 136460261, 359959211. Hijo: 1220993495, 1386554089, 526188376, 1917849625, 199746400, 136460261, 359959211. La semilla espacial del hijo es 455269. Intercambiar instrucciones no equivale a pegar los polígonos de dos lugares: los genes se reinterpretan sobre la frontera local del hijo.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\crossover.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 14. Mutación: explorar una variación

TIEMPO SUGERIDO: 1.2 minutos

EXPLICACIÓN PARA EXPONER
El ejemplo muestra una mutación real de la generación 1: el parque incorpora una celda vecina, resaltada en ámbar. Pasa de 1 a 2 celdas y de 7,825 a 15,650 MW estimados. El cambio de puntaje es pequeño, de 0,5786 a 0,5798, porque también varían forma y distancias.

DECISIONES Y JUSTIFICACIÓN
La mutación introduce opciones que no surgen del cruce y mantiene exploración. Puede agregar crecimiento, recortar la secuencia, cambiar una instrucción efectiva o modificar el punto de partida. El ejemplo de agregado resulta fácil de seguir sin sugerir que todas las mutaciones expanden un parque.

DETALLE PARA EL LECTOR Y LÍMITES
Probabilidad de mutación 0,20 y hasta cuatro intentos para obtener un conjunto de celdas diferente. El evento mostrado necesitó 1 intento. Genes antes: []. Genes después: [0]. Celda inicial: 69620. La mutación exige un cambio territorial, no una mejora de fitness. Si no consigue cambio en el máximo de intentos, conserva el original.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\mutation.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 15. El ciclo evolutivo

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
Recorrer la secuencia completa: crear candidatos, evaluar y seleccionar, cruzar, mutar y formar la siguiente generación. Este ciclo se repite hasta el número configurado de generaciones. El sistema conserva además candidatos evaluados para preparar el ranking final.

DECISIONES Y JUSTIFICACIÓN
La repetición combina explotación de soluciones prometedoras con exploración de nuevas variantes. Elitismo, control de duplicados y archivo territorial cumplen funciones distintas: proteger avances, sostener diversidad y conservar alternativas para la salida.

DETALLE PARA EL LECTOR Y LÍMITES
El criterio de parada en esta corrida es fijo: 200 generaciones. No es una prueba de convergencia al óptimo. El historial incluye la generación 0, por eso tiene 201 filas. El archivo conserva hasta diez candidatos por sector de 50 km. Ese límite puede descartar opciones útiles para un top 5 sin superposición, como mostró la auditoría previa.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\genetic_algorithm.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 16. Los datos se preparan antes de buscar

TIEMPO SUGERIDO: 1.1 minutos

EXPLICACIÓN PARA EXPONER
Las fuentes externas se consultan y validan antes de ejecutar la optimización. El proyecto prepara la grilla, las exclusiones, la información solar y la infraestructura, y guarda un conjunto de datos local. Cada corrida trabaja sobre ese conjunto y produce registros, un ranking y mapas.

DECISIONES Y JUSTIFICACIÓN
Separar preparación y búsqueda permite repetir semillas sin volver a descargar datos y mejora la trazabilidad. Si falta una fuente activa, el proceso debe informar el problema en lugar de inventar valores. El resultado queda vinculado a un identificador de dataset y a la configuración utilizada.

DETALLE PARA EL LECTOR Y LÍMITES
Implementación: Python y NumPy para el AG propio; pandas para registros; GeoPandas, Shapely y PyProj para geometría; xarray, Zarr, Dask y fsspec para clima; SQLAlchemy y SQLite para persistencia; Folium para mapas. IGN se descarga como shapefile ZIP, INDEC mediante WFS paginado de 500 entidades, líneas mediante CKAN, estaciones mediante CSV y clima mediante bloques ARCO Zarr. La caché evita descargas repetidas. Las versiones quedan en optimization_run.json.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\requirements.txt
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\pipeline\preprocess.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\pipeline\reporting.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\api\indec.py
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\climate\arco.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 17. Escenario de la nueva corrida

TIEMPO SUGERIDO: 0.8 minutos

EXPLICACIÓN PARA EXPONER
Antes de mostrar resultados, fijar las condiciones del experimento. La corrida utiliza 50 individuos durante 200 generaciones, con un límite de 80 MW. Usa el dataset ya procesado y una semilla nueva, sin seleccionar retrospectivamente la mejor ejecución para esta presentación.

DECISIONES Y JUSTIFICACIÓN
Elegir un escenario explícito permite interpretar el resultado y reproducirlo. Se mantuvieron los parámetros actuales del proyecto y solo se cambió la semilla aleatoria a 20261007. No se incorporaron las mejoras futuras de archivo ni la combinación de semillas.

DETALLE PARA EL LECTOR Y LÍMITES
Configuración completa: celdas de 500 m, densidad 31,3 MWac/km², pesos 0,35/0,10/0,35/0,10/0,10 para solar/líneas/ET/potencia/compactación. Cruce 0,75, mutación 0,20, elitismo 2, torneo 3, sectores de 50 km, ocho reintentos de duplicados, cuatro de mutación y archivo de diez por sector. Top 5 territorial sin superposición y con separación adicional 0 km. El registro de eventos observa el algoritmo sin consumir azar adicional.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\config.yaml
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 18. El puntaje mejora durante la búsqueda

TIEMPO SUGERIDO: 1.2 minutos

EXPLICACIÓN PARA EXPONER
El mejor puntaje de la población inicial es 0,6084 y el mejor final es 0,7283. La curva permite ver cuándo aparecen avances y cuándo la búsqueda pasa por períodos sin mejora del líder. La media de la población puede fluctuar, porque permanecen individuos exploratorios.

DECISIONES Y JUSTIFICACIÓN
Mostrar el historial evita reducir el resultado a una sola cifra final. Se incluyen el mejor y el promedio para distinguir avance del líder de comportamiento de la población. El eje horizontal identifica generaciones y el vertical el fitness adimensional.

DETALLE PARA EL LECTOR Y LÍMITES
La gráfica contiene las 201 observaciones reales, incluida la generación 0. El fitness no es porcentaje de eficiencia ni producción. Se observaron 6182 parques distintos en poblaciones, 13981 decodificaciones sin caché y 55772 solicitudes totales. Esas cantidades no son equivalentes. La instrumentación añade trabajo de observación, por lo que no se usa el tiempo de esta corrida como benchmark.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d\history.csv
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 19. Las formas también cambian

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
Comparar el mejor candidato observado al inicio, en la generación 50 y al final. Las formas provienen de celdas reales del territorio. El líder final adopta una forma cuadrada de nueve celdas, coherente con la preferencia por compactación del escenario.

DECISIONES Y JUSTIFICACIÓN
Los contornos ayudan a comprender que el algoritmo modifica una solución territorial, no solo una secuencia de números. Cada imagen se centra para facilitar la comparación de forma. Los candidatos no necesariamente están en la misma ubicación.

DETALLE PARA EL LECTOR Y LÍMITES
Estos son líderes de distintas generaciones, no una genealogía demostrada de un único individuo. No afirmar que el candidato inicial se convirtió directamente en el final. La escala de cada recorte prioriza legibilidad; las cantidades de celdas se indican explícitamente. La forma regular es un resultado del escenario, no una garantía de factibilidad constructiva.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 20. El candidato encontrado

TIEMPO SUGERIDO: 1.5 minutos

EXPLICACIÓN PARA EXPONER
El mejor candidato tiene nueve celdas completas, 225 hectáreas y una potencia estimada de 70,425 MW. Su perímetro es 6 km y su compactación es 0,7854. Recibe un indicador solar de 1.895,96 kWh/m²/año. El valor surge del balance de los cinco criterios, por eso no necesariamente conviene usar todo el límite de 80 MW.

DECISIONES Y JUSTIFICACIÓN
El puntaje 0,7283 coincide, dentro de tolerancia numérica, con el mejor rectángulo completo enumerado en el experimento previo. Ese resultado permite ubicar la corrida frente a una referencia concreta, sin presentarlo como el óptimo entre todas las formas posibles.

DETALLE PARA EL LECTOR Y LÍMITES
La distancia a la línea más próxima es 104,5 m, pero la estación más cercana del conjunto considerado es Santo Tomé, a 169,9 km. Esta diferencia es una limitación material del modelo. Otros ensayos del AG alcanzaron 0,7347 con formas que no pertenecen a la familia de rectángulos completos. No usar la energía ideal calculada como pronóstico de generación vendible.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\experiments\search-quality-compactness-20261006\analysis.json
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 21. Comparación con otras búsquedas

TIEMPO SUGERIDO: 1.5 minutos

EXPLICACIÓN PARA EXPONER
El experimento previo comparó diez semillas del AG con búsqueda aleatoria y búsqueda aleatoria más mejora local. Bajo el mismo presupuesto de evaluaciones por semilla, el AG obtuvo mejor ganador en diez de diez comparaciones con azar puro y en ocho de diez con azar más búsqueda local. El gráfico muestra el promedio del mejor fitness de cada corrida.

DECISIONES Y JUSTIFICACIÓN
La comparación aporta evidencia externa al historial del propio AG. Mantener dataset, restricciones, pesos y presupuesto permite atribuir las diferencias a la estrategia de búsqueda dentro de este experimento. Se muestran medias de diez resultados, no una selección de ganadores favorables.

DETALLE PARA EL LECTOR Y LÍMITES
Son 30 corridas anteriores, separadas de la nueva ejecución de esta defensa. Presupuestos de 13.182 a 15.084 evaluaciones por semilla, promedio 14.016. La búsqueda híbrida destinó 40% al azar y 60% a movimientos locales de agregar, quitar o intercambiar una celda. Además se enumeraron 13.691.836 rectángulos válidos, con máximo 10 celdas completas. Solo dos de diez corridas del AG superaron el mejor rectángulo. El mejor AG previo fue 0,7347. Los resultados respaldan competitividad, sin certificar optimalidad global.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\experiments\search-quality-compactness-20261006\informe.md
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\experiments\search-quality-compactness-20261006\summary.csv
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 22. Alcance y limitaciones

TIEMPO SUGERIDO: 1.3 minutos

EXPLICACIÓN PARA EXPONER
El sistema entrega candidatos para estudiar, pero todavía no comprueba la viabilidad completa de una planta. Faltan condiciones eléctricas, ambientales y del terreno que pueden cambiar la selección. También hay incertidumbre asociada al historial climático breve y a los pesos experimentales.

DECISIONES Y JUSTIFICACIÓN
El MVP priorizó integrar la búsqueda espacial y las fuentes disponibles. Cada variable nueva requiere una fuente verificable y una regla de interpretación. Una omisión no significa que el factor sea irrelevante ni permite suponer que todos los sitios cumplen.

DETALLE PARA EL LECTOR Y LÍMITES
Capacidad libre de red: no se integraron MVA disponibles ni un estudio de flujos. Inundación y agua: falta una máscara hídrica y de amenaza validada. Pendiente: falta incorporar un modelo de elevación y un umbral. Áreas protegidas: falta integrar zonificación. Propiedad, uso, caminos y costos: faltan datos parcelarios y económicos consistentes. Temperatura, orientación, sombras y pérdidas: falta un modelo energético detallado. Los pesos aún no cuentan con calibración experta ni sensibilidad sistemática. La ausencia de estos datos impide afirmar que el parque sea construible.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\README.md
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\config.yaml
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 23. Mejoras futuras

TIEMPO SUGERIDO: 1 minutos

EXPLICACIÓN PARA EXPONER
La primera mejora es conservar más alternativas útiles. La auditoría encontró parques ya evaluados que habían desaparecido del archivo y que mejoraban el ranking territorial. La segunda es reunir candidatos de varias semillas antes de construir el top 5. También hacen falta nuevas restricciones y una calibración de prioridades.

DECISIONES Y JUSTIFICACIÓN
Retener alternativas y combinar semillas aprovecha la capacidad de búsqueda ya demostrada. La identidad debe ser el conjunto de celdas para evitar duplicados. El ranking territorial debe armarse después de reunir candidatos, aplicando la regla de no superposición.

DETALLE PARA EL LECTOR Y LÍMITES
En la auditoría de la semilla 42, recuperar todos los parques evaluados elevó el promedio del top 5 de 0,6991 a 0,7046 sin una búsqueda nueva. Incluye pruebas internas de operadores, no solo individuos que llegaron a la población. Varias semillas aumentan el presupuesto total y deben compararse bajo esa condición. Ninguna de estas mejoras se implementó en la corrida presentada. La selección territorial actual es voraz y tampoco certifica la mejor combinación de cinco parques.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\experiments\search-quality-compactness-20261006\audit_archive\analysis.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\src\optimization\ranking.py
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## 24. Conclusiones

TIEMPO SUGERIDO: 0.7 minutos

EXPLICACIÓN PARA EXPONER
Cerrar con tres afirmaciones respaldadas. El proyecto conecta datos territoriales con un método capaz de explorar ubicación, forma y superficie. La corrida nueva mejora el puntaje y alcanza la mejor solución de la familia rectangular previamente enumerada. La comparación anterior muestra ventaja del AG frente a las referencias estocásticas en este escenario.

DECISIONES Y JUSTIFICACIÓN
El valor de la propuesta está en generar candidatos trazables para una evaluación posterior. Las decisiones, configuraciones y limitaciones quedan explícitas. La conclusión evita confundir un resultado favorable con una demostración matemática de optimalidad.

DETALLE PARA EL LECTOR Y LÍMITES
Frase sugerida para cerrar: El algoritmo genético encuentra soluciones competitivas bajo las reglas del modelo y permite justificar cómo se obtuvieron. Presentamos la mejor solución encontrada en esta corrida, con sus límites, como punto de partida para estudios de viabilidad. Reservar el tiempo restante hasta 30 minutos para preguntas. La guía incluye detalles técnicos y fuentes para defender cada decisión.

FUENTES Y TRAZABILIDAD
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\README.md
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\tmp\presentation_build\defensa_actual\evidence.json
C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\experiments\search-quality-compactness-20261006\informe.md
Corrida de ejemplo: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261007T021047-df88ea4d
Semilla aleatoria: 20261007. Población 50, 200 generaciones, cruce 0,75, mutación 0,20, elitismo 2, torneo de 3.
Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. No se hicieron nuevas descargas para esta corrida.
Las ilustraciones son conceptuales. Los mapas y formas de candidatos proceden de geometrías oficiales y registros reales.

## Registro de ilustraciones

Se reutilizaron ilustraciones conceptuales de la presentación previa y la imagen fotovoltaica aportada por el usuario. La nueva ilustración del ciclo se generó con la herramienta integrada imagegen y se conserva en tmp/presentation_build/defensa_actual/ciclo.png. Prompt: ilustración editorial minimalista, fondo blanco, azul oscuro, verde y ámbar, cinco grupos con parcelas, selección, intercambio de secuencias, nueva celda y parque solar, conectados por flechas y retorno. No incluye una silueta geográfica. Todos los contornos territoriales y formas de candidatos son gráficos de datos reales.
