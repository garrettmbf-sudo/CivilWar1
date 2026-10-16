#!/usr/bin/env python3
"""Regenerate 1862-authentic critical tiles: limestone Pike, dirt roads, period rail, Winchester brick/limestone, rail fences."""
from __future__ import annotations
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
# reuse helpers by importing from generate module pieces inline
MASK = Image.open(ROOT / "data/hex_mask.png").convert("L")
SIZE, CX, CY, R = 2000, 1000.0, 1000.0, 955.0
OUT = ROOT / "mod/Graphics/Tiles/Summer"
OUT2 = ROOT / "mod/Graphics/Tiles/Spring"
OUT.mkdir(parents=True, exist_ok=True); OUT2.mkdir(parents=True, exist_ok=True)

PAL = dict(
    field_tan=(186,158,112), field_brown=(148,118,78), dormant=(156,138,96), mud=(120,96,70),
    limestone=(188,184,172), limestone_dark=(140,136,128), crushed=(210,204,188), crushed_edge=(170,164,148),
    dirt=(118,92,64), dirt_rut=(92,70,48), dirt_edge=(78,58,40),
    water=(78,102,118), water_deep=(48,72,92), water_edge=(140,150,140),
    rail_iron=(55,52,48), tie=(110,82,52), ballast=(130,120,105),
    bark=(78,58,42), bare=(92,78,58), dead=(70,62,52), redbud=(148,88,128),
    brick=(142,92,72), brick_dark=(110,70,55), limestone_ashlar=(175,170,160),
    whitewash=(215,205,185), roof_shake=(105,78,55), roof_slate=(88,90,96),
    fence=(95,75,50), shadow=(55,45,35),
)
VAR = {1:(0,3),2:(1,4),3:(2,5),4:(0,2),5:(1,3),6:(2,4),7:(3,5),8:(0,4),9:(1,5)}

def hex_pts(r=R):
    return [(CX+r*math.cos(math.radians(60*i)), CY+r*math.sin(math.radians(60*i))) for i in range(6)]
def edge_pt(edge, t=0.5, r=R*0.98):
    p=hex_pts(r); a,b=p[edge],p[(edge+1)%6]
    return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
def mask(im):
    im=im.convert("RGBA"); im.putalpha(MASK); return im
def base(seed, relief=0.05):
    rng=np.random.default_rng(seed)
    n=Image.fromarray((rng.random((200,200))*255).astype(np.uint8),"L").resize((SIZE,SIZE), Image.Resampling.BILINEAR)
    n=np.asarray(n,np.float32)/255.0
    yy,xx=np.ogrid[0:SIZE,0:SIZE]
    shade=1.0+relief*((CX-xx)/SIZE*0.35+(CY-yy)/SIZE*0.45)
    tan,brn=np.array(PAL["field_tan"],np.float32),np.array(PAL["field_brown"],np.float32)
    rgb=np.clip((tan*(1-n)[...,None]+brn*n[...,None])*shade[...,None],0,255).astype(np.uint8)
    im=Image.fromarray(np.dstack([rgb,np.full((SIZE,SIZE),255,np.uint8)]),"RGBA")
    d=ImageDraw.Draw(im); rr=random.Random(seed)
    for _ in range(500):
        x,y=rr.randint(120,SIZE-120),rr.randint(240,SIZE-240)
        col=PAL["dormant"] if rr.random()<0.7 else PAL["mud"]
        d.ellipse((x,y,x+rr.randint(2,5),y+rr.randint(2,4)), fill=col+(255,))
    return im
