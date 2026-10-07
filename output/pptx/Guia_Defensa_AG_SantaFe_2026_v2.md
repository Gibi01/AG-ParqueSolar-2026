# Guía ampliada para la defensa

Recorrido principal: 24 diapositivas, unos 25 minutos. Las diapositivas 25–27 se reservan para preguntas. Las notas desarrolladas son material de preparación: usar el guion esencial en la exposición y el detalle para justificar decisiones.

## 1. Parques solares en Santa Fe

Tiempo orientativo: 0.3 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Presentar el objetivo: explorar ubicación, forma y superficie de parques solares mediante un algoritmo genético. La defensa dura unos 26 minutos y reserva las diapositivas de apoyo para preguntas.

DESARROLLO DEL CONTENIDO
El objeto de estudio es un parque completo representado por un conjunto de celdas. El sistema explora al mismo tiempo dónde comienza, cómo se extiende y qué superficie ocupa. Esa combinación diferencia el problema de elegir un punto en el mapa. A lo largo de la defensa conviene separar tres elementos: las fuentes describen el territorio, el modelo traduce esa información en reglas y criterios, y el algoritmo busca propuestas bajo esas reglas.

DECISIONES Y JUSTIFICACIÓN
Organizar el relato alrededor de una decisión territorial permite comprender el algoritmo antes de ver su implementación.

Abrir con el objetivo evita presentar las bibliotecas como si fueran la finalidad del proyecto. La secuencia de exposición permite entender primero el problema y después el mecanismo que lo resuelve. La nueva corrida aporta evidencia concreta, mientras que las diapositivas de apoyo reservan los números extensos para las preguntas.

ALCANCE Y LÍMITES
El resultado es una preselección computacional que requiere estudios posteriores.

PUNTO PARA LA DEFENSA
¿Qué entrega el proyecto? Un conjunto de candidatos espaciales ordenados por los criterios configurados, con geometrías e historial de búsqueda para analizarlos.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 2. La decisión territorial

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Un parque necesita buen recurso solar, terreno suficiente y acceso a infraestructura. Elegir sólo la celda con más radiación omite la forma del parque y la conexión. La pregunta del proyecto es qué combinaciones de celdas conviene estudiar primero.

DESARROLLO DEL CONTENIDO
La situación problemática es una decisión de localización con varios criterios. Un lugar puede ofrecer más radiación y, a la vez, estar lejos de las estaciones consideradas. Otro puede disponer de infraestructura cercana pero recibir menos radiación. Además, un parque ocupa una superficie conectada y su crecimiento modifica su centroide, sus distancias y su potencia estimada. Por eso no alcanza con ordenar puntos por una sola variable.

DECISIONES Y JUSTIFICACIÓN
Santa Fe es el alcance geográfico fijado. Una búsqueda heurística permite explorar un espacio amplio de ubicaciones y configuraciones sin enumerar todas las formas posibles.

El espacio de búsqueda combina muchas semillas posibles con muchas secuencias de crecimiento. El AG explora una parte de ese espacio y concentra nuevas propuestas alrededor de candidatos con mejores puntajes. Se adopta como método heurístico para este MVP. Esa elección no demuestra que sea superior a otros métodos: una comparación con búsqueda aleatoria bajo igual presupuesto queda como trabajo pendiente.

ALCANCE Y LÍMITES
El proyecto no estima rentabilidad ni garantiza disponibilidad del suelo. Tampoco prueba que encontró el óptimo global.

PUNTO PARA LA DEFENSA
¿Por qué un AG? Porque permite combinar exploración aleatoria y selección de configuraciones favorables en un problema espacial con formas variables. Su desempeño debe evaluarse, no darse por supuesto.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
https://www.nlr.gov/gis/rev
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 3. Funcionamiento de un parque solar

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Los paneles convierten radiación en corriente continua. Los inversores la transforman en corriente alterna. Los transformadores adaptan la tensión y la infraestructura permite conectar la planta con la red.

DESARROLLO DEL CONTENIDO
Leer la imagen de izquierda a derecha. Primero, las celdas fotovoltaicas reciben radiación y generan corriente continua mediante el efecto fotovoltaico. Los paneles se agrupan y conducen esa energía a inversores, que convierten la corriente continua en alterna. Después, un transformador adapta o eleva la tensión para transportar la energía y conectarla con la infraestructura eléctrica. La red alimenta puntos de consumo mediante los niveles de tensión y equipos correspondientes.

DECISIONES Y JUSTIFICACIÓN
Esta explicación identifica los elementos que motivan nuestras variables: recurso solar, superficie y proximidad a líneas y estaciones.

Este esquema explica por qué importan el recurso solar y la conexión. Sin embargo, la implementación no simula el circuito ni dimensiona inversores, cableado o transformadores. La superficie se convierte en una potencia instalada estimada mediante una densidad territorial. La irradiación se usa como criterio solar separado. Distinguir potencia y energía es esencial: MW describen capacidad o potencia; MWh describen energía durante un intervalo.

ALCANCE Y LÍMITES
La simulación no dimensiona paneles, inversores, transformadores ni protecciones. La potencia representa capacidad instalada estimada y la energía una producción durante un período.

PUNTO PARA LA DEFENSA
Los beneficios económicos y ambientales que aparecen en la imagen son mensajes generales. El proyecto no calcula ahorro, mantenimiento ni emisiones del ciclo de vida. «Sin emisiones» no debe interpretarse como una afirmación sobre fabricación y construcción. La imagen fue suministrada por el usuario y se incorpora completa como explicación conceptual.

FUENTES
https://www.nlr.gov/news/video/training-module-3-text-version
https://atb.nrel.gov/electricity/2024/utility-scale_pv
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/planta_fotovoltaica_usuario.png
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 4. Variables que usa el modelo

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Los cuatro criterios del fitness son irradiación anual estimada, proximidad a líneas, proximidad a las cuatro estaciones de referencia y potencia instalada estimada por área. Las zonas urbanas son una exclusión previa.

DESARROLLO DEL CONTENIDO
La irradiación anual estimada expresa el recurso recibido por unidad de superficie. Las distancias a líneas y ET expresan proximidad geográfica. La superficie determina la potencia instalada estimada, que favorece aprovechar el límite del escenario. Estas magnitudes tienen unidades diferentes, por lo que se convierten en puntajes antes de sumarlas. Las distancias parten del centroide ponderado por área del parque completo, no de la semilla aislada.

DECISIONES Y JUSTIFICACIÓN
Distinguir criterios graduables de restricciones evita que un puntaje alto compense una celda urbana. La potencia se deriva de la superficie, no de la radiación.

