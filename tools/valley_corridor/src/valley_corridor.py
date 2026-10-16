"""CivilWar1: geo-anchored spring-1862 valley corridor proof of concept.
Continuous geometry, flat-top odd-q grid, topology-first Valley Pike.
CAUTION: geographic route between verified settlement anchors and relief/water outside
Kernstown are PROVISIONAL sketches, NOT traced 1862 roads or USGS DEM.
Do not use this as a historically certified movement map.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, math, random, csv
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews'; DATA=ROOT/'data'
# Historical site anchors, but polyline connecting them is schematically interpolated.
STOPS=[
 ('Winchester',-78.1633,39.1857),
 ('Kernstown',-78.1960,39.1417),
 ('Newtown',-78.2186,39.0838),
 ('Middletown',-78.2805,39.0267),
 ('Strasburg',-78.3587,38.9888),
 ("Tom's Brook",-78.4380,38.9445),
 ('Woodstock',-78.5057,38.8818),
 ('Edinburg',-78.5660,38.8200),
 ('Mount Jackson',-78.6423,38.7459),
 ('New Market',-78.6708,38.6474),
]
# Corridor includes pike and adjoining farms/ridges; east side includes rail exit toward Front Royal.
WEST,EAST,SOUTH,NORTH=-78.790,-78.090,38.608,39.222
LAT0=(SOUTH+NORTH)/2
MX=111132*math.cos(math.radians(LAT0));MY=111132
SPACING_M=250*0.9144
R=SPACING_M/math.sqrt(3)       # outer hex radius: 131.98m
DX=1.5*R; DY=math.sqrt(3)*R
COLS=math.ceil((EAST-WEST)*MX/DX)+2
ROWS=math.ceil((NORTH-SOUTH)*MY/DY)+2

def lonlat_xy(lon,lat):return ((lon-WEST)*MX,(lat-SOUTH)*MY)
def xy_lonlat(x,y):return (WEST+x/MX,SOUTH+y/MY)
def hex_xy(col,row):return (DX*col,DY*(row+.5*(col&1)))
def cube_round(q,r):
 s=-q-r; rq,rr,rs=round(q),round(r),round(s)
 dq,dr,ds=abs(rq-q),abs(rr-r),abs(rs-s)
 if dq>dr and dq>ds:rq=-rr-rs
 elif dr>ds:rr=-rq-rs
 return int(rq),int(rr)
def xy_hex(x,y):
 q,r=cube_round((2*x/3)/R,(-x/3+math.sqrt(3)*y/3)/R)
 return q,r+(q-(q&1))//2

def lonlat_hex(lon,lat):return xy_hex(*lonlat_xy(lon,lat))
def off_ax(h):c,r=h;return c,r-(c-(c&1))//2
def ax_cube(h):q,r=off_ax(h);return q,r,-q-r
def hex_dist(a,b):return max(abs(x-y) for x,y in zip(ax_cube(a),ax_cube(b)))
def cube_line(a,b):
 aa=ax_cube(a);bb=ax_cube(b);n=hex_dist(a,b)
 if n==0:return [a]
 out=[]
 for i in range(n+1):
  t=i/n;q,r=cube_round(aa[0]*(1-t)+bb[0]*t,aa[1]*(1-t)+bb[1]*t)
  h=(q,r+(q-(q&1))//2)
  if not out or out[-1]!=h:out.append(h)
 return out

def sample_route():
 # Stops are ordered north to south; PCHIP latitude->longitude gives smooth no overshoot.
 ordered=sorted(STOPS,key=lambda v:v[2]); lats=np.array([s[2] for s in ordered]); lons=np.array([s[1] for s in ordered]); f=PchipInterpolator(lats,lons)
 la=np.linspace(lats[0],lats[-1],2400)
 return [[float(f(a)),float(a)] for a in la]

def heading_between(a,b):
    ax,ay=hex_xy(*a);bx,by=hex_xy(*b)
    theta=(math.degrees(math.atan2(by-ay,bx-ax))+360)%360
    codes=('E','NE','NW','W','SW','SE')
    sector=int((theta+30)//60)%6
    assert hex_dist(a,b)==1
    return codes[sector]


def pike_graph(route):
 cells=[]
 for lon,lat in route:
  h=lonlat_hex(lon,lat)
  if not cells or cells[-1]!=h:
   if cells and hex_dist(cells[-1],h)>1:cells.extend(cube_line(cells[-1],h)[1:])
   else:cells.append(h)
 edges={}
 for a,b in zip(cells,cells[1:]):
  assert hex_dist(a,b)==1,(a,b)
  edges.setdefault(a,set()).add(b);edges.setdefault(b,set()).add(a)
 return cells,edges

def world_terrain(xm,ym):
 """Prototype directional relief and ground cover, fixed world-coordinate function.
 No DEM claim. Returns normalized elevation proxy, forest tendency, marsh tendency.
 """
 xx=np.asarray(xm)/1000; yy=np.asarray(ym)/1000
 # continuous slope fields, rugged ridges outside the main valley; not geographic elevation
 rwest=np.exp(-((xx-4-0.18*yy)/7.8)**2)
 reast=np.exp(-((xx-51-0.18*yy)/6.8)**2)
 roll=(np.sin(xx*.46+yy*.31)+.6*np.cos(xx*.26-yy*.67)+.3*np.sin(xx*1.1+yy*.79))
 elev=(0.75*rwest+0.75*reast)+0.10*roll
 wooded=np.clip(.28+.52*(rwest+reast)+.21*np.sin(xx*.61+np.cos(yy*.28)) + .11*np.sin(yy*.85),0,1)
 moisture=np.clip(.18+.19*np.sin(xx*.4+yy*.32)+.1*np.cos(xx*.67-yy*.47),0,1)
 return elev,wooded,moisture

def project(lon,lat,W,H):
 x,y=lonlat_xy(lon,lat);return (x/((EAST-WEST)*MX)*W,(1-y/((NORTH-SOUTH)*MY))*H)

def base_texture(W,H):
 """Bounded-memory hand-painted early spring landscape, deterministic across output view."""
 rng=np.random.default_rng(1862)
 gw=max(40,W//35);gh=max(40,H//35)
 field=rng.random((gh,gw)).astype(np.float32)
 coarse=gaussian_filter(field,sigma=3,mode='reflect')
 n1=np.asarray(Image.fromarray(np.uint8(np.clip(field,0,1)*255),'L').resize((W,H),Image.Resampling.BICUBIC),dtype=np.float32)/255
 n2=np.asarray(Image.fromarray(np.uint8(np.clip(coarse*2,0,1)*255),'L').resize((W,H),Image.Resampling.BICUBIC),dtype=np.float32)/255
 # compute world coordinates at low-res grid and resize. Deliberately not DEM.
 tx=np.linspace(0,(EAST-WEST)*MX,gw)
 ty=np.linspace((NORTH-SOUTH)*MY,0,gh)
 elev,woods,wet=world_terrain(*np.meshgrid(tx,ty))
 def up(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255),'L').resize((W,H),Image.Resampling.BICUBIC),dtype=np.float32)/255
 hill=up(np.clip((elev+0.4)/2.0,0,1))
 forest=up(woods)
 moisture=up(wet)
 blend=(n1-.5)*.23 + (n2-.45)*.24
 shadow=np.clip(1.03-.20*hill+.04*moisture,0.5,1.2)
 ochre=np.array([180,151,111],np.float32)
 earth=np.array([139,114,83],np.float32)
 straw=np.array([200,174,125],np.float32)
 col=ochre[None,None,:]+(blend[...,None]*(earth-straw)[None,None,:])+((forest-.37)[...,None]*np.array([-28,-27,-20]))
 col=np.clip(col*shadow[...,None],0,255).astype('uint8')
 del field,n1,n2,coarse,shadow,hill,forest,moisture
 return Image.fromarray(col,'RGB').convert('RGBA')

def draw_regions(im,W,H):
    """Continuous late-March farmland, woods, and orchards. Not one isolated scene per hex."""
    from PIL import ImageDraw
    d=ImageDraw.Draw(im,'RGBA')
    rng=random.Random(18620321)
    # Agricultural parcels: elongated irregular polygons in warm earth tones, not modern perfect rectangles.
    parcel_colors=[(105,77,55,59),(98,82,56,46),(200,174,123,65),
                   (214,184,129,50),(132,100,71,49),(169,153,106,38),
                   (87,81,57,36),(190,178,142,42)]
    for i in range(1500):
        lon=rng.uniform(WEST,EAST);lat=rng.uniform(SOUTH,NORTH)
        px,py=project(lon,lat,W,H)
        xm,ym=lonlat_xy(lon,lat)
        elev,forest,wet=world_terrain(xm,ym)
        if rng.random() < .20 + .20*forest:continue
        pw=rng.uniform(19,91)*W/2600
        ph=rng.uniform(16,64)*H/3150
        shear=rng.uniform(-12,12)*W/2600
        pts=[(px-pw*.58,py-ph*.40),(px+pw*.40,py-ph*.48),
             (px+pw*.58+shear,py+ph*.44),(px-pw*.52+shear,py+ph*.46)]
        color=parcel_colors[rng.randrange(len(parcel_colors))]
        d.polygon(pts,fill=color)
        if rng.random()<.45:
            d.line(pts+[pts[0]],fill=(88,69,48,64),width=1)
        # Fine parallel plough lines within the field; oblique, varied and subdued.
        if color[0]<145 and rng.random()<.65:
            for j in range(2,9):
                sy=py-ph*.40+j*ph/9
                d.line([(px-pw*.46+j*.20,sy),(px+pw*.42+j*.20,sy+shear*.3)],
                       fill=(58,49,38,48),width=1)
    # Ribbons of oak-hickory leaf litter along elevated ridges; no dark round 'stamp' patches.
    for i in range(18500):
        lon=rng.uniform(WEST,EAST);lat=rng.uniform(SOUTH,NORTH)
        x,y=project(lon,lat,W,H);xm,ym=lonlat_xy(lon,lat)
        elev,forest,wet=world_terrain(xm,ym)
        if rng.random() > (.08+.55*forest):continue
        scale=max(.6,W/2600)
        s=rng.uniform(.7,3.8)*scale
        if rng.random()<.07:
            d.ellipse((x-s*1.7,y-s,x+s*1.7,y+s*.8),fill=(155,148,127,135))
            d.arc((x-s*1.7,y-s,x+s*1.7,y+s*.8),20,200,fill=(106,96,78,85),width=1)
            continue
        # Mostly leafless: trunk, asymmetric crown and sparse twigs; isolated evergreen cedars.
        if rng.random()<.14:
            d.polygon([(x,y-s*2),(x-s*1.15,y+s*.65),(x+s*1.15,y+s*.65)],fill=(57,67,47,165))
            continue
        tone=rng.choice([(67,57,46,160),(82,72,58,145),(103,83,62,132)])
        d.line([(x,y+s),(x,y-s)],fill=tone,width=1)
        d.line([(x,y-s*.25),(x-s*.85,y-s*1.2)],fill=tone,width=1)
        d.line([(x,y-s*.32),(x+s,y-s*1.23)],fill=tone,width=1)
    # Scattered orchards near settlements: neat but sparse rows of bare fruit trees.
    for name,lon,lat in STOPS:
        if name in ('Kernstown','Woodstock','Middletown','New Market','Newtown'):
            x,y=project(lon+.011,lat+.006,W,H)
            for j in range(3):
                for k in range(6):
                    dx=x+j*8*W/2600;dy=y+k*8*H/3150
                    d.line([(dx,dy+2),(dx,dy-2)],fill=(74,62,45,140),width=1)
                    d.line([(dx,dy-1),(dx-3,dy-3),(dx+3,dy-4)],fill=(82,68,53,105),width=1)

def draw_river(im,coords,W,H,width=7):
 d=ImageDraw.Draw(im,'RGBA');pts=[project(*p,W,H) for p in coords]
 d.line(pts,fill=(68,64,54,180),width=width+3,joint='curve')
 d.line(pts,fill=(71,105,110,235),width=width,joint='curve')
 d.line(pts,fill=(128,145,132,88),width=max(1,width//3),joint='curve')

def draw_pike(im,coords,W,H,width=9):
 d=ImageDraw.Draw(im,'RGBA');pts=[project(*p,W,H) for p in coords]
 d.line(pts,fill=(82,67,53,205),width=width+5,joint='curve')
 d.line(pts,fill=(187,172,147,255),width=width+1,joint='curve')
 d.line(pts,fill=(220,207,177,255),width=max(2,width-3),joint='curve')
 # wagon wheel ruts in center, subtle and continuous
 # no railroad along pike

def synthetic_hydrology():
    """REVIEW-ONLY diagram of hydrologic relationships. NOT surveyed alignment."""
    hydro=[]
    # North Fork Shenandoah flows north/northeast along eastern side of the main Valley.
    # Its exact crossings/bank position await tracing on Hotchkiss + Brown sheets.
    pts=[(-78.683,38.617),(-78.671,38.667),(-78.646,38.716),(-78.629,38.751),
         (-78.594,38.794),(-78.550,38.836),(-78.504,38.882),(-78.462,38.914),
         (-78.428,38.955),(-78.397,38.976),(-78.340,39.011),(-78.303,39.034),(-78.261,39.072)]
    # Sequence from south to north monotonic lat; meander added smoothly between anchors.
    lat=np.array([p[1] for p in pts]);lon=np.array([p[0] for p in pts]);fn=PchipInterpolator(lat,lon)
    lats=np.linspace(lat[0],lat[-1],880)
    rivers=[[float(fn(x)+0.0024*math.sin(i*.07)+0.001*math.sin(i*.17)),float(x)] for i,x in enumerate(lats)]
    hydro.append({'name':'North Fork Shenandoah — schematic course','route':rivers,'confidence':'approximate regional relationship only; no verified banks or ford geometry','type':'river'})
    # A short tributary from the western ridges should JOIN the North Fork, not go across the entire map.
    tributaries=[('Cedar Creek',39.016,-78.33),('Tom’s Brook',38.948,-78.43),('Stony Creek',38.823,-78.57)]
    for label,join_lat,join_lon in tributaries:
        route=[]
        n=240
        for i in range(n):
            t=i/(n-1)
            x=WEST+0.015 + (join_lon-(WEST+0.015))*t
            y=join_lat + .007*math.sin(math.pi*t) + .003*math.sin(math.pi*t*3)
            route.append([float(x),float(y)])
        hydro.append({'name':label+' — schematic course','route':route,'confidence':'historic named watercourse, approximate position only; crossing status unverified','type':'creek'})
    return hydro

def draw_rail_spur(im,W,H):
 # Manassas Gap RR departs toward Front Royal (east) at Strasburg; NO line to Winchester.
 pts=[[-78.355,38.990],[-78.317,38.990],[-78.282,38.983],[-78.245,38.967],[-78.20,38.962],[-78.115,38.957]]
 d=ImageDraw.Draw(im,'RGBA');p=[project(a,b,W,H) for a,b in pts]
 d.line(p,fill=(66,60,53,225),width=max(2,int(W/900)))
 # tracks shown as provisional corridor. Full 1862 alignment NOT yet traced.
 return {'name':'Manassas Gap Railroad (east of Strasburg only)','route':pts,'confidence':'rail network historic; route geometry provisional'}

def town_marker(im,name,lon,lat,W,H):
 d=ImageDraw.Draw(im,'RGBA');x,y=project(lon,lat,W,H);r=max(4,W/580)
 for j in range(5):
  dx=((j*11)%23-12)/12*r;dy=((j*7)%19-10)/10*r
  d.rectangle((x+dx-r*.3,y+dy-r*.7,x+dx+r*.4,y+dy+r*.25),fill=(116,92,71,220),outline=(66,57,49,180),width=1)
  d.polygon([(x+dx-r*.5,y+dy-r*.7),(x+dx,y+dy-r*1.1),(x+dx+r*.6,y+dy-r*.7)],fill=(76,76,76,230))

def labels(im,W,H):
 d=ImageDraw.Draw(im,'RGBA')
 fonts=['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
 f=ImageFont.truetype(fonts[0],max(12,int(W/170))); fs=ImageFont.truetype(fonts[0],max(9,int(W/245)))
 for name,lon,lat in STOPS:
  x,y=project(lon,lat,W,H); font=f if name in ('Winchester','Strasburg','New Market') else fs
  d.text((x+11,y-12),name,font=font,fill=(45,37,29,255),stroke_width=2,stroke_fill=(230,211,175,235))

def hex_grid_overlay(im,W,H,opacity=25):
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 sx=W/((EAST-WEST)*MX);sy=H/((NORTH-SOUTH)*MY)
 # verify image x/y scaling unequal very slightly; draw via actual projected hex corners in geo meters
 for c in range(COLS):
  for r in range(ROWS):
   cx,cy=hex_xy(c,r)
   if cx>(EAST-WEST)*MX+R or cy>(NORTH-SOUTH)*MY+R:continue
   pts=[((cx+R*math.cos(k*math.pi/3))*sx,(1-(cy+R*math.sin(k*math.pi/3))/((NORTH-SOUTH)*MY))*H) for k in range(6)]
   if any(-5<=p[0]<=W+5 and -5<=p[1]<=H+5 for p in pts):d.line(pts+[pts[0]],fill=(46,40,33,opacity),width=1)
 return Image.alpha_composite(im,layer)

def build_overview(W=2600,H=3150):
 print('render',W,H,flush=True)
 im=base_texture(W,H);draw_regions(im,W,H)
 hydro=synthetic_hydrology()
 for h in hydro:draw_river(im,h['route'],W,H,width=max(3,int(W/260)) if h['type']=='river' else max(2,int(W/500)))
 rr=draw_rail_spur(im,W,H)
 route=sample_route();draw_pike(im,route,W,H,width=max(6,int(W/250)))
 for name,lo,la in STOPS:town_marker(im,name,lo,la,W,H)
 # high quality preview without labels, preserve natural landscape for zooms
 im.convert('RGB').save(OUT/'valley_corridor_continuous_unlabeled.jpg',quality=90,optimize=True)
 labels(im,W,H)
 im=hex_grid_overlay(im,W,H,opacity=18)
 d=ImageDraw.Draw(im,'RGBA');f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',int(W/90))
 d.rounded_rectangle([25,15,W-25,65],radius=10,fill=(36,32,28,210))
 d.text((42,23),'SHENANDOAH 1862  |  WINCHESTER — STRASBURG — NEW MARKET  |  250 yd grid',fill=(237,224,190,255),font=f)
 d.text((45,H-47),'PROTOTYPE — PAINTED TOPOLOGY; roads/water outside Kernstown pending historical digitization',fill=(34,30,26,255),font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',int(W/150)))
 im.convert('RGB').save(OUT/'valley_corridor_continuous_250yd.jpg',quality=92,optimize=True)
 return route,hydro,rr

def build_data(route,hydro,rail):
 cells,edges=pike_graph(route)
 assert len(cells)>200
 assert len(set(cells))==len(cells),'Valley Pike revisits same hex: resolve before finalizing'
 assert all(hex_dist(a,b)==1 for a,b in zip(cells,cells[1:]))
 pset=set(cells)
 # Save small feature graph instead of >75,000 2000px unique image assets.
 ports={}
 for h,ns in edges.items():
  ports[f'{h[0]},{h[1]}']=[list(v) for v in sorted(ns)]
 towns=[{'name':nm,'lon':lon,'lat':lat,'hex':list(lonlat_hex(lon,lat)),'confidence':'settlement historically established; position approximate'} for nm,lon,lat in STOPS]
 data={'schema':'civilwar1.valley.topology.v0.1','status':'VISUAL PROTOTYPE NOT HISTORICAL COMPLETION',
  'grid':{'layout':'flat-top odd-q','column_pitch_m':DX,'row_pitch_m':DY,'center_spacing_m':SPACING_M,'centers_per_mile':1609.344/SPACING_M,'hex_across_flats_m':math.sqrt(3)*R,'hex_across_points_m':2*R,'cols':COLS,'rows':ROWS,'bounds':[WEST,SOUTH,EAST,NORTH], 'coordinates':'local equirectangular WGS84 approximation, not suitable for surveyed placement'},
  'landmarks':towns,'networks':{'valley_pike':{'nodes':[[a,b] for a,b in cells],'topological_ports':ports,'source':'anchored in historical settlement sequence and Kernstown starting path, INTERMEDIATE ALIGNMENT PROVISIONAL','rendering':'continuous geo surface BEFORE hex slicing'},'manassas_gap_railroad':rail,'hydrology':hydro},
  'rules':{'no_winchester_strasburg_railroad':True,'no_grid_lines_baked_into_art':True,'native_png_size':[2000,2000],'native_season_folder':'Summer', 'terrain_dem':'MISSING OUTSIDE KERNSTOWN; preview uses non-georeferenced proxy relief','crossings':'not traversable until separately verified'}}
 DATA.joinpath('corridor_topology.json').write_text(json.dumps(data,separators=(',',':')))
 # Each route crossing edge is explicitly paired with its opposite neighbor edge.
 rows=[]
 opposite={'E':'W','NE':'SW','NW':'SE','W':'E','SW':'NE','SE':'NW'}
 for i,(a,b) in enumerate(zip(cells,cells[1:])):
  edge=heading_between(a,b)
  assert heading_between(b,a)==opposite[edge]
  rows.append({'step':i,'col':a[0],'row':a[1],'exit_edge':edge,'neighbor_col':b[0],'neighbor_row':b[1],'neighbor_enter_edge':opposite[edge],'network':'Valley Pike','status':'route geometry provisional'})
 with (DATA/'valley_pike_edge_manifest.csv').open('w',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

 checks={'topological_edges':sum(len(ns) for ns in edges.values())//2,'pike_tiles':len(cells),'dangling_internal_edges':sum(1 for h,v in edges.items() if len(v)==1 and h not in (cells[0],cells[-1])),'jump_edges':sum(hex_dist(a,b)!=1 for a,b in zip(cells,cells[1:])), 'inside_bounds':all(0<=a<COLS and 0<=b<ROWS for a,b in cells),'unique_nodes':len(cells)==len(pset),'historic_crossing_status':'all unverified in prototype','wall_fence_status':'not generated without period digitization'}
 DATA.joinpath('topology_checks.json').write_text(json.dumps(checks,indent=2));print('grid',COLS,ROWS,'pike',len(cells),'checks',checks,flush=True)
 return checks

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
 route,hydro,rail=build_overview()
 build_data(route,hydro,rail)