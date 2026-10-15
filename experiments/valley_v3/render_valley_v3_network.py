"""Period-toned diagnostic preview using v3 *exact route edges* and hillshade.

This is a 2D offline inspection render, NOT a DEM, Unity 3D mesh, engine atlas,
verified 1862 GIS, or functioning .sav. Doesn't use copyrighted reference art.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import gaussian_filter
from skimage.measure import find_contours

from validate_and_preview import W,H
from valley_v3_connections import audit_v3, adjacent

COLORS={
 0:(205,202,184),1:(112,119,94),2:(155,154,121),3:(92,123,83),
 4:(199,196,150),5:(178,191,173),6:(195,193,146),7:(212,193,143),
 8:(190,193,150),9:(175,178,132),10:(199,198,154),11:(189,193,159),
}


def font(size:int,bold=False):
    names=('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf' if bold else
           '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
           '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf')
    for n in names:
        try:return ImageFont.truetype(n,size)
        except OSError: pass
    return ImageFont.load_default()


def make_preview(script:Path,output:Path,r:float=9.2):
    report,network,world=audit_v3(script)
    dx,dy=1.5*r,math.sqrt(3)*r
    mx,my=55,115
    iw=int(2*mx+(W+1)*dx+25)
    ih=int(2*my+(H+1)*dy+10)
    im=Image.new('RGB',(iw,ih),(225,220,196))
    draw=ImageDraw.Draw(im)
    centers={}
    for y in range(H):
        for x in range(W):
            centers[(x,y)]=(mx+(x+0.5)*dx, my+(H-1-y+(x%2)*0.5)*dy)
    def center(p):return centers[p]
    surface=np.array(world['terrain'],dtype=np.float32).reshape(H,W)
    zval={0:0.12,1:1.35,2:.48,3:.24,4:.10,5:.04,6:.11,7:.12,8:.11,9:.20,10:.10,11:.09}
    elev=np.zeros_like(surface)
    for t,z in zval.items():elev[surface==t]=z
    # Cosmetic interpolation only; cannot be used as true geographic elevation.
    elev=gaussian_filter(elev,1.35,mode='nearest')
    gry,grx=np.gradient(elev)
    shade=np.clip(((-grx*.95)+(gry*.65))*1.3,-.33,.33)
    verts=[(math.cos(math.pi*k/3),math.sin(math.pi*k/3)) for k in range(6)]
    def tint(rgb,k):return tuple(max(0,min(255,int(c*(1+k)))) for c in rgb)
    for y in range(H):
        for x in range(W):
            t=int(surface[y,x]);cx,cy=center((x,y))
            poly=[(cx+r*1.018*vx,cy+r*1.018*vy) for vx,vy in verts]
            noise=((x*79+y*191+x*y*11)%19-9)*.004
            draw.polygon(poly,fill=tint(COLORS[t],shade[y,x]+noise))
            if t in (1,2,3,9) and ((x*43+y*61)%7<5):
                seed=(x*12913+y*1699)&0xffffffff
                n=5 if t==3 else 2 if t==1 else 1
                for i in range(n):
                    sx=((seed*(i+13)*17)%200)/100-1
                    sy=((seed*(i+3)*43)%200)/100-1
                    ax,ay=cx+sx*r*.6,cy+sy*r*.6
                    col=(59,83,58) if t==3 else (86,103,73)
                    draw.ellipse((ax-1.2,ay-1.1,ax+1.1,ay+1.1), fill=col)
    # Continuous shaded relief: contours cross hex edges smoothly instead of
    # being separate isolated brown 'mountain discs'. No factual elevation claim.
    contour=Image.new('RGBA',im.size,(0,0,0,0));co=ImageDraw.Draw(contour)
    for level in np.arange(.30,1.18,.12):
        for curve in find_contours(elev,level):
            if len(curve)<6:continue
            pts=[]
            for py,px in curve[::2]:
                x=int(round(px));y=int(round(py));
                x=max(0,min(W-1,x));y=max(0,min(H-1,y))
                vx,vy=center((x,y))
                # Smooth interpolation in the hex center-plane.
                vx+=(px-x)*dx
                vy-=(py-y)*dy
                pts.append((vx,vy))
            if len(pts)>1:co.line(pts,fill=(79,70,54,70),width=1,joint='curve')
    im=Image.alpha_composite(im.convert('RGBA'),contour)
    draw=ImageDraw.Draw(im)
    # For each network, ONLY draw edges explicitly traced by an ordered route.
    # An occupied neighboring hex with no shared feature edge is never linked.
    blocked_crossing={tuple(e['hex']) for e in report['unresolved_crossings']}
    def segment_iter(kind):
        for a,ports in network['ports'][kind].items():
            for d in ports:
                b=adjacent(a,d)
                if a<b and b in centers:
                    yield a,b
    # Roads before water: unresolved crossings remain blocked on the preview.
    for a,b in segment_iter('road'):
        if a in blocked_crossing or b in blocked_crossing:
            # Draw only to edge of water; do not depict a phantom ford.
            xa,ya=center(a);xb,yb=center(b)
            if a in blocked_crossing and b not in blocked_crossing:
                xa,ya=xa*.50+xb*.50,ya*.50+yb*.50
            elif b in blocked_crossing and a not in blocked_crossing:
                xb,yb=xa*.50+xb*.50,ya*.50+yb*.50
            elif a in blocked_crossing and b in blocked_crossing:
                continue
            draw.line([(xa,ya),(xb,yb)],fill=(112,89,55,255),width=3)
        else:
            draw.line([center(a),center(b)],fill=(108,83,50,255),width=3)
            draw.line([center(a),center(b)],fill=(200,165,109,255),width=1)
    for a,b in segment_iter('rail'):
        # A bridge tile is NOT a rail tile in v3; do not paint it as continuous track.
        if a in network['occupancy']['river'] or b in network['occupancy']['river']:
            continue
        draw.line([center(a),center(b)],fill=(31,37,37,255),width=3)
        ax,ay=center(a);bx,by=center(b)
        theta=math.atan2(by-ay,bx-ax)
        nx,ny=-math.sin(theta),math.cos(theta)        for f in (.25,.50,.75):
            cx=ax+(bx-ax)*f;cy=ay+(by-ay)*f
            draw.line([(cx-nx*3,cy-ny*3),(cx+nx*3,cy+ny*3)],fill=(77,69,55,255),width=1)
    for a,b in segment_iter('river'):
        draw.line([center(a),center(b)],fill=(228,214,175,255),width=10)
        draw.line([center(a),center(b)],fill=(48,111,133,255),width=6)
        draw.line([center(a),center(b)],fill=(101,150,159,255),width=2)
    # Bridges are still candidates, not verified historical crossings.
    for p,site in sorted(world['approved'].items()):
        x,y=center(p)
        draw.ellipse((x-5,y-5,x+5,y+5),fill=(244,210,121,255),outline=(75,55,34,255),width=2)
        draw.line((x-4,y,x+4,y),fill=(70,56,39,255),width=2)
    for p in sorted(blocked_crossing):
        x,y=center(p)
        draw.line((x-3,y-3,x+3,y+3),fill=(151,55,43,255),width=2)
        draw.line((x+3,y-3,x-3,y+3),fill=(151,55,43,255),width=2)
    for p,town in world['towns'].items():
        x,y=center(p)
        overlap=p in network['occupancy']['river']
        draw.ellipse((x-4,y-4,x+4,y+4),fill=(168,61,40,255) if overlap else (36,40,37,255),outline=(248,237,203,255),width=1)
        name=town['N']
        if town['S']==2 or name in ('Port Republic','Luray','Moorefield','McDowell','Kernstown'):
            draw.text((x+7,y-11),name,font=font(13,town['S']==2),fill=(28,33,29,255),stroke_width=2,stroke_fill=(232,224,192,255))
    # Ridge names are indicative locations from schematic, NOT surveyed text.
    for p,label in [((39,55),'NORTH MOUNTAIN'),((62,64),'MASSANUTTEN'),((85,59),'BLUE RIDGE'),((9,71),'ALLEGHENY FRONT')]:
        x,y=center(p)
        draw.text((x-38,y),label,font=font(14,True),fill=(59,72,55,255),stroke_width=2,stroke_fill=(222,215,183,255))
    titlefont=font(24,True)
    draw.text((22,16),'THE SHENANDOAH VALLEY · 1862',font=titlefont,fill=(46,51,42,255))
    draw.text((24,48),'125 × 130 hexes · schematic coordinates · EXACT edge connections',font=font(14),fill=(59,67,59,255))
    draw.text((24,70),'Blue: rivers   Umber: roads   Black: rail   Gold: candidate crossing   Red X: unresolved',font=font(12),fill=(72,68,58,255))
    draw.text((24,91),'Height tint & contours are illustrative, not surveyed DEM.',font=font(12),fill=(122,73,53,255))
    draw.text((24,ih-45),'NOT IN-GAME ART. Route/sprite/crossing validation still required.',font=font(13,True),fill=(139,59,48,255))
    output.parent.mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(output,optimize=True)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--script',type=Path,default=Path(__file__).with_name('build_valley_map_v3.ps1'))
    p.add_argument('--output',type=Path,default=Path('Valley_Map_v3_edge_exact.png'))
    a=p.parse_args()
    print(make_preview(a.script,a.output))
