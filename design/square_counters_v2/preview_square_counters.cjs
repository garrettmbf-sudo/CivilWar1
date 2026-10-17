const fs=require('fs'),path=require('path');
const sharp=require('C:/Users/garre/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname;
const mapPath='C:/Users/garre/.codex/.chatgpt-projects/g-p-6ad11f6471d8819184b9b19af1b48218/counter-design-work/previews/counter_source_full.jpg';
(async()=>{
 const units=JSON.parse(fs.readFileSync(path.join(root,'roster_manifest.json'),'utf8')).units;
 const zoom=20, H=1080, p=H/(2*zoom), R=(4.42/1.5)*p, scale=R/72.59024934521165;
 const meta=await sharp(mapPath).metadata();
 const map=await sharp(mapPath).resize(Math.round(meta.width*scale),Math.round(meta.height*scale)).png().toBuffer();
 const height=Math.round(meta.height*scale);
 const center=(c,r)=>[1.5*R*c,height-Math.sqrt(3)*R*(r+.5*(c%2))];
 const side=Math.round(1024/100*.37*p);
 const metrics=[];
 for(const mode of ['deployment','adjacent']){
  const positions=units.map((u,i)=>mode==='deployment'?u.grid_pos:[16+i%5,23+Math.floor(i/5)]);
  const points=positions.map(a=>center(...a));
  const left=Math.floor(Math.min(...points.map(a=>a[0]))-100),top=Math.floor(Math.min(...points.map(a=>a[1]))-100);
  const width=Math.ceil(Math.max(...points.map(a=>a[0]))-left+100),cropHeight=Math.ceil(Math.max(...points.map(a=>a[1]))-top+100);
  const items=[];
  for(let i=0;i<units.length;i++){
   const u=units[i]; const file=path.join(root,'MODS','First Kernstown 1862','Graphics','Units',u.country,u.filename);
   // Approximate inspected 512-wide loader stage, then projected 1024-source size.
   const input=await sharp(await sharp(file).resize(512,512,{kernel:'linear'}).png().toBuffer()).resize(side,side,{kernel:'linear'}).toBuffer();
   items.push({input,left:Math.round(points[i][0]-left-side/2),top:Math.round(points[i][1]-top-side/2)});
  }
  const crop=await sharp(map).extract({left,top,width,height:cropHeight}).composite(items).png().toBuffer();
  const title=`${mode==='deployment'?'SUPPLIED DEPLOYMENT':'ARTIFICIAL ADJACENT-HEX TEST'} / 18 COUNTERS`;
  const label=Buffer.from(`<svg width="${width}" height="100"><text x="15" y="30" font-family="Arial" font-size="23" fill="#eee4cc">${title}</text><text x="15" y="60" font-family="Arial" font-size="17" fill="#c2c8bd">Offline map composite: 1080px viewport model, S=20, ${side}px sprite canvas.</text><text x="15" y="85" font-family="Arial" font-size="16" fill="#c2c8bd">Painted map reference; no native game overlays. Historical deployment is user-supplied.</text></svg>`);
  await sharp({create:{width,height:cropHeight+100,channels:4,background:'#152327'}}).composite([{input:label,left:0,top:0},{input:crop,left:0,top:100}]).png().toFile(path.join(root,mode+'_map_preview.png'));
  // Conservative bounding-box test. Canvas clearance also proves opaque clearance.
  let minimum=Infinity;
  for(let i=0;i<points.length;i++)for(let j=0;j<i;j++)minimum=Math.min(minimum,Math.max(Math.abs(points[i][0]-points[j][0]),Math.abs(points[i][1]-points[j][1]))-side);
  metrics.push({mode,units:units.length,canvas_px:side,hex_width_px:2*R,minimum_canvas_clearance_px:minimum,overlap:minimum<0});
 }
 fs.writeFileSync(path.join(root,'map_scale_validation.json'),JSON.stringify({model:'Static inspected engine projection, not live game validation',orthographic_size:20,screen_height:1080,results:metrics},null,2));
 console.log(metrics);
})().catch(e=>{console.error(e);process.exit(1)});