def trees(im, seed, bare=12, dead=4, redbud=3):
    rng=random.Random(seed); d=ImageDraw.Draw(im)
    def trunk(x,y,h,lean=0):
        d.line([(x,y),(x+lean,y-h)], fill=PAL["bark"]+(255,), width=rng.randint(2,4))
        for _ in range(3):
            ang=rng.uniform(-1,1); bl=h*rng.uniform(0.25,0.45)
            d.line([(x,y-h*0.55),(x+math.sin(ang)*bl,y-h*0.55-abs(math.cos(ang))*bl*0.3)], fill=PAL["bare"]+(255,), width=1)
    for _ in range(bare):
        trunk(rng.randint(280,SIZE-280), rng.randint(380,SIZE-380), rng.randint(36,80), rng.randint(-7,7))
    for _ in range(dead):
        x,y=rng.randint(280,SIZE-280),rng.randint(380,SIZE-380); h=rng.randint(28,60)
        d.line([(x,y),(x,y-h)], fill=PAL["dead"]+(255,), width=3)
    for _ in range(redbud):
        x,y=rng.randint(300,SIZE-300),rng.randint(400,SIZE-400); h=rng.randint(30,55)
        trunk(x,y,h); 
        for _ in range(rng.randint(8,16)):
            bx,by=x+rng.randint(-18,18),y-h+rng.randint(-5,20)
            d.ellipse((bx,by,bx+5,by+4), fill=PAL["redbud"]+(230,))
def rail_fence(im, edges, seed=1):
    """Split-rail zigzag fence along edge corridor."""
    d=ImageDraw.Draw(im); rng=random.Random(seed)
    a,b=edge_pt(edges[0],0.05), edge_pt(edges[1],0.95)
    for i in range(12):
        t0,t1=i/12,(i+1)/12
        x0,y0=a[0]+(b[0]-a[0])*t0, a[1]+(b[1]-a[1])*t0
        x1,y1=a[0]+(b[0]-a[0])*t1, a[1]+(b[1]-a[1])*t1
        off=8 if i%2==0 else -8
        # offset perpendicular roughly
        d.line([(x0,y0+off),(x1,y1-off)], fill=PAL["fence"]+(255,), width=3)
        d.line([(x0,y0+off+6),(x1,y1-off+6)], fill=PAL["fence"]+(255,), width=2)
def limestone_outcrops(im, seed, n=8):
    rng=random.Random(seed); d=ImageDraw.Draw(im)
    for _ in range(n):
        x,y=rng.randint(340,SIZE-340),rng.randint(420,SIZE-420)
        w,h=rng.randint(14,40),rng.randint(8,20)
        d.polygon([(x,y),(x+w,y-2),(x+w+2,y+h),(x-2,y+h)], fill=PAL["limestone"]+(255,), outline=PAL["limestone_dark"]+(255,))

def paint_pike(v, seed=250):
    """Pale crushed-limestone macadam Valley Pike — wide, light, distinct."""
    im=base(seed+v, 0.04); d=ImageDraw.Draw(im); e=VAR.get(v,(0,3))
    p1,p2=edge_pt(e[0]), edge_pt(e[1])
    # wide pale macadam bed
    d.line([p1,p2], fill=PAL["crushed_edge"]+(255,), width=52)
    d.line([p1,p2], fill=PAL["crushed"]+(255,), width=38)
    # faint center crown / wheel polish (still pale, not brown)
    d.line([p1,p2], fill=(225,220,205,180), width=10)
    # limestone grit speckles along road
    rng=random.Random(seed+v)
    for i in range(1,40):
        t=i/40; x=p1[0]+(p2[0]-p1[0])*t+rng.randint(-12,12); y=p1[1]+(p2[1]-p1[1])*t+rng.randint(-8,8)
        d.point((x,y), fill=PAL["limestone_dark"]+(200,))
    trees(im, seed+2, 6, 2, 2); limestone_outcrops(im, seed, 4)
    return mask(im)

def paint_dirt(v, seed=200):
    """Narrow rutted brown dirt road / farm lane."""
    im=base(seed+v, 0.05); d=ImageDraw.Draw(im); e=VAR.get(v,(0,3))
    p1,p2=edge_pt(e[0]), edge_pt(e[1])
    d.line([p1,p2], fill=PAL["dirt_edge"]+(255,), width=22)
    d.line([p1,p2], fill=PAL["dirt"]+(255,), width=14)
    # dual ruts
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0])+math.pi/2
    for side in (-4, 4):
        q1=(p1[0]+math.cos(ang)*side, p1[1]+math.sin(ang)*side)
        q2=(p2[0]+math.cos(ang)*side, p2[1]+math.sin(ang)*side)
        d.line([q1,q2], fill=PAL["dirt_rut"]+(255,), width=3)
    trees(im, seed+2, 8, 3, 2)
    if v % 3 == 0:
        rail_fence(im, e, seed)
    return mask(im)

