import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026';
const dir=path.join(root,'tmp/presentation_build/defensa_nueva');
const skill='C:/Users/creis/.codex/plugins/cache/openai-primary-runtime/presentations/26.1004.11800/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const P=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/pptx/Defensa_AG_SantaFe_2026_Redisenada.pptx')));
const n=JSON.parse(await fs.readFile(path.join(dir,'notes.json'),'utf8'));
const d=JSON.parse((await fs.readFile(path.join(dir,'evidence.json'),'utf8')).replace(/\bNaN\b/g,'null'));
const clean=s=>s.replace(/([a-záéíóúñ])(\d)/gi,'$1 $2').replace(/(\d)([a-záéíóúñ])/gi,'$1 $2');
for(let i=0;i<n.length;i++){
 const x=n[i];for(const k of ['explanation','decision','limits'])x[k]=clean(x[k]);
 x.sources=x.sources.map(s=>s.replace(root+'/'+root+'/',root+'/'));
 let note=`Tiempo sugerido: ${x.time} minutos${i>=24?' (apoyo para preguntas)':''}\n\nEXPLICACIÓN\n${x.explanation}\n\nDECISIONES Y JUSTIFICACIÓN\n${x.decision}\n\nALCANCE Y LÍMITES\n${x.limits}\n\nFUENTES\n${x.sources.join('\n')}\nCorrida: ${d.run_dir}\nSemilla: 20261006. Dataset: ${d.metadata.dataset_id}\nLas ilustraciones son conceptuales. Todos los contornos de Santa Fe proceden de la geometría oficial IGN del dataset existente. Los eventos de cruce y mutación son registros de la corrida nueva.`;
 if(i===14)note+=`\nGenes A: ${JSON.stringify(d.crossover.a.genes)}\nGenes B: ${JSON.stringify(d.crossover.b.genes)}\nGenes hijo A: ${JSON.stringify(d.crossover.child.genes)}`;
 P.slides.items[i].speakerNotes.textFrame.setText(note);
}
const snap=(await P.inspect({kind:'chart',maxChars:20000})).ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
for(const [num,max,format] of [[10,.5,'0%'],[20,.8,'0.00']]){
 const rec=snap.find(r=>r.kind==='chart'&&r.slideIndex===num-1);if(!rec)throw new Error('Missing chart '+num);
 const c=P.resolve(rec.id);c.xAxis={visible:true,textStyle:{typeface:'Arial',fontSize:22,fill:'#253C49'}};c.yAxis={visible:false,min:0,max,numberFormatCode:format,textStyle:{typeface:'Arial',fontSize:22,fill:'#253C49'}};
}
const candidate=path.join(dir,'candidate_final.pptx');await(await PresentationFile.exportPptx(P)).save(candidate);
await fs.mkdir(path.join(dir,'adjusted'),{recursive:true});
for(const i of [10,20]){const b=await P.export({slide:P.slides.items[i-1],format:'png',scale:1});await fs.writeFile(path.join(dir,'adjusted',`slide-${i}.png`),new Uint8Array(await b.arrayBuffer()));}
let guide=await fs.readFile(path.join(root,'output/pptx/Guia_Defensa_AG_SantaFe_2026.md'),'utf8');
const pre=guide.slice(0,guide.indexOf('## 1.'));
guide=pre+n.map(x=>`## ${x.number}. ${x.title}\n\nTiempo: ${x.time?x.time+' minutos':'apoyo para preguntas'}.\n\n**Explicación para exponer:** ${x.explanation}\n\n**Decisiones y justificación:** ${x.decision}\n\n**Alcance y límites:** ${x.limits}\n\n**Fuentes:**\n\n${x.sources.map(s=>'- '+s).join('\n')}\n\n`).join('');
guide+='## Imágenes y cartografía\n\nTodas las imágenes de Santa Fe usan la geometría oficial IGN del dataset preparado, conservando su contorno. Las ilustraciones conceptuales de paneles, transformadores, operadores y flujo se generaron con la herramienta integrada imagegen y se guardaron en tmp/presentation_build/defensa_nueva. Los mapas, formas de parques y gráficas usan los datos de la nueva corrida.\n\nPrompts utilizados: flujo paneles–inversor–transformador–red; flujo fuentes–caché–grilla rectangular–dataset–búsqueda sin siluetas provinciales; torneo de tres candidatos sin puntajes inventados; crossover real A1 A2 A3 + B5 B6 con cortes 3 y 4; factores pendientes de pendiente, agua, protección ambiental, suelo y capacidad de red.\n';
await fs.writeFile(path.join(root,'output/pptx/Guia_Defensa_AG_SantaFe_2026.md'),guide);
await fs.writeFile(path.join(dir,'notes_final.json'),JSON.stringify(n,null,2));
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'output/pptx/Defensa_AG_SantaFe_2026.pptx'),pythonExecutable:'C:/Users/creis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[24,25,26].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[24,25,26],requiredNativeChartOwnerSlides:[10,18,20],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:['Georgia','Arial']},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation_final.json')});
console.log('FINAL_READY');

