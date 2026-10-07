# Guía de defensa: parques solares en Santa Fe

Recorrido principal: 24 diapositivas, 25.3 minutos sugeridos. Tres diapositivas de apoyo quedan fuera del recorrido y se consultan durante preguntas. Ensayar con cronómetro y reservar el margen hasta 30 minutos.

## Esqueleto elegido

1. Problema y funcionamiento del parque (1–3).
2. Variables, omisiones y supuestos (4–8).
3. Representación, evaluación y flujo del proyecto (9–11).
4. Nueva corrida y operadores reales del AG (12–17).
5. Resultados y conclusiones (18–21).
6. Detalle técnico al final (22–24).
7. Apoyo para preguntas (25–27).

## Experimento

- Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
- Semilla: 20261006. Población 50. Generaciones 200. Cruce 0,75. Mutación 0,20. Elitismo 2. Torneo 3.
- Límite experimental 80 MW. Densidad 31,3 MW/km². Grilla 500 m. Pesos solar 0,40, líneas 0,10, ET 0,40 y potencia 0,10.
- Territorios de 50 km, 8 reintentos de duplicados, 4 de mutación efectiva, archivo de 10 candidatos por territorio y separación territorial adicional 0 km.
- Dataset 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e. 526.194 celdas válidas de 535.751.
- Clima: 11 períodos de enero, abril, julio y octubre entre 2024 y julio de 2026. Es estimación estacional.
- Mejor fitness 0,6384 a 0,7174. Candidato final 250 ha y78,25 MW.

## 1. Parques solares en Santa Fe

Tiempo: 0.3 minutos.

**Explicación para exponer:** Presentar el objetivo: explorar ubicación, forma y superficie de parques solares mediante un algoritmo genético. La defensa dura unos 26 minutos y reserva las diapositivas de apoyo para preguntas.

**Decisiones y justificación:** Organizar el relato alrededor de una decisión territorial permite comprender el algoritmo antes de ver su implementación.

**Alcance y límites:** El resultado es una preselección computacional que requiere estudios posteriores.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md

## 2. La decisión territorial

Tiempo: 1 minutos.

**Explicación para exponer:** Un parque necesita buen recurso solar, terreno suficiente y acceso a infraestructura. Elegir sólo la celda con más radiación omite la forma del parque y la conexión. La pregunta del proyecto es qué combinaciones de celdas conviene estudiar primero.

**Decisiones y justificación:** Santa Fe es el alcance geográfico fijado. Una búsqueda heurística permite explorar un espacio amplio de ubicaciones y configuraciones sin enumerar todas las formas posibles.

**Alcance y límites:** El proyecto no estima rentabilidad ni garantiza disponibilidad del suelo. Tampoco prueba que encontró el óptimo global.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
- https://www.nlr.gov/gis/rev

## 3. Funcionamiento de un parque solar

Tiempo: 1 minutos.

**Explicación para exponer:** Los paneles convierten radiación en corriente continua. Los inversores la transforman en corriente alterna. Los transformadores adaptan la tensión y la infraestructura permite conectar la planta con la red.

**Decisiones y justificación:** Esta explicación identifica los elementos que motivan nuestras variables: recurso solar, superficie y proximidad a líneas y estaciones.

**Alcance y límites:** La simulación no dimensiona paneles, inversores, transformadores ni protecciones. La potencia representa capacidad instalada estimada y la energía una producción durante un período.

**Fuentes:**

- https://www.nlr.gov/news/video/training-module-3-text-version
- https://atb.nrel.gov/electricity/2024/utility-scale_pv

## 4. Variables que usa el modelo

Tiempo: 1 minutos.

**Explicación para exponer:** Los cuatro criterios del fitness son irradiación anual estimada, proximidad a líneas, proximidad a las cuatro estaciones de referencia y potencia instalada estimada por área. Las zonas urbanas son una exclusión previa.

**Decisiones y justificación:** Distinguir criterios graduables de restricciones evita que un puntaje alto compense una celda urbana. La potencia se deriva de la superficie, no de la radiación.

