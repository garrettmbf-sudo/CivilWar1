import sys,math;sys.path.insert(0,'scripts')
from hex_grid import KERNSTOWN as G
from PIL import Image,ImageDraw
Image.MAX_IMAGE_PIXELS=None
P=0.55;im=Image.open('data/basemap_kernstown.png').convert('RGB');H=im.size[1];R=G.size_m*P
def c(col,row):x,y=G.hex_to_xy_m(col,row);return x*P,H-y*P
C0,C1,R0,R1=10,25,17,28
pts=[c(a,b) for a in(C0,C1) for b in(R0,R1)]
x0=min(p[0] for p in pts)-R;x1=max(p[0] for p in pts)+R;y0=min(p[1] for p in pts)-R;y1=max(p[1] for p in pts)+R
box=tuple(int(v) for v in(x0,y0,x1,y1));crop=im.crop(box);crop.save('painted_sections/guide_sandy_ridge_nogrid.jpg',quality=90)
d=ImageDraw.Draw(crop)
wall={(c_,23) for c_ in range(14,21)}|{(19,22)}
for a in range(C0-1,C1+2):
  for b in range(R0-1,R1+2):
    cx,cy=c(a,b);cx-=box[0];cy-=box[1]
    poly=[(cx+R*math.cos(math.radians(60*k)),cy+R*math.sin(math.radians(60*k))) for k in range(7)]
    d.line(poly,fill=(255,0,0) if (a,b) in wall else (20,20,20),width=4 if (a,b) in wall else 2)
    d.text((cx-12,cy-R*0.8),f"{a},{b}",fill=(0,0,0))
crop.save('painted_sections/guide_sandy_ridge_grid.jpg',quality=90);print(box,crop.size)
