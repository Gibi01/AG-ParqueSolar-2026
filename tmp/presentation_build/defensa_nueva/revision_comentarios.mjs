import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import {pathToFileURL} from 'node:url';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026',dir=path.join(root,'tmp/presentation_build/defensa_nueva');
const skill='C:/Users/creis/.codex/plugins/cache/openai-primary-runtime/presentations/26.1004.11800/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const P=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/pptx/Defensa_AG_SantaFe_2026_v2.pptx')));
const d=JSON.parse((await fs.readFile(path.join(dir,'evidence.json'),'utf8')).replace(/\bNaN\b/g,'null'));
const pixels=JSON.parse(await fs.readFile(path.join(dir,'solar_pixels_verificados.json'),'utf8'));
const notes=JSON.parse(await fs.readFile(path.join(dir,'notas_actuales.json'),'utf8'));
const base=JSON.parse(await fs.readFile(path.join(dir,'notes_final.json'),'utf8'));
function text(s,t,x,y,w,h,size=28,color='#253C49',bold=false){let a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none',verticalAlignment:'middle'};return a;}
async function img(s,name,x,y,w,h){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(dir,name))),contentType:'image/png',alt:name,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function clear(s){for(const a of [...s.images.items])s.images.deleteById(a.id);for(const a of [...s.shapes.items])if(a.position.top>125&&a.position.top<673)s.shapes.deleteById(a.id);}
const g=d.region_geojson.features[0].geometry,polys=g.type==='Polygon'?[g.coordinates]:g.coordinates,points=polys.flat(2);
const bounds=[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))];
function projection(b,w,h,pad){let cos=Math.cos((b[1]+b[3])/2*Math.PI/180),k=Math.min((w-2*pad)/((b[2]-b[0])*cos),(h-2*pad)/(b[3]-b[1])),ox=(w-(b[2]-b[0])*cos*k)/2,oy=(h-(b[3]-b[1])*k)/2;return p=>[ox+(p[0]-b[0])*cos*k,h-oy-(p[1]-b[1])*k];}
const f=projection([-63.2,-34.6,-59.3,-27.7],620,710,20),xy=p=>{let a=f(p);return [a[0]+110,a[1]+25];};
const outline=polys.map(p=>p.map(r=>r.map((c,i)=>`${i?'L':'M'}${xy(c).join(',')}`).join(' ')+' Z').join(' ')).join(' ');
const lo=Math.min(...pixels.map(p=>p.solar)),hi=Math.max(...pixels.map(p=>p.solar));
const col=v=>{let t=(v-lo)/(hi-lo);return `rgb(${Math.round(225-170*t)},${Math.round(236-100*t)},${Math.round(231-87*t)})`;};
let body=`<defs><clipPath id="province"><path d="${outline}"/></clipPath><linearGradient id="scale" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="${col(lo)}"/><stop offset="100%" stop-color="${col(hi)}"/></linearGradient></defs>`;
body+=`<path d="${outline}" fill="#EAF1F1"/><g clip-path="url(#province)">`;
for(const p of pixels){let a=xy([p.longitude-.05,p.latitude+.05]),b=xy([p.longitude+.05,p.latitude-.05]);body+=`<rect x="${a[0]}" y="${a[1]}" width="${b[0]-a[0]+.2}" height="${b[1]-a[1]+.2}" fill="${col(p.solar)}"/>`;}
body+=`</g><path d="${outline}" fill="none" stroke="#172F3E" stroke-width="2"/>`;
const label=(t,x,y,size=29,extra='')=>`<text x="${x}" y="${y}" font-family="Arial" font-size="${size}" fill="#253C49" ${extra}>${t}</text>`;
for(let lat=-34;lat<=-28;lat++){let [x,y]=xy([-63.2,lat]);body+=`<path d="M110 ${y}H${x+620}" stroke="#D2DDDF" stroke-dasharray="4 6"/>`+label(`${lat}°`,95,y+10,29,'text-anchor="end"');}
for(let lon=-63;lon<=-60;lon++){let [x,y]=xy([lon,-34.6]);body+=label(`${lon}°`,x,770,29,'text-anchor="middle"');}
body+=label('Longitud',420,817,33,'text-anchor="middle"')+label('Latitud',35,415,33,'transform="rotate(-90 35 415)" text-anchor="middle"');
body+=`<rect x="780" y="150" width="28" height="470" fill="url(#scale)" stroke="#60747C"/>`;
for(const v of [lo,1820,1840,1860,1880,hi]){let y=620-(v-lo)/(hi-lo)*470;body+=label(Math.round(v).toLocaleString('es-AR'),820,y+9,29);}
body+=label('kWh/m²/año',758,108,30)+label('Irradiación anual estimada',450,855,32,'text-anchor="middle"');
await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="960" height="880"><rect width="100%" height="100%" fill="white"/>${body}</svg>`)).png().toFile(path.join(dir,'solar_mapa_ejes.png'));
// Marker is deliberately enlarged to remain visible at provincial scale.
const s1=P.slides.items[0],pf=projection(bounds,700,850,35),p=pf([-62.0665474769,-30.4672828622]);
const factor=310/700,marker=[860+p[0]*factor,155+(440-850*factor)/2+p[1]*factor];
for(let r=0;r<2;r++)for(let c=0;c<3;c++)s1.shapes.add({geometry:'rect',position:{left:marker[0]-12+c*8,top:marker[1]-8+r*8,width:8,height:8},fill:'#439956',line:{fill:'white',width:.6}});
await img(s1,'emoji_candidato.png',marker[0]-124,marker[1]-42,70,70);
s1.shapes.add({geometry:'rightArrow',position:{left:marker[0]-54,top:marker[1]-6,width:35,height:13},fill:'#439956',line:{fill:'none',width:0}});
text(s1,'Parque candidato',820,605,350,35,23,'#367C86',true);
const s2=P.slides.items[1];clear(s2);await img(s2,'preguntas_visuales.png',535,150,220,445);await img(s2,'region.png',835,150,320,445);
text(s2,'¿Dónde ubicarlo?',67,190,450,75,33);text(s2,'¿Qué forma darle?',67,333,450,75,33);text(s2,'¿Cuánto puede crecer?',67,476,470,75,33);text(s2,'Una ubicación debe equilibrar recurso, superficie e infraestructura',64,631,1135,40,22,'#60747C');
const s3=P.slides.items[2];for(const a of [...s3.images.items])s3.images.deleteById(a.id);await img(s3,'planta_fotovoltaica_usuario.png',0,0,1280,623);
text(s3,'El área del parque incluye paneles, separación, caminos e infraestructura.',64,625,1135,32,23,'#253C49',true);
text(s3,'31,3 MW/km² de área total · Referencia: NREL (2013), 7,9 acres/MWac. No se calcula el área exacta de módulos.',64,659,1135,32,20,'#60747C');
const s4=P.slides.items[3];clear(s4);text(s4,'Santa Fe se dividió en celdas de 500 × 500 m. El tamaño es configurable.',64,137,1145,45,27,'#367C86',true);await img(s4,'variables_visuales.png',54,203,1170,330);
const names=['Irradiación solar','Distancia a líneas','Distancia a ET','Área y potencia'],desc=['Recurso anual estimado\nkWh/m²/año','Proximidad geométrica\nkm','Estación más cercana\nkm','Superficie total × densidad\nkm² → MW'];
for(let i=0;i<4;i++){let x=64+i*295;text(s4,names[i],x,519,280,44,25,'#172F3E',true);text(s4,desc[i],x,570,280,62,22);}
text(s4,'Cambiar el tamaño requiere reprocesar el dataset y ejecutar nuevamente el AG.',64,645,1135,32,22,'#60747C');
const s5=P.slides.items[4];clear(s5);await img(s5,'solar_mapa_ejes.png',43,137,660,477);
text(s5,'Mapa de calor del dataset',735,160,460,55,29,'#367C86',true);text(s5,'Valores procesados de ERA5-Land\n2024–2026 · 11 períodos',735,231,460,83,28);
text(s5,'De horas a un año estimado',735,350,460,65,29,'#172F3E',true);text(s5,'Meses completos → promedio\nentre años → ponderación\npor días de estación',735,426,460,125,27);
text(s5,'Reanálisis e indicador anual estimado; no son mediciones directas de producción.',64,631,1135,40,22,'#60747C');
const adds=[
'El conjunto verde y el emoji identifican visualmente un parque candidato. El marcador se amplía como símbolo para que sea legible a escala provincial; no representa la superficie a escala. Su ubicación se ancla al centroide del líder de la corrida. El contorno provincial procede de IGN y se conserva sin reconstruirlo con IA.',
'Las ilustraciones corresponden a las tres decisiones: el pin representa ubicación, los conjuntos de celdas representan formas posibles y el crecimiento representa la superficie que puede alcanzar un parque. Son ayudas conceptuales; no sustituyen los resultados geográficos de la corrida.',
'La densidad de 31,3 MW/km² se aplica al terreno TOTAL del parque, no a una superficie completamente cubierta por módulos. Su referencia es la media de 7,9 acres/MWac de superficie total para parques fotovoltaicos grandes (>20 MW) del estudio NREL de 2013. La conversión es 1/(7,9 × 0,0040468564) = 31,279 MWac/km², redondeada en la configuración a 31,3. El área total incluye espacios de separación y otras instalaciones. Incluso el concepto de área directa de NREL incluye caminos y subestaciones, por lo que no equivale al área de paneles. El código no calcula una fracción exacta de cobertura ni la superficie de módulos: usa una densidad agregada constante como supuesto. No se debe defender 31,3 como eficiencia del panel, producción eléctrica o un valor específico medido en Santa Fe. Fuente: https://docs.nlr.gov/docs/fy13osti/56290.pdf , tabla ES-1 y definiciones de uso de suelo. La distinción MW/MWh sigue vigente: MW es potencia; MWh es energía durante un período.',
'El tamaño de 500 × 500 m corresponde a grid.resolution_km = 0.5. GridConfig admite un valor positivo configurable; el generador convierte kilómetros a metros para construir la grilla. Cambiarlo exige reprocesar las fuentes y crear otro snapshot, porque altera el número de celdas, sus áreas y los posibles crecimientos. No basta cambiarlo en una corrida que utiliza el dataset anterior. Cada ilustración representa un criterio implementado; la potencia se deriva del área total mediante la densidad constante. Fuentes: config.yaml, src/config/settings.py y src/gis/grid.py (constructor de la grilla).',
'El mapa revisado es un mapa de calor geográfico del indicador de irradiación anual estimada del dataset. Se verificaron 1370 píxeles climáticos: el valor es constante para las celdas válidas vinculadas al mismo píxel. Para dibujarlo se usan las coordenadas nativas ERA5 guardadas en pixel_months, con cuadrados de 0,1° y recorte por el contorno IGN. Los ejes son latitud y longitud en grados y el color corresponde a kWh/m²/año, aproximadamente 1796–1896. No se interpolan círculos ni se inventa un gradiente. Es evidencia del procesamiento del modelo, no una medición directa de cada parcela ni un mapa de producción. El indicador usa once períodos completos entre 2024 y julio de 2026 y una estimación estacional, por lo que no equivale a una climatología de largo plazo. Fuentes: snapshot SQLite del dataset de la corrida, tablas spatial_cells y pixel_months; src/climate/climatology.py; contorno oficial IGN.'
];
for(let i=0;i<27;i++){if(i===4)notes[i]=notes[i].replace('Los puntos del mapa representan agregados por píxel climático, no una medición independiente por celda.','El color muestra el indicador del píxel climático nativo, no una medición independiente por celda.');if(i<5)notes[i]+='\n\nACLARACIÓN DE LA REVISIÓN\n'+adds[i];P.slides.items[i].speakerNotes.textFrame.setText(notes[i]);}
await fs.writeFile(path.join(root,'output/pptx/Guia_Defensa_AG_SantaFe_2026_v3.md'),'# Guía ampliada para la defensa\n\n24 diapositivas principales, unos 25 minutos; 3 diapositivas de apoyo.\n\n'+notes.map((n,i)=>`## ${i+1}. ${base[i].title}\n\n${n}\n\n`).join(''));
await fs.mkdir(path.join(dir,'comentarios_previews'),{recursive:true});
for(let i=0;i<5;i++){const png=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,`comentarios_previews/slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));}
const candidate=path.join(dir,'candidate_comentarios.pptx');await(await PresentationFile.exportPptx(P)).save(candidate);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'output/pptx/Defensa_AG_SantaFe_2026_v3.pptx'),pythonExecutable:'C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[24,25,26].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[24,25,26],requiredNativeChartOwnerSlides:[10,18,20],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:['Georgia','Arial']},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation_comentarios_final.json')});
console.log('READY_V3');


