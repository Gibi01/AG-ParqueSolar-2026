# Inicialización × crossover: 80 corridas

Diseño fijado antes de ver resultados: semillas nuevas 501–520, población 50, 150 generaciones; inicialización territorial estratificada (actual) y uniforme sobre todas las celdas semilla válidas, cada una con crossover competitivo 0,75 y sin crossover. Configuración guardada del estudio original, sin compactación ponderada (peso 0); dataset idéntico. Mantener genes aleatorios, archivo territorial y muestreo territorial de reemplazos durante todas las generaciones. Sólo cambian las primeras 50 llamadas al sampler de cada corrida.

El AG de producción y los cambios de compactación presentes en el workspace no se modifican. Usar un envoltorio experimental del runner existente. Ejecutar secuencialmente; tiempos descriptivos sujetos a carga del equipo. Guardar hashes, poblaciones iniciales, historias, ganadores y alternativas.

- [x] Verificar con tests que el muestreo uniforme admite repetir sectores inicialmente y que después vuelve al territorial; reproducibilidad; parches limitados por context managers.
- [x] Ejecutar 20 corridas por condición (80 total), verificar poblaciones iniciales idénticas con/sin cruce dentro de cada método, capacidad y contigüidad con runner existente.
- [x] Medir diversidad inicial (sectores 50 km ocupados, distancias entre semillas, parques distintos y fitness inicial).
- [x] Análisis principal: diferencia pareada con−sin en cada método y la interacción (delta uniforme−delta territorial) a 150 generaciones, IC bootstrap 95 % y prueba exacta por signos. Evaluar umbrales 0,70/0,72 e historias a 100/150 como descriptivos.
- [x] Repetir contrastes a presupuestos comunes de solicitudes y decodificaciones a las cuatro condiciones; documentar límites de checkpoints por generación.
- [x] Generar informe español, CSV/JSON y figura; verificar integridad, revisar gráficos y tests.

Bootstrap 20.000 muestras, semilla fija. Interacción principal; demás contrastes exploratorios sin corrección por multiplicidad. Veinte semillas no garantizan potencia suficiente; no ajustar operador ni método después de observar resultados. El mismo número aleatorio entre métodos no supone poblaciones idénticas; sí se exige coincidencia entre las variantes de cruce del mismo método.

Resultado: delta sectores +0,008658 (16/20 victorias), delta uniforme +0,000017 (9/20); interacción −0,008641, IC 95 % [−0,016092, −0,001750], p=0,02877. Inicialización aleatoria reduce cobertura media de 50 a 33,7 sectores. No ventaja concluyente de eficiencia por sectores; contraste uniforme negativo bajo ambos presupuestos comunes. 93 tests pasan (suite completa fuera del sandbox por permisos temporales); verificaciones integrales de manifiestos, huellas, hashes de las 2.000 entradas iniciales e historias pasan.
