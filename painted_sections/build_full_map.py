"""Full 62x55 painted basemap: section texture method (build_sandy_ridge.py, FULL=1) for ground,
then compose_painted_map.py's (imported, unmodified) hydro/roads/landmarks/Winchester, then natural stone wall + labels."""
import os, sys, math
os.environ['FULL'] = '1'
sys.path.insert(0, 'scripts')
src = open('painted_sections/build_sandy_ridge.py').read()
ground = src.split('# ---------- roads')[0]
mid = src.split('# ---------- split-rail fences')[1].split('# ---------- stone wall')[0]
wall = src.split('# ---------- stone wall')[1].split('# ---------- sprites')[0]
exec(ground)                      # textures + hillshade -> canvas (RGBA, full basemap size)
import compose_painted_map as CPM
assert (CPM.W, CPM.H) == canvas.size, (CPM.W, CPM.H, canvas.size)
lib = CPM.build_sprite_library()
canvas = CPM.draw_hydro(canvas)
# roads: muddy tan ruts; Valley Pike pale limestone
d = ImageDraw.Draw(canvas, 'RGBA')
for k, rd in CPM.FEAT['roads'].items():
    pts = [CPM.ll2px(*c) for c in rd['waypoints']]
    if rd.get('kind') == 'pike':
        d.line(pts, fill=(90, 78, 60, 170), width=22, joint='curve'); d.line(pts, fill=(176, 166, 146, 255), width=16, joint='curve')
        d.line(pts, fill=(204, 196, 178, 255), width=9, joint='curve')
    else:
        d.line(pts, fill=(92, 70, 48, 150), width=15, joint='curve'); d.line(pts, fill=(146, 112, 78, 255), width=10, joint='curve')
        d.line(pts, fill=(118, 88, 60, 200), width=2, joint='curve')
rr_ = [CPM.ll2px(*c) for c in CPM.FEAT['railroads']['winchester_and_potomac']['waypoints']]
d.line(rr_, fill=(70, 60, 50, 255), width=8, joint='curve'); d.line(rr_, fill=(140, 128, 110, 255), width=4, joint='curve')
canvas = CPM.place_fords(canvas, lib)
canvas = CPM.place_landmarks(canvas, lib)
canvas = CPM.place_winchester(canvas, lib)   # Loudoun St strip, houses, courthouse, churches, Fort Collier/Alabama earthworks
exec('#' + mid)
exec('#' + wall)
out = canvas.convert('RGB')
out = ImageEnhance.Color(out).enhance(0.92)
out.save('data/basemap_painted_full.png', compress_level=3)
lab = CPM.draw_labels(out.convert('RGBA'), scale=1.15).convert('RGB')
lab.save('data/basemap_painted_full_labeled.png', compress_level=3)
os.makedirs('previews', exist_ok=True)
s_ = 3000/max(lab.size); lab.resize((int(lab.width*s_), int(lab.height*s_)), Image.Resampling.LANCZOS).save('previews/final_full.jpg', quality=90)
def crop(lon0, lat0, lon1, lat1, name):
    x0, y1 = CPM.ll2px(lon0, lat0); x1, y0 = CPM.ll2px(lon1, lat1)
    lab.crop((int(x0), int(y0), int(x1), int(y1))).save('previews/'+name, quality=90)
crop(-78.180, 39.170, -78.148, 39.200, 'final_closeup_winchester.jpg')
crop(-78.240, 39.135, -78.200, 39.160, 'final_closeup_wall_sandy_ridge.jpg')
print('FULL DONE', out.size)