def paint_rail(v, seed=300):
    """Single-track period RR: wooden ties, dual iron rails, light ballast — no modern multi-track."""
    im=base(seed+v, 0.04); d=ImageDraw.Draw(im); e=VAR.get(v,(0,3))
    p1,p2=edge_pt(e[0]), edge_pt(e[1])
    # ballast bed (narrow)
    d.line([p1,p2], fill=PAL["ballast"]+(255,), width=20)
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0])+math.pi/2
    # wooden ties
    for i in range(1, 22):
        t=i/22
        mx=p1[0]+(p2[0]-p1[0])*t; my=p1[1]+(p2[1]-p1[1])*t
        L=16
        d.line([(mx-math.cos(ang)*L, my-math.sin(ang)*L),(mx+math.cos(ang)*L, my+math.sin(ang)*L)],
               fill=PAL["tie"]+(255,), width=4)
    # two iron rails (single track gauge)
    for side in (-5, 5):
        q1=(p1[0]+math.cos(ang)*side, p1[1]+math.sin(ang)*side)
        q2=(p2[0]+math.cos(ang)*side, p2[1]+math.sin(ang)*side)
        d.line([q1,q2], fill=PAL["rail_iron"]+(255,), width=3)
    trees(im, seed+2, 5, 2, 1)
    return mask(im)

def paint_winchester(seed=520, variant=0):
    """1862 Winchester: brick + limestone ashlar, shake/slate roofs, dirt streets, rail fences — no asphalt/cars."""
    im=base(seed, 0.03); d=ImageDraw.Draw(im); rng=random.Random(seed+variant)
    # dirt street grid (Loudoun/Piccadilly hint)
    for i in range(-2, 3):
        d.line([(CX-300, CY+i*58),(CX+300, CY+i*58)], fill=PAL["dirt"]+(200,), width=7)
        d.line([(CX+i*72, CY-240),(CX+i*72, CY+240)], fill=PAL["dirt"]+(200,), width=6)
    # pale limestone sidewalks hint near center (macadam-ish town street)
    d.line([(CX-40, CY-200),(CX-40, CY+200)], fill=PAL["crushed"]+(120,), width=3)
    for _ in range(16):
        x=CX+rng.randint(-240,240); y=CY+rng.randint(-200,200)
        w,h=rng.randint(32,60), rng.randint(28,48)
        # brick or limestone ashlar — period Winchester
        if rng.random()<0.55:
            wall=PAL["brick"]; trim=PAL["brick_dark"]
        else:
            wall=PAL["limestone_ashlar"]; trim=PAL["limestone_dark"]
        d.rectangle((x,y,x+w,y+h), fill=wall+(255,), outline=PAL["shadow"]+(255,))
        # ashlar/brick courses
        for yy in range(y+6, y+h, 7):
            d.line([(x+1,yy),(x+w-1,yy)], fill=trim+(90,), width=1)
        roof=PAL["roof_shake"] if rng.random()<0.65 else PAL["roof_slate"]
        d.polygon([(x-4,y),(x+w/2,y-16-rng.randint(0,8)),(x+w+4,y)], fill=roof+(255,))
        if rng.random()<0.75:
            d.rectangle((x+8,y+12,x+18,y+22), fill=(55,60,70,255))
            d.rectangle((x+w-18,y+12,x+w-8,y+22), fill=(55,60,70,255))
    # courthouse / church mass near center
    d.rectangle((CX-28, CY-30, CX+28, CY+35), fill=PAL["limestone_ashlar"]+(255,), outline=PAL["shadow"]+(255,))
    d.polygon([(CX-36, CY-30),(CX, CY-70),(CX+36, CY-30)], fill=PAL["roof_slate"]+(255,))
    d.rectangle((CX-5, CY-88, CX+5, CY-70), fill=PAL["limestone_dark"]+(255,))
    # rail fence at block edge
    rail_fence(im, (5,2), seed)
    trees(im, seed+3, 6, 2, 4)
    limestone_outcrops(im, seed, 3)
    return mask(im)

