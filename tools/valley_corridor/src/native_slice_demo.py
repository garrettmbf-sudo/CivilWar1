"""Small experimental proof of actual Hex of Steel PNG export by SHARED CANVAS slicing.
3 x 3 Strasburg neighborhood; native 2000x2000 stock flat-top mask, 250yd spacing.
Artwork is synthetic and NOT a trace of historical 1862 farm boundaries or bridges.
"""
from __future__ import annotations
from pathlib import Path
import sys, math,random,json,io,zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
sys.path.insert(0,str(Path(__file__).resolve().parent))
import valley_corridor as vc
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tiles_demo';OUT.mkdir(exist_ok=True)
# Prefer existing stock reference bundled in CivilWar1; never redistribute game-owned artwork.
stock_png=ROOT.parents[1]/'maps'/'Plain.png'
if stock_png.exists():
 MASK=Image.open(stock_png).convert('RGBA').getchannel('A')
elif Path('/mnt/data/civilhex.zip').exists():
 with zipfile.ZipFile('/mnt/data/civilhex.zip') as z:
  MASK=Image.open(io.BytesIO(z.read('civilhex/Plain.png'))).convert('RGBA').getchannel('A')
else:
 raise SystemExit('Place a stock Hex of Steel Plain.png in the repository maps/ directory before slicing.')
SZ=2000;CX=CY=999.5;HW=1910;HH=1672;CP=1432.5;RP=1672
CC,RR=vc.lonlat_hex(-78.36,38.989)
C0=CC-1;R0=RR-1; NC=NR=3
CENTERS={}
for ic in range(NC):
 for ir in range(NR):
  col=C0+ic;row=R0+ir
  CENTERS[(col,row)]=(int(round(1000+ic*CP)),int(round(1000+(2-ir-.5*(col&1))*RP+1400)))
