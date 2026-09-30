# Plan de implementacion: capacidades MVA de estaciones transformadoras

## Resumen

La capa local contiene 4 estaciones transformadoras unicas dentro de Santa Fe. La fuente ya informa `potencia_instalada_mv` para todas: SANTO TOME (900), RIO CORONDA (0), ROSARIO OESTE (1200) y ROMANG (150). Por el volumen reducido, es viable mantener correcciones manuales, pero deben funcionar como overrides explicitos por `id` estable y no como ediciones directas del GeoPackage generado, que se perderian al regenerar la cache.

## Inventario verificado

| ID | Estacion | Valor de fuente | Estado propuesto |
|---|---|---:|---|
| `ST` | SANTO TOME | 900 MVA | Conservar salvo evidencia en contrario |
| `CN` | RIO CORONDA | 0 MVA | Validar: puede significar no informado/no aplicable |
| `RO` | ROSARIO OESTE | 1200 MVA | Conservar salvo evidencia en contrario |
| `RM` | ROMANG | 150 MVA | Conservar salvo evidencia en contrario |

Conteo comprobado sobre `data/raw/layers/transformers.gpkg`: 4 filas, 4 IDs unicos, 4 nombres unicos y 0 valores nulos.

## Decisiones de arquitectura

- Usar un diccionario opcional `capacity_overrides_mva` dentro de `infrastructure.transformers`, indexado por el `id` estable de la fuente. Con cuatro elementos, un archivo o sistema de administracion separado seria complejidad innecesaria.
- Aplicar los overrides durante la ingesta, despues de leer y normalizar el CSV y antes de recortar/guardar la capa. Asi la base SQLite, el mapa y cualquier calculo posterior reciben el mismo dato.
- Mantener el valor original de la fuente cuando no exista override. Un valor `0` no se convertira automaticamente en faltante ni se estimara.
- Registrar en los metadatos de la capa cuantos valores se reemplazaron y que IDs fueron afectados, para conservar trazabilidad.
- No incorporar la capacidad MVA al fitness en este cambio. Primero se corrige y valida el dato; usarlo para ranking requiere una especificacion separada sobre capacidad instalada versus capacidad disponible.

## Grafo de dependencias

Validacion documental de MVA
    -> contrato de configuracion
        -> aplicacion del override en ingesta
            -> cache y persistencia SQLite
                -> verificacion de salida y documentacion

## Lista de tareas

### Fase 1: Confirmar el dato

- [ ] Tarea 1: Validar las cuatro capacidades, especialmente el `0` de RIO CORONDA.

### Punto de control: fuente

- [ ] Cada valor manual tiene fuente, fecha de consulta y unidad MVA.
- [ ] Se decidio explicitamente si `0` significa cero real, no informado o no aplicable.

### Fase 2: Override minimo y durable

- [ ] Tarea 2: Agregar y validar `capacity_overrides_mva` en la configuracion.
- [ ] Tarea 3: Aplicar los overrides en la ingesta y registrar trazabilidad.

### Punto de control: implementacion

- [ ] Las pruebas focalizadas pasan.
- [ ] Una regeneracion forzada conserva los overrides.
- [ ] Los valores sin override permanecen iguales a la fuente.

### Fase 3: Cierre

- [ ] Tarea 4: Documentar el mecanismo y verificar la capa persistida.

### Punto de control: completo

- [ ] La capa contiene exactamente 4 estaciones unicas.
- [ ] Las cuatro capacidades finales coinciden con la tabla aprobada.
- [ ] La suite completa pasa y el proyecto queda listo para revision.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Confundir potencia instalada con capacidad disponible para conectar un parque | Alto | No usar MVA en el fitness sin una fuente de capacidad disponible y una regla de negocio acordada |
| Interpretar `0` como una capacidad fisica real | Alto | Exigir validacion documental antes de crear el override de RIO CORONDA |
| Perder cambios al regenerar cache | Medio | Guardar overrides en configuracion y aplicarlos antes de `cache.save` |
| Vincular el override a un nombre que cambie | Medio | Usar el campo `id` (`ST`, `CN`, `RO`, `RM`) y fallar ante IDs desconocidos |
| Unidad ambigua por el nombre actual `potencia_instalada_mv` | Medio | Documentar que la unidad esperada es MVA; una migracion de nombre queda fuera de este cambio minimo |

## Preguntas abiertas

- Cual es la fuente autorizada para corregir las capacidades y su fecha de vigencia?
- Que representa exactamente el `0` de RIO CORONDA?
- Se busca solo almacenar/mostrar MVA o usarlo despues para modificar el ranking? Lo segundo requiere otro plan.

