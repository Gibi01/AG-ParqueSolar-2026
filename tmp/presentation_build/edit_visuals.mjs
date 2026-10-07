import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026';
const dir=path.join(root,'tmp/presentation_build');
const skill='C:/Users/creis/.codex/plugins/cache/openai-primary-runtime/presentations/26.1004.11800/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const source=path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026.pptx');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const s6=p.resolve('sl/x8f69ofe'),s9=p.resolve('sl/udsvah03');
const C={navy:'#102A43',teal:'#087F8C',ink:'#183B4E',muted:'#526778',pale:'#EEF5F5'};
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false){let z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=t;z.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none',verticalAlignment:'middle'};return z;}
async function image(s,name,x,y,w,h){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(dir,name))),contentType:'image/png',alt:name,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
for(const id of ['sh/98rqt4r6','sh/7m98ru9g'])s6.shapes.deleteById(p.resolve(id).id);
s6.tables.deleteById(p.resolve('tb/3uh4nud4').id);
p.resolve('sh/zi98nu94').position={left:60,top:154,width:380,height:45};
p.resolve('sh/87ipkzal').position={left:60,top:203,width:380,height:60};
p.resolve('sh/87ipkzal').text.style={typeface:'Arial',fontSize:40,color:C.navy,bold:true,autoFit:'none'};
await image(s6,'santafe_grilla.png',62,277,358,325);
text(s6,'Grilla esquemática de Santa Fe',60,613,380,36,19,C.muted);
const values=[['Variable / etapa','Tratamiento','Qué representa'],['Horas SSRD','J/m² ÷ 3.600.000','Radiación solar recibida en la superficie'],['Mes completo','100% de horas válidas','Todas las horas del mes deben tener datos'],['Media interanual','Enero, abril, julio, octubre','Promedio de cada mes entre años completos'],['Estimación anual','Media diaria × días de estación','Suma estacional en kWh/m²/año']];
const t=s6.tables.add({rows:5,columns:3,left:470,top:178,width:740,height:425,columnWidths:[185,255,300],values});
for(let r=0;r<5;r++)for(let c=0;c<3;c++){const z=t.getCell(r,c);z.fill=r===0?C.navy:r%2?'#FFFFFF':C.pale;z.text.style={typeface:'Arial',fontSize:23,color:r===0?'#FFFFFF':C.ink,bold:r===0};}
t.borders.assign({fill:'#CFDCE0',width:1,style:'solid'});
s6.speakerNotes.textFrame.setText('SSRD representa la radiación solar descendente que recibe la superficie. El código suma valores horarios y convierte J/m² a kWh/m² dividiendo por 3.600.000. Un mes completo exige todas las horas esperadas, únicas y finitas. Luego calcula medias interanuales de enero, abril, julio y octubre. La estimación anual multiplica las medias diarias por los días de las estaciones y suma sus aportes. La imagen provincial con celdas es una ilustración esquemática generada con IA, no una representación de las 535.751 celdas reales ni de su validez. Fuentes: '+root+'/src/climate/arco.py y '+root+'/src/climate/climatology.py');
s9.shapes.deleteById(p.resolve('sh/nex4jq5k').id);
await image(s9,'celda_solar.png',60,220,575,315);
text(s9,'7,825 MW',487,344,162,62,28,C.navy,true);
text(s9,'Potencia\nestimada',487,413,157,65,20,C.muted);
p.resolve('sh/0b65obm9').text='Una celda completa: 25 ha';
p.resolve('sh/mdonql4z').position={left:60,top:546,width:570,height:62};
text(s9,'Radiación solar recibida',68,223,330,36,20,C.teal,true);
s9.speakerNotes.textFrame.setText('Una celda completa mide 500 × 500 m y tiene 25 ha, equivalentes a 0,25 km². El proyecto estima su potencia instalada con la densidad configurada de 31,3 MW/km²: 0,25 × 31,3 = 7,825 MW. La radiación que llega a la celda y su potencia instalada son conceptos distintos. MW expresa potencia, no energía anual. La ilustración es conceptual, generada con IA, y muestra una celda dentro de Santa Fe, una ampliación con paneles y rayos solares. Diez celdas completas representan 78,25 MW. Se mantienen contigüidad por borde, exclusión urbana y el límite experimental de 80 MW. Los fragmentos del límite provincial conservan su área real. Fuentes: '+root+'/config.yaml y '+root+'/src/optimization/spatial.py');
const candidate=path.join(dir,'candidate_visual_v2.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
await fs.mkdir(path.join(dir,'visual-v2-previews'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,'visual-v2-previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
const final=path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026_v2.pptx');
const owners=[3,4,5,6,8,9,10,11,12,13,14,16,17,19,20,22];
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...owners.flatMap(x=>['--require-native-table-slide',String(x)])],requiredNativeTableOwnerSlides:owners,requiredNativeChartOwnerSlides:[15,18,20],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'reference',families:['Arial'],referencePath:source,referenceSha256:createHash('sha256').update(await fs.readFile(source)).digest('hex')},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation_visual_v2.json')});
console.log(final);
