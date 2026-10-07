import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026',dir=path.join(root,'tmp/presentation_build/defensa_actual');
const P=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/pptx/Defensa_AG_SantaFe_2026_v4.pptx')));
if(P.slides.items.length!==24)throw new Error('Wrong slide count');
await fs.mkdir(path.join(dir,'final_previews'),{recursive:true});
let changed=[];
for(let i=0;i<24;i++){const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1}),bytes=new Uint8Array(await blob.arrayBuffer());const name=`slide-${String(i+1).padStart(2,'0')}.png`;await fs.writeFile(path.join(dir,'final_previews',name),bytes);const before=await fs.readFile(path.join(dir,'previews',name));if(createHash('sha256').update(before).digest('hex')!==createHash('sha256').update(bytes).digest('hex'))changed.push(i+1);}
console.log(JSON.stringify({slides:24,changed}));