Una restricción decide si una propuesta puede construirse dentro del modelo. Un criterio de fitness decide cuánto se prefiere entre propuestas permitidas. Por ejemplo, una celda urbana queda excluida antes de evaluar el fitness, mientras que una distancia grande a una ET reduce el puntaje pero no invalida automáticamente el parque. Esta diferencia explica cómo el líder final puede estar lejos de una estación.

ALCANCE Y LÍMITES
Las distancias se calculan desde el centroide del parque. Se usan las geometrías disponibles y cuatro ET seleccionadas, no una representación completa de todas las conexiones posibles.

PUNTO PARA LA DEFENSA
¿La superficie cuenta dos veces? Tiene dos funciones distintas: transforma área en potencia estimada y permite aplicar el límite de 80 MW. Además, el cociente de potencia aporta un criterio de aprovechamiento del escenario.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 5. Radiación solar en Santa Fe

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
La fuente ERA 5-Land entrega SSRD horario. El proyecto convierte J/m² a kWh/m², exige meses completos, promedia años por mes y pondera días de estación para enero, abril, julio y octubre. El parque usa una media ponderada por el área de sus celdas.

DESARROLLO DEL CONTENIDO
SSRD representa radiación solar descendente sobre la superficie. Cada registro horario se convierte de J/m² a kWh/m² dividiendo por 3.600.000 y se resume por mes. El control de integridad exige todas las horas esperadas, sin duplicados y con valores finitos. Para cada mes representativo, se promedian los registros de años disponibles y completos. Se divide ese total mensual por los días del mes para obtener una media diaria y se multiplica por los días de su estación.

DECISIONES Y JUSTIFICACIÓN
Los cuatro meses representan las estaciones y reducen el volumen de datos. El requisito de horas completas evita comparar un mes incompleto con otro completo.

La suma utiliza enero para verano, abril para otoño, julio para invierno y octubre para primavera. Las ponderaciones son 90,25, 92, 92 y 91 días. En el dataset usado hay 11 períodos: los cuatro meses de 2024 y 2025, más enero, abril y julio de 2026. No hay octubre de 2026. El indicador del parque es un promedio ponderado por la superficie de sus celdas, lo que evita dar a un fragmento pequeño la misma influencia que a una celda completa.

ALCANCE Y LÍMITES
Es una estimación estacional. El historial empieza en 2024 y cubre 11 períodos hasta julio de 2026. Es breve y no sustituye una climatología larga. Los puntos del mapa representan agregados por píxel climático, no una medición independiente por celda.

PUNTO PARA LA DEFENSA
¿Es energía eléctrica producida? Es irradiación de referencia. Para estimar producción real harían falta inclinación, tecnología, temperatura, sombras, pérdidas e inversores. El indicador estacional y su historial breve son supuestos del modelo.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/arco.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/climatology.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 6. Infraestructura eléctrica de referencia

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El modelo calcula la menor distancia entre el centroide del parque y las líneas disponibles y la menor distancia a las cuatro ET: Río Coronda, Romang, Rosario Oeste y Santo Tomé. Ambas son medidas geográficas en un sistema proyectado.

DESARROLLO DEL CONTENIDO
Las líneas son geometrías lineales y las ET son ubicaciones puntuales. El evaluador busca la línea más cercana al centroide del parque y, por separado, la ET más cercana entre las cuatro identidades habilitadas. Las distancias se calculan en el sistema proyectado del dataset y se expresan en kilómetros. El mapa conserva el límite oficial del IGN y la geometría de las capas utilizadas, sin generar una forma provincial nueva.

DECISIONES Y JUSTIFICACIÓN
Usar distancias aporta un indicador simple de proximidad. Mantener cuatro identidades estables hace el escenario repetible y evita confundir entidades entre corridas.

La elección de CN, RM, RO y ST mantiene el alcance del MVP y permite reproducir el escenario con un conjunto estable. Esto también introduce una limitación importante: el modelo no busca entre todas las estaciones potencialmente disponibles. La cercanía es sólo una aproximación a la accesibilidad eléctrica. Una línea puede resultar próxima y aun así requerir estudios de tensión, capacidad, protección, trazado y conexión.

ALCANCE Y LÍMITES
La selección de cuatro ET es una delimitación del MVP que restringe los resultados. Cercanía no acredita posibilidad de conexión. No usamos capacidad libre, MVA, flujos eléctricos ni una ruta de cableado. La capa de líneas disponible no equivale a una red de transporte validada para conexión.

PUNTO PARA LA DEFENSA
¿Por qué no usamos MVA? La evaluación implementada trabaja con ubicaciones y distancias. No integra capacidad disponible ni un modelo de flujo eléctrico. Tampoco convierte una potencia nominal de transformador en capacidad libre para inyectar generación.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 7. Variables pendientes para evaluar viabilidad

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Una preselección completa también debería considerar pendiente, inundaciones y cuerpos de agua, áreas protegidas, uso y propiedad del suelo, acceso vial y capacidad de conexión. Estos factores pueden modificar o invalidar los candidatos actuales.

DESARROLLO DEL CONTENIDO
La pendiente afecta implantación y movimiento de suelo, pero todavía no se integró un modelo de elevación ni un umbral validado. Las inundaciones y los cuerpos de agua pueden impedir una instalación, pero requieren capas específicas de amenaza y exclusión hídrica. Las áreas protegidas necesitan zonificación ambiental verificable. La propiedad y el uso del suelo requieren información parcelaria y permisos. Los accesos necesitan geometrías viales y un criterio de costo o logística.

DECISIONES Y JUSTIFICACIÓN
No se implementaron porque el MVP prioriza la búsqueda espacial con las fuentes actualmente integradas. Cada factor necesita una fuente verificable, una regla y validación propia. Esto delimita el alcance, no demuestra irrelevancia.

La capacidad de conexión requiere datos técnicos de la red y un estudio eléctrico. La producción requiere un modelo fotovoltaico con temperatura, pérdidas y diseño del sistema. La economía requiere inversión, operación, tarifas y horizonte temporal. La justificación de estas omisiones es el alcance actual y la falta de integración y validación de esos datos o modelos. No se comprobó que fueran constantes, poco relevantes o innecesarios.

ALCANCE Y LÍMITES
Pendiente: falta integrar y validar un modelo de elevación. Inundaciones y agua: falta una máscara hídrica y de amenaza. Áreas protegidas: falta integrar zonificación ambiental. Propiedad, uso y accesos: faltan datos parcelarios, permisos y costos. Capacidad real: faltan capacidad disponible y un estudio eléctrico. Temperatura, inclinación, sombras y pérdidas requieren un modelo de producción fotovoltaica. Costos y tarifas requieren un modelo económico. Ninguna de estas omisiones autoriza construir en el candidato.

