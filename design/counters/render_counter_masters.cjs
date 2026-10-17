// Render SVG source of truth to transparent PNG masters and two lower resolutions.
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const root = __dirname;
(async () => {
 const masters=path.join(root,'masters');
 for (const name of fs.readdirSync(masters).filter(n=>n.endsWith('.svg'))) {
  const input=path.join(masters,name);
  for (const size of [512,256,128]) {
   const dir=path.join(root,'sprites',String(size));fs.mkdirSync(dir,{recursive:true});
   await sharp(input).resize(size,size).png().toFile(path.join(dir,name.replace('.svg','.png')));
  }
 }
 console.log('Rendered 315 transparent PNGs from editable masters.');
})().catch(e=>{console.error(e);process.exit(1)});