**Alcance y límites:** Las distancias se calculan desde el centroide del parque. Se usan las geometrías disponibles y cuatro ET seleccionadas, no una representación completa de todas las conexiones posibles.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py

## 5. Radiación solar en Santa Fe

Tiempo: 1 minutos.

**Explicación para exponer:** La fuente ERA 5-Land entrega SSRD horario. El proyecto convierte J/m² a kWh/m², exige meses completos, promedia años por mes y pondera días de estación para enero, abril, julio y octubre. El parque usa una media ponderada por el área de sus celdas.

**Decisiones y justificación:** Los cuatro meses representan las estaciones y reducen el volumen de datos. El requisito de horas completas evita comparar un mes incompleto con otro completo.

**Alcance y límites:** Es una estimación estacional. El historial empieza en 2024 y cubre 11 períodos hasta julio de 2026. Es breve y no sustituye una climatología larga. Los puntos del mapa representan agregados por píxel climático, no una medición independiente por celda.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/arco.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/climatology.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py

## 6. Infraestructura eléctrica de referencia

Tiempo: 1 minutos.

**Explicación para exponer:** El modelo calcula la menor distancia entre el centroide del parque y las líneas disponibles y la menor distancia a las cuatro ET: Río Coronda, Romang, Rosario Oeste y Santo Tomé. Ambas son medidas geográficas en un sistema proyectado.

**Decisiones y justificación:** Usar distancias aporta un indicador simple de proximidad. Mantener cuatro identidades estables hace el escenario repetible y evita confundir entidades entre corridas.

**Alcance y límites:** La selección de cuatro ET es una delimitación del MVP que restringe los resultados. Cercanía no acredita posibilidad de conexión. No usamos capacidad libre, MVA, flujos eléctricos ni una ruta de cableado. La capa de líneas disponible no equivale a una red de transporte validada para conexión.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py

## 7. Variables pendientes para evaluar viabilidad

Tiempo: 1.2 minutos.

**Explicación para exponer:** Una preselección completa también debería considerar pendiente, inundaciones y cuerpos de agua, áreas protegidas, uso y propiedad del suelo, acceso vial y capacidad de conexión. Estos factores pueden modificar o invalidar los candidatos actuales.

**Decisiones y justificación:** No se implementaron porque el MVP prioriza la búsqueda espacial con las fuentes actualmente integradas. Cada factor necesita una fuente verificable, una regla y validación propia. Esto delimita el alcance, no demuestra irrelevancia.

**Alcance y límites:** Pendiente: falta integrar y validar un modelo de elevación. Inundaciones y agua: falta una máscara hídrica y de amenaza. Áreas protegidas: falta integrar zonificación ambiental. Propiedad, uso y accesos: faltan datos parcelarios, permisos y costos. Capacidad real: faltan capacidad disponible y un estudio eléctrico. Temperatura, inclinación, sombras y pérdidas requieren un modelo de producción fotovoltaica. Costos y tarifas requieren un modelo económico. Ninguna de estas omisiones autoriza construir en el candidato.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
- https://www.nlr.gov/gis/rev
- https://atb.nrel.gov/electricity/2024/utility-scale_pv

## 8. Supuestos y restricciones

Tiempo: 1.2 minutos.

**Explicación para exponer:** Trabajamos con celdas de 500 metros y parques que crecen por bordes compartidos. Se excluyen las celdas que tocan la máscara urbana INDEC. La potencia es el área real por 31,3 MW/km² y el crecimiento se limita a 80 MW.

**Decisiones y justificación:** 500 m es la discretización del problema. La contigüidad garantiza un conjunto conectado. La exclusión urbana es conservadora, con buffer cero y relleno de huecos internos. La densidad de potencia procede del estudio NREL de uso de tierra: 7,9 acres/MWac de área total en grandes plantas FV, equivalentes aproximadamente a 31,3 MWac/km². Los 80 MW son un escenario experimental configurable.

**Alcance y límites:** No existe calibración local de la densidad. El límite de 80 MW no corresponde a capacidad libre de ninguna ET. Los pesos 0,4/0,1/0,4/0,1 son iniciales y requieren análisis de sensibilidad. La exclusión urbana no cubre las restricciones hídricas o ambientales pendientes.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- https://docs.nrel.gov/docs/fy13osti/56290.pdf