PUNTO PARA LA DEFENSA
¿El parque final puede caer en un sitio no apto? Sí. La exclusión implementada es urbana y no sustituye la validación hídrica, ambiental o parcelaria. Por eso presentamos candidatos para estudiar y no terrenos aprobados para construir.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
https://www.nlr.gov/gis/rev
https://atb.nrel.gov/electricity/2024/utility-scale_pv
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 8. Supuestos y restricciones

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Trabajamos con celdas de 500 metros y parques que crecen por bordes compartidos. Se excluyen las celdas que tocan la máscara urbana INDEC. La potencia es el área real por 31,3 MW/km² y el crecimiento se limita a 80 MW.

DESARROLLO DEL CONTENIDO
La grilla discretiza el territorio con celdas de 500 × 500 m. Cada celda completa ocupa 0,25 km². El parque crece incorporando vecinos por borde, de modo que forma un conjunto conectado. La máscara urbana procede de INDEC. Con buffer cero, se excluye la celda que toca o intersecta la máscara y se conserva la política de rellenar sus huecos internos. En el borde provincial se usa la superficie real del fragmento.

DECISIONES Y JUSTIFICACIÓN
500 m es la discretización del problema. La contigüidad garantiza un conjunto conectado. La exclusión urbana es conservadora, con buffer cero y relleno de huecos internos. La densidad de potencia procede del estudio NREL de uso de tierra: 7,9 acres/MWac de área total en grandes plantas FV, equivalentes aproximadamente a 31,3 MWac/km². Los 80 MW son un escenario experimental configurable.

La densidad de 31,3 MW/km² deriva de una referencia de uso total de tierra de grandes plantas FV: 7,9 acres/MWac. Convertir acres a km² e invertir el cociente da aproximadamente 31,279 MWac/km², redondeados a 31,3. Así, una celda completa aporta 0,25 × 31,3 = 7,825 MW. Diez celdas completas aportan 78,25 MW. Añadir una undécima completa produciría 86,075 MW y superaría el límite de 80.

ALCANCE Y LÍMITES
No existe calibración local de la densidad. El límite de 80 MW no corresponde a capacidad libre de ninguna ET. Los pesos 0,4/0,1/0,4/0,1 son iniciales y requieren análisis de sensibilidad. La exclusión urbana no cubre las restricciones hídricas o ambientales pendientes.

PUNTO PARA LA DEFENSA
¿Por qué 80 MW? Es un límite experimental configurable para estudiar crecimiento y aprovechamiento, no una capacidad certificada de una ET. La densidad es una referencia adoptada y requiere validación local, especialmente si se pretende diseñar una planta concreta.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
https://docs.nrel.gov/docs/fy13osti/56290.pdf
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 9. Representación de un parque

Tiempo orientativo: 1.3 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Un individuo contiene una celda semilla y una secuencia variable de genes enteros. El decodificador empieza por la semilla y usa cada gen para elegir una celda de la frontera. Así aparecen ubicación, forma y superficie.

DESARROLLO DEL CONTENIDO
El genotipo se compone de una semilla y una tupla de enteros de longitud variable. El fenotipo es el conjunto de celdas que resulta al decodificarlo. Al comenzar, la frontera contiene vecinos válidos de la semilla. En cada paso se ordena esa frontera de forma determinista y se aplica el entero módulo su tamaño. El resultado selecciona una posición de la lista. Si la celda cabe bajo el límite, se incorpora y se actualiza la frontera.

DECISIONES Y JUSTIFICACIÓN
La representación construye contigüidad por crecimiento. Una longitud variable permite explorar distintos tamaños. La secuencia guarda decisiones de crecimiento, no coordenadas de cada panel.

Con esta representación, la semilla modifica la ubicación y la secuencia modifica forma y tamaño. Un mismo entero puede seleccionar celdas distintas según el estado de la frontera. Si una incorporación concreta excede la capacidad se salta ese gen; si ninguna celda de la frontera cabe, el crecimiento termina. Esta lógica permite obtener un parque válido dentro de las reglas sin interpretar los genes como direcciones fijas.

ALCANCE Y LÍMITES
Un gen no es una dirección fija. Su significado depende de la frontera actual. Genes distintos pueden dar el mismo conjunto de celdas. La longitud del cromosoma puede exceder la cantidad de genes que realmente produce crecimiento.

PUNTO PARA LA DEFENSA
¿Por qué longitud variable? Porque el área también es una decisión de la búsqueda. La cantidad de genes no coincide siempre con la cantidad de celdas: algunos se omiten o quedan sin procesar.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/initialization.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 10. Fitness: cómo comparamos parques

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El fitness combina cuatro puntajes entre cero y uno. Más irradiación aumenta el puntaje solar, menos distancia aumenta la proximidad y más potencia aumenta el aprovechamiento del límite. Los pesos suman uno.

DESARROLLO DEL CONTENIDO
Cada parque obtiene cuatro puntajes. La suma ponderada es F = 0,40 × solar + 0,10 × proximidad a líneas + 0,40 × proximidad a ET + 0,10 × potencia. Para un mismo dataset, los puntajes tienen escala común y los pesos suman uno. Esto permite ordenar propuestas, aunque las métricas originales tengan unidades diferentes. El algoritmo selecciona según esta preferencia definida por el modelo.

DECISIONES Y JUSTIFICACIÓN
Una suma ponderada proporciona un orden explícito y fácil de auditar. Los pesos iniciales priorizan radiación y ET, con 40% cada una, y asignan 10% a líneas y 10% a potencia.

La suma admite compensaciones. Por ejemplo, un parque puede ganar en radiación y perder en proximidad a una estación. La exclusión urbana no entra en esta suma porque opera como restricción previa. Los pesos expresan prioridades iniciales del MVP. No proceden de un análisis económico ni de una validación de preferencias con especialistas. Una evaluación futura debería estudiar cuánto cambia la ubicación al modificar esas prioridades.

ALCANCE Y LÍMITES
Estos pesos no se validaron científicamente y no representan euros, producción real ni probabilidad de éxito. Un fitness alto significa buen desempeño bajo el escenario configurado. Los criterios pueden compensarse dentro de esta suma.

PUNTO PARA LA DEFENSA
¿Qué significa F = 0,7174? Es un puntaje relativo bajo este escenario. No significa 71,74% de eficiencia, probabilidad de viabilidad ni porcentaje de energía captada.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 11. Flujo de trabajo del proyecto

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Primero se obtienen las fuentes y se guarda la caché. Luego se validan geometrías y cobertura climática, se construye la grilla y sus vecinos, y se guarda un snapshot local. El AG carga ese dataset para buscar y exporta mapas, rankings e historial.

DESARROLLO DEL CONTENIDO
Las fuentes externas pasan por una etapa de acceso y caché. El procesamiento unifica referencias espaciales, recorta Santa Fe, construye la grilla, aplica la máscara urbana, vincula el clima y obtiene el grafo de vecinos. Luego guarda el conjunto preparado como snapshot en SQLite. La optimización carga ese snapshot, construye poblaciones, evalúa parques y exporta ranking, geometrías, mapa e historial.

