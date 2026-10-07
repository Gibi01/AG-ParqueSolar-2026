import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026';
const dir=path.join(root,'tmp/presentation_build');
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/pptx/Defensa_Proyecto_AG_Parques_Solares_2026_v2.pptx')));
const out=path.join(dir,'visual-v2-final');await fs.mkdir(out,{recursive:true});
const changed=[];
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});const bytes=new Uint8Array(await b.arrayBuffer());const name=`slide-${String(i+1).padStart(2,'0')}.png`;await fs.writeFile(path.join(out,name),bytes);const old=await fs.readFile(path.join(dir,'visual-v2-previews',name));if(createHash('sha256').update(bytes).digest('hex')!==createHash('sha256').update(old).digest('hex'))changed.push(i+1);}
console.log(JSON.stringify({slides:p.slides.items.length,renderDifferences:changed}));