## 9. Representación de un parque

Tiempo: 1.3 minutos.

**Explicación para exponer:** Un individuo contiene una celda semilla y una secuencia variable de genes enteros. El decodificador empieza por la semilla y usa cada gen para elegir una celda de la frontera. Así aparecen ubicación, forma y superficie.

**Decisiones y justificación:** La representación construye contigüidad por crecimiento. Una longitud variable permite explorar distintos tamaños. La secuencia guarda decisiones de crecimiento, no coordenadas de cada panel.

**Alcance y límites:** Un gen no es una dirección fija. Su significado depende de la frontera actual. Genes distintos pueden dar el mismo conjunto de celdas. La longitud del cromosoma puede exceder la cantidad de genes que realmente produce crecimiento.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/initialization.py

## 10. Fitness: cómo comparamos parques

Tiempo: 1.2 minutos.

**Explicación para exponer:** El fitness combina cuatro puntajes entre cero y uno. Más irradiación aumenta el puntaje solar, menos distancia aumenta la proximidad y más potencia aumenta el aprovechamiento del límite. Los pesos suman uno.

**Decisiones y justificación:** Una suma ponderada proporciona un orden explícito y fácil de auditar. Los pesos iniciales priorizan radiación y ET, con 40% cada una, y asignan 10% a líneas y 10% a potencia.

**Alcance y límites:** Estos pesos no se validaron científicamente y no representan euros, producción real ni probabilidad de éxito. Un fitness alto significa buen desempeño bajo el escenario configurado. Los criterios pueden compensarse dentro de esta suma.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py

## 11. Flujo de trabajo del proyecto

Tiempo: 1 minutos.

**Explicación para exponer:** Primero se obtienen las fuentes y se guarda la caché. Luego se validan geometrías y cobertura climática, se construye la grilla y sus vecinos, y se guarda un snapshot local. El AG carga ese dataset para buscar y exporta mapas, rankings e historial.

**Decisiones y justificación:** Separar preparación de optimización evita repetir descargas por individuo y permite ejecutar múltiples escenarios sobre el mismo conjunto de datos. El identificador del dataset y la configuración hacen trazable cada resultado.

**Alcance y límites:** El mapa puede usar teselas web, pero el bucle del AG trabaja sólo con datos locales. Cambios incompatibles de fuente o configuración espacial exigen reprocesar.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/main.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/database/spatial.py

## 12. Parámetros de la nueva corrida

Tiempo: 0.8 minutos.

**Explicación para exponer:** La corrida del 6 de octubre usa semilla aleatoria 20261006, 50 individuos y 200 generaciones. Se mantienen 75% de cruce, 20% de mutación, dos élites y torneo de tres. El escenario es 80 MW, densidad 31,3 y pesos 0,4/0,1/0,4/0,1.

**Decisiones y justificación:** Mantener el escenario y cambiar la semilla respecto de la presentación anterior produce un experimento nuevo comparable. Los parámetros se conservaron para demostrar el comportamiento del proyecto actual, no se eligieron mediante una búsqueda de hiperparámetros.

**Alcance y límites:** La semilla reproduce la secuencia pseudoaleatoria bajo el mismo dataset y entorno. Una sola corrida no mide robustez estadística. El criterio de parada es completar 200 generaciones, con evaluación inicial en generación cero.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/config_corrida.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json

## 13. Un cromosoma real y su crecimiento

Tiempo: 1.2 minutos.

**Explicación para exponer:** El padre A del cruce real tiene semilla 194480 y cuatro genes:2083272650,938200436,671673529,538685106. Mostrar tres pasos de decodificación: sólo semilla, primer par de genes y secuencia completa, que genera cinco celdas y 39,125 MW.

**Decisiones y justificación:** Seguir prefijos de un cromosoma permite ver cómo una secuencia se transforma en un parque sin inventar una geometría. El orden de la frontera es determinista y cada selección usa gen módulo cantidad de vecinos candidatos.