DECISIONES Y JUSTIFICACIÓN
Separar preparación de optimización evita repetir descargas por individuo y permite ejecutar múltiples escenarios sobre el mismo conjunto de datos. El identificador del dataset y la configuración hacen trazable cada resultado.

Esta separación hace que una evaluación del AG no tenga que repetir una petición HTTP ni reconstruir toda la grilla. También distingue la caché de fuentes, que evita transferencias repetidas, del snapshot, que fija el dataset, y de la memoria del evaluador, que reutiliza resultados de un genotipo dentro de un escenario. Un cambio incompatible en la información espacial exige preparar un dataset nuevo antes de optimizar.

ALCANCE Y LÍMITES
El mapa puede usar teselas web, pero el bucle del AG trabaja sólo con datos locales. Cambios incompatibles de fuente o configuración espacial exigen reprocesar.

PUNTO PARA LA DEFENSA
¿El AG consulta la API en cada generación? No. Las consultas necesarias ocurren durante preparación. El bucle de búsqueda consume el dataset local. El mapa puede necesitar internet para cargar las teselas de fondo.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/main.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/preprocess.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/database/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 12. Parámetros de la nueva corrida

Tiempo orientativo: 0.8 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
La corrida del 6 de octubre usa semilla aleatoria 20261006, 50 individuos y 200 generaciones. Se mantienen 75% de cruce, 20% de mutación, dos élites y torneo de tres. El escenario es 80 MW, densidad 31,3 y pesos 0,4/0,1/0,4/0,1.

DESARROLLO DEL CONTENIDO
La semilla pseudoaleatoria 20261006 controla la secuencia de sorteos: semillas de parques, longitudes, torneos, cortes y operaciones de mutación. La población tiene 50 individuos. La generación cero evalúa los iniciales y después se completan 200 reemplazos. El cruce se intenta por pareja con probabilidad 0,75 y la mutación por hijo con probabilidad 0,20. Dos élites distintas se preservan. Cada torneo compara tres sorteos con reemplazo.

DECISIONES Y JUSTIFICACIÓN
Mantener el escenario y cambiar la semilla respecto de la presentación anterior produce un experimento nuevo comparable. Los parámetros se conservaron para demostrar el comportamiento del proyecto actual, no se eligieron mediante una búsqueda de hiperparámetros.

El resto del escenario conserva 80 MW de límite, 31,3 MW/km² de densidad y los cuatro pesos 0,40, 0,10, 0,40 y 0,10. La inicialización usa territorios de 50 km. El control de duplicados permite ocho reemplazos, la mutación efectiva cuatro intentos y el archivo conserva diez candidatos por territorio. El ranking territorial aplica separación adicional cero. Estos valores están registrados, junto con el dataset y las versiones efectivas.

ALCANCE Y LÍMITES
La semilla reproduce la secuencia pseudoaleatoria bajo el mismo dataset y entorno. Una sola corrida no mide robustez estadística. El criterio de parada es completar 200 generaciones, con evaluación inicial en generación cero.

PUNTO PARA LA DEFENSA
¿Por qué esos parámetros? Se conservaron los del proyecto para explicar su funcionamiento con una nueva semilla. No afirmamos que sean hiperparámetros óptimos. La reproducibilidad exige también el mismo dataset y un entorno compatible.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/config_corrida.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 13. Un cromosoma real y su crecimiento

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El padre A del cruce real tiene semilla 194480 y cuatro genes:2083272650,938200436,671673529,538685106. Mostrar tres pasos de decodificación: sólo semilla, primer par de genes y secuencia completa, que genera cinco celdas y 39,125 MW.

DESARROLLO DEL CONTENIDO
La figura muestra la decodificación de prefijos del padre A, cuya semilla es 194480. Con cero genes queda la semilla. Con los primeros dos genes se obtienen tres celdas. Con los cuatro genes se obtienen cinco. Los enteros son 2083272650, 938200436, 671673529 y 538685106. Son decisiones de crecimiento que se aplican sobre fronteras sucesivas. La secuencia completa genera 125 ha y 39,125 MW estimados.

DECISIONES Y JUSTIFICACIÓN
Seguir prefijos de un cromosoma permite ver cómo una secuencia se transforma en un parque sin inventar una geometría. El orden de la frontera es determinista y cada selección usa gen módulo cantidad de vecinos candidatos.

Se mantiene la misma ventana espacial en los tres dibujos para que el crecimiento sea comparable. La semilla aparece en dorado y las incorporaciones en verde azulado. Los dibujos proceden de las celdas reales obtenidas por el decodificador. Este padre participó en un evento que produce la generación dos y no se lo identifica como ganador global. Seguir prefijos sirve para enseñar la representación antes de mostrar la evolución poblacional.

ALCANCE Y LÍMITES
Estos son pasos de crecimiento dentro de un individuo, no generaciones del AG. El ejemplo se observó como padre del evento de cruce que produce la generación 2, no se afirma que fuera el mejor de la población.

PUNTO PARA LA DEFENSA
¿Cada imagen es una generación? No. Son pasos internos de construcción del mismo individuo. Las generaciones comparan poblaciones completas y pueden cambiar de líder y ubicación.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 14. Población inicial y selección

Tiempo orientativo: 1.1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
La inicialización recorre territorios ocupados de 50×50 km en orden aleatorio y escoge una semilla dentro de cada uno. Genera longitudes de secuencia aleatorias y evalúa 50 parques. En cada torneo extrae tres candidatos con reemplazo y conserva el de mayor fitness.

DESARROLLO DEL CONTENIDO
La población inicial no se concentra en una única zona: el muestreador agrupa semillas por territorios ocupados de 50 × 50 km y recorre esos grupos en un orden aleatorio. Dentro de cada territorio escoge una semilla y sortea una longitud de genes. En la selección, cada torneo extrae tres índices de la población con reemplazo y elige el que tiene mayor fitness. El mismo candidato puede aparecer más de una vez o ganar varios torneos.

DECISIONES Y JUSTIFICACIÓN
El muestreo por territorios favorece cobertura espacial en lugar de concentrar todas las semillas en una zona. El torneo ejerce presión selectiva conservando azar. Dos élites distintas por conjunto de celdas pasan directamente a la próxima población.

El muestreo territorial busca ampliar cobertura inicial, mientras que el torneo concentra reproducción en candidatos favorables sin eliminar el azar. El elitismo conserva dos parques distintos por su conjunto de celdas. La figura del torneo es conceptual y no atribuye puntajes inventados a una ejecución. Los cruces y mutaciones que siguen sí se registraron en la corrida. Es importante separar el mecanismo general de un evento concreto.

