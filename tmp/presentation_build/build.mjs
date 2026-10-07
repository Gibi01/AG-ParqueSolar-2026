import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026';
const dir=path.join(root,'tmp/presentation_build');
const skill='C:/Users/creis/.codex/plugins/cache/openai-primary-runtime/presentations/26.1004.11800/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const d=JSON.parse((await fs.readFile(path.join(dir,'evidence.json'),'utf8')).replace(/\bNaN\b/g,'null'));
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#102A43',teal:'#087F8C',gold:'#C7902C',ink:'#183B4E',muted:'#526778',pale:'#EEF5F5',white:'#FFFFFF',line:'#CFDCE0'};
const F='Arial';let n=0;const tableOwners=[],chartOwners=[];
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false){let z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=t;z.text.style={typeface:F,fontSize:size,color,bold,autoFit:'none',verticalAlignment:'middle'};return z;}
function slide(title,notes,source='README.md'){const s=P.slides.add();n++;s.background.fill=C.white;text(s,title,60,40,1160,94,43,C.navy,true);text(s,String(n).padStart(2,'0'),1190,669,50,27,18,C.muted);s.speakerNotes.textFrame.setText(notes+'\n\nFuentes del proyecto: '+source.split(',').map(x=>root+'/'+x.trim()).join('\n')+'\nCorrida de referencia: '+d.run_dir+'\nLas cifras y eventos del ejemplo se verificaron al reproducir la corrida con semilla 42.');return s;}
function caption(s,t){text(s,t,60,628,1110,38,21,C.muted);}
function table(s,values,x,y,w,h,widths,size=24){tableOwners.push(n);const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values:values.map(r=>r.map(String)),...(widths?{columnWidths:widths}: {})});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let z=t.getCell(r,c);z.fill=r===0?C.navy:r%2?C.white:C.pale;z.text.style={typeface:F,fontSize:size,color:r===0?C.white:C.ink,bold:r===0};}t.borders.assign({fill:C.line,width:1,style:'solid'});return t;}
function grid(s,park,x,y,w,h,extra=[]){const points=[...park.coordinates,...extra];const minr=Math.min(...points.map(p=>p.row))-1,maxr=Math.max(...points.map(p=>p.row))+1,minc=Math.min(...points.map(p=>p.column))-1,maxc=Math.max(...points.map(p=>p.column))+1;const values=[];for(let r=maxr;r>=minr;r--){let row=[];for(let c=minc;c<=maxc;c++){const q=park.coordinates.find(z=>z.row===r&&z.column===c);row.push(q?String(q.cell_id):'');}values.push(row);}tableOwners.push(n);let t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values:w<300?values.map(r=>r.map(()=>'')):values});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let z=t.getCell(r,c);z.fill=values[r][c]?Number(values[r][c])===park.seed?C.gold:C.teal:C.pale;z.text.style={typeface:F,fontSize:20,color:C.white,bold:true};}t.borders.assign({fill:C.white,width:2,style:'solid'});return t;}
function chart(s,type,options){chartOwners.push(n);let z=s.charts.add(type,{chartFill:C.white,plotAreaFill:C.white,chartLine:{fill:'none',width:0},...options});applyPresentationChartFont(z,{fontFamily:F});return z;}
async function img(s,file,x,y,w,h,fit='contain'){s.images.add({blob:new Uint8Array(await fs.readFile(file)),contentType:'image/png',alt:path.basename(file),fit,position:{left:x,top:y,width:w,height:h}});}
const fmt=(x,k=3)=>Number(x).toLocaleString('es-AR',{minimumFractionDigits:k,maximumFractionDigits:k});
const num=x=>Number(x).toLocaleString('es-AR');
const a=d.random,m=d.mutation,c=d.crossover;