**Alcance y límites:** Estos son pasos de crecimiento dentro de un individuo, no generaciones del AG. El ejemplo se observó como padre del evento de cruce que produce la generación 2, no se afirma que fuera el mejor de la población.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json

## 14. Población inicial y selección

Tiempo: 1.1 minutos.

**Explicación para exponer:** La inicialización recorre territorios ocupados de 50×50 km en orden aleatorio y escoge una semilla dentro de cada uno. Genera longitudes de secuencia aleatorias y evalúa 50 parques. En cada torneo extrae tres candidatos con reemplazo y conserva el de mayor fitness.

**Decisiones y justificación:** El muestreo por territorios favorece cobertura espacial en lugar de concentrar todas las semillas en una zona. El torneo ejerce presión selectiva conservando azar. Dos élites distintas por conjunto de celdas pasan directamente a la próxima población.

**Alcance y límites:** Cobertura equilibrada no es un muestreo uniforme por superficie. El gráfico ilustra el mecanismo, no un torneo observado. Los ejemplos de operadores de las siguientes slides sí son eventos registrados. Los parámetros de torneo y elitismo no se calibraron para demostrar optimalidad.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/initialization.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/selection.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py

## 15. Cruce de secuencias: evento real

Tiempo: 1.3 minutos.

**Explicación para exponer:** En la generación 2, el padre A tiene semilla 194480 y cuatro genes; el B tiene semilla 78089 y seis. El cruce corta A tras el tercer gen y B tras el cuarto. El hijo A conserva la semilla A y combina A 1,A 2,A 3,B 5,B 6. Pasa de cinco a seis celdas y su fitness aumenta de 0,5273 a 0,5371.

**Decisiones y justificación:** El cruce de prefijo y sufijo admite secuencias de longitudes diferentes. Conservar la semilla del prefijo da un inicio definido para el nuevo decodificado. La probabilidad de 75% se aplica por pareja.

**Alcance y límites:** Los genes del otro padre se reinterpretan en la frontera del hijo, no transportan celdas físicas de B. El código también crea un hijo recíproco. Este evento mejoró al padre A, pero el cruce no garantiza mejora.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/crossover.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json

## 16. Mutación: una celda nueva

Tiempo: 1.2 minutos.

**Explicación para exponer:** En la generación 1, el individuo de semilla 23162 añade el gen 7 a su secuencia. El parque crece de 7 a 8 celdas, de 54,775 a 62,6 MW. El fitness pasa de 0,5174 a 0,5273.

**Decisiones y justificación:** La mutación efectiva elige al azar entre operaciones aplicables: añadir un gen que permita crecer, borrar el último crecimiento aceptado, cambiar un gen aceptado o cambiar la semilla. Reintenta hasta cuatro veces buscando un cambio de celdas.

**Alcance y límites:** 20% es probabilidad por hijo, no cantidad fija de mutaciones. Un cambio efectivo modifica el parque, pero no implica mejora del fitness. En el caso mostrado hubo un intento. Dorado señala semilla y nueva celda.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/mutation.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json

## 17. Ciclo de una generación

Tiempo: 1 minutos.

**Explicación para exponer:** El ciclo evalúa los 50 parques, conserva dos élites, selecciona hijos por torneo, cruza parejas, muta hijos y controla duplicados antes de formar la próxima población. Repite hasta 200 generaciones.

**Decisiones y justificación:** El elitismo conserva soluciones buenas. Cruce y mutación exploran otras configuraciones. El control de duplicados intenta evitar repetir el mismo conjunto de celdas, con hasta ocho reemplazos por muestreo.

**Alcance y límites:** Las élites pasan directamente a la nueva población, sin aplicarles los operadores. El flujo es conceptual y no expresa esa bifurcación literalmente. Si los reintentos se agotan se conserva el candidato. Además del mejor actual, un archivo conserva hasta 10 candidatos por territorio.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py

## 18. Evolución de la nueva corrida

Tiempo: 1.3 minutos.

**Explicación para exponer:** El mejor fitness crece de 0,6384 a 0,7174. La mejora relativa del puntaje es 12,4%. El historial registra 201 evaluaciones de población, de 0 a 200. La búsqueda visitó 6309 parques distintos.

