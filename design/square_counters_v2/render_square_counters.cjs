// Render the editable SVG layouts; source paintings and portraits are not changed.
const fs=require('fs'), path=require('path');
const sharp=require('C:/Users/garre/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname;
(async()=>{
 const data=JSON.parse(fs.readFileSync(path.join(root,'roster_manifest.json'),'utf8'));
 const panels=[]; const tests=[];
 for(const u of data.units){
  const file=path.join(root,'MODS','First Kernstown 1862','Graphics','Units',u.country,u.filename);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  await sharp(path.join(root,'masters',u.country,u.name+'.svg')).png().toFile(file);
  const meta=await sharp(file).metadata(); const {data:bytes,info}=await sharp(file).raw().toBuffer({resolveWithObject:true});
  let xmin=1024,ymin=1024,xmax=-1,ymax=-1;
  for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(bytes[(y*info.width+x)*4+3]>0){xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
  if(meta.width!==1024||meta.height!==1024||!meta.hasAlpha||xmin<60||ymin<60||xmax>963||ymax>963)throw Error('Invalid export: '+file);
  tests.push({name:u.name,dimensions:[meta.width,meta.height],alpha:true,visible_bounds:[xmin,ymin,xmax,ymax]});
  panels.push({input:await sharp(file).resize(250,250).toBuffer(),left:25+(u.index-1)%6*270,top:100+Math.floor((u.index-1)/6)*290});
 }
 const title=Buffer.from('<svg width="1640" height="60"><text x="20" y="32" font-family="Arial" font-size="28" fill="#eee4cc">KERNSTOWN / 23 MARCH 1862 — PAINTED SQUARE COUNTERS</text><text x="20" y="56" font-family="Arial" font-size="17" fill="#c5c6b6">18 formation counters • portraits reserved for division / army HQ • review exports, not an in-game capture</text></svg>');
 await sharp({create:{width:1640,height:980,channels:4,background:'#152327'}}).composite([{input:title,left:0,top:0},...panels]).png().toFile(path.join(root,'all_18_counters.png'));
 fs.writeFileSync(path.join(root,'export_validation.json'),JSON.stringify({count:tests.length,results:tests,game_tested:false},null,2));
 console.log('18 RGBA exports validated; overview sheet created.');
})().catch(e=>{console.error(e);process.exit(1)});
