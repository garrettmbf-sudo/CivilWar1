"""Parallel slicer for data/basemap_painted_full.png -> mod/Graphics/Tiles/Summer/SV_K_<col>_<row>.png (2000x2000, NO grid).
v0.3.1 fix: the game abuts tiles by the stock alpha hex (data/hex_mask.png: 1910x1672 px, centred at 999.5),
so the basemap hex (outer radius R) is mapped EXACTLY onto that hex (sx=1910/2R, sy=1672/(sqrt3 R)) instead of
stretching a 2R square over the whole 2000px PNG (old content was ~4.7%/3.6% too zoomed -> every edge mismatched).
Alpha = analytic hex + BLEED px of overlap beyond the hex edge with a 1.5px antialiased ramp (no hairline seams).
Orientation unchanged: hex (c,r) centre from hex_grid (odd-q, rows north, odd cols half row north), image y = H - y*P."""
import math, sys, os
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, 'scripts')
from hex_grid import KERNSTOWN as G
Image.MAX_IMAGE_PIXELS = None
P = 0.55; PAD = 200; BLEED = 4.0; HW, HH, C0 = 1910.0, 1672.0, 999.5
SRC = Image.open('data/basemap_painted_full.png').convert('RGB'); H = SRC.height
BIG = Image.new('RGB', (SRC.width+2*PAD, SRC.height+2*PAD), (150, 125, 90)); BIG.paste(SRC, (PAD, PAD)); del SRC
R = G.size_m*P; SX = HW/(2*R); SY = HH/(math.sqrt(3)*R)
u = np.arange(2000)-C0; X, Y = np.abs(u)[None, :], np.abs(u)[:, None]
a, b = HW/2, HH/2
d = np.maximum(Y-b, (X*2*b+Y*a-2*a*b)/math.hypot(2*b, a))  # signed px distance outside the hex
ALPHA = (np.clip((BLEED-d)/1.5+0.5, 0, 1)*255+0.5).astype(np.uint8)
OUT = 'mod/Graphics/Tiles/Summer'; os.makedirs(OUT, exist_ok=True)
def job(cr):
    col, row = cr
    x, y = G.hex_to_xy_m(col, row); cx, cy = x*P+PAD, H-y*P+PAD
    rgb = BIG.transform((2000, 2000), Image.Transform.AFFINE,
                        (1/SX, 0, cx-(C0+0.5)/SX, 0, 1/SY, cy-(C0+0.5)/SY), Image.Resampling.BICUBIC)
    rgba = np.dstack([np.asarray(rgb), ALPHA]); rgba[ALPHA == 0, :3] = 0
    Image.fromarray(rgba).save(f'{OUT}/SV_K_{col}_{row}.png', compress_level=6)
    return 1
if __name__ == '__main__':
    with Pool(7) as p: n = sum(p.imap_unordered(job, [(c, r) for c in range(G.cols) for r in range(G.rows)], chunksize=8))
    print('sliced', n)
