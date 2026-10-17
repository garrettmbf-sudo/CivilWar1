"""Offline size harness derived from inspected HoS code and prefab measurements.

Optional --map PATH --output PATH renders local reference-only map crops. No
proprietary sprites, guessed stats, or simulated NATO screenshot is emitted.
"""
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.build_miniature_assets import ART, font

SCREEN_HEIGHT = 1080
UNIT_SCALE = .37
COL_PITCH, ROW_PITCH = 4.42, 5.10
POSITIONS = [(17,23),(27,17),(25,26),(21,21)]

def screen_size(source_width, orthographic_size, screen_height=SCREEN_HEIGHT):
    # Loader: width 512; PPU = 100 * 512 / source_width.
    return source_width / 100 * UNIT_SCALE * screen_height / (2 * orthographic_size)

def sprite(unit):
    return Image.open(ART/'sprites/1024'/unit['country']/(unit['name']+'.png')).convert('RGBA')

def label(image, xy, text, size=18):
    ImageDraw.Draw(image).text(xy,text,font=font(size),fill='#eee6d5')

def panel(unit, zoom, map_image=None, col=17, row=23):
    w,h=320,260
    pixels_per_world=SCREEN_HEIGHT/(2*zoom)
    im=Image.new('RGBA',(w,h),'#606344')
    if map_image:
        # Old candidate map is flat-top odd-q, north-up; its own source radius
        # is 72.590249px. This local crop is visual context, not a map import.
        radius=72.59024934521165
        cx=1.5*radius*col;cy=map_image.height-math.sqrt(3)*radius*(row+.5*(col&1))
        factor=(COL_PITCH/1.5)/radius*pixels_per_world
        box=(cx-w/(2*factor),cy-h/(2*factor),cx+w/(2*factor),cy+h/(2*factor))
        im=map_image.crop(tuple(round(x) for x in box)).resize((w,h),Image.Resampling.LANCZOS).convert('RGBA')
    else:
        draw=ImageDraw.Draw(im)
        # Native grid uses EVEN columns offset +2.55, unlike prior map tooling.
        radius=COL_PITCH/1.5*pixels_per_world
        for c in range(-12,13):
            for r in range(-12,13):
                x=w/2+c*COL_PITCH*pixels_per_world
                y=h/2-(r*ROW_PITCH+(2.55 if c%2==0 else 0)-2.55)*pixels_per_world
                pts=[(x+radius*math.cos(k*math.pi/3),y+radius*math.sin(k*math.pi/3)) for k in range(6)]
                draw.polygon(pts,outline='#929472',width=1)
    side=round(screen_size(1024,zoom))
    # Approximate loader's bilinear 512-wide stage, without claiming BC3 parity.
    sp=sprite(unit).resize((512,512),Image.Resampling.BILINEAR).resize((side,side),Image.Resampling.BILINEAR)
    im.alpha_composite(sp,((w-side)//2,(h-side)//2))
    ImageDraw.Draw(im).rectangle((0,0,w,38),fill='#262b27')
    label(im,(9,8),f'{unit["label"]} | S={zoom} | {side}px',15)
    return im

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--map',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    units=json.loads((ART/'asset_manifest.json').read_text())['units']
    sheet=Image.new('RGBA',(1280,480),'#292e2b')
    label(sheet,(20,15),'KERNSTOWN / MARCH 23, 1862 - REVIEW CANDIDATES',23)
    label(sheet,(20,49),'Approved whole portraits composited after generation. No game UI is baked into these sprites.',15)
    for i,u in enumerate(units):
        side=310;sheet.alpha_composite(sprite(u).resize((side,side),Image.Resampling.LANCZOS),(i*320+5,85))
        label(sheet,(i*320+16,403),u['label'],22)
        label(sheet,(i*320+16,440),'1024 RGBA / transparent',14)
    sheet.convert('RGB').save(ART/'previews/four_unit_review.jpg',quality=95)
    map_image=Image.open(args.map).convert('RGB') if args.map else None
    sheet=Image.new('RGBA',(1280,1120),'#292e2b')
    label(sheet,(18,10),'OFFLINE ZOOM HARNESS / 1080px viewport height',23)
    label(sheet,(18,44),'Measured prefab scale; no runtime stat overlays or NATO screenshots. S = orthographicSize.',15)
    for j,z in enumerate([10,20,40,80]):
        for i,u in enumerate(units):sheet.alpha_composite(panel(u,z,map_image,*POSITIONS[i]),(i*320,80+j*260))
    out=args.output or ART/'previews/native_scale_zoom.jpg';out.parent.mkdir(parents=True,exist_ok=True)
    sheet.convert('RGB').save(out,quality=95)
    metrics=[{'orthographic_size':z,'canvas_width_px':screen_size(1024,z),
              'hex_row_pitch_px':ROW_PITCH*SCREEN_HEIGHT/(2*z)} for z in [10,20,40,80]]
    (ART/'evidence/zoom_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(out)

if __name__=='__main__':main()
