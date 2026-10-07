# Comparación a 100 y 150 generaciones

Diseño fijado antes de ejecutar: 10 semillas 301–310, crossover competitivo actual (0,75) frente a sin crossover (0), presupuestos 100 y 150 generaciones. Dataset guardado y demás parámetros del experimento previo; no modificar el AG. Ejecutar condiciones secuencialmente para medir tiempos comparables, con salvedades por caché/sistema operativo.

- [x] Ejecutar 40 corridas y verificar manifiestos completos, mismos hashes iniciales y prefijos idénticos a las historias anteriores de 200 generaciones (excepto tiempo de reloj).
- [x] Comparar fitness pareado, victorias, IC bootstrap y prueba bilateral por signos con helpers existentes; contrastes exploratorios sin corrección por multiplicidad.
- [x] Medir convergencia: generaciones hasta fitness 0,70 y 0,72 (umbrales descriptivos fijados aquí, no criterios de viabilidad física), incluyendo no alcanzados sin omitirlos; presupuestos comunes de solicitudes y decodificaciones.
- [x] Generar CSV, JSON, informe y figura; revisar consistencia y gráfico.

Los cortes de 100 y 150 son puntos de la misma trayectoria con la misma semilla: no se cuentan como 20 semillas independientes. La muestra ya se usó en validación anterior: este análisis es exploratorio, no una nueva validación independiente. No sobrescribir otros planes o resultados.

Resultado: 100 generaciones −0,000958 (5/10 victorias); 150 +0,005240 (7/10), ambos IC de fitness incluyen cero. Mayor costo con crossover; sin ventaja media bajo presupuestos comunes. Cinco tests de los helpers pasan; comprobaciones integrales de datos pasan; gráfico revisado visualmente; sin cambios al AG.
