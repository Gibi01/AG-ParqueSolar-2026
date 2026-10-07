# Verificación del experimento

- [x] Preparar ejecutor independiente y prueba de comparación pareada y conteo geográfico.
  Aceptación: diferencias por semilla, no por posición; presencia por corrida sin duplicados.
  Verificación: unittest focalizado. Dependencia: ninguna.
- [x] Ejecutar 20 corridas sobre el mismo dataset y exportar resultados individuales.
  Aceptación: 201 generaciones registradas, igual población inicial por pareja, parques factibles.
  Verificación: validaciones del ejecutor y manifiesto completo. Dependencia: ejecutor validado.
- [x] Analizar fitness y recurrencia geográfica; generar mapas, curvas e informe.
  Aceptación: denominadores explícitos, presupuesto observado, conclusión acorde a evidencia.
  Verificación: revisión de CSV y figuras; suite de regresión. Dependencia: corridas completas.

Resultados: `results/experiments/crossover-20261006-10-pares/informe.md`.
Pruebas focalizadas: 4/4. Suite completa: 79/79 fuera del aislamiento
(el primer intento encontró permisos insuficientes en directorios temporales).
Figuras inspeccionadas visualmente; manifiesto con 20 corridas completas.