**Decisiones y justificación:** Mostrar el mejor y la media permite distinguir progreso del líder y comportamiento de la población. Conservar el historial y métricas por generación permite auditar la búsqueda.

**Alcance y límites:** La mejora del fitness no es un aumento porcentual de producción. Una meseta no prueba óptimo global. Las élites reducen el riesgo de perder el mejor candidato y no eliminan la variabilidad entre semillas.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/history.csv

## 19. Mejor candidato encontrado

Tiempo: 1.2 minutos.

**Explicación para exponer:** El mejor parque tiene 10 celdas completas,2,5 km² o 250 ha y 78,25 MW estimados. Su irradiación media es 1.896,0 kWh/m²/año. Está a 14,9 m de la línea disponible más próxima y a 175,1 km de Santo Tomé, la ET de referencia más cercana.

**Decisiones y justificación:** La combinación favorece la irradiación máxima del dataset y proximidad a una línea. El score de potencia es 78,25/80=0,9781. En conjunto produce fitness 0,7174.

**Alcance y límites:** La gran distancia a la ET muestra una compensación de criterios y el efecto de trabajar con sólo cuatro estaciones. La distancia de 14,9 m se refiere al centroide y geometría de la línea, no a una traza viable. Deben revisarse las variables de viabilidad pendientes antes de interpretar el candidato como sitio construible.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/ranking.csv

## 20. Alternativas territoriales

Tiempo: 0.8 minutos.

**Explicación para exponer:** El ranking general ordena por fitness y puede contener variantes superpuestas. El ranking territorial selecciona hasta cinco alternativas sin superposición desde el archivo de candidatos. El mapa muestra sus centroides.

**Decisiones y justificación:** Separar ambos rankings entrega opciones espaciales además de variaciones del líder. La separación adicional configurada es 0 km: se prohíbe solapar, pero pueden existir alternativas próximas.

**Alcance y límites:** Las alternativas territoriales dependen del archivo acotado, no de una búsqueda exhaustiva. El mapa de la diapositiva ubica centroides y no muestra dimensiones de los parques a escala provincial.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/ranking.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/ranking_territorial.csv

## 21. Conclusiones y próximos pasos

Tiempo: 1.4 minutos.

**Explicación para exponer:** La corrida demuestra que el AG construye parques conectados y mejora el puntaje bajo un escenario explícito. El proyecto entrega candidatos, un mapa y un historial reproducible. El resultado también muestra que buenas puntuaciones pueden coexistir con limitaciones de conexión.

**Decisiones y justificación:** La principal contribución es integrar crecimiento espacial, criterios comparables y trazabilidad de búsqueda. Separar la preparación de datos permite ensayar nuevas semillas y parámetros.

**Alcance y límites:** No se demostró optimalidad ni robustez con una sola corrida. Próximos pasos: integrar restricciones territoriales faltantes y capacidad de red, ampliar la referencia climática, repetir semillas, variar pesos y comparar con una búsqueda aleatoria bajo igual presupuesto. Modelar producción y economía requiere trabajo adicional.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/history.csv

## 22. Detalle técnico: normalización

Tiempo: 1 minutos.

**Explicación para exponer:** Para irradiación se utiliza min-max: (x−mín)/(máx−mín). Para distancias se invierte:1−min-max. Los límites provienen de todas las celdas válidas y permanecen fijos en la corrida. La potencia se normaliza conP/80 MW.

**Decisiones y justificación:** Fijar los límites evita que cambiar la población altere la escala de comparación. Las métricas del parque usan irradiación media ponderada por área y distancias desde su centroide. Se recorta a[0,1]. Si mínimo y máximo coinciden, el criterio asigna 1 a todos.

**Alcance y límites:** No usamos z-score ni renormalizamos por generación. Estos puntajes son relativos al dataset y escenario. No comparar directamente fitness entre escenarios de distinto límite sin analizar sus componentes.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py

## 23. Implementación y bibliotecas

Tiempo: 0.8 minutos.

