import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const root='C:/Users/creis/OneDrive/Escritorio/AG-ParqueSolar-2026',dir=path.join(root,'tmp/presentation_build/defensa_nueva');
const P=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'output/pptx/Defensa_AG_SantaFe_2026.pptx')));
if(P.slides.items.length!==27)throw new Error('Wrong count');
await fs.mkdir(path.join(dir,'final_previews'),{recursive:true});
const changed=[];
for(let i=0;i<P.slides.items.length;i++){
 const b=await P.export({slide:P.slides.items[i],format:'png',scale:1}),bytes=new Uint8Array(await b.arrayBuffer());
 const name=`slide-${String(i+1).padStart(2,'0')}.png`;
 await fs.writeFile(path.join(dir,'final_previews',name),bytes);
 const expected=await fs.readFile(path.join(dir,[10,20].includes(i+1)?'adjusted':'previews',name));
 if(createHash('sha256').update(expected).digest('hex')!==createHash('sha256').update(bytes).digest('hex'))changed.push(i+1);
}
console.log(JSON.stringify({slides:P.slides.items.length,renderDifferences:changed}));
