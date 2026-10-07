# Revisión del cambio

- Corrección: las propuestas usan el decodificador existente. Compactar genes
  saltados/no procesados no cambia la frontera ni las celdas del padre. Los cortes
  comunes y la competencia por fitness están acotados a tres intentos.
- Contrato: hijos con la misma semilla correspondiente y fitness al menos igual
  al padre antes de mutación/reemplazo. Padres inmutables; RNG inyectado reproducible.
- Pruebas: rechazo de un hijo peor, mejora real por recombinación sin mutación,
  compactación con límite de capacidad, cadenas vacías y repetibilidad.
- Integración: CLI y salida de metadatos comprobados en la suite espacial; versión
  4 y nombre del operador distinguen resultados nuevos de históricos.
- Rendimiento: mayor costo de evaluación observado; no se presenta como mejora
  de eficiencia con presupuesto fijo. No hay nuevos accesos de red en el AG.
- Trazabilidad: mismos datos e inicio por pareja; controles sin cruce idénticos,
  hashes del código y resultados completos, sin eliminar casos desfavorables.
- Alcance: cambio mínimo del bucle del AG; se conservó el desvío estándar y otras
  modificaciones locales anteriores. No se alteraron fitness, grilla, clima,
  mutación, elitismo, capacidad ni configuración principal.
- Incertidumbre: validación independiente de diez semillas con IC que incluye cero;
  resultado prometedor de calidad, no demostración de superioridad universal.

Verificación final: 84/84 pruebas aprobadas, 60 condiciones comparables entre
20 semillas y tres variantes, poblaciones iniciales idénticas por pareja,
controles sin crossover reproducidos exactamente y figuras inspeccionadas.