// 01
{
const s=P.slides.add();n++;await img(s,path.join(dir,'portada.png'),0,0,1280,720,'cover');
text(s,'Parques solares\ny algoritmo genético',62,92,710,185,66,C.white,true);
text(s,'Ubicación, forma y superficie\nen Santa Fe',65,317,590,100,34,C.white);
text(s,'Guía visual para la presentación y defensa\nProyecto AG-ParqueSolar-2026',65,550,680,90,25,C.white);
s.speakerNotes.textFrame.setText('Apertura: el proyecto explora configuraciones de parques solares sobre una grilla. Explicaremos primero de dónde provienen los datos y luego cómo el AG produce y compara propuestas. Duración sugerida: 20 a 25 minutos. La ilustración de portada es conceptual, generada con IA, y no representa una instalación real. Fuente técnica: '+root+'/README.md');
}
// 02
{
const s=slide('El problema territorial','El algoritmo propone dónde ubicar un parque, qué forma darle y cuánto puede crecer. Un parque contiene celdas conectadas por borde. La escala de trabajo es provincial y la grilla de análisis usa 500 metros. La cartografía oficial aquí es contexto: el pipeline usa capas vectoriales y registros climáticos, no extrae datos de esta imagen. El mapa es de agosto de 2024.','README.md,generacion_electrica.pdf');
await img(s,path.join(root,'mapa_revision.png'),60,151,390,462);
text(s,'Cada propuesta combina',500,166,690,45,32,C.teal,true);
text(s,'Una ubicación dentro de Santa Fe\n\nUna forma de celdas contiguas\n\nUna superficie bajo el límite experimental',500,235,710,255,30);
text(s,'Resultado: candidatos para estudiar\ncon mayor detalle',500,525,700,85,30,C.navy,true);
}
// 03
{
const s=slide('Fuentes y funciones de los datos','Separar fuentes evita confundir líneas con estaciones o geometría con capacidad eléctrica. IGN aporta el límite. INDEC aporta polígonos urbanos del Censo 2022. CKAN aporta líneas. El archivo CSV aporta estaciones. ERA5-Land aporta radiación. La preparación selecciona cuatro ET identificadas por CN, RM, RO y ST: Río Coronda, Romang, Rosario Oeste y Santo Tomé. El AG no usa MVA.','config.yaml,src/pipeline/ingest.py,src/pipeline/preprocess.py');
table(s,[['Fuente','Dato','Uso en el modelo'],['IGN','Límite provincial','Recorte de Santa Fe'],['INDEC 2022','Envolventes urbanas','Exclusión de celdas'],['datos.gob.ar / CKAN','Geometría de líneas','Distancia a la red'],['Secretaría de Energía','CSV de estaciones','Distancia a 4 ET de referencia'],['Copernicus ERA5-Land','Radiación horaria SSRD','Indicador solar anual']],60,166,1160,399,[310,355,495],25);
caption(s,'Cada fuente tiene un formato y una validación propios');
}
// 04
{
const s=slide('Una petición real: polígonos urbanos','Este es un ejemplo fiel a src/api/indec.py. El cliente hace GET al WFS con parámetros separados. count=500 es el tamaño de página configurado. En la segunda página startIndex pasa a 500 y continúa hasta reunir numberMatched. El cliente verifica FeatureCollection, numberReturned, IDs únicos y un total estable. Si una página falta, falla. No es una consulta que se haga por cada cromosoma. Fuente: endpoint configurado https://geonode.indec.gob.ar/geoserver/geonode/wfs','src/api/indec.py,config.yaml');
text(s,'GET al servicio WFS de INDEC',60,158,1130,50,32,C.teal,true);
table(s,[['Parámetro','Valor enviado'],['request / version','GetFeature / 2.0.0'],['typeNames','geonode:localidades_censales'],['outputFormat / srsName','application/json / EPSG:4326'],['count / startIndex','500 / 0, luego 500, 1.000…'],['sortBy','fid']],60,230,770,321,[305,465],24);
text(s,'Respuesta GeoJSON',878,246,335,60,30,C.navy,true);
text(s,'features\nnumberMatched\nnumberReturned',878,330,335,143,28);
caption(s,'El cliente exige una descarga nacional completa antes del recorte provincial');
}
// 05
{
const s=slide('Los otros accesos a datos','La app no trata todas las fuentes como una única API. IGN es un ZIP que contiene un shapefile. CKAN usa datastore_search paginado con resource_id, limit y offset. Las estaciones son un CSV descargado directamente. El clima usa xarray.open_zarr sobre ARCO con autorización Bearer de CDS_API_KEY, sin mostrar la credencial. La clave queda fuera de los metadatos de corrida. Los pesos cero desactivan su fuente, pero la exclusión urbana sigue activa.','src/api/datos_gob_ar.py,src/pipeline/ingest.py,src/climate/arco.py,src/main.py');
table(s,[['Recurso','Petición / acceso','Respuesta'],['Límite IGN','Descarga del ZIP','Shapefile y CRS'],['Líneas eléctricas','datastore_search\nresource_id, limit, offset','JSON con geometrías'],['Estaciones','Descarga del archivo','CSV con ubicaciones'],['Radiación ARCO','Lectura de bloques Zarr\nAutorización CDS','Series horarias SSRD']],60,174,1160,370,[295,510,355],25);
caption(s,'--download obtiene las capas vectoriales. --process también consulta el clima');
}
// 06
{
const s=slide('Radiación: de horas a un indicador anual','La radiación SSRD acumulada se convierte de joules por metro cuadrado a kWh por metro cuadrado dividiendo por 3.600.000. El resumen mensual exige 100% de horas únicas y finitas. Se promedian años completos de enero, abril, julio y octubre y se usan los días de cada estación para estimar un indicador anual. La corrida incluye 11 períodos: los cuatro meses de 2024 y 2025, más enero, abril y julio de 2026. No incluye octubre de 2026. Múltiples celdas de 500 m comparten el mismo píxel nativo, sin interpolación.','src/climate/arco.py,src/climate/climatology.py');
text(s,'Grilla de análisis',60,166,550,45,31,C.teal,true);
text(s,'500 × 500 m',60,225,550,72,56,C.navy,true);
text(s,'Varias celdas pueden compartir\nun píxel climático nativo',60,325,560,96,29);
table(s,[['Paso','Tratamiento'],['Horas SSRD','J/m² ÷ 3.600.000'],['Mes completo','100% de horas válidas'],['Media interanual','Enero, abril, julio, octubre'],['Estimación anual','Media diaria × días de estación']],660,172,550,331,[215,335],23);
text(s,'500 m de grilla no equivale a 500 m\nde resolución climática',60,533,1160,70,31,C.navy,true);
}
// 07
{
const s=slide('Preparación y persistencia','Narrar las cuatro etapas. Primero cacheamos fuentes. Luego unificamos CRS para trabajar en metros, recortamos, validamos geometrías y excluimos zonas urbanas. Construimos el grafo de vecinos y asociamos cada celda válida al píxel climático más cercano. El snapshot guarda celdas, vecinos, clima y capas en SQLite. Su identificador depende del contenido. La optimización carga ese snapshot y exporta resultados en una carpeta nueva. Los datos anteriores no se reemplazan.','src/pipeline/preprocess.py,src/database/spatial.py,src/main.py');
const parts=[['01','Fuentes y caché','Capas vectoriales en disco\nBloques climáticos NPZ'],['02','Procesamiento','Grilla, máscara urbana\nClima y vecinos por borde'],['03','Snapshot SQLite','Celdas y geometrías\nID basado en contenido'],['04','Optimización local','Población y fitness\nCSV, GeoJSON y HTML']];
parts.forEach((p,i)=>{let x=60+i*300;text(s,p[0],x,184,240,85,62,C.gold,true);text(s,p[1],x,300,250,90,31,C.navy,true);text(s,p[2],x,420,252,135,25);});
caption(s,'Las consultas externas terminan antes del bucle de generaciones');
}
// 08
{
const s=slide('Caché, validación y trazabilidad','Hay tres mecanismos diferentes. La caché de fuentes evita descargar lo existente salvo --force. La caché ARCO reutiliza períodos ya guardados y consulta los faltantes. El evaluador memoriza hasta 10.000 genotipos por dataset/configuración, para repetir cálculos sin reconstruir el parque. SQLite conserva snapshots y corridas. Si cambia la huella urbana o falta una fuente activa, el pipeline pide reprocesar o se detiene. No se inventan estaciones ni valores solares. Los metadatos conservan configuración, semilla y versiones, sin credenciales.','src/data/cache.py,src/climate/arco.py,src/optimization/spatial.py,src/database/spatial.py');
table(s,[['Mecanismo','Qué reutiliza','Cómo mantiene coherencia'],['Caché de capas','Descargas vectoriales','Fuente, fecha y huella INDEC'],['Caché ARCO','Bloques y meses climáticos','Consulta períodos faltantes'],['Snapshot SQLite','Dataset preparado','Identificador de contenido'],['Caché del evaluador','Parque de un genotipo','Ligada a dataset y configuración']],60,181,1160,355,[290,390,480],24);
caption(s,'La misma semilla y el mismo snapshot permiten repetir el experimento');
}
// 09
{
const s=slide('Restricciones del parque','Una celda completa tiene 0,25 km², equivalentes a 25 hectáreas. Con 31,3 MW/km² representa 7,825 MW. La contigüidad viene del grafo con vecinos por borde, no por una esquina. La exclusión urbana descarta celdas que tocan o intersectan la máscara, con margen cero y huecos internos rellenados en esta configuración. El límite 80 MW es una restricción experimental. Diez celdas completas suman 78,25 MW. En bordes provinciales hay celdas recortadas y el parque puede incluir más de diez fragmentos.','config.yaml,src/gis/grid.py,src/optimization/spatial.py');
text(s,'Una celda completa',60,161,580,53,33,C.teal,true);
text(s,'25 ha\n7,825 MW',60,239,550,178,58,C.navy,true);
text(s,'10 celdas completas = 78,25 MW',60,487,550,94,31,C.ink,true);
table(s,[['Regla','Efecto'],['Vecinos por borde','Mantiene el parque contiguo'],['Máscara urbana','Impide usar celdas excluidas'],['Área × 31,3 MW/km²','Calcula la potencia instalada'],['Potencia ≤ 80 MW','Limita el crecimiento']],655,180,555,351,[220,335],23);
caption(s,'Las celdas recortadas en el límite provincial conservan su área real');
}
// 10
{
const s=slide('Un cromosoma del proyecto','Este cromosoma proviene del ejemplo registrado en la generación inicial de la corrida reproducida. La semilla es 46.504 y los cuatro genes son enteros. Cada entero selecciona una posición dentro de la frontera ordenada mediante módulo. El gen no es una coordenada, un ID de celda ni una dirección fija. Con la misma semilla, la misma secuencia y el mismo grafo se obtiene siempre el mismo parque. El genotipo codifica instrucciones y el fenotipo es el conjunto de celdas.','src/optimization/spatial.py,src/optimization/initialization.py');
table(s,[['Semilla','g1','g2','g3','g4'],['46.504','429014945','1856101005','1726844270','53904684']],60,181,1160,121,[200,240,240,240,240],23);
grid(s,a,60,361,560,224);
text(s,'Genotipo',700,359,480,49,31,C.teal,true);text(s,'Semilla + secuencia de enteros',700,414,500,60,27);
text(s,'Fenotipo',700,495,480,49,31,C.teal,true);text(s,'5 celdas contiguas\n125 ha y 39,125 MW',700,549,500,73,27);
caption(s,'Oro: celda semilla. Verde: celdas del parque. Los números son IDs de celda');
}
// 11
{
const tr=d.trace[0];const s=slide('Decodificación: cómo actúa un gen','La frontera contiene celdas válidas que comparten borde con el parque. Se ordena por la posición en la grilla, que usa fila, columna y componente. Para el primer gen, la frontera real es [46165,46503,46505,46843]. 429014945 módulo 4 da 1, por lo que se elige la segunda entrada: 46503. El índice comienza en cero. Luego se actualiza la frontera y el próximo entero usa una lista distinta. El evaluador omite una adición que excede potencia, o termina si no cabe ninguna celda de la frontera.','src/optimization/spatial.py');
table(s,[['Frontera ordenada','Índice'],['46.165','0'],['46.503','1   ← elegida'],['46.505','2'],['46.843','3']],60,180,480,300,[320,160],25);
text(s,'429014945 mod 4 = 1',610,197,600,74,40,C.teal,true);
text(s,'El gen elige la posición 1\nde la frontera actual',610,309,600,111,32);
text(s,'Nueva celda: 46.503',610,479,600,72,37,C.navy,true);
caption(s,'Después de cada adición cambia la frontera sobre la que actúa el siguiente gen');
}
// 12
{
const s=slide('Crecimiento del mismo cromosoma','Leer de izquierda a derecha. Esto muestra la decodificación de un cromosoma, no generaciones evolutivas. Semilla sola, luego uno, dos, tres y cuatro genes. La traza real agrega 46503,46505,46843 y46506. Cada adición comparte borde con una celda del parque. Todos los fragmentos de este ejemplo son cuadrados completos. En los recuadros pequeños los IDs se omiten porque la tabla inferior conserva la traza numérica.','src/optimization/spatial.py');
for(let k=0;k<5;k++){let p=d.prefixes[k],x=60+k*237;text(s,k===0?'Semilla':'Hasta g'+k,x,168,223,49,27,C.teal,true);grid(s,p,x,234,211,180,a.coordinates);text(s,p.number_of_cells+' celda'+(p.number_of_cells>1?'s':''),x,437,219,45,26,C.ink,true);}
table(s,[['Paso','Semilla','g1','g2','g3','g4'],['Celda incorporada','46.504',...d.trace.map(t=>num(t.chosen))]],60,519,1160,93,[240,184,184,184,184,184],22);
caption(s,'Lectura del genotipo: 1 celda inicial + 4 adiciones = 5 celdas contiguas');
}
// 13
{
const s=slide('Fitness: cómo comparamos propuestas','Los cuatro scores están entre cero y uno. Radiación usa min-max de las celdas válidas, con promedio ponderado por área para cada parque. Las distancias se calculan desde el centroide ponderado por área y se invierten para que cerca valga más. La potencia usa P/80. Los límites de normalización son del dataset y los resultados se recortan a [0,1]. Para este cromosoma: radiación 1830,38 kWh/m²/año, distancia a línea 0,967 km y a Rosario Oeste 62,764 km. Los pesos son provisionales y el score es comparativo.','src/optimization/spatial.py,config.yaml');
const keys=['solar_score','grid_proximity_score','transformer_proximity_score','installed_power_score'],weights=[.4,.1,.4,.1],labels=['Radiación solar','Proximidad a líneas','Proximidad a ET','Potencia / 80 MW'];
table(s,[['Criterio','Score','Peso','Aporte al fitness'],...keys.map((key,i)=>[labels[i],fmt(a[key]),fmt(weights[i],2),fmt(a[key]*weights[i],4)])],60,177,1160,313,[400,220,220,320],27);
text(s,'F = 0,40 S + 0,10 L + 0,40 T + 0,10 P',60,532,840,65,33,C.navy,true);
text(s,fmt(a.fitness,4),946,514,267,94,54,C.teal,true);
caption(s,'Los pesos permiten expresar prioridades. Requieren análisis de sensibilidad');
}
// 14
{
const s=slide('El ciclo de una generación','La inicialización genera 50 individuos distribuidos por territorios de 50 km. Cada generación evalúa la población. Conserva hasta dos élites con fenotipos distintos. Completa 48 plazas con torneos de tres, cruza parejas con probabilidad 0,75 y muta hijos con probabilidad 0,20. Intenta evitar duplicados por conjunto de celdas. El archivo territorial conserva hasta diez candidatos por territorio. Se repite hasta 200 generaciones, más la evaluación inicial de generación cero. Las probabilidades no aseguran mejora individual.','src/optimization/genetic_algorithm.py,src/optimization/initialization.py,config.yaml');
table(s,[['Etapa','Acción','Configuración actual'],['Evaluación','Decodifica parques y calcula fitness','50 individuos'],['Elitismo','Conserva parques fuertes distintos','2 élites'],['Selección','Compara participantes de un torneo','3 participantes'],['Cruce','Combina prefijos y sufijos','Probabilidad 75%'],['Mutación','Cambia genes o la semilla','Probabilidad 20%'],['Nueva población','Controla duplicados y repite','200 generaciones']],60,164,1160,420,[255,600,305],24);
caption(s,'La generación 0 evalúa la población inicial antes del primer cruce');
}
// 15
{
const s=slide('Selección por torneo','Este es un torneo didáctico compuesto por tres scores reales del ejemplo. No afirmamos que estos tres hayan participado juntos en un torneo de la corrida. La selección toma tres índices aleatorios con reemplazo dentro de cada torneo y elige el mayor fitness. Vuelve a sortear para cada plaza, por eso un ganador puede repetirse. Esto favorece buenas propuestas, sin convertir la selección en una regla que elige sólo a los mejores de toda la población.','src/optimization/selection.py');
chart(s,'bar',{position:{left:60,top:181,width:770,height:373},categories:['A','B','C'],series:[{name:'Fitness',values:[c.a.fitness,c.b.fitness,m.parent.fitness],fill:C.teal,valuesFormatCode:'0.000'}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:false,xAxis:{textStyle:{typeface:F,fontSize:24}},yAxis:{min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',title:'Fitness',textStyle:{typeface:F,fontSize:22}},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:F,fontSize:24},numberFormatCode:'0.000'}});
text(s,'Gana B',910,229,300,72,48,C.navy,true);text(s,fmt(c.b.fitness,4),910,322,300,66,40,C.teal,true);text(s,'El ganador puede\nproducir descendencia',910,440,300,101,29);
caption(s,'Ejemplo de torneo con valores reales, no registro de un sorteo específico');
}
// 16
{
const s=slide('Cruce real: una nueva secuencia','Evento real del primer paso evolutivo. El corte A ocurre después de sus cuatro genes, y el corte B deja sólo su último gen para el sufijo. El hijo conserva la semilla A=46504. Reinterpreta el entero B7=1986680326 en la frontera correspondiente a esa semilla. No traslada las celdas del parque B. El padre A tenía cinco celdas y el hijo tiene seis. El fitness pasa de 0,5839 a 0,5937, aunque sigue por debajo del padre B. Un cruce puede también empeorar. Los aliases A1 a B7 sólo facilitan la lectura, todos los enteros constan en las notas.','src/optimization/crossover.py,src/optimization/spatial.py');
s.speakerNotes.textFrame.setText('Cruce real en la generación 1: A conserva los cuatro genes y agrega el último gen de B. Corte A=4 y corte B=6. El hijo conserva la semilla de A. Estos alias facilitan leer el cruce y no sustituyen la codificación entera. Un cruce puede producir un hijo mejor o peor.\nGenotipo A: '+JSON.stringify(c.a.genes)+'\nGenotipo B: '+JSON.stringify(c.b.genes)+'\nHijo: '+JSON.stringify(c.child.genes)+'\nFuente: '+root+'/src/optimization/crossover.py\nCorrida: '+d.run_dir);
table(s,[['Individuo','Semilla','Secuencia de genes'],['Padre A','46.504','A1  A2  A3  A4'],['Padre B','249.997','B1  B2  B3  B4  B5  B6  B7'],['Hijo A','46.504','A1  A2  A3  A4  B7']],60,174,1160,244,[220,220,720],29);
text(s,'El hijo conserva el prefijo A\ny agrega el sufijo B7',60,475,570,123,33,C.navy,true);
text(s,'5 celdas / '+fmt(c.a.fitness,4)+'\n6 celdas / '+fmt(c.child.fitness,4),750,480,460,125,35,C.teal,true);
caption(s,'Las celdas resultantes dependen de decodificar toda la secuencia con su semilla');
}
// 17
{
const s=slide('Mutación real: el parque agrega una celda','Evento real en la generación 1, semilla 380674. Se conserva el padre, y el hijo agrega un gen de valor 6. El decoder elige la celda 381148 y el fenotipo cambia de seis a siete celdas. La potencia aumenta 7,825 MW. La irradiación se mantiene en 1830,91 kWh/m²/año, pero cambian algo las distancias del centroide. Esta mutación mejora el fitness de 0,4498 a 0,4597. Otras mutaciones pueden cambiar un gen, eliminar crecimiento o cambiar la semilla. El operador intenta hasta cuatro veces lograr un fenotipo diferente, sin exigir que sea mejor.','src/optimization/mutation.py,src/optimization/spatial.py');
text(s,'Padre',60,163,500,49,30,C.navy,true);text(s,'Hijo: agrega el gen 6',690,163,510,49,30,C.teal,true);
grid(s,m.parent,60,235,500,275,m.child.coordinates);grid(s,m.child,690,235,500,275,m.parent.coordinates);
text(s,'6 celdas   46,950 MW\nFitness '+fmt(m.parent.fitness,4),60,542,500,79,29);
text(s,'7 celdas   54,775 MW\nFitness '+fmt(m.child.fitness,4),690,542,500,79,29);
caption(s,'La nueva celda 381148 cambia la forma, el área y el centroide del parque');
}
// 18
{
const s=slide('Evolución observada en 200 generaciones','La curva corresponde a history.csv de la corrida del 4 de octubre de 2026 con semilla 42 y 50 individuos. El mejor fitness inicial es 0,646999 y el final 0,725455. Son 0,078455 puntos de score, no un porcentaje de rendimiento eléctrico. El promedio fluctúa porque hay mutación, cruces y nuevos muestreos para resolver duplicados. La comparación de mejores se conserva mediante élites y archivo. Esta corrida visita 6214 parques únicos entre poblaciones evaluadas, no todos los parques posibles. La curva por sí sola no demuestra óptimo global.','results/spatial/run-20261004T164747-1cc83f35/history.csv,src/optimization/genetic_algorithm.py');
chart(s,'scatter',{position:{left:60,top:158,width:1150,height:399},series:[{name:'Mejor fitness',xValues:d.history.map(x=>x.generation),values:d.history.map(x=>x.best_fitness),line:{fill:C.teal,width:3},marker:{symbol:'none'}},{name:'Fitness medio',xValues:d.history.map(x=>x.generation),values:d.history.map(x=>x.mean_fitness),line:{fill:'#93A7B3',width:2},marker:{symbol:'none'}}],scatterOptions:{style:'line'},hasLegend:true,legend:{position:'bottom',textStyle:{typeface:F,fontSize:22}},xAxis:{title:'Generación',min:0,max:200,majorUnit:50,textStyle:{typeface:F,fontSize:22}},yAxis:{title:'Fitness',min:.4,max:.8,majorUnit:.1,numberFormatCode:'0.00',textStyle:{typeface:F,fontSize:22}}});
text(s,fmt(d.history[0].best_fitness,4)+' inicial',60,574,370,49,31,C.navy,true);text(s,fmt(d.first.fitness,4)+' final',482,574,370,49,31,C.teal,true);text(s,'6.214 parques visitados',876,574,360,49,26,C.ink,true);
}
// 19
{
const s=slide('Cómo cambia el mejor individuo','Estas filas son los líderes de la población en generaciones seleccionadas. No describen una genealogía única ni una mejora del cromosoma individual anterior. Incluso con una semilla repetida pueden cambiar genes, forma y métricas. El mejor final tiene once fragmentos, algunos recortados en el borde provincial, y por eso su área no equivale a once cuadrados completos. Los genes no procesados por alcanzar el límite de potencia pueden hacer que un cromosoma tenga más genes que adiciones efectivas.','src/optimization/genetic_algorithm.py,src/optimization/spatial.py');
table(s,[['Generación','Semilla','Genes','Celdas','Potencia MW','Fitness'],...d.leaders.map(p=>[p.generation,num(p.seed),p.genes.length,p.number_of_cells,fmt(p.installed_power_mw,2),fmt(p.fitness,4)])],60,169,1160,387,[200,240,140,140,240,200],26);
caption(s,'Son líderes sucesivos de la población. Cada fila puede pertenecer a otro linaje');
}
// 20
{
const s=slide('Resultados para explorar el territorio','El ranking general ordena por fitness y puede incluir parques solapados. El ranking territorial selecciona alternativas sin solapamiento, con separación adicional cero en la configuración actual. El mapa muestra centroides del top cinco territorial, con contorno de Santa Fe simplificado para esta visualización. Los símbolos son posiciones, no tamaños de parque. La corrida conserva geometría exacta en GeoJSON, métricas en CSV, curva en evolution.html y mapa en map.html. ET en la tabla significa la estación más cercana de las cuatro de referencia, no conexión habilitada.','src/pipeline/reporting.py,results/spatial/run-20261004T164747-1cc83f35/ranking_territorial.csv');
chart(s,'scatter',{position:{left:60,top:157,width:440,height:451},series:[{name:'Santa Fe',xValues:d.boundary.map(p=>p[0]),values:d.boundary.map(p=>p[1]),line:{fill:'#9BB2BA',width:2},marker:{symbol:'none'}},...d.territorial.map(p=>({name:p.rank===3?'#3 a #5':'#'+p.rank,xValues:[p.longitude],values:[p.latitude],line:{fill:'none',width:0},marker:{symbol:'circle',size:10,fill:p.rank===1?C.gold:C.teal},dataLabels:{showSeriesName:p.rank<=3,position:p.rank===3?'left':'right',textStyle:{typeface:F,fontSize:22}}}))],scatterOptions:{style:'lineWithMarkers'},hasLegend:false,xAxis:{visible:false,min:-63,max:-59},yAxis:{visible:false,min:-35,max:-28}});
table(s,[['#','ET de referencia','MW','Fitness'],...d.territorial.map(p=>[p.rank,p.station_name,fmt(p.installed_power_mw,2),fmt(p.fitness,4)])],554,171,657,311,[60,290,145,162],23);
text(s,'CSV: métricas y genotipos\nGeoJSON: geometrías\nHTML: mapa y evolución',555,529,655,99,27);
caption(s,'Centroides del TOP 5 territorial. La posición del símbolo no muestra el área');
}
// 21
{
const s=slide('Alcance eléctrico y límites del modelo','Esta es una limitación central para la defensa. El mapa oficial distingue tensiones, no capacidad de transformación. El pipeline actual conserva ID, nombre y geometría de cuatro estaciones y calcula distancia, no MVA ni flujo de potencia. El mejor final está a unos 170,92 km de Santo Tomé, la más cercana de ese conjunto, aunque a 0,081 km de una línea. Esto muestra que un score alto no garantiza una conexión adecuada y que el inventario de referencia es limitado. Tampoco evalúa titularidad, catastro, costos, pendientes, permisos, pérdidas ni rendimiento fotovoltaico. La energía calculada es idealizada.','README.md,src/optimization/spatial.py,generacion_electrica.pdf');
await img(s,'C:/Users/creis/AppData/Local/Temp/codex-clipboard-66b9cbcb-4414-4468-b9ac-ad9de08b0f2d.png',60,183,512,330);
text(s,'kV = nivel de tensión\nMVA = capacidad de transformación',630,179,590,120,32,C.navy,true);
text(s,'80 MW es un límite experimental\n\nLa proximidad es un criterio geométrico\n\nLa conexión requiere un estudio eléctrico',630,342,590,244,29);
caption(s,'Mejor candidato: 0,081 km de una línea y 170,92 km de una ET de referencia');
}
// 22
{
const s=slide('Preguntas para la defensa','Respuestas sugeridas. ¿Por qué un AG? Porque explora combinaciones de ubicación y secuencias de crecimiento sin enumerarlas todas. No se afirma superioridad frente a otros métodos sin benchmark. ¿Contigüidad? Cada gen agrega una celda en la frontera por borde. ¿Por qué separar descarga y fitness? Para eficiencia y reproducibilidad. ¿Garantiza el mejor parque? Sólo el mejor encontrado en esta corrida bajo los supuestos. ¿Qué hace falta para aplicación real? Inventario completo y actualizado, capacidad y acceso a red, terreno, costos y permisos. Para sostener la calidad de la búsqueda conviene comparar varias semillas y sensibilidades de pesos y capacidad experimental.','README.md,config.yaml,src/optimization/genetic_algorithm.py');
table(s,[['Pregunta','Respuesta que sostiene el proyecto'],['¿Qué optimiza?','Ubicación, forma y superficie según un fitness ponderado'],['¿Cómo asegura contigüidad?','Cada adición proviene de vecinos válidos por borde'],['¿Consulta APIs en cada generación?','El fitness lee el snapshot local y reutiliza evaluaciones'],['¿Encuentra el óptimo global?','Entrega el mejor encontrado en el experimento'],['¿Qué falta para decidir una obra?','Estudios de terreno, conexión eléctrica y economía']],60,173,1160,391,[445,715],25);
caption(s,'Próxima validación: varias semillas, sensibilidad de pesos y comparación con otra búsqueda');
}

await fs.mkdir(path.join(dir,'previews'),{recursive:true});
const candidate=path.join(dir,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(candidate);
for(let i=0;i<P.slides.items.length;i++){const s=P.slides.items[i];const b=await P.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(dir,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
const final=path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026.pptx');
const layoutArgs=['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[...new Set(tableOwners)].flatMap(x=>['--require-native-table-slide',String(x)])];
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs,requiredNativeTableOwnerSlides:[...new Set(tableOwners)],requiredNativeChartOwnerSlides:[...new Set(chartOwners)],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:[F]},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation.json')});
console.log(JSON.stringify({slides:n,final,result}));
const check=await PresentationFile.importPptx(await FileBlob.load(final));
await fs.mkdir(path.join(dir,'final-previews'),{recursive:true});
for(let i=0;i<check.slides.items.length;i++){const b=await check.export({slide:check.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,'final-previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}