**Explicación para exponer:** Python organiza el pipeline y el AG propio. NumPy gestiona azar y cálculos, pandas los registros, GeoPandas y Shapely las geometrías y distancias, y PyProj los sistemas de coordenadas. xarray,Zarr,Dask y fsspec leen el clima. SQLAlchemy y SQLite persisten datasets y corridas. Folium y HTML presentan resultados.

**Decisiones y justificación:** Separar módulos de datos, procesamiento, optimización y visualización permite cambiar una fuente o probar un escenario sin mezclar acceso remoto con evaluación. Pydantic valida configuración y requests realiza los accesos HTTP vectoriales.

**Alcance y límites:** El AG no depende de DEAP. La librería específica de dibujo de gráficas es JavaScript embebido del proyecto. El mapa puede requerir teselas de OpenStreetMap. Las versiones efectivas de las bibliotecas principales están en los metadatos de la corrida.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/requirements.txt
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/main.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/reporting.py

## 24. Fuentes, peticiones y manejo de datos

Tiempo: 1 minutos.

**Explicación para exponer:** IGN se obtiene como ZIP con shapefile. INDEC usa GET WFS paginado, con 500 registros por página. Las líneas usan CKAN datastore_search paginado y las ET un CSV directo. El clima usa lectura de bloques ARCO Zarr. Se valida la respuesta y se conserva la caché antes de preparar el dataset.

**Decisiones y justificación:** WFS requiere controles de IDs, páginas y total para evitar capas incompletas. El clima exige horas únicas y finitas para cada mes. La caché reduce transferencias repetidas. SQLite conserva snapshots de contenido y la corrida guarda semilla, configuración, versiones y límites de normalización.

**Alcance y límites:** La credencial de Copernicus se toma del entorno y se excluye de los resultados. Si falta una fuente activa, el pipeline se detiene. El código no inventa ET ni valores solares. La exclusión urbana siempre permanece activa.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/api/indec.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/api/datos_gob_ar.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/arco.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/database/spatial.py

## 25. Apoyo: límites y valores del escenario

Tiempo: apoyo para preguntas.

**Explicación para exponer:** Consultar durante preguntas los rangos fijos de normalización y principales supuestos.

**Decisiones y justificación:** Estos valores proceden directamente de optimization_run.json y no se recalcularon a partir de la población.

**Alcance y límites:** Los rangos reflejan el dataset utilizado. No son valores universales.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json

## 26. Apoyo: genes del cruce observado

Tiempo: apoyo para preguntas.

**Explicación para exponer:** Los alias del diagrama corresponden a los enteros indicados en esta tabla. La semilla del hijo A es 194480.

**Decisiones y justificación:** La tabla permite auditar el ejemplo sin cargar la explicación principal con enteros largos. Los cortes son 3 y 4.

**Alcance y límites:** Los enteros se interpretan mediante módulo sobre la frontera actual. Un alias no identifica una dirección fija.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/crossover.py
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json

## 27. Apoyo: mejores parques por generación

Tiempo: apoyo para preguntas.

**Explicación para exponer:** Comparar formas del mejor candidato en generaciones 0,50 y 200. Los tres son resultados reales de la nueva corrida.

**Decisiones y justificación:** Esta comparación ilustra cambios en el liderazgo de la población.

**Alcance y límites:** No es una genealogía: distintos líderes pueden proceder de diferentes padres y ubicaciones. El líder final conserva 32 genes, de los cuales 9 producen crecimiento, y termina con 10 celdas.

**Fuentes:**

- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
- C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py

## Imágenes y cartografía

Todas las imágenes de Santa Fe usan la geometría oficial IGN del dataset preparado, conservando su contorno. Las ilustraciones conceptuales de paneles, transformadores, operadores y flujo se generaron con la herramienta integrada imagegen y se guardaron en tmp/presentation_build/defensa_nueva. Los mapas, formas de parques y gráficas usan los datos de la nueva corrida.

Prompts utilizados: flujo paneles–inversor–transformador–red; flujo fuentes–caché–grilla rectangular–dataset–búsqueda sin siluetas provinciales; torneo de tres candidatos sin puntajes inventados; crossover real A1 A2 A3 + B5 B6 con cortes 3 y 4; factores pendientes de pendiente, agua, protección ambiental, suelo y capacidad de red.