ALCANCE Y LÍMITES
Cobertura equilibrada no es un muestreo uniforme por superficie. El gráfico ilustra el mecanismo, no un torneo observado. Los ejemplos de operadores de las siguientes slides sí son eventos registrados. Los parámetros de torneo y elitismo no se calibraron para demostrar optimalidad.

PUNTO PARA LA DEFENSA
¿Selección significa quedarse sólo con los mejores 50? No. Los hijos se eligen mediante torneos, dos élites se preservan y los operadores producen nuevas propuestas. El reemplazo combina conservación y exploración.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/initialization.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/selection.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 15. Cruce de secuencias: evento real

Tiempo orientativo: 1.3 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
En la generación 2, el padre A tiene semilla 194480 y cuatro genes; el B tiene semilla 78089 y seis. El cruce corta A tras el tercer gen y B tras el cuarto. El hijo A conserva la semilla A y combina A 1,A 2,A 3,B 5,B 6. Pasa de cinco a seis celdas y su fitness aumenta de 0,5273 a 0,5371.

DESARROLLO DEL CONTENIDO
El padre A tiene cuatro genes y semilla 194480. El padre B tiene seis y semilla 78089. En este evento de la generación dos, el corte de A es tres y el de B es cuatro. El hijo A conserva A1, A2 y A3 y agrega B5 y B6. Por lo tanto, su secuencia tiene cinco genes y mantiene la semilla A. Al decodificarse, produce seis celdas, 150 ha y 46,95 MW. Su fitness es 0,537136 frente a 0,527348 del padre A.

DECISIONES Y JUSTIFICACIÓN
El cruce de prefijo y sufijo admite secuencias de longitudes diferentes. Conservar la semilla del prefijo da un inicio definido para el nuevo decodificado. La probabilidad de 75% se aplica por pareja.

Este operador es un cruce de secuencias con cortes independientes. No es cruce aritmético ni promedia coordenadas. Admite longitudes diferentes y el código también produce el hijo recíproco: prefijo de B y sufijo de A. Los alias simplifican el dibujo; las secuencias completas quedan al final de estas notas y en el apoyo técnico. La geometría se construye de nuevo sobre la semilla elegida.

ALCANCE Y LÍMITES
Los genes del otro padre se reinterpretan en la frontera del hijo, no transportan celdas físicas de B. El código también crea un hijo recíproco. Este evento mejoró al padre A, pero el cruce no garantiza mejora.

PUNTO PARA LA DEFENSA
¿El hijo copia terreno del padre B? No. Copia enteros que vuelven a interpretarse en su propia frontera. Este evento mejora al padre A, pero no demuestra que todo cruce mejore ni que el hijo supere a ambos padres.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/crossover.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

Genes A: [2083272650,938200436,671673529,538685106]
Genes B: [949832610,786802762,1753680651,1864815592,1486342001,1918520519]
Genes hijo A: [2083272650,938200436,671673529,1486342001,1918520519]

## 16. Mutación: una celda nueva

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
En la generación 1, el individuo de semilla 23162 añade el gen 7 a su secuencia. El parque crece de 7 a 8 celdas, de 54,775 a 62,6 MW. El fitness pasa de 0,5174 a 0,5273.

DESARROLLO DEL CONTENIDO
El evento mostrado ocurre en la generación uno y conserva la semilla 23162. La secuencia original tiene seis genes y decodifica siete celdas. Se añade el entero 7, que selecciona una incorporación compatible con el límite. La nueva celda es 23405. El parque pasa de 175 a 200 ha y de 54,775 a 62,6 MW. El fitness aumenta de 0,517387 a 0,527346. La comparación usa la misma ventana espacial para reconocer el cambio.

DECISIONES Y JUSTIFICACIÓN
La mutación efectiva elige al azar entre operaciones aplicables: añadir un gen que permita crecer, borrar el último crecimiento aceptado, cambiar un gen aceptado o cambiar la semilla. Reintenta hasta cuatro veces buscando un cambio de celdas.

La mutación efectiva trabaja con operaciones aplicables al parque actual. Puede añadir crecimiento, recortar la secuencia antes del último crecimiento aceptado, cambiar un gen aceptado o sustituir la semilla. Si una propuesta no cambia las celdas, intenta otra, hasta cuatro veces. El evento de la figura funcionó en el primer intento. La operación de adición puede usar un entero pequeño porque selecciona una posición compatible de la frontera.

ALCANCE Y LÍMITES
20% es probabilidad por hijo, no cantidad fija de mutaciones. Un cambio efectivo modifica el parque, pero no implica mejora del fitness. En el caso mostrado hubo un intento. Dorado señala semilla y nueva celda.

PUNTO PARA LA DEFENSA
¿El 20% asegura cambios en el 20% de la población? Es una probabilidad por hijo. El número observado varía y un evento puede agotar sus intentos. «Efectiva» significa cambiar la geometría, no mejorar el puntaje.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/mutation.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

Genes antes: [1904438052,1615252215,1128450819,495451334,1316918323,1577479957]
Genes después: [1904438052,1615252215,1128450819,495451334,1316918323,1577479957,7]

## 17. Ciclo de una generación

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El ciclo evalúa los 50 parques, conserva dos élites, selecciona hijos por torneo, cruza parejas, muta hijos y controla duplicados antes de formar la próxima población. Repite hasta 200 generaciones.

DESARROLLO DEL CONTENIDO
Una generación comienza evaluando la población y actualizando el archivo de candidatos. Después se preservan dos élites de geometrías distintas y se seleccionan los restantes padres por torneos. Se cruzan parejas según la probabilidad configurada y se consideran mutaciones en los hijos. Antes de agregarlos se compara su conjunto de celdas con los ya presentes. Un duplicado activa nuevos muestreos hasta el límite de intentos.

DECISIONES Y JUSTIFICACIÓN
El elitismo conserva soluciones buenas. Cruce y mutación exploran otras configuraciones. El control de duplicados intenta evitar repetir el mismo conjunto de celdas, con hasta ocho reemplazos por muestreo.

Las élites siguen una vía directa a la próxima población y no atraviesan cruce o mutación. La figura resume el ciclo sin dibujar esa bifurcación en detalle. El archivo conserva hasta diez candidatos por territorio visitado para mantener alternativas, además del líder. La parada se produce al completar 200 generaciones. Si se agotan los intentos de reemplazar un duplicado, el código acepta la propuesta, por lo que la diversidad perfecta no está garantizada por definición.

ALCANCE Y LÍMITES
Las élites pasan directamente a la nueva población, sin aplicarles los operadores. El flujo es conceptual y no expresa esa bifurcación literalmente. Si los reintentos se agotan se conserva el candidato. Además del mejor actual, un archivo conserva hasta 10 candidatos por territorio.

