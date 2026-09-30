# Tareas: capacidades MVA de estaciones transformadoras

## Tarea 1: Validar la tabla de capacidades

**Descripcion:** Confirmar con una fuente tecnica autorizada los valores MVA de las cuatro estaciones y resolver el significado del valor `0` de RIO CORONDA antes de modificar datos.

**Criterios de aceptacion:**

- [ ] Existe una tabla aprobada con los IDs `ST`, `CN`, `RO` y `RM`, su capacidad MVA y la fuente de cada valor.
- [ ] El valor de RIO CORONDA esta clasificado como capacidad real, no informado o no aplicable.
- [ ] Ningun valor es una estimacion sin marcar.

**Verificacion:**

- [ ] Revision manual: comparar los cuatro registros contra la fuente autorizada.
- [ ] Revision manual: confirmar que la unidad es MVA y no MW ni kVA.

**Dependencias:** Ninguna.

**Archivos probablemente afectados:**

- `config.yaml`

**Alcance estimado:** XS, 1 archivo.

## Punto de control: fuente validada

- [ ] Los cuatro valores y sus unidades fueron aprobados antes de escribir codigo.

## Tarea 2: Definir overrides MVA tipados

**Descripcion:** Incorporar un diccionario opcional `capacity_overrides_mva` a la configuracion de transformadores, indexado por ID de estacion y restringido a numeros no negativos.

**Criterios de aceptacion:**

- [ ] La configuracion acepta un mapa vacio o ausente sin cambiar el comportamiento actual.
- [ ] Rechaza valores negativos o no numericos.
- [ ] `config.yaml` contiene solamente los overrides respaldados por la Tarea 1.

**Verificacion:**

- [ ] Pruebas focalizadas: `.\.venv\Scripts\python.exe -m unittest tests.test_transformer_capacity -v`.
- [ ] Carga manual: la configuracion actual se valida correctamente.

**Dependencias:** Tarea 1.

**Archivos probablemente afectados:**

- `src/config/settings.py`
- `config.yaml`
- `config.test.yaml`
- `tests/test_transformer_capacity.py`

**Alcance estimado:** M, 4 archivos.

## Tarea 3: Aplicar y auditar los overrides durante la ingesta

**Descripcion:** Reemplazar `potencia_instalada_mv` solo para IDs configurados, antes de guardar la capa, y registrar los IDs modificados en los metadatos.

**Criterios de aceptacion:**

- [ ] Cada override coincide con exactamente una estacion; un ID desconocido produce un error claro.
- [ ] Las estaciones sin override conservan el valor de la fuente.
- [ ] Los metadatos enumeran los IDs reemplazados y la cantidad de cambios.

**Verificacion:**

- [ ] Pruebas focalizadas: `.\.venv\Scripts\python.exe -m unittest tests.test_transformer_capacity -v`.
- [ ] Prueba de regresion: una configuracion sin overrides reproduce los valores originales.
- [ ] Comprobacion manual: ejecutar ingesta forzada y revisar el GeoPackage y su JSON de metadatos.

**Dependencias:** Tarea 2.

**Archivos probablemente afectados:**

- `src/pipeline/ingest.py`
- `tests/test_transformer_capacity.py`

**Alcance estimado:** S, 2 archivos.

## Punto de control: override durable

- [ ] Las pruebas focalizadas pasan.
- [ ] Regenerar la cache no elimina los valores manuales.
- [ ] El inventario sigue teniendo 4 IDs y nombres unicos.

## Tarea 4: Documentar y verificar de extremo a extremo

**Descripcion:** Explicar el mecanismo de override, su precedencia respecto de la fuente y su limitacion: MVA instalado no equivale a capacidad disponible de conexion.

**Criterios de aceptacion:**

- [ ] El README muestra un ejemplo minimo de configuracion y explica como forzar la regeneracion de cache.
- [ ] La base persistida contiene las cuatro capacidades aprobadas.
- [ ] No se modifica el fitness ni el ranking por capacidad en este alcance.

**Verificacion:**

- [ ] Suite completa: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- [ ] Comprobacion manual: consultar la tabla `transformers` y comparar sus cuatro valores con la tabla aprobada.
- [ ] Comprobacion manual: revisar los metadatos de la capa regenerada.

**Dependencias:** Tarea 3.

**Archivos probablemente afectados:**

- `README.md`
- `data/raw/layers/<scope>/transformers.gpkg` (salida regenerada, no codigo fuente)
- `data/raw/layers/<scope>/transformers.meta.json` (salida regenerada, no codigo fuente)

**Alcance estimado:** S, 1 archivo de documentacion mas artefactos generados.

## Punto de control: completo

- [ ] Todos los criterios de aceptacion estan cumplidos.
- [ ] La suite completa pasa.
- [ ] El plan fue revisado y aprobado antes de implementar.