MAXX=max(x for x,y in CENTERS.values())+1000
MAXY=max(y for x,y in CENTERS.values())+1000
MINX=min(x for x,y in CENTERS.values())-1000
MINY=min(y for x,y in CENTERS.values())-1000
assert MINX>=0 and MINY>=0,(MINX,MINY)
W=MAXX;H=MAXY
print('shared canvas',W,H,'center Hex',CC,RR,'and positions',CENTERS,flush=True)
rng=random.Random(33)
# low-frequency handpainted tones with continuity across entire canvas
low_w=max(200,W//16);low_h=max(200,H//16)
rngnp=np.random.default_rng(1862)
noise=rngnp.normal(.5,.19,size=(low_h,low_w)).astype(np.float32)
bl=np.asarray(Image.fromarray(np.uint8(np.clip(noise,0,1)*255),'L').filter(ImageFilter.GaussianBlur(9)))
base=Image.fromarray(bl,'L').resize((W,H),Image.Resampling.BICUBIC)
# low memory palette / RGB LUT in-place
rgb=Image.new('RGB',(W,H),(184,160,121))
# tinted texture via mode L->RGB and opacity; naturally undulates and soft
import PIL.ImageChops
palette=Image.new('RGB',(256,1))
pix=palette.load()
for v in range(256):
 a=(v-125)/125
 pix[v,0]=(int(max(0,min(255,183+a*24))),int(max(0,min(255,154+a*20))),int(max(0,min(255,112+a*19))))
base=base.point([i for i in range(256)])
rgb=base.convert('RGB');rgb.putpalette(None) if rgb.mode=='P' else None
# map a tonal gradient to RGB through a low-memory numpy LUT in 512px vertical bands
lut=np.array([pix[v,0] for v in range(256)],dtype=np.uint8)
for top in range(0,H,512):
 bot=min(H,top+512)
 band=np.asarray(base.crop((0,top,W,bot)),dtype=np.uint8)
 rgb.paste(Image.fromarray(lut[band],'RGB'),(0,top))
base.close();canvas=rgb.convert('RGBA');rgb.close()
d=ImageDraw.Draw(canvas,'RGBA')
# road passage drawn as one continuous regional vector from the original pike geography.
# Convert lon/lat directly to world canvas coords from center of reference hex.
origin_w=vc.hex_xy(CC,RR)
rx,ry=CENTERS[(CC,RR)]
scale=955/vc.R

def world_to_canvas(lon,lat):
 wx,wy=vc.lonlat_xy(lon,lat)
 return (rx+(wx-origin_w[0])*scale,ry-(wy-origin_w[1])*scale)

# irregular tilled field parcels and fences (no artificial hex-based stopping)
for _ in range(125):
 x=rng.uniform(200,W-200);y=rng.uniform(200,H-200)
 ww=rng.uniform(160,650);hh=rng.uniform(180,600)
 pts=[(x-ww*.51,y-hh*.48),(x+ww*.46,y-hh*.45),(x+ww*.53,y+hh*.48),(x-ww*.47,y+hh*.5)]
 col=rng.choice([(145,106,79,90),(200,167,124,80),(120,96,73,68),(177,154,109,68)])
 d.polygon(pts,fill=col)
 if rng.random()<.28:
  d.line(pts+[pts[0]],fill=(91,70,49,145),width=4)
 for t in range(2,13):
  if rng.random()<.4:
   yy=y-hh*.42+t*hh/13
   d.line([(x-ww*.43,yy),(x+ww*.41,yy+4)],fill=(82,70,54,50),width=2)
# varied leafless oak/hickory trees, a few evergreens; every tree sits across shared canvas
for _ in range(1050):
 x=rng.randrange(0,W);y=rng.randrange(0,H)
 hh=rng.randrange(12,40)
 color=(84,67,53,rng.randrange(105,195))
 if rng.random()<.08:
  d.polygon([(x,y-hh),(x-hh*.52,y+hh*.45),(x+hh*.52,y+hh*.45)],fill=(57,65,48,190))
  continue
 d.ellipse((x-hh*.5,y+hh*.4,x+hh*.5,y+hh*.72),fill=(73,62,49,35))
 d.line([(x,y+hh*.48),(x,y-hh)],fill=color,width=rng.randrange(2,5))
 d.line([(x,y-hh*.1),(x-hh*.48,y-hh*.93)],fill=color,width=2)
 d.line([(x,y-hh*.11),(x+hh*.5,y-hh*.81)],fill=color,width=2)
# period-style macadam pike: width ~22 ft = ~48px at 7.24 pix/m; widened for playtest visibility.
route=vc.sample_route();route_pts=[world_to_canvas(*p) for p in route]
part=[p for p in route_pts if -50 < p[0]<W+50 and -50<p[1]<H+50]
# Drawing only filtered points can bridge disconnected portions. This path is monotone locally.
if len(part)>2:
 d.line(part,fill=(95,80,60,235),width=73,joint='curve')
 d.line(part,fill=(189,179,154,255),width=58,joint='curve')
 d.line(part,fill=(219,202,172,180),width=27,joint='curve')
# small sheet demonstration: houses near road but not georeferenced
for x,y in [(W*.23,H*.42),(W*.72,H*.70)]:
 d.ellipse((x-46,y+22,x+44,y+48),fill=(50,43,33,50))
 d.rectangle((x-48,y-13,x+48,y+29),fill=(172,147,117,245),outline=(105,84,61,255),width=3)
 d.polygon([(x-61,y-13),(x-3,y-67),(x+59,y-13)],fill=(87,80,76,245))
 d.rectangle((x+28,y-83,x+40,y-46),fill=(148,111,82,245))
 d.rectangle((x-14,y+2,x+2,y+28),fill=(95,67,49,255))
# Export each 2000x2000 tile from EXACT shared canvas with same stock alpha mask.
# Since centers may be fractional in model, we use integer snapped placement consistently.
for (c,r),(cx,cy) in CENTERS.items():
 crop=canvas.crop((cx-1000,cy-1000,cx+1000,cy+1000))
 crop.putalpha(MASK)
 fn=OUT/f'SV_CORRIDOR_{c}_{r}.png'
 crop.save(fn,optimize=True,compress_level=9)
print('wrote 9 native-size sprites',flush=True)
# Reconstruct sample from cutouts: transparent mask along outer boundary only.
re=Image.new('RGBA',(W,H),(0,0,0,0))
for (c,r),(cx,cy) in CENTERS.items():
 t=Image.open(OUT/f'SV_CORRIDOR_{c}_{r}.png').convert('RGBA')
 re.alpha_composite(t,(cx-1000,cy-1000))
# 600 deterministic sampled pixels inside the mask must reproduce the original composite.
rrr=random.Random(8612); checked=0; mismatches=0
for _ in range(1500):
 x=rrr.randrange(0,W);y=rrr.randrange(0,H)
 p=re.getpixel((x,y))
 if p[3] >= 250:
  checked+=1
  if p[:3]!=canvas.getpixel((x,y))[:3]:mismatches+=1
preview=Image.new('RGBA',(W,H),(221,216,202,255));preview.alpha_composite(re)
preview.thumbnail((1300,1600),Image.Resampling.LANCZOS)
preview.save(ROOT/'previews'/'strasburg_nine_hex_stitch.png',optimize=True)
# Verify center-weighted colors equal original shared canvas for tiles before mask.
errors=[]
for (c,r),(cx,cy) in CENTERS.items():
 tile=Image.open(OUT/f'SV_CORRIDOR_{c}_{r}.png').convert('RGBA')
 target=canvas.crop((cx-1000,cy-1000,cx+1000,cy+1000)).convert('RGBA')
 for pt in ((1000,1000),(600,1000),(1400,1000),(1000,600),(1000,1400)):
  if tile.getpixel(pt)[:3]!=target.getpixel(pt)[:3]:errors.append([c,r,*pt])
checks={'tiles_exported':len(CENTERS),'sampled_shared_canvas_pixel_mismatches':len(errors),'stitch_original_pixel_samples':checked,'stitch_original_pixel_mismatches':mismatches,'alpha_mask':'Exact stock Plain.png alpha channel','native_tile_pixels':[2000,2000],'status':'seam construction technique verified; visual/navigational engine test still needed'}
(ROOT/'qa'/'native_slice_checks.json').write_text(json.dumps(checks,indent=2))
assert not errors and not mismatches,checks
print('slice test',checks,flush=True)