PUNTO PARA LA DEFENSA
¿Qué evita perder una solución buena? El elitismo preserva candidatos en la población y el archivo mantiene alternativas históricas. Esto protege resultados observados, pero no acredita óptimo global.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 18. Evolución de la nueva corrida

Tiempo orientativo: 1.3 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El mejor fitness crece de 0,6384 a 0,7174. La mejora relativa del puntaje es 12,4%. El historial registra 201 evaluaciones de población, de 0 a 200. La búsqueda visitó 6309 parques distintos.

DESARROLLO DEL CONTENIDO
La curva del mejor muestra el puntaje máximo de cada población y la media resume a sus 50 integrantes. El salto inicial refleja mejoras tempranas y luego los incrementos se vuelven menores. La media fluctúa porque siguen entrando descendientes y nuevos muestreos. El mejor empieza en 0,6383617 y termina en 0,7174265. El historial contiene 201 filas: evaluación inicial y generaciones uno a 200. Se visitaron 6309 conjuntos de celdas distintos.

DECISIONES Y JUSTIFICACIÓN
Mostrar el mejor y la media permite distinguir progreso del líder y comportamiento de la población. Conservar el historial y métricas por generación permite auditar la búsqueda.

La mejora relativa del puntaje es aproximadamente 12,4%, calculada como (F final / F inicial − 1) × 100. Se aplica al fitness compuesto, no a energía, eficiencia o rentabilidad. Los límites de normalización permanecen fijos, de modo que la curva compara la misma escala durante toda la corrida. Una meseta indica que esta ejecución encontró pocas mejoras recientes, pero puede deberse a la dinámica de búsqueda y al presupuesto disponible.

ALCANCE Y LÍMITES
La mejora del fitness no es un aumento porcentual de producción. Una meseta no prueba óptimo global. Las élites reducen el riesgo de perder el mejor candidato y no eliminan la variabilidad entre semillas.

PUNTO PARA LA DEFENSA
¿La curva demuestra convergencia al óptimo? Demuestra progreso observado y estabilización bajo estos parámetros. Para discutir robustez y calidad relativa hacen falta otras semillas y métodos de referencia.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/history.csv
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 19. Mejor candidato encontrado

Tiempo orientativo: 1.2 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El mejor parque tiene 10 celdas completas,2,5 km² o 250 ha y 78,25 MW estimados. Su irradiación media es 1.896,0 kWh/m²/año. Está a 14,9 m de la línea disponible más próxima y a 175,1 km de Santo Tomé, la ET de referencia más cercana.

DESARROLLO DEL CONTENIDO
El parque líder contiene diez celdas completas conectadas, con una forma irregular que surge de los genes. Su área es 2,5 km², equivalentes a 250 ha. Multiplicar por 31,3 da 78,25 MW. Aprovecha el 97,8125% del límite de 80 MW. La irradiación media estimada es 1895,958 kWh/m²/año. Desde su centroide, la línea más próxima está a unos 14,9 m y la estación de referencia más cercana es Santo Tomé, a unos 175,1 km.

DECISIONES Y JUSTIFICACIÓN
La combinación favorece la irradiación máxima del dataset y proximidad a una línea. El score de potencia es 78,25/80=0,9781. En conjunto produce fitness 0,7174.

El score solar es 1, el de líneas aproximadamente 0,999645, el de ET 0,299124 y el de potencia 0,978125. Sus aportes ponderados son aproximadamente 0,400000, 0,099964, 0,119650 y 0,097813, que suman 0,717427. Esta descomposición explica por qué el modelo favorece el sitio pese a la gran distancia a una ET: radiación y línea compensan parcialmente la menor proximidad a estaciones.

ALCANCE Y LÍMITES
La gran distancia a la ET muestra una compensación de criterios y el efecto de trabajar con sólo cuatro estaciones. La distancia de 14,9 m se refiere al centroide y geometría de la línea, no a una traza viable. Deben revisarse las variables de viabilidad pendientes antes de interpretar el candidato como sitio construible.

PUNTO PARA LA DEFENSA
¿Es una recomendación de construcción? Es el mejor candidato de esta corrida y escenario. Deben revisarse capacidad de red, agua, ambiente y suelo. Los 14,9 m no representan longitud de un cableado diseñado ni costo de conexión.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/ranking.csv
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 20. Alternativas territoriales

Tiempo orientativo: 0.8 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
El ranking general ordena por fitness y puede contener variantes superpuestas. El ranking territorial selecciona hasta cinco alternativas sin superposición desde el archivo de candidatos. El mapa muestra sus centroides.

DESARROLLO DEL CONTENIDO
El ranking general presenta los candidatos con mayor fitness y puede contener variaciones de un mismo entorno. El territorial recorre el archivo ordenado y selecciona alternativas compatibles sin superposición. La configuración no exige distancia adicional, por lo que varias alternativas pueden estar próximas. En el mapa provincial se muestran centroides, con el líder en dorado y el grupo de alternativas dos a cinco en el sur.

DECISIONES Y JUSTIFICACIÓN
Separar ambos rankings entrega opciones espaciales además de variaciones del líder. La separación adicional configurada es 0 km: se prohíbe solapar, pero pueden existir alternativas próximas.

La comparación de puntajes es útil para reconocer que la segunda opción no tiene que ser sólo una modificación mínima del líder. Sin embargo, las alternativas proceden de un archivo limitado y de los territorios visitados. No se garantizan los mejores cinco sitios de toda la provincia ni una cobertura exhaustiva. A escala provincial los centroides ayudan a ubicar los parques, mientras que sus dimensiones y posibles superposiciones se revisan en las geometrías exportadas.

ALCANCE Y LÍMITES
Las alternativas territoriales dependen del archivo acotado, no de una búsqueda exhaustiva. El mapa de la diapositiva ubica centroides y no muestra dimensiones de los parques a escala provincial.

PUNTO PARA LA DEFENSA
¿Por qué alternativas cercanas? La separación configurada es cero kilómetros adicionales. Se evita solapar los polígonos y no se impone dispersión regional. Un escenario con separación positiva cambiaría la selección territorial.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/ranking.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/ranking_territorial.csv
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 21. Conclusiones y próximos pasos

Tiempo orientativo: 1.4 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
La corrida demuestra que el AG construye parques conectados y mejora el puntaje bajo un escenario explícito. El proyecto entrega candidatos, un mapa y un historial reproducible. El resultado también muestra que buenas puntuaciones pueden coexistir con limitaciones de conexión.

DESARROLLO DEL CONTENIDO
La ejecución confirma que el sistema construye geometrías conectadas, las evalúa bajo criterios explícitos y registra mejoras respecto de la población inicial. El aporte incluye la integración de fuentes, el procesamiento territorial, la representación por crecimiento y la persistencia de resultados. El líder de 250 ha ilustra el comportamiento del escenario y también una limitación: proximidad a una línea y gran distancia a las ET consideradas pueden coexistir en un candidato favorecido.