def paint_village(seed=500, church=False, kernstown=False):
    im=base(seed, 0.04); d=ImageDraw.Draw(im); rng=random.Random(seed)
    d.line([(CX-170, CY+25),(CX+170, CY+25)], fill=PAL["dirt"]+(220,), width=10)
    d.line([(CX-170, CY+22),(CX+170, CY+22)], fill=PAL["dirt_rut"]+(200,), width=2)
    d.line([(CX-170, CY+28),(CX+170, CY+28)], fill=PAL["dirt_rut"]+(200,), width=2)
    n=7 if not church else 4
    for _ in range(n):
        x=CX+rng.randint(-150,150); y=CY+rng.randint(-90,90)
        w,h=rng.randint(34,55), rng.randint(26,40)
        # farm: whitewashed frame or brick; limestone chimney
        wall=PAL["whitewash"] if rng.random()<0.6 else PAL["brick"]
        d.rectangle((x,y,x+w,y+h), fill=wall+(255,), outline=PAL["shadow"]+(255,))
        d.polygon([(x-3,y),(x+w/2,y-18),(x+w+3,y)], fill=PAL["roof_shake"]+(255,))
        # limestone chimney
        d.rectangle((x+w-12,y-28,x+w-4,y+8), fill=PAL["limestone"]+(255,))
        if rng.random()<0.5:
            d.rectangle((x+10,y+12,x+20,y+22), fill=(50,55,65,255))
    if church:
        d.rectangle((CX-22, CY-20, CX+22, CY+45), fill=PAL["whitewash"]+(255,))
        d.polygon([(CX-32, CY-20),(CX, CY-62),(CX+32, CY-20)], fill=PAL["roof_shake"]+(255,))
        d.rectangle((CX-4, CY-78, CX+4, CY-62), fill=PAL["limestone_dark"]+(255,))
    rail_fence(im, (0,3) if not kernstown else (5,2), seed)
    trees(im, seed+2, 8, 3, 5)
    limestone_outcrops(im, seed, 5)
    return mask(im)

def paint_stone_wall(seed=80):
    im=base(seed, 0.25); d=ImageDraw.Draw(im)
    a,b=edge_pt(5,0.0,R*0.9), edge_pt(2,1.0,R*0.9)
    d.line([a,b], fill=PAL["limestone_dark"]+(255,), width=16)
    rng=random.Random(seed)
    for i in range(1, 24):
        t=i/24; x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
        d.rectangle((x-5,y-6,x+5,y+6), fill=PAL["limestone"]+(255,), outline=PAL["limestone_dark"]+(255,))
    trees(im, seed+2, 12, 5, 3); limestone_outcrops(im, seed, 10)
    return mask(im)

def save(name, im):
    im.save(OUT/f"{name}.png")
    im.save(OUT2/f"{name}.png")
    print("regen", name, flush=True)

def main():
    for v in range(1,10):
        save(f"SV_ValleyPike{v}", paint_pike(v))
        save(f"SV_Road{v}", paint_dirt(v))
        save(f"SV_Railroad{v}", paint_rail(v))
    save("SV_WinchesterBlock", paint_winchester(520,0))
    save("SV_WinchesterBlock2", paint_winchester(521,1))
    save("SV_WinchesterBlock3", paint_winchester(522,2))
    save("SV_Town", paint_winchester(510,3))
    save("SV_Village", paint_village(500))
    save("SV_Village2", paint_village(501))
    save("SV_Kernstown", paint_village(540, kernstown=True))
    save("SV_Church", paint_village(530, church=True))
    save("SV_StoneWall", paint_stone_wall(80))
    # contact sheet of key authentic tiles
    names=["SV_ValleyPike1","SV_Road1","SV_Railroad1","SV_StoneWall","SV_Church","SV_Kernstown","SV_WinchesterBlock","SV_Plain"]
    # plain may exist
    cell=240
    sheet=Image.new("RGBA",(cell*len(names),cell),(36,32,28,255))
    for i,n in enumerate(names):
        p=OUT/f"{n}.png"
        if p.exists():
            sheet.alpha_composite(Image.open(p).resize((cell,cell), Image.Resampling.LANCZOS),(i*cell,0))
    (ROOT/"previews").mkdir(exist_ok=True)
    sheet.convert("RGB").save(ROOT/"previews/tile_contact_authentic.jpg", quality=92)
    print("AUTHENTIC REGEN DONE")

if __name__=="__main__":
    main()
