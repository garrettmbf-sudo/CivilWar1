"""Composite editable UI sprites onto the unaltered Kernstown branch map preview."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,math,csv,hashlib,zipfile
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
F=Path('C:/Windows/Fonts')
def ft(n,b=False):
 for path in [F/('arialbd.ttf' if b else 'arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]:
  if path.exists():return ImageFont.truetype(str(path),n)
 return ImageFont.load_default()
def text(im,xy,s,n=20,fill='#eee4ce',b=False):ImageDraw.Draw(im).text(xy,s,font=ft(n,b),fill=fill)
R=44.0; ORIGINAL_R=72.59024934521165; H=6723;SCALE=R/ORIGINAL_R
# compose_painted_map.py uses geographic north-up: x=1.5Rcol; y=H - sqrt(3)R(row+parity/2).
def center(c,r):return (1.5*R*c,H*SCALE-math.sqrt(3)*R*(r+.5*(c&1)))
CROP=(740,1750,2100,2910)
def sprite(style,id,size=70):return Image.open(D/'sprites/512'/f'{style.lower()}_{id}.png').convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
def main():
 units=json.loads((D/'roster.json').read_text());P=D/'previews';P.mkdir(exist_ok=True)
 source=ROOT/'previews/counter_source_full.jpg'
 if not source.exists():source=ROOT/'previews/kernstown_full.jpg'
 base=Image.open(source).convert('RGBA');assert base.size==(6635,6723)
 base=base.resize((round(base.width*SCALE),round(base.height*SCALE)),Image.Resampling.LANCZOS).crop(CROP)
 width,height=base.size
 # Empty map retained as exact reference for terrain visibility assessment.
 base.convert('RGB').save(P/'map_reference.jpg',quality=93)
 stats=[];panels=[]
 for style,title in [('A','Historical Command'),('B','Traditional Wargame'),('C','Illustrated Formation'),('D','Commander Portrait'),('E','Preferred: soldiers for brigades / faces for HQ')]:
  m=base.copy();coverage=Image.new('L',m.size,0);al=Image.new('L',m.size,0)
  for u in units:
   sp=sprite(style,u['id']);x,y=center(u['col'],u['row']);pos=(round(x-CROP[0]-35),round(y-CROP[1]-35))
   m.alpha_composite(sp,pos);al.paste(sp.getchannel('A'),pos);coverage=ImageChops.lighter(coverage,al)
  opaque=sum(1 for v in coverage.get_flattened_data() if v>127)
  # White border labels stay outside the map, never hide terrain.
  panel=Image.new('RGB',(width,height+142),'#152327');panel.paste(m.convert('RGB'),(0,112))
  text(panel,(25,15),f'{style} / {title.upper()}',30,b=True)
  text(panel,(25,57),'20 counters  |  88 px hex width  |  56 px counter width  |  identical positions',21,fill='#bbc8c1')
  text(panel,(25,85),'18 branch units + Jackson HQ / Kimball acting HQ added for visual stress only',16,fill='#d0b981')
  text(panel,(25,height+119),'Map preview composite; target scale proposed. In-game camera/import validation remains required.',17,fill='#bbc8c1')
  panel.save(P/f'{style.lower()}_map_20.png');panels.append(panel)
  stats.append(dict(style=style,opaque_pixels=opaque,map_pixels=width*height,viewport_coverage_pct=round(opaque/(width*height)*100,3),hex_radius_px=44,counter_visible_width_px=56,opaque_area_over_hex_area_pct=round((opaque/20)/(3*math.sqrt(3)/2*R*R)*100,2)))
 # Artificial adjacent-hex cluster: same 20 identities, no claim of historical deployment.
 dense_panels=[]
 for style in 'ABCDE':
  m=base.copy();clusters=[]
  for i,u in enumerate(units):
   c=16+i%5;r=23+i//5;clusters.append([c,r]);sp=sprite(style,u['id']);x,y=center(c,r);m.alpha_composite(sp,(round(x-CROP[0]-35),round(y-CROP[1]-35)))
  # One-to-one crop: this is a magnifier viewport, no upscaling.
  pts=[center(c,r) for c,r in clusters];left=round(min(p[0] for p in pts)-CROP[0]-65);top=round(min(p[1] for p in pts)-CROP[1]-55)
  region=m.crop((left,top,left+400,top+400));pan=Image.new('RGB',(440,525),'#152327');pan.paste(region.convert('RGB'),(20,85));text(pan,(15,14),style+' / ADJACENT-HEX STRESS',22,b=True);text(pan,(15,46),'20 units • 56 px width • same map scale',16,fill='#bbc8c1');text(pan,(15,495),'Artificial placements; visual test only.',17,fill='#d0b981');pan.save(P/f'{style.lower()}_dense_20.png');dense_panels.append(pan)
 dense_sheet=Image.new('RGB',(880,1050),'#152327')
 for i,pan in enumerate(dense_panels[:4]):dense_sheet.paste(pan,((i%2)*440,(i//2)*525))
 dense_sheet.save(P/'four_designs_dense_20.png')
 # 2x2 comparison, no resampling; each panel is available separately at original pixel size.
 sheet=Image.new('RGB',(width*2,(height+142)*2),'#152327')
 for i,panel in enumerate(panels[:4]):sheet.paste(panel,((i%2)*width,(i//2)*(height+142)))
 sheet.save(P/'four_designs_map_comparison.jpg',quality=94)
 # Large detailed master comparison with same two people across all four directions.
 detail=Image.new('RGB',(1800,1260),'#152327');text(detail,(55,32),'FOUR DIRECTIONS / EXACT APPROVED PORTRAITS',37,b=True)
 text(detail,(55,90),'Enlarged inspection above; true-size 56 px footprints below. All strengths and movement values remain unset.',21,fill='#bbc8c1')
 for i,style in enumerate('ABCD'):
  x=45+i*440;text(detail,(x,150),{'A':'A  HISTORICAL COMMAND','B':'B  TRADITIONAL WARGAME','C':'C  ILLUSTRATED FORMATION','D':'D  COMMANDER PORTRAIT'}[style],21,b=True)
  for j,id in enumerate(['k01','k11']):
   sp=sprite(style,id,360);detail.paste(sp,(x+20,200+j*355),sp)
  sp=sprite(style,'k01');detail.paste(sp,(x+45,980),sp);sp=sprite(style,'k11');detail.paste(sp,(x+175,980),sp)
  text(detail,(x+35,1085),'56 px visible width  /  88 px hex',19,fill='#bbc8c1')
 text(detail,(55,1165),'Original four directions. Preferred hybrid: C brigade formations + D headquarters portraits.',24,fill='#d0b981',b=True)
 text(detail,(55,1210),'No invented faces. Missing officer portraits use military symbols. These are review candidates.',21,fill='#bbc8c1')
 detail.save(P/'four_designs_details.png')
 # State examples are visual vocabulary, not purported historical starting conditions.
 state=Image.new('RGB',(1600,620),'#152327');text(state,(45,30),'PREFERRED FORMATION COUNTER / CONDITIONS',35,b=True)
 text(state,(45,88),'Independent examples - no troop-quality stars, rank stars, or invented ratings.',22,fill='#bbc8c1')
 for i,(key,label) in enumerate([('normal','NORMAL'),('shaken','MORALE: SHAKEN'),('fatigued','FATIGUED'),('forced','FORCED MARCH'),('supply','IN SUPPLY')]):
  sp=Image.open(D/'sprites/512'/f'hybrid_garnett_{key}.png').resize((280,280),Image.Resampling.LANCZOS);state.paste(sp,(20+i*315,150),sp);text(state,(35+i*315,440),label,20,b=True)
 text(state,(45,520),'! = morale warning   F = fatigue   >> = forced-march state   + = supply',23,fill='#d0b981')
 text(state,(45,560),'Capability belongs in the unit interface until its rule and value are verified. State is separate from capability.',20,fill='#bbc8c1')
 state.save(P/'hybrid_condition_examples.png')
 preferred=Image.new('RGB',(1600,1010),'#152327');text(preferred,(45,30),'PREFERRED / SOLDIERS FOR BRIGADES, FACES FOR COMMAND',32,b=True)
 text(preferred,(45,83),'Same compact footprint. Approved portrait inset on brigades; face-led headquarters.',22,fill='#bbc8c1')
 for i,(id,label) in enumerate([('k01','GARNETT / STONEWALL BDE'),('k11','KIMBALL / 1ST BDE'),('k19','JACKSON / VALLEY HQ'),('k20','KIMBALL / ACTING DIV HQ')]):
  x=30+i*395;sp=sprite('E',id,370);preferred.paste(sp,(x,150),sp);text(preferred,(x+5,555),label,19,b=True);sp=sprite('E',id);preferred.paste(sp,(x+145,610),sp)
 text(preferred,(45,730),'Brigades: infantry formation + small unchanged commander image.',26,fill='#d0b981',b=True)
 text(preferred,(45,780),'HQ: commander portrait dominates. Kernstown has no invented corps headquarters.',23,fill='#bbc8c1')
 text(preferred,(45,840),'No approved portrait? Keep the correct name and formation symbol until one is supplied.',22,fill='#bbc8c1')
 text(preferred,(45,900),'Ordinary-scale proof: 56 px visible width against 88 px hex width; enlarged views above.',22,fill='#bbc8c1')
 text(preferred,(45,950),'Review candidate; numerical unit ratings and in-game import remain unverified.',21,fill='#bbc8c1');preferred.save(P/'preferred_formation_and_hq.png')
 (D/'coverage_metrics.json').write_text(json.dumps(stats,indent=2)+'\n')
 # Atlas and explicit pixel metadata; frames retain fixed center pivots.
 atlas_manifest={'format':'RGBA PNG','frame_size':512,'pivot_normalized':[.5,.5],'engine_binding':'unverified; review assets only','atlases':{}}
 for style in 'ABCDE':
  atlas=Image.new('RGBA',(2048,2560));frames={}
  for i,u in enumerate(units):
   im=Image.open(D/'sprites/512'/f'{style.lower()}_{u["id"]}.png');x=i%4*512;y=i//4*512;atlas.paste(im,(x,y));frames[u['id']]={'rect':[x,y,512,512],'name':u['name'],'portrait':u['portrait']}
  atlas.save(D/'sprites'/f'{style.lower()}_atlas.png');atlas_manifest['atlases'][style]={'file':f'{style.lower()}_atlas.png','frames':frames}
 (D/'sprites/atlas_manifest.json').write_text(json.dumps(atlas_manifest,indent=2)+'\n')
 print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