DECISIONES Y JUSTIFICACIÓN
La principal contribución es integrar crecimiento espacial, criterios comparables y trazabilidad de búsqueda. Separar la preparación de datos permite ensayar nuevas semillas y parámetros.

Las conclusiones deben corresponder a lo que se observó. No se midió rentabilidad, producción real ni capacidad disponible de red. Tampoco se demostró que el AG supere otras búsquedas. Para avanzar conviene integrar exclusiones territoriales faltantes, revisar la cobertura de infraestructura, ampliar el clima y repetir varias semillas. El análisis de sensibilidad de pesos permite estudiar si la preferencia depende fuertemente de prioridades arbitrarias.

ALCANCE Y LÍMITES
No se demostró optimalidad ni robustez con una sola corrida. Próximos pasos: integrar restricciones territoriales faltantes y capacidad de red, ampliar la referencia climática, repetir semillas, variar pesos y comparar con una búsqueda aleatoria bajo igual presupuesto. Modelar producción y economía requiere trabajo adicional.

PUNTO PARA LA DEFENSA
¿Cuál sería una validación siguiente? Comparar varias semillas y una búsqueda aleatoria con igual cantidad de evaluaciones, examinando fitness y métricas físicas. Después incorporar estudios territoriales y eléctricos sobre los candidatos.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/README.md
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/history.csv
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 22. Detalle técnico: normalización

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Para irradiación se utiliza min-max: (x−mín)/(máx−mín). Para distancias se invierte:1−min-max. Los límites provienen de todas las celdas válidas y permanecen fijos en la corrida. La potencia se normaliza conP/80 MW.

DESARROLLO DEL CONTENIDO
El min-max solar ubica el mínimo de las celdas válidas en cero y el máximo en uno. Para distancia se invierte el resultado, de modo que lo más próximo obtiene mayor preferencia. En cada parque se aplican esos límites fijos al promedio de irradiación y a las distancias de su centroide. Los valores se recortan al intervalo de cero a uno. Si un criterio tiene mínimo y máximo iguales, todos reciben uno porque no discrimina entre alternativas.

DECISIONES Y JUSTIFICACIÓN
Fijar los límites evita que cambiar la población altere la escala de comparación. Las métricas del parque usan irradiación media ponderada por área y distancias desde su centroide. Se recorta a[0,1]. Si mínimo y máximo coinciden, el criterio asigna 1 a todos.

La potencia sigue otra normalización: instalada / límite experimental. En esta corrida, 78,25 / 80 = 0,978125. Usar referencias fijas permite comparar generaciones sin cambiar la escala cuando la población cambia. Los límites provienen de los datos válidos del snapshot, no de los mejores individuos. Por ello, cambiar el dataset o el escenario puede alterar el significado de un mismo fitness y exige analizar los componentes originales.

ALCANCE Y LÍMITES
No usamos z-score ni renormalizamos por generación. Estos puntajes son relativos al dataset y escenario. No comparar directamente fitness entre escenarios de distinto límite sin analizar sus componentes.

PUNTO PARA LA DEFENSA
¿Por qué no z-score? La implementación elige una escala acotada y orientada a preferencia para combinar criterios. Es una decisión del modelo. No se recalculan media ni desvío por generación para puntuar.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 23. Implementación y bibliotecas

Tiempo orientativo: 0.8 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Python organiza el pipeline y el AG propio. NumPy gestiona azar y cálculos, pandas los registros, GeoPandas y Shapely las geometrías y distancias, y PyProj los sistemas de coordenadas. xarray,Zarr,Dask y fsspec leen el clima. SQLAlchemy y SQLite persisten datasets y corridas. Folium y HTML presentan resultados.

DESARROLLO DEL CONTENIDO
Python conecta los módulos del proyecto. NumPy aporta el generador pseudoaleatorio y operaciones numéricas; pandas organiza métricas y tablas. GeoPandas maneja datos geográficos, Shapely realiza operaciones de geometría y PyProj transforma coordenadas. xarray y Zarr permiten acceder al almacén climático, con Dask y fsspec para la lectura. SQLAlchemy administra la interacción con SQLite. Folium y las gráficas HTML presentan los resultados.

DECISIONES Y JUSTIFICACIÓN
Separar módulos de datos, procesamiento, optimización y visualización permite cambiar una fuente o probar un escenario sin mezclar acceso remoto con evaluación. Pydantic valida configuración y requests realiza los accesos HTTP vectoriales.

El algoritmo genético se implementa en módulos propios de inicialización, selección, cruce, mutación y evaluación. Pydantic valida parámetros y requests participa en los accesos HTTP vectoriales. Esta división facilita detectar en qué etapa aparece un problema: una fuente incompleta no es un fallo del operador de cruce. Los metadatos conservan versiones efectivas de NumPy, pandas, Shapely, GeoPandas y PyProj para interpretar y reproducir la corrida.

ALCANCE Y LÍMITES
El AG no depende de DEAP. La librería específica de dibujo de gráficas es JavaScript embebido del proyecto. El mapa puede requerir teselas de OpenStreetMap. Las versiones efectivas de las bibliotecas principales están en los metadatos de la corrida.

PUNTO PARA LA DEFENSA
¿Usamos una biblioteca de AG como DEAP? No. Los operadores espaciales pertenecen al código del proyecto. Las bibliotecas geoespaciales y numéricas proveen operaciones de apoyo, no definen por sí mismas la búsqueda.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/requirements.txt
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/main.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/genetic_algorithm.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/pipeline/reporting.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 24. Fuentes, peticiones y manejo de datos

Tiempo orientativo: 1 minutos. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
IGN se obtiene como ZIP con shapefile. INDEC usa GET WFS paginado, con 500 registros por página. Las líneas usan CKAN datastore_search paginado y las ET un CSV directo. El clima usa lectura de bloques ARCO Zarr. Se valida la respuesta y se conserva la caché antes de preparar el dataset.

DESARROLLO DEL CONTENIDO
Los formatos de entrada requieren estrategias diferentes. IGN ofrece un ZIP con shapefile y referencia espacial. INDEC usa GetFeature WFS 2.0.0 con páginas de 500 registros, startIndex creciente y salida GeoJSON. Se controlan total, páginas, IDs y consistencia para evitar descargar una capa parcial. Las líneas se obtienen mediante CKAN datastore_search y las ET por descarga CSV. El clima se lee del almacén ARCO Zarr autorizado con una credencial de Copernicus.

DECISIONES Y JUSTIFICACIÓN
WFS requiere controles de IDs, páginas y total para evitar capas incompletas. El clima exige horas únicas y finitas para cada mes. La caché reduce transferencias repetidas. SQLite conserva snapshots de contenido y la corrida guarda semilla, configuración, versiones y límites de normalización.

