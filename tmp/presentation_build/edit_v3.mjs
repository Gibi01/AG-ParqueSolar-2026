import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026',dir=path.join(root,'tmp/presentation_build');
const skill='C:/Users/creis/.codex/plugins/cache/openai-primary-runtime/presentations/26.1004.11800/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const source=path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026_v2.pptx');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const snap=(await p.inspect({kind:'slide,textbox,table,image',maxChars:100000})).ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
const C={navy:'#102A43',teal:'#087F8C',ink:'#183B4E',muted:'#526778'};
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false){let z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=t;z.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none',verticalAlignment:'middle'};return z;}
async function image(s,name,x,y,w,h,crop){return s.images.add({blob:new Uint8Array(await fs.readFile(path.join(dir,name))),contentType:'image/png',alt:name,fit:'contain',position:{left:x,top:y,width:w,height:h},...(crop?{crop}: {})});}
function clear(s,index){for(const r of snap.filter(x=>x.slideIndex===index)){if(r.kind==='textbox'&&![40,669].includes(r.position.top))s.shapes.deleteById(p.resolve(r.id).id);if(r.kind==='table')s.tables.deleteById(p.resolve(r.id).id);if(r.kind==='image')s.images.deleteById(p.resolve(r.id).id);}}
const s6=p.resolve('sl/x8f69ofe');clear(s6,5);
await image(s6,'v3_clima.png',60,182,1160,417,{left:0,top:.13,right:0,bottom:.15});
const climate=[['Horas SSRD','Radiación recibida\nJ/m² ÷ 3.600.000'],['Mes completo','Todas las horas del mes\ndeben tener datos válidos'],['Media interanual','Promedio por mes\nentre años completos'],['Estimación anual','Media diaria × días\nde cada estación']];
climate.forEach((v,i)=>{const x=112+i*263;text(s6,v[0],x,141,255,52,26,C.teal,true);text(s6,v[1],x,596,255,63,21);});
s6.speakerNotes.textFrame.setText('Las cuatro imágenes representan las cuatro variables o etapas de la tabla anterior. SSRD es la radiación solar descendente en la superficie, registrada por hora. El cálculo divide J/m² por 3.600.000 para obtener kWh/m². Un mes completo exige todas las horas esperadas, únicas y finitas. La media interanual promedia enero, abril, julio y octubre entre los años disponibles. La estimación anual convierte a media diaria y pondera por días de cada estación. Cada silueta corresponde esquemáticamente a Santa Fe. Los símbolos de reloj, calendario, años y estaciones son ilustraciones, no mapas de valores observados. Ilustración generada con IA. Fuentes: '+root+'/src/climate/arco.py y '+root+'/src/climate/climatology.py');
const s9=p.resolve('sl/udsvah03');clear(s9,8);
await image(s9,'v3_restricciones.png',60,195,1160,377,{left:0,top:.18,right:0,bottom:.18});
const rules=[['Contigüidad','Agregar celdas que\ncomparten un borde'],['Exclusión urbana','Excluir celdas que tocan\no intersectan la ciudad'],['Potencia por área','P = área del parque\n× 31,3 MW/km²'],['Límite experimental','Aceptar crecimiento\nmientras P ≤ 80 MW']];
rules.forEach((v,i)=>{const x=90+i*278;text(s9,v[0],x,143,269,52,26,C.teal,true);text(s9,v[1],x,580,267,63,21);});
text(s9,'Reglas del modelo. Las celdas recortadas conservan su área real',60,641,1130,30,19,C.muted);
s9.speakerNotes.textFrame.setText('Las imágenes ilustran las reglas del evaluador. Contigüidad: cada celda añadida procede de la frontera de vecinos por borde. Exclusión urbana: se elimina toda celda que toca o intersecta la máscara urbana, incluso huecos internos con la política actual. Potencia por área: se usa el área real, no una cuenta fija de celdas. Límite experimental: el crecimiento debe mantener P≤80 MW. No es la capacidad real de una estación. Las geometrías de la ilustración son conceptuales. La densidad de referencia se explica en la siguiente diapositiva. Ilustración generada con IA. Fuentes: '+root+'/config.yaml y '+root+'/src/optimization/spatial.py');
const {slide:deriv}=p.slides.insert({after:s9});deriv.background.fill='#FFFFFF';
text(deriv,'Origen de los 7,825 MW por celda',60,40,1160,94,43,C.navy,true);
await image(deriv,'celda_solar.png',60,189,525,338);
text(deriv,'Área de una celda completa',645,160,565,47,29,C.teal,true);
text(deriv,'0,5 km × 0,5 km = 0,25 km²',645,214,565,62,31,C.navy,true);
text(deriv,'Densidad adoptada en config.yaml',645,305,565,47,29,C.teal,true);
text(deriv,'31,3 MW/km²',645,357,565,55,37,C.navy,true);
text(deriv,'0,25 × 31,3 = 7,825 MW',60,529,1130,67,43,C.teal,true);
text(deriv,'10 celdas completas: 2,5 km² × 31,3 = 78,25 MW',60,598,1130,40,27,C.navy,true);
text(deriv,'Referencia: NREL (2013), tabla ES-1. 7,9 acres/MWac ≈ 31,3 MWac/km²',60,642,1130,31,19,C.muted);
deriv.speakerNotes.textFrame.setText('La configuración adopta 31,3 MW/km² a partir del estudio de NREL Land-Use Requirements for Solar Power Plants in the United States, Ong et al. (2013), tabla ES-1. La media ponderada por capacidad para grandes plantas FV (>20 MW) es 7,9 acres/MWac de área total. Un acre son 0,0040468564224 km². 7,9 acres/MWac = 0,03197016573696 km²/MWac. Invertir da aproximadamente 31,279 MWac/km², redondeados en config.yaml a 31,3. Una celda completa de 500×500 m tiene 0,25 km². Su potencia estimada es 0,25×31,3=7,825 MW. Es un supuesto de densidad territorial del modelo, basado en instalaciones grandes de EEUU, no una medición de potencia de Santa Fe ni una producción derivada de la radiación. Aunque se muestre una celda aislada para la cuenta, la fuente se refiere a grandes instalaciones. Diez celdas completas:2,5×31,3=78,25 MW. Fuente pública: https://docs.nrel.gov/docs/fy13osti/56290.pdf . Fuente local: '+root+'/config.yaml . La ilustración solar es conceptual y generada con IA.');
const cycle=p.resolve('sl/6lsnupw7');clear(cycle,13);
await image(cycle,'v3_ciclo.png',60,135,1160,476);
text(cycle,'La generación 0 evalúa la población inicial antes del primer cruce',60,633,1120,36,21,C.muted);
cycle.speakerNotes.textFrame.setText('El diagrama conserva las etapas y parámetros de la tabla anterior: evaluar 50 individuos, conservar dos élites distintas, seleccionar por torneos de tres, cruzar con probabilidad75% y mutar con probabilidad20%, controlar duplicados y repetir hasta 200 generaciones. El archivo conserva candidatos por territorio. El flujo gráfico es conceptual: el código lleva dos élites directamente a la siguiente población y aplica los operadores a los hijos. Las probabilidades no garantizan mejora. La generación0 es la evaluación inicial. Ilustración generada con IA. Fuente:'+root+'/src/optimization/genetic_algorithm.py y '+root+'/config.yaml');
const cross=p.resolve('sl/gny5sjyp');clear(cross,15);
await image(cross,'v3_cruce.png',60,142,1160,435);
text(cross,'Padre A: 5 celdas, F = 0,5839',60,578,555,42,26,C.navy,true);
text(cross,'Hijo A: 6 celdas, F = 0,5937',660,578,550,42,26,C.teal,true);
text(cross,'El hijo reinterpreta los genes con la semilla A. B7 representa el entero 1986680326',60,638,1130,35,21,C.muted);
cross.speakerNotes.textFrame.setText('Evento real de la generación1 de la corrida con semilla42. Padre A semilla46504, genes[429014945,1856101005,1726844270,53904684]. Padre B semilla249997, genes[222056182,376207307,1261957109,1703992271,366345610,644229613,1986680326]. CorteA=4, corteB=6. HijoA conserva la semilla46504 y obtiene[429014945,1856101005,1726844270,53904684,1986680326]. A1–A4 y B1–B7 son alias para lectura del diagrama. El crossover del código también produce el hijo recíproco, omitido aquí para seguir el mismo hijo del ejemplo. El decoder vuelve a interpretar la secuencia completa, no traslada físicamente celdas de B. Fuente:'+root+'/src/optimization/crossover.py . Ilustración generada con IA y verificada contra los genes del ejemplo.');
// Refresh page numbers while preserving the rest of each source slide.
const updated=(await p.inspect({kind:'textbox',maxChars:200000})).ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
for(let i=0;i<p.slides.items.length;i++){const s=p.slides.items[i];for(const r of updated.filter(r=>r.kind==='textbox'&&r.slideIndex===i&&r.position.top===669))s.shapes.deleteById(p.resolve(r.id).id);if(i>0)text(s,String(i+1).padStart(2,'0'),1190,669,50,27,18,C.muted);}
await fs.mkdir(path.join(dir,'v3-previews'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,'v3-previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
const candidate=path.join(dir,'candidate_v3.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const final=path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026_v3.pptx');
const owners=[3,4,5,8,11,12,13,14,18,20,21,23];
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...owners.flatMap(x=>['--require-native-table-slide',String(x)])],requiredNativeTableOwnerSlides:owners,requiredNativeChartOwnerSlides:[16,19,21],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'reference',families:['Arial'],referencePath:source,referenceSha256:createHash('sha256').update(await fs.readFile(source)).digest('hex')},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation_v3.json')});
console.log(final);
