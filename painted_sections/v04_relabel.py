"""Re-draw labels + previews from data/basemap_painted_full.png without rebuilding the art (v0.4)."""
import sys, json, math
sys.path.insert(0, 'scripts')
import numpy as np
from PIL import Image
from hex_grid import KERNSTOWN as G
import compose_painted_map as CPM
Image.MAX_IMAGE_PIXELS = None
P = 0.55; BH = 6723; R = G.size_m * P; APO = R * math.sqrt(3) / 2
def hexc(c, r):
    x, y = G.hex_to_xy_m(c, r); return x * P, BH - y * P
def ll(lon, lat):
    x, y = G.lonlat_to_xy_m(lon, lat); return x * P, BH - y * P
wh = sorted(tuple(h) for h in json.load(open('data/features/stone_wall_hexsides.json'))['confederate_hexes'])
ax_ = np.array([hexc(c, r)[0] for c, r in wh]); ay_ = np.array([hexc(c, r)[1] - 0.38 * APO for c, r in wh])
cf = np.polyfit(ax_, ay_, 2); x0w, x1w = ax_.min() - 0.8 * R, ax_.max() + 0.8 * R
wx = x0w + (x1w - x0w) * 0.58; wy = np.polyval(cf, wx)
rt = CPM.FEAT.setdefault('_runtime', {})
rt['stone_wall_label_xy'] = (wx + 30, wy + 40)
rt['taylor_hotel_ll'] = [-78.1645 + 0.00028, 39.1856]
out = Image.open('data/basemap_painted_full.png')
lab = CPM.draw_labels(out.convert('RGBA'), scale=1.15).convert('RGB')
lab.save('data/basemap_painted_full_labeled.png', compress_level=3)
s_ = 3000 / max(lab.size); lab.resize((int(lab.width * s_), int(lab.height * s_)), Image.Resampling.LANCZOS).save('previews/v04_full.jpg', quality=90)
wcx, wcy = ll(-78.16444, 39.18389)
def crop(x0, y0, x1, y1, name): lab.crop((int(x0), int(y0), int(x1), int(y1))).save('previews/' + name, quality=90)
crop(wcx - 900, wcy - 820, wcx + 900, wcy + 760, 'v04_closeup_winchester.jpg')
x0k, y1k = ll(-78.240, 39.135); x1k, y0k = ll(-78.192, 39.162)
crop(x0k, y0k, x1k, y1k, 'v04_closeup_kernstown_wall.jpg')
fx, fy = hexc(14, 11); crop(fx - 700, fy - 500, fx + 700, fy + 500, 'v04_closeup_fields.jpg')
crop(wx - 600, wy - 160, wx + 400, wy + 220, 'v04_closeup_wall_label.jpg')
print('relabeled')