La caché conserva material obtenido y el procesamiento genera el snapshot local. La huella de las fuentes y el identificador del dataset permiten reconocer cambios relevantes. El código comprueba cobertura mensual y no inventa valores para completar una fuente faltante. La corrida registra configuración, semilla, límites y versiones. La credencial permanece en el entorno y se excluye de los resultados. La exclusión urbana sigue activa incluso al desactivar algún criterio de fitness.

ALCANCE Y LÍMITES
La credencial de Copernicus se toma del entorno y se excluye de los resultados. Si falta una fuente activa, el pipeline se detiene. El código no inventa ET ni valores solares. La exclusión urbana siempre permanece activa.

PUNTO PARA LA DEFENSA
¿Qué ocurre si cambia una fuente? Se debe validar y reprocesar cuando el cambio sea incompatible. Si falta una fuente requerida, la ejecución informa el problema y se detiene en lugar de reemplazarla por datos ficticios.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/config.yaml
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/api/indec.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/api/datos_gob_ar.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/climate/arco.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/database/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 25. Apoyo: límites y valores del escenario

Tiempo orientativo: apoyo para preguntas. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Consultar durante preguntas los rangos fijos de normalización y principales supuestos.

DESARROLLO DEL CONTENIDO
Esta tabla permite auditar las referencias numéricas de la corrida. La irradiación va aproximadamente de 1795,942 a 1895,958 kWh/m²/año. La distancia a línea tiene un mínimo de unos 0,000006 km y máximo de 41,857 km. La distancia a ET va de 0,088 a 249,735 km. Esos límites se calcularon usando todas las celdas válidas. La potencia usa 80 MW como denominador y 31,3 MW/km² como densidad constante.

DECISIONES Y JUSTIFICACIÓN
Estos valores proceden directamente de optimization_run.json y no se recalcularon a partir de la población.

Los mínimos pequeños son distancias geométricas entre centroides y elementos de la capa. No implican precisión equivalente de levantamiento ni acceso inmediato a la infraestructura. Los números visibles están redondeados para lectura, mientras que el evaluador usa mayor precisión. Esta diapositiva no forma parte del recorrido principal y sirve para responder cómo se obtuvieron los puntajes de una propuesta.

ALCANCE Y LÍMITES
Los rangos reflejan el dataset utilizado. No son valores universales.

PUNTO PARA LA DEFENSA
¿Por qué son límites del dataset y no del ranking? Porque así el criterio mantiene la misma referencia durante la búsqueda. El ranking es una salida de la evaluación y no define su escala.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/results/spatial/run-20261006T231108-428e45c4/optimization_run.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 26. Apoyo: genes del cruce observado

Tiempo orientativo: apoyo para preguntas. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Los alias del diagrama corresponden a los enteros indicados en esta tabla. La semilla del hijo A es 194480.

DESARROLLO DEL CONTENIDO
La tabla muestra los enteros que se ocultan detrás de los alias A1–A4 y B1–B6 del diagrama. Con corte A igual a tres, se conservan los primeros tres enteros de A. Con corte B igual a cuatro, se toma B desde su quinto entero hasta el final. La concatenación produce cinco genes. El hijo A conserva la semilla 194480 y el hijo recíproco mantiene 78089. No se promedian los valores ni se mezclan las coordenadas de las semillas.

DECISIONES Y JUSTIFICACIÓN
La tabla permite auditar el ejemplo sin cargar la explicación principal con enteros largos. Los cortes son 3 y 4.

Los enteros grandes provienen del generador aleatorio dentro del dominio permitido. Su magnitud no expresa metros, potencia ni calidad. El decodificador usa el resto de dividir cada entero por el tamaño de la frontera actual. Por eso cambiar una decisión temprana modifica la frontera y puede cambiar el efecto de genes posteriores, aunque se conserven los mismos enteros. La tabla documenta un evento real y permite reproducir el ejemplo.

ALCANCE Y LÍMITES
Los enteros se interpretan mediante módulo sobre la frontera actual. Un alias no identifica una dirección fija.

PUNTO PARA LA DEFENSA
¿Por qué usar alias en el cuerpo? Porque la estructura del cruce se entiende mejor con pocos símbolos. Los valores completos quedan disponibles para auditar el evento sin saturar la diapositiva principal.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/crossover.py
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

## 27. Apoyo: mejores parques por generación

Tiempo orientativo: apoyo para preguntas. El desarrollo siguiente sirve para estudio y consulta. No es necesario leerlo completo durante la exposición.

GUION ESENCIAL
Comparar formas del mejor candidato en generaciones 0,50 y 200. Los tres son resultados reales de la nueva corrida.

DESARROLLO DEL CONTENIDO
Las figuras muestran al mejor de la población en generaciones cero, 50 y 200. Sus semillas son 157900, 79617 y 265259 y sus fitness aproximadamente 0,6384, 0,6907 y 0,7174. El conjunto de celdas cambia de forma y ubicación. Los dibujos son ventanas locales centradas en cada parque y no deben interpretarse como si todos ocuparan el mismo terreno. La semilla aparece en dorado dentro de cada conjunto.

DECISIONES Y JUSTIFICACIÓN
Esta comparación ilustra cambios en el liderazgo de la población.

La comparación ilustra cómo cambia el liderazgo, no una relación directa entre padre e hijo. Para seguir una genealogía concreta habría que registrar y enlazar todos sus eventos. En el líder final hay 32 genes, pero sólo los primeros nueve producen incorporaciones antes de detener el crecimiento. El resultado tiene diez celdas contando la semilla. Esta diferencia muestra por qué el tamaño genético puede crecer sin aumentar la superficie del parque.

ALCANCE Y LÍMITES
No es una genealogía: distintos líderes pueden proceder de diferentes padres y ubicaciones. El líder final conserva 32 genes, de los cuales 9 producen crecimiento, y termina con 10 celdas.

PUNTO PARA LA DEFENSA
¿Los genes restantes son error? El decodificador puede detenerse cuando ninguna celda de la frontera cabe bajo el límite. Los genes posteriores quedan sin procesar. Son parte del genotipo, pero no modifican ese fenotipo en este escenario.

FUENTES
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/tmp/presentation_build/defensa_nueva/evidence.json
C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026/src/optimization/spatial.py
Corrida: C:\Users\creis\OneDrive\Escritorio\AG-ParqueSolar-2026\results\spatial\run-20261006T231108-428e45c4
Semilla: 20261006. Dataset: 6faf11ae1cb9762cc5a86283208eeb1998185d43777af5bec977a12d3325117e
Cartografía provincial: contorno oficial IGN conservado. Los eventos de cruce y mutación corresponden a la corrida nueva. Las demás ilustraciones son conceptuales.

